"""Magnet geometry study for doc 19: arc segments versus flat (rectangular) blocks.

Compares, on the frozen doc 06 machine (40 poles / 45 slots, P1 geometry):

  A   arc segment per pole, radially magnetised (doc 18 baseline, NP1-220)
  F1  one flat block per pole (parallel magnetised)
  F2  two flat blocks side by side per pole
  F3  three flat blocks side by side per pole

For each: no-load EMF and harmonics, cogging, rated-load torque and ripple,
short-circuit demagnetisation (120 C), net magnetic force on one pole of
magnets, and magnet eddy-current loss at rated load (time stepped over one
electrical period, rotor-frame field history, net-zero current per piece,
3D correction for the axial piece length). The eddy result settles the
axial segmentation (doc 14 open point 3, doc 18 M8).

Model details
- Real P1 radii: stator r 299.0, gap 2.0, sleeve 0.5 (mandrel moulded, bore
  r 301.0), magnet inner face r 301.5 at the pole (or block) centre line,
  bond line 0.15 mm (glass beads) between magnet and seat, drum shell outer
  r 323.0, stack 74 mm. The seat radius follows from the magnet shape.
- Flat blocks: the block's inner face centre sits at r 301.5, its outer
  corners on the bond beads, so the bond is thicker under the block middle.
- Magnet sources are sampled per element on a fixed mesh (fem.py), so the
  same mesh handles every shape.

Run:  python3 magnets.py            (~25-40 min, all variants)
      python3 magnets.py quick      (coarse mesh, a few minutes, for checks)
Writes results/magnets_summary.json and results/magnets_*.png
"""
from __future__ import annotations

import json
import math
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from fem import Geometry, Mesh, Model, MU0

OUT = Path(__file__).parent / "results"
OUT.mkdir(exist_ok=True)
QUICK = "quick" in sys.argv
N_THETA = 720 if QUICK else 1440

N_RATED = 178.0
T_SIZING = 802.0              # Nm, rated x 1.1 (doc 06)
TURNS = 28                    # doc 18
SIGMA_MAG = 1 / 1.5e-6        # S/m, sintered NdFeB (1.4 to 1.6 µOhm m)
RHO_MAG = 7600.0              # kg/m3
HCJ20 = 1990e3                # N40UH, A/m
HCJ_TC = -0.0055              # 1/K
STACK = 0.074
R_YOKE_OUT = 0.323            # drum shell outer radius under the magnets
BOND = 0.15e-3                # bond line (glass beads)
POLE_ARC = 0.80               # magnet arc / pole pitch (doc 06)
CLEAR = 0.20e-3               # clearance between blocks of one pole, at the inner corners


# ------------------------------------------------------------------ shapes
@dataclass
class Shape:
    key: str
    name: str
    k: int = 1                 # pieces side by side per pole (circumferential)
    flat: bool = False
    alpha: float = POLE_ARC    # pole span / pole pitch
    hm: float = 0.0077         # magnet thickness [m]

    def blocks(self, geo):
        """Block centre angles (rad, from pole centre) and width b [m] (flat) or arc (rad)."""
        tau = 2 * math.pi / geo.poles
        span = self.alpha * tau
        pitch = span / self.k
        phis = [(j - (self.k - 1) / 2) * pitch for j in range(self.k)]
        if not self.flat:
            return phis, pitch
        # inner corners of neighbouring blocks: half-angle pitch/2 at r_m1, minus half the clearance
        b = 2 * geo.r_m1 * math.tan(pitch / 2) - (CLEAR if self.k > 1 else 0.0)
        return phis, b

    def seat_radius(self, geo):
        if not self.flat:
            return geo.r_m1 + geo.hm + BOND
        _, b = self.blocks(geo)
        return math.hypot(geo.r_m1 + geo.hm, b / 2) + BOND


SHAPES = [Shape("A", "Arc segment, radial (doc 18)", 1, False),
          Shape("F1", "1 flat block per pole", 1, True),
          Shape("F2", "2 flat blocks per pole", 2, True),
          Shape("F3", "3 flat blocks per pole", 3, True),
          Shape("F2w", "2 flat blocks, span 0.84", 2, True, alpha=0.84),
          Shape("F2t", "2 flat blocks, 8.2 mm thick", 2, True, hm=0.0082),
          Shape("F2wt", "2 flat blocks, span 0.84, 8.0 mm", 2, True, alpha=0.84, hm=0.0080)]


@dataclass
class MagGeometry(Geometry):
    r_seat: float = 0.30935
    r_y_out: float = R_YOKE_OUT

    @property
    def r_m2(self) -> float:          # top of the magnet-capable ring (below the bond line)
        return self.r_seat - BOND

    @property
    def r_ry(self) -> float:
        return self.r_y_out


class MagMesh(Mesh):
    def radial_edges(self):
        g = self.geo
        lay = self.layers
        e = [g.r_in]

        def add(r_to, n):
            e.extend(list(np.linspace(e[-1], r_to, n + 1)[1:]))
        add(g.r_slot_bot, lay["yoke"]); add(g.r_slot_top, lay["slot"])
        add(g.r_s - g.h_tip, lay["wedge"]); add(g.r_s, lay["tip"])
        add(g.r_s + g.g, lay["gap"]); add(g.r_m1, 1)
        n_mag = max(8, int(round((g.r_m2 - g.r_m1) / (0.5e-3 if not QUICK else 1.0e-3))))
        add(g.r_m2, n_mag)
        add(g.r_seat, 1)                         # bond line ring (non-magnetic)
        add(g.r_ry, 6)
        add(g.r_ry + 0.004, 2)
        return e

    def _regions(self):
        super()._regions()
        g = self.geo
        bond = (self.cr > g.r_m2) & (self.cr < g.r_seat)
        self.region[bond] = 7


class MagModel(Model):
    def __init__(self, geo, shape: Shape, n_theta=N_THETA):
        super().__init__(geo, n_theta=n_theta, mesh_cls=MagMesh)
        self.shape = shape
        m = self.mesh
        pts = np.einsum("sk,ekd->esd", m.bary, m.xy[m.mag_el])
        self.pts_r = np.hypot(pts[..., 0], pts[..., 1])
        self.pts_th = np.arctan2(pts[..., 1], pts[..., 0])
        self.phis, self.bw = shape.blocks(geo)
        n_sec = geo.poles // geo.sym
        self.pole_scale = np.ones(n_sec)          # tolerance study: remanence of each pole
        self.pole_shift = np.zeros(n_sec)         # tolerance study: pole centre error [rad]

    def inside(self, r, th_rot):
        """Piece index (0..k-1) or -1 for points given in rotor-frame polar coords; also pole and sign."""
        g = self.geo
        tau = 2 * math.pi / g.poles
        pole = np.floor(th_rot / tau + 0.5)
        pk = pole.astype(int) % len(self.pole_shift)
        dth = th_rot - pole * tau - self.pole_shift[pk]
        idx = np.full(np.shape(r), -1)
        for j, phi in enumerate(self.phis):
            psi = dth - phi
            if self.shape.flat:
                u, v = r * np.sin(psi), r * np.cos(psi)
                ok = (np.abs(u) <= self.bw / 2) & (v >= g.r_m1) & (v <= g.r_m1 + g.hm)
            else:
                ok = (np.abs(psi) <= self.bw / 2) & (r >= g.r_m1) & (r <= g.r_m1 + g.hm)
            idx = np.where(ok, j, idx)
        sign = np.where(np.mod(pole, 2) == 0, 1.0, -1.0) * self.pole_scale[pk]
        return idx, pole, sign

    def magnet_source(self, theta_r: float):
        g = self.geo
        tau = 2 * math.pi / g.poles
        th_rot = self.pts_th - theta_r
        idx, pole, sign = self.inside(self.pts_r, th_rot)
        inside = idx >= 0
        if self.shape.flat:
            phi = np.array(self.phis)[np.maximum(idx, 0)]
            ang = theta_r + pole * tau + phi          # parallel magnetisation along the block centre line
        else:
            ang = self.pts_th                          # radial
        brx = np.where(inside, sign * g.br * np.cos(ang), 0.0).mean(1)
        bry = np.where(inside, sign * g.br * np.sin(ang), 0.0).mean(1)
        self._frac = inside.mean(1)
        return brx, bry, self._frac

    def magnet_field_along_magnetisation(self, A=None):
        """As fem.Model, but only for elements completely inside a magnet: in elements cut by a
        slanted block side the blended source would show a false demagnetising field."""
        m, g = self.mesh, self.geo
        A = self.A if A is None else A
        Bx, By = self.flux_density(A)
        el = m.mag_el
        full = self._frac > 0.999
        brn = np.hypot(self.brx, self.bry)
        ux, uy = self.brx[full] / brn[full], self.bry[full] / brn[full]
        Bpar = Bx[el][full] * ux + By[el][full] * uy
        H = (Bpar - brn[full]) / (MU0 * g.mu_rm)
        return H, m.cr[el][full]

    # net force on one pole of magnets (Maxwell stress on a closed contour in non-magnetic material)
    def pole_force(self, theta_r, pole_index=0):
        m, g = self.mesh, self.geo
        Bx, By = self.flux_density(self.A)
        tau = 2 * math.pi / g.poles
        c_ang = theta_r + pole_index * tau
        r_in, r_out = g.r_s + g.g + 0.25e-3, g.r_seat - BOND / 2
        th = np.linspace(c_ang - tau / 2, c_ang + tau / 2, 400)

        def B_at(r, t):
            tt = np.mod(t, g.sec_angle)
            i = np.searchsorted(m.r, r) - 1
            j = np.floor(tt / (g.sec_angle / m.nt)).astype(int) % m.nt
            # element pair in ring i, column j: take the mean of both triangles
            e0 = (i * m.nt + j) * 2
            bx = (Bx[e0] + Bx[e0 + 1]) / 2
            by = (By[e0] + By[e0 + 1]) / 2
            return bx, by

        def stress(bx, by, nx, ny):
            bn = bx * nx + by * ny
            b2 = bx * bx + by * by
            return (bx * bn - 0.5 * b2 * nx) / MU0, (by * bn - 0.5 * b2 * ny) / MU0

        F = np.zeros(2)
        for r, s in ((r_out, 1), (r_in, -1)):
            bx, by = B_at(r, th)
            nx, ny = s * np.cos(th), s * np.sin(th)
            tx, ty = stress(bx, by, nx, ny)
            dl = r * (th[1] - th[0])
            F += np.array([np.sum(tx) * dl, np.sum(ty) * dl])
        rs = np.linspace(r_in, r_out, 60)
        for t, s in ((c_ang + tau / 2, 1), (c_ang - tau / 2, -1)):
            bx, by = B_at(rs, np.full_like(rs, t))
            nx, ny = s * -math.sin(t), s * math.cos(t)
            tx, ty = stress(bx, by, nx, ny)
            dl = rs[1] - rs[0]
            F += np.array([np.sum(tx) * dl, np.sum(ty) * dl])
        F *= STACK
        er = np.array([math.cos(c_ang), math.sin(c_ang)])
        et = np.array([-math.sin(c_ang), math.cos(c_ang)])
        return float(F @ er), float(F @ et)        # radial (+ = outwards, into the drum), tangential


def fourier(y, n):
    N = len(y)
    c = 2 / N * np.sum(y * np.exp(-2j * math.pi * n * np.arange(N) / N))
    return abs(c), math.atan2(-c.imag, c.real)


def torsion_factor(w, l, terms=40):
    """Eddy loss of a w x l piece relative to the same width in 2D (infinitely long).
    Exact for a uniform alternating field normal to the piece (Prandtl torsion analogy)."""
    a, b = min(w, l), max(w, l)
    s = sum(math.tanh(n * math.pi * b / (2 * a)) / n ** 5 for n in range(1, 2 * terms, 2))
    J = a ** 3 * b / 3 * (1 - 192 / math.pi ** 5 * a / b * s)
    return J / (w ** 3 * l / 3)


# ------------------------------------------------------------------ one variant
def run_variant(shape: Shape, NI_load=None):
    t0 = time.time()
    geo = MagGeometry(br20=1.26, hm=shape.hm, d_slot=0.065, L=STACK, g=0.0020, sleeve=0.0005)
    geo.r_seat = shape.seat_radius(geo)
    M = MagModel(geo, shape)
    m = M.mesh
    p = geo.poles // 2
    el_period = 2 * math.pi / p
    res = dict(key=shape.key, name=shape.name, pieces_per_pole_width=shape.k, flat=shape.flat,
               seat_diameter_mm=round(2 * geo.r_seat * 1e3, 3))
    phis, bw = M.phis, M.bw
    if shape.flat:
        res["block_width_mm"] = round(bw * 1e3, 3)
        sag = (bw / 2) ** 2 / (2 * (geo.r_m1 + geo.hm))
        res["bond_centre_mm"] = round((BOND + sag) * 1e3, 3)
        res["inner_corner_radius_mm"] = round(math.hypot(geo.r_m1, bw / 2) * 1e3, 3)
        area = shape.k * bw * geo.hm
    else:
        res["arc_deg"] = round(math.degrees(bw), 3)
        area = bw / 2 * ((geo.r_m1 + geo.hm) ** 2 - geo.r_m1 ** 2)
    res["magnet_mass_kg"] = round(area * STACK * RHO_MAG * geo.poles, 3)

    # ---- no-load, 36 positions over one electrical period
    th_nl = np.arange(36) * el_period / 36
    psi = []
    for i, th in enumerate(th_nl):
        M.solve(th)
        psi.append(M.flux_linkage_per_turn())
        if i == 0:
            th_g, Br_g = M.gap_flux()
            res["_gap"] = (np.degrees(th_g).tolist()[::4], Br_g.tolist()[::4])
            res["force_no_load_N_per_pole"] = [round(v, 1) for v in M.pole_force(th, 0)]
    psi = np.array(psi)
    psi1, _ = fourier(psi[:, 0], 1)
    deltas = [fourier(psi[:, ph], 1)[1] for ph in range(3)]
    harm = [fourier(psi[:, 0], n)[0] * n for n in range(1, 14)]
    line = psi[:, 0] - psi[:, 1]
    lh = [fourier(line, n)[0] * n for n in range(1, 14)]
    w_e = p * N_RATED * 2 * math.pi / 60
    e_line = math.sqrt(3) * w_e * psi1 / math.sqrt(2) * TURNS
    res["no_load"] = dict(
        psi1_per_turn_Wb=round(psi1, 5),
        line_emf_178rpm_100C_V=round(e_line, 1),
        phase_thd_pct=round(100 * math.sqrt(sum(h * h for h in harm[1:])) / harm[0], 2),
        line_thd_pct=round(100 * math.sqrt(sum(h * h for h in lh[1:])) / lh[0], 2),
        harmonics_pct={str(n + 1): round(100 * h / harm[0], 2) for n, h in enumerate(harm) if n in (2, 4, 6, 10, 12)})
    res["_emf"] = (psi[:, 0] * TURNS).tolist()

    # ---- cogging, 24 positions over 1 deg
    cog_period = 2 * math.pi / 360
    th_c = np.arange(24) * cog_period / 24
    cog = []
    for th in th_c:
        M.solve(th)
        cog.append(M.torque())
    cog = np.array(cog)
    res["cogging_pp_Nm"] = round(float(np.ptp(cog)), 3)
    res["_cog"] = cog.tolist()

    # ---- rated load (Id = 0), current from the baseline unless given
    def currents(theta, NI_pk, axis="q", sgn=1.0):
        out = []
        for ph in range(3):
            a = p * theta - deltas[ph]
            out.append(sgn * NI_pk * (-math.sin(a) if axis == "q" else math.cos(a)))
        return out
    M.solve(0.0, currents(0.0, 900.0))
    sgn = 1.0 if M.torque() > 0 else -1.0
    if NI_load is None:
        NI_a, t_a = 900.0, abs(M.torque())
        NI_b = NI_a * T_SIZING / t_a
        M.solve(0.0, currents(0.0, NI_b, sgn=sgn)); t_b = M.torque()
        NI_load = NI_b + (T_SIZING - t_b) * (NI_b - NI_a) / (t_b - t_a)

    # ---- time stepping over one electrical period (stator field is periodic in 18 deg)
    n_steps = 90 if not QUICK else 45
    dth = el_period / n_steps
    step_nodes = int(round(dth / (geo.sec_angle / m.nt)))
    assert abs(step_nodes * geo.sec_angle / m.nt - dth) < 1e-12
    # material nodes inside the magnets (rotor frame at theta_r = 0)
    ring = np.where((m.r >= geo.r_m1 - 1e-9) & (m.r <= geo.r_m2 + 1e-9))[0]
    th_nodes = np.arange(m.nt) * geo.sec_angle / m.nt
    RR, TT = np.meshgrid(m.r[ring], th_nodes, indexing="ij")
    idx, pole, _ = M.inside(RR, TT)
    piece = np.where(idx >= 0, (pole.astype(int) % (geo.poles // geo.sym)) * shape.k + idx, -1)
    dr = np.gradient(m.r)[ring]
    wgt = (RR * dr[:, None] * (geo.sec_angle / m.nt)) * (idx >= 0)
    A_hist, tq = [], []
    for k in range(n_steps):
        th = k * dth
        M.solve(th, currents(th, NI_load, sgn=sgn))
        tq.append(M.torque())
        A_hist.append(M.A.reshape(m.nr, m.nt)[ring].copy())
    tq = np.array(tq)
    res["load"] = dict(NI_peak_per_side=round(NI_load, 1), mean_torque_Nm=round(float(tq.mean()), 1),
                       ripple_pp_pct=round(float(np.ptp(tq) / tq.mean() * 100), 2),
                       phase_current_rms_A=round(NI_load / math.sqrt(2) / TURNS, 2))
    res["_ripple"] = tq.tolist()
    res["force_load_N_per_pole"] = [round(v, 1) for v in M.pole_force(th, 0)]
    # rotor-frame history over 4 electrical periods (one section turn = periodic for every node)
    n_tot = n_steps * geo.poles // geo.sym // 2        # 4 periods
    A_hist = np.array(A_hist)                          # (n_steps, n_ring, nt)
    jj = np.arange(m.nt)
    A_rot = np.empty((n_tot, len(ring), m.nt))
    for kk in range(n_tot):
        A_rot[kk] = A_hist[kk % n_steps][:, (jj + step_nodes * kk) % m.nt]
    omega = N_RATED * 2 * math.pi / 60
    t_span = geo.sec_angle / omega
    F = np.fft.rfft(A_rot, axis=0)
    freqs = np.fft.rfftfreq(n_tot, d=t_span / n_tot)
    E = -np.fft.irfft(F * (2j * math.pi * freqs)[:, None, None], n=n_tot, axis=0)
    # net-zero current per piece and time step
    loss_2d = 0.0
    pieces = np.unique(piece[piece >= 0])
    for pc in pieces:
        sel = piece == pc
        w = wgt[sel]
        e = E[:, sel]
        e = e - (e @ w / w.sum())[:, None]
        loss_2d += SIGMA_MAG * np.mean((e ** 2) @ w)          # W/m, time average
    loss_2d *= geo.sym                                         # whole machine, per metre of stack
    # spectrum of the rotor-frame field (mean over magnet nodes): dominant frequencies
    spec = np.sqrt(np.mean(np.abs(F[:, idx >= 0]) ** 2, axis=1))
    top = np.argsort(spec[1:])[::-1][:5] + 1
    res["rotor_field_main_freqs_Hz"] = [round(float(freqs[i]), 1) for i in top]
    width = (bw * geo.r_m1 if not shape.flat else bw)
    seg = {}
    for n_ax in (1, 2, 3, 4, 6, 8):
        l = (STACK - (n_ax - 1) * 0.2e-3) / n_ax
        seg[str(n_ax)] = round(loss_2d * STACK * torsion_factor(width, l), 1)
    res["eddy_loss_rated_W"] = dict(width_mm=round(width * 1e3, 2), loss_2d_W=round(loss_2d * STACK, 1),
                                    by_axial_pieces=seg)

    # ---- short-circuit demagnetisation at 120 C (as run_fea.py)
    geo.t_mag = 120.0
    th_d = deltas[0] / p
    M.solve(th_d)
    psi_pm = M.flux_linkage_per_turn()[0] * TURNS
    NI_d = NI_load
    for s_d in (1.0, -1.0):
        M.solve(th_d, currents(th_d, NI_d, axis="d", sgn=s_d))
        psi_d = M.flux_linkage_per_turn()[0] * TURNS
        if abs(psi_d) < abs(psi_pm):
            break
    Ld = abs(psi_pm - psi_d) / (NI_d / TURNS)
    I_sc = abs(psi_pm) / Ld
    M.solve(th_d, currents(th_d, 2 * I_sc * TURNS, axis="d", sgn=s_d))
    H, _ = M.magnet_field_along_magnetisation()
    hcj120 = HCJ20 * (1 + HCJ_TC * 100)
    res["demag_120C"] = dict(Ld_mH=round(Ld * 1e3, 2), transient_peak_A=round(2 * I_sc, 1),
                             min_H_kA_m=round(float(H.min()) / 1e3, 1),
                             H_1pct_kA_m=round(float(np.percentile(H, 1)) / 1e3, 1),
                             margin_pct=round(100 * (1 - abs(float(H.min())) / hcj120), 1))
    geo.t_mag = 100.0
    res["runtime_s"] = round(time.time() - t0)
    print(shape.key, json.dumps({k: v for k, v in res.items() if not k.startswith("_")}), flush=True)
    return res, NI_load


def tolerance_study(key):
    """Cogging sensitivity to pole-to-pole scatter (the 72 deg section repeats the pattern 5 times)."""
    shape = next(s for s in SHAPES if s.key == key)
    geo = MagGeometry(br20=1.26, hm=shape.hm, d_slot=0.065, L=STACK, g=0.0020, sleeve=0.0005)
    geo.r_seat = shape.seat_radius(geo)
    M = MagModel(geo, shape)
    th_c = np.arange(24) * (2 * math.pi / 360) / 24
    rng = np.random.default_rng(7)
    n = len(M.pole_scale)
    deg = math.pi / 180
    cases = {
        "nominal": (np.ones(n), np.zeros(n)),
        "sorted poles, +-0.5 % alternating strong/weak": (1 + 0.005 * np.array([1, -1] * (n // 2)), np.zeros(n)),
        "unsorted, random +-1.5 %": (1 + rng.uniform(-0.015, 0.015, n), np.zeros(n)),
        "one pole 3 % weak": (np.r_[0.97, np.ones(n - 1)], np.zeros(n)),
        "pole centres random +-0.05 deg": (np.ones(n), rng.uniform(-0.05, 0.05, n) * deg),
        "pole centres random +-0.10 deg": (np.ones(n), rng.uniform(-0.10, 0.10, n) * deg),
        "pole centres random +-0.25 deg": (np.ones(n), rng.uniform(-0.25, 0.25, n) * deg),
    }
    out = {}
    for name, (sc, sh) in cases.items():
        M.pole_scale, M.pole_shift = sc, sh
        cog = []
        for th in (np.arange(96) * (2 * math.pi / geo.slots) / 96 if name != "nominal" else th_c):
            M.solve(th)
            cog.append(M.torque())
        out[name] = round(float(np.ptp(cog)), 3)
        print(name, out[name], flush=True)
    suffix = "_quick" if QUICK else ""
    (OUT / f"magnets_tolerance_{key}{suffix}.json").write_text(json.dumps(out, indent=2))


def main():
    if "tol" in sys.argv:
        key = [a for a in sys.argv[1:] if a in {s.key for s in SHAPES}][0]
        return tolerance_study(key)
    only = [a for a in sys.argv[1:] if a in {s.key for s in SHAPES}]
    shapes = [s for s in SHAPES if not only or s.key in only]
    suffix = "_quick" if QUICK else ""
    raw_f, sum_f = OUT / f"magnets_raw{suffix}.json", OUT / f"magnets_summary{suffix}.json"
    old = {r["key"]: r for r in json.loads(raw_f.read_text())} if raw_f.exists() else {}
    NI = None
    if shapes[0].key != "A":     # all variants run at the baseline (arc) current: torque per ampere
        NI = old["A"]["load"]["NI_peak_per_side"] if "A" in old else 895.5
    for s in shapes:
        r, NI_s = run_variant(s, NI)
        NI = NI if NI is not None else NI_s
        cur = {r_["key"]: r_ for r_ in json.loads(raw_f.read_text())} if raw_f.exists() else {}
        cur[s.key] = r
        order = [x.key for x in SHAPES if x.key in cur]
        results = [cur[k] for k in order]
        raw_f.write_text(json.dumps(results))
        sum_f.write_text(json.dumps([{k: v for k, v in r_.items() if not k.startswith("_")} for r_ in results],
                                    indent=2))
    plots([r_ for r_ in results if r_["key"] in ("A", "F1", "F2", "F3")], suffix)


def plots(results, suffix=""):
    cols = {"A": "#d9463b", "F1": "#6b6b6b", "F2": "#2f7ed8", "F3": "#2f9e44", "F2w": "#9c36b5", "F2t": "#f59f00", "F2wt": "#0c8599"}
    fig, ax = plt.subplots(1, 3, figsize=(14, 3.8))
    for r in results:
        c = cols[r["key"]]
        x = np.linspace(0, 360, len(r["_emf"]), endpoint=False)
        e = np.array(r["_emf"]); de = (np.roll(e, -1) - np.roll(e, 1)) / 2 / (2 * math.pi / 20 / len(e))
        ax[0].plot(x, de * N_RATED * 2 * math.pi / 60, c=c, label=r["key"])
        ax[1].plot(np.linspace(0, 1, len(r["_cog"]), endpoint=False), r["_cog"], "o-", c=c, ms=3, label=r["key"])
        ax[2].plot(np.linspace(0, 18, len(r["_ripple"]), endpoint=False), r["_ripple"], c=c, label=r["key"])
    ax[0].set(title="Phase EMF, 178 rpm, 100 °C, 28 turns", xlabel="electrical deg", ylabel="V")
    ax[1].set(title="Cogging torque", xlabel="rotor deg (one period)", ylabel="Nm")
    ax[2].set(title="Torque at rated current", xlabel="rotor deg", ylabel="Nm")
    for a in ax:
        a.grid(alpha=.3); a.legend()
    fig.tight_layout(); fig.savefig(OUT / f"magnets_compare{suffix}.png", dpi=120)


if __name__ == "__main__":
    main()
