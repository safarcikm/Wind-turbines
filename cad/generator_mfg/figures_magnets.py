"""Detail drawings (M01..M10) and isometric views (MI01..MI04) for doc 19, the final
magnet geometry (flat N40UH blocks, NP1-220 Rev C).

Run:  python3 figures_magnets.py          -> out/M*.svg, out/MI*.svg
      python3 figures_magnets.py --png    -> also PNG copies of everything in out/

Every dimension comes from magnet_geom.py (which reads cad/nacelle_p1/geometry.py),
the FEA numbers from analysis/generator/results/magnets_summary.json.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import magnet_geom as MG  # noqa: E402
from iso import Scene, move, rotz  # noqa: E402
from svgfig import C, Svg  # noqa: E402
from figures_iso import fit, tag, cyl_pt  # noqa: E402

OUT = HERE / "out"
OUT.mkdir(exist_ok=True)
RES = HERE.parent.parent / "analysis" / "generator" / "results"
_f = RES / "magnets_summary.json"
FEA = {r["key"]: r for r in json.loads((_f if _f.exists() else RES / "magnets_summary_quick.json").read_text())}
FIGS = []
STEEL = C["steel"]
SLEEVE = C["resin"]
GLUE = "#f1e3a6"


def fig(fn):
    FIGS.append(fn)
    return fn


def P(r, a_deg):
    """World point at radius r, angle a from the pole centre line (+y is outwards)."""
    t = math.radians(a_deg)
    return r * math.sin(t), r * math.cos(t)


def sector(r0, r1, a0, a1, n=48):
    pts = [P(r1, a0 + (a1 - a0) * i / n) for i in range(n + 1)]
    pts += [P(r0, a1 - (a1 - a0) * i / n) for i in range(n + 1)]
    return pts


class View:
    """World mm -> screen px, outward (bigger radius) is up on paper."""

    def __init__(self, cx, cy, s, y0):
        self.cx, self.cy, self.s, self.y0 = cx, cy, s, y0

    def __call__(self, pts):
        return [(self.cx + self.s * x, self.cy - self.s * (y - self.y0)) for x, y in pts]

    def pt(self, x, y):
        return self(([(x, y)]))[0]


def arc_piece(r0, r1, a0, a1):
    return sector(r0, r1, a0, a1, 24)


def block_pts(phi, pole=0.0):
    return MG.block_outline(phi, pole)


def comb_pts(a_mid):
    """Trapezoid comb bar centred on the radial line a_mid (deg), on the seat."""
    wi, wo, h = MG.comb_bar()
    r0, r1 = MG.R_SEAT - h, MG.R_SEAT + 0.3
    t = math.radians(a_mid)
    loc = [(-wi / 2, r0), (wi / 2, r0), (wo / 2, r1), (-wo / 2, r1)]
    return [(u * math.cos(t) + v * math.sin(t), -u * math.sin(t) + v * math.cos(t)) for u, v in loc]


def draw_pole_section(S, V, kind, k=1, h=7.7, sleeve=True, stator=True, half_poles=True):
    """One pole of the rotor in cross-section. kind 'arc' or 'flat' (k blocks)."""
    a_half = MG.TAU / 2 + (1.6 if half_poles else 0)
    if stator:
        S.poly(V(sector(296.0, MG.R_STATOR, -a_half, a_half)), fill=C["steel_d"], sw=1.5)
        for a in (-4.0, 4.0):    # slot openings near the pole edges (one slot pitch = 8°)
            S.poly(V(sector(296.0, MG.R_STATOR + 0.05, a - 0.38, a + 0.38, 6)), fill="white", stroke="none", sw=0)
    if kind == "arc":
        seat = 309.35
        S.poly(V(sector(seat, 316.0, -a_half, a_half)), fill=STEEL, sw=1.5)
        S.poly(V(sector(301.5, 309.2, -3.6, 3.6)), fill=C["mag_n"], sw=1.5)
        if sleeve:
            S.poly(V(sector(301.0, 301.5, -a_half, a_half)), fill=SLEEVE, sw=1)
        for s in (-1, 1):
            S.poly(V(sector(seat - 7.0, seat, s * 3.75, s * 5.25, 6)), fill=C["grp"], sw=1.2)
            S.poly(V(sector(301.5, 309.2, s * (MG.TAU - 3.6), s * a_half, 8)), fill=C["mag_s"], sw=1.2)
    else:
        if k == 1:
            w = 2 * 301.5 * math.tan(math.radians(3.6))
            phis = [0.0]
        else:
            pitch = MG.SPAN / k
            w = 2 * 301.5 * math.tan(math.radians(pitch / 2)) - 0.2
            phis = [(j - (k - 1) / 2) * pitch for j in range(k)]
        r_c = math.hypot(301.5 + h, w / 2)
        seat = r_c + 0.15
        S.poly(V(sector(seat, 316.0, -a_half, a_half)), fill=STEEL, sw=1.5)
        S.poly(V(sector(301.5, seat, -a_half, a_half)), fill=GLUE, stroke="none", sw=0)
        if sleeve:
            S.poly(V(sector(301.0, 301.5 + (r_c - 301.5 - h) + 0.02, -a_half, a_half)), fill=SLEEVE, sw=1)
        r_in = math.sqrt((seat - 0.15) ** 2 - (w / 2) ** 2) - h

        def blk(phi, pole, col):
            t = math.radians(pole + phi)
            loc = [(-w / 2, r_in), (w / 2, r_in), (w / 2, r_in + h), (-w / 2, r_in + h)]
            pts = [(u * math.cos(t) + v * math.sin(t), -u * math.sin(t) + v * math.cos(t)) for u, v in loc]
            S.poly(V(pts), fill=col, sw=1.5)
        for phi in phis:
            blk(phi, 0.0, C["mag_n"])
        for s in (-1, 1):
            S.poly(V(sector(seat - 7.0, seat, s * 3.75, s * 5.25, 6)), fill=C["grp"], sw=1.2)
            if half_poles:
                blk(phis[0] if s > 0 else phis[-1], s * MG.TAU, C["mag_s"])


_CLIP = [0]


def clip_begin(S, x, y, w, h):
    _CLIP[0] += 1
    cid = f"clip{_CLIP[0]}"
    S.raw(f'<clipPath id="{cid}"><rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}"/></clipPath>'
          f'<g clip-path="url(#{cid})">')


def clip_end(S):
    S.raw("</g>")


# ============================================================ M01 four options
@fig
def m01_options():
    S = Svg(1240, 1010, "M01 Four ways to make a pole")
    S.header("M01  Four ways to make one magnet pole: curved arc or flat blocks",
             "One pole cut across, drawn 9× real size. Drum on top, stator at the bottom, red = N pole, blue = next (S) pole.")
    opts = [("A", "arc", 1, 7.7, "A  Curved arc 7.7 (doc 18)"), ("F1", "flat", 1, 7.7, "F1  One flat block 7.7"),
            ("F3", "flat", 3, 7.7, "F3  Three flat blocks 7.7"), ("F2t", "flat", 2, 8.2, "F2t  Two flat blocks 8.2")]
    for i, (key, kind, k, h, title) in enumerate(opts):
        col, row = i % 2, i // 2
        x, y = 20 + col * 610, 80 + row * 455
        chosen = key == "F2t"
        S.rect(x, y, 590, 440, fill="white", stroke=C["ok"] if chosen else "#c9ced6", sw=4 if chosen else 2, rx=10)
        S.text(x + 20, y + 32, title, 20, "start", "bold")
        if chosen:
            S.tick(x + 555, y + 26)
            S.text(x + 535, y + 32, "chosen", 15, "end", "bold", C["ok"])
        V = View(x + 295, y + 215, 9.0, 305.5)
        clip_begin(S, x + 12, y + 50, 566, 295)
        draw_pole_section(S, V, kind, k, h)
        clip_end(S)
        r = FEA[key]
        e = r["eddy_loss_rated_W"]["by_axial_pieces"]
        n_ax = "4" if key in ("A", "F1") else "2"
        rows = [f"EMF {r['no_load']['line_emf_178rpm_100C_V']:.0f} V   torque {r['load']['mean_torque_Nm']:.0f} Nm   "
                f"cogging {r['cogging_pp_Nm']:.2f} Nm",
                f"magnet heat {e[n_ax]:.0f} W with {n_ax} pieces along   ·   magnets {r['magnet_mass_kg']:.2f} kg",
                {"A": "2 part numbers (N and S), ground curved faces",
                 "F1": "bond 0.73 mm thick in the middle, −6 % EMF",
                 "F2t": "1 part number, turn it over for S. 160 pieces",
                 "F3": "1 part number, but 240 small pieces"}[key]]
        S.rect(x + 10, y + 350, 570, 80, fill=C["light"], stroke="none", rx=6)
        S.lines(x + 295, y + 375, rows, 14)
    return S


# ============================================================ M02 one part, two poles
@fig
def m02_flip():
    S = Svg(1200, 620, "M02 One magnet, two ways round")
    S.header("M02  Why flat is easier: ONE magnet part, turned over for the other pole",
             "A flat block is magnetised straight through its thickness. Turn it over and the north face points the other way.")
    # left: arc needs two kinds
    S.rect(20, 80, 560, 500, fill="white", stroke="#c9ced6", sw=2, rx=10)
    S.text(300, 115, "Curved arc: 2 kinds to buy", 19, weight="bold")
    for i, n in enumerate((True, False)):
        x = 70 + i * 260
        S.path(f"M{x},{250} Q{x + 100},{205} {x + 200},{250} L{x + 200},{290} Q{x + 100},{245} {x},{290} Z",
               fill=C["mag_n"] if n else C["mag_s"], sw=2.5)
        S.arrow(x + 100, 205 if n else 300, x + 100, 300 if n else 205, C["ink"], 4)
        S.lines(x + 100, 340, ["NP1-220-N" if n else "NP1-220-S", "north inside" if n else "south inside"], 15,
                weight="bold")
    S.cross(300, 430, 18)
    S.lines(300, 475, ["turning it over does not work:", "the curve then faces the wrong way"], 15)
    # right: flat one kind
    S.rect(620, 80, 560, 500, fill="white", stroke=C["ok"], sw=3, rx=10)
    S.text(900, 115, "Flat block: 1 kind to buy", 19, weight="bold")
    for i, up in enumerate((True, False)):
        x = 670 + i * 260
        S.rect(x, 225, 200, 60, fill=C["mag_n"] if up else C["mag_s"], sw=2.5, rx=3)
        S.text(x + 100, 220 if up else 305, "N face  •" if up else "S face", 15, weight="bold")
        S.text(x + 100, 305 if up else 220, "S face" if up else "N face  •", 15, weight="bold")
        S.arrow(x + 100, 280 if up else 230, x + 100, 230 if up else 280, "white", 4)
        S.lines(x + 100, 340, ["NP1-220", "dot UP = N pole" if up else "dot DOWN = S pole"], 15, weight="bold")
    S.path("M830,255 C 860,200 890,200 920,255", stroke=C["ok"], sw=4)
    S.arrow(912, 240, 922, 258, C["ok"], 4)
    S.text(875, 192, "turn over", 15, weight="bold", color=C["ok"])
    S.tick(900, 430, 18)
    S.lines(900, 475, ["same part for N and S poles,", "one stock, one spare box, no mix-ups"], 15)
    S.text(600, 605, "Arrow = direction of magnetisation (from S face to N face, inside the magnet). "
                     "The white dot marks the N face.", 14, color=C["grey"])
    return S


# ============================================================ M03 detail drawing of the block
@fig
def m03_block():
    S = Svg(1240, 900, "M03 Detail drawing NP1-220 Rev C")
    S.header("M03  Detail drawing  NP1-220 Rev C  Magnet block (bought part)",
             "Drawn 10× real size. Dimensions in mm. Tolerances as marked, all others ±0.05.")
    s = 10.0
    W, L, H = MG.W, MG.L, MG.H
    ch = 0.3 * s * 2.2           # chamfer drawn exaggerated so it can be seen
    # top view (N face): L horizontal, W vertical
    x0, y0 = 90, 120
    S.text(x0, y0 - 14, "View A: looking at the N face", 15, "start", "bold")
    pts = [(x0 + ch, y0), (x0 + L * s - ch, y0), (x0 + L * s, y0 + ch), (x0 + L * s, y0 + W * s - ch),
           (x0 + L * s - ch, y0 + W * s), (x0 + ch, y0 + W * s), (x0, y0 + W * s - ch), (x0, y0 + ch)]
    S.poly(pts, fill=C["mag_n"], sw=2.5)
    S.circle(x0 + 30, y0 + 30, 9, fill="white", stroke=C["ink"], sw=1.5)
    S.leader(x0 + 30, y0 + 30, x0 + 30, y0 + W * s + 75, "N mark: white dot Ø3 near one corner", 13, anchor="start")
    S.text(x0 + L * s / 2, y0 + W * s / 2 + 8, "N", 30, weight="bold", color="white")
    S.dim(x0, y0 + W * s + 30, x0 + L * s, y0 + W * s + 30, f"{L:.2f} ±0.05  (along the stack)", size=14,
          color=C["ink"])
    S.dim(x0 - 35, y0 + W * s, x0 - 35, y0, f"{W:.2f} ±0.03", size=14, color=C["ink"])
    S.line(x0 - 50, y0, x0, y0, C["grey"], 1)
    S.line(x0 - 50, y0 + W * s, x0, y0 + W * s, C["grey"], 1)
    # front view (W x H) at right: section across the block, magnetisation arrow
    fx, fy = 640, 120
    S.text(fx, fy - 14, "View B: end of the block (across)", 15, "start", "bold")
    pts = [(fx + ch, fy), (fx + W * s - ch, fy), (fx + W * s, fy + ch), (fx + W * s, fy + H * s - ch),
           (fx + W * s - ch, fy + H * s), (fx + ch, fy + H * s), (fx, fy + H * s - ch), (fx, fy + ch)]
    S.poly(pts, fill=C["mag_n"], sw=2.5)
    S.arrow(fx + W * s / 2, fy + H * s - 10, fx + W * s / 2, fy + 12, "white", 5, 16)
    S.text(fx + W * s + 12, fy + 14, "N face", 14, "start", "bold")
    S.text(fx + W * s + 12, fy + H * s, "S face", 14, "start", "bold")
    S.dim(fx, fy + H * s + 30, fx + W * s, fy + H * s + 30, f"{W:.2f} ±0.03", size=14, color=C["ink"])
    S.dim(fx + W * s + 90, fy + H * s, fx + W * s + 90, fy, f"{H:.2f} ±0.02", size=14, color=C["ink"])
    S.leader(fx + W * s - 4, fy + 4, fx + W * s + 40, fy - 40, "chamfer 0.2 to 0.3 × 45°, all 12 edges", 13)
    S.text(fx + W * s / 2, fy + H * s + 70, f"magnetised through the {H:.2f} thickness", 14, weight="bold")
    # side view (L x H) under the top view
    sx, sy = 90, 470
    S.text(sx, sy - 14, "View C: side of the block (along)", 15, "start", "bold")
    pts = [(sx + ch, sy), (sx + L * s - ch, sy), (sx + L * s, sy + ch), (sx + L * s, sy + H * s - ch),
           (sx + L * s - ch, sy + H * s), (sx + ch, sy + H * s), (sx, sy + H * s - ch), (sx, sy + ch)]
    S.poly(pts, fill=C["mag_n"], sw=2.5)
    for k in range(5):
        xa = sx + L * s * (k + 0.5) / 5
        S.arrow(xa, sy + H * s - 8, xa, sy + 10, "white", 3, 10)
    S.dim(sx, sy + H * s + 30, sx + L * s, sy + H * s + 30, f"{L:.2f} ±0.05", size=14, color=C["ink"])
    # geometric tolerances
    S.rect(sx, sy + 140, 380, 128, fill=C["light"], stroke="#c9ced6", rx=6)
    S.lines(sx + 14, sy + 166, ["Flatness of N and S faces  0.02", "Parallelism N to S face  0.02",
                                "Squareness of the sides to the N face  0.05",
                                "Magnetic axis within 2° of the face normal"], 14, "start")
    # title block
    tx, ty, tw = 620, 470, 590
    rows = [("Part", "NP1-220 Rev C  magnet block (replaces NP1-220-N and -S arcs)"),
            ("Material", "Sintered NdFeB N40UH, Br ≥ 1.26 T, HcJ ≥ 1990 kA/m (20 °C)"),
            ("Magnetised", f"Fully, parallel, through the {MG.H:.2f} thickness"),
            ("Coating", "NiCuNi ≥ 15 µm + epoxy ≥ 15 µm (total 30 to 45 µm, in the sizes)"),
            ("Mark", "White dot Ø3 on the N face, one corner"),
            ("Mass", f"{MG.MASS_G:.1f} g each"),
            ("Quantity", f"{MG.COUNT} + 8 spare + 8 test pieces per generator"),
            ("Moment", "Each piece within ±1.5 % of the lot mean, value per serial"),
            ("Surfaces", "Faces ground, Ra ≤ 1.6 before coating"),
            ("Scale", "10 : 1 on this sheet")]
    S.rect(tx, ty, tw, 30 + 30 * len(rows), fill="white", stroke=C["ink"], sw=2)
    for i, (a, b) in enumerate(rows):
        yy = ty + 30 * i
        S.line(tx, yy, tx + tw, yy, C["grey"], 1)
        S.text(tx + 10, yy + 21, a, 14, "start", "bold")
        S.text(tx + 115, yy + 21, b, 13, "start")
    S.line(tx + 105, ty, tx + 105, ty + 30 * len(rows), C["grey"], 1)
    S.text(tx + 10, ty + 30 * len(rows) + 21, "Doc 19 · Wind turbine 12 kW · P1 generator", 13, "start",
           color=C["grey"])
    return S


# ============================================================ M04 pole section detail
@fig
def m04_pole_section():
    S = Svg(1240, 900, "M04 Detail of one pole")
    S.header("M04  Detail: one pole of two blocks on the drum seat (cross-section, 20× real size)",
             "Everything a drawing checker needs: radii from the generator axis, bond line, sleeve, comb bars.")
    V = View(620, 430, 20.0, 305.6)
    a_half = 6.0
    clip_begin(S, 140, 215, 960, 450)
    # drum
    S.poly(V(sector(MG.R_SEAT, 316.5, -a_half, a_half, 80)), fill=STEEL, sw=1.5)
    S.poly(V(sector(MG.R_SLEEVE_BORE, MG.R_SEAT, -a_half, a_half, 80)), fill=GLUE, stroke="none", sw=0)
    S.poly(V(sector(MG.R_SLEEVE_BORE, MG.R_IN + 0.02, -a_half, a_half, 80)), fill=SLEEVE, sw=1)
    for phi in MG.PHIS:
        S.poly(V(block_pts(phi)), fill=C["mag_n"], sw=2)
        c = V.pt(*P(MG.R_IN + MG.H / 2, phi))
        S.arrow(c[0], c[1] + 50, c[0], c[1] - 50, "white", 4, 12)
        S.text(c[0], c[1] + 80, "N inward", 13, weight="bold", color="white")
    for s in (-1, 1):
        S.poly(V(comb_pts(s * MG.TAU / 2)), fill=C["grp"], sw=1.5)
        t = math.radians(s * MG.TAU)
        loc = [(-MG.W / 2, MG.R_IN), (MG.W / 2, MG.R_IN), (MG.W / 2, MG.R_BACK), (-MG.W / 2, MG.R_BACK)]
        phi = MG.PHIS[0] if s > 0 else MG.PHIS[-1]
        tt = math.radians(s * MG.TAU + phi)
        pts = [(u * math.cos(tt) + v * math.sin(tt), -u * math.sin(tt) + v * math.cos(tt)) for u, v in loc]
        S.poly(V(pts), fill=C["mag_s"], sw=2)
    # stator tips
    S.poly(V(sector(297.5, MG.R_STATOR, -a_half, a_half, 80)), fill=C["steel_d"], sw=1.5)
    for a in (-4.0, 4.0):
        S.poly(V(sector(297.4, MG.R_STATOR + 0.02, a - 0.38, a + 0.38, 6)), fill="white", stroke="none", sw=0)
    clip_end(S)
    S.line(620, 200, 620, 660, C["grey"], 1, "14,5,3,5")
    S.text(626, 650, "pole centre line", 12, "start", color=C["grey"])
    # call-outs with numbers
    g = MG.summary()
    lab = [  # world point, label centre x, top (True) or bottom row, text
        (P(MG.R_SEAT + 2.5, -4.0), 250, True, [f"drum seat Ø{MG.SEAT_D:.2f} +0.05/0", "Ra 3 to 6 µm, grit blasted"]),
        (P(MG.R_CORNER - 0.05, MG.PHIS[0] - 1.72), 560, True, ["bond 0.15 at the block corners", "(0.15 glass beads)"]),
        (P(MG.R_BACK + 0.12, MG.PHIS[-1]), 860, True, [f"bond {g['bond_mid']:.2f} under the block middle",
                                                       "(seat is round, block is flat)"]),
        (P(MG.R_SEAT - 3, 4.15), 1110, True, ["comb bar NP1-221 (G11)",
                                                          f"{g['comb_w_in']:.2f} → {g['comb_w_out']:.2f} wide, 7.0 high"]),
        (P(MG.R_STATOR - 0.8, -2.0), 230, False, ["stator tooth tips r 299.0", "air gap 2.0 to the sleeve"]),
        (P(MG.R_IN + 3, 0.0), 500, False, ["gap between the two", f"blocks {g['gap_between']:.2f} (glue)"]),
        (P(MG.R_IN + 0.05, MG.PHIS[-1] + 0.8), 780, False, [f"block inner face r {MG.R_IN:.2f}", "at its centre line"]),
        (P(MG.R_SLEEVE_BORE + 0.25, 3.3), 1060, False, [f"sleeve bore Ø{2 * MG.R_SLEEVE_BORE:.1f}",
                                                        f"sleeve {g['sleeve_min']:.2f} to {g['sleeve_max']:.2f} thick"]),
    ]
    for (wx, wy), tx, top, rows in lab:
        x, y = V.pt(wx, wy)
        ty = 175 if top else 690
        S.line(x, y, tx, ty + (8 if top else -8), C["ink"], 1.3)
        S.circle(x, y, 3.5, fill=C["ink"], stroke="white", sw=1)
        if top:
            S.lines(tx, ty - 18, rows, 13)
        else:
            S.lines(tx, ty + 12, rows, 13)
    # dimension of block width and thickness
    p1, p2 = V.pt(*P(MG.R_IN - 1.4, MG.PHIS[0] - 1.75)), V.pt(*P(MG.R_IN - 1.4, MG.PHIS[0] + 1.75))
    S.text((p1[0] + p2[0]) / 2, p1[1] + 6, f"← {MG.W:.2f} →", 14, weight="bold")
    S.rect(380, 790, 480, 92, fill=C["light"], stroke="#c9ced6", rx=6)
    S.lines(620, 815, [f"Pole pitch 9.000°, pole span 7.20°, block centres at ±{MG.PITCH / 2:.2f}°",
                       f"Blocks: {MG.W:.2f} × {MG.L:.2f} × {MG.H:.2f}, magnetised through {MG.H:.2f}",
                       f"Drum yoke under the seat: {323 - MG.R_SEAT:.1f} mm (shell OD Ø646)"], 14)
    return S


# ============================================================ M05 comb bar and end ring
@fig
def m05_comb():
    S = Svg(1240, 640, "M05 Comb bar and end rings")
    S.header("M05  Detail drawings  NP1-221 comb bar (40 + 4 spare)  and  NP1-222 end rings (2)",
             "Glass-epoxy G11 (class H). The comb bars set where every pole sits. Dimensions in mm.")
    wi, wo, h = MG.comb_bar()
    s = 22
    x0, y0 = 120, 170
    # section
    S.text(x0, y0 - 60, "Section (22× real size)", 15, "start", "bold")
    cx = x0 + 160
    pts = [(cx - wi / 2 * s, y0 + h * s), (cx + wi / 2 * s, y0 + h * s), (cx + wo / 2 * s, y0), (cx - wo / 2 * s, y0)]
    S.poly(pts, fill=C["grp"], sw=2.5)
    S.dim(cx - wo / 2 * s, y0 - 20, cx + wo / 2 * s, y0 - 20, f"{wo:.2f} ±0.05 (seat side)", size=13, color=C["ink"])
    S.dim(cx - wi / 2 * s, y0 + h * s + 24, cx + wi / 2 * s, y0 + h * s + 24, f"{wi:.2f} ±0.05", size=13,
          color=C["ink"])
    S.dim(cx + wo / 2 * s + 40, y0 + h * s, cx + wo / 2 * s + 40, y0, f"{h:.1f} ±0.1", size=13, color=C["ink"])
    S.text(cx, y0 + h * s + 75, "faces 2.70° to the bar centre line (each side)", 13, color=C["grey"])
    S.text(cx, y0 + h * s + 95, "wide face is glued to the drum seat", 13, color=C["grey"])
    # length view
    lx, ly = 560, 170
    S.text(lx, ly - 60, "Length (2× real size)", 15, "start", "bold")
    Lb = 82.0
    S.rect(lx, ly, Lb * 7, h * 7, fill=C["grp"], sw=2.5)
    S.dim(lx, ly + h * 7 + 24, lx + Lb * 7, ly + h * 7 + 24, f"{Lb:.1f} ±0.2  (x 339 to 421, into both end rings)",
          size=13, color=C["ink"])
    S.text(lx + Lb * 7 / 2, ly + h * 7 + 70, "ends square, edges broken 0.3", 13, color=C["grey"])
    # end ring
    ex, ey = 120, 470
    S.text(ex, ey - 16, "NP1-222 end ring (front and rear, same part)", 15, "start", "bold")
    S.rect(ex, ey, 540, 120, fill="white", stroke="#c9ced6", rx=8)
    S.lines(ex + 20, ey + 30, ["G11 ring, OD Ø620.0 −0.1/−0.2 (glued in the seat),",
                                "ID Ø604.0 ±0.1 (stays 1.5 mm outside the sleeve bore),",
                                "width 8.0 −0.1 axial (x 335 to 343 front, x 417 to 425 rear),",
                                "40 notches 7.1 deep × comb bar width +0.2, pitch 9.000°."], 14, "start")
    S.rect(700, 470, 510, 120, fill=C["light"], stroke="#c9ced6", rx=8)
    S.lines(715, 500, ["Comb bars are slightly longer than the stack (82 vs 74)", "so their ends sit in the end-ring notches:",
                       "the ring fixes the angle, the bar fixes the pole.", "Locate notch 1 from hub bolt hole 1."], 14,
            "start")
    return S


# ============================================================ M06 unrolled layout
@fig
def m06_layout():
    S = Svg(1240, 760, "M06 Where every block goes")
    S.header("M06  Where every block goes: the drum seat unrolled, seen from the stator",
             "Part of the ring, 6 of the 40 poles. Each pole = 2 blocks across × 2 blocks along = 4 blocks of the SAME part.")
    px, y2 = 70, 110
    pw, ph = 172, 420
    x = px
    for p in range(6):
        n = p % 2 == 0
        S.rect(x, y2 + 20, 22, ph, fill=C["grp"])
        xm = x + 26
        for c in range(2):
            for k in range(2):
                ym = y2 + 30 + k * 202
                S.rect(xm + c * 72, ym, 68, 196, fill=C["mag_n"] if n else C["mag_s"], rx=3)
                S.text(xm + c * 72 + 34, ym + 105, "N" if n else "S", 22, weight="bold", color="white")
                if n:
                    S.circle(xm + c * 72 + 14, ym + 14, 5, fill="white", stroke="none")
                if k == 0:
                    S.rect(xm + c * 72 + 6, ym + 196, 56, 6, fill=C["ptfe"], sw=1)
        S.text(x + 96, y2 + ph + 52, f"pole {p + 1}", 14, weight="bold")
        S.text(x + 96, y2 + ph + 70, "dot UP" if n else "dot DOWN", 13, color=C["grey"])
        x += pw
    S.rect(x, y2 + 20, 22, ph, fill=C["grp"])
    S.rect(px, y2 + 20 + ph, x - px + 22, 18, fill=C["grp"])
    S.rect(px, y2 + 2, x - px + 22, 18, fill=C["grp"])
    S.text(px + 520, y2 - 4, "rear end ring NP1-222  (open end of the drum: blocks go in here)", 13)
    S.text(px + 520, y2 + ph + 34, "front end ring NP1-222", 13)
    S.dim(1150, y2 + 30, 1150, y2 + 432, "74.0 = 36.9 + 0.2 + 36.9", size=13, color=C["ink"])
    S.legend(70, y2 + ph + 95, [(C["grp"], "tan = G11 comb bars and end rings"),
                                (C["ptfe"], "white strip = 0.2 mm PTFE shim (taken out after cure)")], 14)
    S.lines(700, y2 + ph + 110, ["• white dot visible = N pole (dot faces the stator)",
                                 "• dot hidden against the drum = S pole",
                                 "• N and S always alternate, 20 + 20 poles"], 14, "start")
    return S


# ============================================================ M07 radial stack-up
@fig
def m07_stack():
    S = Svg(1240, 760, "M07 Radial tolerance stack")
    S.header("M07  From the drum to the stator: every layer and its tolerance (radial, mm)",
             "The sleeve is moulded on the Ø602.0 mandrel, so magnet and bond scatter only change the sleeve thickness, not the air gap.")
    g = MG.summary()
    layers = [  # name, nominal thickness, tol text, colour
        ("drum seat (radius)", None, f"r {MG.R_SEAT:.3f}  +0.025/0  (Ø +0.05/0)", STEEL),
        ("bond at the corners", 0.15, "+0.05 / 0  (beads set the minimum)", GLUE),
        ("block thickness", MG.H, "±0.02", C["mag_n"]),
        ("sleeve at the block centre", g["sleeve_min"], "result: 0.49 to 0.60", SLEEVE),
        ("sleeve bore (radius)", None, "r 301.00  +0.025/−0.01, run-out ≤ 0.03", SLEEVE),
        ("air gap", 2.0, "≥ 1.80 anywhere (doc 18 §7)", "#ffffff"),
        ("stator tooth tips (radius)", None, "r 299.00", C["steel_d"]),
    ]
    y = 110
    for name, t, tol, col in layers:
        h = 70 if t is None else max(36, min(160, t * 16 if t > 1 else 46))
        S.rect(80, y, 300, h, fill=col, sw=1.5)
        S.text(230, y + h / 2 + 6, name, 15, weight="bold", color="white" if col in (C["mag_n"], C["steel_d"]) else C["ink"])
        S.text(410, y + h / 2 - 4, (f"{t:.2f}" if t is not None else ""), 16, "start", "bold")
        S.text(480, y + h / 2 + 6, tol, 14, "start")
        y += h + 6
    S.rect(840, 110, 380, 330, fill=C["light"], stroke="#c9ced6", rx=8)
    lo, hi = MG.R_IN - 0.02, MG.R_IN + 0.025 + 0.05 + 0.02
    S.lines(860, 140, ["Magnet inner face at a block centre:", f"  nominal r {MG.R_IN:.3f}",
                       f"  lowest  r {lo:.2f} (thick block, small seat)",
                       f"  highest r {hi:.2f} (thin block, big seat,", "            thick bond)", "",
                       f"Sleeve {lo - 301.0:.2f} to {hi - 301.0:.2f} at the block centre,",
                       f"up to {MG.SLEEVE_MAX + 0.1:.2f} at the block edges: inside", "the 0.4 to 0.8 range tested on Q1.", "",
                       "Air gap: unchanged, set by the mandrel."], 14, "start")
    S.rect(840, 460, 380, 150, fill="#fff4e6", stroke=C["warn"], sw=2, rx=8)
    S.lines(860, 490, ["Reject a drum if the seat is", "smaller than Ø620.00: the blocks would",
                       "push into the sleeve space.", "Larger seat: just thicker sleeve."], 14, "start")
    return S


# ============================================================ M08 forces on a block
@fig
def m08_forces():
    S = Svg(1300, 700, "M08 What holds a magnet")
    A = FEA["F2t"]
    fr_nl, ft_nl = A["force_no_load_N_per_pole"]
    fr_ld, ft_ld = A["force_load_N_per_pole"]
    S.header("M08  The forces on one pole of magnets, and what carries them",
             "Outer rotor: the magnets sit inside the drum, so spinning pushes them OUTWARDS into the steel.")
    V = View(320, 360, 8.0, 306.0)
    clip_begin(S, 40, 150, 560, 400)
    S.poly(V(sector(MG.R_SEAT, 318, -6, 6, 60)), fill=STEEL, sw=1.5)
    for phi in MG.PHIS:
        S.poly(V(block_pts(phi)), fill=C["mag_n"], sw=2)
    for s in (-1, 1):
        S.poly(V(comb_pts(s * MG.TAU / 2)), fill=C["grp"], sw=1.2)
    S.poly(V(sector(MG.R_SLEEVE_BORE, MG.R_IN + 0.02, -6, 6, 60)), fill=SLEEVE, sw=1)
    clip_end(S)
    c = V.pt(0, 305.5)
    S.arrow(c[0], c[1], c[0], c[1] - 120, C["ok"], 7, 20)
    S.text(c[0] + 14, c[1] - 125, "outwards", 16, "start", "bold", C["ok"])
    S.arrow(c[0] - 140, c[1] + 70, c[0] + 140, c[1] + 70, C["warn"], 7, 20)
    S.text(c[0], c[1] + 105, "sideways (torque)", 16, weight="bold", color=C["warn"])
    m_pole = 4 * MG.MASS_G / 1000
    w = 250 * 2 * math.pi / 60
    fc = m_pole * w * w * 0.305
    rows = [("Spinning at 250 rpm (overspeed)", f"{fc:.0f} N outwards", "drum steel"),
            ("Magnetic pull, no load", f"{fr_nl:.0f} N outwards", "drum steel"),
            ("Magnetic pull, rated load", f"{fr_ld:.0f} N outwards", "drum steel"),
            ("Torque share, rated (local peak)", f"{abs(ft_ld):.0f} N sideways", "glue shear, comb bar"),
            ("Short circuit, 4 × torque", f"≈ {4 * 66:.0f} N sideways", "glue shear, comb bar"),
            ("Cold −40 °C (steel shrinks more)", "≈ 0.02 mm at corners", "tough room-cure glue"),
            ("If a block ever cracks", "pieces stay put", "sleeve + end rings")]
    x0, y0 = 650, 110
    S.rect(x0, y0, 630, 40 + 46 * len(rows), fill="white", stroke=C["ink"], sw=1.5)
    S.text(x0 + 12, y0 + 27, "Load on one pole (4 blocks)", 15, "start", "bold")
    S.text(x0 + 270, y0 + 27, "size", 15, "start", "bold")
    S.text(x0 + 455, y0 + 27, "carried by", 15, "start", "bold")
    for i, (a, b, cc) in enumerate(rows):
        yy = y0 + 40 + 46 * i
        S.line(x0, yy, x0 + 630, yy, "#c9ced6", 1)
        S.text(x0 + 12, yy + 28, a, 13, "start")
        S.text(x0 + 270, yy + 28, b, 13, "start", "bold")
        S.text(x0 + 455, yy + 28, cc, 13, "start")
    area = MG.K * MG.N_AX * MG.W * MG.L
    S.rect(x0, 520, 630, 140, fill=C["light"], stroke="#c9ced6", rx=8)
    S.lines(x0 + 14, 548, [f"Glue area per pole {area:.0f} mm². Rated shear {abs(ft_ld) / area * 1000:.0f} kPa,",
                           f"short circuit ≈ {4 * 66 / area * 1000:.0f} kPa, against ≥ 5 MPa at 120 °C:",
                           "more than 50× margin. The glue never carries a pull-off load,",
                           "so a block cannot fall into the air gap even with no glue."], 14, "start")
    return S


# ============================================================ M09 incoming inspection
@fig
def m09_inspect():
    S = Svg(1200, 820, "M09 Check the magnets when they arrive")
    S.header("M09  When the box arrives: 6 checks for every block (in the magnet room)",
             "Two people. Only one block out of its spacer at a time. Gloves and glasses.")
    W, H = 380, 340
    pan = [(1, ["Count and read the label:", "168 + 8 test pieces, one part number"]),
           (2, ["Look: no chips > 0.5 mm,", "coating not scratched"]),
           (3, ["Size with go / no-go gauges:", f"{MG.W:.2f}, {MG.L:.2f}, {MG.H:.2f}"]),
           (4, ["Helmholtz coil: moment within", "±1.5 % of the lot mean"]),
           (5, ["Check the dot is on the N face", "(gaussmeter: N reads +)"]),
           (6, ["Sort into 40 poles of 4: each pole", "within ±0.5 %, strong next to weak"])]
    for i, (n, cap) in enumerate(pan):
        x, y = 20 + (i % 3) * 395, 80 + (i // 3) * 360
        S.panel(x, y, W, H, n, cap)
        cx, cy = x + W / 2, y + 140
        if n == 1:
            for k in range(4):
                S.rect(cx - 120 + k * 60, cy - 40, 50, 30, fill=C["mag_n"], rx=2)
                S.rect(cx - 124 + k * 60, cy - 46, 58, 42, fill="none", stroke=C["grey"], sw=1.5, rx=3)
            S.rect(cx - 140, cy + 20, 280, 50, fill="white", sw=2)
            S.text(cx, cy + 52, "NP1-220 Rev C  N40UH", 15, weight="bold")
        elif n == 2:
            S.rect(cx - 90, cy - 40, 180, 80, fill=C["mag_n"], rx=3)
            S.circle(cx + 70, cy - 30, 30, fill="none", stroke=C["ink"], sw=3)
            S.line(cx + 92, cy - 8, cx + 130, cy + 30, C["ink"], 6)
            S.cross(cx - 120, cy + 70, 14)
            S.text(cx - 96, cy + 76, "chip = scrap (oil tin)", 13, "start")
        elif n == 3:
            S.rect(cx - 120, cy - 30, 240, 60, fill=C["al"], sw=2)
            S.rect(cx - 40, cy - 30, 80, 30, fill="white", sw=1.5)
            S.rect(cx - 34, cy - 54, 68, 24, fill=C["mag_n"], rx=2)
            S.text(cx - 80, cy + 18, "GO", 14, weight="bold", color=C["ok"])
            S.text(cx + 80, cy + 18, "NO-GO", 14, weight="bold", color=C["bad"])
            S.text(cx, cy + 70, "aluminium gauges, no steel", 13, color=C["grey"])
        elif n == 4:
            for r in (60, 48):
                S.circle(cx - 40, cy, r, fill="none", stroke=C["cu"], sw=6)
            S.rect(cx - 52, cy - 10, 24, 20, fill=C["mag_n"], rx=2)
            S.rect(cx + 50, cy - 35, 90, 70, fill="#ffe066", rx=8)
            S.text(cx + 95, cy + 6, "1.002", 18, weight="bold")
        elif n == 5:
            S.rect(cx - 90, cy - 10, 180, 50, fill=C["mag_n"], rx=3)
            S.circle(cx - 66, cy + 2, 6, fill="white", stroke="none")
            S.rect(cx - 20, cy - 110, 70, 80, fill="#ffe066", rx=8)
            S.text(cx + 15, cy - 62, "N +", 20, weight="bold")
            S.line(cx + 15, cy - 30, cx + 15, cy - 10, C["ink"], 3)
        else:
            for k in range(4):
                S.rect(cx - 100 + (k % 2) * 60, cy - 50 + (k // 2) * 60, 50, 50, fill=C["mag_n"], rx=2)
            S.text(cx + 80, cy, "Σ = pole", 18, weight="bold")
            S.text(cx + 80, cy + 26, "±0.5 %", 16)
    S.rect(20, 770, 1160, 40, fill="#fff3bf", stroke=C["warn"], sw=2, rx=8)
    S.text(600, 796, "Record every serial, its moment and its pole number. The record goes with the rotor.", 15)
    return S


# ============================================================ M10 bonding a pole of blocks
@fig
def m10_bond():
    S = Svg(1200, 900, "M10 Glue one pole of blocks")
    S.header("M10  Glue one pole: 4 blocks of the same part, with the jig NP1-T02 (Rev C shoe)",
             "Drum upright, open (rear) end up, on the non-magnetic turntable. Comb bars and front end ring already cured.")
    W, H = 380, 360

    def channel(x, y):
        S.rect(x + 40, y + 60, 24, 230, fill=C["grp"])
        S.rect(x + 316, y + 60, 24, 230, fill=C["grp"])
        S.rect(x + 40, y + 290, 300, 14, fill=C["grp"])
        S.rect(x + 64, y + 60, 252, 230, fill="#e3e6ea", stroke="none")
    pan = [(1, ["Glue + 0.15 mm beads on the seat", "and on the block's back face"]),
           (2, ["Block 1 down with the jig, slid", "against the LEFT comb bar"]),
           (3, ["Block 2 down: the two push apart,", "so it goes against the RIGHT bar"]),
           (4, ["PTFE shim 0.2 on top, then", "blocks 3 and 4 the same way"]),
           (5, ["Clamp bar on all 4 until cured.", "Gaussmeter: correct pole?"]),
           (6, ["N poles day 1, S poles day 2.", "Post-cure 80 °C, 4 h, then sleeve"])]
    for i, (n, cap) in enumerate(pan):
        x, y = 20 + (i % 3) * 395, 80 + (i // 3) * 390
        S.panel(x, y, W, H, n, cap)
        if n == 6:
            cx, cy = x + W / 2, y + 160
            for p in range(40):
                a = math.radians(p * 9)
                nn = p % 2 == 0
                S.circle(cx + 115 * math.sin(a), cy - 115 * math.cos(a), 9, fill=C["mag_n"] if nn else "white",
                         stroke=C["mag_n"] if nn else C["mag_s"], sw=2)
            S.text(cx, cy - 8, "day 1: dot up", 15, weight="bold", color=C["mag_n"])
            S.text(cx, cy + 16, "day 2: dot down", 15, weight="bold", color=C["mag_s"])
            continue
        channel(x, y)
        bw, bh = 122, 110
        if n == 1:
            S.rect(x + 64, y + 70, 252, 216, fill=GLUE, stroke="none")
            for k in range(30):
                S.circle(x + 80 + (k * 37) % 230, y + 90 + (k * 53) % 180, 3, fill="white", stroke=C["grey"], sw=1)
        if n >= 2:
            S.rect(x + 66, y + 178, bw, bh, fill=C["mag_n"], rx=3)
        if n == 2:
            S.arrow(x + 200, y + 232, x + 140, y + 232, C["ink"], 4)
        if n >= 3:
            S.rect(x + 192, y + 178, bw, bh, fill=C["mag_n"], rx=3)
        if n == 3:
            S.arrow(x + 190, y + 150, x + 120, y + 150, C["bad"], 3)
            S.arrow(x + 190, y + 150, x + 260, y + 150, C["bad"], 3)
            S.text(x + 190, y + 140, "push apart", 13, weight="bold", color=C["bad"])
        if n >= 4:
            S.rect(x + 66, y + 172, 248, 5, fill=C["ptfe"], sw=1)
            S.rect(x + 66, y + 62, bw, bh, fill=C["mag_n"], rx=3)
            S.rect(x + 192, y + 62, bw, bh, fill=C["mag_n"], rx=3)
        if n == 5:
            S.rect(x + 100, y + 40, 180, 16, fill=C["al"], sw=1.5)
            S.rect(x + 300, y + 6, 64, 46, fill="#ffe066", rx=8)
            S.text(x + 332, y + 37, "N", 20, weight="bold")
            S.line(x + 300, y + 40, x + 250, y + 70, C["ink"], 3)
            S.tick(x + 70, y + 30)
    return S


# ============================================================ isometric views
def block_prism(sc, phi, pole, z0, z1, col, layer=0, bias=0.0, w=None, h=None, r_in=None):
    w = w or MG.W
    h = h or MG.H
    r_in = r_in or MG.R_IN
    t = math.radians(pole + phi)
    loc = [(-w / 2, r_in), (w / 2, r_in), (w / 2, r_in + h), (-w / 2, r_in + h)]
    # world: angle measured from +Y towards +X (same as the section drawings)
    pts = [(u * math.cos(t) + v * math.sin(t), -u * math.sin(t) + v * math.cos(t)) for u, v in loc]
    sc.prism([pts], z0, z1, col, layer=layer, bias=bias)


@fig
def mi01_block():
    S = Svg(1200, 700, "MI01 The magnet block in 3D")
    S.header("MI01  The magnet block NP1-220 Rev C in 3D (isometric, 8× real size)",
             "One part for every pole. The arrow shows the magnetisation, from the S face to the N face.")
    sc = Scene()
    W, L, H = MG.W, MG.L, MG.H
    sc.box(0, 0, 0, L, W, H, C["mag_n"])
    F = fit(sc, 300, 110, 560, 420)
    sc.render(S, *F)
    a = sc.proj((L * 0.75, W * 0.4, H), *F)
    S.circle(a[0], a[1], 8, fill="white", stroke=C["ink"], sw=1.5)
    S.leader(a[0], a[1], 980, 170, ["white dot = N face", "(here facing up)"], 15)
    p0, p1 = sc.proj((0, W, 0), *F), sc.proj((L, W, 0), *F)
    S.dim(p0[0], p0[1] + 30, p1[0], p1[1] + 30, f"{L:.2f}", size=15, color=C["ink"])
    q0, q1 = sc.proj((L, 0, 0), *F), sc.proj((L, W, 0), *F)
    S.dim(q1[0] + 30, q1[1], q0[0] + 30, q0[1], f"{W:.2f}", size=15, color=C["ink"])
    r0, r1 = sc.proj((0, W, 0), *F), sc.proj((0, W, H), *F)
    S.dim(r0[0] - 34, r0[1], r1[0] - 34, r1[1], f"{H:.2f}", size=15, color=C["ink"])
    c0 = sc.proj((L * 0.35, W * 0.5, H), *F)
    S.arrow(c0[0], c0[1], c0[0], c0[1] - 130, C["ok"], 6, 18)
    S.text(c0[0] + 14, c0[1] - 110, "magnetisation: out of the N face", 16, "start", "bold", C["ok"])
    S.rect(30, 560, 1140, 110, fill=C["light"], stroke="#c9ced6", rx=8)
    S.lines(50, 592, [f"N40UH, {MG.MASS_G:.0f} g, size of a matchbox cut in half. Pulls ≈ 280 N (28 kg) on thick steel.",
                      "Flat faces ground, edges chamfered 0.2 to 0.3, NiCuNi + epoxy coated, white dot on the N face.",
                      f"{MG.COUNT} per generator (+8 spare): 40 poles × 2 across × 2 along."], 15, "start")
    return S


@fig
def mi02_pole():
    S = Svg(1240, 900, "MI02 One pole pulled apart")
    S.header("MI02  One pole pulled apart (isometric), seen from the stator side",
             "From the back: drum seat, comb bars, four blocks, glass sleeve. Each layer is pulled towards you (towards the axis).")
    sc = Scene()
    z0 = MG.X_STACK[0]
    ROT = 90.0                       # section +Y (pole centre) -> world 180° (-X), stator side faces the viewer

    def W(pts, lift):
        c, s_ = math.cos(math.radians(ROT)), math.sin(math.radians(ROT))
        out = []
        for x, y in pts:
            y = y - lift                 # lift towards the axis
            out.append((x * c - y * s_, x * s_ + y * c))
        return out
    a = 7.0
    sc.revolve([(335 - z0, MG.R_SEAT), (425 - z0, MG.R_SEAT), (425 - z0, 318.0), (335 - z0, 318.0)], STEEL,
               180 - a, 180 + a, step=0.5, axial=(0, 1))
    L1, L2, L3 = 40.0, 85.0, 135.0
    for s in (-1, 1):
        sc.prism([W(comb_pts(s * MG.TAU / 2), L1)], 339 - z0, 421 - z0, C["grp"])
    for x in MG.X_BLOCKS:
        for phi in MG.PHIS:
            sc.prism([W(block_pts(phi), L2)], x - z0, x - z0 + MG.L, C["mag_n"])
    sl = [P(MG.R_SLEEVE_BORE, -a + 0.25 * j) for j in range(int(2 * a / 0.25) + 1)]
    sl += [P(MG.R_IN + 0.15, a - 0.25 * j) for j in range(int(2 * a / 0.25) + 1)]
    sc.prism([W(sl, L3)], 339 - z0, 421 - z0, SLEEVE)
    F = fit(sc, 200, 100, 760, 700)
    sc.render(S, *F)

    def wp(x, y, z, lift):
        return (*W([(x, y)], lift)[0], z)
    tag(S, sc, F, (-318.0, 0, 70), 250, 150, 1, [f"drum seat Ø{MG.SEAT_D:.1f}", "grit blasted + primer"])
    tag(S, sc, F, wp(comb_pts(-MG.TAU / 2)[0][0], comb_pts(-MG.TAU / 2)[0][1], 60, L1), 250, 560, 2,
        ["comb bar G11", "one each side"])
    tag(S, sc, F, wp(4, MG.R_IN, 20, L2), 1060, 300, 3, ["4 blocks, same part,", "dot facing the stator"])
    tag(S, sc, F, wp(0, MG.R_SLEEVE_BORE, 10, L3), 1060, 640, 4, ["glass sleeve 0.5,", "moulded last"])
    S.rect(30, 700, 330, 150, fill=C["light"], stroke="#c9ced6", rx=8)
    S.lines(45, 728, ["Not drawn: the glue line", "(0.15 at the corners,", f"{MG.BOND_MID:.2f} under the middle)",
                      "and the end rings."], 15, "start")
    return S


@fig
def mi03_drum():
    S = Svg(1300, 900, "MI03 Drum with 160 flat blocks")
    S.header("MI03  The rotor drum with its 160 flat blocks (isometric, cut open)",
             "Open end up, as on the jig. A quarter is cut away. 40 poles: red N, blue S, each 2 × 2 blocks.")
    sc = Scene()
    cut = (90.0, 360.0)
    import figures as F18
    for pts in F18.G.DRUM_PARTS.values():
        q = [(x, MG.R_SEAT if abs(r - F18.GEN["r_m2"]) < 1e-6 else r) for x, r in pts]
        sc.revolve(q, "#c3cad2", cut[0], cut[1], step=3.0, axial=(-80.0, 1))
    for p in range(MG.POLES):
        centre = 4.5 + p * MG.TAU           # pole centre angle, measured from +X (revolve convention)
        if centre - 9 < cut[0] or centre + 9 > cut[1]:
            continue
        col = C["mag_n"] if p % 2 == 0 else C["mag_s"]
        for x in MG.X_BLOCKS:
            for phi in MG.PHIS:
                t = math.radians(centre + phi)
                loc = [(MG.R_IN, -MG.W / 2), (MG.R_BACK, -MG.W / 2), (MG.R_BACK, MG.W / 2), (MG.R_IN, MG.W / 2)]
                pts = [(v * math.cos(t) - u * math.sin(t), v * math.sin(t) + u * math.cos(t)) for v, u in loc]
                sc.prism([pts], x - 80, x - 80 + MG.L, col, bias=15)
    Fp = fit(sc, 330, 90, 680, 760)
    sc.render(S, *Fp)
    tag(S, sc, Fp, cyl_pt(301.6, 184.5, MG.X_BLOCKS[1] - 80 + 20), 300, 210, 1, ["one pole = 4 blocks,", "all one colour"])
    tag(S, sc, Fp, cyl_pt(301.6, 175.5, MG.X_BLOCKS[0] - 80 + 18), 300, 340, 2, ["next pole: same part", "turned over (S)"])
    tag(S, sc, Fp, cyl_pt(318, 90, 300), 1060, 420, 3, ["drum wall (cut)", f"seat Ø{MG.SEAT_D:.1f}"])
    S.rect(20, 690, 330, 150, fill=C["light"], stroke="#c9ced6", rx=8)
    S.lines(35, 718, ["Seen up close, each pole is a", "shallow 'roof' of two flat", "blocks instead of one curved",
                      "piece, 0.5 mm thicker so the", "EMF stays on target (381 V)."], 15, "start")
    return S


@fig
def mi04_compare():
    S = Svg(1240, 640, "MI04 Arc pole and flat pole")
    S.header("MI04  Curved arc pole (before) and flat block pole (now), isometric",
             "Both fill the same 7.2° of the 9° pole pitch on the same 74 mm stack.")
    for i, kind in enumerate(("arc", "flat")):
        sc = Scene()
        if kind == "arc":
            for k in range(4):
                u0 = k * 18.55
                sc.revolve([(u0, 301.5), (u0 + 18.35, 301.5), (u0 + 18.35, 309.2), (u0, 309.2)], C["mag_n"], 86.4,
                           93.6, step=0.6, axial=(0, 1))
        else:
            for x in MG.X_BLOCKS:
                for phi in MG.PHIS:
                    t = math.radians(90 + phi)
                    loc = [(MG.R_IN, -MG.W / 2), (MG.R_BACK, -MG.W / 2), (MG.R_BACK, MG.W / 2), (MG.R_IN, MG.W / 2)]
                    pts = [(v * math.cos(t) - u * math.sin(t), v * math.sin(t) + u * math.cos(t)) for v, u in loc]
                    sc.prism([pts], x - MG.X_STACK[0], x - MG.X_STACK[0] + MG.L, C["mag_n"])
        x0 = 40 + i * 610
        S.panel(x0, 80, 580, 530, None,
                ["Before: 4 curved arcs per pole,", "2 part numbers (N, S)"] if kind == "arc"
                else ["Now: 2 × 2 flat blocks per pole,", "1 part number, turned over for S"], cap_h=70)
        Fp = fit(sc, x0 + 60, 120, 460, 380)
        sc.render(S, *Fp)
        if kind == "flat":
            S.tick(x0 + 540, 110)
    return S


def main(png=False):
    for fn in FIGS:
        S = fn()
        name = fn.__name__.split("_", 1)
        fname = f"{name[0].upper()}-{name[1]}.svg"
        S.save(OUT / fname)
        print(fname)
    if png:
        import subprocess
        tmp = OUT / "_m"
        tmp.mkdir(exist_ok=True)
        for f in tmp.glob("*"):
            f.unlink()
        for fn in FIGS:
            name = fn.__name__.split("_", 1)
            fname = f"{name[0].upper()}-{name[1]}.svg"
            (tmp / fname).write_text((OUT / fname).read_text())
        subprocess.run(["node", str(HERE / "render_png.js"), str(tmp)], check=True)
        for f in tmp.glob("*.png"):
            f.replace(OUT / f.name)
        for f in tmp.glob("*"):
            f.unlink()
        tmp.rmdir()


if __name__ == "__main__":
    main("--png" in sys.argv)
