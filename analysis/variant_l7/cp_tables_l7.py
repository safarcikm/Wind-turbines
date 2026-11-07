"""Extend the doc 27 non-dimensional rotor tables to design TSR 10 (doc 38).

Run:  python3 cp_tables_l7.py   (~3 min) -> results/rotor_tables_ext.json
Same blade rule and BEM model as ../size_tsr_map/cp_tables.py (imported unchanged); only the TSR list grows.
"""
import json, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "size_tsr_map"))
import cp_tables as CT  # noqa: E402

TSRS = [4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0]
old = json.loads((HERE.parent / "size_tsr_map" / "results" / "rotor_tables.json").read_text())
have = {t["tsr"]: t for t in old["tables"]}
tabs = [have.get(t) or CT.table(t) for t in TSRS]
res = dict(lams=old["lams"], tsrs=TSRS, note=old["note"] + " Extended to TSR 10 for doc 38.", tables=tabs)
(HERE / "results" / "rotor_tables_ext.json").write_text(json.dumps(res))
for t in tabs:
    print(t["tsr"], round(t["area_R2"], 4), round(t["cmax_R"], 4), t["rough"]["cp_max"], t["rough"]["lam_opt"], t["clean"]["cp_max"], round(t["park_M_R3"], 5))
