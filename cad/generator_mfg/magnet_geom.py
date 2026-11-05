"""Final magnet geometry for the P1 generator (doc 19, NP1-220 Rev C).

Flat (rectangular) N40UH blocks, parallel magnetised through the thickness,
K blocks side by side per pole and N_AX blocks along the stack. All other
drawings and the doc 19 tables are computed from this file.

Coordinates: r = radius from the generator axis [mm], x = axial position along
the spindle [mm] (same x as geometry.py, stack x 343 to 417).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "nacelle_p1"))
import geometry as G  # noqa: E402

GEN = G.GEN
POLES = GEN["poles"]
TAU = 360.0 / POLES                 # pole pitch, 9.000°
SPAN = TAU * GEN["alpha_m"]         # pole span 7.20° (unchanged from doc 06)

K = 2                               # blocks side by side per pole
N_AX = 2                            # blocks along the stack
H = 8.20                            # thickness (magnetised direction); doc 06 arcs were 7.70
BOND = 0.15                         # bond line at the block corners (glass beads)
SHIM = 0.20                         # axial gap between blocks (PTFE shim, removed)
STACK = GEN["stack"]                # 74.0
X_STACK = G.X_STACK                 # (343, 417)
R_STATOR = GEN["r_s"]               # 299.0
GAP = GEN["gap"]                    # 2.0
R_SLEEVE_BORE = R_STATOR + GAP      # 301.0 (mandrel Ø602.0)

# block width: two blocks fill the 7.20° span at the inner face, 0.20 mm apart
PITCH = SPAN / K                    # 3.60°
W = 18.75                           # block width (circumferential), mm
L = round((STACK - (N_AX - 1) * SHIM) / N_AX, 2)   # 36.90 block length (axial)
SEAT_D = 620.00                     # drum magnet seat diameter (was 618.4 in doc 18)
R_SEAT = SEAT_D / 2
R_CORNER = R_SEAT - BOND            # outer corners of the block sit on the beads
R_IN = math.sqrt(R_CORNER ** 2 - (W / 2) ** 2) - H        # inner face, block centre line
R_BACK = R_IN + H                                          # back face, block centre line
SAG = R_CORNER - R_BACK                                    # extra bond under the block middle
BOND_MID = BOND + SAG
R_IN_CORNER = math.hypot(R_IN, W / 2)                      # inner corners
SLEEVE_MIN = R_IN - R_SLEEVE_BORE                          # sleeve at the block centre
SLEEVE_MAX = R_IN_CORNER - R_SLEEVE_BORE                   # sleeve at the block edges
PHIS = [(j - (K - 1) / 2) * PITCH for j in range(K)]       # block centre angles in a pole


def gap_between_blocks():
    """Clearance between the two blocks of one pole at their inner corners (mm)."""
    a = math.radians(PITCH / 2)
    # inner corner of the +phi block, measured from the pole centre line
    u, v = W / 2, R_IN
    x = v * math.sin(a) - u * math.cos(a)        # distance of the corner from the pole centre line
    return 2 * x


def block_outline(phi_deg, pole_deg=0.0):
    """Block section corners (x, y) in mm, y along the pole centre line, for drawing."""
    t = math.radians(pole_deg + phi_deg)
    pts = []
    for u, v in ((-W / 2, R_IN), (W / 2, R_IN), (W / 2, R_BACK), (-W / 2, R_BACK)):
        pts.append((u * math.cos(t) + v * math.sin(t), -u * math.sin(t) + v * math.cos(t)))
    return pts


def comb_bar():
    """Trapezoid comb bar between two poles: faces parallel to the neighbouring block sides.
    Returns (width at inner face radius, width at the seat, height)."""
    # side of the +1.8° block of pole 0 and the -1.8° block of pole 1 (centre 9°)
    def side_dist(r):
        # distance from the comb mid line (4.5°) to the block side face at radius r, approx
        a_mid = math.radians(TAU / 2)
        a_blk = math.radians(PHIS[-1])
        # block side face: points u = W/2 in the block frame; perpendicular distance in the plane
        # from the mid line (a radial line at a_mid) = r sin(a_mid - angle of side point)
        v = math.sqrt(max(r * r - (W / 2) ** 2, 0))
        ang = a_blk + math.atan2(W / 2, v)
        return r * math.sin(a_mid - ang)
    w_in = 2 * side_dist(R_SEAT - COMB_H) - 2 * COMB_CLEAR
    w_out = 2 * side_dist(R_SEAT) - 2 * COMB_CLEAR
    return round(w_in, 2), round(w_out, 2), COMB_H


COMB_H = 7.0          # comb bar height from the seat (stays 1.2 mm under the sleeve bore side of the magnets)
COMB_CLEAR = 0.10     # glue clearance each side of the comb bar


VOL = W * L * H                                  # mm3
MASS_G = VOL * 7.6e-3
COUNT = POLES * K * N_AX                         # 160
SPARES = 8
TOTAL_KG = COUNT * MASS_G / 1000
X_BLOCKS = [X_STACK[0] + i * (L + SHIM) for i in range(N_AX)]   # front edge of each block row


def summary():
    wi, wo, hc = comb_bar()
    return dict(K=K, N_AX=N_AX, W=W, L=L, H=H, seat_d=SEAT_D, r_in=round(R_IN, 3), r_back=round(R_BACK, 3),
                r_corner=round(R_CORNER, 3), r_in_corner=round(R_IN_CORNER, 3), bond_mid=round(BOND_MID, 3),
                sleeve_min=round(SLEEVE_MIN, 3), sleeve_max=round(SLEEVE_MAX, 3),
                gap_between=round(gap_between_blocks(), 3), comb_w_in=wi, comb_w_out=wo, comb_h=hc,
                mass_g=round(MASS_G, 1), count=COUNT, total_kg=round(TOTAL_KG, 2),
                yoke_under_magnets=round(323.0 - R_SEAT, 2), x_blocks=X_BLOCKS)


if __name__ == "__main__":
    import json
    print(json.dumps(summary(), indent=1))
