"""Rotor concept study: compare rotor diameters and design tip speed ratios.

Run:  python3 study.py
Writes results/*.csv, results/*.png and results/summary.json.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from bem import Blade, CLEAN, ROUGH, solve

OUT = Path(__file__).parent / "results"
OUT.mkdir(exist_ok=True)

RHO = 1.225
P_RATED_E = 12_000.0          # W at power module output
P_FIXED = 120.0               # W fixed losses (controller, heaters idle, core loss)
P_AERO_RATED = 13_600.0       # W rotor shaft power at rated
ETA_PROP = (P_RATED_E + P_FIXED) / P_AERO_RATED   # proportional efficiency gen x PE
TIP_SPEED_MAX = 70.0          # m/s, erosion and noise limit (ash, rain)
V_STORM_START, V_CUTOUT, STORM_FRAC = 25.0, 30.0, 0.40
AVAILABILITY = 0.97
PITCH_MIN = -2.0              # deg, fine pitch limit
TSR_DESIGN = 6.5
CL_DESIGN = 1.0

DIAMETERS = [7.0, 7.5, 8.0]
VAVES = [5.0, 6.0, 7.0, 8.0, 10.0]
VS = np.arange(2.0, 32.01, 0.5)

# Parked extreme (design basis): V_e50 3 s gust, cold dense air
V_E50, RHO_COLD, CD_BROADSIDE = 77.0, 1.35, 1.8


def elec(p_aero: float) -> float:
    return max(ETA_PROP * p_aero - P_FIXED, 0.0)


def best_point(blade: Blade, V: float, omega_max: float, polar, _cache={}):
    """Max-power operating point below rated (variable speed, capped rpm).

    Cp(tsr, pitch) does not depend on V in this model (no Reynolds effect), so
    the optimum is found once per blade and reused; the rpm cap is handled by
    a pitch search at the capped tip speed ratio.
    """
    key = (id(blade), polar.name)
    if key not in _cache:
        best = None
        for tsr in np.arange(4.0, 10.01, 0.25):
            for p in np.arange(PITCH_MIN, 3.01, 0.5):
                cp = solve(blade, 8.0, tsr * 8.0 / blade.R, p, RHO, polar).cp
                if best is None or cp > best[0]:
                    best = (cp, tsr, p)
        _cache[key] = best
    _, tsr_opt, p_opt = _cache[key]
    om = tsr_opt * V / blade.R
    if om <= omega_max:
        return solve(blade, V, om, p_opt, RHO, polar), om, p_opt
    om = omega_max
    best = None
    for p in np.arange(PITCH_MIN, 6.01, 0.5):
        res = solve(blade, V, om, p, RHO, polar)
        if best is None or res.power > best[0].power:
            best = (res, om, p)
    return best


def pitch_for_power(blade: Blade, V: float, omega: float, target: float, polar):
    """Bisection on pitch (towards feather) to hold aerodynamic power."""
    lo, hi = 0.0, 45.0
    for _ in range(22):
        mid = 0.5 * (lo + hi)
        if solve(blade, V, omega, mid, RHO, polar).power > target:
            lo = mid
        else:
            hi = mid
    p = 0.5 * (lo + hi)
    return solve(blade, V, omega, p, RHO, polar), p


def power_curve(D: float, polar):
    blade = Blade(R=D / 2, tsr_design=TSR_DESIGN, cl_design=CL_DESIGN)
    om_max = TIP_SPEED_MAX / blade.R
    rows = []
    for V in VS:
        res, om, p = best_point(blade, V, om_max, polar)
        target = P_AERO_RATED
        if V > V_STORM_START:
            target = P_AERO_RATED * (1 - (1 - STORM_FRAC) * (V - V_STORM_START) / (V_CUTOUT - V_STORM_START))
        if res.power > target:
            res, p = pitch_for_power(blade, V, om_max, target, polar)
            om = om_max
        pe = elec(res.power) if V <= V_CUTOUT else 0.0
        rows.append(dict(V=V, rpm=om * 60 / (2 * math.pi), pitch=p, P_aero=res.power, P_elec=pe,
                         Cp=res.cp, Ct=res.ct, thrust=res.thrust, torque=res.torque,
                         M_flap=res.root_flap_moment))
    return blade, rows


def rayleigh_aep(rows, vave: float, hard_cutout_25: bool = False) -> float:
    V = np.array([r["V"] for r in rows])
    P = np.array([r["P_elec"] for r in rows])
    if hard_cutout_25:
        P = np.where(V > 25.0, 0.0, P)
    dv = V[1] - V[0]
    k, c = 2.0, vave / math.gamma(1.5)
    f = (k / c) * (V / c) ** (k - 1) * np.exp(-(V / c) ** k)
    return float(np.sum(P * f * dv) * 8760 * AVAILABILITY / 1000)  # kWh


def parked_loads(blade: Blade):
    q = 0.5 * RHO_COLD * V_E50 ** 2
    dF = q * CD_BROADSIDE * blade.chord * blade.dr
    F = float(dF.sum())
    M = float(np.sum(dF * (blade.r - blade.r_hub)))
    return F, M


def main():
    summary = {"assumptions": dict(rho=RHO, P_rated_elec=P_RATED_E, P_aero_rated=P_AERO_RATED,
                                   eta_prop=round(ETA_PROP, 3), P_fixed=P_FIXED,
                                   tip_speed_max=TIP_SPEED_MAX, tsr_design=TSR_DESIGN,
                                   cl_design=CL_DESIGN, storm=[V_STORM_START, V_CUTOUT, STORM_FRAC],
                                   availability=AVAILABILITY, V_e50=V_E50, rho_cold=RHO_COLD,
                                   cd_broadside=CD_BROADSIDE),
               "tsr_sweep": [], "rotors": []}

    # 1. Design TSR sweep at R = 3.75 m
    for tsr in [5.5, 6.0, 6.5, 7.0, 7.5, 8.0]:
        b = Blade(R=3.75, tsr_design=tsr, cl_design=CL_DESIGN)
        entry = dict(tsr=tsr, c_max=round(b.c_max, 3), blade_area=round(b.solidity_area(), 3))
        for pol in (CLEAN, ROUGH):
            cp = max(solve(b, 8.0, l * 8.0 / b.R, p, RHO, pol).cp
                     for l in np.arange(4, 11, 0.25) for p in np.arange(-2, 3.1, 0.5))
            entry[f"cp_{pol.name}"] = round(cp, 3)
        entry["tip_speed_at_11ms"] = round(tsr * 11.0, 1)
        summary["tsr_sweep"].append(entry)

    # 2. Diameter comparison
    fig, ax = plt.subplots(2, 2, figsize=(11, 8))
    for D in DIAMETERS:
        for pol in (CLEAN, ROUGH):
            blade, rows = power_curve(D, pol)
            tag = f"D{D:.1f}_{pol.name}"
            with open(OUT / f"power_curve_{tag}.csv", "w") as fh:
                fh.write(",".join(rows[0].keys()) + "\n")
                for r in rows:
                    fh.write(",".join(f"{v:.4g}" for v in r.values()) + "\n")
            rated = next((r["V"] for r in rows if r["P_elec"] >= P_RATED_E - 1), None)
            rated_row = next(r for r in rows if r["V"] == rated) if rated else rows[-1]
            cut_in = next(r["V"] for r in rows if r["P_elec"] > 0)
            Fp, Mp = parked_loads(blade)
            op = [r for r in rows if r["V"] <= V_CUTOUT]
            entry = dict(
                D=D, polar=pol.name, rated_wind=rated, cut_in=cut_in,
                rated_rpm=round(rated_row["rpm"], 1), rated_torque_Nm=round(rated_row["torque"]),
                max_steady_thrust_N=round(max(r["thrust"] for r in op)),
                max_steady_flap_Nm=round(max(r["M_flap"] for r in op)),
                pitch_at_25=round(next(r["pitch"] for r in rows if r["V"] == 25.0), 1),
                pitch_at_30=round(next(r["pitch"] for r in rows if r["V"] == 30.0), 1),
                c_max=round(blade.c_max, 3), c_tip=round(float(blade.chord[-1]), 3),
                blade_area=round(blade.solidity_area(), 3),
                twist_root=round(float(blade.twist[blade.r / blade.R >= 0.2][0]), 1),
                parked_broadside_force_N=round(Fp), parked_broadside_root_moment_Nm=round(Mp),
                aep_kWh={str(v): round(rayleigh_aep(rows, v)) for v in VAVES},
                aep_hard_cutout25_kWh={str(v): round(rayleigh_aep(rows, v, True)) for v in VAVES},
            )
            summary["rotors"].append(entry)
            if pol is ROUGH:
                V = [r["V"] for r in rows]
                ax[0, 0].plot(V, [r["P_elec"] / 1000 for r in rows], label=f"D = {D} m")
                ax[0, 1].plot(V, [r["Cp"] for r in rows], label=f"D = {D} m")
                ax[1, 0].plot(V, [r["thrust"] / 1000 for r in rows], label=f"D = {D} m")
                ax[1, 1].plot(V, [r["pitch"] for r in rows], label=f"D = {D} m")
    for a_, t, yl in [(ax[0, 0], "Electrical power (rough blades)", "kW"),
                      (ax[0, 1], "Power coefficient Cp", "-"),
                      (ax[1, 0], "Rotor thrust (steady)", "kN"),
                      (ax[1, 1], "Pitch angle", "deg")]:
        a_.set_title(t); a_.set_xlabel("Hub wind speed [m/s]"); a_.set_ylabel(yl)
        a_.grid(alpha=0.3); a_.legend()
    fig.tight_layout(); fig.savefig(OUT / "power_curves.png", dpi=120)

    # 3. Blade geometry plot for recommended rotor
    b = Blade(R=3.75, tsr_design=TSR_DESIGN, cl_design=CL_DESIGN)
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].plot(b.r, b.chord, label="Chosen (linear taper)")
    ax[0].plot(b.r, b.chord_opt, "--", label="Schmitz optimum")
    ax[0].set_ylim(0, 0.8); ax[0].set_xlabel("Radius [m]"); ax[0].set_ylabel("Chord [m]")
    ax[0].legend(); ax[0].grid(alpha=0.3); ax[0].set_title("Chord, D = 7.5 m")
    ax[1].plot(b.r, b.twist); ax[1].set_xlabel("Radius [m]"); ax[1].set_ylabel("Twist [deg]")
    ax[1].grid(alpha=0.3); ax[1].set_title("Twist (tip = 0)")
    fig.tight_layout(); fig.savefig(OUT / "blade_geometry_D7.5.png", dpi=120)
    with open(OUT / "blade_geometry_D7.5.csv", "w") as fh:
        fh.write("r_m,r_over_R,chord_m,twist_deg\n")
        for r_, c_, t_ in zip(b.r, b.chord, b.twist):
            fh.write(f"{r_:.3f},{r_ / b.R:.3f},{c_:.4f},{t_:.2f}\n")

    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
