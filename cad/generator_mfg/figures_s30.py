"""Drawings for doc 20 (N42SH 30 x 15 x 6 variant) and its comparison with doc 19 Rev B.

Run:  python3 figures_s30.py [--png]   -> out/D01..D04, out/DI01..DI02
Dimensions from magnet_geom_s30.py (variant) and magnet_geom.py (Rev B).
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import magnet_geom as MG  # noqa: E402
import magnet_geom_s30 as SG  # noqa: E402
import figures_magnets as FM  # noqa: E402
from figures_magnets import P, sector, View, clip_begin, clip_end, comb_pts, STEEL, SLEEVE, GLUE  # noqa: E402
from iso import Scene  # noqa: E402
from svgfig import C, Svg  # noqa: E402
from figures_iso import fit, tag  # noqa: E402

OUT = HERE / "out"
RES = HERE.parent.parent / "analysis" / "generator" / "results"
FIGS = []


def fig(fn):
    FIGS.append(fn)
    return fn


def s30_comb_pts(a_mid):
    wi, wo, h = SG.comb_bar()
    r0, r1 = SG.R_SEAT - h, SG.R_SEAT + 0.3
    t = math.radians(a_mid)
    loc = [(-wi / 2, r0), (wi / 2, r0), (wo / 2, r1), (-wo / 2, r1)]
    return [(u * math.cos(t) + v * math.sin(t), -u * math.sin(t) + v * math.cos(t)) for u, v in loc]


def draw_s30_pole(S, V, a_half, labels=False):
    S.poly(V(sector(SG.R_SEAT, 324.0, -a_half, a_half, 80)), fill=STEEL, sw=1.5)
    S.poly(V(sector(SG.R_SLEEVE_BORE, SG.R_SEAT, -a_half, a_half, 80)), fill=GLUE, stroke="none", sw=0)
    S.poly(V(sector(SG.R_SLEEVE_BORE, SG.R_IN + 0.02, -a_half, a_half, 80)), fill=SLEEVE, sw=1)
    for pole, col in ((0.0, C["mag_n"]), (SG.TAU, C["mag_s"]), (-SG.TAU, C["mag_s"])):
        for layer in (0, 1):
            S.poly(V(SG.block_outline(pole, layer)), fill=col, sw=1.8)
    for s in (-1, 1):
        S.poly(V(s30_comb_pts(s * SG.TAU / 2)), fill=C["grp"], sw=1.5)
    S.poly(V(sector(296.0, SG.R_STATOR, -a_half, a_half, 80)), fill=C["steel_d"], sw=1.5)
    for a in (-4.0, 4.0, -12.0, 12.0):
        S.poly(V(sector(295.9, SG.R_STATOR + 0.02, a - 0.38, a + 0.38, 6)), fill="white", stroke="none", sw=0)


# ============================================================ D01 block and pair
@fig
def d01_block():
    S = Svg(1240, 880, "D01 Detail drawing NP1-220S block 30 x 15 x 6")
    S.header("D01  Detail drawing NP1-220S: N42SH block 30 × 15 × 6 and the bonded pair",
             "Drawn 10× real size. Dimensions in mm. Two blocks are bonded N face to S face into one 12 mm pair (shop step).")
    s = 10.0
    W, L, T = SG.W, SG.L, SG.T
    ch = 5
    x0, y0 = 90, 130
    S.text(x0, y0 - 14, "View A: N face", 15, "start", "bold")
    S.rect(x0, y0, W * s, L * s, fill=C["mag_n"], sw=2.5, rx=4)
    S.circle(x0 + 26, y0 + 26, 9, fill="white", stroke=C["ink"], sw=1.5)
    S.text(x0 + W * s / 2, y0 + L * s / 2 + 10, "N", 30, weight="bold", color="white")
    S.dim(x0, y0 + L * s + 30, x0 + W * s, y0 + L * s + 30, f"{W:.2f} ±0.03 (across)", size=14, color=C["ink"])
    S.dim(x0 - 35, y0 + L * s, x0 - 35, y0, f"{L:.2f} ±0.03", size=14, color=C["ink"])
    S.text(x0 + W * s / 2, y0 + L * s + 70, "(15 runs along the stack)", 13, color=C["grey"])
    fx, fy = 560, 130
    S.text(fx, fy - 14, "View B: end (one block)", 15, "start", "bold")
    S.rect(fx, fy, W * s, T * s, fill=C["mag_n"], sw=2.5, rx=4)
    S.arrow(fx + W * s / 2, fy + T * s - 8, fx + W * s / 2, fy + 10, "white", 5, 14)
    S.dim(fx + W * s + 40, fy + T * s, fx + W * s + 40, fy, f"{T:.2f} ±0.02", size=14, color=C["ink"])
    S.text(fx + W * s + 12, fy + 14, "N", 14, "start", "bold")
    S.text(fx + W * s + 12, fy + T * s, "S", 14, "start", "bold")
    S.text(fx + W * s / 2, fy + T * s + 34, "magnetised through the 6.00 thickness", 14, weight="bold")
    px, py = 560, 330
    S.text(px, py - 14, "View C: bonded pair (one pole position)", 15, "start", "bold")
    for k in range(2):
        S.rect(px, py + k * (T * s + 3), W * s, T * s, fill=C["mag_n"], sw=2.5, rx=4)
        S.arrow(px + W * s / 2, py + k * (T * s + 3) + T * s - 8, px + W * s / 2, py + k * (T * s + 3) + 10,
                "white", 4, 12)
    S.dim(px + W * s + 40, py + 2 * T * s + 3, px + W * s + 40, py, "12.05 ±0.06", size=14, color=C["ink"])
    S.lines(880, py + 2 * T * s + 40, ["N face of one block on the S face of the other:",
                                                  "they pull together. Thin epoxy 0.02 to 0.05, edges flush ±0.05."],
            13)
    S.rect(90, 480, 420, 130, fill=C["light"], stroke="#c9ced6", rx=6)
    S.lines(105, 508, ["Flatness of N and S faces 0.02", "Parallelism N to S face 0.02",
                       "Chamfer 0.2 to 0.3 × 45°, all 12 edges", "Magnetic axis within 2° of the face normal"], 14,
            "start")
    tx, ty, tw = 560, 560, 650
    rows = [("Part", "NP1-220S  N42SH block, catalogue 30 × 15 × 6"),
            ("Material", "Sintered NdFeB N42SH: Br ≥ 1.29 T, HcJ ≥ 1,592 kA/m (20 kOe)"),
            ("Coating", "NiCuNi ≥ 15 µm + epoxy ≥ 15 µm (in the sizes)"),
            ("Mark", "White dot Ø3 on the N face"),
            ("Mass", f"{SG.MASS_G:.1f} g each"),
            ("Quantity", f"{SG.COUNT} + {SG.SPARES} spare per generator (200 pairs)"),
            ("Moment", "Each piece within ±1.5 % of the lot mean, value per serial")]
    S.rect(tx, ty, tw, 30 * len(rows), fill="white", stroke=C["ink"], sw=2)
    for i, (a, b) in enumerate(rows):
        yy = ty + 30 * i
        S.line(tx, yy, tx + tw, yy, C["grey"], 1)
        S.text(tx + 10, yy + 21, a, 14, "start", "bold")
        S.text(tx + 115, yy + 21, b, 13, "start")
    S.line(tx + 105, ty, tx + 105, ty + 30 * len(rows), C["grey"], 1)
    S.text(tx + 10, ty + 30 * len(rows) + 22, "Doc 20 · Wind turbine 12 kW · P1 generator, N42SH variant", 13,
           "start", color=C["grey"])
    return S


# ============================================================ D02 pole section
@fig
def d02_pole():
    S = Svg(1240, 880, "D02 One pole of the N42SH variant")
    S.header("D02  One pole of the N42SH variant (cross-section, 20× real size)",
             "One 30 mm wide pair of blocks (12 mm) per pole, wide comb bars between the poles.")
    V = View(620, 420, 20.0, 307.0)
    clip_begin(S, 100, 170, 1040, 500)
    draw_s30_pole(S, V, 7.0)
    clip_end(S)
    c = V.pt(*P(SG.R_IN + SG.H / 2, 0.0))
    S.arrow(c[0], c[1] + 90, c[0], c[1] - 90, "white", 5, 14)
    S.line(620, 180, 620, 660, C["grey"], 1, "14,5,3,5")
    g = SG.summary()
    lab = [((P(SG.R_SEAT + 3.5, -2.5)), 260, True, [f"drum seat Ø{SG.SEAT_D:.2f} +0.05/0", f"yoke under it {g['yoke']:.1f} mm"]),
           ((P(SG.R_BACK + 0.2, 1.8)), 640, True, [f"bond {g['bond_mid']:.2f} under the middle,", "0.15 at the corners"]),
           ((P(SG.R_SEAT - 4, 4.5)), 1020, True, ["comb bar NP1-221S (G11), stepped",
                                                 f"{g['comb_w_in']:.1f} → {g['comb_w_out']:.1f} wide, {g['comb_h']:.0f} high"]),
           ((P(SG.R_IN + 3, -1.0)), 300, False, ["pair of blocks, 2 × 6.00 = 12", "magnetised the same way"]),
           ((P(SG.R_IN + 0.1, 2.4)), 640, False, [f"inner face r {SG.R_IN:.2f} at the centre,",
                                                  f"sleeve {g['sleeve_min']:.2f} to {g['sleeve_max']:.2f}"]),
           ((P(SG.R_STATOR - 1, 5.0)), 1000, False, ["stator r 299.0, gap 2.0", "(unchanged)"])]
    for (wx, wy), tx, top, rows in lab:
        x, y = V.pt(wx, wy)
        ty = 150 if top else 700
        S.line(x, y, tx, ty + (8 if top else -8), C["ink"], 1.3)
        S.circle(x, y, 3.5, fill=C["ink"], stroke="white", sw=1)
        S.lines(tx, ty - 18 if top else ty + 12, rows, 13)
    S.rect(300, 770, 640, 92, fill=C["light"], stroke="#c9ced6", rx=6)
    S.lines(620, 795, [f"Pole pitch 9.000°, pole span {SG.SPAN:.2f}° ({SG.SPAN / SG.TAU:.2f}), block {SG.W:.0f} wide",
                       f"Five rows along the stack, turned {SG.SKEW_STEP:.2f}° from row to row",
                       f"(front −{max(SG.ROW_SHIFT):.1f}° … rear +{max(SG.ROW_SHIFT):.1f}° from the drawn centre)"], 14)
    return S


# ============================================================ D03 layout
@fig
def d03_layout():
    S = Svg(1240, 820, "D03 Where every block goes, N42SH variant")
    S.header("D03  Where every block goes (N42SH variant): drum seat unrolled",
             "6 of the 40 poles. Each pole = 5 rows along the stack, each row a pair of blocks. Rows step 0.20° (1.1 mm).")
    px, y2 = 80, 120
    pw = 172
    mm = pw / (2 * math.pi * SG.R_SEAT / SG.POLES)
    sc = 6.0
    ring = SG.RING_W * sc
    bw = SG.W * mm
    bl = SG.L * sc
    comb_w = SG.comb_bar()[1] * mm
    xs = [px + p * pw for p in range(7)]
    ys = [y2 + ring + i * (SG.L + SG.SHIM) * sc for i in range(SG.N_AX)]
    shift = [d / SG.TAU * pw for d in SG.ROW_SHIFT[::-1]]      # top row = rear row
    for yy, dx in zip(ys, shift):
        for p in range(7):
            S.rect(xs[p] - comb_w / 2 + dx, yy - 0.5, comb_w, bl + SG.SHIM * sc + 0.5, fill=C["grp"], stroke="none")
        for p in range(6):
            n = p % 2 == 0
            xb = xs[p] + pw / 2 + dx - bw / 2
            S.rect(xb, yy, bw, bl, fill=C["mag_n"] if n else C["mag_s"], rx=3)
            S.text(xb + bw / 2, yy + bl / 2 + 7, "N" if n else "S", 18, weight="bold", color="white")
            if n:
                S.circle(xb + 10, yy + 10, 4, fill="white", stroke="none")
    ph = SG.ROWS_LEN * sc
    x_end = xs[-1] + 40
    S.rect(px - 40, y2, x_end - px + 40, ring, fill=C["grp"])
    S.rect(px - 40, y2 + ring + ph, x_end - px + 40, ring, fill=C["grp"])
    st0 = y2 + ring + SG.OVERHANG * sc
    S.rect(px - 40, st0, x_end - px + 40, SG.STACK * sc, fill="none", stroke=C["steel_d"], sw=2.5)
    for p in range(6):
        S.text(xs[p] + pw / 2, y2 + 2 * ring + ph + 30, f"pole {p + 1}", 14, weight="bold")
    S.text(px + 520, y2 - 8, "rear end ring NP1-222S (7.1 wide)", 13)
    S.text(px + 520, y2 + 2 * ring + ph + 54, "front end ring NP1-222S", 13)
    S.dim(1160, y2 + ring, 1160, y2 + ring + ph, f"{SG.ROWS_LEN:.1f} = 5 × 15 + 4 × 0.2", size=13, color=C["ink"])
    S.dim(1210, st0, 1210, st0 + SG.STACK * sc, "stator stack 74 (grey frame)", size=13, color=C["steel_d"])
    yl = y2 + 2 * ring + ph + 90
    S.legend(80, yl, [(C["grp"], "tan = G11 stepped comb bars and end rings")], 14)
    S.lines(640, yl + 8, [f"• rows turned {SG.SKEW_STEP:.2f}° from one to the next (0.80° front to rear)",
                          "• the comb bar is ONE stepped G11 part per gap: the steps set the skew",
                          "• white dot visible = N pole; N and S alternate"], 14, "start")
    return S


# ============================================================ D04 comparison
@fig
def d04_compare():
    rb = {r["key"]: r for r in json.loads((RES / "magnets_summary.json").read_text())}
    sv = json.loads((RES / "sh30_S1d.json").read_text())
    S = Svg(1240, 1000, "D04 Rev B and the N42SH variant side by side")
    S.header("D04  Rev B (40 × 20 × 7.5) and the N42SH variant (30 × 15 × 6 pairs)",
             "Same stator, gap, sleeve and drum outside. One pole cut across, 12× real size.")
    for i in range(2):
        x = 20 + i * 610
        S.rect(x, 80, 590, 400, fill="white", stroke=C["ok"] if i == 1 else "#c9ced6", sw=3 if i == 1 else 2, rx=10)
        S.text(x + 20, 112, ["Rev B: 2 blocks 20 wide, 7.5", "N42SH variant: 1 pair 30 wide, 12"][i], 19, "start",
               "bold")
        V = View(x + 295, 300, 12.0, 308.0)
        clip_begin(S, x + 10, 125, 570, 345)
        if i == 0:
            FM.draw_pole_section(S, V, "flat", 2, MG.H, cat=True)
        else:
            draw_s30_pole(S, V, 7.0)
        clip_end(S)
    c = rb["C2t"]
    sk = c["skewed_rows"]
    rows = [("", "Rev B (doc 19)", "N42SH variant (doc 20)"),
            ("Block", "40 × 20 × 7.5", "30 × 15 × 6, bonded in pairs"),
            ("Grade", "N40EH / N40UH", "N42SH"),
            ("Pieces per generator", "160 + 8", "400 + 20"),
            ("Magnet mass", f"{c['magnet_mass_kg']:.2f} kg", f"{sv['magnet_kg']:.2f} kg"),
            ("Pole span / rows / skew", "0.85 / 2 / 0.50°", "0.63 / 5 / 4 × 0.20°"),
            ("Drum seat / yoke under it", f"Ø{MG.SEAT_D:.2f} × 96 / 13.7 mm", f"Ø{SG.SEAT_D:.2f} × 90 / {SG.YOKE:.1f} mm"),
            ("Turns per coil", "28", "29"),
            ("Line EMF, 100 °C", f"{c['no_load']['line_emf_178rpm_100C_V'] * sk['emf_factor']:.0f} V",
             f"{sv['line_emf_100C_V'] * 29 / 28:.0f} V"),
            ("Torque at the same phase current", "787 Nm", f"{sv['torque_at_sizing_current_100C_Nm'] * 29 / 28:.0f} Nm"),
            ("Copper loss at rated torque", "reference", "+ 8 %"),
            ("Cogging (skewed)", f"{sk['cogging_pp_Nm']:.2f} Nm", f"{sv['cogging_skewed_pp_Nm']:.2f} Nm"),
            ("Magnet eddy loss, rated", "15.5 W", f"{rb['S1d']['eddy_loss_rated_W']['catalogue_pieces']:.1f} W"),
            ("Worst short circuit margin, 100 / 120 °C", "N40EH –/47 %, N40UH –/30 %",
             f"{sv['demag_margin_pct']['100C']['transient_sc_d']:.0f} / {sv['demag_margin_pct']['120C']['transient_sc_d']:.0f} %"),
            ("Sourcing", "Dy/Tb heavy, mostly China", "SH: little Dy/Tb, EU/US makers")]
    y0 = 500
    S.rect(20, y0, 1200, 30 * len(rows) + 10, fill="white", stroke=C["ink"], sw=1.5)
    for i, (a, b, d) in enumerate(rows):
        yy = y0 + 8 + 30 * i
        if i % 2:
            S.rect(21, yy, 1198, 30, fill=C["light"], stroke="none")
        w = "bold" if i == 0 else "normal"
        S.text(36, yy + 21, a, 14, "start", "bold")
        S.text(470, yy + 21, b, 14, "start", w)
        S.text(850, yy + 21, d, 14, "start", w)
    return S


# ============================================================ DI01 iso of one pole
@fig
def di01_pole():
    S = Svg(1240, 860, "DI01 One pole of the N42SH variant in 3D")
    S.header("DI01  One pole of the N42SH variant (isometric), seen from the stator side",
             "Five rows of bonded pairs on the drum seat, each row turned 0.20° further. Stepped comb bars either side.")
    sc = Scene()
    z0 = SG.X_STACK[0]
    ROT = 90.0
    LIFT = 0.0

    def Wp(pts, lift):
        c, s_ = math.cos(math.radians(ROT)), math.sin(math.radians(ROT))
        return [(x * c - (y - lift) * s_, x * s_ + (y - lift) * c) for x, y in pts]
    a = 7.0
    sc.revolve([(SG.SEAT_X[0] - z0, SG.R_SEAT), (SG.SEAT_X[1] - z0, SG.R_SEAT), (SG.SEAT_X[1] - z0, 323.0),
                (SG.SEAT_X[0] - z0, 323.0)], STEEL, 180 - a, 180 + a, step=0.5, axial=(0, 1))
    for x, sh in zip(SG.X_BLOCKS, SG.ROW_SHIFT):
        for s in (-1, 1):
            sc.prism([Wp(s30_comb_pts(s * SG.TAU / 2 + sh), 0)], x - z0 - 0.1, x - z0 + SG.L + 0.1, C["grp"])
        for layer in (1, 0):
            sc.prism([Wp(SG.block_outline(sh, layer), LIFT * (1 + layer * 0.0))], x - z0, x - z0 + SG.L,
                     C["mag_n"])
    F = fit(sc, 200, 100, 820, 660)
    sc.render(S, *F)
    tag(S, sc, F, (-318.0, 0, 70), 250, 170, 1, [f"drum seat Ø{SG.SEAT_D:.2f}", "(x 335 to 425, as doc 18)"])
    cp = s30_comb_pts(SG.TAU / 2 + SG.ROW_SHIFT[2])
    cx, cy = sum(q[0] for q in cp) / 4, sum(q[1] for q in cp) / 4
    tag(S, sc, F, (*Wp([(cx, cy)], 0)[0], 40), 250, 600, 2, ["stepped comb bar G11,", "one part per gap"])
    tag(S, sc, F, (*Wp([(0, SG.R_IN)], LIFT)[0], 40), 980, 300, 3, ["5 pairs of blocks (10 blocks),",
                                                                 "N face towards the stator"])
    S.rect(30, 720, 520, 110, fill=C["light"], stroke="#c9ced6", rx=8)
    S.lines(45, 748, ["Not drawn: glue, end rings, glass sleeve.", "Rows step 0.20° = 1.1 mm at the seat."], 15,
            "start")
    return S


def main(png=False):
    for fn in FIGS:
        Sv = fn()
        name = fn.__name__.split("_", 1)
        fname = f"{name[0].upper()}-{name[1]}.svg"
        Sv.save(OUT / fname)
        print(fname)
    if png:
        import subprocess
        tmp = OUT / "_d"
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
