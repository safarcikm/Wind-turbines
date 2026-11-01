"""Tower frequency placement: Campbell diagram and the energy cost of each option.

Run:  python3 frequency.py    (~2 min; writes results/frequency.json, results/campbell.png)

The rotor runs from 40 to 178 rpm, so the 1P band (0.67-2.97 Hz) and the 3P
band (2.0-8.9 Hz) overlap and no tower frequency is clear of both with the
+-10 % margin of R6.2. Options evaluated:
  A  stiff tower above 1.1 x 3P_max                   (frequency check only)
  B  soft tower below 1P_min / 1.1                    (frequency check only)
  C  raise the minimum rotor speed so a window opens above 1P_max
  D  keep 40 rpm minimum, tower above 1P_max, and a speed exclusion zone
     around the 3P crossing (the controller jumps through it)
  E  soft-stiff tower between 1.1 x 1P_min and 3P_min / 1.1 (0.73-1.82 Hz), with a
     speed exclusion zone around the 1P crossing. Chosen in doc 09: tower.py shows
     a freestanding (or guyed) tilt-up tower cannot reach 3.3 Hz.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "rotor"))
import study  # noqa: E402
from bem import Blade, CLEAN, solve  # noqa: E402

OUT = HERE / "results"
OUT.mkdir(exist_ok=True)
RPM_MIN, RPM_RATED = 40.0, 178.0
MARGIN = 0.10


def windows():
    p1 = (RPM_MIN / 60, RPM_RATED / 60)
    p3 = (3 * RPM_MIN / 60, 3 * RPM_RATED / 60)
    return dict(
        band_1P_Hz=[round(p1[0], 3), round(p1[1], 3)],
        band_3P_Hz=[round(p3[0], 3), round(p3[1], 3)],
        A_stiff_min_Hz=round(p3[1] * (1 + MARGIN), 2),
        B_soft_max_Hz=round(p1[0] / (1 + MARGIN), 2),
        C_lower_bound_Hz=round(p1[1] * (1 + MARGIN), 2),
    )


def curve(blade, rpm_min=0.0, excl=None):
    """Power curve with a minimum speed and/or an exclusion band (rpm_lo, rpm_hi)."""
    om_max = study.TIP_SPEED_MAX / blade.R
    rows = []
    for V in study.VS:
        res, om, p = study.best_point(blade, V, om_max, CLEAN)
        rpm = om * 60 / (2 * math.pi)
        cands = []
        if rpm < rpm_min:
            cands = [rpm_min]
        elif excl and excl[0] < rpm < excl[1]:
            cands = [excl[0], excl[1]]
        if cands:
            best = None
            for rr in cands:
                o = rr * 2 * math.pi / 60
                for pp in np.arange(study.PITCH_MIN, 6.01, 0.5):
                    r_ = solve(blade, V, o, pp, study.RHO, CLEAN)
                    if best is None or r_.power > best[0].power:
                        best = (r_, o, pp)
            res, om, p = best
        target = study.P_AERO_RATED
        if V > study.V_STORM_START:
            target = study.P_AERO_RATED * (1 - (1 - study.STORM_FRAC) * (V - study.V_STORM_START)
                                           / (study.V_CUTOUT - study.V_STORM_START))
        if res.power > target:
            res, p = study.pitch_for_power(blade, V, om_max, target, CLEAN)
            om = om_max
        pe = study.elec(res.power) if V <= study.V_CUTOUT else 0.0
        rows.append(dict(V=float(V), rpm=om * 60 / (2 * math.pi), P_elec=pe))
    return rows


def main():
    w = windows()
    blade = Blade(R=3.75, tsr_design=study.TSR_DESIGN, cl_design=study.CL_DESIGN)
    vaves = [5.0, 6.0, 7.0, 8.0, 10.0]
    base = curve(blade)
    aep0 = {v: study.rayleigh_aep(base, v) for v in vaves}
    res = dict(windows=w, options={})
    # Option C: minimum speed such that 3P_min / 1.1 is above the tower target
    for rpm_min in (70.0, 75.0, 80.0, 85.0):
        hi = 3 * rpm_min / 60 / (1 + MARGIN)
        rows = curve(blade, rpm_min=rpm_min)
        res["options"][f"C_rpm_min_{int(rpm_min)}"] = dict(
            window_Hz=[w["C_lower_bound_Hz"], round(hi, 2)] if hi > w["C_lower_bound_Hz"] else None,
            aep_loss_pct={str(v): round(100 * (1 - study.rayleigh_aep(rows, v) / aep0[v]), 2) for v in vaves})
    # Option D: tower f_t, exclusion zone +-10 % around the 3P crossing
    for ft in (3.3, 3.5, 3.8, 4.2):
        n3 = ft / 3 * 60
        excl = (n3 / (1 + MARGIN), n3 * (1 + MARGIN))
        rows = curve(blade, excl=excl)
        res["options"][f"D_tower_{ft}Hz"] = dict(
            exclusion_rpm=[round(excl[0], 1), round(excl[1], 1)],
            exclusion_wind_ms=[round(excl[0] * 2 * math.pi / 60 * 3.75 / 6.5, 1),
                               round(excl[1] * 2 * math.pi / 60 * 3.75 / 6.5, 1)],
            margin_above_1P_pct=round(100 * (ft / (RPM_RATED / 60) - 1), 1),
            aep_loss_pct={str(v): round(100 * (1 - study.rayleigh_aep(rows, v) / aep0[v]), 2) for v in vaves})
    # Option E: soft-stiff towers of doc 09 (18 m: 1.21 Hz, 24 m: 0.87 Hz), zone around the 1P crossing
    for ft in (0.87, 1.21, 1.5, 1.78):
        n1 = ft * 60
        excl = (n1 / (1 + MARGIN), n1 * (1 + MARGIN))
        rows = curve(blade, excl=excl)
        res["options"][f"E_tower_{ft}Hz"] = dict(
            exclusion_rpm=[round(excl[0], 1), round(excl[1], 1)],
            exclusion_wind_ms=[round(excl[0] * 2 * math.pi / 60 * 3.75 / 6.5, 1),
                               round(excl[1] * 2 * math.pi / 60 * 3.75 / 6.5, 1)],
            margin_below_3P_min_pct=round(100 * (1 - ft / (3 * RPM_MIN / 60)), 1),
            aep_loss_pct={str(v): round(100 * (1 - study.rayleigh_aep(rows, v) / aep0[v]), 2) for v in vaves})
    res["aep_baseline_kWh"] = {str(v): round(a) for v, a in aep0.items()}
    (OUT / "frequency.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=1))

    # Campbell diagram
    n = np.linspace(0, 200, 200)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(n, n / 60, "C0", label="1P")
    ax.plot(n, 3 * n / 60, "C1", label="3P")
    ax.fill_between(n, n / 60 * 0.9, n / 60 * 1.1, color="C0", alpha=0.15)
    ax.fill_between(n, 3 * n / 60 * 0.9, 3 * n / 60 * 1.1, color="C1", alpha=0.15)
    ax.axvspan(RPM_MIN, RPM_RATED, color="grey", alpha=0.08, label="operating range 40-178 rpm")
    ax.axhspan(0.73, 1.82, color="C2", alpha=0.15, label="soft-stiff window 0.73-1.82 Hz (option E)")
    ax.axhline(1.21, color="C2", lw=1.5, label="18 m tower, 1.21 Hz")
    ax.axhline(0.87, color="C2", lw=1.5, ls="--", label="24 m tower, 0.87 Hz")
    ax.axvspan(1.21 * 60 / 1.1, 1.21 * 60 * 1.1, color="C3", alpha=0.2, label="18 m exclusion zone 66-80 rpm")
    ax.axvspan(0.87 * 60 / 1.1, 0.87 * 60 * 1.1, color="C3", alpha=0.1, label="24 m exclusion zone 47-57 rpm")
    ax.axhline(3.26, color="k", ls=":", lw=1, label="stiff tower would need > 3.3 Hz (not reachable)")
    ax.set_xlim(0, 200); ax.set_ylim(0, 10)
    ax.set_xlabel("Rotor speed [rpm]"); ax.set_ylabel("Frequency [Hz]")
    ax.set_title("Campbell diagram: rotor excitation vs tower first mode")
    ax.legend(loc="upper left", fontsize=8); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(OUT / "campbell.png", dpi=110)


if __name__ == "__main__":
    main()
