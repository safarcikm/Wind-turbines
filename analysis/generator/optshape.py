"""Best magnet shape for N42SH (doc 21): blocks of any size and fully custom shapes.

Same machine and model as magnets.py / sh30.py (40 poles / 45 slots, stack 74,
sleeve bore r 301.0, magnet face r 301.5 at the pole centre, bond 0.15 mm).

Families
  B   flat rectangular block, parallel magnetised, one per pole across
      (custom size: width from the pole span alpha, thickness hm), on a round seat
  AR  arc segment, radially magnetised, back face on the round seat
  AP  arc segment, parallel magnetised
  L   loaf: back face an arc on the seat, gap face lifted towards the edges by
      `edge` (lift = edge * (2 psi / span)^2, a ground cylinder in practice),
      parallel magnetised

For each case: line EMF at 100 °C with 28 turns (not skewed and with 4 rows
skewed 0.25°), phase THD, cogging (60 °C) not skewed and skewed, and the
demagnetisation margin (worst element against N42SH catalogue HcJ) for rated
load, steady and 2 x transient short circuit at 100 and 120 °C, from which the
temperature that keeps 20 % in the transient short circuit is interpolated.

Run:  python3 optshape.py <key> [<key> ...]   -> results/opt_<key>.json
      python3 optshape.py table              -> results/opt_summary.json
"""
from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from magnets import (Shape, MagGeometry, MagModel, fourier, shift_avg, STACK, TURNS, N_RATED, BOND,
                     RHO_MAG)

OUT = Path(__file__).parent / "results"
NI_LOAD = 895.5
N42SH = dict(br20=1.29, hcj20=1592e3, a_br=-0.0012, b_hcj=-0.0060)
N_SKEW = 4                       # rows for the skewed figures (0.25° steps)


@dataclass
class Custom(Shape):
    profile: str = "arc"         # arc | loaf
    mag: str = "radial"          # radial | parallel
    edge: float = 0.0            # loaf: lift of the gap face at the pole edges [m]


class CustomModel(MagModel):
    def inside(self, r, th_rot):
        g, s = self.geo, self.shape
        tau = 2 * math.pi / g.poles
        pole = np.floor(th_rot / tau + 0.5)
        pk = pole.astype(int) % len(self.pole_shift)
        dth = th_rot - pole * tau - self.pole_shift[pk]
        half = s.alpha * tau / 2
        r_front = g.r_m1 + (s.edge * (dth / half) ** 2 if s.profile == "loaf" else 0.0)
        ok = (np.abs(dth) <= half) & (r >= r_front) & (r <= g.r_m1 + g.hm)
        idx = np.where(ok, 0, -1)
        sign = np.where(np.mod(pole, 2) == 0, 1.0, -1.0) * self.pole_scale[pk]
        return idx, pole, sign

    def magnet_source(self, theta_r):
        g = self.geo
        tau = 2 * math.pi / g.poles
        th_rot = self.pts_th - theta_r
        idx, pole, sign = self.inside(self.pts_r, th_rot)
        inside = idx >= 0
        ang = self.pts_th if self.shape.mag == "radial" else theta_r + pole * tau
        brx = np.where(inside, sign * g.br * np.cos(ang), 0.0).mean(1)
        bry = np.where(inside, sign * g.br * np.sin(ang), 0.0).mean(1)
        self._frac = inside.mean(1)
        return brx, bry, self._frac


def cases():
    c = {}
    for a in (0.63, 0.72, 0.80):
        for h in (9, 11, 13):
            c[f"B{int(a * 100)}_{h}"] = Shape(f"B{int(a * 100)}_{h}", f"block span {a}, {h} mm", 1, True, alpha=a,
                                               hm=h / 1e3, n_ax=5)
    for a in (0.72, 0.80):
        for h in (9, 11):
            c[f"AR{int(a * 100)}_{h}"] = Custom(f"AR{int(a * 100)}_{h}", f"arc radial span {a}, {h} mm", 1, False,
                                                 alpha=a, hm=h / 1e3, n_ax=5)
    c["AP80_10"] = Custom("AP80_10", "arc parallel span 0.80, 10 mm", 1, False, alpha=0.80, hm=0.010, n_ax=5,
                          mag="parallel")
    for h in (10, 12):
        for e in (2, 4):
            c[f"L80_{h}_{e}"] = Custom(f"L80_{h}_{e}", f"loaf span 0.80, {h} mm, edge lift {e}", 1, False,
                                       alpha=0.80, hm=h / 1e3, n_ax=5, profile="loaf", mag="parallel", edge=e / 1e3)
    c["L90_11_4"] = Custom("L90_11_4", "loaf span 0.90, 11 mm, edge lift 4", 1, False, alpha=0.90, hm=0.011,
                           n_ax=5, profile="loaf", mag="parallel", edge=0.004)
    # second round, around the best of the first: span 0.68 to 0.72, parallel arc at narrower spans
    for a, h in ((0.68, 11), (0.70, 11), (0.70, 12)):
        c[f"B{int(a * 100)}_{h}"] = Shape(f"B{int(a * 100)}_{h}", f"block span {a}, {h} mm", 1, True, alpha=a,
                                           hm=h / 1e3, n_ax=5)
    for a, h in ((0.63, 12), (0.68, 11), (0.72, 11)):
        c[f"AP{int(a * 100)}_{h}"] = Custom(f"AP{int(a * 100)}_{h}", f"arc parallel span {a}, {h} mm", 1, False,
                                             alpha=a, hm=h / 1e3, n_ax=5, mag="parallel")
    c["S1d"] = Shape("S1d", "30x15x6 x2 stacked (doc 20)", 1, True, hm=0.012, b=0.030, n_ax=5, l_ax=0.015)
    return c


def area(shape, geo):
    """Magnet cross-section [m2] per pole."""
    tau = 2 * math.pi / geo.poles
    if shape.flat:
        _, b = shape.blocks(geo)
        return b * shape.hm
    half = shape.alpha * tau / 2
    th = np.linspace(-half, half, 2001)
    r0 = geo.r_m1 + (shape.edge * (th / half) ** 2 if getattr(shape, "profile", "") == "loaf" else 0.0 * th)
    r1 = geo.r_m1 + shape.hm
    return float(np.trapezoid((r1 ** 2 - r0 ** 2) / 2, th))


def run(key):
    shape = cases()[key]
    geo = MagGeometry(br20=N42SH["br20"], br_tc=N42SH["a_br"], hm=shape.hm, d_slot=0.065, L=STACK, g=0.0020,
                      sleeve=0.0005)
    geo.r_seat = shape.seat_radius(geo)
    M = (CustomModel if isinstance(shape, Custom) else MagModel)(geo, shape)
    p = geo.poles // 2
    el = 2 * math.pi / p
    w_e = p * N_RATED * 2 * math.pi / 60
    per = 2 * math.pi / 360
    offs = [i / N_SKEW * per for i in range(N_SKEW)]
    skf = abs(np.mean([np.exp(1j * p * o) for o in offs]))
    A = area(shape, geo)
    l_mag = shape.n_ax * shape.l_ax if shape.l_ax else STACK
    out = dict(key=key, name=shape.name, hm_mm=shape.hm * 1e3, seat_d_mm=round(2e3 * geo.r_seat, 2),
               yoke_mm=round(323.0 - 1e3 * geo.r_seat, 2), magnet_kg=round(geo.poles * A * l_mag * RHO_MAG, 2))
    if shape.flat:
        _, b = shape.blocks(geo)
        out["width_mm"] = round(b * 1e3, 2)
        out["alpha"] = round(2 * math.atan(b / 2 / geo.r_m1) / (2 * math.pi / geo.poles), 3)
    else:
        out["width_mm"] = round(2 * geo.r_m1 * math.sin(shape.alpha * math.pi / geo.poles) * 1e3, 2)
        out["alpha"] = shape.alpha
    geo.t_mag = 100.0
    psi = []
    for t in np.arange(18) * el / 18:
        M.solve(t)
        psi.append(M.flux_linkage_per_turn())
    psi = np.array(psi)
    psi1, _ = fourier(psi[:, 0], 1)
    h = [fourier(psi[:, 0], n)[0] * n for n in (3, 5, 7)]
    deltas = [fourier(psi[:, k], 1)[1] for k in range(3)]
    e = math.sqrt(3) * w_e * psi1 / math.sqrt(2) * TURNS
    out["line_emf_100C_V"] = round(e, 1)
    out["line_emf_100C_skewed_V"] = round(e * skf, 1)
    out["phase_thd_pct"] = round(100 * math.sqrt(sum(x * x for x in h)) / psi1, 2)
    out["turns_for_380V"] = round(TURNS * 380 / (e * skf), 1)
    out["copper_loss_vs_revB"] = round((380.0 / (e * skf)) ** 2, 3)
    print(key, json.dumps(out), flush=True)

    geo.t_mag = 60.0
    cog = []
    for t in np.arange(12) * per / 12:
        M.solve(t)
        cog.append(M.torque())
    out["cogging_pp_Nm"] = round(float(np.ptp(cog)), 2)
    out["cogging_skewed_pp_Nm"] = round(float(np.ptp(shift_avg(cog, per, offs))), 2)

    def currents(theta, NI, axis, sgn=1.0):
        return [sgn * NI * (-math.sin(p * theta - d) if axis == "q" else math.cos(p * theta - d)) for d in deltas]

    geo.t_mag = 100.0
    M.solve(0.0, currents(0.0, NI_LOAD, "q"))
    sgn = 1.0 if M.torque() > 0 else -1.0
    th_d = deltas[0] / p
    demag = {}
    for T in (100.0, 120.0):
        geo.t_mag = T
        hcj = N42SH["hcj20"] * (1 + N42SH["b_hcj"] * (T - 20))
        M.solve(th_d)
        psi_pm = M.flux_linkage_per_turn()[0] * TURNS
        for s_d in (1.0, -1.0):
            M.solve(th_d, currents(th_d, NI_LOAD, "d", s_d))
            psi_d = M.flux_linkage_per_turn()[0] * TURNS
            if abs(psi_d) < abs(psi_pm):
                break
        Ld = abs(psi_pm - psi_d) / (NI_LOAD / TURNS)
        I_sc = abs(psi_pm) / Ld
        row = {}
        for name, NI, ax, sg in (("rated", NI_LOAD, "q", sgn), ("steady_sc", I_sc * TURNS, "d", s_d),
                                 ("transient_sc", 2 * I_sc * TURNS, "d", s_d)):
            th = th_d if ax == "d" else 0.0
            M.solve(th, currents(th, NI, ax, sg))
            H, _ = M.magnet_field_along_magnetisation()
            row[name] = round(100 * (1 - abs(float(H.min())) / hcj), 1)
        demag[f"{int(T)}C"] = row
    out["demag_margin_pct"] = demag
    m100, m120 = demag["100C"]["transient_sc"], demag["120C"]["transient_sc"]
    out["t20_C"] = round(100 + 20 * (m100 - 20) / (m100 - m120), 0)
    (OUT / f"opt_{key}.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out), flush=True)


def table():
    rows = []
    for k in cases():
        f = OUT / f"opt_{k}.json"
        if f.exists():
            rows.append(json.loads(f.read_text()))
    (OUT / "opt_summary.json").write_text(json.dumps(rows, indent=1))
    for r in rows:
        print(f"{r['key']:10s} a{r['alpha']:.2f} h{r['hm_mm']:4.1f} {r['magnet_kg']:5.2f}kg "
              f"E{r['line_emf_100C_skewed_V']:6.1f} THD{r['phase_thd_pct']:5.1f} cog{r['cogging_pp_Nm']:5.2f}/"
              f"{r['cogging_skewed_pp_Nm']:4.2f} m100 {r['demag_margin_pct']['100C']['transient_sc']:5.1f} "
              f"m120 {r['demag_margin_pct']['120C']['transient_sc']:5.1f} T20 {r['t20_C']} seat {r['seat_d_mm']}")


if __name__ == "__main__":
    if sys.argv[1] == "table":
        table()
    else:
        for k in sys.argv[1:]:
            run(k)
