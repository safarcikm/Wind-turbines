"""Power electronics concept sizing for the 12 kW turbine.

Run:  python3 sizing.py     (seconds; writes results/power_summary.json and plots)

Inputs from the generator (docs 05/06, analysis/generator/results/iter2):
  line EMF 379 V rms at 178 rpm (hot magnets), 580 V rms at 250 rpm (cold magnets)
  synchronous inductance 13.95 mH, phase resistance from 496 W copper loss at 23.2 A
  20 pole pairs (40 poles)
and from the rotor and control (docs 03, 11): speed range 40-178 rpm, 13.6 kW shaft,
design overspeed 250 rpm, emergency stop braking 1.25 x rated torque.

Computes the generator terminal envelope with an active rectifier, the DC link window,
device and filter ratings, the dump load, an efficiency chain and annual energy.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
OUT = HERE / "results"
OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(HERE.parent / "rotor"))
import study  # noqa: E402
from bem import Blade, CLEAN  # noqa: E402

# generator
POLE_PAIRS = 20
E_LINE_RATED_HOT = 378.7          # V rms at 178 rpm, magnets hot
E_LINE_250_COLD_PEAK = 820.6 * 250 / 230
K_COLD = 580.3 / 230 / (378.7 / 178)   # cold/hot EMF ratio
LS = 13.95e-3
I_RATED = 23.2
R_PH = 496 / (3 * I_RATED ** 2)
GEN_LOSS_RATED = 825.0            # W at rated (doc 06)
RPM_RATED, RPM_MIN, RPM_OS = 178.0, 40.0, 250.0
P_SHAFT = 13_600.0
J_ROTOR = 216.0

# power electronics
V_DC_NOM, V_DC_CHOP, V_DC_MAX_DEVICE = 750.0, 820.0, 1200.0
F_SW = 16e3
GRID_V_LINE = 400.0


def e_line(rpm, cold=False):
    k = E_LINE_RATED_HOT / RPM_RATED * (K_COLD if cold else 1.0)
    return k * rpm


def terminal(rpm, torque, cold=False):
    """Active rectifier with id = 0 (surface magnets): phase terminal voltage and current."""
    w_e = POLE_PAIRS * rpm * 2 * math.pi / 60
    E_ph = e_line(rpm, cold) / math.sqrt(3)
    w_m = rpm * 2 * math.pi / 60
    I = torque * w_m / (3 * E_ph) if E_ph > 0 else 0.0     # q-axis current in phase with EMF
    V_d = -w_e * LS * I                                      # generator convention
    V_q = E_ph - R_PH * I
    V_ph = math.hypot(V_d, V_q)
    return dict(rpm=rpm, f_el=w_e / (2 * math.pi), E_line=e_line(rpm, cold), I=I, V_line=V_ph * math.sqrt(3),
                V_line_peak=V_ph * math.sqrt(6), Vdc_min=V_ph * math.sqrt(6) * 1.10)   # SVPWM + 10 % margin


def efficiency_chain(P_shaft, rpm):
    """Loss model: generator (scaled from doc 06), active rectifier and inverter (SiC, typical)."""
    I = P_shaft / (3 * e_line(rpm) / math.sqrt(3)) if rpm > 0 else 0
    p_cu = 3 * I ** 2 * R_PH
    p_fe = 219 * (rpm / RPM_RATED) ** 1.6 + 40 * (rpm / RPM_RATED) ** 2 + 70 * (P_shaft / P_SHAFT) ** 2
    P_gen = P_shaft - p_cu - p_fe
    # converter: fixed + linear (switching, diode) + quadratic (conduction, filter)
    def conv(P, p0, k1, k2, Pn=13e3):
        return p0 + k1 * P + k2 * Pn * (P / Pn) ** 2
    P_dc = P_gen - conv(P_gen, 25, 0.004, 0.006)
    P_ac = P_dc - conv(P_dc, 30, 0.005, 0.008)
    P_aux = 120.0
    return dict(P_gen=P_gen, P_dc=P_dc, P_ac=P_ac, P_net=P_ac - P_aux, I=I,
                eta_gen=P_gen / P_shaft, eta_rect=P_dc / P_gen, eta_inv=P_ac / P_dc)


def main():
    res = {}
    # 1. envelope over the speed range on the optimal torque curve and at rated/overspeed
    rows = []
    blade = Blade(R=3.75, tsr_design=study.TSR_DESIGN, cl_design=study.CL_DESIGN)
    k_opt = 2.489
    for rpm in np.linspace(RPM_MIN, RPM_RATED, 15):
        om = rpm * 2 * math.pi / 60
        rows.append(terminal(rpm, k_opt * om ** 2))
    rows.append(terminal(RPM_RATED, P_SHAFT / (RPM_RATED * 2 * math.pi / 60)))
    rated = rows[-1]
    estop = terminal(231.6, 1.25 * P_SHAFT / (RPM_RATED * 2 * math.pi / 60))
    res["envelope"] = dict(
        rated=dict((k, round(v, 1)) for k, v in rated.items()),
        min_speed=dict((k, round(v, 1)) for k, v in rows[0].items()),
        estop_braking_at_232rpm=dict((k, round(v, 1)) for k, v in estop.items()),
        open_circuit_250rpm_cold_peak_V=round(E_LINE_250_COLD_PEAK, 0),
        phase_resistance_ohm=round(R_PH, 3), inductance_mH=LS * 1e3,
        reactance_rated_ohm=round(rated["f_el"] * 2 * math.pi * LS, 2),
    )
    # DC link window
    vdc_grid = GRID_V_LINE * 1.10 * math.sqrt(2) * 1.10       # grid +10 %, SVPWM, 10 % control margin
    res["dc_link"] = dict(
        needed_by_generator_at_rated_V=round(rated["Vdc_min"], 0),
        needed_by_generator_at_estop_V=round(estop["Vdc_min"], 0),
        needed_by_400V_grid_inverter_V=round(vdc_grid, 0),
        nominal_V=V_DC_NOM, chopper_on_V=V_DC_CHOP,
        uncontrolled_rectification_250rpm_cold_V=round(E_LINE_250_COLD_PEAK, 0),
        device_class_V=V_DC_MAX_DEVICE,
        device_margin_at_worst_pct=round(100 * (1 - E_LINE_250_COLD_PEAK / V_DC_MAX_DEVICE), 0),
    )
    # 2. ratings
    I_max = max(estop["I"], rated["I"] * 1.25)
    res["ratings"] = dict(
        generator_side_current_continuous_A_rms=round(rated["I"], 1),
        generator_side_current_max_A_rms=round(I_max, 1),
        recommended_module="1200 V SiC MOSFET six-pack, >= 60 A (2 x margin on peak current for cold start and faults)",
        switching_frequency_kHz=F_SW / 1e3,
        grid_current_400V_A_rms=round(12_000 / (math.sqrt(3) * 400), 1),
        grid_current_230V_1ph_A_rms=round(12_000 / 230, 1),
        battery_current_48V_A=round(12_000 / 48, 0),
    )
    # 3. dump load
    Ek_232 = 0.5 * J_ROTOR * (231.6 * 2 * math.pi / 60) ** 2
    # aerodynamic energy while feathering at 30 deg/s from full power: about 1.5 s of rated power decaying linearly
    E_aero_estop = P_SHAFT * 1.25 * 1.5 / 2
    # normal stop on grid loss: pitch at 8 deg/s, about 6 s of decaying rated power
    E_normal_stop = P_SHAFT * 6 / 2
    P_dump = 1.5 * P_SHAFT
    res["dump_load"] = dict(
        rating_continuous_kW=round(P_dump / 1e3, 1),
        resistance_ohm=round(V_DC_CHOP ** 2 / P_dump, 1),
        energy_emergency_stop_kJ=round((Ek_232 + E_aero_estop) / 1e3, 0),
        energy_normal_stop_grid_loss_kJ=round((E_normal_stop + 0.5 * J_ROTOR * (RPM_RATED * 2 * math.pi / 60) ** 2) / 1e3, 0),
        note="rated continuous so it never limits a stop; hardware-triggered by DC link voltage, independent of the controller",
    )
    # 4. efficiency chain and annual energy
    curve = []
    for V in study.VS:
        res_, om, p = study.best_point(blade, V, study.TIP_SPEED_MAX / blade.R, CLEAN)
        P = min(res_.power, P_SHAFT)
        if V > study.V_STORM_START:
            P = P_SHAFT * (1 - (1 - study.STORM_FRAC) * (V - study.V_STORM_START) / (study.V_CUTOUT - study.V_STORM_START))
        if V > study.V_CUTOUT:
            P = 0.0
        rpm = min(om * 60 / (2 * math.pi), RPM_RATED)
        e = efficiency_chain(P, rpm) if P > 0 and rpm >= RPM_MIN * 0.9 else dict(P_net=0.0, eta_gen=0, eta_rect=0, eta_inv=0)
        curve.append(dict(V=float(V), P_shaft=P, rpm=rpm, P_net=max(e["P_net"], 0.0), eta_gen=e["eta_gen"],
                          eta_rect=e["eta_rect"], eta_inv=e["eta_inv"]))
    r_ = efficiency_chain(P_SHAFT, RPM_RATED)
    res["efficiency_rated"] = dict(generator=round(r_["eta_gen"], 4), rectifier=round(r_["eta_rect"], 4),
                                   inverter=round(r_["eta_inv"], 4),
                                   front_end_plus_grid_module=round(r_["eta_rect"] * r_["eta_inv"], 4),
                                   net_output_kW=round(r_["P_net"] / 1e3, 2))
    V = np.array([c["V"] for c in curve]); Pn = np.array([c["P_net"] for c in curve])
    aep = {}
    for va in (5.0, 6.0, 7.0, 8.0, 10.0):
        k, c = 2.0, va / math.gamma(1.5)
        f = (k / c) * (V / c) ** (k - 1) * np.exp(-(V / c) ** k)
        aep[str(va)] = round(float(np.sum(Pn * f * (V[1] - V[0])) * 8760 * 0.97 / 1000))
    res["aep_kWh_net_by_vave"] = aep
    res["rated_wind_for_12kW_net"] = float(next(c["V"] for c in curve if c["P_net"] >= 11_999)) if any(c["P_net"] >= 11_999 for c in curve) else None
    (OUT / "power_summary.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))

    fig, ax = plt.subplots(1, 2, figsize=(11, 4.5))
    rr = [r["rpm"] for r in rows[:-1]]
    ax[0].plot(rr, [r["E_line"] * math.sqrt(2) for r in rows[:-1]], label="EMF line peak (hot)")
    ax[0].plot(rr, [r["V_line_peak"] for r in rows[:-1]], label="terminal line peak, optimal torque")
    ax[0].plot(rr, [e_line(x, cold=True) * math.sqrt(2) for x in rr], "--", label="EMF line peak (−40 °C magnets)")
    xs = np.linspace(RPM_RATED, RPM_OS, 10)
    ax[0].plot(xs, [e_line(x, cold=True) * math.sqrt(2) for x in xs], "r--", label="open circuit overspeed, cold")
    ax[0].axhline(V_DC_NOM, color="k", lw=1, label="DC link 750 V")
    ax[0].axhline(V_DC_CHOP, color="k", ls=":", lw=1, label="dump load on 820 V")
    ax[0].axhline(V_DC_MAX_DEVICE, color="r", lw=1, label="1200 V device class")
    ax[0].set_xlabel("Rotor speed [rpm]"); ax[0].set_ylabel("Voltage [V]"); ax[0].legend(fontsize=7); ax[0].grid(alpha=0.3)
    ax[1].plot(V, [c["P_shaft"] / 1e3 for c in curve], label="shaft power")
    ax[1].plot(V, Pn / 1e3, label="net electrical output")
    ax[1].set_xlabel("Wind speed [m/s]"); ax[1].set_ylabel("Power [kW]"); ax[1].legend(); ax[1].grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(OUT / "power_envelope.png", dpi=110)


if __name__ == "__main__":
    main()
