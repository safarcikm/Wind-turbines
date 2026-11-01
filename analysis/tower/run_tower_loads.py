"""Operating tower loads with the chosen freestanding towers (aeroelastic simulation).

Run:  python3 run_tower_loads.py      (~35 min on 4 cores; writes results/ops_loads_<tower>.json)

Reruns the doc 08 power production, fault and parked-fault cases with:
- the tower first mode from tower.py (frequency and modal mass),
- the speed exclusion zone around the 1P crossing of the tower frequency,
- +-0.3 deg pitch misalignment (aerodynamic imbalance),
and adds quasi-static tower drag and the hub tilt moment to the tower
bending moment. Rainflow spectra at the base and at the section flanges are
scaled to 20 years for the fatigue check in tower.py.
"""
from __future__ import annotations

import json
import math
import multiprocessing as mp
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "loads"))
import run_dlcs  # noqa: E402
from sim import Turbine, Scenario, simulate, rainflow  # noqa: E402
from wind import turbulent_field, uniform_field, eog, sigma_ntm, sigma_etm, V_AVE  # noqa: E402

OUT = HERE / "results"
RHO, CF, ALPHA = 1.225, 0.8, 0.2

TOWERS = {
    # name: H, D_base, D_top, f1 [Hz], modal mass excl. top [kg], flange levels (fraction of H)
    "monopole_18m": dict(H=18.0, D_base=0.55, D_top=0.32, f1=1.21, m_modal=305.0, levels=(0.0, 0.5)),
    "monopole_24m": dict(H=24.0, D_base=0.60, D_top=0.32, f1=0.87, m_modal=417.0, levels=(0.0, 1 / 3, 2 / 3)),
}


def drag_coeff(tw, z0):
    """C such that M_drag(z0) = C * V_hub^2 (shear exponent ALPHA, quasi-static)."""
    z = np.linspace(z0, tw["H"], 200)
    D = tw["D_base"] + (tw["D_top"] - tw["D_base"]) * z / tw["H"]
    return float(np.trapezoid(0.5 * RHO * CF * D * (np.maximum(z, 1) / tw["H"]) ** (2 * ALPHA) * (z - z0), z))


def run_case(args):
    name, cs = args
    tw = TOWERS[name]
    n1 = tw["f1"] * 60
    tb = Turbine(hub_height=tw["H"], f_tower=tw["f1"], m_tower_modal=tw["m_modal"],
                 excl_rpm=(n1 / 1.1, n1 * 1.1), pitch_err=(0.3, 0.0, -0.3))
    V = cs["V"]
    if cs["kind"] == "ntm":
        field = turbulent_field(V, sigma_ntm(V), T=cs["T"], dt=0.05, seed=cs["seed"])
    elif cs["kind"] == "etm":
        field = turbulent_field(V, sigma_etm(V), T=cs["T"], dt=0.05, seed=cs["seed"])
    elif cs["kind"] == "eog":
        t, v, _ = eog(V, t_end=cs["T"], dt=0.05)
        field = uniform_field(t, v)
    else:
        field = turbulent_field(V, 0.11 * V, T=cs["T"], dt=0.05, seed=cs["seed"])
    sc = Scenario(name=cs["dlc"], T=cs["T"], field=field, yaw=cs.get("yaw", 0.0),
                  parked=cs["kind"] == "parked", park_azimuth=cs.get("az", 0.0),
                  events=cs.get("events", {}), ice_blade_mass=cs.get("ice", 0.0), rho=cs.get("rho"))
    r = simulate(tb, sc)
    F_top = tb.k_tower * r["xt"]                       # equivalent top force incl. inertia
    out = dict(cs, tower=name)
    skip = int(30 / (r["t"][1] - r["t"][0])) if cs["dlc"] == "1.1" else 0
    out["levels"] = {}
    for lv in tw["levels"]:
        z0 = lv * tw["H"]
        M = F_top * (tw["H"] - z0) + r["Mtilt"] + drag_coeff(tw, z0) * r["Vhub"] ** 2
        d = dict(max=float(np.max(np.abs(M))))
        if cs["dlc"] == "1.1":
            rg, ct = rainflow(M[skip:])
            hist, edges = np.histogram(rg, bins=np.linspace(0, 120e3, 241), weights=ct)
            d["hist"] = hist.tolist()
            d["duration"] = float(r["t"][-1] - r["t"][skip])
        out["levels"][f"{lv:.3f}"] = d
    rpm = r["rpm"][skip:]
    lo, hi = n1 / 1.1 * 1.02, n1 * 1.1 * 0.98
    out["time_in_zone"] = float(np.mean((rpm > lo) & (rpm < hi)))
    out["P_mean"] = float(np.mean(r["P"]))
    out["thrust_max"] = float(np.max(np.abs(r["thrust"])))
    return out


def main():
    cases = [c for c in run_dlcs.build_cases() if not c["dlc"].startswith("6.")]
    jobs = [(name, cs) for name in TOWERS for cs in cases]
    with mp.Pool(4) as pool:
        res = pool.map(run_case, jobs, chunksize=1)
    c_ray = V_AVE / math.gamma(1.5)
    life = 20 * 8760 * 3600 * 0.97
    edges = np.linspace(0, 120e3, 241)
    mids = 0.5 * (edges[1:] + edges[:-1])
    for name, tw in TOWERS.items():
        rs = [r for r in res if r["tower"] == name]
        summary = dict(source=f"run_tower_loads.py ({name})", tower=name, levels={}, fatigue={})
        for lv in tw["levels"]:
            key = f"{lv:.3f}"
            best = max(rs, key=lambda r: r["levels"][key]["max"])
            summary["levels"][key] = dict(M_char_max=best["levels"][key]["max"],
                                          governing=f"DLC {best['dlc']} at {best['V']} m/s")
            # lifetime spectrum
            cyc = np.zeros(len(mids))
            for V in sorted({r["V"] for r in rs if r["dlc"] == "1.1"}):
                rv = [r for r in rs if r["dlc"] == "1.1" and r["V"] == V]
                per_s = np.mean([np.array(r["levels"][key]["hist"]) / r["levels"][key]["duration"] for r in rv], axis=0)
                p = math.exp(-((V - 1) / c_ray) ** 2) - math.exp(-((V + 1) / c_ray) ** 2)
                cyc += per_s * p * life
            summary["fatigue"][key] = [[float(m), float(n)] for m, n in zip(mids, cyc) if n > 0]
            dels = {}
            for m in (3, 4, 5):
                dels[f"m{m}"] = round(float((np.sum(cyc * mids ** m) / 1e7) ** (1 / m)), 0)
            summary["levels"][key]["DEL_1e7_Nm"] = dels
        summary["M_base_char"] = summary["levels"]["0.000"]["M_char_max"]
        summary["F_top_equiv_char"] = summary["M_base_char"] / tw["H"]
        summary["M_top_char"] = 0.0
        summary["time_in_zone_by_wind"] = {str(V): round(float(np.mean([r["time_in_zone"] for r in rs if r["dlc"] == "1.1" and r["V"] == V])), 3)
                                           for V in sorted({r["V"] for r in rs if r["dlc"] == "1.1"})}
        summary["mean_power_by_wind"] = {str(V): round(float(np.mean([r["P_mean"] for r in rs if r["dlc"] == "1.1" and r["V"] == V])))
                                         for V in sorted({r["V"] for r in rs if r["dlc"] == "1.1"})}
        summary["per_dlc_base_max_kNm"] = {}
        for r in rs:
            k = r["dlc"]
            summary["per_dlc_base_max_kNm"][k] = round(max(summary["per_dlc_base_max_kNm"].get(k, 0), r["levels"]["0.000"]["max"] / 1e3), 1)
        (OUT / f"ops_loads_{name}.json").write_text(json.dumps(summary, indent=1))
        print(name, json.dumps({k: v for k, v in summary.items() if k != "fatigue"}, indent=1))


if __name__ == "__main__":
    main()
