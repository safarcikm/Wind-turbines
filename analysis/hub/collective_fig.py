"""Layout figure for doc 24: side section through the top blade (rotor axis horizontal) + yoke force curve.

Run after collective.py:  python3 collective_fig.py  -> results/collective_layout.png
"""
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon

import collective as C

OUT = Path(__file__).parent / "results"
S = json.loads((OUT / "collective_summary.json").read_text())

STEEL, BRG, MECH, ELEC, STAT = "#8a8f98", "#c8a040", "#3a6ea5", "#5a9a5a", "#b0b0b0"


def rect(ax, x0, x1, z0, z1, fc, ec="k", lw=0.6, mirror=True, **kw):
    ax.add_patch(Rectangle((x0, z0), x1 - x0, z1 - z0, fc=fc, ec=ec, lw=lw, **kw))
    if mirror:
        ax.add_patch(Rectangle((x0, -z1), x1 - x0, z1 - z0, fc=fc, ec=ec, lw=lw, **kw))


fig, (ax, ax2) = plt.subplots(1, 2, figsize=(15, 7.2), gridspec_kw=dict(width_ratios=[2.1, 1]))

# ---------------------------------------------------------------- hub (rotationally drawn about the rotor axis)
x_front, x_rear = -240.0, 200.0
rect(ax, x_front, 175, 220, 230, STEEL)                       # shell Ø460 x 10
rect(ax, 175, 200, 170, 235, STEEL)                           # rear flange to the drum (PCD 400, Ø361 recess)
rect(ax, x_front - 12, x_front, 150, 230, STEEL)              # front plate Ø460/Ø300
# drum hub web and spindle nose (context, stationary grey)
rect(ax, 200, 220, 70, 232, "#d8d8d8", ec="#888")
rect(ax, 40, 330, 45, 70, STAT, ec="#888")                    # spindle nose
rect(ax, -80, 38, 0, 50, ELEC, ec="k")                        # slip ring
ax.text(-21, -95, "slip ring", ha="center", fontsize=7)
# top blade: neck, flange, pitch bearing, blade root (only top drawn; the blade axis is vertical here)
for sgn in (-1, 1):
    ax.add_patch(Rectangle((sgn * 155 - (10 if sgn > 0 else 0), 228), 10, 97, fc=STEEL, ec="k", lw=0.6))
ax.add_patch(Rectangle((-180, 325), 360, 25, fc=STEEL, ec="k", lw=0.6))                       # neck flange 25
ax.add_patch(Rectangle((-177.5, 350), 355, 50, fc=BRG, ec="k", lw=0.6))                       # slewing ring Ø355 x 50
ax.add_patch(Rectangle((-110, 402), 220, 120, fc="#e9e2cf", ec="k", lw=0.6))                  # blade root Ø220
ax.text(0, 470, "blade root Ø220\n10 × M16 studs", ha="center", fontsize=7)
ax.text(205, 372, "pitch bearing, ungeared\nØ355 × 50, Dpw 250", fontsize=7, va="center")
ax.text(205, 300, "welded neck Ø330 × 10\nflange 25", fontsize=7, va="center")

# crank: tube from the blade ring down to the pin plane, lever, pin (projected)
g = S["geometry"]
ax.add_patch(Rectangle((-84, 150), 8, 200, fc=MECH, ec="k", lw=0.5))
ax.add_patch(Rectangle((76, 150), 8, 200, fc=MECH, ec="k", lw=0.5))
ax.add_patch(Rectangle((-125, g["s_pin"] - 12), 250, 25, fc=MECH, ec="k", lw=0.5, alpha=0.35))
ax.text(95, 175, "crank Ø168 × 8,\nr 120 (clamped by\nthe blade studs)", fontsize=7)

# linkage in the two end positions
for th, ls, lab in ((C.TH_FINE, "-", "fine pitch −2°"), (C.TH_FEATHER, "--", "feather 92°")):
    p = C.pin(th)
    xy, e = C.yoke_x(th)
    ax.plot([p[0], e[0]], [p[1], e[1]], ls, color=MECH, lw=2.2)
    ax.plot(p[0], p[1], "o", color=MECH, ms=7, mfc="w")
    ax.plot(e[0], e[1], "o", color=MECH, ms=7, mfc="w")
    # yoke (plate 20) and arm
    ax.add_patch(Rectangle((xy - 10, -120), 20, 240, fc=MECH, ec="k", lw=0.5, alpha=0.9 if ls == "-" else 0.25,
                           ls=ls))
    ax.text(xy, 135 if ls == "-" else -150, f"yoke\n{lab}\nx {xy:.0f}", ha="center", fontsize=7, color=MECH)

# guide rods, electric cylinder, supercap, controller in the nose housing
x_nose = -760.0
ax.add_patch(Polygon([[x_front - 12, 150], [x_nose, 120], [x_nose, -120], [x_front - 12, -150]], closed=True,
                     fc="none", ec="#555", lw=1.0, ls="-."))
ax.text(-560, 160, "nose housing, Al 6082 (inside the spinner)", fontsize=7, color="#333")
rect(ax, -330, -127, 30, 36, "#999", mirror=True)                                 # guide rods Ø25 (drawn thin)
rect(ax, -700, -330, 0, 42, MECH, mirror=True, alpha=0.8)                         # cylinder body
rect(ax, -330, -127, 0, 15, "#666", mirror=True)                                  # rod (extended = fine)
rect(ax, -690, -520, 48, 95, MECH, alpha=0.5, mirror=False)                       # parallel motor + brake
ax.text(-605, 71, "48 V servo\n+ brake", ha="center", va="center", fontsize=7, color="w")
ax.text(-515, 0, "electric cylinder 21 kN, ball screw Ø32 × 5", ha="center", va="center", fontsize=7, color="w")
rect(ax, -680, -500, -110, -55, ELEC, mirror=False)
ax.text(-590, -83, "supercap 16.7 F\n+ drive (STO)", ha="center", va="center", fontsize=7, color="w")

ax.axhline(0, color="k", lw=0.5, ls=(0, (8, 3, 2, 3)))
ax.axvline(0, color="k", lw=0.5, ls=(0, (8, 3, 2, 3)))
ax.text(5, 540, "pitch axis (blade 1)", fontsize=7)
ax.text(140, 8, "rotor axis →  nacelle", fontsize=7)
ax.text(186, -250, "hub face x 200\n12 × M16 PCD 400", fontsize=7, ha="center")
ax.set_xlim(-800, 340)
ax.set_ylim(-280, 560)
ax.set_aspect("equal")
ax.set_xlabel("x along the rotor axis from the blade plane (mm, + towards the nacelle)")
ax.set_ylabel("radius (mm)")
ax.set_title("Collective pitch, section through blade 1 (crank pin and link projected)", fontsize=10)

# ---------------------------------------------------------------- force curve
cu = S["curves"]
sv = S["supercap_variant"]["actuator"]
ax2.plot(cu["theta"], cu["F_req_design_kN"], color=MECH, lw=2, label="trip, −30 °C, SLM G edge moment (γ 3.0)")
ax2.plot(cu["theta"], cu["F_req_single_kN"], color=MECH, lw=1.2, ls="--", label="trip, −30 °C, simulated e-stop")
ax2.axhline(sv["F_rated_kN"], color="k", lw=1, ls=":", label=f"cylinder force limit {sv['F_rated_kN']} kN")
ax2.axhline(sv["F_normal_peak_kN"], color=ELEC, lw=1, ls="-.", label=f"normal pitching peak {sv['F_normal_peak_kN']} kN")
ax2.set_xlabel("pitch angle (deg)")
ax2.set_ylabel("yoke force (kN), all three blades")
ax2.set_ylim(0, 25)
ax2.grid(alpha=0.3)
ax2.legend(fontsize=7, loc="upper center")
ax2.set_title("Force needed at the yoke", fontsize=10)
fig.tight_layout()
fig.savefig(OUT / "collective_layout.png", dpi=150)
print("written", OUT / "collective_layout.png")
