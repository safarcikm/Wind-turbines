"""Step-by-step picture instructions for the P1 generator (doc 18).

Run:  python3 figures.py          -> out/G01..G19 *.svg
      python3 figures.py --png    -> also PNG copies (needs Node + Playwright)

Drawings that show real parts (overview, segment, slot and layer plan,
connection ring, potting envelope, drum, sleeve mandrel) are computed from
cad/nacelle_p1/geometry.py and analysis/generator/manufacturing.py, so they
follow any change of the design. The rest are simplified "how to" pictures.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "nacelle_p1"))
import geometry as G  # noqa: E402
from svgfig import C, Svg  # noqa: E402

OUT = HERE / "out"
OUT.mkdir(exist_ok=True)
GEN = G.GEN
FIGS = []


def fig(fn):
    FIGS.append(fn)
    return fn


# ============================================================ shared shapes
def polar(r, th_deg):
    t = math.radians(th_deg)
    return r * math.sin(t), r * math.cos(t)


def segment_world(n_arc=8):
    """One stator segment (tooth on +Y), world mm. Same magnetic contour as the
    one-piece lamination; joints on the slot centrelines (±4°); dovetail foot."""
    half = 180.0 / GEN["slots"]                      # 4°
    wt2 = GEN["w_t"] / 2
    th_f = math.degrees(math.asin(wt2 / GEN["r_slot_bot"]))
    th_t1 = half - math.degrees(GEN["b0"] / 2 / (GEN["r_s"] - GEN["h_tip"]))
    th_t2 = half - math.degrees(GEN["b0"] / 2 / GEN["r_s"])
    r_si = GEN["r_si"]
    th_foot = math.degrees(math.asin(7.0 / r_si))
    R = [(0.0, r_si - 6.0), (10.46, r_si - 6.0), (7.0, math.sqrt(r_si ** 2 - 49))]
    R += [polar(r_si, th_foot + (half - th_foot) * i / n_arc) for i in range(1, n_arc + 1)]
    R += [polar(GEN["r_slot_bot"], half - (half - th_f) * i / n_arc) for i in range(0, n_arc + 1)]
    R += [(wt2, math.sqrt(GEN["r_slot_top"] ** 2 - wt2 ** 2)),
          polar(GEN["r_s"] - GEN["h_tip"], th_t1), polar(GEN["r_s"], th_t2)]
    R += [polar(GEN["r_s"], th_t2 * (1 - i / n_arc)) for i in range(1, n_arc + 1)]
    L = [(-x, y) for x, y in reversed(R[1:-1])]
    return R + L


def to_screen(pts, cx, cy, s, y0=0.0, rot=0.0):
    out = []
    c, sn = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    for x, y in pts:
        y = y - y0
        xr, yr = x * c - y * sn, x * sn + y * c
        out.append((cx + s * xr, cy - s * yr))
    return out


def seg_side(S, x, y, w, h, coil=False, caps=False, liner=False):
    """Side view of a segment (stack length horizontal, tooth up)."""
    S.rect(x, y + h * 0.55, w, h * 0.45, fill=C["steel_d"])          # yoke + foot
    S.rect(x, y, w, h * 0.55, fill=C["steel"])                       # tooth
    for i in range(1, 12):
        S.line(x + w * i / 12, y + 2, x + w * i / 12, y + h - 2, "#9aa3ad", 1)
    if caps:
        S.rect(x - 10, y + 4, 10, h * 0.55, fill=C["pps"])
        S.rect(x + w, y + 4, 10, h * 0.55, fill=C["pps"])
    if liner:
        S.rect(x - 6, y + h * 0.53, w + 12, 6, fill=C["liner"], sw=1)
    if coil:
        S.rect(x - 22, y + 6, w + 44, h * 0.47, fill=C["cu"], rx=10)
        for i in range(1, 6):
            S.line(x - 18, y + 6 + h * 0.47 * i / 6, x + w + 18, y + 6 + h * 0.47 * i / 6, C["cu_l"], 1.5)


def magnet_piece(S, x, y, w, h, n=True, dot=True):
    S.rect(x, y, w, h, fill=C["mag_n"] if n else C["mag_s"], rx=3)
    S.text(x + w / 2, y + h / 2 + 7, "N" if n else "S", 20, weight="bold", color="white")
    if dot:
        S.circle(x + w - 9, y + 9, 5, fill="white" if n else "white", stroke="none")


def drum_section_world():
    return G.DRUM_PARTS


# ============================================================ G01 overview
@fig
def g01_overview():
    S = Svg(1200, 820, "G01 What we are building")
    S.header("G01  What we are building: the P1 generator, cut in half",
             "Real shape and size from geometry.py. Only the top half is drawn; the bottom half is the same.")
    s, ox, oy = 1.55, 40, 760

    def P(pts):
        return [(ox + s * (x - 30), oy - s * r) for x, r in pts]

    # rotor (turns) parts
    hub = [(150, 120), (200, 120), (200, 240), (150, 240)]
    S.poly(P(hub), fill="#eeeeee", dash="6,5", stroke=C["grey"])
    S.text(ox + s * (160 - 30), oy - s * 250, "hub", 14, color=C["grey"])
    for name, pts in G.DRUM_PARTS.items():
        S.poly(P(pts), fill=C["steel"])
    S.poly(P(G.DISC_POLY), fill="#9aa3ad")
    S.poly(P(G.REAR_COVER), fill=C["al"])
    S.poly(P(G.REAR_SEAL_CARRIER), fill=C["al"])
    S.poly(P(G.SEAL_COVER_FRONT), fill=C["steel"])
    S.poly(P(G.SEAL_COVER_REAR), fill=C["steel"])
    m = G.MAGNET
    S.poly(P([(343, m["r_in"]), (417, m["r_in"]), (417, m["r_out"]), (343, m["r_out"])]), fill=C["mag_n"])
    S.poly(P([(343, m["r_in"] - 0.6), (417, m["r_in"] - 0.6), (417, m["r_in"]), (343, m["r_in"])]),
           fill=C["resin"], sw=1)
    # bearings
    for xc in (G.X_BRG_FRONT, G.X_BRG_REAR):
        S.poly(P([(xc - 22.5, 70), (xc + 22.5, 70), (xc + 22.5, 105), (xc - 22.5, 105)]), fill="#ffe08a")
        S.line(ox + s * (xc - 22.5 - 30), oy - s * 70, ox + s * (xc + 22.5 - 30), oy - s * 105, C["ink"], 1.5)
    # stationary parts
    S.poly(P(G.spindle_section()), fill="#8a95a5")
    S.poly(P([(46, 20), (466, 20), (466, 45), (46, 45)]), fill=C["al"], sw=1.5)
    S.poly(P(G.SPACER_POLY), fill="#8a95a5")
    S.poly(P(G.SEAL_SLEEVE_POLY), fill="#8a95a5")
    S.poly(P(G.CARRIER), fill="#6f7b8a")
    S.poly(P(G.STATOR_RING), fill="#d5d9de")
    S.poly(P(G.STACK_POLY), fill="#5f6b7a")
    for i in range(1, 15):
        x = 343 + 74 * i / 15
        S.line(ox + s * (x - 30), oy - s * GEN["r_si"], ox + s * (x - 30), oy - s * GEN["r_s"], "#8792a0", 1)
    for x0, x1 in ((321, 343), (417, 439)):
        S.poly(P([(x0, 232), (x1, 232), (x1, 294), (x0, 294)]), fill=C["cu"], sw=1.5)
    # axis
    S.line(ox, oy, ox + s * 460, oy, C["grey"], 1.5, "18,6,4,6")
    S.text(ox + s * 455, oy - 8, "axis", 13, "end", color=C["grey"])
    S.arrow(ox + 160, oy + 30, ox + 30, oy + 30, C["grey"], 2)
    S.text(ox + 170, oy + 35, "front: towards the blades", 13, "start", color=C["grey"])

    labels = [
        (443, 400, ["Brake disc (turns)"]),
        (470, 300, ["Rear cover (turns)"]),
        (300, 316, ["Rotor drum (turns)"]),
        (380, 306, ["Magnets (160 pieces)", "glued inside the drum"]),
        (395, 301, ["Glass sleeve 0.5 mm", "covers the magnets"]),
        (432, 270, ["Coil ends (potted)"]),
        (380, 250, ["Stator: 45 tooth segments", "with copper coils"]),
        (428, 150, ["Stator carrier (still)"]),
        (360, 95, ["Rear main bearing"]),
        (120, 95, ["Front main bearing"]),
        (250, 60, ["Spindle (still)"]),
        (300, 32, ["Cooling insert (air)"]),
    ]
    for i, (x, r, lab) in enumerate(labels):
        S.leader(ox + s * (x - 30), oy - s * r, 850, 95 + i * 50, lab, 15)
    S.rect(840, 700, 340, 100, fill=C["light"], stroke="#c9ced6", rx=8)
    S.lines(855, 727, ["Air gap: 2.0 mm between the sleeve", "and the stator teeth. Everything in",
                       "this document protects that gap."], 15, "start")
    return S


# ============================================================ G02 process map
@fig
def g02_process():
    S = Svg(1200, 560, "G02 The three work tracks")
    S.header("G02  The order of work: two tracks side by side, then they meet",
             "Each box is one operation in section 3. Do them left to right. Do not skip a test box.")
    st = ["S20 Cut", "S30 Bond", "S40 Check", "S60 Insulate", "S70 Wind", "Test coil",
          "S80 Assemble", "S90 Connect", "Test", "S100 VPI", "S110 Pot", "S120 Test"]
    ro = ["R10 Weld", "R20 Machine", "R30 Balance", "R40 Comb", "R50 Sort",
          "R60 Glue", "R70 Pole map", "R80 Sleeve", "R90 Finish"]
    tests = {"S40 Check", "Test coil", "Test", "S120 Test", "R30 Balance", "R70 Pole map"}

    def row(items, y, col, label):
        S.text(20, y + 30, label, 17, "start", "bold", col)
        w, gap, x0 = 78, 10, 140
        for i, t in enumerate(items):
            x = x0 + i * (w + gap)
            f = "#fff3bf" if t in tests else "white"
            S.rect(x, y, w, 52, fill=f, stroke=col, sw=2.5, rx=8)
            parts = t.split(" ", 1)
            S.lines(x + w / 2, y + 22 if len(parts) > 1 else y + 31, parts, 13, weight="bold")
            if i < len(items) - 1:
                S.arrow(x + w + 1, y + 26, x + w + gap - 1, y + 26, col, 2, 7)
        return x0 + len(items) * (w + gap) - gap

    xe1 = row(st, 110, "#5f6b7a", "STATOR")
    xe2 = row(ro, 260, C["mag_n"], "ROTOR")
    jy = 400
    yb = jy + 30
    S.poly([(xe1, 136), (xe1 + 12, 136), (xe1 + 12, yb), (195, yb)], stroke="#5f6b7a", sw=3, closed=False)
    S.poly([(xe2, 286), (xe2 + 30, 286), (xe2 + 30, yb + 8), (205, yb + 8)], stroke=C["mag_n"], sw=3, closed=False)
    S.arrow(200, yb + 8, 200, jy + 66, C["ink"], 3)
    S.text(xe2 + 40, yb - 8, "both finished? then join", 14, "start", "bold")
    for i, t in enumerate(["J10 Spindle", "J20 Stator on", "J30 Sleeve+cone", "J40 Rotor over",
                           "J50 Front brg", "J60 Cover+gap"]):
        x = 140 + i * 122
        S.rect(x, jy + 70, 112, 52, fill="#fff3bf" if "gap" in t else "white", stroke=C["ink"], sw=2.5, rx=8)
        a_, b_ = t.split(" ", 1)
        S.lines(x + 56, jy + 92, [a_, b_], 13, weight="bold")
        if i < 5:
            S.arrow(x + 113, jy + 96, x + 121, jy + 96, C["ink"], 2, 7)
    S.text(20, jy + 100, "JOIN", 17, "start", "bold")
    S.rect(880, 470, 300, 70, fill="#fff3bf", stroke=C["warn"], sw=2, rx=8)
    S.lines(895, 498, ["Yellow boxes are checks. Fails?", "Stop, mark it, tell Cat. 4."], 15, "start")
    S.warn(150 + 4 * 88 + 39, 92, 22)
    S.text(150 + 4 * 88 + 56, 97, "Q1 trial first (section 10)", 13, "start", "bold", C["warn"])
    return S


# ============================================================ G03 segment
@fig
def g03_segment():
    S = Svg(1200, 760, "G03 One segment sheet")
    S.header("G03  One segment sheet (NP1-201 Rev C): 0.35 mm thin, cut by laser",
             "Drawn to scale from the frozen design. 205 sheets glued together make one segment; 45 segments make the stator.")
    s, cx, cy = 6.4, 380, 730
    y0 = GEN["r_si"] - 8
    pts = to_screen(segment_world(), cx, cy, s, y0)
    S.poly(pts, fill=C["steel"], sw=2.5)
    # dims
    yt = lambda r: cy - s * (r - y0)  # noqa: E731
    wt2 = GEN["w_t"] / 2
    S.dim(cx - s * wt2, yt(265), cx + s * wt2, yt(265), "tooth 22.3")
    tip = 2 * math.pi * GEN["r_s"] / GEN["slots"] - GEN["b0"]
    S.dim(cx - s * tip / 2, yt(GEN["r_s"]) - 4, cx + s * tip / 2, yt(GEN["r_s"]) - 4, "tip 37.7", off=-22)
    S.dim(cx + s * 26, yt(GEN["r_slot_bot"]), cx + s * 26, yt(GEN["r_slot_top"]), "slot 65", off=0)
    S.dim(cx - s * 7, yt(GEN["r_si"]) + 30, cx + s * 7, yt(GEN["r_si"]) + 30, "14", size=13)
    S.leader(cx + s * 8, yt(GEN["r_si"] - 3), 650, 640, ["Dovetail foot, 6 mm deep:", "slides into the carrier groove"])
    S.leader(cx + s * 15.3, yt(GEN["r_si"] + 6), 650, 560, ["Joint face: touches the", "next segment (8.00° wide)"])
    S.leader(cx + s * 17, yt(GEN["r_s"] - 2.5), 650, 230, ["Wedge seat under the tip:", "the slot wedge slides in here"])
    S.leader(cx, yt(GEN["r_s"]), 650, 150, ["Tooth tip faces the magnets", "(air gap side). Keep it clean."])
    S.arrow(130, 600, 130, 260, C["ok"], 5, 20)
    S.lines(130, 640, ["Rolling", "direction", "of the steel"], 15, weight="bold", color=C["ok"])
    # small ring
    rx, ry, rs = 1045, 575, 0.40
    for k in range(GEN["slots"]):
        S.poly(to_screen(segment_world(4), rx, ry, rs, 0, rot=-k * 8.0), fill=C["steel"] if k else C["warn"], sw=0.8)
    S.text(rx, ry + 5, "45 segments", 15, weight="bold")
    S.text(rx, ry + 25, "= one ring Ø598", 14)
    S.rect(650, 300, 520, 70, fill=C["light"], stroke="#c9ced6", rx=8)
    S.lines(665, 328, ["Burr max 0.02 mm, all burrs on the same side.", "Never anneal (it burns off the glue layer)."], 15, "start")
    return S


# ============================================================ G04 stacking
@fig
def g04_stacking():
    S = Svg(1200, 430, "G04 Stack and bond a segment")
    S.header("G04  Stack and bond one segment (fixture NP1-T03)")
    W, H, y = 280, 330, 80
    xs = [20, 315, 610, 905]
    # 1 count
    x = xs[0]
    S.panel(x, y, W, H, 1, ["Count 205 sheets by weight", "(≈ 5.5 g each, ±1 sheet)"])
    S.rect(x + 60, y + 180, 160, 40, fill="#dde1e6", rx=4)
    S.rect(x + 50, y + 220, 180, 16, fill=C["grey"], rx=4)
    S.text(x + 140, y + 207, "1123 g", 18, weight="bold")
    for i in range(10):
        S.rect(x + 85, y + 172 - i * 5, 110, 4, fill=C["steel"], sw=1)
    S.text(x + 140, y + 90, "mix sheets from", 14)
    S.text(x + 140, y + 108, "3 places of the coil", 14)
    # 2 load fixture
    x = xs[1]
    S.panel(x, y, W, H, 2, ["Slide them onto the dovetail", "mandrel, burrs all one way"])
    S.rect(x + 50, y + 225, 180, 20, fill=C["grey"])
    S.rect(x + 125, y + 70, 30, 160, fill="#8a95a5")
    for i in range(14):
        S.rect(x + 75, y + 215 - i * 10, 130, 7, fill=C["steel"], sw=1)
    S.arrow(x + 230, y + 70, x + 210, y + 110, C["ink"], 3)
    # 3 press + heat
    x = xs[2]
    S.panel(x, y, W, H, 3, ["Press and heat as the steel", "maker says, cool under load"])
    S.rect(x + 60, y + 80, 160, 22, fill=C["hot"])
    S.rect(x + 60, y + 238, 160, 22, fill=C["hot"])
    for i in range(13):
        S.rect(x + 75, y + 228 - i * 10, 130, 7, fill=C["steel"], sw=1)
    for xx in (x + 90, x + 190):
        S.arrow(xx, y + 45, xx, y + 76, C["ink"], 4)
    S.thermo(x + 245, y + 160, "")
    S.text(x + 140, y + 66, "1–3 MPa", 14, weight="bold")
    # 4 measure
    x = xs[3]
    S.panel(x, y, W, H, 4, ["Measure: 74.0 ± 0.1 mm.", "Wrong? Change sheet count."])
    S.rect(x + 90, y + 100, 70, 148, fill=C["steel"])
    for i in range(1, 14):
        S.line(x + 90, y + 100 + i * 11, x + 160, y + 100 + i * 11, "#9aa3ad", 1)
    S.dim(x + 185, y + 248, x + 185, y + 100, "74.0", size=16, color=C["ink"])
    S.tick(x + 240, y + 120)
    S.text(x + 240, y + 155, "74.0", 14, weight="bold")
    S.cross(x + 240, y + 200)
    S.text(x + 240, y + 235, "no shims", 14, weight="bold", color=C["bad"])
    return S


# ============================================================ G05 insulate
@fig
def g05_insulate():
    S = Svg(1200, 430, "G05 Insulate a segment")
    S.header("G05  Dress the segment before winding: end caps and slot liner")
    W, H, y = 280, 330, 80
    xs = [20, 315, 610, 905]
    x = xs[0]
    S.panel(x, y, W, H, 1, ["Blow off dust, wipe the", "flanks with isopropanol"])
    seg_side(S, x + 70, y + 120, 140, 90)
    S.path(f"M{x + 40},{y + 100} q20,-30 40,0 q20,30 40,0", stroke=C["vac"], sw=4)
    x = xs[1]
    S.panel(x, y, W, H, 2, ["Push an end cap on each", "tooth end (front and rear)"])
    seg_side(S, x + 70, y + 120, 140, 90, caps=True)
    S.arrow(x + 30, y + 145, x + 55, y + 145, C["ink"], 3)
    S.arrow(x + 250, y + 145, x + 225, y + 145, C["ink"], 3)
    S.text(x + 140, y + 105, "PPS end caps", 14, weight="bold")
    # 3 liner in cross-section
    x = xs[2]
    S.panel(x, y, W, H, 3, ["Fold the yellow liner along", "both slot flanks"])
    pts = to_screen(segment_world(), x + 140, y + 255, 2.2, GEN["r_si"] - 8)
    S.poly(pts, fill=C["steel"])
    yy = lambda r: y + 255 - 2.2 * (r - GEN["r_si"] + 8)  # noqa: E731
    wt = GEN["w_t"] / 2 * 2.2
    for sgn in (-1, 1):
        S.poly([(x + 140 + sgn * wt, yy(GEN["r_slot_top"])), (x + 140 + sgn * (wt + 3), yy(GEN["r_slot_top"])),
                (x + 140 + sgn * (wt + 3), yy(GEN["r_slot_bot"]) - 3),
                (x + 140 + sgn * 38, yy(GEN["r_slot_bot"]) - 3), (x + 140 + sgn * 38, yy(GEN["r_slot_bot"])),
                (x + 140 + sgn * wt, yy(GEN["r_slot_bot"]))], fill=C["liner"], sw=1.2)
    S.text(x + 140, y + 62, "0.30 mm NKN liner", 14, weight="bold")
    x = xs[3]
    S.panel(x, y, W, H, 4, ["Run a dummy wire around:", "it must never catch"])
    seg_side(S, x + 70, y + 140, 140, 90, caps=True, liner=True)
    S.path(f"M{x + 50},{y + 140} C{x + 50},{y + 95} {x + 230},{y + 95} {x + 230},{y + 140}", stroke=C["cu"], sw=4)
    S.tick(x + 140, y + 92)
    return S


# ============================================================ G06 winding
def layer_positions():
    """Wire centres of one coil side, slot-local coords (u from tooth flank, r radial)."""
    pitch, liner, sep = 1.70, 0.30, 0.25
    tau = 360.0 / GEN["slots"]
    r0, r1 = GEN["r_slot_bot"] + liner, GEN["r_slot_top"] - 0.5

    def half_free(r):
        return (2 * math.pi * r / GEN["slots"] - GEN["w_t"]) / 2 - liner - sep

    used = [37, 37, 31, 7, 0]
    cap = [37, 37, 31, 17, 3]          # positions per layer, as manufacturing.py
    out = []
    for j, n_use in enumerate(used):
        need = (j + 1) * pitch
        k = 0
        r = r1 - pitch / 2
        while r > r0 and half_free(r - pitch / 2) >= need and k < cap[j]:
            out.append((j, liner + (j + 0.5) * pitch, r, k < n_use))
            k += 1
            r -= pitch
    return out, half_free


@fig
def g06_winding():
    S = Svg(1200, 820, "G06 Wind a coil")
    S.header("G06  Wind one coil: 28 turns, 4 wires side by side (chuck NP1-T04)",
             "Every coil is wound the same way. Reversing happens later, when connecting (G09).")
    W, H, y = 380, 330, 80
    x = 20
    S.panel(x, y, W, H, 1, ["Clamp the segment on the chuck.", "4 spools, 25–30 N on each wire"])
    for i in range(4):
        S.circle(x + 50, y + 80 + i * 45, 18, fill=C["cu_l"])
        S.circle(x + 50, y + 80 + i * 45, 6, fill="white")
        S.line(x + 68, y + 80 + i * 45, x + 170, y + 170 + i * 4, C["cu"], 2)
    S.rect(x + 150, y + 150, 30, 50, fill=C["grey"], rx=4)
    S.text(x + 165, y + 218, "tension", 12)
    seg_side(S, x + 220, y + 120, 120, 80, caps=True, liner=True)
    S.circle(x + 280, y + 240, 12, fill=C["grey"])
    S.path(f"M{x + 255},{y + 255} a25,25 0 1 0 50,0", stroke=C["ink"], sw=2.5)
    S.arrow(x + 305, y + 255, x + 306, y + 248, C["ink"], 2, 9)
    x = 410
    S.panel(x, y, W, H, 2, ["Leave 150 mm start lead at the", "rear end. Put a red tag on it"])
    seg_side(S, x + 120, y + 110, 150, 90, caps=True, liner=True)
    S.path(f"M{x + 280},{y + 125} L{x + 345},{y + 125}", stroke=C["cu"], sw=5)
    S.rect(x + 330, y + 112, 22, 26, fill=C["bad"], rx=3)
    S.dim(x + 270, y + 165, x + 350, y + 165, "150", size=13)
    S.text(x + 195, y + 240, "rear end = connection side", 14, weight="bold")
    S.arrow(x + 195, y + 250, x + 300, y + 250, C["ink"], 2)
    x = 800
    S.panel(x, y, W, H, 3, ["Tie the coil ends with glass tape,", "fit the separator on each side"])
    seg_side(S, x + 120, y + 110, 150, 90, coil=True, caps=True, liner=True)
    S.rect(x + 150, y + 105, 14, 60, fill="white", sw=1.5)
    S.rect(x + 256, y + 105, 14, 60, fill="white", sw=1.5)
    S.text(x + 195, y + 240, "count = 28 on the winder", 14, weight="bold")
    S.tick(x + 340, y + 120)
    # layer plan, real positions
    y2 = 430
    S.rect(20, y2, 1160, 370, fill="white", stroke="#c9ced6", sw=2, rx=10)
    S.bubble(42, y2 + 22, 4)
    S.text(70, y2 + 30, "Layer plan: lay the wires in this order, one layer at a time, starting next to the tooth",
           17, "start", "bold")
    pos, half_free = layer_positions()
    s = 11.5
    r_top = GEN["r_slot_top"]
    ox, oy = 60, y2 + 130

    def P(u, r):  # slot drawn lying down: radial -> x (slot top on the right), u -> y
        return (ox + s * (r - GEN["r_slot_bot"] + 1), oy + s * u)

    # tooth (top band) and slot centreline (bottom boundary)
    S.poly([P(-6, GEN["r_slot_bot"] - 1), P(-6, GEN["r_s"]), P(0, GEN["r_s"]), P(0, GEN["r_slot_bot"] - 1)],
           fill=C["steel"])
    S.text(P(-3, 262)[0], P(-3, 262)[1] + 6, "TOOTH (seen end-on, cut through the coil side)", 15, weight="bold")
    S.poly([P(0, GEN["r_slot_bot"] - 1)] + [P(0.3, r) for r in (GEN["r_slot_bot"], r_top)] +
           [P(0, r_top)], fill=C["liner"], sw=1)
    rr = [GEN["r_slot_bot"] + i for i in range(0, 66)]
    S.poly([P(0, GEN["r_slot_bot"])] + [P(half_free(r) + 0.3, r) for r in rr] + [P(0, rr[-1])],
           fill="none", stroke=C["grey"], sw=1.5, dash="5,4")
    S.line(*P(half_free(r_top) + 0.55, GEN["r_slot_bot"]), *P(half_free(r_top) + 0.55, r_top), "white", 0)
    S.poly([P(0, GEN["r_slot_bot"] - 1), P(12, GEN["r_slot_bot"] - 1), P(12, GEN["r_slot_bot"]),
            P(0, GEN["r_slot_bot"])], fill=C["steel_d"], sw=1)
    cols = ["#d9822b", "#2b8a3e", "#1c7ed6", "#ae3ec9", "#adb5bd"]
    for j, u, r, used in pos:
        x_, y_ = P(u, r)
        S.circle(x_, y_, 0.83 * s, fill=cols[j] if used else "white", stroke=cols[j], sw=1)
    S.text(*P(9.5, GEN["r_slot_bot"] + 4), "slot bottom", 13, "start")
    S.text(P(11.5, r_top - 12)[0], P(11.5, r_top - 12)[1], "slot top (wider) →", 13, "start")
    S.text(P(13.5, 263)[0], P(13.5, 263)[1], "dashed line = half-slot edge (separator): wires must stay above it", 14, color=C["grey"])
    lx, ly = 860, y2 + 80
    rows = [("Layer 1", "37 wires", cols[0]), ("Layer 2", "37 wires", cols[1]), ("Layer 3", "31 wires", cols[2]),
            ("Layer 4", "7 wires", cols[3]), ("Layer 5", "spare room", cols[4])]
    for i, (a, b, c) in enumerate(rows):
        S.circle(lx, ly + i * 32, 9, fill=c if i < 4 else "white", stroke=c, sw=2)
        S.text(lx + 20, ly + i * 32 + 5, f"{a}: {b}", 16, "start", "bold" if i < 4 else "normal")
    S.lines(lx - 10, ly + 180, ["4 wires = 1 turn.", "28 turns × 4 = 112 wires.", "Max 60 rpm. Wires parallel,",
                                "never crossed inside the slot."], 15, "start")
    return S


# ============================================================ G07 coil tests
@fig
def g07_coiltests():
    S = Svg(1200, 390, "G07 Test every coil")
    S.header("G07  Test every coil before it goes into the stator (all 48)")
    W, H, y = 220, 270, 70
    items = [
        ("4 wires one by one", ["Each wire:", "same ±2 %"]),
        ("Resistance", ["14.5 mΩ ±3 %", "at 20 °C"]),
        ("Surge 3.5 kV", ["Same wave as", "the master coil"]),
        ("Hipot 1.8 kV", ["1 minute,", "coil to steel"]),
        ("Size gauge", ["Slides through", "the half-slot gauge"]),
    ]
    for i, (t, cap) in enumerate(items):
        x = 20 + i * 233
        S.panel(x, y, W, H, i + 1, cap)
        S.text(x + W / 2, y + 60, t, 16, weight="bold")
        cx, cy = x + W / 2, y + 130
        if i == 0:
            for k in range(4):
                S.line(cx - 60, cy - 30 + k * 18, cx + 60, cy - 30 + k * 18, C["cu"], 5)
            S.gauge(cx + 75, cy + 45, 16)
        elif i == 1:
            S.rect(cx - 50, cy - 30, 100, 60, fill="#fff", rx=6)
            S.text(cx, cy + 8, "14.5 mΩ", 20, weight="bold")
        elif i == 2:
            S.rect(cx - 70, cy - 40, 140, 80, fill="#e9f5ff", rx=6)
            S.path(f"M{cx - 60},{cy} " + " ".join(
                f"L{cx - 60 + k * 4},{cy - 30 * math.exp(-k / 9) * math.cos(k / 2.2)}" for k in range(31)),
                stroke=C["mag_s"], sw=2.5)
        elif i == 3:
            S.path(f"M{cx - 10},{cy - 40} L{cx - 25},{cy + 5} L{cx},{cy + 5} L{cx - 12},{cy + 40} L{cx + 25},{cy - 10} "
                   f"L{cx + 2},{cy - 10} L{cx + 15},{cy - 40} Z", fill=C["warn"], sw=2)
        else:
            S.rect(cx - 70, cy - 35, 140, 70, fill="#dde1e6", rx=4)
            S.poly([(cx - 40, cy - 35), (cx + 40, cy - 35), (cx + 20, cy + 35), (cx - 20, cy + 35)], fill="white")
        S.tick(x + W - 26, y + 26, 12)
    S.cross(40, 368, 10)
    S.text(58, 373, "Fail: unwind, new liner, wind again on the same segment.", 14, "start", "bold", C["bad"])
    return S


# ============================================================ G08 assemble
@fig
def g08_assemble():
    S = Svg(1200, 820, "G08 Put the segments on the carrier")
    S.header("G08  Put the 45 wound segments onto the carrier (stand NP1-T05)")
    W, H, y = 380, 330, 80
    x = 20
    S.panel(x, y, W, H, 1, ["Carrier on the turntable,", "FRONT side up, stop at the bottom"])
    S.rect(x + 70, y + 170, 240, 60, fill="#6f7b8a")
    S.rect(x + 70, y + 150, 240, 20, fill="#8a95a5")
    for i in range(9):
        S.rect(x + 80 + i * 26, y + 150, 10, 12, fill="white", sw=1)
    S.rect(x + 40, y + 230, 300, 22, fill=C["grey"], rx=4)
    S.text(x + 190, y + 130, "45 dovetail grooves", 15, weight="bold")
    S.arrow(x + 190, y + 100, x + 190, y + 70, C["ok"], 3)
    S.text(x + 220, y + 80, "front", 14, "start", "bold", C["ok"])
    x = 410
    S.panel(x, y, W, H, 2, ["Tape the 6 PT100 sensors to the", "coil sides: slot TOP, mid-length"])
    seg_side(S, x + 110, y + 120, 160, 90, coil=True, caps=True, liner=True)
    S.rect(x + 175, y + 118, 30, 10, fill="white", sw=1.5)
    S.line(x + 205, y + 123, x + 330, y + 90, C["ink"], 1.5)
    S.text(x + 300, y + 82, "PT100", 14, weight="bold")
    S.text(x + 190, y + 250, "teeth 2, 17, 32 (A) and the same for B, C", 13)
    x = 800
    S.panel(x, y, W, H, 3, ["Slide each segment down its groove", "until it sits on the rear stop"])
    S.rect(x + 60, y + 230, 260, 20, fill="#6f7b8a")
    for i in range(3):
        S.rect(x + 70 + i * 82, y + 130, 70, 100, fill=C["steel"])
        S.rect(x + 66 + i * 82, y + 140, 78, 60, fill=C["cu"], rx=6)
    S.rect(x + 234, y + 40, 70, 80, fill=C["steel"], dash="6,4")
    S.arrow(x + 270, y + 60, x + 270, y + 140, C["ink"], 4)
    S.text(x + 130, y + 75, "push the yoke only,", 13)
    S.text(x + 130, y + 93, "with a plastic drift", 13)
    # 4 measure ring
    y2 = 430
    x = 20
    S.panel(x, y2, 580, 370, 4, ["Measure every tooth tip, front and rear:", "all within 0.05 mm. Bad tooth? Swap the segment."])
    cx, cy, rs = x + 230, y2 + 165, 0.42
    for k in range(GEN["slots"]):
        S.poly(to_screen(segment_world(4), cx, cy, rs, 0, rot=-k * 8.0), fill=C["steel"], sw=0.8)
    S.circle(cx, cy, 299 * rs + 8, stroke=C["grey"], sw=1.5, dash="4,4")
    S.rect(cx + 299 * rs + 12, cy - 8, 70, 16, fill=C["grey"], rx=3)
    S.circle(cx + 299 * rs + 10, cy, 5, fill=C["bad"])
    S.text(cx + 299 * rs + 47, cy - 16, "probe", 13)
    S.path(f"M{cx - 60},{cy - 145} A150,150 0 0 1 {cx + 60},{cy - 145}", stroke=C["ok"], sw=3)
    S.arrow(cx + 58, cy - 146, cx + 66, cy - 142, C["ok"], 3, 10)
    S.text(cx, cy + 5, "turn slowly", 14, weight="bold")
    S.gauge(x + 500, y2 + 140, 30, "≤ 0.05")
    x = 610
    S.panel(x, y2, 570, 370, 5, ["Slide a wedge into every slot from the front,", "then bolt the clamp ring (yokes only)"])
    cxs, cys, ss = x + 200, y2 + 80 + 2.6 * 299 + 10, 2.6
    for k in (0, 1):
        S.poly(to_screen(segment_world(), cxs, cys, ss, 0, rot=4.0 - k * 8.0), fill=C["steel"])
    wx, wy = cxs, cys - ss * 296
    S.rect(wx - 12, wy - 3, 24, 7, fill=C["g10"], sw=1.5)
    S.leader(wx + 12, wy + 2, x + 400, y2 + 90, ["glass-epoxy wedge", "(2 mm)"])
    S.rect(x + 380, y2 + 200, 160, 30, fill="#d5d9de")
    S.text(x + 460, y2 + 221, "clamp ring", 14, weight="bold")
    S.text(x + 460, y2 + 255, "A4-80 screws", 13)
    return S


# ============================================================ G09 connection
@fig
def g09_connection():
    S = Svg(1200, 760, "G09 Connect the coils")
    S.header("G09  Connect the coils: each phase = 15 coils in a row",
             "Look at the stator from the REAR (connection side). Tooth 1 is at 12 o'clock at the carrier mark.")
    plan = []
    import csv
    p = HERE.parent.parent / "analysis" / "generator" / "results" / "coil_connection.csv"
    with open(p) as f:
        plan = list(csv.DictReader(f))
    col = {"A": C["ph_a"], "B": C["ph_b"], "C": C["ph_c"]}
    cx, cy, R = 320, 420, 250
    for r in plan:
        k = int(r["tooth"]) - 1
        a = math.radians(k * 8.0)
        x, y = cx + R * math.sin(a), cy - R * math.cos(a)
        S.circle(x, y, 17, fill=col[r["phase"]], stroke="white", sw=2)
        S.text(x, y + 5, r["sense"] + r["phase"], 12, weight="bold", color="white")
        xo, yo = cx + (R + 34) * math.sin(a), cy - (R + 34) * math.cos(a)
        S.text(xo, yo + 5, r["tooth"], 12, color=C["grey"])
    # phase A path
    a_teeth = [int(r["tooth"]) for r in plan if r["phase"] == "A"]
    pts = [(cx + (R - 32) * math.sin(math.radians((t - 1) * 8)), cy - (R - 32) * math.cos(math.radians((t - 1) * 8)))
           for t in a_teeth]
    S.poly(pts, stroke=C["ph_a"], sw=3, closed=False)
    S.arrow(pts[-2][0], pts[-2][1], pts[-1][0], pts[-1][1], C["ph_a"], 3)
    S.text(cx, cy - 10, "phase A path", 16, weight="bold", color=C["ph_a"])
    S.text(cx, cy + 14, "1→2→3→10→11→12→19…→39", 14, color=C["ph_a"])
    S.text(cx, cy + 36, "→ star point", 14, color=C["ph_a"])
    # strip of first 9 teeth
    x0, y0 = 650, 190
    S.text(x0, y0 - 70, "How to join one group (teeth 1, 2, 3):", 17, "start", "bold")
    for i in range(3):
        x = x0 + 30 + i * 160
        S.rect(x, y0 + 40, 60, 90, fill=C["steel"])
        S.rect(x - 15, y0 + 55, 90, 60, fill=C["cu"], rx=8)
        sign = ["+", "−", "+"][i]
        S.text(x + 30, y0 + 92, sign + "A", 20, weight="bold", color="white")
        S.text(x + 5, y0 + 30, "S", 15, weight="bold", color=C["bad"])
        S.text(x + 55, y0 + 30, "F", 15, weight="bold")
    # jumpers: S1 from lead; F1->F2 ; S2->S3 ; F3 -> next group
    def J(xa, xb, yy, c=C["ph_a"]):
        S.path(f"M{xa},{y0 + 36} C{xa},{yy} {xb},{yy} {xb},{y0 + 36}", stroke=c, sw=3)
    J(x0 + 85, x0 + 245, y0 - 25)        # F1 -> F2
    J(x0 + 195, x0 + 355, y0 + 5)        # S2 -> S3
    S.arrow(x0 + 35, y0 - 15, x0 + 35, y0 + 18, C["ph_a"], 3)
    S.text(x0 + 35, y0 - 22, "U lead in", 13, weight="bold", color=C["ph_a"])
    S.arrow(x0 + 385, y0 + 36, x0 + 440, y0 - 12, C["ph_a"], 3)
    S.text(x0 + 540, y0 - 22, "F3 to tooth 10", 13, "end", "bold", C["ph_a"])
    S.lines(x0, y0 + 175, ["S = start (red tag), F = finish.",
                           "+ coil: current goes in at S.  − coil: in at F.",
                           "So: F1 joins F2, S2 joins S3, F3 goes on to tooth 10."], 15, "start")
    S.legend(x0, y0 + 270, [(C["ph_a"], "Phase A = U (brown), starts at tooth 1"),
                            (C["ph_b"], "Phase B = V (black), starts at tooth 7"),
                            (C["ph_c"], "Phase C = W (grey), starts at tooth 4")], 15, 18)
    S.rect(x0, y0 + 370, 520, 150, fill=C["light"], stroke="#c9ced6", rx=8)
    S.lines(x0 + 15, y0 + 400, ["Long jumpers between groups run on the", "glass-epoxy connection ring, one track per phase.",
                                "The 3 phase ends meet in the star point.", "Then check polarity with a compass (5.10)."], 15, "start")
    return S


# ============================================================ G10 joint
@fig
def g10_joint():
    S = Svg(1200, 430, "G10 Make a joint")
    S.header("G10  Make one brazed joint (same for every joint)")
    W, H, y = 220, 330, 80
    caps = [["Strip 15 mm of enamel", "with the rotary stripper"], ["Twist the wires into", "a copper ferrule"],
            ["Crimp the ferrule", "firmly"], ["Braze with CuP rod", "(induction, no flux)"],
            ["Glass sleeve over it,", "lace it to the ring"]]
    for i, cap in enumerate(caps):
        x = 20 + i * 233
        S.panel(x, y, W, H, i + 1, cap)
        cx, cy = x + W / 2, y + 150
        for k in range(4):
            S.line(cx - 90, cy - 12 + k * 8, cx - 15 if i == 0 else cx - 20, cy - 12 + k * 8, C["cu"], 5)
        if i == 0:
            for k in range(4):
                S.line(cx - 15, cy - 12 + k * 8, cx + 20, cy - 12 + k * 8, "#e8a15a", 5)
            S.dim(cx - 15, cy + 35, cx + 20, cy + 35, "15", size=13)
            S.text(cx, cy - 40, "no chemicals!", 14, weight="bold", color=C["bad"])
        if i >= 1:
            S.rect(cx - 25, cy - 18 if i > 1 else cy - 22, 60, 36 if i > 1 else 44,
                   fill="#c87533" if i < 4 else C["ptfe"], rx=6 if i < 4 else 12)
            for k in range(4):
                S.line(cx + 35, cy - 12 + k * 8, cx + 90, cy - 12 + k * 8, C["cu"], 5)
        if i == 2:
            S.arrow(cx + 5, cy - 70, cx + 5, cy - 24, C["ink"], 4)
            S.arrow(cx + 5, cy + 70, cx + 5, cy + 24, C["ink"], 4)
        if i == 3:
            for k in range(3):
                S.circle(cx + 5, cy, 40 + k * 8, stroke=C["hot"], sw=3)
            S.text(cx, cy - 75, "≈ 750 °C", 14, weight="bold", color=C["hot"])
        if i == 4:
            for k in range(5):
                S.line(cx - 20 + k * 12, cy - 22, cx - 14 + k * 12, cy + 22, C["grey"], 2)
    return S


# ============================================================ G11 VPI
@fig
def g11_vpi():
    S = Svg(1200, 860, "G11 Soak the stator in resin (VPI)")
    S.header("G11  Soak the stator in resin under vacuum and pressure (VPI)",
             "The resin glues every wire, fills every gap and keeps water out for 20 years.")
    W, H, y = 280, 300, 80
    xs = [20, 315, 610, 905]

    def stator_icon(x, y, w=120):
        S.rect(x, y, w, 50, fill="#5f6b7a", rx=4)
        S.rect(x - 8, y + 6, 8, 38, fill=C["cu"])
        S.rect(x + w, y + 6, 8, 38, fill=C["cu"])

    def tank(x, y, fill_to=None, col=C["resin"]):
        S.rect(x, y, 180, 160, fill="#eef2f6", sw=3, rx=8)
        if fill_to:
            S.rect(x + 3, y + 160 - fill_to, 174, fill_to - 3, fill=col, stroke="none", rx=6, op=0.75)
        S.rect(x - 6, y - 14, 192, 16, fill=C["grey"], rx=4)

    x = xs[0]
    S.panel(x, y, W, H, 1, ["Mask the tooth tips and holes,", "weigh it, measure capacitance"])
    stator_icon(x + 80, y + 140)
    S.rect(x + 78, y + 132, 124, 8, fill=C["bad"], stroke="none")
    S.text(x + 140, y + 120, "silicone tape", 13, weight="bold", color=C["bad"])
    S.text(x + 140, y + 230, "m₀ = ____ kg", 15, weight="bold")
    x = xs[1]
    S.panel(x, y, W, H, 2, ["Dry in the oven:", "130 °C for 4 hours"])
    S.rect(x + 50, y + 70, 180, 150, fill="#ffe3d3", sw=3, rx=8)
    stator_icon(x + 80, y + 130)
    S.thermo(x + 220, y + 120)
    S.clock(x + 85, y + 98, 14)
    S.text(x + 105, y + 103, "4 h", 15, "start", "bold")
    x = xs[2]
    S.panel(x, y, W, H, 3, ["Into the tank, pump air out:", "≤ 1 mbar, hold 2 hours"])
    tank(x + 50, y + 80)
    stator_icon(x + 80, y + 150)
    S.arrow(x + 140, y + 66, x + 140, y + 36, C["mag_s"], 4)
    S.text(x + 175, y + 50, "vacuum", 14, "start", "bold", C["mag_s"])
    x = xs[3]
    S.panel(x, y, W, H, 4, ["Let resin in (still vacuum) until", "it is 50 mm above the stator"])
    tank(x + 50, y + 80, 125)
    stator_icon(x + 80, y + 150)
    S.dim(x + 245, y + 115, x + 245, y + 150, "50", size=13)
    y = 400
    x = xs[0]
    S.panel(x, y, W, H, 5, ["Push with dry nitrogen:", "5 bar for 2 hours"])
    tank(x + 50, y + 80, 125)
    stator_icon(x + 80, y + 150)
    for k in range(3):
        S.arrow(x + 90 + k * 50, y + 30, x + 90 + k * 50, y + 74, C["ok"], 3)
    x = xs[1]
    S.panel(x, y, W, H, 6, ["Lift out, let it drip 30 min", "while turning slowly"])
    stator_icon(x + 80, y + 110)
    for k in range(4):
        S.path(f"M{x + 95 + k * 30},{y + 168} q-4,10 0,14 q4,-4 0,-14", fill=C["resin"], stroke=C["resin"], sw=1)
    S.path(f"M{x + 110},{y + 95} A40,40 0 0 1 {x + 170},{y + 95}", stroke=C["ink"], sw=2.5)
    S.arrow(x + 168, y + 94, x + 174, y + 100, C["ink"], 2, 9)
    x = xs[2]
    S.panel(x, y, W, H, 7, ["Bake while TURNING (2–5 rpm)", "as the resin datasheet says"])
    S.rect(x + 50, y + 70, 180, 150, fill="#ffe3d3", sw=3, rx=8)
    stator_icon(x + 80, y + 120)
    S.path(f"M{x + 100},{y + 205} A40,20 0 0 0 {x + 180},{y + 205}", stroke=C["ink"], sw=2.5)
    S.arrow(x + 178, y + 206, x + 184, y + 200, C["ink"], 2, 9)
    S.text(x + 140, y + 105, "≈ 150–160 °C", 14, weight="bold", color=C["hot"])
    x = xs[3]
    S.panel(x, y, W, H, 8, ["Unmask, clean tips (plastic only),", "weigh again: + 3 to 5 kg"])
    stator_icon(x + 80, y + 130)
    S.text(x + 140, y + 230, "m₁ − m₀ = ____ kg", 15, weight="bold")
    S.tick(x + 240, y + 100)
    # timeline chart
    y3 = 720
    S.rect(20, y3 - 10, 1160, 140, fill="white", stroke="#c9ced6", sw=2, rx=10)
    S.text(40, y3 + 15, "One VPI run at a glance", 16, "start", "bold")
    t = [("dry 130 °C", 4, C["hot"]), ("cool", 1.5, "#ffc9a8"), ("vacuum", 2, C["vac"]), ("fill", 0.5, C["resin"]),
         ("5 bar", 2, C["ok"]), ("drip", 0.5, "#cfe9cf"), ("bake turning", 8, C["hot"])]
    tot = sum(d for _, d, _ in t)
    x = 40
    for name, d, c in t:
        w = 1120 * d / tot
        S.rect(x, y3 + 30, w, 50, fill=c, sw=1.5)
        S.text(x + w / 2, y3 + 60, name, 13, weight="bold")
        S.text(x + w / 2, y3 + 100, f"{d:g} h", 13)
        x += w
    return S


# ============================================================ G12 potting
@fig
def g12_potting():
    S = Svg(1200, 600, "G12 Pot the coil ends")
    S.header("G12  Pour potting around the coil ends (moulds NP1-T08)",
             "Section through the stator, real size scale. Green = where the potting goes. It must stay inside the dashed lines.")
    s, ox, oy = 2.6, 60, 560

    def P(pts):
        return [(ox + s * (x - 300), oy - s * (r - 150)) for x, r in pts]

    S.poly(P(G.CARRIER), fill="#6f7b8a")
    S.poly(P(G.STATOR_RING), fill="#d5d9de")
    S.poly(P(G.STACK_POLY), fill="#5f6b7a")
    for x0, x1 in ((321, 343), (417, 439)):
        S.poly(P([(x0 - 12, 226), (x1 + 12, 226), (x1 + 12, 304), (x0 - 12, 304)]), fill="#f3d9fa", stroke="#da77f2", sw=3)
        S.poly(P([(x0 - 4, 230), (x1 + 4, 230), (x1 + 4, 298), (x0 - 4, 298)]), fill=C["resin"], sw=1.5)
        S.poly(P([(x0, 234), (x1, 234), (x1, 292), (x0, 292)]), fill=C["cu"], sw=1.5)
        S.poly(P([(x0 - 4, 230), (x1 + 4, 230), (x1 + 4, 298), (x0 - 4, 298)]), stroke=C["bad"], sw=2, dash="8,5")
    S.poly(P(G.STACK_POLY), fill="#5f6b7a")
    S.line(*P([(300, 299)])[0], *P([(470, 299)])[0], C["grey"], 1.5, "4,4")
    S.text(P([(472, 299)])[0][0], P([(472, 299)])[0][1] + 5, "Ø598 limit", 14, "start", "bold")
    S.leader(*P([(326, 262)])[0], 70, 140, ["front coil ends (x 321–343)"], anchor="start")
    S.leader(*P([(428, 262)])[0], 640, 185, ["rear coil ends + joints (x 417–439)"])
    S.leader(*P([(436, 296)])[0], 640, 240, ["potting (green), 4 mm all round"])
    S.leader(*P([(450, 270)])[0], 640, 295, ["silicone mould (pink)"])
    S.leader(*P([(380, 260)])[0], 640, 350, ["stack: no potting on the tooth tips"])
    S.leader(*P([(430, 160)])[0], 640, 460, ["carrier: keep clean"])
    rows = ["1  Warm the stator to 60 °C.", "2  Fit both moulds.", "3  Mix, then degas under vacuum.",
            "4  Pour slowly from ONE point.", "5  Cure with slow heating (≤ 1 K/min).",
            "6  Demould. Look for holes and cracks."]
    S.rect(870, 380, 315, 200, fill=C["light"], stroke="#c9ced6", rx=8)
    S.lines(885, 410, rows, 14, "start")
    return S


# ============================================================ G13 drum
@fig
def g13_drum():
    S = Svg(1200, 640, "G13 Machine the drum")
    S.header("G13  Machine the drum in ONE clamping, then measure before unclamping",
             "Section of the welded drum (real shape). Blue = surfaces that must line up within 0.02 mm.")
    s, ox, oy = 1.35, 60, 610

    def P(pts):
        return [(ox + s * (x - 80), oy - s * r) for x, r in pts]

    for pts in G.DRUM_PARTS.values():
        S.poly(P(pts), fill=C["steel"])
    S.line(ox, oy, ox + s * 420, oy, C["grey"], 1.5, "18,6,4,6")
    hi = dict(stroke=C["mag_s"], sw=6)
    S.line(*P([(142.5, 98)])[0], *P([(92, 98)])[0], **hi)
    S.line(*P([(385, 98)])[0], *P([(337.5, 98)])[0], **hi)
    S.line(*P([(335, GEN["r_m2"])])[0], *P([(425, GEN["r_m2"])])[0], **hi)
    S.line(*P([(200, 232)])[0], *P([(200, 180)])[0], **hi)
    S.leader(*P([(117, 98)])[0], 200, 570, ["front cup seat Ø210 P7"])
    S.leader(*P([(360, 98)])[0], 560, 570, ["rear cup seat Ø210 P7"])
    S.leader(*P([(380, GEN["r_m2"])])[0], 700, 130, ["MAGNET SEAT Ø618.4 (+0.05/0)", "run-out ≤ 0.02 to the cup seats"])
    S.leader(*P([(200, 210)])[0], 420, 400, ["hub face + Ø360 spigot", "12 × M16 on PCD 400"])
    S.leader(*P([(458, 340)])[0], 700, 220, ["rear flange ring Ø710:", "disc + rear cover bolts"])
    S.rect(820, 300, 360, 150, fill=C["light"], stroke="#c9ced6", rx=8)
    S.lines(835, 330, ["Before machining: weld, check (MT/UT),", "stress relieve 580–620 °C.",
                       "Rough, rest 24 h, then finish.", "Measure the magnet seat at",
                       "3 depths × 8 angles. Write it down."], 15, "start")
    return S


# ============================================================ G14 comb + magnet variants
@fig
def g14_magnets():
    S = Svg(1200, 700, "G14 Magnets and their places")
    S.header("G14  The magnets: two kinds, and where each one goes",
             "The drum seat is shown unrolled flat, looking from the stator side (as the stator sees it).")
    # variants
    y = 90
    for i, (n, txt) in enumerate([(True, ["NP1-220-N", "north on the inside", "RED dot"]),
                                  (False, ["NP1-220-S", "south on the inside", "BLUE dot"])]):
        x = 40 + i * 300
        S.path(f"M{x},{y + 110} Q{x + 100},{y + 70} {x + 200},{y + 110} L{x + 200},{y + 140} "
               f"Q{x + 100},{y + 100} {x},{y + 140} Z", fill=C["mag_n"] if n else C["mag_s"], sw=2.5)
        S.circle(x + 100, y + 95, 7, fill=C["mag_n"] if n else C["mag_s"], stroke="white", sw=3)
        S.lines(x + 100, y + 170, txt, 15, weight="bold")
        S.text(x + 100, y + 60, "convex side (to drum) ↑", 13, color=C["grey"])
    S.rect(640, y + 20, 520, 160, fill="#fff3bf", stroke=C["warn"], sw=2, rx=8)
    S.warn(670, y + 60, 34)
    S.lines(700, y + 55, ["A curved magnet cannot be turned over:", "it only fits one way round.",
                          "So we order two kinds: 84 N + 84 S.", "Check the dot colour before every piece."], 15, "start")
    # developed view
    y2 = 330
    S.text(40, y2, "Unrolled seat (part of it: 6 of the 40 poles)", 16, "start", "bold")
    px, pw, ph = 60, 170, 260
    x = px
    for p in range(6):
        n = p % 2 == 0
        S.rect(x, y2 + 20, 26, ph, fill=C["grp"])
        xm = x + 30
        for k in range(4):
            ym = y2 + 30 + k * 60
            S.rect(xm, ym, 136, 54, fill=C["mag_n"] if n else C["mag_s"], rx=3)
            S.text(xm + 68, ym + 34, "N" if n else "S", 20, weight="bold", color="white")
            if k < 3:
                S.rect(xm + 10, ym + 54, 116, 5, fill=C["ptfe"], sw=1)
        x += pw
    S.rect(x, y2 + 20, 26, ph, fill=C["grp"])
    S.rect(px, y2 + 20 + ph, x - px + 26, 18, fill=C["grp"])
    S.rect(px, y2 + 2, x - px + 26, 18, fill=C["grp"])
    S.text(px + 520, y2 + 16, "rear end ring (glass-epoxy)  ← open end of the drum, magnets go in here", 13, color=C["ink"])
    S.text(px + 520, y2 + 293, "front end ring (glass-epoxy)", 13)
    S.dim(1090, y2 + 30, 1090, y2 + 270, "74 mm = 4 pieces", size=13, color=C["ink"])
    S.legend(60, y2 + 320, [(C["grp"], "tan = glass-epoxy comb bars (9.6 mm) and end rings"),
                            (C["ptfe"], "white = 0.2 mm PTFE shim between pieces")], 14)
    S.lines(760, y2 + 334, ["Pole pitch 9.000°. N and S always alternate."], 14, "start")
    return S


# ============================================================ G15 magnet insertion
@fig
def g15_insert():
    S = Svg(1200, 900, "G15 Put a magnet in")
    S.header("G15  Put the magnets in with the jig (NP1-T02). Two people. Never by hand.",
             "The drum stands upright, open (rear) end up, on the non-magnetic turntable.")
    W, H, y = 380, 340, 80

    def drum_cut(x, y, h=220):
        S.rect(x, y, 30, h, fill=C["steel"])                      # shell wall cut
        S.rect(x + 30, y + h - 150, 6, 150, fill=C["grp"], sw=1)    # comb/end
        S.rect(x - 10, y + h, 120, 14, fill=C["grey"], rx=3)

    x = 20
    S.panel(x, y, W, H, 1, ["Thin glue on the seat AND on the", "magnet's curved face (with beads)"])
    drum_cut(x + 70, y + 60)
    S.rect(x + 100, y + 130, 5, 150, fill=C["resin"], stroke="none")
    S.rect(x + 210, y + 150, 30, 80, fill=C["mag_n"], rx=3)
    S.rect(x + 206, y + 150, 5, 80, fill=C["resin"], stroke="none")
    S.text(x + 290, y + 150, "0.15 mm", 14, weight="bold")
    S.text(x + 290, y + 170, "glass beads", 14)
    S.text(x + 290, y + 190, "in the glue", 14)
    x = 410
    S.panel(x, y, W, H, 2, ["The jig holds the magnet 5 mm away", "and slides it DOWN the channel"])
    drum_cut(x + 70, y + 60)
    S.rect(x + 150, y + 40, 90, 230, fill=C["al"])
    S.rect(x + 108, y + 110, 42, 70, fill="#e9ecef", sw=1.5)
    S.rect(x + 112, y + 115, 24, 60, fill=C["mag_n"], rx=3)
    S.dim(x + 100, y + 95, x + 112, y + 95, "5", size=12)
    S.arrow(x + 270, y + 90, x + 270, y + 200, C["ink"], 4)
    S.text(x + 195, y + 35, "aluminium jig", 13, weight="bold")
    x = 800
    S.panel(x, y, W, H, 3, ["Turn the brass screw to move it", "onto the seat. SLOWLY."])
    drum_cut(x + 70, y + 60)
    S.rect(x + 150, y + 40, 90, 230, fill=C["al"])
    S.rect(x + 102, y + 200, 24, 60, fill=C["mag_n"], rx=3)
    S.rect(x + 126, y + 222, 40, 14, fill=C["brass"], sw=1.5)
    S.arrow(x + 200, y + 229, x + 130, y + 229, C["ink"], 3)
    S.warn(x + 300, y + 100, 36)
    S.lines(x + 300, y + 150, ["last 2 mm:", "it pulls hard!"], 14, weight="bold", color=C["bad"])
    y = 440
    x = 20
    S.panel(x, y, W, H, 4, ["Next piece on top, white PTFE shim", "between. Clamp bar holds all 4"])
    drum_cut(x + 70, y + 60)
    for k in range(4):
        S.rect(x + 102, y + 205 - k * 46, 24, 42, fill=C["mag_n"], rx=3)
        if k:
            S.rect(x + 100, y + 248 - k * 46, 28, 4, fill=C["ptfe"], sw=1)
    S.rect(x + 128, y + 70, 16, 180, fill=C["al"])
    S.text(x + 250, y + 120, "same poles PUSH", 14, weight="bold", color=C["bad"])
    S.text(x + 250, y + 140, "each other apart:", 14, weight="bold", color=C["bad"])
    S.text(x + 250, y + 160, "keep the clamp", 14)
    S.text(x + 250, y + 180, "on until cured", 14)
    # order
    x = 410
    S.panel(x, y, W, H, 5, ["First ALL 20 north poles, cure 24 h.", "Then all 20 south poles."])
    cx, cy = x + 190, y + 150
    for p in range(40):
        a = math.radians(p * 9)
        n = p % 2 == 0
        xx, yy = cx + 110 * math.sin(a), cy - 110 * math.cos(a)
        S.circle(xx, yy, 8.5, fill=C["mag_n"] if n else "white", stroke=C["mag_n"] if n else C["mag_s"], sw=2)
    S.text(cx, cy - 8, "day 1: red", 15, weight="bold", color=C["mag_n"])
    S.text(cx, cy + 16, "day 2: blue", 15, weight="bold", color=C["mag_s"])
    x = 800
    S.panel(x, y, W, H, 6, ["Check each pole with the gaussmeter", "before the glue gets hard"])
    drum_cut(x + 70, y + 60)
    for k in range(4):
        S.rect(x + 102, y + 205 - k * 46, 24, 42, fill=C["mag_n"], rx=3)
    S.rect(x + 170, y + 120, 70, 100, fill="#ffe066", rx=8)
    S.text(x + 205, y + 165, "N", 22, weight="bold")
    S.line(x + 170, y + 170, x + 132, y + 170, C["ink"], 3)
    S.tick(x + 300, y + 170)
    S.rect(20, 800, 1160, 80, fill="#fff3bf", stroke=C["warn"], sw=2, rx=8)
    S.lines(40, 830, ["After all 40 poles: rear end ring, then warm the whole drum to 80 °C for 4 hours (slow heating).",
                      "Then scan every pole (section 6.6). Chipped magnet = scrap it in the oil tin, never glue chips."], 15, "start")
    return S


# ============================================================ G16 sleeve
@fig
def g16_sleeve():
    S = Svg(1200, 680, "G16 Mould the sleeve")
    S.header("G16  Mould the glass sleeve over the magnets (mandrel NP1-T06)",
             "The aluminium mandrel sits in both bearing seats, so the sleeve comes out perfectly round and centred.")
    s, ox, oy = 1.5, 80, 590

    def P(pts):
        return [(ox + s * (x - 60), oy - s * r) for x, r in pts]

    for pts in G.DRUM_PARTS.values():
        S.poly(P(pts), fill=C["steel"])
    m = G.MAGNET
    S.poly(P([(343, m["r_in"]), (417, m["r_in"]), (417, m["r_out"]), (343, m["r_out"])]), fill=C["mag_n"])
    S.poly(P([(335, m["r_in"]), (343, m["r_in"]), (343, m["r_out"]), (335, m["r_out"])]), fill=C["grp"])
    S.poly(P([(417, m["r_in"]), (425, m["r_in"]), (425, m["r_out"]), (417, m["r_out"])]), fill=C["grp"])
    body = [(330, 265), (432, 265), (432, 301.0), (330, 301.0)]          # sleeve-forming ring
    web = [(422, 110), (432, 110), (432, 265), (422, 265)]
    hub = [(340, 60), (432, 60), (432, 110), (385, 110), (385, 104.9), (340, 104.9)]  # rear spigot
    plug = [(92, 20), (142, 20), (142, 104.9), (92, 104.9)]               # front plug
    rod = [(85, 0), (440, 0), (440, 20), (85, 20)]
    for part in (body, web, hub, plug):
        S.poly(P(part), fill=C["al"])
    S.poly(P(rod), fill=C["steel_d"])
    S.poly(P([(335, 301.0), (425, 301.0), (425, 301.5), (335, 301.5)]), fill=C["resin"], sw=3, stroke=C["resin"])
    S.line(ox, oy, ox + s * 420, oy, C["grey"], 1.5, "18,6,4,6")
    S.leader(*P([(380, 301.2)])[0], 820, 165, ["glass sleeve 0.4–0.6 mm", "inner Ø602.0"])
    S.leader(*P([(380, 305)])[0], 820, 120, ["magnets"])
    S.leader(*P([(427, 200)])[0], 820, 220, ["aluminium mandrel", "(not magnetic: no pull)"])
    S.leader(*P([(117, 80)])[0], 820, 370, ["front plug in the FRONT cup seat", "(fitted from the front)"])
    S.leader(*P([(362, 90)])[0], 820, 425, ["spigot in the REAR cup seat"])
    S.leader(*P([(300, 10)])[0], 820, 300, ["tie rod joins plug and mandrel"])
    rows = ["1  Wrap dry glass cloth on the mandrel.", "2  Lower it in from the rear; fit the front", "    plug from the front, tighten the tie rod.",
            "3  Seal the ends, suck the resin in from", "    the bottom until it comes out clear.",
            "4  24 h room temp, then 80 °C for 4 h.", "5  Cool: aluminium shrinks more, the", "    mandrel comes out by itself.",
            "6  Trim. NEVER grind the rotor."]
    S.rect(820, 470, 360, 160, fill=C["light"], stroke="#c9ced6", rx=8)
    S.lines(832, 492, rows, 13.5, "start", gap=1.28)
    return S


# ============================================================ G17 joining
@fig
def g17_join():
    S = Svg(1200, 900, "G17 Put the rotor over the stator")
    S.header("G17  Put the rotor over the stator: the most dangerous step",
             "≈ 27 kN of magnet pull. If the rotor goes 1 mm off centre, it pulls 1.9 kN more to that side.")
    W, H, y = 380, 380, 80

    def stand(x, y):
        S.rect(x + 60, y + 330, 260, 20, fill=C["grey"])                 # floor stand
        S.rect(x + 175, y + 110, 30, 220, fill="#8a95a5")               # spindle
        S.rect(x + 110, y + 260, 160, 70, fill="#5f6b7a")               # stator
        S.rect(x + 105, y + 270, 5, 50, fill=C["cu"], stroke="none")
        S.rect(x + 270, y + 270, 5, 50, fill=C["cu"], stroke="none")

    def rotor(x, y, dy):
        S.path(f"M{x + 95},{y + 330 - 120 + dy} L{x + 95},{y + 150 + dy} L{x + 285},{y + 150 + dy} "
               f"L{x + 285},{y + 330 - 120 + dy}", stroke=C["ink"], sw=10)
        S.path(f"M{x + 95},{y + 330 - 120 + dy} L{x + 95},{y + 150 + dy} L{x + 285},{y + 150 + dy} "
               f"L{x + 285},{y + 330 - 120 + dy}", stroke=C["steel"], sw=7)
        S.rect(x + 100, y + 220 + dy, 6, 60, fill=C["mag_n"], stroke="none")
        S.rect(x + 274, y + 220 + dy, 6, 60, fill=C["mag_n"], stroke="none")

    x = 20
    S.panel(x, y, W, H, 1, ["Clear the area: no steel, no phones,", "nobody with a pacemaker"])
    stand(x, y - 40)
    S.cross(x + 70, y + 90, 20)
    S.text(x + 70, y + 130, "steel", 13, weight="bold")
    S.cross(x + 310, y + 90, 20)
    S.text(x + 310, y + 130, "pacemaker", 13, weight="bold")
    x = 410
    S.panel(x, y, W, H, 2, ["Guide tool on the spindle nose,", "4 green G10 strips in the gap"])
    stand(x, y - 40)
    S.rect(x + 165, y + 50, 50, 50, fill=C["al"])
    S.rect(x + 185, y + 25, 10, 40, fill=C["brass"])
    S.text(x + 245, y + 80, "NP1-T01", 13, "start", "bold")
    for xx in (x + 104, x + 270):
        S.rect(xx, y + 185, 6, 60, fill=C["g10"], sw=1.5)
    S.text(x + 300, y + 170, "1.5 mm strips", 13, weight="bold", color="#2b8a3e")
    x = 800
    S.panel(x, y, W, H, 3, ["Turn the jack screw. The rotor", "goes down ONLY by the screw"])
    stand(x, y - 40)
    rotor(x, y - 40, -40)
    S.rect(x + 180, y + 20, 20, 50, fill=C["brass"])
    S.path(f"M{x + 160},{y + 30} A30,12 0 0 0 {x + 220},{y + 30}", stroke=C["ink"], sw=2.5)
    S.arrow(x + 218, y + 31, x + 224, y + 24, C["ink"], 2, 9)
    S.arrow(x + 330, y + 140, x + 330, y + 220, C["ink"], 4)
    y = 490
    x = 20
    S.panel(x, y, W, H, 4, ["A strip gets tight? STOP. Check the", "guide. Never push the rotor sideways"])
    stand(x, y - 60)
    rotor(x, y - 60, 0)
    S.rect(x + 104, y + 165, 6, 60, fill=C["g10"], sw=1.5)
    S.cross(x + 60, y + 90, 22)
    S.path(f"M{x + 15},{y + 230} l40,0", stroke=C["bad"], sw=4)
    S.text(x + 35, y + 220, "no!", 15, weight="bold", color=C["bad"])
    S.text(x + 190, y + 312, "stop · look · fix the guide", 14, weight="bold")
    x = 410
    S.panel(x, y, W, H, 5, ["Rear bearing sits on its cone:", "take the load off, pull out the strips"])
    stand(x, y - 60)
    rotor(x, y - 60, 40)
    for xx in (x + 107, x + 270):
        S.arrow(xx + 3, y + 160, xx + 3, y + 90, "#2b8a3e", 3)
    S.tick(x + 330, y + 70)
    x = 800
    S.panel(x, y, W, H, 6, ["Turn it one full turn by hand:", "free, smooth, no rubbing"])
    S.circle(x + 190, y + 170, 110, fill=C["steel"], sw=3)
    S.circle(x + 190, y + 170, 95, fill="#5f6b7a", sw=2)
    S.circle(x + 190, y + 170, 30, fill="#8a95a5", sw=2)
    S.path(f"M{x + 110},{y + 40} A140,140 0 0 1 {x + 290},{y + 50}", stroke=C["ok"], sw=4)
    S.arrow(x + 286, y + 48, x + 296, y + 56, C["ok"], 4, 14)
    S.text(x + 190, y + 300, "rub? lift it off and look", 14, weight="bold", color=C["bad"])
    return S


# ============================================================ G18 air gap
@fig
def g18_gap():
    S = Svg(1200, 560, "G18 Check the air gap")
    S.header("G18  Check the air gap at 8 places × 2 ends (brass or plastic feelers only)")
    cx, cy, R1, R2 = 300, 300, 200, 180
    S.circle(cx, cy, R1 + 30, fill=C["steel"], sw=3)
    S.circle(cx, cy, R1, fill=C["mag_n"], sw=1.5)
    S.circle(cx, cy, R1 - 4, fill="white", sw=1)
    S.circle(cx, cy, R2, fill="#5f6b7a", sw=2)
    S.circle(cx, cy, 70, fill="#8a95a5", sw=2)
    for k in range(8):
        a = math.radians(k * 45)
        xx, yy = cx + (R1 + R2) / 2 * math.sin(a), cy - (R1 + R2) / 2 * math.cos(a)
        S.bubble(xx, yy, k + 1, 13, C["brass"])
    S.text(cx, cy + 6, "rear view", 15, weight="bold", color="white")
    S.rect(620, 90, 560, 300, fill=C["light"], stroke="#c9ced6", rx=8)
    S.lines(640, 125, ["1  Look through the inspection port.", "2  Slide a brass feeler between the sleeve",
                       "    and a tooth tip. Write the size.", "3  Turn the rotor 45°, repeat to 8.",
                       "4  Do it at the front end and rear end.", "", "Every reading:      ≥ 1.80 mm",
                       "Biggest − smallest:  ≤ 0.20 mm"], 17, "start")
    S.tick(1120, 330)
    S.rect(620, 410, 560, 120, fill="white", stroke="#c9ced6", rx=8)
    hdr = ["pos", "1", "2", "3", "4", "5", "6", "7", "8"]
    for i, h in enumerate(hdr):
        S.text(650 + i * 60, 440, h, 15, weight="bold")
        S.text(650 + i * 60, 475, "front" if i == 0 else "____", 13)
        S.text(650 + i * 60, 505, "rear" if i == 0 else "____", 13)
    return S


# ============================================================ G19 safety
@fig
def g19_safety():
    S = Svg(1200, 520, "G19 Safety signs")
    S.header("G19  Safety: read this before any magnet, resin or high-voltage work")
    items = [
        ("magnet", ["Magnets snap together", "and crush fingers.", "Use the jig. Rings off."]),
        ("heart", ["Pacemaker or ICD?", "Do not enter the", "magnet room."]),
        ("steel", ["No loose steel", "near magnets.", "Non-magnetic tools."]),
        ("grind", ["Never grind or drill", "magnets. Dust burns.", "Chips → oil tin."]),
        ("hv", ["High voltage tests", "only in the fenced", "area. Earth after."]),
        ("glove", ["Resin hurts skin.", "Nitrile gloves,", "glasses, extraction."]),
        ("sling", ["Lift with textile", "slings near the", "rotor, never chains."]),
        ("two", ["Magnet work:", "always two people,", "one only watches."]),
    ]
    for i, (k, txt) in enumerate(items):
        x = 20 + (i % 4) * 292
        y = 80 + (i // 4) * 215
        S.rect(x, y, 276, 200, fill="white", stroke="#c9ced6", sw=2, rx=10)
        cx, cy = x + 138, y + 68
        S.circle(cx, cy, 48, fill="white", stroke=C["bad"] if k not in ("glove", "sling", "two") else C["mag_s"], sw=7)
        if k == "magnet":
            S.path(f"M{cx - 25},{cy - 25} L{cx - 25},{cy + 5} A25,25 0 0 0 {cx + 25},{cy + 5} L{cx + 25},{cy - 25}",
                   stroke=C["mag_n"], sw=12)
            S.rect(cx - 31, cy - 30, 12, 10, fill="white", stroke="white", sw=0)
            S.rect(cx + 19, cy - 30, 12, 10, fill="white", stroke="white", sw=0)
        elif k == "heart":
            S.path(f"M{cx},{cy + 22} C{cx - 40},{cy - 5} {cx - 18},{cy - 35} {cx},{cy - 12} "
                   f"C{cx + 18},{cy - 35} {cx + 40},{cy - 5} {cx},{cy + 22} Z", fill=C["bad"], stroke=C["bad"])
        elif k == "steel":
            S.rect(cx - 25, cy - 8, 50, 16, fill=C["steel_d"])
            S.circle(cx - 20, cy - 16, 6, fill=C["grey"])
        elif k == "grind":
            S.circle(cx, cy, 20, fill=C["grey"])
            for a in range(5):
                S.line(cx + 22, cy + a * 4 - 8, cx + 38, cy + a * 8 - 20, C["hot"], 2)
        elif k == "hv":
            S.path(f"M{cx - 4},{cy - 30} L{cx - 16},{cy + 4} L{cx + 2},{cy + 4} L{cx - 6},{cy + 30} L{cx + 18},{cy - 6} "
                   f"L{cx + 1},{cy - 6} L{cx + 10},{cy - 30} Z", fill=C["warn"], sw=2)
        elif k == "glove":
            S.rect(cx - 18, cy - 20, 36, 40, fill="#74c0fc", rx=10)
            for j in range(4):
                S.rect(cx - 18 + j * 9, cy - 34, 8, 18, fill="#74c0fc", rx=4)
        elif k == "sling":
            S.path(f"M{cx - 25},{cy + 20} L{cx},{cy - 20} L{cx + 25},{cy + 20}", stroke=C["warn"], sw=8)
        elif k == "two":
            for dx in (-14, 14):
                S.circle(cx + dx, cy - 14, 8, fill=C["ink"])
                S.rect(cx + dx - 9, cy - 4, 18, 26, fill=C["ink"], rx=6)
        if k not in ("glove", "sling", "two"):
            S.line(cx - 34, cy - 34, cx + 34, cy + 34, C["bad"], 7)
        S.lines(x + 138, y + 142, txt, 15)
    return S


def main(png=False):
    names = []
    for fn in FIGS:
        S = fn()
        name = fn.__name__.split("_", 1)
        fname = f"{name[0].upper()}-{name[1]}.svg"
        S.save(OUT / fname)
        names.append(fname)
    print("\n".join(names))
    if png:
        import subprocess
        subprocess.run(["node", str(HERE / "render_png.js"), str(OUT)], check=True)


if __name__ == "__main__":
    main("--png" in sys.argv)
