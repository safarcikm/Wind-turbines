"""6 kW turbine S6 drawing set (doc 32).

    python3 drawings6.py          -> out/NS6-drawing-set.pdf, out/pdf, out/dxf, out/svg, out/png, out/drawing-index.md

Uses the drafting library and the Rev B / Rev C drivetrain geometry of cad/nacelle_p1 (one source of truth),
and the S6 results of analysis/turbine_6kw (design6.json, bedplate6.json, g6.json).
New 6 kW parts are drawn here; shared 12 kW parts are listed on NS6-001 with their existing drawing numbers.
"""
from __future__ import annotations

import json
import re
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "cad" / "nacelle_p1"))
sys.path.insert(0, str(ROOT / "analysis" / "turbine_6kw"))
import geometry as G  # noqa: E402
from draft import Sheet  # noqa: E402

RES = ROOT / "analysis" / "turbine_6kw" / "results"
D6 = json.loads((RES / "design6.json").read_text())
BP = json.loads((RES / "bedplate6.json").read_text())["NS6-300 (6 kW)"]
BPI = BP["inputs"]
DES = json.loads((RES / "design.json").read_text())
OUT = HERE / "out"
PROJECT = "6 kW WIND TURBINE S6 (ICELAND) · FIXED PITCH, STALL CONTROL"
DATE = "2026-11-06"
TILT = math.radians(G.TILT_DEG)
RC = (-G.X_YAW, G.H_ROTOR + 40.0)        # rotor centre, nacelle world frame (X fwd = downwind, Z up from bedplate underside)
R_ROT = 3000.0
TW = D6["tower"]["tower"]
HEAD_MASS = None                          # filled in main() from the doc 32 mass list


def S(number, title, material, mass, scale):
    return Sheet(number, title, material, mass, scale, rev="A", date=DATE, project=PROJECT)


def P(s, u):
    """spindle frame (s along the axis rearwards, u up) -> nacelle world (X, Z)"""
    return (RC[0] + math.cos(TILT) * s + math.sin(TILT) * u, RC[1] - math.sin(TILT) * s + math.cos(TILT) * u)


def title(v, x, y, text, h=3.2):
    v.text((x, y), text, h, "left", "bottom")


# ======================================================================== NS6-000
def ga_turbine():
    s = S("NS6-000", "GENERAL ARRANGEMENT · TURBINE", "see parts list", f"≈ {HEAD_MASS:.0f} kg head + {TW['mass_kg']:.0f} kg tower", "1:125")
    v = s.view("side", 0.008, (110, 45))
    H = 18000.0
    zt = H - 360.0                                     # tower top flange below the yaw bearing
    # tower
    db, dt = TW["geometry"]["D_base"] * 1000, TW["geometry"]["D_top"] * 1000
    v.poly([(-db / 2, 0), (db / 2, 0), (dt / 2, zt), (-dt / 2, zt)])
    v.line((-(db + dt) / 4, 9000), ((db + dt) / 4, 9000), "THIN")
    v.text(((db + dt) / 4 + 150, 9200), "section flange 12 × M24", 2.0, va="bottom")
    # nacelle and rotor (X fwd = towards the rotor = left on the sheet)
    zb = H - 360.0 + 360.0                             # yaw bearing top = bedplate underside at hub height - 570
    z0 = H - (G.H_ROTOR + 40.0)                        # bedplate underside so that the rotor centre is at 18 m
    hub = (-G.X_YAW, H)
    v.poly([(-330, z0), (150, z0), (150, z0 + 200), (-232, z0 + 755), (-296, z0)])
    v.poly([(hub[0] + 200, H - 345), (hub[0] + 480, H - 345), (hub[0] + 480, H + 345), (hub[0] + 200, H + 345)])
    v.poly([(hub[0] - 330, H), (hub[0] - 150, H + 330), (hub[0] + 200, H + 360), (hub[0] + 200, H - 360), (hub[0] - 150, H - 330)])
    for a in (0.0, 120.0, 240.0):                     # blades seen from the side: one up, two at ±120°
        z1 = H + R_ROT * math.cos(math.radians(a))
        v.line((hub[0] - 40, H + 280 * math.cos(math.radians(a))), (hub[0] - 40, z1), "OUTLINE")
    v.circle(hub, 40, "CENTER")
    # ground and footing
    v.line((-3500, 0), (3500, 0), "OUTLINE")
    B = 3800.0
    v.poly([(-B / 2, -1600), (B / 2, -1600), (B / 2, -1000), (600, -1000), (600, 0), (-600, 0), (-600, -1000), (-B / 2, -1000)], hatch=True)
    v.dim((3200, 0), (3200, H), -6, kind="v", text="18 000 hub height")
    v.dim((hub[0], H + R_ROT), (hub[0], H - R_ROT), 16, kind="v", text="Ø6 000 rotor")
    v.dim((-B / 2, -1600), (B / 2, -1600), -6, kind="h", text="3 800 (firm) … 4 200 (soft) square")
    v.dim((2400, 0), (2400, -1600), -6, kind="v", text="1 600")
    v.leader((dt / 2, zt - 1500), (1400, zt - 3500), f"tower Ø{dt:.0f} × 8 top, Ø{db:.0f} × 10 base, 2 × 9 m, tilt-up", 2.0)
    v.leader((hub[0] - 40, H + 2200), (1400, H + 2600), "3 blades 2 720 long, fixed pitch −2°", 2.0)
    v.leader((0, z0 + 400), (1400, H - 2200), "nacelle: G6 generator, NS6-300 bedplate, yaw ring", 2.0)
    v.leader((db / 2, 300), (1400, 1500), "base hinge + 24 × M24 base flange", 2.0)
    title(v, -3500, H + R_ROT + 500, "SIDE VIEW (wind from the left)", 3.0)
    w = s.view("front", 0.008, (265, 45))
    w.poly([(-db / 2, 0), (db / 2, 0), (dt / 2, zt), (-dt / 2, zt)])
    w.circle((0, H), R_ROT, "PHANTOM")
    for a in (90.0, 210.0, 330.0):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        w.poly([(280 * ca - 100 * sa, H + 280 * sa + 100 * ca), (R_ROT * ca - 90 * sa, H + R_ROT * sa + 90 * ca),
                (R_ROT * ca + 60 * sa, H + R_ROT * sa - 60 * ca), (280 * ca + 100 * sa, H + 280 * sa - 100 * ca)])
    w.circle((0, H), 330)
    w.line((-3500, 0), (3500, 0))
    title(w, -3500, H + R_ROT + 500, "VIEW FROM UPWIND", 3.0)
    s.table = [["Item", "Value"], ["Rated power", "6 kW electric at ≈ 9.7 m/s"], ["Rotor", "Ø6.0 m, 3 blades, TSR 5.5, fixed pitch −2°"],
               ["Speed", "41–164 rpm, trip 189 rpm"], ["Control", "stall by speed (converter), storm ramp 25–30 m/s"],
               ["Stopping", "K1 braking resistor 3 × 4 Ω + spring brake 1.5 kNm"], ["Storm", "stop, yaw 90° out, hold"],
               ["Hub height", "18 m, tilt-up monopole"], ["Tower f1", "0.87 Hz (exclusion 47.5–57.4 rpm)"],
               ["Head mass", f"≈ {HEAD_MASS:.0f} kg above the tower flange"], ["Tower mass", f"{TW['mass_kg']:.0f} kg"]]
    s.table_pos = (330, 285); s.table_widths = [26, 54]
    s.notes = ["Docs 28–32. Shared 12 kW parts are listed on NS6-001 with their own drawing numbers.",
               "Rotor plane 750 mm upwind of the yaw axis, shaft tilt 5°, rotor centre 570 mm above the yaw bearing top face.",
               "Footing size depends on the ground class (doc 30 §6): firm 3.8 m / 9.5 m³, frost silt 3.9 m / 10.0 m³, soft volcanic 4.2 m / 11.4 m³; rock: 1.6 × 1.6 × 0.8 m plinth with 8 anchors (NS6-500)."]
    return s


# ======================================================================== NS6-001 parts list / reused drawings
def parts_list():
    s = S("NS6-001", "PARTS LIST AND REUSED 12 kW DRAWINGS", "–", "–", "–")
    rows = [["Item", "Drawing", "Part", "Source", "Qty", "Mass kg"],
            ["1", "NS6-100", "Blade, glass/epoxy, glass UD caps", "new", "3", f"{D6['blade']['glass']['mass_kg']:.1f}"],
            ["2", "NS6-200", "Fixed hub weldment S355NL + shims ±2°", "new", "1", f"{D6['hub']['mass_kg']:.0f}"],
            ["3", "NS6-210", "Spinner (GRP)", "new", "1", "6"],
            ["4", "Rev C gen.", "G6 generator: Rev C stator, drum, magnets, no fins/ribs", "doc 23/29", "1", "263"],
            ["5", "NS6-610", "Plain rear cover (replaces the bladed Rev C cover)", "new", "1", "7"],
            ["6", "NP1-100/101", "Spindle 42CrMo4 Ø140/90 + spacer", "12 kW", "1", "58"],
            ["7", "NP1-230", "Brake disc 16 mm", "12 kW", "1", "34.5"],
            ["8", "NP1-310", "Brake caliper bracket (one of two positions used)", "12 kW", "1", "–"],
            ["9", "bought", "Spring caliper, 1.5 kNm spring pack", "doc 29", "1", "≈ 9"],
            ["10", "NP1-320", "Rotor lock pin and holder", "12 kW", "1", "4"],
            ["11", "NS6-300", "Bedplate weldment, 6 kW (lighter)", "new (doc 32)", "1", f"{BP['mass_kg']:.0f}"],
            ["12", "NY-400…460", "Yaw ring, adapter, 2 gearmotors, pads, lock, encoder, hanger", "12 kW doc 25", "1 set", "≈ 275"],
            ["13", "NS6-400", "Tower 18 m, 2 sections, base hinge", "new size", "1", f"{TW['mass_kg']:.0f}"],
            ["14", "NS6-500", "Foundation: spread footing or rock plinth", "new size", "1", "concrete"],
            ["15", "NS6-600", "Braking resistor box + K1 + safety chain", "new (doc 29)", "1", "≈ 18"],
            ["16", "doc 12", "Converter, dump chopper, 48 V module (6 kW firmware)", "12 kW", "1", "–"]]
    s.table = rows
    s.table_pos = (14, 280)
    s.table_widths = [12, 26, 110, 30, 14, 20]
    s.notes = ["The 12 kW drawings named here (cad/nacelle_p1 NP1-xxx, cad/yaw NY-4xx, generator Rev C sheets in project files generator/revC) are used unchanged.",
               "G6 differences from Rev C (doc 29): inner fins, outer ribs and cover blades left off; one caliper with a lighter spring pack; braking resistor and contactor added.",
               "NS6-300 replaces the 12 kW bedplate NP1-300 (doc 32). Same interfaces: spindle flange, yaw inner ring, gearmotor brackets NP1-420, pad units NY-410, lock pin holder, cable hanger.",
               "Masses: calculated. Head mass above the tower flange in doc 32 §2."]
    s.notes_top = (14, 190)
    return s


# ======================================================================== NS6-010 nacelle GA
def ga_nacelle():
    s = S("NS6-010", "GENERAL ARRANGEMENT · NACELLE SECTION", "see NS6-001", f"≈ {HEAD_MASS:.0f} kg above the tower flange", "1:10")
    v = s.view("side", 0.1, (250, 120))
    # drivetrain (spindle frame -> world)
    def tp(poly, mirror=False):
        return [P(x, -r if mirror else r) for x, r in poly]
    v.poly(tp(G.spindle_section()), hatch=True); v.poly(tp(G.spindle_section(), True), hatch=True)
    for nm, poly in G.DRUM_PARTS.items():
        if nm in ("fins", "ribs"):
            continue
        v.poly(tp(poly), hatch=True); v.poly(tp(poly, True), hatch=True)
    v.poly(tp(G.DISC_POLY), hatch=True); v.poly(tp(G.DISC_POLY, True), hatch=True)
    v.poly(tp(G.REAR_COVER), hatch=True); v.poly(tp(G.REAR_COVER, True), hatch=True)
    v.poly(tp(G.STACK_POLY)); v.poly(tp(G.STACK_POLY, True))
    v.poly(tp(G.CARRIER)); v.poly(tp(G.CARRIER, True))
    # fixed hub: drum flange, centre shell, arm stubs, root flanges (spindle frame)
    hub = [(175, 150), (200, 150), (200, 240), (175, 240)]
    shell = [(-65, 178), (175, 178), (175, 190), (-65, 190)]
    v.poly(tp(hub), hatch=True); v.poly(tp(hub, True), hatch=True)
    v.poly(tp(shell), hatch=True); v.poly(tp(shell, True), hatch=True)
    arm = [(-110, 190), (110, 190), (110, 280), (-110, 280)]
    v.poly(tp(arm)); v.poly(tp([(-140, 280), (140, 280), (140, 305), (-140, 305)]), hatch=True)
    v.poly(tp([(-70, -190), (70, -190), (70, -230), (-70, -230)]), layer="PHANTOM")
    # blade root (upper blade) and spinner
    v.poly(tp([(-110, 305), (110, 305), (95, 900), (-60, 900)]), layer="OUTLINE")
    v.poly(tp([(-330, 0), (-250, 160), (-120, 300), (60, 360), (180, 360)]), closed=False, layer="PHANTOM")
    v.poly(tp([(-330, 0), (-250, -160), (-120, -300), (60, -360), (180, -360)]), closed=False, layer="PHANTOM")
    # bedplate NS6-300 (world)
    tb = -BP["axis_above_bottom_top"]
    xf, xr = 480.0, 480.0 + BPI["t_front"]
    v.poly([P(xf, tb), P(xf, BPI["u_top"]), P(xr, BPI["u_top"]), P(xr, tb)], hatch=True)
    v.poly([P(470, -205), P(470, 205), P(xf, 205), P(xf, -205)], hatch=True)
    v.poly([(BPI["x_bot_front"], 0), (BPI["x_rear"], 0), (BPI["x_rear"], BPI["t_bottom"]), (BPI["x_bot_front"], BPI["t_bottom"])], hatch=True)
    v.poly([tuple(p) for p in BP["side_poly"]])
    for x, z, r in BPI["holes"]:
        v.circle((x, z), r, "HIDDEN")
    # yaw bearing, adapter, tower top
    v.poly([(-175, 0), (175, 0), (175, -70), (-175, -70)], hatch=True)
    v.poly([(-250, -70), (-150, -70), (-150, -95), (-250, -95)], hatch=True); v.poly([(150, -70), (250, -70), (250, -95), (150, -95)], hatch=True)
    v.poly([(-304, -70), (-185, -70), (-185, -10), (-304, -10)], layer="PHANTOM"); v.poly([(185, -70), (304, -70), (304, -10), (185, -10)], layer="PHANTOM")
    v.poly([(-198, -95), (-166, -330), (-154, -330), (-186, -95)]); v.poly([(198, -95), (166, -330), (154, -330), (186, -95)])
    v.poly([(-210, -330), (210, -330), (210, -360), (-210, -360)], hatch=True)
    v.poly([(-160, -360), (-160, -600), (-152, -600), (-152, -360)]); v.poly([(160, -360), (160, -600), (152, -600), (152, -360)])
    # yaw gearmotor (left, behind the section plane)
    v.poly([(-50, -65), (50, -65), (50, 335), (-50, 335)], layer="HIDDEN")
    # axes
    v.line(P(-400, 0), P(800, 0), "CENTER")
    v.line((0, -620), (0, 950), "CENTER")
    v.dim((RC[0], RC[1] + 900), (0, RC[1] + 900), 6, kind="h", text="750 rotor plane to yaw axis")
    v.line((RC[0], RC[1]), (RC[0], RC[1] + 960), "THIN")
    v.dim((0, 0), (0, RC[1]), -48, kind="v", text="570")
    v.dim((-175, -360), (175, -360), -8, kind="h", text="Ø320 tower top")
    labels = [((P(300, 330)), (-500, 1000), "G6 drum (Rev C, no ribs) + magnets"),
              (P(380, 260), (-330, 1100), "stator 45 slots, 74 mm stack"),
              (P(443, 420), (300, 1050), "brake disc NP1-230, 1 caliper 1.5 kNm"),
              (P(0, 600), (-1300, 1000), "blade root Ø220, 10 × M12 inserts"),
              (P(0, 250), (-1350, 780), "fixed hub NS6-200, ±2° shims"),
              (P(150, 60), (-1350, 300), "spindle NP1-100 (fixed), tapered roller pair"),
              ((BPI["x_rear"] - 30, 120), (350, 650), "bedplate NS6-300"),
              ((0, -40), (380, -160), "yaw ring Dpw 360, z150 m4"),
              ((0, 200), (380, 300), "yaw gearmotor (2, ±90°), NP1-420 bracket"),
              ((170, -200), (380, -420), "adapter NY-400, 16 × M20 to the tower")]
    for p, q, t in labels:
        v.leader(p, q, t, 2.0)
    title(v, -2300, 1480, "SECTION ON THE ROTOR AXIS (yaw 0°, wind from the left)", 3.0)
    s.notes = ["Drivetrain geometry from cad/nacelle_p1/geometry.py (Rev B nacelle, Rev C generator, doc 23); fins, ribs and cover blades not fitted on G6 (doc 29).",
               "Rotor turns with the drum on two tapered roller bearings on the stationary spindle; the hub bolts to the drum front face (12 × M16 PCD 400).",
               "Section shows the hub arm of the upper blade; the other two arms are at ±120°. Spinner (phantom) is GRP, NS6-210.",
               "Braking resistor box NS6-600 is mounted on the tower base cabinet wall, not in the nacelle (heat). Phase leads run in the hanger tube."]
    return s


# ======================================================================== NS6-100 blade
def blade():
    s = S("NS6-100", "BLADE · PLANFORM, TWIST AND ROOT", "E-glass/epoxy infused; glass UD caps; PVC core shells",
          f"{D6['blade']['glass']['mass_kg']:.1f} kg", "1:10")
    st = D6["blade_stations"]
    r = np.array(st["r"]) * 1000; c = np.array(st["chord"]) * 1000
    v = s.view("plan", 0.1, (40, 200))
    # pitch axis at 30 % chord: leading edge at +0.3c, trailing edge at -0.7c (sheet y)
    le = [(x, 0.3 * cc) for x, cc in zip(r, c)]
    te = [(x, -0.7 * cc) for x, cc in zip(r, c)]
    v.poly(le + te[::-1])
    v.centerline((r[0] - 30, 0), (r[-1] + 30, 0))
    v.text((r[-1] + 60, 0), "pitch axis 30 % c", 2.0, va="center")
    for x in (280, 500, 1000, 1500, 2000, 2500, 3000):
        cc = float(np.interp(x, r, c))
        v.line((x, 0.3 * cc + 8), (x, -0.7 * cc - 8), "THIN")
    v.dim((r[0], 260), (r[-1], 260), 6, kind="h", text="2 720 blade length (r 280 → 3 000)")
    v.dim((620, 0.3 * 373), (620, -0.7 * 373), -10, kind="v", text="373 max chord")
    v.dim((3000, 0.3 * 177), (3000, -0.7 * 177), -8, kind="v", text="177")
    title(v, 0, 330, "PLANFORM (suction side up, root on the left)", 3.0)
    # root end view
    w = s.view("root", 0.3, (365, 235))
    w.circle((0, 0), 110)
    w.circle((0, 0), 82, "HIDDEN")
    w.bolt_circle((0, 0), 185, 10, 12.0, start=18.0)
    w.dim((-110, 0), (110, 0), -38, kind="h", prefix="Ø", text="220")
    w.text((-110, -150), "10 × M12 inserts, PCD 185, 36° pitch", 2.0)
    title(w, -110, 135, "ROOT END (from the hub)", 2.8)
    # twist / thickness table
    sys.argv = sys.argv[:1]
    import design6 as D  # noqa: E402
    b = D.blade_shape(n=40)
    tw = np.array(b.twist + b.twist_tip_offset)
    rr = np.array(b.r) * 1000
    rows = [["r mm", "chord", "twist °", "t/c", "cap mm"]]
    for x in (280, 400, 600, 800, 1000, 1400, 1800, 2200, 2600, 3000):
        rows.append([f"{x}", f"{np.interp(x, r, c):.0f}", f"{np.interp(x, rr, tw):.1f}", f"{np.interp(x, r, st['t_over_c']):.2f}",
                     f"{np.interp(x, r, st['t_cap_mm']):.2f}"])
    s.table = rows
    s.table_pos = (320, 165); s.table_widths = [16, 16, 16, 14, 16]
    s.notes = ["Aerofoil family and twist from analysis/rotor/bem.py (TSR 5.5, cl 1.0, R 3.0 m, root r 0.28 m); twist given at the pitch axis, positive nose up towards feather; blade set at −2° with the hub shims (NS6-200).",
               "Structure doc 30 §2 / doc 10 model: two glass UD caps (table), ±45° glass skins, PVC foam core, single shear web 1.5 mm glass; root wall builds up 12 mm over the first 0.7 m. Cap buckling at minimum thickness governs (use 1.00); strength 0.43 (SLM H), fatigue 0.10 with simulated loads (doc 31).",
               "Root: 10 bonded steel inserts M12 (IKEA-type sleeve), PCD 185, pull-out ≥ 60 kN each (test). Bolt force 43 kN at SLM H.",
               "Mass 20.6 kg ± 0.3 kg; static moment matched within 0.5 % per set of three (balance class doc 09). Erosion tape on the outer 1 m of the leading edge.",
               "First flap 15.2 Hz, first edge 38.3 Hz at standstill. Tip deflection 0.06 m, tower clearance 0.83 m."]
    s.notes_top = (14, 140)
    return s


# ======================================================================== NS6-200 fixed hub
def hub():
    h = D6["hub"]
    s = S("NS6-200", "FIXED HUB WELDMENT", "S355NL (EN 10025-3), welded, stress relieved, machined", f"{h['mass_kg']:.0f} kg (+ 6 kg spinner)", "1:5")
    v = s.view("front", 0.2, (110, 160))
    v.circle((0, 0), 190); v.circle((0, 0), 178, "HIDDEN")
    v.bolt_circle((0, 0), 400, 12, 18.0, start=15.0, layer="HIDDEN")
    v.circle((0, 0), 240, "HIDDEN")
    for a in (90.0, 210.0, 330.0):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        rot = lambda x, y: (x * ca - y * sa, x * sa + y * ca)  # noqa: E731
        v.poly([rot(186, -110), rot(280, -110), rot(280, 110), rot(186, 110)])
        v.poly([rot(280, -140), rot(305, -140), rot(305, 140), rot(280, 140)], hatch=True)
        v.line(rot(150, 0), rot(360, 0), "CENTER")
    v.dim((-190, 0), (190, 0), -40, kind="h", prefix="Ø", text="380 × 12 centre shell")
    v.dim((0, 0), (0, 305), -60, kind="v", text="305 root face radius")
    title(v, -330, 340, "VIEW FROM UPWIND (spinner removed)", 3.0)
    w = s.view("section", 0.2, (300, 160))
    # side section through the upper arm: x along the axis (rotor plane at 0), y radial
    w.poly([(-65, 178), (175, 178), (175, 190), (-65, 190)], hatch=True)
    w.poly([(-65, -178), (175, -178), (175, -190), (-65, -190)], hatch=True)
    w.poly([(175, 150), (200, 150), (200, 240), (175, 240)], hatch=True)
    w.poly([(175, -150), (200, -150), (200, -240), (175, -240)], hatch=True)
    w.poly([(-110, 190), (-102, 190), (-102, 280), (-110, 280)], hatch=True)
    w.poly([(102, 190), (110, 190), (110, 280), (102, 280)], hatch=True)
    w.poly([(-140, 280), (140, 280), (140, 305), (-140, 305)], hatch=True)
    w.poly([(-65, 178), (-55, 178), (-55, -178), (-65, -178)], hatch=True)
    w.line((-200, 0), (260, 0), "CENTER")
    w.line((0, -260), (0, 360), "CENTER")
    w.dim((-140, 305), (140, 305), 8, kind="h", prefix="Ø", text="280 root flange 25")
    w.dim((175, -240), (200, -240), -8, kind="h", text="25")
    w.dim((-65, -190), (175, -190), -16, kind="h", text="240")
    w.leader((106, 240), (220, 330), "arm Ø220 × 8", 2.0)
    w.leader((175, -210), (250, -300), "drum flange Ø480 / 12 × Ø18 PCD 400", 2.0)
    title(w, -200, 380, "SECTION THROUGH THE UPPER ARM", 3.0)
    s.notes = [f"Arms Ø220 × 8: parked SLM stress {h['chosen']['static_MPa']} MPa (allow 323); fatigue at the flange weld 5.7 MPa with simulated loads (allow 30.8, detail 71).",
               "Drum joint: 12 × M16 10.9 PCD 400 (Rev C interface), friction grip, slip OK at 5.7 kNm design torque.",
               "Root flange faces machined after stress relief at −2.0° ± 0.05° pitch about each arm axis; 10 × M12 clearance holes Ø13 PCD 185; shim seat for ±2° tapered shims (0.5° steps).",
               "Welds full penetration at arm-to-shell and arm-to-flange, ISO 5817 B, 100 % MT + UT on the flange welds. Hot-dip galvanised or zinc sprayed + C5 paint.",
               "Front plate Ø356 × 10 closes the shell; spinner brackets (3 × M8) on the arms. FE check of the arm-to-shell weld before release (doc 30 §11)."]
    return s


# ======================================================================== NS6-300 bedplate
def bedplate():
    s = S("NS6-300", "BEDPLATE WELDMENT 6 kW (LIGHT)", "S355J2+N plates, stress relieved, machined", f"{BP['mass_kg']:.0f} kg", "1:5")
    v = s.view("side", 0.2, (150, 95))
    tb = -BP["axis_above_bottom_top"]
    xf, xr = 480.0, 480.0 + BPI["t_front"]
    tbot = BPI["t_bottom"]
    v.poly([P(xf, tb), P(xf, BPI["u_top"]), P(xr, BPI["u_top"]), P(xr, tb - BPI["t_front"] * math.tan(TILT))], hatch=True)
    v.poly([P(470, -205), P(470, 205), P(xf, 205), P(xf, -205)], hatch=True)
    v.poly([(BPI["x_bot_front"], 0), (BPI["x_rear"], 0), (BPI["x_rear"], tbot), (BPI["x_bot_front"], tbot)], hatch=True)
    sp = [tuple(p) for p in BP["side_poly"]]
    v.poly(sp)
    v.poly([(BPI["x_rear"] - 10, tbot), (BPI["x_rear"], tbot), (BPI["x_rear"], tbot + 100), (BPI["x_rear"] - 10, tbot + 100)], hatch=True)
    for x, z, r in BPI["holes"]:
        v.circle((x, z), r)
    for x in (-50.0, 50.0):
        for z in (70.0, 140.0):
            v.circle((x, z), 9.0)
    gp = P(xr, tb)
    v.poly([gp, (gp[0] + 180, tbot), (gp[0], tbot + 180)], layer="HIDDEN")
    v.line(P(-50, 0), P(700, 0), "CENTER")
    v.line((0, -40), (0, 830), "CENTER")
    v.text((5, 810), "YAW AXIS", 2.2)
    v.poly([P(x, min(r, 400)) for x, r in G.DISC_POLY], layer="PHANTOM")
    v.poly([P(x, -r) for x, r in G.DISC_POLY], layer="PHANTOM")
    v.poly([(-175, 0), (175, 0), (175, -70), (-175, -70)], layer="PHANTOM")
    v.dim((BPI["x_bot_front"], 0), (BPI["x_rear"], 0), -14, kind="h")
    v.dim((0, 0), (0, RC[1]), -60, kind="v", text="570 to rotor centre")
    v.dim(sp[1], (BPI["x_rear"], 0), -14, kind="v")
    v.leader((-150, 435), (250, 830), "lightening holes Ø150 + Ø110 per side, edges ground R2", 2.0)
    v.leader((50, 140), (260, 560), "4 × Ø18 for NP1-420 (x ±50, z 70/140)", 2.0)
    v.leader((BPI["x_rear"] - 5, 100), (260, 380), "rear tie 10 × 100", 2.0)
    v.leader((gp[0] + 40, tbot + 60), (-560, 180), "2 gussets 12, 180 × 180", 2.0)
    title(v, -600, 920, "SIDE VIEW (Z = 0 section), phantom: disc and yaw bearing", 3.0)
    w = s.view("front", 0.1, (355, 225))
    hf = BP["axis_above_bottom_top"]
    w.poly([(-250, -hf), (250, -hf), (250, BPI["u_top"]), (-250, BPI["u_top"])])
    w.circle((0, 0), 205, "HIDDEN"); w.circle((0, 0), 100)
    w.bolt_circle((0, 0), 350, 12, 22.0)
    for a in (15, 195):
        w.circle((145 * math.cos(math.radians(a)), 145 * math.sin(math.radians(a))), 16)
    w.poly([(-150, -hf + 40), (150, -hf + 40), (150, -hf + 180), (-150, -hf + 180)])
    w.centerline((-270, 0), (270, 0)); w.centerline((0, -hf - 20), (0, BPI["u_top"] + 20))
    w.dim((-250, BPI["u_top"]), (250, BPI["u_top"]), 6, kind="h")
    w.text((-250, BPI["u_top"] + 45), f"FRONT PLATE {BPI['t_front']:.0f}, view along the spindle axis", 2.4)
    w.text((-150, -hf + 190), "window 300 × 140", 1.9)
    u = s.view("plan", 0.1, (355, 120))
    u.poly([(BPI["x_bot_front"], -260), (BPI["x_rear"] - 150, -260), (BPI["x_rear"], -110), (BPI["x_rear"], 110),
            (BPI["x_rear"] - 150, 260), (BPI["x_bot_front"], 260)])
    u.circle((0, 0), 110)
    u.bolt_circle((0, 0), 300, 16, 18.0, start=11.25)
    for a in (141.8, -141.8):
        for (du, dv) in ((340, -60), (340, 60), (420, -60), (420, 60)):
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            u.circle((du * ca - dv * sa, du * sa + dv * ca), 7.0, "HIDDEN")
    u.circle((0, 0), 130, "PHANTOM")
    u.dim((BPI["x_bot_front"], -260), (BPI["x_bot_front"], 260), 6, kind="v", text="520")
    u.dim((BPI["x_bot_front"], -260), (BPI["x_rear"], -260), -6, kind="h")
    u.text((BPI["x_bot_front"], 290), "BOTTOM PLATE (yaw flange), from below", 2.4)
    s.notes = [f"Replaces NP1-300 (12 kW, {json.loads((RES / 'bedplate6.json').read_text())['NP1-300 (12 kW, as drawn)']['mass_kg']:.0f} kg as drawn) on S6 (doc 32). Same interfaces: Ø410 × 10 pad at x 470, Ø200 H7 spigot, 12 × Ø22 PCD 350 (M20 10.9 from inside, 540 Nm), 2 × Ø32 cable holes PCD 290; bottom Ø220 bore, 16 × Ø18 PCD 300 (yaw inner ring, M16 10.9 with nuts).",
               f"Plates: front {BPI['t_front']:.0f}, bottom {BPI['t_bottom']:.0f}, sides {BPI['t_side']:.0f} (outer faces Y ±260 for NP1-420), rear tie 10, gussets 12. Rear corners of the bottom plate chamfered 150 × 150.",
               "Pad units NY-410 bolt under the front corners (4 × M12 each, tapped, hidden); hanger tube flange NY-460 on Ø260 at the bore; caliper bracket NP1-310 on the left side plate front edge; lock pin holder NP1-321 on 2 × M12 in the front plate top edge.",
               "Design checks (SLM γ 3, doc 32): root section 21 MPa, front plate 51 MPa, bottom plate 144 MPa (allow 323); fatigue 0.07. Thicknesses are set by machining and slewing ring flatness, not strength: FE stiffness check of the ring seat before release.",
               "Welds ISO 5817 B, 100 % MT; stress relieve; machine front and bottom plates in one set-up on a 5° fixture: front face square to the yaw flange within 0.05/400 at 5.00° ± 0.05°; ring seat flatness 0.05."]
    return s


# ======================================================================== NS6-400 tower
def tower():
    g = TW["geometry"]
    s = S("NS6-400", "TOWER 18 m · TILT-UP MONOPOLE", "S355J2+N, rolled and seam welded; hot-dip galvanised", f"{TW['mass_kg']:.0f} kg", "1:50 / 1:10")
    v = s.view("elev", 0.0125, (50, 25))
    H = 18000.0; zt = H - 600.0
    db, dt = g["D_base"] * 1000, g["D_top"] * 1000
    v.poly([(-db / 2, 0), (db / 2, 0), (dt / 2, zt), (-dt / 2, zt)])
    for z in (0.0, 9000.0, zt):
        d = db + (dt - db) * z / zt
        v.line((-d / 2 - 60, z), (d / 2 + 60, z), "OUTLINE")
    v.dim((db / 2 + 200, 0), (db / 2 + 200, 9000), -8, kind="v", text="9 000 lower, t 10")
    v.dim((db / 2 + 200, 9000), (db / 2 + 200, zt), -8, kind="v", text=f"{zt - 9000:.0f} upper, t 8")
    v.dim((-db / 2, 0), (db / 2, 0), -6, kind="h", prefix="Ø", text=f"{db:.0f}")
    v.dim((-dt / 2, zt), (dt / 2, zt), 6, kind="h", prefix="Ø", text=f"{dt:.0f}")
    v.text((db / 2 + 1500, zt + 200), "adapter NY-400 on top; rotor centre 18 000", 2.0)
    title(v, -2000, zt + 900, "ELEVATION", 3.0)
    f = s.view("flanges", 0.07, (250, 215))
    for (cx, d_in, d_out, n, bolt, pcd, lab) in ((0, 500 - 20, 760, 24, 26, 600, "BASE FLANGE 40, 24 × M24 PCD 600"),
                                                  (1000, 410 - 18, 560, 12, 26, 480, "FLANGE 30 at 9 m, 12 × M24 PCD 480"),
                                                  (1800, 320 - 16, 420, 16, 22, 380, "TOP FLANGE 30, 16 × M20 PCD 380")):
        f.circle((cx, 0), d_out / 2); f.circle((cx, 0), d_in / 2)
        f.bolt_circle((cx, 0), pcd, n, bolt)
        f.text((cx - d_out / 2, -d_out / 2 - 80 - (cx // 1000) * 120), lab, 1.8)
    title(f, -380, 450, "FLANGES (plan)", 3.0)
    s.table = [["Item", "Value"], ["Shell", f"Ø{db:.0f} × 10 → Ø{dt:.0f} × 8, linear taper, D/t ≤ 51"], ["Sections", "2: 9.0 m + 8.4 m, flanged"],
               ["First frequency", f"{TW['f1_rigid_Hz']} Hz (soft footing, ice {TW['f1_soft_ice_Hz']} Hz)"], ["Governing", "parked V_e50, use 0.97"],
               ["Fatigue", "0.06 base, 0.02 at 9 m (doc 31 spectra)"], ["Tilt-up", "base moment 405 kNm, 6 m gin pole, winch 68 kN"],
               ["Base flange", f"24 × M24 10.9, F_bolt {TW['base_flange']['F_bolt_kN']} kN / {TW['base_flange']['F_t_Rd_kN']} kN"]]
    s.table_pos = (250, 150); s.table_widths = [30, 120]
    s.notes = ["Doc 09 design (tilt-up on a base hinge, removable gin pole 0.33 H, no crane) at the doc 30 S6 size; door-free base: cables leave through the base hinge frame into the cabinet.",
               "Longitudinal seam welds full penetration, staggered 90° between cans; flange welds full penetration, ISO 5817 B, 100 % UT; flanges machined flat after welding (0.2 mm).",
               "Climbing: none (service by lowering the tower). Lightning: tower is the down conductor, 2 earthing lugs at the base.",
               "Tower 1P exclusion zone 47.5–57.4 rpm in the controller (doc 31)."]
    s.notes_top = (95, 120)
    s.notes_wrap = 70
    return s


# ======================================================================== NS6-500 foundation
def foundation():
    fnd = D6["tower"]["foundations"]
    s = S("NS6-500", "FOUNDATION · SPREAD FOOTING AND ROCK PLINTH", "C30/37 XF4 air-entrained; B500C rebar", "9.5–11.4 m³ (soil), 2.0 m³ (rock)", "1:50")
    v = s.view("section", 0.02, (110, 150))
    B = 3800.0
    v.poly([(-B / 2, -1600), (B / 2, -1600), (B / 2, -1000), (-B / 2, -1000)], hatch=True)
    v.poly([(-600, -1000), (600, -1000), (600, 150), (-600, 150)], hatch=True)
    v.line((-3000, 0), (3000, 0))
    v.poly([(-380, 150), (380, 150), (380, 300), (-380, 300)])
    for x in (-300, 300):
        v.line((x, -1450), (x, 260), "HIDDEN")
    v.dim((-B / 2, -1600), (B / 2, -1600), -8, kind="h", text="B (table)")
    v.dim((B / 2, -1600), (B / 2, -1000), -8, kind="v", text="600")
    v.dim((600, -1000), (600, 150), -8, kind="v", text="1 150 pedestal Ø1 200")
    v.leader((-300, -800), (-2300, 900), "anchor cage 24 × M24 PCD 600", 2.0)
    v.leader((0, 220), (1200, 900), "hinge frame (doc 09)", 2.0)
    title(v, -2000, 1200, "SPREAD FOOTING, SECTION", 3.0)
    w = s.view("rock", 0.02, (310, 150))
    w.poly([(-800, -800), (800, -800), (800, 0), (-800, 0)], hatch=True)
    w.line((-1600, -200), (1600, -200), "THIN")
    for x in (-600, -200, 200, 600):
        w.line((x, -3800), (x, -100), "HIDDEN")
    w.dim((-800, 0), (800, 0), 8, kind="h", text="1 600")
    w.leader((600, -2500), (1100, -2000), "8 × Ø28 threadbar on Ø1 200, ≥ 3 m bond", 2.0)
    title(w, -1600, 600, "ROCK PLINTH (lava, basalt)", 3.0)
    rows = [["Ground", "B m", "Concrete m³", "Bearing kPa", "q_rd kPa"]]
    for k, f in fnd.items():
        if "B" in f:
            rows.append([k, f"{f['B']}", f"{f['concrete_m3']}", f"{f['bearing_kPa']}", f"{f['q_rd_kPa']}"])
    rows.append(["rock (anchored plinth)", "1.6", "2.0", "–", "anchors 249 kN"])
    s.table = rows
    s.table_pos = (14, 95); s.table_widths = [70, 14, 22, 22, 26]
    s.notes = ["Base 1.6 m below ground (frost depth). Design for the parked V_e50 base moment 617 kNm (doc 30 §6); characteristic eccentricity ≤ B/4, operation ≤ B/6.",
               "Concrete C30/37 XF4 with air entrainment, cover 50 mm; rebar mesh top and bottom Ø16/150 both ways (to be detailed with the local engineer).",
               "Rock: drill Ø76, grout cement 100 %, proof-load each anchor to 1.25 × design before tensioning; plinth cast on cleaned rock with 20 mm shear keys.",
               "Soil class must be confirmed by a site inspection; soft volcanic ash needs a plate-load test."]
    s.notes_top = (14, 55)
    return s


# ======================================================================== NS6-600 braking resistor and safety chain
def resistor():
    s = S("NS6-600", "BRAKING RESISTOR BOX AND SAFETY CHAIN", "Box 1.4301, IP54; resistors steel-grid", "≈ 18 kg", "schematic / 1:5")
    v = s.view("schematic", 0.92, (22, 150))
    # generator
    v.circle((20, 60), 14); v.text((20, 60), "G6\n3~ PM", 2.2, "center", "center")
    for i, y in enumerate((80, 60, 40)):
        v.line((34, y), (150, y))
        v.text((36, y + 1), ["U", "V", "W"][i], 2.0)
    # converter branch
    v.poly([(150, 30), (190, 30), (190, 90), (150, 90)]); v.text((170, 60), "CONVERTER\n(doc 12)", 2.2, "center", "center")
    # K1 + resistors branch
    for i, y in enumerate((80, 60, 40)):
        x = 70 + i * 18
        v.line((x, y), (x, 15))
        v.line((x - 3, 15), (x + 3, 9))           # NC contact symbol
        v.line((x, 9), (x, 0))
        v.poly([(x - 3, 0), (x + 3, 0), (x + 3, -22), (x - 3, -22)])
        v.line((x, -22), (x, -32))
    v.line((70, -32), (106, -32)); v.text((107, -32), "star point", 2.0, va="center")
    v.text((112, 8), "K1 (NC, 3 poles, coil 24 V,\nheld open in normal operation)", 2.0)
    v.text((112, -30), "R 3 × 4.0 Ω star, 3 × 2.5 kW\n(25 kW 10 s), steel grid", 2.0)
    # safety relay
    v.poly([(210, -40), (300, -40), (300, 20), (210, 20)])
    v.text((255, 12), "SAFETY RELAY (PL d, cat. 3)", 2.2, "center")
    for i, t in enumerate(["overspeed 189 rpm (2 sensors)", "converter fault / 24 V loss", "E-stop button", "vibration trip", "brake pad wear / caliper fault"]):
        v.text((214, 4 - i * 7), "– " + t, 2.0)
    v.line((210, -10), (125, -10), "HIDDEN"); v.text((140, -8), "drops K1 coil", 1.9)
    v.line((300, -10), (340, -10), "HIDDEN"); v.text((305, -8), "drops valve", 1.9)
    v.poly([(340, -30), (390, -30), (390, 10), (340, 10)]); v.text((365, -10), "SPRING CALIPER\n1.5 kNm\n(power releases)", 2.0, "center", "center")
    title(v, 0, 105, "SINGLE-LINE: BOTH STOPPING CHANNELS DROP TOGETHER ON A TRIP", 3.0)
    s.notes = ["Doc 29 / 31: K1 is normally closed. While the safety relay is healthy it holds K1 open; any trip or loss of 24 V closes K1 and drops the brake at the same time. Either channel alone keeps the rotor below the trip speed (doc 31: brake alone stops in ≤ 2.4 s, peak 173 rpm; resistor alone slows to a 3–15 rpm crawl).",
               "Resistor current 43 A peak at trip speed with hot magnets; energy of one stop ≈ 120 kJ. Grid resistors in a ventilated 1.4301 box (600 × 400 × 250) on the tower base cabinet wall, not in the nacelle.",
               "K1: 3-pole contactor with mechanically linked mirror contact (EN 60947-4-1 Annex F) for monitoring; AC-3 rating ≥ 63 A at 690 V.",
               "Brake fault alarm: with the brake failed the rotor only crawls, so a failed or worn brake keeps the turbine parked and yawed out until repaired (doc 31 §6).",
               "Spring pack stays 1.5 kNm (Martin, 2026-11-06). Parked yaw-lost 50-year peak aero torque 1.45 kNm; if exceeded the rotor creeps slowly against the brake and the closed K1 (doc 32 §1). Use the lock pin NP1-320 for long unattended outages."]
    s.notes_top = (14, 85)
    return s


# ======================================================================== NS6-610 plain rear cover
def rear_cover():
    s = S("NS6-610", "G6 PLAIN REAR COVER (NO FAN BLADES)", "EN AW-5083-H111, 10 mm plate", "≈ 7 kg", "1:5")
    v = s.view("plan", 0.2, (120, 150))
    v.circle((0, 0), 345); v.circle((0, 0), 216)
    v.bolt_circle((0, 0), 662, 24, 13.0, layer="HIDDEN")
    v.bolt_circle((0, 0), 670, 24, 9.0, start=7.5)
    v.dim((-345, 0), (345, 0), -80, kind="h", prefix="Ø", text="690")
    v.dim((-216, 0), (216, 0), 20, kind="h", prefix="Ø", text="432")
    title(v, -345, 420, "VIEW FROM THE REAR", 3.0)
    w = s.view("sec", 0.2, (330, 150))
    w.poly([(0, 216), (10, 216), (10, 345), (0, 345)], hatch=True)
    w.poly([(0, -216), (10, -216), (10, -345), (0, -345)], hatch=True)
    w.dim((0, 345), (10, 345), 6, kind="h", text="10")
    w.dim((10, -345), (10, 345), -10, kind="v", prefix="Ø", text="690")
    w.line((-20, 0), (40, 0), "CENTER")
    title(w, -40, 380, "SECTION", 3.0)
    s.notes = ["Replaces the Rev C rear cover with 24 fan blades (doc 23/29): G6 runs at half load with no forced cooling; hot spot 86 °C at 1.2 × rated torque without fins, ribs or blades (doc 29).",
               "24 × M8 on PCD 670 to the drum rear ring; seal carrier as Rev C (NP1-212 inner ring).",
               "Rear face runs 5 mm from the bedplate front plate outside the Ø410 pad (as Rev B)."]
    return s


ALL = [ga_turbine, parts_list, ga_nacelle, blade, hub, bedplate, tower, foundation, resistor, rear_cover]


def main():
    global HEAD_MASS
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    HEAD_MASS = json.loads((RES / "head6.json").read_text())["head_mass_kg"]
    for d in ("pdf", "dxf", "svg", "png"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    index = []
    with PdfPages(OUT / "NS6-drawing-set.pdf") as book:
        for fn in ALL:
            sh = fn()
            fig = sh.render()
            fig.savefig(OUT / "pdf" / f"{sh.number}.pdf")
            svg = OUT / "svg" / f"{sh.number}.svg"
            fig.savefig(svg)
            svg.write_text(re.sub(r"<!DOCTYPE[^>]*>\s*", "", svg.read_text(), count=1))   # no DTD: web viewer (viewer6) rejects it
            fig.savefig(OUT / "png" / f"{sh.number}.png", dpi=110)
            book.savefig(fig)
            plt.close(fig)
            sh.to_dxf(OUT / "dxf" / f"{sh.number}.dxf")
            index.append((sh.number, sh.title, sh.material, sh.mass))
            print(sh.number, sh.title)
    md = ["| Drawing | Title | Material | Mass |", "|---|---|---|---|"] + [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in index]
    (OUT / "drawing-index.md").write_text("\n".join(md) + "\n")
    (OUT / "drawing-index.json").write_text(json.dumps([dict(number=a, title=b, material=c, mass=d) for a, b, c, d in index], indent=1))


if __name__ == "__main__":
    main()
