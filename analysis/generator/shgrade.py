"""SH-grade feasibility for the production rotor (doc 19 §16).

Rev B layout (2 x 2 blocks 40 x 20 per pole, rows skewed 0.50 deg, block inner
face r 301.5, drum seat fitted to the block) with SH grades at several block
thicknesses. For each case: line EMF at 100 °C with 28 turns (skewed), turns for
380 V, and the demagnetisation margin (worst element against HcJ) for rated
load, steady and 2 x transient short circuit at 60 to 120 °C, plus the highest
magnet temperature at which the transient short circuit keeps 20 % margin.

Run:  python3 shgrade.py N42SH 7.5 8.5 9.5    -> results/shgrade_<grade>_<t>.json
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

from magnets import Shape, MagGeometry, MagModel, fourier, STACK, TURNS, N_RATED

OUT = Path(__file__).parent / "results"
NI_LOAD = 895.5
GRADES = {   # catalogue minimum Br [T], HcJ [kA/m] at 20 °C, coefficients [1/K]
    "N42SH": (1.29, 1592e3, -0.0012, -0.0060),
    "N38SH": (1.22, 1592e3, -0.0012, -0.0060),
    "N45SH": (1.32, 1592e3, -0.0012, -0.0060),
    "N40UH": (1.26, 1990e3, -0.0012, -0.0055),
}
TEMPS = (60.0, 80.0, 100.0, 110.0, 120.0)
SKEW = math.radians(0.50)


def run(grade, t_mm):
    br20, hcj20, a_br, b_hcj = GRADES[grade]
    hm = t_mm / 1e3
    shape = Shape("C", f"{grade} 40x20x{t_mm}", 2, True, hm=hm, b=0.020, n_ax=2, l_ax=0.040)
    geo = MagGeometry(br20=br20, br_tc=a_br, hm=hm, d_slot=0.065, L=STACK, g=0.0020, sleeve=0.0005)
    geo.r_seat = shape.seat_radius(geo)
    M = MagModel(geo, shape)
    p = geo.poles // 2
    el = 2 * math.pi / p
    w_e = p * N_RATED * 2 * math.pi / 60
    skf = abs(np.mean([np.exp(1j * p * o) for o in (0.0, SKEW)]))
    out = dict(grade=grade, thickness_mm=t_mm, seat_d_mm=round(2e3 * geo.r_seat, 2),
               magnet_kg=round(160 * 0.02 * 0.04 * hm * 7600, 2))
    geo.t_mag = 100.0
    psi = []
    for t in np.arange(18) * el / 18:
        M.solve(t)
        psi.append(M.flux_linkage_per_turn())
    psi = np.array(psi)
    psi1, _ = fourier(psi[:, 0], 1)
    deltas = [fourier(psi[:, k], 1)[1] for k in range(3)]
    e = math.sqrt(3) * w_e * psi1 / math.sqrt(2) * TURNS * skf
    out["line_emf_100C_V"] = round(e, 1)
    out["turns_for_380V"] = round(TURNS * 380 / e, 1)

    def currents(theta, NI, axis, sgn=1.0):
        return [sgn * NI * (-math.sin(p * theta - d) if axis == "q" else math.cos(p * theta - d)) for d in deltas]

    M.solve(0.0, currents(0.0, NI_LOAD, "q"))
    sgn = 1.0 if M.torque() > 0 else -1.0
    th_d = deltas[0] / p
    demag = {}
    for T in TEMPS:
        geo.t_mag = T
        hcj = hcj20 * (1 + b_hcj * (T - 20))
        M.solve(th_d)
        psi_pm = M.flux_linkage_per_turn()[0] * TURNS
        for s_d in (1.0, -1.0):
            M.solve(th_d, currents(th_d, NI_LOAD, "d", s_d))
            psi_d = M.flux_linkage_per_turn()[0] * TURNS
            if abs(psi_d) < abs(psi_pm):
                break
        Ld = abs(psi_pm - psi_d) / (NI_LOAD / TURNS)
        I_sc = abs(psi_pm) / Ld
        row = dict(HcJ_kA_m=round(hcj / 1e3))
        for name, NI, ax, sg in (("rated", NI_LOAD, "q", sgn), ("steady_sc", I_sc * TURNS, "d", s_d),
                                 ("transient_sc", 2 * I_sc * TURNS, "d", s_d)):
            th = th_d if ax == "d" else 0.0
            M.solve(th, currents(th, NI, ax, sg))
            H, _ = M.magnet_field_along_magnetisation()
            row[name] = round(100 * (1 - abs(float(H.min())) / hcj), 1)
        demag[f"{int(T)}C"] = row
        print(grade, t_mm, T, json.dumps(row), flush=True)
    out["demag_margin_pct"] = demag
    # highest temperature with 20 % margin in the transient short circuit (linear between temperatures)
    tr = [(T, demag[f"{int(T)}C"]["transient_sc"]) for T in TEMPS]
    t20 = None
    for (t0, m0), (t1, m1) in zip(tr, tr[1:]):
        if m0 >= 20 > m1:
            t20 = t0 + (m0 - 20) * (t1 - t0) / (m0 - m1)
    if t20 is None:
        t20 = TEMPS[-1] if tr[-1][1] >= 20 else (TEMPS[0] if tr[0][1] < 20 else None)
    out["max_temp_transient_sc_20pct_C"] = round(t20, 0) if t20 else None
    (OUT / f"shgrade_{grade}_{t_mm}.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out), flush=True)


if __name__ == "__main__":
    g = sys.argv[1]
    for t in sys.argv[2:]:
        run(g, float(t))
