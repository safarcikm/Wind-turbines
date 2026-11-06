"""6 kW generator G6 (doc 29): the Rev C active part run at 6 kW stall-control duty.

Run:  python3 g6.py     (~20 s) -> results/g6.json and figures G6-01..G6-05

Inputs
  * Rev C FEA and checks (doc 23): analysis/generator/results/sh30_S1x.json, rc_checks.json
  * 6 kW rotor and stall control (doc 28): analysis/turbine_6kw/results/design.json, regulation.json
  * thermal network (doc 06) with the Rev C passive cooling package (doc 23 §4a)

What it does
  1. candidates: Rev C (Ø646 x 74), Ø646 x 59 (4 magnet rows), dedicated Ø490 (doc 22 FEA) -> torque, reactance, mass
  2. electrical data at 164 rpm: EMF, current, reactance per unit, losses, efficiency, annual energy
  3. braking resistor: value, torque-speed curve, resistor-alone storm simulations, brake stops
  4. thermal at the 6 kW cases (stall duty), 10 s overload, demagnetisation, voltage, bond and brake checks
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
ROOT = HERE.parent
OUT = HERE / "results"; OUT.mkdir(exist_ok=True)
sys.argv = sys.argv[:1]
sys.path.insert(0, str(ROOT / "generator"))
sys.path.insert(0, str(ROOT / "rotor"))
sys.path.insert(0, str(ROOT / "size_tsr_map"))
sys.path.insert(0, str(ROOT.parent / "cad" / "nacelle_p1"))
sys.path.insert(0, str(ROOT.parent / "cad" / "generator_rc"))

import thermal as TH  # noqa: E402
import checks_rc as CK  # noqa: E402
import passive_cooling as PC  # noqa: E402
from bem import Blade, ROUGH, solve  # noqa: E402
import model as m27  # noqa: E402

FEA = json.loads((ROOT / "generator" / "results" / "sh30_S1x.json").read_text())
RC = json.loads((ROOT / "generator" / "results" / "rc_checks.json").read_text())
SMALL = {k: json.loads((ROOT / "generator" / "results" / f"small_{k}.json").read_text()) for k in ("P1", "D490")}
DES = json.loads((ROOT / "turbine_6kw" / "results" / "design.json").read_text())
REG = json.loads((ROOT / "turbine_6kw" / "results" / "regulation.json").read_text())

C = dict(blue="#2f6db5", orange="#d9822b", green="#3a8f5c", red="#c0392b", grey="#7f8c8d", purple="#7d5ba6")

# ------------------------------------------------------------------ machine constants (Rev C)
POLE_PAIRS = 20
L_S = 13.95e-3                    # H, synchronous inductance per phase (doc 06/12)
R_PH75 = 0.307                    # ohm per phase at 75 C (doc 12)
T12, P_CU12 = 729.0, 518.0        # 12 kW rated torque and its copper loss at 75 C (doc 23)
KT = T12 / (23.2 * 380.0 / 372.0) # Nm per A rms, effective (doc 12 current, Rev C EMF) -> 30.8
P_FE178, P_ROT178, P_STRAY12 = 218.0, 40.0, 70.0
RPM12 = 178.0
EMF_LINE = {20: FEA["line_emf_20C_V"], 60: FEA["line_emf_60C_V"], 100: FEA["line_emf_100C_V"]}
EMF_LINE[-30] = EMF_LINE[20] * (1 + 0.0012 * 50)


def ke(T_mag):
    """Phase EMF constant, V rms per rad/s mechanical."""
    return EMF_LINE[T_mag] / math.sqrt(3) / (RPM12 * math.pi / 30)


# ------------------------------------------------------------------ 6 kW duty (doc 28)
RPM6 = DES["rpm"]
OM6 = RPM6 * math.pi / 30
P_SHAFT6 = m27.SHAFT_PER_E * 6 * 1000
T6 = P_SHAFT6 / OM6                       # ≈ 397 Nm
T6_CONT, T6_10S, T6_STOP = 1.2 * T6, 1.5 * T6, 3.0 * T6
RPM_TRIP, RPM_DESIGN_OS = 1.15 * RPM6, 1.25 * RPM6
J = DES["J_rotor"] + 25.0                 # + Rev C drum, magnets, brake disc about the axis (≈ 25 kg m2)
BL = Blade(R=DES["R"], r_hub=0.40 / 3.75 * DES["R"], tsr_design=DES["tsr"], cl_design=1.0)
PF = REG["PF"]
AREA = math.pi * DES["R"] ** 2

# aero torque table of the fixed-pitch rotor
LAM_T = np.round(np.concatenate([np.arange(0.2, 1.0, 0.1), np.arange(1.0, 12.01, 0.25)]), 3)
CQ_T = np.array([solve(BL, 10.0, l * 10.0 / DES["R"], PF, 1.225, ROUGH).cq for l in LAM_T])


def q_aero(om, V, rho=1.35, stall_factor=1.0):
    lam = max(om, 0.0) * DES["R"] / V
    cq = float(np.interp(lam, LAM_T, CQ_T, left=CQ_T[0]))
    if lam < 4.0:
        cq *= stall_factor               # 3D stall: more torque in deep stall than 2D BEM
    return cq * 0.5 * rho * AREA * V ** 2 * DES["R"]


# ------------------------------------------------------------------ 1. candidates
def candidates():
    t2d_p1 = SMALL["P1"]["torque_74mm_Nm"]
    k3d = 802.0 / t2d_p1 * FEA["torque_at_sizing_current_100C_Nm"] / t2d_p1      # P1 calibration + N45SH gain
    rows = []
    for key, L, rows_n, label in (("P1", 74.0, 5, "Rev C as built for 12 kW (Ø646 × 74)"),
                                  ("P1", 59.0, 4, "Ø646, 4 magnet rows (stack 59)"),
                                  ("D490", 105.0, 7, "Dedicated Ø490, 7 rows (stack 105)"),
                                  ("D490", 120.0, 8, "Dedicated Ø490, 8 rows (stack 120)")):
        s = SMALL[key]
        t_cap = s["torque_74mm_Nm"] * L / 74.0 * k3d * (1.0 if key == "P1" else 1.0)
        x_sizing = 1.0 / s["NI_sc_over_NI_rated"]           # pu at the sizing current density
        x_pu = x_sizing * T6 * 1.1 / t_cap                   # pu at the 6 kW rating (sizing = 1.1 x rated)
        # end-winding leakage grows in relative terms for a short stack (doc 06: ~15 % of L at 74 mm)
        x_pu *= (1 + 0.15 * (74.0 / L - 1))
        if key == "P1":
            m_rot = 161.0 - 12.5 - (91.8 + 8.2) * (1 - (L + 120) / 194)          # no fins/ribs at 6 kW
            m_st = 115.0 - (48.0 + 24 * 0.6) * (1 - L / 74)
            mag = 8.21 * rows_n / 5
        else:
            sc = 490 / 646
            m_rot = (91.8 * sc * (L + 120) / 194 + 10 * sc ** 2 + 34.5 * sc ** 2 + 2) + 41e-3 * 32 * rows_n
            m_st = 40.6 * sc * 1.15 + 71.5 * L / 154.8 + 20.5 * L / 154.8 * 1.25 + 2
            mag = 41e-3 * 32 * rows_n
        rows.append(dict(label=label, key=key, stack_mm=L, magnet_rows=rows_n, torque_capability_Nm=round(t_cap),
                         x_pu_at_6kW=round(x_pu, 2), resistor_torque_pu=round(1 / (2 * x_pu), 2),
                         magnet_kg=round(mag, 1), mass_kg=round(m_rot + m_st),
                         new_tooling={"P1": "none" if L == 74 else "coil former, drum length, sleeve mould length",
                                      "D490": "lamination die, coil former, drum, sleeve mandrel, all jigs"}[key]))
    return rows


# ------------------------------------------------------------------ 2. electrical data and losses
def gen_losses(T, rpm, T_cu=75.0):
    I = abs(T) / KT
    p_cu = 3 * I ** 2 * R_PH75 * (1 + 0.00393 * (T_cu - 75))
    x = rpm / RPM12
    p_fe = P_FE178 * x ** 1.6
    p_rot = P_ROT178 * x ** 2 * (T / T12) ** 2 + 5.0 * x ** 2
    p_stray = P_STRAY12 * (T / T12) ** 2
    return dict(I=I, cu=p_cu, fe=p_fe, rot=p_rot, stray=p_stray, total=p_cu + p_fe + p_rot + p_stray)


def electrical():
    out = {}
    w_e = POLE_PAIRS * OM6
    X = w_e * L_S
    for Tm in (-30, 20, 60, 100):
        E = ke(Tm) * OM6
        I = T6 / KT * (EMF_LINE[100] / EMF_LINE[Tm])
        out[f"{Tm}C"] = dict(line_emf_164rpm_V=round(E * math.sqrt(3), 1), current_rated_A=round(I, 2),
                             x_pu=round(X * I / E, 3), resistor_peak_torque_pu=round(3 * ke(Tm) ** 2 / (2 * POLE_PAIRS * L_S) / T6, 2))
    l = gen_losses(T6, RPM6)
    eff = 1 - l["total"] / P_SHAFT6
    return dict(rated_torque_Nm=round(T6, 1), rpm=round(RPM6, 1), f_el_Hz=round(POLE_PAIRS * RPM6 / 60, 2),
                X_ohm=round(X, 2), R_ohm_75C=R_PH75, by_magnet_T=out,
                losses_rated_W={k: round(v, 1) for k, v in l.items()}, eff_rated_pct=round(100 * eff, 2),
                torque_10s_Nm=round(T6_10S), current_10s_A=round(T6_10S / KT, 1),
                rev_c_12kW_current_A=round(T12 / KT, 1))


def energy():
    """Net yearly energy with the G6 generator in the doc 27/28 chain (converter and auxiliaries unchanged)."""
    s = 0.5
    curves = {}
    for name, key in (("stall", "stall_curve"), ("stall_cold", "stall_curve_cold")):
        rows = REG[key]
        V = np.array([r["V"] for r in rows]); out = []
        for r in rows:
            P, rpm = r["P"], max(r["rpm"], 1)
            if P <= 0:
                out.append(0.0); continue
            T = P / (rpm * math.pi / 30)
            p_gen = P - gen_losses(T, rpm)["total"]
            Pn = 13e3 * s
            conv = lambda P_, p0, k1, k2: p0 * s ** 0.5 + k1 * P_ + k2 * Pn * (P_ / Pn) ** 2
            p_dc = p_gen - conv(p_gen, 25, 0.004, 0.006)
            p_ac = p_dc - conv(p_dc, 30, 0.005, 0.008)
            out.append(max(p_ac - 120 * s ** 0.3, 0.0))
        curves[name] = (V, np.array(out))
    aep = {}
    V, Pn = curves["stall"]
    for sc in m27.SCENARIOS:
        c = sc["v"] / math.gamma(1 + 1 / sc["k"])
        f = (sc["k"] / c) * (V / c) ** (sc["k"] - 1) * np.exp(-(V / c) ** sc["k"])
        aep[sc["key"]] = round(float(np.sum(Pn * f) * 0.5 * 8760 * 0.97 / 1000))
    doc28 = {k: round(v) for k, v in REG["aep"]["stall"].items()}
    return dict(aep_kWh=aep, doc28_kWh=doc28,
                change_pct={k: round(100 * (aep[k] / doc28[k] - 1), 1) for k in aep},
                net_rated_W=round(float(Pn.max())), curve=[(float(v), round(float(p))) for v, p in zip(V, Pn)])


# ------------------------------------------------------------------ 3. braking resistor
def t_res(om, R_ext, T_mag=100):
    """Torque from the generator into a star resistor bank R_ext per phase (copper loss included)."""
    if om <= 0:
        return 0.0
    E = ke(T_mag) * om
    X = POLE_PAIRS * om * L_S
    Rt = R_ext + R_PH75 * 1.2
    I = E / math.hypot(Rt, X)
    return 3 * I * I * Rt / om


def simulate(V, R_ext, brake_Nm=0.0, brake_delay=0.0, gust=1.3, stall_factor=1.0, T_mag=100, t_end=20.0, om0=None):
    """Converter lost at t = 0 while a gust takes the wind from V to gust*V; contactor closes after 50 ms.
    Returns max speed, final speed, energy into the resistor."""
    st = [r for r in REG["stall_curve_cold"] if abs(r["V"] - V) < 1e-6]
    om = om0 if om0 is not None else (st[0]["rpm"] if st else RPM6) * math.pi / 30
    dt, t, om_max, E_res, P_res_max, trace = 0.005, 0.0, om, 0.0, 0.0, []
    while t < t_end:
        Vt = V * (1 + (gust - 1) * min(t / 1.0, 1.0))           # gust rises over 1 s and stays
        qa = q_aero(om, Vt, stall_factor=stall_factor)
        qr = t_res(om, R_ext, T_mag) if t >= 0.05 else 0.0
        qb = brake_Nm * min(max((t - brake_delay) / 0.3, 0), 1) if brake_Nm else 0.0
        qb = qb if om > 0.01 else min(qb, qa - qr) if qa > qr else 0.0
        om = max(om + (qa - qr - qb) / J * dt, 0.0)
        p_r = qr * om * R_ext / (R_ext + R_PH75 * 1.2)
        E_res += p_r * dt; P_res_max = max(P_res_max, p_r)
        om_max = max(om_max, om)
        if int(t / dt) % 20 == 0:
            trace.append((round(t, 2), round(om * 30 / math.pi, 1), round(Vt, 1)))
        t += dt
    return dict(rpm_max=om_max * 30 / math.pi, rpm_end=om * 30 / math.pi, E_res_kJ=E_res / 1000,
                P_res_max_kW=P_res_max / 1000, trace=trace)


def resistor_design():
    # sweep the resistor value: highest mean wind at which the resistor alone keeps the rotor under the trip speed
    winds = np.arange(10.0, 30.01, 1.0)

    def holds_to(R_ext, **kw):
        last = 0.0
        for V in winds:
            if simulate(V, R_ext, **kw)["rpm_max"] > RPM_DESIGN_OS:
                break
            last = float(V)
        return last

    sweep = []
    for R_ext in (2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0):
        sweep.append(dict(R_ext=R_ext, peak_torque_speed_rpm=round((R_ext + R_PH75 * 1.2) / (POLE_PAIRS * L_S) * 30 / math.pi),
                          torque_at_164rpm_pu=round(t_res(OM6, R_ext) / T6, 2),
                          holds_to_V_bem_100C=holds_to(R_ext),
                          holds_to_V_3d_100C=holds_to(R_ext, stall_factor=1.5),
                          holds_to_V_3d_20C=holds_to(R_ext, stall_factor=1.5, T_mag=20)))
    best = max(sweep, key=lambda s: (s["holds_to_V_bem_100C"], s["holds_to_V_3d_20C"], s["holds_to_V_3d_100C"], -abs(s["R_ext"] - 4)))
    R_ext = best["R_ext"]
    cases = {}
    for name, kw in (("25ms_resistor_only", dict(V=25.0)),
                     ("25ms_resistor_only_3d", dict(V=25.0, stall_factor=1.5)),
                     ("25ms_resistor_only_3d_20C", dict(V=25.0, stall_factor=1.5, T_mag=20)),
                     ("30ms_resistor_only", dict(V=30.0)),
                     ("20ms_resistor_only_cold_magnets", dict(V=20.0, T_mag=20)),
                     ("25ms_brake_only_1p5kNm", dict(V=25.0, brake_Nm=1500.0, brake_delay=0.2)),
                     ("25ms_brake_only_1p5kNm_3d", dict(V=25.0, brake_Nm=1500.0, brake_delay=0.2, stall_factor=1.5)),
                     ("30ms_brake_only_1p5kNm_3d", dict(V=30.0, brake_Nm=1500.0, brake_delay=0.2, stall_factor=1.5)),
                     ("25ms_both", dict(V=25.0, brake_Nm=1500.0, brake_delay=0.2))):
        V = kw.pop("V")
        if "brake_Nm" in kw:
            r = simulate(V, 1e6 if "brake_only" in name else R_ext, **kw)
        else:
            r = simulate(V, R_ext, **kw)
        r["stopped"] = r["rpm_end"] < 1.0
        cases[name] = {k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()}
    # resistor rating: hold at 25 m/s mean for 60 s before the brake (worst normal sequence), and a 10 s stop
    hold = simulate(25.0, R_ext, gust=1.0, t_end=60.0)
    return dict(sweep=sweep, R_ext_ohm=R_ext, cases=cases,
                rating=dict(continuous_kW=round(hold["E_res_kJ"] / 60, 1), energy_60s_kJ=round(hold["E_res_kJ"]),
                            peak_kW=round(max(v["P_res_max_kW"] for k, v in cases.items() if "brake_only" not in k), 1),
                            current_peak_A=round(ke(-30) * RPM_DESIGN_OS * math.pi / 30 / math.hypot(R_ext + R_PH75, POLE_PAIRS * RPM_DESIGN_OS * math.pi / 30 * L_S), 1)))


# ------------------------------------------------------------------ 4. thermal, demag, voltage, mechanical
def thermal():
    CK.thermal()
    A_in, A_out = PC.inner_area0(), PC.outer_area0()
    f_in = 1 + PC.inner_fins()["add"] / A_in + 0.07
    f_out = 1 + PC.outer_ribs()["add"] / A_out
    cfg_full = dict(support_R=0.33, h_int_run=40, fin_in=f_in, fin_out=f_out)
    cfg_none = dict(support_R=0.33, h_int_run=15, fin_in=1.0, fin_out=1.0)
    TH.P_CU_75 = P_CU12
    cases = {
        "6kW_rated_hot_day_10ms": dict(T=T6, rpm=160, V=10.0, T_amb=30, induction=0.3),
        "6kW_rated_hot_weak_wake": dict(T=T6, rpm=160, V=10.0, T_amb=30, induction=0.6),
        "1.2x_continuous_hot_weak_wake": dict(T=T6_CONT, rpm=150, V=10.0, T_amb=30, induction=0.6),
        "stall_25ms_cold_air_10C": dict(T=466.0, rpm=139, V=25.0, T_amb=10, induction=0.1),
        "12kW_reference_hot_rated": dict(T=T12, rpm=178, V=10.5, T_amb=30, induction=0.3),
    }
    out = {}
    for cn, cfg in (("RevC_passive_package", cfg_full), ("no_fins_no_blades", cfg_none)):
        row = {}
        for k, c in cases.items():
            TH.P_FE = P_FE178 * (c["rpm"] / RPM12) ** 1.6
            r = TH.solve_case(T_amb=c["T_amb"], V_wind=c["V"], load=c["T"] / T12, solar_W=100, induction=c["induction"],
                              rpm=c["rpm"], **cfg)
            row[k] = dict(hotspot=r["T_hotspot"], magnets=r["T_rotor_magnets"], P_cu=r["P_cu"])
        out[cn] = row
    TH.P_FE = P_FE178
    # 10 s at 1.5 x from the continuous 1.2 x temperature: adiabatic copper
    m_cu = 20.2
    p10 = gen_losses(T6_10S, 150, T_cu=out["RevC_passive_package"]["1.2x_continuous_hot_weak_wake"]["hotspot"])["cu"]
    out["overload_10s_1.5x"] = dict(P_cu_W=round(p10), rise_K=round(p10 * 10 / (m_cu * 385), 2))
    return out


def demag():
    tab = FEA["demag_margin_pct"]
    i_res_pk = ke(100) * OM6 / math.hypot(4.0 + R_PH75, POLE_PAIRS * OM6 * L_S) * math.sqrt(2)
    return dict(rule="transient SC margin >= 20 % at 100 C (doc 23)", table_100C=tab["100C"],
                sc_peak_current_A=tab["100C"]["I_sc_A_peak"],
                current_10s_peak_A=round(T6_10S / KT * math.sqrt(2), 1),
                resistor_braking_peak_A=round(i_res_pk, 1),
                note="10 s current below the 12 kW rated-load current; resistor braking current below the steady short-circuit current")


def voltage():
    pk = lambda rpm: EMF_LINE[-30] * rpm / RPM12 * math.sqrt(2)
    rpm_bus = 750.0 / (EMF_LINE[-30] / RPM12 * math.sqrt(2))
    return dict(line_peak_V={"164rpm_-30C": round(pk(RPM6)), "trip_189rpm_-30C": round(pk(RPM_TRIP)),
                             "design_205rpm_-30C": round(pk(RPM_DESIGN_OS)), "250rpm_-30C_RevC": round(pk(250))},
                rpm_where_diodes_charge_750V_bus=round(rpm_bus), limit_V=1200,
                rpm_at_1200V=round(1200 / (EMF_LINE[-30] / RPM12 * math.sqrt(2))))


def mechanical():
    m = RC["mechanical"]
    k = T6_STOP / 802.0
    return dict(bond_shear_at_3x_6kW_kPa=round(m["bond_shear_rated_kPa"] * k, 1), bond_allow_MPa=5.0,
                torque_vs_RevC_rated=round(T6_STOP / 802.0, 2),
                brake=dict(required_Nm=round(T6_STOP), chosen_Nm=1500,
                           disc="Rev C disc NP1 (34.5 kg) kept, one caliper with a lighter spring pack instead of two",
                           max_decel_rad_s2=round(1500 / J, 1), stop_from_trip_speed_no_wind_s=round(RPM_TRIP * math.pi / 30 / (1500 / J), 2)),
                drum_stability=m["drum_stability_margin_ends_round"], ump_kN_per_mm=m["ump_kN_per_mm"])


# ------------------------------------------------------------------ figures
def figures(res):
    plt.rcParams.update({"font.size": 9, "axes.grid": True, "grid.alpha": 0.3})
    # G6-01 efficiency and losses
    V = [c[0] for c in res["energy"]["curve"]]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.4))
    rows = REG["stall_curve"]
    Ts = [r["P"] / max(r["rpm"] * math.pi / 30, 1e-3) for r in rows]
    L = [gen_losses(T, max(r["rpm"], 1)) for T, r in zip(Ts, rows)]
    eff = [100 * (1 - l["total"] / r["P"]) if r["P"] > 300 else np.nan for l, r in zip(L, rows)]
    a1.plot([r["V"] for r in rows], eff, color=C["blue"]); a1.set_ylim(80, 100)
    a1.set_xlabel("Wind, m/s"); a1.set_ylabel("Generator efficiency, %"); a1.set_title("Efficiency along the 6 kW operating line")
    for k, col in (("cu", C["orange"]), ("fe", C["blue"]), ("rot", C["grey"]), ("stray", C["purple"])):
        a2.plot([r["V"] for r in rows], [l[k] for l in L], color=col, label={"cu": "copper", "fe": "iron", "rot": "rotor", "stray": "stray"}[k])
    a2.set_xlabel("Wind, m/s"); a2.set_ylabel("Loss, W"); a2.legend(frameon=False); a2.set_title("Losses")
    fig.suptitle("G6-01 Rev C active part at 6 kW duty"); fig.tight_layout(); fig.savefig(OUT / "G6-01-efficiency.png", dpi=160); plt.close(fig)

    # G6-02 resistor torque vs speed against aero torque
    R_ext = res["resistor"]["R_ext_ohm"]
    rpm = np.linspace(1, 230, 200); om = rpm * math.pi / 30
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    for Tm, ls in ((100, "-"), (20, "--")):
        ax.plot(rpm, [t_res(o, R_ext, Tm) for o in om], color=C["green"], ls=ls, lw=2, label=f"Braking resistor {R_ext:g} Ω, magnets {Tm} °C")
    for V, col in ((15, C["blue"]), (25, C["orange"]), (32.5, C["red"])):
        ax.plot(rpm, [q_aero(o, V) for o in om], color=col, label=f"Aero torque, {V:g} m/s, cold air")
        ax.plot(rpm, [q_aero(o, V, stall_factor=1.5) for o in om], color=col, ls=":", lw=1)
    ax.axvline(RPM6, color=C["grey"], lw=1); ax.text(RPM6 + 1, 50, "164 rpm", fontsize=7)
    ax.axvline(RPM_DESIGN_OS, color=C["grey"], lw=1, ls="--"); ax.text(RPM_DESIGN_OS + 1, 50, "205 rpm design", fontsize=7)
    ax.set_xlabel("Rotor speed, rpm"); ax.set_ylabel("Torque, Nm"); ax.set_xlim(0, 230)
    ax.set_title("G6-02 Braking resistor against the stalled rotor (dotted: +50 % deep-stall torque)")
    ax.legend(frameon=False, fontsize=7, loc="upper left"); fig.tight_layout(); fig.savefig(OUT / "G6-02-resistor-torque.png", dpi=160); plt.close(fig)

    # G6-03 simulations
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    for name, col, lab in (("25ms_resistor_only", C["green"], "25 m/s + 30 % gust, resistor only"),
                           ("25ms_resistor_only_3d", C["red"], "same, +50 % deep-stall torque, magnets 100 °C"),
                           ("25ms_resistor_only_3d_20C", C["purple"], "same, +50 % deep-stall torque, magnets 20 °C"),
                           ("30ms_resistor_only", C["orange"], "30 m/s + 30 % gust, resistor only"),
                           ("25ms_brake_only_1p5kNm", C["blue"], "25 m/s + gust, brake only 1.5 kNm"),
                           ("25ms_brake_only_1p5kNm_3d", C["purple"], "25 m/s + gust, brake only, +50 % stall torque"),
                           ("30ms_brake_only_1p5kNm_3d", C["orange"], "30 m/s + gust, brake only, +50 % stall torque")):
        tr = res["resistor"]["cases"][name]["trace"]
        ax.plot([p[0] for p in tr], [p[1] for p in tr], color=col, ls=":" if "3d" in name and "brake" not in name else ("--" if "brake" in name else "-"), label=lab)
    ax.axhline(RPM_DESIGN_OS, color=C["grey"], ls="--", lw=1)
    ax.set_xlabel("Time after converter loss, s"); ax.set_ylabel("Rotor speed, rpm"); ax.set_xlim(0, 12); ax.set_ylim(0, 260)
    ax.set_title("G6-03 Each stopping system alone, cold air 1.35 kg/m³ (magnets 100 °C unless noted)"); ax.legend(frameon=False, fontsize=7)
    fig.tight_layout(); fig.savefig(OUT / "G6-03-stop-simulations.png", dpi=160); plt.close(fig)

    # G6-04 safety chain one-line diagram
    fig, ax = plt.subplots(figsize=(8.5, 3.2)); ax.axis("off")
    box = lambda x, y, w, h, t, fc: (ax.add_patch(plt.Rectangle((x, y), w, h, fc=fc, ec="k", lw=1)),
                                     ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=7.5))
    box(0.2, 1.2, 1.6, 1.0, "G6 generator\nRev C active part\n3 ph, 343 V @ 164 rpm", "#e8f0fa")
    box(2.6, 1.9, 1.7, 0.9, "Active rectifier\n(normal control,\n1.5x torque 10 s)", "#eef7ee")
    box(4.9, 1.9, 1.5, 0.9, "750 V DC bus\n+ dump chopper\n12 kW (heater)", "#eef7ee")
    box(6.9, 1.9, 1.5, 0.9, "AC / heating /\n48 V battery\nmodules", "#eef7ee")
    box(2.6, 0.2, 1.7, 0.9, f"K1 normally-closed\ncontactor (held open\nby safety relay)", "#fdecea")
    box(4.9, 0.2, 1.5, 0.9, f"Braking resistor\n3 x {R_ext:g} Ω star\n(stainless, IP54)", "#fdecea")
    box(6.9, 0.2, 1.5, 0.9, "Spring disc brake\n1.5 kNm, 1 caliper\n(released by power)", "#fdecea")
    for x0, y0, x1, y1 in ((1.8, 2.0, 2.6, 2.35), (4.3, 2.35, 4.9, 2.35), (6.4, 2.35, 6.9, 2.35), (1.8, 1.4, 2.6, 0.65), (4.3, 0.65, 4.9, 0.65)):
        ax.annotate("", (x1, y1), (x0, y0), arrowprops=dict(arrowstyle="-|>", lw=1))
    ax.text(5.6, 1.45, "Safety relay (PL d): overspeed 189 rpm, converter fault, loss of 24 V → K1 closes AND brake drops",
            ha="center", fontsize=7.5, color=C["red"])
    ax.set_xlim(0, 8.6); ax.set_ylim(0, 3)
    ax.set_title("G6-04 Power and stopping chain (both red paths work with no power and no controller)", fontsize=9)
    fig.tight_layout(); fig.savefig(OUT / "G6-04-safety-chain.png", dpi=160); plt.close(fig)


def main():
    res = dict(duty=dict(rated_Nm=round(T6, 1), continuous_Nm=round(T6_CONT), ten_s_Nm=round(T6_10S), stop_Nm=round(T6_STOP),
                         rpm=round(RPM6, 1), trip_rpm=round(RPM_TRIP), design_overspeed_rpm=round(RPM_DESIGN_OS), J_kgm2=round(J, 1)))
    res["candidates"] = candidates()
    res["electrical"] = electrical()
    res["energy"] = energy()
    res["resistor"] = resistor_design()
    res["thermal"] = thermal()
    res["demag"] = demag()
    res["voltage"] = voltage()
    res["mechanical"] = mechanical()
    for k, v in res.items():
        if k == "energy":
            print(k, {kk: vv for kk, vv in v.items() if kk != "curve"})
        elif k == "resistor":
            print("resistor sweep", json.dumps(v["sweep"]))
            print("R", v["R_ext_ohm"], json.dumps({kk: {q: w for q, w in vv.items() if q != "trace"} for kk, vv in v["cases"].items()}))
            print("rating", v["rating"])
        else:
            print(k, json.dumps(v))
    (OUT / "g6.json").write_text(json.dumps(res, indent=1, default=float))
    figures(res)


if __name__ == "__main__":
    main()
