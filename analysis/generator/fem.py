"""2D nonlinear magnetostatic finite element model of the 40-pole / 45-slot
outer-rotor PM generator (docs/04-generator-concept.md).

Self-contained (numpy + scipy only):
- Structured polar mesh of one periodic section (8 poles / 9 slots = 72 deg),
  with periodic boundary conditions built into the node numbering.
- Linear triangles, vector potential A_z formulation, nonlinear iron (Picard).
- Rotor motion: the rotor iron is a smooth ring, so rotation is represented by
  rotating the magnet pattern on a fixed mesh. Magnet coverage and
  magnetisation are integrated per element by sub-sampling, which keeps the
  torque free of remeshing noise (important for cogging).
- Torque by Arkkio's method over the mechanical air gap.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

MU0 = 4e-7 * math.pi
NU0 = 1 / MU0


# ------------------------------------------------------------------ geometry
@dataclass
class Geometry:
    poles: int = 40
    slots: int = 45
    L: float = 0.069                 # stack length [m]
    r_s: float = 0.299               # stator outer (bore) radius [m]
    g: float = 0.0020                # mechanical air gap [m]
    sleeve: float = 0.0005           # non-magnetic retaining layer [m]
    hm: float = 0.0074               # magnet thickness [m]
    h_ry: float = 0.012              # rotor yoke [m]
    alpha_m: float = 0.80            # magnet arc / pole pitch
    w_t: float = 0.0223              # tooth body width (parallel sided) [m]
    b0: float = 0.004                # slot opening [m]
    h_tip: float = 0.002             # tooth tip height [m]
    h_wedge: float = 0.002           # tip-to-body transition [m]
    d_slot: float = 0.060            # slot body depth [m]
    h_sy: float = 0.0114             # stator yoke [m]
    br20: float = 1.30               # N42SH remanence at 20 C [T]
    br_tc: float = -0.0012           # 1/K
    mu_rm: float = 1.05
    t_mag: float = 100.0             # magnet temperature [C]

    @property
    def sym(self) -> int:
        return math.gcd(self.poles, self.slots)

    @property
    def sec_angle(self) -> float:
        return 2 * math.pi / self.sym

    @property
    def br(self) -> float:
        return self.br20 * (1 + self.br_tc * (self.t_mag - 20))

    @property
    def r_m1(self) -> float:
        return self.r_s + self.g + self.sleeve

    @property
    def r_m2(self) -> float:
        return self.r_m1 + self.hm

    @property
    def r_ry(self) -> float:
        return self.r_m2 + self.h_ry

    @property
    def r_slot_top(self) -> float:
        return self.r_s - self.h_tip - self.h_wedge

    @property
    def r_slot_bot(self) -> float:
        return self.r_slot_top - self.d_slot

    @property
    def r_in(self) -> float:
        return self.r_slot_bot - self.h_sy


# B-H curves (B [T], H [A/m])
BH_M270 = (np.array([0, 0.5, 1.0, 1.2, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.1, 2.3]),
           np.array([0, 40, 90, 130, 250, 450, 1000, 2500, 5500, 12000, 25000, 50000, 209000]))
BH_S355 = (np.array([0, 0.5, 1.0, 1.2, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.2]),
           np.array([0, 250, 550, 800, 1400, 2000, 3000, 5000, 9000, 16000, 30000, 190000]))


from scipy.interpolate import PchipInterpolator

_PCHIP = {}


def _hb(bh):
    key = id(bh)
    if key not in _PCHIP:
        _PCHIP[key] = PchipInterpolator(bh[0], bh[1], extrapolate=False)
    return _PCHIP[key]


def nu_and_dnu_db2(bh, B):
    """Reluctivity nu(B) = H/B and its derivative with respect to B^2."""
    Bb, Hh = bh
    f = _hb(bh)
    B = np.maximum(B, 1e-4)
    inside = B <= Bb[-1]
    Bi = np.where(inside, B, Bb[-1])
    H = f(Bi)
    dH = f.derivative()(Bi)
    H = np.where(inside, H, Hh[-1] + (B - Bb[-1]) * NU0)
    dH = np.where(inside, dH, NU0)
    # near B=0 use initial permeability
    small = B < 0.05
    nu0i = f.derivative()(0.0) if np.isfinite(f.derivative()(0.0)) else Hh[1] / Bb[1]
    nu = np.where(small, Hh[1] / Bb[1], H / B)
    dnu_dB = np.where(small, 0.0, (dH - H / B) / B)
    return nu, dnu_dB / (2 * B)


def nu_of_b(bh, B):
    return nu_and_dnu_db2(bh, B)[0]


# ---------------------------------------------------------------------- mesh
@dataclass
class Mesh:
    geo: Geometry
    n_theta: int = 1440
    layers: dict = field(default_factory=lambda: dict(
        yoke=4, slot=22, wedge=3, tip=3, gap=6, sleeve=1, mag=6, ryoke=5, air=2))

    def radial_edges(self):
        """Radii of the element rings (inner to outer). Subclasses may add rings."""
        g = self.geo
        edges_r = [g.r_in]
        def add(r_to, n):
            r0 = edges_r[-1]
            edges_r.extend(list(np.linspace(r0, r_to, n + 1)[1:]))
        add(g.r_slot_bot, self.layers["yoke"])
        add(g.r_slot_top, self.layers["slot"])
        add(g.r_s - g.h_tip, self.layers["wedge"])
        add(g.r_s, self.layers["tip"])
        add(g.r_s + g.g, self.layers["gap"])
        add(g.r_m1, self.layers["sleeve"])
        add(g.r_m2, self.layers["mag"])
        add(g.r_ry, self.layers["ryoke"])
        add(g.r_ry + 0.004, self.layers["air"])
        return edges_r

    def __post_init__(self):
        g = self.geo
        self.r = np.array(self.radial_edges())
        nr, nt = len(self.r), self.n_theta
        self.theta = np.arange(nt) * g.sec_angle / nt
        self.nr, self.nt = nr, nt
        self.n_nodes = nr * nt
        # triangles: unwrapped coordinates per element, wrapped node ids
        tri_ids, tri_xy = [], []
        dth = g.sec_angle / nt
        for i in range(nr - 1):
            for j in range(nt):
                jn = (j + 1) % nt
                a, b = i * nt + j, i * nt + jn
                c, d = (i + 1) * nt + jn, (i + 1) * nt + j
                th0, th1 = j * dth, (j + 1) * dth
                pa = (self.r[i], th0); pb = (self.r[i], th1)
                pc = (self.r[i + 1], th1); pd = (self.r[i + 1], th0)
                if (i + j) % 2 == 0:
                    tri_ids += [(a, b, c), (a, c, d)]; tri_xy += [(pa, pb, pc), (pa, pc, pd)]
                else:
                    tri_ids += [(a, b, d), (b, c, d)]; tri_xy += [(pa, pb, pd), (pb, pc, pd)]
        self.tri = np.array(tri_ids)
        rt = np.array(tri_xy)                       # (ne, 3, 2) as (r, theta)
        self.xy = np.stack([rt[..., 0] * np.cos(rt[..., 1]), rt[..., 0] * np.sin(rt[..., 1])], -1)
        x, y = self.xy[..., 0], self.xy[..., 1]
        ar = 0.5 * ((x[:, 1] - x[:, 0]) * (y[:, 2] - y[:, 0]) - (x[:, 2] - x[:, 0]) * (y[:, 1] - y[:, 0]))
        neg = ar < 0                                   # make all triangles counter-clockwise
        self.tri[neg] = self.tri[neg][:, [0, 2, 1]]
        self.xy[neg] = self.xy[neg][:, [0, 2, 1]]
        x, y = self.xy[..., 0], self.xy[..., 1]
        self.area = 0.5 * ((x[:, 1] - x[:, 0]) * (y[:, 2] - y[:, 0]) - (x[:, 2] - x[:, 0]) * (y[:, 1] - y[:, 0]))
        assert np.all(self.area > 0)
        # shape function gradients
        self.bx = np.stack([y[:, 1] - y[:, 2], y[:, 2] - y[:, 0], y[:, 0] - y[:, 1]], 1) / (2 * self.area[:, None])
        self.by = np.stack([x[:, 2] - x[:, 1], x[:, 0] - x[:, 2], x[:, 1] - x[:, 0]], 1) / (2 * self.area[:, None])
        cxy = self.xy.mean(1)
        self.cr = np.hypot(cxy[:, 0], cxy[:, 1])
        self.cth = np.mod(np.arctan2(cxy[:, 1], cxy[:, 0]), g.sec_angle)
        self._regions()
        # Dirichlet: inner and outer radius
        self.fixed = np.concatenate([np.arange(nt), (nr - 1) * nt + np.arange(nt)])
        self.free = np.setdiff1d(np.arange(self.n_nodes), self.fixed)
        # sub-sample points for magnet integration (barycentric grid)
        k = 6
        bary = [(i / k + 1 / (3 * k), j / k + 1 / (3 * k)) for i in range(k) for j in range(k - i)]
        bary += [((i + 1) / k - 1 / (3 * k), (j + 1) / k - 1 / (3 * k)) for i in range(k - 1) for j in range(k - 1 - i)]
        self.bary = np.array([(1 - u - v, u, v) for u, v in bary])
        mag_el = np.where(self.region == 5)[0]
        self.mag_el = mag_el
        pts = np.einsum("sk,ekd->esd", self.bary, self.xy[mag_el])    # (nm, ns, 2)
        self.mag_pts_th = np.arctan2(pts[..., 1], pts[..., 0])

    def _regions(self):
        """0 air, 1 stator iron, 2 slot copper, 3 gap air, 4 sleeve, 5 magnet annulus,
        6 rotor yoke."""
        g = self.geo
        r, th = self.cr, self.cth
        reg = np.zeros(len(r), int)
        tau_s = 2 * math.pi / g.slots
        # angle of nearest tooth centre (tooth k centred at k*tau_s)
        k = np.round(th / tau_s)
        dth = th - k * tau_s
        # perpendicular distance from tooth centre line
        dist_tooth = np.abs(r * np.sin(dth))
        # slot centre at (k+0.5) tau_s; distance to slot centre line
        ks = np.floor(th / tau_s)
        dist_slot = np.abs(r * np.sin(th - (ks + 0.5) * tau_s))
        stator = r < g.r_s
        reg[stator] = 1
        body = (r > g.r_slot_bot) & (r < g.r_slot_top) & (dist_tooth > g.w_t / 2)
        reg[body] = 2
        # wedge: slot narrows linearly from body width to opening
        in_wedge = (r >= g.r_slot_top) & (r < g.r_s - g.h_tip)
        half_body = np.maximum(r * np.sin(tau_s / 2) - g.w_t / 2 / np.cos(tau_s / 2), g.b0 / 2)
        frac = (r - g.r_slot_top) / g.h_wedge
        half_w = half_body + (g.b0 / 2 - half_body) * frac
        reg[in_wedge & (dist_slot < half_w)] = 0
        in_tip = (r >= g.r_s - g.h_tip) & (r < g.r_s)
        reg[in_tip & (dist_slot < g.b0 / 2)] = 0
        reg[(r > g.r_s) & (r < g.r_s + g.g)] = 3
        reg[(r > g.r_s + g.g) & (r < g.r_m1)] = 4
        reg[(r > g.r_m1) & (r < g.r_m2)] = 5
        reg[(r > g.r_m2) & (r < g.r_ry)] = 6
        self.region = reg
        self.slot_index = np.where(reg == 2, ks.astype(int), -1)
        # coil side: left (lower theta) or right half of the slot
        self.slot_half = np.where(th - (ks + 0.5) * tau_s < 0, 0, 1)


# ------------------------------------------------------------------- winding
def winding_layout(Q: int, poles: int, n_sec_slots: int):
    """Phase (0,1,2) and sign of the coil around each tooth in one section."""
    p = poles // 2
    out = []
    for k in range(n_sec_slots):
        ang = (k * p * 2 * math.pi / Q) % (2 * math.pi)
        best = None
        for ph in range(3):
            for sgn in (1, -1):
                ref = (-ph * 2 * math.pi / 3 + (0 if sgn > 0 else math.pi)) % (2 * math.pi)
                d = abs((ang - ref + math.pi) % (2 * math.pi) - math.pi)
                if best is None or d < best[0]:
                    best = (d, ph, sgn)
        out.append((best[1], best[2]))
    return out


# ------------------------------------------------------------------- solver
class Model:
    def __init__(self, geo: Geometry | None = None, n_theta: int = 1440, mesh_cls=None):
        self.geo = geo or Geometry()
        self.mesh = (mesh_cls or Mesh)(self.geo, n_theta=n_theta)
        m = self.mesh
        self.n_sec_slots = self.geo.slots // self.geo.sym
        self.coils = winding_layout(self.geo.slots, self.geo.poles, self.n_sec_slots)
        # coil side areas
        self.side_area = np.zeros((self.n_sec_slots, 2))
        for s in range(self.n_sec_slots):
            for h in range(2):
                sel = (m.slot_index == s) & (m.slot_half == h)
                self.side_area[s, h] = m.area[sel].sum()
        self.A = np.zeros(m.n_nodes)
        self.nu = np.full(len(m.area), NU0)
        iron = (m.region == 1) | (m.region == 6)
        self.nu[iron] = NU0 / 2000
        # stiffness pattern
        ne = len(m.area)
        self.rows = np.repeat(m.tri, 3, axis=1).ravel()
        self.cols = np.tile(m.tri, (1, 3)).ravel()
        self.kel = (m.bx[:, :, None] * m.bx[:, None, :] + m.by[:, :, None] * m.by[:, None, :]) * m.area[:, None, None]

    # magnet remanence per element for rotor angle theta_r (mech, rad)
    def magnet_source(self, theta_r: float):
        m, g = self.mesh, self.geo
        tau_p = 2 * math.pi / g.poles
        th = m.mag_pts_th - theta_r
        pole = np.floor(th / tau_p + 0.5)
        dth = th - pole * tau_p
        inside = np.abs(dth) < g.alpha_m * tau_p / 2
        sign = np.where(np.mod(pole, 2) == 0, 1.0, -1.0)
        # radial magnetisation at each sample point
        brx = np.where(inside, sign * g.br * np.cos(m.mag_pts_th), 0.0).mean(1)
        bry = np.where(inside, sign * g.br * np.sin(m.mag_pts_th), 0.0).mean(1)
        frac = inside.mean(1)
        return brx, bry, frac

    def solve(self, theta_r: float, i_abc=(0.0, 0.0, 0.0), turns_amp=1.0, iters=40, tol=1e-4,
              verbose=False):
        """i_abc: phase ampere-turns per coil side (instantaneous)."""
        m, g = self.mesh, self.geo
        brx, bry, frac = self.magnet_source(theta_r)
        nu_mag = NU0 / (1 + (g.mu_rm - 1) * frac)
        self.nu[m.mag_el] = nu_mag
        # load vector: magnets
        f = np.zeros(m.n_nodes)
        el = m.mag_el
        # curl v = (dv/dy, -dv/dx) = (by, -bx) with our gradient arrays (bx = dN/dx, by = dN/dy)
        fm = nu_mag[:, None] * (brx[:, None] * m.by[el] - bry[:, None] * m.bx[el]) * m.area[el, None]
        np.add.at(f, m.tri[el], fm)
        # load vector: currents
        for s in range(self.n_sec_slots):
            for h in range(2):
                # slot s: right side of coil s (h=0, lower theta half belongs to coil s? see below)
                # tooth k is centred at k*tau_s, slot s lies between tooth s and s+1:
                # lower-theta half (h=0) is the right side of coil s (return, -),
                # upper-theta half (h=1) is the left side of coil s+1 (+).
                coil = s if h == 0 else (s + 1) % self.n_sec_slots
                sign = -1.0 if h == 0 else 1.0
                ph, csgn = self.coils[coil]
                NI = sign * csgn * i_abc[ph] * turns_amp
                J = NI / self.side_area[s, h]
                sel = np.where((m.slot_index == s) & (m.slot_half == h))[0]
                np.add.at(f, m.tri[sel], (J * m.area[sel] / 3)[:, None] * np.ones((1, 3)))
        iron_s = np.where(m.region == 1)[0]
        iron_r = np.where(m.region == 6)[0]
        iron = np.concatenate([iron_s, iron_r])
        A = self.A.copy()
        free = m.free
        fn = np.linalg.norm(f[free]) + 1e-12

        def nonlinear_nu(A_):
            Bx, By = self.flux_density(A_)
            B2 = Bx ** 2 + By ** 2
            B = np.sqrt(B2)
            nu = self.nu.copy()
            dnu = np.zeros_like(nu)
            n_s, d_s = nu_and_dnu_db2(BH_M270, B[iron_s] / 0.96)
            nu[iron_s], dnu[iron_s] = n_s / 0.96, d_s / 0.96 / 0.96 ** 2
            n_r, d_r = nu_and_dnu_db2(BH_S355, B[iron_r])
            nu[iron_r], dnu[iron_r] = n_r, d_r
            return nu, dnu

        def residual(A_, nu):
            Ae = A_[m.tri]
            ke_a = np.einsum("eij,ej->ei", self.kel, Ae) * nu[:, None]
            r = np.zeros(m.n_nodes)
            np.add.at(r, m.tri, ke_a)
            return r - f

        nu, dnu = nonlinear_nu(A)
        res = residual(A, nu)
        for it in range(iters):
            Ae = A[m.tri]
            gA = np.einsum("eij,ej->ei", self.kel, Ae) / m.area[:, None]   # G A_e
            jac_e = nu[:, None, None] * self.kel + \
                (2 * dnu * m.area)[:, None, None] * gA[:, :, None] * gA[:, None, :]
            J = sp.csr_matrix((jac_e.ravel(), (self.rows, self.cols)), shape=(m.n_nodes, m.n_nodes))
            dA = np.zeros(m.n_nodes)
            dA[free] = spla.spsolve(J[free][:, free].tocsc(), -res[free])
            # backtracking line search on residual norm
            r0 = np.linalg.norm(res[free])
            step = 1.0
            for _ in range(8):
                A_try = A + step * dA
                nu_t, dnu_t = nonlinear_nu(A_try)
                res_t = residual(A_try, nu_t)
                if np.linalg.norm(res_t[free]) < r0 or step < 0.02:
                    break
                step *= 0.5
            A, nu, dnu, res = A_try, nu_t, dnu_t, res_t
            rel = np.linalg.norm(res[free]) / fn
            if verbose:
                print(f"  newton {it}: |r|/|f| = {rel:.2e}, step {step}")
            if rel < tol:
                break
        self.nu = nu
        self.A = A
        self.brx, self.bry = brx, bry
        return A

    def flux_density(self, A):
        m = self.mesh
        Ae = A[m.tri]
        Bx = (m.by * Ae).sum(1)       # Bx = dA/dy
        By = -(m.bx * Ae).sum(1)      # By = -dA/dx
        return Bx, By

    def torque(self, A=None):
        """Arkkio torque for the full machine [Nm]."""
        m, g = self.mesh, self.geo
        A = self.A if A is None else A
        Bx, By = self.flux_density(A)
        sel = m.region == 3
        cx, cy = m.xy[sel].mean(1).T
        th = np.arctan2(cy, cx)
        Br = Bx[sel] * np.cos(th) + By[sel] * np.sin(th)
        Bt = -Bx[sel] * np.sin(th) + By[sel] * np.cos(th)
        T_sec = g.L / (MU0 * g.g) * np.sum(m.cr[sel] * Br * Bt * m.area[sel])
        return T_sec * g.sym

    def flux_linkage_per_turn(self, A=None):
        """Phase flux linkage per turn of each coil, full machine (all coils in series) [Wb]."""
        m, g = self.mesh, self.geo
        A = self.A if A is None else A
        Ael = A[m.tri].mean(1)
        psi = np.zeros(3)
        for s in range(self.n_sec_slots):
            for h in range(2):
                coil = s if h == 0 else (s + 1) % self.n_sec_slots
                sign = -1.0 if h == 0 else 1.0
                ph, csgn = self.coils[coil]
                sel = (m.slot_index == s) & (m.slot_half == h)
                Aavg = np.sum(Ael[sel] * m.area[sel]) / self.side_area[s, h]
                psi[ph] += sign * csgn * Aavg * g.L
        return psi * g.sym

    def gap_flux(self, A=None):
        """Radial flux density along the middle of the air gap."""
        m, g = self.mesh, self.geo
        A = self.A if A is None else A
        Bx, By = self.flux_density(A)
        rmid = g.r_s + g.g / 2
        sel = (m.region == 3) & (np.abs(m.cr - rmid) < g.g / 6 + 1e-9)
        cx, cy = m.xy[sel].mean(1).T
        th = np.arctan2(cy, cx)
        Br = Bx[sel] * np.cos(th) + By[sel] * np.sin(th)
        order = np.argsort(np.mod(th, g.sec_angle))
        return np.mod(th, g.sec_angle)[order], Br[order]

    def magnet_field_along_magnetisation(self, A=None):
        """H component along the local magnetisation direction in magnet elements [A/m]
        (negative = demagnetising)."""
        m, g = self.mesh, self.geo
        A = self.A if A is None else A
        Bx, By = self.flux_density(A)
        el = m.mag_el
        brn = np.hypot(self.brx, self.bry)
        ok = brn > 0.5 * g.br
        ux, uy = self.brx[ok] / brn[ok], self.bry[ok] / brn[ok]
        Bpar = Bx[el][ok] * ux + By[el][ok] * uy
        H = (Bpar - g.br) / (MU0 * g.mu_rm)
        return H, m.cr[el][ok]
