"""M8 at 8 m hub height: speed-loop retune check (doc 37 §2).

Run:  python3 ctrl8_m8.py   (after dlc8_m8.py; ~10 min on 4 cores) -> results/ctrl8_m8.json

The 8 m load run (dlc8_m8.py, controller tuned at 18 m: pitch speed loop 4 rad/s) tripped on overspeed in 24 of
the DLC 1.1/1.3 runs and reached 219.6 rpm once (DLC 1.3, 24 m/s, seed 100). This re-runs the worst turbulent
cases with faster pitch speed loops (natural frequency 4, 6, 8 rad/s; f1 of the stiff tower is 19 rad/s) and
reports trips and peak speed, so the 8 m controller setting can be chosen before the full rerun.
"""
from __future__ import annotations
import json, multiprocessing as mp, sys
import common as C
import dlc8_m8 as D8  # noqa: E402  (sets the 8 m wind, tower and TB_KW)

D = D8.D
PICK = [("1.3", 24, 100), ("1.3", 24, 101), ("1.3", 18, 101), ("1.1", 26, 0), ("1.1", 22, 0), ("1.1", 20, 1), ("1.1", 16, 2), ("1.1", 12, 0)]
WN = (4.0, 6.0, 8.0)
# second pass: with any loop speed the 118 % trip (154.6 rpm) still fires in every case, so the trip threshold and
# the normal pitch rate are varied at 6 rad/s (the design overspeed 184 rpm stays the limit for the peak)
VARIANTS = {"wn6_trip165": dict(pitch_wn=6.0, rpm_trip=165.0), "wn6_trip165_rate20": dict(pitch_wn=6.0, rpm_trip=165.0, pitch_rate_normal=20.0),
            "wn6_trip170_rate20": dict(pitch_wn=6.0, rpm_trip=170.0, pitch_rate_normal=20.0)}


def job(a):
    wn, cs = a
    D.RD.TB_KW = dict(D.RD.TB_KW, **(VARIANTS[wn] if isinstance(wn, str) else dict(pitch_wn=wn, rpm_trip=C.RPM_TRIP, pitch_rate_normal=15.0)))
    r = D.run_case(cs)
    return dict(wn=wn, dlc=cs["dlc"], V=cs["V"], seed=cs["seed"], rpm_max=round(r["max"]["rpm"], 1), trip=r["trip"],
                thrust_max=round(r["max"]["thrust"]), Mtilt_max=round(r["max"]["Mtilt"]), P_mean=round(r["mean"].get("P", 0.0)))


def main():
    cases = [c for c in D.RD.build_cases() if (c["dlc"], c["V"], c.get("seed")) in PICK]
    old = json.loads((C.OUT / "ctrl8_m8.json").read_text())["runs"] if (C.OUT / "ctrl8_m8.json").exists() else []
    done = {r["wn"] for r in old}
    keys = [k for k in list(WN) + list(VARIANTS) if k not in done]
    jobs = [(wn, c) for wn in keys for c in cases]
    with mp.Pool(4) as pool:
        res = old + pool.map(job, jobs, chunksize=1)
    summ = {}
    for wn in list(WN) + list(VARIANTS):
        rs = [r for r in res if r["wn"] == wn]
        summ[wn if isinstance(wn, str) else f"wn_{wn:.0f}"] = dict(P_mean_sum_kW=round(sum(r["P_mean"] for r in rs) / 1e3, 1), trips=sum(r["trip"] for r in rs), rpm_max=max(r["rpm_max"] for r in rs),
                                     thrust_max=max(r["thrust_max"] for r in rs), Mtilt_max=max(r["Mtilt_max"] for r in rs))
    out = dict(cases=PICK, summary=summ, runs=res)
    (C.OUT / "ctrl8_m8.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
