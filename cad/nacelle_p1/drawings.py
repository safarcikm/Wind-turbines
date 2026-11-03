"""Drawing sheets for nacelle prototype P1. Each function returns a draft.Sheet."""
from __future__ import annotations

import math

import geometry as G
from draft import Sheet

M = {it.name.split(" NP1")[0] if "NP1" in it.name else it.name: it.mass for it in G.mass_table()}


def kg(name):
    for it in G.mass_table():
        if name in it.name:
            return f"{it.mass:.1f} kg"
    return ""


def title(v, x, y, text, h=3.5):
    v.text((x, y), text, h, "left", "bottom")


def mirror(poly):
    return [(x, -r) for x, r in poly]


# ======================================================================
def ga_drivetrain():
    s = Sheet("NP1-000", "GENERAL ARRANGEMENT · DRIVETRAIN SECTION", "see parts list",
              "≈ 336 kg (drivetrain, no hub)", "1:4")
    v = s.view("GA", 0.25, (180, 172))
    # spindle
    v.poly(G.spindle_section(), hatch=True)
    v.poly(mirror(G.spindle_section()), hatch=True)
    # drum and covers
    for p in list(G.DRUM_PARTS.values()) + [G.SEAL_COVER_FRONT, G.SEAL_COVER_REAR, G.REAR_COVER,
                                             G.REAR_SEAL_CARRIER, G.DISC_POLY]:
        v.poly(p, hatch=True)
        v.poly(mirror(p), hatch=True)
    # bearings (simplified): cone + cup outlines with a roller line
    for xc in (G.X_BRG_FRONT, G.X_BRG_REAR):
        for sg in (1, -1):
            box = [(xc - 22.5, 70 * sg), (xc + 22.5, 70 * sg), (xc + 22.5, 105 * sg), (xc - 22.5, 105 * sg)]
            v.poly(box, layer="OUTLINE")
            tilt = 1 if xc == G.X_BRG_FRONT else -1
            v.line((xc - 12 * tilt, 79 * sg), (xc + 12 * tilt, 96 * sg), "OUTLINE")
            v.line((xc - 15, 87.5 * sg), (xc + 15, 87.5 * sg), "THIN")
    # spacer, locknut
    for sg in (1, -1):
        v.poly([(x, r * sg) for x, r in G.SPACER_POLY], hatch=True)
        v.poly([(x, r * sg) for x, r in G.SEAL_SLEEVE_POLY], hatch=True)
        v.poly([(52, 67.5 * sg), (80, 67.5 * sg), (80, 87 * sg), (52, 87 * sg)], layer="OUTLINE")
    # stator: carrier, stack, ring, end windings
    for sg in (1, -1):
        v.poly([(x, r * sg) for x, r in G.CARRIER], hatch=True)
        v.poly([(x, r * sg) for x, r in G.STATOR_RING], hatch=True)
        v.poly([(x, r * sg) for x, r in G.STACK_POLY], layer="OUTLINE")
        for x0, x1 in ((G.X_STACK[0] - G.END_WINDING, G.X_STACK[0]), (G.X_STACK[1], G.X_STACK[1] + G.END_WINDING)):
            v.poly([(x0, 232 * sg), (x1, 232 * sg), (x1, 292 * sg), (x0, 292 * sg)], layer="HIDDEN")
        v.poly([(335, G.GEN["r_m1"] * sg), (425, G.GEN["r_m1"] * sg),
                (425, G.GEN["r_m2"] * sg), (335, G.GEN["r_m2"] * sg)], fill="0.35")
    # cooling insert, hub interface, bedplate front plate (phantom)
    for sg in (1, -1):
        v.poly([(46, 20 * sg), (466, 20 * sg), (466, 45 * sg), (46, 45 * sg)], layer="HIDDEN")
        v.poly([(470, 100 * sg), (480, 100 * sg), (480, 205 * sg), (480, 205 * sg), (480, 270 * sg),
                (520, 270 * sg), (520, 100 * sg)], layer="PHANTOM")
        v.poly([(470, 100 * sg), (470, 205 * sg), (480, 205 * sg)], closed=False, layer="PHANTOM")
        v.poly([(-10, 200 * sg), (200, 200 * sg), (200, 235 * sg)], closed=False, layer="PHANTOM")
    v.centerline((-20, 0), (560, 0))
    v.line((0, -420), (0, 420), "CENTER")
    v.text((3, 410), "ROTOR PLANE x = 0", 2.2)
    # balloons / leaders
    tags = [((380, 305), "NP1-220 magnets N40UH, air gap 2.0"),
            ((443, 420), "NP1-230 brake disc Ø880 (2 calipers), lock holes PCD 740"),
            ((198, 175), "hub interface 12×M16 10.9 PCD 400, spigot Ø360"),
            ((470, 230), "NP1-212 rear cover, Ø400 lip seal on flange OD"),
            ((380, 260), "NP1-201 stator core 74 mm, 45 slots"),
            ((428, 150), "NP1-200 stator carrier (steel)"),
            ((150, 116), "NP1-210 drum weldment (rotating)"),
            ((120, 100), "32028 X front bearing, O arrangement"),
            ((89, 85), "NP1-101 spacer Ø180 + KMT 27 locknut"),
            ((390, 90), "NP1-102 rear seal sleeve Ø195"),
            ((60, 52), "NP1-100 spindle 42CrMo4+QT"),
            ((300, -32), "NP1-110 finned cooling insert (U-flow)"),
            ((360, -100), "32028 X rear bearing"),
            ((500, -150), "NP1-300 bedplate front plate (phantom), Ø410 pad")]
    for i, (p, t) in enumerate(tags):
        v.leader(p, (-90, 390 - i * 62), t, 2.1)
    # key dimensions
    v.dim((G.X_BRG_FRONT, -105), (G.X_BRG_REAR, -105), -6, kind="h", suffix=" bearing spread", h=2.0)
    v.dim((0, 345), (G.X_HUB_FLANGE, 345), 14, kind="h", suffix=" hub face", h=2.0)
    v.dim((G.X_STACK[0], -345), (G.X_STACK[1], -345), -4, kind="h", suffix=" stack", h=2.0)
    v.dim((40, -400), (476, -400), -6, kind="h", suffix=" spindle", h=2.0)
    title(v, -20, 440, "SECTION ON SPINDLE AXIS (both halves sectioned)", 3.0)
    s.notes = [
        "x is measured rearward from the rotor plane along the spindle axis; the spindle axis is tilted 5° nose up (bedplate NP1-300).",
        "Stationary: spindle, cones, stator carrier, stator, cooling insert, bedplate. Rotating: drum, cups, seal covers, rear cover, magnets, brake disc, hub.",
        "Bearings: back-to-back (O) tapered roller pair, preload 2 to 4 kN (end play −0.02 to −0.05) set by the KMT 27 locknut, checked by rolling torque before the front seal cover is fitted (doc 14, 5.3; it now goes on after the nut).",
        "Rev B (doc 17): disc Ø880/Ø652 slides on from the front, lock holes in the disc only, seal sleeve NP1-102 behind the rear cone, spacer Ø180, bedplate face on a Ø410 pad (rear cover runs 5 mm from the plate).",
        "Air gap 2.0 mm nominal; eccentricity ≤ 0.20 mm after assembly, measured with 4 capacitive gap sensors (doc 15).",
        "Sealed generator volume: front by the hub, rear by the Ø400 lip seal + labyrinth, desiccant breather on the rear cover.",
        "Hub, pitch system, nacelle cover and slip ring are not part of P1 bench article (dummy hub NP1-600 instead).",
    ]
    s.table = [["Item", "Part", "Qty", "Material / type"],
               ["1", "NP1-100 spindle", "1", "42CrMo4+QT forged"],
               ["2", "NP1-101 spacer", "1", "42CrMo4, induction hard."],
               ["3", "32028 X bearing", "2", "bought"],
               ["4", "KMT 27 locknut", "1", "bought"],
               ["5", "NP1-110 cooling insert", "1", "6082-T6 extrusion"],
               ["6", "NP1-200 stator carrier", "1", "S355J2+N"],
               ["7", "NP1-201 stator core", "≈205 sheets", "M270-35A bonded"],
               ["8", "NP1-202 clamp ring", "1", "1.4404"],
               ["9", "NP1-210 drum weldment", "1", "S355J2+N"],
               ["10", "NP1-211 seal covers", "2", "S355J2"],
               ["11", "NP1-212 rear cover", "1", "5083-H111"],
               ["12", "NP1-220 magnets", "160", "N40UH bought"],
               ["13", "NP1-230 brake disc", "1", "C45E+N"]]
    s.table_pos = (318, 283)
    s.table_widths = [8, 34, 15, 34]
    s.notes_top = (318, 216)
    s.notes_wrap = 58
    return s


# ======================================================================
def spindle():
    s = Sheet("NP1-100", "SPINDLE (STATIONARY MAIN SHAFT)", "42CrMo4+QT (EN 10083-3), forged",
              kg("Spindle"), "1:2.86 (A) / 1:4.5 (B)")
    v = s.view("A", 0.35, (22, 192))
    sec = G.spindle_section()
    v.turned_half_section(sec, G.SPINDLE_OUTER)
    v.line((40, -45), (476, -45), "HIDDEN")
    v.centerline((40, 0), (476, 0))
    xs = [40, 52, 80, 142.5, 337.5, 382.5, 400, 430, 440, 470, 476]
    feat = [60, 67.5, 70, 70, 70, 77.5, 75, 75, 200, 200, 100]
    v.ordinate(xs, feat, 214, h=2.0)
    v.ordinate([120, 360], [70, 70], 120, h=2.0, origin=40,
               labels=["80 brg ⊕", "320 brg ⊕"])
    for x, r, t in [(46, 60, "Ø120 h9"), (66, 67.5, "M135×2-6g"), (111, 70, "Ø140 f6"),
                    (240, 69, "Ø138"), (360, 70, "Ø140 j6"), (415, 75, "Ø150"), (455, 200, "Ø400 h8")]:
        v.dim((x, -r), (x, r), 0, kind="v", prefix="", text=t, h=2.0, tpos=0.18)
    v.leader((391, -77.5), (330, -150), "Ø155 k6 × 17.5 (cone abutment + seal sleeve NP1-102)", 2.0)
    v.leader((473, -100), (520, -150), "Ø200 f7 spigot", 2.0)
    v.leader((200, 45), (230, 110), "Ø90 H8 thru, Ra 1.6", 2.0)
    v.leader((433, 80), (520, 150), "R10 rolled, Ra 0.8", 2.0)
    v.leader((382.5, 72), (330, 150), "R2.5 max", 2.0)
    title(v, 40, 285 - 0 * 1, "", 1)
    v.text((40, -205), "VIEW A · HALF SECTION (upper half sectioned)", 3.0)
    w = s.view("B", 0.22, (285, 205))
    w.circle((0, 0), 200)
    w.circle((0, 0), 100, "HIDDEN")
    w.circle((0, 0), 45)
    w.circle((0, 0), 75, "HIDDEN")
    sp = G.SPINDLE
    w.bolt_circle((0, 0), sp["bedplate_bolts"]["pcd"], 12, 20.0, start=0)
    w.bolt_circle((0, 0), sp["carrier_bolts"]["pcd"], 12, 12.0, start=0, layer="HIDDEN")
    for a in sp["cable_holes"]["angles"]:
        c = (145 * math.cos(math.radians(a)), 145 * math.sin(math.radians(a)))
        w.circle(c, 14)
        w.cross(c, 18)
    for a in sp["dowels"]["angles"]:
        c = (120 * math.cos(math.radians(a)), 120 * math.sin(math.radians(a)))
        w.circle(c, 5, "HIDDEN")
    w.leader((175, 0), (250, 190), "12× M20-6H ↧26 PCD 350 (rear face)", 2.0)
    w.leader((120 * math.cos(math.radians(30)), 120 * math.sin(math.radians(30))), (250, 110),
             "12× M12-6H ↧24 PCD 240 (front face)", 2.0)
    w.leader((145 * math.cos(math.radians(15)), 145 * math.sin(math.radians(15))), (250, 30),
             "2× Ø28 thru PCD 290 at 15°/195°", 2.0)
    w.leader((85, 85), (250, -50), "2× Ø10 H7 ↧16 PCD 240 at 45°/225°", 2.0)
    w.leader((0, -200), (250, -130), "Ø400 h8 flange", 2.0)
    w.centerline((-215, 0), (215, 0))
    w.centerline((0, -215), (0, 215))
    w.text((-210, 225), "VIEW B · FLANGE FROM REAR", 3.0)
    s.notes = [
        "Blank: open-die forging 42CrMo4, forging ratio ≥ 3, quenched and tempered to Rp0.2 ≥ 650 MPa, Rm 900 to 1100 MPa; KV ≥ 27 J at −40 °C (3 specimens, longitudinal, taken from the flange zone). Certificate EN 10204 3.1.",
        "Ultrasonic test of the blank to EN 10228-3 quality class 3; MT of the finished part (fillets, shoulders, thread) to EN ISO 9934, no linear indications.",
        "Bearing seats: Ø140 f6 front (cone must slide for preload), Ø140 j6 rear; Ra 0.8; cylindricity 0.006; run-out of both seats and of Ø400 and Ø200 to common axis A-B ≤ 0.01.",
        "Flange rear face and front face perpendicular to A-B within 0.02; flatness 0.02. Ø400 seal surface Ra 0.2 to 0.4, plunge ground (no lead), hard chrome 30 µm or wear sleeve.",
        "Thread M135×2-6g with undercut DIN 76-D; precision locknut KMT 27 (or equivalent with locking screws).",
        "Bore Ø90 H8 for the cooling insert NP1-110 (installed with liquid nitrogen shrink, interference 0.02 to 0.06).",
        "Two radial holes Ø6 from the bore to under each bearing cone seat at 90° (bottom dead centre at 0°) for PT100 bearing temperature sensors; deburr, edges R0.5.",
        "All fillets and the shoulders rolled or shot peened; no stamping on the part: mark serial number on the flange OD rear chamfer by etching.",
        "Protect: phosphate + oil in storage; seats and seal surfaces taped until assembly.",
    ]
    return s


# ======================================================================
def spacer():
    s = Sheet("NP1-101", "FRONT SPACER + REAR SEAL SLEEVE NP1-102", "42CrMo4+QT, surface induction hardened",
              kg("spacer"), "1:1")
    v = s.view("A", 1.0, (60, 160))
    sec = [(0, 70), (17.5, 70), (17.5, 90), (0, 90)]
    v.poly(sec, hatch=True)
    v.poly(mirror(sec), layer="OUTLINE")
    v.line((0, -70), (17.5, -70), "HIDDEN")
    v.centerline((-5, 0), (25, 0))
    v.dim((0, 90), (17.5, 90), 8, kind="h")
    v.dim((17.5, 70), (17.5, -70), -14, kind="v", prefix="Ø", text="140 H7")
    v.dim((0, 90), (0, -90), 14, kind="v", prefix="Ø", text="180 h9")
    title(v, -10, 105, "NP1-101 SECTION", 3.2)
    w = s.view("B", 1.0, (220, 160))
    sl = [(0, 77.5), (15.5, 77.5), (15.5, 97.5), (0, 97.5)]
    w.poly(sl, hatch=True)
    w.poly(mirror(sl), layer="OUTLINE")
    w.centerline((-5, 0), (25, 0))
    w.dim((0, 97.5), (15.5, 97.5), 8, kind="h")
    w.dim((15.5, 77.5), (15.5, -77.5), -14, kind="v", prefix="Ø", text="155 H7")
    w.dim((0, 97.5), (0, -97.5), 14, kind="v", prefix="Ø", text="195 h9")
    title(w, -10, 120, "NP1-102 REAR SEAL SLEEVE (Rev B)", 3.2)
    s.notes = ["Faces parallel within 0.005 (it sets the bearing preload path).",
               "NP1-102: same material and hardening as NP1-101; O-ring 155 × 3 in a bore groove (static seal); slides onto the Ø155 shoulder before the rear cone, front face against the cone back face.",
               "Rev B: OD 160 → 180 so the front seal cover clears the KMT 27 nut (doc 17).",
               "Ø180 surface induction hardened 55 to 60 HRC, depth 1 mm, ground Ra 0.2 to 0.4, no lead.",
               "Bore chamfer 1.5×30° on the cone side."]
    return s


# ======================================================================
def cooling_insert():
    s = Sheet("NP1-110", "SPINDLE COOLING INSERT (FINNED EXTRUSION)", "EN AW-6082-T6 extrusion",
              kg("Cooling insert"), "2:1 / 1:4")
    ins = G.INSERT
    v = s.view("profile", 2.0, (110, 185))
    v.circle((0, 0), ins["od"] / 2)
    v.circle((0, 0), ins["od"] / 2 - ins["shell"])
    v.circle((0, 0), ins["tube_od"] / 2)
    v.circle((0, 0), ins["tube_id"] / 2)
    for k in range(ins["fins"]):
        a = 2 * math.pi * k / ins["fins"]
        t = ins["fin_t"] / 2
        for sg in (1, -1):
            p0 = (20 * math.cos(a) - sg * t * math.sin(a), 20 * math.sin(a) + sg * t * math.cos(a))
            p1 = (41 * math.cos(a) - sg * t * math.sin(a), 41 * math.sin(a) + sg * t * math.cos(a))
            v.line(p0, p1)
    # partition fins (thicker) splitting forward/return halves
    v.text((-44, 48), "FORWARD FLOW (8 cells)", 2.2)
    v.text((-44, -52), "RETURN FLOW (8 cells)", 2.2)
    v.dim((-45, 0), (45, 0), 50, kind="h", prefix="Ø", text="90 +0.06/+0.02")
    v.dim((-20, 0), (20, 0), -50, kind="h", prefix="Ø", text="40")
    v.leader((0, 17), (55, 30), "cable conduit Ø34", 2.2)
    v.leader((30.5, 6), (60, 10), "16 fins × 2.5, 4 mm shell", 2.2)
    v.centerline((-50, 0), (50, 0))
    v.centerline((0, -50), (0, 50))
    title(v, -50, 58, "EXTRUSION PROFILE (2:1)", 3.2)
    w = s.view("side", 0.25, (240, 230))
    w.poly([(0, -45), (ins["length"], -45), (ins["length"], 45), (0, 45)])
    w.line((0, 20), (ins["length"], 20), "HIDDEN")
    w.line((0, -20), (ins["length"], -20), "HIDDEN")
    w.dim((0, 45), (ins["length"], 45), 6, kind="h")
    title(w, 0, 90, "INSERT LENGTH (1:4), x = 46 to 466 in spindle", 2.6)
    s.notes = [
        "The two fins at 0° and 180° are the flow partition: they are continuous and sealed to the front plenum cap so that air flows forward in the upper 8 cells and returns in the lower 8 (U-flow, both ports at the rear).",
        "Front plenum cap (6082, 10 mm, O-ring to bore) closes the cells 10 mm from the insert front end and lets the Ø34 conduit pass through to the slip ring position.",
        "Shrink into spindle bore with liquid nitrogen; interference 0.02 to 0.06 at 20 °C gives contact pressure in operation (Al expands more than steel). Thermal paste is not used (shrink fit).",
        "Profile tolerances EN 755-9; cut length ±0.5; deburr; no anodising on the OD (thermal contact).",
        "Rear manifold (fan, filter, inlet/outlet split) bolts to the spindle rear face, see NP1-300 and doc 14 section 6.",
    ]
    return s


# ======================================================================
def lamination():
    g = G.GEN
    s = Sheet("NP1-201", "STATOR LAMINATION (45 SLOTS) · LASER / STAMPING", "M270-35A, 0.35 mm, self-bonding varnish",
              f"{kg('Stator core')} per stack", "1:3.6 / 2:1")
    v = s.view("lam", 0.28, (115, 185))
    pts = G.lamination_outline(n_arc=8)
    v.poly(pts)
    v.circle((0, 0), g["r_si"])
    # 3 key notches 10 wide 4 deep at 90, 210, 330 deg
    for a in (90, 210, 330):
        ar = math.radians(a)
        ux, uy = math.cos(ar), math.sin(ar)
        nx, ny = -uy, ux
        r0 = g["r_si"]
        p = [(r0 * ux + 5 * nx, r0 * uy + 5 * ny), ((r0 + 4) * ux + 5 * nx, (r0 + 4) * uy + 5 * ny),
             ((r0 + 4) * ux - 5 * nx, (r0 + 4) * uy - 5 * ny), (r0 * ux - 5 * nx, r0 * uy - 5 * ny)]
        v.poly(p, closed=False)
    v.centerline((-310, 0), (310, 0))
    v.centerline((0, -310), (0, 310))
    v.dim((-g["r_s"], 0), (g["r_s"], 0), 90, kind="h", prefix="Ø", text="598.00 ±0.03 (tooth tips)")
    v.dim((-g["r_si"], -40), (g["r_si"], -40), -8, kind="h", prefix="Ø", text="437.20 +0.03/0")
    v.leader((0, g["r_si"] + 4), (-170, 280), "3× key notch 10 H9 × 4 at 90°/210°/330°", 2.0)
    title(v, 110, 330, "LAMINATION (1:3.6)", 3.0)
    # slot detail
    d = s.view("det", 2.0, (330, 200))
    tau = 2 * math.pi / g["slots"]
    rot = -math.pi / 2  # draw slot pointing up, local slot at angle 0 rotated
    local = []
    for p in pts:
        a = math.atan2(p[1], p[0])
        if -tau * 0.75 < a < tau * 0.75:
            local.append(p)
    local.sort(key=lambda p: math.atan2(p[1], p[0]))
    # keep sequence order instead: take points of first slot from outline
    first = pts[:4 + 7 + 4 + 0]
    pts1 = pts[:4 + 7 + 4]
    tr = [(-(y), x - 265) for x, y in pts1]  # rotate so slot points up, shift
    d.poly(tr, closed=False)
    d.dim((-g["b0"] / 2, 299 - 265), (g["b0"] / 2, 299 - 265), 6, kind="h", text="4.0")
    top = G.lamination_outline(8)
    d.dim((-9.4, 30), (9.4, 30), -8, kind="h", text="18.8 ref")
    d.dim((-4.9, -35), (4.9, -35), -6, kind="h", text="9.7 ref")
    d.dim((12, 230 - 265), (12, 295 - 265), -30, kind="v", text="65.0")
    d.dim((12, 295 - 265), (12, 299 - 265), -30, kind="v", text="4")
    d.text((-40, 38), "SLOT DETAIL (2:1)", 3.0)
    d.text((-40, 34.5), "tooth body 22.3 parallel-sided", 2.0)
    d.text((-40, 32), "slot area 932 mm² (FEA basis)", 2.0)
    s.notes = [
        "DXF of this sheet (layer OUTLINE) is the cutting contour. Production: stamping die or laser + edge-anneal; P1: laser cut, burr ≤ 0.02 mm, cut-edge heat zone ≤ 0.1 mm.",
        "Material M270-35A (EN 10106) with self-bonding varnish (Backlack, e.g. class C coating, both sides). Grain orientation irrelevant (non-oriented), but rotate each sheet 3 slot pitches (24°) when stacking to average thickness variation.",
        "Stack: ≈ 205 sheets for 74.0 mm at stacking factor ≥ 0.97; bond-cure in fixture on a Ø437.20 mandrel with 3 keys, 1.0 to 1.5 MPa axial pressure.",
        "Stack checks: length 74.0 ±0.2; Ø598.0 OD run-out ≤ 0.05 to the bore; slot alignment: Ø3.9 gauge pin passes every slot opening full length.",
        "Interlaminar resistance: Franklin test to IEC 60404-11, ≥ 10 Ω·cm² after bonding.",
        "Tooth tips are not machined after stacking (damages insulation). If OD run-out exceeds 0.05, reject the stack.",
    ]
    return s


# ======================================================================
def carrier():
    s = Sheet("NP1-200", "STATOR CARRIER", "S355J2+N plate or ring forging, stress relieved",
              kg("Stator carrier"), "1:2.86 / 1:3.6")
    v = s.view("A", 0.35, (50, 185))
    sec = G.CARRIER
    v.poly([(x - 340, r) for x, r in sec], hatch=True)
    v.poly([(x - 340, -r) for x, r in sec], hatch=False)
    v.centerline((0, 0), (110, 0))
    X = lambda x: x - 340  # noqa: E731
    v.dim((X(343.5), 218.6), (X(417), 218.6), 14, kind="h", text="73.5", h=2.0)
    v.dim((X(343.5), 228), (X(440), 228), 24, kind="h", h=2.0)
    v.dim((X(415), 90), (X(440), 90), -8, kind="h")
    v.dim((X(440), 90), (X(440), -90), -16, kind="v", prefix="Ø", text="180", h=2.0)
    v.dim((X(343.5), 218.6), (X(343.5), -218.6), 14, kind="v", prefix="Ø", text="437.25 +0.05/+0.03", h=2.0)
    v.dim((X(417), 228), (X(440), -228), -8, kind="v", prefix="Ø", text="456", h=2.0)
    v.dim((X(343.5), 200), (X(343.5), -200), 6, kind="v", prefix="Ø", text="400", h=2.0)
    title(v, 0, 262, "SECTION A-A", 3.0)
    w = s.view("B", 0.28, (250, 185))
    w.circle((0, 0), 228)
    w.circle((0, 0), 218.6)
    w.circle((0, 0), 200, "HIDDEN")
    w.circle((0, 0), 90)
    w.bolt_circle((0, 0), 240, 12, 13.0)
    w.bolt_circle((0, 0), 418, 12, 6.8, start=15, layer="HIDDEN")
    for a in (15, 195):
        c = (145 * math.cos(math.radians(a)), 145 * math.sin(math.radians(a)))
        w.circle(c, 15)
    for a in (90, 210, 330):
        ar = math.radians(a)
        w.circle((218.6 * math.cos(ar), 218.6 * math.sin(ar)), 5, "THIN")
    w.centerline((-240, 0), (240, 0))
    w.centerline((0, -240), (0, 240))
    w.leader((120, 0), (270, 40), "12× Ø13 thru PCD 240", 2.0)
    w.leader((209 * math.cos(math.radians(15)), 209 * math.sin(math.radians(15))), (270, 120),
             "12× M8 ↧16 PCD 418 (clamp ring)", 2.0)
    w.leader((140, 37), (270, -40), "2× Ø30 PCD 290, 15°/195°", 2.0)
    w.leader((-109, 189), (270, 200), "3× key 10×8 DIN 6885, 90°/210°/330°", 2.0)
    w.leader((85, -85), (270, -120), "2× Ø10 H7 PCD 240, 45°/225°", 2.0)
    w.text((-230, 250), "VIEW B (from front)", 3.0)
    s.notes = [
        "Steel, not aluminium, is used for P1: steel matches the lamination expansion, so the stack stays tight and centred from −40 °C to +130 °C. An aluminium carrier loses ≈ 0.6 mm of fit on Ø437 at −40 °C (doc 14, 4.2).",
        "Stack seat Ø437.25 +0.05/+0.03 against lamination Ø437.20 +0.03/0: interference 0 to 0.05; assemble by cooling the carrier (dry ice / LN2) and sliding the bonded stack on against the rear stop.",
        "Run-out of the stack seat and of the rear stop face to the bolting face and Ø180 spigot ≤ 0.02. Bolting face flatness 0.02.",
        "Rim front face sits 0.5 below the stack face so the clamp ring NP1-202 clamps the stack (12× M8 A4-80, 20 Nm).",
        "Bolt to the spindle flange with 12× M12 10.9 + hardened washers, 110 Nm (μ 0.12), with 2 fitted dowels; thermal interface: Al-filled paste, 0.05 mm, on the full bolting face.",
        "Machine after stress relief (580 to 620 °C, 2 h). Paint: none on the stack seat and bolting face; elsewhere epoxy primer 60 µm.",
    ]
    return s


# ======================================================================
def clamp_ring():
    s = Sheet("NP1-202", "STATOR FRONT CLAMP RING", "1.4404 (non-magnetic)", kg("clamp ring"), "1:3.3")
    v = s.view("A", 0.3, (150, 175))
    v.circle((0, 0), 229)
    v.circle((0, 0), 203)
    v.bolt_circle((0, 0), 418, 12, 9.0, start=15)
    v.centerline((-240, 0), (240, 0))
    v.centerline((0, -240), (0, 240))
    v.dim((-229, 0), (229, 0), 75, kind="h", prefix="Ø", text="458")
    v.dim((-203, 0), (203, 0), -75, kind="h", prefix="Ø", text="406 H9")
    v.leader((209 * math.cos(math.radians(15)), 209 * math.sin(math.radians(15))), (250, 200),
             "12× Ø9 thru, c'sunk for M8 A4-80, PCD 418", 2.2)
    title(v, -230, 270, "VIEW (thickness 8.0, faces parallel 0.05)", 3.2)
    s.notes = ["Laser cut from 8 mm plate, faces machined flat 0.05.",
               "Must not touch the coils: inner end-winding radius ≥ 232; ring OD 229."]
    return s


# ======================================================================
def drum():
    s = Sheet("NP1-210", "ROTOR DRUM WELDMENT (GENERATOR YOKE + BEARING HOUSING)", "S355J2+N, welded, stress relieved",
              kg("Rotor drum"), "1:3.8")
    v = s.view("A", 0.265, (40, 168))
    X = lambda x: x - 90  # noqa: E731
    for name, p in G.DRUM_PARTS.items():
        q = [(X(x), r) for x, r in p]
        v.poly(q, hatch=True)
        v.poly([(x, -r) for x, r in q])
    v.centerline((0, 0), (X(470), 0))
    v.dim((X(92), 120), (X(385), 120), 8, kind="h", h=2.0)
    v.dim((X(195), 345), (X(465), 345), 6, kind="h", h=2.0)
    v.dim((X(335), -323), (X(425), -323), -6, kind="h", h=2.0, suffix=" magnet seat")
    for x, r, t in [(120, 105, "Ø210 P7"), (240, 98, "Ø196"), (360, 105, "Ø210 P7")]:
        v.dim((X(x), -r), (X(x), r), 0, kind="v", text=t, h=2.0, tpos=0.25)
    v.dim((X(390), -G.GEN["r_m2"]), (X(390), G.GEN["r_m2"]), 0, kind="v", text="Ø618.40 H7", h=2.0, tpos=0.3)
    v.dim((X(440), -312), (X(440), 312), 0, kind="v", text="Ø624", h=2.0, tpos=0.7)
    s.table = [["Feature", "Size", "Tolerance / note"],
               ["cup seats (2)", "Ø210 × 45", "P7, Ra 0.8, coax. 0.02"],
               ["cup shoulders", "Ø196", "square 0.01 to axis"],
               ["housing OD", "Ø240 / Ø224", "seal cover faces at x 92, 385"],
               ["hub spigot", "Ø360 × 5", "f7; face flat 0.03"],
               ["hub web", "20 thick, Ø464", "12× M16 thru PCD 400"],
               ["outer web", "8 thick", "full pen. weld to shell"],
               ["magnet seat", "Ø618.40 × 90", "H7, coax. 0.02 to cups"],
               ["shell OD", "Ø646 / Ø636", "magnet zone 13.8 wall"],
               ["shell ID (free)", "Ø624", "clearance to magnets"],
               ["rear flange ring", "Ø624/Ø710 × 14", "M10 PCD 644 + M10 PCD 678"],
               ["lock holes", "none (Rev B)", "in the disc only, PCD 740"]]
    s.table_pos = (195, 283)
    s.table_widths = [32, 34, 56]
    title(v, 420, 330, "SECTION A-A (weld preps not shown, note 2)", 3.0)
    s.notes = [
        "Parts: housing tube (seamless S355J2H or ring forging), hub web 20 mm, outer web 8 mm, shell (rolled 16 mm plate, one longitudinal full-penetration weld, or ring rolled), rear flange ring 14 mm.",
        "Welds: full penetration where the web meets the housing and the shell; ISO 5817 class B; 100 % MT, UT on the shell seam. Stress relieve 580 to 620 °C before machining.",
        "Machine in one set-up after stress relief: cup seats Ø210 P7, magnet seat Ø618.40 H7, hub spigot Ø360 f7, rear flange face. Coaxiality of both cup seats and magnet seat ≤ 0.02; cup shoulder faces square to axis ≤ 0.01.",
        "Hub web: 12× M16-6H through, PCD 400 (doc 13 joint, 10.9 preloaded). Rear flange ring Ø710 (Rev B): 24× M10-6H thru PCD 644 from 5° (rear cover) and 24× M10-6H thru PCD 678 from 7.5° (brake disc); no lock holes.",
        "Front and rear housing end faces: 6× M8 ↧16 on PCD 225 for the seal covers NP1-211; 2 grease nipples M10×1 into each bearing space with purge holes opposite.",
        "Balance the finished rotor (drum, magnets, disc) to ISO 21940-11 G2.5 at 250 rpm, correction on the rear flange ring.",
        "Magnet seat: degrease, grit blast Sa 2½ just before bonding; no paint inside. Outside: zinc spray + epoxy (C5) after machining.",
    ]
    return s


# ======================================================================
def seal_covers():
    s = Sheet("NP1-211", "MAIN BEARING SEAL COVERS (FRONT / REAR)", "S355J2", kg("Seal covers"), "1:1")
    for i, (poly, nm, seal) in enumerate(((G.SEAL_COVER_FRONT, "FRONT", "lip seal 180×200×10 HNBR + V-ring"),
                                          (G.SEAL_COVER_REAR, "REAR", "lip seal 195×220×12 HNBR on NP1-102"))):
        v = s.view(nm, 0.75, (70 + i * 170, 165))
        x0 = poly[0][0]
        q = [(x - x0, r) for x, r in poly]
        v.poly(q, hatch=True)
        v.poly([(x, -r) for x, r in q])
        v.centerline((-10, 0), (20, 0))
        v.dim((0, q[2][1]), (q[1][0], q[2][1]), 8, kind="h", text=f"{q[1][0]:.0f}")
        v.dim((q[1][0], q[0][1]), (q[1][0], -q[0][1]), -20, kind="v", prefix="Ø", text=f"{2 * q[0][1]:.0f}")
        v.dim((0, q[2][1]), (0, -q[2][1]), 15, kind="v", prefix="Ø", text=f"{2 * q[2][1]:.0f}")
        v.text((-20, 158), f"{nm} COVER: {seal}", 2.6)
        v.text((-20, 150), "6× Ø9 PCD 225; seal bore H8, Ra 1.6", 2.4)
    s.notes = ["Rev B (doc 17): both bores are larger than every part they pass. Front cover goes on after the KMT 27 nut and the rolling-torque check; rear cover is bolted to the drum before the drum goes over the fitted rear cone (Ø191 envelope) onto the sleeve NP1-102.",
               "Seal lips face the bearing (grease retention); V-ring outside on the front cover runs against the spacer face.",
               "Purge: grease exits under the lip; collect with absorbent ring at service.",
               "Pilot on the housing bore Ø210, 2 mm deep (not shown), for concentric seals."]
    return s


# ======================================================================
def rear_cover():
    s = Sheet("NP1-212", "DRUM REAR COVER WITH SEAL CARRIER", "EN AW-5083-H111 plate + ring",
              kg("rear cover"), "1:3.6")
    v = s.view("A", 0.28, (140, 175))
    v.circle((0, 0), 345)
    v.circle((0, 0), 236, "HIDDEN")
    v.circle((0, 0), 216)
    v.bolt_circle((0, 0), 644, 24, 11.0, start=5)
    v.circle((0, 280), 12)
    v.leader((0, 280), (150, 330), "breather port M24×1.5 (desiccant breather)", 2.2)
    v.leader((322 * math.cos(math.radians(5)), 322 * math.sin(math.radians(5))), (360, 100),
             "24× Ø11 thru PCD 644", 2.2)
    v.dim((-345, 0), (345, 0), 100, kind="h", prefix="Ø", text="690")
    v.dim((-216, 0), (216, 0), -10, kind="h", prefix="Ø", text="432 H8 (seal Ø400×432×15)")
    v.centerline((-360, 0), (360, 0))
    v.centerline((0, -360), (0, 360))
    title(v, -340, 380, "VIEW FROM REAR · plate 10, seal ring 15 × 20 welded (x 450 to 465)", 3.0)
    s.notes = ["Rear seal: radial lip seal Ø400×432×15 HNBR −40 °C (or split seal), plus labyrinth groove; runs on the spindle flange OD (3.7 m/s at 178 rpm).",
               "Ring to plate: TIG fillet both sides, then machine seal bore concentric to the bolt-circle pilot within 0.05.",
               "Inspection port Ø60 with cover at 180° (not shown) for air-gap feeler and sensor cables during P1 tests."]
    return s


# ======================================================================
def magnet():
    m = G.MAGNET
    s = Sheet("NP1-220", "MAGNET SEGMENT (PURCHASE DRAWING)", "NdFeB N40UH, NiCuNi + epoxy coating",
              f"{G.RHO['ndfeb'] * math.radians(m['arc_deg']) / 2 * (m['r_out'] ** 2 - m['r_in'] ** 2) * m['length'] * 1000:.0f} g each",
              "4:1 / 2:1")
    v = s.view("A", 4.0, (170, 190))
    a = math.radians(m["arc_deg"]) / 2
    yc = m["r_in"]
    pts = []
    for i in range(13):
        t = -a + 2 * a * i / 12
        pts.append((m["r_out"] * math.sin(t), m["r_out"] * math.cos(t) - yc))
    for i in range(13):
        t = a - 2 * a * i / 12
        pts.append((m["r_in"] * math.sin(t), m["r_in"] * math.cos(t) - yc))
    v.poly(pts, hatch=True)
    v.line((0, -6), (0, 14), "CENTER")
    xl, yl = m["r_in"] * math.sin(a), m["r_in"] * math.cos(a) - yc
    v.dim((-xl, yl), (xl, yl), -8, kind="h", text=f"{2 * m['r_in'] * math.sin(a):.2f} ref (chord at R{m['r_in']:.1f})", h=2.2)
    v.dim((-22, 0), (-22, m["r_out"] - yc), 6, kind="v", text="7.70 ±0.03", h=2.2)
    v.text((-24, 18), f"R{m['r_out']:.2f} −0.05/0 outer (bonded face), R{m['r_in']:.2f} inner, arc {m['arc_deg']:.2f}°", 2.4)
    v.text((-24, 15), "magnetised radially; pole marked on the outer face", 2.4)
    v.text((-24, 22), "SECTION (4:1)", 3.0)
    w = s.view("B", 2.0, (110, 105))
    L = m["length"]
    w.poly([(0, 0), (L, 0), (L, 7.7), (0, 7.7)])
    w.dim((0, 7.7), (L, 7.7), 5, kind="h", text=f"{L:.2f} ±0.05", h=2.2)
    w.text((0, 14), "SIDE (2:1)", 3.0)
    s.notes = [
        f"Grade N40UH (Br ≥ 1.25 T, HcJ ≥ 1990 kA/m at 20 °C); supplier to give the demagnetisation curve at 20, 80, 120 and 150 °C (doc 05: HcJ ≥ 896 kA/m at 120 °C required).",
        f"Length {m['length']:.2f} ±0.05 (4 pieces per pole, axial segmentation for eddy loss; 0.2 mm bond gaps). 160 pieces + 8 spares, half N-in, half S-in, marked on the outer face.",
        "Coating NiCuNi 10 to 20 µm + epoxy 15 to 25 µm; salt spray ≥ 240 h (ISO 9227) on witness samples; corners R0.3.",
        "Flux check: each piece within ±1.5 % of the batch mean (Helmholtz coil); reject outliers. Record the serial batch for traceability.",
        "Bonding into the drum: structural epoxy rated 150 °C, positioned by a GRP comb (pole pitch 9.000°, 40 poles), then 0.5 mm glass/epoxy wet layup over the inner face (vacuum bag) as retention and corrosion barrier.",
        "Handling: magnets must never approach a steel surface uncontrolled; magnet insertion jig with brass slider and screw feed (doc 14, 7.2).",
    ]
    return s


# ======================================================================
def brake_disc():
    s = Sheet("NP1-230", "BRAKE DISC AND ROTOR LOCK HOLES", "C45E+N (or S355J2+N), 16 mm",
              kg("Brake disc"), "1:4.8")
    v = s.view("A", 0.21, (130, 180))
    D, L = G.DISC, G.LOCK
    ro, ri = D["od"] / 2, D["id"] / 2
    v.circle((0, 0), ro)
    v.circle((0, 0), ri)
    v.circle((0, 0), D["pad_r"][1], "HIDDEN")
    v.circle((0, 0), D["pad_r"][0], "HIDDEN")
    db = G.DRUM["disc_bolts"]
    for i in range(db["n"]):
        a = math.radians(db["start"] + 360.0 * i / db["n"])
        v.circle((db["pcd"] / 2 * math.cos(a), db["pcd"] / 2 * math.sin(a)), 5.5)
    for i in range(L["n"]):
        a = math.radians(L["start"] + 360.0 * i / L["n"])
        v.circle((L["pcd"] / 2 * math.cos(a), L["pcd"] / 2 * math.sin(a)), L["hole"] / 2)
    v.circle((0, 0), db["pcd"] / 2, "CENTER")
    v.circle((0, 0), L["pcd"] / 2, "CENTER")
    v.centerline((-ro - 10, 0), (ro + 10, 0))
    v.centerline((0, -ro - 10), (0, ro + 10))
    v.dim((-ro, 0), (ro, 0), 88, kind="h", prefix="Ø", text=f"{D['od']:.0f}")
    v.dim((-ri, 0), (ri, 0), -10, kind="h", prefix="Ø", text=f"{D['id']:.0f} H9")
    a = math.radians(db["start"])
    v.leader((db["pcd"] / 2 * math.cos(a), db["pcd"] / 2 * math.sin(a)), (470, 120),
             f"24× Ø11 thru PCD {db['pcd']:.0f} from {db['start']}° (M10 10.9, 65 Nm)", 2.0)
    a = math.radians(L["start"] - 30)
    v.leader((L["pcd"] / 2 * math.cos(a), L["pcd"] / 2 * math.sin(a)), (470, 380),
             f"12× Ø{L['hole']:.0f} H8 lock holes PCD {L['pcd']:.0f}, first at top", 2.0)
    v.leader((-410 * 0.7, -410 * 0.7), (470, -300),
             f"pad track r {D['pad_r'][0]:.0f} to {D['pad_r'][1]:.0f} (eff. r {G.BRAKE['r_eff']:.3f} m)", 2.0)
    title(v, -440, 465, f"VIEW · Rev B · thickness 16 · slides on from the front over the Ø646 drum shell", 3.0)
    s.notes = ["Faces ground parallel 0.03, flatness 0.05, Ra 1.6. Axial run-out mounted on the drum ≤ 0.10.",
               f"Two spring-applied hydraulically released calipers (bought), at 90° and 270° (horizontal), each ≥ {G.BRAKE['clamp_kN']:.1f} kN clamp force on 16 mm disc; brake torque 8.7 kNm at μ 0.4.",
               "Rev B (doc 17): bore Ø640 → Ø652 (fits over the drum shell from the front), OD Ø800 → Ø880 (pad track outside the Ø710 flange ring, room for the caliper behind the disc), lock holes moved here from the ring.",
               "Corrosion: zinc-flake coating outside the pad track; pad track left bare (it is cleaned by the weekly brake test, doc 11)."]
    return s


# ======================================================================
def bedplate():
    s = Sheet("NP1-300", "BEDPLATE WELDMENT (P1 FABRICATED VERSION)", "S355J2+N plates, stress relieved, machined",
              "≈ 150 kg", "1:5")
    v = s.view("side", 0.2, (195, 82))
    t = math.radians(G.TILT_DEG)
    d = (math.cos(t), -math.sin(t))            # rearward along the axis
    up = (math.sin(t), math.cos(t))            # perpendicular, up
    rc = (-G.X_YAW, G.H_ROTOR + 40.0)          # rotor centre (world, Y up from bedplate bottom)
    P = lambda s_, u: (rc[0] + d[0] * s_ + up[0] * u, rc[1] + d[1] * s_ + up[1] * u)  # noqa: E731
    xf, xr = G.BED["x_front"], G.BED["x_front"] + G.BED["front_plate"]
    pf = P(xf, 0)
    tb = -(pf[1] - 40.0) / math.cos(t)
    front = [P(xf, tb), P(xf, 250), P(xr, 250), P(xr, tb - 40 * math.tan(t))]
    v.poly([P(470, -205), P(470, 205), P(xf, 205), P(xf, -205)], hatch=True)
    v.poly(front, hatch=True)
    v.poly([(-330, 0), (330, 0), (330, 40), (-330, 40)], hatch=True)
    side = [P(xr, 250), (330, 330), (330, 40), front[3]]
    v.poly(side)
    v.poly([(310, 40), (330, 40), (330, 330), (310, 330)], hatch=True)
    # spindle axis
    v.line(P(-50, 0), P(1000, 0), "CENTER")
    v.line((0, -40), (0, 700), "CENTER")
    v.text((5, 680), "YAW AXIS", 2.4)
    # drivetrain phantom
    for poly in [G.DISC_POLY, [(212, 323), (465, 323), (465, 355)]]:
        v.poly([P(x, r) for x, r in poly], closed=False, layer="PHANTOM")
        v.poly([P(x, -r) for x, r in poly], closed=False, layer="PHANTOM")
    v.poly([P(40, 60), P(476, 60), P(476, -60), P(40, -60)], layer="PHANTOM")
    v.circle(rc, 8, "CENTER")
    v.text((rc[0] - 60, rc[1] + 20), "ROTOR CENTRE", 2.4)
    # yaw bearing phantom
    v.poly([(-175, 0), (175, 0), (175, -70), (-175, -70)], layer="PHANTOM")
    v.poly([(-304, -70), (304, -70), (304, -10), (-304, -10)], layer="PHANTOM")
    v.dim((rc[0], rc[1]), (0, rc[1]), 12, kind="h", text="750 overhang")
    v.dim((0, 0), (0, rc[1]), -12, kind="v", text=f"{G.H_ROTOR + 40:.0f}")
    v.dim((-330, 0), (330, 0), -20, kind="h")
    v.text(P(250, 270), "5° TILT", 2.4)
    title(v, -800, 900, "SIDE VIEW (Z = 0 section), phantom: drivetrain and yaw bearing", 3.0)
    w = s.view("front", 0.2, (350, 185))
    w.poly([(-250, -260), (250, -260), (250, 250), (-250, 250)])
    w.circle((0, 0), 100)
    w.bolt_circle((0, 0), 350, 12, 22.0)
    for a in (15, 195):
        w.circle((145 * math.cos(math.radians(a)), 145 * math.sin(math.radians(a))), 16)
    w.centerline((-270, 0), (270, 0))
    w.centerline((0, -280), (0, 270))
    w.dim((-250, 250), (250, 250), 6, kind="h")
    w.text((-250, 290), "FRONT PLATE (40), view along spindle axis", 2.6)
    s.notes = [
        "P1 bedplate is a stress-relieved S355J2+N weldment instead of the EN-GJS-400-18U-LT casting (doc 07): no pattern lead time, same interfaces. The cast version follows after P1 strain-gauge data.",
        "Front plate 40, perpendicular to the spindle axis, front face x 480 with a machined Ø410 × 10 pad (face x 470 = spindle flange face; Rev B, the rotating rear cover runs 5 mm from the plate outside the pad): Ø200 H7 spigot bore, 12× Ø22 PCD 350 (M20 10.9 from inside, 540 Nm at μ 0.12), 2× Ø32 cable holes PCD 290. Face flatness 0.03, square to the yaw flange within 0.05/400 at 5.00° ±0.05° tilt.",
        "Bottom plate 40 (yaw flange): Ø220 bore, 16× Ø18 PCD 300 for the yaw bearing inner ring (M16 10.9). Flatness 0.05 (slewing ring requirement, confirm with supplier).",
        "Side plates 20 (Z = ±240), rear plate 20, internal gusset under the front plate; top is open for access in P1 (bolted lid).",
        "Brake caliper brackets NP1-310 bolt to side plates at the spindle axis height; yaw drive and yaw brake brackets bolt to the bottom plate (positions after yaw supplier drawing).",
        "Welds ISO 5817 B, 100 % MT; stress relieve; machine front plate and bottom plate in one set-up on a 5° fixture.",
    ]
    return s


# ======================================================================
def lock_pin():
    s = Sheet("NP1-320", "ROTOR LOCK PIN AND HOLDER", "pin 42CrMo4+QT; holder S355J2", "≈ 4 kg", "1:1")
    v = s.view("A", 1.0, (60, 170))
    pin = [(0, 0), (0, 10), (150, 10), (150, 15), (170, 15), (170, 0)]
    v.poly(pin + [(0, 0)], hatch=True)
    v.poly([(x, -r) for x, r in pin])
    v.centerline((-5, 0), (135, 0))
    v.dim((0, 10), (21, 10), 10, kind="h", text="21 (engagement: disc 16 + 5)")
    v.dim((0, 10), (0, -10), 12, kind="v", prefix="Ø", text="20 f7")
    v.dim((0, 15), (170, 15), 22, kind="h")
    v.leader((160, 15), (190, 40), "knob Ø30, M10 for the handle", 2.2)
    title(v, 0, 60, "LOCK PIN", 3.0)
    s.notes = ["Rev B (doc 17): pin Ø20 at the top (12 o'clock) on PCD 740, entering the disc from behind; holder NP1-321 sits on the top edge of the bedplate front plate and also carries the two overspeed sensors. Shear at 8.7 kNm: 23.5 kN, τ = 75 MPa (allowable 300); bearing on the 16 mm disc 73 MPa.",
               "Stroke 40: retracted, the nose is 19 mm behind the disc and clear of the Ø710 ring and the rear cover (r ≥ 360).",
               "Holder has a proximity switch that reports 'pin engaged' to the safety chain (no rotor release while engaged, doc 11).",
               "Insert only at standstill with the brake applied."]
    return s


# ======================================================================
def dummy_hub():
    dh = G.DUMMY_HUB
    s = Sheet("NP1-600", "BENCH DUMMY HUB (DRIVE AND LOAD ADAPTER)", "S355J2+N weldment, stress relieved",
              "≈ 75 kg", "1:3.3")
    v = s.view("A", 0.3, (190, 178))
    flange = [(175, 170), (190, 170), (190, 180.5), (200, 180.5), (200, 235), (175, 235)]   # Rev B: recess at the hub face
    bell = [(25, 155), (175, 155), (175, 170), (25, 170)]
    front = [(0, 50), (25, 50), (25, 170), (0, 170)]
    shaft = [(-520, 50), (0, 50), (0, 0), (-520, 0)]
    for p in (flange, bell, front):
        v.poly(p, hatch=True)
        v.poly(mirror(p), hatch=True)
    v.poly([(-520, 50), (0, 50), (0, -50), (-520, -50)])
    v.poly([(-215, 50), (-185, 50), (-185, 90), (-215, 90)], layer="PHANTOM")
    v.poly([(-215, -50), (-185, -50), (-185, -90), (-215, -90)], layer="PHANTOM")
    v.centerline((-540, 0), (220, 0))
    v.dim((0, 170), (200, 170), 30, kind="h")
    v.dim((-520, 50), (0, 50), 40, kind="h", suffix=" shaft")
    v.dim((200, 235), (200, -235), -15, kind="v", prefix="Ø", text="470")
    v.dim((175, 180.5), (175, -180.5), 12, kind="v", prefix="Ø", text="361 H7 recess")
    v.dim((-300, 50), (-300, -50), 10, kind="v", prefix="Ø", text="100 m6")
    v.leader((-200, 90), (-260, 150), "load bearing 22220 E in housing, x = −200 (load unit)", 2.2)
    v.leader((-520, 30), (-500, -150), "coupling flange to torque transducer", 2.2)
    v.leader((190, 220), (260, 200), "12× Ø17 PCD 400 (M16 10.9, 280 Nm)", 2.2)
    title(v, -520, 250, "SECTION (x as in GA; drive end left)", 3.0)
    s.notes = [
        "Replaces the cast hub for P1. Same interface as doc 13: 12× M16 10.9 on PCD 400, Ø360 spigot; it clears the spindle nose, nose cap and front seal cover (min. radial gap 30).",
        "Shaft Ø100 forged 42CrMo4+QT, shrink fitted and welded into the front plate; run-out of Ø100 to the recess ≤ 0.05.",
        "Radial arm interface (not shown): 4× M24 on the bell at 90° for the 1.0 m torque arm used in brake, lock pin and yaw tests (doc 15).",
        "Balanced with the drum to G2.5.",
    ]
    return s


# ======================================================================
def bench_layout():
    s = Sheet("NP1-620", "BENCH TEST RIG · GENERAL LAYOUT", "see doc 15", "", "1:20")
    v = s.view("side", 0.05, (205, 75))
    H = 1200.0           # spindle axis height above floor
    # floor
    v.line((-3600, 0), (2000, 0), "OUTLINE")
    # pedestal
    v.poly([(-200, 0), (200, 0), (200, H - 600), (-200, H - 600)])
    v.text((-180, 200), "PEDESTAL", 2.0)
    # yaw + wedge + bedplate block
    v.poly([(-304, H - 600), (304, H - 600), (304, H - 520), (-304, H - 520)])
    v.poly([(-330, H - 520), (330, H - 520), (330, H - 120), (-280, H - 120)])
    # drivetrain
    v.poly([(-750 + 212, H - 323), (-750 + 465, H - 323), (-750 + 465, H + 323), (-750 + 212, H + 323)])
    v.poly([(-750 + 435, H - 400), (-750 + 451, H - 400), (-750 + 451, H + 400), (-750 + 435, H + 400)])
    # dummy hub + load unit + drive
    v.poly([(-750, H - 235), (-750 + 200, H - 235), (-750 + 200, H + 235), (-750, H + 235)])
    v.poly([(-1270, H - 50), (-750, H - 50), (-750, H + 50), (-1270, H + 50)])
    v.poly([(-1000, 0), (-900, 0), (-900, H - 90), (-1000, H - 90)])
    v.text((-1120, H - 300), "LOAD UNIT", 2.0)
    v.poly([(-1500, H - 100), (-1300, H - 100), (-1300, H + 100), (-1500, H + 100)])
    v.text((-1520, H + 140), "TORQUE 2 kNm", 2.0)
    v.poly([(-2100, H - 200), (-1600, H - 200), (-1600, H + 200), (-2100, H + 200)])
    v.text((-2100, H + 240), "GEARBOX i=6", 2.0)
    v.poly([(-3200, H - 250), (-2200, H - 250), (-2200, H + 250), (-3200, H + 250)])
    v.text((-3200, H + 290), "DRIVE MOTOR 37 kW", 2.0)
    v.poly([(-3300, 0), (-1250, 0), (-1250, H - 400), (-3300, H - 400)], layer="HIDDEN")
    v.text((-3200, 300), "DRIVE BED (T-slot)", 2.0)
    v.line((-3300, H), (500, H), "CENTER")
    v.dim((0, 0), (0, H), -60, kind="v", text="1200")
    # cylinders
    v.poly([(-1010, H - 600), (-990, H - 600), (-990, H - 90), (-1010, H - 90)], layer="PHANTOM")
    v.text((-1200, H - 700), "Fz cylinder 30 kN", 2.0)
    v.poly([(-1350, H - 30), (-1290, H - 30), (-1290, H + 30), (-1350, H + 30)], layer="PHANTOM")
    title(v, -3500, 2050, "SIDE VIEW · spindle horizontal (5° wedge under the yaw bearing)", 3.0)
    s.notes = [
        "Energy is recirculated: drive inverter and generator-side load inverter share one DC bus; the grid supplies only the losses (≈ 3 kW at rated).",
        "Load unit: spherical roller bearing on the dummy hub shaft at x = −200, pushed by a vertical cylinder (≤ 30 kN, servo-hydraulic) and an axial cylinder (≤ 45 kN, static tests only). Couplings each side of the torque transducer decouple bending from the torque reading.",
        "Pedestal, load frame and drive bed bolted to a strong floor or a 6 t concrete block; first pedestal mode > 25 Hz (well above 250 rpm × 3 = 12.5 Hz).",
        "Guards: full enclosure of the rotating drum, coupling guards, magnet hazard zone during assembly, interlocked access door wired into the bench safety relay.",
    ]
    return s


# ======================================================================
def assembly_tool():
    s = Sheet("NP1-T01", "DRUM ASSEMBLY GUIDE (MAGNET SAFETY TOOL)", "S355 / PA6 bushes", "≈ 30 kg", "1:5")
    v = s.view("A", 0.2, (190, 175))
    v.poly([(-600, 60), (40, 60), (40, -60), (-600, -60)])
    v.poly([(-560, 60), (-520, 60), (-520, 125), (-560, 125)], hatch=True)
    v.poly([(-560, -60), (-520, -60), (-520, -125), (-560, -125)], hatch=True)
    v.poly([(-620, 20), (60, 20), (60, -20), (-620, -20)], layer="HIDDEN")
    v.centerline((-650, 0), (120, 0))
    v.leader((-540, 125), (-500, 250), "PA6 guide bushes in drum front housing bore", 2.2)
    v.leader((0, 60), (40, 200), "guide tube Ø120 h7, bolts to spindle nose", 2.2)
    v.leader((-610, 0), (-640, -200), "M24 screw jack, 1 mm per turn", 2.2)
    title(v, -620, 280, "GUIDE TUBE ON SPINDLE NOSE", 3.0)
    s.notes = [
        "Radial magnetic pull with the drum off-centre is ≈ 1.9 kN per mm of eccentricity (doc 07) and grows quickly; never let the magnet ring approach the stator by hand.",
        "Procedure: spindle vertical, nose up; guide tube bolted to the nose; drum hung from the crane, centred by two PA6 bushes on the tube before the magnets reach the stator; lowered by the screw jack until the rear cup reaches the rear cone.",
        "Gap check during lowering: 4 non-magnetic feelers (G10, 1.5 mm) in the gap at 90°.",
    ]
    return s


ALL = [ga_drivetrain, spindle, spacer, cooling_insert, carrier, lamination, clamp_ring, drum,
       seal_covers, rear_cover, magnet, brake_disc, bedplate, lock_pin, dummy_hub, bench_layout,
       assembly_tool]
