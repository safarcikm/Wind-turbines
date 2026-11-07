"""Doc 38 addendum: what a Ø5.0 m 12 kW rotor at high TSR does (doc 27 model, extended tables).
Run: python3 d5_check.py -> results/d5_check.json"""
import json, math, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "size_tsr_map"))
import model as M  # noqa: E402
TAB = json.loads((HERE.parent / "variant_l7" / "results" / "rotor_tables_ext.json").read_text())
M.TAB, M.TSRS, M.LAMS = TAB, np.array(TAB["tsrs"]), np.array(TAB["lams"])
M.calibrate()
out = []
for D, tsr, tip in ((8.0, 7.5, 75.0), (5.0, 7.5, 75.0), (5.0, 8.0, 90.0), (5.0, 9.0, 100.0), (5.0, 10.0, 110.0), (6.0, 8.0, 85.0)):
    r = M.evaluate(12, tsr, D / 2, tip)
    out.append(dict(D=D, tsr=tsr, tip=tip, rpm=round(r["rpm"]), rated_wind=round(r["rated_wind"], 1),
                    Lp60=round(M.spl(r["Lw8"], 60), 1), d45=round(M.dist_for(r["Lw8"], 45)),
                    M_park=round(r["M_park"], 1), Q=round(r["Q_rated"]), head=round(r["m_head"]), tower=round(r["m_tower"]),
                    capex=round(r["capex"]), aep={k: round(v) for k, v in r["aep"].items()},
                    eur_MWh={k: round(1000 * r["capex"] * (M.COST["crf"] + M.COST["om_frac"]) / v) for k, v in r["aep"].items()},
                    cf={k: round(100 * v, 1) for k, v in r["cf"].items()}))
(HERE / "results" / "d5_check.json").write_text(json.dumps(out, indent=1))
for o in out: print(o)
