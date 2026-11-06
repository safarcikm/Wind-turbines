"""Doc 31 figures from the dlc6.py results.  Run: python3 plots6.py  -> results/S01..S04 png."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
RES = HERE / "results"
D6 = RES / "dlc6"
S = json.loads((D6 / "dlc_summary.json").read_text())
REG = json.loads((RES / "regulation.json").read_text())


def s01_power():
    pc = S["power_by_wind"]
    V = np.array([float(k) for k in pc])
    Pm = np.array([pc[k]["P_mean"] for k in pc]) / 1e3
    Ps = np.array([pc[k]["P_std"] for k in pc]) / 1e3
    Px = np.array([pc[k]["P_max"] for k in pc]) / 1e3
    rpm = np.array([pc[k]["rpm_mean"] for k in pc])
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    ax[0].fill_between(V, Pm - Ps, Pm + Ps, alpha=0.25, color="C0", label="±1 std of the 0.02 s signal")
    ax[0].plot(V, Pm, "o-", color="C0", label="Simulated mean, turbulence class A")
    ax[0].plot(V, Px, "v:", color="C3", label="Peak in 3 × 10 min")
    sc = REG["stall_curve"]
    ax[0].plot([p["V"] for p in sc], [p["P"] / 1e3 for p in sc], "k--", lw=0.8, label="Steady BEM (doc 28)")
    ax[0].axhline(6.8 * 1.5, color="grey", lw=0.6); ax[0].text(4.2, 10.4, "converter torque limit × rated speed", fontsize=7, color="grey")
    ax[0].set_xlabel("10-min mean hub wind [m/s]"); ax[0].set_ylabel("Rotor shaft power [kW]")
    ax[0].set_ylim(0, 11); ax[0].grid(alpha=0.3); ax[0].legend(fontsize=7, loc="lower right")
    ax[0].set_title("S01a  Power with stall speed control")
    ax[1].plot(V, rpm, "o-", label="Simulated mean")
    ax[1].plot([p["V"] for p in sc], [p["rpm"] for p in sc], "k--", lw=0.8, label="Steady stall schedule (doc 28)")
    ax[1].axhspan(47.5, 57.4, color="C1", alpha=0.2, label="Tower 1P exclusion zone")
    ax[1].set_xlabel("10-min mean hub wind [m/s]"); ax[1].set_ylabel("Rotor speed [rpm]"); ax[1].grid(alpha=0.3)
    ax[1].legend(fontsize=7); ax[1].set_title("S01b  Rotor speed")
    fig.tight_layout(); fig.savefig(RES / "S01_power_speed.png", dpi=130); plt.close(fig)


def s02_timeseries():
    fig, ax = plt.subplots(4, 2, figsize=(12, 9), sharex="col")
    for j, (name, title) in enumerate([("ntm14", "14 m/s normal turbulence"), ("ntm24", "24 m/s normal turbulence")]):
        r = np.load(D6 / f"ts_{name}.npz")
        m = (r["t"] > 200) & (r["t"] < 320)
        t = r["t"][m]
        ax[0, j].plot(t, r["Vhub"][m]); ax[0, j].set_ylabel("Hub wind [m/s]"); ax[0, j].set_title(f"S02  {title}")
        ax[1, j].plot(t, r["rpm"][m]); ax[1, j].set_ylabel("Rotor [rpm]")
        ax[2, j].plot(t, r["P"][m] / 1e3); ax[2, j].set_ylabel("Power [kW]"); ax[2, j].axhline(6.8, color="k", lw=0.6)
        ax[3, j].plot(t, r["Mflap0"][m] / 1e3, label="flap"); ax[3, j].plot(t, r["Medge0"][m] / 1e3, lw=0.8, label="edge")
        ax[3, j].set_ylabel("Blade root [kNm]"); ax[3, j].legend(fontsize=7, loc="upper right"); ax[3, j].set_xlabel("Time [s]")
        for a in ax[:, j]:
            a.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(RES / "S02_timeseries.png", dpi=120); plt.close(fig)


def s03_stops():
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
    for name, lab, c in (("lot25_both", "resistor + brake (normal)", "C0"), ("lot25_res", "braking resistor only", "C1"),
                         ("lot25_brk", "spring brake only", "C2")):
        r = np.load(D6 / f"ts_{name}.npz")
        ax[0].plot(r["t"], r["rpm"], color=c, label=lab)
        ax[1].plot(r["t"], (r["Qres"] + r["Qbrk"]) / 1e3, color=c, label=f"{lab}: stopping torque")
        ax[1].plot(r["t"], r["Qaero"] / 1e3, color=c, ls=":", lw=0.8)
    ax[0].axhline(189, color="r", lw=0.6); ax[0].text(15.5, 182, "overspeed trip 189 rpm", fontsize=7, color="r")
    ax[0].set_xlim(15, 45); ax[1].set_xlim(15, 45)
    ax[0].set_ylabel("Rotor [rpm]"); ax[0].set_xlabel("Time [s]"); ax[0].legend(fontsize=7); ax[0].grid(alpha=0.3)
    ax[0].set_title("S03  Converter lost at the 25 m/s gust peak (t = 25 s)")
    ax[1].set_ylabel("Torque [kNm] (dotted: rotor aero torque)"); ax[1].set_xlabel("Time [s]"); ax[1].legend(fontsize=7); ax[1].grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(RES / "S03_stops.png", dpi=130); plt.close(fig)


def s04_parked():
    pk = [p for p in S["parked"] if p["case"].startswith("6.x")]
    yaws = sorted({p["yaw"] for p in pk})
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    for key, lab in (("Mflap", "blade root flap"), ("Mres", "blade root resultant"), ("Mtilt", "hub tilt"), ("Myaw", "hub yaw")):
        ax[0].plot(yaws, [max(p[key] for p in pk if p["yaw"] == y) / 1e3 for y in yaws], "o-", label=lab)
    ax[0].set_xlabel("Yaw error [deg] (90 = yawed out)"); ax[0].set_ylabel("Characteristic max [kNm]")
    ax[0].set_title("S04a  Parked at V_ref 55 m/s, I 0.11, 1.35 kg/m³"); ax[0].legend(fontsize=7); ax[0].grid(alpha=0.3)
    ax[1].plot(yaws, [max(p["Qaero"] for p in pk if p["yaw"] == y) / 1e3 for y in yaws], "o-", label="V_ref 55 m/s")
    p4 = [p for p in S["parked"] if p["case"].startswith("6.4")]
    ax[1].plot(sorted({p["yaw"] for p in p4}), [max(p["Qaero"] for p in p4 if p["yaw"] == y) / 1e3 for y in sorted({p["yaw"] for p in p4})],
               "s--", label="1-year 44 m/s")
    ax[1].axhline(1.5, color="r", lw=0.8); ax[1].text(100, 1.53, "spring brake 1.5 kNm", color="r", fontsize=7)
    ax[1].set_xlabel("Yaw error [deg]"); ax[1].set_ylabel("Peak aero torque on the parked rotor [kNm]")
    ax[1].set_title("S04b  Brake hold"); ax[1].legend(fontsize=7); ax[1].grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(RES / "S04_parked.png", dpi=130); plt.close(fig)


if __name__ == "__main__":
    s01_power(); s02_timeseries(); s03_stops(); s04_parked()
