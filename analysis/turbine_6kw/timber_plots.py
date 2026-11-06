"""Doc 33 figures from timber6.py results.  Run: python3 timber_plots.py -> results/T01, T02 png."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
RES = HERE / "results"
T6 = json.loads((RES / "timber6.json").read_text())
T12 = json.loads((RES / "timber12.json").read_text())
G = json.loads((RES / "design6.json").read_text())["blade_stations"]
sys.argv = sys.argv[:1]
import timber6 as TB  # noqa: E402


def t01():
    opts = [("Glass (doc 30/31)", None, "#7f8c8d"),
            ("Veneer shell DF", "shell_DF_std", "#c0392b"),
            ("Carved DF", "carved_DF_std", "#c0392b"),
            ("Carved DF, thick airfoils", "carved_DF_xthick", "#3a8f5c"),
            ("Carved DF + carbon strips", "hybrid_DF_std", "#2f6db5"),
            ("Carved spruce + carbon strips", "hybrid_SS_std", "#2f6db5")]
    fig, ax = plt.subplots(1, 3, figsize=(13, 4.3))
    names = [o[0] for o in opts]
    m = [T6["glass_doc31"]["mass_kg"] if k is None else T6[k]["mass_kg"] for _, k, _ in opts]
    u = [0.43 if k is None else max(T6[k]["max_util"].values()) for _, k, _ in opts]
    f = [T6["glass_doc31"]["f_flap_Hz"] if k is None else T6[k]["f_flap_Hz"] for _, k, _ in opts]
    cols = [o[2] for o in opts]
    y = np.arange(len(opts))[::-1]
    for a, val, lab in ((ax[0], m, "Blade mass [kg]"), (ax[1], u, "Highest utilisation (≤ 1.0 passes)"), (ax[2], f, "1st flap frequency, standstill [Hz]")):
        a.barh(y, val, color=cols)
        for yy, v in zip(y, val):
            a.text(v, yy, f" {v:.1f}" if lab.startswith(("Blade", "1st")) else f" {v:.2f}", va="center", fontsize=8)
        a.set_xlabel(lab); a.grid(axis="x", alpha=0.3)
        a.set_yticks(y); a.set_yticklabels(names if a is ax[0] else [""] * len(y), fontsize=8)
    ax[1].axvline(1.0, color="k", lw=0.8)
    ax[2].axvline(3 * 164 / 60, color="#d9822b", lw=1); ax[2].text(3 * 164 / 60, -0.7, " 3P at 164 rpm", color="#d9822b", fontsize=7)
    ax[0].set_title("T01a  Mass", fontsize=10); ax[1].set_title("T01b  Strength (parked storm SLM H governs)", fontsize=10)
    ax[2].set_title("T01c  Stiffness", fontsize=10)
    fig.suptitle("S6 blade, Ø6.0 m: glass vs timber builds (red = fails on the unchanged outline)", fontsize=10)
    fig.tight_layout(); fig.savefig(RES / "T01_timber_options.png", dpi=130); plt.close(fig)


def t02():
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
    ax[0].plot(G["r"], G["mass_per_m"], color="#7f8c8d", label="Glass (doc 30)")
    for k, col, lab in (("hybrid_DF_std", "#2f6db5", "Carved DF + carbon strips"), ("carved_DF_xthick", "#3a8f5c", "Carved DF, thick airfoils")):
        st = T6[k]["stations"]
        ax[0].plot(st["r"], st["mass_per_m"], color=col, label=lab)
    st = T6["hybrid_DF_std"]["stations"]
    a2 = ax[0].twinx()
    a2.fill_between(st["r"], st["t_carbon_mm"], color="#2f6db5", alpha=0.15, step="mid")
    a2.set_ylabel("Carbon strip thickness, each face [mm]", color="#2f6db5"); a2.set_ylim(0, 10)
    ax[0].set_xlabel("Radius [m]"); ax[0].set_ylabel("Mass per metre [kg/m]"); ax[0].grid(alpha=0.3); ax[0].legend(fontsize=8)
    ax[0].set_title("T02a  Spanwise mass", fontsize=10)
    # section sketch at r = 1.3 m, hybrid
    TB.set_thickness("std")
    r = 1.3
    c = float(np.interp(r, TB.BLD.BL.r, TB.BLD.BL.chord)); tc = TB.BLD.t_over_c(r)
    x, y = TB.BLD.outline(c, tc)[:2]
    tw = 0.015
    ci = c - 3 * tw; tci = (c * tc - 2 * tw) / ci
    xi, yi = TB.BLD.outline(ci, tci)[:2]; xi = xi + 1.2 * tw
    ax[1].fill(x * 1000, y * 1000, color="#e8c99b", label="Douglas fir laminate")
    ax[1].fill(xi * 1000, yi * 1000, color="white")
    b = TB.B_CF * c; x0 = 0.18 * c
    i_up = np.argmax(y)
    ytop, ybot = y.max(), y.min()
    ax[1].add_patch(plt.Rectangle((x0 * 1000, (ytop - 0.003) * 1000), b * 1000, 3, color="#2b2b2b", label="Carbon strip in routed pocket"))
    ax[1].add_patch(plt.Rectangle((x0 * 1000, ybot * 1000), b * 1000, 3, color="#2b2b2b"))
    ax[1].plot(np.r_[x, x[0]] * 1000, np.r_[y, y[0]] * 1000, color="#2f6db5", lw=1.6, label="Glass sheath + PU (LE tape)")
    ax[1].set_aspect("equal"); ax[1].set_xlabel("Chord [mm]"); ax[1].set_ylabel("[mm]")
    ax[1].legend(fontsize=7, loc="lower right"); ax[1].set_title(f"T02b  Carved hybrid section at r = {r} m (chord {c*1000:.0f} mm, wall 15 mm)", fontsize=10)
    fig.tight_layout(); fig.savefig(RES / "T02_timber_section.png", dpi=130); plt.close(fig)


if __name__ == "__main__":
    t01(); t02()
