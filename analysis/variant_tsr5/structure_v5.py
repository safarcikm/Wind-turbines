"""V5 blade structure and IEC 61400-2 SLM loads (doc 26 §3-4).

Run:  python3 structure_v5.py [dlc]     (~2 min; writes results/slm_v5.json, results/blade_v5.json)
      with "dlc", the aeroelastic loads come from results/dlc_v5/dlc_summary.json (dlc_v5.py),
      otherwise from the doc 11 final run scaled by the steady flap-moment ratio (first pass).

Reuses analysis/loads/slm.py and analysis/blade/blade.py unchanged; only their module
constants (radius, speed, masses, loads) and the two geometry helpers are replaced.
"""
from __future__ import annotations
import json, math, sys
import numpy as np
import common as C
import slm as S
import blade as BLD
from bem import solve

USE_DLC = len(sys.argv) > 1 and sys.argv[1] == "dlc"
# Rotor brake: 4 calipers of the doc 07 type instead of 2 (parked V_ref aero torque 12.0 kNm char. in
# dlc_v5, x 1.45). Feeds SLM G (shutdown torque on shaft and blade edge).
BRAKE_V5 = 2 * 8_730.0


def run_slm(m_b, r_cog, m_hub_drum):
    S.R = C.R
    S.blade = C.blade_shape()
    S.A_PROJ_B = S.blade.solidity_area()
    S.M_B, S.R_COG = m_b, r_cog
    S.I_B = m_b * (r_cog * 1.19) ** 2              # same radius of gyration ratio as slm.py (1.85/1.55)
    S.M_R = 3 * m_b + m_hub_drum
    S.L_RB, S.L_RT, S.E_R = 0.12, C.OVERHANG, 0.005 * C.R
    S.N_DESIGN, S.W_DESIGN, S.Q_DESIGN = C.RPM, C.OMEGA, C.Q_RATED
    S.V_DESIGN = C.V_RATED
    S.LAMBDA_DESIGN = C.OMEGA * C.R / C.V_RATED
    S.N_MAX = C.RPM_MAX
    S.W_MAX = C.RPM_MAX * math.pi / 30
    S.M_BRAKE = BRAKE_V5
    S.OUT = C.OUT
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        S.main()
    (C.OUT / "slm.json").rename(C.OUT / "slm_v5.json")
    return json.loads((C.OUT / "slm_v5.json").read_text())


def patch_blade(loads):
    k = (C.R - 0.40) / (3.75 - 0.40)
    pts = [(0.40, 1.00), (0.55, 0.70), (0.775, 0.30), (1.5, 0.25), (2.25, 0.21), (3.2, 0.18)]
    pts = [(0.40 + (r - 0.40) * k, tc) for r, tc in pts] + [(C.R, 0.18)]
    x, y = zip(*pts)
    BLD.t_over_c = lambda r: float(np.interp(r, x, y))
    BLD.R = C.R
    BLD.BL = C.blade_shape(n=40)
    BLD.OVERHANG = C.OVERHANG
    BLD.D_TOWER_TIP = 0.42                      # V5 tower top (heavier head, see tower_v5)
    BLD.LOADS = loads

    def load_shapes(r, mass_pl):
        c = np.interp(r, BLD.BL.r, BLD.BL.chord)
        dr = np.gradient(r)
        def mom(q):
            return np.array([np.sum(q[i:] * (r[i:] - r[i]) * dr[i:]) for i in range(len(r))])
        m_park = mom(c); m_park /= m_park[0]
        bl = C.blade_shape(n=len(r))
        res = solve(bl, C.V_RATED, C.OMEGA, 0.0)
        qop = np.interp(r, bl.r, res.dT / bl.dr / 3)
        m_op = mom(qop); m_op /= m_op[0]
        m_g = mom(mass_pl); m_g /= m_g[0]
        return m_park, m_op, m_g
    BLD.load_shapes = load_shapes


def sim_loads():
    if USE_DLC:
        d = json.loads((C.OUT / "dlc_v5" / "dlc_summary.json").read_text())
        env, fat = d["ultimate_envelope"], d["fatigue_DEL"]
        return dict(SIM_res=env["Mres0"]["design"], SIM_op_flap=d["per_dlc_max"]["1.3"]["Mflap0"] * 1.35,
                    DEL_flap=fat["Mflap0"]["DEL_1e7"], DEL_edge=fat["Medge0"]["DEL_1e7"], source="dlc_v5")
    # first pass: doc 11 final run scaled by the steady flap moment (1914/1570) and the
    # parked planform area for the parked-governed resultant (1.728/0.849)
    k_op, k_area = 1914 / 1570, 1.728 / 0.849
    return dict(SIM_res=8510.0 * k_area, SIM_op_flap=1.35 * 3850 * k_op, DEL_flap=3403 * k_op,
                DEL_edge=1285 * 2.0, source="doc 11 final scaled")


def root_joint(M, N):
    out = {}
    for D in (0.28, 0.30, 0.34):
        Dbc = D - 0.035
        for size, As, Fins, d_ins in (("M16", 157e-6, 75e3, 0.026), ("M20", 245e-6, 110e3, 0.032)):
            Ft_rd = 0.9 * 1000e6 * As / 1.25
            for n in range(8, 41, 2):
                F = 4 * M / (n * Dbc) + N / n
                if F <= min(Ft_rd, Fins) and math.pi * Dbc / n >= 1.4 * d_ins:
                    out[f"root Ø {D:.2f} m, {size}"] = dict(inserts=n, bolt_circle_m=round(Dbc, 3), F_bolt_kN=round(F / 1e3, 1),
                                                       F_t_Rd_kN=round(Ft_rd / 1e3, 1), pitch_mm=round(math.pi * Dbc / n * 1000))
                    break
    return out


def main():
    m_b, r_cog = 45.0, 1.75
    m_hub_drum = 240.0 + 95.0       # hub + collective pitch (doc 24, upsized) + generator drum
    hist = []
    for it in range(4):
        slm = run_slm(m_b, r_cog, m_hub_drum)
        ult = slm["ultimate_design_values_gamma_3_kN_kNm"]
        sl = sim_loads()
        loads = dict(SLM_H_flap=ult["H_parked"]["M_yB"] * 1e3, SLM_G_edge=ult["G_shutdown"]["M_xB"] * 1e3,
                     SIM_res=sl["SIM_res"], SIM_op_flap=sl["SIM_op_flap"], DEL_flap=sl["DEL_flap"],
                     DEL_edge=sl["DEL_edge"], rpm_max=C.RPM_MAX, gamma_E=3.0)
        patch_blade(loads)
        res = {}
        for opt, mat, core in (("glass", "UD_glass", False), ("carbon", "UD_carbon", False),
                               ("carbon_cored_caps", "UD_carbon", True)):
            d = BLD.design(mat, t_root_wall=0.016, cap_core=core)
            d["f_flap_110rpm_Hz"] = round(float(BLD.beam_modes(d["_r"], d["_EIf"], d["_mu"], rpm=C.RPM)[0]), 2)
            d["f_edge_110rpm_Hz"] = round(float(BLD.beam_modes(d["_r"], d["_EIe"], d["_mu"], rpm=C.RPM)[0]), 2)
            for k in ("_r", "_mu", "_EIf", "_EIe", "_tcap", "f_flap_178rpm_Hz", "f_edge_178rpm_Hz"):
                d.pop(k)
            res[opt] = d
        hist.append((m_b, res["carbon"]["mass_kg"]))
        if abs(res["carbon"]["mass_kg"] - m_b) < 1.0:
            break
        m_b, r_cog = res["carbon"]["mass_kg"], res["carbon"]["r_cog_m"]
    w = 2 * math.pi * C.RPM_MAX / 60
    N_root = 3.0 * res["carbon"]["static_moment_kgm_about_axis"] * w ** 2
    res["root_joint"] = root_joint(loads["SLM_H_flap"], N_root)
    res["root_joint_inputs"] = dict(M_design_kNm=round(loads["SLM_H_flap"] / 1e3, 2), N_design_kN=round(N_root / 1e3, 1))
    res["loads_used"] = {k: round(v, 1) for k, v in loads.items()}
    res["sim_source"] = sl["source"]
    res["mass_iteration"] = hist
    (C.OUT / "blade_v5.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: ({kk: vv for kk, vv in v.items() if kk not in ("stations", "governing_by_station")} if isinstance(v, dict) else v)
                      for k, v in res.items()}, indent=1))
    print(json.dumps(slm, indent=1))


if __name__ == "__main__":
    main()
