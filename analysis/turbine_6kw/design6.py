"""6 kW turbine S6 (doc 30): blades, hub, drivetrain reuse check, yaw-out, tower and foundation, masses.

Run:  python3 design6.py     (~3 min) -> results/design6.json, figures D01-D03

First-pass design with the IEC 61400-2 simple load model (SLM) and scaled operating loads, using the
project models unchanged (analysis/loads/slm.py, blade/blade.py, tower/tower.py) with 6 kW inputs,
as doc 26 did for V5. Aeroelastic load cases for the stall-controlled rotor are a later step (doc 30 §10).
"""
from __future__ import annotations
import json, math, sys, io, contextlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
ROOT = HERE.parent
OUT = HERE / "results"
for p in ("rotor", "loads", "blade", "tower", "size_tsr_map"):
    sys.path.insert(0, str(ROOT / p))
sys.argv = sys.argv[:1]
from bem import Blade, ROUGH, Polar, solve  # noqa: E402
import slm as S  # noqa: E402
import blade as BLD  # noqa: E402
import tower as T  # noqa: E402
import model as m27  # noqa: E402

DES = json.loads((OUT / "design.json").read_text())
REG = json.loads((OUT / "regulation.json").read_text())
G6 = json.loads((ROOT / "generator6" / "results" / "g6.json").read_text())
SLM12 = json.loads((ROOT / "loads" / "results" / "slm.json").read_text())
YAW12 = json.loads((ROOT / "yaw" / "results" / "yaw_summary.json").read_text())

R = DES["R"]; TSR = DES["tsr"]; RPM = DES["rpm"]; OM = RPM * math.pi / 30
P_SHAFT = m27.SHAFT_PER_E * 6000; Q_RATED = P_SHAFT / OM
RPM_TRIP, RPM_MAX, RPM_MIN = 1.15 * RPM, 1.25 * RPM, 0.25 * RPM
OVERHANG = 0.75              # Rev C generator and spindle unchanged -> same rotor plane as doc 13/25
R_HUB = 0.28                 # blade root flange radius on the fixed hub (no pitch bearing)
BRAKE = 1500.0
C = dict(blue="#2f6db5", orange="#d9822b", green="#3a8f5c", red="#c0392b", grey="#7f8c8d")


def blade_shape(n=30):
    return Blade(R=R, r_hub=R_HUB, tsr_design=TSR, cl_design=1.0, n=n)


# ------------------------------------------------------------------ SLM
def run_slm(m_b, r_cog, m_hub_drum):
    S.R = R; S.blade = blade_shape(); S.A_PROJ_B = S.blade.solidity_area()
    S.M_B, S.R_COG = m_b, r_cog
    S.I_B = m_b * (r_cog * 1.19) ** 2
    S.M_R = 3 * m_b + m_hub_drum
    S.L_RB, S.L_RT, S.E_R = 0.12, OVERHANG, 0.005 * R
    S.P_DESIGN = P_SHAFT
    S.N_DESIGN, S.W_DESIGN, S.Q_DESIGN = RPM, OM, Q_RATED
    S.V_DESIGN = DES["rated_wind"]; S.LAMBDA_DESIGN = OM * R / S.V_DESIGN
    S.N_MAX, S.W_MAX = RPM_MAX, RPM_MAX * math.pi / 30
    S.M_BRAKE = BRAKE
    S.OUT = OUT
    with contextlib.redirect_stdout(io.StringIO()):
        S.main()
    (OUT / "slm.json").rename(OUT / "slm_6kw.json")
    return json.loads((OUT / "slm_6kw.json").read_text())


# ------------------------------------------------------------------ blade
def patch_blade(loads):
    k = (R - R_HUB) / (3.75 - 0.40)
    pts = [(0.40, 1.00), (0.55, 0.70), (0.775, 0.30), (1.5, 0.25), (2.25, 0.21), (3.2, 0.18)]
    pts = [(R_HUB + (r - 0.40) * k, tc) for r, tc in pts] + [(R, 0.18)]
    x, y = zip(*pts)
    BLD.t_over_c = lambda r: float(np.interp(r, x, y))
    BLD.R, BLD.R_HUB = R, R_HUB
    BLD.BL = blade_shape(n=40)
    BLD.OVERHANG = OVERHANG
    BLD.D_TOWER_TIP = 0.37
    BLD.LOADS = loads

    def load_shapes(r, mass_pl):
        c = np.interp(r, BLD.BL.r, BLD.BL.chord)
        dr = np.gradient(r)
        mom = lambda q: np.array([np.sum(q[i:] * (r[i:] - r[i]) * dr[i:]) for i in range(len(r))])
        m_park = mom(c); m_park /= m_park[0]
        bl = blade_shape(n=len(r))
        res = solve(bl, DES["rated_wind"], OM, REG["PF"], 1.225, ROUGH)
        qop = np.interp(r, bl.r, res.dT / bl.dr / 3)
        m_op = mom(qop); m_op /= m_op[0]
        m_g = mom(mass_pl); m_g /= m_g[0]
        return m_park, m_op, m_g
    BLD.load_shapes = load_shapes


def blade_loop():
    m_b, r_cog = 12.0, 1.1
    m_hub_drum = 60.0 + 148.5
    # operating and fatigue loads: doc 11 final (12 kW) scaled. Stall control: flap moment from the
    # cold-air stall curve, fatigue x 1.3 for stall turbulence response (no pitch damping of gusts).
    k_op = REG["thrust"]["stall_flap_max"] / 1570.0
    for it in range(5):
        slm = run_slm(m_b, r_cog, m_hub_drum)
        ult = slm["ultimate_design_values_gamma_3_kN_kNm"]
        k_park = ult["H_parked"]["M_yB"] / 26.02
        loads = dict(SLM_H_flap=ult["H_parked"]["M_yB"] * 1e3, SLM_G_edge=ult["G_shutdown"]["M_xB"] * 1e3,
                     SIM_res=8510.0 * k_park, SIM_op_flap=1.35 * 3850 * k_op * 1.3, DEL_flap=3403 * k_op * 1.3,
                     DEL_edge=1285 * (m_b * r_cog) / (20.5 * 1.55) * 1.1, rpm_max=RPM_MAX, gamma_E=3.0)
        patch_blade(loads)
        res = {}
        for opt, mat, core in (("glass", "UD_glass", False), ("carbon", "UD_carbon", False)):
            d = BLD.design(mat, t_root_wall=0.012, cap_core=core)
            d[f"f_flap_{RPM:.0f}rpm_Hz"] = round(float(BLD.beam_modes(d["_r"], d["_EIf"], d["_mu"], rpm=RPM)[0]), 2)
            d[f"f_edge_{RPM:.0f}rpm_Hz"] = round(float(BLD.beam_modes(d["_r"], d["_EIe"], d["_mu"], rpm=RPM)[0]), 2)
            for k in ("_r", "_mu", "_EIf", "_EIe", "_tcap", "f_flap_178rpm_Hz", "f_edge_178rpm_Hz"):
                d.pop(k)
            res[opt] = d
        new = res["glass"]["mass_kg"]
        if abs(new - m_b) < 0.5:
            break
        m_b, r_cog = new, res["glass"]["r_cog_m"]
    w = RPM_MAX * math.pi / 30
    N_root = 3.0 * res["glass"]["static_moment_kgm_about_axis"] * w ** 2
    res["root_joint"] = root_joint(loads["SLM_H_flap"], N_root)
    res["loads_used_Nm"] = {k: round(v, 1) for k, v in loads.items()}
    return res, slm


def root_joint(M, N):
    out = {}
    for D in (0.20, 0.22, 0.24):
        Dbc = D - 0.035
        for size, As, Fins, d_ins in (("M12", 84.3e-6, 45e3, 0.020), ("M16", 157e-6, 75e3, 0.026)):
            Ft_rd = 0.9 * 1000e6 * As / 1.25
            for n in range(6, 31, 2):
                F = 4 * M / (n * Dbc) + N / n
                if F <= min(Ft_rd, Fins) and math.pi * Dbc / n >= 1.4 * d_ins:
                    out[f"root Ø{D:.2f} m, {size}"] = dict(inserts=n, bolt_circle_m=round(Dbc, 3), F_bolt_kN=round(F / 1e3, 1),
                                                         F_t_Rd_kN=round(Ft_rd / 1e3, 1))
                    break
    return out


# ------------------------------------------------------------------ fixed hub
def fixed_hub(slm, blade):
    """Welded S355NL hub: central ring bolted to the Rev C drum (12 x M16 PCD 400, doc 23 interface),
    three tubular arms ending in the blade root flanges with the ±2° shim seat."""
    ult = slm["ultimate_design_values_gamma_3_kN_kNm"]
    M = ult["H_parked"]["M_yB"] * 1e3
    DEL = blade["loads_used_Nm"]["DEL_flap"]
    rows = []
    for d in (0.22, 0.24, 0.26):
        for t in (0.008, 0.010, 0.012):
            W = math.pi * (d ** 4 - (d - 2 * t) ** 4) / (32 * d)
            s = M / W
            ds = 2 * DEL / W
            ds_allow = 71e6 * (2e6 / 1e7) ** (1 / 3) / 1.35        # detail 71 weld at the flange, 1e7 cycles
            rows.append(dict(d_arm_mm=round(d * 1e3), t_mm=t * 1e3, static_MPa=round(s / 1e6), allow_MPa=round(355 / 1.1),
                             fat_MPa=round(ds / 1e6, 1), fat_allow_MPa=round(ds_allow / 1e6, 1), ok=bool(s <= 355e6 / 1.1 and ds <= ds_allow)))
    ch = next(r for r in rows if r["ok"])
    d, t = ch["d_arm_mm"] / 1e3, ch["t_mm"] / 1e3
    L_arm = R_HUB - 0.19
    rho = 7850
    m = (3 * math.pi * (d - t) * t * L_arm * rho                          # arms
         + 3 * math.pi / 4 * ((d + 0.06) ** 2 - (d - 0.05) ** 2) * 0.025 * rho   # root flanges
         + 2 * math.pi * 0.19 * 0.24 * 0.012 * rho                        # central shell Ø380 x 240
         + math.pi / 4 * (0.48 ** 2 - 0.30 ** 2) * 0.025 * rho            # drum flange PCD 400
         + 4.0)                                                           # shims, spinner brackets
    T_hub = max(ult["G_shutdown"]["M_x_shaft"], ult["F_short_circuit"]["M_x_shaft"]) * 1e3
    Fx = ult["H_parked"]["F_x_shaft"] * 1e3
    M_hub = ult["B_yaw"]["M_shaft"] * 1e3 + Fx * 0.12
    n, pcd, As = 12, 0.40, 157e-6
    Fp = 0.7 * 1000e6 * As
    Ft = 4 * M_hub / (n * pcd) + Fx / n
    slip_ok = n * 0.30 * (Fp - 0.8 * Ft) / 1.25 >= T_hub / (pcd / 2)
    return dict(arm_checks=rows, chosen=ch, mass_kg=round(m, 1), spinner_kg=6.0,
                drum_joint=dict(bolts="12 x M16 10.9 PCD 400 (Rev C interface)", Ft_kN=round(Ft / 1e3, 1),
                                F_t_Rd_kN=round(0.9 * 1000e6 * As / 1.25 / 1e3, 1), slip_ok=bool(slip_ok),
                                T_design_kNm=round(T_hub / 1e3, 2)))


# ------------------------------------------------------------------ drivetrain reuse check
def drivetrain(slm):
    u6 = slm["ultimate_design_values_gamma_3_kN_kNm"]; u12 = SLM12["ultimate_design_values_gamma_3_kN_kNm"]
    f6 = slm["A_fatigue_ranges_kN_kNm"]; f12 = SLM12["A_fatigue_ranges_kN_kNm"]
    rows = {}
    for case, keys in u12.items():
        for k, v in keys.items():
            if k in u6.get(case, {}):
                rows[f"{case} {k}"] = dict(kW6=u6[case][k], kW12=v, ratio=round(u6[case][k] / v, 2))
    fat = {k: dict(kW6=f6[k], kW12=f12[k], ratio=round(f6[k] / f12[k], 2)) for k in f12 if not k.startswith("cycles")}
    shaft_keys = [k for k in rows if any(s in k for s in ("shaft", "F_x"))]
    return dict(ultimate=rows, fatigue_ranges=fat, max_shaft_ratio=max(rows[k]["ratio"] for k in shaft_keys),
                verdict="Doc 07/14 spindle (42CrMo4 140/90) and tapered roller pair reused: every shaft load below the 12 kW values")


# ------------------------------------------------------------------ yaw: masses, ring, yaw-out torque
def parked_forces(gamma_deg, V, rho=1.35, pitch=None):
    """Total force (N) and moment about the yaw axis (Nm) of the parked fixed-pitch rotor, worst azimuth."""
    pitch = REG["PF"] if pitch is None else pitch
    bl = blade_shape(n=30)
    pol = Polar("park", cl0=ROUGH.cl0, cla=ROUGH.cla, clmax=ROUGH.clmax, cd0=ROUGH.cd0, kd=ROUGH.kd,
                cl_cdmin=ROUGH.cl_cdmin, cdmax=1.5)
    g = math.radians(gamma_deg)
    W = V * np.array([math.cos(g), math.sin(g), 0.0])
    best = None
    for psi0 in range(0, 120, 10):
        F = np.zeros(3); Mz = 0.0
        for b in range(3):
            s = math.radians(psi0 + 120 * b)
            e_s = np.array([0.0, math.sin(s), math.cos(s)]); e_t = np.cross([1.0, 0, 0], e_s)
            u_ax, u_tan = W[0], -float(W @ e_t)
            phi = math.atan2(u_ax, u_tan)
            alpha = (np.degrees(phi - np.radians(bl.twist + bl.twist_tip_offset + pitch)) + 180) % 360 - 180
            cl, cd = pol.coeffs(alpha)
            cl = np.where(bl.is_cylinder, 0.0, cl); cd = np.where(bl.is_cylinder, 1.0, cd)
            q = 0.5 * rho * (u_ax ** 2 + u_tan ** 2) * bl.chord * bl.dr
            fx = q * (cl * math.cos(phi) + cd * math.sin(phi)); ft = q * (cl * math.sin(phi) - cd * math.cos(phi))
            for i in range(len(bl.r)):
                f = fx[i] * np.array([1.0, 0, 0]) + ft[i] * e_t
                pos = np.array([-OVERHANG, 0, 0]) + bl.r[i] * e_s
                F += f; Mz += pos[0] * f[1] - pos[1] * f[0]
        if best is None or abs(Mz) > abs(best[1]):
            best = (F, Mz)
    return best


def yaw(m_blade, m_hub):
    items = [("Blades 3 x %.1f kg" % m_blade, 3 * m_blade, -770, 570), ("Fixed hub + spinner", m_hub, -720, 570),
             ("Generator rotor G6 (no fins)", 148.5, -451, 544), ("Generator stator G6", 115.0, -370, 537),
             ("Spindle (doc 14, reused)", 57.0, -420, 535), ("Bedplate P1 weldment (reused)", 150.0, -40, 170),
             ("Nacelle cover and electrics", 20.0, 0, 300), ("Slip ring (signals only), sensors, cabling, 1 caliper", 15.0, -150, 400)]
    above = YAW12["tower_top"]["yaw_above"]
    m_above = sum(i[1] for i in items + [tuple(a) for a in above])
    m_total = m_above + YAW12["tower_top"]["m_tower_side_kg"]
    x_cg = sum(i[1] * i[2] for i in items + [tuple(a) for a in above]) / m_above
    # ring: doc 25 SLM set scaled with the 6 kW SLM H thrust and the head mass
    slm = json.loads((OUT / "slm_6kw.json").read_text())["ultimate_design_values_gamma_3_kN_kNm"]
    Fr6 = slm["H_parked"]["F_x_shaft"]
    M6 = Fr6 * 0.605 + slm["B_yaw"]["M_shaft"] + m_above * 9.81 * abs(x_cg) / 1e6
    M12 = YAW12["loads"]["sets"]["SLM H parked thrust + SLM shaft moment (gamma 3.0)"]["M_tilt"]
    s0 = YAW12["ring"]["checks"]["SLM H parked thrust + SLM shaft moment (gamma 3.0)"]["s0"] * M12 / M6
    # yaw-out: aero yaw moment while turning the stopped rotor 0 -> 90 deg at storm onset
    yo = {}
    for V in (20.0, 25.0, 30.0):
        yo[f"{V:g}"] = {f"{g}": round(parked_forces(g, V)[1] / 1e3, 2) for g in range(0, 91, 15)}
    M_aero_max = max(abs(v) for d in yo.values() for v in d.values())
    pads = YAW12["pads"]["T_kNm"]["max_cold_breakaway"]
    need = M_aero_max * 1.35 + pads + YAW12["ring"]["friction_Nm"]["-30 C"] / 1e3
    cap_cont = 2 * YAW12["drives"]["per_drive_at_ring_Nm"] / 1e3 * YAW12["drives"]["T_motor_rated_Nm"] / YAW12["drives"]["T_motor_one_drive_Nm"]
    # parked at 90 deg in V_e50: holding moment
    F90, M90 = parked_forces(90, 77.0)
    F0, M0 = parked_forces(0, 77.0)
    return dict(items=items, m_above_bearing_kg=round(m_above), m_above_tower_flange_kg=round(m_total), x_cg_mm=round(x_cg),
                ring=dict(choice="doc 25 ring Dpw 360 reused", M_tilt_6kW_kNm=round(M6, 1), M_tilt_12kW_kNm=M12, s0=round(s0, 2)),
                yaw_out=dict(aero_yaw_moment_kNm_by_wind_and_angle=yo, aero_max_kNm=round(M_aero_max, 2),
                             pads_breakaway_cold_kNm=pads, need_kNm=round(need, 2), drives_rated_capacity_kNm=round(cap_cont, 1),
                             time_90deg_s=180, energy_Wh=round(95 * 180 / 3600 * need / 6.63 * 1.5, 1)),
                parked_Ve50=dict(yawed_90_thrust_kN=round(float(np.linalg.norm(F90)) / 1e3, 1), yawed_90_yaw_moment_kNm=round(M90 / 1e3, 2),
                                 facing_thrust_kN=round(float(np.linalg.norm(F0)) / 1e3, 1), facing_yaw_moment_kNm=round(M0 / 1e3, 2),
                                 yaw_hold_doc25_kNm=YAW12["yaw_moments"]["hold_design_Nm"] / 1e3))


# ------------------------------------------------------------------ tower and footing
def tower(m_top, slm, blade_area):
    ops12 = json.loads((ROOT / "tower" / "results" / "ops_loads_monopole_18m.json").read_text())
    m27.calibrate()
    r12 = m27.evaluate(12, 6.5, 3.75, 70.0)
    k_fat = REG["thrust"]["stall_cold_max"] / (r12["T_op"] * 1000) * 1.3
    k_ult = slm["ultimate_design_values_gamma_3_kN_kNm"]["H_parked"]["F_x_shaft"] / 41.64
    ops = dict(ops12)
    ops["M_base_char"] = ops12["M_base_char"] * k_ult
    ops["F_top_equiv_char"] = ops12["F_top_equiv_char"] * k_ult
    ops["fatigue"] = {lvl: [[rng * k_fat, n] for rng, n in data] for lvl, data in ops12["fatigue"].items()}
    T.M_TOP = m_top
    T.J_TOP = 300.0 * m_top / 480.0 * 0.9
    T.D_TOP = 0.32
    T.F_SIDE_VE50 = 8.0e3 * blade_area / 0.849 + 5.8e3
    T.M_TOP_GRAV = m_top * OVERHANG * 0.45 * T.G
    T.SLM_FX_DESIGN = slm["ultimate_design_values_gamma_3_kN_kNm"]["H_parked"]["F_x_shaft"] * 1e3
    T.SLM_FX_CHAR = T.SLM_FX_DESIGN / 3
    T.F_MAX_SOFT = 3 * RPM_MIN / 60 / 1.1
    T.F_MIN_SOFT = RPM_MIN / 60 * 1.1
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
                    D, t_, *_ = tw.geom(np.linspace(0, H, 50))
                    if np.max(D / t_) > T.DT_MAX:
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
    fnd["rock (anchored plinth)"] = T.rock_anchor_plinth(M_design, V_top)
    for f in fnd.values():
        if "K_theta" in f:
            f["K_theta_MNm_per_rad"] = round(f.pop("K_theta") / 1e6)
    r.pop("_profiles", None)
    r["geometry"] = dict(H=H, D_base=round(tw.D_base, 2), D_top=tw.D_top, t_mm=[round(x * 1000) for x in tw.t])
    f1 = r["f1_rigid_Hz"]
    r["exclusion_zone_rpm"] = [round(60 * f1 / 1.1, 1), round(60 * f1 * 1.1, 1)]
    r["fatigue_damage"] = T.fatigue_check(tw, ops["fatigue"])
    r["base_flange"] = dict(M_design_kNm=round(M_design / 1e3, 1), **(T.flange_bolts(M_design, tw.D_base) or {}))
    return dict(tower=r, foundations=fnd, window_Hz=[round(T.F_MIN_SOFT, 2), round(T.F_MAX_SOFT, 2)],
                scaling=dict(k_ultimate=round(k_ult, 2), k_fatigue=round(k_fat, 2)),
                twelve_kW_doc09=dict(mass_kg=1940, D_base=None))


# ------------------------------------------------------------------ power electronics and control ratings
def electronics():
    e = G6["electrical"]
    return dict(
        generator_current_rated_A=e["by_magnet_T"]["100C"]["current_rated_A"], generator_current_10s_A=e["current_10s_A"],
        front_end="doc 12 SiC active rectifier, 1,200 V, same hardware as 12 kW (rated 25 A), firmware limits 13 A / 20 A 10 s",
        dc_bus_V=750, dump_chopper_kW=12, ac_module_kW=6.5, single_phase_possible=True,
        battery_module="doc 12 isolated 48 V module, same", braking_resistor=f"3 x {G6['resistor']['R_ext_ohm']:g} ohm star via K1 (doc 29)",
        aux_battery_for_yaw_out_Wh=200)


def figure_elevation(res):
    fig, ax = plt.subplots(figsize=(5.2, 7.5))
    H = 18.0; tw = res["tower"]["tower"]["geometry"]
    Db, Dt = tw["D_base"], tw["D_top"]
    ax.fill([-Db / 2, Db / 2, Dt / 2, -Dt / 2], [0, 0, H, H], color="#c8ced6", ec="k", lw=0.8)
    ax.add_patch(plt.Rectangle((-1.2, H), 1.6, 0.75, fc="#e6e9ee", ec="k"))
    ax.add_patch(plt.Rectangle((-1.05, H - 0.02), 0.25, 0.8, fc="#9aa3ad", ec="k"))     # generator drum side view
    hub_y = H + 0.57
    ax.plot([-OVERHANG - 0.2, -OVERHANG - 0.2], [hub_y - R, hub_y + R], color="#2f6db5", lw=3)
    ax.add_patch(plt.Circle((-OVERHANG - 0.25, hub_y), 0.22, fc="#ffffff", ec="k"))
    f = res["tower"]["foundations"]
    ax.add_patch(plt.Rectangle((-2.0, -1.2), 4.0, 1.2, fc="#d9cbb2", ec="k", hatch="//"))
    ax.annotate("", (2.4, 0), (2.4, H), arrowprops=dict(arrowstyle="<->"))
    ax.text(2.55, H / 2, "18 m hub tower\ntilt-up monopole", va="center", fontsize=8)
    ax.annotate("", (-3.9, hub_y - R), (-3.9, hub_y + R), arrowprops=dict(arrowstyle="<->"))
    ax.text(-4.0, hub_y, "Ø6.0 m\nfixed pitch\n164 rpm", ha="right", va="center", fontsize=8)
    ax.text(0.5, H + 1.1, "G6 generator (Rev C)\nactive yaw, yaw-out parking", fontsize=8)
    ax.text(0, -1.7, "spread footing or rock plinth", ha="center", fontsize=8)
    ax.text(0.6, 4, f"Ø{Db:.2f} base\nØ{Dt:.2f} top", fontsize=8)
    ax.set_xlim(-6.5, 5); ax.set_ylim(-2.2, H + R + 1.2); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("D01 S6 6 kW turbine, side elevation (schematic)", fontsize=9)
    fig.tight_layout(); fig.savefig(OUT / "D01-elevation.png", dpi=160); plt.close(fig)


def figure_yaw(y):
    fig, ax = plt.subplots(figsize=(7, 3.4))
    for V, col in (("20", C["blue"]), ("25", C["orange"]), ("30", C["red"])):
        d = y["yaw_out"]["aero_yaw_moment_kNm_by_wind_and_angle"][V]
        ax.plot([int(k) for k in d], list(d.values()), "o-", color=col, label=f"{V} m/s")
    ax.axhline(y["yaw_out"]["drives_rated_capacity_kNm"], color=C["grey"], ls="--")
    ax.text(2, y["yaw_out"]["drives_rated_capacity_kNm"] + 0.2, "two doc 25 drives at rated motor torque", fontsize=7)
    ax.axhline(-y["yaw_out"]["drives_rated_capacity_kNm"], color=C["grey"], ls="--")
    ax.set_xlabel("Yaw angle out of the wind, deg"); ax.set_ylabel("Aero yaw moment, kNm")
    ax.set_title("D02 Turning the stopped rotor out of the wind (cold air, worst azimuth)"); ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(OUT / "D02-yaw-out.png", dpi=160); plt.close(fig)


def main():
    blade, slm = blade_loop()
    hub = fixed_hub(slm, blade)
    dt = drivetrain(slm)
    m_b = blade["glass"]["mass_kg"]
    y = yaw(m_b, hub["mass_kg"] + hub["spinner_kg"])
    tw = tower(y["m_above_tower_flange_kg"], slm, blade_shape().solidity_area())
    res = dict(slm=slm, blade={k: ({kk: vv for kk, vv in v.items() if kk not in ("stations", "governing_by_station")} if isinstance(v, dict) and "mass_kg" in v else v)
                               for k, v in blade.items()},
               blade_stations=blade["glass"]["stations"], hub=hub, drivetrain=dt, yaw=y, tower=tw, electronics=electronics())
    (OUT / "design6.json").write_text(json.dumps(res, indent=1, default=float))
    figure_elevation(res); figure_yaw(y)
    for k in ("blade", "hub", "drivetrain", "yaw", "tower"):
        print(k, json.dumps(res[k], default=float)[:2500])
    print("slm", json.dumps(slm["ultimate_design_values_gamma_3_kN_kNm"]))


if __name__ == "__main__":
    main()
