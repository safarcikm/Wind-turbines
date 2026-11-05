"""Yaw system detail sizing (doc 25).

Concept chosen by Martin on 2026-11-05: bought four-point contact slewing ring
with external gear (doc 13 / doc 16 geometry kept), passive spring-loaded
friction pads on the tower-top track for damping, and two gearmotors with
spring-applied motor brakes for holding. No hydraulics on the yaw system and
no controlled-slip setting (the doc 13 hydraulic calipers and R3.7 are
replaced).

Sections
1. Tower-top mass and centre of gravity (Rev C generator, doc 24 hub).
2. Loads at the yaw bearing and the bolted joints.
3. Slewing ring static check and friction (models of analysis/hub/hub.py).
4. Why controlled slip does not protect anything (reflected inertia, tower torsion).
5. Friction pad units: torque band, clamp, disc spring stack, pad pressure, wear.
6. Drives: torque, motor, gearbox, motor brake, holding with one pinion.
7. Gear check (ISO 6336 simplified, static and operating).
8. Electrical: yaw power, backup battery update.
9. Cable twist loop length.
10. Yaw system mass.

Run:  python3 yaw.py      (writes results/yaw_summary.json)
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "hub"))
import hub as H  # noqa: E402  (slewing ring models, load sets, duty)

G = 9.81
OUT = HERE / "results"
OUT.mkdir(exist_ok=True)


# ============================================================ 1. tower-top mass
# World frame of the nacelle model (cad/nacelle_fitcheck): X rearward from the
# yaw axis, Z up from the yaw bearing top face. Rotor centre X -750, Z 570.
def tower_top():
    items = [  # name, kg, x_mm, z_mm
        ("Blades 3 x 20.5 kg (doc 10)", 61.5, -770, 570),
        ("Hub + collective pitch, welded (doc 24)", 239.0, -720, 570),
        ("Generator rotor Rev C (doc 23)", 161.0, -451, 544),
        ("Generator stator Rev C (doc 23)", 115.0, -370, 537),
        ("Spindle (doc 14)", 57.0, -420, 535),
        ("Bedplate P1 weldment (doc 14)", 150.0, -40, 170),
        ("Nacelle cover and electrics", 20.0, 0, 300),
        ("Slip ring, sensors, cabling, fans, seals", 25.0, -150, 400),
    ]
    yaw_above = [  # nacelle-side yaw parts (sections 5-10), rotate with the nacelle
        ("Yaw bearing inner ring (half of the 55 kg ring)", 27.5, 0, -30),
        ("2 yaw gearmotors with motor brakes", 2 * 22.0, 0, 180),
        ("2 drive brackets NP1-420 (model)", 2 * 7.7, 0, 60),
        ("Yaw VFD, brake relay, cabling", 4.0, 100, 200),
        ("2 friction pad units NY-410 (model)", 2 * 13.2, -280, -80),
        ("Yaw lock NY-430, encoder unit NY-440 (model)", 13.4, 100, 0),
        ("Cable hanger NY-460 (model)", 10.0, 0, -120),
    ]
    tower_side = [
        ("Yaw bearing outer ring with gear", 27.5),
        ("Tower-top adapter NY-400 (seat, track, cone, flange; model)", 106.7),
    ]
    m = sum(i[1] for i in items + yaw_above)
    x = sum(i[1] * i[2] for i in items + yaw_above) / m
    z = sum(i[1] * i[3] for i in items + yaw_above) / m
    m_tower_side = sum(i[1] for i in tower_side)
    return dict(items=items, yaw_above=yaw_above, tower_side=tower_side, m_above=m, x_cg=x, z_cg=z,
                m_tower_side=m_tower_side, m_total=m + m_tower_side)


# ============================================================ 2. loads
H_HUB = 0.570 + 0.035          # rotor centre above the bearing centre plane (bearing 70 high)


def bearing_loads(tt):
    W = tt["m_above"] * G
    M_grav = -W * tt["x_cg"] / 1e3              # nose-down positive (CoG ahead of the axis, x < 0)
    sets = {
        "SLM H parked thrust + SLM shaft moment (gamma 3.0)":
            dict(Fx=H.SLM["H_parked"]["F_x_shaft"] * 1e3, Mh=H.SLM["B_yaw"]["M_shaft"] * 1e3),
        "Simulated envelope (gamma 1.35)":
            dict(Fx=H.SIM["ultimate_envelope"]["thrust"]["design"], Mh=H.SIM["ultimate_envelope"]["Mtilt"]["design"]),
    }
    rows = {}
    for k, s in sets.items():
        M = s["Fx"] * H_HUB + s["Mh"] + 1.1 * max(M_grav, 0.0)
        rows[k] = dict(M_tilt=M, Fa=1.1 * W, Fr=s["Fx"])
    return W, M_grav, rows


def bolt_checks(Mmax, Fr, W):
    out = {}
    # ISO 898 M16 10.9: As 157 mm2, 0.7 Rp0.2 preload ~ 0.7*940*157 = 103 kN; use 90 kN (torque scatter)
    for name, n, pcd, F_pre in (("Bedplate to inner ring, 16 x M16 10.9 PCD 300", 16, 0.300, 90e3),
                                ("Outer ring to adapter, 16 x M16 10.9 PCD 440", 16, 0.440, 90e3)):
        F = 4 * Mmax / (n * pcd) - W / n
        out[name] = dict(F_ext_kN=F / 1e3, F_pre_kN=F_pre / 1e3, ratio=F / F_pre,
                         added_bolt_force_kN=0.2 * F / 1e3)  # load factor 0.2 (stiff steel flanges)
    # tower flange: moment grows by the radial force times the 0.36 m adapter height
    Mt = Mmax + Fr * 0.36
    F = 4 * Mt / (16 * 0.380) - W / 16
    out["Adapter to tower flange, 16 x M20 10.9 PCD 380"] = dict(F_ext_kN=F / 1e3, F_pre_kN=110.0,
                                                               ratio=F / 110e3, M_kNm=Mt / 1e3)
    return out


# ============================================================ 3. slewing ring
YAW_RING = dict(Dpw=0.360, Dw=0.019, Z=53)


def ring_check(rows):
    r = YAW_RING
    res = {}
    for k, s in rows.items():
        Q = H.ball_load(s["M_tilt"], s["Fa"], s["Fr"], r["Dpw"], r["Z"])
        p = H.hertz_pmax(Q, r["Dw"], r["Dpw"])
        res[k] = dict(Q_kN=Q / 1e3, p_MPa=p / 1e6, s0=(H.P_STATIC / p) ** 3)
    return res


def ring_friction(W, M_grav):
    M_op = H.SIM["fatigue_DEL"]["Mtilt"]["DEL_1e7"] / 2 + abs(M_grav)
    return {lab: H.friction_torque(M_op, W, 0.0, YAW_RING["Dpw"], mu, seal, YAW_RING["Dpw"] + 0.08)
            for lab, mu, seal in (("warm", 0.006, 40.0), ("-30 C", 0.012, 120.0))}


# ============================================================ 4. why not slip
I_RING, I_GB = 150 / 14, 1680.0
J_MOTOR = 5.0e-4               # kg m2, 0.18 kW 4-pole frame 63/71 motor with brake disc


def slip_argument(tt):
    i_tot = I_RING * I_GB
    J_refl = 2 * J_MOTOR * i_tot ** 2
    # nacelle yaw inertia: rotor about a diameter (216/2) + parallel axis of rotor, + rest
    J_nac = 216 / 2 + 300.5 * 0.75 ** 2 + 276 * 0.42 ** 2 + 230 * 0.35 ** 2
    # tower torsion at 15 kNm in the Ø320 x 8 tube
    rm, t = (0.320 - 0.008) / 2, 0.008
    tau = 15e3 / (2 * math.pi * rm ** 2 * t)
    return dict(i_total=i_tot, J_reflected_kgm2=J_refl, J_nacelle_kgm2=J_nac,
                share_of_gust_into_gears=J_refl / (J_refl + J_nac), tower_torsion_15kNm_MPa=tau / 1e6)


# ============================================================ 5. friction pads
PAD = dict(units=2, faces=2, r_in=0.325, r_out=0.385, width_t=0.090,
           mu_nom=0.40, mu_min=0.32, mu_max=0.48, cold=1.15, static_over_kinetic=1.15,
           T_nom=3000.0, thickness=12.0, min_thickness=3.0)
# DIN 2093 group 2 disc spring, series B: De 63, Di 31, t 2.5, l0 4.25 (h0 1.75); 8 single discs in series
DISC = dict(De=63.0, Di=31.0, t=2.5, h0=1.75, E=206e3, nu=0.3, parallel=1, series=8)


def disc_force(s, d=DISC):
    """Almen-Laszlo force (N) of one disc at deflection s (mm)."""
    De, Di, t, h0, E, nu = d["De"], d["Di"], d["t"], d["h0"], d["E"], d["nu"]
    delta = De / Di
    K1 = (1 / math.pi) * ((delta - 1) / delta) ** 2 / ((delta + 1) / (delta - 1) - 2 / math.log(delta))
    return 4 * E / (1 - nu ** 2) * t ** 4 / (K1 * De ** 2) * (s / t) * ((h0 / t - s / t) * (h0 / t - s / (2 * t)) + 1)


def pads(T_op_p95):
    P = PAD
    r_eff = (P["r_in"] + P["r_out"]) / 2
    F_clamp = P["T_nom"] / (P["units"] * P["faces"] * P["mu_nom"] * r_eff)
    T = lambda mu: P["units"] * P["faces"] * mu * F_clamp * r_eff  # noqa: E731
    area = (P["r_out"] - P["r_in"]) * P["width_t"]
    # disc spring stack: find the deflection per disc that gives F_clamp
    d = DISC
    s_set = next(s / 1000 for s in range(1, 1400) if d["parallel"] * disc_force(s / 1000) >= F_clamp)
    F_flat = d["parallel"] * disc_force(0.75 * d["h0"])
    # wear: yaw travel assumption and specific wear of the pad material
    travel_deg_day = 1500.0               # incl. untwisting; about 50 min of yawing a day at 0.5 deg/s
    rad_20y = math.radians(travel_deg_day) * 365 * 20
    E_20y = P["T_nom"] * rad_20y          # J, all four pads
    k_wear = 0.25e-6                      # m3/MJ -> 0.25 cm3/MJ, organic industrial pad, low temperature (to test)
    V_pad = k_wear * E_20y / 1e6 / (P["units"] * P["faces"])
    wear_mm_20y = V_pad / area * 1e3
    # clamp drop from one year of wear on both faces of a unit, taken by the series stack
    wear_yr_unit = 2 * wear_mm_20y / 20
    s_new = s_set - wear_yr_unit / d["series"]
    drop = 1 - d["parallel"] * disc_force(s_new) / F_clamp
    return dict(r_eff=r_eff, F_clamp_per_unit_kN=F_clamp / 1e3,
                T_kNm=dict(nominal=T(P["mu_nom"]) / 1e3, min=T(P["mu_min"]) / 1e3, max=T(P["mu_max"]) / 1e3,
                           max_cold_breakaway=T(P["mu_max"]) * P["cold"] * P["static_over_kinetic"] / 1e3),
                T_min_over_op_p95=T(P["mu_min"]) / T_op_p95,
                pad_area_cm2=area * 1e4, pad_pressure_MPa=F_clamp / area / 1e6,
                sliding_speed_mm_s=math.radians(0.5) * r_eff * 1e3, heat_W=P["T_nom"] * math.radians(0.5),
                disc=dict(spec="DIN 2093 B 63 (63 x 31 x 2.5, l0 4.25)", parallel=d["parallel"], series=d["series"],
                          s_set_per_disc_mm=s_set, s_set_over_h0=s_set / d["h0"], F_at_0p75h0_kN=F_flat / 1e3,
                          stack_preset_mm=s_set * d["series"]),
                wear=dict(travel_deg_day=travel_deg_day, energy_20y_MJ=E_20y / 1e6, k_cm3_per_MJ=k_wear * 1e6,
                          wear_per_pad_20y_mm=wear_mm_20y, usable_mm=P["thickness"] - P["min_thickness"],
                          clamp_drop_after_1y=drop))


# ============================================================ 6. drives and holding
DRIVE = dict(n=2, P_motor=180.0, n_motor=1500.0, eta_fwd=0.75, eta_fwd_cold=0.60, eta_back=0.65,
             T_brake=2.0, pinion_z=14, module=4.0, b=50.0)
M_HOLD = 8000.0                # design yaw moment to hold (doc 07 parked V_e50 side wind; sim. 7.0 kNm)


def drives(pd, fr, T_op_p95):
    r_ring = 150 * 4.0 / 2 / 1e3
    r_pin = 14 * 4.0 / 2 / 1e3
    T_need = pd["T_kNm"]["max_cold_breakaway"] * 1e3 + fr["-30 C"] + T_op_p95
    per_drive = T_need / DRIVE["n"]
    T_gb = per_drive / I_RING                               # gearbox output torque (Nm)
    T_motor = T_gb / (I_GB * DRIVE["eta_fwd_cold"])
    T_motor_one = 2 * T_motor                              # one drive failed
    T_rated = DRIVE["P_motor"] / (DRIVE["n_motor"] * 2 * math.pi / 60)
    rate = DRIVE["n_motor"] / I_GB / I_RING * 360 / 60      # deg/s
    hold_per_drive = DRIVE["T_brake"] * I_GB * DRIVE["eta_back"] * I_RING
    # holding: one pinion takes everything (backlash), no friction credit
    F_one = M_HOLD / r_ring
    T_gb_hold = F_one * r_pin
    return dict(T_need_Nm=T_need, per_drive_at_ring_Nm=per_drive, T_gearbox_out_Nm=T_gb,
                T_motor_Nm=T_motor, T_motor_one_drive_Nm=T_motor_one, T_motor_rated_Nm=T_rated,
                yaw_rate_deg_s=rate, motor_brake_Nm=DRIVE["T_brake"],
                hold_capacity_per_drive_at_ring_kNm=hold_per_drive / 1e3,
                hold_case=dict(M_design_kNm=M_HOLD / 1e3, F_one_pinion_kN=F_one / 1e3,
                               T_gearbox_static_Nm=T_gb_hold, required_gearbox_static_Nm=2 * T_gb_hold),
                F_operating_per_pinion_kN=per_drive / r_ring / 1e3)


# ============================================================ 7. gear check
def gear_check(dr):
    m, b, z1, z2 = 4.0, DRIVE["b"], 14, 150
    d1 = m * z1
    u = z2 / z1
    YFS = dict(pinion=4.3, ring=4.0)        # x1 = +0.3, x2 = 0 (ISO 6336-3 charts)
    ZE, ZH, Zeps = 189.8, 2.49, 0.90
    lim = dict(pinion=dict(F=500.0, H=1500.0, mat="18CrNiMo7-6 case hardened"),
               ring=dict(F=370.0, H=1150.0, mat="42CrMo4, teeth induction hardened (slewing ring option)"))
    YNT_static, ZNT_static = 2.5, 1.6
    out = {}
    for case, F in (("static hold, one pinion", dr["hold_case"]["F_one_pinion_kN"] * 1e3),
                    ("yawing, max cold", dr["F_operating_per_pinion_kN"] * 1e3)):
        sH = ZE * ZH * Zeps * math.sqrt(F / (b * d1) * (u + 1) / u)
        row = dict(F_kN=F / 1e3, sigma_H=sH)
        static = case.startswith("static")
        for g in ("pinion", "ring"):
            sF = F / (b * m) * YFS[g]
            sFP = lim[g]["F"] * 2 * (YNT_static if static else 1.0)
            sHP = lim[g]["H"] * (ZNT_static if static else 1.0)
            row[g] = dict(sigma_F=sF, S_F=sFP / sF, S_H=sHP / sH)
        out[case] = row
    out["materials"] = {k: v["mat"] for k, v in lim.items()}
    return out


# ============================================================ 8. electrical
def electrical(pd, fr):
    w = math.radians(0.5)
    P_mech = (pd["T_kNm"]["nominal"] * 1e3 + fr["warm"]) * w
    P_el = P_mech / (DRIVE["eta_fwd"] * 0.70 * 0.95) + 2 * 20.0      # motor 0.70, VFD 0.95, 2 brake coils 20 W (held)
    duty, P_base = 0.20, 54.0
    E72 = 72 * (duty * P_el + P_base)
    return dict(P_mech_W=P_mech, P_el_yawing_W=P_el, E_72h_Wh=E72, installed_kWh=1.5 * E72 / 1e3,
                doc13_installed_kWh=8.4)


# ============================================================ 9. cable loop
def cable_loop():
    turns, torsion = 3.0, 150.0                # deg per m, torsion-rated wind turbine cables
    L = turns * 360 / torsion
    return dict(turns_max=turns, torsion_deg_per_m=torsion, free_length_m=L, chosen_m=7.5)


def main():
    tt = tower_top()
    W, M_grav, rows = bearing_loads(tt)
    Mmax = max(r["M_tilt"] for r in rows.values())
    Frmax = max(r["Fr"] for r in rows.values())
    ring = ring_check(rows)
    fr = ring_friction(W, M_grav)
    T_op_p95 = max(v["Myaw_p95"] for v in H.DUTY["per_wind"].values())
    pd = pads(T_op_p95)
    dr = drives(pd, fr, T_op_p95)
    s = dict(
        tower_top=dict(m_above_bearing_kg=tt["m_above"], m_tower_side_kg=tt["m_tower_side"],
                       m_total_kg=tt["m_total"], x_cg_mm=tt["x_cg"], z_cg_mm=tt["z_cg"],
                       items=tt["items"], yaw_above=tt["yaw_above"], tower_side=tt["tower_side"]),
        loads=dict(W_kN=W / 1e3, M_grav_kNm=M_grav / 1e3, h_hub_m=H_HUB,
                   sets={k: {kk: vv / 1e3 for kk, vv in v.items()} for k, v in rows.items()}),
        bolts=bolt_checks(Mmax, Frmax, W),
        ring=dict(geometry=YAW_RING, checks=ring, friction_Nm=fr),
        slip=slip_argument(tt),
        yaw_moments=dict(op_p95_Nm=T_op_p95, hold_design_Nm=M_HOLD,
                         sim_design_Nm=H.SIM["ultimate_envelope"]["Myaw"]["design"],
                         sim_governing=H.SIM["ultimate_envelope"]["Myaw"]["governing"]),
        pads=pd, drives=dr, gears=gear_check(dr), electrical=electrical(pd, fr), cable=cable_loop(),
    )
    (OUT / "yaw_summary.json").write_text(json.dumps(s, indent=1, default=float))
    print(json.dumps(s, indent=1, default=lambda x: round(x, 3)))


if __name__ == "__main__":
    main()
