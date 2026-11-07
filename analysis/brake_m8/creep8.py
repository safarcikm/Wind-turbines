"""Doc 40: storm creep of a parked M8 rotor whose brake is smaller than the peak aero torque.

Run: python3 creep8.py  (~2 min) -> results/creep8.json
All 36 parked cases of doc 37 (DLC 6.x V_ref all yaw/azimuth, DLC 7.1 one blade stuck at fine pitch) are rerun
with the rotor locked to record the aerodynamic torque time series. Creep with a brake of torque Qb is then
integrated offline: J dw/dt = Q_aero - Qb*sign (slip only while |Q_aero| > Qb), no aero damping from the
rotation and no generator/K1 torque (both would reduce the creep), so the numbers are upper bounds.
"""
import json, math, sys, multiprocessing as mp
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "variant_m8"))
sys.argv = [sys.argv[0]]
import dlc8_m8  # noqa
import dlc_m8 as D
import numpy as np
import sim

J = D.RD.TB_KW["J_rotor"]
BRAKES = (3600.0, 4800.0, 6000.0, 7200.0, 9600.0, 14400.0)
FACT = 1.35   # design load factor on the aero torque (doc 35/37: 10.6 char -> 14.3 design)

def run(cs):
    t = sim.Turbine(**D.RD.TB_KW)
    f = D.RD.turbulent_field(cs["V"], 0.11 * cs["V"], T=cs["T"], dt=0.05, seed=cs["seed"])
    sc = sim.Scenario(cs["dlc"], cs["T"], f, yaw=cs["yaw"], parked=True, park_azimuth=cs["az"], events=cs.get("events", {}), rho=cs.get("rho"))
    r = sim.simulate(t, sc)
    return cs, r["t"].tolist(), r["Qaero"].tolist()

def creep(t, Q, Qb):
    dt = t[1] - t[0]; w = 0.0; ang = 0.0; wmax = 0.0
    for q in Q:
        if w == 0.0 and abs(q) <= Qb: continue
        if w == 0.0: w = 1e-9 * math.copysign(1, q)
        acc = (q - Qb * math.copysign(1, w)) / J
        w_new = w + acc * dt
        if w_new * w <= 0: w_new = 0.0
        w = w_new; ang += abs(w) * dt; wmax = max(wmax, abs(w))
    return ang / (2 * math.pi), wmax * 30 / math.pi

if __name__ == "__main__":
    cases = [c for c in D.RD.build_cases() if c["kind"] == "parked"]
    with mp.Pool(4) as p:
        out = p.map(run, cases)
    res = []
    for cs, t, Q in out:
        Qa = np.array(Q)
        row = dict(dlc=cs["dlc"], yaw=cs["yaw"], az=cs["az"], Q_max=round(float(np.abs(Qa).max())), Q_mean=round(float(Qa.mean())))
        for Qb in BRAKES:
            for lab, k in (("char", 1.0), ("design", FACT)):
                rev, rpm = creep(t, Qa * k, Qb)
                row[f"{int(Qb)}_{lab}"] = dict(revs=round(float(rev), 3), max_rpm=round(float(rpm), 2), t_above=round(float(np.mean(np.abs(Qa * k) > Qb)) * 300, 1))
        res.append(row)
    summ = {}
    for Qb in BRAKES:
        for lab in ("char", "design"):
            k = f"{int(Qb)}_{lab}"
            w = max(res, key=lambda r: r[k]["revs"])
            summ[k] = dict(worst_revs_300s=float(w[k]["revs"]), worst_max_rpm=float(max(r[k]["max_rpm"] for r in res)),
                           cases_slipping=int(sum(r[k]["revs"] > 0.001 for r in res)), worst_case=f'{w["dlc"]} yaw {w["yaw"]} az {w["az"]}')
            print(k, summ[k])
    (HERE / "results" / "creep8.json").write_text(json.dumps(dict(summary=summ, cases=res), indent=1))
