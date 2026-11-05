"""Magnet grade assessment for doc 19 §12: the final flat-block geometry (F2t,
2 x 2 blocks per pole, 8.20 mm) run with the catalogue minimum values of each
candidate grade.

For each grade: no-load line EMF at 178 rpm with magnets at 100 °C (28 turns),
and the worst-case transient short circuit (2 x steady short-circuit current on
the d axis, as docs 06 and 19) at 120 °C and 150 °C magnet temperature, giving
the margin between the worst demagnetising field in the magnet and the grade's
intrinsic coercivity HcJ at that temperature. Also the block thickness that
would give the 380 V target with that grade.

Run:  python3 grades.py   (~10 min)  -> results/grades_summary.json
      python3 grades.py C2t N40UH N40EH   (one shape, some grades) -> results/grades_summary_C2t.json
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

from magnets import SHAPES, MagGeometry, MagModel, fourier, STACK, TURNS, N_RATED

OUT = Path(__file__).parent / "results"
NI_LOAD = 895.5          # peak ampere-turns per coil side at the doc 06 sizing current (magnets.py, arc case)
E_TARGET = 380.0
DEDH = 10.6              # V per mm of block thickness near 8.2 mm (F2 7.7 -> F2t 8.2 in magnets.py)

# Catalogue minimum values (GB/T 13560 / maker data sheets), temperature coefficients typical
# br20 [T], hcj20 [kA/m], alpha_Br [%/K], beta_HcJ [%/K], heavy rare earth class, density
GRADES = [
    # key,        Br,   HcJ,  aBr,    bHcJ,  family
    ("N42SH",     1.29, 1592, -0.12, -0.60, "NdFeB SH"),
    ("N48SH",     1.37, 1592, -0.12, -0.60, "NdFeB SH"),
    ("N38UH",     1.22, 1990, -0.12, -0.55, "NdFeB UH"),
    ("N40UH",     1.26, 1990, -0.12, -0.55, "NdFeB UH"),
    ("N42UH",     1.28, 1990, -0.12, -0.55, "NdFeB UH"),
    ("N45UH",     1.32, 1990, -0.11, -0.53, "NdFeB UH (GBD)"),
    ("N38EH",     1.22, 2388, -0.11, -0.50, "NdFeB EH"),
    ("N40EH",     1.25, 2388, -0.11, -0.50, "NdFeB EH (GBD)"),
    ("N35AH",     1.17, 2786, -0.11, -0.47, "NdFeB AH"),
    ("SmCo 30H",  1.08, 1990, -0.035, -0.20, "Sm2Co17"),
]


SHAPE = next((a for a in sys.argv[1:] if a in {s.key for s in SHAPES}), "F2t")
ONLY = [a for a in sys.argv[1:] if a in {g[0] for g in GRADES}]


def run_grade(key, br20, hcj20, a_br, b_hcj):
    shape = next(s for s in SHAPES if s.key == SHAPE)
    geo = MagGeometry(br20=br20, br_tc=a_br / 100, hm=shape.hm, d_slot=0.065, L=STACK, g=0.0020,
                      sleeve=0.0005)
    geo.mu_rm = 1.05 if not key.startswith("SmCo") else 1.03
    geo.r_seat = shape.seat_radius(geo)
    M = MagModel(geo, shape)
    p = geo.poles // 2
    el = 2 * math.pi / p
    th = np.arange(18) * el / 18
    geo.t_mag = 100.0
    psi = []
    for t in th:
        M.solve(t)
        psi.append(M.flux_linkage_per_turn())
    psi = np.array(psi)
    psi1, _ = fourier(psi[:, 0], 1)
    deltas = [fourier(psi[:, k], 1)[1] for k in range(3)]
    w_e = p * N_RATED * 2 * math.pi / 60
    e_line = math.sqrt(3) * w_e * psi1 / math.sqrt(2) * TURNS

    def currents(theta, NI, axis, sgn):
        return [sgn * NI * (-math.sin(p * theta - d) if axis == "q" else math.cos(p * theta - d)) for d in deltas]

    out = dict(grade=key, br20=br20, hcj20_kA_m=hcj20, line_emf_V=round(e_line, 1),
               thickness_for_380V_mm=round(shape.hm * 1e3 + (E_TARGET - e_line) / DEDH * (1.26 / br20), 2))
    for T in (120.0, 150.0):
        geo.t_mag = T
        th_d = deltas[0] / p
        M.solve(th_d)
        psi_pm = M.flux_linkage_per_turn()[0] * TURNS
        for s_d in (1.0, -1.0):
            M.solve(th_d, currents(th_d, NI_LOAD, "d", s_d))
            psi_d = M.flux_linkage_per_turn()[0] * TURNS
            if abs(psi_d) < abs(psi_pm):
                break
        Ld = abs(psi_pm - psi_d) / (NI_LOAD / TURNS)
        I_sc = abs(psi_pm) / Ld
        M.solve(th_d, currents(th_d, 2 * I_sc * TURNS, "d", s_d))
        H, _ = M.magnet_field_along_magnetisation()
        hcj_T = hcj20 * (1 + b_hcj / 100 * (T - 20))
        out[f"Hmin_{int(T)}C_kA_m"] = round(float(H.min()) / 1e3, 1)
        out[f"HcJ_{int(T)}C_kA_m"] = round(hcj_T, 1)
        out[f"margin_{int(T)}C_pct"] = round(100 * (1 - abs(float(H.min())) / 1e3 / hcj_T), 1)
    print(json.dumps(out), flush=True)
    return out


def main():
    grades = [g for g in GRADES if not ONLY or g[0] in ONLY]
    res = [run_grade(k, br, hcj, a, b) for k, br, hcj, a, b, _ in grades]
    for r, g in zip(res, grades):
        r["family"] = g[5]
    suffix = "" if SHAPE == "F2t" else f"_{SHAPE}"
    (OUT / f"grades_summary{suffix}.json").write_text(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
