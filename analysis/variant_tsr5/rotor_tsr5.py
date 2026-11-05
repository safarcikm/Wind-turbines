"""Slow-running variant V5: rotor, power curve and annual energy vs the current D 7.5 m rotor.

Run:  python3 rotor_tsr5.py      (~1 min, writes results/rotor_tsr5.json, power_curves.csv, plots)

Variant: 3 blades, design TSR 5, rated speed 110 rpm, same 13.6 kW shaft / 12 kW electric rating.
Uses the doc 03 BEM model (analysis/rotor/bem.py, study.py) unchanged, only the rotor
radius, design TSR and tip-speed cap differ. Same polars, same storm ramp, same losses.
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "rotor"))
import study  # noqa: E402
from bem import Blade, CLEAN, ROUGH, solve  # noqa: E402

OUT = HERE / "results"; OUT.mkdir(exist_ok=True)
RPM_RATED_V5 = 110.0
TSR_V5 = 5.0
R_V5 = 4.15                 # Ø8.3 m


def find_radius(tsr, rpm, polar=ROUGH):
    """Radius at which the rotor reaches 13.6 kW shaft power exactly at the speed cap (rated point
    where optimum-TSR operation meets the rpm limit), i.e. rated wind = rated rpm * R / tsr_opt."""
    lo, hi = 3.6, 5.0
    for _ in range(20):
        R = 0.5 * (lo + hi)
        b = Blade(R=R, tsr_design=tsr, cl_design=study.CL_DESIGN)
        cp, l_opt, p = max((solve(b, 8.0, l * 8.0 / R, p, study.RHO, polar).cp, l, p)
                           for l in np.arange(3.5, 7.01, 0.125) for p in np.arange(-2, 3.1, 0.5))
        om = rpm * 2 * math.pi / 60
        V = om * R / l_opt
        P = 0.5 * study.RHO * math.pi * R ** 2 * V ** 3 * cp
        if P < study.P_AERO_RATED:
            lo = R
        else:
            hi = R
    return R, cp, l_opt, V


def curve(R, tsr, tip_cap, polar):
    study.TSR_DESIGN = tsr
    study.TIP_SPEED_MAX = tip_cap
    study.best_point.__defaults__[0].clear()
    blade, rows = study.power_curve(2 * R, polar)
    return blade, rows


def summarise(blade, rows):
    rated = next((r["V"] for r in rows if r["P_elec"] >= study.P_RATED_E - 1), None)
    rr = next(r for r in rows if r["V"] == rated)
    op = [r for r in rows if r["V"] <= study.V_CUTOUT]
    Fp, Mp = study.parked_loads(blade)
    return dict(R=round(blade.R, 3), D=round(2 * blade.R, 2), rated_wind=rated,
                cut_in=next(r["V"] for r in rows if r["P_elec"] > 0),
                rated_rpm=round(rr["rpm"], 1), tip_speed=round(rr["rpm"] * math.pi / 30 * blade.R, 1),
                rated_torque_Nm=round(rr["torque"]),
                max_steady_thrust_N=round(max(r["thrust"] for r in op)),
                thrust_at_rated_N=round(rr["thrust"]),
                max_steady_flap_Nm=round(max(r["M_flap"] for r in op)),
                cp_max=round(max(r["Cp"] for r in rows), 3),
                c_max=round(blade.c_max, 3), c_tip=round(float(blade.chord[-1]), 3),
                c_root=round(blade.c_root, 3), blade_area=round(blade.solidity_area(), 3),
                solidity=round(3 * blade.solidity_area() / (math.pi * blade.R ** 2), 4),
                parked_broadside_force_N=round(Fp), parked_broadside_root_moment_Nm=round(Mp),
                pitch_at_25=round(next(r["pitch"] for r in rows if r["V"] == 25.0), 1),
                aep_kWh={str(v): round(study.rayleigh_aep(rows, v)) for v in study.VAVES})


def main():
    # Ø8.3 m as proposed in the viewer thread. find_radius() (rated exactly at the speed cap with
    # rough blades) gives R 4.38 m; Ø8.3 keeps loads lower and reaches rated 0.4 m/s later.
    R5 = R_V5
    tip_cap = RPM_RATED_V5 * math.pi / 30 * R5
    out = dict(R=R5, tip_cap=round(tip_cap, 1), knee_radius_note="R 4.38 m would reach rated exactly at the 110 rpm knee (rough)", polars={})
    fig, ax = plt.subplots(2, 2, figsize=(11, 8))
    with open(OUT / "power_curves.csv", "w") as fh:
        fh.write("variant,polar,V,rpm,pitch,P_aero,P_elec,Cp,Ct,thrust,torque,M_flap\n")
        for pol in (CLEAN, ROUGH):
            res = {}
            for name, R, tsr, cap in (("current_D7.5_TSR6.5", 3.75, 6.5, 70.0), ("V5_TSR5_110rpm", R5, TSR_V5, tip_cap)):
                b, rows = curve(R, tsr, cap, pol)
                res[name] = summarise(b, rows)
                for r in rows:
                    fh.write(f"{name},{pol.name}," + ",".join(f"{v:.4g}" for v in r.values()) + "\n")
                if pol is ROUGH:
                    V = [r["V"] for r in rows]
                    ax[0, 0].plot(V, [r["P_elec"] / 1e3 for r in rows], label=name)
                    ax[0, 1].plot(V, [r["rpm"] for r in rows], label=name)
                    ax[1, 0].plot(V, [r["thrust"] / 1e3 for r in rows], label=name)
                    ax[1, 1].plot(V, [r["torque"] / 1e3 for r in rows], label=name)
                if pol is CLEAN and name.startswith("V5"):
                    with open(OUT / "blade_geometry_V5.csv", "w") as g:
                        g.write("r_m,r_over_R,chord_m,twist_deg\n")
                        for r_, c_, t_ in zip(b.r, b.chord, b.twist):
                            g.write(f"{r_:.3f},{r_ / b.R:.3f},{c_:.4f},{t_:.2f}\n")
            a, v = res["current_D7.5_TSR6.5"]["aep_kWh"], res["V5_TSR5_110rpm"]["aep_kWh"]
            res["aep_gain_pct"] = {k: round(100 * (v[k] / a[k] - 1), 1) for k in a}
            out["polars"][pol.name] = res
    for a_, t, yl in [(ax[0, 0], "Electrical power (rough blades)", "kW"), (ax[0, 1], "Rotor speed", "rpm"),
                      (ax[1, 0], "Steady rotor thrust", "kN"), (ax[1, 1], "Rotor torque", "kNm")]:
        a_.set_title(t); a_.set_xlabel("Hub wind speed [m/s]"); a_.set_ylabel(yl); a_.grid(alpha=0.3); a_.legend()
    fig.tight_layout(); fig.savefig(OUT / "power_curves_V5.png", dpi=110)
    (OUT / "rotor_tsr5.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
