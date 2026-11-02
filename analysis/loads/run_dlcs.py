"""Run the design load case set with the in-house time-domain simulator.

Run:  python3 run_dlcs.py          (doc 08 baseline; writes results/dlc_*.json, plots)
      python3 run_dlcs.py final    (doc 11 controller, doc 09 tower, doc 10 blade; writes results/final/)
"""
from __future__ import annotations

import json
import math
import multiprocessing as mp
import sys
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sim import Turbine, Scenario, simulate, damage_sum
from wind import turbulent_field, uniform_field, eog, sigma_ntm, sigma_etm, V_AVE

CONFIG = sys.argv[1] if len(sys.argv) > 1 else "baseline"
TB_KW = {}
if CONFIG == "final":
    # doc 11 controller (constant power, storm control, exclusion zone), doc 09 18 m tower,
    # doc 10 carbon-cap blade, +-0.3 deg pitch misalignment
    TB_KW = dict(const_power=True, storm_control=True, f_flap=13.2, m_blade=20.5, f_tower=1.21,
                 m_tower_modal=305.0, excl_rpm=(66.5, 80.5), pitch_err=(0.3, 0.0, -0.3))
OUT = Path(__file__).parent / "results" / ("" if CONFIG == "baseline" else CONFIG)
OUT.mkdir(parents=True, exist_ok=True)
T_RUN = 600.0
CHANNELS = ["thrust", "Mflap0", "Medge0", "Mres0", "Mtilt", "Myaw", "Mbase", "Qaero", "Qgen", "rpm", "pitch0", "P", "Fimb"]
FATIGUE = {"Mflap0": 10, "Medge0": 10, "thrust": 4, "Mtilt": 4, "Myaw": 4, "Mbase": 4, "Qaero": 4}
GAMMA = 1.35
V_REF = 55.0


def build_cases():
    cases = []
    # DLC 1.1 / 1.2: normal turbulence, power production (fatigue + ultimate)
    v_max = 31 if CONFIG == "final" else 25          # final: include storm control 26-30 m/s
    for V in range(4, v_max, 2):
        for seed in range(3):
            cases.append(dict(dlc="1.1", V=V, seed=seed, kind="ntm", T=T_RUN))
    # DLC 1.3: extreme turbulence
    for V in (10.5, 14, 18, 24):
        for seed in range(2):
            cases.append(dict(dlc="1.3", V=V, seed=100 + seed, kind="etm", T=T_RUN))
    # EOG at rated - 2, rated + 2, cut-out
    for V in (8.5, 12.5, 25.0):
        cases.append(dict(dlc="1.4-EOG", V=V, kind="eog", T=60))
    # DLC 1.5: operation with ice on one blade (IEC cold climate), until detection would stop it
    for V in (8, 12):
        cases.append(dict(dlc="1.5-ice", V=V, seed=200 + V, kind="ntm", T=T_RUN, ice=15.1))
    # DLC 2.1: pitch runaway of one blade
    for V in (12, 18, 24):
        cases.append(dict(dlc="2.1-runaway", V=V, seed=300 + V, kind="ntm", T=120,
                          events={"pitch_runaway_t": 30.0, "estop_t": 31.0}))
    # DLC 2.2: loss of generator torque (converter fault), at the EOG peak and in turbulence
    for V in (12.5, 25.0):
        cases.append(dict(dlc="2.2-loss-torque-EOG", V=V, kind="eog", T=60, events={"loss_of_torque_t": 25.0}))
    for V in (14, 20):
        cases.append(dict(dlc="2.2-loss-torque", V=V, seed=400 + V, kind="ntm", T=120,
                          events={"loss_of_torque_t": 30.0}))
    # DLC 2.3: emergency stop with one blade stuck
    for V in (14, 25):
        cases.append(dict(dlc="2.3-stuck-blade-stop", V=V, seed=500 + V, kind="ntm", T=120,
                          events={"estop_t": 30.0, "stuck_blade": 0}))
    # DLC 5.1: emergency stop
    for V in (10.5, 18, 25):
        cases.append(dict(dlc="5.1-estop", V=V, seed=600 + int(V), kind="ntm", T=120, events={"estop_t": 30.0}))
    # DLC 6.1 / 6.2: parked, 50-year wind (10-min V_ref, I = 0.11), all yaw errors (grid loss), cold air
    for az in (0, 30, 60, 90):
        for yaw in (0, 8, 30, 60, 90, 135, 180):
            cases.append(dict(dlc="6.x-parked-Vref", V=V_REF, seed=700 + az + yaw, kind="parked", T=300,
                              yaw=yaw, az=az, rho=1.35))
    # DLC 7.1: parked with one blade stuck at fine pitch, 1-year wind (0.8 V_ref)
    for az in (0, 60):
        for yaw in (0, 8, 30, 90):
            cases.append(dict(dlc="7.1-parked-stuck-fine", V=0.8 * V_REF, seed=800 + az + yaw, kind="parked", T=300,
                              yaw=yaw, az=az, rho=1.35, events={"stuck_blade": 0, "stuck_value": 0.0}))
    return cases


def run_case(cs):
    tb = Turbine(**TB_KW)
    V = cs["V"]
    if cs["kind"] == "ntm":
        field = turbulent_field(V, sigma_ntm(V), T=cs["T"], dt=0.05, seed=cs["seed"])
    elif cs["kind"] == "etm":
        field = turbulent_field(V, sigma_etm(V), T=cs["T"], dt=0.05, seed=cs["seed"])
    elif cs["kind"] == "eog":
        t, v, _ = eog(V, t_end=cs["T"], dt=0.05)
        field = uniform_field(t, v)
    elif cs["kind"] == "parked":
        field = turbulent_field(V, 0.11 * V, T=cs["T"], dt=0.05, seed=cs["seed"])
    sc = Scenario(name=cs["dlc"], T=cs["T"], field=field, yaw=cs.get("yaw", 0.0),
                  parked=cs["kind"] == "parked", park_azimuth=cs.get("az", 0.0),
                  events=cs.get("events", {}), ice_blade_mass=cs.get("ice", 0.0), rho=cs.get("rho"))
    r = simulate(tb, sc)
    out = dict(cs)
    out["max"] = {k: float(np.max(r[k])) for k in CHANNELS}
    out["min"] = {k: float(np.min(r[k])) for k in CHANNELS}
    out["mean"] = {k: float(np.mean(r[k])) for k in CHANNELS}
    if cs["dlc"] == "1.1":
        skip = int(30 / (r["t"][1] - r["t"][0]))       # drop start-up transient
        out["damage"] = {k: damage_sum(r[k][skip:], m) for k, m in FATIGUE.items()}
        out["duration"] = float(r["t"][-1] - r["t"][skip])
    out["trip"] = bool(np.any(r["pitch0"][int(len(r["t"]) * 0.05):] > 85)) and cs["kind"] not in ("parked",)
    if cs.get("plot"):
        np.savez_compressed(OUT / f"ts_{cs['plot']}.npz", **r)
    return out


def main():
    cases = build_cases()
    # keep a few time series for plots
    for cs in cases:
        if cs["dlc"] == "1.1" and cs["V"] == 14 and cs["seed"] == 0:
            cs["plot"] = "ntm14"
        if cs["dlc"] == "5.1-estop" and cs["V"] == 25:
            cs["plot"] = "estop25"
        if cs["dlc"] == "2.2-loss-torque-EOG" and cs["V"] == 25:
            cs["plot"] = "losstorque25"
    with mp.Pool(4) as pool:
        results = pool.map(run_case, cases, chunksize=1)
    (OUT / "dlc_raw.json").write_text(json.dumps(results, indent=1))
    summarise(results)


def summarise(results):
    # ultimate envelope per channel, with the governing case
    chans = ["thrust", "Mflap0", "Medge0", "Mres0", "Mtilt", "Myaw", "Mbase", "Qaero", "Qgen", "rpm", "Fimb"]
    env = {}
    for ch in chans:
        best = None
        for r in results:
            val = max(abs(r["max"][ch]), abs(r["min"][ch]))
            if best is None or val > best[0]:
                best = (val, r["dlc"], r["V"], r.get("yaw", 0), r.get("az", 0))
        env[ch] = dict(characteristic=round(best[0], 1),
                       design=round(best[0] * (GAMMA if ch not in ("rpm",) else 1.0), 1),
                       governing=f"DLC {best[1]} at {best[2]} m/s, yaw {best[3]}, azimuth {best[4]}")
    # per-DLC-group maxima for the key channels
    groups = {}
    for r in results:
        g = groups.setdefault(r["dlc"], {})
        for ch in chans:
            val = max(abs(r["max"][ch]), abs(r["min"][ch]))
            g[ch] = round(max(g.get(ch, 0), val), 1)
    # fatigue: lifetime damage-equivalent loads (N_eq = 1e7), Rayleigh at V_ave
    c = V_AVE / math.gamma(1.5)
    life = 20 * 8760 * 3600 * 0.97
    bins = sorted({r["V"] for r in results if r["dlc"] == "1.1"})
    dV = 2.0
    DEL = {}
    for ch, m in FATIGUE.items():
        D = 0.0
        for V in bins:
            rs = [r for r in results if r["dlc"] == "1.1" and r["V"] == V]
            dmg = np.mean([r["damage"][ch] / r["duration"] for r in rs])     # per second
            p = math.exp(-((V - dV / 2) / c) ** 2) - math.exp(-((V + dV / 2) / c) ** 2)
            D += dmg * p * life
        DEL[ch] = dict(m=m, DEL_1e7=round((D / 1e7) ** (1 / m), 1))
    # power curve check from DLC 1.1
    pc = {str(V): round(float(np.mean([r["mean"]["P"] for r in results if r["dlc"] == "1.1" and r["V"] == V])), 0) for V in bins}
    trips = [f"{r['dlc']} {r['V']} seed {r.get('seed')}" for r in results if r["dlc"] in ("1.1", "1.3") and r["trip"]]
    summary = dict(gamma_f=GAMMA, ultimate_envelope=env, per_dlc_max=groups, fatigue_DEL=DEL,
                   mean_power_W_by_wind=pc, unintended_trips_in_DLC_1_1_1_3=trips, n_runs=len(results))
    (OUT / "dlc_summary.json").write_text(json.dumps(summary, indent=2))
    plots()
    print(json.dumps(summary, indent=1))


def plots():
    for name, title in [("ntm14", "DLC 1.1, 14 m/s, normal turbulence"),
                        ("estop25", "DLC 5.1, emergency stop at 25 m/s"),
                        ("losstorque25", "DLC 2.2, loss of generator torque at EOG peak, 25 m/s")]:
        f = OUT / f"ts_{name}.npz"
        if not f.exists():
            continue
        r = np.load(f)
        fig, ax = plt.subplots(4, 1, figsize=(9, 9), sharex=True)
        ax[0].plot(r["t"], r["Vhub"]); ax[0].set_ylabel("Hub wind [m/s]")
        ax[1].plot(r["t"], r["rpm"]); ax[1].set_ylabel("Rotor [rpm]")
        a2 = ax[1].twinx(); a2.plot(r["t"], r["pitch0"], "C1", lw=0.8); a2.set_ylabel("Pitch [deg]", color="C1")
        ax[2].plot(r["t"], r["Mflap0"] / 1e3, label="Blade root flap"); ax[2].plot(r["t"], r["Medge0"] / 1e3, label="Blade root edge", lw=0.8)
        ax[2].set_ylabel("kNm"); ax[2].legend(loc="upper right")
        ax[3].plot(r["t"], r["thrust"] / 1e3, label="Rotor thrust [kN]"); ax[3].plot(r["t"], r["Mtilt"] / 1e3, label="Hub tilt [kNm]", lw=0.8)
        ax[3].legend(loc="upper right"); ax[3].set_xlabel("Time [s]")
        for a_ in ax:
            a_.grid(alpha=0.3)
        ax[0].set_title(title)
        if name == "ntm14":
            ax[0].set_xlim(100, 250)
        fig.tight_layout(); fig.savefig(OUT / f"dlc_{name}.png", dpi=110)


if __name__ == "__main__":
    main()
