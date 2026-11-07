"""Doc 38: low-cost 12 kW concept LC8 vs the M8 baseline - masses, part count and production cost.

Run:  python3 concepts.py   (after stall12.py 7.5 and blade_e8.py at TSR 7.5) -> results/concepts.json

Cost rates are the doc 27 model (analysis/size_tsr_map/model.py COST): in-house manufacture, installed,
no development, tooling, certification or margin. Use for comparison, not for a price.
M8 masses: CAD model of doc 37 (cad/turbine_m8/out/model8-parts.json) and the doc 35 18 m tower.
LC8 masses: the S6 6 kW CAD build (bom6.csv, doc 34) for every shared part, plus the LC8 blade (blade_e8.py),
a fixed hub scaled from the S6 hub by the SLM H moment, and the Rev C cooling parts.
18 m towers: doc 27 tower law (base moment from blade area and head mass) calibrated on the doc 09/35 towers.
"""
import json, math, sys
from pathlib import Path
HERE = Path(__file__).parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE.parent / "size_tsr_map"))
import model as M  # noqa: E402

C = M.COST
BL = json.loads((HERE / "results" / "blade_e8_tsr7.5.json").read_text())
ST = json.loads((HERE / "results" / "stall12_tsr7.5.json").read_text())
CAD = json.loads((ROOT / "cad" / "turbine_m8" / "out" / "model8-parts.json").read_text())

# ---------------------------------------------------------------- M8 (doc 35/37), CAD masses
m8 = {p["pid"]: (p["mass_kg"] or 0) * (p["qty"] or 1) for p in CAD["parts"] if p["group"] not in ("tower", "foundation", "tooling")}
grp = {}
for p in CAD["parts"]:
    if p["group"] in ("tower", "foundation", "tooling"):
        continue
    grp.setdefault(p["group"], 0.0); grp[p["group"]] += (p["mass_kg"] or 0) * (p["qty"] or 1)
blades_m8 = sum(v for k, v in m8.items() if k.startswith("NM8-100"))
M8 = dict(
    blades=blades_m8,
    hub_pitch=grp["rotor"] - blades_m8,
    generator=sum(v for k, v in m8.items() if k[:6] in ("NP1-20", "NP1-21", "NP1-22")) ,
    spindle_brake=grp["drivetrain"] - sum(v for k, v in m8.items() if k[:6] in ("NP1-20", "NP1-21", "NP1-22")),
    nacelle=grp["nacelle"], yaw=grp["yaw"], electrical=grp["electrical"],
    tower18=2356.0, footing18_m3=13.5, area=1.337, calipers=3, pitch=True)

# ---------------------------------------------------------------- LC8 (this doc)
S6 = dict(blade=20.6, hub=79.2, spinner=10.7, gen_g6=263.0, spindle_brake=56.5 + 2.7 + 33.6 + 18.1 + 0.5 + 24.5 + 8.0 + 9.0 + 0.4,
          bedplate=122.1, cover=46.0, yaw=55.0 + 2 * 19.0 + 2 * 7.7 + 106.7 + 2 * 14.0 + 6.5 + 6.0 + 10.0, electrical=134.0)
M_H_S6, M_H_LC8 = 18.5, BL["slm"]["H_parked"]["M_yB"]
hub_lc8 = S6["hub"] * (M_H_LC8 / M_H_S6) ** 0.8                  # arms and flanges scale with the root moment
LC8 = dict(
    blades=3 * BL["chosen"]["mass_kg"],
    hub_pitch=hub_lc8 + S6["spinner"] * 1.3,                        # fixed welded hub, no bearings; larger spinner
    generator=39.9 + 50.5 + 2.2 + 20.0 + 91.2 + 10.7 + 2.9 + 7.2 + 12.0,  # Rev C active part = G6 CAD parts (bom6) + Rev C fins/ribs/cover blades (~12 kg); same bookkeeping as the M8 CAD sum
    spindle_brake=S6["spindle_brake"] + 0.0,                        # one caliper, 12 kW 4.4 kNm spring pack (same body)
    nacelle=S6["bedplate"] + S6["cover"], yaw=S6["yaw"], electrical=S6["electrical"],
    area=0.731, calipers=1, pitch=False)


def tower18(head, area):
    sc = 1.0
    F_r = 0.623 * (area / 0.849) + 0.377 * sc
    Mb_r = 0.448 * F_r + 0.552 * head / 1103.0
    return 1940 * Mb_r ** 0.96, 11.9 * Mb_r ** 0.59


def head(d):
    return sum(d[k] for k in ("blades", "hub_pitch", "generator", "spindle_brake", "nacelle", "yaw", "electrical")) - 95.0  # base cabinet sits on the ground


def cost(d, pe_saving=0.0, guyed=False):
    h = head(d)
    if "tower18" in d:
        tw, ft = d["tower18"], d["footing18_m3"]
        k_t, k_f = tower18(1362.4 - 0.0, 1.337)
        cal = (d["tower18"] / k_t, d["footing18_m3"] / k_f)   # calibrate the law on the M8 18 m tower
    else:
        k_t, k_f = tower18(1362.4, 1.337)
        t2, f2 = tower18(h, d["area"])
        tw, ft = 2356.0 * t2 / k_t, 13.5 * f2 / k_f
    parts = dict(blades=d["blades"] * C["blade"], hub_pitch=d["hub_pitch"] * C["hub"], generator=d["generator"] * C["gen"],
                 spindle_brake=d["spindle_brake"] * C["spindle"] + (d["calipers"] - 1) * 900.0,
                 nacelle=d["nacelle"] * C["nacelle"], yaw=d["yaw"] * C["yaw"],
                 electronics=C["pe_fixed"] + C["pe_per_kw"] * 12 - pe_saving,
                 control=C["control"] + (1500.0 if d["pitch"] else 0.0),   # pitch controller, supercap, slip-ring power
                 tower=tw * C["tower"], footing=ft * C["footing"],
                 install=C["install_fixed"] + C["install_per_kg"] * (h + tw))
    return dict(head_kg=round(h), tower18_kg=round(tw), footing18_m3=round(ft, 1), parts={k: round(v) for k, v in parts.items()},
                total=round(sum(parts.values())), masses={k: round(v, 1) for k, v in d.items() if isinstance(v, float)})


res = dict(M8=cost(M8), LC8=cost(LC8))
SW = json.loads((HERE.parent / "variant_l7" / "results" / "sweep_l7.json").read_text())["rows"]
aep = {"M8": next(r["aep"] for r in SW if r["tsr"] == 5.5),      # doc 27 model, pitch, same site scenarios as stall12
       "LC8": {k: round(v * 0.995) for k, v in ST["aep"]["stall"].items()}}   # stall curve; 0.5 % for the 1P/3P exclusion zone
res["aep_kWh"] = aep
crf = C["crf"] + C["om_frac"]
for k in ("M8", "LC8"):
    res[k]["eur_per_MWh"] = {s: round(1000 * res[k]["total"] * crf / aep[k][s]) for s in aep[k]}
res["saving_pct"] = round(100 * (1 - res["LC8"]["total"] / res["M8"]["total"]), 1)
res["isk_per_eur"] = C["isk_per_eur"]
(HERE / "results" / "concepts.json").write_text(json.dumps(res, indent=1))
print(json.dumps(res, indent=1))
