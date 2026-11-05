"""Drawing set for generator Rev C (doc 23): segmented stator + N45SH block rotor.

Each function returns a draft.Sheet (A3, PDF + 1:1 DXF). Geometry comes from
cad/nacelle_p1/geometry.py (master, Rev C), rotor_rc.py (magnets, comb bars,
end rings) and generator_mfg/figures.py (segment outline with dovetail foot).

Run via build_rc.py.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "nacelle_p1"))
sys.path.insert(0, str(HERE.parent / "generator_mfg"))
sys.path.insert(0, str(HERE))
import geometry as G  # noqa: E402
from draft import Sheet as _Sheet  # noqa: E402
import drawings as D0  # noqa: E402
import rotor_rc as R  # noqa: E402
from figures import segment_world  # noqa: E402

GEN = G.GEN
DATE = "2026-11-05"
PROJ = "12 kW WIND TURBINE (ICELAND) · GENERATOR REV C (DOC 23)"
ALL = []


def sheet(*a, **k):
    s = _Sheet(*a, **k)
    s.date, s.project, s.rev = DATE, PROJ, k.get("rev", "C")
    return s


def reg(fn):
    ALL.append(fn)
    return fn


def kg(name):
    for it in G.mass_table():
        if name in it.name:
            return f"{it.mass:.1f} kg"
    return ""


def title(v, x, y, text, h=3.0):
    v.text((x, y), text, h, "left", "bottom")


# Rev C cooling (doc 23 §6): fan blades on the inside of the rear cover
FAN = dict(n=24, r0=240.0, r1=308.0, h=18.0, t=4.0)   # x 447 to 465, inside the shell ID 624


# ====================================================================== GA

def fin_poly():
    f = G.ROTOR_FINS
    return [(f["x0"], f["leg_r0"]), (f["leg_x1"], f["leg_r0"]), (f["leg_x1"], f["r0"]), (f["x1"], f["r0"]),
            (f["x1"], f["r1"]), (f["x0"], f["r1"])]


def rib_poly():
    rb = G.DRUM_RIBS
    return [(rb["x0"], 318.0), (335.0, 318.0), (335.0, 323.0), (425.0, 323.0), (425.0, 318.0), (rb["x1"], 318.0),
            (rb["x1"], rb["r_tip"]), (rb["x0"], rb["r_tip"])]


@reg
def ga_generator():
    s = sheet("NP1-G00", "GENERATOR REV C · ASSEMBLY SECTION", "see parts list",
              "≈ 330 kg drivetrain (no hub)", "1:2.2", rev="C")
    v = s.view("GA", 0.45, (0, 55))
    # stationary
    v.poly(G.spindle_section(), hatch=True)
    v.poly([(46, 20), (466, 20), (466, 45), (46, 45)])                      # cooling insert
    v.poly(G.SPACER_POLY, hatch=True)
    v.poly(G.SEAL_SLEEVE_POLY, hatch=True)
    v.poly(G.CARRIER, hatch=True)
    v.poly(G.STATOR_RING, hatch=True)
    # stack (segments) incl. dovetail foot, coils
    v.poly([(G.X_STACK[0], GEN["r_si"] - 6), (G.X_STACK[1], GEN["r_si"] - 6), (G.X_STACK[1], GEN["r_s"]),
            (G.X_STACK[0], GEN["r_s"])], fill="0.55")
    for x0, x1 in ((G.X_STACK[0] - G.END_WINDING, G.X_STACK[0] - 1), (G.X_STACK[1] + 1, G.X_STACK[1] + G.END_WINDING)):
        v.poly([(x0, GEN["r_slot_bot"] + 2), (x1, GEN["r_slot_bot"] + 2), (x1, GEN["r_slot_top"] - 1),
                (x0, GEN["r_slot_top"] - 1)], fill="#c87533")
    # bearings
    for xc in (G.X_BRG_FRONT, G.X_BRG_REAR):
        v.poly([(xc - 22.5, 70), (xc + 22.5, 70), (xc + 22.5, 105), (xc - 22.5, 105)])
        v.line((xc - 22.5, 70), (xc + 22.5, 105), "THIN")
    # rotating
    for p in G.DRUM_PARTS.values():
        v.poly(p, hatch=True)
    for p in (G.SEAL_COVER_FRONT, G.SEAL_COVER_REAR, G.REAR_COVER, G.REAR_SEAL_CARRIER, G.DISC_POLY):
        v.poly(p, hatch=True)
    # fan blades on the rear cover (inside face)
    v.poly([(465 - FAN["h"], FAN["r0"]), (465, FAN["r0"]), (465, FAN["r1"]), (465 - FAN["h"], FAN["r1"])], "THIN")
    # passive cooling: inner fins (front cavity) and outer ribs, rotating with the drum
    v.poly(fin_poly(), fill="0.8")
    v.poly(rib_poly(), fill="0.8")
    # magnets, comb/end rings, sleeve
    for x in R.X_BLOCKS:
        v.poly([(x, R.R_IN), (x + R.L, R.R_IN), (x + R.L, R.R_BACK), (x, R.R_BACK)], fill="0.15")
    for x0, x1 in ((R.SEAT_X[0], R.X_BLOCKS[0]), (R.X_BLOCKS[-1] + R.L, R.SEAT_X[1])):
        v.poly([(x0, R.R_IN), (x1, R.R_IN), (x1, R.R_SEAT), (x0, R.R_SEAT)], fill="#e3c77b")
    v.poly([(R.SEAT_X[0], 301.0), (R.SEAT_X[1], 301.0), (R.SEAT_X[1], R.R_IN), (R.SEAT_X[0], R.R_IN)], fill="#5aa05a")
    v.centerline((30, 0), (485, 0))
    # dims
    v.dim((G.X_STACK[0], GEN["r_s"]), (G.X_STACK[1], GEN["r_s"]), -27, kind="h", text="74 stack", h=2.0)
    v.dim((R.SEAT_X[0], 323), (R.SEAT_X[1], 323), 22, kind="h", text="90 seat", h=2.0)
    tags = [((385, 307), (245, 445), "5 magnet rows, N45SH 30×15×12 (NP1-220E), seat Ø628.05"),
            ((338, 309), (245, 425), "end rings / stepped comb bars, G11 (NP1-222C / 221C)"),
            ((360, 301.2), (245, 405), "glass sleeve, bore Ø602.0; air gap 2.0"),
            ((380, 270), (195, 300), "45 tooth segments Ø598 (NP1-201C)"),
            ((330, 280), (195, 280), "coils 28 turns, potted (NP1-203C)"),
            ((300, 315), (195, 360), "drum NP1-210C, Ø646"),
            ((428, 150), (500, 180), "carrier, 45 dovetails (NP1-200C)"),
            ((456, 280), (500, 150), f"rear cover + {FAN['n']} fan blades (NP1-212C)"),
            ((443, 400), (500, 120), "brake disc NP1-230"),
            ((240, 200), (195, 220), f"{G.ROTOR_FINS['n']} inner fins, 3 mm, on hub web + shell (NP1-210C)"),
            ((300, 336), (195, 380), f"{G.DRUM_RIBS['n']} outer ribs 4 mm, tips Ø{2 * G.DRUM_RIBS['r_tip']:.0f}"),
            ((338, 215), (500, 90), "clamp ring NP1-202")]
    for p, q, t in tags:
        v.leader(p, q, t, 2.0)
    title(v, 30, 465, "GENERATOR SECTION (upper half, 1:2.2)", 3.2)
    s.table = [["#", "Part", "Qty", "Material / note"],
               ["1", "NP1-100 spindle (stationary)", "1", "42CrMo4+QT"],
               ["2", "NP1-200C stator carrier", "1", "S355J2+N, 45 dovetails"],
               ["3", "NP1-201C tooth segment stack", "45+3", "M270-35A bonded, 205 sh."],
               ["4", "NP1-203C coil on segment", "45+3", "28 t × 4 × Ø1.55, cl. 200"],
               ["5", "NP1-202 clamp ring", "1", "1.4404"],
               ["6", "NP1-210C drum weldment", "1", "S355J2+N, seat Ø628.05"],
               ["7", "NP1-220E magnet block", "200+10", "N45SH 30×15×12"],
               ["8", "NP1-221C stepped comb bar", "40+4", "G11"],
               ["9", "NP1-222C end ring F / R", "1+1", "G11"],
               ["10", "glass sleeve (moulded)", "1", "E-glass/epoxy 0.5–0.9"],
               ["11", "NP1-212C rear cover + fan", "1", "5083, 24 blades"],
               ["12", "NP1-230 brake disc", "1", "C45E+N"],
               ["13", "main bearings 32028 X", "2", "bought"]]
    s.table_pos = (243, 283)
    s.table_widths = [7, 55, 13, 82]
    s.notes = [
        "Rev C generator (doc 23): segmented stator of doc 18 (45 tooth segments in carrier dovetail grooves) and the block rotor: one N45SH block 30 × 15 × 12 per pole across, five rows along the 74 mm stack, rows step-skewed 0.20° by the stepped comb bars.",
        "Air gap 2.0 (stator Ø598.0 to sleeve bore Ø602.0); sleeve 0.52 at the block centre, 0.89 at the block edges; magnet face r 301.52.",
        "Interfaces to the nacelle (spindle, bearings, hub flange, disc, bedplate) unchanged from NP1-000 Rev B. Drum OD Ø646 unchanged.",
        "Cooling, all passive (doc 23 §4 and §4a): carrier → spindle → finned insert path (doc 14 §6), 24 blades on the rear cover, 36 inner fins and 48 outer ribs on the drum; hot spot 94 to 105 °C on the hot-day cases (limit 130).",
    ]
    s.notes_top = (243, 214)
    s.notes_wrap = 92
    return s


# ====================================================================== segment
@reg
def segment():
    g = GEN
    s = sheet("NP1-201C", "STATOR TOOTH SEGMENT LAMINATION (45 + 3 PER STATOR)", "M270-35A, 0.35 mm, self-bonding varnish",
              "1.07 kg per stack", "2:1", rev="C")
    v = s.view("seg", 2.0, (110, -372))
    pts = segment_world(12)
    v.poly(pts)
    v.centerline((0, 205), (0, 303))
    for a in (-4.0, 4.0):
        t = math.radians(a)
        v.line((205 * math.sin(t), 205 * math.cos(t)), (303 * math.sin(t), 303 * math.cos(t)), "CENTER")
    wt2 = g["w_t"] / 2
    v.dim((-wt2, 262), (wt2, 262), 0, kind="h", text="22.30 ±0.02 tooth", h=2.0)
    t4 = math.radians(4)
    tip = g["r_s"] * math.sin(t4 - math.radians(math.degrees(g["b0"] / 2 / g["r_s"])))
    v.dim((-tip, g["r_s"]), (tip, g["r_s"]), 10, kind="h", text=f"{2 * tip:.2f} ref (tips; 4.0 slot opening)", h=2.0)
    v.dim((-34, g["r_s"]), (-34, g["r_slot_top"]), 4, kind="v", text="4", h=2.0)
    v.dim((-34, g["r_slot_top"]), (-34, g["r_slot_bot"]), 4, kind="v", text="65.0", h=2.0)
    v.dim((-34, g["r_slot_bot"]), (-34, g["r_si"]), 4, kind="v", text="11.4", h=2.0)
    v.dim((-34, g["r_si"]), (-34, g["r_si"] - 6), 4, kind="v", text="6.0", h=2.0)
    v.dim((-7, g["r_si"] + 0.4), (7, g["r_si"] + 0.4), 6, kind="h", text="14.00 −0.01/−0.03", h=2.0)
    v.dim((-10.46, g["r_si"] - 6), (10.46, g["r_si"] - 6), -5, kind="h", text="20.92 ref", h=2.0)
    v.leader((8.7, g["r_si"] - 3), (30, g["r_si"] - 14), "dovetail flanks 60°", 2.0)
    v.leader((0, g["r_s"]), (28, g["r_s"] + 8), "R299.00 ±0.02 (tooth tip arc)", 2.0)
    v.leader((15, g["r_slot_bot"] + 0.3), (34, g["r_slot_bot"] + 12), "R230.0 slot bottom", 2.0)
    v.leader((13, g["r_si"] + 2), (34, g["r_si"] + 22), "R218.6 yoke (carrier rim)", 2.0)
    v.leader((19.5, 278), (34, 282), "joint on slot centre line, ±4.000°", 2.0)
    title(v, -45, 312, "SEGMENT (2:1), radial direction up", 3.0)
    # small assembled view, 3 segments
    w = s.view("asm", 0.5, (330, 40))
    for k in (-1, 0, 1):
        a = math.radians(8 * k)
        w.poly([(x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)) for x, y in segment_world(6)])
    w.text((-60, 312), "3 OF 45 SEGMENTS (1:2)", 3.0)
    s.notes = [
        "DXF layer OUTLINE = cutting contour. Laser cut (P1), burr ≤ 0.02, heat zone ≤ 0.1; or progressive die (series).",
        "Magnetic contour identical to the doc 14 one-piece lamination; joints on the slot centre lines in the yoke (8.000° pitch).",
        "Stack: 205 sheets, 74.0 ±0.1 (sheets counted, height measured per segment), bonded in fixture NP1-T03 at 1.0 to 1.5 MPa, varnish cure per supplier.",
        "Checks per stack: tip radius R299.00 ±0.02 on gauge, foot width 14.00 −0.01/−0.03, slot opening edges straight 0.05 over 74; Franklin test ≥ 10 Ω·cm².",
        "Do not machine tooth tips after stacking. 45 + 3 spare segments per stator; all identical.",
    ]
    s.notes_top = (215, 285)
    s.notes_wrap = 105
    return s


# ====================================================================== carrier
@reg
def carrier():
    s = sheet("NP1-200C", "STATOR CARRIER WITH 45 DOVETAIL GROOVES", "S355J2+N ring forging or plate, stress relieved",
              kg("Stator carrier"), "1:2.86 / 1:3.6 / 5:1", rev="C")
    v = s.view("A", 0.35, (50, 185))
    X = lambda x: x - 340  # noqa: E731
    v.poly([(X(x), r) for x, r in G.CARRIER], hatch=True)
    v.poly([(X(x), -r) for x, r in G.CARRIER])
    v.centerline((0, 0), (110, 0))
    v.dim((X(343.5), 218.6), (X(417), 218.6), 14, kind="h", text="73.5", h=2.0)
    v.dim((X(343.5), 228), (X(440), 228), 24, kind="h", h=2.0)
    v.dim((X(440), 90), (X(440), -90), -16, kind="v", prefix="Ø", text="180", h=2.0)
    v.dim((X(343.5), 218.6), (X(343.5), -218.6), 14, kind="v", text="Ø437.20 −0.01/−0.02 (groove land)", h=2.0)
    v.dim((X(417), 228), (X(440), -228), -8, kind="v", prefix="Ø", text="456", h=2.0)
    v.text((X(320), -250), "SECTION A-A (1:2.86)", 3.0)
    w = s.view("B", 0.28, (250, 185))
    r = GEN["r_si"]
    pts = []
    for k in range(45):
        for x, y in [(-7.0, math.sqrt(r * r - 49)), (-10.46, r - 6.0), (10.46, r - 6.0), (7.0, math.sqrt(r * r - 49))]:
            a = math.radians(-8 * k)
            pts.append((x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)))
    w.poly(pts)
    w.circle((0, 0), 228, "HIDDEN")
    w.circle((0, 0), 200, "HIDDEN")
    w.circle((0, 0), 90)
    w.bolt_circle((0, 0), 240, 12, 13.0)
    w.bolt_circle((0, 0), 418, 12, 6.8, start=15, layer="HIDDEN")
    w.centerline((-240, 0), (240, 0))
    w.centerline((0, -240), (0, 240))
    w.leader((0, r - 6), (150, 260), "45 dovetail grooves, pitch 8.000° ±0.01°", 2.0)
    w.leader((120, 0), (270, 40), "12× Ø13 thru PCD 240", 2.0)
    w.leader((209 * math.cos(math.radians(15)), 209 * math.sin(math.radians(15))), (270, 120),
             "12× M8 ↧16 PCD 418 (clamp ring)", 2.0)
    w.text((-230, 250), "VIEW B (from front, 1:3.6)", 3.0)
    d = s.view("C", 5.0, (330, 60))
    d.poly([(-14, 212.0 - 212.6 + 6.0), (-7.0, 6.0), (-10.46, 0.0), (10.46, 0.0), (7.0, 6.0), (14, 6.0)], closed=False)
    d.dim((-7.0, 6.0), (7.0, 6.0), 4, kind="h", text="14.00 +0.02/+0.01", h=2.0)
    d.dim((-10.46, 0), (10.46, 0), -4, kind="h", text="20.92", h=2.0)
    d.dim((12, 0), (12, 6), -6, kind="v", text="6.00 ±0.01", h=2.0)
    d.text((-14, 9.5), "DETAIL C: GROOVE (5:1), flanks 60°", 2.6)
    s.notes = [
        "Rev C (doc 18 §5.1): grooves replace the shrink fit and the 3 keys. Grooves open to the front (x 343.5), closed by the rear stack stop (x 417); broached or wire-EDM.",
        "Groove angular position ±0.01°, groove seat radius R212.60 ±0.01 to the bolting-face axis; foot clearance 0.01 to 0.03 (slides by hand when clean), fixed by VPI resin, clamped by NP1-202 (12× M8 A4-80, 20 Nm).",
        "Run-out of groove lands and rear stop face to the bolting face and Ø180 spigot ≤ 0.02; bolting face flatness 0.02.",
        "Bolt to the spindle flange: 12× M12 10.9 + hardened washers, 110 Nm, 2 fitted dowels Ø10 H7 PCD 240; Al-filled paste 0.05 on the full face (heat path, doc 14 §6).",
        "Stress relieve 580 to 620 °C, 2 h, before final machining. No paint on grooves and bolting face; elsewhere epoxy primer 60 µm.",
    ]
    return s


# ====================================================================== coil
@reg
def coil():
    g = GEN
    s = sheet("NP1-203C", "COIL ON SEGMENT (WOUND SEGMENT)", "Cu enamelled Ø1.55 grade 2, class 200; NKN 0.30; PPS GF40 caps",
              "≈ 0.45 kg Cu per coil", "2:1 / 1:1", rev="C")
    v = s.view("sec", 2.0, (110, -372))
    v.poly(segment_world(10))
    wt2 = g["w_t"] / 2
    for sgn in (-1, 1):
        # coil side: layers of 1.66 from the tooth flank (+ liner), heights from the layer plan
        x0 = sgn * (wt2 + 0.35)
        for k, n in enumerate((37, 37, 31, 7)):
            y0 = g["r_slot_bot"] + 1.0
            y1 = min(y0 + n * 1.66, g["r_slot_top"] - 0.8)
            xa, xb = x0 + sgn * k * 1.66, x0 + sgn * (k + 1) * 1.66
            v.poly([(xa, y0), (xb, y0), (xb, y1), (xa, y1)], fill="#c87533")
    v.dim((-wt2, 236), (wt2, 236), 0, kind="h", text="22.3", h=2.0)
    v.leader((wt2 + 3.5, 255), (36, 262), "coil side: 4 layers, 28 turns × 4 strands", 2.0)
    v.leader((wt2 + 0.2, 240), (36, 244), "slot liner NKN 0.30", 2.0)
    v.leader((20.5, 270), (36, 280), "phase separator NKN 0.25 on slot centre line", 2.0)
    v.text((-45, 312), "COIL SIDES IN THE SLOT (2:1)", 3.0)
    w = s.view("side", 1.0, (300, 115))
    L = g["stack"]
    w.poly([(-L / 2, -32), (L / 2, -32), (L / 2, 32), (-L / 2, 32)])
    for d_, lay in ((3, "OUTLINE"), (3 + 6.6, "OUTLINE")):
        w.poly([(-L / 2 - d_, -32 - 0), (L / 2 + d_, -32 - 0), (L / 2 + d_, 32), (-L / 2 - d_, 32)], closed=True,
               layer=lay)
    w.dim((-L / 2, 32), (L / 2, 32), 10, kind="h", text="74.0 stack", h=2.0)
    w.dim((-L / 2 - 9.6, -32), (L / 2 + 9.6, -32), -10, kind="h", text="≈ 93.2 over end turns", h=2.0)
    w.leader((L / 2 + 6.5, 20), (55, 48), "end cap PPS GF40 3 mm", 2.0)
    w.leader((-L / 2 - 6, -20), (-80, -55), "start lead 150, rear end, red tag", 2.0)
    w.text((-60, 62), "SIDE VIEW OF COIL ON TOOTH (1:1, simplified)", 3.0)
    s.table = [["Layer (from tooth flank)", "Positions", "Used"],
               ["1", "37", "37"], ["2", "37", "37"], ["3", "31", "31"], ["4", "17", "7"], ["5", "3", "0 (reserve)"],
               ["Total (28 turns × 4 strands)", "125", "112"]]
    s.table_pos = (215, 283)
    s.table_widths = [48, 22, 24]
    s.notes = [
        "Wind on chuck NP1-T04 by the dovetail, 4 parallel strands Ø1.55 (≤ 1.66 over enamel), 25 to 30 N per strand, layer by layer from the tooth flank, ≤ 60 rpm (doc 18 §5.6).",
        "28 turns per coil (Rev C keeps doc 18): 373 V line at 178 rpm, magnets 100 °C; 389 V at 60 °C. Wire per coil ≈ 6.6 m per strand; R20 per phase 0.217 Ω.",
        "All coils wound the same direction; reversal at connection (doc 18 Appendix A): 15 coils per phase in series, star.",
        "Tests before assembly (doc 18 §5.7): resistance ±2 % of the lot mean, surge 3.5 kV, hipot to the segment 2.3 kV 1 min, IR ≥ 1 GΩ.",
        "After assembly: VPI class H epoxy, end windings potted (doc 18 §5.11, §5.12). PT100 in 6 separator gaps (2 per phase).",
    ]
    s.notes_top = (215, 245)
    s.notes_wrap = 105
    return s


# ====================================================================== drum
@reg
def drum():
    s = sheet("NP1-210C", "ROTOR DRUM WELDMENT (GENERATOR YOKE + BEARING HOUSING)", "S355J2+N, welded, stress relieved",
              f'{kg("Rotor drum")} + {kg("Rotor fins")} fins/ribs', "1:3.8", rev="C")
    v = s.view("A", 0.265, (40, 168))
    X = lambda x: x - 90  # noqa: E731
    for p in G.DRUM_PARTS.values():
        q = [(X(x), r) for x, r in p]
        v.poly(q, hatch=True)
        v.poly([(x, -r) for x, r in q])
    v.poly([(X(x), r) for x, r in fin_poly()], fill="0.8")
    v.poly([(X(x), r) for x, r in rib_poly()], fill="0.8")
    v.leader((X(240), 180), (X(560), 150), f"FIN, {G.ROTOR_FINS['n']}× equally spaced, t3 (note 7)", 2.0)
    v.leader((X(380), 333), (X(560), 190), f"RIB 4×20, {G.DRUM_RIBS['n']}× equally spaced (note 7)", 2.0)
    v.centerline((0, 0), (X(470), 0))
    v.dim((X(92), 120), (X(385), 120), 8, kind="h", h=2.0)
    v.dim((X(195), 345), (X(465), 345), 6, kind="h", h=2.0)
    v.dim((X(335), -323), (X(425), -323), -6, kind="h", h=2.0, suffix=" magnet seat")
    for x, r, t in [(120, 105, "Ø210 P7"), (240, 98, "Ø196"), (360, 105, "Ø210 P7")]:
        v.dim((X(x), -r), (X(x), r), 0, kind="v", text=t, h=2.0, tpos=0.25)
    v.dim((X(390), -R.R_SEAT), (X(390), R.R_SEAT), 0, kind="v", text="Ø628.05 +0.05/0", h=2.0, tpos=0.3)
    v.dim((X(440), -312), (X(440), 312), 0, kind="v", text="Ø624", h=2.0, tpos=0.7)
    s.table = [["Feature", "Size", "Tolerance / note"],
               ["cup seats (2)", "Ø210 × 45", "P7, Ra 0.8, coax. 0.02"],
               ["cup shoulders", "Ø196", "square 0.01 to axis"],
               ["hub spigot", "Ø360 × 5", "f7; face flat 0.03"],
               ["hub web", "20 thick, Ø464", "12× M16 thru PCD 400"],
               ["outer web", "8 thick", "full pen. weld to shell"],
               ["magnet seat (Rev C)", "Ø628.05 × 90", "+0.05/0, coax. 0.02, Ra 3.2"],
               ["seat land x", "335 to 425", "as Rev B"],
               ["shell OD", "Ø646", "steel under seat 8.98"],
               ["shell ID (free)", "Ø624", "clearance to magnets"],
               ["rear flange ring", "Ø624/Ø710 × 14", "M10 PCD 644 + M10 PCD 678"],
               ["inner fins (36)", "t3, x 220-312, r 140-312", "L-plate, web + bore, every 10°"],
               ["outer ribs (48)", "4 × 20, x 222-430", "tips Ø676, every 7.5°"]]
    s.table_pos = (195, 283)
    s.table_widths = [36, 32, 54]
    title(v, 0, 380, "SECTION A-A (weld preps not shown, note 2)", 3.0)
    s.notes = [
        "Rev C: magnet seat Ø628.05 +0.05/0 (was Ø618.40) for the 12 mm N45SH blocks; steel under the seat 8.98 (FEA: 1.45 T median, 1.7 T at the pole edges, included in the EMF).",
        "Welds full penetration at web/housing and web/shell, ISO 5817 B, 100 % MT, UT of the shell seam (ring-rolled shell preferred, doc 18 §4.2). Stress relieve 580 to 620 °C before machining.",
        "Machine in one set-up: cup seats Ø210 P7, magnet seat, hub spigot Ø360 f7, rear flange face; coaxiality ≤ 0.02, shoulders square ≤ 0.01.",
        "Hub web 12× M16 thru PCD 400; rear flange ring 24× M10 PCD 644 (rear cover) and 24× M10 PCD 678 (disc).",
        "Magnet seat: degrease, grit blast Sa 2½ just before bonding; no paint inside. Outside zinc spray + epoxy (C5).",
        "Balance finished rotor (drum, magnets, sleeve, disc, cover) to ISO 21940-11 G2.5 at 250 rpm, correction on the rear flange ring.",
        "Passive cooling (doc 23 §4a): 36 inner fins t3 S355, L-shaped, fillet-welded both sides to hub web and shell bore, every 10°, 9 mm clear of the end windings; 48 outer ribs 4 × 20 S355 on the shell outside, every 7.5°, intermittent fillet welds 30/60 both sides, ends rounded. Weld fins and ribs before stress relief and machining.",
        "Rear flange ring welded to the shell full round, continuous: with the hub web it keeps the 9 mm shell round against the magnet pull (doc 23 §5). Seat roundness 0.05 after stress relief.",
    ]
    return s


# ====================================================================== magnet block
@reg
def magnet():
    W, L, T = R.W, R.L, R.T
    s = sheet("NP1-220E", "MAGNET BLOCK 30 × 15 × 12 (PURCHASE DRAWING)", "Sintered NdFeB N45SH, NiCuNi",
              f"{R.MASS_G:.1f} g each, {R.COUNT * R.MASS_G / 1000:.2f} kg per generator", "5:1", rev="E")
    a = s.view("A", 5.0, (60, 150))
    a.poly([(0, 0), (W, 0), (W, L), (0, L)])
    a.circle((3.5, L - 3.5), 1.5)
    a.dim((0, 0), (W, 0), -8, kind="h", text="30.00 ±0.05", h=2.4)
    a.dim((W, 0), (W, L), -8, kind="v", text="15.00 ±0.05", h=2.4)
    a.text((6.5, L - 4.5), "white dot Ø3 = N face", 2.2)
    a.text((0, L + 4), "VIEW A: N FACE (5:1)", 3.0)
    b = s.view("B", 5.0, (60, 45))
    b.poly([(0, 0), (W, 0), (W, T), (0, T)])
    b.line((W / 2, 1.5), (W / 2, T - 3.0), "THIN")
    b.poly([(W / 2 - 1.2, T - 3.0), (W / 2 + 1.2, T - 3.0), (W / 2, T - 1.0)], fill="k")
    b.text((W / 2 + 1.5, T - 2.5), "N", 3.0)
    b.text((W / 2 + 1.5, 1.0), "S", 3.0)
    b.dim((0, 0), (W, 0), -8, kind="h", text="30.00 ±0.05", h=2.4)
    b.dim((W, 0), (W, T), -8, kind="v", text="12.00 ±0.03", h=2.4)
    b.text((0, T + 4), "VIEW B: END, magnetised through 12 (5:1)", 3.0)
    s.table = [["Item", "Requirement"],
               ["Grade", "N45SH: Br ≥ 1.32 T, HcJ ≥ 1,592 kA/m (20 kOe), (BH)max ≥ 342 kJ/m³ at 20 °C"],
               ["Curves", "J-H and B-H per batch at 20, 60, 100, 120 °C; αBr, βHcJ stated"],
               ["Magnetisation", "Through the 12 mm thickness, saturated; axis within 2° of the face normal"],
               ["Tolerances", "30 ±0.05, 15 ±0.05, 12 ±0.03; faces flat 0.02, parallel 0.02"],
               ["Edges", "Chamfer 0.2 to 0.3 × 45° all 12 edges; no chips > 0.3"],
               ["Coating", "NiCuNi 10 to 20 µm; 72 h neutral salt spray clean; adhesion OK with the epoxy"],
               ["Uniformity", "Moment of each piece within ±1.5 % of the lot mean; value per serial"],
               ["Marking", "White dot Ø3 on the N face; serial on the packaging position"],
               ["Quantity", f"{R.COUNT} + {R.SPARES} spare per generator; 8 extra for Q1 tests"],
               ["Packing", "Repelling layout in non-magnetic spacers; air freight per IATA PI 953"]]
    s.table_pos = (230, 283)
    s.table_widths = [26, 152]
    s.notes = [
        "One part for N and S poles: N poles face N towards the stator, S poles are the same block flipped (dot hidden against the seat).",
        "Solid block (not two 6 mm pieces bonded). If a maker offers only 30 × 15 × 6, the doc 20 bonded pair is the fall-back with identical magnetics.",
        "Five blocks per pole along the stack (15 mm pieces = axial segmentation for eddy loss, 4.7 W at rated).",
        "Release of N45SH for production is conditional on the 100 °C design basis (doc 19 §16.3, doc 23 §4): bench magnet temperature ≤ 75 °C, temperature watch, no deliberate phase shorting.",
    ]
    s.notes_top = (230, 230)
    s.notes_wrap = 98
    return s


# ====================================================================== comb bar
@reg
def comb_bar():
    wi, wo, h = R.comb_bar()
    step = math.radians(R.SKEW_STEP) * R.R_SEAT
    s = sheet("NP1-221C", "STEPPED POLE COMB BAR (40 + 4 PER ROTOR)", "G11 glass-epoxy sheet, CNC machined",
              "≈ 25 g", "3:1 / 5:1", rev="C")
    v = s.view("plan", 3.0, (40, 175))
    x0 = R.SEAT_X[0] + 4.0
    xs = [x0] + [R.X_BLOCKS[i] + R.L + R.SHIM / 2 for i in range(4)] + [x0 + R.COMB_L]
    pts_l, pts_r = [], []
    for i in range(5):
        off = R.ROW_SHIFT[i] / R.SKEW_STEP * step
        pts_l += [(xs[i] - x0, off - wo / 2), (xs[i + 1] - x0, off - wo / 2)]
        pts_r += [(xs[i] - x0, off + wo / 2), (xs[i + 1] - x0, off + wo / 2)]
    v.poly(pts_l + list(reversed(pts_r)))
    v.centerline((-3, 0), (R.COMB_L + 3, 0))
    v.dim((0, -wo / 2 - 3), (R.COMB_L, -wo / 2 - 3), -6, kind="h", text=f"{R.COMB_L:.1f} ±0.1", h=2.2)
    v.ordinate([xs[i] - x0 for i in range(6)], wo / 2 + 2.2, wo / 2 + 9, h=2.0)
    v.dim((xs[2] - x0 + 4, -wo / 2), (xs[2] - x0 + 4, wo / 2), 0, kind="v", text=f"{wo:.2f}", h=2.0, tpos=0.5)
    v.leader((xs[3] - x0, R.ROW_SHIFT[3] / R.SKEW_STEP * step + wo / 2), (60, 26),
             f"step {step:.3f} per row (0.20° at R314.03)", 2.0)
    v.text((0, 31), "PLAN, seen from the stator (3:1). Steps set the row skew.", 3.0)
    w = s.view("sec", 5.0, (360, 115))
    w.poly([(-wi / 2, 0), (wi / 2, 0), (wo / 2, h), (-wo / 2, h)], hatch=True)
    w.dim((-wi / 2, 0), (wi / 2, 0), -6, kind="h", text=f"{wi:.2f} ±0.05", h=2.2)
    w.dim((-wo / 2, h), (wo / 2, h), 6, kind="h", text=f"{wo:.2f} ±0.05 (seat side)", h=2.2)
    w.dim((wo / 2, 0), (wo / 2, h), -8, kind="v", text=f"{h:.1f}", h=2.2)
    w.text((-12, h + 9), "SECTION (5:1), flanks follow the block sides", 2.6)
    s.notes = [
        "One bar per pole gap (40 per rotor + 4 spare). Bar sits on the seat (wide face), bonded with the magnet epoxy; ends engage 4 mm pockets in the end rings NP1-222C.",
        "Row boundaries (ordinates from the front end): steps of 0.20° each; the bar is identical for every gap. Mark the front end.",
        "Side faces are the datum for the blocks: 0.10 glue clearance each side (comb width = gap between neighbouring blocks − 0.20).",
        "G11 (class H), ±0.05 on widths; edges deburred, no delamination. Prove on the Q1 panel (doc 18 §10).",
    ]
    return s


# ====================================================================== end rings
@reg
def end_rings():
    wi, wo, h = R.comb_bar()
    s = sheet("NP1-222C", "MAGNET END RINGS, FRONT AND REAR", "G11 glass-epoxy, machined from tube or segmented",
              "≈ 0.12 kg each", "1:4 / 4:1", rev="C")
    v = s.view("A", 0.25, (120, 160))
    v.circle((0, 0), R.R_SEAT)
    v.circle((0, 0), R.R_IN)
    for k in range(40):
        a = math.radians(k * 9 + 4.5)
        v.line((R.R_SEAT * math.cos(a), R.R_SEAT * math.sin(a)), ((R.R_SEAT - h) * math.cos(a), (R.R_SEAT - h) * math.sin(a)),
               "THIN")
    v.dim((-R.R_SEAT, 0), (R.R_SEAT, 0), 95, kind="h", text="Ø628.05 −0.05/−0.10 (on the seat)", h=2.2)
    v.dim((-R.R_IN, 0), (R.R_IN, 0), -95, kind="h", text="Ø603.03 ±0.05 (flush with block faces)", h=2.2)
    v.leader((R.R_SEAT * math.cos(math.radians(4.5)), R.R_SEAT * math.sin(math.radians(4.5))), (360, 200),
             "40 pockets for the comb bar ends", 2.2)
    v.text((-330, 345), "VIEW (1:4), front ring; rear ring mirrored", 3.0)
    d = s.view("B", 4.0, (300, 90))
    d.poly([(0, 0), (R.RING_W, 0), (R.RING_W, R.R_SEAT - R.R_IN), (0, R.R_SEAT - R.R_IN)], hatch=True)
    d.dim((0, 0), (R.RING_W, 0), -6, kind="h", text=f"{R.RING_W:.1f}", h=2.2)
    d.dim((R.RING_W, 0), (R.RING_W, R.R_SEAT - R.R_IN), -8, kind="v", text=f"{R.R_SEAT - R.R_IN:.2f}", h=2.2)
    d.text((0, 16), "SECTION (4:1)", 3.0)
    s.notes = [
        f"Front ring at x {R.SEAT_X[0]:.0f} to {R.X_BLOCKS[0]:.1f}, rear ring at x {R.X_BLOCKS[-1] + R.L:.1f} to {R.SEAT_X[1]:.0f} (both {R.RING_W:.1f} wide). They close the magnet pack and hold the comb bar ends.",
        f"Pockets: {wo:.2f} wide (seat side), {h:.0f} deep radially, 4 deep axially, on the gap centre lines (4.5° + n × 9°), front ring rotated −0.40°, rear ring +0.40° (row skew).",
        "May be made in 4 bonded arcs if no G11 tube of this size is available; joints on pocket centre lines.",
        "Bonded to the seat with the magnet epoxy, then covered by the moulded glass sleeve.",
    ]
    return s


# ====================================================================== magnet pack
@reg
def magnet_pack():
    s = sheet("NP1-223C", "ROTOR MAGNET PACK: POLE SECTION, LAYOUT AND SLEEVE", "assembly", "8.2 kg magnets",
              "3:1 / 1:1", rev="C")
    v = s.view("pole", 3.0, (125, -721))
    a = math.radians(6.5)
    v.arc((0, 0), R.R_SEAT, 90 - 5.5, 90 + 5.5)
    v.arc((0, 0), 301.0, 90 - 5.5, 90 + 5.5)
    v.arc((0, 0), 323.0, 90 - 5.5, 90 + 5.5, "THIN")
    v.poly(R.block_outline(0.0), hatch=True)
    from figures_s30 import s30_comb_pts  # noqa: E402 (same comb geometry)
    for sgn in (-1, 1):
        v.poly(s30_comb_pts(sgn * R.TAU / 2))
    v.dim((-R.W / 2, R.R_IN), (R.W / 2, R.R_IN), -8, kind="h", text="30.00 block", h=2.2)
    v.dim((18, R.R_IN), (18, R.R_BACK), -8, kind="v", text="12.00", h=2.2)
    v.leader((0, R.R_BACK + 0.25), (12, 327), f"bond {R.BOND_MID:.2f} at the centre, 0.15 at the corners (glass beads)", 2.0)
    v.leader((5, 301.25), (36, 296.5), "sleeve bore Ø602.0, 0.52 to 0.89 thick", 2.0)
    v.text((-30, 330), "POLE SECTION (3:1), centre line = pole N1", 3.0)
    w = s.view("lay", 1.0, (260, 160))
    step = math.radians(R.SKEW_STEP) * R.R_SEAT
    pitch = math.radians(R.TAU) * R.R_SEAT
    for i, x in enumerate(R.X_BLOCKS):
        off = R.ROW_SHIFT[i] / R.SKEW_STEP * step
        for p in range(3):
            yc = (p - 1) * pitch + off
            w.poly([(x - R.X_BLOCKS[0], yc - R.W / 2), (x - R.X_BLOCKS[0] + R.L, yc - R.W / 2),
                    (x - R.X_BLOCKS[0] + R.L, yc + R.W / 2), (x - R.X_BLOCKS[0], yc + R.W / 2)],
                   hatch=(p == 1))
    w.dim((0, -pitch - 20), (R.ROWS_LEN, -pitch - 20), -4, kind="h", text=f"{R.ROWS_LEN:.1f} = 5 × 15 + 4 × 0.20", h=2.0)
    w.dim((R.ROWS_LEN + 4, -pitch / 2 * 0), (R.ROWS_LEN + 4, pitch), -6, kind="v", text=f"{pitch:.2f} pole pitch at the seat", h=2.0)
    w.text((0, pitch + 22), "LAYOUT, 3 POLES UNROLLED (1:1), front row left", 3.0)
    w.text((0, pitch + 17), "rows offset −0.4, −0.2, 0, +0.2, +0.4° (front → rear)", 2.4)
    s.notes = [
        "Bond: two-component toughened epoxy, RT cure, 80 °C post-cure, with 0.15 glass beads (doc 18 §4.2). Blocks placed with jig NP1-T02 against the comb bar faces; all N poles first, then S.",
        "Sequence per pole: comb bars and end rings bonded and cured first; blocks row by row from the front; check each row against the template (skew 0.20 ±0.02° per row).",
        "Pole map NP1-T10 after cure: every pole centre within ±0.05° of nominal, flux per pole within ±1.5 %.",
        "Sleeve: E-glass/epoxy moulded on the Al mandrel NP1-T06 located on both cup seats; bore Ø602.0 ±0.03, thickness 0.52 at the block centres, 0.89 at the edges; covers the end rings.",
        "Q1 check (doc 18 §10): sleeve thickness by section 0.45 to 0.95; air gap feeler check 2.0 ±0.1 all round after joining.",
    ]
    return s


# ====================================================================== rear cover with fan
@reg
def rear_cover():
    s = sheet("NP1-212C", "DRUM REAR COVER WITH SEAL CARRIER AND FAN BLADES", "EN AW-5083-H111 plate, ring and blades",
              "≈ 9.0 kg", "1:3.6", rev="C")
    v = s.view("A", 0.28, (140, 175))
    v.circle((0, 0), 345)
    v.circle((0, 0), 236, "HIDDEN")
    v.circle((0, 0), 216)
    v.bolt_circle((0, 0), 644, 24, 11.0, start=5)
    for k in range(FAN["n"]):
        a = math.radians(360 / FAN["n"] * k)
        c, s_ = math.cos(a), math.sin(a)
        t = FAN["t"] / 2
        v.poly([(FAN["r0"] * c - t * s_, FAN["r0"] * s_ + t * c), (FAN["r1"] * c - t * s_, FAN["r1"] * s_ + t * c),
                (FAN["r1"] * c + t * s_, FAN["r1"] * s_ - t * c), (FAN["r0"] * c + t * s_, FAN["r0"] * s_ - t * c)],
               layer="HIDDEN")
    v.leader((290, 0), (360, -120), f"{FAN['n']} radial fan blades {FAN['t']:.0f} × {FAN['h']:.0f} high, r {FAN['r0']:.0f} to {FAN['r1']:.0f}, inside face", 2.2)
    v.dim((-345, 0), (345, 0), 100, kind="h", prefix="Ø", text="690")
    v.dim((-216, 0), (216, 0), -10, kind="h", prefix="Ø", text="432 H8 (seal Ø400×432×15)")
    v.centerline((-360, 0), (360, 0))
    v.centerline((0, -360), (0, 360))
    v.text((-340, 380), "VIEW FROM FRONT (inside), plate 10, seal ring 15 × 20 at x 450 to 465", 3.0)
    s.notes = [
        "Rev C (doc 23 §6): 24 radial blades welded (TIG) or bolted to the inside face; they stir the internal air over the end windings and carry heat to the cover (h_int ≈ 40 W/m²K instead of 15, to be measured on the bench, doc 15 T5).",
        "Blades span x 447 to 465: 8 mm clear of the potted end turns (x ≤ 439) and of the carrier rear stop (x 440); tips r 308 run 4 mm inside the shell bore Ø624.",
        "Rear seal: radial lip seal Ø400×432×15 HNBR −40 °C on the spindle flange OD; breather port M24×1.5 with desiccant breather.",
        "Balance with the rotor (NP1-210C note 6). Inspection port Ø60 with cover at 180° (not shown).",
    ]
    return s


@reg
def clamp_ring():
    s = D0.clamp_ring()
    s.date, s.project = DATE, PROJ
    return s
