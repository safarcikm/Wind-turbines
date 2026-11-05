"""Prototype magnet check (doc 19 §14): plain N42 blocks 40 x 20 x 5 mm in the
Rev B rotor (seat Ø618.65 made for 7.5 mm blocks), the missing 2.5 mm filled
behind each block with a filler plate. Two fillers:

  resin   G11 / epoxy plate (non-magnetic, mu_r 1)
  steel   mild steel plate (mu_r ~1000, linear: it runs far below saturation)

The block's inner face stays at r 301.5 (the sleeve and air gap are unchanged),
so the filler sits between the block's back and the drum seat.

For each: line EMF at 20 and 60 °C (28 turns, 178 rpm, rows skewed 0.50°),
cogging with and without skew, torque at the doc 06 sizing current, and the
demagnetising field for rated load, steady short circuit and the 2 x transient
short circuit at 20 to 80 °C against plain N42's HcJ. Also the largest d-axis
current the magnets survive with 20 % margin.

Run:  python3 proto.py resin   /   python3 proto.py steel   (~10 min each)
      -> results/proto_<filler>.json
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

from magnets import Shape, MagGeometry, MagModel, fourier, shift_avg, STACK, TURNS, N_RATED

OUT = Path(__file__).parent / "results"
NI_LOAD = 895.5             # doc 06 sizing current, peak ampere-turns per coil side (22.6 A rms)
SEAT_R = 0.309325           # Rev B drum seat Ø618.65
HM = 0.005
FILL = 0.0025
# plain N42 (no temperature suffix), catalogue minimum values, typical coefficients
N42 = dict(br20=1.28, hcj20=955e3, a_br=-0.0012, b_hcj=-0.0062, t_max=80.0)
SKEW = math.radians(0.50)


def build(filler):
    shape = Shape("P5", "N42 40x20x5 + 2.5 filler", 2, True, hm=HM, b=0.020, n_ax=2, l_ax=0.040)
    geo = MagGeometry(br20=N42["br20"], br_tc=N42["a_br"], hm=HM, d_slot=0.065, L=STACK, g=0.0020,
                      sleeve=0.0005)
    geo.r_seat = SEAT_R
    M = MagModel(geo, shape)
    M.fill_h = FILL
    M.fill_mu = 1000.0 if filler == "steel" else 1.0
    return geo, M


def main(filler):
    geo, M = build(filler)
    p = geo.poles // 2
    el = 2 * math.pi / p
    w_e = p * N_RATED * 2 * math.pi / 60
    skf = abs(np.mean([np.exp(1j * p * o) for o in (0.0, SKEW)]))
    out = dict(filler=filler, block="N42 40 x 20 x 5", fill_mm=FILL * 1e3)

    # EMF at 20 and 60 C
    deltas = None
    for T in (20.0, 60.0):
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
        print(filler, T, out[f"line_emf_{int(T)}C_V"], flush=True)

    def currents(theta, NI, axis, sgn=1.0):
        return [sgn * NI * (-math.sin(p * theta - d) if axis == "q" else math.cos(p * theta - d)) for d in deltas]

    # cogging at 20 C (worst: strongest magnets)
    geo.t_mag = 20.0
    per = 2 * math.pi / 360
    cog = []
    for t in np.arange(24) * per / 24:
        M.solve(t)
        cog.append(M.torque())
    out["cogging_pp_Nm"] = round(float(np.ptp(cog)), 2)
    out["cogging_skewed_pp_Nm"] = round(float(np.ptp(shift_avg(cog, per, [0.0, SKEW]))), 2)

    # torque at the sizing current, 60 C, mean of 6 positions over one slot pitch
    geo.t_mag = 60.0
    M.solve(0.0, currents(0.0, NI_LOAD, "q"))
    sgn = 1.0 if M.torque() > 0 else -1.0
    tq = []
    for t in np.arange(6) * (2 * math.pi / geo.slots) / 6:
        M.solve(t, currents(t, NI_LOAD, "q", sgn))
        tq.append(M.torque())
    out["torque_at_sizing_current_60C_Nm"] = round(float(np.mean(tq)) * skf, 1)

    # demagnetisation
    th_d = deltas[0] / p
    demag = {}
    for T in (20.0, 40.0, 60.0, 80.0):
        geo.t_mag = T
        hcj = N42["hcj20"] * (1 + N42["b_hcj"] * (T - 20))
        M.solve(th_d)
        psi_pm = M.flux_linkage_per_turn()[0] * TURNS
        H0, _ = M.magnet_field_along_magnetisation()
        for s_d in (1.0, -1.0):
            M.solve(th_d, currents(th_d, NI_LOAD, "d", s_d))
            psi_d = M.flux_linkage_per_turn()[0] * TURNS
            if abs(psi_d) < abs(psi_pm):
                break
        Ld = abs(psi_pm - psi_d) / (NI_LOAD / TURNS)
        I_sc = abs(psi_pm) / Ld
        row = dict(HcJ_kA_m=round(hcj / 1e3), Ld_mH=round(Ld * 1e3, 2), I_sc_A_peak=round(I_sc, 1))
        cases = (("rated_load_q", NI_LOAD, "q", sgn), ("steady_sc_d", I_sc * TURNS, "d", s_d),
                 ("transient_sc_d", 2 * I_sc * TURNS, "d", s_d))
        h_ss = None
        for name, NI, ax, sg in cases:
            M.solve(th_d if ax == "d" else 0.0, currents(th_d if ax == "d" else 0.0, NI, ax, sg))
            H, _ = M.magnet_field_along_magnetisation()
            hmin = float(H.min())
            row[name] = dict(Hmin_kA_m=round(hmin / 1e3, 1), margin_pct=round(100 * (1 - abs(hmin) / hcj), 1))
            if name == "steady_sc_d":
                h_ss = hmin
        # largest d-axis current with 20 % margin (H linear in current between 0 and I_sc)
        h0 = float(H0.min())
        slope = (h_ss - h0) / I_sc
        i_max = (-0.8 * hcj - h0) / slope
        row["max_d_current_20pct_margin_A_peak"] = round(i_max, 1)
        row["max_d_current_20pct_margin_x_Isc"] = round(i_max / I_sc, 2)
        demag[f"{int(T)}C"] = row
        print(filler, T, json.dumps(row), flush=True)
    out["demag"] = demag
    (OUT / f"proto_{filler}.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out), flush=True)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "steel")
