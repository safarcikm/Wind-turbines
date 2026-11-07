"""Doc 36 figure B01: copper loss against demagnetisation reserve for every block (results/blocks_summary.json)."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
OUT = HERE / "results"
rows = json.loads((OUT / "blocks_summary.json").read_text())

INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
FAM = {  # fixed categorical order: blue, orange, aqua
    "one": ("#2a78d6", "o", "N42SH, one block across the pole"),
    "two": ("#eb6834", "s", "N42SH, two blocks across the pole"),
    "base": ("#1baf7a", "D", "N45SH 30×15×12 (M8 baseline)"),
}
LABEL = {"REF": "baseline 30×15×12 N45SH", "A40": "40×20×7.5 (asked)", "W31_12": "31×21×12",
         "W33_11": "33×21×11", "D17_10": "2× 17×35×10", "D20_10": "2× 20×35×10", "W36_12": "36×15×12",
         "W33_8": "33×26×8", "W30_8": "30×26×8", "W36_8": "36×26×8", "G30": "30×15×12 N42SH"}
OFF = {"REF": (8, -12), "A40": (8, 4), "W31_12": (-20, 9), "W33_11": (8, -4), "D17_10": (8, 4), "D20_10": (-4, 10),
       "W36_12": (8, -12), "W33_8": (8, -4), "W30_8": (-6, 8), "W36_8": (8, -10), "G30": (10, -3)}


REF = next(r for r in rows if r["key"] == "REF")


def total(r):
    """Generator loss at rated as compare_m8.py: copper + core (∝ flux²) + rotor (eddy) + 70 W stray."""
    return r["copper_W"] + 202 * (r["emf_28t_100C_V"] / REF["emf_28t_100C_V"]) ** 2 + 30 - REF["eddy_W"] + r["eddy_W"] + 70


def t20(r):
    v = r["T20_C"]
    return 121 if isinstance(v, str) else v


fig, ax = plt.subplots(figsize=(8.6, 5.4), dpi=150)
fig.patch.set_facecolor(SURF)
ax.set_facecolor(SURF)
for fam in ("one", "two", "base"):
    sel = [r for r in rows if (r["key"] == "REF") == (fam == "base") and
           (fam == "base" or (r["k_across"] == 1) == (fam == "one"))]
    c, mk, lab = FAM[fam]
    ax.scatter([total(r) for r in sel], [t20(r) for r in sel], s=64, c=c, marker=mk, label=lab,
               edgecolors=SURF, linewidths=2, zorder=3)
for r in rows:
    if r["key"] in LABEL:
        ax.annotate(LABEL[r["key"]], (total(r), t20(r)), xytext=OFF[r["key"]], textcoords="offset points",
                    fontsize=8, color=INK2 if r["key"] not in ("A40", "W31_12", "D17_10") else INK,
                    fontweight="bold" if r["key"] in ("A40", "W31_12", "D17_10") else "normal")
ax.axhline(100, color=INK2, lw=1, ls=(0, (4, 3)), zorder=1)
ax.text(1010, 100.4, "design rule: 20 % margin at 100 °C", fontsize=8, color=INK2, ha="right", va="bottom")
ax.axvline(total(REF), color=GRID, lw=1, zorder=0)
ax.set_xlabel("Generator loss at rated (copper + core + rotor + stray), W", color=INK2, fontsize=9)
ax.set_ylabel("Highest magnet temperature with 20 % margin\nin the worst short circuit, °C", color=INK2, fontsize=9)
ax.set_title("M8 generator (Ø646, 104 mm, 131 rpm): every block tried", color=INK, fontsize=11, loc="left")
ax.grid(color=GRID, lw=0.6)
ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(GRID)
ax.tick_params(colors=INK2, labelsize=8)
ax.text(0.99, 0.02, "better: up and to the left", transform=ax.transAxes, ha="right", fontsize=8, color=INK2)
ax.legend(loc="upper right", fontsize=8, frameon=False)
ax.set_ylim(97, 115)
fig.tight_layout()
fig.savefig(OUT / "B01-blocks.png", facecolor=SURF)
print("B01 written")
