"""V5 power electronics check and net annual energy with the full efficiency chain (doc 26 §8-9).

Run:  python3 power_v5.py   -> results/power_v5.json   (~1 min)

Reuses analysis/power/sizing.py (terminal voltage, active rectifier, loss chain) with the V5
generator data from generator_v5.py, and the doc 03 BEM operating points for both rotors.
Net energy = after generator, rectifier, inverter and 120 W auxiliaries, 97 % availability,
Rayleigh winds, rough (weathered) and clean blades.
"""
from __future__ import annotations
import json, math
import numpy as np
import common as C
import sizing as S
import study
from bem import Blade, CLEAN, ROUGH

GEN = json.loads((C.OUT / "generator_v5.json").read_text())
BASE = {k: getattr(S, k) for k in ("E_LINE_RATED_HOT", "E_LINE_250_COLD_PEAK", "LS", "R_PH", "RPM_RATED", "RPM_MIN", "RPM_OS", "J_ROTOR")}
K_L = 120 / 74


def configure(v5):
    for k, v in BASE.items():
        setattr(S, k, v)
    if v5:
        S.E_LINE_RATED_HOT = BASE["E_LINE_RATED_HOT"] * K_L * C.RPM / 178
        S.E_LINE_250_COLD_PEAK = BASE["E_LINE_250_COLD_PEAK"]           # same V/rpm ratio up to the design overspeed
        S.LS = BASE["LS"] * (0.62 * K_L + 0.38)                          # slot part grows with the stack, end part does not
        S.R_PH = BASE["R_PH"] * GEN["losses_W"]["k_cu"]
        S.RPM_RATED, S.RPM_MIN, S.RPM_OS = C.RPM, C.RPM_MIN, C.RPM_MAX
        S.J_ROTOR = 480.0
    fe0 = 185.0 if v5 else 219.0
    rot0 = 25.0 if v5 else 40.0

    def chain(P_shaft, rpm):
        I = P_shaft / (3 * S.e_line(rpm) / math.sqrt(3)) if rpm > 0 else 0
        p_cu = 3 * I ** 2 * S.R_PH
        p_fe = fe0 * (rpm / S.RPM_RATED) ** 1.6 + rot0 * (rpm / S.RPM_RATED) ** 2 + 70 * (P_shaft / S.P_SHAFT) ** 2
        P_gen = P_shaft - p_cu - p_fe
        conv = lambda P, p0, k1, k2, Pn=13e3: p0 + k1 * P + k2 * Pn * (P / Pn) ** 2
        P_dc = P_gen - conv(P_gen, 25, 0.004, 0.006)
        P_ac = P_dc - conv(P_dc, 30, 0.005, 0.008)
        return dict(P_net=P_ac - 120.0, eta_gen=P_gen / P_shaft, eta_rect=P_dc / P_gen, eta_inv=P_ac / P_dc)
    return chain


def curve(v5, polar):
    chain = configure(v5)
    R, tsr, cap = (C.R, C.TSR, C.RPM * math.pi / 30 * C.R) if v5 else (3.75, 6.5, 70.0)
    study.TSR_DESIGN = tsr
    study.best_point.__defaults__[0].clear()
    blade = Blade(R=R, tsr_design=tsr, cl_design=1.0)
    rows = []
    for V in study.VS:
        res, om, p = study.best_point(blade, V, cap / R, polar)
        P = min(res.power, S.P_SHAFT)
        if V > study.V_STORM_START:
            P = S.P_SHAFT * (1 - (1 - study.STORM_FRAC) * (V - study.V_STORM_START) / (study.V_CUTOUT - study.V_STORM_START))
        if V > study.V_CUTOUT:
            P = 0.0
        rpm = min(om * 30 / math.pi, S.RPM_RATED)
        e = chain(P, rpm) if P > 0 and rpm >= S.RPM_MIN * 0.9 else dict(P_net=0.0, eta_gen=0.0)
        rows.append(dict(V=float(V), rpm=rpm, P_shaft=P, P_net=max(e["P_net"], 0.0), eta_gen=e["eta_gen"]))
    V = np.array([r["V"] for r in rows]); Pn = np.array([r["P_net"] for r in rows])
    aep = {}
    for va in (5.0, 6.0, 7.0, 8.0, 10.0):
        c = va / math.gamma(1.5)
        f = (2 / c) * (V / c) * np.exp(-(V / c) ** 2)
        aep[str(va)] = round(float(np.sum(Pn * f * (V[1] - V[0])) * 8760 * 0.97 / 1000))
    r_ = chain(S.P_SHAFT, S.RPM_RATED)
    return rows, aep, r_


def main():
    out = dict(aep_net_kWh={}, rated_chain={}, power_curve_net_kW={})
    for pol in (ROUGH, CLEAN):
        for name, v5 in (("current_D7.5", False), ("V5_D8.3", True)):
            rows, aep, r_ = curve(v5, pol)
            out["aep_net_kWh"][f"{name}_{pol.name}"] = aep
            out["rated_chain"][name] = {k: round(v, 4) for k, v in r_.items()}
            if pol is ROUGH:
                out["power_curve_net_kW"][name] = {str(r["V"]): round(r["P_net"] / 1e3, 2) for r in rows if r["V"] <= 26 and r["V"] % 1 == 0}
        a, b = out["aep_net_kWh"][f"current_D7.5_{pol.name}"], out["aep_net_kWh"][f"V5_D8.3_{pol.name}"]
        out["aep_net_kWh"][f"gain_pct_{pol.name}"] = {k: round(100 * (b[k] / a[k] - 1), 1) for k in a}
    configure(True)
    T_r = S.P_SHAFT / (C.OMEGA)
    rated = S.terminal(C.RPM, T_r)
    estop = S.terminal(C.RPM_TRIP * 1.1, 1.25 * T_r)
    low = S.terminal(C.RPM_MIN, 0.5 * 1.225 * math.pi * C.R ** 5 * 0.47 / 5.375 ** 3 * (C.RPM_MIN * math.pi / 30) ** 2)
    Ek = 0.5 * S.J_ROTOR * (C.RPM_TRIP * 1.1 * math.pi / 30) ** 2
    out["v5_electrical"] = dict(
        rated={k: round(v, 1) for k, v in rated.items()}, estop={k: round(v, 1) for k, v in estop.items()},
        min_speed={k: round(v, 1) for k, v in low.items()},
        dc_link_needed_rated_V=round(rated["Vdc_min"]), dc_link_needed_estop_V=round(estop["Vdc_min"]),
        open_circuit_peak_V_cold_design_overspeed=GEN["electrical"]["peak_line_V_m30C_at_design_overspeed"],
        estop_rotor_energy_kJ=round(Ek / 1e3, 1), estop_rotor_energy_current_kJ=round(0.5 * 216 * (231.6 * math.pi / 30) ** 2 / 1e3, 1),
        dump_load_energy_estop_kJ=round((Ek + S.P_SHAFT * 1.25 * 1.5 / 2) / 1e3),
        min_speed_note="at 30 rpm the EMF is 103 V line; the active rectifier boosts to the 750 V link (boost ratio ~5), as at 40 rpm today (138 V)")
    (C.OUT / "power_v5.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "power_curve_net_kW"}, indent=1))


if __name__ == "__main__":
    main()
