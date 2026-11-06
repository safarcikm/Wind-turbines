"""S6 on an 8 m hub-height tower (doc 34): tower, footing, frequencies, energy, turbulence and noise.

Run:  python3 tower8.py      (~2 min) -> results/tower8.json, results/E01-tower8.png

Same tower model as doc 30 (analysis/tower/tower.py, called the same way as design6.tower()), with:
  * hub height 8.0 m above ground: tower tube 6.87 m from the base flange (pedestal top +0.20 m) to the
    top flange (+7.07 m); yaw bearing top +7.43 m; rotor centre +8.00 m (570 above the bearing, doc 30).
  * the S6 head 912 kg (doc 32) and the doc 30 load scaling; operating top force from the 18 m simulation,
    applied 0.93 m above the tower top (top flange to rotor centre).
  * fatigue spectra scaled for the shorter lever and for the higher turbulence near the ground.
  * class S extreme winds kept AT HUB HEIGHT (IEC 61400-2 defines V_ref at hub height): no credit is
    taken for the lower wind speed at 8 m in the extreme cases.
Two frequency strategies are sized and compared:
  soft-stiff  f1 inside 1.1 x 1P_min ... 3P_min / 1.1 (as the 18 m tower, 1P crossing at low speed)
  stiff       f1 above 1.1 x 1P_max (3.0 Hz), 3P crossing at low speed instead
"""
from __future__ import annotations
import json, math, sys, io, contextlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
ROOT = HERE.parent
OUT = HERE / "results"
sys.argv = sys.argv[:1]
sys.path.insert(0, str(HERE))
with contextlib.redirect_stdout(io.StringIO()):
    import design6 as D6m  # noqa: E402   (sets up the doc 30 modules; main() not run)
T = D6m.T
m27 = D6m.m27

D6 = json.loads((OUT / "design6.json").read_text())
HEAD = json.loads((OUT / "head6.json").read_text())["head_mass_kg"]          # 912 kg (doc 32 list)
_CAD = ROOT.parent / "cad" / "turbine_6kw" / "out" / "model6-parts.json"
if _CAD.exists():                                                             # doc 34: CAD mass of every part
    HEAD = max(HEAD, round(json.loads(_CAD.read_text())["head_kg"]))
REG = json.loads((OUT / "regulation.json").read_text())

HUB_H = 8.0
Z_PED = 0.20                   # base flange (pedestal top) above ground
TOP_TO_RC = 0.36 + 0.57        # tower top flange -> yaw bearing top -> rotor centre
L_TUBE = HUB_H - Z_PED - TOP_TO_RC      # 6.87 m
RPM = D6m.RPM; RPM_MIN = D6m.RPM_MIN
R = D6m.R

# site roughness for the shear and turbulence estimates (Wieringa / EN 1991-1-4 classes)
SITES = {"sheltered": dict(z0=0.25, name="Sheltered valley / farm"),
         "inland": dict(z0=0.05, name="Open inland lowland"),
         "coastal": dict(z0=0.01, name="Coast / exposed lowland"),
         "highland": dict(z0=0.03, name="Highland / headland")}


def setup_tower_module(m_top, slm, blade_area, window):
    T.M_TOP = m_top
    T.J_TOP = 300.0 * m_top / 480.0 * 0.9
    T.D_TOP = 0.32
    T.F_SIDE_VE50 = 8.0e3 * blade_area / 0.849 + 5.8e3
    T.M_TOP_GRAV = m_top * D6m.OVERHANG * 0.45 * T.G
    T.SLM_FX_DESIGN = slm["ultimate_design_values_gamma_3_kN_kNm"]["H_parked"]["F_x_shaft"] * 1e3
    T.SLM_FX_CHAR = T.SLM_FX_DESIGN / 3
    T.F_MIN_SOFT, T.F_MAX_SOFT = window
    T.fe_assemble.__defaults__ = (T.M_TOP, T.J_TOP, False, None)
    T.fe_modes.__defaults__ = (T.M_TOP, T.J_TOP, False, 4, None)


def ops_8m(turb_factor):
    ops12 = json.loads((ROOT / "tower" / "results" / "ops_loads_monopole_18m.json").read_text())
    k_ult = D6["tower"]["scaling"]["k_ultimate"]
    k_fat = D6["tower"]["scaling"]["k_fatigue"]
    F = ops12["F_top_equiv_char"] * k_ult
    ops = dict(ops12)
    ops["F_top_equiv_char"] = F
    ops["M_top_char"] = F * TOP_TO_RC
    ops["M_base_char"] = F * (L_TUBE + TOP_TO_RC)
    lever = (L_TUBE + TOP_TO_RC) / 18.0
    ops["fatigue"] = {lvl: [[rng * k_fat * lever * turb_factor, n] for rng, n in data] for lvl, data in ops12["fatigue"].items()}
    return ops


def size(strategy, ops, slm, blade_area):
    f1p_min, f1p_max = RPM_MIN / 60, RPM / 60
    if strategy == "soft-stiff":
        lo, hi = 1.1 * f1p_min, 3 * f1p_min / 1.1
    else:
        lo, hi = 1.15 * f1p_max, 3 * RPM / 60 / 1.1       # stiff: 15 % above 1P max (margin for mass/soil scatter), below 3P at rated
    setup_tower_module(HEAD, slm, blade_area, (lo, hi))
    H = L_TUBE
    K_soft = 5e8
    best = None
    for _ in range(4):
        best = None
        for Db in np.arange(0.32, 1.01, 0.02):
            for tb in (5, 6, 8, 10, 12, 14, 16):
                for tt in (5, 6, 8, 10, 12, 14, 16):
                    if tt > tb:
                        continue
                    tw = T.Tower(H=H, D_base=float(Db), D_top=T.D_TOP, t=(tb / 1000, tt / 1000))
                    D, t_, *_ = tw.geom(np.linspace(0, H, 50))
                    if np.max(D / t_) > T.DT_MAX:
                        continue
                    r = T.evaluate(tw, ops, K_soft)
                    f_hi = r["f1_rigid_Hz"]; f_lo = r["f1_soft_ice_Hz"]
                    if r["util_max"] > 1 or r["util_tilt_up"] > 1 or f_hi > hi or f_lo < lo:
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
    r["geometry"] = dict(L_tube=round(H, 3), D_base=round(tw.D_base, 2), D_top=tw.D_top, t_mm=[round(x * 1000) for x in tw.t])
    f1 = r["f1_rigid_Hz"]; f1s = r["f1_soft_ice_Hz"]
    if strategy == "soft-stiff":
        zone = [round(60 * f1s / 1.1, 1), round(60 * f1 * 1.1, 1)]           # 1P crossing
        kind = "1P"
    else:
        zone = [round(20 * f1s / 1.1, 1), round(20 * f1 * 1.1, 1)]           # 3P crossing: rpm = 20 f1
        kind = "3P"
    r["exclusion_zone_rpm"] = zone
    r["exclusion_kind"] = kind
    r["fatigue_damage"] = T.fatigue_check(tw, ops["fatigue"])
    r["base_flange"] = dict(M_design_kNm=round(M_design / 1e3, 1), **(T.flange_bolts(M_design, tw.D_base) or {}))
    r["H_design_kN"] = round(H_design / 1e3, 1)
    r["M_char_parked_kNm"] = round(M_char / 1e3, 1)
    r["top_deflection_parked_char_mm"] = None
    # resonance damage with the zone (rotor imbalance 1P side-side and 3P on mode 1 for the stiff tower)
    return dict(strategy=strategy, window_Hz=[round(lo, 2), round(hi, 2)], feasible=True, tower=r, foundations=fnd,
                K_soft_MNm=round(K_soft / 1e6))


# ------------------------------------------------------------------ energy, turbulence, noise
def log_ratio(z1, z2, z0):
    return math.log(z1 / z0) / math.log(z2 / z0)


def energy():
    sc = REG["stall_curve"]
    V = np.array(sc["V"]) if isinstance(sc, dict) else np.array([r["V"] for r in sc])
    P = np.array(sc["P"]) if isinstance(sc, dict) else np.array([r["P"] for r in sc])
    rpm = np.array(sc["rpm"]) if isinstance(sc, dict) and "rpm" in sc else (np.array([r.get("rpm", RPM) for r in sc]) if not isinstance(sc, dict) else None)
    import regulation as RG  # noqa: E402
    out = {}
    for s in m27.SCENARIOS:
        z0 = SITES[s["key"]]["z0"]
        k18 = s["k"]
        ratio = log_ratio(HUB_H, 18.0, z0)
        k8 = k18 * (1 - 0.088 * math.log(18.0 / HUB_H) / (1 - 0.088 * math.log(18.0 / 10.0)) * 0.0)  # k kept (Justus k(z) change < 3 %)
        s8 = dict(s, v=s["v"] * ratio, k=k8)
        e18 = RG.aep_from(V, P, [s], rpm)[s["key"]]
        e8 = RG.aep_from(V, P, [s8], rpm)[s["key"]]
        I18 = 1 / math.log(18.0 / z0); I8 = 1 / math.log(HUB_H / z0)
        out[s["key"]] = dict(name=s["name"], z0=z0, v18=s["v"], v8=round(s8["v"], 2), speed_ratio=round(ratio, 3),
                             aep18_kWh=round(e18), aep8_kWh=round(e8), loss_pct=round(100 * (1 - e8 / e18), 1),
                             I18=round(I18, 3), I8=round(I8, 3), turb_increase_pct=round(100 * (I8 / I18 - 1), 1))
    return out


def noise():
    """Hau sound power vs tip speed (doc 27 model) at the same 10 m reference wind; SPL at 60 m ground distance."""
    out = {}
    for key in ("inland", "coastal"):
        z0 = SITES[key]["z0"]
        row = {}
        for H in (18.0, HUB_H):
            v_hub = 8.0 * log_ratio(H, 10.0, z0)
            tip = min(D6m.TSR * v_hub, RPM * math.pi / 30 * R)
            lw = 50 * math.log10(tip) + 10 * math.log10(2 * R) - 4
            spl = lw - 10 * math.log10(2 * math.pi * (60 ** 2 + H ** 2)) - 0.003 * math.hypot(60, H)
            row[f"{H:.0f}m"] = dict(v_hub=round(v_hub, 2), tip=round(tip, 1), LwA=round(lw, 1), SPL60=round(spl, 1))
        tip_r = RPM * math.pi / 30 * R
        lw_r = 50 * math.log10(tip_r) + 10 * math.log10(2 * R) - 4
        row["rated_any_height"] = dict(tip=round(tip_r, 1), LwA=round(lw_r, 1),
                                       SPL60_18m=round(lw_r - 10 * math.log10(2 * math.pi * (3600 + 324)) - 0.003 * 62.6, 1),
                                       SPL60_8m=round(lw_r - 10 * math.log10(2 * math.pi * (3600 + 64)) - 0.003 * 60.5, 1))
        out[key] = row
    return out


def figure(en, res):
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
    keys = list(en)
    x = np.arange(len(keys))
    ax[0].bar(x - 0.18, [en[k]["aep18_kWh"] / 1000 for k in keys], 0.36, label="18 m hub", color="#2f6db5")
    ax[0].bar(x + 0.18, [en[k]["aep8_kWh"] / 1000 for k in keys], 0.36, label="8 m hub", color="#d9822b")
    for i, k in enumerate(keys):
        ax[0].text(i + 0.18, en[k]["aep8_kWh"] / 1000 + 0.4, f"−{en[k]['loss_pct']:.0f} %", ha="center", fontsize=8)
    ax[0].set_xticks(x, [k for k in keys]); ax[0].set_ylabel("MWh / year"); ax[0].legend(frameon=False, fontsize=8)
    ax[0].set_title("Annual energy, S6", fontsize=10)
    z = np.linspace(1, 20, 100)
    for k in keys:
        z0 = en[k]["z0"]
        ax[1].plot(np.log(z / z0) / np.log(18 / z0), z, label=f"{k} (z0 {z0} m)")
    ax[1].axhspan(5.0, 11.0, color="#d9822b", alpha=0.12); ax[1].axhline(8.0, color="#d9822b", lw=1)
    ax[1].axhspan(15.0, 21.0, color="#2f6db5", alpha=0.08)
    ax[1].text(0.52, 8.2, "8 m rotor 5–11 m", fontsize=8); ax[1].text(0.52, 15.2, "18 m rotor 15–21 m", fontsize=8)
    ax[1].set_xlabel("wind speed / speed at 18 m"); ax[1].set_ylabel("height m"); ax[1].set_xlim(0.5, 1.1); ax[1].set_ylim(0, 21)
    ax[1].legend(frameon=False, fontsize=7, loc="upper left"); ax[1].set_title("Wind shear (log law)", fontsize=10)
    for a in ax:
        a.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(OUT / "E01-tower8.png", dpi=150); plt.close(fig)


def main():
    slm = json.loads((OUT / "slm_6kw.json").read_text()) if (OUT / "slm_6kw.json").exists() else D6["slm"]
    if "ultimate_design_values_gamma_3_kN_kNm" not in slm:
        slm = D6["slm"]
    area = D6m.blade_shape().solidity_area()
    en = energy()
    turb = 1 + max(v["turb_increase_pct"] for v in en.values()) / 100
    ops = ops_8m(turb)
    res = {}
    for st in ("soft-stiff", "stiff"):
        res[st] = size(st, ops, slm, area)
        print(st, json.dumps(res[st], default=float)[:1800])
    out = dict(hub_height_m=HUB_H, L_tube_m=round(L_TUBE, 3), z_pedestal_m=Z_PED, head_kg=HEAD, rotor_tip_low_m=round(HUB_H - R, 2),
               fatigue_turbulence_factor=round(turb, 3), ops=dict(F_top_char_kN=round(ops["F_top_equiv_char"] / 1e3, 2),
                                                                   M_base_char_kNm=round(ops["M_base_char"] / 1e3, 1)),
               towers=res, energy=en, noise=noise(), tower18=D6["tower"]["tower"])
    (OUT / "tower8.json").write_text(json.dumps(out, indent=1, default=float))
    figure(en, res)
    print(json.dumps(en, indent=1)); print(json.dumps(out["noise"], indent=1))


if __name__ == "__main__":
    main()
