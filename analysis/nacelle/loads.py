"""Concept loads and sizing for hub, main bearings, spindle, brake and yaw.

Run:  python3 loads.py      (writes results/summary.json)

Concept-level, quasi-static: steady BEM results (analysis/rotor) times
dynamic factors, plus first-principles storm, ice, fault and gyroscopic
cases. Replaced later by aeroelastic DLC results (docs/02 section 5).
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "rotor"))
from bem import Blade, ROUGH, solve  # noqa: E402

OUT = HERE / "results"
OUT.mkdir(exist_ok=True)
G = 9.81

# ------------------------------------------------------------ assumptions
R = 3.75
N_RATED, N_OVER = 178.0, 230.0
M_BLADE = 20.0          # kg, glass/epoxy 3.35 m blade (estimate, TBC by layup study)
R_CG_BLADE = 1.55       # m, blade centre of gravity radius
RG_BLADE = 1.85         # m, radius of gyration about rotor axis
M_HUB = 80.0            # kg, hub casting + 3 pitch systems
M_DRUM = 60.0           # kg, generator rotor: yoke, magnets, drum, covers, brake disc
M_STATOR = 75.0         # kg, stator core, winding, aluminium carrier
M_SPINDLE = 45.0        # kg
M_FRAME = 70.0          # kg, nacelle bedplate
M_YAW = 45.0            # kg, yaw bearing, drives, brake
M_COVER = 20.0          # kg, nacelle cover, electrics in nacelle
M_MISC = 25.0           # kg, slip ring, sensors, cabling, cooling fan, seals

# Axial positions along the spindle (x = 0 at rotor centre, + towards tower)
X_ROTOR = 0.0
X_BRG_FRONT = 0.12
X_BRG_REAR = 0.36       # bearing spacing 0.24 m
X_DRUM_CG = 0.30
X_STATOR = 0.38
X_TOWER = 0.75          # yaw axis behind rotor centre (overhang)

# Gamma: partial safety factor on loads used with these concept loads
GAMMA_F = 1.35
DYN = 1.5               # dynamic amplification on steady values (until aeroelastic)

RHO_COLD = 1.35
V_E50, V_E1 = 77.0, 58.0
CD_FLAT = 1.8


def blade_geometry():
    b = Blade(R=R, tsr_design=6.5, cl_design=1.0)
    return b


def rotor_inertia():
    I_bl = 3 * M_BLADE * RG_BLADE ** 2
    I_hub = 0.5 * M_HUB * 0.35 ** 2
    I_drum = M_DRUM * 0.31 ** 2
    return I_bl + I_hub + I_drum


# ------------------------------------------------------------ storm cases
def parked_broadside(b, V, rho=RHO_COLD, n_az=72):
    """Wind in the rotor plane (yaw error 90 deg), blades feathered so the
    flat side faces the wind component normal to each blade. Returns max over
    azimuth of: rotor torque (holding torque for the brake) and in-plane force."""
    best_T, best_F = 0.0, 0.0
    for az in np.linspace(0, 2 * math.pi / 3, n_az, endpoint=False):
        T = 0.0; Fy = 0.0
        for k in range(3):
            psi = az + k * 2 * math.pi / 3
            e = np.array([0.0, math.sin(psi), math.cos(psi)])     # blade span unit vector
            w = np.array([0.0, 1.0, 0.0])                         # wind direction
            wn = w - np.dot(w, e) * e                             # normal component direction
            vn = V * np.linalg.norm(wn)
            if vn < 1e-9:
                continue
            fdir = wn / np.linalg.norm(wn)
            q = 0.5 * rho * vn ** 2 * CD_FLAT
            dF = q * b.chord * b.dr                               # per element
            F = dF.sum()
            Fy += F * fdir[1]
            M = np.cross(e * np.sum(dF * b.r) / F, fdir) * F       # moment about hub
            T += M[0]
        best_T = max(best_T, abs(T)); best_F = max(best_F, abs(Fy))
    return best_T, best_F


def one_blade_fine_pitch_flap(b, V, rho=RHO_COLD):
    """One blade stuck near fine pitch (DLC 7.1), parked, wind along the axis:
    the blade is broadside to the wind. Root flap moment and force."""
    q = 0.5 * rho * V ** 2 * CD_FLAT
    dF = q * b.chord * b.dr
    return float(np.sum(dF * (b.r - b.r_hub))), float(dF.sum()), float(np.sum(dF * b.r))


def torque_one_blade_fine(b, V, rpm):
    """Aerodynamic torque with one blade at fine pitch (others feathered): 1/3 of
    a full rotor at fine pitch (BEM, rough polars)."""
    om = rpm * 2 * math.pi / 60
    res = solve(b, V, om, 0.0, 1.225, ROUGH)
    return res.torque / 3


def torque_all_fine(b, V, rpm):
    om = rpm * 2 * math.pi / 60
    return solve(b, V, om, 0.0, 1.225, ROUGH).torque


# ------------------------------------------------------------ ice (IEC 61400-1 cold climate)
def ice_mass(b):
    """Ice on one blade: mu_E = rho_ice * k * c_min * (c_min + c_max); linear from 0 at the
    rotor axis to mu_E at R/2, constant to the tip."""
    rho_ice = 700.0
    c_max, c_min = float(b.chord.max()), float(b.chord[-1])
    k = 0.00675 + 0.3 * math.exp(-0.32 * R / 1.0)
    mu = rho_ice * k * c_min * (c_min + c_max)
    mu_r = np.where(b.r < R / 2, mu * b.r / (R / 2), mu)
    m = float(np.sum(mu_r * b.dr))
    r_cg = float(np.sum(mu_r * b.dr * b.r) / m)
    return m, r_cg, mu


# ------------------------------------------------------------ bearings
def bearing_reactions(Fx, Fy, Fz, My, Mz):
    """Hub loads at rotor centre -> radial reactions at front and rear bearing
    (simply supported pair on the spindle). Returns (Fr_front, Fr_rear, Fa)."""
    a, c = X_BRG_FRONT - X_ROTOR, X_BRG_REAR - X_ROTOR
    s = c - a
    def split(F, M):
        # moment about the rear bearing: F*(c) + M = R_f * s
        Rf = (F * c + M) / s
        Rr = F - Rf
        return Rf, Rr
    Rfy, Rry = split(Fy, -Mz)
    Rfz, Rrz = split(Fz, My)
    return math.hypot(Rfy, Rfz), math.hypot(Rry, Rrz), abs(Fx)


def read_power_curve():
    rows = list(csv.DictReader(open(HERE.parent / "rotor" / "results" / "power_curve_D7.5_rough.csv")))
    return [{k: float(v) for k, v in r.items()} for r in rows]


def main():
    b = blade_geometry()
    I_rot = rotor_inertia()
    m_rotor_overhang = 3 * M_BLADE + M_HUB
    res = {}

    # --- mass budget
    masses = dict(blades=3 * M_BLADE, hub_and_pitch=M_HUB, generator_rotor_drum=M_DRUM,
                  generator_stator_and_carrier=M_STATOR, spindle=M_SPINDLE, bedplate=M_FRAME,
                  yaw_system=M_YAW, cover_and_electrics=M_COVER, misc=M_MISC)
    res["mass_budget_kg"] = dict(masses, tower_top_total=sum(masses.values()))
    res["rotor_inertia_kgm2"] = round(I_rot)

    # --- storm and fault cases
    T_hold_e50, F_inplane_e50 = parked_broadside(b, V_E50)
    M_flap_e1, F_bl_e1, M_hub_e1 = one_blade_fine_pitch_flap(b, V_E1)
    m_ice, r_ice, mu_ice = ice_mass(b)
    w_r = N_RATED * 2 * math.pi / 60
    F_ice_cf = m_ice * r_ice * w_r ** 2
    w_yaw = 5 * math.pi / 180     # fault yaw rate
    M_gyro = I_rot * w_r * w_yaw
    pc = read_power_curve()
    T_op_max = max(r["thrust"] for r in pc if r["V"] <= 30)
    Mflap_op_max = max(r["M_flap"] for r in pc if r["V"] <= 30)

    # tilt / yaw moment at hub from asymmetric aerodynamic load (turbulence, shear,
    # yaw error): take one blade at max operating flap moment as unbalanced,
    # times dynamic factor
    M_asym_op = DYN * Mflap_op_max * 1.0

    W_rot = m_rotor_overhang * G
    W_drum = M_DRUM * G
    # express drum weight as equivalent at rotor centre plus moment about rotor centre
    cases = {
        "U1_operating_gust": dict(Fx=DYN * T_op_max, Fz=-(W_rot + W_drum),
                                   My=-W_drum * X_DRUM_CG + M_asym_op, Mz=M_asym_op * 0.5),
        "U2_one_blade_stuck_fine_Ve1": dict(Fx=F_bl_e1, Fz=-(W_rot + W_drum),
                                             My=-W_drum * X_DRUM_CG + M_hub_e1, Mz=0.0),
        "U3_parked_broadside_Ve50": dict(Fx=0.0, Fy=F_inplane_e50, Fz=-(W_rot + W_drum),
                                          My=-W_drum * X_DRUM_CG, Mz=0.0),
        "U4_ice_one_blade_operating": dict(Fx=DYN * T_op_max, Fz=-(W_rot + W_drum + m_ice * G) - F_ice_cf,
                                            My=-W_drum * X_DRUM_CG + M_asym_op, Mz=0.0),
        "U5_gyroscopic_yaw_fault": dict(Fx=DYN * T_op_max, Fz=-(W_rot + W_drum),
                                         My=-W_drum * X_DRUM_CG + M_gyro, Mz=M_asym_op),
    }
    ult = {}
    worst_front = worst_rear = 0.0
    for name, c in cases.items():
        Fx, Fy, Fz = c.get("Fx", 0), c.get("Fy", 0), c.get("Fz", 0)
        My, Mz = c.get("My", 0), c.get("Mz", 0)
        Rf, Rr, Fa = bearing_reactions(Fx, Fy, Fz, My, Mz)
        M_res = math.hypot(My, Mz)
        ult[name] = dict(Fx_kN=round(Fx / 1e3, 2), Fy_kN=round(Fy / 1e3, 2), Fz_kN=round(Fz / 1e3, 2),
                         M_hub_kNm=round(M_res / 1e3, 2),
                         front_bearing_radial_kN=round(GAMMA_F * Rf / 1e3, 2),
                         rear_bearing_radial_kN=round(GAMMA_F * Rr / 1e3, 2),
                         axial_kN=round(GAMMA_F * Fa / 1e3, 2))
        worst_front = max(worst_front, GAMMA_F * Rf); worst_rear = max(worst_rear, GAMMA_F * Rr)
    res["ultimate_cases_design_values"] = ult
    res["storm_and_fault_inputs"] = dict(
        parked_Ve50_holding_torque_kNm=round(T_hold_e50 / 1e3, 2),
        parked_Ve50_inplane_force_kN=round(F_inplane_e50 / 1e3, 2),
        one_blade_fine_Ve1_root_flap_kNm=round(M_flap_e1 / 1e3, 2),
        ice_mass_one_blade_kg=round(m_ice, 1), ice_mu_tip_kg_per_m=round(mu_ice, 2),
        ice_imbalance_centrifugal_kN=round(F_ice_cf / 1e3, 2),
        gyroscopic_moment_5deg_s_kNm=round(M_gyro / 1e3, 2),
        max_operating_thrust_steady_kN=round(T_op_max / 1e3, 2))

    # --- bearing fatigue (Rayleigh, V_ave = 10 m/s at hub: Class S fatigue)
    vave = 10.0
    c = vave / math.gamma(1.5)
    dv = pc[1]["V"] - pc[0]["V"]
    hours = 20 * 8760 * 0.97
    p_exp = 10 / 3
    sum_n, sum_pn_f, sum_pn_r = 0.0, 0.0, 0.0
    e_tr, Y_tr = 0.37, 1.6           # typical single-row tapered roller bearing factors
    for r in pc:
        V = r["V"]
        if V > 30 or r["rpm"] <= 0:
            continue
        f = (2 / c) * (V / c) * math.exp(-(V / c) ** 2) * dv
        revs = r["rpm"] * 60 * hours * f
        # loads in this bin: gravity, mean thrust (axial), rotating/turbulent hub moment
        Fx = r["thrust"]
        M_turb = 0.5 * r["M_flap"]   # equivalent cyclic hub moment from turbulence & shear (assumption)
        Rf, Rr, Fa = bearing_reactions(Fx, 0.0, -(W_rot + W_drum), -W_drum * X_DRUM_CG + M_turb, 0.0)
        # O-arrangement: front bearing takes thrust towards tower
        Pf = Rf if Fa / max(Rf, 1) <= e_tr else 0.4 * Rf + Y_tr * Fa
        Pr = Rr
        sum_n += revs
        sum_pn_f += revs * Pf ** p_exp
        sum_pn_r += revs * Pr ** p_exp
    Peq_f = (sum_pn_f / sum_n) ** (1 / p_exp)
    Peq_r = (sum_pn_r / sum_n) ** (1 / p_exp)
    L_target = 2 * sum_n / 1e6             # million revolutions, 2 x design life (R5.1)
    a_iso = 1.0                            # no life modification credit (quality-first)
    C_req_f = Peq_f * (L_target / a_iso) ** (1 / p_exp)
    C_req_r = Peq_r * (L_target / a_iso) ** (1 / p_exp)
    res["bearings"] = dict(
        arrangement="pair of single-row tapered roller bearings, back-to-back (O), preloaded",
        revolutions_20y_million=round(sum_n / 1e6, 1),
        target_L10_million_rev=round(L_target, 1),
        front_equivalent_load_kN=round(Peq_f / 1e3, 2), rear_equivalent_load_kN=round(Peq_r / 1e3, 2),
        front_C_required_kN=round(C_req_f / 1e3, 1), rear_C_required_kN=round(C_req_r / 1e3, 1),
        front_static_design_load_kN=round(worst_front / 1e3, 1),
        rear_static_design_load_kN=round(worst_rear / 1e3, 1),
        note="Static safety factor s0 >= 2 on C0 against the design static loads (quality-first choice)")

    # --- spindle
    D_o, D_i = 0.140, 0.090
    W_b = math.pi * (D_o ** 4 - D_i ** 4) / (32 * D_o)
    I_s = math.pi * (D_o ** 4 - D_i ** 4) / 64
    E = 210e9
    # bending moment at the rear bearing seat / flange (worst ultimate case)
    M_spindle = 0.0
    for name, cse in cases.items():
        Fz = cse.get("Fz", 0); Fy = cse.get("Fy", 0)
        My, Mz = cse.get("My", 0), cse.get("Mz", 0)
        Mb = math.hypot(Fz * X_BRG_REAR + My, Fy * X_BRG_REAR - Mz)
        # add stator weight on the spindle behind the rear bearing (lever to flange)
        M_spindle = max(M_spindle, GAMMA_F * Mb)
    sigma = M_spindle / W_b
    Re_42CrMo4 = 650e6          # 42CrMo4+QT, 100-160 mm section, minimum yield (EN 10083-3)
    res["spindle"] = dict(material="42CrMo4+QT", OD_mm=D_o * 1e3, bore_mm=D_i * 1e3,
                          design_bending_moment_kNm=round(M_spindle / 1e3, 2),
                          bending_stress_MPa=round(sigma / 1e6, 1),
                          yield_MPa=Re_42CrMo4 / 1e6,
                          reserve_factor_yield=round(Re_42CrMo4 / 1.1 / sigma, 2))

    # --- air gap stiffness: drum (rotating, on bearings) vs stator (on spindle)
    # magnetic negative stiffness ~ (B^2/2mu0) * pi R L / g_eff
    B_avg2 = 0.92 ** 2 * 0.8
    g_eff = 0.0025 + 0.0077 / 1.05
    k_mag = B_avg2 / (2 * 4e-7 * math.pi) * math.pi * 0.30 * 0.074 / g_eff
    # spindle cantilever from flange (x = X_TOWER - 0.15) to stator (x = X_STATOR): gravity deflection
    L_cant = (X_TOWER - 0.15) - X_STATOR
    k_spindle_stator = 3 * E * I_s / L_cant ** 3
    res["air_gap_stiffness"] = dict(
        magnetic_negative_stiffness_kN_per_mm=round(k_mag / 1e6, 2),
        spindle_stiffness_at_stator_kN_per_mm=round(k_spindle_stator / 1e6, 1),
        ratio=round(k_spindle_stator / k_mag, 1),
        stator_sag_from_own_weight_mm=round(M_STATOR * G / (k_spindle_stator - k_mag) * 1e3, 4),
        requirement="eccentricity <= 0.2 mm (10 % of gap); structural stiffness >= 10 x magnetic")

    # --- brake
    T_fine_one = max(torque_one_blade_fine(b, V, rpm) for V in (15, 20, 25, 30) for rpm in (60, 120, 178, 230))
    T_fine_all = max(torque_all_fine(b, V, rpm) for V in (15, 20, 25) for rpm in (60, 120, 178, 230))
    E_kin = 0.5 * I_rot * (N_OVER * 2 * math.pi / 60) ** 2
    T_brake_req = max(1.5 * T_hold_e50, 1.5 * T_fine_one)
    r_brake = 0.30
    mu_pad = 0.35
    F_clamp_per_caliper = T_brake_req / (2 * mu_pad * r_brake * 2)   # 2 calipers, 2 friction faces each
    res["brake"] = dict(
        concept="spring-applied, hydraulically released calipers on a disc at the generator drum (r = 0.30 m)",
        holding_torque_parked_Ve50_kNm=round(T_hold_e50 / 1e3, 2),
        aero_torque_one_blade_stuck_fine_max_kNm=round(T_fine_one / 1e3, 2),
        aero_torque_all_blades_fine_max_kNm=round(T_fine_all / 1e3, 2),
        required_brake_torque_kNm=round(T_brake_req / 1e3, 2),
        clamp_force_per_caliper_kN=round(F_clamp_per_caliper / 1e3, 1),
        kinetic_energy_at_overspeed_kJ=round(E_kin / 1e3, 1))

    # --- yaw: overturning moment at the yaw bearing and yaw holding torque
    H_HUB = 0.45            # rotor axis height above yaw bearing [m]
    W_nac_rear = (M_STATOR + M_SPINDLE + M_FRAME + M_COVER + M_MISC) * G   # roughly at 0.45 m from rotor
    M_tilt_max, M_yawtorque_max = 0.0, 0.0
    for name, cse in cases.items():
        Fx, Fy, Fz = cse.get("Fx", 0), cse.get("Fy", 0), cse.get("Fz", 0)
        My, Mz = cse.get("My", 0), cse.get("Mz", 0)
        # tilt about the yaw bearing: rotor-side weight ahead of the yaw axis, thrust above it
        M_tilt = abs(Fz) * X_TOWER - W_nac_rear * (X_TOWER - 0.45) + abs(My) + abs(Fx) * H_HUB
        M_yt = abs(Fy) * X_TOWER + abs(Mz)
        M_tilt_max = max(M_tilt_max, GAMMA_F * M_tilt)
        M_yawtorque_max = max(M_yawtorque_max, GAMMA_F * M_yt)
    # nacelle side drag at Ve50 (cover + drum side area ~1.2 m2, Cd 1.2) acting ~0.1 m behind yaw axis
    F_side = 0.5 * RHO_COLD * V_E50 ** 2 * 1.2 * 1.2
    M_yawtorque_max = max(M_yawtorque_max, GAMMA_F * (cases["U3_parked_broadside_Ve50"]["Fy"] * X_TOWER - F_side * 0.10))
    res["yaw"] = dict(
        concept="active yaw: four-point contact ball slewing ring, 2 geared motors, spring-applied yaw brake with controlled slip",
        tilt_moment_at_yaw_bearing_design_kNm=round(M_tilt_max / 1e3, 1),
        yaw_holding_torque_design_kNm=round(M_yawtorque_max / 1e3, 1),
        nacelle_side_drag_Ve50_kN=round(F_side / 1e3, 1),
        tower_top_weight_kN=round(sum(masses.values()) * G / 1e3, 2),
        yaw_rate="0.5 deg/s in operation; 5 deg/s analysed as a fault")

    # --- spindle bore cooling path (generator thermal requirement <= 0.40 K/W)
    r_in_core = 0.299 - 0.004 - 0.065 - 0.0114
    t_carrier, k_al = 0.025, 150.0
    R_carrier = math.log(r_in_core / (D_o / 2)) / (2 * math.pi * k_al * t_carrier)
    R_contact = 1e-4 / (2 * math.pi * r_in_core * 0.074) + 1e-4 / (2 * math.pi * D_o / 2 * 0.06)
    R_wall = math.log(D_o / D_i) / (2 * math.pi * 42 * 0.30)
    def bore_R(V_air, fin_factor):
        Re = V_air * D_i / 1.6e-5
        Nu = 0.023 * Re ** 0.8 * 0.71 ** 0.4
        h = Nu * 0.026 / D_i
        return 1 / (h * math.pi * D_i * 0.30 * fin_factor)
    res["cooling_path"] = dict(
        target_K_per_W=0.40,
        carrier_K_per_W=round(R_carrier, 3), contacts_K_per_W=round(R_contact, 4),
        spindle_wall_K_per_W=round(R_wall, 3),
        total_plain_bore_10ms_K_per_W=round(R_carrier + R_contact + R_wall + bore_R(10, 1), 3),
        total_finned_insert_10ms_K_per_W=round(R_carrier + R_contact + R_wall + bore_R(10, 3), 3),
        total_finned_insert_5ms_K_per_W=round(R_carrier + R_contact + R_wall + bore_R(5, 3), 3))

    (OUT / "summary.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
