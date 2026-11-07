"""M8 12 kW turbine on the 8 m tower: drawing set NM8 rev A (doc 37).

    python3 drawings8.py     -> out/NM8-drawing-set.pdf, out/pdf, out/dxf, out/svg, out/png, out/drawing-index.md
    (run model8.py, iso8.py and bom8.py first)

Same drafting library (cad/nacelle_p1/draft.py) and sheet layout as the S6 set (cad/turbine_6kw). Numbers and sizes
are read from the M8 results (analysis/variant_m8/results) and the CAD model (model8.py), so the sheets follow the
sizing. Parts that are unchanged 12 kW parts (NP1-xxx Rev B/C, NY-4xx) keep their own drawings; the Rev D
generator parts get one change sheet (NM8-215) with the stretched section.
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "cad" / "nacelle_p1"))
import model8 as M8  # noqa: E402
from draft import Sheet  # noqa: E402

M6, G, C = M8.M6, M8.G, M8.C
RES = M8.RES
OUT = HERE / "out"
ISO = OUT / "iso"
PROJECT = "12 kW WIND TURBINE M8 (ICELAND) · Ø8.0 m, COLLECTIVE PITCH · 8 m TOWER"
DATE = "2026-11-06"
T8 = M8.T8
TW = T8["towers"][M8.TOWER_KEY]["tower"]
FND = T8["towers"][M8.TOWER_KEY]["foundations"]
HY, GEN, BLD, BPM = M8.HY, M8.GEN, M8.BLD, M8.BPM
SP = json.loads((RES / "spindle_m8.json").read_text())
ROTJ = json.loads((RES / "rotor_m8.json").read_text())
PARTS = {p["pid"]: p for p in json.loads((OUT / "model8-parts.json").read_text())["parts"]}
HEAD = json.loads((OUT / "model8-parts.json").read_text())["head_kg"]


def mass(pid, nd=0):
    m = PARTS.get(pid, {}).get("mass_kg")
    return "–" if m is None else f"{m:.{nd}f} kg"


def S(number, title, material, mass_, scale):
    return Sheet(number, title, material, mass_, scale, rev="A", date=DATE, project=PROJECT)


def title(v, x, y, text, h=3.2):
    v.text((x, y), text, h, "left", "bottom")


def iso(s, pid, x, y, w, h):
    s.iso = getattr(s, "iso", []) + [(ISO / "parts" / f"{pid}.png", x, y, w, h)]


def iso_assy(s, name, x, y, w, h):
    s.iso = getattr(s, "iso", []) + [(ISO / f"{name}.png", x, y, w, h)]


def rot2(p, a_deg):
    a = math.radians(a_deg)
    return (p[0] * math.cos(a) - p[1] * math.sin(a), p[0] * math.sin(a) + p[1] * math.cos(a))


R_ROT = M8.R_ROT


# ======================================================================== NM8-000 GA turbine
def ga_turbine():
    s = S("NM8-000", "GENERAL ARRANGEMENT · 12 kW M8 ON 8 m TOWER", "see BOM NM8-002/003",
          f"≈ {HEAD:.0f} kg head + {TW['mass_kg']:.0f} kg tower", "1:75")
    sc = 1 / 75
    v = s.view("side", sc, (95, 112))
    H = 8000.0
    zb, zt = 200.0, 200.0 + M6.L_TUBE
    db, dt = M6.D_BASE, M6.D_TOP
    v.poly([(-db / 2, zb), (db / 2, zb), (dt / 2, zt), (-dt / 2, zt)])
    yb = zt + 360.0
    hub = (-780.0, H)
    v.poly([(-400, yb - 200), (520, yb - 200), (520, yb + 690), (-400, yb + 1040)])
    v.poly([(hub[0] - 1050, H), (hub[0] - 700, H + 420), (hub[0] - 150, H + 520), (hub[0] + 175, H + 520),
            (hub[0] + 175, H - 520), (hub[0] - 150, H - 520), (hub[0] - 700, H - 420)])
    v.poly([(hub[0] + 200, H - 338), (hub[0] + 490, H - 338), (hub[0] + 490, H + 338), (hub[0] + 200, H + 338)])
    for a in (0.0, 120.0, 240.0):
        z1 = H + R_ROT * math.cos(math.radians(a))
        v.line((hub[0], H + 442 * math.cos(math.radians(a))), (hub[0], z1))
    v.line((-5000, 0), (4500, 0))
    B = FND["firm soil (dense gravel, moraine)"]["B"] * 1000
    v.poly([(-B / 2, -1600), (B / 2, -1600), (B / 2, -1000), (600, -1000), (600, 170), (-600, 170), (-600, -1000), (-B / 2, -1000)], hatch=True)
    v.dim((3000, 0), (3000, H), -4, kind="v", text="8 000 hub height")
    v.dim((hub[0] - 1300, H - R_ROT), (hub[0] - 1300, 0), 4, kind="v", text=f"{H - R_ROT:.0f} lowest tip")
    v.dim((-B / 2, -1600), (B / 2, -1600), -5, kind="h", text=f"{B:.0f} square (firm ground)")
    v.dim((hub[0], H + 600), (0, H + 600), 4, kind="h", text="780 overhang")
    v.leader((dt / 2 + 40, 4000), (1500, 3300), f"tower Ø{db:.0f}→Ø{dt:.0f}, t {TW['geometry']['t_mm'][0]}/{TW['geometry']['t_mm'][1]}, one piece", 2.0)
    v.leader((M6.HINGE["x"], zb + 40), (-4300, 1800), "base hinge NM8-410", 2.0)
    v.leader((0, yb + 300), (1500, 10200), "generator Rev D, NP8-300 bedplate, yaw Dpw 410", 2.0)
    title(v, -5000, 12600, "SIDE VIEW (wind from the left)", 3.0)
    w = s.view("front", sc, (215, 112))
    w.poly([(-db / 2, zb), (db / 2, zb), (dt / 2, zt), (-dt / 2, zt)])
    w.circle((0, H), R_ROT, "PHANTOM")
    b = C.blade_shape(n=20)
    for a in (90.0, 210.0, 330.0):
        up = [rot2((r * 1000, 0.3 * c * 1000), a - 90 + 90) for r, c in zip(b.r, b.chord)]
        lo = [rot2((r * 1000, -0.7 * c * 1000), a - 90 + 90) for r, c in zip(b.r, b.chord)]
        w.poly([(x, y + H) for x, y in up] + [(x, y + H) for x, y in lo[::-1]])
    w.circle((0, H), 520)
    w.line((-4500, 0), (4500, 0))
    w.dim((-R_ROT, H + R_ROT + 300), (R_ROT, H + R_ROT + 300), 3, kind="h", text="Ø8 000 rotor")
    title(w, -2500, 12600, "VIEW FROM UPWIND", 3.0)
    en = T8["energy"]
    s.table = [["Item", "Value"], ["Rated power", "12 kW electric at 10.0 m/s (hub)"],
               ["Rotor", "Ø8.0 m, 3 blades, TSR 5.5, collective pitch"],
               ["Speed", f"{C.RPM_MIN}–{C.RPM:.0f} rpm, trip {C.RPM_TRIP:.0f} rpm"],
               ["Hub height", f"8.0 m; lowest tip {(H - R_ROT) / 1000:.1f} m"],
               ["Tower", f"{TW['mass_kg']:.0f} kg, f1 {TW['f1_rigid_Hz']} Hz ({TW['f1_soft_ice_Hz']} soft+ice)"],
               ["Exclusion zone", f"{TW['exclusion_zone_rpm'][0]:.0f}–{TW['exclusion_zone_rpm'][1]:.0f} rpm (3P × f1)"],
               ["Head mass", f"{HEAD:.0f} kg above the tower flange (CAD)"],
               ["Energy vs 18 m", f"−{en['highland']['loss_pct']:.0f} % highland … −{en['inland']['loss_pct']:.0f} % inland"],
               ["Stopping", "pitch to feather (supercap) + 3 spring calipers 13.1 kNm"],
               ["Storm", "feathered, idling or braked, yaw active"]]
    s.table_pos = (254, 285); s.table_widths = [24, 66]
    iso_assy(s, "A01-turbine", 345, 58, 62, 226)
    s.notes = ["Docs 35 and 37. Shared 12 kW parts keep their drawings (index NM8-001). Generator Rev D change sheet NM8-215.",
               "Keep people and vehicles out of the rotor disc: fenced zone of radius 5 m round the tower base; lowest tip 4.0 m. Ice-fall zone 1.5 × (H + D) = 24 m when icing is possible.",
               "Siting at 8 m: rotor bottom must be clear of the wake of buildings and shelter belts (≥ 20 × obstacle height upwind in the main wind directions); snow drift must stay below 2.5 m."]
    s.notes_top = (14, 52); s.notes_wrap = 100
    return s


# ======================================================================== NM8-001 drawing index
REUSED = [("NP1-101/102", "Front spacer, rear seal sleeve (Rev B)", "12 kW P1 rev B"),
          ("NP1-202", "Stator front clamp ring", "12 kW P1 rev B"),
          ("NP1-211", "Bearing seal covers front / rear", "12 kW P1 rev B"),
          ("NP1-212C", "Drum rear cover with 24 fan blades", "Rev C (doc 23)"),
          ("NP1-230", "Brake disc 16 mm Ø880 / Ø652", "12 kW P1 rev B"),
          ("NP1-310", "Brake caliper brackets 3 and 9 o'clock", "12 kW P1 rev B"),
          ("NP1-320/321", "Rotor lock pin and holder", "12 kW P1 rev B"),
          ("NP1-420", "Yaw drive brackets (radius +30)", "12 kW doc 25"),
          ("NY-400…460", "Adapter, pad units, lock, encoder, cable hanger (radii +25, see NM8-410)", "12 kW doc 25"),
          ("NM8-700/710/720/730", "Nacelle cover, frame, met mast, junction box (S6 parts, cover front 15 mm longer)", "S6 rev B"),
          ("NM8-420", "Gin pole and tilt-up rigging (S6 tool, line pull see NM8-400)", "S6 rev B"),
          ("NM8-600/620/800", "Resistor box, base cabinet, cabling routes (S6)", "S6 rev B")]


def index_sheet(rows):
    s = S("NM8-001", "DRAWING INDEX (NM8 SET REV A + REUSED DRAWINGS)", "–", "–", "–")
    s.table = [["Drawing", "Title", "Source"]] + [r[:3] for r in rows]
    s.table_pos = (14, 285); s.table_widths = [30, 150, 30]
    s.notes = ["Rev A (2026-11-06): first issue for the 12 kW M8 on the 8 m tower (doc 37). Every new or changed part has an axonometric view from the 3D model (cad/turbine_m8/model8.py).",
               "Reused drawings are used unchanged except where this index says otherwise. Their PDFs are in the earlier sets (cad/nacelle_p1, cad/yaw, cad/turbine_6kw).",
               "All sheets NOT CHECKED: prototype release only after review, the open checks of doc 37 §9 and the supplier drawings of the bought parts."]
    s.notes_top = (254, 285); s.notes_wrap = 60
    return s


def bom_sheets(bom):
    out = []
    per = 52
    chunks = [bom[i:i + per] for i in range(0, len(bom), per)]
    for k, ch in enumerate(chunks):
        s = S(f"NM8-00{2 + k}", f"BILL OF MATERIALS ({k + 1}/{len(chunks)})", "see lines", "see lines", "–")
        s.table = [["Pos", "Part no.", "Description", "Qty", "Make/buy", "Material / spec", "kg each"]] + \
            [[r["pos"], r["pid"], r["name"][:62], r["qty"], r["make_buy"], r["material"][:44], r["mass"]] for r in ch]
        s.table_pos = (14, 285); s.table_widths = [10, 24, 112, 12, 16, 84, 16]
        s.notes = ["Masses from the CAD model (cad/turbine_m8/model8.py) for made parts; supplier data or the doc 35 budget for bought and pitch parts. Full BOM: bom8.csv."]
        s.notes_top = (14, 285 - 4.2 * (len(ch) + 1) - 4); s.notes_wrap = 120
        out.append(s)
    return out


# ======================================================================== NM8-010 nacelle assembly
def ga_nacelle():
    s = S("NM8-010", "GENERAL ARRANGEMENT · NACELLE AND DRIVETRAIN", "see BOM", f"≈ {HEAD:.0f} kg above the tower flange", "–")
    iso_assy(s, "A03-nacelle-open", 14, 120, 250, 165)
    iso_assy(s, "A02-head", 268, 150, 140, 135)
    s.table = [["Interface", "Value"],
               ["Rotor plane to yaw axis", "780 mm (doc 35 overhang; 750 + 30 Rev D)"],
               ["Rotor centre above yaw bearing top", "570 mm; shaft tilt 5°"],
               ["Generator Rev D", f"stack {GEN['geometry']['stack_mm']:.0f} mm, {GEN['geometry']['magnet_rows']} rows, {GEN['geometry']['blocks']} blocks, {GEN['geometry']['turns']} turns"],
               ["Stretch plane", "spindle x 410: parts ahead move 30 mm forward"],
               ["Bearings", "2 × 32028 X, span 240 (unchanged)"],
               ["Brake", "3 spring calipers at 0°, 135°, 180° (lock pin at 90°)"],
               ["Bedplate", f"NP8-300, {BPM['mass_kg']:.0f} kg (plate model), util {BPM['util_max']}"],
               ["Yaw", "ring Dpw 410 z165 m4, 2 gearmotors, 2 pad units"],
               ["Hub to drum", "12 × M16 10.9 PCD 400, Ø360 spigot"],
               ["Spindle to bedplate", "12 × M20 10.9 PCD 350, Ø200 spigot"]]
    s.table_pos = (268, 140); s.table_widths = [56, 84]
    s.notes = ["A03: nacelle with the upper cover lid, met mast, spinner and blades removed, seen from the rear left. A02: complete head.",
               "Whole-turbine interference check (cad/turbine_m8/clash8.py): no clashes left except intended fits (spigots, pins in eyes, bolts in tapped holes, embedded anchors, gear mesh contact) - list in doc 37 §6.",
               "The hub, drum, stator and spindle front move 30 mm forward together, so all front interfaces (hub spigot, bearing seats, seal covers) are as drawn on the Rev B/C sheets; only the lengths in NM8-215 change."]
    s.notes_top = (14, 72); s.notes_wrap = 118
    return s


# ======================================================================== NM8-020 rotor assembly
def rotor_ga():
    rot_mass = sum((PARTS[p]["mass_kg"] or 0) for p in PARTS if PARTS[p]["group"] == "rotor")
    s = S("NM8-020", "ROTOR ASSEMBLY · HUB, PITCH SYSTEM, BLADES, SPINNER", "see BOM", f"≈ {rot_mass:.0f} kg", "1:40")
    v = s.view("front", 1 / 40, (110, 165))
    v.circle((0, 0), R_ROT, "PHANTOM")
    b = C.blade_shape(n=24)
    for a in (90.0, 210.0, 330.0):
        up = [rot2((r * 1000, 0.3 * c * 1000), a) for r, c in zip(b.r, b.chord)]
        lo = [rot2((r * 1000, -0.7 * c * 1000), a) for r, c in zip(b.r, b.chord)]
        v.poly(up + lo[::-1])
        v.line(rot2((0, 0), a), rot2((R_ROT + 200, 0), a), "CENTER")
    v.circle((0, 0), 520)
    v.circle((0, 0), 265, "HIDDEN")
    v.dim((-R_ROT, -R_ROT - 250), (R_ROT, -R_ROT - 250), -3, kind="h", text="Ø8 000")
    v.leader(rot2((2500, 0), 90), (1500, 3800), "blade NM8-100 (pitch axis at 30 % chord)", 2.0)
    v.leader((450, 200), (2600, 900), "spinner NM8-210 Ø1 040", 2.0)
    title(v, -4100, 4200, "VIEW FROM UPWIND, blade 1 up, pitch −2°", 3.0)
    iso_assy(s, "A04-rotor", 220, 150, 190, 135)
    st = ROTJ if isinstance(ROTJ, dict) else {}
    s.table = [["Item", "Value"], ["Blades", f"3 × {M8.M_BLADE:.1f} kg, carbon UD caps (D3)"],
               ["Blade root", "Ø280, 12 × M16 inserts PCD 245"],
               ["Pitch bearings", "4-point Dpw 300, balls 30, Z 28"],
               ["Pitch drive", "one electric cylinder, crank r140, collective"],
               ["Hub", f"S355NL weldment {PARTS['NM8-200']['mass_kg']:.0f} kg (budget)"],
               ["Rotor inertia", "≈ 385 kg m²"], ["Pitch range", "−2° (fine) … 92° (feather)"]]
    s.table_pos = (220, 140); s.table_widths = [40, 80]
    s.notes = ["Assembly order (NM8-020 = build book steps 8–10): hub pre-assembled with bearings, cranks, links, yoke, cylinder and nose frame on the bench; mounted on the drum; blades fitted with the cylinder at the −2° end stop; spinner last.",
               "Static-moment matched blade set: moments within 0.5 % (balance by root ballast pocket); mark each blade with its hub position.",
               "Bolt torques NM8-900. Blade root bolts M16 10.9: 280 Nm, re-torque after 50 h."]
    s.notes_top = (220, 98); s.notes_wrap = 70
    return s


# ======================================================================== NM8-100 blade
def blade():
    b = C.blade_shape(n=30)
    s = S("NM8-100", "BLADE Ø8.0 m · PLANFORM, TWIST AND ROOT", "E-glass/epoxy infused; carbon UD caps; PVC core shells", f"{M8.M_BLADE:.1f} kg", "1:20")
    v = s.view("planform", 1 / 20, (40, 200))
    xs = [M8.PB_TOP] + [r * 1000 for r in b.r if r * 1000 > 470]
    def chord(x):
        return M8.ROOT_D if x <= 470 else float(np.interp(x, np.array(b.r) * 1000, np.array(b.chord) * 1000))
    le = [(x, 0.3 * chord(x)) for x in xs]
    te = [(x, -0.7 * chord(x)) for x in xs]
    v.poly(le + te[::-1])
    v.line((M8.PB_TOP - 100, 0), (R_ROT + 100, 0), "CENTER")
    v.text((R_ROT - 900, 60), "pitch axis (30 % chord)", 2.0)
    v.dim((M8.PB_TOP, -600), (R_ROT, -600), -4, kind="h", text=f"{R_ROT - M8.PB_TOP:.0f} blade length (root face r {M8.PB_TOP:.0f})")
    cmax = max(b.chord) * 1000
    rmax = b.r[int(np.argmax(b.chord))] * 1000
    v.dim((rmax, 0.3 * cmax), (rmax, -0.7 * cmax), 30, kind="v", text=f"{cmax:.0f} max chord")
    title(v, M8.PB_TOP, 330, "PLANFORM (suction side up, leading edge up)", 3.0)
    w = s.view("root", 0.4, (60, 95))
    w.circle((0, 0), M8.ROOT_D / 2); w.circle((0, 0), M8.ROOT_D / 2 - 20)
    w.bolt_circle((0, 0), M8.ROOT_PCD, M8.ROOT_N, 16.0, start=15.0)
    w.dim((-M8.ROOT_D / 2, -170), (M8.ROOT_D / 2, -170), -2, kind="h", prefix="Ø", text="280 root")
    w.leader((M8.ROOT_PCD / 2 * math.cos(math.radians(15)), M8.ROOT_PCD / 2 * math.sin(math.radians(15))), (220, 120),
             "12 × M16 inserts NM8-105, PCD 245", 2.0)
    title(w, -180, 175, "ROOT FACE", 3.0)
    rows = [["r mm", "chord mm", "twist °", "t/c"]]
    for r in (0.45, 0.6, 0.8, 1.0, 1.4, 1.8, 2.2, 2.6, 3.0, 3.4, 3.8, 4.0):
        rows.append([f"{r * 1000:.0f}", f"{chord(r * 1000):.0f}",
                     f"{float(np.interp(r, b.r, b.twist + b.twist_tip_offset)):.1f}", f"{M8._tc(r):.2f}"])
    s.table = rows; s.table_pos = (250, 160); s.table_widths = [18, 20, 18, 16]
    iso(s, "NM8-100-1", 120, 30, 120, 80)
    lam = BLD["carbon"]
    s.notes = ["Twist relative to the pitch reference at −2° setting (blade at its fine end stop). Aerofoil family as doc 10, thickness scaled to the 4.0 m span (structure_m8.py).",
               f"Laminate: doc 10 construction scaled; carbon UD caps sized by buckling. Mass {lam['mass_kg']:.1f} kg; flap frequency ≈ 18.8 Hz at rated (3P 6.6 Hz).",
               "Root: 12 bonded inserts M16 on PCD 245 (bolt force 64 kN design, F_t,Rd 113 kN). Root face machined flat 0.1 after cure, square to the pitch axis 0.1°.",
               "First-article static test SLM H × 1.35 flap, edge test, insert pull-out (3 per batch). Balance set to 0.5 % static moment."]
    s.notes_top = (250, 100); s.notes_wrap = 70
    return s


def root_insert():
    s = S("NM8-105", "BLADE ROOT INSERT M16 (BONDED)", "C45E+QT, zinc-flake coated (Geomet 500)", "0.78 kg", "2:1")
    v = s.view("section", 2.0, (80, 170))
    k = 4.0 / 3.0
    p = [(0, 6.0), (0, 12.0)]
    x = 0.0
    for _ in range(6):
        p += [(x + 8, 12.0), (x + 8, 10.5), (x + 13, 10.5), (x + 13, 12.0)]
        x += 13
    p += [(110, 12.0), (110, 0.0), (30, 0.0), (30, 5.1), (0, 5.1)]
    pts = [(a * k, r * k) for a, r in [(0.0, 5.1), (0.0, 12.0)] + p[2:-1]]
    v.poly(pts, hatch=True)
    v.poly([(a, -r) for a, r in pts], hatch=False)
    v.line((-10, 0), (160, 0), "CENTER")
    v.dim((0, -20), (110 * k, -20), -4, kind="h", text=f"{110 * k:.0f}")
    v.dim((110 * k + 8, 16), (110 * k + 8, -16), 4, kind="v", prefix="Ø", text="32")
    v.dim((0, 22), (30 * k, 22), 3, kind="h", text="M16 × 40 thread")
    title(v, 0, 35, "SECTION (6 bond grooves)", 3.0)
    iso(s, "NM8-105", 270, 150, 120, 110)
    s.notes = ["The doc 34 M12 insert scaled 4/3: Ø32 × 147, internal M16-6H 40 deep, 6 grooves 2 deep for the bond.",
               "Bonded into the root laminate with the NM8-115 fixture (12 spigots on PCD 245, as NS6-115 with the M8 pattern).",
               "Pull-out test 3 per batch to 1.5 × 64 kN; thread gauge every insert."]
    s.notes_top = (14, 80)
    return s


def mould():
    s = S("NM8-110", "BLADE MOULD SET (PLUG, TWO HALVES, FRAME)", "GRP tooling laminate on S235 RHS frame", "≈ 2 × 118 kg + frame 179 kg", "–")
    iso_assy(s, "A07-mould", 14, 120, 300, 165)
    s.notes = ["Same construction as NS6-110 (doc 34), lengthened for the 3.56 m M8 blade: CNC-machined plug from the NM8-100 surfaces, GRP halves 12 mm with vinylester tooling gelcoat, steel frame RHS 80 × 80 × 4.",
               "Parting line on the leading/trailing edge; root end with the NM8-115 insert fixture flange; 6 locating cones.",
               "Mould acceptance: blade profile within 0.5 mm of the plug at 10 stations; twist within 0.2°."]
    s.notes_top = (14, 100)
    return s


# ======================================================================== NM8-200 hub
def hub():
    H = M8.HM.M.HUB
    s = S("NM8-200", "HUB WELDMENT (COLLECTIVE PITCH)", "S355NL, welded, stress relieved, machined", f"{PARTS['NM8-200']['mass_kg']:.0f} kg (budget)", "1:8")
    v = s.view("front", 1 / 8, (90, 185))
    v.circle((0, 0), H["shell_r"][1]); v.circle((0, 0), H["shell_r"][0], "HIDDEN")
    v.circle((0, 0), H["front"]["r"][0])
    v.bolt_circle((0, 0), 450, 12, 13.0, start=15.0)
    for a in M8.M6.BLADE_ANGLES:
        v.poly([rot2((H["neck_s"][0], -H["neck_r"][1]), a - 90 + 90), rot2((H["neck_s"][1], -H["neck_r"][1]), a),
                rot2((H["neck_s"][1], H["neck_r"][1]), a), rot2((H["neck_s"][0], H["neck_r"][1]), a)])
        v.poly([rot2((H["flange"]["s"][0], -H["flange"]["r"][1]), a), rot2((H["flange"]["s"][1], -H["flange"]["r"][1]), a),
                rot2((H["flange"]["s"][1], H["flange"]["r"][1]), a), rot2((H["flange"]["s"][0], H["flange"]["r"][1]), a)], hatch=True)
        v.line(rot2((100, 0), a), rot2((460, 0), a), "CENTER")
    v.dim((-265, -330), (265, -330), -3, kind="h", prefix="Ø", text="530 × 10 shell")
    v.dim((0, 0), (0, 385), -30, kind="v", text="385 neck face")
    title(v, -300, 470, "VIEW FROM UPWIND (spinner and nose frame removed)", 3.0)
    w = s.view("section", 1 / 8, (250, 185))
    x0, x1 = H["shell_x"]
    ri, ro = H["shell_r"]
    for sg in (1, -1):
        w.poly([(x0, sg * ri), (x1, sg * ri), (x1, sg * ro), (x0, sg * ro)], hatch=True)
        rx0, rx1 = H["rear"]["x"]; r0, r1 = H["rear"]["r"]
        w.poly([(rx0, sg * r0), (rx1, sg * r0), (rx1, sg * r1), (rx0, sg * r1)], hatch=True)
        fx0, fx1 = H["front"]["x"]; f0, f1 = H["front"]["r"]
        w.poly([(fx0, sg * f0), (fx1, sg * f0), (fx1, sg * f1), (fx0, sg * f1)], hatch=True)
    w.poly([(-180, 265), (-170, 265), (-170, 360), (-180, 360)], hatch=True)
    w.poly([(170, 265), (180, 265), (180, 360), (170, 360)], hatch=True)
    w.poly([(-215, 360), (-156, 360), (-156, 385), (-215, 385)], hatch=True)
    w.poly([(156, 360), (215, 360), (215, 385), (156, 385)], hatch=True)
    w.line((-320, 0), (240, 0), "CENTER"); w.line((0, -300), (0, 440), "CENTER")
    w.dim((x0, -ro), (H["rear"]["x"][1], -ro), -14, kind="h", text=f"{H['rear']['x'][1] - x0:.0f}")
    w.dim((-215, 385), (215, 385), 6, kind="h", prefix="Ø", text="430 neck flange × 25")
    w.leader((200, -200), (260, -320), "Ø361 H7 × 5 spigot recess, 12 × Ø17 PCD 400", 2.0)
    w.leader((-282, 220), (-420, 380), "front ring r 190–265 × 12, 12 × M12 PCD 450 (nose frame)", 2.0)
    title(w, -330, 470, "SECTION THROUGH BLADE 1 AXIS", 3.0)
    wh = HY["welded_hub"]["neck_checks"]
    ok = next(c for c in wh if c["d_neck_mm"] == 360 and c["t_mm"] == 10.0)
    s.notes = [f"Necks Ø360 × 10 on the Ø530 × 10 shell: parked SLM stress {ok['static_MPa']} MPa (allow {ok['static_allow']}); fatigue {ok['fat_MPa']} MPa (allow {ok['fat_allow']}).",
               "Neck flanges Ø430 × 25 carry the pitch bearing outer rings: 20 × M16 tapped on PCD 360; faces machined after stress relief, flat 0.05, square to the neck axis 0.05.",
               "Rear gussets stop on the drum flange ring (x 200) so they clear the drum web; front gussets 68 long. Full penetration welds ISO 5817 B, 100 % MT, UT on neck welds.",
               "Drum joint as Rev C: Ø360 spigot, 12 × M16 10.9 PCD 400, 280 Nm. FE check of the neck-to-shell weld before release (doc 37 §9)."]
    s.notes_top = (14, 72)
    iso(s, "NM8-200", 315, 50, 92, 72)
    return s


def pitch_sheet():
    co = HY["collective"]["options"]["crank_r140"]
    pb = HY["pitch_bearing"]
    s = S("NM8-250", "COLLECTIVE PITCH · BEARINGS, CRANKS, LINKS, YOKE, CYLINDER", "see BOM", "≈ 140 kg pitch parts (budget)", "1:5")
    v = s.view("kinematics", 0.2, (120, 190))
    v.line((-450, 0), (300, 0), "CENTER"); v.line((0, -50), (0, 480), "CENTER")
    v.poly([(-205, 385), (205, 385), (205, 440), (-205, 440)], hatch=True)
    v.poly([(-147.5, 387), (147.5, 387), (147.5, 442), (-147.5, 442)])
    v.poly([(-140, 442), (140, 442), (140, 480), (-140, 480)], layer="PHANTOM")
    v.poly([(176, 100), (196, 100), (196, 150), (176, 150)], hatch=True)
    v.circle((186, 150), 15)
    v.line((186, 150), (-180, 140))
    v.circle((-180, 140), 12)
    v.poly([(-190, -40), (-170, -40), (-170, 160), (-190, 160)])
    v.dim((0, 150), (186, 150), 20, kind="h", text="r 140 crank (pin plane 150 from the rotor axis)")
    v.leader((-180, 140), (-430, 330), "yoke eye R 140, link 220, phase 5°", 2.0)
    v.leader((205, 420), (300, 470), "pitch bearing Dpw 300 (outer ring on the hub neck)", 2.0)
    title(v, -450, 520, "BLADE 1 PLANE, PITCH −2° (schematic)", 3.0)
    iso_assy(s, "A08-hub-pitch", 250, 150, 160, 135)
    s.table = [["Pitch system (hub_yaw_m8, crank r140)", "Value"],
               ["Cylinder stroke", f"{co['stroke_mm']:.0f} mm"], ["Force at trip (design)", f"{co['F_trip_design_kN']} kN"],
               ["Rated force", f"{co['F_rated_kN']} kN"], ["Motor peak torque", f"{co['motor_T_peak_Nm']} Nm"],
               ["Energy per feather stroke", f"{co['E_stroke_kJ']} kJ"], ["Strokes from one module (EOL)", f"{co['strokes_EOL_one_module']}"],
               ["Storm hold force on screw", f"{co['F_storm_on_screw_kN']} kN"], ["Motor brake needed", f"{co['motor_brake_needed_Nm']} Nm"],
               ["Pitch bearing", f"Dpw {pb['chosen']['Dpw'] * 1000:.0f}, balls {pb['chosen']['Dw'] * 1000:.0f}, Z {pb['chosen']['Z']}"],
               ["Bearing s0 (SLM H)", f"{pb['chosen']['s0']['SLM H parked flap']}"], ["Clash check", "clean at −2, 10, 30, 45, 60, 80, 92°"]]
    s.table_pos = (14, 120); s.table_widths = [62, 40]
    s.notes = ["Kinematics from analysis/hub/collective.py with R_C 140, S_P 150, R_Y 140, L 220, phase 5° (cad/hub_m8/model_m8.py). The pin plane was moved out from 118 to 150 so the crank pin clears the drum bearing housing (r ≤ 120).",
               "Bearings: 4-point ungeared, 20 × M16 outer to the neck flange (PCD 360), 12 × M16 inner to the blade root (PCD 245). Grease, sealed, −40 °C grease.",
               "Cylinder ≈ 28.5 kN rated, 204 mm stroke, motor brake ≥ 14.2 Nm; supercap module sized for 3.6 feather strokes at end of life; nose frame carries both.",
               "Mechanical end stops at −2.5° and 93° on crank 1; limit switches at −2° and 92°."]
    s.notes_top = (120, 62); s.notes_wrap = 95
    return s


def spinner_sheet():
    s = S("NM8-210", "SPINNER (GRP) WITH BLADE BOOTS", "glass/polyester 4 mm, gelcoat RAL 9010", mass("NM8-210", 1), "1:10")
    v = s.view("half section", 0.1, (150, 160))
    x0, xm, xb, R = -1050.0, -150.0, 175.0, 520.0
    prof = [(x0, 0.0)] + [(x0 + (xm - x0) * k / 24, R * math.sqrt(max(0.0, 1 - (1 - k / 24) ** 2))) for k in range(1, 25)] + [(xb, R)]
    v.poly(prof, closed=False)
    v.poly([(x, -r) for x, r in prof], closed=False, layer="THIN")
    v.line((x0 - 50, 0), (xb + 100, 0), "CENTER")
    v.line((0, -600), (0, 650), "CENTER")
    v.dim((x0, -620), (xb, -620), -3, kind="h", text=f"{xb - x0:.0f}")
    v.dim((xb + 60, R), (xb + 60, -R), 4, kind="v", prefix="Ø", text=f"{2 * R:.0f}")
    v.leader((0, R), (300, 700), "3 openings Ø320 round the blade roots, rubber boots", 2.0)
    title(v, x0, 700, "HALF SECTION / VIEW", 3.0)
    iso(s, "NM8-210", 280, 140, 125, 120)
    s.notes = ["Ogive nose to r 520 at x −150, cylindrical to the base ring at x 175 (spindle frame, rotor plane x 0). 4 mm glass/polyester, 3 split segments with flanged joints.",
               "Encloses the pitch bearings (outer edge r 485), the nose frame and the cylinder; inspection hatch Ø200 at the nose for the slip ring and the pitch electronics.",
               "Fixed to the hub front ring and neck flanges with 9 brackets (A4 M8), 10 mm clearance to all moving pitch parts."]
    s.notes_top = (14, 70)
    return s


# ======================================================================== NM8-215 generator Rev D change sheet
def stretch_x(x):
    return x + 30.0 if x >= M8.X_CUT else x


def rev_d():
    s = S("NM8-215", "GENERATOR REV D · CHANGE SHEET (STACK 74 → 104 mm)", "as Rev C sheets", f"{GEN['mass_kg']['total']['M8']:.0f} kg generator", "1:4")
    v = s.view("section", 0.25, (60, 150))
    def draw(poly, hatch=True, sg=1):
        v.poly([(stretch_x(x), sg * r) for x, r in poly], hatch=hatch)
    sp = [(x, r) for x, r in G.SPINDLE_OUTER]
    draw(sp + [(sp[-1][0], G.SPINDLE_BORE_R), (sp[0][0], G.SPINDLE_BORE_R)])
    for nm, poly in G.DRUM_PARTS.items():
        draw(poly)
    draw(G.CARRIER); draw(G.STACK_POLY, hatch=False); draw(G.STATOR_RING); draw(G.DISC_POLY); draw(G.REAR_COVER)
    v.line((0, 0), (520, 0), "CENTER")
    v.line((stretch_x(M8.X_CUT), 0), (stretch_x(M8.X_CUT), 380), "PHANTOM")
    v.line((M8.X_CUT, 0), (M8.X_CUT, 380), "PHANTOM")
    v.text((M8.X_CUT - 10, 385), "+30 stretch", 2.2)
    x0s, x1s = G.X_STACK
    v.dim((x0s, G.GEN["r_s"] + 40), (stretch_x(x1s), G.GEN["r_s"] + 40), 6, kind="h", text=f"{stretch_x(x1s) - x0s:.0f} stack (Rev C 74)")
    v.dim((G.X_BRG_FRONT, -30), (G.X_BRG_REAR, -30), -4, kind="h", text="240 bearing span (unchanged)")
    v.dim((0, -60), (stretch_x(430.0), -60), -8, kind="h", text="460 flange fillet")
    title(v, 0, 430, "UPPER HALF SECTION, Rev D lengths (rotor plane x 0)", 3.0)
    gg = GEN["geometry"]; ge = GEN["electrical"]
    s.table = [["Part", "Rev C", "Rev D"],
               ["NP1-100D spindle", "x 40–476", "x 40–506 (Ø150 section 400–460)"],
               ["NP1-200D stator carrier", "rim 74", "rim 104, web unchanged"],
               ["NP1-201D stator", "5 rows, 74 mm", f"{gg['magnet_rows']} rows, {gg['stack_mm']:.0f} mm"],
               ["NP1-203D coils", "28 turns", f"{gg['turns']} turns, longer side (turn +60 mm)"],
               ["NP1-210D drum", "shell 239", "shell 269; fins/ribs as Rev C"],
               ["NP1-220F magnets", "200 blocks", f"{gg['blocks']} blocks (+{gg['spares']} spare)"],
               ["Torque rated", f"{ge['torque_RevC_Nm']} Nm", f"{ge['torque_rated_Nm']} Nm"],
               ["Line EMF 100 °C", f"{ge['line_emf_RevC_100C_V']} V", f"{ge['line_emf_100C_V']} V"],
               ["Efficiency rated", f"{GEN['efficiency_rated']['RevC']}", f"{GEN['efficiency_rated']['M8']}"],
               ["Drum stability margin", f"{GEN['drum_stability_margin']['L_shell_239mm']}", f"{GEN['drum_stability_margin']['L_shell_269mm']}"]]
    s.table_pos = (220, 285); s.table_widths = [46, 40, 104]
    iso(s, "NP1-210D", 250, 60, 80, 70)
    iso(s, "NP1-100D", 330, 60, 80, 70)
    s.notes = ["All Rev C drawings stay valid with the lengths of this sheet: every feature ahead of spindle x 410 keeps its Rev C distance to the rotor plane, every feature behind x 410 moves 30 mm aft (bedplate, disc, calipers, rear cover).",
               f"Spindle check with Rev D lengths and M8 loads: static reserve {SP['spindle']['static_reserve_min']}, bearings s0 {SP['bearings']['s0_front']} / {SP['bearings']['s0_rear']}, life factor {SP['bearings']['life_factor'][0]} (spindle_m8.py).",
               "Cooling as Rev C (36 inner fins, 48 outer ribs, 24 cover blades); hot spot 117 °C at 110 % (generator_m8_cooling.json). Fins and ribs are not in the 3D model.",
               f"Magnet comb and sleeve lengthened by 30; skew step {GEN['geometry']['skew_step_deg']}° between the 7 rows (±0.43°)."]
    s.notes_top = (14, 72)
    return s


# ======================================================================== NM8-311 brake
def brake_sheet():
    bk = SP["brake"]
    s = S("NM8-311", "ROTOR BRAKE · THREE CALIPERS AND THIRD CALIPER BRACKET", "bracket S355J2+N 25 plate, welded", f"bracket {mass('NM8-311', 1)}", "1:8")
    v = s.view("view from rear", 1 / 8, (110, 160))
    v.circle((0, 0), G.DISC["od"] / 2); v.circle((0, 0), G.DISC["id"] / 2)
    v.circle((0, 0), G.LOCK["pcd"] / 2, "CENTER")
    for a, nm in ((0.0, "left (NP1-310)"), (180.0, "right (NP1-310)"), (M8.A_TOP, "third (NM8-311)")):
        r0, r1 = FP_r = (G.DISC["pad_r"][0] - 15.0, G.DISC["pad_r"][0] + 115.0)
        v.poly([rot2((r0, -90), a), rot2((r1, -90), a), rot2((r1, 90), a), rot2((r0, 90), a)], hatch=True)
        v.text(rot2((r1 + 40, 0), a), nm, 2.0, ha="center")
    v.poly([rot2((355, -15), 90), rot2((385, -15), 90), rot2((385, 15), 90), rot2((355, 15), 90)])
    v.text(rot2((470, 0), 90), "rotor lock pin (90°)", 2.0, ha="center")
    v.poly([(-250, -260), (250, -260), (250, 230), (-250, 230)], layer="PHANTOM")
    v.text((-240, 240), "bedplate front plate (rear face)", 2.0)
    title(v, -560, 600, "VIEW FROM THE REAR (downwind), angles from +y towards +z", 3.0)
    iso(s, "NM8-311", 260, 150, 70, 70)
    iso(s, "NM8-915-T", 335, 150, 70, 70)
    s.table = [["Brake (spindle_m8 / hub_yaw_m8)", "Value"], ["Required holding torque", f"{HY['rotor_brake']['brake_M8_kNm']} kNm (1.41 × doc 07)"],
               ["Calipers", "3 × spring-applied, 4.4 kNm each"], ["Clamp force per caliper", f"{bk.get('clamp_per_caliper_kN', 14.8)} kN at μ 0.40, r_eff 0.41"],
               ["Parked aero torque (sim, char.)", f"{HY['rotor_brake']['parked_aero_torque_sim_char_kNm']} kNm"],
               ["Disc", "NP1-230 Rev B, 16 mm, unchanged"]]
    s.table_pos = (260, 72); s.table_widths = [60, 86]
    s.notes = ["The third caliper sits at 135° (upper right seen from the rear) because the rotor lock pin holder occupies 90°. It uses the same caliper and mounting plate as NP1-310 (4 × M16 axial).",
               "Bracket: 25 mm mounting plate + 25 mm web + 25 mm foot, bolted 4 × M16 10.9 through the bedplate front plate outside the spindle flange bolts (r ≥ 205). Weld a5, MT 100 %.",
               "Alternative (decision D2 of doc 35): two calipers with a stronger spring pack (6.6 kNm each) in the existing positions; the third bracket then goes."]
    s.notes_top = (14, 72); s.notes_wrap = 110
    return s


# ======================================================================== NP8-300 bedplate
def bedplate():
    B = BPM["inputs"]
    s = S("NP8-300", "BEDPLATE WELDMENT 12 kW NP8 (LIGHT)", "S355J2+N plates, stress relieved, machined", f"{BPM['mass_kg']:.0f} kg (plate model), {mass('NP8-300')} CAD", "1:8")
    v = s.view("side", 1 / 8, (120, 175))
    v.poly([tuple(p) for p in M8.M6.BPJ["side_poly"]], hatch=False)
    v.line((-450, 0), (300, 0), "CENTER")
    v.line((0, -60), (0, 400), "CENTER")
    v.text((5, 380), "yaw axis", 2.0)
    v.dim((B["x_bot_front"], -40), (B["x_rear"], -40), -3, kind="h", text=f"{B['x_rear'] - B['x_bot_front']:.0f} bottom plate")
    title(v, -500, 450, "SIDE VIEW (front to the left)", 3.0)
    w = s.view("plan", 1 / 8, (120, 70))
    w.poly([(B["x_bot_front"], -B["width"] / 2), (B["x_rear"], -B["width"] / 2), (B["x_rear"], B["width"] / 2), (B["x_bot_front"], B["width"] / 2)])
    w.bolt_circle((0, 0), G.YAW["inner"]["pcd"], 16, 18.0, start=11.25)
    w.circle((0, 0), 135.0)
    w.dim((B["x_bot_front"], -B["width"] / 2 - 40), (B["x_rear"], -B["width"] / 2 - 40), -2, kind="h", text=f"{B['x_rear'] - B['x_bot_front']:.0f}")
    w.dim((B["x_rear"] + 40, -B["width"] / 2), (B["x_rear"] + 40, B["width"] / 2), 2, kind="v", text=f"{B['width']:.0f}")
    w.leader((G.YAW["inner"]["pcd"] / 2, 0), (300, 330), "16 × Ø18 PCD 350 (yaw inner ring), bore Ø270", 2.0)
    title(w, -500, 330, "PLAN OF THE BOTTOM PLATE", 3.0)
    ck = BPM["checks"]
    s.table = [["Plate", "t mm", "kg"], ["Front plate", f"{B['t_front']:.0f}", f"{BPM['masses_kg']['front plate']}"],
               ["Bottom plate (yaw flange)", f"{B['t_bottom']:.0f}", f"{BPM['masses_kg']['bottom plate (yaw flange)']}"],
               ["Side plates (2)", f"{B['t_side']:.0f}", f"{BPM['masses_kg']['side plates']}"],
               ["Check", "util", ""], ["Root section", f"{ck['root_section']['util']}", ""], ["Front plate", f"{ck['front_plate']['util']}", ""],
               ["Bottom plate", f"{ck['bottom_plate']['util']}", ""], ["Yaw bolts", f"{ck['yaw_bolts']['util']}", ""],
               ["Fatigue root", f"{ck['fatigue_root']['util']}", ""]]
    s.table_pos = (260, 285); s.table_widths = [50, 18, 18]
    iso(s, "NP8-300", 260, 50, 145, 120)
    s.notes = ["NS6-300 geometry (doc 32) with the M8 plate thicknesses from bedplate_m8.py (decision D1): front 20, bottom 30, sides 10. Interfaces as NP1-300: spindle flange 12 × M20 PCD 350 + Ø200 spigot, pad unit and gearmotor brackets.",
               "Changed for the Dpw 410 yaw ring: 16 × Ø18 on PCD 350 (was 300), central bore Ø270, pad unit bracket holes 25 mm further out. Third caliper bracket NM8-311 bolts through the front plate (4 × Ø17).",
               "Stress relieve before machining; spigot bore and the yaw face machined in one set-up (parallel 0.05, square 0.05)."]
    s.notes_top = (14, 30); s.notes_wrap = 120
    return s


# ======================================================================== NM8-410 yaw layout (Dpw 410)
def yaw_sheet():
    y = HY["yaw"]
    s = S("NM8-911", "YAW SYSTEM LAYOUT · SLEWING RING Dpw 410", "ring bought; NY parts per doc 25", "ring ≈ 66 kg", "1:8")
    v = s.view("plan", 1 / 8, (120, 160))
    Y = G.YAW
    v.circle((0, 0), Y["d_pw"] / 2, "CENTER")
    v.circle((0, 0), Y["inner"]["id"] / 2); v.circle((0, 0), Y["outer"]["id"] / 2, "HIDDEN")
    v.circle((0, 0), 165 * 4 / 2 + 4)
    v.bolt_circle((0, 0), Y["inner"]["pcd"], 16, 16.0, start=11.25)
    v.bolt_circle((0, 0), Y["outer"]["pcd"], 16, 16.0, layer="HIDDEN")
    for a in (90.0, -90.0):
        c = rot2((M8.FP.YAW_DRIVE["r"], 0), a)
        v.circle(c, 28 * 2); v.text((c[0] + 70, c[1]), "gearmotor", 2.0)
    for a in M8.YM.PADU["angles"]:
        u0, u1 = M8.YM.PADU["bracket"]["u"]
        v.poly([rot2((u0, -85), a), rot2((u1, -85), a), rot2((u1, 85), a), rot2((u0, 85), a)], hatch=True)
    a = M8.YM.LOCK["angle"]; u0, u1 = M8.YM.LOCK["housing"]["u"]
    v.poly([rot2((u0, -50), a), rot2((u1, -50), a), rot2((u1, 50), a), rot2((u0, 50), a)])
    v.text(rot2((u1 + 30, 0), a), "lock NY-430", 2.0)
    e = rot2((M8.YM.ENC["r"], 0), M8.YM.ENC["angle"]); v.circle(e, 48); v.text((e[0] + 60, e[1]), "encoder NY-440", 2.0)
    v.dim((-Y["d_pw"] / 2, -560), (Y["d_pw"] / 2, -560), -2, kind="h", text="Dpw 410")
    title(v, -560, 600, "PLAN (X downwind to the right), bedplate removed", 3.0)
    s.table = [["Yaw (hub_yaw_m8)", "Value"], ["Ring", f"Dpw {y['ring_chosen']['Dpw_mm']}, gear z165 m4, face {y['ring_chosen']['gear_face_mm']:.0f}"],
               ["s0 (SLM H + shaft moment)", f"{y['ring_chosen']['s0_min']} (Dpw 360: {y['ring_s0_Dpw360']['SLM H parked thrust + SLM shaft moment (gamma 3.0)']})"],
               ["Tilt moment design", f"{max(y['M_tilt_kNm'].values())} kNm"],
               ["Gearbox static need", f"{y['gearbox_static_needed_Nm']} Nm"],
               ["Gear static S_F pinion / ring", f"{y['gear_static_S_F']['pinion']} / {y['gear_static_S_F']['ring']}"],
               ["Gear static S_H pinion / ring", f"{y['gear_static_S_H']['pinion']} / {y['gear_static_S_H']['ring']}"],
               ["Inner ring bolts", "16 × M16 10.9 PCD 350 (bedplate)"], ["Outer ring bolts", "16 × M16 10.9 PCD 490 (adapter NY-400)"]]
    s.table_pos = (250, 285); s.table_widths = [54, 100]
    iso(s, "NY-400", 250, 50, 75, 80); iso(s, "NM8-911-O", 330, 50, 75, 80)
    s.notes = ["Doc 25 yaw system with the ring one size up (Dpw 360 fails s0 0.95 under the M8 SLM). Every radial NY dimension moves out 25 mm: adapter seat r 150–275, friction track r 275–420, pad units, lock and encoder.",
               "Gearmotor centre r 358 (pinion z14 m4 on z165); NP1-420 brackets moved out 30 mm. Gearbox output ≥ 2.3 kNm static, motor brake on the input.",
               "Ring bolt circles are preliminary: the supplier drawing of the chosen ring replaces this sheet's PCDs and hole sizes; bolt checks in hub_yaw_m8 used the Dpw 360 PCDs and are conservative."]
    s.notes_top = (14, 50); s.notes_wrap = 110
    return s


# ======================================================================== NM8-400 tower
def tower():
    s = S("NM8-400", "TOWER 8 m · ONE-PIECE TILT-UP MONOPOLE", "S355J2+N, rolled and seam welded; hot-dip galvanised",
          f"{TW['mass_kg']:.0f} kg (sizing), {mass('NM8-400')} CAD", "1:40")
    v = s.view("elevation", 1 / 40, (90, 30))
    db, dt, L = M6.D_BASE, M6.D_TOP, M6.L_TUBE
    v.poly([(-db / 2, 0), (db / 2, 0), (dt / 2, L), (-dt / 2, L)])
    v.poly([(-M6.FL_BASE["od"] / 2, 0), (M6.FL_BASE["od"] / 2, 0), (M6.FL_BASE["od"] / 2, 35), (-M6.FL_BASE["od"] / 2, 35)], hatch=True)
    v.poly([(-210, L - 30), (210, L - 30), (210, L), (-210, L)], hatch=True)
    v.line((0, -100), (0, L + 200), "CENTER")
    v.line((-(db + dt) / 4 - 30, L / 2), ((db + dt) / 4 + 30, L / 2), "THIN")
    v.poly([(-75, 550), (75, 550), (75, 850), (-75, 850)])
    v.dim((900, 0), (900, L), 6, kind="v", text=f"{L:.0f}")
    v.dim((-db / 2, -150), (db / 2, -150), -2, kind="h", prefix="Ø", text=f"{db:.0f} × {TW['geometry']['t_mm'][0]}")
    v.dim((-dt / 2, L + 150), (dt / 2, L + 150), 2, kind="h", prefix="Ø", text=f"{dt:.0f} × {TW['geometry']['t_mm'][-1]}")
    v.leader((75, 700), (900, 1500), "hand hole 150 × 300, frame 15", 2.0)
    v.leader((-db / 2 - 160, 40), (-1800, 900), "hinge lugs (pin Ø50) NM8-410", 2.0)
    v.leader(((db + dt) / 4, L / 2), (900, L / 2 + 800), "can joint: butt weld, full penetration", 2.0)
    title(v, -1800, L + 400, "ELEVATION", 3.0)
    bf = TW["base_flange"]
    fd = TW["fatigue_damage"]
    s.table = [["Tower (tower8_m8, " + M8.TOWER_KEY + ")", "Value"], ["Mass", f"{TW['mass_kg']:.0f} kg"],
               ["f1 rigid / soft soil + ice", f"{TW['f1_rigid_Hz']} / {TW['f1_soft_ice_Hz']} Hz"],
               ["f2", f"{TW['f2_rigid_Hz']} Hz"], ["3P exclusion zone", f"{TW['exclusion_zone_rpm'][0]:.0f}–{TW['exclusion_zone_rpm'][1]:.0f} rpm"],
               ["Utilisation (governing)", f"{TW['util_max']} ({TW['governing']})"],
               ["Fatigue damage base / mid", " / ".join(f"{v_:.2f}" for v_ in fd.values())],
               ["Base flange", f"{bf['bolts']} × {bf['size']} on Ø{bf['circle_m'] * 1000:.0f}, F_bolt {bf['F_bolt_kN']} kN (F_t,Rd {bf['F_t_Rd_kN']})"],
               ["Top flange", "Ø420 × 30, 16 × M20 PCD 380 to NY-400"],
               ["Tilt-up base moment", f"{TW['tilt_up_base_moment_kNm']} kNm, line pull {TW['winch_line_pull_kN_ginpole_033H']} kN"],
               ["D/t max", f"{TW['D_over_t_max']}"]]
    s.table_pos = (200, 285); s.table_widths = [60, 140]
    iso_assy(s, "A05-tower-base", 200, 50, 100, 120); iso_assy(s, "A06-tilt-up", 300, 50, 108, 120)
    s.notes = ["Stiff tower: f1 above 1.15 × 1P at 131 rpm (2.51 Hz) and below 3P/1.1 at rated (5.95 Hz). The controller passes the 3P crossing zone under torque at start-up (no dwell).",
               "Shell plates EN 10025-2 S355J2+N, 3.1 certificates; longitudinal and circumferential welds full penetration, UT 100 %; flanges flat 0.2 after galvanising.",
               "Base flange on 30 mm non-shrink grout; nuts M24 tensioned per NM8-900."]
    s.notes_top = (200, 168); s.notes_wrap = 95
    return s


def hinge_sheet():
    s = S("NM8-410", "BASE HINGE, GIN POLE INTERFACE AND ERECTION", "S355J2+N 30 mm plate, galv.; pin 42CrMo4+QT Ø50 h9", mass("NM8-410"), "–")
    iso(s, "NM8-410", 14, 150, 130, 130)
    iso(s, "NM8-420", 150, 150, 130, 130)
    iso_assy(s, "A06-tilt-up", 280, 150, 128, 130)
    s.table = [["Erection (tower8_m8)", "Value"], ["Tilt-up base moment", f"{TW['tilt_up_base_moment_kNm']} kNm"],
               ["Winch line pull (gin pole 0.33 H)", f"{TW['winch_line_pull_kN_ginpole_033H']} kN"],
               ["Tower utilisation in tilt-up", f"{TW['util_tilt_up']}"], ["Hinge pin", "Ø50 h9, 42CrMo4+QT, double shear"],
               ["Gin pole", "Ø168.3 × 6.3, 3.0 m (S6 tool NS6-420)"]]
    s.table_pos = (14, 140); s.table_widths = [62, 80]
    s.notes = ["The S6 hinge and gin pole (doc 34) carry the M8 head: line pull rises with the 1.39 t head; use a 10 t winch with a 2-part line (≈ 32 kN on the drum) or a 5 t winch with a 4-part line.",
               "Hinge brackets on 4 × M24 anchors in the pedestal; pin greased, secured by R-clips; tower lies on a trestle at 2.5 m during head mounting.",
               "No one inside the fall zone (1.5 × tower height) while lifting; wind below 8 m/s; tag lines on two blade tips."]
    s.notes_top = (160, 140); s.notes_wrap = 95
    return s


def foundation():
    s = S("NM8-500", "FOUNDATION · SPREAD FOOTING (8 m TOWER, M8)", "C30/37 XF4 air-entrained; B500C rebar", f"{FND['firm soil (dense gravel, moraine)']['concrete_m3']}–{FND['soft volcanic soil (loose ash, pumice sand)']['concrete_m3']} m³", "1:40")
    f = FND["firm soil (dense gravel, moraine)"]
    B, d = f["B"] * 1000, f["depth"] * 1000
    v = s.view("section", 1 / 40, (110, 170))
    v.poly([(-B / 2, -d), (B / 2, -d), (B / 2, -d + 600), (600, -d + 600), (600, 170), (-600, 170), (-600, -d + 600), (-B / 2, -d + 600)], hatch=True)
    v.line((-B / 2 - 600, 0), (B / 2 + 600, 0), "THIN")
    for x in (-260, 260):
        v.line((x, -1450), (x, 300), "OUTLINE")
    v.dim((-B / 2, -d - 200), (B / 2, -d - 200), -3, kind="h", text=f"{B:.0f} (firm)")
    v.dim((B / 2 + 200, 0), (B / 2 + 200, -d), 3, kind="v", text=f"{d:.0f}")
    v.dim((-600, 400), (600, 400), 3, kind="h", text="1 200 pedestal")
    v.text((-B / 2 - 500, 50), "ground", 2.0)
    title(v, -B / 2 - 500, 900, "SECTION (firm ground)", 3.0)
    rows = [["Ground class", "B m", "depth m", "concrete m³", "bearing kPa (q_Rd)"]]
    for k, f_ in FND.items():
        if "B" in f_:
            rows.append([k, f"{f_['B']}", f"{f_['depth']}", f"{f_['concrete_m3']}", f"{f_['bearing_kPa']} ({f_['q_rd_kPa']})"])
        else:
            rows.append([k, f_["plinth_m"], "–", f"{f_['concrete_m3']}", f"{f_['anchors']} anchors Ø{f_['bar_mm']}"])
    s.table = rows; s.table_pos = (220, 285); s.table_widths = [74, 28, 16, 20, 40]
    iso(s, "NM8-500", 250, 120, 80, 80); iso(s, "NM8-510", 330, 120, 80, 80)
    s.notes = [f"Anchor cage NM8-510: {M6.FL_BASE['n']} × M24 8.8 HDG on PCD {M6.FL_BASE['pcd']:.0f}, two template rings, embedded 1.45 m; 4 hinge anchors M24.",
               "Pedestal top 170 above ground; 30 mm grout under the base flange. Concrete C30/37 XF4 air-entrained, cover 50, rebar ≈ 75 kg/m³.",
               "Ground class from a trial pit at the site (depth 2 m); frost-susceptible silt: replace 0.5 m under the slab with compacted gravel. Rock: drilled plinth with 8 anchors."]
    s.notes_top = (14, 72); s.notes_wrap = 110
    return s


# ======================================================================== fasteners + bought parts
def fastener_sheet():
    s = S("NM8-900", "FASTENER AND TORQUE SCHEDULE", "ISO 4014/4017, EN 14399-4 (HV), 10.9 zinc-flake unless stated", "–", "–")
    J = {j["joint"].split(" (")[0]: j for j in SP["bolted_joints"]}
    def jj(k):
        j = J[k]
        return f"{j['tightening_Nm']} Nm", f"slip {j['slip_factor']}" + (f", separation {j['separation_factor']}" if j["separation_factor"] < 100 else "")
    s.table = [["Joint", "Fasteners", "Torque / preload", "Check"],
               ["Blade root → pitch bearing inner ring", "12 × M16 10.9 per blade", "280 Nm (μ 0.12), re-torque at 50 h", "F_bolt 64 kN design vs 113"],
               ["Pitch bearing outer ring → hub neck", "20 × M16 10.9 per blade", "280 Nm", "doc 35 §5"],
               ["Hub → drum web", "12 × M16 10.9 PCD 400", *jj("hub to drum web")],
               ["Spindle → bedplate", "12 × M20 10.9 PCD 350", *jj("spindle flange to bedplate")],
               ["Stator carrier → spindle flange", "12 × M12 10.9 PCD 240", *jj("stator carrier to spindle flange")],
               ["Disc → drum ring", "24 × M12 10.9 PCD 662", *jj("brake disc to drum flange ring")],
               ["Caliper → bracket", "4 × M16 10.9 each (3 calipers)", "280 Nm", "–"],
               ["Third caliper bracket → bedplate", "4 × M16 10.9 + nuts", "280 Nm", "–"],
               ["Yaw inner ring → bedplate", "16 × M16 10.9 HV PCD 350", "280 Nm", "util 0.42"],
               ["Yaw outer ring → adapter", "16 × M16 10.9 PCD 490", "280 Nm", "–"],
               ["Adapter → tower top flange", "16 × M20 10.9 HV PCD 380", "540 Nm", "ratio 0.45"],
               ["Tower base flange → anchors", f"{M6.FL_BASE['n']} × M24 8.8 HDG, 3 nuts each", "tension to 150 kN (tool), re-check at 3 months", f"F_bolt {TW['base_flange']['F_bolt_kN']} kN"],
               ["Hinge brackets → pedestal", "4 × M24 8.8 HDG", "350 Nm", "–"],
               ["Cover, spinner, mast, nose frame", "M6–M12 A4-70", "A4 table", "–"]]
    s.table_pos = (14, 285); s.table_widths = [80, 70, 90, 80]
    s.notes = ["Torques for 10.9 zinc-flake with μ 0.12 (lubricated); mark every bolt after torquing; check 10 % of each joint at the first service (3 months) and yearly.",
               "HV sets (EN 14399-4) where the joint carries the yaw moment; no washers under the nut side of HV sets other than those in the set."]
    s.notes_top = (14, 200)
    return s


def bought_sheet():
    s = S("NM8-910", "BOUGHT PARTS SPECIFICATION (ENVELOPES AND INTERFACES)", "see lines", "see lines", "–")
    pb = HY["pitch_bearing"]["chosen"]
    s.table = [["Part", "Specification", "Interface", "Qty"],
               ["Pitch bearing (NM8-250)", f"4-point, Dpw {pb['Dpw'] * 1000:.0f}, balls {pb['Dw'] * 1000:.0f}, Z {pb['Z']}, s0 ≥ 1.25 under SLM H", "outer 20 holes PCD 360, inner 12 × M16 PCD 245", "3"],
               ["Pitch cylinder + motor (NM8-270)", "≥ 28.5 kN rated, 37 kN static, 204 mm stroke, motor brake ≥ 14.2 Nm", "trunnion in the nose frame", "1"],
               ["Supercap module (NM8-280)", "≥ 4.1 kJ per stroke × 3.6 at EOL, −30 °C heater", "nose frame tray", "1"],
               ["Main bearings (NM8-913)", "32028 X tapered roller, C 280 kN, C0 430 kN", "Ø140 j6 / f6, Ø210 P7", "2"],
               ["Brake calipers (NM8-915)", "spring-applied, 4.4 kNm each on the Ø880 × 16 disc, ≥ 14.8 kN clamp", "4 × M16 axial", "3"],
               ["Yaw slewing ring (NM8-911)", "Dpw 410, external gear z165 m4, face 60, s0 ≥ 1.25", "PCD 350 / 490, 16 × M16 each", "1"],
               ["Yaw gearmotor (NM8-912)", "≥ 2.3 kNm static output, pinion z14 m4, motor brake", "NP1-420 bracket", "2"],
               ["Magnets (NP1-220F)", "N45SH 30 × 15 × 12, NiCuNi, 280 + spares", "comb + sleeve", "280"],
               ["Slip ring", "6 power + 6 signal, IP65, −30 °C", "spindle nose Ø120", "1"],
               ["Overspeed sensors", "M18 inductive PNP, 2 channels", "NP1-321 seats", "2"],
               ["Converter + controller", "12 kW, doc 12 / doc 35 §8", "base cabinet", "1"]]
    s.table_pos = (14, 285); s.table_widths = [60, 140, 90, 14]
    s.notes = ["Replace the 3D envelopes with the supplier models before release and rerun cad/turbine_m8/clash8.py.",
               "Low-temperature grades (−30 °C operation, −40 °C storage) for all lubricants, seals and electronics."]
    s.notes_top = (14, 200)
    return s


# ======================================================================== build
def all_sheets():
    bom = json.loads((OUT / "bom8.json").read_text())
    own = [ga_turbine, None, "BOM", ga_nacelle, rotor_ga, blade, root_insert, mould, hub, spinner_sheet, rev_d, pitch_sheet,
           bedplate, brake_sheet, yaw_sheet, tower, hinge_sheet, foundation, fastener_sheet, bought_sheet]
    sheets = []
    for fn in own:
        if fn is None:
            sheets.append(None)
        elif fn == "BOM":
            sheets += bom_sheets(bom)
        else:
            sheets.append(fn())
    rows = []
    for sh in sheets:
        rows.append(["NM8-001", "DRAWING INDEX", "M8 rev A"] if sh is None else [sh.number, sh.title[:80], "M8 rev A"])
    rows += [[a, b[:80], c] for a, b, c in REUSED]
    sheets[sheets.index(None)] = index_sheet(rows)
    return sheets


def add_iso(fig, sh):
    W, H = sh.size
    for path, x, y, w, h in getattr(sh, "iso", []):
        path = Path(path)
        if not path.exists():
            print("missing iso", path)
            continue
        img = plt.imread(path)
        ih, iw = img.shape[:2]
        k = min(w / iw, (h - 4) / ih)
        ww, hh = iw * k, ih * k
        ax = fig.add_axes([(x + (w - ww) / 2) / W, (y + (h - 4 - hh) / 2) / H, ww / W, hh / H])
        ax.imshow(img, interpolation="lanczos")
        ax.axis("off")
        fig.text((x + 1) / W, (y + h - 2.5) / H, "AXONOMETRIC VIEW (not to scale)", fontsize=4.2, color="0.35")


def main():
    from matplotlib.backends.backend_pdf import PdfPages
    for d in ("pdf", "dxf", "svg", "png"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
        for f in (OUT / d).glob("*"):
            f.unlink()
    index = []
    with PdfPages(OUT / "NM8-drawing-set.pdf") as book:
        for sh in all_sheets():
            fig = sh.render()
            add_iso(fig, sh)
            fig.savefig(OUT / "pdf" / f"{sh.number}.pdf")
            svg = OUT / "svg" / f"{sh.number}.svg"
            fig.savefig(svg)
            svg.write_text(re.sub(r"<!DOCTYPE[^>]*>\s*", "", svg.read_text(), count=1))
            fig.savefig(OUT / "png" / f"{sh.number}.png", dpi=110)
            book.savefig(fig)
            plt.close(fig)
            sh.to_dxf(OUT / "dxf" / f"{sh.number}.dxf")
            index.append((sh.number, sh.title, sh.material, sh.mass))
            print(sh.number, sh.title, flush=True)
    md = ["| Drawing | Title | Material | Mass |", "|---|---|---|---|"] + [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in index]
    (OUT / "drawing-index.md").write_text("\n".join(md) + "\n")
    (OUT / "drawing-index.json").write_text(json.dumps([dict(number=a, title=b, material=c, mass=d) for a, b, c, d in index], indent=1))


if __name__ == "__main__":
    main()
