"""Detail design checks for nacelle prototype P1 (doc 14).

    python3 detail.py      # writes results/detail_summary.json

Geometry comes from cad/nacelle_p1/geometry.py (single source of truth).
Loads come from doc 07 / doc 08 / doc 13 (design values, partial safety
factors already included unless stated).
"""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parents[1] / "cad" / "nacelle_p1"))
import geometry as G  # noqa: E402

OUT = HERE / "results"
res = {}

# ------------------------------------------------------------------ loads
M_HUB = 9.8e3          # Nm, spindle design moment (doc 08: doc 07 x 1.27, gamma 1.35)
F_STATIC = (41e3, 44e3)  # N, bearing static design loads front/rear (doc 08)
F_AX_PARKED = 41.6e3   # N, SLM H parked thrust (doc 13)
T_RATED = 802.0        # Nm generator design torque (doc 06)
T_SC = 4 * T_RATED     # Nm, short-circuit peak torque allowance on the stator joint
T_BRAKE = 8.7e3        # Nm (doc 07)
T_SLM_G = 28.4e3       # Nm, SLM G shutdown shaft torque (doc 13)
TILT_YAW = 24.3e3      # Nm, yaw bearing tilt moment (doc 13)
REV_20Y = 1407.2e6
L10_TARGET = 2 * REV_20Y

# ------------------------------------------------------------- bearings
b = G.BRG
P_eq = [3.0e3 * 3, 0.92e3 * 3]   # doc 07 equivalent loads x 3 (doc 08 DEL implies 2 to 3 x)
L10 = [(b["C_kN"] * 1e3 / p) ** (10 / 3) * 1e6 for p in P_eq]
res["bearings"] = dict(
    designation=b["designation"], d_D_T_mm=[b["d"], b["D"], b["T"]],
    C_kN=b["C_kN"], C0_kN=b["C0_kN"], ratings_note="typical catalogue values, confirm with supplier",
    s0_front=round(b["C0_kN"] * 1e3 / F_STATIC[0], 1), s0_rear=round(b["C0_kN"] * 1e3 / F_STATIC[1], 1),
    s0_axial_parked=round(b["C0_kN"] * 1e3 / (F_AX_PARKED / b["Y0"] * 0.5 + F_AX_PARKED), 1),
    equivalent_load_kN=[p / 1e3 for p in P_eq],
    L10_million_rev=[round(x / 1e6) for x in L10],
    L10_target_million_rev=round(L10_TARGET / 1e6),
    life_factor=[round(x / L10_TARGET, 1) for x in L10],
    fits=dict(cups="Ø210 P7 (rotating outer-ring load): interference 0.006 to 0.079",
              front_cone="Ø140 f6 (stationary inner ring, point load, slides for preload): clearance 0.018 to 0.068",
              rear_cone="Ø140 j6 against shoulder Ø155"),
    preload="axial preload 2 to 4 kN, set as −0.02 to −0.05 mm end play with the KMT 27 nut; "
            "verified by bearing rolling torque before seals are fitted",
)

# ------------------------------------------------------------- spindle
def W(do, di):
    return math.pi * (do ** 4 - di ** 4) / (32 * do)


sec = {}
# moment at a station x: hub moment + (rotor-side shear) x lever; conservative shear 15 kN
# (SLM parked thrust is axial; in-plane parked force 8 kN x 1.35, rotor weight)
F_SHEAR = 15e3
for name, x, do, kt in [("rear seat Ø140 (x 360)", 360, 140, 1.0),
                        ("cone shoulder Ø155/140 R2.5 (x 382.5)", 382.5, 140, 1.9),
                        ("flange fillet Ø150 R10 (x 430)", 430, 150, 1.45),
                        ("thread relief M135 (x 80)", 80, 132.4, 2.5)]:
    m = M_HUB + F_SHEAR * x / 1e3 if x > 150 else F_SHEAR * x / 1e3 * 0.5
    s_nom = m * 1e3 / W(do, 90)
    sec[name] = dict(M_kNm=round(m / 1e3, 1), sigma_nom_MPa=round(s_nom, 1), Kt=kt,
                     sigma_peak_MPa=round(s_nom * kt, 1))
Rp = 650.0
res["spindle"] = dict(
    sections=sec, yield_MPa=Rp,
    static_reserve_min=round(Rp / 1.1 / max(v["sigma_peak_MPa"] for v in sec.values()), 1),
)
# fatigue: rotating-bending-equivalent amplitude assumed 50 % of the design moment at 1e9 cycles
# (very conservative; doc 08 DELs are lower). Endurance of 42CrMo4+QT: 0.45 Rm = 430 MPa,
# size 0.8, surface (ground/rolled) 0.9, reliability 0.8, gamma_M 1.25.
s_e = 0.45 * 950 * 0.8 * 0.9 * 0.8 / 1.25
amp = max(v["sigma_peak_MPa"] for v in sec.values()) * 0.5
res["spindle"]["fatigue"] = dict(endurance_allow_MPa=round(s_e), worst_amplitude_MPa=round(amp, 1),
                                 reserve=round(s_e / amp, 1))
mass_sp = next(it.mass for it in G.mass_table() if "Spindle" in it.name)
res["spindle"]["mass_kg"] = round(mass_sp, 1)

# ------------------------------------------------------------- bolted joints
# Standard preloads/torques at mu 0.12, 90 % yield utilisation (VDI 2230 table values)
BOLT = {"M8 A4-80": (14e3, 22), "M10 10.9": (43e3, 65), "M12 10.9": (63e3, 110),
        "M16 10.9": (117e3, 280), "M20 10.9": (184e3, 540)}


def joint(name, size, n, pcd, torque, shear=0.0, moment=0.0, axial=0.0, mu=0.2, fm_factor=0.7):
    Fm = BOLT[size][0] * fm_factor        # tightening scatter alpha_A 1.6 -> minimum preload
    r = pcd / 2e3
    slip_cap = n * Fm * mu
    demand = torque / r + shear
    f_bolt_ext = 4 * moment / (n * pcd / 1e3) + axial / n
    return dict(joint=name, bolts=f"{n}x {size}", pcd_mm=pcd, tightening_Nm=BOLT[size][1],
                min_preload_kN=round(Fm / 1e3, 1), slip_capacity_kN=round(slip_cap / 1e3, 1),
                slip_demand_kN=round(demand / 1e3, 1), slip_factor=round(slip_cap / max(demand, 1), 1),
                max_external_axial_per_bolt_kN=round(f_bolt_ext / 1e3, 1),
                separation_factor=round(Fm / max(f_bolt_ext, 1), 1))


res["bolted_joints"] = [
    joint("spindle flange to bedplate", "M20 10.9", 12, 350, T_SC, shear=F_SHEAR, moment=TILT_YAW,
          axial=F_AX_PARKED),
    joint("stator carrier to spindle flange (thermal paste, mu 0.1)", "M12 10.9", 12, 240, T_SC,
          shear=1.2e3 * 9.81 / 10, mu=0.10),
    joint("hub to drum web (doc 13)", "M16 10.9", 12, 400, T_SLM_G, shear=20e3, moment=M_HUB,
          axial=F_AX_PARKED, mu=0.3, fm_factor=110e3 / 117e3),
    joint("brake disc to drum flange ring", "M12 10.9", 24, 662, T_SLM_G),
    joint("rear cover to drum (non-structural)", "M10 10.9", 24, 644, 0.0, shear=0.5e3),
]

# ------------------------------------------------------------- stator fit
lam_d = 2 * G.GEN["r_si"]
d_alpha = 23e-6 - 11.5e-6
res["stator_fit"] = dict(
    lamination_bore_mm=lam_d,
    aluminium_carrier_fit_change_at_minus40_mm=round(-d_alpha * 60 * lam_d, 2),
    aluminium_carrier_fit_change_at_plus80_mm=round(d_alpha * 60 * lam_d, 2),
    decision="steel carrier: same expansion as the laminations, interference 0 to 0.05 at all temperatures",
)

# ------------------------------------------------------------- cooling path
# heat from stack -> steel carrier rim/web -> bolted face -> spindle flange -> spindle tube,
# which acts as a fin cooled by the finned insert (U-flow).
k_st, k_al = 48.0, 170.0
r_si = G.GEN["r_si"] / 1e3
R_stack_contact = 1 / (3000 * 2 * math.pi * r_si * 0.074)              # shrink fit, h = 3000 W/m2K
R_web = math.log(r_si / 0.150) / (2 * math.pi * k_st * 0.025)
R_bolted = 1 / (3000 * math.pi * (0.150 ** 2 - 0.090 ** 2))            # Al-filled paste
R_flange = math.log(0.150 / 0.075) / (2 * math.pi * k_st * 0.030)
ins = G.INSERT
P_wet = (math.pi * 0.082 + math.pi * 0.040 + ins["fins"] * 2 * 0.021)  # m, wetted perimeter
A_flow = (math.pi / 4 * (0.082 ** 2 - 0.040 ** 2) - ins["fins"] * 0.0025 * 0.021)
Dh = 4 * A_flow / P_wet
kA = k_st * math.pi / 4 * (0.140 ** 2 - 0.090 ** 2) + k_al * (math.pi / 4 * (0.090 ** 2 - 0.082 ** 2)
                                                              + ins["fins"] * 0.0025 * 0.021)


def bore(v_air):
    Re = v_air * Dh / 1.6e-5
    Nu = 0.023 * Re ** 0.8 * 0.71 ** 0.4
    h = Nu * 0.026 / Dh
    hP = h * P_wet * 0.85                      # 0.85 for fin efficiency and contact
    m = math.sqrt(hP / kA)
    R_fin = 1 / (math.sqrt(hP * kA) * math.tanh(m * 0.39))
    flow = v_air * A_flow / 2                  # U-flow: half the cells each way
    dT_air = 600 / (1.2 * 1005 * flow)         # K for 600 W through this path
    dp = 0.03 * (2 * 0.42) / Dh * 0.5 * 1.2 * v_air ** 2 + 1.5 * 0.5 * 1.2 * v_air ** 2
    return R_fin, flow, dT_air, dp, h


cool = {}
for v_air in (12.0, 10.0, 7.0, 5.0):
    R_fin, flow, dT_air, dp, h = bore(v_air)
    R_tot = R_stack_contact + R_web + R_bolted + R_flange + R_fin
    R_eff = R_tot + dT_air / 2 / 600
    cool[f"{v_air:.0f} m/s"] = dict(h_W_m2K=round(h), R_path_K_per_W=round(R_tot, 3),
                                    R_incl_air_rise_K_per_W=round(R_eff, 3),
                                    air_flow_m3_h=round(flow * 3600), air_rise_K=round(dT_air, 1),
                                    pressure_drop_Pa=round(dp), fan_air_power_W=round(dp * flow, 1))
res["cooling_path"] = dict(target_K_per_W=0.40, elements_K_per_W=dict(
    stack_to_carrier=round(R_stack_contact, 4), carrier_web=round(R_web, 4), bolted_face=round(R_bolted, 4),
    spindle_flange=round(R_flange, 4)), cases=cool,
    note="doc 07 had 0.17 to 0.25 K/W with an aluminium carrier shrunk directly on the spindle "
         "and the full bore length counted; this layout routes heat through the flange, so the "
         "spindle works as a fin. Still meets 0.40 K/W; measured on the bench (doc 15, T5).")

# ------------------------------------------------------------- air gap budget (radial, mm)
gap = {"bearing run-out (P5 class recommended, preloaded)": 0.010,
       "spindle seats to flange/spigot run-out": 0.010,
       "carrier stack seat to bolting face": 0.020,
       "stack OD run-out to bore (laser cut + bonded)": 0.050,
       "drum cup seats to magnet seat coaxiality": 0.020,
       "magnet thickness + bond line variation": 0.050,
       "spindle + bearing deflection at 9.8 kNm (tilt of drum vs stator)": 0.040,
       "magnetic pull amplification (1 / (1 - k_mag/k_struct))": 0.005}
gap_rss = math.sqrt(sum(v ** 2 for v in gap.values()))
gap_lin = sum(gap.values())
res["air_gap_budget"] = dict(items_mm=gap, worst_case_sum_mm=round(gap_lin, 3), rss_mm=round(gap_rss, 3),
                             limit_mm=0.20, nominal_gap_mm=G.GEN["gap"])

# ------------------------------------------------------------- magnets and assembly forces
Bg = 0.92                       # T, peak gap flux density (FEA no-load)
p_mag = (Bg / math.sqrt(2)) ** 2 / (2 * 4e-7 * math.pi) * 1.15   # Pa, average incl. harmonics
A_gap = 2 * math.pi * 0.300 * 0.074
k_mag = 1.91e3                  # N/mm, doc 07
res["magnet_forces"] = dict(
    average_magnetic_pressure_kPa=round(p_mag / 1e3), total_radial_attraction_kN=round(p_mag * A_gap / 1e3),
    unbalanced_pull_per_mm_kN=k_mag / 1e3,
    pull_at_1_8mm_offset_kN=round(k_mag * 1.8 / (1 - 0.9 * 0.5) / 1e3, 1),
    note="the drum must be guided coaxially (tool NP1-T01) before the magnets reach the stator; "
         "one magnet piece to a steel surface at 10 mm gap pulls about 50 to 80 N")

# ------------------------------------------------------------- brake, lock, disc
res["brake"] = dict(
    disc_od_id_mm=[G.DISC["od"], G.DISC["id"]], effective_radius_m=0.37,
    clamp_per_caliper_kN_at_mu_0_4=round(T_BRAKE / (2 * 2 * 0.4 * 0.37) / 1e3, 1),
    energy_from_250rpm_kJ=74, disc_bulk_temperature_rise_K=round(74e3 / (22.7 * 460), 1),
    lock_pin_shear_MPa=round(T_BRAKE / 0.331 / (math.pi / 4 * 25 ** 2), 1),
    lock_pin_bearing_MPa=round(T_BRAKE / 0.331 / (25 * 40), 1))

# ------------------------------------------------------------- bench drive
n_max = 275.0
res["bench_drive"] = dict(
    rated_mech_power_kW=round(T_RATED * 178 * 2 * math.pi / 60 / 1e3, 1),
    torque_needed_Nm=round(1.25 * T_RATED), motor="37 kW 4-pole induction, 240 Nm, inverter fed",
    gearbox_ratio=6, output_torque_continuous_Nm=round(240 * 6 * 0.97),
    output_speed_at_base_rpm=round(1480 / 6), motor_speed_at_275rpm=round(n_max * 6),
    torque_transducer="2 kNm flange, accuracy class 0.05 (≈ 0.5 % of rated power error budget for efficiency)",
    energy="common DC bus between drive inverter and generator load inverter; grid supplies losses only")

# ------------------------------------------------------------- masses
items = G.mass_table()
tot = sum(i.mass for i in items)
res["masses_kg"] = {i.name: round(i.mass, 1) for i in items}
res["masses_kg"]["total_drivetrain_no_hub"] = round(tot, 1)
res["masses_kg"]["doc07_budget_same_scope"] = 60 + 75 + 45 + 10
res["masses_kg"]["note"] = ("P1 is machined and fabricated for low risk and short lead time; "
                            "the cast and FEA-optimised P2 drum, carrier and bedplate must recover "
                            "most of the difference (tower update pending, doc 13 section 8)")

OUT.mkdir(exist_ok=True)
(OUT / "detail_summary.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
print(json.dumps(res, indent=1, ensure_ascii=False))
