"""M8 hub, collective pitch, rotor brake and yaw checks (doc 35 §5-6).

Run after dlc_m8.py, structure_m8.py and bedplate_m8.py:  python3 hub_yaw_m8.py  -> results/hub_yaw_m8.json

Reuses the doc 13/24/25 models (hub.py, collective.py, yaw.py): pitch moments, slewing-ring
Hertz/ISO 281 checks, bearing friction, collective linkage kinematics, yaw ring/bolts/gears.
Their load inputs are replaced by the M8 SLM (structure_m8.py) and the M8 simulation
envelope (dlc_m8.py). The M8 Turbine (TSR 5.5 blade) is put into hub.py for the pitch moments.
The bedplate mass comes from bedplate_m8.py (the real NP1-300 is 333 kg, not the 150 kg of doc 25).
"""
from __future__ import annotations
import json, math
import numpy as np
import common as C
import sim
sim.Blade = C.Blade8
import hub as H  # noqa: E402
import collective as CO  # noqa: E402
# M8 linkage (cad/hub_m8 clash check, doc 37): pin plane 150 mm and yoke eye 140 mm from the rotor axis, so the
# r 140 crank pin passes outside the drum bearing housing without a phase shift
CO.S_P, CO.R_Y = 150.0, 140.0
import yaw as Y  # noqa: E402
from bem import solve  # noqa: E402
import dlc_m8 as D  # noqa: E402

SLM = json.loads((C.OUT / "slm_m8.json").read_text())["ultimate_design_values_gamma_3_kN_kNm"]
SIM = json.loads((C.OUT / "dlc_m8" / "dlc_summary.json").read_text())
BLD = json.loads((C.OUT / "blade_m8.json").read_text())
GEN = json.loads((C.OUT / "generator_m8.json").read_text())
SIM_C = H.SIM
BL = BLD["carbon"]          # plain carbon caps (doc 10 build), recommended for M8
M_B, R_COG = BL["mass_kg"], BL["r_cog_m"]

H.SLM, H.SIM = SLM, SIM
H.TB = sim.Turbine(**{**D.RD.TB_KW, "m_blade": M_B})
H.R_COG, H.RPM_MAX = R_COG, C.RPM_MAX
# lifetime pitch duty (doc 13 run_pitch_duty.py): same controller and travel; loads scaled by the flap DEL ratio
K_DEL = SIM["fatigue_DEL"]["Mflap0"]["DEL_1e7"] / SIM_C["fatigue_DEL"]["Mflap0"]["DEL_1e7"]
LIFE = dict(H.LIFE)
for k in ("M_eq_motion_weighted_kNm", "M_mean_motion_weighted_kNm", "Mres_DEL_m3_1e7_kNm", "Mres_DEL_m5_1e7_kNm"):
    LIFE[k] = H.LIFE[k] * K_DEL
W_MAXSIM = SIM["ultimate_envelope"]["rpm"]["characteristic"] * math.pi / 30
W_TRIP = C.RPM_TRIP * math.pi / 30
_bp = C.OUT / "bedplate_m8.json"
BEDPLATE = (("Bedplate NP8-300 (bedplate_m8.py)", json.loads(_bp.read_text())["chosen_mass_kg"]) if _bp.exists()
            else ("Bedplate NP1-300 as drawn (doc 32)", 333.0))


def pitch_bearing():
    sets = {
        "SLM H parked flap": dict(M=SLM["H_parked"]["M_yB"] * 1e3, Fa=0.0, Fr=SLM["H_parked"]["F_x_shaft"] * 1e3 / 3),
        "SLM E overspeed": dict(M=0.0, Fa=SLM["E_max_speed"]["F_zB"] * 1e3, Fr=0.0),
        "SLM G shutdown": dict(M=SLM["G_shutdown"]["M_xB"] * 1e3, Fa=1.35 * M_B * W_TRIP ** 2 * R_COG, Fr=0.0),
        "Simulated envelope": dict(M=SIM["ultimate_envelope"]["Mres0"]["design"], Fa=1.35 * M_B * W_MAXSIM ** 2 * R_COG,
                                   Fr=SIM["ultimate_envelope"]["thrust"]["design"] / 3),
    }
    M_eq, F_eq = LIFE["M_eq_motion_weighted_kNm"] * 1e3, M_B / 20.5 * LIFE["F_eq_motion_weighted_kN"] * 1e3 * (C.RPM / 178) ** 2
    revs_req = 2 * LIFE["pitch_travel_revs_20y"]
    cands = []
    for Dpw in (0.250, 0.275, 0.300, 0.325, 0.350, 0.375, 0.400):
        for Dw in (0.0190, 0.0222, 0.0254, 0.0300):
            Z = int(math.floor(math.pi * Dpw / (Dw * 1.12)))
            ok, rows = True, {}
            for n, L in sets.items():
                p = H.hertz_pmax(H.ball_load(L["M"], L["Fa"], L["Fr"], Dpw, Z), Dw, Dpw)
                s0 = (H.P_STATIC / p) ** 3
                need = 1.25 if n.startswith("SLM") else 1.5
                rows[n] = round(s0, 2); ok &= s0 >= need
            L10 = (H.ca_iso(Dw, Dpw, Z) / (F_eq + 2.5 * M_eq / Dpw)) ** 3 * 1e6
            ok &= L10 >= revs_req
            cands.append(dict(Dpw=Dpw, Dw=Dw, Z=Z, s0=rows, L10_over_req=round(L10 / revs_req, 1), ok=bool(ok)))
    # blade bolt circle (Ø0.28 root, 12 x M16 on Ø245) must sit inside the inner ring: Dpw >= PCD + 55 mm
    chosen = min((c for c in cands if c["ok"] and c["Dpw"] >= 0.300), key=lambda c: (c["Dpw"], c["Dw"]))
    Dpw = chosen["Dpw"]
    od = Dpw + chosen["Dw"] + 0.080
    mass = math.pi / 4 * (od ** 2 - (Dpw - 0.07) ** 2) * 0.055 * 0.65 * 7850
    fr = {}
    for lab, mu, seal in (("warm", 0.006, 40.0), ("-30 C", 0.012, 120.0)):
        Lg = sets["SLM G shutdown"]
        fr[lab] = dict(emergency_SLM_G=H.friction_torque(Lg["M"], Lg["Fa"], 0, Dpw, mu, seal, od - 0.02),
                       emergency_sim=H.friction_torque(SIM["per_dlc_max"]["5.1-estop"]["Mres0"] * 1.35,
                                                       1.35 * M_B * W_TRIP ** 2 * R_COG, 0, Dpw, mu, seal, od - 0.02),
                       operating_eq=H.friction_torque(M_eq, F_eq, 0, Dpw, mu, seal, od - 0.02))
    return dict(load_sets={k: {kk: round(vv / 1e3, 2) for kk, vv in v.items()} for k, v in sets.items()},
                chosen=chosen, od=round(od, 3), mass_kg=round(mass, 1), friction_Nm={k: {kk: round(vv) for kk, vv in v.items()} for k, v in fr.items()},
                doc24=dict(Dpw=0.250, Dw=0.0222, mass_kg=19.0))


def collective(brg, pm):
    """Doc 24 linkage with the crank radius scaled up so the cylinder force stays in a standard size."""
    resist = 1.35 * abs(pm["worst_resisting_feather_Nm"])
    T_trip = brg["friction_Nm"]["-30 C"]["emergency_SLM_G"] + resist
    out = {}
    for R_c in (110.0, 125.0, 140.0):
        CO.R_C = R_c
        CO.BETA = CO.yoke_eye_angle()
        th, xy, dxdth, ang = CO.kinematics()
        lever = np.abs(dxdth) / 1e3
        F_des = 3 * T_trip / lever / CO.ETA_LINK
        F_rated = math.ceil(float(F_des.max()) * 1.2 / 500) * 500
        E_stroke = float(abs(np.trapezoid(F_des / 0.90, xy / 1e3))) / 0.85
        E_mod = 0.5 * 16.7 * (56.0 ** 2 - 30.0 ** 2)
        F_storm = 3 * 1.5 * abs(pm["storm_hold_Nm"]) / float(lever.min())
        out[f"crank_r{int(R_c)}"] = dict(stroke_mm=round(float(xy.max() - xy.min()), 1), F_trip_design_kN=round(float(F_des.max()) / 1e3, 1),
                                         F_rated_kN=F_rated / 1e3, motor_T_peak_Nm=round(F_rated * 5e-3 / (2 * math.pi * 0.9 * 2), 1),
                                         E_stroke_kJ=round(E_stroke / 1e3, 2), strokes_EOL_one_module=round(0.8 * E_mod / E_stroke, 1),
                                         F_storm_on_screw_kN=round(F_storm / 1e3, 1),
                                         motor_brake_needed_Nm=round(F_storm * 5e-3 * 0.8 / (2 * math.pi * 2) * 1.2, 1))
    CO.R_C = 140.0; CO.BETA = CO.yoke_eye_angle()
    return dict(T_trip_per_blade_Nm=round(T_trip), resisting_aero_ctm_Nm=round(resist), options=out,
                doc24=dict(F_trip_design_kN=20.9, F_rated_kN=25.5, motor_T_peak_Nm=11.3, strokes_EOL=5.1))


def welded_hub(brg):
    """Doc 24 welded S355NL hub resized: necks follow the larger pitch bearing."""
    Dpw = brg["chosen"]["Dpw"]
    M_slm = SLM["H_parked"]["M_yB"] * 1e3
    DEL3 = LIFE["Mres_DEL_m3_1e7_kNm"] * 1e3
    rows = []
    for d_neck in (Dpw + 0.06, Dpw + 0.08):
        for t in (0.010, 0.012, 0.015, 0.020):
            W = math.pi * (d_neck ** 4 - (d_neck - 2 * t) ** 4) / (32 * d_neck)
            s = 2.5 * M_slm / W
            ds = 2.5 * 2 * DEL3 / W
            ds_allow = 90e6 * (2e6 / 1e7) ** (1 / 3) / 1.25
            rows.append(dict(d_neck_mm=round(d_neck * 1e3), t_mm=t * 1e3, static_MPa=round(s / 1e6), static_allow=323,
                             fat_MPa=round(ds / 1e6, 1), fat_allow=round(ds_allow / 1e6, 1),
                             ok=bool(s <= 323e6 and ds <= ds_allow)))
    ch = next(r for r in rows if r["ok"])
    d, t = ch["d_neck_mm"] / 1e3, ch["t_mm"] / 1e3
    R_sh, t_sh, L_sh = d / 2 + 0.085, t, d + 0.11              # shell grows with the necks (doc 24: Ø460 for Ø330 necks)
    rho = 7850
    m = (2 * math.pi * R_sh * L_sh * t_sh * rho - 3 * math.pi / 4 * (d - 2 * t) ** 2 * t_sh * rho * 1.15
         + 3 * math.pi * (d - t) * t * (0.35 + 0.05 - R_sh + 0.03) * rho
         + 3 * math.pi / 4 * ((brg["od"]) ** 2 - (Dpw - 0.06) ** 2) * 0.025 * rho
         + math.pi / 4 * (0.52 ** 2 - 0.36 ** 2) * 0.030 * rho + math.pi / 4 * ((2 * R_sh) ** 2 - 0.3 ** 2) * 0.012 * rho + 9.0)
    # hub-to-drum joint
    M_hub = max(SIM["ultimate_envelope"]["Mtilt"]["design"], SIM["ultimate_envelope"]["Myaw"]["design"], SLM["B_yaw"]["M_shaft"] * 1e3)
    T_hub = max(SLM["G_shutdown"]["M_x_shaft"] * 1e3, SIM["ultimate_envelope"]["Qgen"]["design"])
    Fx = max(SLM["H_parked"]["F_x_shaft"] * 1e3, SIM["ultimate_envelope"]["thrust"]["design"])
    joint = {}
    for size, As in (("M16", 157e-6), ("M20", 245e-6)):
        for pcd in (0.40, 0.44):
            for n in range(12, 41, 2):
                Fp = 0.7 * 1000e6 * As
                Ft = 4 * M_hub / (n * pcd) + Fx / n
                if n * 0.30 * (Fp - 0.8 * Ft) / 1.25 >= T_hub / (pcd / 2) and Ft <= 0.9 * 1000e6 * As / 1.25:
                    joint[f"{size} PCD {pcd * 1e3:.0f}"] = dict(n=n, Ft_kN=round(Ft / 1e3, 1)); break
    return dict(neck_checks=rows, chosen=ch, shell_d_mm=round(2 * R_sh * 1e3), mass_kg=round(m, 1), doc24_mass_kg=117.0,
                joint_loads=dict(M_kNm=round(M_hub / 1e3, 1), T_kNm=round(T_hub / 1e3, 1), Fx_kN=round(Fx / 1e3, 1)), joint=joint,
                joint_doc24="12 x M16 10.9 PCD 400")


def standstill_torque():
    """R3.8 (doc 24): rotor brake alone must hold the rotor with all blades stuck at fine pitch."""
    out = {}
    for name, bl in (("current_D7.5", __import__("bem").Blade(R=3.75, tsr_design=6.5, cl_design=1.0)), ("M8", C.blade_shape())):
        out[name] = {f"{V} m/s": round(max(solve(bl, V, 0.05, p, 1.35).torque for p in (-2.0, 0.0, 2.0)) / 1e3, 2) for V in (25, 32, 40)}
    out["brake_kNm"] = 8.73
    return out


def yaw_m8(hub_pitch_mass):
    tt = Y.tower_top()
    rep = {"Blades": ("Blades 3 x %.1f kg (doc 35)" % M_B, 3 * M_B, -800),
           "Hub + collective": ("Hub + collective pitch M8", hub_pitch_mass, -750),
           "Generator rotor": ("Generator rotor M8", GEN["mass_kg"]["rotor"]["M8"], -466),
           "Generator stator": ("Generator stator M8", GEN["mass_kg"]["stator"]["M8"], -385),
           "Spindle": ("Spindle (longer by 30 mm)", 63.0, -435),
           "Bedplate": (BEDPLATE[0], BEDPLATE[1], -40)}
    items = []
    for it in tt["items"]:
        key = next((k for k in rep if it[0].startswith(k)), None)
        items.append((rep[key][0], rep[key][1], rep[key][2], it[3]) if key else it)
    orig = Y.tower_top
    def tower_top_m8():
        m = sum(i[1] for i in items + tt["yaw_above"])
        x = sum(i[1] * i[2] for i in items + tt["yaw_above"]) / m
        z = sum(i[1] * i[3] for i in items + tt["yaw_above"]) / m
        return dict(tt, items=items, m_above=m, x_cg=x, z_cg=z, m_total=m + tt["m_tower_side"])
    Y.tower_top = tower_top_m8
    t5 = tower_top_m8()
    W, M_grav, rows = Y.bearing_loads(t5)
    Mmax = max(r["M_tilt"] for r in rows.values()); Frmax = max(r["Fr"] for r in rows.values())
    ring = Y.ring_check(rows)
    bolts = Y.bolt_checks(Mmax, Frmax, W)
    M_hold = Y.M_HOLD * SIM["ultimate_envelope"]["Myaw"]["design"] / SIM_C["ultimate_envelope"]["Myaw"]["design"]
    Y.M_HOLD = M_hold
    # ring options: next standard four-point sizes, external gear m 4 (pitch radius grows with the ring)
    alt, choice = {}, None
    for Dpw, Dw, Z, r_ring in ((0.360, 0.019, 53, 0.300), (0.410, 0.0222, 52, 0.330), (0.450, 0.0222, 56, 0.360)):
        s0 = {k: round((H.P_STATIC / H.hertz_pmax(H.ball_load(s["M_tilt"], s["Fa"], s["Fr"], Dpw, Z), Dw, Dpw)) ** 3, 2)
              for k, s in rows.items()}
        alt[f"Dpw {Dpw * 1e3:.0f}"] = s0
        if choice is None and min(s0.values()) >= 1.25:
            choice = dict(Dpw_mm=round(Dpw * 1e3), r_gear_m=r_ring, s0_min=min(s0.values()))
    r_ring, r_pin = choice["r_gear_m"], 0.028
    T_gb_hold = M_hold / r_ring * r_pin
    for b_face in (50.0, 60.0, 70.0, 80.0):
        Y.DRIVE["b"] = b_face
        gear = Y.gear_check(dict(hold_case=dict(F_one_pinion_kN=M_hold / r_ring / 1e3), F_operating_per_pinion_kN=4.0))
        g = gear["static hold, one pinion"]
        if min(g["pinion"]["S_H"], g["ring"]["S_H"]) >= 1.1 and min(g["pinion"]["S_F"], g["ring"]["S_F"]) >= 2.0:
            break
    choice["gear_face_mm"] = b_face
    Y.DRIVE["b"] = 50.0
    Y.tower_top = orig
    return dict(m_above_bearing_kg=round(t5["m_above"]), m_above_tower_flange_kg=round(t5["m_total"]), x_cg_mm=round(t5["x_cg"]),
                doc25=dict(m_above_bearing_kg=969, m_total_kg=1103, M_tilt_max_kNm=34.6, s0=1.44),
                M_tilt_kNm={k: round(v["M_tilt"] / 1e3, 1) for k, v in rows.items()},
                ring_s0_Dpw360={k: round(v["s0"], 2) for k, v in ring.items()}, ring_options_s0=alt, ring_chosen=choice,
                bolts={k: dict(F_ext_kN=round(v["F_ext_kN"], 1), ratio=round(v["ratio"], 2)) for k, v in bolts.items()},
                yaw_hold_design_kNm=round(M_hold / 1e3, 1), gearbox_static_needed_Nm=round(2 * T_gb_hold),
                gear_static_S_F={g: round(gear["static hold, one pinion"][g]["S_F"], 2) for g in ("pinion", "ring")},
                gear_static_S_H={g: round(gear["static hold, one pinion"][g]["S_H"], 2) for g in ("pinion", "ring")})


def main():
    pm_all, J_blade = H.pitch_moments()
    pm = pm_all[0.30]
    brg = pitch_bearing()
    col = collective(brg, pm)
    hub = welded_hub(brg)
    # crank r 140 with the pin plane moved out (cad/hub_m8 clash check); ~28.5 kN cylinder
    opt_key = "crank_r140"   # chosen: clash-free in cad/hub_m8 (doc 37)
    opt = col["options"][opt_key]
    col["chosen"] = opt_key
    parts = {"pitch bearings x 3 (ungeared)": 3 * brg["mass_kg"], "cranks x 3": 3 * 10.0, "links x 3": 3 * 1.5,
             "yoke + guide rods": 8.0, "electric cylinder + motor": 14.0 if opt["F_rated_kN"] > 25.5 else 11.0,
             "supercap module(s) + heater": 3.5 * max(1, math.ceil(2 / opt["strokes_EOL_one_module"])),
             "nose housing": 6.0, "controller, sensors, switches": 3.0, "spinner (larger), boots, slip ring, cabling": 12.0}
    m_pitch = sum(parts.values())
    res = dict(pitch_moments_Nm=dict(worst_resisting_feather=pm["worst_resisting_feather_Nm"],
                                     worst_resisting_operating=pm["worst_resisting_operating_Nm"], storm_hold=pm["storm_hold_Nm"],
                                     J_blade_kgm2=round(J_blade, 2)),
               pitch_bearing=brg, collective=col, welded_hub=hub,
               hub_pitch_mass=dict(parts={k: round(v, 1) for k, v in parts.items()}, pitch_system=round(m_pitch, 1),
                                   hub=hub["mass_kg"], total=round(m_pitch + hub["mass_kg"], 1), doc24_total=239.0),
               rotor_brake_standstill_aero_torque_kNm=standstill_torque(),
               rotor_brake=dict(parked_aero_torque_sim_char_kNm=round(SIM["ultimate_envelope"]["Qaero"]["characteristic"] / 1e3, 2),
                                parked_aero_torque_sim_char_current_kNm=round(SIM_C["ultimate_envelope"]["Qaero"]["characteristic"] / 1e3, 2),
                                governing=SIM["ultimate_envelope"]["Qaero"]["governing"],
                                brake_current_kNm=8.73, brake_M8_kNm=13.1, ratio_M8=round(13.1e3 / SIM["ultimate_envelope"]["Qaero"]["characteristic"], 2),
                                note="3 calipers of the doc 07 type on the same disc"),
               slm_G_shaft_torque_kNm=SLM["G_shutdown"]["M_x_shaft"])
    res["yaw"] = yaw_m8(res["hub_pitch_mass"]["total"])
    (C.OUT / "hub_yaw_m8.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
