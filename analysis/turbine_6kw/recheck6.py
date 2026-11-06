"""Doc 31: recheck the S6 blade, hub and tower with the simulated loads of dlc6.py.

Run after dlc6.py:  python3 recheck6.py   (writes results/recheck6.json)

The doc 30 first pass scaled the 12 kW (doc 11) operating and fatigue loads to the 6 kW rotor and
added x1.3 on fatigue for stall. Here the same design6.py models are run again with the
simulated values in their place: blade (doc 10 model), fixed hub arms, tower and footings (doc 09
model). Parked storm loads still come from the IEC 61400-2 SLM, as in doc 30.
"""
from __future__ import annotations
import json, math
import numpy as np
import design6 as D

S = json.loads((D.OUT / "dlc6" / "dlc_summary.json").read_text())
OPS = json.loads((D.OUT / "dlc6" / "ops_loads_6kw_18m.json").read_text())
D30 = json.loads((D.OUT / "design6.json").read_text())


def blade_sim():
    m_b, r_cog = 20.6, 1.12
    m_hub_drum = 60.0 + 148.5
    env, ops, DEL = S["ultimate_envelope"], S["operating_envelope"], S["fatigue_DEL"]
    for _ in range(5):
        slm = D.run_slm(m_b, r_cog, m_hub_drum)
        ult = slm["ultimate_design_values_gamma_3_kN_kNm"]
        loads = dict(SLM_H_flap=ult["H_parked"]["M_yB"] * 1e3, SLM_G_edge=ult["G_shutdown"]["M_xB"] * 1e3,
                     SIM_res=env["Mres0"]["design"], SIM_op_flap=ops["Mflap0"]["design"],
                     DEL_flap=DEL["Mflap0"]["DEL_1e7"], DEL_edge=DEL["Medge0"]["DEL_1e7"],
                     rpm_max=D.RPM_MAX, gamma_E=3.0)
        D.patch_blade(loads)
        d = D.BLD.design("UD_glass", t_root_wall=0.012, cap_core=False)
        d["f_flap_rpm_Hz"] = round(float(D.BLD.beam_modes(d["_r"], d["_EIf"], d["_mu"], rpm=D.RPM)[0]), 2)
        for k in [k for k in d if k.startswith("_") or k.startswith("f_flap_178") or k.startswith("f_edge_178")]:
            d.pop(k)
        if abs(d["mass_kg"] - m_b) < 0.5:
            break
        m_b, r_cog = d["mass_kg"], d["r_cog_m"]
    d.pop("stations", None)
    return dict(glass=d, loads_used_Nm={k: round(v, 1) for k, v in loads.items()}), slm


def main():
    blade, slm = blade_sim()
    hub = D.fixed_hub(slm, blade)
    ops = dict(OPS)
    lv = OPS["levels"]["0.000"]
    ops["M_base_char"] = lv["M_char_max_operating"]
    ops["F_top_equiv_char"] = ops["M_base_char"] / 18.0
    ops["M_top_char"] = 0.0
    m_head = D30["yaw"]["m_above_tower_flange_kg"]
    orig = json.loads((D.ROOT / "tower" / "results" / "ops_loads_monopole_18m.json").read_text())
    tw = tower_with(ops, m_head, slm)
    out = dict(blade=blade, hub=hub, tower=tw,
               first_pass=dict(blade_mass=D30["blade"]["glass"]["mass_kg"], loads=D30["blade"]["loads_used_Nm"],
                               hub=D30["hub"]["chosen"], tower=D30["tower"]["tower"]["geometry"],
                               tower_mass=D30["tower"]["tower"]["mass_kg"]),
               ops_base_12kW_scaled=round(orig["M_base_char"] * D30["tower"]["scaling"]["k_ultimate"]),
               ops_base_sim=ops["M_base_char"])
    (D.OUT / "recheck6.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps(out, indent=1, default=float)[:6000])


def tower_with(ops, m_top, slm):
    """design6.tower() with `ops` used directly (no 12 kW scaling)."""
    T = D.T
    T.M_TOP = m_top
    T.J_TOP = 300.0 * m_top / 480.0 * 0.9
    T.D_TOP = 0.32
    T.F_SIDE_VE50 = 8.0e3 * D.blade_shape().solidity_area() / 0.849 + 5.8e3
    T.M_TOP_GRAV = m_top * D.OVERHANG * 0.45 * T.G
    T.SLM_FX_DESIGN = slm["ultimate_design_values_gamma_3_kN_kNm"]["H_parked"]["F_x_shaft"] * 1e3
    T.SLM_FX_CHAR = T.SLM_FX_DESIGN / 3
    T.F_MAX_SOFT = 3 * D.RPM_MIN / 60 / 1.1
    T.F_MIN_SOFT = D.RPM_MIN / 60 * 1.1
    T.fe_assemble.__defaults__ = (T.M_TOP, T.J_TOP, False, None)
    T.fe_modes.__defaults__ = (T.M_TOP, T.J_TOP, False, 4, None)
    H = 18.0
    K_soft = 5e8
    for _ in range(3):
        best = None
        for Db in np.arange(0.45, 1.01, 0.05):
            for tb in (5, 6, 8, 10, 12):
                for tt in (5, 6, 8, 10):
                    if tt > tb:
                        continue
                    tw = T.Tower(H=H, D_base=float(Db), D_top=T.D_TOP, t=(tb / 1000, tt / 1000))
                    Dd, t_, *_ = tw.geom(np.linspace(0, H, 50))
                    if np.max(Dd / t_) > T.DT_MAX:
                        continue
                    r = T.evaluate(tw, ops, K_soft)
                    if r["util_max"] > 1 or r["util_tilt_up"] > 1 or r["f1_rigid_Hz"] > T.F_MAX_SOFT or r["f1_soft_ice_Hz"] < T.F_MIN_SOFT:
                        continue
                    if max(T.fatigue_check(tw, ops["fatigue"]).values()) > 1.0:
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
    governing = max(res, key=lambda k: res[k][0])
    r.pop("_profiles", None)
    r["geometry"] = dict(H=H, D_base=round(tw.D_base, 2), D_top=tw.D_top, t_mm=[round(x * 1000) for x in tw.t])
    r["fatigue_damage"] = T.fatigue_check(tw, ops["fatigue"])
    r["governing_base_case"] = governing
    r["base_moments_design_kNm"] = {k: round(v[0] / 1e3, 1) for k, v in res.items()}
    for f in fnd.values():
        f["K_theta_MNm_per_rad"] = round(f.pop("K_theta") / 1e6)
    # same geometry as doc 30, fatigue with simulated spectra
    tw30 = D30["tower"]["tower"]["geometry"]
    t30 = T.Tower(H=H, D_base=tw30["D_base"], D_top=tw30["D_top"], t=tuple(x / 1000 for x in tw30["t_mm"]))
    r30 = T.evaluate(t30, ops, K_soft)
    r30.pop("_profiles", None)
    return dict(tower=r, footings=fnd,
                doc30_geometry_with_sim_loads=dict(util_max=r30["util_max"], fatigue_damage=T.fatigue_check(t30, ops["fatigue"])))


if __name__ == "__main__":
    main()
