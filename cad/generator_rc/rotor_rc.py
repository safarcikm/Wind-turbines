"""Rotor magnet geometry, generator Rev C (doc 23): one solid N45SH block 30 x 15 x 12.

Each pole: one block across (30 wide, magnetised through 12), five along the
stack (15 long). 5 blocks per pole, 200 per generator. The five rows are
step-skewed 0.20 deg apart (0.80 deg in all), which cancels the cogging of the
0.63 pole span. Same layout as the doc 20 bonded pair, now one solid block.

Same coordinates as magnet_geom.py: r from the generator axis, x along the
spindle (stack x 343 to 417).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "nacelle_p1"))
import geometry as G  # noqa: E402

GEN = G.GEN
POLES = GEN["poles"]
TAU = 360.0 / POLES
K = 1                               # blocks across per pole
N_AX = 5                            # rows along the stack
N_STACK = 1                         # one solid block (Rev C)
W, L, T = 30.00, 15.00, 12.00       # block: across, along, thickness (magnetised through T)
H = N_STACK * T                     # 12.0 magnet height
BOND = 0.15
SHIM = 0.20
STACK = GEN["stack"]
X_STACK = G.X_STACK
R_STATOR = GEN["r_s"]
R_SLEEVE_BORE = R_STATOR + GEN["gap"]          # 301.0
R_IN_NOM = 301.5
SEAT_D = G.SEAT_D                               # 628.05, from geometry.py (Rev B 618.65)
R_SEAT = SEAT_D / 2
R_CORNER = R_SEAT - BOND
R_IN = math.sqrt(R_CORNER ** 2 - (W / 2) ** 2) - H
R_BACK = R_IN + H
BOND_MID = BOND + R_CORNER - R_BACK
SPAN = math.degrees(2 * math.atan(W / 2 / R_IN))  # 5.70 deg
SKEW_STEP = 1.0 / N_AX                          # 0.20 deg between neighbouring rows
ROW_SHIFT = [(i - (N_AX - 1) / 2) * SKEW_STEP for i in range(N_AX)]   # -0.4 ... +0.4 deg, front to rear
ROWS_LEN = N_AX * L + (N_AX - 1) * SHIM         # 75.8
X_MID = (X_STACK[0] + X_STACK[1]) / 2
X_BLOCKS = [X_MID - ROWS_LEN / 2 + i * (L + SHIM) for i in range(N_AX)]
OVERHANG = (ROWS_LEN - STACK) / 2               # 0.9
SEAT_X = (335.0, 425.0)                         # doc 18 land length unchanged
RING_W = round(X_BLOCKS[0] - SEAT_X[0], 2)      # 7.1
COMB_H = 10.0                                   # comb bar height from the seat (2 mm under the magnet inner face)
COMB_CLEAR = 0.10
COMB_L = SEAT_X[1] - SEAT_X[0] - 8.0            # 82: one stepped bar per gap, 4 mm into each end ring
YOKE = 323.0 - R_SEAT                           # drum steel under the seat
MASS_G = W * L * T * 7.6e-3
COUNT = POLES * K * N_AX * N_STACK              # 200
SPARES = 10
GRADE = "N45SH"


def comb_width(r):
    """Width of the comb bar at radius r: between the side faces of two neighbouring blocks, minus glue clearance."""
    a_mid = math.radians(TAU / 2)
    v = math.sqrt(max(r * r - (W / 2) ** 2, 0))
    ang = math.atan2(W / 2, v)
    return 2 * r * math.sin(a_mid - ang) - 2 * COMB_CLEAR


def comb_bar():
    return round(comb_width(R_SEAT - COMB_H), 2), round(comb_width(R_SEAT), 2), COMB_H


def block_outline(pole_deg=0.0, layer=None):
    """Section corners (x, y) of the magnet stack (or one layer 0/1, 0 = inner) at a pole angle."""
    t = math.radians(pole_deg)
    r0, r1 = (R_IN, R_BACK) if layer is None else (R_IN + layer * T, R_IN + (layer + 1) * T)
    pts = []
    for u, v in ((-W / 2, r0), (W / 2, r0), (W / 2, r1), (-W / 2, r1)):
        pts.append((u * math.cos(t) + v * math.sin(t), -u * math.sin(t) + v * math.cos(t)))
    return pts


def summary():
    wi, wo, h = comb_bar()
    return dict(W=W, L=L, T=T, H=H, n_ax=N_AX, n_stack=N_STACK, seat_d=SEAT_D, r_in=round(R_IN, 3),
                r_back=round(R_BACK, 3), bond_mid=round(BOND_MID, 3), span_deg=round(SPAN, 3),
                alpha=round(SPAN / TAU, 3), skew_step=SKEW_STEP, row_shift=ROW_SHIFT, rows_len=round(ROWS_LEN, 2),
                overhang=round(OVERHANG, 2), x_blocks=[round(x, 2) for x in X_BLOCKS], ring_w=RING_W,
                comb_w_in=wi, comb_w_out=wo, comb_h=h, comb_l=COMB_L, yoke=round(YOKE, 2),
                sleeve_min=round(R_IN - R_SLEEVE_BORE, 3),
                sleeve_max=round(math.hypot(R_IN, W / 2) - R_SLEEVE_BORE, 3),
                mass_g=round(MASS_G, 1), count=COUNT, total_kg=round(COUNT * MASS_G / 1000, 2))


if __name__ == "__main__":
    import json
    print(json.dumps(summary(), indent=1))
