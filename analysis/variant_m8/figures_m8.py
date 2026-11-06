"""Comparison figures for doc 35: blade planforms, power curves, energy, loads.

Run:  python3 figures_m8.py   (after the other m8 scripts) -> results/F01..F04 png
"""
from __future__ import annotations
import csv, json, math
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import common as C
from bem import Blade

OUT = C.OUT
plt.rcParams.update({"font.size": 9})
CUR, NEW = "#7a8794", "#1f6fb2"


def planforms():
    fig, ax = plt.subplots(figsize=(9, 3.2))
    for bl, col, lab in ((Blade(R=3.75, tsr_design=6.5, cl_design=1.0, n=60), CUR, "Current: Ø7.5 m, TSR 6.5, 178 rpm"),
                         (C.blade_shape(n=60), NEW, "M8: Ø8.0 m, TSR 5.5, 131 rpm")):
        r, c = bl.r, bl.chord
        le, te = 0.30 * c, -0.70 * c
        ax.fill_between(r, te, le, color=col, alpha=0.35, lw=0)
        ax.plot(r, le, col, lw=1.2); ax.plot(r, te, col, lw=1.2, label=lab)
        ax.plot([0.40, 0.40], [-0.7 * c[0], 0.3 * c[0]], col, lw=1.2)
    ax.axvline(0, color="k", lw=0.6)
    ax.set_aspect("equal"); ax.set_xlim(-0.1, 4.2); ax.set_xlabel("Radius from rotor axis [m]"); ax.set_ylabel("[m]")
    ax.set_title("Blade planforms to scale (pitch axis at 30 % chord)")
    ax.legend(loc="lower right", fontsize=8); ax.grid(alpha=0.25)
    fig.tight_layout(); fig.savefig(OUT / "F01-planforms.png", dpi=150); plt.close(fig)


def power_and_energy():
    p = json.loads((OUT / "power_m8.json").read_text())
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
    for name, col, lab in (("current_D7.5", CUR, "Current Ø7.5 m"), ("M8_D8.0", NEW, "M8 Ø8.0 m")):
        d = p["power_curve_net_kW"][name]
        V = [float(k) for k in d]; P = list(d.values())
        ax[0].plot(V, P, "o-", ms=3, color=col, label=lab)
    ax[0].set_xlabel("Hub wind speed [m/s]"); ax[0].set_ylabel("Net power [kW]"); ax[0].set_xlim(0, 26)
    ax[0].set_title("Net power curve (weathered blades)"); ax[0].grid(alpha=0.3); ax[0].legend()
    a, b = p["aep_net_kWh"]["current_D7.5_rough"], p["aep_net_kWh"]["M8_D8.0_rough"]
    ks = ["5.0", "6.0", "7.0", "8.0"]
    x = np.arange(len(ks))
    ax[1].bar(x - 0.2, [a[k] / 1e3 for k in ks], 0.4, color=CUR, label="Current Ø7.5 m")
    ax[1].bar(x + 0.2, [b[k] / 1e3 for k in ks], 0.4, color=NEW, label="M8 Ø8.0 m")
    for i, k in enumerate(ks):
        ax[1].text(i + 0.2, b[k] / 1e3 + 0.8, f"+{100 * (b[k] / a[k] - 1):.0f} %", ha="center", fontsize=8)
    ax[1].set_xticks(x, [f"{float(k):.0f} m/s" for k in ks]); ax[1].set_xlabel("Annual mean wind at hub")
    ax[1].set_ylabel("MWh per year (net)"); ax[1].set_title("Yearly energy"); ax[1].legend(); ax[1].grid(alpha=0.3, axis="y")
    fig.tight_layout(); fig.savefig(OUT / "F02-power-energy.png", dpi=150); plt.close(fig)


def loads():
    s8 = json.loads((OUT / "slm_m8.json").read_text())["ultimate_design_values_gamma_3_kN_kNm"]
    sc = json.loads((C.ROOT / "loads" / "results" / "slm.json").read_text())["ultimate_design_values_gamma_3_kN_kNm"]
    d8 = json.loads((OUT / "dlc_m8" / "dlc_summary.json").read_text())["ultimate_envelope"]
    dc = json.loads((C.ROOT / "loads" / "results" / "final" / "dlc_summary.json").read_text())["ultimate_envelope"]
    items = [("Blade root, parked storm\n(SLM H)", sc["H_parked"]["M_yB"], s8["H_parked"]["M_yB"]),
             ("Rotor thrust, parked\n(SLM H)", sc["H_parked"]["F_x_shaft"], s8["H_parked"]["F_x_shaft"]),
             ("Blade root, simulated\nenvelope", dc["Mres0"]["design"] / 1e3, d8["Mres0"]["design"] / 1e3),
             ("Rotor thrust, simulated\nenvelope", dc["thrust"]["design"] / 1e3, d8["thrust"]["design"] / 1e3),
             ("Hub tilt, simulated", dc["Mtilt"]["design"] / 1e3, d8["Mtilt"]["design"] / 1e3),
             ("Yaw moment, simulated", dc["Myaw"]["design"] / 1e3, d8["Myaw"]["design"] / 1e3),
             ("Rated torque", 0.730, C.Q_RATED / 1e3)]
    fig, ax = plt.subplots(figsize=(9, 3.8))
    y = np.arange(len(items))[::-1]
    r = [b / a for _, a, b in items]
    ax.barh(y, r, color=[NEW if v > 1 else "#3a9d8d" for v in r])
    ax.axvline(1, color="k", lw=0.8)
    for yi, v, (_, a, b) in zip(y, r, items):
        ax.text(v + 0.03, yi, f"×{v:.2f}  ({a:.1f} → {b:.1f})", va="center", fontsize=8)
    ax.set_yticks(y, [i[0] for i in items]); ax.set_xlim(0, 2.6)
    ax.set_xlabel("M8 / current (design values, kN or kNm)"); ax.set_title("What the Ø8.0 m rotor does to the loads")
    ax.grid(alpha=0.3, axis="x")
    fig.tight_layout(); fig.savefig(OUT / "F03-loads.png", dpi=150); plt.close(fig)


def generator():
    fig, ax = plt.subplots(figsize=(8, 2.8))
    for i, (n, L, col) in enumerate((("Rev C: 5 rows, stack 74 mm, 730 Nm at 178 rpm", 74, CUR),
                                     ("M8: 7 rows, stack 104 mm, 991 Nm at 131 rpm", 106, NEW))):
        y0 = 1.2 - i * 1.3
        for k in range(L // 15):
            ax.add_patch(plt.Rectangle((k * 15.2, y0), 15, 0.8, color=col, alpha=0.8))
        ax.text(0, y0 + 0.95, n, fontsize=8)
    ax.set_xlim(-5, 140); ax.set_ylim(-0.4, 2.4); ax.set_yticks([]); ax.set_xlabel("Axial position along the stack [mm]")
    ax.set_title("Magnet rows per pole (N45SH 30 × 15 × 12 blocks, drum Ø646 unchanged)")
    fig.tight_layout(); fig.savefig(OUT / "F04-generator-rows.png", dpi=150); plt.close(fig)


if __name__ == "__main__":
    planforms(); power_and_energy(); generator()
    if (OUT / "dlc_m8" / "dlc_summary.json").exists():
        loads()
