"""L7 (copied from tower8_m8.py) on an 8 m hub-height tower (doc 35 §12): tower, footing, frequencies, energy, turbulence, noise.

Run:  python3 tower8_l7.py   (after the other m8 scripts; ~3 min) -> results/tower8_l7.json, results/F05-tower8.png

Same method as doc 34 (analysis/turbine_6kw/tower8.py), with the M8 inputs:
  * hub height 8.0 m: 0.20 m pedestal, tube to the top flange, then 0.36 m yaw stack + 0.57 m to the rotor centre
    (doc 25 / doc 34 geometry), so the tube is 6.87 m;
  * M8 head 1,280 kg (hub_yaw_l7.py), M8 SLM loads (structure_l7.py), M8 operating loads from dlc_l7.py
    (18 m simulation, top force applied at the rotor centre), fatigue spectra scaled for the shorter lever
    and the higher turbulence near the ground;
  * class S extreme winds kept AT HUB HEIGHT (IEC 61400-2): no credit for the lower wind at 8 m.
Frequency strategies:
  soft-stiff  f1 between 1.1 x 1P(35 rpm) and 3P(35 rpm)/1.1 = 0.64-1.59 Hz (as the 18 m tower)
  stiff       f1 above 1.15 x 1P(131 rpm) = 2.51 Hz and below 3P(131 rpm)/1.1 = 5.95 Hz; 3P crosses f1 at low speed
Energy: M8 net power curve (power_l7.py, weathered blades), doc 27 site scenarios defined at 18 m,
log-law shear to 8 m with the site roughness (doc 34 values).
"""
from __future__ import annotations
import json, math
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import common as C
import tower as T
import power_l7 as PW
from bem import ROUGH

M8OUT = C.HERE.parent / "variant_m8" / "results"
_hy = C.OUT / "hub_yaw_l7.json"
HY = json.loads(_hy.read_text()) if _hy.exists() else None
SLM = json.loads((C.OUT / "slm_l7.json").read_text())
# L7: no 18 m load run. First-pass 8 m operating loads come from the M8 18 m run (same rotor diameter, steady thrust
# 2.23 vs 2.24 kN); the final tower uses the L7 8 m run (dlc8_l7.py) directly, as doc 37 did.
OPS18 = json.loads((M8OUT / "dlc_m8" / "ops_loads_m8_18m.json").read_text())
T18 = json.loads((M8OUT / "tower_m8.json").read_text())["M8"]     # M8 18 m tower, for reference only

HUB_H = 8.0
Z_PED = 0.20
TOP_TO_RC = 0.36 + 0.57
L_TUBE = HUB_H - Z_PED - TOP_TO_RC          # 6.87 m
# L7 head: hub_yaw_l7 result + the 82 kg that the M8 CAD model (cad/turbine_m8, doc 37) added over the M8 analysis
# total (cover, frame, adapter, lock holder...: 1,362 vs 1,280 kg). First pass (no hub_yaw_l7 yet): 1,160 kg estimate.
CAD_EXTRA = 1362.4 - 1280.0
HEAD = float(HY["yaw"]["m_above_tower_flange_kg"]) + CAD_EXTRA if HY else 1160.0
AREA = 0.842
SITES = [dict(key="sheltered", name="Sheltered valley / farm", v=5.0, k=1.8, z0=0.25),
         dict(key="inland", name="Open inland lowland", v=6.0, k=1.9, z0=0.05),
         dict(key="coastal", name="Coast / exposed lowland", v=7.0, k=2.0, z0=0.01),
         dict(key="highland", name="Highland / headland", v=8.5, k=2.0, z0=0.03)]


def setup(window):
    T.M_TOP = HEAD
    T.J_TOP = 300.0 * HEAD / 480.0 * 1.15
    T.D_TOP = 0.40
    T.F_SIDE_VE50 = 8.0e3 * AREA / C.BLADE_AREA_CUR + 5.8e3 * 1.06
    T.M_TOP_GRAV = HEAD * C.OVERHANG * 0.45 * T.G
    T.SLM_FX_DESIGN = SLM["ultimate_design_values_gamma_3_kN_kNm"]["H_parked"]["F_x_shaft"] * 1e3
    T.SLM_FX_CHAR = T.SLM_FX_DESIGN / 3
    T.F_MIN_SOFT, T.F_MAX_SOFT = window
    T.fe_assemble.__defaults__ = (T.M_TOP, T.J_TOP, False, None)
    T.fe_modes.__defaults__ = (T.M_TOP, T.J_TOP, False, 4, None)


def ops_8m(turb):
    ops = dict(OPS18)
    F = OPS18["F_top_equiv_char"]                     # = M_base(18 m) / 18 m, same rotor forces
    ops["F_top_equiv_char"] = F
    ops["M_top_char"] = F * TOP_TO_RC
    ops["M_base_char"] = F * (L_TUBE + TOP_TO_RC)
    lever = (L_TUBE + TOP_TO_RC) / 18.0
    ops["fatigue"] = {lvl: [[rng * lever * turb, n] for rng, n in data] for lvl, data in OPS18["fatigue"].items()}
    return ops


def size(strategy, ops, t_base_min=6):
    if strategy == "soft-stiff":
        lo, hi = 1.1 * C.RPM_MIN / 60, 3 * C.RPM_MIN / 60 / 1.1
    else:
        lo, hi = 1.15 * C.RPM / 60, 3 * C.RPM / 60 / 1.1
    setup((lo, hi))
    K_soft, best = 5e8, None
    for _ in range(4):
        best = None
        for Db in np.arange(0.40, 1.21, 0.02):
            for tb in (6, 8, 10, 12, 14, 16, 20):
                if tb < t_base_min:
                    continue
                for tt in (6, 8, 10, 12, 14, 16):
                    if tt > tb:
                        continue
                    tw = T.Tower(H=L_TUBE, D_base=float(Db), D_top=T.D_TOP, t=(tb / 1000, tt / 1000))
                    D, t_, *_ = tw.geom(np.linspace(0, L_TUBE, 50))
                    if np.max(D / t_) > T.DT_MAX:
                        continue
                    r = T.evaluate(tw, ops, K_soft)
                    if r["util_max"] > 1 or r["util_tilt_up"] > 1 or r["f1_rigid_Hz"] > hi or r["f1_soft_ice_Hz"] < lo:
                        continue
                    if max(T.fatigue_check(tw, ops["fatigue"]).values()) > 1.0:
                        continue
                    if best is None or r["mass_kg"] < best[1]["mass_kg"]:
                        best = (tw, r)
        if best is None:
            return dict(strategy=strategy, window_Hz=[round(lo, 2), round(hi, 2)], feasible=False)
        tw, r = best
        prof = T.evaluate(tw, ops, K_soft, verbose=True)["_profiles"]
        res = prof["res"]
        M_char = res["parked V_e50"][0] / T.GAMMA_WIND_EC
        M_design = max(v[0] for v in res.values())
        H_design = T.GAMMA_WIND_EC * (T.F_SIDE_VE50 + np.trapezoid(*T.drag_profile(tw, T.V_E50, T.CF_CLEAN)[::-1]))
        V_top = (tw.mass() + T.M_TOP) * T.G
        fnd = {n: T.footing(M_char, M_design, H_design, V_top, s, ops["M_base_char"]) for n, s in T.SOILS.items()}
        K_new = min(f["K_theta"] for f in fnd.values())
        if abs(K_new - K_soft) / K_soft < 0.05:
            break
        K_soft = K_new
    fnd["rock (anchored plinth)"] = T.rock_anchor_plinth(M_design, V_top)
    for f in fnd.values():
        if "K_theta" in f:
            f["K_theta_MNm_per_rad"] = round(f.pop("K_theta") / 1e6)
    r.pop("_profiles", None)
    r["geometry"] = dict(L_tube=round(L_TUBE, 3), D_base=round(tw.D_base, 2), D_top=tw.D_top, t_mm=[round(x * 1000) for x in tw.t])
    f1, f1s = r["f1_rigid_Hz"], r["f1_soft_ice_Hz"]
    r["exclusion_zone_rpm"] = ([round(60 * f1s / 1.1, 1), round(60 * f1 * 1.1, 1)] if strategy == "soft-stiff"
                               else [round(20 * f1s / 1.1, 1), round(20 * f1 * 1.1, 1)])
    r["fatigue_damage"] = T.fatigue_check(tw, ops["fatigue"])
    r["base_flange"] = dict(M_design_kNm=round(M_design / 1e3, 1), **(T.flange_bolts(M_design, tw.D_base) or {}))
    return dict(strategy=strategy, window_Hz=[round(lo, 2), round(hi, 2)], feasible=True, tower=r, foundations=fnd)


def log_ratio(z1, z2, z0):
    return math.log(z1 / z0) / math.log(z2 / z0)


def energy():
    rows, _, _ = PW.curve(True, ROUGH)
    V = np.array([r["V"] for r in rows]); P = np.array([r["P_net"] for r in rows])
    dV = V[1] - V[0]

    def aep(v, k):
        c = v / math.gamma(1 + 1 / k)
        f = (k / c) * (V / c) ** (k - 1) * np.exp(-(V / c) ** k)
        return float(np.sum(P * f) * dV * 8760 * 0.97 / 1000)
    out = {}
    for s in SITES:
        ratio = log_ratio(HUB_H, 18.0, s["z0"])
        e18, e8 = aep(s["v"], s["k"]), aep(s["v"] * ratio, s["k"])
        I18, I8 = 1 / math.log(18.0 / s["z0"]), 1 / math.log(HUB_H / s["z0"])
        out[s["key"]] = dict(name=s["name"], z0=s["z0"], v18=s["v"], v8=round(s["v"] * ratio, 2), aep18_kWh=round(e18),
                             aep8_kWh=round(e8), loss_pct=round(100 * (1 - e8 / e18), 1), turb_increase_pct=round(100 * (I8 / I18 - 1), 1))
    return out


def figure(en):
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    keys = list(en); x = np.arange(len(keys))
    ax.bar(x - 0.18, [en[k]["aep18_kWh"] / 1e3 for k in keys], 0.36, label="18 m hub", color="#1f6fb2")
    ax.bar(x + 0.18, [en[k]["aep8_kWh"] / 1e3 for k in keys], 0.36, label="8 m hub", color="#d9822b")
    for i, k in enumerate(keys):
        ax.text(i + 0.18, en[k]["aep8_kWh"] / 1e3 + 0.8, f"−{en[k]['loss_pct']:.0f} %", ha="center", fontsize=8)
    ax.set_xticks(x, [en[k]["name"].replace(" / ", "\n") for k in keys], fontsize=8)
    ax.set_ylabel("MWh per year (net)"); ax.set_title("M8 yearly energy: 18 m vs 8 m hub height"); ax.legend()
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout(); fig.savefig(C.OUT / "F05-tower8.png", dpi=150); plt.close(fig)


def ops_sim8():
    """Operating loads simulated at 8 m (dlc8_l7.py): used directly, no scaling."""
    o = json.loads((C.OUT / "dlc8_l7" / "ops_loads_l7_8m.json").read_text())
    o["F_top_equiv_char"] = o["M_base_char"] / HUB_H
    o["M_top_char"] = 0.0
    return o


def resonance_stiff(tw, K_theta, U_imb=0.20, zeta=0.005, dT3=0.05, vave=10.0):
    """Stiff tower: fatigue from (a) 1P side-side below resonance (rotor imbalance, 0.2 kg m, R6.6) and
    (b) the 3P thrust harmonic crossing mode 1 during start-up/low wind, with the 3P exclusion zone passed
    under torque (5 % of the time between its edges, as tower.py assumes for the 1P zone)."""
    f, sh, M, zn = T.fe_modes(tw, K_theta, n_modes=2)
    f1 = f[0]
    m1 = (sh[:, 0] / sh[-2, 0]) @ M @ (sh[:, 0] / sh[-2, 0])
    k1 = m1 * (2 * math.pi * f1) ** 2
    _, _, _, _, Wb = tw.geom(np.array([0.0]))
    tsr, rpm_max = 7.25, C.RPM
    c_ray = vave / math.gamma(1.5)
    life = 20 * 8760 * 3600 * 0.97
    zone = (20 * f1 / 1.1, 20 * f1 * 1.1)
    dsc = T.DETAIL / T.GAMMA_MF; dsd = 0.737 * dsc

    def dmg(s_, n):
        N = 2e6 * (dsc / s_) ** 3 if s_ >= dsd else 5e6 * (dsd / s_) ** 5
        return n / N
    D1 = D3 = 0.0
    for V in np.arange(3.0, 25.01, 0.5):
        p = math.exp(-((V - 0.25) / c_ray) ** 2) - math.exp(-((V + 0.25) / c_ray) ** 2)
        rpm0 = min(tsr * V / C.R * 60 / (2 * math.pi), rpm_max)
        thrust = 2.2e3 * min(1.0, (V / C.V_RATED) ** 2)
        for rpm in np.linspace(rpm0 * 0.85, rpm0 * 1.15, 13):
            w8 = math.exp(-0.5 * ((rpm - rpm0) / (0.1 * rpm0)) ** 2) / 4.39
            if zone[0] < rpm < zone[1]:
                continue
            t = p * life * w8
            om = rpm * 2 * math.pi / 60
            r1 = (rpm / 60) / f1
            x1 = U_imb * om ** 2 / k1 / math.sqrt((1 - r1 ** 2) ** 2 + (2 * zeta * r1) ** 2)
            D1 += dmg(max(2 * k1 * x1 * tw.H / Wb[0], 1.0), t * rpm / 60)
            r3 = (3 * rpm / 60) / f1
            x3 = dT3 * thrust / k1 / math.sqrt((1 - r3 ** 2) ** 2 + (2 * 0.02 * r3) ** 2)
            D3 += dmg(max(2 * k1 * x3 * tw.H / Wb[0], 1.0), t * 3 * rpm / 60)
    V_lo, V_hi = (z * 2 * math.pi / 60 * C.R / tsr for z in zone)
    p_zone = math.exp(-(V_lo / c_ray) ** 2) - math.exp(-(V_hi / c_ray) ** 2)
    th_zone = 2.2e3 * (0.5 * (V_lo + V_hi) / C.V_RATED) ** 2
    x_res = dT3 * th_zone / k1 / (2 * 0.02) * 0.5
    D3 += dmg(2 * k1 * x_res * tw.H / Wb[0], 0.05 * p_zone * life * 3 * zone[0] / 60)
    return dict(f1=round(float(f1), 2), r_1P_rated=round(C.RPM / 60 / f1, 2), zone_3P_rpm=[round(z, 1) for z in zone],
                zone_wind_m_s=[round(V_lo, 1), round(V_hi, 1)], damage_1P_side_side=round(D1, 4), damage_3P=round(D3, 4))


def tilt_up_l7(tw, L_gp_frac=0.33, dyn=1.3, V_wind=15.0):
    """tower.py tilt_up_ginpole with the M8 blade area (3 x 1.337 m2 instead of 3 x 0.85)."""
    z = np.linspace(0, tw.H, 400)
    _, _, A, _, Wz = tw.geom(z)
    w = A * T.STEEL_RHO * (1 + tw.extra_mass_frac) * T.G * dyn
    P = HEAD * T.G * dyn + 0.5 * 1.225 * V_wind ** 2 * 1.2 * 3 * AREA
    mom = np.array([np.trapezoid(w[z >= ze] * (z[z >= ze] - ze), z[z >= ze]) + P * (tw.H - ze) for ze in z])
    return dict(base_moment_kNm=round(float(mom[0]) / 1e3, 1), util=round(float(np.max(mom / Wz) / (T.FY / T.GAMMA_M1)), 3),
                winch_line_pull_kN=round(float(mom[0] / (L_gp_frac * tw.H)) / 1e3, 1))


def final_stiff():
    """Final 8 m tower: re-sized with the loads simulated at 8 m, then the stiff-tower resonance and tilt-up checks."""
    ops = ops_sim8()
    res = size("stiff", ops, t_base_min=10)
    # doc 37: the lightest tube with the simulated loads is 8/8 mm (611 kg) but its f1 with soft soil and ice (2.54 Hz) sits
    # on the 1.15 x 1P limit (2.51 Hz); the base can is kept at 10 mm for frequency margin and fatigue (the 8 m load run used it).
    res["lightest_8mm_kg"] = size("stiff", ops)["tower"]["mass_kg"]
    g = res["tower"]["geometry"]
    tw = T.Tower(H=L_TUBE, D_base=g["D_base"], D_top=g["D_top"], t=tuple(x / 1000 for x in g["t_mm"]))
    K = min(f["K_theta_MNm_per_rad"] for f in res["foundations"].values() if "K_theta_MNm_per_rad" in f) * 1e6
    res["resonance"] = resonance_stiff(tw, K)
    res["tilt_up_M8_area"] = tilt_up_l7(tw)
    res["ops_source"] = ops["source"]
    res["ops_M_base_char_kNm"] = round(ops["M_base_char"] / 1e3, 1)
    return res


def main():
    en = energy()
    turb = 1 + max(v["turb_increase_pct"] for v in en.values()) / 100
    ops = ops_8m(turb)
    towers = {st: size(st, ops) for st in ("soft-stiff", "stiff")}
    if (C.OUT / "dlc8_l7" / "ops_loads_l7_8m.json").exists():
        towers["stiff_final_sim8"] = final_stiff()
    out = dict(hub_height_m=HUB_H, L_tube_m=round(L_TUBE, 3), z_pedestal_m=Z_PED, head_kg=HEAD, lowest_tip_m=round(HUB_H - C.R, 2),
               fatigue_turbulence_factor=round(turb, 3), towers=towers, energy=en,
               tower18=dict(mass_kg=T18["tower"]["mass_kg"], f1_Hz=T18["tower"]["f1_rigid_Hz"],
                            footing_soft=T18["foundations"]["soft volcanic soil (loose ash, pumice sand)"]["concrete_m3"]))
    (C.OUT / "tower8_l7.json").write_text(json.dumps(out, indent=1, default=float))
    figure(en)
    print(json.dumps(out, indent=1, default=float)[:6000])


if __name__ == "__main__":
    main()
