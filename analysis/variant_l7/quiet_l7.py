"""Doc 38: noise-reduced operation for the high-TSR blades (doc 27 model, extended tables).

Run:  python3 quiet_l7.py  -> results/quiet_l7.json
A quiet mode caps the rotor speed (tip speed) of a high-TSR blade. The blade then runs below its optimum
TSR above the cap and reaches 12 kW at a higher wind (or not at all). Reported: sound at 60 m (Hau model
at 8 m/s, as doc 27) and yearly energy against the same blade at full speed, Rayleigh/Weibull doc 27 sites.
"""
import json, math, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "size_tsr_map"))
import model as M  # noqa: E402
TAB = json.loads((HERE / "results" / "rotor_tables_ext.json").read_text())
M.TAB, M.TSRS, M.LAMS = TAB, np.array(TAB["tsrs"]), np.array(TAB["lams"])
M.calibrate()
R = 4.0
out = {}
for tsr in (5.5, 6.5, 7.0, 7.5, 8.0, 9.0):
    full = M.evaluate(12, tsr, R, tsr * 10.0)
    rows = {}
    for tip in sorted({tsr * 10.0, 70.0, 62.0, 55.0, 50.0, 48.0}, reverse=True):
        if tip > tsr * 10.0:
            continue
        r = M.evaluate(12, tsr, R, tip)
        lw8, _ = M.noise(2 * R, min(r["lam_opt"] * 8.0, tip), tip)
        rows[f"tip{tip:.0f}"] = dict(rpm=round(tip / R * 30 / math.pi), Lp60=round(M.spl(lw8, 60), 1), d45=round(M.dist_for(lw8, 45)),
                                     rated_wind=round(r["rated_wind"], 1),
                                     aep_loss_pct={k: round(100 * (1 - r["aep"][k] / full["aep"][k]), 1) for k in r["aep"]})
    out[f"TSR{tsr}"] = rows
(HERE / "results" / "quiet_l7.json").write_text(json.dumps(out, indent=1))
for k, v in out.items():
    print(k)
    for kk, vv in v.items():
        print("  ", kk, vv)
