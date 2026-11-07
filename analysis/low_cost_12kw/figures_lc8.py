"""Doc 38 figures: F01 TSR sweep at Ø8.0 m, F02 cost breakdown M8 vs LC8.  Run: python3 figures_lc8.py"""
import json
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = Path(__file__).parent
OUT = HERE / "results"
SW = json.loads((HERE.parent / "variant_l7" / "results" / "sweep_l7.json").read_text())["rows"]
CO = json.loads((OUT / "concepts.json").read_text())
BLUE, ORANGE, INK, MUTED, GRID = "#2a78d6", "#eb6834", "#222222", "#6b6b6b", "#e6e6e6"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False})

t = [r["tsr"] for r in SW]
panels = [("Sound at 60 m, dB(A) (Hau model, ±4 dB)", [r["Lp60"] for r in SW], 45.0, "target 45"),
          ("Parked blade root moment, kNm (SLM H, design)", [r["M_park"] for r in SW], None, None),
          ("Rated shaft torque, Nm", [r["Q_rated"] for r in SW], 730.0, "Rev C rating"),
          ("Rain / ash erosion rate vs M8 (∝ tip speed⁶)", [r["erosion_vs_M8"] for r in SW], None, None)]
fig, axs = plt.subplots(2, 2, figsize=(9, 6))
for ax, (title, y, ref, lab) in zip(axs.flat, panels):
    ax.plot(t, y, color=BLUE, lw=2)
    ax.set_title(title, fontsize=9, color=INK, loc="left")
    ax.grid(color=GRID, lw=0.8); ax.set_axisbelow(True)
    for x, name, col in ((5.5, "M8", MUTED), (7.5, "LC8", ORANGE)):
        yi = y[t.index(x)]
        ax.plot([x], [yi], "o", ms=8, color=col, mec="white", mew=2, zorder=3)
        ax.annotate(f"{name} {yi:g}", (x, yi), xytext=(6, -12 if name == "M8" else 6), textcoords="offset points", fontsize=8, color=INK)
    if ref:
        ax.axhline(ref, color=MUTED, lw=1, ls="--"); ax.text(t[-1], ref, lab, ha="right", va="bottom", fontsize=8, color=MUTED)
    ax.set_xlabel("Design TSR (Ø8.0 m, rated 10 m/s)")
fig.tight_layout(); fig.savefig(OUT / "F01-tsr-sweep.png", dpi=150); plt.close(fig)

keys = ["blades", "hub_pitch", "generator", "spindle_brake", "nacelle", "yaw", "electronics", "control", "tower", "footing", "install"]
names = ["Blades", "Hub + pitch", "Generator", "Spindle + brake", "Bedplate + cover", "Yaw", "Power electronics", "Control", "18 m tower", "Footing", "Installation"]
fig, ax = plt.subplots(figsize=(8, 4.8))
y = range(len(keys))
a = [CO["M8"]["parts"][k] / 1e3 for k in keys]; b = [CO["LC8"]["parts"][k] / 1e3 for k in keys]
ax.barh([i - 0.2 for i in y], a, 0.38, color=MUTED, label=f"M8 (doc 35/37): {CO['M8']['total']/1e3:.0f} k€")
ax.barh([i + 0.2 for i in y], b, 0.38, color=ORANGE, label=f"LC8 (this doc): {CO['LC8']['total']/1e3:.0f} k€")
ax.set_yticks(list(y), names); ax.invert_yaxis(); ax.set_xlabel("Installed cost, k€ (doc 27 rates)")
ax.grid(axis="x", color=GRID); ax.set_axisbelow(True); ax.legend(frameon=False, loc="lower right")
ax.set_title("Where the cost goes", loc="left", fontsize=10, color=INK)
fig.tight_layout(); fig.savefig(OUT / "F02-cost-breakdown.png", dpi=150); plt.close(fig)
print("ok")
