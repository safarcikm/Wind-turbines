"""Pitch and yaw duty from the aeroelastic simulator (doc 13).

Runs normal-turbulence production cases with the final turbine configuration
(doc 11 controller, doc 09 18 m tower, doc 10 blade) and records what the
pitch bearing, pitch drive and yaw drive see:

- pitch travel, reversals and time at the fine-pitch stop,
- pitch rate distribution,
- blade root moment and centrifugal force while the blade is moving
  (bearing friction torque and bearing fatigue are weighted by motion),
- hub yaw moment percentiles (yaw drive sizing),
- blade root resultant moment DEL with m = 3 (ball bearing raceway) and
  m = 5 (ductile iron hub).

Run:  python3 run_pitch_duty.py   (about 15 minutes on 4 cores; writes results/pitch_duty.json)
"""
from __future__ import annotations

import json
import math
import multiprocessing as mp
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "loads"))
from sim import Turbine, Scenario, simulate, rainflow  # noqa: E402
from wind import turbulent_field, sigma_ntm, V_AVE  # noqa: E402

TB_KW = dict(const_power=True, storm_control=True, f_flap=13.2, m_blade=20.5, f_tower=1.21,
             m_tower_modal=305.0, excl_rpm=(66.5, 80.5), pitch_err=(0.3, 0.0, -0.3))
WINDS = list(range(4, 31, 2))
SEEDS = (0, 1)
T_RUN = 600.0
SKIP = 30.0
OUT = HERE / "results"
OUT.mkdir(exist_ok=True)


def run(case):
    V, seed = case
    tb = Turbine(**TB_KW)
    field = turbulent_field(V, sigma_ntm(V), T=T_RUN, dt=0.05, seed=900 + seed)
    r = simulate(tb, Scenario(name="duty", T=T_RUN, field=field))
    t = r["t"]
    k0 = int(SKIP / (t[1] - t[0]))
    dt = float(t[1] - t[0])
    th = r["pitch1"][k0:]                     # blade 1 has no misalignment offset
    rpm = r["rpm"][k0:]
    Mres = r["Mres0"][k0:]
    Myaw = r["Myaw"][k0:]
    rate = np.abs(np.gradient(th, dt))
    travel = float(np.sum(np.abs(np.diff(th))))
    # reversals with 0.05 deg hysteresis
    rev, last, d = 0, th[0], 0
    for x in th[1:]:
        if d >= 0 and x < last - 0.05:
            rev += d > 0; d = -1; last = x
        elif d <= 0 and x > last + 0.05:
            rev += d < 0; d = 1; last = x
        elif (d >= 0 and x > last) or (d <= 0 and x < last):
            last = x
    dur = float(t[-1] - t[k0])
    moving = rate > 0.2
    om = rpm * 2 * math.pi / 60
    Fc = tb.m_blade * om ** 2 * 1.55          # centrifugal force at the root, N (blade CoG 1.55 m)
    dth = np.abs(np.diff(th, prepend=th[0]))
    rg, ct = rainflow(Mres)
    return dict(
        V=V, seed=seed, duration=dur,
        travel_deg=travel, reversals=rev,
        frac_fine=float(np.mean(th < 0.5)),
        frac_moving=float(np.mean(moving)),
        rate_p99=float(np.percentile(rate, 99)), rate_max=float(rate.max()),
        Mres_mean=float(Mres.mean()), Mres_max=float(Mres.max()),
        # motion-weighted sums for bearing life (P^3 weighted by angle travelled)
        sum_dth=float(dth.sum()),
        sum_dth_M3=float(np.sum(dth * Mres ** 3)),
        sum_dth_F3=float(np.sum(dth * Fc ** 3)),
        sum_dth_M=float(np.sum(dth * Mres)),
        sum_dth_F=float(np.sum(dth * Fc)),
        dmg_M3=float(np.sum(ct * rg ** 3)), dmg_M5=float(np.sum(ct * rg ** 5)),
        Myaw_p50=float(np.percentile(np.abs(Myaw), 50)),
        Myaw_p95=float(np.percentile(np.abs(Myaw), 95)),
        Myaw_mean=float(np.mean(Myaw)),
        Myaw_max=float(np.max(np.abs(Myaw))),
        P_mean=float(np.mean(r["P"][k0:])),
    )


def lifetime(results):
    c = V_AVE / math.gamma(1.5)
    life_s = 20 * 8760 * 3600 * 0.97
    dV = 2.0
    out = dict(travel_deg=0.0, reversals=0.0, sum_dth=0.0, sum_dth_M3=0.0, sum_dth_F3=0.0,
               sum_dth_M=0.0, sum_dth_F=0.0, dmg_M3=0.0, dmg_M5=0.0, t_fine_s=0.0, t_prod_s=0.0)
    per_V = {}
    for V in WINDS:
        rs = [r for r in results if r["V"] == V]
        p = math.exp(-((V - dV / 2) / c) ** 2) - math.exp(-((V + dV / 2) / c) ** 2)
        T = p * life_s
        per = {k: float(np.mean([r[k] / r["duration"] for r in rs])) for k in
               ("travel_deg", "reversals", "sum_dth", "sum_dth_M3", "sum_dth_F3", "sum_dth_M", "sum_dth_F",
                "dmg_M3", "dmg_M5")}
        for k, v in per.items():
            out[k] += v * T
        ff = float(np.mean([r["frac_fine"] for r in rs]))
        out["t_fine_s"] += ff * T
        out["t_prod_s"] += T
        per_V[V] = dict(prob=p, travel_deg_per_h=per["travel_deg"] * 3600, reversals_per_h=per["reversals"] * 3600,
                        frac_fine=ff, rate_p99=max(r["rate_p99"] for r in rs),
                        rate_max=max(r["rate_max"] for r in rs),
                        Myaw_p95=max(r["Myaw_p95"] for r in rs), Myaw_mean=float(np.mean([r["Myaw_mean"] for r in rs])),
                        Mres_max=max(r["Mres_max"] for r in rs))
    s = out["sum_dth"]
    life = dict(
        pitch_travel_revs_20y=out["travel_deg"] / 360,
        pitch_reversals_20y=out["reversals"],
        frac_time_fine_in_production=out["t_fine_s"] / out["t_prod_s"],
        M_eq_motion_weighted_kNm=(out["sum_dth_M3"] / s) ** (1 / 3) / 1e3,
        F_eq_motion_weighted_kN=(out["sum_dth_F3"] / s) ** (1 / 3) / 1e3,
        M_mean_motion_weighted_kNm=out["sum_dth_M"] / s / 1e3,
        F_mean_motion_weighted_kN=out["sum_dth_F"] / s / 1e3,
        Mres_DEL_m3_1e7_kNm=(out["dmg_M3"] / 1e7) ** (1 / 3) / 1e3,
        Mres_DEL_m5_1e7_kNm=(out["dmg_M5"] / 1e7) ** (1 / 5) / 1e3,
    )
    return life, per_V


def main():
    cases = [(V, s) for V in WINDS for s in SEEDS]
    with mp.Pool(4) as pool:
        results = pool.map(run, cases, chunksize=1)
    life, per_V = lifetime(results)
    summary = dict(config=TB_KW, winds=WINDS, seeds=list(SEEDS), T_run=T_RUN, lifetime_20y=life, per_wind=per_V)
    (OUT / "pitch_duty.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
