"""Isometric views for doc 23 (generator Rev C, one N45SH 30 x 15 x 12 block per pole and row).

Run:  python3 iso_rc.py [--png]   -> out/iso/IR01..IR06 *.svg (+ .png)

Same renderer and parts as the doc 18 views (cad/generator_mfg/figures_iso.py); the rotor is
rebuilt from rotor_rc.py: 200 blocks in 5 skewed rows, stepped comb bars, end rings, and the
rear cover with its 24 fan blades (drawings_rc.FAN).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).parent
MFG = HERE.parent / "generator_mfg"
sys.path.insert(0, str(MFG))
sys.path.insert(0, str(HERE))
import rotor_rc as R  # noqa: E402
import figures_iso as FI  # noqa: E402
from figures_iso import (G, GEN, X0, DRUM_COL, add_carrier, add_spindle, add_stator, cyl_pt, fit,  # noqa: E402
                         tag)
from iso import Scene  # noqa: E402
from svgfig import C, Svg  # noqa: E402
from drawings_rc import FAN  # noqa: E402

OUT = HERE / "out" / "iso"
POLE = 360.0 / GEN["poles"]
FIGS = []


def fig(fn):
    FIGS.append(fn)
    return fn


def comb_loop(polar_deg):
    """Comb bar section (x, y) centred on a polar angle (deg from +x)."""
    wi, wo, h = R.comb_bar()
    r0, r1 = R.R_SEAT - h, R.R_SEAT + 0.2
    t = math.radians(90.0 - polar_deg)
    loc = [(-wi / 2, r0), (wi / 2, r0), (wo / 2, r1), (-wo / 2, r1)]
    return [(u * math.cos(t) + v * math.sin(t), -u * math.sin(t) + v * math.cos(t)) for u, v in loc]


def zspan(x0, x1, dz, front_up):
    """Axial x range -> scene z range."""
    if front_up:
        return X0 + dz - x1, X0 + dz - x0
    return x0 + dz, x1 + dz


def add_rotor_rc(sc, dz=0.0, cut=(90.0, 360.0), front_up=True, magnets=True, disc=True, combs=True,
                 rings=True, fins=True, step=4.0, layer=0):
    """Rev C drum with 200 blocks (5 skewed rows), comb bars and end rings, cut open between 0 and 90 deg."""
    axial = (X0 + dz, -1) if front_up else (dz, 1)
    for pts in G.DRUM_PARTS.values():
        sc.revolve(pts, DRUM_COL, cut[0], cut[1], step=step, axial=axial, layer=layer)
    if disc:
        sc.revolve(G.DISC_POLY, "#9aa3ad", cut[0], cut[1], step=step, axial=axial, layer=layer)
    if rings:
        for x0, x1 in ((R.SEAT_X[0], R.X_BLOCKS[0]), (R.X_BLOCKS[-1] + R.L, R.SEAT_X[1])):
            prof = [(x0, R.R_IN), (x1, R.R_IN), (x1, R.R_SEAT), (x0, R.R_SEAT)]
            sc.revolve(prof, C["g10"], cut[0], cut[1], step=step, axial=axial, layer=layer, bias=10.0)
    if fins:
        add_fins_ribs(sc, dz, cut, front_up, layer)
    if not magnets:
        return
    for p in range(GEN["poles"]):
        tc = 4.5 + p * POLE
        col = C["mag_n"] if p % 2 == 0 else C["mag_s"]
        for x, sh in zip(R.X_BLOCKS, R.ROW_SHIFT):
            a = tc + sh
            if a - R.SPAN / 2 < cut[0] or a + R.SPAN / 2 > cut[1]:
                continue
            # blocks behind the near half of the drum wall are hidden; leaving them out avoids
            # painter's-order artefacts.
            if not 135.0 <= a <= 315.0:
                continue
            z0, z1 = zspan(x, x + R.L, dz, front_up)
            sc.prism([R.block_outline(90.0 - a)], z0, z1, col, layer=layer, bias=15.0)
            if combs:
                ac = a + POLE / 2
                if ac + 1.5 < cut[1]:
                    sc.prism([comb_loop(ac)], z0 - 0.1, z1 + 0.1, C["grp"], layer=layer, bias=12.0)


def radial_plate(a_deg, r0, r1, t):
    c, s_ = math.cos(math.radians(a_deg)), math.sin(math.radians(a_deg))
    h = t / 2
    return [(r0 * c + h * s_, r0 * s_ - h * c), (r1 * c + h * s_, r1 * s_ - h * c),
            (r1 * c - h * s_, r1 * s_ + h * c), (r0 * c - h * s_, r0 * s_ + h * c)]


FIN_COL = "#b4bcc5"


def add_fins_ribs(sc, dz=0.0, cut=(90.0, 360.0), front_up=True, layer=0):
    """Passive cooling parts on the drum: L-shaped inner fins (front cavity) and outer ribs."""
    f, rb = G.ROTOR_FINS, G.DRUM_RIBS
    for k in range(f["n"]):
        a = 360.0 / f["n"] * k + 5.0
        if not cut[0] + 2 < a < cut[1] - 2:
            continue
        if front_up and cut[0] + 15.0 < a < cut[1] - 15.0:      # front up: hidden under the closed end, keep the cut faces
            continue
        z0, z1 = zspan(f["x0"], f["x1"], dz, front_up)
        sc.prism([radial_plate(a, f["r0"], f["r1"] - 0.5, f["t"])], z0, z1, FIN_COL, layer=layer, bias=5.0)
        z0, z1 = zspan(f["x0"], f["leg_x1"], dz, front_up)
        sc.prism([radial_plate(a, f["leg_r0"], f["r0"], f["t"])], z0, z1, FIN_COL, layer=layer, bias=5.0)
    for k in range(rb["n"]):
        a = 360.0 / rb["n"] * k + 3.75
        if not cut[0] + 1 < a < cut[1] - 1 or 150.0 < a < 300.0:     # far side is hidden behind the drum
            continue
        z0, z1 = zspan(rb["x0"], rb["x1"], dz, front_up)
        sc.prism([radial_plate(a, 318.5, rb["r_tip"], rb["t"])], z0, z1, FIN_COL, layer=layer, bias=5.0)


def add_rear_cover_fan(sc, dz=0.0, cut=(0.0, 360.0), layer=0):
    sc.revolve(G.REAR_COVER, C["al"], cut[0], cut[1], step=5, axial=(X0 + dz, -1), layer=layer)
    z0, z1 = X0 + dz - 465.0, X0 + dz - 465.0 + FAN["h"]
    for k in range(FAN["n"]):
        a = 360.0 / FAN["n"] * k + 7.5
        if a < cut[0] or a > cut[1]:
            continue
        t = math.radians(a)
        c, s_ = math.cos(t), math.sin(t)
        h = FAN["t"] / 2
        lp = [(FAN["r0"] * c + h * s_, FAN["r0"] * s_ - h * c), (FAN["r1"] * c + h * s_, FAN["r1"] * s_ - h * c),
              (FAN["r1"] * c - h * s_, FAN["r1"] * s_ + h * c), (FAN["r0"] * c - h * s_, FAN["r0"] * s_ + h * c)]
        sc.prism([lp], z0, z1, shade_al(), layer=layer)


def shade_al():
    return "#b9c2cc"


# ============================================================ IR01 exploded generator
@fig
def ir01_exploded():
    S = Svg(1300, 1240, "IR01 Exploded generator Rev C")
    S.header("IR01  Generator Rev C pulled apart (isometric, exploded)",
             "Front (hub) end up. Parts go together straight down the middle line, in the order 1 to 5.")
    sc = Scene()
    DZ_ROTOR, DZ_STATOR, DZ_COVER = 520.0, 230.0, -130.0
    add_spindle(sc)
    add_carrier(sc)
    add_stator(sc, dz=DZ_STATOR)
    add_rotor_rc(sc, dz=DZ_ROTOR)
    add_rear_cover_fan(sc, dz=DZ_COVER)
    F = fit(sc, 340, 90, 640, 1110)
    sc.render(S, *F)
    a = sc.proj((0, 0, X0 + DZ_COVER - 480), *F)
    b = sc.proj((0, 0, X0 + DZ_ROTOR - 60), *F)
    S.line(a[0], a[1], b[0], b[1], C["grey"], 1.5, "16,6,4,6")
    zr = X0 + DZ_ROTOR
    tag(S, sc, F, cyl_pt(323, 120, zr - 330), 300, 230, 4, ["ROTOR drum Ø646", "turns with the blades"])
    tag(S, sc, F, cyl_pt(302, 93, zr - 380), 300, 370, None, ["200 N45SH blocks 30×15×12", "glued inside (see IR02)"])
    tag(S, sc, F, cyl_pt(318, 0, zr - 300), 1040, 230, None, ["cut open here so you", "can see inside"])
    tag(S, sc, F, cyl_pt(437, 330, zr - 443), 1040, 380, None, ["brake disc"])
    tag(S, sc, F, cyl_pt(290, 45, X0 + DZ_STATOR - 380), 300, 660, 3, ["STATOR: 45 segments,", "28 turns each"])
    tag(S, sc, F, cyl_pt(70, -20, X0 - 80), 1040, 580, 1, ["SPINDLE: fixed,", "never turns"])
    tag(S, sc, F, cyl_pt(228, 330, X0 - 430), 1040, 780, 2, ["CARRIER: 45 dovetail", "grooves"])
    tag(S, sc, F, cyl_pt(300, 157.5, X0 + DZ_COVER - 456), 300, 1010, 5,
        ["rear cover with 24 fan", "blades (NP1-212C)"])
    S.rect(980, 1050, 300, 150, fill=C["light"], stroke="#c9ced6", rx=8)
    S.lines(995, 1078, ["Order: 1 spindle on the stand,", "2 carrier bolted on, 3 slide", "segments into the grooves,",
                        "4 rotor lowered on (J40),", "5 rear cover, blades inward."], 15, "start")
    return S


# ============================================================ IR02 rotor cut-away
@fig
def ir02_rotor():
    S = Svg(1300, 900, "IR02 Rotor Rev C")
    S.header("IR02  Rotor drum Rev C with its 200 blocks (isometric, cut open)",
             "Open (rear) end up, as on the magnet jig. A quarter is cut away so the five skewed rows can be seen.")
    sc = Scene()
    add_rotor_rc(sc, dz=-80, front_up=False, step=3.0)
    F = fit(sc, 330, 90, 680, 760)
    sc.render(S, *F)
    zm = R.X_BLOCKS[2] - 80 + R.L / 2
    tag(S, sc, F, cyl_pt(R.R_IN, 184.5, zm), 300, 200, 1, ["a pole = 5 blocks along,", "one colour, each row 0.20°"])
    tag(S, sc, F, cyl_pt(R.R_IN, 175.5, zm - 16), 300, 330, 2, ["next pole: other colour", "N, S, N, S ... 40 poles"])
    tag(S, sc, F, cyl_pt(R.R_SEAT - 5, 180.0, zm + 16), 300, 460, 3, ["G11 stepped comb bar", "between the poles"])
    tag(S, sc, F, cyl_pt(316, 90, zm), 1040, 420, 4, ["drum wall (cut)", f"seat Ø{R.SEAT_D:.2f}"])
    tag(S, sc, F, cyl_pt(437, 330, G.DISC_POLY[0][0] - 80 + 8), 1040, 230, 5, ["brake disc", "(open end)"])
    tag(S, sc, F, cyl_pt(R.R_IN + 3, 270.0, R.SEAT_X[1] - 80 - 3), 1040, 580, 6, ["G11 end ring", "(front and rear)"])
    tag(S, sc, F, cyl_pt(292, 245, 270 - 80), 1040, 700, 7, ["36 inner fins (passive", "cooling, front cavity)"])
    tag(S, sc, F, cyl_pt(330, 340, 330 - 80), 1040, 810, 8, ["48 outer ribs, tips Ø676"])
    S.rect(20, 690, 360, 140, fill=C["light"], stroke="#c9ced6", rx=8)
    S.lines(35, 718, ["Glue one row at a time, all 40", "blocks of the row, N and S", "alternating in the comb.",
                      "Every block pulls hard: one at", "a time, in the jig, never two."], 15, "start")
    return S


# ============================================================ IR03 one pole
@fig
def ir03_pole():
    S = Svg(1240, 860, "IR03 One pole Rev C")
    S.header("IR03  One pole of Rev C (isometric), seen from the stator side",
             "Five solid N45SH blocks 30 × 15 × 12 on the drum seat, each row turned 0.20° further. Comb bars either side.")
    sc = Scene()
    z0 = R.X_STACK[0]
    ROT = 90.0

    def Wp(pts):
        c, s_ = math.cos(math.radians(ROT)), math.sin(math.radians(ROT))
        return [(x * c - y * s_, x * s_ + y * c) for x, y in pts]
    a = 7.0
    sc.revolve([(R.SEAT_X[0] - z0, R.R_SEAT), (R.SEAT_X[1] - z0, R.R_SEAT), (R.SEAT_X[1] - z0, 323.0),
                (R.SEAT_X[0] - z0, 323.0)], "#aeb6bf", 180 - a, 180 + a, step=0.5, axial=(0, 1))
    for x0, x1 in ((R.SEAT_X[0], R.X_BLOCKS[0]), (R.X_BLOCKS[-1] + R.L, R.SEAT_X[1])):
        sc.revolve([(x0 - z0, R.R_IN), (x1 - z0, R.R_IN), (x1 - z0, R.R_SEAT), (x0 - z0, R.R_SEAT)], C["g10"],
                   180 - a, 180 + a, step=0.5, axial=(0, 1))
    for x, sh in zip(R.X_BLOCKS, R.ROW_SHIFT):
        for s in (-1, 1):
            sc.prism([Wp(comb_loop(90.0 + s * POLE / 2 - sh))], x - z0 - 0.1, x - z0 + R.L + 0.1, C["grp"])
        sc.prism([Wp(R.block_outline(sh))], x - z0, x - z0 + R.L, C["mag_n"])
    F = fit(sc, 200, 100, 820, 660)
    sc.render(S, *F)
    tag(S, sc, F, (-320.0, 0, R.SEAT_X[1] - z0), 250, 170, 1, [f"drum seat Ø{R.SEAT_D:.2f}", "(x 335 to 425)"])
    cp = comb_loop(90.0 + POLE / 2 - R.ROW_SHIFT[2])
    cx, cy = sum(q[0] for q in cp) / 4, sum(q[1] for q in cp) / 4
    tag(S, sc, F, (*Wp([(cx, cy)])[0], 40), 250, 600, 2, ["stepped comb bar G11,", "one part per gap"])
    tag(S, sc, F, (*Wp([(0, R.R_IN)])[0], 40), 980, 300, 3, ["5 solid blocks, 12 mm thick,", "N face to the stator"])
    tag(S, sc, F, (*Wp([(0, R.R_IN + 2)])[0], R.X_BLOCKS[0] - z0 - 3), 980, 520, 4, ["G11 end ring"])
    S.rect(30, 720, 560, 110, fill=C["light"], stroke="#c9ced6", rx=8)
    S.lines(45, 748, ["Not drawn: glue, glass sleeve.", "Rows step 0.20° = 1.1 mm at the seat; 0.20 mm shims",
                      "between rows (removed after curing)."], 15, "start")
    return S


# ============================================================ IR04 assembled generator, cut
@fig
def ir04_assembled():
    S = Svg(1300, 1100, "IR04 Assembled generator Rev C")
    S.header("IR04  Generator Rev C assembled (isometric, cut in half)",
             "Front end up, the half nearest you cut away. The magnets run 2 mm outside the stator teeth all the way round.")
    sc = Scene()
    cut = (135.0, 315.0)
    add_spindle(sc, th=cut)
    rear = [(415.0, 90.0), (440.0, 90.0), (440.0, 228.0), (417.0, 228.0), (417.0, 200.0), (415.0, 200.0)]
    sc.revolve(rear, FI.CARRIER_COL, cut[0], cut[1], step=6.0, axial=(X0, -1))
    sc.revolve([(343.5, 200.0), (417.0, 200.0), (417.0, GEN["r_si"]), (343.5, GEN["r_si"])], FI.CARRIER_COL,
               cut[0], cut[1], step=4.0, axial=(X0, -1))
    z0, z1 = X0 - G.X_STACK[1], X0 - G.X_STACK[0]
    for k in range(GEN["slots"]):
        ang = 90 + k * FI.PITCH
        a = ang % 360
        if a < cut[0] + 4 or a > cut[1] - 4:
            continue
        FI.add_segment(sc, FI.rotz(k * FI.PITCH), z0, z1, n_arc=3, coil=True)
    add_rotor_rc(sc, cut=cut, step=3.0)
    add_rear_cover_fan(sc, cut=cut)
    F = fit(sc, 330, 120, 660, 900)
    sc.render(S, *F)
    zc = X0 - 380
    tag(S, sc, F, cyl_pt(323, 139, zc + 20), 300, 380, 1, ["rotor drum (turns)"])
    tag(S, sc, F, cyl_pt(R.R_IN + 6, 138.5, zc), 300, 480, 2, ["N45SH blocks, 12 mm", "gap 2.0 mm to the teeth"])
    tag(S, sc, F, cyl_pt(437, 140, X0 - 443), 300, 780, 7, ["brake disc"])
    tag(S, sc, F, cyl_pt(290, 137, X0 - 300), 300, 250, 8, ["36 inner fins (passive cooling)"])
    tag(S, sc, F, cyl_pt(300, 136, X0 - 470), 300, 860, 6, ["rear cover + 24 fan blades"])
    tag(S, sc, F, cyl_pt(285, 316, zc), 1040, 430, 3, ["stator teeth + coils", "(fixed)"])
    tag(S, sc, F, cyl_pt(206, 316, zc + 20), 1040, 560, 4, ["carrier"])
    tag(S, sc, F, cyl_pt(55, 316, X0 - 200), 1040, 330, 5, ["spindle (fixed)"])
    return S


# ============================================================ IR05/IR06 stator views (unchanged design)
@fig
def ir05_segment():
    return FI.i02_segment()


@fig
def ir06_stator():
    return FI.i03_stator()


def main(png=False):
    OUT.mkdir(parents=True, exist_ok=True)
    for fn in FIGS:
        S = fn()
        name = fn.__name__.split("_", 1)
        fname = f"{name[0].upper()}-iso-{name[1]}.svg"
        S.save(OUT / fname)
        print(fname)
    if png:
        import subprocess
        subprocess.run(["node", str(MFG / "render_png.js"), str(OUT)], check=True)


if __name__ == "__main__":
    main("--png" in sys.argv)
