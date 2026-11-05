"""Collective pitch system with spring feathering and a welded hub (doc 24).

Replaces the three independent electric pitch drives of doc 13 (Martin,
2026-11-05: "simplify, this is too much for a 12 kW windmill"; chose one
collective actuator with spring feathering).

Mechanism (blade-local frame: x = rotor axis, rearward positive; s = distance
from the rotor axis along the pitch axis; y = tangential):

  nose housing (in the spinner, bolted to the hub front plate)
    gas springs ──► carriage ──(latched by a pawl held by a power-on solenoid)
                      └─ electric cylinder (ball screw, servo, holding brake)
                            └─ rod ──► yoke (3 arms, guided on 2 rods)
                                         └─ 3 links (rod ends, turnbuckle)
                                               └─ crank pin on each blade root

Normal operation: carriage latched, the electric cylinder moves the yoke and so
all three blades together. Trip (safety chain opens, power lost): the solenoid
drops, the pawl releases the carriage and the gas springs pull the whole
carriage + cylinder + yoke forward, feathering all blades; a hydraulic speed
damper sets the rate (about 30 deg/s). No electronics or software in that
path. Re-cocking: with the blades on the feather stop the cylinder retracts,
which pushes the carriage back against the springs until the pawl engages.

Inputs reused from hub.py (doc 13): pitch moments, bearing friction, loads.
Run:  python3 collective.py   (writes results/collective_summary.json)
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

import hub as H   # doc 13 models (pitch moments, bearing, loads)

OUT = Path(__file__).parent / "results"

# ------------------------------------------------------------------ geometry (mm, deg)
TH_FINE, TH_FEATHER = -2.0, 92.0          # working range between the limit switches (doc 13: -2 / 91, stops -3 / 93)
TH_MID = (TH_FINE + TH_FEATHER) / 2
R_C = 110.0          # crank radius about the pitch axis
S_P = 118.0          # link eye plane on the crank pin: distance from the rotor axis along the pitch axis
PHI0 = 5.0           # crank phase: arc -42..+52 deg about the stroke centre, keeps the pin 8 mm clear of the
                     # drum bearing housing (x 92) at fine pitch (clash check, cad/hub_c)
R_Y = 110.0          # yoke arm eye: distance from the rotor axis
L_LINK = 220.0       # link length between spherical eye centres (turnbuckle +-6 mm = +-3 deg blade setting)
ETA_LINK = 0.95      # rod ends + guide friction

T_K = dict(cold=243.15, ref=293.15, hot=313.15)      # -30 C (lowest operating), +20 C, +40 C in the hub


def pin(theta):
    """Crank pin centre (x, s, y) in the blade frame. Feathering moves the pin forward (-x)."""
    a = math.radians(theta - TH_MID + PHI0)
    return np.array([-R_C * math.sin(a), S_P, -R_C * math.cos(a)])


def yoke_eye_angle():
    """Place the yoke eye on the mean angular position of the pin around the rotor axis."""
    p = pin(TH_MID)
    return math.atan2(-p[2], p[1])


BETA = yoke_eye_angle()


def yoke_x(theta):
    p = pin(theta)
    s_y, y_y = R_Y * math.cos(BETA), -R_Y * math.sin(BETA)
    d2 = L_LINK ** 2 - (p[1] - s_y) ** 2 - (p[2] - y_y) ** 2
    return p[0] - math.sqrt(d2), np.array([p[0] - math.sqrt(d2), s_y, y_y])


def kinematics():
    th = np.linspace(TH_FINE, TH_FEATHER, 189)
    xy = np.array([yoke_x(t)[0] for t in th])
    dxdth = np.gradient(xy, np.radians(th))            # mm per rad (negative: yoke moves forward)
    ang = []
    for t in th:
        p = pin(t)
        _, e = yoke_x(t)
        v = p - e
        ang.append(math.degrees(math.acos(abs(v[0]) / np.linalg.norm(v))))
    return th, xy, dxdth, np.array(ang)


# ------------------------------------------------------------------ loads per blade (doc 13 models)
def blade_torques():
    moments, J_blade = H.pitch_moments()
    brg = H.pitch_bearing()
    pm = moments[0.30]
    fr_c, fr_w = brg["friction_Nm"]["-30 C"], brg["friction_Nm"]["warm"]
    resist = 1.35 * abs(pm["worst_resisting_feather_Nm"])
    return dict(
        trip_design=fr_c["emergency_SLM_G"] + resist,     # both spring sets, SLM G edge moment, -30 C
        trip_single=fr_c["emergency_sim"] + resist,       # one spring set alone, simulated e-stop moment, -30 C
        trip_warm_min=fr_w["operating_mean"] - abs(pm["worst_resisting_operating_Nm"]),   # least resistance (sets the damper)
        normal_cold_eq=fr_c["operating_eq"],              # motor thermal
        normal_warm_mean=fr_w["operating_mean"],
        storm_hold=1.5 * abs(pm["storm_hold_Nm"]),
        J_blade=J_blade,
    ), brg


# ------------------------------------------------------------------ main sizing
def size():
    T, brg = blade_torques()
    th, xy, dxdth, ang = kinematics()
    stroke = float(xy.max() - xy.min())
    lever = np.abs(dxdth)                              # mm of yoke travel per rad of pitch
    lev_min = float(lever.min())

    def yoke_force(T_blade):                           # N, all three blades, along x
        return 3 * T_blade / (lever / 1e3) / ETA_LINK

    F_req_design = yoke_force(T["trip_design"])
    F_req_single = yoke_force(T["trip_single"])

    # ---- gas springs (nitrogen die springs, ISO 11901 type), two in parallel, each alone >= single-set case
    # spring stroke u = 0 latched (fine pitch) -> u = stroke (feather). Force rises with compression:
    # F(u) = F_ext * prog ** ((stroke - u) / stroke) (progression 1.30 over the stroke, die-spring practice)
    prog = 1.30
    u = xy.max() - xy                                  # carriage travel from the latched position, follows theta
    need_single = F_req_single * 1.20                  # 20 % function margin, one spring alone, -30 C
    need_both = F_req_design * 1.20
    shape = prog ** ((stroke - u) / stroke)            # >= 1, = 1 at full extension (feather)
    F_ext_ref = max(np.max(need_single / shape) * T_K["ref"] / T_K["cold"],
                    np.max(need_both / 2 / shape) * T_K["ref"] / T_K["cold"])   # per spring at +20 C, extended
    F_ext_ref = math.ceil(F_ext_ref / 500) * 500
    F_one = lambda Tk: F_ext_ref * shape * Tk / T_K["ref"]
    margin_single = float(np.min(F_one(T_K["cold"]) / F_req_single))
    margin_both = float(np.min(2 * F_one(T_K["cold"]) / F_req_design))
    F_latched_hot = float(2 * F_ext_ref * prog * T_K["hot"] / T_K["ref"])
    springs = dict(n=2, type="nitrogen gas spring (die spring, ISO 11901 type), low-temperature seals",
                   stroke_mm=round(stroke + 10), F_extended_20C_each_kN=round(F_ext_ref / 1e3, 1),
                   F_compressed_20C_each_kN=round(F_ext_ref * prog / 1e3, 1), progression=prog,
                   margin_one_spring_cold_vs_sim_estop=round(margin_single, 2),
                   margin_both_cold_vs_SLM_G=round(margin_both, 2),
                   F_latched_both_40C_kN=round(F_latched_hot / 1e3, 1),
                   energy_released_both_kJ=round(float(np.trapezoid(2 * F_one(T_K["ref"]), u)) / 1e6, 2),
                   cycles="trips and weekly tests only (about 2,000 in 20 years); the springs do not move in normal pitching")

    # ---- damper: sets the trip rate. Warm, least resistance, both springs at full force
    rate = 30.0                                         # deg/s
    v_max = float(np.max(lever) * math.radians(rate)) / 1e3   # m/s yoke speed at 30 deg/s
    F_spring_max = float(2 * F_ext_ref * prog * T_K["hot"] / T_K["ref"])
    F_damp = F_spring_max - float(np.min(yoke_force(max(T["trip_warm_min"], 0.0))))
    damper = dict(type="hydraulic speed controller (sealed, adjustable), in parallel with the springs",
                  v_design_m_s=round(v_max, 3), F_max_kN=round(F_damp / 1e3, 1),
                  c_Ns_per_m=round(F_damp / v_max), feather_time_s=round((TH_FEATHER - TH_FINE) / rate, 1),
                  end_buffer="industrial shock absorber on the carriage end stop + rubber blade stops at 93 deg")

    # ---- electric cylinder (normal pitching + re-cocking)
    F_norm_cold = float(np.max(yoke_force(T["normal_cold_eq"])))
    acc = math.radians(30.0) / 0.2
    F_norm_peak = float(np.max(yoke_force(T["normal_cold_eq"] * 1.35 + 3 * 0 + T["J_blade"] * acc)))
    F_recock = F_latched_hot * 1.10                    # push the carriage back against both springs, +10 %
    lead = 10.0e-3                                      # m, ball screw lead
    belt = 3.0                                          # motor-to-screw reduction (parallel belt)
    eta_screw = 0.90
    v_norm = float(np.max(lever)) * math.radians(15.0) / 1e3      # m/s at 15 deg/s
    n_motor = v_norm / lead * belt * 60
    T_motor_norm = F_norm_peak * lead / (2 * math.pi * eta_screw * belt)
    T_motor_cont = F_norm_cold * lead / (2 * math.pi * eta_screw * belt)
    T_motor_recock = F_recock * lead / (2 * math.pi * eta_screw * belt)
    act = dict(type="electric cylinder, ball screw, parallel servo motor with spring-applied holding brake",
               stroke_mm=round(stroke + 20), F_normal_cont_kN=round(F_norm_cold / 1e3, 2),
               F_normal_peak_kN=round(F_norm_peak / 1e3, 2), F_recock_kN=round(F_recock / 1e3, 1),
               F_rated_required_kN=round(F_recock / 1e3 + 0.5), lead_mm=lead * 1e3, belt_ratio=belt,
               v_15dps_m_s=round(v_norm, 3), motor_rpm_15dps=round(n_motor),
               motor_T_cont_Nm=round(T_motor_cont, 2), motor_T_peak_normal_Nm=round(T_motor_norm, 2),
               motor_T_recock_Nm=round(T_motor_recock, 2),
               motor="48 V PMSM servo, about 4 Nm peak / 1.3 Nm continuous, 0.4 kW (re-cocking is slow: 10 mm/s)",
               C_dyn_needed="ball screw dynamic rating >= 25 kN; screw travel 20 years from pitch duty below")
    revs_20y = H.LIFE["pitch_travel_revs_20y"]
    act["screw_travel_20y_km"] = round(revs_20y * 2 * math.pi * float(np.mean(lever)) / 1e6, 0)

    # ---- latch
    latch = dict(holding_kN=round(F_latched_hot / 1e3, 1),
                 type="roller pawl over a hardened step, toggle ratio >= 25:1, held by a power-on solenoid",
                 solenoid_force_N=round(F_latched_hot / 25 * 0.15 * 1.5),
                 release="safety chain opens solenoid power: release < 50 ms; weekly test = real trip at low wind")

    # ---- links, crank, yoke
    F_link_trip = F_req_design.max() / 3 * 1.2 / math.cos(math.radians(ang.max()))
    F_link_recock = F_recock / 3 / math.cos(math.radians(ang.max()))
    E, d_o, t_w = 210e9, 0.030, 0.004
    I = math.pi / 64 * (d_o ** 4 - (d_o - 2 * t_w) ** 4)
    P_cr = math.pi ** 2 * E * I / (L_LINK / 1e3) ** 2
    F_link_comp = F_recock / 3 / math.cos(math.radians(ang.max()))   # actuator stall at the fine stop, current limited
    links = dict(eye="spherical plain bearings, steel/steel, greased from the hub lubricator (not PTFE: 230 million reversals)",
                 tube=f"Ø{d_o*1e3:.0f} x {t_w*1e3:.0f} S355 with M20 turnbuckle", L_mm=L_LINK,
                 F_tension_trip_kN=round(F_link_trip / 1e3, 1), F_tension_recock_kN=round(F_link_recock / 1e3, 1),
                 F_compression_max_kN=round(F_link_comp / 1e3, 1), buckling_kN=round(P_cr / 1e3), angle_max_deg=round(float(ang.max()), 1))
    T_crank = F_link_recock * R_C / 1e3                # crank torque against the feather stop while re-cocking
    crank = dict(r_mm=R_C, pin_plane_s_mm=S_P,
                 form="welded S355: flange ring 15 (clamped by the 10 blade studs), tube Ø168 x 4 down to s 160, lever plate 20 (s 140-160), pin Ø30 with the link eye below the lever at s 118",
                 T_recock_Nm=round(T_crank), T_trip_design_Nm=round(T["trip_design"] * 1.2),
                 storm_hold_Nm=round(T["storm_hold"]),
                 storm_note="storm holding: the cylinder's holding brake + screw hold all three blades; one blade's 440 Nm gives "
                            f"{round(T['storm_hold'] / (lev_min / 1e3) / 1e3, 1)} kN on the yoke, far below the cylinder rating")
    yoke = dict(form="S355 three-arm plate yoke 20 thick, eyes at R 110, central boss on the cylinder rod, guided by 2 rods Ø25 "
                     "(also take the yoke torque from the link angles)",
                stroke_mm=round(stroke), x_fine_mm=round(float(xy.max())), x_feather_mm=round(float(xy.min())))

    # ---- welded hub (S355NL), checks at the neck-to-shell weld
    R_shell, t_shell, L_shell = 0.230, 0.010, 0.440
    d_neck, t_neck = 0.330, 0.010
    W_neck = math.pi * (d_neck ** 4 - (d_neck - 2 * t_neck) ** 4) / (32 * d_neck)
    M_slm = H.SLM["H_parked"]["M_yB"] * 1e3
    DEL3 = H.LIFE["Mres_DEL_m3_1e7_kNm"] * 1e3
    SCF = 2.5                                           # nozzle-in-cylinder hot spot (to confirm by FEA)
    ds = SCF * 2 * DEL3 / W_neck                        # DEL treated as amplitude-like, x2 (as doc 13)
    FAT, gMf = 90e6, 1.25                               # full-penetration, toe ground, hot-spot FAT 90 (IIW), 2e6
    ds_allow = FAT * (2e6 / 1e7) ** (1 / 3) / gMf
    s_static = SCF * M_slm / W_neck
    rho = 7850
    m_shell = 2 * math.pi * R_shell * L_shell * t_shell * rho - 3 * math.pi / 4 * (d_neck - 2 * t_neck) ** 2 * t_shell * rho * 1.15
    neck_len = 0.350 - 0.030 - R_shell + 0.03         # from shell to the flange underside, + saddle
    m_necks = 3 * math.pi * (d_neck - t_neck) * t_neck * neck_len * rho
    m_flanges = 3 * math.pi / 4 * (0.360 ** 2 - 0.262 ** 2) * 0.025 * rho
    m_rear = math.pi / 4 * (0.470 ** 2 - 0.340 ** 2) * 0.025 * rho
    m_front = math.pi / 4 * ((2 * R_shell) ** 2 - 0.300 ** 2) * 0.012 * rho
    m_gussets = 6.0
    m_hub = m_shell + m_necks + m_flanges + m_rear + m_front + m_gussets
    hub = dict(material="S355NL (impact tested -50 C), stress relieved after welding, flanges machined after",
               shell=f"rolled tube Ø{2*R_shell*1e3:.0f} x {t_shell*1e3:.0f}, length {L_shell*1e3:.0f}",
               necks=f"3 x tube Ø{d_neck*1e3:.0f} x {t_neck*1e3:.0f}, full-penetration welds, toes ground",
               neck_flanges="3 x ring Ø360/Ø262 x 25 (pitch bearing seat, 16 x M16 PCD 300, flatness 0.05 after machining)",
               rear_flange="ring Ø470/Ø340 x 25: 12 x M16 10.9 PCD 400, Ø361 H7 recess (unchanged interface to the drum)",
               front_plate="ring Ø460/Ø300 x 12: nose housing flange, 12 x M12 PCD 340",
               static_hot_spot_MPa=round(s_static / 1e6), static_allow_MPa=round(355 / 1.1),
               fatigue_range_MPa=round(ds / 1e6, 1), fatigue_allow_1e7_MPa=round(ds_allow / 1e6, 1),
               fatigue_ok=bool(ds <= ds_allow),
               mass=dict(shell=round(m_shell, 1), necks=round(m_necks, 1), neck_flanges=round(m_flanges, 1),
                         rear_flange=round(m_rear, 1), front_plate=round(m_front, 1), gussets=m_gussets,
                         total=round(m_hub, 1)),
               joint=H.hub_casting()["joint"])

    # ---- masses (kg) against doc 13
    m_brg = brg["mass_kg"] * 0.92                      # same ring set without gear teeth: bore opened Ø150 -> Ø180
    parts = {"pitch bearings x 3 (ungeared)": 3 * m_brg, "cranks x 3": 3 * 4.0, "links x 3": 3 * 1.2,
             "yoke + guide rods": 6.5, "electric cylinder + motor": 11.0, "carriage, latch, solenoid": 5.0,
             "gas springs x 2": 2 * 3.5, "damper + end buffer": 2.0, "nose housing (Al 6082, welded)": 7.0,
             "pitch controller, position sensor, limit switches": 3.0, "spinner, boots, slip ring rotor, cabling": 8.0}
    m_pitch = sum(parts.values())
    m_total = m_pitch + m_hub
    doc13 = dict(hub_cast=90.0, three_pitch_axes=3 * 33.8, spinner_slip_ring=8.0, total=199.4)
    mass = dict(parts={k: round(v, 1) for k, v in parts.items()}, pitch_system=round(m_pitch, 1),
                hub_welded=round(m_hub, 1), total_welded_hub=round(m_total, 1),
                total_with_cast_hub=round(m_pitch + 90.0 + 6.0, 1), doc13=doc13)

    # ---- part count (bought + made units in the hub) against doc 13
    count = dict(doc13=dict(servo_gearmotors=3, drive_controllers=3, supercap_modules=3, encoders=3, ring_gears_pinions=3,
                            limit_switch_sets=3, heater_pads=6),
                 doc24=dict(electric_cylinder=1, controller=1, linear_position_sensor=1, limit_switch_set=1,
                            gas_springs=2, latch_solenoid=1, damper=1, heater_pads=2, links=3, cranks=3, yoke=1))
    return dict(geometry=dict(theta_range=[TH_FINE, TH_FEATHER], r_crank=R_C, s_pin=S_P, R_yoke=R_Y, L_link=L_LINK,
                              beta_deg=round(math.degrees(BETA), 1), stroke_mm=round(stroke, 1),
                              lever_mm_per_rad=[round(lev_min, 1), round(float(lever.max()), 1)],
                              link_angle_max_deg=round(float(ang.max()), 1)),
                blade_torques_Nm={k: round(v, 1) for k, v in T.items()},
                yoke_force_required_kN=dict(design_max=round(float(F_req_design.max()) / 1e3, 2),
                                            single_max=round(float(F_req_single.max()) / 1e3, 2)),
                springs=springs, damper=damper, actuator=act, latch=latch, links=links, crank=crank, yoke=yoke,
                hub=hub, mass=mass, part_count=count,
                curves=dict(theta=th[::12].round(1).tolist(), yoke_x=xy[::12].round(1).tolist(),
                            F_req_design_kN=(F_req_design[::12] / 1e3).round(2).tolist(),
                            F_springs_cold_kN=(2 * F_one(T_K["cold"])[::12] / 1e3).round(2).tolist(),
                            F_one_spring_cold_kN=(F_one(T_K["cold"])[::12] / 1e3).round(2).tolist(),
                            F_req_single_kN=(F_req_single[::12] / 1e3).round(2).tolist()))



def size_supercap(sp):
    """Chosen variant (Martin, 2026-11-05): no springs; the electric cylinder feathers the blades itself,
    from one supercapacitor module, when the safety chain opens or power is lost."""
    T, brg = blade_torques()
    th, xy, dxdth, ang = kinematics()
    lever = np.abs(dxdth) / 1e3                        # m per rad
    F_des = 3 * T["trip_design"] / lever / ETA_LINK    # N along the stroke
    F_rated = math.ceil(float(F_des.max()) * 1.2 / 500) * 500
    lead, belt, eta_s, eta_back, eta_el = 5.0e-3, 2.0, 0.90, 0.80, 0.85
    w = math.radians(30.0)
    v = lever * w                                      # m/s at 30 deg/s
    P_mech = F_des * v / eta_s
    T_mot = F_rated * lead / (2 * math.pi * eta_s * belt)
    n_mot = float(v.max()) / lead * belt * 60
    E_stroke = float(np.trapezoid(F_des / eta_s, xy / 1e3).__abs__()) / eta_el
    C, V1, V2 = 16.7, 56.0, 30.0
    E_mod = 0.5 * C * (V1 ** 2 - V2 ** 2)
    strokes_eol = 0.8 * E_mod / E_stroke
    I_peak = float(P_mech.max()) / eta_el / V2
    # storm: all three blades pushing the same way through the screw (back-driving) onto the motor brake
    F_storm = 3 * T["storm_hold"] / float(lever.min())
    T_brake = F_storm * lead * eta_back / (2 * math.pi * belt)
    F_norm = 3 * (T["normal_cold_eq"] * 1.35) / lever / ETA_LINK
    T_cont = float(F_norm.max()) * lead / (2 * math.pi * eta_s * belt)
    links = dict(sp["links"])
    links["F_tension_trip_kN"] = round(F_rated / 3 / math.cos(math.radians(float(ang.max()))) / 1e3, 1)
    links["F_compression_max_kN"] = links["F_tension_trip_kN"]
    links.pop("F_tension_recock_kN", None)
    crank = dict(sp["crank"])
    crank.pop("T_recock_Nm", None)
    crank["T_max_Nm"] = round(F_rated / 3 * float(lever.max()))     # cylinder at its force limit on an end stop
    crank["storm_note"] = (f"storm holding: worst case all three blades push the same way, {round(F_storm / 1e3, 1)} kN on the screw, "
                           "held by the motor brake through the back-driven screw (ball screws are not self-locking)")
    act = dict(type="electric cylinder: ball screw lead 5 mm, belt 1:2 to a parallel 48 V PMSM servo, spring-applied holding brake",
               stroke_mm=round(float(xy.max() - xy.min()) + 20), F_trip_design_kN=round(float(F_des.max()) / 1e3, 1),
               F_rated_kN=round(F_rated / 1e3, 1), F_normal_peak_kN=round(float(F_norm.max()) / 1e3, 1),
               v_30dps_m_s=round(float(v.max()), 3), motor_rpm_30dps=round(n_mot),
               motor_T_peak_Nm=round(T_mot, 1), motor_T_cont_Nm=round(T_cont, 2),
               P_mech_peak_W=round(float(P_mech.max())), brake_motor_Nm=round(T_brake * 1.2, 1),
               F_storm_on_screw_kN=round(F_storm / 1e3, 1),
               screw="ball screw Ø32 x 5, C_dyn >= 30 kN, C_0 >= 60 kN; 20-year travel " + str(sp["actuator"]["screw_travel_20y_km"]) + " km at small strokes: L10 by supplier",
               current_limit=f"force limit {F_rated/1e3:.1f} kN (current), so an end-stop stall cannot overload links, cranks or stops")
    sc = dict(module="21 x 2.7 V / 350 F in series (56.7 V, 16.7 F), active balancing, heater pad (same module as doc 13, one instead of three)",
              window_V=[V1, V2], E_usable_kJ=round(E_mod / 1e3, 1), E_stroke_kJ=round(E_stroke / 1e3, 2),
              strokes_end_of_life=round(strokes_eol, 1), required=2, I_peak_A=round(I_peak))
    fail = dict(triggers=["safety chain opens (STO input + supercap-only mode)", "48 V slip-ring supply lost",
                          "controller watchdog / bus loss", "supercap below 2-stroke reserve: feather and stop"],
                sequence="fixed in the drive firmware (certified with the safety system, PL d): drive to 91 deg at 30 deg/s on supercap power, "
                         "stop on the feather limit switch, set the holding brake",
                drive_dead="if the drive itself fails, the blades stay where they are; the two spring-applied rotor brakes "
                           "(8.7 kNm, 12 x rated torque) stop the rotor as the independent second system (doc 11)")
    parts = dict(sp["mass"]["parts"])
    for k in ("carriage, latch, solenoid", "gas springs x 2", "damper + end buffer"):
        parts.pop(k)
    parts["electric cylinder + motor"] = 11.0          # 25 kN class
    parts["cranks x 3"] = 3 * 8.0                      # from the 3D model (cad/hub_c)
    parts["supercap module + heater"] = 3.5
    parts["nose housing (Al 6082, welded)"] = 5.0
    m_pitch = sum(parts.values())
    m_hub = sp["hub"]["mass"]["total"]
    mass = dict(parts={k: round(v, 1) for k, v in parts.items()}, pitch_system=round(m_pitch, 1), hub_welded=m_hub,
                total_welded_hub=round(m_pitch + m_hub, 1), total_with_cast_hub=round(m_pitch + 96.0, 1),
                doc13_total=199.4, spring_variant_total_welded=sp["mass"]["total_welded_hub"])
    count = dict(electric_cylinder=1, drive_controller=1, supercap_module=1, linear_position_sensor=1,
                 limit_switch_set=1, heater_pads=2, links=3, cranks=3, yoke=1)
    return dict(actuator=act, supercap=sc, fail_safe=fail, links=links, crank=crank, mass=mass, part_count=count)


def main():
    s = size()
    out = dict(chosen="collective, one electric cylinder feathering from one supercap module (Martin 2026-11-05)",
               geometry=s["geometry"], blade_torques_Nm=s["blade_torques_Nm"], yoke_force_required_kN=s["yoke_force_required_kN"],
               supercap_variant=size_supercap(s), yoke=s["yoke"], hub=s["hub"],
               spring_variant_rejected={k: s[k] for k in ("springs", "damper", "actuator", "latch", "mass")},
               doc13_part_count=s["part_count"]["doc13"], curves=s["curves"])
    (OUT / "collective_summary.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps({k: v for k, v in out.items() if k not in ("curves", "spring_variant_rejected")}, indent=1, default=float))


if __name__ == "__main__":
    main()
