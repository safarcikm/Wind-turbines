"""Isometric pictures for doc 18 (I01..I05), drawn from the real P1 geometry.

Run:  python3 figures_iso.py          -> out/I01..I05 *.svg
      python3 figures_iso.py --png    -> also PNG copies of everything in out/

All solids come from cad/nacelle_p1/geometry.py (drum, carrier, spindle,
magnets, covers) and from the segment outline in figures.py, so the views
follow the design. Generator axis is vertical in every view; "front up" means
the hub end is at the top (z = 480 - x), as on the S80 stand and in J40.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from figures import G, GEN, OUT, polar, segment_world  # noqa: E402
from iso import STAND, Scene, Xf, move, rotz  # noqa: E402
from svgfig import C, Svg  # noqa: E402

FIGS = []


def fig(fn):
    FIGS.append(fn)
    return fn


PITCH = 360.0 / GEN["slots"]           # 8°
POLE = 360.0 / GEN["poles"]            # 9°
X0 = 480.0                             # z = X0 - x  (front up)
STEEL_SEG = "#aeb6bf"
CARRIER_COL = "#8f9aa6"
DRUM_COL = "#c3cad2"
SPINDLE_COL = "#7d8792"


# ------------------------------------------------------------ building blocks
def rrect(cx, cy, w, h, r, n=4):
    """Rounded rectangle loop (CCW)."""
    pts = []
    for (qx, qy, a0) in ((cx + w / 2 - r, cy + h / 2 - r, 0), (cx - w / 2 + r, cy + h / 2 - r, 90),
                         (cx - w / 2 + r, cy - h / 2 + r, 180), (cx + w / 2 - r, cy - h / 2 + r, 270)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((qx + r * math.cos(a), qy + r * math.sin(a)))
    return pts


COIL_T = 6.5          # coil build per side (mm), from the layer plan (4 layers of Ø1.6 grade 2)


def coil_loops(stack0, stack1, gap=1.6):
    w = GEN["w_t"] + 2 * gap
    h = (stack1 - stack0) + 2 * gap
    zc = (stack0 + stack1) / 2
    inner = rrect(0, zc, w, h, 2.5)
    outer = rrect(0, zc, w + 2 * COIL_T, h + 2 * COIL_T, 2.5 + COIL_T)
    return [outer, inner]


def add_segment(sc, xf, w0, w1, n_arc=4, coil=False, caps=False, layer=0, bias=0.0):
    """One stator segment in its own (x, y=radial) plane, extruded along w."""
    sc.prism([segment_world(n_arc)], w0, w1, STEEL_SEG, xf=xf, layer=layer, bias=bias)
    if caps:
        cap = rrect(0, (GEN["r_slot_bot"] + GEN["r_s"]) / 2 - 2, GEN["w_t"] + 3, GEN["r_s"] - GEN["r_slot_bot"] - 2, 2)
        sc.prism([cap], w0 - 3, w0, C["pps"], xf=xf, layer=layer, bias=bias)
        sc.prism([cap], w1, w1 + 3, C["pps"], xf=xf, layer=layer, bias=bias)
    if coil:
        # coil frame: a = x (tangential), b = w (axial), c = y (radial)
        cf = Xf(((1, 0, 0), (0, 0, 1), (0, 1, 0))).then(xf)
        sc.prism(coil_loops(w0, w1), GEN["r_slot_bot"] + 1.5, GEN["r_slot_top"] - 1.5, C["cu"], xf=cf,
                 layer=layer, bias=bias, cap_fill=C["cu_l"])


def carrier_grooved_loop(n_arc=3):
    """Carrier outer outline at the stack: circle r_si with 45 dovetail grooves (CCW, world XY)."""
    r = GEN["r_si"]
    half = PITCH / 2
    th_foot = math.degrees(math.asin(7.0 / r))
    one = [polar(r, half - (half - th_foot) * i / n_arc) for i in range(n_arc + 1)]
    one += [(7.0, math.sqrt(r * r - 49)), (10.46, r - 6.0), (-10.46, r - 6.0), (-7.0, math.sqrt(r * r - 49))]
    one += [polar(r, -th_foot - (half - th_foot) * i / n_arc) for i in range(n_arc + 1)][:-1]
    loop = []
    for k in range(GEN["slots"]):
        c, s = math.cos(math.radians(k * PITCH)), math.sin(math.radians(k * PITCH))
        loop += [(x * c - y * s, x * s + y * c) for x, y in one]
    return loop


def circle_loop(r, n=90):
    return [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def spindle_profile():
    return list(G.SPINDLE_OUTER) + [(G.SPINDLE["x_front"], 45.0)]


def add_spindle(sc, dz=0.0, step=8.0, th=(0, 360), layer=0):
    sc.revolve(spindle_profile(), SPINDLE_COL, th[0], th[1], step=step, axial=(X0 + dz, -1), layer=layer)


def add_carrier(sc, dz=0.0, grooves=True, layer=0):
    rear = [(415.0, 90.0), (440.0, 90.0), (440.0, 228.0), (417.0, 228.0), (417.0, 200.0), (415.0, 200.0)]
    sc.revolve(rear, CARRIER_COL, step=6.0, axial=(X0 + dz, -1), layer=layer)
    z0, z1 = X0 + dz - 417.0, X0 + dz - 343.5
    outer = carrier_grooved_loop() if grooves else circle_loop(GEN["r_si"])
    sc.prism([outer, circle_loop(200.0, 72)], z0, z1, CARRIER_COL, layer=layer)


def add_stator(sc, dz=0.0, coils=True, missing=(), n_arc=3, layer=0):
    z0, z1 = X0 + dz - G.X_STACK[1], X0 + dz - G.X_STACK[0]
    for k in range(GEN["slots"]):
        if k in missing:
            continue
        add_segment(sc, rotz(k * PITCH), z0, z1, n_arc=n_arc, coil=coils, layer=layer)


def add_rotor(sc, dz=0.0, cut=(90.0, 360.0), front_up=True, magnets=True, disc=True, step=4.0, layer=0):
    """Drum (cut-away between 0° and 90°, the side facing the viewer) with its 160 magnets."""
    axial = (X0 + dz, -1) if front_up else (dz, 1)
    for pts in G.DRUM_PARTS.values():
        sc.revolve(pts, DRUM_COL, cut[0], cut[1], step=step, axial=axial, layer=layer)
    if disc:
        sc.revolve(G.DISC_POLY, "#9aa3ad", cut[0], cut[1], step=step, axial=axial, layer=layer)
    if magnets:
        m = G.MAGNET
        for p in range(GEN["poles"]):
            tc = 4.5 + p * POLE
            a0, a1 = tc - m["arc_deg"] / 2, tc + m["arc_deg"] / 2
            if a1 <= cut[0] or a0 >= cut[1]:
                continue
            a0, a1 = max(a0, cut[0]), min(a1, cut[1])
            col = C["mag_n"] if p % 2 == 0 else C["mag_s"]
            for i in range(m["axial_pieces"]):
                u0 = G.X_STACK[0] + i * 18.5
                prof = [(u0, m["r_in"]), (u0 + m["length"], m["r_in"]), (u0 + m["length"], m["r_out"]),
                        (u0, m["r_out"])]
                sc.revolve(prof, col, a0, a1, step=8.0, axial=axial, layer=layer, bias=15.0)


def fit(sc, x, y, w, h):
    """Scale and origin that fit the whole scene into a box on paper."""
    pts = [p for f in sc.faces for lp in (f.get("loops") or [f["wire"]]) for p in lp]
    xs = [(p[0] - p[1]) * 0.8660254 for p in pts]
    ys = [-(p[2] - (p[0] + p[1]) * 0.5) for p in pts]
    s = min(w / (max(xs) - min(xs)), h / (max(ys) - min(ys)))
    ox = x + (w - s * (max(xs) - min(xs))) / 2 - s * min(xs)
    oy = y + (h - s * (max(ys) - min(ys))) / 2 - s * min(ys)
    return ox, oy, s


def tag(S, sc, F, p3, tx, ty, n, rows, size=15):
    """Numbered call-out: dot on the part, line to a numbered bubble and text."""
    x, y = sc.proj(p3, *F)
    S.line(x, y, tx, ty, C["ink"], 1.5)
    S.circle(x, y, 4, fill=C["ink"], stroke="white", sw=1.5)
    right = tx >= x
    if n is None:
        S.circle(tx, ty, 4, fill=C["ink"], stroke="none")
        off = 8
    else:
        S.bubble(tx, ty, n, r=15)
        off = 22
    S.lines(tx + (off if right else -off), ty + size * 0.35, rows if isinstance(rows, list) else [rows], size,
            "start" if right else "end")


def cyl_pt(r, th_deg, z):
    t = math.radians(th_deg)
    return (r * math.cos(t), r * math.sin(t), z)


# ============================================================ I01 exploded generator
@fig
def i01_exploded():
    S = Svg(1300, 1180, "I01 Exploded generator")
    S.header("I01  The generator in 3D, pulled apart (isometric, exploded)",
             "Real shapes from geometry.py. Parts go together straight down the middle line, in the order 1 to 5.")
    sc = Scene()
    DZ_ROTOR, DZ_STATOR, DZ_COVER = 520.0, 230.0, -110.0
    add_spindle(sc)
    add_carrier(sc)
    add_stator(sc, dz=DZ_STATOR)
    add_rotor(sc, dz=DZ_ROTOR)
    sc.revolve(G.REAR_COVER, C["al"], step=5, axial=(X0 + DZ_COVER, -1))
    F = fit(sc, 340, 90, 640, 1060)
    sc.render(S, *F)
    # dashed centre line on top so it reads as "everything on one axis"
    a = sc.proj((0, 0, X0 + DZ_COVER - 480), *F)
    b = sc.proj((0, 0, X0 + DZ_ROTOR - 60), *F)
    S.line(a[0], a[1], b[0], b[1], C["grey"], 1.5, "16,6,4,6")
    zr = X0 + DZ_ROTOR
    tag(S, sc, F, cyl_pt(323, 120, zr - 330), 300, 230, 4, ["ROTOR drum", "turns with the blades"])
    tag(S, sc, F, cyl_pt(305.3, 90, zr - 380), 300, 360, None, ["160 magnets glued inside", "(red = N, blue = S)"])
    tag(S, sc, F, cyl_pt(318, 0, zr - 300), 1040, 230, None, ["cut open here so you", "can see inside"])
    tag(S, sc, F, cyl_pt(437, 330, zr - 443), 1040, 380, None, ["brake disc"])
    tag(S, sc, F, cyl_pt(290, 45, X0 + DZ_STATOR - 380), 300, 640, 3, ["STATOR: 45 segments,", "each with 1 copper coil"])
    tag(S, sc, F, cyl_pt(70, -20, X0 - 80), 1040, 560, 1, ["SPINDLE: fixed,", "never turns"])
    tag(S, sc, F, cyl_pt(228, 330, X0 - 430), 1040, 760, 2, ["CARRIER: holds the", "segments in 45 grooves"])
    tag(S, sc, F, cyl_pt(345, 120, X0 + DZ_COVER - 470), 300, 960, 5, ["rear cover", "(fitted last)"])
    S.rect(980, 1000, 300, 130, fill=C["light"], stroke="#c9ced6", rx=8)
    S.lines(995, 1028, ["Order: 1 spindle on the stand,", "2 carrier bolted on, 3 slide", "segments into the grooves,",
                        "4 rotor lowered on (J40),", "5 rear cover."], 15, "start")
    return S


# ============================================================ I02 one segment, 3 steps
@fig
def i02_segment():
    S = Svg(1200, 640, "I02 One segment in 3D")
    S.header("I02  One stator segment in 3D: stack it, insulate it, wind it",
             "Isometric views, drawn 3× larger than real. The tooth points up, the dovetail foot is at the bottom.")
    y_off = GEN["r_si"] - 6.0
    base = move(0, 0, -y_off)
    xf = STAND.then(Xf(t=(0, 0, -y_off)))
    panels = [(20, "Stack 205 sheets (0.35 mm) = 74 mm", "1"), (410, "Caps on both ends, yellow liner", "2"),
              (800, "Wind 28 turns around the tooth", "3")]
    for i, (px, cap, n) in enumerate(panels):
        S.panel(px, 80, 380, 540, int(n), [cap])
        sc = Scene()
        if i == 0:
            add_segment(sc, xf, 0, 60, n_arc=8)
            for j, w in enumerate((92, 104, 116)):
                add_segment(sc, xf, w, w + 1.4, n_arc=8, bias=200 + j)
        elif i == 1:
            add_segment(sc, xf, 0, 74, n_arc=8, caps=True)
            # slot liner on both tooth sides (drawn 1.2 mm thick so it can be seen)
            for sx in (-1, 1):
                x0 = sx * GEN["w_t"] / 2
                x1 = x0 + sx * 1.2
                lp = [(min(x0, x1), GEN["r_slot_bot"]), (max(x0, x1), GEN["r_slot_bot"]),
                      (max(x0, x1), GEN["r_slot_top"] - 1), (min(x0, x1), GEN["r_slot_top"] - 1)]
                sc.prism([lp], -2, 76, C["liner"], xf=xf)
        else:
            add_segment(sc, xf, 0, 74, n_arc=8, caps=True, coil=True)
            top = GEN["r_slot_top"] - 1.5 - y_off
            for dx, col in ((-4, C["cu"]), (4, C["cu"])):
                sc.wire([(dx, -7, top - 8), (dx, -30, top + 6), (dx, -55, top + 6)], col, 4, bias=500)
        F = fit(sc, px + 30, 125, 320, 370)
        sc.render(S, *F)
        if i == 0:
            a = sc.proj((0, 135, 60), *F)
            b = sc.proj((0, 75, 60), *F)
            S.arrow(a[0], a[1], b[0], b[1], C["ok"], 4)
            p0, p1 = sc.proj((20, 0, 0), *F), sc.proj((20, 60, 0), *F)
            S.text(px + 200, 524, "glue every sheet; push", 14, color=C["grey"])
            S.text(px + 200, 542, "on the dovetail gauge", 14, color=C["grey"])
        if i == 1:
            S.text(px + 190, 524, "black = PPS end caps", 14, color=C["grey"])
            S.text(px + 190, 542, "yellow = slot liner", 14, color=C["grey"])
        if i == 2:
            S.text(px + 190, 524, "4 wires side by side,", 14, color=C["grey"])
            S.text(px + 190, 542, "two leads out at the rear", 14, color=C["grey"])
    return S


# ============================================================ I03 segments into the carrier
@fig
def i03_stator():
    S = Svg(1300, 900, "I03 Segments into the carrier")
    S.header("I03  Slide the wound segments down into the carrier grooves (stand NP1-T05)",
             "Isometric view, front end up. 40 segments are in, the next one goes straight down its groove.")
    sc = Scene()
    add_carrier(sc)
    k = 36                                   # front-right, so the empty grooves face the viewer
    missing = set(range(k - 2, k + 3))
    add_stator(sc, coils=True, missing=missing)
    z0, z1 = X0 - G.X_STACK[1], X0 - G.X_STACK[0]
    LIFT = 330.0
    add_segment(sc, rotz(k * PITCH), z0 + LIFT, z1 + LIFT, n_arc=3, coil=True, bias=3000)
    F = fit(sc, 300, 90, 680, 780)
    sc.render(S, *F)
    t = math.radians(90 + k * PITCH)
    a = sc.proj((330 * math.cos(t), 330 * math.sin(t), z1 + LIFT - 20), *F)
    b = sc.proj((330 * math.cos(t), 330 * math.sin(t), z1 + 10), *F)
    S.arrow(a[0] + 40, a[1], b[0] + 40, b[1], C["ok"], 5, 16)
    g0 = sc.proj((GEN["r_si"] * math.cos(t), GEN["r_si"] * math.sin(t), z1 + LIFT), *F)
    g1 = sc.proj((GEN["r_si"] * math.cos(t), GEN["r_si"] * math.sin(t), z1), *F)
    S.line(g0[0], g0[1], g1[0], g1[1], C["ok"], 2, "8,6")
    tag(S, sc, F, (262 * math.cos(t), 262 * math.sin(t), z1 + LIFT - 30), 1040, 160, 1,
        ["next segment, coil on,", "slides DOWN its groove"])
    tq = math.radians(90 + (k - 2) * PITCH)
    tag(S, sc, F, (GEN["r_si"] * math.cos(tq), GEN["r_si"] * math.sin(tq), z1 - 30), 1040, 330, 2,
        ["empty dovetail groove", "(clean, no burrs)"])
    tc = math.radians(90 + 31 * PITCH)
    tag(S, sc, F, (296 * math.cos(tc), 296 * math.sin(tc), z1 - 37), 1040, 500, 3,
        ["copper coil around", "every steel tooth"])
    tr = math.radians(90 + (k - 1) * PITCH)
    tag(S, sc, F, (226 * math.cos(tr), 226 * math.sin(tr), X0 - 421), 280, 760, 4,
        ["rear stop: every segment", "must touch it"])
    tw = math.radians(150)
    tag(S, sc, F, (200 * math.cos(tw), 200 * math.sin(tw), z1), 280, 230, 5,
        ["CARRIER (bolted to", "the spindle later)"])
    S.rect(980, 660, 300, 145, fill=C["light"], stroke="#c9ced6", rx=8)
    S.lines(995, 688, ["Push only on the steel yoke,", "with the plastic drift.", "Never push on the copper.",
                       "Go in tooth order 1 to 45", "(Appendix A).", "Leads all point to the rear."], 15, "start")
    return S


# ============================================================ I04 rotor with magnets
@fig
def i04_rotor():
    S = Svg(1300, 860, "I04 Rotor drum with magnets")
    S.header("I04  The rotor drum with its 160 magnets (isometric, cut open)",
             "Open end up, as on the magnet jig. A quarter is cut away so you can see the rings of magnets inside.")
    sc = Scene()
    add_rotor(sc, dz=-80, front_up=False, step=3.0)
    F = fit(sc, 330, 90, 680, 740)
    sc.render(S, *F)
    zm = G.X_STACK[0] - 80
    tag(S, sc, F, cyl_pt(301.5, 184.5, zm + 45), 300, 200, 1, ["a pole = 4 magnets in", "a row, all one colour"])
    tag(S, sc, F, cyl_pt(301.5, 175.5, zm + 25), 300, 330, 2, ["next pole: other colour", "N, S, N, S ... 40 poles"])
    tag(S, sc, F, cyl_pt(316, 90, zm + 20), 1040, 420, 3, ["drum wall (cut)", "magnets sit on Ø618.4"])
    tag(S, sc, F, cyl_pt(437, 330, G.DISC_POLY[0][0] - 80 + 8), 1040, 230, 4, ["brake disc", "(open end)"])
    tag(S, sc, F, cyl_pt(120, 300, 200 - 80), 1040, 640, 5, ["bearing housing", "(front end, bottom)"])
    S.rect(20, 660, 330, 130, fill=C["light"], stroke="#c9ced6", rx=8)
    S.lines(35, 688, ["Glue all 80 red (N) pieces first,", "then the 80 blue (S) pieces.",
                      "Every magnet pulls very hard:", "one at a time, with the jig,", "never two in your hands."],
            15, "start")
    return S


# ============================================================ I05 rotor lowered onto stator
@fig
def i05_join():
    S = Svg(1300, 1100, "I05 Rotor over the stator")
    S.header("I05  J40: lower the rotor over the stator, by the screw only",
             "Isometric view. Spindle stands on its rear flange, rotor comes down rear end first, magnets facing the coils.")
    sc = Scene()
    LIFT = 230.0
    add_spindle(sc)
    add_carrier(sc)
    add_stator(sc)
    add_rotor(sc, dz=LIFT, step=4.0)
    # guide tool NP1-T01: guide sleeve on the spindle nose + screw jack above
    top = X0 + LIFT - 80
    sc.cylinder(55, X0 - 40, top + 160, "#d9dde2", r_in=45, step=10)
    sc.cylinder(18, top + 160, top + 300, C["brass"], step=20)
    sc.cylinder(90, top + 300, top + 318, C["warn"], r_in=70, step=8)
    sc.box(-78, -6, top + 303, 78, 6, top + 313, C["warn"])
    sc.box(-6, -78, top + 303, 6, 78, top + 313, C["warn"])
    # four feelers at the gap entry
    for a in (45, 135, 225, 315):
        t = math.radians(a)
        cx, cy = 300.0 * math.cos(t), 300.0 * math.sin(t)
        sc.box(cx - 5, cy - 5, X0 - 343, cx + 5, cy + 5, X0 - 343 + 70, C["g10"], bias=50)
    F = fit(sc, 320, 80, 680, 990)
    sc.render(S, *F)
    a = sc.proj(cyl_pt(330, 0, X0 + LIFT - 200), *F)
    S.arrow(a[0] + 60, a[1] - 60, a[0] + 60, a[1] + 120, C["ok"], 6, 18)
    S.text(a[0] + 80, a[1] + 40, "slowly", 18, "start", "bold", C["ok"])
    tag(S, sc, F, cyl_pt(90, 330, top + 318), 1040, 150, 1, ["screw jack: turn the wheel,", "the rotor goes down"])
    tag(S, sc, F, cyl_pt(55, 330, top + 60), 1040, 300, 2, ["guide sleeve NP1-T01", "keeps it on centre"])
    tag(S, sc, F, cyl_pt(323, 120, X0 + LIFT - 330), 300, 420, 3, ["ROTOR (cut open),", "rear end down"])
    tag(S, sc, F, cyl_pt(300, 45, X0 - 343 + 60), 1040, 640, 4, ["4 feelers 1.5 mm at 90°", "in the gap: watch them"])
    tag(S, sc, F, cyl_pt(290, 60, X0 - 380), 300, 800, 5, ["STATOR with coils,", "on the spindle"])
    S.rect(960, 860, 320, 170, fill="#fff4e6", stroke=C["warn"], sw=2.5, rx=8)
    S.warn(990, 895, 34)
    S.lines(1015, 900, ["Magnets pull 1.9 kN per mm", "if the rotor goes off centre."], 15, "start", "bold")
    S.lines(980, 960, ["A feeler goes tight: STOP.", "Never push sideways by hand.", "No loose steel within 2 m."],
            15, "start")
    return S


def main(png=False):
    for fn in FIGS:
        S = fn()
        name = fn.__name__.split("_", 1)
        fname = f"{name[0].upper()}-iso-{name[1]}.svg"
        S.save(OUT / fname)
        print(fname)
    if png:
        import subprocess
        subprocess.run(["node", str(HERE / "render_png.js"), str(OUT)], check=True)


if __name__ == "__main__":
    main("--png" in sys.argv)
