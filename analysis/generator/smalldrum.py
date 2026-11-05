"""Smaller generator drums with the doc 20 magnets (doc 22).

Martin, 2026-11-05: a version with a drum diameter under 500 mm and one under
300 mm, using the 30 x 15 x 12 magnets (two 30 x 15 x 6 N42SH blocks bonded),
compared with the present Ø646 drum, and the effect on energy output.

Each machine keeps the doc 20 pole (one 30 mm wide, 12 mm magnet across, rows
of 15 mm blocks step-skewed, 0.15 bond, 2 mm gap, 0.5 mm sleeve, 9 mm drum
steel under the seat), the 9/8 slot/pole family of the P1 winding (tooth coils,
45/40, 36/32, 18/16), the same current density and slot fill, and a pole count
that keeps the pole pitch near the P1's 47 mm.

  P1   drum Ø646, gap Ø598, 40 poles / 45 slots, slots 65 deep (doc 20 rotor)
  D490 drum Ø490, 32 poles / 36 slots
  D290 drum Ø290, 16 poles / 18 slots (stator inside clears the Ø140 spindle)

FEA (2D, per 74 mm of stack, 100 °C magnets): EMF per turn, torque at the
sizing current density, transient short-circuit margin. From it:
  A  stack length for the full 802 Nm design torque (12 kW stays)
  B  torque and power if the stack stays 74 mm
then losses and the annual energy for both (energy.py-style Rayleigh, as doc 12).

Run:  python3 smalldrum.py fea P1 D490 D290   -> results/small_<key>.json  (~5 min each)
      python3 smalldrum.py energy             -> results/small_summary.json
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

from magnets import Shape, MagGeometry, MagModel, fourier, N_RATED

OUT = Path(__file__).parent / "results"
HERE = Path(__file__).parent
N42SH = dict(br20=1.29, hcj20=1592e3, a_br=-0.0012, b_hcj=-0.0060)
STACK0 = 0.074
NI_P1 = 895.5               # peak ampere-turns per coil side at 802 Nm in the P1 (doc 06 sizing current)
T_DES = 802.0
T_RATED = 729.0
YOKE = 0.009                # drum steel under the seat (doc 20)
W, HM, BOND = 0.030, 0.012, 0.15e-3
FILL = 0.45

VARIANTS = {
    # key: drum OD [m], poles, slots, slot depth [m], stator yoke [m]
    "P1": (0.646, 40, 45, 0.065, 0.0114),
    "D490": (0.490, 32, 36, 0.060, 0.0110),
    "D290": (0.290, 16, 18, 0.030, 0.0100),
}


def r_s_for(drum_od):
    """Stator bore radius that puts the drum outside at drum_od/2 with the 30 x 12 magnet."""
    r_out = drum_od / 2
    lo, hi = 0.05, 0.40
    for _ in range(60):
        rs = (lo + hi) / 2
        rm1 = rs + 0.0025
        seat = math.hypot(rm1 + HM, W / 2) + BOND
        if seat + YOKE > r_out:
            hi = rs
        else:
            lo = rs
    return lo


def build(key):
    od, poles, slots, d_slot, h_sy = VARIANTS[key]
    r_s = 0.299 if key == "P1" else r_s_for(od)
    tau_s = 2 * math.pi * r_s / slots
    w_t = 0.0223 * tau_s / (2 * math.pi * 0.299 / 45)       # same tooth share of the slot pitch as the P1
    shape = Shape(key, f"30x15x12, {poles} poles", 1, True, hm=HM, b=W, n_ax=5, l_ax=0.015)
    geo = MagGeometry(poles=poles, slots=slots, br20=N42SH["br20"], br_tc=N42SH["a_br"], hm=HM, d_slot=d_slot,
                      h_sy=h_sy, w_t=w_t, L=STACK0, g=0.0020, sleeve=0.0005, r_s=r_s)
    geo.r_seat = shape.seat_radius(geo)
    geo.r_y_out = geo.r_seat + YOKE
    return geo, shape


def fea(key):
    geo, shape = build(key)
    M = MagModel(geo, shape, n_theta=1440)
    p = geo.poles // 2
    el = 2 * math.pi / p
    w_e = p * N_RATED * 2 * math.pi / 60
    a_side = float(M.side_area[0, 0])
    out = dict(key=key, poles=geo.poles, slots=geo.slots, drum_od_mm=round(2e3 * geo.r_y_out, 1),
               gap_d_mm=round(2e3 * (geo.r_s + geo.g / 2), 1), r_s_mm=round(1e3 * geo.r_s, 2),
               seat_d_mm=round(2e3 * geo.r_seat, 2), stator_bore_mm=round(2e3 * geo.r_in, 1),
               slot_depth_mm=geo.d_slot * 1e3, tooth_mm=round(geo.w_t * 1e3, 2), slot_side_mm2=round(a_side * 1e6, 1),
               pole_pitch_mm=round(2 * math.pi * geo.r_m1 / geo.poles * 1e3, 1),
               alpha=round(2 * math.atan(W / 2 / geo.r_m1) / (2 * math.pi / geo.poles), 3),
               f_el_rated_Hz=round(p * N_RATED / 60, 1))
    geo.t_mag = 100.0
    psi = []
    for t in np.arange(18) * el / 18:
        M.solve(t)
        psi.append(M.flux_linkage_per_turn())
    psi = np.array(psi)
    psi1, _ = fourier(psi[:, 0], 1)
    deltas = [fourier(psi[:, k], 1)[1] for k in range(3)]
    out["line_emf_per_turn_100C_V"] = round(math.sqrt(3) * w_e * psi1 / math.sqrt(2), 3)
    out["turns_for_380V"] = round(380 / out["line_emf_per_turn_100C_V"], 1)

    def currents(theta, NI, axis, sgn=1.0):
        return [sgn * NI * (-math.sin(p * theta - d) if axis == "q" else math.cos(p * theta - d)) for d in deltas]

    # same current density and fill as the P1 at its sizing point
    P1_side = json.loads((OUT / "small_P1.json").read_text())["slot_side_mm2"] * 1e-6 if key != "P1" else a_side
    NI = NI_P1 * a_side / P1_side
    out["NI_peak_per_side"] = round(NI, 1)
    M.solve(0.0, currents(0.0, NI, "q"))
    sgn = 1.0 if M.torque() > 0 else -1.0
    tq = []
    for t in np.arange(6) * (2 * math.pi / geo.slots) / 6:
        M.solve(t, currents(t, NI, "q", sgn))
        tq.append(M.torque())
    out["torque_74mm_Nm"] = round(abs(float(np.mean(tq))), 1)
    # transient short circuit at 100 °C
    th_d = deltas[0] / p
    hcj = N42SH["hcj20"] * (1 + N42SH["b_hcj"] * 80)
    M.solve(th_d)
    psi_pm = M.flux_linkage_per_turn()[0]
    for s_d in (1.0, -1.0):
        M.solve(th_d, currents(th_d, NI, "d", s_d))
        psi_d = M.flux_linkage_per_turn()[0]
        if abs(psi_d) < abs(psi_pm):
            break
    NI_sc = NI * abs(psi_pm) / abs(psi_pm - psi_d)
    out["NI_sc_over_NI_rated"] = round(NI_sc / NI, 2)
    for name, mult in (("steady_sc", 1), ("transient_sc", 2)):
        M.solve(th_d, currents(th_d, mult * NI_sc, "d", s_d))
        H, _ = M.magnet_field_along_magnetisation()
        out[f"{name}_margin_100C_pct"] = round(100 * (1 - abs(float(H.min())) / hcj), 1)
    (OUT / f"small_{key}.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out), flush=True)


# ------------------------------------------------------------------ losses and energy
def losses(r, L):
    """Copper volume and lamination volume for stack L (relative measures, calibrated on the P1)."""
    geo, _ = build(r["key"])
    a_side = r["slot_side_mm2"] * 1e-6
    tau_s = 2 * math.pi * (geo.r_s - geo.h_tip - geo.d_slot / 2) / geo.slots
    l_end = math.pi / 2 * (geo.w_t + (tau_s - geo.w_t) / 2)        # end-turn overhang per coil end
    v_cu = geo.slots * 2 * a_side * FILL * (L + l_end)
    v_lam = (math.pi * (geo.r_s ** 2 - geo.r_in ** 2) - geo.slots * 2 * a_side) * L
    return v_cu, v_lam


def energy():
    sys.path.insert(0, str(HERE.parent / "power"))
    sys.path.insert(0, str(HERE.parent / "rotor"))
    import study
    from bem import Blade, CLEAN
    import sizing as PW

    rows = {k: json.loads((OUT / f"small_{k}.json").read_text()) for k in VARIANTS}
    p1 = rows["P1"]
    t1 = p1["torque_74mm_Nm"]
    vcu1, vlam1 = losses(p1, STACK0)
    f1 = p1["f_el_rated_Hz"]
    blade = Blade(R=3.75, tsr_design=study.TSR_DESIGN, cl_design=study.CL_DESIGN)
    w_r = PW.RPM_RATED * 2 * math.pi / 60
    aero = []
    for V in study.VS:
        res_, om, _ = study.best_point(blade, V, study.TIP_SPEED_MAX / blade.R, CLEAN)
        P = min(res_.power, PW.P_SHAFT)
        if V > study.V_STORM_START:
            P = PW.P_SHAFT * (1 - (1 - study.STORM_FRAC) * (V - study.V_STORM_START) /
                              (study.V_CUTOUT - study.V_STORM_START))
        if V > study.V_CUTOUT:
            P = 0.0
        aero.append((float(V), P, min(om * 60 / (2 * math.pi), PW.RPM_RATED)))

    def conv(P, p0, k1, k2, Pn=13e3):
        return p0 + k1 * P + k2 * Pn * (P / Pn) ** 2

    summary = []
    for key, r in rows.items():
        # torque per metre: the 2D torque scales with stack length (end effects left out)
        t_per_m = r["torque_74mm_Nm"] / STACK0 * (T_DES / t1)       # calibrated so the P1 makes 802 Nm at 74 mm
        for case, L in (("A_same_power", T_DES / t_per_m), ("B_stack_74mm", STACK0)):
            if key == "P1" and case == "B_stack_74mm":
                continue
            t_max = t_per_m * L                   # torque at the sizing current density
            v_cu, v_lam = losses(r, L)
            pcu_at_tmax = 496.0 * (T_DES / T_RATED) ** 2 * v_cu / vcu1     # doc 06: 496 W at 729 Nm, 75 °C
            fe_scale = v_lam / vlam1 * (r["f_el_rated_Hz"] / f1) ** 1.4
            t_cap = min(t_max / 1.10, T_RATED)                         # keep the doc 06 10 % torque margin
            p_cap = t_cap * w_r
            curve = []
            for V, P, rpm in aero:
                w = rpm * 2 * math.pi / 60
                Pg = min(P, p_cap)
                if Pg <= 0 or rpm < PW.RPM_MIN * 0.9:
                    curve.append((V, 0.0)); continue
                # below the cap the rotor follows its optimum; at the cap it runs at rated speed
                if Pg < P:
                    w = w_r
                T = Pg / w
                p_cu = pcu_at_tmax * (T / t_max) ** 2
                p_fe = fe_scale * 219 * (w / w_r) ** 1.6 + 40 * (w / w_r) ** 2 + 70 * (Pg / PW.P_SHAFT) ** 2
                P_gen = Pg - p_cu - p_fe
                P_dc = P_gen - conv(P_gen, 25, 0.004, 0.006)
                P_ac = P_dc - conv(P_dc, 30, 0.005, 0.008)
                curve.append((V, max(P_ac - 120.0, 0.0)))
            Vs = np.array([c[0] for c in curve]); Pn = np.array([c[1] for c in curve])
            aep = {}
            for va in (5.0, 6.0, 7.0, 8.0, 10.0):
                k, c = 2.0, va / math.gamma(1.5)
                f = (k / c) * (Vs / c) ** (k - 1) * np.exp(-(Vs / c) ** k)
                aep[str(va)] = round(float(np.sum(Pn * f * (Vs[1] - Vs[0])) * 8760 * 0.97 / 1000))
            T_r = min(T_RATED, t_cap)
            pcu_r = pcu_at_tmax * (T_r / t_max) ** 2
            pfe_r = fe_scale * 219 + 40 + 70 * (T_r * w_r / PW.P_SHAFT) ** 2
            n_rows = max(1, round((L + 0.0002) / 0.0152))
            geo_, _ = build(key)
            m_drum = math.pi * (geo_.r_y_out ** 2 - geo_.r_seat ** 2) * L * 7850
            summary.append(dict(
                key=key, case=case, stack_mm=round(L * 1e3, 1), drum_od_mm=r["drum_od_mm"], poles=r["poles"],
                slots=r["slots"], torque_max_Nm=round(t_max), rated_torque_Nm=round(T_r),
                rated_shaft_kW=round(T_r * w_r / 1e3, 2), net_rated_kW=round(max(Pn), 2) / 1e3,
                copper_loss_rated_W=round(pcu_r), iron_loss_rated_W=round(pfe_r),
                gen_eff_rated_pct=round(100 * (1 - (pcu_r + pfe_r) / (T_r * w_r)), 1),
                turns_for_380V=r["turns_for_380V"], transient_sc_margin_100C_pct=r["transient_sc_margin_100C_pct"],
                magnet_blocks=r["poles"] * n_rows * 2, magnet_kg=round(r["poles"] * n_rows * 2 * 20.5e-3, 2),
                copper_kg=round(v_cu * 8900, 1), drum_band_kg=round(m_drum, 1), lamination_kg=round(v_lam * 7650, 1),
                aep_kWh=aep, net_power_curve=[(c[0], round(c[1])) for c in curve]))
    base = next(s for s in summary if s["key"] == "P1")
    for s in summary:
        s["aep_vs_P1_pct"] = {k: round(100 * (v / base["aep_kWh"][k] - 1), 1) for k, v in s["aep_kWh"].items()}
    (OUT / "small_summary.json").write_text(json.dumps(summary, indent=1))
    for s in summary:
        print(s["key"], s["case"], s["stack_mm"], s["torque_max_Nm"], s["rated_shaft_kW"], s["copper_loss_rated_W"],
              s["iron_loss_rated_W"], s["gen_eff_rated_pct"], s["magnet_blocks"], s["magnet_kg"], s["copper_kg"], s["lamination_kg"], s["drum_band_kg"],
              s["aep_kWh"], s["aep_vs_P1_pct"])


if __name__ == "__main__":
    if sys.argv[1] == "fea":
        for k in sys.argv[2:]:
            fea(k)
    else:
        energy()
