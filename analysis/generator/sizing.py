"""Analytical sizing of direct-drive PM generator concepts for the 12 kW turbine.

Run:  python3 sizing.py     (writes results/summary.json and results/*.csv)

Concept-level electromagnetic sizing (shear stress method with flux, slot and
loss estimates). Final design needs 2D FEA (e.g. FEMM / Ansys Maxwell),
thermal network and structural checks.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

OUT = Path(__file__).parent / "results"
OUT.mkdir(exist_ok=True)

# ---------------------------------------------------------------- inputs
N_RATED = 178.0                     # rpm, from rotor study (doc 03)
T_RATED = 729.0                     # Nm shaft torque at rated
MARGIN = 1.10                       # continuous torque margin (turbulence, ageing)
T_DES = T_RATED * MARGIN
P_SHAFT = T_RATED * N_RATED * 2 * math.pi / 60
N_OVERSPEED = 230.0                 # rpm design overspeed

MU0 = 4e-7 * math.pi
RHO_CU_120 = 2.38e-8                # ohm m, copper at 120 C (hot-spot design)
RHO_CU_75 = 2.08e-8                 # ohm m, copper at 75 C (typical operating)
D_STEEL, D_NDFEB, D_CU, D_LAM = 7850, 7500, 8900, 7650

# NdFeB grade: N42SH (Br 1.30 T at 20 C, -0.12 %/K); worst case hot 100 C
BR_20 = 1.30
BR_HOT = BR_20 * (1 - 0.0012 * (100 - 20))
BR_COLD = BR_20 * (1 - 0.0012 * (-40 - 20))   # higher Br at -40 C

# Lamination M270-35A: ~2.7 W/kg at 1.5 T, 50 Hz; build factor 1.5
P15_50 = 2.7
BUILD = 1.5


def iron_loss_wkg(B: float, f: float) -> float:
    return BUILD * P15_50 * (B / 1.5) ** 2 * (f / 50.0) ** 1.4


def winding_factor(Q: int, two_p: int) -> float:
    """Fundamental winding factor of a double-layer tooth-coil winding.

    Each tooth carries one coil spanning one slot pitch. Coils are assigned
    to phase A when their EMF phasor lies within +/-30 deg of 0 (positive)
    or 180 deg (reversed). kw = pitch factor x distribution factor.
    """
    p = two_p // 2
    kp = abs(math.sin(math.pi * p / Q))
    acc_re = acc_im = 0.0
    n = 0
    for k in range(Q):
        a = (k * p * 2 * math.pi / Q + math.pi) % (2 * math.pi) - math.pi
        if abs(a) <= math.pi / 6 + 1e-9:
            v = a
        elif abs(a) >= 5 * math.pi / 6 - 1e-9:
            v = a - math.copysign(math.pi, a)
        else:
            continue
        acc_re += math.cos(v); acc_im += math.sin(v); n += 1
    kd = math.hypot(acc_re, acc_im) / n
    return kp * kd


# ---------------------------------------------------------- radial outer rotor
def radial_outer_rotor(D: float, slot_pole=(9, 8), tau_target=0.050, g=0.002,
                       A=30_000.0, J=3.5e6, fill=0.45, alpha_m=0.80,
                       B_tooth=1.6, B_yoke=1.4):
    """Outer-rotor surface-PM machine, fractional-slot concentrated winding.

    D: air gap diameter [m]. A: electric loading [A/m rms]. J: current density.
    """
    # pole count from target pole pitch, constrained to the Q/2p = 9/8 family
    k = max(1, round(math.pi * D / tau_target / slot_pole[1]))
    two_p = slot_pole[1] * k
    Q = slot_pole[0] * k
    p = two_p // 2
    tau = math.pi * D / two_p
    tau_s = math.pi * D / Q
    f = p * N_RATED / 60
    kw = winding_factor(Q, two_p)

    # magnet thickness for ~0.85 T flat-top gap flux at hot Br, Carter ~1.1
    g_eff = 1.10 * g + 0.0005              # + retaining sleeve / coating
    Bg_target = 0.85
    hm = Bg_target * 1.05 * g_eff / (BR_HOT - Bg_target)
    hm = max(hm, 0.005)                    # >= 5 mm for demag robustness
    Bg = BR_HOT * hm / (hm + 1.05 * g_eff)
    B1 = 4 / math.pi * Bg * math.sin(alpha_m * math.pi / 2)

    sigma = B1 * A * kw / math.sqrt(2)     # tangential stress [Pa]
    L = 2 * T_DES / (math.pi * D ** 2 * sigma)

    # slots
    w_t = Bg * tau_s / B_tooth
    w_s = tau_s - w_t
    cu_area_total = A * math.pi * D / J    # conductor area summed over slots
    slot_area = cu_area_total / Q / fill
    d_s = 1.15 * slot_area / w_s           # 15 % for inward narrowing (outer rotor)
    h_sy = Bg * alpha_m * tau / (2 * B_yoke)
    h_ry = max(Bg * alpha_m * tau / (2 * B_yoke), 0.010)  # >=10 mm for stiffness/sealing

    # masses
    l_end = 1.3 * tau_s                    # per side, concentrated coils
    l_turn_half = L + l_end
    m_cu = cu_area_total * l_turn_half * D_CU
    m_teeth = Q * w_t * d_s * L * 0.96 * D_LAM
    r_yo = D / 2 - d_s
    m_syoke = math.pi * (r_yo ** 2 - (r_yo - h_sy) ** 2) * L * 0.96 * D_LAM
    m_mag = two_p * alpha_m * tau * hm * L * D_NDFEB
    r_m = D / 2 + g + hm
    m_ryoke = math.pi * ((r_m + h_ry) ** 2 - r_m ** 2) * L * D_STEEL

    # losses at rated
    p_cu = RHO_CU_120 * J ** 2 * cu_area_total * l_turn_half
    p_cu_75 = RHO_CU_75 * J ** 2 * cu_area_total * l_turn_half
    p_fe = m_teeth * iron_loss_wkg(B_tooth, f) + m_syoke * iron_loss_wkg(B_yoke, f)
    p_mag_eddy = 0.003 * P_SHAFT           # segmented magnets
    p_stray = 0.005 * P_SHAFT
    p_loss = p_cu_75 + p_fe + p_mag_eddy + p_stray
    eta = (P_SHAFT - p_loss) / P_SHAFT

    # magnetic attraction (unbalanced pull per mm eccentricity, rough)
    f_attr = Bg ** 2 / (2 * MU0) * math.pi * D * L  # total radial pressure force (balanced)

    return dict(
        topology="radial_outer_rotor", D_gap_m=round(D, 3), L_m=round(L, 3),
        poles=two_p, slots=Q, freq_Hz=round(f, 1), freq_overspeed_Hz=round(p * N_OVERSPEED / 60, 1),
        winding_factor=round(kw, 3), pole_pitch_mm=round(tau * 1000, 1),
        magnet_thickness_mm=round(hm * 1000, 1), Bg_T=round(Bg, 2), B1_T=round(B1, 2),
        shear_stress_kPa=round(sigma / 1000, 1), A_kA_per_m=A / 1000, J_A_per_mm2=J / 1e6,
        slot_depth_mm=round(d_s * 1000, 1), tooth_width_mm=round(w_t * 1000, 1),
        stator_yoke_mm=round(h_sy * 1000, 1), rotor_yoke_mm=round(h_ry * 1000, 1),
        outer_diameter_m=round(2 * (r_m + h_ry), 3),
        mass_magnet_kg=round(m_mag, 1), mass_copper_kg=round(m_cu, 1),
        mass_lamination_kg=round(m_teeth + m_syoke, 1), mass_rotor_yoke_kg=round(m_ryoke, 1),
        mass_active_kg=round(m_mag + m_cu + m_teeth + m_syoke + m_ryoke, 1),
        loss_cu_W=round(p_cu_75), loss_cu_hot_W=round(p_cu), loss_fe_W=round(p_fe),
        loss_total_W=round(p_loss), efficiency=round(eta, 4),
        radial_magnetic_pressure_kN=round(f_attr / 1000, 1),
    )


# ------------------------------------------------------- axial flux, coreless
def axial_coreless(Ro: float, ratio=0.60, t_coil=0.014, clearance=0.003, J=3.0e6,
                   fill=0.55, alpha_m=0.70, kw=0.85, disk=0.020):
    """Double-rotor axial flux machine with an air-cored (resin-cast) stator."""
    Ri = ratio * Ro
    Rm = 0.5 * (Ro + Ri)
    g_mag = t_coil + 2 * clearance
    Bg_target = 0.55
    hm = Bg_target * g_mag / (2 * (BR_HOT - Bg_target))   # each side
    Bg = BR_HOT * 2 * hm / (2 * hm + g_mag)
    B1 = 4 / math.pi * Bg * math.sin(alpha_m * math.pi / 2)
    A = J * t_coil * fill                    # A/m at mean radius
    sigma = B1 * A * kw / math.sqrt(2)
    T = sigma * 2 * math.pi / 3 * (Ro ** 3 - Ri ** 3)
    ann = math.pi * (Ro ** 2 - Ri ** 2)
    m_mag = 2 * ann * alpha_m * hm * D_NDFEB
    m_cu = ann * t_coil * fill * 1.35 * D_CU   # 35 % end-turn allowance
    m_disk = 2 * math.pi * Ro ** 2 * disk * D_STEEL
    p_cu = RHO_CU_75 * J ** 2 * ann * t_coil * fill * 1.35
    p_eddy = 0.010 * P_SHAFT                 # eddy loss in conductors in the gap (litz reduces)
    p_stray = 0.003 * P_SHAFT
    p_loss = p_cu + p_eddy + p_stray
    attraction = Bg ** 2 / (2 * MU0) * ann * alpha_m
    return dict(
        topology="axial_coreless_double_rotor", Ro_m=round(Ro, 3), Ri_m=round(Ri, 3),
        outer_diameter_m=round(2 * Ro + 0.04, 3), torque_Nm=round(T),
        magnet_thickness_each_side_mm=round(hm * 1000, 1), Bg_T=round(Bg, 2),
        shear_stress_kPa=round(sigma / 1000, 1),
        mass_magnet_kg=round(m_mag, 1), mass_copper_kg=round(m_cu, 1),
        mass_rotor_disks_kg=round(m_disk, 1), mass_active_kg=round(m_mag + m_cu + m_disk, 1),
        loss_total_W=round(p_loss), efficiency=round((P_SHAFT - p_loss) / P_SHAFT, 4),
        axial_attraction_per_disk_kN=round(attraction / 1000, 1),
    )


def solve_axial_for_torque():
    lo, hi = 0.2, 0.8
    for _ in range(50):
        mid = 0.5 * (lo + hi)
        if axial_coreless(mid)["torque_Nm"] < T_DES:
            lo = mid
        else:
            hi = mid
    return axial_coreless(hi)


def main():
    radial = [radial_outer_rotor(D) for D in (0.45, 0.50, 0.55, 0.60, 0.65, 0.70)]
    axial = solve_axial_for_torque()
    j_sens = [radial_outer_rotor(0.60, J=J) for J in (3.0e6, 3.5e6, 4.0e6)]
    recommended = radial_outer_rotor(0.60, J=3.0e6)
    summary = dict(inputs=dict(n_rated_rpm=N_RATED, T_rated_Nm=T_RATED, T_design_Nm=round(T_DES),
                               P_shaft_W=round(P_SHAFT), n_overspeed_rpm=N_OVERSPEED,
                               magnet="N42SH", Br_hot_100C=round(BR_HOT, 3), Br_cold_m40C=round(BR_COLD, 3),
                               lamination="M270-35A"),
                   radial_outer_rotor=radial, axial_coreless=axial,
                   current_density_sensitivity_D060=j_sens, recommended=recommended)
    keys = list(radial[0].keys())
    with open(OUT / "radial_sweep.csv", "w") as fh:
        fh.write(",".join(keys) + "\n")
        for r in radial:
            fh.write(",".join(str(r[k]) for k in keys) + "\n")
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
