"""6 kW turbine (doc 28): is variable pitch needed? Power regulation and storm survival study.

Run:  python3 regulation.py     (~1 min) -> results/regulation.json and figures F01-F05

One rotor (sized in sizing.py) is run with the doc 03 BEM model under four ways of limiting power:
  pitch   collective pitch to feather, variable speed (the 12 kW approach, doc 11/24)
  stall   fixed pitch, variable speed; above rated the converter slows the rotor into stall
  furl    fixed pitch, tail vane turns the rotor out of the wind (passive)
  (electrical braking alone is checked as a stopping means, not as a regulation method)

Then the storm cases that decide the question:
  * parked blade loads at V_e50 for every yaw error and azimuth (strip theory, 360 deg polars)
  * the torque needed to hold and stop a fixed-pitch rotor, against what the generator,
    a passive resistor and a spring brake can give
  * runaway speed if all electrical load is lost
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
OUT = HERE / "results"; OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(HERE.parent / "rotor"))
sys.path.insert(0, str(HERE.parent / "size_tsr_map"))
from bem import Blade, ROUGH, Polar, solve  # noqa: E402
import model as m27  # noqa: E402

DES = json.loads((OUT / "design.json").read_text())
P_E = DES["P_e"]                       # kW electrical
R = DES["R"]; TSR = DES["tsr"]; RPM_CAP = DES["rpm"]
OM_CAP = RPM_CAP * math.pi / 30
P_SHAFT = m27.SHAFT_PER_E * P_E * 1000
Q_RATED = P_SHAFT / OM_CAP
RHO, RHO_COLD = 1.225, 1.35
V_E50 = 77.0
A = math.pi * R ** 2
BL = Blade(R=R, r_hub=0.40 / 3.75 * R, tsr_design=TSR, cl_design=1.0)
VS = np.arange(3.0, 30.01, 0.5)

C = dict(blue="#2f6db5", orange="#d9822b", green="#3a8f5c", red="#c0392b", grey="#7f8c8d", purple="#7d5ba6")


def pt(V, om, pitch, rho=RHO):
    return solve(BL, V, om, pitch, rho, ROUGH)


# ---------------------------------------------------------------- Cp tables at fixed pitch
LAMS = np.round(np.arange(0.4, 12.01, 0.1), 2)


def cp_table(pitch):
    rows = [pt(10.0, l * 10.0 / R, pitch) for l in LAMS]
    return np.array([r.cp for r in rows]), np.array([r.cq for r in rows]), np.array([r.ct for r in rows])


def lam_opt(cp):
    return float(LAMS[int(np.argmax(cp))])


# ---------------------------------------------------------------- pitch regulation
def pitch_schedule(p0=0.0):
    cp, _, _ = cp_table(p0)
    lo = lam_opt(cp)
    out = []
    for V in VS:
        target = P_SHAFT
        if V > 25:
            target = P_SHAFT * (1 - 0.6 * (V - 25) / 5)
        om = min(lo * V / R, OM_CAP)
        r = pt(V, om, p0)
        p = p0
        if r.power > target:
            a, b = p0, 40.0
            for _ in range(40):
                mid = 0.5 * (a + b)
                if pt(V, om, mid).power > target:
                    a = mid
                else:
                    b = mid
            p = 0.5 * (a + b); r = pt(V, om, p)
        out.append(dict(V=float(V), rpm=om * 30 / math.pi, pitch=p, P=r.power, Q=r.torque, T=r.thrust,
                        Mflap=r.root_flap_moment))
    return out


# ---------------------------------------------------------------- stall regulation by speed
def stall_schedule(pf, rho=RHO, ramp=True):
    """Fixed pitch pf. Below rated: optimum TSR up to the speed cap. Above: the lowest-loading
    speed on the stall side (lambda < lambda_opt) where P = target. Returns None-power if not reachable."""
    cp, cq, ct = cp_table(pf)
    lo = lam_opt(cp)
    out = []
    for V in VS:
        target = P_SHAFT
        if ramp and V > 25:
            target = P_SHAFT * (1 - 0.6 * (V - 25) / 5)
        om = min(lo * V / R, OM_CAP)
        r = pt(V, om, pf, rho)
        ok = True
        if r.power > target:
            # search downwards in speed (stall side) for P = target
            a, b = 0.15 * om, om          # P(a) < target assumed, P(b) > target
            if pt(V, a, pf, rho).power > target:
                ok = False
            for _ in range(40):
                mid = 0.5 * (a + b)
                if pt(V, mid, pf, rho).power > target:
                    b = mid
                else:
                    a = mid
            om = 0.5 * (a + b); r = pt(V, om, pf, rho)
        # gust torque: wind steps up 30 % before the controller can react (rotor speed unchanged)
        g = pt(min(V * 1.3, 40.0), om, pf, rho)
        out.append(dict(V=float(V), rpm=om * 30 / math.pi, P=r.power, Q=r.torque, T=r.thrust,
                        Mflap=r.root_flap_moment, Q_gust=g.torque, P_gust=g.power, reachable=ok))
    return out


def runaway_rpm(pf, V):
    cp, _, _ = cp_table(pf)
    i = int(np.argmax(cp))
    j = i + int(np.argmax(cp[i:] <= 0)) if np.any(cp[i:] <= 0) else len(cp) - 1
    return float(LAMS[j] * V / R * 30 / math.pi), float(LAMS[j])


def max_aero_torque(pf, V, om_max, rho=RHO):
    """Largest aerodynamic torque on a fixed-pitch rotor at wind V for any speed 0..om_max
    (what a brake or the generator must overcome to stop it)."""
    oms = np.linspace(0.02, om_max, 60)
    q = [pt(V, o, pf, rho).torque for o in oms]
    k = int(np.argmax(q))
    return float(q[k]), float(oms[k] * 30 / math.pi)


# ---------------------------------------------------------------- parked loads, strip theory
def parked_root_moment(pitch, gamma_deg, psi_deg, cdmax=1.5, V=V_E50, rho=RHO_COLD):
    """Resultant blade root bending moment (flap+edge) of a stopped blade. Wind from yaw error gamma,
    blade at azimuth psi (0 = up). No induction. 360 deg polar with flat plate Cd = cdmax at 90 deg."""
    pol = Polar("park", cl0=ROUGH.cl0, cla=ROUGH.cla, clmax=ROUGH.clmax, cd0=ROUGH.cd0, kd=ROUGH.kd,
                cl_cdmin=ROUGH.cl_cdmin, cdmax=cdmax)
    g, s = math.radians(gamma_deg), math.radians(psi_deg)
    W = V * np.array([math.cos(g), math.sin(g), 0.0])
    e_s = np.array([0.0, math.sin(s), math.cos(s)])
    e_t = np.cross([1.0, 0, 0], e_s)
    u_ax = W[0]
    u_tan = -float(W @ e_t)
    phi = math.atan2(u_ax, u_tan)
    theta = np.radians(BL.twist + BL.twist_tip_offset + pitch)
    alpha = np.degrees(phi - theta)
    alpha = (alpha + 180) % 360 - 180
    cl, cd = pol.coeffs(alpha)
    cl = np.where(BL.is_cylinder, 0.0, cl); cd = np.where(BL.is_cylinder, 1.0, cd)
    q = 0.5 * rho * (u_ax ** 2 + u_tan ** 2) * BL.chord * BL.dr
    fx = q * (cl * math.cos(phi) + cd * math.sin(phi))
    ft = q * (cl * math.sin(phi) - cd * math.cos(phi))
    arm = BL.r - BL.r_hub
    return math.hypot(float(np.sum(fx * arm)), float(np.sum(ft * arm))), float(np.sum(fx))


def parked_sweep(pitch):
    gs = np.arange(-180, 181, 5); ps = np.arange(0, 360, 10)
    M = np.array([[parked_root_moment(pitch, g, p)[0] for p in ps] for g in gs])
    return gs, M.max(axis=1)


def broadside_ref(cdmax=1.5, V=V_E50, rho=RHO_COLD):
    q = 0.5 * rho * V ** 2 * cdmax * BL.chord * BL.dr
    return float(np.sum(q * (BL.r - BL.r_hub)))


# ---------------------------------------------------------------- electrical braking
def elec_brake_pu(w_pu, x_pu, r_pu=0.04):
    """Torque (per unit of rated) from a PM generator: shorted terminals and an ideal matched resistor."""
    w = np.asarray(w_pu, float)
    t_sc = w * r_pu / (r_pu ** 2 + (w * x_pu) ** 2)
    t_res = np.full_like(w, 1.0 / (2 * x_pu))           # R_ext = w X: max power transfer
    t_res = np.minimum(t_res, w / (r_pu + 1e-9))         # cannot exceed the short-circuit current limit at low speed
    return t_sc, t_res


# ---------------------------------------------------------------- energy
def aep_from(curve_V, curve_P, scen, curve_rpm=None):
    net = m27.chain_losses(P_E)
    rpms = curve_rpm if curve_rpm is not None else [RPM_CAP] * len(curve_P)
    Pn = np.array([max(net(p, max(n, 0.3 * RPM_CAP), RPM_CAP)[0], 0) if p > 0 else 0 for p, n in zip(curve_P, rpms)])
    V = np.array(curve_V)
    out = {}
    for s in scen:
        c = s["v"] / math.gamma(1 + 1 / s["k"])
        f = (s["k"] / c) * (V / c) ** (s["k"] - 1) * np.exp(-(V / c) ** s["k"])
        out[s["key"]] = float(np.sum(Pn * f) * 0.5 * 8760 * 0.97 / 1000)
    return out


def furl_curve(base_V, base_P, kind):
    """Furling: 'ideal' holds rated like pitch; 'typical' follows the shape of published small
    furling turbine curves: furl starts at rated, power falls to 70 % at 15 m/s and 55 % at 25 m/s,
    and the rotor keeps running furled (no storm stop)."""
    P = []
    for V, p in zip(base_V, base_P):
        if p < P_SHAFT * 0.999 and V < 12:
            P.append(p); continue
        if kind == "ideal":
            P.append(P_SHAFT)
        else:
            Vr = DES["rated_wind"]
            f = np.interp(V, [Vr, Vr + 1.5, 15, 25, 30], [1.0, 0.92, 0.70, 0.55, 0.50])
            P.append(min(p, P_SHAFT) * f if V <= Vr else P_SHAFT * f)
    return P


def main():
    res = dict(design=DES, Q_rated=Q_RATED, rpm_cap=RPM_CAP)
    # -------- fixed pitch choice
    choice = {}
    for pf in (-3.0, -2.0, -1.0, 0.0, 1.0):
        cp, cq, ct = cp_table(pf)
        st = stall_schedule(pf)
        aep = aep_from([r["V"] for r in st], [r["P"] for r in st], m27.SCENARIOS, [r["rpm"] for r in st])
        choice[pf] = dict(cp_max=float(cp.max()), lam_opt=lam_opt(cp),
                          Q_max_cont=max(r["Q"] for r in st) / Q_RATED,
                          Q_gust=max(r["Q_gust"] for r in st) / Q_RATED,
                          reachable=all(r["reachable"] for r in st), aep=aep)
        print("pitch", pf, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in choice[pf].items() if k != "aep"},
              {k: round(v) for k, v in aep.items()})
    res["fixed_pitch_choice"] = {str(k): v for k, v in choice.items()}
    PF = -2.0   # chosen: stalls earlier, lower stall torque, -1 % Cp
    res["PF"] = PF

    pit = pitch_schedule(0.0)
    sta = stall_schedule(PF)
    sta_cold = stall_schedule(PF, rho=RHO_COLD)
    res["pitch_curve"] = pit; res["stall_curve"] = sta; res["stall_curve_cold"] = sta_cold

    # -------- energy
    V = [r["V"] for r in pit]
    curves = dict(pitch=[r["P"] for r in pit], stall=[r["P"] for r in sta],
                  furl_ideal=furl_curve(V, [r["P"] for r in sta], "ideal"),
                  furl_typical=furl_curve(V, [r["P"] for r in sta], "typical"))
    rpms = dict(pitch=[r["rpm"] for r in pit], stall=[r["rpm"] for r in sta])
    aeps = {k: aep_from(V, c, m27.SCENARIOS, rpms.get(k, rpms["stall"])) for k, c in curves.items()}
    res["aep"] = aeps
    for k, a in aeps.items():
        print("AEP", k, {s: round(v) for s, v in a.items()})

    # -------- stall torque demands
    Qc = max(r["Q"] for r in sta_cold) / Q_RATED
    Qg = max(r["Q_gust"] for r in sta_cold) / Q_RATED
    Pg = max(r["P_gust"] for r in sta_cold) / P_SHAFT
    qm30, rpm30 = max_aero_torque(PF, 30.0, OM_CAP * 1.15, RHO_COLD)
    qm35, rpm35 = max_aero_torque(PF, 35.0, OM_CAP * 1.15, RHO_COLD)
    ra25, lam_ra = runaway_rpm(PF, 25.0)
    res["stall_demands"] = dict(Q_cont_pu=Qc, Q_gust_pu=Qg, P_gust_pu=Pg,
                                Q_stop_30_pu=qm30 / Q_RATED, Q_stop_30_at_rpm=rpm30,
                                Q_stop_35_pu=qm35 / Q_RATED, runaway_rpm_25=ra25, runaway_lambda=lam_ra,
                                runaway_tip_25=ra25 * math.pi / 30 * R)
    # pitch: torque never above rated + control margin; thrust
    res["pitch_demands"] = dict(Q_max_pu=max(r["Q"] for r in pit) / Q_RATED,
                                pitch_at_25=[r for r in pit if r["V"] == 25.0][0]["pitch"])
    print(json.dumps(res["stall_demands"], indent=1))

    # -------- parked loads
    ref = broadside_ref()
    gs, Mf = parked_sweep(0.0)
    _, Mfe = parked_sweep(85.0)
    res["parked"] = dict(broadside_ref_kNm=ref / 1000, yaw=gs.tolist(),
                         fixed_kNm=(Mf / 1000).tolist(), feathered_kNm=(Mfe / 1000).tolist())
    def band(M, lo, hi):
        sel = (np.abs(gs) >= lo) & (np.abs(gs) <= hi)
        return float(M[sel].max() / 1000)
    res["parked_summary"] = dict(
        feathered_aligned_15=band(Mfe, 0, 15), feathered_any=float(Mfe.max() / 1000),
        fixed_aligned_15=band(Mf, 0, 15), fixed_yawed_75_105=band(Mf, 75, 105), fixed_any=float(Mf.max() / 1000),
        broadside=ref / 1000)
    print(json.dumps(res["parked_summary"], indent=1))

    # -------- operating thrust
    res["thrust"] = dict(pitch_max=max(r["T"] for r in pit), stall_max=max(r["T"] for r in sta),
                         stall_cold_max=max(r["T"] for r in sta_cold),
                         pitch_flap_max=max(r["Mflap"] for r in pit), stall_flap_max=max(r["Mflap"] for r in sta_cold))

    # -------- electrical braking
    w = np.linspace(0.01, 1.3, 200)
    eb = {}
    for x in (0.55, 0.35, 0.25):
        tsc, tres = elec_brake_pu(w, x)
        eb[str(x)] = dict(sc_at_rated=float(np.interp(1.0, w, tsc)), sc_peak=float(tsc.max()),
                          sc_peak_speed=float(w[int(np.argmax(tsc))]), resistor=float(1 / (2 * x)))
    res["elec_brake"] = eb

    # -------- brake stop simulation: fixed pitch at 30 m/s gust, cold air, from 1.15 x speed cap
    J = DES["J_rotor"]
    stops = {}
    for Tb_pu in (2.0, 2.5, 3.0, 3.5):
        om = OM_CAP * 1.15; t = 0.0; E = 0.0
        while om > 0.05 and t < 30:
            qa = pt(30.0, om, PF, RHO_COLD).torque
            dom = (qa - Tb_pu * Q_RATED) / J
            E += Tb_pu * Q_RATED * om * 0.01
            om += dom * 0.01; t += 0.01
            if dom >= 0 and t > 1:
                break
        stops[str(Tb_pu)] = dict(stopped=om <= 0.05, time_s=round(t, 2), energy_kJ=round(E / 1000, 1))
    res["brake_stop_30ms"] = stops
    print(stops)

    (OUT / "regulation.json").write_text(json.dumps(res, indent=1, default=float))
    figures(res, curves, V, gs, Mf, Mfe, ref, w)


def figures(res, curves, V, gs, Mf, Mfe, ref, w):
    plt.rcParams.update({"font.size": 9, "axes.grid": True, "grid.alpha": 0.3})
    # F01 power curves
    fig, ax = plt.subplots(figsize=(7, 3.6))
    for k, lab, col, ls in (("pitch", "Active pitch", C["blue"], "-"), ("stall", "Stall by speed control", C["green"], "--"),
                            ("furl_typical", "Furling (typical)", C["orange"], "-.")):
        ax.plot(V, np.array(curves[k]) / 1000, color=col, ls=ls, label=lab, lw=1.8)
    ax.set_xlabel("Wind speed at hub, m/s"); ax.set_ylabel("Shaft power, kW"); ax.set_xlim(3, 30)
    ax.set_title(f"F01 Power curves, same rotor Ø{2 * R:.1f} m"); ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(OUT / "F01-power-curves.png", dpi=160); plt.close(fig)

    # F02 stall operation: rpm and torque
    sta, sc = res["stall_curve"], res["stall_curve_cold"]
    pit = res["pitch_curve"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.6))
    a1.plot([r["V"] for r in pit], [r["rpm"] for r in pit], color=C["blue"], label="Active pitch")
    a1.plot([r["V"] for r in sta], [r["rpm"] for r in sta], color=C["green"], ls="--", label="Stall control, 1.225 kg/m³")
    a1.plot([r["V"] for r in sc], [r["rpm"] for r in sc], color=C["green"], ls=":", label="Stall control, cold 1.35")
    a1.set_xlabel("Wind, m/s"); a1.set_ylabel("Rotor speed, rpm"); a1.legend(frameon=False, fontsize=8); a1.set_title("Rotor speed")
    a2.plot([r["V"] for r in pit], [r["Q"] / Q_RATED for r in pit], color=C["blue"], label="Pitch, steady")
    a2.plot([r["V"] for r in sc], [r["Q"] / Q_RATED for r in sc], color=C["green"], ls=":", label="Stall, steady (cold)")
    a2.plot([r["V"] for r in sc], [r["Q_gust"] / Q_RATED for r in sc], color=C["red"], label="Stall, +30 % gust before control reacts")
    a2.axhline(1 / (2 * 0.55), color=C["grey"], ls="--", lw=1); a2.text(17, 1 / (2 * 0.55) - 0.09, "passive resistor, X = 0.55 pu", fontsize=7, color=C["grey"])
    a2.axhline(2.0, color=C["grey"], ls="--", lw=1); a2.text(17, 1.92, "passive resistor, X = 0.25 pu", fontsize=7, color=C["grey"])
    a2.set_xlabel("Wind, m/s"); a2.set_ylabel("Torque / rated torque"); a2.legend(frameon=False, fontsize=8, loc="center right"); a2.set_title("Generator torque needed")
    fig.suptitle("F02 Stall by speed control: the generator does the regulating"); fig.tight_layout()
    fig.savefig(OUT / "F02-stall-operation.png", dpi=160); plt.close(fig)

    # F03 parked loads vs yaw
    fig, ax = plt.subplots(figsize=(7, 3.6))
    ax.plot(gs, Mfe / 1000, color=C["blue"], label="Pitch: blades feathered (85°)")
    ax.plot(gs, Mf / 1000, color=C["green"], ls="--", label="Fixed pitch: blades at run pitch")
    ax.axhline(ref / 1000, color=C["grey"], ls=":", label="Broadside reference (IEC SLM case H style)")
    ax.axvspan(-15, 15, color=C["blue"], alpha=0.08); ax.axvspan(75, 105, color=C["green"], alpha=0.08); ax.axvspan(-105, -75, color=C["green"], alpha=0.08)
    ax.set_xlabel("Yaw error of parked rotor, deg"); ax.set_ylabel("Max blade root moment, kNm")
    ax.set_title(f"F03 Parked blade root moment at V_e50 = {V_E50:.0f} m/s (worst azimuth)"); ax.set_xlim(-180, 180)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    fig.tight_layout(); fig.savefig(OUT / "F03-parked-loads.png", dpi=160); plt.close(fig)

    # F04 electrical braking
    fig, ax = plt.subplots(figsize=(7, 3.6))
    for x, col in ((0.55, C["red"]), (0.25, C["green"])):
        tsc, tres = elec_brake_pu(w, x)
        ax.plot(w, tsc, color=col, ls="--", label=f"Short circuit, X = {x} pu")
        ax.plot(w, tres, color=col, label=f"Matched resistor, X = {x} pu")
    sd = res["stall_demands"]
    ax.axhline(sd["Q_stop_30_pu"], color="k", lw=1); ax.text(0.02, sd["Q_stop_30_pu"] + 0.06, "aero torque to overcome, fixed pitch, 30 m/s, cold air", fontsize=7)
    ax.set_xlabel("Rotor speed / rated speed"); ax.set_ylabel("Braking torque / rated torque"); ax.set_ylim(0, 3.5)
    ax.set_title("F04 What electrical braking can do"); ax.legend(frameon=False, fontsize=8, loc="upper right")
    fig.tight_layout(); fig.savefig(OUT / "F04-electrical-braking.png", dpi=160); plt.close(fig)


if __name__ == "__main__":
    main()
