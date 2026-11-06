"""6 kW turbine (doc 28): rotor size and TSR from the doc 27 decision-map model.

Run:  python3 sizing.py   -> results/sizing.json, results/design.json (input to regulation.py)
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "results"; OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(HERE.parent / "size_tsr_map"))
import model as m27  # noqa: E402

P_E = 6
m27.calibrate()


def row(r):
    return dict(D=round(r["D"], 2), rpm=round(r["rpm"]), tip=round(r["tip"], 1), rated_wind=round(r["rated_wind"], 2),
                Lp60=round(m27.spl(r["Lw8"], 60), 1), d40=round(r["d40"]),
                aep={k: round(v / 1000, 1) for k, v in r["aep"].items()},
                M_park=round(r["M_park"], 1), T_park=round(r["T_park"], 1), Q=round(r["Q_rated"]),
                m_blade=round(r["m_blade"], 1), m_head=round(r["m_head"]), m_tower=round(r["m_tower"]),
                capex=round(r["capex"]), lcoe={k: round(v * 1000) for k, v in r["lcoe"].items()})


grid = []
for vr in (9.0, 9.5, 10.0, 10.5):
    for tsr in (5.0, 5.5, 6.0, 6.5):
        R, tip = m27.size(P_E, tsr, vr)
        o = row(m27.evaluate(P_E, tsr, R, tip, rated_wind=vr)); o.update(vr=vr, tsr=tsr); grid.append(o)

# chosen: TSR 5.5, round Ø6.0 m, speed cap so that tip = TSR x rated wind of the sizing rule
TSR = 5.5
R = 3.0
Rs, tips = m27.size(P_E, TSR, 9.5)
tip = tips * R / Rs * (Rs / R) ** 0.0       # keep the tip speed of the 9.5 m/s rule
r = m27.evaluate(P_E, TSR, R, tip)
chosen = row(r)
J = 216.0 * (r["m_blade"] / 20.5) * (R / 3.75) ** 2 + 6.0   # doc 12 rotor inertia scaled with blade mass and R^2, + generator drum
design = dict(P_e=P_E, R=R, D=2 * R, tsr=TSR, rpm=r["rpm"], tip=tip, rated_wind=r["rated_wind"], J_rotor=J,
              m_blade=r["m_blade"])
(OUT / "design.json").write_text(json.dumps(design, indent=1))
(OUT / "sizing.json").write_text(json.dumps(dict(grid=grid, chosen=chosen, design=design), indent=1))
for g in grid:
    print(g["vr"], g["tsr"], g["D"], g["rpm"], g["tip"], g["Lp60"], g["aep"], g["M_park"], g["m_head"], g["capex"], g["lcoe"])
print("chosen", json.dumps(chosen), json.dumps(design))
