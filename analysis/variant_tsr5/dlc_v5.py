"""V5 aeroelastic design load cases with the in-house simulator (doc 26 §4).

Run:  python3 dlc_v5.py     (~40 min on 4 cores; writes results/dlc_v5/dlc_summary.json and
                             results/dlc_v5/ops_loads_v5_18m.json for the tower sizing)

Same case set as `run_dlcs.py final` (doc 11 controller: constant power, storm ramp
25-30 m/s, speed exclusion zone, +-0.3 deg pitch misalignment, parked Vref cases, stuck
blade), with the V5 rotor and head mass. Tower base moment and rainflow spectra are
computed in the same runs as in run_tower_loads.py. Nothing in sim.py is changed: the
blade shape is switched to TSR 5 by replacing sim.Blade.
"""
from __future__ import annotations
import functools, json, math, multiprocessing as mp, sys
from pathlib import Path
import numpy as np
import common as C

sys.argv = [sys.argv[0], "final"]
import sim  # noqa: E402
import run_dlcs as RD  # noqa: E402
import wind as W  # noqa: E402

sim.Blade = C.Blade5
OUT = C.OUT / "dlc_v5"; OUT.mkdir(parents=True, exist_ok=True)
RD.OUT = OUT
RD.eog = functools.partial(W.eog, D=2 * C.R)
RD.turbulent_field = functools.partial(W.turbulent_field, width=9.2)

TOWER = dict(H=18.0, D_base=0.50, D_top=0.42, f1=0.97, m_modal=440.0, levels=(0.0, 0.5))   # tower_v5.py result, 2nd pass
N1 = TOWER["f1"] * 60
RD.TB_KW = dict(R=C.R, m_blade=42.0, f_flap=13.9, J_rotor=480.0, m_top=1300.0,
                rpm_rated=C.RPM, rpm_trip=C.RPM_TRIP, pitch_wn=4.0,
                k_overspeed=1050.0,     # 400 Nm/(rad/s) scaled by torque and speed ratio; speed loop 4 rad/s (3 tripped in DLC 1.1 at 24-26 m/s)
                const_power=True, storm_control=True, f_tower=TOWER["f1"], m_tower_modal=TOWER["m_modal"],
                excl_rpm=(round(N1 / 1.1, 1), round(N1 * 1.1, 1)), pitch_err=(0.3, 0.0, -0.3))
ICE_V5 = 34.0     # kg, IEC 61400-1 ice mass scales with chord and radius: 15.1 x 2.25
RHO, CF, ALPHA = 1.225, 0.8, 0.2


def drag_coeff(z0):
    tw = TOWER
    z = np.linspace(z0, tw["H"], 200)
    D = tw["D_base"] + (tw["D_top"] - tw["D_base"]) * z / tw["H"]
    return float(np.trapezoid(0.5 * RHO * CF * D * (np.maximum(z, 1) / tw["H"]) ** (2 * ALPHA) * (z - z0), z))


def run_case(cs):
    tb = sim.Turbine(**RD.TB_KW)
    V = cs["V"]
    if cs["kind"] == "ntm":
        field = RD.turbulent_field(V, W.sigma_ntm(V), T=cs["T"], dt=0.05, seed=cs["seed"])
    elif cs["kind"] == "etm":
        field = RD.turbulent_field(V, W.sigma_etm(V), T=cs["T"], dt=0.05, seed=cs["seed"])
    elif cs["kind"] == "eog":
        t, v, _ = RD.eog(V, t_end=cs["T"], dt=0.05)
        field = W.uniform_field(t, v)
    else:
        field = RD.turbulent_field(V, 0.11 * V, T=cs["T"], dt=0.05, seed=cs["seed"])
    sc = sim.Scenario(name=cs["dlc"], T=cs["T"], field=field, yaw=cs.get("yaw", 0.0),
                      parked=cs["kind"] == "parked", park_azimuth=cs.get("az", 0.0),
                      events=cs.get("events", {}), ice_blade_mass=cs.get("ice", 0.0), rho=cs.get("rho"))
    r = sim.simulate(tb, sc)
    out = dict(cs)
    out["max"] = {k: float(np.max(r[k])) for k in RD.CHANNELS}
    out["min"] = {k: float(np.min(r[k])) for k in RD.CHANNELS}
    out["mean"] = {k: float(np.mean(r[k])) for k in RD.CHANNELS}
    skip = int(30 / (r["t"][1] - r["t"][0])) if cs["dlc"] == "1.1" else 0
    if cs["dlc"] == "1.1":
        out["damage"] = {k: sim.damage_sum(r[k][skip:], m) for k, m in RD.FATIGUE.items()}
        out["duration"] = float(r["t"][-1] - r["t"][skip])
    out["trip"] = bool(np.any(r["pitch0"][int(len(r["t"]) * 0.05):] > 85)) and cs["kind"] != "parked"
    F_top = tb.k_tower * r["xt"]
    out["levels"] = {}
    for lv in TOWER["levels"]:
        z0 = lv * TOWER["H"]
        M = F_top * (TOWER["H"] - z0) + r["Mtilt"] + drag_coeff(z0) * r["Vhub"] ** 2
        d = dict(max=float(np.max(np.abs(M))))
        if cs["dlc"] == "1.1":
            rg, ct = sim.rainflow(M[skip:])
            hist, _ = np.histogram(rg, bins=np.linspace(0, 200e3, 401), weights=ct)
            d["hist"] = hist.tolist(); d["duration"] = out["duration"]
        out["levels"][f"{lv:.3f}"] = d
    rpm = r["rpm"][skip:]
    lo, hi = RD.TB_KW["excl_rpm"]
    out["time_in_zone"] = float(np.mean((rpm > lo * 1.02) & (rpm < hi * 0.98)))
    return out


def tower_summary(results):
    c_ray = W.V_AVE / math.gamma(1.5)
    life = 20 * 8760 * 3600 * 0.97
    edges = np.linspace(0, 200e3, 401); mids = 0.5 * (edges[1:] + edges[:-1])
    rs = [r for r in results if not r["dlc"].startswith("6.")]
    s = dict(source="dlc_v5.py (V5, 18 m tower f1 0.97 Hz)", tower=TOWER, levels={}, fatigue={})
    for lv in TOWER["levels"]:
        key = f"{lv:.3f}"
        best = max(rs, key=lambda r: r["levels"][key]["max"])
        s["levels"][key] = dict(M_char_max=best["levels"][key]["max"], governing=f"DLC {best['dlc']} at {best['V']} m/s")
        cyc = np.zeros(len(mids))
        for V in sorted({r["V"] for r in rs if r["dlc"] == "1.1"}):
            rv = [r for r in rs if r["dlc"] == "1.1" and r["V"] == V]
            per_s = np.mean([np.array(r["levels"][key]["hist"]) / r["levels"][key]["duration"] for r in rv], axis=0)
            p = math.exp(-((V - 1) / c_ray) ** 2) - math.exp(-((V + 1) / c_ray) ** 2)
            cyc += per_s * p * life
        s["fatigue"][key] = [[float(m), float(n)] for m, n in zip(mids, cyc) if n > 0]
        s["levels"][key]["DEL_1e7_Nm_m4"] = round(float((np.sum(cyc * mids ** 4) / 1e7) ** 0.25))
    s["M_base_char"] = s["levels"]["0.000"]["M_char_max"]
    s["F_top_equiv_char"] = s["M_base_char"] / TOWER["H"]
    s["M_top_char"] = 0.0
    s["time_in_zone_by_wind"] = {str(V): round(float(np.mean([r["time_in_zone"] for r in rs if r["dlc"] == "1.1" and r["V"] == V])), 3)
                                 for V in sorted({r["V"] for r in rs if r["dlc"] == "1.1"})}
    (OUT / "ops_loads_v5_18m.json").write_text(json.dumps(s, indent=1))


def main():
    cases = RD.build_cases()
    for cs in cases:
        if "ice" in cs:
            cs["ice"] = ICE_V5
        if cs["dlc"] == "1.1" and cs["V"] == 14 and cs["seed"] == 0:
            cs["plot"] = "ntm14"
    if len(sys.argv) > 2:
        cases = cases[: int(sys.argv[2])]
    with mp.Pool(4) as pool:
        results = pool.map(run_case, cases, chunksize=1)
    (OUT / "dlc_raw.json").write_text(json.dumps([{k: v for k, v in r.items() if k != "levels"} for r in results]))
    tower_summary(results)
    RD.plots = lambda: None
    RD.summarise(results)


if __name__ == "__main__":
    main()
