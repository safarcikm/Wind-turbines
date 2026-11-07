"""Doc 41: cost and hours of the CNC foam-core blade against the doc 39 mould blade (one turbine = 3 blades).

Run:  python3 cost_foam.py      (needs results/foam_m8.json from foam_m8.py) -> results/cost_foam.json, F02 figure

Rates are the doc 39 Rates sheet (analysis/cost_m8/cost_m8.py), read from that file so the two stay in step.
The mould route is the doc 39 blade lines (38 h + 1.5 h per blade), split into steps here only to show where
the hours go; its total is unchanged. Inserts (12 x M16 per blade, doc 39 line NM8-105) are identical in both.
"""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
src = (HERE.parent / "cost_m8" / "cost_m8.py").read_text().split("# ------------------------------------------------------------------ parts")[0]
g = {"__file__": str(HERE.parent / "cost_m8" / "cost_m8.py")}
exec(src, g)
R = g["R"]
VOL = R["VOLUME"]

foam = json.loads((HERE / "results" / "foam_m8.json").read_text())["RECOMMENDED_foam_H80_carbon_aged"]
ms = foam["mass_split_kg"]

# ------------------------------------------------------------------ mould route (doc 39, per blade)
MOULD_STEPS = [  # step, composite h
    ("Mould prep, release, gelcoat (2 halves)", 2.5),
    ("Cut and kit plies, PVC core, web kit", 3.0),
    ("Lay up 2 shells dry: glass, core, carbon caps", 6.0),
    ("Bag and infuse 2 shells", 4.0),
    ("Shear web: lay up, infuse, trim", 4.0),
    ("Root build-up round inserts in jig", 4.0),
    ("Dry-fit, bond web, close mould, cure", 4.0),
    ("Demould, trim flash and TE", 2.0),
    ("Post-cure handling", 0.5),
    ("Bond-line inspection, pinhole repair", 2.0),
    ("Finish seams, topcoat", 3.0),
    ("LEP, tip receptor, drill and face root", 3.0),
]
MOULD = dict(
    comp_h=sum(h for _, h in MOULD_STEPS), mach_h=0.0, assy_h=1.5,
    material={"glass fabrics 14.5 kg x 1.15": 14.5 * 1.15 * R["GLASS"],
              "carbon UD fabric 4.2 kg x 1.10": 4.2 * 1.10 * R["CARBON"],
              "epoxy + paste 11.0 kg x 1.35": 11.0 * 1.35 * R["EPOXY"],
              "PVC core kitted 3.0 kg x 1.30": 3.0 * 1.30 * R["CORE"]},
    bought={"vacuum consumables (3 infusions)": 160, "LEP + topcoat": 120, "lightning receptor + conductor": 90},
    tooling={"plug milled outside": 14000,
             "mould halves: 2 x 118 kg tooling laminate + 230 h": 2 * 118.1 * 1.2 * R["TOOLGRP"] + 230 * R["R_COMP"],
             "mould frame 179 kg RHS + 40 h": 178.6 * 1.1 * R["S235"] + 40 * R["R_FAB"],
             "root insert jig, drilling + balancing fixtures": 4000},
    mass_kg=34.07, lead_time="12-16 weeks (plug, 2 moulds, first-article blade)")

# ------------------------------------------------------------------ foam-core route (doc 41, per blade)
FOAM_STEPS = [  # step, composite h, CNC h
    ("Cut H80 sheets near-net and bond the stacked blank", 1.0, 0.5),
    ("CNC the core, two sides: outline, cap pockets, web slits, conductor groove, balance pocket", 0.0, 3.5),
    ("Split into LE / spar / TE blocks, seal cut surfaces", 1.0, 0.0),
    ("Down conductor, biax wrap round spar block (= webs)", 1.5, 0.0),
    ("Carbon planks: cut, chamfer 1:50, sand, place in pockets", 1.5, 0.0),
    ("Root tube on mandrel with the 12 inserts (excl. insert line), face on lathe", 3.0, 1.0),
    ("Assemble blocks, root tube and tip block on the core", 1.0, 0.0),
    ("Outer triax skin + TE UD + root plies dry, peel ply, flow mesh, bag, leak test", 3.5, 0.0),
    ("One-shot infusion, cure, post-cure 65 C handling", 1.0, 0.0),
    ("Debag, trim TE and tip, tap test / thermography", 1.0, 0.0),
    ("Fill, fair and sand the bag-side surface, prime", 4.0, 0.0),
    ("Topcoat, LEP, tip receptor", 2.0, 0.0),
]
core_blank_kg = foam["core_volume_m3"] * 1.6 * 80          # near-net stacked blank, buy-to-fly 1.6
glass_fibre_kg = ms["glass_laminate_incl_10pct"] / 1.10 * 0.65   # fibre mass fraction 0.65 (infused)
resin_kg = (ms["glass_laminate_incl_10pct"] / 1.10 * 0.35 + ms["resin_uptake"] + 0.6) * 1.30   # + 0.6 kg adhesive, 30 % loss
FOAM = dict(
    comp_h=sum(h for _, h, _ in FOAM_STEPS), mach_h=sum(m for _, _, m in FOAM_STEPS), assy_h=1.5,
    material={f"PVC H80 sheet {core_blank_kg:.1f} kg (blank, buy-to-fly 1.6)": core_blank_kg * R["CORE"],
              f"glass fabrics {glass_fibre_kg:.1f} kg x 1.15": glass_fibre_kg * 1.15 * R["GLASS"],
              f"pultruded carbon planks {ms['cap_laminate']:.1f} kg x 1.08 at 32 EUR/kg": ms["cap_laminate"] * 1.08 * 32.0,
              f"epoxy {resin_kg:.1f} kg (laminate, cut-cell uptake, adhesive, 30 % loss)": resin_kg * R["EPOXY"]},
    bought={"vacuum consumables (1 infusion + root tube)": 120, "fairing filler + primer": 35, "LEP + topcoat": 120,
            "lightning receptor + conductor": 90},
    tooling={"root tube mandrel + insert fixture plate (turned in-house)": 3000,
             "core flip/registration board, assembly cradles": 1500,
             "root insert jig, drilling + balancing fixtures (as mould route)": 4000},
    mass_kg=foam["mass_kg"], lead_time="3-4 weeks (CAM files, mandrel, first core)")

INSERTS_PER_SET = 1875.0   # doc 39 NM8-105, 36 inserts incl. bonding, identical in both routes
ROUTER_CAPEX = 50000.0     # 3-axis gantry router 4.5 x 1.8 m, Z 600 mm, if one has to be bought for this


def per_set(d, volume=VOL, router=False):
    lab = 3 * (d["comp_h"] * R["R_COMP"] + d["mach_h"] * R["R_MACH"] + d["assy_h"] * R["R_ASSY"])
    mat = 3 * sum(d["material"].values())
    buy = 3 * sum(d["bought"].values())
    tool = sum(d["tooling"].values()) + (ROUTER_CAPEX if router else 0.0)
    tool_pt = tool / volume
    return dict(labour=round(lab), material=round(mat), bought=round(buy), inserts=INSERTS_PER_SET,
                tooling_per_turbine=round(tool_pt), tooling_total=round(tool),
                total=round(lab + mat + buy + INSERTS_PER_SET + tool_pt),
                hours_per_blade=round(d["comp_h"] + d["mach_h"] + d["assy_h"], 1),
                hours_per_set=round(3 * (d["comp_h"] + d["mach_h"] + d["assy_h"]), 1))


def main():
    out = dict(rates_from="analysis/cost_m8/cost_m8.py", volume=VOL,
               mould=dict(per_set(MOULD), steps=MOULD_STEPS, material_lines=MOULD["material"], bought_lines=MOULD["bought"],
                          tooling=MOULD["tooling"], mass_kg=MOULD["mass_kg"], lead_time=MOULD["lead_time"]),
               foam=dict(per_set(FOAM), steps=FOAM_STEPS, material_lines=FOAM["material"], bought_lines=FOAM["bought"],
                         tooling=FOAM["tooling"], mass_kg=FOAM["mass_kg"], lead_time=FOAM["lead_time"]),
               foam_with_router_capex=per_set(FOAM, router=True))
    m, f = out["mould"]["total"], out["foam"]["total"]
    out["saving_per_turbine"] = m - f
    out["saving_pct_of_blade_line"] = round(100 * (m - f) / m, 1)
    out["saving_pct_of_turbine_exw_118k"] = round(100 * (m - f) / 118300, 1)
    out["breakeven_extra_hours_per_blade"] = round((m - f) / 3 / R["R_COMP"], 1)
    # learning: doc 39 lever 38 -> 25 h for the mould blade; same -33 % on the foam composite hours
    lm = dict(MOULD, comp_h=25.0); lf = dict(FOAM, comp_h=FOAM["comp_h"] * 25 / 38)
    out["mature_unit50"] = dict(mould=per_set(lm), foam=per_set(lf))
    out["volume_sensitivity"] = {str(v): dict(mould=per_set(MOULD, v)["total"], foam=per_set(FOAM, v)["total"],
                                               foam_router=per_set(FOAM, v, router=True)["total"])
                                 for v in (1, 2, 5, 10, 25, 50, 100, 200)}
    (HERE / "results" / "cost_foam.json").write_text(json.dumps(out, indent=1))
    for k in ("mould", "foam", "foam_with_router_capex"):
        print(k, {kk: vv for kk, vv in out[k].items() if kk not in ("steps", "material_lines", "bought_lines", "tooling")})
    print("saving", out["saving_per_turbine"], out["saving_pct_of_blade_line"], out["saving_pct_of_turbine_exw_118k"],
          "breakeven h/blade", out["breakeven_extra_hours_per_blade"])
    print("mature", out["mature_unit50"])
    print("volume", out["volume_sensitivity"])
    plot(out)


def plot(out):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.3))
    cats = ["labour", "material", "bought", "inserts", "tooling_per_turbine"]
    labels = ["Labour", "Materials", "Bought-in", "Root inserts", "Tooling / 50"]
    cols = ["#4c72b0", "#55a868", "#c44e52", "#8172b2", "#ccb974"]
    for i, (k, name) in enumerate((("mould", "Mould blade\n(doc 39)"), ("foam", "CNC foam-core\n(doc 41)"))):
        b = 0
        for c, lab, col in zip(cats, labels, cols):
            v = out[k][c]
            ax[0].bar(i, v, bottom=b, color=col, label=lab if i == 0 else None, width=0.55)
            if v > 400:
                ax[0].text(i, b + v / 2, f"{v:,.0f}", ha="center", va="center", fontsize=8, color="white")
            b += v
        ax[0].text(i, b + 250, f"€{b:,.0f}\n{out[k]['hours_per_set']:.0f} h", ha="center", fontsize=9)
    ax[0].set_xticks([0, 1], ["Mould blade\n(doc 39)", "CNC foam-core\n(doc 41)"])
    ax[0].set_ylabel("€ per turbine (3 blades)"); ax[0].set_ylim(0, 19500); ax[0].legend(fontsize=7, loc="upper center", ncol=3)
    ax[0].set_title("Blade set cost at 50 turbines")
    vs = out["volume_sensitivity"]; v = [int(k) for k in vs]
    ax[1].loglog(v, [vs[str(x)]["mould"] for x in v], "k-o", label="Mould blade")
    ax[1].loglog(v, [vs[str(x)]["foam"] for x in v], "C2-o", label="Foam-core, router already owned")
    ax[1].loglog(v, [vs[str(x)]["foam_router"] for x in v], "C2--", label="Foam-core + €50k router bought for it")
    ax[1].set_xlabel("Turbines built (tooling written off over these)"); ax[1].set_ylabel("€ per turbine (3 blades)")
    ax[1].grid(alpha=0.3, which="both"); ax[1].legend(fontsize=8); ax[1].set_title("Effect of production volume")
    fig.tight_layout(); fig.savefig(HERE / "results" / "F02-cost.png", dpi=120)


if __name__ == "__main__":
    main()
