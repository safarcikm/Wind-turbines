"""Run the generator FEA checks: no-load, cogging, rated load, short-circuit demag,
no-load iron loss. Writes results/fea_summary.json and results/fea_*.png.

Run:  python3 run_fea.py      (~10-15 min)
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from fem import Geometry, Model, MU0

import sys

# Design iterations. "iter1" = docs/05 round 1; "iter2" = round 2 (docs/06).
VARIANTS = {
    "iter1": dict(geo={}, hcj20=1592e3, magnet="N42SH"),
    "iter2": dict(geo=dict(br20=1.26, hm=0.0077, d_slot=0.065), hcj20=1990e3, magnet="N40UH"),
}
VARIANT = sys.argv[1] if len(sys.argv) > 1 else "iter1"
OUT = Path(__file__).parent / "results" / ("" if VARIANT == "iter1" else VARIANT)
OUT.mkdir(parents=True, exist_ok=True)

N_RATED = 178.0
T_TARGET = 802.0                      # Nm, sizing torque (rated x 1.1)
A_LOAD = 30_000.0                     # A/m rms electric loading from sizing
E_LINE_TARGET = 380.0                 # V rms line, rated speed, hot magnets
HCJ20 = VARIANTS[VARIANT]["hcj20"]    # intrinsic coercivity at 20 C [A/m] (SH >= 20 kOe, UH >= 25 kOe)
RHO_CU_75 = 2.08e-8
HCJ_TC = -0.0055                      # 1/K, typical for SH grade (datasheet to confirm)
P15_50, HYST_SHARE, BUILD, RHO_LAM = 2.7, 0.7, 1.5, 7650


def fourier(y, n):
    N = len(y)
    k = np.arange(N)
    c = 2 / N * np.sum(y * np.exp(-2j * math.pi * n * k / N))
    return abs(c), math.atan2(-c.imag, c.real)


def main():
    geo = Geometry(**VARIANTS[VARIANT]["geo"])
    M = Model(geo)
    p = geo.poles // 2
    deg = math.pi / 180
    res = dict(variant=VARIANT, magnet=VARIANTS[VARIANT]["magnet"], geometry={k: getattr(geo, k) for k in
                         ["poles", "slots", "L", "r_s", "g", "sleeve", "hm", "h_ry", "alpha_m",
                          "w_t", "b0", "h_tip", "h_wedge", "d_slot", "h_sy", "br20", "t_mag"]},
               mesh=dict(nodes=int(M.mesh.n_nodes), elements=int(len(M.mesh.area)),
                         section_deg=360 / geo.sym))
    m = M.mesh
    stator_el = np.where(m.region == 1)[0]

    # ---------------- no-load over one electrical period (hot magnets 100 C)
    n_pos = 36
    el_period = 2 * math.pi / p
    thetas = np.arange(n_pos) * el_period / n_pos
    psi, Bx_hist, By_hist = [], [], []
    for i, th in enumerate(thetas):
        M.solve(th)
        psi.append(M.flux_linkage_per_turn())
        Bx, By = M.flux_density(M.A)
        Bx_hist.append(Bx[stator_el]); By_hist.append(By[stator_el])
        if i == 0:
            th_g, Br_g = M.gap_flux()
            Bmag = np.hypot(Bx, By)
            res["no_load_flux"] = dict(
                gap_Br_peak_T=round(float(np.max(np.abs(Br_g))), 3),
                gap_Br_fundamental_T=round(fourier(np.interp(np.linspace(0, geo.sec_angle, 2880, endpoint=False), th_g, Br_g), geo.poles // geo.sym // 2)[0], 3),
                stator_B_p50_T=round(float(np.percentile(Bmag[m.region == 1], 50)), 2),
                stator_B_p95_T=round(float(np.percentile(Bmag[m.region == 1], 95)), 2),
                rotor_yoke_B_p95_T=round(float(np.percentile(Bmag[m.region == 6], 95)), 2))
            fig, ax = plt.subplots(figsize=(8, 3))
            ax.plot(np.degrees(th_g), Br_g); ax.set_xlabel("Angle [deg mech], one 72 deg section")
            ax.set_ylabel("B radial [T]"); ax.set_title("No-load air gap flux density (magnets 100 C)")
            ax.grid(alpha=0.3); fig.tight_layout(); fig.savefig(OUT / "fea_gap_flux.png", dpi=120)
            # field plot
            fig, ax = plt.subplots(figsize=(9, 4.5))
            sel = m.region != 0
            sc = ax.scatter(np.degrees(m.cth[sel]), m.cr[sel] * 1000, c=Bmag[sel], s=0.3, cmap="viridis", vmin=0, vmax=2.0)
            plt.colorbar(sc, label="|B| [T]")
            ax.set_xlabel("Angle [deg mech]"); ax.set_ylabel("Radius [mm]")
            ax.set_title("No-load |B| in one section (unrolled)")
            fig.tight_layout(); fig.savefig(OUT / "fea_field_no_load.png", dpi=130)
    psi = np.array(psi)                    # per turn, full machine series, (n_pos, 3)
    psi1, delta = fourier(psi[:, 0], 1)
    deltas = [fourier(psi[:, ph], 1)[1] for ph in range(3)]   # own phase angle of each phase
    line = psi[:, 0] - psi[:, 1]
    lh = [fourier(line, n)[0] * n for n in range(1, 14)]
    thd_line = math.sqrt(sum(h ** 2 for h in lh[1:])) / lh[0]
    harmonics = [fourier(psi[:, 0], n)[0] * n for n in range(1, 14)]  # EMF harmonics scale with n
    thd = math.sqrt(sum(h ** 2 for h in harmonics[1:])) / harmonics[0]
    w_e = p * N_RATED * 2 * math.pi / 60
    e_phase_per_turn = w_e * psi1 / math.sqrt(2)
    n_coils_per_phase = geo.slots // 3
    turns_per_coil = E_LINE_TARGET / math.sqrt(3) / e_phase_per_turn
    nc = int(round(turns_per_coil))
    e_line_hot = math.sqrt(3) * e_phase_per_turn * nc
    br_cold = geo.br20 * (1 + geo.br_tc * (-40 - 20))
    e_line_cold_overspeed = e_line_hot * (230 / N_RATED) * br_cold / geo.br
    res["back_emf"] = dict(
        psi1_per_turn_full_machine_Wb=round(psi1, 5),
        turns_per_coil=nc, coils_per_phase_series=n_coils_per_phase,
        line_emf_rated_hot_V=round(e_line_hot, 1),
        line_emf_overspeed_cold_V=round(e_line_cold_overspeed, 1),
        line_emf_overspeed_cold_peak_V=round(e_line_cold_overspeed * math.sqrt(2), 1),
        phase_emf_THD_pct=round(100 * thd, 2),
        line_emf_THD_pct=round(100 * thd_line, 2),
        emf_harmonics_pct={str(n + 1): round(100 * h / harmonics[0], 2) for n, h in enumerate(harmonics) if n > 0})
    fig, ax = plt.subplots(figsize=(7, 3.5))
    th_el = np.degrees(thetas * p)
    for ph, lab in enumerate("ABC"):
        e = (np.roll(psi[:, ph], -1) - np.roll(psi[:, ph], 1)) / (2 * (thetas[1] - thetas[0]))  # periodic central difference
        ax.plot(th_el, e * N_RATED * 2 * math.pi / 60 * nc, label=f"Phase {lab}")
    ax.set_xlabel("Electrical angle [deg]"); ax.set_ylabel("Phase EMF [V]")
    ax.set_title(f"No-load phase back-EMF at {N_RATED:.0f} rpm, magnets 100 C"); ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(OUT / "fea_back_emf.png", dpi=120)

    # ---------------- no-load iron loss (Bertotti-like, harmonic sum)
    f_e = p * N_RATED / 60
    Bx_hist, By_hist = np.array(Bx_hist), np.array(By_hist)
    kh = HYST_SHARE * P15_50 / (50 * 1.5 ** 2)
    ke = (1 - HYST_SHARE) * P15_50 / (50 ** 2 * 1.5 ** 2)
    Fx = np.fft.rfft(Bx_hist, axis=0) * 2 / n_pos
    Fy = np.fft.rfft(By_hist, axis=0) * 2 / n_pos
    loss_density = np.zeros(len(stator_el))
    for n in range(1, Fx.shape[0]):
        Bn2 = np.abs(Fx[n]) ** 2 + np.abs(Fy[n]) ** 2
        loss_density += kh * n * f_e * Bn2 + ke * (n * f_e) ** 2 * Bn2
    mass_el = m.area[stator_el] * geo.L * 0.96 * RHO_LAM * geo.sym
    p_fe = float(np.sum(loss_density * mass_el) * BUILD)
    res["iron_loss_no_load_W"] = round(p_fe)

    # ---------------- cogging over one cogging period
    lcm = geo.slots * geo.poles // math.gcd(geo.slots, geo.poles)
    cog_period = 2 * math.pi / lcm
    th_c = np.arange(24) * cog_period / 24
    cog = []
    for th in th_c:
        M.solve(th)
        cog.append(M.torque())
    cog = np.array(cog)
    def skewed(n_steps):
        if n_steps == 0:
            return cog
        out = np.zeros_like(cog)
        for k in range(n_steps):
            shift = k / n_steps * cog_period
            out += np.interp(np.mod(th_c + shift, cog_period), th_c, cog, period=cog_period)
        return out / n_steps
    res["cogging"] = dict(
        period_deg_mech=round(360 / lcm, 3),
        peak_to_peak_Nm=round(float(cog.max() - cog.min()), 2),
        peak_to_peak_pct_rated=round(float(cog.max() - cog.min()) / 729 * 100, 3),
        two_step_skew_pp_Nm=round(float(np.ptp(skewed(2))), 3),
        three_step_skew_pp_Nm=round(float(np.ptp(skewed(3))), 3))
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.plot(np.degrees(th_c), cog, "o-", label="No skew")
    ax.plot(np.degrees(th_c), skewed(2), label="2-step skew")
    ax.plot(np.degrees(th_c), skewed(3), label="3-step skew")
    ax.set_xlabel("Rotor angle [deg mech]"); ax.set_ylabel("Cogging torque [Nm]")
    ax.set_title("Cogging torque over one period"); ax.grid(alpha=0.3); ax.legend()
    fig.tight_layout(); fig.savefig(OUT / "fea_cogging.png", dpi=120)

    # ---------------- rated load, q-axis current (Id = 0)
    # flux linkage of phase A ~ psi1 cos(p*theta - delta)
    NI_rms_side = A_LOAD * math.pi * 2 * geo.r_s / geo.slots / 2     # ampere-turns per coil side
    def currents(theta, NI_peak, axis="q"):
        out = []
        for ph in range(3):
            a = p * theta - deltas[ph]
            out.append(NI_peak * (-math.sin(a) if axis == "q" else math.cos(a)))
        return out
    def mean_torque(NI_peak, n=1):
        ts = []
        for th in np.linspace(0, 2 * math.pi / p / 6, n, endpoint=False):
            M.solve(th, currents(th, NI_peak))
            ts.append(M.torque())
        return np.array(ts)
    NI_peak = math.sqrt(2) * NI_rms_side
    t0 = mean_torque(NI_peak, 1)[0]
    sign = 1 if t0 > 0 else -1
    if sign < 0:   # flip current direction convention
        def currents(theta, NI_peak, axis="q", _c=currents):
            return [-c for c in _c(theta, NI_peak, axis)]
        t0 = -t0
    # scale current to reach the target torque (one secant step, then verify)
    NI_t = NI_peak * T_TARGET / t0
    t1 = mean_torque(NI_t, 1)[0]
    NI_t = NI_t + (T_TARGET - t1) * (NI_t - NI_peak) / (t1 - t0)
    ripple_th = np.linspace(0, 2 * math.pi / p / 6, 16, endpoint=False)
    tr = []
    for th in ripple_th:
        M.solve(th, currents(th, NI_t))
        tr.append(M.torque())
    tr = np.array(tr)
    J_cu = NI_t / math.sqrt(2) / (M.side_area[0, 0] * 0.45) / 1e6
    cu_total = geo.slots * 2 * M.side_area[0, 0] * 0.45
    l_half_turn = geo.L + 1.3 * 2 * math.pi * geo.r_s / geo.slots
    p_cu75 = RHO_CU_75 * (J_cu * 1e6) ** 2 * cu_total * l_half_turn
    p_shaft = 729 * N_RATED * 2 * math.pi / 60
    p_fe_load = p_fe * 1.15
    p_tot = p_cu75 + p_fe_load + 40 + 70
    res["losses_rated"] = dict(copper_75C_W=round(p_cu75), iron_W=round(p_fe_load), rotor_W=40, stray_W=70,
                               total_W=round(p_tot), efficiency_75C=round(1 - p_tot / p_shaft, 4),
                               copper_area_total_m2=round(cu_total, 5), slot_area_mm2=round(2 * M.side_area[0, 0] * 1e6))
    res["rated_load"] = dict(
        design_ampere_turns_per_side_rms=round(NI_rms_side),
        torque_at_design_loading_Nm=round(t0, 1),
        ampere_turns_per_side_rms_for_802Nm=round(NI_t / math.sqrt(2)),
        current_density_for_802Nm_A_per_mm2=round(J_cu, 2),
        phase_current_rms_A=round(NI_t / math.sqrt(2) / nc, 1),
        mean_torque_Nm=round(float(tr.mean()), 1),
        ripple_pp_Nm=round(float(np.ptp(tr)), 1),
        ripple_pp_pct=round(float(np.ptp(tr) / tr.mean() * 100), 2))
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.plot(np.degrees(ripple_th), tr, "o-"); ax.axhline(tr.mean(), ls="--", c="gray")
    ax.set_xlabel("Rotor angle [deg mech]"); ax.set_ylabel("Torque [Nm]")
    ax.set_title("Torque at rated load (Id = 0)"); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(OUT / "fea_load_torque.png", dpi=120)

    # ---------------- d-axis inductance and short-circuit demagnetisation (magnets 120 C)
    geo.t_mag = 120.0
    th_d = delta / p      # rotor angle where phase A is aligned with the d axis
    M.solve(th_d)
    psi_pm = M.flux_linkage_per_turn()[0] * nc
    NI_d = NI_t
    M.solve(th_d, currents(th_d, NI_d, axis="d"))
    psi_d = M.flux_linkage_per_turn()[0] * nc
    # d-axis current direction: pick the one that reduces flux
    if abs(psi_d) > abs(psi_pm):
        def currents_d(theta, NI_peak):
            return [-c for c in currents(theta, NI_peak, axis="d")]
    else:
        def currents_d(theta, NI_peak):
            return currents(theta, NI_peak, axis="d")
    M.solve(th_d, currents_d(th_d, NI_d))
    psi_d = M.flux_linkage_per_turn()[0] * nc
    I_d = NI_d / nc                                  # peak phase current used
    # synchronous d-axis inductance: phase A carries its peak current at d alignment
    Ld = abs(psi_pm - psi_d) / I_d
    I_sc_peak = abs(psi_pm) / Ld
    NI_sc = 2.0 * I_sc_peak * nc                     # fully offset transient: 2x steady peak
    M.solve(th_d, currents_d(th_d, NI_sc))
    H, rH = M.magnet_field_along_magnetisation()
    hcj120 = HCJ20 * (1 + HCJ_TC * (120 - 20))
    res["short_circuit_demag"] = dict(
        magnet_temp_C=120, Ld_mH=round(Ld * 1e3, 2),
        steady_short_circuit_current_peak_A=round(I_sc_peak, 1),
        transient_current_peak_A=round(2 * I_sc_peak, 1),
        min_H_in_magnet_kA_per_m=round(float(H.min()) / 1e3, 1),
        H_1pct_worst_kA_per_m=round(float(np.percentile(H, 1)) / 1e3, 1),
        Hcj_120C_kA_per_m=round(hcj120 / 1e3, 1),
        margin_to_Hcj_pct=round(100 * (1 - abs(float(H.min())) / hcj120), 1))
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.hist(H / 1e3, bins=80)
    ax.axvline(-hcj120 / 1e3, c="r", ls="--", label="Hcj at 120 C")
    ax.set_xlabel("H along magnetisation [kA/m]"); ax.set_ylabel("Magnet elements")
    ax.set_title("Magnet field during worst-case short circuit (120 C)"); ax.legend()
    fig.tight_layout(); fig.savefig(OUT / "fea_demag.png", dpi=120)

    # same check with N40UH (Br 1.26 T, Hcj >= 1990 kA/m at 20 C)
    geo.br20 = 1.26
    M.solve(th_d, currents_d(th_d, NI_sc))
    H2, _ = M.magnet_field_along_magnetisation()
    hcj120_uh = 1990e3 * (1 + HCJ_TC * (120 - 20))
    res["short_circuit_demag_N40UH"] = dict(
        min_H_in_magnet_kA_per_m=round(float(H2.min()) / 1e3, 1),
        Hcj_120C_kA_per_m=round(hcj120_uh / 1e3, 1),
        margin_to_Hcj_pct=round(100 * (1 - abs(float(H2.min())) / hcj120_uh), 1))
    geo.br20 = 1.30

    (OUT / "fea_summary.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
