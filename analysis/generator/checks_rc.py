"""Generator Rev C (doc 23): thermal, mechanical and electrical checks of the N45SH 30 x 15 x 12 rotor.

Run:  python3 checks_rc.py   -> results/rc_checks.json

Inputs: FEA of shape S1x (sh30.py S1x -> results/sh30_S1x.json), rotor geometry
(cad/generator_rc/rotor_rc.py), the doc 06 lumped thermal model (thermal.py) and the
cooling parts as drawn in the Rev C set (fan blades on the rear cover NP1-212C).
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.argv = sys.argv[:1]                       # thermal.py reads argv[1] as a variant name
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "cad" / "generator_rc"))
import thermal as TH  # noqa: E402
import rotor_rc as R  # noqa: E402

RES = HERE / "results"
FEA = json.loads((RES / "sh30_S1x.json").read_text())
MU0 = 4e-7 * math.pi

# ------------------------------------------------------------------ rated point
T_RATED = 802.0                 # Nm at 178 rpm (doc 06)
RPM, RPM_MAX = 178.0, 250.0
TURNS_REVB = 28
EMF100 = FEA["line_emf_100C_V"]

# Copper loss: 496 W at the 380 V / 28-turn design point (doc 06, Rev B). Same 28 turns and slot fill;
# Rev C makes 372 V at 100 C, so rated torque needs 380/372 more current.
P_CU_REVB = 496.0
P_CU = P_CU_REVB * (380.0 / EMF100) ** 2


def thermal():
    TH.L = 0.074
    TH.SLOT_DEPTH = 0.065
    TH.P_FE = 218.0
    TH.D_DRUM = 0.646
    TH.L_DRUM = 0.194
    TH.P_CU_75 = P_CU
    configs = {
        "as_P1_drawn_no_fan": dict(support_R=0.33, h_int_run=15.0, fin_in=1.0, fin_out=1.0),
        "fan_blades_RevC_as_drawn": dict(support_R=0.33, h_int_run=40.0, fin_in=1.07, fin_out=1.0),
        "fan_plus_inner_fins": dict(support_R=0.33, h_int_run=40.0, fin_in=3.0, fin_out=1.0),
        "full_doc06_package": dict(support_R=0.40, h_int_run=40.0, fin_in=3.0, fin_out=1.5),
    }
    cases = {
        "hot_rated": dict(T_amb=30, V_wind=10.5, solar_W=100),
        "hot_rated_weak_wake": dict(T_amb=30, V_wind=10.5, solar_W=100, induction=0.6),
        "hot_110pct": dict(T_amb=30, V_wind=12.0, load=1.1, solar_W=100),
        "iceland_10C_rated": dict(T_amb=10, V_wind=12.0),
    }
    out = {}
    for cn, cf in configs.items():
        out[cn] = {k: {q: r[q] for q in ("T_hotspot", "T_winding", "T_core", "T_internal_air", "T_rotor_magnets")}
                   for k, c in cases.items() for r in [TH.solve_case(**c, **cf)]}
    return out


def demag_at(T):
    """Transient short-circuit margin (%) interpolated in the FEA table."""
    tab = sorted((float(k[:-1]), v["transient_sc_d"]) for k, v in FEA["demag_margin_pct"].items())
    for (t0, m0), (t1, m1) in zip(tab, tab[1:]):
        if t0 <= T <= t1:
            return round(m0 + (m1 - m0) * (T - t0) / (t1 - t0), 1)
    return None


def mechanical():
    w_max = RPM_MAX * 2 * math.pi / 60
    a_bond = R.W * R.L * 1e-6                                     # one block on the seat [m2]
    r_seat = R.R_SEAT / 1000
    tau_rated = T_RATED / (r_seat * R.COUNT * a_bond)             # bond shear at rated torque
    tau_sc = 6.0 * tau_rated                                      # transient short-circuit torque, 6 x rated (bound)
    m_block = R.MASS_G / 1000
    f_cf = m_block * w_max ** 2 * (R.R_IN + R.H / 2) / 1000         # centrifugal force per block at 250 rpm
    f_mag_pole = 152.0                                            # net radial pull per pole at rated (FEA, + outward)
    # drum shell stresses at the seat
    t = R.YOKE / 1000
    pole_area = 2 * math.pi * 0.300 / 40 * 0.074
    p_mag = f_mag_pole / pole_area
    p_cf = R.COUNT * f_cf / (2 * math.pi * r_seat * R.ROWS_LEN / 1000)
    s_hoop = (p_mag + p_cf) * r_seat / t + 7850 * w_max ** 2 * (r_seat + t / 2) ** 2
    # unbalanced magnetic pull: doc 18 Rev B value scaled with the effective gap (same gap flux, EMF within 1 %)
    g_eff_b = 2.0 + 7.5 / 1.05
    g_eff_c = 2.0 + R.H / 1.05
    ump = 1.9 * g_eff_b / g_eff_c                                 # kN per mm of eccentricity
    b_rms2 = ump * 1e6 * MU0 * (g_eff_c / 1000) / (math.pi * 0.300 * 0.074)
    k_mag = b_rms2 / (MU0 * g_eff_c / 1000)                       # negative stiffness per area [Pa/m]
    r_m = (323.0 + R.R_SEAT) / 2 / 1000
    k_ring2 = 210e9 * t ** 3 * (2 ** 2 - 1) ** 2 / (12 * r_m ** 4)  # n = 2 ovalisation, ring only, no end discs
    # Donnell shell, both ends held round (front disc, rear brake-disc flange + cover), length between them
    L_sh = 0.239
    lam = math.pi * r_m / L_sh
    k_shell = min(210e9 * t / r_m ** 2 * (lam ** 4 / (n * n + lam * lam) ** 2
                                         + t * t / (12 * r_m * r_m * (1 - 0.09)) * (n * n + lam * lam) ** 2)
                  for n in range(2, 40))
    return dict(
        bond_area_mm2=R.W * R.L, bond_shear_rated_kPa=round(tau_rated / 1e3, 1),
        bond_shear_short_circuit_kPa=round(tau_sc / 1e3), bond_allow_120C_MPa=5.0,
        bond_margin_short_circuit=round(5e6 / tau_sc, 1),
        centrifugal_per_block_250rpm_N=round(f_cf, 1), magnet_pull_per_block_rated_N=round(f_mag_pole / R.N_AX, 1),
        bond_load="compression (both forces push the block outward into the seat)",
        drum_wall_under_seat_mm=round(R.YOKE, 2), magnetic_pressure_kPa=round(p_mag / 1e3, 1),
        hoop_stress_MPa=round(s_hoop / 1e6, 2), S355_yield_MPa=355,
        ump_kN_per_mm=round(ump, 2), ump_doc18_kN_per_mm=1.9,
        ump_at_1p5mm_kN=round(ump * 1.5, 1),
        magnetic_neg_stiffness_Pa_per_m=f"{k_mag:.2e}", drum_ring_stiffness_n2_Pa_per_m=f"{k_ring2:.2e}",
        drum_stability_margin_ring_only=round(k_ring2 / k_mag, 1),
        drum_shell_stiffness_ends_round_Pa_per_m=f"{k_shell:.2e}",
        drum_stability_margin_ends_round=round(k_shell / k_mag),
    )


def electrical():
    emf20 = FEA["line_emf_20C_V"]
    emf_m30 = emf20 * (1 + 0.0012 * 50)                           # Br +0.12 %/K below 20 C
    v_pk = emf_m30 * RPM_MAX / RPM * math.sqrt(2)
    return dict(turns=28, line_emf_V={"20C": emf20, "60C": FEA["line_emf_60C_V"], "100C": EMF100},
                line_emf_m30C_178rpm_V=round(emf_m30, 1), peak_line_V_m30C_250rpm=round(v_pk),
                limit_V=1200, copper_loss_W=round(P_CU), copper_loss_RevB_W=P_CU_REVB,
                torque_2D_at_sizing_current_100C_Nm=FEA["torque_at_sizing_current_100C_Nm"],
                cogging_unskewed_pp_Nm=FEA["cogging_pp_Nm"], cogging_skewed_pp_Nm=FEA["cogging_skewed_pp_Nm"])


def main():
    th = thermal()
    mag_hot = th["fan_blades_RevC_as_drawn"]["hot_110pct"]["T_rotor_magnets"]
    res = dict(thermal=th, mechanical=mechanical(), electrical=electrical(),
               demag=dict(table=FEA["demag_margin_pct"], rule="transient SC margin >= 20 % at 100 C",
                          margin_at_100C=demag_at(100), magnet_T_worst_fan_case_C=mag_hot,
                          margin_at_worst_magnet_T=demag_at(max(60.0, mag_hot))),
               limits=dict(hotspot_design_C=130, class_H_C=180, magnet_design_C=100))
    (RES / "rc_checks.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
