"""M8 bedplate NP8-300: the doc 32 bedplate model (turbine_6kw/bedplate6.py) with the M8 SLM loads (doc 35 §6).

Run:  python3 bedplate_m8.py   (after structure_m8.py)  -> results/bedplate_m8.json

Doc 32 found that the 12 kW bedplate NP1-300 as drawn weighs 333 kg (docs 25/30 carried 150 kg) and
that it is very lightly loaded. Here the same plate-by-plate model checks:
  * NP1-300 as drawn (40/40/20 mm plates),
  * NS6-300, the 6 kW light bedplate (20/25/10 mm, lightening holes, short rear),
  * a scan of NS6-style geometries with thicker plates; the lightest one that keeps every hand-check
    utilisation at or below 0.70 (margin for the FE check still to do) is proposed as NP8-300.
Interfaces are those of NP1-300 (spindle flange Ø410 / 12 x M20 PCD 350, yaw flange 16 x M16 PCD 300).
"""
from __future__ import annotations
import json, sys
import common as C

sys.path.insert(0, str(C.ROOT / "turbine_6kw"))
import bedplate6 as B  # noqa: E402

SLM = json.loads((C.OUT / "slm_m8.json").read_text())
B.SLM = SLM["ultimate_design_values_gamma_3_kN_kNm"]
B.FAT = SLM["A_fatigue_ranges_kN_kNm"]
B.X_YAW = C.OVERHANG * 1e3
B.RC = (-B.X_YAW, B.H_ROTOR + 40.0)
GEN = json.loads((C.OUT / "generator_m8.json").read_text())
BLD = json.loads((C.OUT / "blade_m8.json").read_text())
M_AHEAD = 3 * BLD["carbon"]["mass_kg"] + 337.0 + GEN["mass_kg"]["total"]["M8"] + 0.5 * 63.0   # rotor, hub, generator, front of spindle
X_AHEAD = 0.36                                    # m, their CoG ahead of the spindle flange
U_MAX = 0.70


def evaluate(v):
    plates, geo = B.geometry(v)
    m, tot = B.mass(plates)
    ck = B.checks(v, geo, m_ahead=M_AHEAD, x_ahead=X_AHEAD)
    u = max(ck[k]["util"] for k in ("root_section", "front_plate", "bottom_plate", "yaw_bolts", "fatigue_root"))
    return dict(inputs=v, masses_kg=m, mass_kg=tot, checks=ck, util_max=u)


def main():
    out = {"NP1-300 (12 kW, as drawn)": evaluate(B.NP1), "NS6-300 (6 kW) under M8 loads": evaluate(B.NS6)}
    best = None
    for tf in (20.0, 25.0, 30.0, 35.0):
        for tb in (25.0, 30.0, 35.0, 40.0):
            for ts in (10.0, 12.0, 15.0):
                v = dict(B.NS6, t_front=tf, t_bottom=tb, t_side=ts)
                r = evaluate(v)
                if r["util_max"] <= U_MAX and (best is None or r["mass_kg"] < best["mass_kg"]):
                    best = r
    out["NP8-300 (proposed)"] = best
    out["chosen_mass_kg"] = best["mass_kg"]
    out["saving_vs_NP1_kg"] = round(out["NP1-300 (12 kW, as drawn)"]["mass_kg"] - best["mass_kg"], 1)
    out["inputs"] = dict(m_ahead_kg=round(M_AHEAD), x_ahead_m=X_AHEAD, x_yaw_mm=B.X_YAW, util_limit=U_MAX)
    (C.OUT / "bedplate_m8.json").write_text(json.dumps(out, indent=1))
    for k, v in out.items():
        if isinstance(v, dict) and "mass_kg" in v:
            print(k, v["mass_kg"], "kg, util", v["util_max"], {kk: vv["util"] for kk, vv in v["checks"].items() if isinstance(vv, dict)})
    print("chosen", out["chosen_mass_kg"], "saving", out["saving_vs_NP1_kg"])


if __name__ == "__main__":
    main()
