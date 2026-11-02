"""Hub, pitch system and yaw system sizing (doc 13).

Concept-level sizing from the load sets of doc 08 / doc 11 and the pitch and
yaw duty simulated by run_pitch_duty.py:

1. Pitch moments: aerodynamic, centrifugal twisting and inertia, from the
   steady BEM model and the blade mass distribution of the simulator.
2. Pitch bearing: four-point contact ball slewing ring. Hertz contact stress
   under the SLM and simulated design loads, ISO 281-style life under the
   motion-weighted equivalent load, friction torque (warm and at -30 C).
3. Pitch drive: torque cases, gear train, motor, tooth bending, supercapacitor
   energy store.
4. Hub casting (EN-GJS-400-18U-LT): wall and flange checks, mass estimate,
   hub-to-drum bolted joint.
5. Yaw: loads at the yaw bearing, slewing ring check, friction, drives,
   spring-applied brake with controlled slip, backup battery energy.

Run:  python3 hub.py      (needs results/pitch_duty.json; writes results/hub_summary.json)
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "loads"))
sys.path.insert(0, str(HERE.parent / "rotor"))
from sim import Turbine  # noqa: E402
from bem import solve, CLEAN  # noqa: E402

G = 9.81
OUT = HERE / "results"
OUT.mkdir(exist_ok=True)
LOADS = HERE.parent / "loads" / "results"

SLM = json.loads((LOADS / "slm.json").read_text())["ultimate_design_values_gamma_3_kN_kNm"]
SIM = json.loads((LOADS / "final" / "dlc_summary.json").read_text())
DUTY = json.loads((OUT / "pitch_duty.json").read_text())
LIFE = DUTY["lifetime_20y"]
GAMMA_SIM = 1.35

TB = Turbine(**DUTY["config"])
R_COG = 1.55                      # blade centre of gravity radius (SLM input, doc 08)
RPM_MAX = 250.0                   # design overspeed (R3.1a)
RHO_STORM = 1.35
V_E50 = 77.0


# ===================================================================== 1. pitch moments
def section_props(x_axis):
    """Per-element properties of the blade (from the simulator's blade model)."""
    b = TB.blade
    r, dr, c, mu = TB.r, TB.dr, TB.c, TB.mu
    I_ch = mu * (0.22 * c) ** 2       # chordwise mass radius of gyration about pitch axis (shell, caps)
    I_fl = mu * (0.06 * c) ** 2       # flapwise
    return dict(r=r, dr=dr, c=c, mu=mu, I_ch=I_ch, I_fl=I_fl, twist=TB.twist0, x_axis=x_axis, blade=b)


def cn_xcp_360(alpha_deg, polar=CLEAN):
    """Normal force coefficient and centre of pressure (fraction of chord from LE), any angle.

    Attached flow: polar cl/cd, centre of pressure at the quarter chord plus cm0 (handled outside).
    Separated flow: flat plate, centre of pressure moves from 0.25c at stall to 0.5c at 90 deg and
    to 0.75c (from the LE) for flow arriving from the trailing edge.
    """
    a = (np.asarray(alpha_deg, float) + 180.0) % 360.0 - 180.0
    absa = np.abs(a)
    a_s = polar.alpha_stall
    cl, cd = polar.coeffs(np.clip(a, -90, 90))
    ar = np.radians(a)
    cn_att = cl * np.cos(ar) + cd * np.sin(ar)
    cn_fp = polar.cdmax * np.sin(ar)
    attached = (a > -12.0) & (a < a_s)
    cn = np.where(attached, cn_att, np.where(absa <= 90, np.where(a > 0, np.maximum(cn_att, cn_fp), cn_fp), cn_fp))
    # centre of pressure
    frac = np.clip((np.minimum(absa, 180 - absa) - a_s) / (90 - a_s), 0, 1)
    x_front = 0.25 + 0.25 * frac          # flow from the leading edge
    x_back = 1.0 - x_front                # flow from the trailing edge (mirror)
    xcp = np.where(attached, 0.25, np.where(absa <= 90, x_front, x_back))
    return cn, xcp, attached


CM0 = -0.08          # zero-lift pitching moment of a cambered 18-21 % aerofoil (assumption)


def aero_pitch_moment(sp, V, omega, pitch, rho=1.225):
    """Aerodynamic moment about the pitch axis, positive = towards feather (nose down)."""
    res = solve(sp["blade"], V, omega, pitch, rho, CLEAN)
    r, c, dr = sp["r"], sp["c"], sp["dr"]
    W2 = (V * (1 - res.a)) ** 2 + (omega * r) ** 2
    q = 0.5 * rho * W2
    cn, xcp, att = cn_xcp_360(res.alpha)
    m = cn * (xcp - sp["x_axis"]) - np.where(att, CM0, 0.0)
    return float(np.sum(q * c ** 2 * m * dr)), res


def ctm(sp, omega, pitch):
    """Centrifugal twisting (propeller) moment, positive = towards feather."""
    th = np.radians(sp["twist"] + pitch)
    return float(-np.sum(omega ** 2 * (sp["I_ch"] - sp["I_fl"]) * np.sin(th) * np.cos(th) * sp["dr"]))


def storm_hold_moment(sp, V=V_E50, rho=RHO_STORM):
    """Parked, feathered, rotor stopped: worst moment about the pitch axis over all inflow directions."""
    r, c, dr = sp["r"], sp["c"], sp["dr"]
    worst = 0.0
    worst_dir = 0.0
    for psi in np.arange(0, 360, 2.0):            # inflow direction in the section plane
        # feathered at 90 deg pitch: chord roughly along the wind for psi = 0
        alpha = psi - (sp["twist"] + 90.0 - 90.0)
        cn, xcp, att = cn_xcp_360(alpha)
        m = cn * (xcp - sp["x_axis"]) - np.where(att, CM0, 0.0)
        M = float(np.sum(0.5 * rho * V ** 2 * c ** 2 * m * dr))
        if abs(M) > abs(worst):
            worst, worst_dir = M, psi
    return worst, worst_dir


def pitch_moments():
    out = {}
    for x_axis in (0.25, 0.30, 0.35):
        sp = section_props(x_axis)
        om_r = TB.omega_rated
        om_max = RPM_MAX * 2 * math.pi / 60
        # operating, above rated at the scheduled pitch
        op = []
        for V in (12, 15, 20, 25):
            th = float(np.interp(V, [10.5, 12, 15, 20, 25], [0, 4, 10, 17, 22]))
            Ma, _ = aero_pitch_moment(sp, V, om_r, th)
            op.append((V, th, Ma, ctm(sp, om_r, th)))
        # emergency feather from 25 m/s at design overspeed: sweep pitch 20 -> 90 deg
        sweep = []
        for th in range(20, 91, 5):
            Ma, _ = aero_pitch_moment(sp, 25.0, om_max, float(th))
            sweep.append((th, Ma, ctm(sp, om_max, float(th))))
        hold, hold_dir = storm_hold_moment(sp)
        resist_op = min(min(Ma + Mc for _, _, Ma, Mc in op), 0.0)
        resist_feather = min(min(Ma + Mc for _, Ma, Mc in sweep), 0.0)
        out[x_axis] = dict(
            operating=[dict(V=V, pitch=th, M_aero=round(Ma, 1), M_ctm=round(Mc, 1)) for V, th, Ma, Mc in op],
            feather_sweep_250rpm=[dict(pitch=th, M_aero=round(Ma, 1), M_ctm=round(Mc, 1)) for th, Ma, Mc in sweep],
            worst_resisting_operating_Nm=round(resist_op, 1),
            worst_resisting_feather_Nm=round(resist_feather, 1),
            storm_hold_Nm=round(hold, 1), storm_hold_dir_deg=hold_dir,
        )
    sp = section_props(0.30)
    J_blade = float(np.sum((sp["I_ch"] + sp["I_fl"]) * sp["dr"])) + 4.0 * 0.11 ** 2 / 2   # + root ring
    return out, J_blade


# ===================================================================== 2. pitch bearing
E_PRIME = 228e9          # Pa, steel on steel
ALPHA_C = math.radians(45.0)
OSC = 0.535              # raceway osculation (slewing ring practice 0.52-0.54)
P_STATIC = 4000e6        # Pa, allowable Hertz stress, induction-hardened raceway (NREL DG03, slewing ring practice)
FC_TABLE = ([0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10],     # ISO 281 thrust ball, alpha 45
            [42.1, 51.7, 58.2, 63.3, 67.3, 70.7, 73.5, 75.9, 78.0, 79.7])
F_SLEW = 0.60            # derating of ISO 281 Ca for a slewing ring (induction-hardened rings, osculation, deflection)


def hertz_pmax(Q, Dw, Dpw, f=OSC):
    """Maximum Hertz pressure (Pa) at the more loaded (inner) raceway contact (Hamrock-Brewe)."""
    gam = Dw * math.cos(ALPHA_C) / Dpw
    best = 0.0
    for sgn in (-1, 1):                      # inner (-) / outer (+)
        Rx = Dw * (1 + sgn * gam) / 2
        Ry = f * Dw / (2 * f - 1)
        Rinv = 1 / Rx + 1 / Ry
        Rr = 1 / Rinv
        k = 1.0339 * (Ry / Rx) ** 0.636
        Ee = 1.0003 + 0.5968 * Rx / Ry
        a = (6 * k ** 2 * Ee * Q * Rr / (math.pi * E_PRIME)) ** (1 / 3)
        b = (6 * Ee * Q * Rr / (math.pi * k * E_PRIME)) ** (1 / 3)
        best = max(best, 3 * Q / (2 * math.pi * a * b))
    return best


def ball_load(M, Fa, Fr, Dpw, Z):
    """Most loaded ball of a four-point contact bearing (Stribeck 4.37 for moment)."""
    return (4.37 * M / Dpw + abs(Fa)) / (Z * math.sin(ALPHA_C)) + 2.0 * Fr / (Z * math.cos(ALPHA_C))


def ca_iso(Dw, Dpw, Z):
    x = Dw * math.cos(ALPHA_C) / Dpw
    fc = float(np.interp(x, *FC_TABLE))
    Dmm = Dw * 1e3
    return F_SLEW * 1.3 * fc * math.cos(ALPHA_C) ** 0.7 * math.tan(ALPHA_C) * Z ** (2 / 3) * Dmm ** 1.8   # N


def friction_torque(M, Fa, Fr, Dpw, mu, seal_N_per_m, seal_d):
    """Rothe Erde style rolling friction for four-point contact bearings, plus two lip seals."""
    roll = mu / 2 * (4.4 * M + Fa * Dpw + 3.81 * Fr * Dpw)
    seal = 2 * seal_N_per_m * math.pi * seal_d * seal_d / 2
    return roll + seal


def pitch_bearing():
    # design load sets at the pitch bearing (blade root)
    sets = {
        "SLM H parked flap (gamma 3.0)": dict(M=SLM["H_parked"]["M_yB"] * 1e3, Fa=0.0, Fr=SLM["H_parked"]["F_x_shaft"] * 1e3 / 3),
        "SLM E overspeed centrifugal (gamma 3.0)": dict(M=0.0, Fa=SLM["E_max_speed"]["F_zB"] * 1e3, Fr=0.0),
        "SLM G shutdown edge (gamma 3.0)": dict(M=SLM["G_shutdown"]["M_xB"] * 1e3,
                                               Fa=SLM["E_max_speed"]["F_zB"] * 1e3 / 3.0 * 1.35 * (210 / 250) ** 2, Fr=0.0),
        "Simulated envelope (gamma 1.35)": dict(M=SIM["ultimate_envelope"]["Mres0"]["design"],
                                               Fa=GAMMA_SIM * TB.m_blade * (231.6 * 2 * math.pi / 60) ** 2 * R_COG,
                                               Fr=SIM["ultimate_envelope"]["thrust"]["design"] / 3),
    }
    # equivalent life loads (motion weighted) and revolutions
    M_eq = LIFE["M_eq_motion_weighted_kNm"] * 1e3
    F_eq = LIFE["F_eq_motion_weighted_kN"] * 1e3
    revs = LIFE["pitch_travel_revs_20y"]
    revs_req = 2 * revs                      # 2 x design life, as R5.1 for the main bearings
    cands = []
    for Dpw in (0.200, 0.225, 0.250, 0.275, 0.300):
        for Dw in (0.0159, 0.0190, 0.0222, 0.0254):
            Z = int(math.floor(math.pi * Dpw / (Dw * 1.12)))     # ball pitch 1.12 Dw (spacers)
            rows = {}
            ok = True
            for name, L in sets.items():
                Q = ball_load(L["M"], L["Fa"], L["Fr"], Dpw, Z)
                p = hertz_pmax(Q, Dw, Dpw)
                s0 = (P_STATIC / p) ** 3      # load ratio (ball load scales with p^3)
                need = 1.25 if "SLM" in name else 1.5
                rows[name] = dict(Q_kN=round(Q / 1e3, 2), p_MPa=round(p / 1e6), s0=round(s0, 2), ok=s0 >= need)
                ok &= s0 >= need
            Ca = ca_iso(Dw, Dpw, Z)
            Pa = F_eq + 2.5 * M_eq / Dpw
            L10 = (Ca / Pa) ** 3 * 1e6
            ok &= L10 >= revs_req
            cands.append(dict(Dpw=Dpw, Dw=Dw, Z=Z, static=rows, Ca_kN=round(Ca / 1e3, 1), Pa_kN=round(Pa / 1e3, 2),
                              L10_revs=round(L10), revs_required=round(revs_req), ok=bool(ok)))
    # choose: smallest pitch diameter that passes with the blade bolt circle (190 mm) inside the inner ring
    feasible = [c for c in cands if c["ok"] and c["Dpw"] >= 0.250]
    chosen = min(feasible, key=lambda c: (c["Dpw"], c["Dw"]))
    Dpw, Dw = chosen["Dpw"], chosen["Dw"]
    # geometry and mass of the chosen ring set (rectangular ring sections, gear on the inner ring)
    ring_h = 0.050
    od = Dpw + Dw + 2 * 0.040            # outer ring: raceway + 40 mm wall with hub bolt holes
    id_ = 0.150                          # inner ring bore = root of the internal gear teeth
    vol = math.pi / 4 * (od ** 2 - id_ ** 2) * ring_h * 0.65   # raceway void, gap, gear teeth, holes, chamfers
    mass = vol * 7850
    # friction torque: emergency feather (SLM G edge + centrifugal at trip speed) and typical operation
    Lg = sets["SLM G shutdown edge (gamma 3.0)"]
    fr = {}
    for label, mu, seal in (("warm", 0.006, 40.0), ("-30 C", 0.012, 120.0)):
        fr[label] = dict(
            emergency_SLM_G=round(friction_torque(Lg["M"], Lg["Fa"], 0.0, Dpw, mu, seal, od - 0.02), 1),
            emergency_sim=round(friction_torque(SIM["per_dlc_max"]["5.1-estop"]["Mres0"] * GAMMA_SIM,
                                                GAMMA_SIM * TB.m_blade * (210 * 2 * math.pi / 60) ** 2 * R_COG, 0.0,
                                                Dpw, mu, seal, od - 0.02), 1),
            operating_mean=round(friction_torque(LIFE["M_mean_motion_weighted_kNm"] * 1e3,
                                                 LIFE["F_mean_motion_weighted_kN"] * 1e3, 0.0, Dpw, mu, seal, od - 0.02), 1),
            operating_eq=round(friction_torque(M_eq, F_eq, 0.0, Dpw, mu, seal, od - 0.02), 1),
        )
    return dict(load_sets={k: {kk: round(vv, 1) for kk, vv in v.items()} for k, v in sets.items()},
                M_eq_kNm=round(M_eq / 1e3, 2), F_eq_kN=round(F_eq / 1e3, 2), revs_20y=round(revs),
                candidates=cands, chosen=chosen, outer_diameter=round(od, 3), inner_bore=id_, height=ring_h,
                mass_kg=round(mass, 1), friction_Nm=fr)


# ===================================================================== 3. pitch drive
def pitch_drive(moments, J_blade, brg):
    x_axis = 0.30
    pm = moments[x_axis]
    fr_cold = brg["friction_Nm"]["-30 C"]
    fr_warm = brg["friction_Nm"]["warm"]
    acc = math.radians(30.0) / 0.20                    # reach 30 deg/s in 0.2 s
    # gear train: internal ring gear on the inner (blade) ring, pinion inside the hub
    m_gear, z_ring, z_pin = 3.0e-3, 48, 14
    i1 = z_ring / z_pin
    i2 = 100.0                                         # planetary servo gearbox
    eta_warm, eta_cold = 0.90 * 0.97, 0.75 * 0.97      # gearbox (cold grease) x spur mesh
    J_motor = 1.8e-4 + 0.7e-4                          # kg m2, 0.75 kW servo rotor + brake, gearbox input stage
    J_refl = J_motor * (i1 * i2) ** 2
    T_inertia = (J_blade + J_refl) * acc
    # torque cases at the bearing (Nm). Aero/CTM resisting moments x 1.35 (load factor).
    cases = {
        "Emergency feather at -30 C, SLM G edge moment": fr_cold["emergency_SLM_G"] - 1.35 * pm["worst_resisting_feather_Nm"],
        "Emergency feather at -30 C, simulated e-stop moment": fr_cold["emergency_sim"] - 1.35 * pm["worst_resisting_feather_Nm"],
        "Normal pitching, warm, mean load": fr_warm["operating_mean"] - pm["worst_resisting_operating_Nm"],
        "Normal pitching, -30 C, equivalent load": fr_cold["operating_eq"] - pm["worst_resisting_operating_Nm"],
    }
    T_peak = max(cases.values()) + T_inertia
    T_cont = cases["Normal pitching, -30 C, equivalent load"]
    hold = 1.5 * abs(pm["storm_hold_Nm"])             # holding brake: 1.5 x storm moment, friction ignored
    w30 = math.radians(30.0)
    motor = dict(
        speed_rpm_at_30dps=round(30 / 360 * 60 * i1 * i2),
        T_peak_motor_Nm=round(T_peak / (i1 * i2 * eta_cold), 2),
        T_cont_motor_Nm=round(T_cont / (i1 * i2 * eta_cold), 2),
        P_peak_mech_W=round(T_peak * w30 / eta_cold),
        brake_motor_Nm=round(hold / (i1 * i2) * 1.0, 2),   # gearbox efficiency ignored when holding (conservative)
    )
    # tooth bending (Lewis with stress correction), pinion, face width 30 mm, 42CrMo4 QT, at peak and storm hold
    b, Y_pin, Kv = 0.030, 0.28, 1.2
    r_ring = m_gear * z_ring / 2
    teeth = {}
    for name, T in (("peak drive", T_peak), ("storm hold", hold), ("SLM G friction lock", fr_cold["emergency_SLM_G"] * 1.5)):
        Ft = T / r_ring
        sig = Kv * Ft / (b * m_gear * Y_pin)
        teeth[name] = dict(Ft_kN=round(Ft / 1e3, 2), sigma_MPa=round(sig / 1e6), allow_MPa=450,
                           ok=bool(sig < 450e6))
    # supercapacitor: one full 0 -> 90 deg emergency stroke at peak torque (cold), x2 strokes, end of life 80 %
    E_stroke = T_peak * math.radians(90) / (eta_cold * 0.90)    # 90 % motor + converter
    E_need = 2 * E_stroke / 0.80
    V1, V2 = 56.0, 24.0
    C_need = 2 * E_need / (V1 ** 2 - V2 ** 2)
    sc = dict(E_stroke_J=round(E_stroke), E_required_J=round(E_need), V_window=(V1, V2), C_required_F=round(C_need, 1),
              C_chosen_F=16.7, E_usable_chosen_J=round(0.5 * 16.7 * (V1 ** 2 - V2 ** 2)),
              strokes_at_EOL=round(0.8 * 0.5 * 16.7 * (V1 ** 2 - V2 ** 2) / E_stroke, 1))
    sc["chosen"] = "one module per axis: 21 cells x 2.7 V / 350 F in series (56.7 V, 16.7 F), active balancing, heater pad"
    t_stroke = 90 / 30.0
    return dict(x_axis=x_axis, gear=dict(module_mm=3, z_ring=z_ring, z_pinion=z_pin, i1=round(i1, 2), i2=i2,
                                        i_total=round(i1 * i2)),
                inertia=dict(J_blade=round(J_blade, 3), J_reflected=round(J_refl, 2), T_inertia_Nm=round(T_inertia, 1)),
                torque_cases_Nm={k: round(v, 1) for k, v in cases.items()}, T_peak_Nm=round(T_peak, 1),
                T_cont_Nm=round(T_cont, 1), hold_Nm=round(hold, 1), motor=motor, teeth=teeth, supercap=sc,
                feather_time_s=t_stroke)


# ===================================================================== 4. hub casting
def hub_casting():
    fy, gm = 240e6, 1.1                 # EN-GJS-400-18U-LT, t <= 30 mm (EN 1563), material factor
    d_neck = 0.33                       # neck outside diameter at the pitch bearing flange
    t_min_cast = 0.010                  # minimum sound wall for a sand-cast ductile iron part of this size
    M_slm = SLM["H_parked"]["M_yB"] * 1e3
    Fc_slm = SLM["E_max_speed"]["F_zB"] * 1e3
    del_m5 = LIFE["Mres_DEL_m5_1e7_kNm"] * 1e3
    Kt_static, Kt_fat = 1.5, 2.5
    ds_allow = 55e6                     # stress range at 1e7 cycles, m = 5, incl. gamma_m (GL 2010 synthetic S-N, ductile iron, cast surface)
    rows = []
    for t in (0.008, 0.010, 0.012, 0.015):
        W = math.pi * d_neck ** 2 * t / 4
        A = math.pi * d_neck * t
        s_static = Kt_static * (M_slm / W + Fc_slm / A)
        s_fat = Kt_fat * 2 * del_m5 / W          # DEL is an amplitude-like range? treat DEL as range; x2 margin for flap+edge phasing
        rows.append(dict(t_mm=t * 1e3, static_MPa=round(s_static / 1e6), static_allow=round(fy / gm / 1e6),
                         fatigue_range_MPa=round(s_fat / 1e6), fatigue_allow=round(ds_allow / 1e6),
                         ok=bool(s_static <= fy / gm and s_fat <= ds_allow)))
    t_wall = max(t_min_cast, min(r["t_mm"] for r in rows if r["ok"]) / 1e3)
    # geometry: central sphere + three necks + flanges; openings for necks, front access, rear (drum + bearing)
    Rs = 0.22
    neck_len = 0.35 - math.sqrt(Rs ** 2 - (d_neck / 2) ** 2)       # bearing seat face at r = 0.35 m (bearing 56 mm, root at 0.40)
    A_sphere = 4 * math.pi * Rs ** 2
    cap = lambda a: 2 * math.pi * Rs * (Rs - math.sqrt(Rs ** 2 - a ** 2))
    A_open = 3 * cap(d_neck / 2) + cap(0.125) + cap(0.17)
    A_necks = 3 * math.pi * d_neck * neck_len
    rho_fe = 7100
    m_shell = (A_sphere - A_open + A_necks) * t_wall * rho_fe
    od_brg = 0.36
    m_pitch_flanges = 3 * math.pi / 4 * (od_brg ** 2 - 0.27 ** 2) * 0.020 * rho_fe
    m_rear_flange = math.pi / 4 * (0.44 ** 2 - 0.34 ** 2) * 0.025 * rho_fe
    m_ribs = 0.10 * m_shell
    m_hub = m_shell + m_pitch_flanges + m_rear_flange + m_ribs
    # hub-to-drum bolted joint (PCD 0.40 m), slip-resistant, M16 10.9 preloaded
    pcd = 0.40
    M_hub = max(SIM["ultimate_envelope"]["Mtilt"]["design"], SIM["ultimate_envelope"]["Myaw"]["design"],
                SLM["B_yaw"]["M_shaft"] * 1e3)
    T_hub = max(SLM["G_shutdown"]["M_x_shaft"] * 1e3, SIM["ultimate_envelope"]["Qgen"]["design"])
    Fx = max(SLM["H_parked"]["F_x_shaft"] * 1e3, SIM["ultimate_envelope"]["thrust"]["design"])
    Fp = 0.7 * 1000e6 * 157e-6          # EN 1993-1-8 preload, M16 10.9
    mu_s, gM3 = 0.30, 1.25              # blasted, unpainted contact faces (zinc-silicate allowed)
    joint = None
    for n in range(12, 33, 2):          # >= 12 for an even clamp around the flange
        Ft = 4 * M_hub / (n * pcd) + Fx / n
        F_slip = n * mu_s * (Fp - 0.8 * Ft) / gM3
        F_shear = T_hub / (pcd / 2)
        if F_slip >= F_shear and Ft <= 0.9 * 1000e6 * 157e-6 / 1.25 - 0:
            joint = dict(n_bolts=n, size="M16 10.9", pcd=pcd, Ft_per_bolt_kN=round(Ft / 1e3, 1),
                         preload_kN=round(Fp / 1e3), slip_capacity_kN=round(F_slip / 1e3, 1),
                         shear_demand_kN=round(F_shear / 1e3, 1))
            break
    return dict(material="EN-GJS-400-18U-LT", wall_checks=rows, wall_mm=t_wall * 1e3, sphere_R=Rs,
                neck_len=round(neck_len, 3), mass=dict(shell=round(m_shell, 1), pitch_flanges=round(m_pitch_flanges, 1),
                                                       rear_flange=round(m_rear_flange, 1), ribs=round(m_ribs, 1),
                                                       total=round(m_hub, 1)),
                joint_loads=dict(M_Nm=round(M_hub), T_Nm=round(T_hub), Fx_N=round(Fx)), joint=joint)


# ===================================================================== 5. yaw
def yaw_system(m_rotor):
    # geometry (doc 07): yaw axis 0.75 m behind the rotor centre; shaft axis above the yaw bearing
    x_rot, h_shaft = 0.75, 0.40
    m_rest, x_rest = 300.0, -0.10                       # nacelle without rotor, CoG slightly behind yaw axis
    Wr, Wn = m_rotor * G, m_rest * G
    M_grav = Wr * x_rot - Wn * abs(x_rest)              # nose-down
    sets = {
        "SLM H parked (gamma 3.0)": dict(Fx=SLM["H_parked"]["F_x_shaft"] * 1e3, Mh=SLM["B_yaw"]["M_shaft"] * 1e3),
        "Simulated envelope (gamma 1.35)": dict(Fx=SIM["ultimate_envelope"]["thrust"]["design"],
                                               Mh=SIM["ultimate_envelope"]["Mtilt"]["design"]),
    }
    rows = {}
    for k, s in sets.items():
        M = s["Fx"] * h_shaft + s["Mh"] + 1.1 * max(M_grav, 0)
        Fa = 1.1 * (Wr + Wn)
        Fr = s["Fx"]
        rows[k] = dict(M_tilt_kNm=round(M / 1e3, 2), Fa_kN=round(Fa / 1e3, 2), Fr_kN=round(Fr / 1e3, 2))
    Mmax = max(r["M_tilt_kNm"] for r in rows.values()) * 1e3
    Frmax = max(r["Fr_kN"] for r in rows.values()) * 1e3
    Fa = 1.1 * (Wr + Wn)
    # slewing ring on the 320 mm tower top adapter
    best = None
    for Dpw in (0.36, 0.40, 0.45):          # >= 0.36 m to sit over the 320 mm tower top adapter
        for Dw in (0.0190, 0.0222, 0.0254):
            Z = int(math.floor(math.pi * Dpw / (Dw * 1.12)))
            Q = ball_load(Mmax, Fa, Frmax, Dpw, Z)
            p = hertz_pmax(Q, Dw, Dpw)
            s0 = (P_STATIC / p) ** 3
            if s0 >= 1.0 and best is None:
                best = dict(Dpw=Dpw, Dw=Dw, Z=Z, Q_kN=round(Q / 1e3, 1), p_MPa=round(p / 1e6), s0=round(s0, 2))
    Dpw = best["Dpw"]
    # yaw moments
    Myaw_op_p95 = max(v["Myaw_p95"] for v in DUTY["per_wind"].values())
    Myaw_op_mean = max(abs(v["Myaw_mean"]) for v in DUTY["per_wind"].values())
    M_op_tilt = SIM["fatigue_DEL"]["Mtilt"]["DEL_1e7"] / 2 + abs(M_grav)
    fr = {}
    for label, mu, seal in (("warm", 0.006, 40.0), ("-30 C", 0.012, 120.0)):
        fr[label] = round(friction_torque(M_op_tilt, Wr + Wn, 0.0, Dpw, mu, seal, Dpw + 0.08), 1)
    residual_brake = 500.0                                      # damping friction while yawing (Nm)
    T_drive = fr["-30 C"] + residual_brake + Myaw_op_mean + 0.5 * (Myaw_op_p95 - Myaw_op_mean)
    hold_design = 8000.0                                         # doc 07: parked side wind at V_e50, design
    hold_sim = SIM["ultimate_envelope"]["Myaw"]["design"]
    slip_set = max(hold_design, hold_sim) * 1.0
    r_disc, mu_pad = 0.24, 0.40
    clamp_total = slip_set / (r_disc * mu_pad * 2)
    # drives: two planetary gearmotors, pinion z 14 on external ring gear z 150 (module 4)
    i1 = 150 / 14
    w_yaw = math.radians(0.5)
    n_ring_rpm = 0.5 / 360 * 60
    i2 = round(1500 / (n_ring_rpm * i1), -1)
    T_each_out = T_drive / 2
    motor_T = T_each_out / (i1 * i2 * 0.6)
    P_mech = T_drive * w_yaw
    # backup battery for 72 h storm yawing (doc 11, 5.3)
    yaw_duty = 0.20                    # fraction of time yawing in a storm with a wandering wind direction (assumption)
    P_yaw_el = 2 * 60.0                # W electrical while yawing, two 0.18 kW gearmotors at light load incl. inverter
    P_base = 15 + 10 + 3 * 3 + 20      # controller + sensors + pitch drives idle + heated vane (W)
    E_72h = 72 * (yaw_duty * P_yaw_el + P_base)
    return dict(load_sets=rows, M_grav_Nm=round(M_grav), bearing=best, Myaw_op_p95_Nm=round(Myaw_op_p95),
                Myaw_op_mean_Nm=round(Myaw_op_mean), friction_Nm=fr, residual_brake_Nm=residual_brake,
                T_drive_Nm=round(T_drive), slip_setting_Nm=round(slip_set), brake_clamp_total_kN=round(clamp_total / 1e3, 1),
                gear=dict(i_ring=round(i1, 2), i_gearbox=i2), motor_T_Nm=round(motor_T, 2), P_mech_W=round(P_mech, 1),
                battery=dict(yaw_duty=yaw_duty, P_yaw_W=P_yaw_el, P_base_W=P_base, E_72h_Wh=round(E_72h),
                             note="48 V LiFePO4, heated; sized x1.5 for cold and ageing"),
                battery_kWh_installed=round(1.5 * E_72h / 1e3, 1))


# ===================================================================== main
def main():
    moments, J_blade = pitch_moments()
    brg = pitch_bearing()
    drv = pitch_drive(moments, J_blade, brg)
    hub = hub_casting()
    # pitch system mass per axis: bearing + gearmotor + supercap + drive electronics + covers
    m_axis = brg["mass_kg"] + 6.0 + 3.0 + 2.5 + 1.5      # bearing, gearmotor, supercap, drive, covers/switches
    m_hub_pitch = hub["mass"]["total"] + 3 * m_axis + 8.0           # + spinner, slip ring rotor part, cabling
    m_rotor = 3 * TB.m_blade + m_hub_pitch + 60.0                   # + generator drum (doc 07)
    yaw = yaw_system(m_rotor)
    # effect on tower-top mass and the 18 m tower frequency (doc 09: 480 kg budget with 80 kg hub+pitch)
    d_top = m_hub_pitch - 80.0
    m_top_new = 480.0 + d_top
    f_new = 1.21 * math.sqrt((480.0 + 305.0) / (m_top_new + 305.0))
    rpm_zone = (66.5 * f_new / 1.21, 80.5 * f_new / 1.21)
    J_hub_extra = d_top * 0.25 ** 2
    summary = dict(pitch_moments=moments, pitch_bearing=brg, pitch_drive=drv, hub=hub, yaw=yaw,
                   masses=dict(per_pitch_axis=round(m_axis, 1), hub_and_pitch=round(m_hub_pitch, 1),
                               budget_doc07=80.0, delta=round(d_top, 1), tower_top_new=round(m_top_new),
                               rotor_assembly=round(m_rotor)),
                   tower_effect_18m=dict(f1_old=1.21, f1_new=round(f_new, 3),
                                         exclusion_zone_rpm=[round(rpm_zone[0], 1), round(rpm_zone[1], 1)]),
                   rotor_inertia_increase_kgm2=round(J_hub_extra, 1),
                   duty=LIFE)
    (OUT / "hub_summary.json").write_text(json.dumps(summary, indent=1, default=float))
    print(json.dumps(summary, indent=1, default=float))


if __name__ == "__main__":
    main()
