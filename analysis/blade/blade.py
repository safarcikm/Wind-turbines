"""Blade structural concept: section model, layup sizing and checks for two material options.

Run:  python3 blade.py     (about a minute; writes results/blade_summary.json, results/*.csv, plots)

Options:
  glass              glass/epoxy UD spar caps, glass triax skins, glass biax webs, PET foam core
  glass_cored_caps   as glass, spar caps backed by foam core and an inner skin
  carbon             carbon/epoxy UD spar caps (pultruded or infused), otherwise as glass
  carbon_cored_caps  carbon caps backed by foam core and an inner skin

Section model: thin-walled closed section on a NACA 4-digit thickness outline (camber
ignored for stiffness), blended to a circle towards the root. Spar caps between two shear
webs (0.15c to 0.45c), sandwich shell panels elsewhere, trailing edge UD strip.
Integrates EA, EI_flap, EI_edge, mass, and strains at every perimeter point.

Loads (doc 08):
  SLM H   parked, wind on the blade's flat side, root 26.02 kNm design (gamma_f 3.0)
  SLM G   shutdown edgewise, root 10.37 kNm design
  SLM E   centrifugal at 250 rpm, gamma_f 3.0
  SIM     aeroelastic ultimate: resultant root 8.52 kNm design (gamma_f 1.35)
  FATIGUE aeroelastic DEL at 1e7: flap 3.19 kNm, edge 1.22 kNm (m = 10 glass, 14 carbon)

Material factors (assumptions until IEC 61400-2:2013 is checked, doc 08):
  ultimate, aeroelastic route: gamma_m 2.2 (DNV-ST-0376 style product of factors)
  ultimate, SLM route: gamma_m 1.35 (the SLM gamma_f of 3.0 already covers model uncertainty)
  fatigue: gamma_m 1.96; stiffness (deflection): 1.1
"""
from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.linalg import eigh
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "rotor"))
from bem import Blade, CLEAN, solve  # noqa: E402

OUT = HERE / "results"
OUT.mkdir(exist_ok=True)

# ------------------------------------------------------------------ materials (characteristic)
MAT = {
    #            E_span [Pa]  rho    eps_t   eps_c   m (S-N)   note
    "UD_glass": (42e9, 1950, 0.020, 0.015, 10, "E-glass UD / epoxy, infused, Vf 0.55"),
    "UD_carbon": (125e9, 1580, 0.013, 0.0085, 14, "standard modulus carbon UD / epoxy"),
    "triax": (22e9, 1900, 0.015, 0.012, 10, "glass 0/+45/-45 / epoxy"),
    "biax": (12e9, 1900, 0.015, 0.012, 10, "glass +-45 / epoxy (webs), G 11 GPa, shear strain 1.5 %"),
}
G_BIAX, GAMMA_SHEAR = 11e9, 0.015
E_TRANS = {"UD_glass": 12e9, "UD_carbon": 8e9, "triax": 12e9, "biax": 12e9}
RHO_CORE, RHO_ADH = 100.0, 1200.0       # PET foam, adhesive
GM_ULT_SIM, GM_ULT_SLM, GM_FAT, GM_STIFF, GM_BUCK = 2.2, 1.35, 1.96, 1.1, 1.5

# ------------------------------------------------------------------ geometry
R, R_HUB = 3.75, 0.40
BL = Blade(R=R, tsr_design=6.5, cl_design=1.0, n=40)
X_CAP0, X_CAP1 = 0.15, 0.45            # spar caps / webs, fraction of chord
T_SKIN = 0.0010                         # triax per face of sandwich shell
T_CORE = 0.006                          # PET foam core in shell panels
T_CORE_WEB = 0.008
T_TE = 0.002                            # trailing edge UD glass strip (width 0.04 c)
OVERHANG, TILT_DEG, D_TOWER_TIP = 0.75, 5.0, 0.37   # rotor plane ahead of tower axis; tower Ø at tip height
N_PER = 160


def t_over_c(r):
    """Thickness distribution: root cylinder at the pitch bearing, 30 % at max chord, 18 % outboard."""
    pts = [(R_HUB, 1.00), (0.55, 0.70), (0.775, 0.30), (1.5, 0.25), (2.25, 0.21), (3.2, 0.18), (R, 0.18)]
    x, y = zip(*pts)
    return float(np.interp(r, x, y))


def outline(c, tc):
    """Closed outline (x, y) of a section, LE at x = 0. Blends NACA 00xx (30 %) to a circle."""
    s = np.linspace(0, 2 * math.pi, N_PER, endpoint=False)
    xs = 0.5 * (1 - np.cos(s))                       # 0 -> 1 -> 0 around the section
    up = s < math.pi
    t_af = min(tc, 0.30)
    yt = 5 * t_af * (0.2969 * np.sqrt(xs) - 0.1260 * xs - 0.3516 * xs ** 2 + 0.2843 * xs ** 3 - 0.1036 * xs ** 4)
    y_af = np.where(up, yt, -yt) * c
    x_af = xs * c
    if tc <= 0.30:
        return x_af, y_af, xs, up
    w = (tc - 0.30) / 0.70
    x_ci = 0.5 * c * (1 - np.cos(s)); y_ci = 0.5 * c * np.sin(s)
    return (1 - w) * x_af + w * x_ci, (1 - w) * y_af + w * y_ci, xs, up


@dataclass
class Layup:
    cap_mat: str
    t_cap: np.ndarray        # per station [m]
    t_web: np.ndarray
    t_root: np.ndarray       # extra root build-up (triax) per station


def section(r, c, tc, cap_mat, t_cap, t_web, t_root, cap_core=False):
    x, y, xs, up = outline(c, tc)
    xn, yn = np.roll(x, -1), np.roll(y, -1)
    ds = np.hypot(xn - x, yn - y)
    xm, ym = 0.5 * (x + xn), 0.5 * (y + yn)
    in_cap = (xs >= X_CAP0) & (xs <= X_CAP1) & (tc < 0.9)
    in_te = xs > 0.96
    E = np.full_like(ds, MAT["triax"][0]); t = np.full_like(ds, 2 * T_SKIN + t_root)
    rho_t = t * MAT["triax"][1]
    core = (~in_cap) & (~in_te) & (tc < 0.9)
    rho_t = rho_t + np.where(core, T_CORE * RHO_CORE, 0.0)
    # spar cap: UD plus the two skins
    Ec = MAT[cap_mat][0]
    E = np.where(in_cap, (Ec * t_cap + MAT["triax"][0] * (2 * T_SKIN + t_root)) / (t_cap + 2 * T_SKIN + t_root), E)
    rho_t = np.where(in_cap, rho_t + t_cap * MAT[cap_mat][1], rho_t)
    if cap_core:
        # cap backed by foam core and an inner triax skin (sandwich cap against buckling)
        rho_t = np.where(in_cap, rho_t + T_CORE * RHO_CORE + T_SKIN * MAT["triax"][1], rho_t)
        E = np.where(in_cap, (E * (t + t_cap) + MAT["triax"][0] * T_SKIN) / (t + t_cap + T_SKIN), E)
    t = np.where(in_cap, t + t_cap + (T_SKIN if cap_core else 0.0), t)
    # trailing edge UD strip
    E = np.where(in_te, (MAT["UD_glass"][0] * T_TE + MAT["triax"][0] * (2 * T_SKIN + t_root)) / (T_TE + 2 * T_SKIN + t_root), E)
    rho_t = np.where(in_te, rho_t + T_TE * MAT["UD_glass"][1], rho_t)
    t = np.where(in_te, t + T_TE, t)
    EA_s = E * t * ds
    # webs (vertical lines at X_CAP0 and X_CAP1)
    webs = []
    if tc < 0.9:
        for xw in (X_CAP0, X_CAP1):
            yt = 5 * min(tc, 0.3) * (0.2969 * math.sqrt(xw) - 0.1260 * xw - 0.3516 * xw ** 2 + 0.2843 * xw ** 3 - 0.1036 * xw ** 4) * c
            webs.append((xw * c, 2 * yt))
    EA = EA_s.sum() + sum(MAT["biax"][0] * t_web * h for _, h in webs)
    xc = (np.sum(EA_s * xm) + sum(MAT["biax"][0] * t_web * h * xw for xw, h in webs)) / EA
    yc = np.sum(EA_s * ym) / EA_s.sum()
    EI_flap = np.sum(EA_s * (ym - yc) ** 2) + sum(MAT["biax"][0] * t_web * h ** 3 / 12 for _, h in webs)
    EI_edge = np.sum(EA_s * (xm - xc) ** 2) + sum(MAT["biax"][0] * t_web * h * (xw - xc) ** 2 for xw, h in webs)
    mass = np.sum(rho_t * ds) + sum((2 * MAT["biax"][1] * t_web + RHO_CORE * T_CORE_WEB) * h for _, h in webs)
    mass *= 1.10                                   # adhesive, paint, LEP, heating elements
    h_spar = max([h for _, h in webs], default=c * tc)
    return dict(EA=EA, EIf=EI_flap, EIe=EI_edge, mass=mass, xm=xm - xc, ym=ym - yc, in_cap=in_cap, in_te=in_te,
                h_spar=h_spar, b_cap=(X_CAP1 - X_CAP0) * c, t_cap=t_cap, E_pt=E, t_pt=t, c=c, tc=tc, webs=webs,
                cap_core=cap_core)


# ------------------------------------------------------------------ loads along the span
def load_shapes(r, mass_pl):
    """Unit-root-moment shapes: uniform pressure on the planform (parked), operating thrust, gravity/inertia."""
    c = BL.chord if len(r) == len(BL.r) else np.interp(r, BL.r, BL.chord)
    dr = np.gradient(r)
    def mom(q):
        return np.array([np.sum(q[i:] * (r[i:] - r[i]) * dr[i:]) for i in range(len(r))])
    m_park = mom(c); m_park /= m_park[0]
    bl = Blade(R=R, tsr_design=6.5, cl_design=1.0, n=len(r))
    res = solve(bl, 10.5, 178 * 2 * math.pi / 60, 0.0)                # rated operating thrust distribution
    qop = np.interp(r, bl.r, res.dT / bl.dr / 3)
    m_op = mom(qop); m_op /= m_op[0]
    m_g = mom(mass_pl); m_g /= m_g[0]
    return m_park, m_op, m_g


LOADS = dict(SLM_H_flap=26.02e3, SLM_G_edge=10.37e3, SIM_res=8.52e3, SIM_op_flap=1.35 * 3.85e3,
             DEL_flap=3.19e3, DEL_edge=1.22e3, rpm_max=250.0, gamma_E=3.0)


def strains(sec, Mf, Me, N=0.0):
    """Strain at each perimeter point for flap moment Mf (about chord axis) and edge moment Me."""
    return Mf * sec["ym"] / sec["EIf"] + Me * sec["xm"] / sec["EIe"] + N / sec["EA"]


def check_station(sec, M, cap_mat):
    """Return utilisations (ultimate, fatigue, buckling, web shear) at one station."""
    util = {}
    cap = sec["in_cap"]
    def lim(mat, gm):
        return MAT[mat][2] / gm, MAT[mat][3] / gm
    for name, (Mf, Me, N, gm) in dict(
            SLM_H=(M["H"], 0.0, 0.0, GM_ULT_SLM), SLM_G=(0.0, M["G"], 0.0, GM_ULT_SLM), SLM_E=(0.0, 0.0, M["N"], GM_ULT_SLM),
            SIM_flap=(M["SIM"], 0.0, 0.0, GM_ULT_SIM), SIM_edge=(0.0, M["SIM"], 0.0, GM_ULT_SIM)).items():
        e = strains(sec, Mf, Me, N)
        for sgn in (1, -1):
            ee = sgn * e
            # caps
            if cap.any():
                lt, lc = lim(cap_mat, gm)
                u_cap = max(np.max(ee[cap]) / lt, np.max(-ee[cap]) / lc)
            else:
                u_cap = 0.0
            lt, lc = lim("triax", gm)
            u_sh = max(np.max(ee[~cap]) / lt, np.max(-ee[~cap]) / lc)
            util[f"{name}{'+' if sgn > 0 else '-'}"] = max(u_cap, u_sh)
    # fatigue (strain range from DEL, amplitude S-N on compression strain, R = -1 approx.)
    dF = strains(sec, M["DELf"], 0.0); dE = strains(sec, 0.0, M["DELe"])
    def fat_allow(mat):
        return 2 * MAT[mat][3] * (1e7) ** (-1 / MAT[mat][4]) / GM_FAT
    u_fat = 0.0
    if cap.any():
        u_fat = max(u_fat, np.max(np.abs(dF[cap])) / fat_allow(cap_mat))
    u_fat = max(u_fat, np.max(np.abs(dF[~cap] + dE[~cap])) / fat_allow("triax"))
    util["fatigue"] = u_fat
    # spar cap panel buckling (simply supported orthotropic plate between webs, k = 4)
    if cap.any():
        Ex = MAT[cap_mat][0]; Ey = E_TRANS[cap_mat]
        t1 = sec["t_cap"] + T_SKIN                     # outer face: skin + UD cap
        if sec["cap_core"]:
            t2 = 2 * T_SKIN                            # inner face: inner skin + inner sandwich skin
            d = T_CORE + 0.5 * (t1 + t2)
            Ef1, Ef2 = math.sqrt(Ex * Ey), MAT["triax"][0] * 0.75
            D = Ef1 * t1 * Ef2 * t2 * d ** 2 / (Ef1 * t1 + Ef2 * t2)
            EA_strip = Ex * sec["t_cap"] + MAT["triax"][0] * 3 * T_SKIN
        else:
            t_tot = sec["t_cap"] + 2 * T_SKIN
            D = math.sqrt(Ex * Ey) * t_tot ** 3 / 12
            EA_strip = Ex * sec["t_cap"] + MAT["triax"][0] * 2 * T_SKIN
        eps_cr = 4 * math.pi ** 2 * D / (sec["b_cap"] ** 2 * EA_strip) * 0.8   # k = 4, 0.8 knock-down
        e_slm = np.max(np.abs(strains(sec, M["H"], 0.0)[cap]))
        e_sim = np.max(np.abs(strains(sec, M["SIM"], 0.0)[cap]))
        util["buckling_cap"] = max(e_slm / (eps_cr / GM_ULT_SLM), e_sim / (eps_cr / GM_BUCK))
        # trailing panel sandwich buckling, width from rear web to 0.96 c
        b_te = (0.96 - X_CAP1) * sec["c"]
        d = T_CORE + T_SKIN
        Dp = MAT["triax"][0] * T_SKIN * d ** 2 / 2
        eps_cr_p = 4 * math.pi ** 2 * Dp / (b_te ** 2 * MAT["triax"][0] * 2 * T_SKIN) * 0.8
        e_pan_slm = np.max(np.abs(strains(sec, M["H"], 0.0)[~cap & ~sec["in_te"]]))
        e_pan_sim = np.max(np.abs(strains(sec, M["SIM"], 0.0)[~cap & ~sec["in_te"]]))
        util["buckling_panel"] = max(e_pan_slm / (eps_cr_p / GM_ULT_SLM), e_pan_sim / (eps_cr_p / GM_BUCK))
    # web shear (flap shear force shared by two webs), SLM H governs
    if sec["webs"]:
        h = min(hh for _, hh in sec["webs"])
        tau_strain = M["V"] / (2 * h * sec_web_t(sec) * G_BIAX)
        util["web_shear"] = tau_strain / (GAMMA_SHEAR / GM_ULT_SLM)
    return util


def sec_web_t(sec):
    return sec["_t_web"]


# ------------------------------------------------------------------ beam model
def beam_modes(r, EI, mu, rpm=0.0, n_modes=2):
    n = len(r) - 1
    ndof = 2 * (n + 1)
    K = np.zeros((ndof, ndof)); M = np.zeros((ndof, ndof)); Kg = np.zeros((ndof, ndof))
    om = rpm * 2 * math.pi / 60
    for e in range(n):
        L = r[e + 1] - r[e]
        EIe = 0.5 * (EI[e] + EI[e + 1]); m = 0.5 * (mu[e] + mu[e + 1])
        ke = EIe / L ** 3 * np.array([[12, 6 * L, -12, 6 * L], [6 * L, 4 * L * L, -6 * L, 2 * L * L],
                                       [-12, -6 * L, 12, -6 * L], [6 * L, 2 * L * L, -6 * L, 4 * L * L]])
        me = m * L / 420 * np.array([[156, 22 * L, 54, -13 * L], [22 * L, 4 * L * L, 13 * L, -3 * L * L],
                                      [54, 13 * L, 156, -22 * L], [-13 * L, -3 * L * L, -22 * L, 4 * L * L]])
        # centrifugal stiffening
        rm = 0.5 * (r[e] + r[e + 1])
        Nf = np.sum([0.5 * (mu[j] + mu[j + 1]) * (r[j + 1] - r[j]) * 0.5 * (r[j] + r[j + 1]) for j in range(e, n)]) * om ** 2
        kg = Nf / (30 * L) * np.array([[36, 3 * L, -36, 3 * L], [3 * L, 4 * L * L, -3 * L, -L * L],
                                        [-36, -3 * L, 36, -3 * L], [3 * L, -L * L, -3 * L, 4 * L * L]])
        idx = [2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3]
        K[np.ix_(idx, idx)] += ke + kg; M[np.ix_(idx, idx)] += me
    free = np.arange(2, ndof)
    w2, _ = eigh(K[np.ix_(free, free)], M[np.ix_(free, free)])
    return np.sqrt(np.maximum(w2[:n_modes], 0)) / (2 * math.pi)


def tip_deflection(r, EI, M):
    """Tip deflection of a cantilever for a bending moment distribution M(r)."""
    kappa = M / EI
    theta = np.concatenate([[0], np.cumsum(0.5 * (kappa[1:] + kappa[:-1]) * np.diff(r))])
    w = np.concatenate([[0], np.cumsum(0.5 * (theta[1:] + theta[:-1]) * np.diff(r))])
    return float(w[-1])


# ------------------------------------------------------------------ sizing
def design(cap_mat, t_root_wall=0.012, cap_core=False):
    r = np.linspace(R_HUB, R, 41)
    c = np.interp(r, BL.r, BL.chord, left=BL.chord[0])
    tc = np.array([t_over_c(x) for x in r])
    t_root = t_root_wall * np.clip((0.95 - r) / (0.95 - R_HUB), 0, 1)
    t_cap = np.full(len(r), 0.0010); t_web = np.full(len(r), 0.0015)
    for it in range(12):
        secs = [section(r[i], c[i], tc[i], cap_mat, t_cap[i], t_web[i], t_root[i], cap_core) for i in range(len(r))]
        mu = np.array([s["mass"] for s in secs])
        m_park, m_op, m_g = load_shapes(r, mu)
        om_max = LOADS["rpm_max"] * 2 * math.pi / 60
        N = LOADS["gamma_E"] * np.array([np.sum(mu[i:] * r[i:] * np.gradient(r)[i:]) for i in range(len(r))]) * om_max ** 2
        V_park = -np.gradient(m_park * LOADS["SLM_H_flap"], r)
        changed = False
        utils = []
        for i in range(len(r)):
            Mi = dict(H=LOADS["SLM_H_flap"] * m_park[i], G=LOADS["SLM_G_edge"] * m_g[i], N=N[i],
                      SIM=LOADS["SIM_res"] * m_park[i], DELf=LOADS["DEL_flap"] * m_op[i], DELe=LOADS["DEL_edge"] * m_g[i],
                      V=max(V_park[i], 1.0))
            while True:
                s = section(r[i], c[i], tc[i], cap_mat, t_cap[i], t_web[i], t_root[i], cap_core); s["_t_web"] = t_web[i]
                u = check_station(s, Mi, cap_mat)
                worst = max(u, key=u.get)
                if u[worst] <= 1.0:
                    break
                if worst == "web_shear":
                    t_web[i] += 0.00025
                elif tc[i] >= 0.9:
                    t_root[i] += 0.0005           # root cylinder: thicken the triax wall
                else:
                    t_cap[i] += 0.00025
                changed = True
                if t_cap[i] > 0.04 or t_root[i] > 0.05:
                    break
            utils.append(u)
        # monotonic cap thickness from root to tip (manufacturable ply drops)
        t_cap = np.maximum.accumulate(t_cap[::-1])[::-1]
        if not changed:
            break
    secs = [section(r[i], c[i], tc[i], cap_mat, t_cap[i], t_web[i], t_root[i], cap_core) for i in range(len(r))]
    mu = np.array([s["mass"] for s in secs])
    EIf = np.array([s["EIf"] for s in secs]); EIe = np.array([s["EIe"] for s in secs])
    m_park, m_op, m_g = load_shapes(r, mu)
    # deflection: operating extreme (DLC 1.3 flap 3.85 kNm char x 1.35) with stiffness factor
    d_tip = tip_deflection(r, EIf / GM_STIFF, LOADS["SIM_op_flap"] * m_op)
    clearance = OVERHANG - D_TOWER_TIP / 2 + R * math.sin(math.radians(TILT_DEG))
    f_flap0 = beam_modes(r, EIf, mu)[0]; f_edge0 = beam_modes(r, EIe, mu)[0]
    f_flap_rot = beam_modes(r, EIf, mu, rpm=178)[0]; f_edge_rot = beam_modes(r, EIe, mu, rpm=178)[0]
    mass = float(np.trapezoid(mu, r))
    static_moment = float(np.trapezoid(mu * r, r))
    dr = np.gradient(r)
    return dict(
        cap_material=MAT[cap_mat][5], mass_kg=round(mass + 1.5, 2),       # + root inserts and fittings 1.5 kg
        static_moment_kgm_about_axis=round(static_moment, 2),
        r_cog_m=round(static_moment / mass, 2),
        tip_deflection_m=round(d_tip, 3), tower_clearance_m=round(clearance, 3),
        clearance_util=round(d_tip / clearance, 2),
        f_flap_Hz=round(float(f_flap0), 2), f_edge_Hz=round(float(f_edge0), 2),
        f_flap_178rpm_Hz=round(float(f_flap_rot), 2), f_edge_178rpm_Hz=round(float(f_edge_rot), 2),
        max_util={k: round(max(u.get(k, 0) for u in utils), 2) for k in sorted({kk for u in utils for kk in u})},
        governing_by_station=[max(u, key=u.get) for u in utils],
        stations=dict(r=r.round(3).tolist(), chord=c.round(3).tolist(), t_over_c=tc.round(3).tolist(),
                      t_cap_mm=(t_cap * 1000).round(2).tolist(), t_web_mm=(t_web * 1000).round(2).tolist(),
                      t_root_extra_mm=(t_root * 1000).round(1).tolist(), mass_per_m=mu.round(3).tolist(),
                      EI_flap_kNm2=(EIf / 1e3).round(2).tolist(), EI_edge_kNm2=(EIe / 1e3).round(2).tolist()),
        _r=r, _mu=mu, _EIf=EIf, _EIe=EIe, _tcap=t_cap)


def root_joint(M_design=26.02e3, N_design=63.7e3, D_root=0.19, gm_insert=1.5):
    """Bolted root: number of steel inserts on a circle in the root laminate."""
    out = {}
    for D in (D_root, 0.22, 0.25):
        Dbc = D - 0.03
        for size, As, Fins in (("M12", 84.3e-6, 45e3), ("M16", 157e-6, 75e3), ("M20", 245e-6, 110e3)):
            Ft_rd = 0.9 * 1000e6 * As / 1.25
            for n in range(8, 41, 2):
                F = 4 * M_design / (n * Dbc) + N_design / n
                pitch = math.pi * Dbc / n
                d_ins = {"M12": 0.020, "M16": 0.026, "M20": 0.032}[size]
                if F <= min(Ft_rd, Fins / gm_insert * 1.5) and pitch >= 1.4 * d_ins:
                    out[f"root Ø {D:.2f} m, {size}"] = dict(inserts=n, bolt_circle_m=round(Dbc, 3), F_bolt_kN=round(F / 1e3, 1),
                                                       F_t_Rd_kN=round(Ft_rd / 1e3, 1), insert_pitch_mm=round(pitch * 1000))
                    break
    return out


def main():
    res = {}
    for opt, mat, core in (("glass", "UD_glass", False), ("glass_cored_caps", "UD_glass", True),
                           ("carbon", "UD_carbon", False), ("carbon_cored_caps", "UD_carbon", True)):
        res[opt] = design(mat, cap_core=core)
    res["root_joint"] = root_joint()
    res["assumptions"] = dict(gamma_m_ultimate_sim=GM_ULT_SIM, gamma_m_ultimate_SLM=GM_ULT_SLM, gamma_m_fatigue=GM_FAT,
                              gamma_stiffness=GM_STIFF, gamma_buckling=GM_BUCK, tilt_deg=TILT_DEG, overhang_m=OVERHANG,
                              materials={k: dict(E_GPa=v[0] / 1e9, rho=v[1], eps_t=v[2], eps_c=v[3], m=v[4], note=v[5]) for k, v in MAT.items()},
                              loads=LOADS)
    # plots
    fig, ax = plt.subplots(2, 2, figsize=(11, 8))
    for opt, col in (("glass", "C0"), ("glass_cored_caps", "C1"), ("carbon", "C3"), ("carbon_cored_caps", "C2")):
        d = res[opt]
        ax[0, 0].plot(d["_r"], d["_tcap"] * 1000, col, label=f"{opt} caps")
        ax[0, 1].plot(d["_r"], d["_mu"], col, label=opt)
        ax[1, 0].semilogy(d["_r"], d["_EIf"] / 1e3, col, label=f"{opt} flap")
        ax[1, 0].semilogy(d["_r"], d["_EIe"] / 1e3, col + "--", label=f"{opt} edge")
    ax[0, 0].set_ylabel("Spar cap UD thickness [mm]"); ax[0, 1].set_ylabel("Mass per length [kg/m]")
    ax[1, 0].set_ylabel("Bending stiffness [kNm²]")
    r = res["glass"]["_r"]
    c = np.interp(r, BL.r, BL.chord, left=BL.chord[0])
    ax[1, 1].plot(r, c, "k", label="chord [m]"); ax[1, 1].plot(r, [t_over_c(x) for x in r], "k--", label="t/c")
    for a in ax.flat:
        a.set_xlabel("Radius [m]"); a.grid(alpha=0.3); a.legend(fontsize=8)
    fig.suptitle("Blade structural concept: glass vs carbon spar caps")
    fig.tight_layout(); fig.savefig(OUT / "blade_layup.png", dpi=110)
    # section sketch at max chord
    fig, ax = plt.subplots(figsize=(8, 3))
    for rr in (0.775, 1.5, 3.0):
        cc = float(np.interp(rr, BL.r, BL.chord)); x, y, xs, up = outline(cc, t_over_c(rr))
        ax.plot(np.append(x, x[0]), np.append(y, y[0]), label=f"r = {rr} m")
        for xw in (X_CAP0, X_CAP1):
            yy = np.interp(xw * cc, x[up], y[up])
            ax.plot([xw * cc, xw * cc], [-yy, yy], "k", lw=0.8)
    ax.set_aspect("equal"); ax.legend(fontsize=8); ax.set_title("Sections with shear webs at 15 % and 45 % chord")
    fig.tight_layout(); fig.savefig(OUT / "blade_sections.png", dpi=110)
    for opt in ("glass", "glass_cored_caps", "carbon", "carbon_cored_caps"):
        for k in ("_r", "_mu", "_EIf", "_EIe", "_tcap"):
            res[opt].pop(k)
    (OUT / "blade_summary.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: ({kk: vv for kk, vv in v.items() if kk != "stations"} if isinstance(v, dict) else v)
                      for k, v in res.items() if k != "assumptions"}, indent=1))


if __name__ == "__main__":
    main()
