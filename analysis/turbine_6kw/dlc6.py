"""S6 aeroelastic design load cases with the stall-controlled simulator sim6.py (doc 31).

Run:  python3 dlc6.py        (~15 min on 4 cores; writes results/dlc6/dlc_summary.json,
                              results/dlc6/ops_loads_6kw_18m.json, dlc_raw.json and time series)

Case set follows `run_dlcs.py final` with the 6 kW changes:
  * no pitch runaway, stuck blade or stuck-at-fine cases (there is no pitch system)
  * DLC 2.2 loss of torque and 5.1 emergency stop run three times: both stopping systems,
    braking resistor only (no_brake) and spring brake only (no_k1)
  * normal stop (converter to 30 rpm, then the brake) at 14 and 25 m/s
  * parked at V_ref with fixed blades at -2 deg for every yaw error: yaw 90 deg is the yaw-out
    storm position, yaw 0 is yaw lost with the wind straight on (broadside blades)
Tower base and mid moments and their rainflow spectra are computed in the same runs (as dlc_v5.py).
"""
from __future__ import annotations
import functools, json, math, multiprocessing as mp, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "loads"))
import sim6  # noqa: E402
import wind as W  # noqa: E402
from sim import damage_sum, rainflow  # noqa: E402

OUT = HERE / "results" / "dlc6"; OUT.mkdir(parents=True, exist_ok=True)
T_RUN = 600.0
V_REF = 55.0
GAMMA = 1.35
eog = functools.partial(W.eog, D=6.0)
turbulent_field = functools.partial(W.turbulent_field, width=6.8)

TOWER = dict(H=18.0, D_base=0.50, D_top=0.32, f1=0.87, m_modal=456.0, levels=(0.0, 0.5))   # doc 30 tower
N1 = TOWER["f1"] * 60
TB_KW = dict(f_tower=TOWER["f1"], m_tower_modal=TOWER["m_modal"],
             excl_rpm=(round(N1 / 1.1, 1), round(N1 * 1.1, 1)), pitch_err=(0.3, 0.0, -0.3))
ICE = 9.1         # kg, IEC 61400-1 ice mass on one blade, 15.1 kg (12 kW) scaled by chord x radius
RHO, CF, ALPHA = 1.225, 0.8, 0.2
CHANNELS = ["thrust", "Mflap0", "Medge0", "Mres0", "Mtilt", "Myaw", "Mbase", "Qaero", "Qgen", "Qres", "Qbrk",
            "rpm", "P", "Fimb"]
FATIGUE = {"Mflap0": 10, "Medge0": 10, "thrust": 4, "Mtilt": 4, "Myaw": 4, "Mbase": 4, "Qaero": 4}
STOP_VARIANTS = {"both": {}, "resistor-only": {"no_brake": True}, "brake-only": {"no_k1": True}}


def build_cases():
    cases = []
    for V in range(4, 31, 2):                       # DLC 1.1/1.2, includes the 25-30 m/s storm ramp
        for seed in range(3):
            cases.append(dict(dlc="1.1", V=V, seed=seed, kind="ntm", T=T_RUN))
    for V in (10.5, 14, 18, 24):                    # DLC 1.3 extreme turbulence
        for seed in range(2):
            cases.append(dict(dlc="1.3", V=V, seed=100 + seed, kind="etm", T=T_RUN))
    for V in (8.0, 12.0, 25.0):                     # EOG at rated -2, rated +2, cut-out
        cases.append(dict(dlc="1.4-EOG", V=V, kind="eog", T=60))
    for V in (8, 12):                               # DLC 1.5 ice on one blade
        cases.append(dict(dlc="1.5-ice", V=V, seed=200 + V, kind="ntm", T=T_RUN, ice=ICE))
    for name, ev in STOP_VARIANTS.items():          # DLC 2.2 loss of torque, 5.1 emergency stop
        for V in (12.0, 25.0):
            cases.append(dict(dlc=f"2.2-loss-torque-EOG/{name}", V=V, kind="eog", T=60,
                              events={"loss_of_torque_t": 25.0, **ev}))
        for V in (14, 20, 26):
            cases.append(dict(dlc=f"2.2-loss-torque/{name}", V=V, seed=400 + V, kind="ntm", T=120,
                              events={"loss_of_torque_t": 30.0, **ev}))
        for V in (10.5, 18, 25):
            cases.append(dict(dlc=f"5.1-estop/{name}", V=V, seed=600 + int(V), kind="ntm", T=120,
                              events={"estop_t": 30.0, **ev}))
    for V in (14, 25):                              # normal stop by the converter
        cases.append(dict(dlc="4.1-normal-stop", V=V, seed=650 + V, kind="ntm", T=120, events={"normal_stop_t": 30.0}))
    for az in (0, 30, 60, 90):                      # DLC 6.1/6.2 parked, 50-year wind, every yaw error
        for yaw in (0, 8, 30, 60, 90, 135, 180):
            cases.append(dict(dlc="6.x-parked-Vref", V=V_REF, seed=700 + az + yaw, kind="parked", T=300,
                              yaw=yaw, az=az, rho=1.35))
    for az in (0, 60):                              # DLC 6.4-like 1-year wind, brake hold check
        for yaw in (0, 30):
            cases.append(dict(dlc="6.4-parked-V1", V=0.8 * V_REF, seed=800 + az + yaw, kind="parked", T=300,
                              yaw=yaw, az=az, rho=1.35))
    for cs in cases:
        if cs["dlc"] == "1.1" and cs["V"] in (14, 24) and cs["seed"] == 0:
            cs["plot"] = f"ntm{cs['V']}"
        if cs["dlc"] == "2.2-loss-torque-EOG/both" and cs["V"] == 25:
            cs["plot"] = "lot25_both"
        if cs["dlc"] == "2.2-loss-torque-EOG/resistor-only" and cs["V"] == 25:
            cs["plot"] = "lot25_res"
        if cs["dlc"] == "2.2-loss-torque-EOG/brake-only" and cs["V"] == 25:
            cs["plot"] = "lot25_brk"
    return cases


def drag_coeff(z0):
    tw = TOWER
    z = np.linspace(z0, tw["H"], 200)
    D = tw["D_base"] + (tw["D_top"] - tw["D_base"]) * z / tw["H"]
    return float(np.trapezoid(0.5 * RHO * CF * D * (np.maximum(z, 1) / tw["H"]) ** (2 * ALPHA) * (z - z0), z))


def run_case(cs):
    tb = sim6.Turbine6(**TB_KW)
    V = cs["V"]
    if cs["kind"] == "ntm":
        field = turbulent_field(V, W.sigma_ntm(V), T=cs["T"], dt=0.05, seed=cs["seed"])
    elif cs["kind"] == "etm":
        field = turbulent_field(V, W.sigma_etm(V), T=cs["T"], dt=0.05, seed=cs["seed"])
    elif cs["kind"] == "eog":
        t, v, _ = eog(V, t_end=cs["T"], dt=0.05)
        field = W.uniform_field(t, v, width=6.8)
    else:
        field = turbulent_field(V, 0.11 * V, T=cs["T"], dt=0.05, seed=cs["seed"])
    sc = sim6.Scenario(name=cs["dlc"], T=cs["T"], field=field, yaw=cs.get("yaw", 0.0),
                       parked=cs["kind"] == "parked", park_azimuth=cs.get("az", 0.0),
                       events=cs.get("events", {}), ice_blade_mass=cs.get("ice", 0.0), rho=cs.get("rho"))
    r = sim6.simulate6(tb, sc)
    out = dict(cs)
    out["max"] = {k: float(np.max(r[k])) for k in CHANNELS}
    out["min"] = {k: float(np.min(r[k])) for k in CHANNELS}
    out["mean"] = {k: float(np.mean(r[k])) for k in CHANNELS}
    dtr = r["t"][1] - r["t"][0]
    skip = int(30 / dtr) if cs["dlc"] == "1.1" else 0
    if cs["dlc"] == "1.1":
        out["damage"] = {k: damage_sum(r[k][skip:], m) for k, m in FATIGUE.items()}
        out["duration"] = float(r["t"][-1] - r["t"][skip])
        out["P_std"] = float(np.std(r["P"][skip:]))
        out["rpm_mean"] = float(np.mean(r["rpm"][skip:]))
    out["trip"] = bool(np.any(r["stopped"] > 0)) and cs["kind"] != "parked"
    ev = cs.get("events", {})
    t_ev = ev.get("loss_of_torque_t", ev.get("estop_t", ev.get("normal_stop_t")))
    if t_ev is not None:
        after = r["t"] >= t_ev
        out["rpm_at_event"] = float(np.interp(t_ev, r["t"], r["rpm"]))
        out["rpm_peak_after"] = float(np.max(r["rpm"][after]))
        slow = np.where(after & (r["rpm"] < 2.0))[0]
        out["t_to_stop"] = float(r["t"][slow[0]] - t_ev) if len(slow) else None
        out["rpm_end"] = float(r["rpm"][-1])
    F_top = tb.k_tower * r["xt"]
    out["levels"] = {}
    for lv in TOWER["levels"]:
        z0 = lv * TOWER["H"]
        M = F_top * (TOWER["H"] - z0) + r["Mtilt"] + drag_coeff(z0) * r["Vhub"] ** 2
        d = dict(max=float(np.max(np.abs(M))))
        if cs["dlc"] == "1.1":
            rg, ct = rainflow(M[skip:])
            hist, _ = np.histogram(rg, bins=np.linspace(0, 100e3, 401), weights=ct)
            d["hist"] = hist.tolist(); d["duration"] = out["duration"]
        out["levels"][f"{lv:.3f}"] = d
    lo, hi = TB_KW["excl_rpm"]
    rpm = r["rpm"][skip:]
    out["time_in_zone"] = float(np.mean((rpm > lo * 1.02) & (rpm < hi * 0.98)))
    if cs.get("plot"):
        np.savez_compressed(OUT / f"ts_{cs['plot']}.npz", **r)
    return out


def rayleigh_p(V, dV=2.0):
    c = W.V_AVE / math.gamma(1.5)
    return math.exp(-((V - dV / 2) / c) ** 2) - math.exp(-((V + dV / 2) / c) ** 2)


LIFE = 20 * 8760 * 3600 * 0.97


def tower_summary(results):
    edges = np.linspace(0, 100e3, 401); mids = 0.5 * (edges[1:] + edges[:-1])
    s = dict(source="dlc6.py (S6, 18 m tower f1 0.87 Hz)", tower=TOWER, levels={}, fatigue={})
    bins = sorted({r["V"] for r in results if r["dlc"] == "1.1"})
    for lv in TOWER["levels"]:
        key = f"{lv:.3f}"
        best = max(results, key=lambda r: r["levels"][key]["max"])
        s["levels"][key] = dict(M_char_max=round(best["levels"][key]["max"]),
                                governing=f"DLC {best['dlc']} at {best['V']} m/s yaw {best.get('yaw', 0)}")
        ops = [r for r in results if not r["dlc"].startswith("6.")]
        bo = max(ops, key=lambda r: r["levels"][key]["max"])
        s["levels"][key]["M_char_max_operating"] = round(bo["levels"][key]["max"])
        s["levels"][key]["governing_operating"] = f"DLC {bo['dlc']} at {bo['V']} m/s"
        cyc = np.zeros(len(mids))
        for V in bins:
            rv = [r for r in results if r["dlc"] == "1.1" and r["V"] == V]
            per_s = np.mean([np.array(r["levels"][key]["hist"]) / r["levels"][key]["duration"] for r in rv], axis=0)
            cyc += per_s * rayleigh_p(V) * LIFE
        s["fatigue"][key] = [[float(m), float(n)] for m, n in zip(mids, cyc) if n > 0]
        s["levels"][key]["DEL_1e7_Nm_m4"] = round(float((np.sum(cyc * mids ** 4) / 1e7) ** 0.25))
    s["time_in_zone_by_wind"] = {str(V): round(float(np.mean([r["time_in_zone"] for r in results
                                                                  if r["dlc"] == "1.1" and r["V"] == V])), 3) for V in bins}
    (OUT / "ops_loads_6kw_18m.json").write_text(json.dumps(s, indent=1))
    return s


def summarise(results):
    chans = ["thrust", "Mflap0", "Medge0", "Mres0", "Mtilt", "Myaw", "Mbase", "Qaero", "Qgen", "rpm", "P", "Fimb"]
    env, env_ops = {}, {}
    for target, rs in ((env, results), (env_ops, [r for r in results if not r["dlc"].startswith("6.")])):
        for ch in chans:
            best = max(rs, key=lambda r: max(abs(r["max"][ch]), abs(r["min"][ch])))
            val = max(abs(best["max"][ch]), abs(best["min"][ch]))
            target[ch] = dict(characteristic=round(val, 1), design=round(val * (1.0 if ch in ("rpm", "P") else GAMMA), 1),
                              governing=f"DLC {best['dlc']} at {best['V']} m/s, yaw {best.get('yaw', 0)}, azimuth {best.get('az', 0)}")
    groups = {}
    for r in results:
        g = groups.setdefault(r["dlc"], {})
        for ch in chans:
            g[ch] = round(max(g.get(ch, 0), abs(r["max"][ch]), abs(r["min"][ch])), 1)
    bins = sorted({r["V"] for r in results if r["dlc"] == "1.1"})
    DEL = {}
    for ch, m in FATIGUE.items():
        D = sum(np.mean([r["damage"][ch] / r["duration"] for r in results if r["dlc"] == "1.1" and r["V"] == V])
                * rayleigh_p(V) * LIFE for V in bins)
        DEL[ch] = dict(m=m, DEL_1e7=round((D / 1e7) ** (1 / m), 1))
    pc = {}
    for V in bins:
        rv = [r for r in results if r["dlc"] == "1.1" and r["V"] == V]
        pc[str(V)] = dict(P_mean=round(float(np.mean([r["mean"]["P"] for r in rv]))),
                          P_std=round(float(np.mean([r["P_std"] for r in rv]))),
                          P_max=round(float(max(r["max"]["P"] for r in rv))),
                          rpm_mean=round(float(np.mean([r["rpm_mean"] for r in rv])), 1),
                          Qgen_max=round(float(max(r["max"]["Qgen"] for r in rv))),
                          trips=sum(r["trip"] for r in rv))
    aep = sum(pc[str(V)]["P_mean"] * rayleigh_p(V) for V in bins) * 8760 / 1e3
    stops = []
    for r in results:
        if "rpm_at_event" in r:
            stops.append(dict(case=r["dlc"], V=r["V"], rpm_event=round(r["rpm_at_event"], 1),
                              rpm_peak=round(r["rpm_peak_after"], 1),
                              t_to_stop=None if r["t_to_stop"] is None else round(r["t_to_stop"], 1),
                              rpm_end=round(r["rpm_end"], 1), Qres_max=round(r["max"]["Qres"]),
                              Mflap_max=round(max(abs(r["max"]["Mflap0"]), abs(r["min"]["Mflap0"])))))
    parked = []
    for r in results:
        if r["dlc"].startswith("6."):
            parked.append(dict(case=r["dlc"], V=round(r["V"], 1), yaw=r["yaw"], az=r["az"],
                               Mflap=round(max(abs(r["max"]["Mflap0"]), abs(r["min"]["Mflap0"]))),
                               Mres=round(r["max"]["Mres0"]), thrust=round(max(abs(r["max"]["thrust"]), abs(r["min"]["thrust"]))),
                               Mtilt=round(max(abs(r["max"]["Mtilt"]), abs(r["min"]["Mtilt"]))),
                               Myaw=round(max(abs(r["max"]["Myaw"]), abs(r["min"]["Myaw"]))),
                               Qaero=round(max(abs(r["max"]["Qaero"]), abs(r["min"]["Qaero"])))))
    trips = [f"{r['dlc']} {r['V']} seed {r.get('seed')}" for r in results if r["dlc"] in ("1.1", "1.3", "1.4-EOG", "1.5-ice") and r["trip"]]
    summary = dict(gamma_f=GAMMA, ultimate_envelope=env, operating_envelope=env_ops, per_dlc_max=groups,
                   fatigue_DEL=DEL, power_by_wind=pc, aep_rayleigh_vave10_kwh=round(aep),
                   stops=stops, parked=parked, unintended_stops=trips, n_runs=len(results))
    (OUT / "dlc_summary.json").write_text(json.dumps(summary, indent=1))
    return summary


def main():
    cases = build_cases()
    if len(sys.argv) > 1:
        cases = cases[: int(sys.argv[1])]
    with mp.Pool(4) as pool:
        results = pool.map(run_case, cases, chunksize=1)
    (OUT / "dlc_raw.json").write_text(json.dumps([{k: v for k, v in r.items() if k != "levels"} for r in results]))
    tower_summary(results)
    s = summarise(results)
    print(json.dumps({k: s[k] for k in ("operating_envelope", "fatigue_DEL", "power_by_wind", "aep_rayleigh_vave10_kwh",
                                         "unintended_stops")}, indent=1))


if __name__ == "__main__":
    main()
