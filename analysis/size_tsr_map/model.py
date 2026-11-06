"""Size x TSR decision map (doc 27): fast parametric turbine model.

Run:  python3 model.py        (needs results/rotor_tables.json from cp_tables.py; ~10 s)
Writes results/grid.csv, results/map_data.json (embedded in the interactive page),
results/calibration.json and figures.

One function, evaluate(), takes a rated power, design TSR, rotor radius and tip speed and returns
rotor speed, power curve, net annual energy, noise, storm loads, masses and a rough cost.
size() picks the radius and tip speed for a given rated power, TSR and rated wind speed.

Every model is a project model or is calibrated against the two designed turbines:
  current  Ø7.5 m, TSR 6.5, 178 rpm   (docs 03, 08-13, 23-25)
  V5       Ø8.3 m, TSR 5.0, 110 rpm   (doc 26)
See docs/27-size-tsr-decision-map.md for the assumptions behind each number.
"""
from __future__ import annotations
import csv, json, math
from pathlib import Path
import numpy as np

HERE = Path(__file__).parent
OUT = HERE / "results"
TAB = json.loads((OUT / "rotor_tables.json").read_text())
LAMS = np.array(TAB["lams"])
TSRS = np.array(TAB["tsrs"])

RHO = 1.225                      # sizing and default energy density (doc 03)
SHAFT_PER_E = 13.6 / 12.0        # shaft power per kW electrical rating (doc 03/12)
AVAIL = 0.97
V_STORM, V_STOP, STORM_FRAC = 25.0, 30.0, 0.40      # doc 11 storm ramp
RPM_MIN_FRAC = 0.25              # lowest operating speed / rated (40/178 and 30/110)
HUB_H = 18.0                     # standard tower (doc 09)
Q_PARK = 0.5 * 1.35 * 77.0 ** 2  # parked V_e50 dynamic pressure, cold air (doc 03)
VS = np.arange(0.25, 32.01, 0.25)

# Icelandic site scenarios at 18 m hub height (Weibull). Replace with site data when available.
SCENARIOS = [
    dict(key="sheltered", name="Sheltered valley / farm", v=5.0, k=1.8),
    dict(key="inland", name="Open inland lowland", v=6.0, k=1.9),
    dict(key="coastal", name="Coast / exposed lowland", v=7.0, k=2.0),
    dict(key="highland", name="Highland / headland", v=8.5, k=2.0),
]

# Rough in-house cost rates (EUR). Installed cost, excludes development, tooling, certification, margin.
COST = dict(blade=70, hub=30, gen=40, spindle=25, nacelle=25, yaw=30, tower=6, footing=450,
            pe_fixed=6000, pe_per_kw=600, control=6000, install_fixed=4000, install_per_kg=1.0,
            crf=0.0872, om_frac=0.02, isk_per_eur=145)

# Calibration constants (derived in calibrate(); fixed here so the page uses identical values)
K_PARK_M = None
K_PARK_T = None


def tables(tsr, polar="rough"):
    """Linear interpolation of the non-dimensional rotor tables in design TSR."""
    tsr = float(np.clip(tsr, TSRS[0], TSRS[-1]))
    i = int(np.clip(np.searchsorted(TSRS, tsr) - 1, 0, len(TSRS) - 2))
    w = (tsr - TSRS[i]) / (TSRS[i + 1] - TSRS[i])
    a, b = TAB["tables"][i], TAB["tables"][i + 1]
    mix = lambda x, y: (1 - w) * np.asarray(x) + w * np.asarray(y)
    cp = mix(a[polar]["cp"], b[polar]["cp"]); ct = mix(a[polar]["ct"], b[polar]["ct"])
    j = int(np.argmax(cp))
    return dict(cp=cp, ct=ct, lam_opt=float(LAMS[j]), cp_max=float(cp[j]),
                area_R2=float(mix(a["area_R2"], b["area_R2"])), cmax_R=float(mix(a["cmax_R"], b["cmax_R"])),
                park_M_R3=float(mix(a["park_M_R3"], b["park_M_R3"])), park_F_R2=float(mix(a["park_F_R2"], b["park_F_R2"])))


def chain_losses(P_e):
    """doc 12 / doc 26 loss chain, scaled with rating (s) and rated speed."""
    s = P_e / 12.0

    def net(P_shaft, rpm, rpm_r):
        pr = SHAFT_PER_E * P_e * 1000
        cu_r = 496 * s ** 0.85 * (178 / rpm_r) ** 0.725
        fe0 = 219 * s ** 0.85 * (rpm_r / 178) ** 0.35
        rot0 = 40 * s ** 0.85 * (rpm_r / 178) ** 0.976
        x = rpm / rpm_r
        p_cu = cu_r * (P_shaft / pr) ** 2 / max(x, 1e-3) ** 2
        p_gen = P_shaft - p_cu - fe0 * x ** 1.6 - rot0 * x ** 2 - 70 * s * (P_shaft / pr) ** 2
        Pn = 13e3 * s
        conv = lambda P, p0, k1, k2: p0 * s ** 0.5 + k1 * P + k2 * Pn * (P / Pn) ** 2
        p_dc = p_gen - conv(p_gen, 25, 0.004, 0.006)
        p_ac = p_dc - conv(p_dc, 30, 0.005, 0.008)
        return p_ac - 120 * s ** 0.3, p_gen / P_shaft if P_shaft > 0 else 0.0
    return net


def power_curve(P_e, tsr, R, tip, polar="rough", rho=RHO):
    t = tables(tsr, polar)
    om_cap = tip / R
    om_min = RPM_MIN_FRAC * om_cap
    pr = SHAFT_PER_E * P_e * 1000
    rpm_r = om_cap * 30 / math.pi
    net = chain_losses(P_e)
    rows = []
    for V in VS:
        om = min(t["lam_opt"] * V / R, om_cap)
        lam = om * R / V
        cp = float(np.interp(lam, LAMS, t["cp"]))
        P = min(0.5 * rho * math.pi * R ** 2 * V ** 3 * cp, pr)
        if V > V_STORM:
            P = pr * (1 - (1 - STORM_FRAC) * (V - V_STORM) / (V_STOP - V_STORM))
        if V > V_STOP or om < 0.9 * om_min:
            P = 0.0
        pn = max(net(P, om * 30 / math.pi, rpm_r)[0], 0.0) if P > 0 else 0.0
        rows.append((V, om * 30 / math.pi, P, pn))
    return np.array(rows)


def aep(curve, v_mean, k, avail=AVAIL):
    V, Pn = curve[:, 0], curve[:, 3]
    c = v_mean / math.gamma(1 + 1 / k)
    f = (k / c) * (V / c) ** (k - 1) * np.exp(-(V / c) ** k)
    return float(np.sum(Pn * f) * (V[1] - V[0]) * 8760 * avail / 1000)   # kWh


def noise(D, tip8, tip_r):
    """Hau's empirical sound power: LwA = 50 log10(v_tip) + 10 log10(D) - 4 (+-4 dB absolute)."""
    lw = lambda v: 50 * math.log10(v) + 10 * math.log10(D) - 4
    return lw(tip8), lw(tip_r)


def spl(lw, d, h=HUB_H, alpha=0.003):
    s = math.hypot(d, h)
    return lw - 10 * math.log10(2 * math.pi * s * s) - alpha * s


def dist_for(lw, target):
    lo, hi = 0.0, 5000.0
    if spl(lw, 0.0) <= target:
        return 0.0
    for _ in range(50):
        m = 0.5 * (lo + hi)
        lo, hi = (m, hi) if spl(lw, m) > target else (lo, m)
    return 0.5 * (lo + hi)


def evaluate(P_e, tsr, R, tip, rated_wind=None, polar="rough", rho=RHO, scenarios=SCENARIOS):
    t = tables(tsr, polar)
    D = 2 * R
    pr = SHAFT_PER_E * P_e * 1000
    om = tip / R
    rpm = om * 30 / math.pi
    curve = power_curve(P_e, tsr, R, tip, polar, rho)
    # rated wind (continuous): first speed where shaft power reaches the rating
    Vr = rated_wind
    if Vr is None:
        idx = np.where(curve[:, 2] >= pr - 1)[0]
        Vr = float(curve[idx[0], 0]) if len(idx) else float("nan")
        if len(idx) and idx[0] > 0:   # interpolate inside the bin
            V0, P0 = curve[idx[0] - 1, 0], curve[idx[0] - 1, 2]
            V1 = curve[idx[0], 0]
            P1 = 0.5 * rho * math.pi * R ** 2 * V1 ** 3 * float(np.interp(min(t["lam_opt"], om * R / V1), LAMS, t["cp"]))
            Vr = float(V0 + (V1 - V0) * (pr - P0) / max(P1 - P0, 1e-9))
    tip8 = min(t["lam_opt"] * 8.0, tip)
    lw8, lwr = noise(D, tip8, tip)
    # loads, calibrated to SLM H (doc 08 / doc 26)
    M_park = K_PARK_M * t["park_M_R3"] * Q_PARK * R ** 3 / 1000      # kNm, design, blade root
    T_park = K_PARK_T * 3 * t["park_F_R2"] * Q_PARK * R ** 2 / 1000  # kN, design, shaft thrust
    Q_r = pr / om
    ct_r = float(np.interp(tip / Vr, LAMS, t["ct"])) if Vr == Vr else float("nan")
    T_op = 0.5 * RHO * math.pi * R ** 2 * Vr ** 2 * ct_r / 1000
    area = t["area_R2"] * R ** 2
    # masses (kg), linear / power laws through the two designed turbines; fixed parts scale with sqrt(kW/12)
    sc = (P_e / 12.0) ** 0.5
    m_blade = 20.5 * (M_park / 26.0) ** 0.86
    m_hub = 138.5 * sc + 3.865 * M_park
    m_gen = 276 * (Q_r / 730.0) ** 0.5
    m_spindle = 46.6 * sc + 0.40 * M_park
    m_nac = 336 * sc
    m_yaw = 134 * (M_park / 26.0) ** 0.3
    m_head = 3 * m_blade + m_hub + m_gen + m_spindle + m_nac + m_yaw
    F_r = 0.623 * (area / 0.849) + 0.377 * sc
    Mb_r = 0.448 * F_r + 0.552 * m_head / 1103.0
    m_tower = 1940 * Mb_r ** 0.96
    v_footing = 11.9 * Mb_r ** 0.59
    c = COST
    parts = dict(blades=3 * m_blade * c["blade"], hub_pitch=m_hub * c["hub"], generator=m_gen * c["gen"],
                 spindle=m_spindle * c["spindle"], nacelle=m_nac * c["nacelle"], yaw=m_yaw * c["yaw"],
                 electronics=c["pe_fixed"] + c["pe_per_kw"] * P_e, control=c["control"],
                 tower=m_tower * c["tower"], footing=v_footing * c["footing"],
                 install=c["install_fixed"] + c["install_per_kg"] * (m_head + m_tower))
    capex = sum(parts.values())
    res = dict(P_e=P_e, tsr=tsr, D=D, R=R, tip=tip, rpm=rpm, rated_wind=Vr, spec_power=pr / 1.1333 / (math.pi * R * R),
               cp_max=t["cp_max"], lam_opt=t["lam_opt"], cmax=t["cmax_R"] * R, blade_area=area,
               P_net_rated=chain_losses(P_e)(pr, rpm, rpm)[0] / 1000, eta_gen=chain_losses(P_e)(pr, rpm, rpm)[1],
               tip8=tip8, Lw8=lw8, Lw_rated=lwr,
               Lp8={str(d): spl(lw8, d) for d in (50, 100, 200)},
               d40=dist_for(lw8, 40.0), d35=dist_for(lw8, 35.0),
               M_park=M_park, T_park=T_park, Q_rated=Q_r, T_op=T_op,
               m_blade=m_blade, m_hub=m_hub, m_gen=m_gen, m_head=m_head, m_tower=m_tower, v_footing=v_footing,
               cost_parts=parts, capex=capex, aep={}, lcoe={}, cf={})
    for s in scenarios:
        e = aep(curve, s["v"], s["k"])
        res["aep"][s["key"]] = e
        res["cf"][s["key"]] = e / (P_e * 8760)
        res["lcoe"][s["key"]] = capex * (c["crf"] + c["om_frac"]) / e
    return res


def size(P_e, tsr, Vr, polar="rough"):
    """Radius and tip speed for rated power at rated wind Vr, with tip speed = TSR x Vr
    (the rotor reaches rated power at its design TSR and maximum rpm)."""
    t = tables(tsr, polar)
    cp_r = float(np.interp(tsr, LAMS, t["cp"]))
    pr = SHAFT_PER_E * P_e * 1000
    R = math.sqrt(pr / (0.5 * RHO * math.pi * Vr ** 3 * cp_r))
    return R, tsr * Vr


def calibrate():
    """Fix the parked-load constants against SLM H of the two designs and check the energy engine."""
    global K_PARK_M, K_PARK_T
    designs = dict(current=dict(R=3.75, tsr=6.5, tip=70.0, M=26.0, T=41.6, aep6=30418, aep7=40813, aep5=19703, aep8=50065),
                   V5=dict(R=4.15, tsr=5.0, tip=110 * math.pi / 30 * 4.15, M=58.6, T=84.7, aep6=34619, aep7=45155, aep5=23241, aep8=54224))
    km, kt = [], []
    for d in designs.values():
        t = tables(d["tsr"])
        km.append(d["M"] * 1000 / (t["park_M_R3"] * Q_PARK * d["R"] ** 3))
        kt.append(d["T"] * 1000 / (3 * t["park_F_R2"] * Q_PARK * d["R"] ** 2))
    K_PARK_M, K_PARK_T = float(np.sqrt(km[0] * km[1])), float(np.sqrt(kt[0] * kt[1]))
    rayleigh = [dict(key=f"r{v:g}", name="", v=v, k=2.0) for v in (5, 6, 7, 8)]
    out = dict(K_PARK_M=K_PARK_M, K_PARK_T=K_PARK_T, designs={})
    for name, d in designs.items():
        r = evaluate(12, d["tsr"], d["R"], d["tip"], scenarios=rayleigh)
        Rs, tips = size(12, d["tsr"], r["rated_wind"])
        out["designs"][name] = dict(
            rpm=round(r["rpm"], 1), rated_wind_model=round(r["rated_wind"], 2),
            aep_model={k: round(v) for k, v in r["aep"].items()},
            aep_doc26={f"r{v}": d[f"aep{v}"] for v in (5, 6, 7, 8)},
            aep_err_pct={f"r{v}": round(100 * (r["aep"][f"r{v}"] / d[f"aep{v}"] - 1), 1) for v in (5, 6, 7, 8)},
            M_park=round(r["M_park"], 1), M_park_doc=d["M"], T_park=round(r["T_park"], 1), T_park_doc=d["T"],
            m_head=round(r["m_head"]), m_tower=round(r["m_tower"]), v_footing=round(r["v_footing"], 1),
            m_blade=round(r["m_blade"], 1), m_hub=round(r["m_hub"]), m_gen=round(r["m_gen"]),
            Lw8=round(r["Lw8"], 1), Lp60=round(spl(r["Lw8"], 60), 1),
            sizing_rule_D=round(2 * Rs, 2), sizing_rule_rpm=round(tips / Rs * 30 / math.pi, 1),
            capex_eur=round(r["capex"]))
    return out


def named_designs():
    """The two designed turbines plus the doc 26 middle suggestion."""
    return [
        dict(key="current", label="Current Ø7.5 m, TSR 6.5, 178 rpm", P_e=12, tsr=6.5, R=3.75, tip=70.0),
        dict(key="M8", label="Middle Ø8.0 m, TSR 5.5, 135 rpm (suggested)", P_e=12, tsr=5.5, R=4.0, tip=135 * math.pi / 30 * 4.0),
        dict(key="V5", label="V5 Ø8.3 m, TSR 5, 110 rpm", P_e=12, tsr=5.0, R=4.15, tip=110 * math.pi / 30 * 4.15),
    ]


def slim(r):
    keys = ["P_e", "tsr", "D", "tip", "rpm", "rated_wind", "cmax", "blade_area", "P_net_rated", "eta_gen", "tip8",
            "Lw8", "Lw_rated", "d40", "d35", "M_park", "T_park", "Q_rated", "T_op", "m_blade", "m_hub", "m_gen",
            "m_head", "m_tower", "v_footing", "capex", "cp_max", "spec_power"]
    o = {k: round(float(r[k]), 3) for k in keys}
    o["Lp8"] = {k: round(v, 1) for k, v in r["Lp8"].items()}
    o["aep"] = {k: round(v) for k, v in r["aep"].items()}
    o["parts"] = {k: round(v) for k, v in r["cost_parts"].items()}
    return o


def main():
    cal = calibrate()
    (OUT / "calibration.json").write_text(json.dumps(cal, indent=1))
    print(json.dumps(cal, indent=1))
    kws = list(range(4, 21, 2))
    tsrs = [4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0]
    vrs = [9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0]
    grid = []
    for vr in vrs:
        for kw in kws:
            for tsr in tsrs:
                R, tip = size(kw, tsr, vr)
                r = evaluate(kw, tsr, R, tip, rated_wind=vr)
                grid.append(slim(r))
    named = []
    for d in named_designs():
        r = evaluate(d["P_e"], d["tsr"], d["R"], d["tip"])
        o = slim(r); o.update(key=d["key"], label=d["label"]); named.append(o)
    with open(OUT / "grid.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        hdr = ["rated_wind", "kW", "TSR", "D_m", "rpm", "tip_ms", "tip_8ms", "LwA_8ms", "Lp50", "Lp100", "Lp200",
               "dist_40dBA_m"] + [f"AEP_{s['key']}_kWh" for s in SCENARIOS] + \
              ["blade_root_park_kNm", "park_thrust_kN", "torque_Nm", "blade_kg", "head_kg", "tower_kg",
               "capex_EUR", "capex_per_kW", "cost_index"] + [f"EUR_per_MWh_{s['key']}" for s in SCENARIOS]
        w.writerow(hdr)
        base = named[0]["capex"]
        for g in grid:
            w.writerow([g["rated_wind"], int(g["P_e"]), g["tsr"], round(g["D"], 2), round(g["rpm"]), round(g["tip"], 1),
                        round(g["tip8"], 1), round(g["Lw8"], 1), g["Lp8"]["50"], g["Lp8"]["100"], g["Lp8"]["200"],
                        round(g["d40"])] + [g["aep"][s["key"]] for s in SCENARIOS] +
                       [round(g["M_park"], 1), round(g["T_park"], 1), round(g["Q_rated"]), round(g["m_blade"], 1),
                        round(g["m_head"]), round(g["m_tower"]), round(g["capex"]), round(g["capex"] / g["P_e"]),
                        round(100 * g["capex"] / base)] +
                       [round(1000 * g["capex"] * (COST["crf"] + COST["om_frac"]) / g["aep"][s["key"]]) for s in SCENARIOS])
    data = dict(generated="2026-11-06", scenarios=SCENARIOS, cost=COST, kws=kws, tsrs=tsrs, vrs=vrs,
                grid=grid, named=named, calibration=cal,
                consts=dict(K_PARK_M=K_PARK_M, K_PARK_T=K_PARK_T, Q_PARK=Q_PARK, RHO=RHO, HUB_H=HUB_H),
                tables=dict(lams=TAB["lams"], tsrs=TAB["tsrs"],
                            t=[dict(tsr=t["tsr"], area_R2=t["area_R2"], cmax_R=t["cmax_R"], park_M_R3=t["park_M_R3"],
                                    park_F_R2=t["park_F_R2"], cp=t["rough"]["cp"], ct=t["rough"]["ct"],
                                    cp_clean=t["clean"]["cp"]) for t in TAB["tables"]]))
    (OUT / "map_data.json").write_text(json.dumps(data, separators=(",", ":")))
    for n in named:
        print(n["label"], round(n["D"], 2), round(n["rpm"]), n["aep"], round(n["capex"]), round(n["Lw8"], 1), round(n["M_park"], 1), round(n["m_head"]))


if __name__ == "__main__":
    main()
