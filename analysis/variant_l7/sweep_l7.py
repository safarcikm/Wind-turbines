"""Doc 38 step 1: TSR sweep at fixed Ø8.0 m, rated 10 m/s, with the doc 27 parametric model.

Run:  python3 sweep_l7.py   (needs results/rotor_tables_ext.json) -> results/sweep_l7.json, sweep_l7.csv
The doc 27 model (../size_tsr_map/model.py) is imported unchanged; only its rotor table is replaced by the
extended one (TSR 4-10). Tip speed = TSR x 10 m/s, as for M8 (131 rpm = 5.5 x 10 / 4.0).
"""
import csv, json, math, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "size_tsr_map"))
import model as M  # noqa: E402

TAB = json.loads((HERE / "results" / "rotor_tables_ext.json").read_text())
M.TAB, M.TSRS, M.LAMS = TAB, np.array(TAB["tsrs"]), np.array(TAB["lams"])
cal = M.calibrate()          # constants re-derived; identical, since TSR 5-6.5 rows are unchanged
R, VR = 4.0, 10.0
rows = []
for tsr in np.arange(5.5, 10.01, 0.5):
    tip = tsr * VR
    r = M.evaluate(12, float(tsr), R, tip)
    t = M.tables(float(tsr))
    erosion = (tip / 54.9) ** 6.0          # rain/ash erosion rate vs M8, ~v^5-8 (v^6 mid value)
    rows.append(dict(tsr=float(tsr), rpm=round(r["rpm"], 1), tip=round(tip, 1), tip8=round(r["tip8"], 1),
                     rated_wind=round(r["rated_wind"], 2), cp_rough=round(r["cp_max"], 3), cp_clean=round(max(t_["clean"]["cp"]) if False else 0, 3),
                     cmax=round(r["cmax"], 3), area=round(r["blade_area"], 3), Lw8=round(r["Lw8"], 1),
                     Lp60=round(M.spl(r["Lw8"], 60), 1), d45=round(M.dist_for(r["Lw8"], 45.0)), d40=round(r["d40"]), d35=round(r["d35"]),
                     M_park=round(r["M_park"], 1), T_park=round(r["T_park"], 1), Q_rated=round(r["Q_rated"]),
                     m_blade=round(r["m_blade"], 1), m_hub=round(r["m_hub"]), m_gen=round(r["m_gen"]), m_head=round(r["m_head"]),
                     m_tower18=round(r["m_tower"]), aep={k: round(v) for k, v in r["aep"].items()}, erosion_vs_M8=round(erosion, 2)))
    del rows[-1]["cp_clean"]
base = rows[0]
for x in rows:
    x["aep_vs_M8_pct"] = {k: round(100 * (x["aep"][k] / base["aep"][k] - 1), 1) for k in x["aep"]}
(HERE / "results" / "sweep_l7.json").write_text(json.dumps(dict(calibration=cal["designs"], rows=rows), indent=1))
with open(HERE / "results" / "sweep_l7.csv", "w", newline="") as fh:
    w = csv.writer(fh); keys = [k for k in rows[0] if k not in ("aep", "aep_vs_M8_pct")]
    w.writerow(keys + [f"AEP_{k}" for k in base["aep"]])
    for x in rows:
        w.writerow([x[k] for k in keys] + list(x["aep"].values()))
for x in rows:
    print({k: v for k, v in x.items() if k not in ("aep",)})
