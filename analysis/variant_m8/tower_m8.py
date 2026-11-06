"""M8 tower and footing sizing (doc 35 §7). Run after dlc_m8.py and hub_yaw_m8.py.

Run:  python3 tower_m8.py   -> results/tower_m8.json   (~3 min)

Reuses analysis/tower/tower.py (beam FE model, storm/ice/earthquake/tilt-up cases,
section class, fatigue, footings) with M8 inputs:
- tower-top mass from hub_yaw_m8.py (the full count, as doc 25 §2),
- parked side force on the rotor scaled with blade planform area (1.337 / 0.849 m2),
- SLM H thrust from structure_m8.py, operating loads and fatigue spectra from dlc_m8.py,
- frequency window for the M8 speed range 35-131 rpm: 1P max 2.18 Hz, 3P min 1.75 Hz,
  so a freestanding tower must be below 3P(35 rpm)/1.1 = 1.59 Hz, with a speed exclusion zone
  around its 1P crossing (as doc 09).
For comparison the current D7.5 turbine is sized the same way with its true 1,103 kg head
(doc 25) and its doc 09 operating loads (which were simulated with a 480 kg head).
"""
from __future__ import annotations
import json, math
import numpy as np
import common as C
import tower as T

HY = json.loads((C.OUT / "hub_yaw_m8.json").read_text())
SLM8 = json.loads((C.OUT / "slm_m8.json").read_text())


def configure(m8: bool):
    if m8:
        T.M_TOP = float(HY["yaw"]["m_above_tower_flange_kg"])
        T.J_TOP = 300.0 * T.M_TOP / 480.0 * 1.15            # rotor flap inertia grows more than the mass
        T.D_TOP = 0.40
        T.F_SIDE_VE50 = 8.0e3 * 1.337 / C.BLADE_AREA_CUR + 5.8e3 * 1.06
        T.M_TOP_GRAV = T.M_TOP * C.OVERHANG * 0.45 * T.G       # head CoG ahead of the tower axis
        T.SLM_FX_DESIGN = SLM8["ultimate_design_values_gamma_3_kN_kNm"]["H_parked"]["F_x_shaft"] * 1e3
        T.SLM_FX_CHAR = T.SLM_FX_DESIGN / 3
        T.F_MAX_SOFT = 3 * C.RPM_MIN / 60 / 1.1
        T.F_MIN_SOFT = C.RPM_MIN / 60 * 1.1
        ops = json.loads((C.OUT / "dlc_m8" / "ops_loads_m8_18m.json").read_text())
    else:
        T.M_TOP, T.J_TOP, T.D_TOP = 1286.0, 300.0 * 1286 / 480, 0.32
        T.F_SIDE_VE50, T.M_TOP_GRAV = 8.0e3 + 5.8e3, 1286 * 0.75 * 0.45 * T.G
        T.SLM_FX_DESIGN, T.SLM_FX_CHAR = 41.64e3, 13.88e3
        T.F_MAX_SOFT, T.F_MIN_SOFT = 2.0 / 1.1, 0.667 * 1.1
        ops = json.loads((T.OUT / "ops_loads_monopole_18m.json").read_text())
    # tower.py binds M_TOP/J_TOP as default arguments at import: rebind them
    T.fe_assemble.__defaults__ = (T.M_TOP, T.J_TOP, False, None)
    T.fe_modes.__defaults__ = (T.M_TOP, T.J_TOP, False, 4, None)
    return ops


def size(ops, H=18.0, n_sec=2):
    best = None
    K_soft = 5e8
    for _ in range(3):
        best = None
        for Db in np.arange(0.50, 1.21, 0.05):
            for tb in (6, 8, 10, 12, 14, 16, 20):
                for tt in (6, 8, 10, 12, 14, 16):
                    if tt > tb:
                        continue
                    tw = T.Tower(H=H, D_base=float(Db), D_top=T.D_TOP, t=(tb / 1000, tt / 1000))
                    D, t_, *_ = tw.geom(np.linspace(0, H, 50))
                    if np.max(D / t_) > T.DT_MAX:
                        continue
                    r = T.evaluate(tw, ops, K_soft)
                    if r["util_max"] > 1 or r["util_tilt_up"] > 1 or r["f1_rigid_Hz"] > T.F_MAX_SOFT or r["f1_soft_ice_Hz"] < T.F_MIN_SOFT:
                        continue
                    if ops.get("fatigue") and max(T.fatigue_check(tw, ops["fatigue"]).values()) > 1.0:
                        continue
                    if best is None or r["mass_kg"] < best[1]["mass_kg"]:
                        best = (tw, r)
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
    r["geometry"] = dict(H=H, D_base=round(tw.D_base, 2), D_top=tw.D_top, t_mm=[round(x * 1000) for x in tw.t])
    f1 = r["f1_rigid_Hz"]
    r["exclusion_zone_rpm"] = [round(60 * f1 / 1.1, 1), round(60 * f1 * 1.1, 1)]
    if ops.get("fatigue"):
        r["fatigue_damage"] = T.fatigue_check(tw, ops["fatigue"])
    zf = H / 2
    Mf = float(np.interp(zf, prof["z"], np.max(np.array(list(prof["res"].values())), axis=0)))
    r["flange_mid"] = dict(M_design_kNm=round(Mf / 1e3, 1), **(T.flange_bolts(Mf, float(tw.geom(np.array([zf]))[0][0])) or {}))
    r["base_flange"] = dict(M_design_kNm=round(M_design / 1e3, 1), **(T.flange_bolts(M_design, tw.D_base) or {}))
    return dict(tower=r, foundations=fnd, head_mass_kg=T.M_TOP, F_side_Ve50_kN=round(T.F_SIDE_VE50 / 1e3, 1),
                ops_M_base_char_kNm=round(ops["M_base_char"] / 1e3, 1), window_Hz=[round(T.F_MIN_SOFT, 2), round(T.F_MAX_SOFT, 2)])


def main():
    out = {}
    for key, m8 in (("current_D7.5_head1286", False), ("M8", True)):
        out[key] = size(configure(m8))
        print(key, json.dumps(out[key], indent=1, default=float)[:3000])
    (C.OUT / "tower_m8.json").write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
