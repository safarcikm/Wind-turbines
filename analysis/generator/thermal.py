"""Lumped-parameter thermal network for the outer-rotor generator.

Run:  python3 thermal.py      (reads results/fea_summary.json if present)

Nodes: winding (slot part), end winding, stator core, internal air, rotor drum
(magnets), ambient (fixed). Steady state, copper resistance updated with
temperature. Concept-level: coefficients are textbook correlations with
conservative choices; a CFD or test-rig calibration follows.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import sys

import numpy as np

VARIANT = sys.argv[1] if len(sys.argv) > 1 else "iter1"
OUT = Path(__file__).parent / "results" / ("" if VARIANT == "iter1" else VARIANT)

# ---- geometry (recommended design, docs/04)
L = 0.069                  # stack length
R_S = 0.299                # stator bore radius
SLOTS = 45
SLOT_DEPTH, SLOT_W = 0.060, 0.015
D_DRUM = 0.65              # outer drum diameter
L_DRUM = L + 2 * 0.06      # drum length incl. end-winding space
L_END = 1.3 * (2 * math.pi * R_S / SLOTS)   # end-winding length per side (from sizing)
GAP = 0.002

# ---- losses (W) at rated, from sizing / FEA
P_CU_75 = 435.0            # copper loss referenced to 75 C
P_FE = 200.0
P_ROTOR = 40.0             # magnet + rotor yoke eddy loss
P_STRAY = 70.0             # stray load loss, assigned to stator core

# ---- materials
K_AIR = 0.026
NU_AIR_30, NU_AIR_M30 = 1.6e-5, 1.1e-5
PR = 0.71
K_SLOT_INS = 0.20          # liner + impregnation effective [W/mK]
T_SLOT_INS = 0.0006        # liner + resin gap [m]
K_BUNDLE = 1.2             # VPI round-wire bundle, transverse [W/mK]
EPS = 0.90                 # painted drum emissivity
SIGMA = 5.67e-8


def cylinder_h(V, D, nu):
    """Churchill-Bernstein correlation, cross flow over a cylinder."""
    Re = V * D / nu
    Nu = 0.3 + 0.62 * Re ** 0.5 * PR ** (1 / 3) / (1 + (0.4 / PR) ** (2 / 3)) ** 0.25 * \
        (1 + (Re / 282000) ** (5 / 8)) ** (4 / 5)
    return Nu * K_AIR / D


def solve_case(T_amb, V_wind, load=1.0, solar_W=0.0, induction=0.30, rpm=178.0,
               support_R=0.66, extra_stator_heat=0.0, nu=NU_AIR_30,
               h_int_run=15.0, fin_in=1.0, fin_out=1.0):
    w = rpm * 2 * math.pi / 60
    V_eff = math.hypot(V_wind * (1 - induction), w * D_DRUM / 2)
    h_out = cylinder_h(max(V_eff, 0.5), D_DRUM, nu)
    A_drum = (math.pi * D_DRUM * L_DRUM + math.pi * D_DRUM ** 2 / 4) * fin_out   # shell + rear cover
    # gap: Taylor-Couette, conservative Nu ~ 2
    h_gap = 2 * K_AIR / GAP / 2 * 2 if rpm > 20 else K_AIR / GAP
    h_gap = min(h_gap, 27.0)
    A_gap = 2 * math.pi * R_S * L
    h_int = h_int_run if rpm > 20 else 5.0  # internal air, stirred by the rotor
    A_ew = 2 * SLOTS * (L_END * 2 * 0.015 + 0.015 * 0.06)              # end-winding surface (approx)
    A_core_faces = 2 * math.pi * (R_S ** 2 - (R_S - 0.085) ** 2)
    A_drum_in = math.pi * D_DRUM * (L_DRUM - L) + math.pi * D_DRUM ** 2 / 4 * 2

    # winding -> core through slot (slot part)
    A_slot_wall = SLOTS * (2 * SLOT_DEPTH + SLOT_W) * L
    R_ins = T_SLOT_INS / (K_SLOT_INS * A_slot_wall)
    R_bundle = (SLOT_W / 4) / (3 * K_BUNDLE * A_slot_wall / 2)          # half-width slab, average
    R_w_core = R_ins + R_bundle
    # end winding -> slot winding along copper (axial conduction)
    cu_area = 30_000 * math.pi * 2 * R_S / 3.0e6                       # total conductor area [m2]
    R_ew_w = (L_END / 2 + L / 4) / (390 * cu_area * 0.8) / 2           # two ends in parallel
    R_ew_air = 1 / (h_int * A_ew)
    R_core_air = 1 / (h_int * A_core_faces)
    R_core_rotor = 1 / (h_gap * A_gap)
    R_air_rotor = 1 / (h_int * A_drum_in * fin_in)
    T_amb_K = T_amb + 273.15
    T = dict(w=T_amb + 60, ew=T_amb + 60, core=T_amb + 40, air=T_amb + 30, rot=T_amb + 20)
    for _ in range(50):
        h_rad = 4 * EPS * SIGMA * ((T["rot"] + T_amb) / 2 + 273.15) ** 3
        R_rot_amb = 1 / ((h_out + h_rad) * A_drum)
        # copper loss split: slot part vs end part by length
        frac_slot = L / (L + L_END)
        P_cu = load ** 2 * P_CU_75 * (1 + 0.00393 * ((T["w"] + T["ew"]) / 2 - 75))
        P_slot, P_ew = P_cu * frac_slot, P_cu * (1 - frac_slot)
        P_core = P_FE * load ** 0 + P_STRAY * load ** 2 + extra_stator_heat
        P_rot = P_ROTOR * load ** 2 + solar_W
        # nodes: w, ew, core, air, rot
        G = np.zeros((5, 5)); b = np.zeros(5)
        def link(i, j, R):
            G[i, i] += 1 / R; G[j, j] += 1 / R; G[i, j] -= 1 / R; G[j, i] -= 1 / R
        link(0, 2, R_w_core); link(1, 0, R_ew_w); link(1, 3, R_ew_air)
        link(2, 3, R_core_air); link(2, 4, R_core_rotor); link(3, 4, R_air_rotor)
        # ground links
        G[4, 4] += 1 / R_rot_amb; b[4] += T_amb / R_rot_amb
        G[2, 2] += 1 / support_R; b[2] += T_amb / support_R
        b += np.array([P_slot, P_ew, P_core, 0.0, P_rot])
        x = np.linalg.solve(G, b)
        T_new = dict(zip(["w", "ew", "core", "air", "rot"], x))
        if max(abs(T_new[k] - T[k]) for k in T) < 0.01:
            T = T_new; break
        T = T_new
    # hot spot: centre of the slot bundle, plus end-winding peak
    q_vol = P_slot / (SLOTS * SLOT_W * SLOT_DEPTH * L * 0.45 + 1e-12) * 0.45
    hot = max(T["w"], T["ew"]) + q_vol * (SLOT_W / 2) ** 2 / (2 * K_BUNDLE) * 0.5
    return dict(T_amb=T_amb, V_wind=V_wind, load=load, h_out=round(h_out, 1),
                P_cu=round(P_cu), T_winding=round(T["w"], 1), T_end_winding=round(T["ew"], 1),
                T_hotspot=round(hot, 1), T_core=round(T["core"], 1), T_internal_air=round(T["air"], 1),
                T_rotor_magnets=round(T["rot"], 1),
                rise_winding_K=round(T["w"] - T_amb, 1))


def heating_power_for_margin(T_amb, V_wind, margin_K=5.0, **kw):
    """Stator DC-injection power to keep the stator margin_K above ambient when parked."""
    lo, hi = 0.0, 2000.0
    for _ in range(50):
        mid = 0.5 * (lo + hi)
        r = solve_case(T_amb, V_wind, load=0.0, rpm=0.0, extra_stator_heat=mid - P_FE,
                       nu=NU_AIR_M30, **kw)
        if r["T_core"] - T_amb < margin_K:
            lo = mid
        else:
            hi = mid
    return round(hi)


def main():
    global P_CU_75, P_FE, SLOT_DEPTH
    fea = OUT / "fea_summary.json"
    if fea.exists():
        d = json.loads(fea.read_text())
        P_FE = float(d.get("iron_loss_no_load_W", P_FE)) * 1.15   # +15 % under load
        SLOT_DEPTH = d["geometry"]["d_slot"]
        if "losses_rated" in d:
            P_CU_75 = d["losses_rated"]["copper_75C_W"]
        else:
            J_ratio = d["rated_load"]["current_density_for_802Nm_A_per_mm2"] / 3.0
            P_CU_75 = 435.0 * J_ratio ** 2
    # Baseline: plain drum, steel stator support, rotor-stirred internal air.
    # Improved: aluminium stator carrier into a hollow spindle cooled by nacelle air
    # (support_R 0.40 K/W incl. ventilated spindle bore), internal fan blades on the rotor end cover (h 40),
    # inner drum fins (3x area), outer drum ribs (1.5x area).
    imp = dict(support_R=0.40, h_int_run=40.0, fin_in=3.0, fin_out=1.5)
    cases = {
        "hot_day_rated_10.5ms": solve_case(30, 10.5, solar_W=100),
        "hot_day_rated_wake_calm_nacelle": solve_case(30, 10.5, solar_W=100, induction=0.6),
        "hot_day_110pct_overload": solve_case(30, 12.0, load=1.1, solar_W=100),
        "typical_iceland_rated_10C": solve_case(10, 12.0),
        "cold_rated_minus30C": solve_case(-30, 15.0, nu=NU_AIR_M30),
        "IMPROVED_hot_day_rated_10.5ms": solve_case(30, 10.5, solar_W=100, **imp),
        "IMPROVED_hot_day_rated_wake_calm_nacelle": solve_case(30, 10.5, solar_W=100, induction=0.6, **imp),
        "IMPROVED_hot_day_110pct_overload": solve_case(30, 12.0, load=1.1, solar_W=100, **imp),
        "IMPROVED_typical_iceland_rated_10C": solve_case(10, 12.0, **imp),
    }
    heat = {f"parked_{T}C_{V}ms": heating_power_for_margin(T, V, **imp) for T, V in [(-30, 2.0), (-30, 10.0), (0, 5.0)]}
    res = dict(inputs=dict(P_cu_75=round(P_CU_75), P_fe=round(P_FE), P_rotor=P_ROTOR, P_stray=P_STRAY),
               cases=cases, anti_condensation_heating_W=heat,
               limits=dict(class_H_C=180, design_hotspot_C=130, magnet_design_C=100))
    (OUT / "thermal_summary.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
