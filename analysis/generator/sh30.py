"""Study for doc 19 §15: N42SH blocks 30 x 15 x 6 mm (Martin, 2026-11-05).

Layouts on the Rev B rotor (stack 74, 40 poles / 45 slots, sleeve bore Ø602,
block inner face r 301.5, drum seat fitted to the block):

  S1  1 block across (30 wide) x 5 along (15 long)  -> 75.8 mm rows, span 0.63
  S3  3 blocks across (15 wide) x 3 along (30 long) -> 90.4 mm rows, span 0.96
  S1d as S1 with two blocks stacked (12 mm magnet), 400 pieces

(2 across x 15 wide gives the same span as S1 with more pieces and 90.4 mm
rows, so it is not run separately.) For each: line EMF at 60 and 100 °C with
28 turns and the rows step-skewed by 1/n of the 1° cogging period, the turns
needed for 380 V, cogging with and without skew, torque at the doc 06 sizing
current, and the demagnetising field at 60 to 120 °C for rated load, steady
and 2x transient short circuit against N42SH's HcJ.

Run:  python3 sh30.py S1  /  python3 sh30.py S3   -> results/sh30_<key>.json
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

from magnets import Shape, MagGeometry, MagModel, fourier, shift_avg, STACK, TURNS, N_RATED

OUT = Path(__file__).parent / "results"
NI_LOAD = 895.5
N42SH = dict(br20=1.29, hcj20=1592e3, a_br=-0.0012, b_hcj=-0.0060)
SHAPES = {"S1": Shape("S1", "N42SH 30x15x6: 1 across x 5 along", 1, True, hm=0.006, b=0.030, n_ax=5, l_ax=0.015),
          "S3": Shape("S3", "N42SH 30x15x6: 3 across x 3 along", 3, True, hm=0.006, b=0.015, n_ax=3, l_ax=0.030),
          # two blocks stacked (bonded N face to S face) = one 12 mm magnet
          "S1d": Shape("S1d", "N42SH 30x15x6 x2 stacked: 1 across x 5 along x 2 high", 1, True, hm=0.012, b=0.030,
                       n_ax=5, l_ax=0.015)}


def main(key):
    shape = SHAPES[key]
    geo = MagGeometry(br20=N42SH["br20"], br_tc=N42SH["a_br"], hm=shape.hm, d_slot=0.065, L=STACK, g=0.0020,
                      sleeve=0.0005)
    geo.r_seat = shape.seat_radius(geo)
    M = MagModel(geo, shape)
    p = geo.poles // 2
    el = 2 * math.pi / p
    w_e = p * N_RATED * 2 * math.pi / 60
    per = 2 * math.pi / 360
    offs = [i / shape.n_ax * per for i in range(shape.n_ax)]
    skf = abs(np.mean([np.exp(1j * p * o) for o in offs]))
    phis, bw = shape.blocks(geo)
    span = (phis[-1] - phis[0]) + 2 * math.atan(bw / 2 / geo.r_m1)
    rows = shape.n_ax * shape.l_ax + (shape.n_ax - 1) * 0.0002
    out = dict(key=key, name=shape.name, seat_d_mm=round(2e3 * geo.r_seat, 2),
               span_alpha=round(span / (2 * math.pi / geo.poles), 3), rows_mm=round(rows * 1e3, 1),
               pieces=geo.poles * shape.k * shape.n_ax * round(shape.hm / 0.006),
               magnet_kg=round(geo.poles * shape.k * shape.n_ax * bw * shape.l_ax * shape.hm * 7600, 2),
               skew_step_deg=round(math.degrees(per / shape.n_ax), 3), skew_emf_factor=round(skf, 4))
    deltas = None
    for T in (60.0, 100.0):
        geo.t_mag = T
        psi = []
        for t in np.arange(18) * el / 18:
            M.solve(t)
            psi.append(M.flux_linkage_per_turn())
        psi = np.array(psi)
        psi1, _ = fourier(psi[:, 0], 1)
        if deltas is None:
            deltas = [fourier(psi[:, k], 1)[1] for k in range(3)]
        out[f"line_emf_{int(T)}C_V"] = round(math.sqrt(3) * w_e * psi1 / math.sqrt(2) * TURNS * skf, 1)
        print(key, T, out[f"line_emf_{int(T)}C_V"], flush=True)
    out["turns_for_380V_100C"] = round(TURNS * 380 / out["line_emf_100C_V"], 1)

    def currents(theta, NI, axis, sgn=1.0):
        return [sgn * NI * (-math.sin(p * theta - d) if axis == "q" else math.cos(p * theta - d)) for d in deltas]

    geo.t_mag = 60.0
    cog = []
    for t in np.arange(24) * per / 24:
        M.solve(t)
        cog.append(M.torque())
    out["cogging_pp_Nm"] = round(float(np.ptp(cog)), 2)
    out["cogging_skewed_pp_Nm"] = round(float(np.ptp(shift_avg(cog, per, offs))), 2)
    geo.t_mag = 100.0
    M.solve(0.0, currents(0.0, NI_LOAD, "q"))
    sgn = 1.0 if M.torque() > 0 else -1.0
    tq = []
    for t in np.arange(6) * (2 * math.pi / geo.slots) / 6:
        M.solve(t, currents(t, NI_LOAD, "q", sgn))
        tq.append(M.torque())
    out["torque_at_sizing_current_100C_Nm"] = round(float(np.mean(tq)) * skf, 1)

    th_d = deltas[0] / p
    demag = {}
    for T in (60.0, 80.0, 100.0, 120.0):
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
        row = dict(HcJ_kA_m=round(hcj / 1e3), I_sc_A_peak=round(I_sc, 1))
        for name, NI, ax, sg in (("rated_load_q", NI_LOAD, "q", sgn), ("steady_sc_d", I_sc * TURNS, "d", s_d),
                                 ("transient_sc_d", 2 * I_sc * TURNS, "d", s_d)):
            th = th_d if ax == "d" else 0.0
            M.solve(th, currents(th, NI, ax, sg))
            H, _ = M.magnet_field_along_magnetisation()
            row[name] = round(100 * (1 - abs(float(H.min())) / hcj), 1)
        demag[f"{int(T)}C"] = row
        print(key, T, json.dumps(row), flush=True)
    out["demag_margin_pct"] = demag
    (OUT / f"sh30_{key}.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out), flush=True)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "S1")
