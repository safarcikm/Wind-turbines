"""IEC 61400-2 Simplified Load Model (SLM) applied to the 12 kW turbine.

Run:  python3 slm.py      (writes results/slm.json)

IMPORTANT: the equations are reconstructed from NREL reports on IEC 61400-2
(NREL/TP-5000-83708 and NREL/CP-500-33004) and from general knowledge of the
standard. They must be checked against a purchased copy of IEC 61400-2:2013
before use in certification. Fatigue ranges follow the standard's
peak-to-peak convention (factor 2 on gravity and centrifugal terms).
Load cases B and C mainly govern free-yaw (tail vane) turbines; B is evaluated
with our active-yaw fault rate. Partial safety factor for SLM ultimate loads:
gamma_f = 3.0.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "rotor"))
from bem import Blade  # noqa: E402

OUT = HERE / "results"
OUT.mkdir(exist_ok=True)

G = 9.81
RHO = 1.225                   # the standard uses 1.225 kg/m3
GAMMA_F_ULT = 3.0

# Turbine data
B = 3
R = 3.75
blade = Blade(R=R, tsr_design=6.5, cl_design=1.0)
A_PROJ_B = blade.solidity_area()          # planform area of one blade
M_B = 20.0
R_COG = 1.55
I_B = M_B * 1.85 ** 2                     # blade inertia about rotor axis (flapwise)
M_R = 3 * M_B + 80.0 + 60.0               # rotor incl. hub and generator drum
L_RB = 0.12                               # rotor centre to first bearing
L_RT = 0.75                               # rotor centre to yaw axis
E_R = 0.005 * R                           # rotor eccentricity (default)

P_DESIGN = 13_600.0                       # shaft power at rated
N_DESIGN = 178.0
W_DESIGN = N_DESIGN * 2 * math.pi / 60
Q_DESIGN = P_DESIGN / W_DESIGN
V_DESIGN = 10.5
LAMBDA_DESIGN = W_DESIGN * R / V_DESIGN
N_MAX = 250.0                             # design overspeed (raised from 230 after DLC 1.3, doc 08)
W_MAX = N_MAX * 2 * math.pi / 60
V_AVE = 10.0                              # Class S
V_E50 = 77.0
M_BRAKE = 8_730.0                         # Nm, doc 07
C_D = 1.5
CT_MAX = 0.5
G_SHORT = 2.0                             # short-circuit torque factor if no better data


def main():
    res = dict(inputs=dict(A_proj_B_m2=round(A_PROJ_B, 3), m_B=M_B, R_cog=R_COG, m_r=M_R,
                           Q_design_Nm=round(Q_DESIGN), lambda_design=round(LAMBDA_DESIGN, 2),
                           n_design_rpm=N_DESIGN, n_max_rpm=N_MAX, V_ave=V_AVE, V_e50=V_E50))

    # A: normal operation, fatigue ranges (gamma_f = 1.0)
    A = dict(
        dF_zB_N=2 * M_B * R_COG * W_DESIGN ** 2,
        dM_xB_Nm=Q_DESIGN / B + 2 * M_B * G * R_COG,
        dM_yB_Nm=LAMBDA_DESIGN * Q_DESIGN / B,
        dF_x_shaft_N=1.5 * LAMBDA_DESIGN * Q_DESIGN / R,
        dM_x_shaft_Nm=Q_DESIGN + 2 * M_R * G * E_R,
    )
    A["dM_shaft_Nm"] = 2 * M_R * G * L_RB + R / 6 * A["dF_x_shaft_N"]
    A["cycles_20y"] = N_DESIGN * 60 * 8760 * 20      # one cycle per revolution

    # B: yawing (active yaw fault rate 5 deg/s)
    w_yaw = 5 * math.pi / 180
    B_ = dict(M_yB_Nm=M_B * w_yaw ** 2 * L_RT * R_COG + 2 * w_yaw * I_B * W_DESIGN + R / 9 * A["dF_x_shaft_N"],
              M_shaft_Nm=B * w_yaw * I_B * W_DESIGN + M_R * G * L_RB + R / 6 * A["dF_x_shaft_N"])

    # D: maximum thrust
    D = dict(F_x_shaft_N=CT_MAX * 3.125 * RHO * V_AVE ** 2 * math.pi * R ** 2)

    # E: maximum rotational speed
    E = dict(F_zB_N=M_B * W_MAX ** 2 * R_COG,
             M_shaft_Nm=M_R * G * L_RB + M_R * E_R * W_MAX ** 2 * L_RB)

    # F: short circuit at load connection
    F = dict(M_x_shaft_Nm=G_SHORT * Q_DESIGN)
    F["M_xB_Nm"] = F["M_x_shaft_Nm"] / B + M_B * G * R_COG

    # G: shutdown (braking)
    Gc = dict(M_x_shaft_Nm=M_BRAKE + Q_DESIGN)
    Gc["M_xB_Nm"] = Gc["M_x_shaft_Nm"] / B + M_B * G * R_COG

    # H: parked, V_e50
    H = dict(M_yB_Nm=C_D * 0.25 * RHO * V_E50 ** 2 * A_PROJ_B * R,
             F_x_shaft_N=B * C_D * 0.5 * RHO * V_E50 ** 2 * A_PROJ_B)

    def scale(d, g):
        out = {}
        for k, v in d.items():
            if k.startswith("cycles"):
                out[k] = v
            else:
                out[k.replace("_Nm", "").replace("_N", "")] = round(v * g / 1e3, 2)
        return out

    res["A_fatigue_ranges_kN_kNm"] = scale(A, 1.0)
    res["ultimate_design_values_gamma_3_kN_kNm"] = dict(
        B_yaw=scale(B_, GAMMA_F_ULT), D_max_thrust=scale(D, GAMMA_F_ULT),
        E_max_speed=scale(E, GAMMA_F_ULT), F_short_circuit=scale(F, GAMMA_F_ULT),
        G_shutdown=scale(Gc, GAMMA_F_ULT), H_parked=scale(H, GAMMA_F_ULT))
    res["characteristic_values_kN_kNm"] = dict(
        B_yaw=scale(B_, 1), D_max_thrust=scale(D, 1), E_max_speed=scale(E, 1),
        F_short_circuit=scale(F, 1), G_shutdown=scale(Gc, 1), H_parked=scale(H, 1))
    (OUT / "slm.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
