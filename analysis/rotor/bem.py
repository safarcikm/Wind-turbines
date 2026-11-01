"""Blade element momentum (BEM) model for the 12 kW rotor concept study.

Steady-state BEM with Prandtl tip and hub loss and Buhl's high-induction
correction. Aerofoil polars are a generic parametric model representing a
roughness-tolerant ~18-21 % thick aerofoil at Re ~ 1e6 (clean and rough sets).
Replace with measured / XFOIL polars once the aerofoil family is chosen.

Concept-level only: results feed the rotor choice and early load estimates.
Final loads come from aeroelastic simulation (OpenFAST / QBlade), see
docs/02-design-basis.md section 5.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

B = 3  # number of blades


# --------------------------------------------------------------------------
# Aerofoil model
# --------------------------------------------------------------------------
@dataclass
class Polar:
    """Parametric aerofoil polar with Viterna post-stall extrapolation."""

    name: str
    cl0: float = 0.40          # lift at zero angle of attack (cambered)
    cla: float = 0.105         # lift slope per degree (~0.95 * 2pi /rad)
    clmax: float = 1.35
    cd0: float = 0.0090        # minimum drag
    kd: float = 0.0045         # drag polar curvature
    cl_cdmin: float = 0.60     # lift at minimum drag
    cdmax: float = 1.30        # finite-aspect-ratio flat plate drag (Viterna)

    @property
    def alpha_stall(self) -> float:
        return (self.clmax - self.cl0) / self.cla

    def coeffs(self, alpha_deg: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        a = np.asarray(alpha_deg, dtype=float)
        a_s = self.alpha_stall
        cl_lin = self.cl0 + self.cla * a
        cd_lin = self.cd0 + self.kd * (cl_lin - self.cl_cdmin) ** 2

        # Viterna-Corrigan post-stall
        ar = np.radians(a)
        as_r = math.radians(a_s)
        cd_s = self.cd0 + self.kd * (self.clmax - self.cl_cdmin) ** 2
        b1 = self.cdmax
        a1 = b1 / 2.0
        a2 = (self.clmax - b1 * math.sin(as_r) * math.cos(as_r)) * math.sin(as_r) / math.cos(as_r) ** 2
        b2 = (cd_s - self.cdmax * math.sin(as_r) ** 2) / math.cos(as_r)
        with np.errstate(divide="ignore", invalid="ignore"):
            cl_post = a1 * np.sin(2 * ar) + a2 * np.cos(ar) ** 2 / np.sin(ar)
            cd_post = b1 * np.sin(ar) ** 2 + b2 * np.cos(ar)

        post = (a > a_s) & (a <= 90)
        cl = np.where(post, cl_post, cl_lin)
        cd = np.where(post, cd_post, cd_lin)
        # flat plate (consistent with the Viterna limit at 90 deg: Cl = cdmax/2 sin 2a,
        # Cd = cdmax sin^2 a) for |a| > 90 deg and on the negative side
        cl_fp = 0.5 * self.cdmax * np.sin(2 * ar)
        cd_fp = self.cd0 + self.cdmax * np.sin(ar) ** 2
        cl = np.where(np.abs(a) > 90, cl_fp, cl)
        cd = np.where(np.abs(a) > 90, cd_fp, cd)
        # negative stall: linear down to -10 deg, blend to flat plate by -20 deg
        a_n1, a_n2 = -10.0, -20.0
        cl_n1 = self.cl0 + self.cla * a_n1
        cd_n1 = self.cd0 + self.kd * (cl_n1 - self.cl_cdmin) ** 2
        w = np.clip((a_n1 - a) / (a_n1 - a_n2), 0, 1)
        w = w * w * (3 - 2 * w)
        neg = (a < a_n1) & (a >= -90)
        cl = np.where(neg, (1 - w) * cl_n1 + w * cl_fp, cl)
        cd = np.where(neg, (1 - w) * cd_n1 + w * cd_fp, cd)
        return cl, np.maximum(cd, self.cd0)

    def design_point(self, cl_design: float) -> tuple[float, float]:
        """Angle of attack and L/D at the design lift coefficient."""
        alpha = (cl_design - self.cl0) / self.cla
        cl, cd = self.coeffs(np.array([alpha]))
        return alpha, float(cl[0] / cd[0])


CLEAN = Polar("clean")
# Leading edge roughness (ash erosion, insects, light ice): lower clmax,
# higher drag. Typical degradation for a roughness-tolerant section.
ROUGH = Polar("rough", cl0=0.32, cla=0.100, clmax=1.12, cd0=0.0135, kd=0.0080, cl_cdmin=0.50)


# --------------------------------------------------------------------------
# Blade geometry
# --------------------------------------------------------------------------
@dataclass
class Blade:
    R: float                     # tip radius [m]
    r_hub: float = 0.40          # hub radius (pitch bearing) [m]
    tsr_design: float = 7.0
    cl_design: float = 1.0
    polar: Polar = field(default_factory=lambda: CLEAN)
    n: int = 30
    root_frac: float = 0.10      # cylindrical root ends here (r/R)
    max_chord_frac: float = 0.20 # max chord location (r/R)

    def __post_init__(self) -> None:
        R = self.R
        # cosine spacing from hub to tip
        s = np.linspace(0, math.pi, self.n + 1)
        edges = self.r_hub + (R - self.r_hub) * (1 - np.cos(s)) / 2
        self.r = 0.5 * (edges[1:] + edges[:-1])
        self.dr = np.diff(edges)
        self.alpha_d, _ = self.polar.design_point(self.cl_design)

        lr = self.tsr_design * self.r / R
        phi = (2.0 / 3.0) * np.arctan(1.0 / lr)  # Schmitz optimum inflow angle
        c_opt = 16 * math.pi * self.r / (B * self.cl_design) * np.sin(phi / 2) ** 2

        # Manufacturable chord: linear taper through the optimum at 0.70R and
        # 0.95R, capped at the optimum at max_chord_frac, cylinder at root.
        x = self.r / R
        def copt_at(xx: float) -> float:
            rr = xx * R
            p = (2 / 3) * math.atan(1 / (self.tsr_design * xx))
            return 16 * math.pi * rr / (B * self.cl_design) * math.sin(p / 2) ** 2
        c70, c95 = copt_at(0.70), copt_at(0.95)
        slope = (c95 - c70) / 0.25
        c_lin = c70 + slope * (x - 0.70)
        c_max = c70 + slope * (self.max_chord_frac - 0.70)
        self.c_max = c_max
        self.c_root = 0.55 * c_max   # circular root diameter
        chord = np.minimum(c_lin, c_max)
        # root transition: blend from cylinder to max chord
        trans = x < self.max_chord_frac
        t = np.clip((x - self.root_frac) / (self.max_chord_frac - self.root_frac), 0, 1)
        chord = np.where(trans, self.c_root + (c_max - self.c_root) * (3 * t**2 - 2 * t**3), chord)
        self.chord = chord
        self.chord_opt = c_opt

        # Twist: optimum, linear-ish near root is acceptable; offset so tip twist = 0
        twist = np.degrees(phi) - self.alpha_d
        # limit root twist (manufacturable, and root carries little power)
        twist = np.minimum(twist, 20.0)
        self.twist = twist - twist[-1]
        self.twist_tip_offset = float(twist[-1])  # add to pitch to get design pitch
        # Root region (cylinder) is aerodynamically poor: flag for drag-only
        self.is_cylinder = x < self.root_frac

    def solidity_area(self) -> float:
        """Planform area of one blade [m^2]."""
        return float(np.sum(self.chord * self.dr))


# --------------------------------------------------------------------------
# BEM solver
# --------------------------------------------------------------------------
@dataclass
class BEMResult:
    cp: float
    ct: float
    cq: float
    thrust: float
    torque: float
    power: float
    root_flap_moment: float
    dT: np.ndarray
    dQ: np.ndarray
    alpha: np.ndarray
    a: np.ndarray


def solve(blade: Blade, V: float, omega: float, pitch_deg: float, rho: float = 1.225,
          polar: Polar | None = None) -> BEMResult:
    """Steady BEM for one operating point. pitch_deg is measured from design pitch."""
    polar = polar or blade.polar
    r, c, dr = blade.r, blade.chord, blade.dr
    R = blade.R
    theta = np.radians(blade.twist + blade.twist_tip_offset + pitch_deg)
    sigma = B * c / (2 * math.pi * r)
    a = np.full_like(r, 0.3)
    ap = np.zeros_like(r)
    for _ in range(300):
        phi = np.arctan2(V * (1 - a), omega * r * (1 + ap))
        phi = np.where(np.abs(phi) < 1e-6, 1e-6, phi)
        alpha = np.degrees(phi - theta)
        cl, cd = polar.coeffs(alpha)
        cl = np.where(blade.is_cylinder, 0.0, cl)
        cd = np.where(blade.is_cylinder, 1.0, cd)
        sphi = np.abs(np.sin(phi))
        ftip = B / 2 * (R - r) / (r * sphi)
        fhub = B / 2 * (r - blade.r_hub) / (blade.r_hub * sphi)
        F = (2 / math.pi) * np.arccos(np.exp(-np.clip(ftip, 0, 50))) * \
            (2 / math.pi) * np.arccos(np.exp(-np.clip(fhub, 0, 50)))
        F = np.maximum(F, 1e-4)
        cn = cl * np.cos(phi) + cd * np.sin(phi)
        ct_ = cl * np.sin(phi) - cd * np.cos(phi)
        k = sigma * cn / (4 * F * np.sin(phi) ** 2)
        a_new = k / (1 + k)
        # Buhl correction for high induction
        CT_loc = sigma * (1 - a) ** 2 * cn / np.sin(phi) ** 2
        hi = CT_loc > 0.96 * F
        if np.any(hi):
            Fh, CTh = F[hi], CT_loc[hi]
            aa = (18 * Fh - 20 - 3 * np.sqrt(np.maximum(CTh * (50 - 36 * Fh) + 12 * Fh * (3 * Fh - 4), 0))) / \
                 (36 * Fh - 50)
            a_new[hi] = aa
        kp = sigma * ct_ / (4 * F * np.sin(phi) * np.cos(phi))
        ap_new = kp / (1 - kp)
        a_new = np.clip(a_new, -0.5, 0.95)
        ap_new = np.clip(ap_new, -0.5, 1.0)
        if np.max(np.abs(a_new - a)) < 1e-5 and np.max(np.abs(ap_new - ap)) < 1e-5:
            a, ap = a_new, ap_new
            break
        a = 0.6 * a + 0.4 * a_new
        ap = 0.6 * ap + 0.4 * ap_new

    W2 = (V * (1 - a)) ** 2 + (omega * r * (1 + ap)) ** 2
    q = 0.5 * rho * W2 * c
    dT = B * q * cn * dr
    dQ = B * q * ct_ * r * dr
    T, Q = float(dT.sum()), float(dQ.sum())
    P = Q * omega
    A = math.pi * R ** 2
    qinf = 0.5 * rho * V ** 2
    M_flap = float(np.sum((dT / B) * (r - blade.r_hub)))  # about pitch bearing
    return BEMResult(cp=P / (qinf * A * V), ct=T / (qinf * A), cq=Q / (qinf * A * R), thrust=T,
                     torque=Q, power=P, root_flap_moment=M_flap, dT=dT, dQ=dQ, alpha=alpha, a=a)
