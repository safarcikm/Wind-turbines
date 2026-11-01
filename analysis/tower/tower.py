"""Tilt-up tower and foundation concept sizing for the 12 kW turbine.

Run:  python3 tower.py [ops_loads.json]    (seconds; writes results/tower_summary.json, plots)

- Beam finite element model (Euler-Bernoulli, consistent mass) of a tapered
  tubular tower with the tower-top mass and rotary inertia, a rotational
  foundation spring and, for the guyed option, a lateral guy spring.
- Load cases: operation (aeroelastic simulation, file from run_tower_loads.py,
  or the doc 08 envelope if absent), parked storm at V_e50 with side wind,
  parked storm with ice (DLC 6.5), earthquake (EN 1998-1 response spectrum,
  1 % damping as in IEC 61400-1 annex C) with operating loads, tilt-up
  (DLC 8.1), and the IEC 61400-2 SLM parked thrust as a sensitivity.
- Checks: section class 3 (no local buckling, D/t <= 90 eps^2), yield with
  gamma_M1 = 1.1, fatigue of the base flange and section flange welds (detail
  71, EN 1993-1-9, gamma_Mf = 1.35), first frequency >= 3.3 Hz on the softest
  soil with ice, deflection.
- Foundations: spread footing on firm, soft volcanic and frost-susceptible
  soil (EN 1997 style checks), and a rock-anchored plinth.

Concept-level: soil data are generic placeholders until site investigation.
"""
from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path

import numpy as np
from scipy.linalg import eigh
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
OUT = HERE / "results"
OUT.mkdir(exist_ok=True)

G = 9.81
STEEL_RHO, E_STEEL, FY = 7850.0, 210e9, 355e6
EPS2 = 235 / 355
DT_MAX = 90 * EPS2                 # class 3 limit for circular hollow sections in bending
GAMMA_M1 = 1.1
GAMMA_WIND_EC = 1.5                # EN 1990 variable action (stricter than IEC 1.35)
GAMMA_IEC = 1.35
F_MIN = 3.3                        # Hz, 1.1 x 1P at 178 rpm: lower bound for a stiff (guyed) tower
F_MAX_SOFT = 2.0 / 1.1             # Hz, 3P at 40 rpm / 1.1: upper bound for a freestanding tower
F_MIN_SOFT = 0.667 * 1.1           # Hz, 1P at 40 rpm x 1.1

# tower top (doc 07)
M_TOP = 480.0
J_TOP = 300.0                      # kg m2, fore-aft rocking inertia of nacelle + rotor
D_TOP = 0.32                       # m, tower top outer diameter (yaw bearing adapter)
F_SIDE_VE50 = 8.0e3 + 5.8e3        # N, parked side wind at V_e50: rotor in-plane 8 kN + nacelle 5.8 kN (doc 07)
M_TOP_GRAV = 1.5e3                 # Nm, overhang of the rotor weight (char.)
SLM_FX_DESIGN = 41.64e3            # N, SLM case H shaft thrust, gamma 3 included (doc 08)
SLM_FX_CHAR = 13.88e3

# wind
RHO_COLD = 1.35
V_E50, V_E1 = 77.0, 58.0
ALPHA_GUST = 0.11                  # IEC extreme wind profile exponent
CF_CLEAN, CF_ICE = 0.8, 1.0
ICE_T, ICE_RHO = 0.05, 700.0       # m radial wet snow / rime on tower, kg/m3 (doc 02: dense Icelandic wet snow)
BLADE_ICE_AREA_FACTOR = 1.3

# earthquake (EN 1998-1 Type 1, ground type D envelope for all sites)
AG = 0.5 * G
SPECTRA = {"A": (1.0, 0.15, 0.4, 2.0), "B": (1.2, 0.15, 0.5, 2.0), "C": (1.15, 0.20, 0.6, 2.0),
           "D": (1.35, 0.20, 0.8, 2.0)}
XI_EQ = 0.01

# fatigue (EN 1993-1-9)
DETAIL = 71e6
GAMMA_MF = 1.35


@dataclass
class Tower:
    H: float = 18.0
    D_base: float = 0.60
    D_top: float = D_TOP
    t: tuple = (0.010, 0.008)      # wall thickness per section, bottom to top
    n_el: int = 48
    guy_z: float | None = None     # guy attachment height for the guyed option
    k_guy: float = 0.0             # lateral guy stiffness [N/m] (both directions handled by symmetry)
    extra_mass_frac: float = 0.10  # flanges, hinge, cable ladder, paint

    @property
    def n_sec(self):
        return len(self.t)

    def geom(self, z):
        D = self.D_base + (self.D_top - self.D_base) * z / self.H
        sec = np.minimum((z / self.H * self.n_sec).astype(int), self.n_sec - 1)
        t = np.array(self.t)[sec]
        A = math.pi * D * t
        I = math.pi * D ** 3 * t / 8
        W = math.pi * D ** 2 * t / 4
        return D, t, A, I, W

    def mass(self):
        z = np.linspace(0, self.H, 400)
        _, _, A, _, _ = self.geom(z)
        return float(np.trapezoid(A, z) * STEEL_RHO * (1 + self.extra_mass_frac))


def fe_assemble(tw: Tower, K_theta: float, top_mass=M_TOP, top_J=J_TOP, ice=False, k_guy=None):
    n = tw.n_el
    zn = np.linspace(0, tw.H, n + 1)
    ndof = 2 * (n + 1)
    K = np.zeros((ndof, ndof)); M = np.zeros((ndof, ndof))
    kes = []
    for e in range(n):
        L = zn[e + 1] - zn[e]
        zm = np.array([0.5 * (zn[e] + zn[e + 1])])
        D, t, A, I, _ = tw.geom(zm)
        EI = E_STEEL * I[0]
        mu = A[0] * STEEL_RHO * (1 + tw.extra_mass_frac)
        if ice:
            mu += ICE_RHO * math.pi * ((D[0] + 2 * ICE_T) ** 2 - D[0] ** 2) / 4
        ke = EI / L ** 3 * np.array([[12, 6 * L, -12, 6 * L], [6 * L, 4 * L * L, -6 * L, 2 * L * L],
                                      [-12, -6 * L, 12, -6 * L], [6 * L, 2 * L * L, -6 * L, 4 * L * L]])
        me = mu * L / 420 * np.array([[156, 22 * L, 54, -13 * L], [22 * L, 4 * L * L, 13 * L, -3 * L * L],
                                       [54, 13 * L, 156, -22 * L], [-13 * L, -3 * L * L, -22 * L, 4 * L * L]])
        idx = [2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3]
        K[np.ix_(idx, idx)] += ke; M[np.ix_(idx, idx)] += me
        kes.append(ke)
    M[-2, -2] += top_mass; M[-1, -1] += top_J
    K[1, 1] += K_theta
    kg = tw.k_guy if k_guy is None else k_guy
    if tw.guy_z is not None and kg > 0:
        ig = int(round(tw.guy_z / tw.H * n))
        K[2 * ig, 2 * ig] += kg
    free = np.arange(1, ndof)      # base translation fixed
    return K, M, zn, free, kes


def fe_moments(kes, u):
    """Bending moment magnitude at the lower node of each element, plus the top node (0)."""
    m = [abs((ke @ u[2 * e:2 * e + 4])[1]) for e, ke in enumerate(kes)]
    return np.array(m + [abs((kes[-1] @ u[-4:])[3])])


def fe_modes(tw: Tower, K_theta: float, top_mass=M_TOP, top_J=J_TOP, ice=False, n_modes=4, k_guy=None):
    """Bending modes of the tower on a rotational spring. Returns freqs [Hz], shapes, M, nodes."""
    K, M, zn, free, _ = fe_assemble(tw, K_theta, top_mass, top_J, ice, k_guy)
    w2, v = eigh(K[np.ix_(free, free)], M[np.ix_(free, free)])
    f = np.sqrt(np.maximum(w2[:n_modes], 0)) / (2 * math.pi)
    shapes = np.zeros((K.shape[0], n_modes)); shapes[free] = v[:, :n_modes]
    return f, shapes, M, zn


def fe_static(tw: Tower, K_theta, F_top, M_top, q_fun, k_guy=None):
    """Linear static solution; returns node heights, bending moments, guy reaction."""
    K, M, zn, free, kes = fe_assemble(tw, K_theta, k_guy=k_guy)
    F = np.zeros(K.shape[0])
    dz = np.gradient(zn)
    F[0::2] += q_fun(zn) * dz
    F[-2] += F_top; F[-1] += M_top
    u = np.zeros(K.shape[0])
    u[free] = np.linalg.solve(K[np.ix_(free, free)], F[free])
    kg = tw.k_guy if k_guy is None else k_guy
    Rg = 0.0
    if tw.guy_z is not None:
        ig = int(round(tw.guy_z / tw.H * tw.n_el))
        Rg = kg * u[2 * ig]
    return zn, fe_moments(kes, u), Rg, u


def drag_profile(tw: Tower, V_hub, cf, ice=False, rho=RHO_COLD, alpha=ALPHA_GUST):
    """Return z, distributed tower drag q(z) [N/m]."""
    z = np.linspace(0.0, tw.H, 200)
    D, *_ = tw.geom(z)
    if ice:
        D = D + 2 * ICE_T
    V = V_hub * (np.maximum(z, 1.0) / tw.H) ** alpha
    return z, 0.5 * rho * V ** 2 * cf * D


def moment_from_top_and_drag(tw, z_eval, F_top, M_top, z, q):
    """Bending moment at heights z_eval from a top force, top moment and drag q(z)."""
    out = []
    for ze in z_eval:
        m = z >= ze
        out.append(F_top * (tw.H - ze) + M_top + np.trapezoid(q[m] * (z[m] - ze), z[m]))
    return np.array(out)


def spectrum(T, ground="D", xi=XI_EQ):
    S, TB, TC, TD = SPECTRA[ground]
    eta = max(math.sqrt(10 / (5 + 100 * xi)), 0.55)
    if T < TB:
        return AG * S * (1 + T / TB * (eta * 2.5 - 1))
    if T < TC:
        return AG * S * eta * 2.5
    if T < TD:
        return AG * S * eta * 2.5 * TC / T
    return AG * S * eta * 2.5 * TC * TD / T ** 2


def seismic_moments(tw, K_theta, z_eval, ground="D", k_guy=None):
    """Response spectrum (SRSS of 4 modes): bending moment envelope at z_eval, and guy force."""
    K, M, zn, free, kes = fe_assemble(tw, K_theta, k_guy=k_guy)
    f, sh, _, _ = fe_modes(tw, K_theta, n_modes=4, k_guy=k_guy)
    r = np.zeros(M.shape[0]); r[0::2] = 1.0           # horizontal ground motion
    mom, rg = [], []
    kg = tw.k_guy if k_guy is None else k_guy
    for k in range(len(f)):
        phi = sh[:, k]
        Gk = (phi @ M @ r) / (phi @ M @ phi)
        Sa = spectrum(1 / f[k], ground)
        u = phi * Gk * Sa / (2 * math.pi * f[k]) ** 2
        mom.append(np.interp(z_eval, zn, fe_moments(kes, u)))
        if tw.guy_z is not None:
            rg.append(kg * u[2 * int(round(tw.guy_z / tw.H * tw.n_el))])
    return np.sqrt(np.sum(np.array(mom) ** 2, axis=0)), f, float(np.sqrt(np.sum(np.array(rg) ** 2))) if rg else 0.0


def tilt_up(tw: Tower, lift_frac, dyn=1.3, V_wind=15.0):
    """Horizontal tower on the hinge, lifted at lift_frac*H; max bending moment and lift force."""
    z = np.linspace(0, tw.H, 400)
    _, _, A, _, _ = tw.geom(z)
    w = A * STEEL_RHO * (1 + tw.extra_mass_frac) * G * dyn
    P = M_TOP * G * dyn
    # wind on the rotor while lowering (worst: pushing down), rotor area flat-plate at 15 m/s gust
    P += 0.5 * 1.225 * V_wind ** 2 * 1.2 * 3 * 0.85
    a = lift_frac * tw.H
    # reactions: hinge at 0, support at a
    Mw0 = np.trapezoid(w * z, z) + P * tw.H
    Ra = Mw0 / a
    mom = []
    for ze in z:
        m = z >= ze
        Mi = np.trapezoid(w[m] * (z[m] - ze), z[m]) + P * (tw.H - ze)
        if ze < a:
            Mi -= Ra * (a - ze)
        mom.append(Mi)
    mom = np.array(mom)
    return float(np.max(np.abs(mom))), float(Ra), z, mom


def tilt_up_ginpole(tw: Tower, L_gp_frac=0.33, dyn=1.3, V_wind=15.0):
    """Monopole tilt-up: gin pole fixed perpendicular to the tower at the hinge, so the tower
    is a cantilever from the hinge when horizontal. Returns base moment, utilisation profile and line pull."""
    z = np.linspace(0, tw.H, 400)
    _, _, A, _, W = tw.geom(z)
    w = A * STEEL_RHO * (1 + tw.extra_mass_frac) * G * dyn
    P = M_TOP * G * dyn + 0.5 * 1.225 * V_wind ** 2 * 1.2 * 3 * 0.85
    mom = np.array([np.trapezoid(w[z >= ze] * (z[z >= ze] - ze), z[z >= ze]) + P * (tw.H - ze) for ze in z])
    T_line = mom[0] / (L_gp_frac * tw.H)
    return float(mom[0]), float(np.max(mom / W) / (FY / GAMMA_M1)), float(T_line)


def resonance_checks(tw: Tower, K_theta, U_imb=0.20, zeta_ss=0.005, dT3=0.05, zeta2=0.01, vave=10.0, excl=True):
    """Fatigue damage at the base from (a) side-side 1P resonance due to rotor mass imbalance and
    (b) the second tower mode crossing 3P, using the steady rpm(V) schedule, Rayleigh winds and a
    +-10 % turbulent spread of rotor speed. dT3: 3P thrust harmonic as a fraction of mean thrust."""
    f, sh, M, zn = fe_modes(tw, K_theta, n_modes=3)
    K, M_, zn, free, kes = fe_assemble(tw, K_theta)
    f1, f2 = f[0], f[1]
    m1 = (sh[:, 0] / sh[-2, 0]) @ M @ (sh[:, 0] / sh[-2, 0])
    k1 = m1 * (2 * math.pi * f1) ** 2
    phi2 = sh[:, 1] / sh[-2, 1]
    m2 = phi2 @ M @ phi2
    k2 = m2 * (2 * math.pi * f2) ** 2
    mom2_unit = fe_moments(kes, phi2)              # moments for a unit top displacement in mode 2
    _, _, _, _, Wn = tw.geom(zn)
    s2_unit = np.max(mom2_unit / Wn)               # worst section stress per unit modal amplitude
    _, _, _, _, Wb = tw.geom(np.array([0.0]))
    R, tsr = 3.75, 6.5
    c_ray = vave / math.gamma(1.5)
    life = 20 * 8760 * 3600 * 0.97
    n1 = f1 * 60
    zone = (n1 / 1.1, n1 * 1.1) if excl else None
    dsc = DETAIL / GAMMA_MF; dsd = 0.737 * dsc; dsl = 0.0   # no cut-off: these cycles add to the turbulence spectrum
    def dmg(s, n):
        if s < dsl:
            return 0.0
        N = 2e6 * (dsc / s) ** 3 if s >= dsd else 5e6 * (dsd / s) ** 5
        return n / N
    D1 = D2 = 0.0
    for V in np.arange(3.0, 25.01, 0.5):
        p = math.exp(-((V - 0.25) / c_ray) ** 2) - math.exp(-((V + 0.25) / c_ray) ** 2)
        rpm0 = min(tsr * V / R * 60 / (2 * math.pi), 178.0)
        thrust = min(0.5 * 1.225 * math.pi * R ** 2 * V ** 2 * 0.8, 2.1e3 * (1 if V > 10.5 else (V / 10.5) ** 2) + 1e-9)
        for rpm in np.linspace(rpm0 * 0.85, rpm0 * 1.15, 13):
            w8 = math.exp(-0.5 * ((rpm - rpm0) / (0.1 * rpm0 / 1.0)) ** 2)
            if zone and zone[0] < rpm < zone[1]:
                continue                            # transits counted separately below
            wts = w8 / 4.39                         # normalised weight (sum over 13 points ~ 4.39 for this grid)
            t = p * life * wts
            om = rpm * 2 * math.pi / 60
            r1 = (rpm / 60) / f1
            x1 = U_imb * om ** 2 / k1 / math.sqrt((1 - r1 ** 2) ** 2 + (2 * zeta_ss * r1) ** 2)
            s1 = 2 * k1 * x1 * tw.H / Wb[0]
            D1 += dmg(s1, t * rpm / 60)
            r2 = (3 * rpm / 60) / f2
            x2 = dT3 * thrust / k2 / math.sqrt((1 - r2 ** 2) ** 2 + (2 * zeta2 * r2) ** 2)
            D2 += dmg(2 * x2 * s2_unit, t * 3 * rpm / 60)
    # transits through the exclusion zone: 5 % of the time spent between the zone edges (simulation)
    if zone:
        om = n1 * 2 * math.pi / 60
        x_res = U_imb * om ** 2 / k1 / (2 * zeta_ss) * 0.5          # transient build-up reaches about half
        V_lo = zone[0] * 2 * math.pi / 60 * R / tsr
        V_hi = zone[1] * 2 * math.pi / 60 * R / tsr
        p_zone = math.exp(-(V_lo / c_ray) ** 2) - math.exp(-(V_hi / c_ray) ** 2)
        D1 += dmg(2 * k1 * x_res * tw.H / Wb[0], 0.05 * p_zone * life * n1 / 60)
    x_peak = U_imb * (2 * math.pi * f1) ** 2 / k1 / (2 * zeta_ss)
    return dict(f1=round(float(f1), 2), f2=round(float(f2), 2), zone_rpm=[round(z, 1) for z in zone] if zone else None,
                side_side_peak_base_moment_amp_kNm=round(k1 * x_peak * tw.H / 1e3, 1),
                damage_side_side_1P=round(D1, 3), damage_mode2_3P=round(D2, 3),
                rpm_mode2_crossing=round(f2 / 3 * 60, 0))


def flange_bolts(M_design, D_flange, N_comp=0.0, prying=1.3):
    """Bolted ring flange: number of M24 or M30 10.9 preloaded bolts on a circle D_flange + 0.1 m."""
    Dbc = D_flange + 0.10
    for size, As in ((24, 353e-6), (30, 561e-6), (36, 817e-6)):
        Ft_rd = 0.9 * 1000e6 * As / 1.25
        for n in range(8, 49, 4):
            Fb = prying * (4 * M_design / (n * Dbc) - N_comp / n)
            if Fb <= Ft_rd:
                return dict(bolts=n, size=f"M{size} 10.9", circle_m=round(Dbc, 2), F_bolt_kN=round(Fb / 1e3, 1),
                            F_t_Rd_kN=round(Ft_rd / 1e3, 1))
    return None


# ---------------------------------------------------------------- foundations
SOILS = {
    # name: G_dyn [Pa] (low-strain, conservative), nu, design bearing resistance [Pa], soil unit weight [N/m3], frost depth [m]
    "firm soil (dense gravel, moraine)": dict(G=60e6, nu=0.30, q_rd=300e3, gamma=19e3, depth=1.6),
    "soft volcanic soil (loose ash, pumice sand)": dict(G=15e6, nu=0.35, q_rd=100e3, gamma=14e3, depth=1.6),
    "frost-susceptible silt (thawed)": dict(G=20e6, nu=0.35, q_rd=150e3, gamma=18e3, depth=1.6),
}
CONC = 24e3


def k_rot_footing(B, G_, nu):
    r = (B ** 4 / (3 * math.pi)) ** 0.25
    return 8 * G_ * r ** 3 / (3 * (1 - nu))


def footing(M_char, M_design, H_design, V_top, soil, M_op_char):
    """Smallest square spread footing (B, thickness 0.6 m, base at frost depth) meeting:
    characteristic extreme e <= B/4 (>= 75 % contact... at least half the base), operating e <= B/6 (no gap),
    design bearing on the effective area <= q_rd (EN 1997 approach 2 style)."""
    d = soil["depth"]
    for B in np.arange(1.5, 10.01, 0.1):
        V_conc = B * B * 0.6 + 0.8 * 0.8 * (d - 0.6 + 0.3)      # slab + pedestal to 0.3 m above ground
        V_soil = (B * B - 0.64) * (d - 0.6)
        W = V_conc * CONC + V_soil * soil["gamma"] + V_top
        Md_base = M_design + H_design * d
        Mk_base = M_char + H_design / 1.5 * d
        e_k = Mk_base / W
        e_op = (M_op_char + 0) / W
        e_d = Md_base / (0.9 * W)
        Bp = B - 2 * e_d
        if Bp <= 0:
            continue
        q = 1.0 * W / (Bp * B)
        if e_k <= B / 4 and e_op <= B / 6 and q <= soil["q_rd"]:
            return dict(B=round(float(B), 2), depth=d, concrete_m3=round(V_conc, 1), weight_kN=round(W / 1e3, 1),
                        e_char_over_B=round(e_k / B, 3), bearing_kPa=round(q / 1e3, 1),
                        q_rd_kPa=soil["q_rd"] / 1e3, K_theta=k_rot_footing(B, soil["G"], soil["nu"]))
    return None


def rock_anchor_plinth(M_design, V_top, n_anchor=8, d_circle=1.2, plinth=(1.6, 0.8)):
    B, h = plinth
    W = B * B * h * CONC + V_top
    T = 4 * M_design / (n_anchor * d_circle) - 0.9 * W / n_anchor
    # grouted threadbar, fy 500 MPa, gamma_M 1.15; bond to rock 1.0 MPa design, drill hole 76 mm
    As = T * 1.15 / 500e6
    d_bar = math.sqrt(4 * As / math.pi)
    bar = next(b for b in (20, 25, 28, 32, 40, 50) if b / 1000 >= d_bar)
    L_bond = T / (1.0e6 * math.pi * 0.076)
    return dict(plinth_m=f"{B} x {B} x {h}", anchors=n_anchor, circle_m=d_circle, T_design_kN=round(T / 1e3, 1),
                bar_mm=bar, bond_length_m=round(max(L_bond, 3.0), 1), concrete_m3=round(B * B * h, 1))


# ---------------------------------------------------------------- loads and checks
def ops_loads(path):
    """Operating tower loads. From run_tower_loads.py if available, else the doc 08 envelope."""
    if path and Path(path).exists():
        d = json.loads(Path(path).read_text())
        return d
    # doc 08 envelope (1.8 Hz tower, includes resonance), plus a tower drag allowance
    return dict(source="doc 08 envelope", M_base_char=74.2e3 + 6.0e3, F_top_equiv_char=74.2e3 / 18.0,
                M_top_char=6.06e3, fatigue=None)


def evaluate(tw: Tower, ops, soil_K_min, verbose=False):
    z_eval = np.linspace(0, tw.H * 0.95, 39)
    D, t, A, I, W = tw.geom(z_eval)
    res = {}
    # 1 operation (simulation): scale envelope along height with top force + top moment
    Fop = ops["M_base_char"] / tw.H if "F_top_equiv_char" not in ops else ops["F_top_equiv_char"]
    Mop = Fop * (tw.H - z_eval) + ops.get("M_top_char", 0.0)
    Mop *= ops["M_base_char"] / Mop[0]
    res["operation and faults (simulation)"] = GAMMA_IEC * Mop
    # 2 parked storm, side wind, V_e50
    z, q = drag_profile(tw, V_E50, CF_CLEAN)
    M2 = moment_from_top_and_drag(tw, z_eval, F_SIDE_VE50, M_TOP_GRAV, z, q)
    res["parked V_e50"] = GAMMA_WIND_EC * M2
    # 3 parked with ice, V_e1
    z, q = drag_profile(tw, V_E1, CF_ICE, ice=True)
    F3 = F_SIDE_VE50 * (V_E1 / V_E50) ** 2 * BLADE_ICE_AREA_FACTOR
    res["parked V_e1 + ice"] = GAMMA_WIND_EC * moment_from_top_and_drag(tw, z_eval, F3, M_TOP_GRAV, z, q)
    # 4 earthquake + operating loads (accidental combination, gamma 1.0)
    Meq, f_eq, _ = seismic_moments(tw, soil_K_min, z_eval, "D")
    res["earthquake 0.5 g (ground D) + operation"] = Meq + Mop
    # SLM sensitivity
    z, q = drag_profile(tw, V_E50, CF_CLEAN, rho=1.225)
    M_slm = moment_from_top_and_drag(tw, z_eval, SLM_FX_DESIGN, 0.0, z, 3.0 * q)
    env = np.max(np.array(list(res.values())), axis=0)
    sig = env / W
    util = sig / (FY / GAMMA_M1)
    util_slm = (M_slm / W) / (FY / GAMMA_M1)
    # tilt-up: best lift point
    M_tilt, util_tilt, T_line = tilt_up_ginpole(tw)
    # frequencies
    f_rigid, *_ = fe_modes(tw, 1e12)
    f_soft, *_ = fe_modes(tw, soil_K_min, ice=True)
    out = dict(mass_kg=round(tw.mass(), 0), D_over_t_max=round(float(np.max(D / t)), 1),
               util_max=round(float(np.max(util)), 3), util_SLM=round(float(np.max(util_slm)), 3),
               util_tilt_up=round(util_tilt, 3), tilt_up_base_moment_kNm=round(M_tilt / 1e3, 1),
               winch_line_pull_kN_ginpole_033H=round(T_line / 1e3, 1),
               governing=max(res, key=lambda k: float(np.max(res[k] / W))),
               M_base_design_kNm={k: round(float(v[0]) / 1e3, 1) for k, v in res.items()},
               M_base_SLM_kNm=round(float(M_slm[0]) / 1e3, 1),
               f1_rigid_Hz=round(float(f_rigid[0]), 2), f2_rigid_Hz=round(float(f_rigid[1]), 2),
               f1_soft_ice_Hz=round(float(f_soft[0]), 2))
    if verbose:
        out["_profiles"] = dict(z=z_eval.tolist(), env=env.tolist(), W=W.tolist(), res={k: v.tolist() for k, v in res.items()})
    return out


def fatigue_check(tw: Tower, fat):
    """fat: dict level -> list of [range_Nm, cycles_per_life]; bilinear S-N detail 71."""
    out = {}
    dsc = DETAIL / GAMMA_MF
    dsd = 0.737 * dsc
    for lvl, data in fat.items():
        z = float(lvl) * tw.H
        _, _, _, _, W = tw.geom(np.array([z]))
        D = 0.0
        for rng, n in data:
            s = rng / W[0]
            if s <= 0:
                continue
            N = 2e6 * (dsc / s) ** 3 if s >= dsd else 5e6 * (dsd / s) ** 5
            D += n / N
        out[f"z={z:.1f} m"] = round(D, 4)
    return out


def size(H, ops, n_sec, K_soft, D_bases=np.arange(0.40, 1.01, 0.05), ts=(5, 6, 8, 10, 12, 14, 16)):
    best = None
    for Db in D_bases:
        for tb in ts:
            for tt in ts:
                if tt > tb:
                    continue
                t = tuple(np.linspace(tb, tt, n_sec).round() / 1000)
                tw = Tower(H=H, D_base=float(Db), t=t)
                D, tt_, *_ = tw.geom(np.linspace(0, H, 50))
                if np.max(D / tt_) > DT_MAX:
                    continue
                r = evaluate(tw, ops, K_soft)
                if (r["util_max"] > 1 or r["util_tilt_up"] > 1 or r["f1_rigid_Hz"] > F_MAX_SOFT
                        or r["f1_soft_ice_Hz"] < F_MIN_SOFT):
                    continue
                if ops.get("fatigue") and max(fatigue_check(tw, ops["fatigue"]).values()) > 1.0:
                    continue
                if best is None or r["mass_kg"] < best[1]["mass_kg"]:
                    best = (tw, r)
    return best


# ---------------------------------------------------------------- guyed option
PIPES_D = (0.2191, 0.2730, 0.3239, 0.3556, 0.4064, 0.4570, 0.5080, 0.6100)
PIPES_T = (0.0063, 0.0080, 0.0100, 0.0125, 0.0160)
ROPES_MM = (10, 12, 14, 16, 18, 20, 22, 24, 26, 28)
E_ROPE, GAMMA_GUY = 100e9, 2.0          # wire rope modulus; resistance factor on MBL (EN 1993-3-1 style)


def rope(d_mm):
    """6x36 IWRC, 1770 grade: metallic area and minimum breaking load (approx.)."""
    return dict(A=0.58 * math.pi * (d_mm / 1000) ** 2 / 4, MBL=0.66e3 * d_mm ** 2, mass=0.0040 * d_mm ** 2)


def chi_column(N_cr, A):
    lam = math.sqrt(A * FY / N_cr)
    ph = 0.5 * (1 + 0.21 * (lam - 0.2) + lam ** 2)
    return min(1.0, 1 / (ph + math.sqrt(max(ph ** 2 - lam ** 2, 0))))


def evaluate_guyed(H, D, t, zg_frac, d_rope, ops, R_frac=0.6):
    tw = Tower(H=H, D_base=D, D_top=D, t=(t,), guy_z=zg_frac * H)
    zg, Ra = tw.guy_z, R_frac * H
    Lg = math.hypot(zg, Ra); c = Ra / Lg; s_ = zg / Lg
    rp = rope(d_rope)
    k1 = E_ROPE * rp["A"] * c * c / Lg            # one guy, horizontal stiffness
    T0 = 0.10 * rp["MBL"]
    hinge = 1e3
    cases = {}
    # parked storm, side wind / ice storm: static with one effective guy (leeward slack, conservative)
    zq, qq = drag_profile(tw, V_E50, CF_CLEAN)
    cases["parked V_e50"] = (GAMMA_WIND_EC, F_SIDE_VE50, M_TOP_GRAV, lambda z: np.interp(z, zq, qq))
    zq2, qq2 = drag_profile(tw, V_E1, CF_ICE, ice=True)
    F3 = F_SIDE_VE50 * (V_E1 / V_E50) ** 2 * BLADE_ICE_AREA_FACTOR
    cases["parked V_e1 + ice"] = (GAMMA_WIND_EC, F3, M_TOP_GRAV, lambda z: np.interp(z, zq2, qq2))
    Fop = ops["M_base_char"] / 18.0
    cases["operation and faults (simulation)"] = (GAMMA_IEC, Fop, ops.get("M_top_char", 0.0), lambda z: 0 * z)
    W = math.pi * D ** 2 * t / 4; A = math.pi * D * t; I = math.pi * D ** 3 * t / 8
    out_cases, util, T_max = {}, 0.0, 0.0
    m_tube = tw.mass()
    for name, (gam, F, Mt, qf) in cases.items():
        zn, mom, Rg, _ = fe_static(tw, hinge, gam * F, gam * Mt, lambda z, qf=qf: gam * qf(z), k_guy=k1)
        T = T0 + abs(Rg) / c
        N = 4 * T0 * s_ + (abs(Rg) / c) * s_ + (m_tube + M_TOP) * G * 1.35
        N_cr = math.pi ** 2 * E_STEEL * I / zg ** 2
        chi = chi_column(N_cr, A)
        u = N / (chi * A * FY / GAMMA_M1) + float(np.max(mom)) / (W * FY / GAMMA_M1)
        out_cases[name] = dict(M_max_kNm=round(float(np.max(mom)) / 1e3, 1), guy_T_kN=round(T / 1e3, 1),
                               N_kN=round(N / 1e3, 1), util=round(u, 3))
        util = max(util, u); T_max = max(T_max, T)
    # earthquake + operation (gamma 1.0)
    z_eval = np.linspace(0, H, 49)
    Meq, feq, Rg_eq = seismic_moments(tw, hinge, z_eval, "D", k_guy=2 * k1)
    zn, mom_op, Rg_op, _ = fe_static(tw, hinge, Fop, ops.get("M_top_char", 0.0), lambda z: 0 * z, k_guy=2 * k1)
    Meq_tot = float(np.max(Meq + np.interp(z_eval, zn, mom_op)))
    T_eq = T0 + (Rg_eq + abs(Rg_op)) / (2 * c)
    u_eq = Meq_tot / (W * FY / GAMMA_M1) + (4 * T0 * s_ + (m_tube + M_TOP) * G) / (A * FY / GAMMA_M1)
    out_cases["earthquake 0.5 g (ground D) + operation"] = dict(M_max_kNm=round(Meq_tot / 1e3, 1),
                                                                guy_T_kN=round(T_eq / 1e3, 1), util=round(u_eq, 3))
    util = max(util, u_eq); T_max = max(T_max, T_eq)
    f, *_ = fe_modes(tw, hinge, k_guy=2 * k1)
    f_ice, *_ = fe_modes(tw, hinge, ice=True, k_guy=k1)     # ice, and leeward guy slack: lower bound
    best = min((tilt_up(tw, lf) + (lf,) for lf in np.arange(0.4, 0.86, 0.05)), key=lambda x: x[0])
    util_tilt = best[0] / (W * FY / GAMMA_M1)
    return dict(geometry=dict(H=H, D=D, t_mm=round(t * 1000, 1), guy_height_m=round(zg, 1), anchor_radius_m=round(Ra, 1),
                              guy_length_m=round(Lg, 1), rope_mm=d_rope, pretension_kN=round(T0 / 1e3, 1)),
                mass_tube_kg=round(m_tube), mass_guys_kg=round(4 * Lg * rp["mass"]),
                util_max=round(util, 3), guy_T_max_kN=round(T_max / 1e3, 1), guy_MBL_kN=round(rp["MBL"] / 1e3),
                guy_util=round(T_max / (rp["MBL"] / GAMMA_GUY), 3), anchor_uplift_kN=round(T_max * s_ / 1e3, 1),
                anchor_horizontal_kN=round(T_max * c / 1e3, 1), cases=out_cases,
                f1_Hz=round(float(f[0]), 2), f2_Hz=round(float(f[1]), 2), f1_ice_one_guy_Hz=round(float(f_ice[0]), 2),
                util_tilt_up=round(float(util_tilt), 3), D_over_t=round(D / t, 1))


def size_guyed(H, ops, band):
    best = None
    for D in PIPES_D:
        for t in PIPES_T:
            if D / t > DT_MAX:
                continue
            for zf in (0.67, 0.75, 0.83):
                for dr in ROPES_MM:
                    r = evaluate_guyed(H, D, t, zf, dr, ops)
                    if r["guy_util"] > 1:
                        continue
                    ok_f = (r["f1_ice_one_guy_Hz"] >= F_MIN) if band == "stiff" else \
                        (r["f1_Hz"] <= F_MAX_SOFT and r["f1_ice_one_guy_Hz"] >= F_MIN_SOFT)
                    if r["util_max"] <= 1 and r["util_tilt_up"] <= 1 and ok_f:
                        score = r["mass_tube_kg"] + r["mass_guys_kg"]
                        if best is None or score < best[0]:
                            best = (score, r)
                    break          # smallest rope that carries the load for this geometry
    return best[1] if best else None


def main():
    summary = dict(ops_source={}, towers={}, foundations={})
    for H, n_sec in ((18.0, 2), (24.0, 3)):
        ops = ops_loads(str(OUT / f"ops_loads_monopole_{int(H)}m.json"))
        summary["ops_source"][f"{int(H)} m"] = ops.get("source")
        # footing on soft soil sets the softest rotational stiffness; iterate (footing size depends on loads)
        K_soft = 5e8
        for _ in range(3):
            tw, r = size(H, ops, n_sec, K_soft)
            prof = evaluate(tw, ops, K_soft, verbose=True)["_profiles"]
            res = prof["res"]
            M_char_storm = res["parked V_e50"][0] / GAMMA_WIND_EC
            M_design = max(v[0] for v in res.values())
            H_design = GAMMA_WIND_EC * (F_SIDE_VE50 + np.trapezoid(*drag_profile(tw, V_E50, CF_CLEAN)[::-1]))
            V_top = (tw.mass() + M_TOP) * G
            fnd = {}
            for name, soil in SOILS.items():
                fnd[name] = footing(M_char_storm, M_design, H_design, V_top, soil, ops["M_base_char"])
            K_new = min(f["K_theta"] for f in fnd.values())
            if abs(K_new - K_soft) / K_soft < 0.05:
                break
            K_soft = K_new
        fnd["rock (anchored plinth)"] = rock_anchor_plinth(M_design, V_top)
        f_by_soil = {name: round(float(fe_modes(tw, f["K_theta"])[0][0]), 2) for name, f in fnd.items() if "K_theta" in f}
        f_by_soil["rock (anchored plinth)"] = round(float(fe_modes(tw, 5e9)[0][0]), 2)
        for f in fnd.values():
            if "K_theta" in f:
                f["K_theta_MNm_per_rad"] = round(f.pop("K_theta") / 1e6, 0)
        key = f"monopole_{int(H)}m"
        r["geometry"] = dict(H=H, D_base=round(tw.D_base, 2), D_top=tw.D_top, t_mm=[round(x * 1000) for x in tw.t],
                             sections=n_sec, section_length_m=H / n_sec)
        r["f1_by_soil_Hz"] = f_by_soil
        f1 = r["f1_rigid_Hz"]
        r["exclusion_zone_rpm"] = [round(60 * f1 / 1.1, 1), round(60 * f1 * 1.1, 1)]
        if ops.get("fatigue"):
            r["fatigue_damage"] = fatigue_check(tw, ops["fatigue"])
        r["resonance"] = {f"V_ave {va} m/s, imbalance {u} kg m, exclusion zone {ex}": resonance_checks(tw, K_soft, U_imb=u, vave=va, excl=ex)
                          for va in (6.0, 10.0) for u in (0.2, 1.0) for ex in (True, False)}
        prof_z = np.array(prof["z"]); env = np.max(np.array(list(prof["res"].values())), axis=0)
        r["flanges"] = {}
        for k in range(n_sec):
            zf = k * H / n_sec
            Mf = float(np.interp(zf, prof_z, env))
            Df = float(tw.geom(np.array([zf]))[0][0])
            r["flanges"][f"z={zf:.0f} m" + (" (base, to hinge frame)" if k == 0 else "")] = dict(
                M_design_kNm=round(Mf / 1e3, 1), D_m=round(Df, 3), **(flange_bolts(Mf, Df) or {}))
        summary["towers"][key] = r
        summary["foundations"][key] = fnd
        if H == 18.0:
            plot_tower(tw, prof, key)
    ops = ops_loads(str(OUT / "ops_loads_monopole_18m.json"))
    for H in (18.0, 24.0):
        for band in ("stiff", "soft"):
            summary["towers"][f"guyed_{int(H)}m_{band}"] = size_guyed(H, ops, band)
    (OUT / "tower_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=1))


def plot_tower(tw, prof, key):
    z = np.array(prof["z"]); W = np.array(prof["W"])
    fig, ax = plt.subplots(1, 2, figsize=(10, 6), sharey=True)
    for k, v in prof["res"].items():
        ax[0].plot(np.array(v) / 1e3, z, label=k)
    ax[0].set_xlabel("Design bending moment [kNm]"); ax[0].set_ylabel("Height [m]"); ax[0].legend(fontsize=8)
    for k, v in prof["res"].items():
        ax[1].plot(np.array(v) / W / (FY / GAMMA_M1), z, label=k)
    ax[1].axvline(1.0, color="k", lw=0.8)
    ax[1].set_xlabel("Utilisation (stress / (fy / 1.1))")
    for a in ax:
        a.grid(alpha=0.3)
    fig.suptitle(f"{key}: base D {tw.D_base:.2f} m, top D {tw.D_top:.2f} m, t {[round(x*1000) for x in tw.t]} mm")
    fig.tight_layout(); fig.savefig(OUT / f"{key}_moments.png", dpi=110)


if __name__ == "__main__":
    main()
