"""S6 drawing set revision B (doc 34): 8 m tower, and every part not drawn in rev A.

Imported by drawings6.py. Each function returns a draft.Sheet with an optional `iso` list
[(png, x, y, w, h)] that drawings6.main() places on the sheet (axonometric view of the part).
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
import drawings6 as D  # noqa: E402
import model6 as M  # noqa: E402

S, P, title, G = D.S, D.P, D.title, D.G
T8 = M.T8
TW = M.TW8["tower"]
FND = M.TW8["foundations"]
ISO = HERE / "out" / "iso"


def iso(s, pid, x, y, w, h):
    s.iso = getattr(s, "iso", []) + [(ISO / "parts" / f"{pid}.png", x, y, w, h)]


def iso_assy(s, name, x, y, w, h):
    s.iso = getattr(s, "iso", []) + [(ISO / f"{name}.png", x, y, w, h)]


# ======================================================================== NS6-000 GA turbine (8 m)
def ga_turbine():
    head = json.loads((HERE / "out" / "model6-parts.json").read_text())["head_kg"]
    s = S("NS6-000", "GENERAL ARRANGEMENT · TURBINE ON 8 m TOWER", "see BOM NS6-002/003",
          f"≈ {head:.0f} kg head + {TW['mass_kg']:.0f} kg tower", "1:60")
    sc = 1 / 60
    v = s.view("side", sc, (100, 95))
    H = 8000.0
    zb, zt = 200.0, 200.0 + M.L_TUBE
    db, dt = M.D_BASE, M.D_TOP
    v.poly([(-db / 2, zb), (db / 2, zb), (dt / 2, zt), (-dt / 2, zt)])
    v.poly([(-M.FL_BASE["od"] / 2, zb), (M.FL_BASE["od"] / 2, zb), (M.FL_BASE["od"] / 2, zb + 35), (-M.FL_BASE["od"] / 2, zb + 35)])
    yb = zt + 360.0                                   # yaw bearing top / bedplate underside
    hub = (-750.0, H)
    v.poly([(-385, yb - 200), (520, yb - 200), (520, yb + 690), (-385, yb + 1040)])      # cover envelope
    v.poly([(hub[0] - 470, H), (hub[0] - 300, H + 250), (hub[0] + 195, H + 335), (hub[0] + 195, H - 335), (hub[0] - 300, H - 250)])
    v.poly([(hub[0] + 200, H - 323), (hub[0] + 460, H - 323), (hub[0] + 460, H + 323), (hub[0] + 200, H + 323)])
    for a in (0.0, 120.0, 240.0):
        z1 = H + 3000 * math.cos(math.radians(a))
        v.line((hub[0] - 20, H + 280 * math.cos(math.radians(a))), (hub[0] - 20, z1))
    v.line((400, yb + 690), (400, yb + 1940), "THIN")
    v.line((-4500, 0), (4000, 0))
    B = FND["firm soil (dense gravel, moraine)"]["B"] * 1000
    v.poly([(-B / 2, -1600), (B / 2, -1600), (B / 2, -1000), (600, -1000), (600, 170), (-600, 170), (-600, -1000), (-B / 2, -1000)], hatch=True)
    v.dim((2600, 0), (2600, H), -4, kind="v", text="8 000 hub height")
    v.dim((hub[0] - 900, H - 3000), (hub[0] - 900, 0), 4, kind="v", text="5 000 tip clearance")
    v.dim((-B / 2, -1600), (B / 2, -1600), -5, kind="h", text=f"{B:.0f} square (firm ground)")
    v.dim((1800, 0), (1800, -1600), -4, kind="v", text="1 600")
    v.leader((dt / 2 + 40, 4000), (1500, 3300), f"tower Ø{db:.0f}→Ø{dt:.0f}, t {TW['geometry']['t_mm'][0]}/{TW['geometry']['t_mm'][1]}, one piece", 2.0)
    v.leader((M.HINGE["x"], zb + 40), (-3600, 1800), "base hinge NS6-410", 2.0)
    v.leader((0, yb + 300), (1400, 9800), "nacelle: G6 generator, NS6-300 bedplate, yaw, GRP cover", 2.0)
    title(v, -4400, 11500, "SIDE VIEW (wind from the left)", 3.0)
    w = s.view("front", sc, (200, 95))
    w.poly([(-db / 2, zb), (db / 2, zb), (dt / 2, zt), (-dt / 2, zt)])
    w.circle((0, H), 3000, "PHANTOM")
    for a in (90.0, 210.0, 330.0):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        w.poly([(280 * ca - 110 * sa, H + 280 * sa + 110 * ca), (3000 * ca - 60 * sa, H + 3000 * sa + 60 * ca),
                (3000 * ca + 45 * sa, H + 3000 * sa - 45 * ca), (280 * ca + 110 * sa, H + 280 * sa - 110 * ca)])
    w.circle((0, H), 335)
    w.line((-3500, 0), (3500, 0))
    w.poly([(1150 + 340, 600), (1150 + 340, 1400), (1150, 1400), (1150, 600)])
    w.leader((1300, 1400), (2600, 2400), "base cabinet NS6-620", 2.0)
    w.dim((-3000, H + 3300), (3000, H + 3300), 3, kind="h", text="Ø6 000 rotor")
    title(w, -1500, 11800, "VIEW FROM UPWIND", 3.0)
    t8 = T8
    en = t8["energy"]
    s.table = [["Item", "Value"], ["Rated power", "6 kW electric at ≈ 9.7 m/s (hub)"], ["Rotor", "Ø6.0 m, 3 blades, TSR 5.5, pitch −2° fixed"],
               ["Speed", "41–164 rpm, trip 189 rpm"], ["Hub height", "8.0 m; lowest tip 5.0 m"],
               ["Tower", f"{TW['mass_kg']:.0f} kg, f1 {TW['f1_rigid_Hz']} Hz ({TW['f1_soft_ice_Hz']} soft+ice)"],
               ["Exclusion zone", f"{TW['exclusion_zone_rpm'][0]:.0f}–{TW['exclusion_zone_rpm'][1]:.0f} rpm (3P × f1)"],
               ["Head mass", f"{head:.0f} kg above the tower flange (CAD)"],
               ["Energy vs 18 m", f"−{en['coastal']['loss_pct']:.0f} % coast … −{en['inland']['loss_pct']:.0f} % inland"],
               ["Stopping", "K1 resistor 3 × 4 Ω + spring brake 1.5 kNm"], ["Storm", "stop, yaw 90° out, hold"]]
    s.table_pos = (254, 285); s.table_widths = [24, 66]
    iso_assy(s, "A01-turbine", 345, 58, 62, 226)
    s.notes = ["Docs 28–34. Rev B: hub height 8 m (was 18 m), tower one piece, footing re-sized; all new parts drawn (index NS6-001).",
               "Keep people and vehicles out of the rotor disc: fence or marked zone of radius 4 m round the tower base; ice-fall zone 1.5 × (H + D) = 21 m when icing is possible.",
               "Siting at 8 m: rotor bottom must be clear of the wake of buildings and shelter belts (≥ 20 × obstacle height upwind in the main wind directions)."]
    s.notes_top = (14, 52); s.notes_wrap = 100
    return s


# ======================================================================== NS6-001 drawing index
def index_sheet(rows):
    s = S("NS6-001", "DRAWING INDEX (S6 SET REV B + REUSED 12 kW DRAWINGS)", "–", "–", "–")
    s.table = [["Drawing", "Title", "Source"]] + [r[:3] for r in rows]
    s.table_pos = (14, 285); s.table_widths = [26, 150, 30]
    s.notes = ["Rev B (2026-11-06): 8 m tower; every S6 part drawn with an axonometric view; BOM NS6-002/003; fasteners NS6-900; cabling NS6-800.",
               "Reused 12 kW drawings are used unchanged except where the BOM says 'G6 variant'. Their PDFs follow in the build book in the order of this index.",
               "All sheets NOT CHECKED: prototype release only after review, FE checks (hub arm welds, bedplate ring seat) and the stall-torque test."]
    s.notes_top = (250, 285); s.notes_wrap = 60
    return s


# ======================================================================== NS6-002/003 BOM sheets
def bom_sheets(bom):
    out = []
    per = 52
    chunks = [bom[i:i + per] for i in range(0, len(bom), per)]
    for k, ch in enumerate(chunks):
        s = S(f"NS6-00{2 + k}", f"BILL OF MATERIALS ({k + 1}/{len(chunks)})", "see lines", "see lines", "–")
        s.table = [["Pos", "Part no.", "Description", "Qty", "Make/buy", "Material / spec", "kg each"]] + \
            [[r["pos"], r["pid"], r["name"][:62], r["qty"], r["make_buy"], r["material"][:44], r["mass"]] for r in ch]
        s.table_pos = (14, 285); s.table_widths = [10, 24, 112, 10, 16, 86, 16]
        s.notes = ["Masses from the CAD model (cad/turbine_6kw/model6.py) for made parts; supplier data or estimates for bought parts. Full BOM with sources: bom6.csv."]
        s.notes_top = (14, 285 - 4.2 * (len(ch) + 1) - 4); s.notes_wrap = 120
        out.append(s)
    return out


# ======================================================================== NS6-020 rotor GA
def rotor_ga():
    s = S("NS6-020", "ROTOR ASSEMBLY · HUB, BLADES, SPINNER", "see BOM", "≈ 162 kg (rotor + hub + spinner)", "1:30")
    v = s.view("front", 1 / 30, (110, 160))
    v.circle((0, 0), 3000, "PHANTOM")
    v.circle((0, 0), 335)
    for i, a in enumerate((90.0, 210.0, 330.0), 1):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        rr = lambda r, t: (r * ca - t * sa, r * sa + t * ca)  # noqa: E731
        st = M.blade_shape()
        r, c = st[0], st[1]
        le = [rr(x, 0.3 * cc) for x, cc in zip(r, c)]
        te = [rr(x, -0.7 * cc) for x, cc in zip(r, c)]
        v.poly(le + te[::-1])
        v.line(rr(200, 0), rr(3100, 0), "CENTER")
        v.text(rr(3250, 0), f"B{i}", 3.0, "center", "center")
    v.dim((-3000, -3150), (3000, -3150), -2, kind="h", text="Ø6 000")
    v.text((-3000, 3300), "VIEW FROM UPWIND · rotation clockwise", 3.0)
    w = s.view("side", 0.08, (350, 200))
    hubpts = [(-125, 190), (170, 190), (170, 240), (200, 240), (200, -240), (170, -240), (170, -190), (-125, -190)]
    w.poly(hubpts, hatch=False)
    sp = [(-470, 0)] + [(-470 + 665 * f, 335 * math.sqrt(max(0, 1 - (1 - f) ** 2))) for f in np.linspace(0.04, 1, 14)]
    w.poly(sp, closed=False, layer="PHANTOM"); w.poly([(x, -y) for x, y in sp], closed=False, layer="PHANTOM")
    w.poly([(-110, 190), (110, 190), (110, 255), (-110, 255)])
    w.poly([(-140, 255), (140, 255), (140, 280), (-140, 280)], hatch=True)
    w.poly([(-110, 280), (110, 280), (100, 900), (-70, 900)])
    w.line((-600, 0), (300, 0), "CENTER")
    w.dim((-140, 280), (140, 280), 4, kind="h", prefix="Ø", text="280 root face r 280")
    w.dim((-470, -380), (200, -380), -4, kind="h", text="670 spinner")
    w.text((-600, 980), "SIDE VIEW, upper blade", 2.6)
    s.table = [["Item", "Value"], ["Blade setting", "−2.0° ± 0.1° at r = 2 000 (gauge NS6-135)"], ["Blade set", "static moments equal within 0.5 %"],
               ["Track", "tip track within ± 15 mm (string / laser)"], ["Rotor balance", "residual ≤ 0.2 kg·m (doc 09 R6.6)"],
               ["Root bolts", "30 × M12 10.9, 95 Nm + 90° (NS6-900)"], ["Hub bolts", "12 × M16 10.9 to the drum, 250 Nm"]]
    s.table_pos = (236, 120); s.table_widths = [26, 72]
    iso_assy(s, "A04-rotor", 232, 180, 75, 100)
    s.notes = ["Blades are numbered B1–B3 at the factory with their static moment; mount B1 on the arm marked 1 (lock-pin side).",
               "Set pitch with the blade on the hub, bolts finger tight, gauge on the r = 2 000 station; tighten in a star pattern; re-check after 50 h of operation.",
               "Balance the rotor on the turbine with the doc 09 procedure (one trial mass on the spinner brackets)."]
    s.notes_top = (14, 50)
    return s


# ======================================================================== NS6-101 blade sections + laminate
def blade_sections():
    s = S("NS6-101", "BLADE · SECTIONS AND LAMINATE SCHEDULE", "E-glass/epoxy (infusion), PVC H80 core", "20.6 kg", "1:2 / 1:4")
    r, c, tc, tw = M.blade_shape()
    st = M.D6["blade_stations"]
    x0 = 30.0
    for k, rr in enumerate((400.0, 700.0, 1200.0, 2000.0, 2800.0)):
        cc = float(np.interp(rr, r, c)); t = float(np.interp(rr, r, tc))
        scale = 0.18
        v = s.view(f"S{k}", scale, (x0 + 0.3 * cc * scale + 5, 230))
        pts = M.airfoil_pts(cc, t)
        v.poly([tuple(p) for p in pts], hatch=False)
        cap = float(np.interp(rr, np.array(st["r"]) * 1000, st["t_cap_mm"]))
        # spar caps (between 15 % and 45 % chord) and web at 30 %
        wcap = 0.3 * cc
        v.line((-0.15 * cc, 0), (0.15 * cc, 0), "CENTER")
        yt = max(p[1] for p in pts if abs(p[0]) < 0.08 * cc)
        yb = min(p[1] for p in pts if abs(p[0]) < 0.08 * cc)
        v.poly([(-wcap / 2, yt), (wcap / 2, yt), (wcap / 2, yt - cap * 3), (-wcap / 2, yt - cap * 3)], hatch=True)
        v.poly([(-wcap / 2, yb), (wcap / 2, yb), (wcap / 2, yb + cap * 3), (-wcap / 2, yb + cap * 3)], hatch=True)
        v.line((0, yb + cap * 3), (0, yt - cap * 3), "OUTLINE")
        v.text((-0.3 * cc, -0.35 * cc - 30), f"r {rr:.0f}: c {cc:.0f}, t/c {t:.2f}, cap {cap:.2f}", 1.9)
        x0 += cc * scale + 14
    s.views[0].text((-60, 140), "SECTIONS (caps hatched ×3 thickness for clarity, web at 30 % c; LE to the left)", 2.6)
    rows = [["Zone (r mm)", "Shell skin", "Core", "Spar cap (each side)", "Web"],
            ["280–700 root", "2 × 600 g ±45° + 0–12 mm UD/biax build-up", "–", "merges into root", "–"],
            ["700–1 400", "2 × 450 g ±45°", "PVC H80 8 mm", "UD 1 200 g: 4.25→3.75 mm", "2 × 450 g ±45° on 10 mm core"],
            ["1 400–2 200", "2 × 450 g ±45°", "PVC H80 6 mm", "UD: 3.50→2.25 mm", "same"],
            ["2 200–3 000 tip", "2 × 300 g ±45°", "PVC H80 5 mm", "UD: 2.00→1.00 mm (min)", "ends at r 2 900"],
            ["LE r 2 000–3 000", "erosion tape 0.3 mm PU", "", "", ""]]
    s.table = rows; s.table_pos = (14, 175); s.table_widths = [30, 80, 30, 52, 52]
    s.notes = ["Vacuum infusion, epoxy (Tg ≥ 80 °C, cold-curing then post-cure 8 h at 70 °C), fibre volume ≥ 50 %. Each blade: two shells + web, bonded with structural paste (1–3 mm gaps), leading-edge and trailing-edge flanges 30 mm.",
               "Cap thickness follows design6.json t_cap_mm (doc 30 §2); minimum cap 1.0 mm governed by buckling: do not reduce. UD glass E-glass 1 200 g/m² stitched, 0° ± 2° to the pitch axis.",
               "Root: laminate builds up from r 700 to a 28 mm wall at the root face around the 10 bonded inserts NS6-105 (fixture NS6-115). Machine the root face square to the pitch axis within 0.2 mm after cure.",
               "Gelcoat: polyurethane, white RAL 9010, 0.4 mm. Drain hole Ø4 at the tip trailing edge. Lightning: none on 3 m blades (LPL I, doc 02: tower and nacelle carry it; blade receptor option).",
               "Quality: weigh and record mass + static moment; tap test the bonds; one blade per 20 static-tested to SLM H × 1.35 (doc 30)."]
    s.notes_top = (14, 140)
    iso_assy(s, "X-blade", 300, 56, 105, 80)
    return s


# ======================================================================== NS6-105 root insert
def root_insert():
    s = S("NS6-105", "BLADE ROOT INSERT M12 (BONDED)", "C45E+QT, zinc-flake coated (Geomet 500)", "0.33 kg", "2:1")
    v = s.view("sec", 2.0, (40, 190))
    prof = [(0, 12.0)]
    x = 0.0
    for k in range(6):
        prof += [(x + 8, 12.0), (x + 8, 10.5), (x + 13, 10.5), (x + 13, 12.0)]
        x += 13
    prof += [(110, 12.0), (110, -12.0)]
    low = [(px, -pr) for px, pr in prof[::-1]]
    v.poly(prof + low[1:], hatch=False)
    v.poly([(0, 5.1), (30, 5.1), (30, -5.1), (0, -5.1)], hatch=True)
    v.line((-5, 0), (118, 0), "CENTER")
    v.dim((0, 12), (110, 12), 6, kind="h", text="110")
    v.dim((0, -12), (30, -12), -6, kind="h", text="30 thread M12-6H")
    v.dim((112, -12), (112, 12), -6, kind="v", prefix="Ø", text="24")
    v.leader((21, 10.5), (40, 40), "6 grooves 5 × 1.5 (bond key)", 2.0)
    title(v, 0, 55, "INSERT (half section)", 3.0)
    s.notes = ["Bonded into the blade root laminate during lay-up with the root fixture NS6-115: insert axis parallel to the pitch axis within 0.3°, PCD 185 ± 0.2, face flush ± 0.2 after root facing.",
               "Pull-out test: 3 inserts per batch in a root coupon, ≥ 60 kN each (design 43 kN at SLM H, doc 30 §2).",
               "Threads protected with plastic plugs until assembly; studs M12 10.9 × 75 (NS6-900) screwed in 30 mm with Loctite 270, 40 Nm."]
    s.notes_top = (14, 120)
    iso_assy(s, "X-insert", 280, 150, 120, 90)
    return s


# ======================================================================== NS6-110 blade mould
def mould():
    s = S("NS6-110", "BLADE MOULD SET (PLUG, TWO HALVES, FRAME)", "GRP tooling laminate on S235 RHS frame", "≈ 2 × 75 kg + frame 155 kg", "1:20")
    r, c, tc, tw = M.blade_shape()
    v = s.view("plan", 1 / 20, (30, 175))
    le = [(x, 0.3 * cc) for x, cc in zip(r, c)]
    te = [(x, -0.7 * cc) for x, cc in zip(r, c)]
    v.poly(le + te[::-1], layer="OUTLINE")
    x0, x1 = 160.0, 3120.0
    v.poly([(x0, 260), (x1, 260), (x1, -440), (x0, -440)])
    v.poly([(x0 + 120, 380), (x1 - 120, 380), (x1 - 120, -560), (x0 + 120, -560)], layer="HIDDEN")
    for xx in np.linspace(x0 + 40, x1 - 120, 6):
        v.line((xx, 380), (xx, -560), "HIDDEN")
    for xx in (400, 1200, 2000, 2800):
        v.line((xx, 280), (xx, -460), "CENTER")
        v.text((xx + 15, 290), f"S{xx:.0f}", 2.0)
    v.dim((x0, -440), (x1, -440), -6, kind="h", text=f"{x1 - x0:.0f} mould")
    v.dim((x1, 260), (x1, -440), -6, kind="v", text="700")
    v.text((x0, 520), "PLAN, LOWER HALF (pressure side), frame RHS 80 × 80 × 4 hidden", 3.0)
    w = s.view("sec", 0.2, (95, 75))
    cc = float(np.interp(1200, r, c)); t = float(np.interp(1200, r, tc))
    pts = M.airfoil_pts(cc, t)
    w.poly([tuple(p) for p in pts])
    w.poly([(-250, 0), (350, 0), (350, -160), (-250, -160)], layer="OUTLINE")
    w.poly([(-250, 0), (350, 0), (350, 160), (-250, 160)], layer="PHANTOM")
    w.poly([(-250, -160), (350, -160), (350, -172), (-250, -172)], hatch=True)
    w.dim((-250, -172), (350, -172), -5, kind="h", text="600 (flange 120 each side)")
    w.text((-250, 200), "SECTION S1200: lower half solid, upper half phantom; parting line on LE/TE", 2.4)
    rows = [["Step", "Process"],
            ["1 Plug", "CNC-machined tooling board (polyurethane 0.7 g/cm³) on an MDF/steel core; ruled parting surface along LE and TE; sand P600, seal, release"],
            ["2 Halves", "Tooling gelcoat 1 mm, skin 2 × 300 g CSM, 10 mm vinylester/glass build-up, egg-crate ribs 12 mm GRP every 400 mm"],
            ["3 Frame", "RHS 80 × 80 × 4 cradle, 6 legs, levelling feet, pins Ø20 at 4 places on the flanges for closing"],
            ["4 Heating", "silicone heating mats 300 W/m² under the lower half, 70 °C post-cure; thermocouples ×4"],
            ["5 Web", "flat-plate web mould: tapered aluminium plate 2 900 × 220 on the bench (NS6-115)"]]
    s.table = rows; s.table_pos = (190, 135); s.table_widths = [18, 196]
    s.notes = ["One mould set makes all blades (≥ 300 parts before refurbishment). Mould flange 120 mm with a 25 mm vacuum sealing land and a 6 mm resin trap groove.",
               "Tolerances: profile ± 0.5 mm, twist ± 0.2°, length ± 2 mm. Check each new mould against the plug with the five section templates S400 … S2800.",
               "Root end: 20 mm steel end plate with the bolt pattern of the root fixture NS6-115 (4 × M12), square to the pitch axis."]
    s.notes_top = (190, 105); s.notes_wrap = 100
    iso_assy(s, "A07-mould", 300, 170, 105, 90)
    return s


def root_fixture_sheet():
    s = S("NS6-115", "ROOT INSERT FIXTURE AND WEB MOULD (TOOLS)", "S355 machined; Al 5083 plate", "9 kg (fixture)", "1:4")
    v = s.view("plan", 0.25, (90, 170))
    v.circle((0, 0), 150); v.circle((0, 0), 60)
    v.bolt_circle((0, 0), 185, 10, 11.8, start=18)
    v.bolt_circle((0, 0), 260, 4, 13.2, start=45, layer="HIDDEN")
    v.dim((-150, 0), (150, 0), -50, kind="h", prefix="Ø", text="300")
    v.text((-150, 175), "ROOT FIXTURE, view on the spigots: 10 × Ø11.8 g6 spigots × 30 on PCD 185", 2.6)
    w = s.view("web", 0.06, (180, 90))
    w.poly([(0, 0), (2900, 30), (2900, 100), (0, 220)])
    w.dim((0, 0), (2900, 0), -6, kind="h", text="2 900")
    w.dim((0, 0), (0, 220), 6, kind="v", text="220")
    w.text((0, 330), "WEB MOULD PLATE (tapered, 10 mm Al)", 2.6)
    s.notes = ["Fixture bolts to the root end plate of the lower mould half (4 × M12); inserts NS6-105 slide over the spigots and are screwed on with M12 bolts so their faces sit on the fixture face.",
               "After demoulding, remove the fixture, face the root on the root-facing jig (lathe or portable facer) to the root length, check PCD with the hub-flange template.",
               "Web mould: flat plate with 25 mm edge flanges; web is infused flat (core 10 mm, 2 × 450 g ±45° each face) and cut to the template lines."]
    s.notes_top = (14, 70)
    iso(s, "NS6-115", 280, 160, 120, 90)
    return s


# ======================================================================== NS6-130 pitch setting
def pitch_sheet():
    s = S("NS6-130", "PITCH SETTING · ROOT SLOTS, WASHER PLATES, GAUGE", "C45 hardened 45 HRC; gauge Al 6082", "30 × 15 g; gauge 1.6 kg", "1:2 / 1:5")
    v = s.view("slots", 0.5, (95, 180))
    v.circle((0, 0), 140); v.circle((0, 0), 75)
    for k in range(10):
        a0 = 18 + 36 * k
        for dd in (-2.5, 2.5):
            a = math.radians(a0 + dd)
            v.circle((92.5 * math.cos(a), 92.5 * math.sin(a)), 6.75, "THIN")
        v.arc((0, 0), 92.5 + 6.75, a0 - 2.5, a0 + 2.5)
        v.arc((0, 0), 92.5 - 6.75, a0 - 2.5, a0 + 2.5)
    v.circle((0, 0), 92.5, "CENTER")
    v.dim((-140, 0), (140, 0), -80, kind="h", prefix="Ø", text="280 root flange 25")
    v.leader((92.5 * math.cos(math.radians(18)), 92.5 * math.sin(math.radians(18))), (190, 110), "10 arc slots 13.5 wide, ±2.5° on PCD 185", 2.0)
    v.text((-140, 160), "HUB ROOT FLANGE (part of NS6-200), from the blade", 2.8)
    w = s.view("washer", 2.0, (270, 220))
    w.circle((0, 0), 14); w.circle((0, 0), 6.5)
    w.dim((-14, 0), (14, 0), -8, kind="h", prefix="Ø", text="28")
    w.text((-14, 22), "WASHER PLATE 28 × 4, 45 HRC", 2.4)
    g = s.view("gauge", 0.2, (250, 120))
    g.poly([(-260, -20), (260, -20), (260, 20), (-260, 20)])
    g.poly([(-60, 20), (60, 20), (60, 60), (-60, 60)])
    g.poly([(-20, -60), (20, -60), (20, -20), (-20, -20)])
    g.text((-260, 80), "GAUGE NS6-135: clamps on r = 2 000 (chord line pads), inclinometer seat", 2.2)
    s.notes = ["Doc 30 called for wedge shims; a wedge tilts the blade axis (cone), it cannot change pitch. Rev B sets pitch by rotating the blade about its axis in arc slots of the hub root flange: ±2.5° around the −2.0° standard (−4.5° … +0.5°).",
               "Setting: rotor locked with B1 horizontal, gauge on the blade at r = 2 000, rotor plane reference from a level on the hub front face; set −2.0° ± 0.1°, torque the studs, re-check.",
               "Joint: 10 × M12 10.9 studs + hardened washer plates over the slots; friction carries the blade pitching moment (≤ 0.05 kNm) with μ 0.2 ≥ 10× margin."]
    s.notes_top = (14, 75)
    iso_assy(s, "X-pitch", 300, 140, 105, 70)
    return s


# ======================================================================== NS6-200 hub (rev B geometry)
def hub():
    m = json.loads((HERE / "out" / "model6-parts.json").read_text())
    mass = next(p["mass_kg"] for p in m["parts"] if p["pid"] == "NS6-200")
    H = M.HUB
    s = S("NS6-200", "FIXED HUB WELDMENT", "S355NL, welded, stress relieved", f"{mass:.0f} kg (CAD)", "1:5")
    v = s.view("front", 0.2, (95, 175))
    v.circle((0, 0), 190); v.circle((0, 0), 178, "HIDDEN"); v.circle((0, 0), 50)
    v.bolt_circle((0, 0), 400, 12, 17.5, start=15.0, layer="HIDDEN")
    v.circle((0, 0), 240, "HIDDEN")
    for a in (90.0, 210.0, 330.0):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        rot = lambda x, y: (x * ca - y * sa, x * sa + y * ca)  # noqa: E731
        v.poly([rot(186, -110), rot(255, -110), rot(255, 110), rot(186, 110)])
        v.poly([rot(255, -140), rot(280, -140), rot(280, 140), rot(255, 140)], hatch=True)
        v.line(rot(150, 0), rot(330, 0), "CENTER")
    v.dim((-190, 0), (190, 0), -40, kind="h", prefix="Ø", text="380 × 12 shell")
    v.dim((0, 0), (0, 280), -60, kind="v", text="280 root face")
    title(v, -300, 330, "VIEW FROM UPWIND (spinner removed)", 3.0)
    w = s.view("section", 0.2, (270, 175))
    x0, x1, ri, ro = H["shell"]
    w.poly([(x0, ri), (x1, ri), (x1, ro), (x0, ro)], hatch=True)
    w.poly([(x0, -ri), (x1, -ri), (x1, -ro), (x0, -ro)], hatch=True)
    w.poly([(x0, 50), (x0 + 10, 50), (x0 + 10, ri), (x0, ri)], hatch=True)
    w.poly([(x0, -50), (x0 + 10, -50), (x0 + 10, -ri), (x0, -ri)], hatch=True)
    fx0, fx1, fri, fro = H["flange"]
    w.poly([(fx0, fri), (fx1, fri), (fx1, fro), (fx0, fro)], hatch=True)
    w.poly([(fx0, -fri), (fx1, -fri), (fx1, -fro), (fx0, -fro)], hatch=True)
    w.poly([(-110, 190), (-102, 190), (-102, 255), (-110, 255)], hatch=True)
    w.poly([(102, 190), (110, 190), (110, 255), (102, 255)], hatch=True)
    w.poly([(-140, 255), (-75, 255), (-75, 280), (-140, 280)], hatch=True)
    w.poly([(75, 255), (140, 255), (140, 280), (75, 280)], hatch=True)
    w.line((-200, 0), (260, 0), "CENTER"); w.line((0, -260), (0, 330), "CENTER")
    w.dim((-140, 280), (140, 280), 6, kind="h", prefix="Ø", text="280 × 25 root flange")
    w.dim((x0, -ro), (fx1, -ro), -14, kind="h", text=f"{fx1 - x0:.0f}")
    w.dim((fx0, -fro), (fx1, -fro), -6, kind="h", text="30")
    w.leader((106, 230), (220, 320), "arm Ø220 × 8", 2.0)
    w.leader((fx1, -200), (250, -300), "Ø360 H7 spigot bore, 12 × Ø17.5 PCD 400", 2.0)
    title(w, -200, 370, "SECTION THROUGH THE UPPER ARM (x = 0 rotor plane)", 3.0)
    s.notes = [f"Arms Ø220 × 8: parked SLM stress {M.D6['hub']['chosen']['static_MPa']} MPa (allow 323); fatigue at the flange weld 5.7 MPa with simulated loads (allow 30.8, detail 71).",
               "Drum joint: Ø360 H7 bore on the drum spigot, 12 × M16 10.9 PCD 400, 250 Nm; friction carries the 5.7 kNm design torque.",
               "Root flanges machined after stress relief: face square to the arm axis within 0.05, 10 arc slots ±2.5° on PCD 185 centred on −2.0° pitch (NS6-130); arm 1 marked at the lock-pin azimuth.",
               "Shell lengthened to 295 (rev A 240) so the arm intersections close on the shell; front plate 10 with Ø100 access hole. Welds full penetration, ISO 5817 B, 100 % MT, UT on flange welds. Zinc spray + C5 paint.",
               "Spinner brackets NS6-211 weld on the front plate edge at 60° between the arms. FE check of the arm-to-shell weld before release (doc 30 §11)."]
    s.notes_top = (14, 72)
    iso(s, "NS6-200", 315, 56, 90, 70)
    return s


# ======================================================================== NS6-210 spinner
def spinner_sheet():
    s = S("NS6-210", "SPINNER (GRP) AND BRACKETS NS6-211", "glass/polyester 4 mm, gelcoat RAL 9010; brackets S235 galv.", "8.7 kg + 3.6 kg", "1:5")
    v = s.view("side", 0.15, (110, 165))
    pr = [(-470 + 665 * f, 335 * math.sqrt(max(0, 1 - (1 - f) ** 2))) for f in np.linspace(0, 1, 24)]
    v.poly(pr, closed=False); v.poly([(x, -y) for x, y in pr], closed=False)
    v.line((195, -335), (195, 335))
    v.line((-520, 0), (260, 0), "CENTER")
    v.circle((0, 270), 122, "HIDDEN")
    v.dim((-470, -360), (195, -360), -6, kind="h", text="665")
    v.dim((195, -335), (195, 335), -10, kind="v", prefix="Ø", text="670")
    v.leader((0, 390), (150, 450), "3 cut-outs Ø244 on the arm axes (40 mm clear to the root)", 2.0)
    title(v, -470, 470, "SIDE VIEW", 3.0)
    w = s.view("br", 0.5, (230, 130))
    w.poly([(0, 0), (10, 0), (10, 112), (0, 112)], hatch=True)
    w.poly([(-50, 106), (10, 106), (10, 112), (-50, 112)], hatch=True)
    w.text((-50, 135), "BRACKET NS6-211: 60 × 10 flat, 3 per hub, M8 rivnut in the spinner", 2.2)
    s.notes = ["Hand lay-up or RTM in a two-part female mould from the same plug supplier as the blades; 4 mm: gelcoat 0.5 + 3 × 450 g CSM + 1 × 300 g woven; flange-less rear edge with a 20 mm stiffening bead.",
               "Rear edge runs 5 mm from the drum front web; the spinner does not seal (drain gaps at the cut-outs).",
               "Fix with 3 × M8 1.4404 screws + rubber washers into the brackets; brackets weld to the hub front plate edge at 60° between the arms."]
    s.notes_top = (14, 70)
    iso(s, "NS6-210", 290, 150, 115, 90)
    return s


# ======================================================================== NS6-310 brackets (NP1-310, NP1-420)
def brackets():
    s = S("NS6-310", "CALIPER BRACKET NP1-310 AND YAW DRIVE BRACKET NP1-420", "S355J2+N plate 25, welded, galv.", "18.1 kg; 2 × 7.7 kg", "1:5")
    C = M.FP.CALIPER
    v = s.view("cal", 0.2, (70, 175))
    y0, y1 = C["r"]
    v.poly([(C["mount_x"][0], y0), (C["mount_x"][1], y0), (C["mount_x"][1], y1), (C["mount_x"][0], y1)], hatch=True)
    v.poly([(C["mount_x"][0], 260), (680, 260), (680, 285), (C["mount_x"][0], 285)], hatch=True)
    v.poly([(C["mount_x"][1], 260), (C["mount_x"][1] + 40, 260), (C["mount_x"][1] + 40, y0), (C["mount_x"][1], y0)])
    for xx in (590, 650):
        v.line((xx, 250), (xx, 295), "CENTER")
    v.dim((C["mount_x"][0], 285), (680, 285), 6, kind="h")
    v.dim((C["mount_x"][1], y0), (C["mount_x"][1], y1), -8, kind="v")
    v.text((C["mount_x"][0], y1 + 60), "NP1-310 · plan (x along the spindle, y lateral)", 2.6)
    w = s.view("yd", 0.2, (260, 175))
    w.poly([(-90, 260), (90, 260), (90, 400), (-90, 400)])
    w.circle((0, 328), 17)
    for dx in (-40, 40):
        for dy in (-40, 40):
            w.circle((dx, 328 + dy), 4.25)
    w.dim((-90, 400), (90, 400), 6, kind="h", text="180")
    w.dim((90, 260), (90, 400), -8, kind="v", text="140")
    w.text((-90, 450), "NP1-420 · top plate (pinion bore Ø34, 4 × M10)", 2.6)
    s.notes = ["NP1-310 (12 kW Rev B geometry, cad/nacelle_fitcheck): only the LEFT bracket is fitted on S6 (one caliper). Mounting plate 25 with 4 × M16 tapped to suit the chosen caliper; web 25 to the bedplate side plate, 4 × M16 10.9 through, 210 Nm.",
               "NP1-420 (doc 25): top plate 25 + web 25; web bolts to the side plate outer face with 4 × M16 at x ±50, z 70/140; gearbox flange 4 × M10 8.8, 49 Nm. Centre distance pinion–ring 328.0 ± 0.1 (shim the web).",
               "Both: welds a = 8 fillet all round, ISO 5817 C; hot-dip galvanise after welding, then machine the caliper face."]
    s.notes_top = (14, 75)
    iso(s, "NP1-310", 190, 60, 80, 60)
    iso(s, "NP1-420-L", 300, 60, 90, 70)
    return s


# ======================================================================== NS6-400 tower 8 m
def tower():
    g = TW["geometry"]
    s = S("NS6-400", "TOWER 8 m · ONE-PIECE TILT-UP MONOPOLE", "S355J2+N, rolled and seam welded; hot-dip galvanised",
          f"{TW['mass_kg']:.0f} kg (CAD {next(p['mass_kg'] for p in json.loads((HERE / 'out' / 'model6-parts.json').read_text())['parts'] if p['pid'] == 'NS6-400'):.0f})", "1:25 / 1:10")
    sc = 0.034
    v = s.view("elev", sc, (75, 30))
    L = M.L_TUBE
    db, dt = M.D_BASE, M.D_TOP
    t0, t1 = g["t_mm"]
    v.poly([(-db / 2, 0), (db / 2, 0), (dt / 2, L), (-dt / 2, L)])
    v.line((-(db + dt) / 4, L / 2), ((db + dt) / 4, L / 2), "THIN")
    for z, d in ((0, M.FL_BASE["od"]), (35, M.FL_BASE["od"])):
        pass
    v.poly([(-M.FL_BASE["od"] / 2, 0), (M.FL_BASE["od"] / 2, 0), (M.FL_BASE["od"] / 2, 35), (-M.FL_BASE["od"] / 2, 35)], hatch=True)
    v.poly([(-210, L - 30), (210, L - 30), (210, L), (-210, L)], hatch=True)
    v.poly([(M.HINGE["x"] - 60, 0), (-db / 2 + 20, 0), (-db / 2 + 20, 160), (M.HINGE["x"] - 60, 160)])
    v.circle((M.HINGE["x"], 40), 25)
    v.poly([(db / 2 - 20, 250), (db / 2 + 140, 250), (db / 2 + 140, 450), (db / 2 - 20, 450)])
    v.circle((db / 2 + 80, 350), 26)
    v.dim((db / 2 + 600, 0), (db / 2 + 600, L), -4, kind="v", text=f"{L:.0f} overall (flange faces)")
    v.dim((db / 2 + 300, 0), (db / 2 + 300, L / 2), -4, kind="v", text=f"lower can t {t0}")
    v.dim((db / 2 + 300, L / 2), (db / 2 + 300, L), -4, kind="v", text=f"upper can t {t1}")
    v.dim((-db / 2, 0), (db / 2, 0), -14, kind="h", prefix="Ø", text=f"{db:.0f}")
    v.dim((-dt / 2, L), (dt / 2, L), 6, kind="h", prefix="Ø", text=f"{dt:.0f}")
    v.leader((M.HINGE["x"], 40), (-1600, 900), "hinge lugs 2 × 25, pin Ø50", 2.0)
    v.leader((db / 2 + 80, 350), (900, 1200), "gin-pole lugs 2 × 25, pin Ø50", 2.0)
    v.leader((db / 2 - 40, 700), (900, 1900), "hand hole 150 × 300 at +700, frame 15", 2.0)
    title(v, -1500, L + 400, "ELEVATION", 3.0)
    f = s.view("flanges", 0.1, (215, 175))
    for (cx, fl, lab, st) in ((0, M.FL_BASE, f"BASE FLANGE {M.FL_BASE['t']:.0f}: {M.FL_BASE['n']} × Ø26 PCD {M.FL_BASE['pcd']:.0f}", 15.0),
                              (900, M.FL_TOP, "TOP FLANGE 30: 16 × Ø22 PCD 380 (to NY-400)", 11.25)):
        f.circle((cx, 0), fl["od"] / 2); f.circle((cx, 0), fl["id"] / 2)
        f.bolt_circle((cx, 0), fl["pcd"], fl["n"], fl["hole"], start=st)
        f.text((cx - fl["od"] / 2, -fl["od"] / 2 - 70), lab, 2.0)
    title(f, -340, 400, "FLANGES (plan)", 3.0)
    tw = TW
    s.table = [["Item", "Value"], ["Shell", f"Ø{db:.0f} × {t0} → Ø{dt:.0f} × {t1}, linear taper, D/t ≤ {tw['D_over_t_max']}"],
               ["Cans", f"2 × {L / 2 / 1000:.2f} m rolled, one circumferential butt weld"],
               ["f1 (rigid / soft+ice)", f"{tw['f1_rigid_Hz']} / {tw['f1_soft_ice_Hz']} Hz; f2 {tw['f2_rigid_Hz']} Hz"],
               ["Window", f"f1 ≥ 1.15 × 1P max (3.14 Hz); 3P crosses at {tw['exclusion_zone_rpm'][0]:.0f}–{tw['exclusion_zone_rpm'][1]:.0f} rpm"],
               ["Governing", f"{tw['governing']}, use {tw['util_max']}"],
               ["Base moment (design)", f"{tw['base_flange']['M_design_kNm']} kNm; SLM sensitivity use {tw['util_SLM']}"],
               ["Base bolts", f"{tw['base_flange']['bolts']} × M24 10.9 anchors: {tw['base_flange']['F_bolt_kN']} / {tw['base_flange']['F_t_Rd_kN']} kN"],
               ["Fatigue (base / mid)", f"{list(tw['fatigue_damage'].values())[0]} / {list(tw['fatigue_damage'].values())[1]} (turbulence × {T8['fatigue_turbulence_factor']})"],
               ["Tilt-up", f"base moment {tw['tilt_up_base_moment_kNm']} kNm, use {tw['util_tilt_up']}"]]
    s.table_pos = (175, 285); s.table_widths = [34, 112]
    s.notes = ["Rev B replaces the 18 m two-section tower. At 8 m a soft tower (f1 below 3P at 41 rpm) is impossible with the 983 kg head, so the tower is stiff: f1 above 1P at full speed; the controller skips the 3P crossing zone like the old 1P zone.",
               "Seam and can welds full penetration, ISO 5817 B, 100 % UT on flange and can welds; flanges machined flat after welding (0.2 mm), top flange square to the axis within 0.5 mm/m.",
               "No climbing: service by tilting the tower down (NS6-420). Earthing bosses 2 × M12 at +300. Hand-hole cover NS6-401 with EPDM gasket and 6 × M8."]
    s.notes_top = (175, 112); s.notes_wrap = 82
    iso(s, "NS6-400", 335, 120, 70, 120)
    return s


# ======================================================================== NS6-410 hinge
def hinge_sheet():
    s = S("NS6-410", "BASE HINGE BRACKETS AND PIN", "S355J2+N 30 mm plate, galv.; pin 42CrMo4+QT Ø50 h9", "37 kg", "1:5")
    Hh = M.HINGE
    v = s.view("side", 0.2, (90, 160))
    v.poly([(-140, -60), (90, -60), (90, -30), (-140, -30)], hatch=True)
    v.poly([(-90, -30), (60, -30), (60, 40), (-90, 40)])
    v.circle((0, 40), 60); v.circle((0, 40), 25.5)
    v.line((-200, -60), (200, -60), "THIN")
    v.dim((-140, -60), (90, -60), -8, kind="h", text="230")
    v.dim((0, -60), (0, 40), -40, kind="v", text="100 pin centre above base plate")
    v.text((-140, 130), "SIDE VIEW (tower lug between the two bracket plates)", 2.6)
    w = s.view("plan", 0.2, (280, 160))
    w.poly([(-140, -230), (90, -230), (90, 230), (-140, 230)])
    for y0 in (Hh["lug_gap"][0] - Hh["lug_t"] - 32, Hh["lug_gap"][1] + Hh["lug_t"] + 2):
        w.poly([(-90, y0), (60, y0), (60, y0 + 30), (-90, y0 + 30)], hatch=True)
    for (x, y) in ((-100, -190), (-100, 190), (50, -190), (50, 190)):
        w.circle((x, y), 13)
    w.line((0, -260), (0, 260), "CENTER")
    w.dim((-140, -230), (-140, 230), 6, kind="v", text="460")
    w.text((-140, 260), "PLAN (4 × M24 anchors, NS6-510)", 2.6)
    s.notes = ["Hinge axis 390 mm upwind of the tower axis (−X side), 40 mm above the base-flange underside: the tower lands on the levelling nuts as it reaches vertical.",
               "Pin Ø50 h9 in Ø51 holes, secured with R-clips; pin load at tilt-up 2 × 55 kN shear (double shear, use 0.15).",
               "Base plate 30 sits on the pedestal under the grout line; anchors 4 × M24 8.8, 350 Nm after the grout has cured."]
    s.notes_top = (14, 70)
    iso(s, "NS6-410", 300, 60, 100, 70)
    return s


# ======================================================================== NS6-420 gin pole + rigging
def ginpole_sheet():
    tw = TW
    s = S("NS6-420", "GIN POLE AND TILT-UP RIGGING (ERECTION TOOL)", "S355 tube 168.3 × 6.3, plates 25", "94 kg", "1:50")
    v = s.view("rig", 0.02, (175, 105))
    L = M.L_TUBE
    v.line((0, 0), (L + 930, 0))                     # tower lying
    v.circle((L + 930, 0), 3000 * 0.02 / 0.02 * 0.0 + 60)
    v.line((0, 0), (0, 3000))                        # gin pole up
    v.line((0, 3000), (L, 0), "THIN")                # bridle to the tower top
    v.line((0, 3000), (-6000, 0), "THIN")            # pull line to the winch
    v.poly([(-6300, -100), (-5700, -100), (-5700, 200), (-6300, 200)])
    v.text((-6300, 400), "winch + ground anchor ≥ 80 kN", 2.0)
    v.dim((0, -300), (L, -300), -4, kind="h", text=f"{L:.0f} tower")
    v.dim((-300, 0), (-300, 3000), 4, kind="v", text="3 000 gin pole")
    v.text((-6300, 3600), "TILT-UP (tower horizontal on the hinge, head fitted, rotor locked)", 2.8)
    pull = tw["winch_line_pull_kN_ginpole_033H"] * (0.33 * L / 1000) / 3.0
    s.table = [["Item", "Value"], ["Gin pole", "3.0 m, fixed square to the tower on its lugs"], ["Peak line pull", f"≈ {pull:.0f} kN (wind ≤ 10 m/s)"],
               ["Bridle", "2 × wire rope Ø16 6×36 IWRC to the top flange lugs"], ["Pull line", "Ø16 wire rope, winch ≥ 50 kN with 1:2 block"],
               ["Ground anchor", "screw anchors or concrete block, ≥ 80 kN at 6 m"], ["Alternative", "truck crane ≥ 3 t at 9 m reach (lift by the top flange)"]]
    s.table_pos = (240, 285); s.table_widths = [26, 140]
    s.notes = ["Two people + winch operator; wind below 10 m/s; nobody inside the fall zone (1.5 × tower + rotor). Rotor locked with pin NP1-320, blade B1 pointing up away from the ground.",
               "Lower the tower the same way for service; support the head on a trestle 1.0 m high so the lower blade clears the ground.",
               "After erection: fit base nuts and torque (NS6-900), remove the gin pole, keep it with the site kit."]
    s.notes_top = (14, 72)
    iso_assy(s, "A06-tilt-up", 14, 190, 215, 92)
    return s


# ======================================================================== NS6-500 foundation (8 m)
def foundation():
    s = S("NS6-500", "FOUNDATION · SPREAD FOOTING AND ROCK PLINTH (8 m)", "C30/37 XF4 air-entrained; B500C rebar",
          f"{FND['firm soil (dense gravel, moraine)']['concrete_m3']}–{FND['soft volcanic soil (loose ash, pumice sand)']['concrete_m3']} m³ (soil), 2.0 m³ (rock)", "1:40")
    v = s.view("section", 0.025, (100, 150))
    B = FND["firm soil (dense gravel, moraine)"]["B"] * 1000
    v.poly([(-B / 2, -1600), (B / 2, -1600), (B / 2, -1000), (-B / 2, -1000)], hatch=True)
    v.poly([(-600, -1000), (600, -1000), (600, 170), (-600, 170)], hatch=True)
    v.line((-2600, 0), (2600, 0))
    for x in (-280, 280):
        v.line((x, -1450), (x, 300), "HIDDEN")
    for y in (-1550, -1050):
        v.line((-B / 2 + 50, y), (B / 2 - 50, y), "PHANTOM")
    v.dim((-B / 2, -1600), (B / 2, -1600), -6, kind="h", text="B (table)")
    v.dim((B / 2, -1600), (B / 2, -1000), -6, kind="v", text="600")
    v.dim((600, -1000), (600, 170), -6, kind="v", text="1 170 pedestal 1 200 sq.")
    v.leader((-280, -800), (-2400, 900), f"anchor cage NS6-510, {M.FL_BASE['n']} × M24 PCD {M.FL_BASE['pcd']:.0f}", 2.0)
    v.leader((300, -1050), (1500, 700), "mesh Ø16/150 top + bottom (phantom)", 2.0)
    v.leader((0, -600), (1500, -2200), "2 × PE ducts Ø110 to the cabinet", 2.0)
    title(v, -2600, 1100, "SPREAD FOOTING, SECTION", 3.0)
    w = s.view("rock", 0.025, (300, 150))
    w.poly([(-800, -800), (800, -800), (800, 0), (-800, 0)], hatch=True)
    w.line((-1600, -200), (1600, -200), "THIN")
    for x in (-600, -200, 200, 600):
        w.line((x, -3800), (x, -100), "HIDDEN")
    w.dim((-800, 0), (800, 0), 6, kind="h", text="1 600")
    rk = FND["rock (anchored plinth)"]
    w.leader((600, -2500), (1000, -2000), f"8 × Ø{rk['bar_mm']} threadbar on Ø1 200, ≥ {rk['bond_length_m']} m bond", 2.0)
    title(w, -1600, 500, "ROCK PLINTH (lava, basalt)", 3.0)
    rows = [["Ground", "B m", "Concrete m³", "Bearing kPa", "q_rd kPa"]]
    for k, f in FND.items():
        if "B" in f:
            rows.append([k, f"{f['B']}", f"{f['concrete_m3']}", f"{f['bearing_kPa']}", f"{f['q_rd_kPa']}"])
    rows.append(["rock (anchored plinth)", "1.6", "2.0", "–", f"anchors {rk['T_design_kN']} kN"])
    s.table = rows; s.table_pos = (14, 95); s.table_widths = [70, 14, 22, 22, 26]
    s.notes = [f"Base 1.6 m below ground (frost depth); pedestal 1.2 × 1.2 m to +0.17, grout 30 to +0.20 under the base flange. Design base moment {TW['base_flange']['M_design_kNm']} kNm (earthquake 0.5 g + operation governs), parked V_e50 {TW['M_base_design_kNm']['parked V_e50']} kNm.",
               "Characteristic eccentricity ≤ B/4, operation ≤ B/6, bearing on the effective area ≤ q_rd (EN 1997 approach 2 style), as doc 09.",
               "Concrete C30/37 XF4 air-entrained, cover 50; mesh Ø16/150 both ways top and bottom, pedestal 12 × Ø16 verticals + Ø10/150 links; earthing ring 50 mm² Cu round the footing, 2 rods 3 m.",
               "Soil class to be confirmed by a site inspection; soft volcanic ash needs a plate-load test. Rock: drill Ø76, grout, proof-load each anchor to 1.25 × design."]
    s.notes_top = (14, 58)
    iso(s, "NS6-500", 320, 180, 85, 70)
    return s


def anchor_sheet():
    s = S("NS6-510", "ANCHOR CAGE AND TEMPLATE", "M24 8.8 HDG threaded rod; S355 rings 100 × 20", "144 kg", "1:10")
    v = s.view("plan", 0.15, (100, 175))
    fl = M.FL_BASE
    v.circle((0, 0), fl["pcd"] / 2 + 50); v.circle((0, 0), fl["pcd"] / 2 - 50)
    v.bolt_circle((0, 0), fl["pcd"], fl["n"], 26.0, start=15.0)
    for (x, y) in ((M.HINGE["x"] - 100, -190), (M.HINGE["x"] - 100, 190), (M.HINGE["x"] + 50, -190), (M.HINGE["x"] + 50, 190)):
        v.circle((x, y), 12); v.cross((x, y), 20)
    v.dim((-fl["pcd"] / 2, 0), (fl["pcd"] / 2, 0), -50, kind="h", prefix="PCD ", text=f"{fl['pcd']:.0f}")
    v.text((-400, 400), "PLAN: template ring (top) on the anchor cage; 4 hinge anchors at −X", 2.6)
    w = s.view("el", 0.06, (250, 150))
    for x in (-280, 280):
        w.line((x, -1450), (x, 290))
    w.poly([(-330, -1420), (330, -1420), (330, -1400), (-330, -1400)], hatch=True)
    w.poly([(-330, -250), (330, -250), (330, -230), (-330, -230)], hatch=True)
    w.line((-500, 0), (500, 0), "THIN")
    w.dim((330, -1450), (330, 290), -6, kind="v", text="1 740 rod")
    w.text((-500, 400), "ELEVATION (ground at 0)", 2.6)
    s.notes = ["Anchor rods M24 8.8 HDG × 1 740, rolled thread both ends, 2 nuts + plate washer at the bottom ring; top 260 above the pedestal: levelling nut, base flange 35, washer, nut, lock nut.",
               "Set the cage with the template ring (= base flange drilling) bolted on top; position ± 3 mm, level ± 1 mm; the hinge anchors from a second template bolted to the same ring.",
               "Pretension after the grout (≥ 40 MPa) has cured 7 days: 450 Nm (≈ 110 kN) with a calibrated wrench, re-check after 1 month."]
    s.notes_top = (14, 70)
    iso(s, "NS6-510", 300, 150, 100, 110)
    return s


# ======================================================================== NS6-620 cabinet
def cabinet_sheet():
    s = S("NS6-620", "TOWER BASE CABINET, STAND AND RESISTOR BOX POSITION", "enclosure 1.4301 IP55; stand S235 galv.", "95 kg + 18 kg", "1:20")
    v = s.view("front", 0.05, (60, 120))
    v.poly([(0, 0), (40, 0), (40, 1500), (0, 1500)]); v.poly([(760, 0), (800, 0), (800, 1500), (760, 1500)])
    v.poly([(0, 600), (800, 600), (800, 1400), (0, 1400)])
    v.poly([(820, 700), (1420, 700), (1420, 1100), (820, 1100)])
    v.poly([(820, 0), (860, 0), (860, 1150), (820, 1150)]); v.poly([(1380, 0), (1420, 0), (1420, 1150), (1380, 1150)])
    v.line((-300, 0), (1700, 0))
    v.dim((0, 1400), (800, 1400), 6, kind="h", text="800")
    v.dim((0, 600), (0, 1400), 6, kind="v", text="800")
    v.dim((1420, 0), (1420, 600), -6, kind="v", text="600 above ground")
    v.text((0, 1700), "FRONT (from +Y): cabinet left, braking resistor box right (vented)", 2.6)
    rows = [["Cabinet content (doc 12 modules)", "Note"], ["SiC active rectifier 1 200 V, 750 V DC link", "6 kW firmware limits"],
            ["Dump chopper 12 kW + heater feed", "hardware trigger 820 V"], ["AC module 6.5 kW (grid / heater)", "single- or three-phase"],
            ["48 V battery module + 200 Wh aux battery", "yaw-out without grid"], ["Safety relay PL d, K1 contactor", "NS6-600 chain"],
            ["Controller, modem, surge arresters T1+T2", "earth bar to the tower lug"]]
    s.table = rows; s.table_pos = (200, 270); s.table_widths = [80, 50]
    s.notes = ["Stand on two concrete pads 400 × 400 × 600 (or bolted to the pedestal side); cabinet door faces away from the tower; minimum 1.0 m from the tower axis, outside the rotor disc projection is not required (tip at 5 m).",
               "Resistor box NS6-600 mounted 20 mm proud of the stand, louvres down, ≥ 300 mm from the cabinet (heat).",
               "Cables enter from below through the two PE ducts in the footing (NS6-800)."]
    s.notes_top = (14, 60)
    iso(s, "NS6-620", 300, 60, 100, 100)
    iso(s, "NS6-600", 205, 70, 80, 60)
    return s


# ======================================================================== NS6-700 nacelle cover
def cover_sheet():
    C = M.COVER
    s = S("NS6-700", "NACELLE COVER · LOWER TRAY AND UPPER LID (GRP)", "glass/polyester 4 mm, gelcoat RAL 9010, PU foam ribs", "19 + 22 kg", "1:20")
    v = s.view("side", 0.05, (110, 150))
    yf, zf0, zf1, rf = C["front"]; yr, zr0, zr1, rr = C["rear"]
    v.poly([(C["x_front"], zf0), (C["x_rear"], zr0), (C["x_rear"], zr1), (C["x_front"], zf1)])
    v.line((C["x_front"] - 30, C["split_z"]), (C["x_rear"] + 30, C["split_z"]), "PHANTOM")
    v.circle(D.P(365, 0), C["opening_r"], "HIDDEN")
    v.line((-C["bottom_r"], zf0), (C["bottom_r"], zf0), "THICK" if False else "HIDDEN")
    v.dim((C["x_front"], zf0), (C["x_rear"], zr0), -8, kind="h", text=f"{C['x_rear'] - C['x_front']:.0f}")
    v.dim((C["x_front"], zf0), (C["x_front"], zf1), 8, kind="v", text=f"{zf1 - zf0:.0f}")
    v.dim((C["x_rear"], zr0), (C["x_rear"], zr1), -8, kind="v", text=f"{zr1 - zr0:.0f}")
    v.leader((0, C["split_z"]), (900, 1100), f"split line z {C['split_z']:.0f}: flange 30 × 6, 14 × M8 + EPDM", 2.0)
    v.leader((0, zf0), (900, -500), f"bottom opening Ø{2 * C['bottom_r']:.0f} + brush skirt", 2.0)
    title(v, C["x_front"], 1250, "SIDE VIEW (yaw axis at x 0)", 3.0)
    w = s.view("front", 0.05, (300, 150))
    w.poly([(-yf, zf0), (yf, zf0), (yf, zf1), (-yf, zf1)])
    w.poly([(-yr, zr0), (yr, zr0), (yr, zr1), (-yr, zr1)], layer="HIDDEN")
    w.circle((0, D.P(365, 0)[1]), C["opening_r"])
    w.dim((-yf, zf0), (yf, zf0), -8, kind="h", text=f"{2 * yf:.0f}")
    w.text((-yf, 1250), f"FRONT (opening Ø{2 * C['opening_r']:.0f} round the drum, 15 gap)", 2.6)
    s.notes = ["Lofted rounded-rectangle shell, front 1 200 × 1 240 (R330) to rear 820 × 890 (R230); encloses the disc, caliper, bedplate, yaw drives and pad units; drum and spinner stay outside (drum cools in the free air).",
               "Lay-up 4 mm: gelcoat 0.5 + 3 × 450 g CSM + 1 × 300 g woven; PU foam hat-section ribs every 300 mm; lid has 2 lifting points and a gas-strut-held service hatch 500 × 400 over the junction box.",
               "Lower tray hangs on the NS6-710 arms (4 × M10 rubber mounts); the lid bolts to the tray flange. Air in at the bottom skirt, out through a labyrinth vent at the rear top (no forced cooling)."]
    s.notes_top = (14, 62)
    iso(s, "NS6-700-1", 230, 60, 85, 60)
    iso(s, "NS6-700-2", 320, 60, 85, 60)
    return s


def cover_frame_sheet():
    s = S("NS6-710", "COVER ARMS, REAR RAIL, MET MAST NS6-720, JUNCTION BOX NS6-730", "S235 galv.; mast 1.4404 Ø42.4 × 2", "22 kg; 4.5 kg; 9 kg", "1:10")
    v = s.view("arm", 0.1, (60, 200))
    v.poly([(260, 140), (436, 140), (436, 146), (260, 146)], hatch=True)
    v.poly([(430, -196), (436, -196), (436, 146), (430, 146)], hatch=True)
    v.dim((260, 146), (436, 146), 6, kind="h", text="176")
    v.dim((436, -196), (436, 146), -6, kind="v", text="342")
    v.text((260, 280), "ARM (4 off): flat 50 × 6, bolted 2 × M10 to the side plate", 2.4)
    w = s.view("mast", 0.06, (240, 70))
    w.line((0, 0), (0, 1150)); w.line((40, 0), (40, 1150))
    w.circle((20, 1350 + 60), 40)
    w.line((20, 1540), (20, 1940))
    w.dim((-30, 0), (-30, 1940), 4, kind="v", text="1 940 above the rail")
    w.text((80, 1900), "air terminal Ø12 (LPL I), anemometer, vane", 2.2)
    s.notes = ["Rear rail RHS 40 × 40 × 3 on the bedplate rear tie carries the junction box NS6-730 (IP66, 400 × 340 × 150) and the met mast clamp.",
               "Met mast: wind sensors 0.5 m above the cover top (doc 25), air terminal bonded with 50 mm² Cu to the bedplate; the bedplate–tower path goes through the yaw pad brush (NY-410).",
               "Junction box: phase terminals 3 × 16 mm², brake/sensor terminals, surge arresters for the sensor lines, 24 V supply; cable glands at the bottom only."]
    s.notes_top = (14, 70)
    iso(s, "NS6-710", 140, 110, 80, 70)
    iso(s, "NS6-720", 300, 150, 60, 110)
    iso(s, "NS6-730", 330, 60, 70, 60)
    return s


# ======================================================================== NS6-800 cabling
def cabling_sheet():
    s = S("NS6-800", "CABLING ROUTES, EARTHING AND LIGHTNING", "see cable schedule", "–", "schematic")
    v = s.view("route", 0.025, (60, 62))
    L = M.L_TUBE
    v.poly([(-230, 0), (230, 0), (160, L), (-160, L)])
    v.poly([(-385, L + 360 - 200), (520, L + 360 - 200), (520, L + 360 + 690), (-385, L + 360 + 1040)])
    v.circle((-750, L + 360 + 570), 330)
    v.poly([(200, L + 360 + 230), (440, L + 360 + 230), (440, L + 360 + 380), (200, L + 360 + 380)])
    v.line((-40, L + 360 - 290), (-40, 700), "OUTLINE")
    v.line((-40, 700), (300, 700)); v.line((300, 700), (300, -600)); v.line((300, -600), (1500, -600)); v.line((1500, -600), (1500, 600))
    v.poly([(1150, 600), (1950, 600), (1950, 1400), (1150, 1400)])
    v.line((-1000, 0), (2500, 0))
    v.text((250, L + 360 + 420), "junction box", 2.0)
    v.text((50, 3500), "drop cable (free-hanging,\ncleat at the hanger)", 2.0)
    v.text((1200, 1500), "base cabinet", 2.0)
    v.text((320, -500), "PE ducts Ø110", 2.0)
    title(v, -1500, L + 1700, "ROUTE (nacelle → loop → tower → cabinet)", 3.0)
    rows = [["Cable", "Type", "From → to", "Length m"],
            ["W1 power", "H07RN-F 4G10 (3 ph + PE)", "generator terminals → junction box", "3"],
            ["W2 power", "H07RN-F 4G10, 2.5 turns loop", "junction box → hanger loop → hand hole", "12"],
            ["W3 power", "NYY-J 4 × 10 in duct", "hand hole → cabinet", "4"],
            ["W4 brake", "ÖLFLEX 4G1.5 shielded", "caliper → junction box → cabinet", "16"],
            ["W5 sensors", "LiYCY 12 × 0.5", "overspeed, encoder, cam, met, PT100 → cabinet", "16"],
            ["W6 yaw motors", "ÖLFLEX 7G1.5", "2 gearmotors + brakes → cabinet", "16"],
            ["W7 earth", "Cu 50 mm² green/yellow", "air terminal → bedplate; tower lug → earth ring", "6"],
            ["W8 data", "CAT6 outdoor or fibre", "cabinet → house / grid meter", "site"]]
    s.table = rows; s.table_pos = (175, 270); s.table_widths = [24, 52, 104, 18]
    s.notes = ["Cable loop NY-460: power and control cables hang free in the tower below the cleat with 2.5 turns of slack; cable-twist limit ±2.5 turns from the encoder/cam switch (doc 25), auto-untwist when idle.",
               "Lightning (LPL I, doc 02): air terminal → bedplate → yaw pad brush → adapter → tower → base flange → 2 earthing lugs → ring earth (≤ 10 Ω). Generator winding star point not earthed (IT, insulation monitor in the cabinet).",
               "Surge protection: T1+T2 arresters at the cabinet entry for W2/W3, data-line arresters for W5/W8; shields bonded at both ends via the junction box gland plate.",
               "All cables UV and cold resistant to −40 °C; drip loops at the hand hole; glands IP68; label every core at both ends."]
    s.notes_top = (175, 225); s.notes_wrap = 100
    iso_assy(s, "A05-tower-base", 290, 58, 115, 110)
    return s


# ======================================================================== NS6-900 fastener & torque schedule
def fastener_sheet():
    s = S("NS6-900", "FASTENER AND TORQUE SCHEDULE", "ISO 4014/4017, EN 14399-4 (HV), 10.9 zinc-flake unless stated", "–", "–")
    rows = [["Joint", "Fastener", "Qty", "Grade / finish", "Tightening", "Notes"],
            ["Blade root → hub flange", "stud M12 × 75 + nut + washer plate", "30", "10.9, zinc-flake", "95 Nm + 90°", "Loctite 270 in the insert, 40 Nm"],
            ["Hub → drum web", "M16 × 70 ISO 4017", "12", "10.9, zinc-flake", "250 Nm (μ 0.12)", "check after 50 h"],
            ["Spinner → brackets", "M8 × 20 + rubber washer", "3", "A4-70", "12 Nm", ""],
            ["Spindle → bedplate front plate", "M20 × 90 ISO 4014", "12", "10.9", "540 Nm", "from inside, NP1-100"],
            ["Stator carrier → spindle", "M12 × 45", "12", "10.9", "110 Nm", "NP1-200"],
            ["Brake disc → drum", "M12 × 40", "12", "10.9", "110 Nm", "NP1-230"],
            ["Rear cover → drum", "M8 × 20", "24", "A4-80", "20 Nm", "NS6-610"],
            ["Caliper → NP1-310", "M16 (caliper pattern)", "4", "10.9", "250 Nm", "per caliper supplier"],
            ["NP1-310 → side plate", "M16 × 70 + nut", "4", "10.9 HV", "210 Nm", ""],
            ["Lock pin holder → front plate", "M12 × 50", "2", "8.8", "80 Nm", ""],
            ["Yaw inner ring → bedplate", "M16 × 110 + nut", "16", "10.9 HV", "250 Nm", "doc 25"],
            ["Yaw outer ring → NY-400", "M16 × 70", "16", "10.9", "250 Nm", "doc 25"],
            ["Pad unit → bedplate", "M16 × 50", "8", "10.9", "250 Nm", "NY-410"],
            ["Gearmotor bracket → side plate", "M16 × 60 + nut", "8", "8.8", "195 Nm", "NP1-420"],
            ["Gearmotor → bracket", "M10 × 30", "8", "8.8", "49 Nm", ""],
            ["NY-400 → tower top flange", "M20 × 90 + nut", "16", "10.9 HV", "450 Nm", "through bolts"],
            ["Cover arms → side plates", "M10 × 25", "8", "A4-70", "35 Nm", "rubber mounts"],
            ["Cover lid → tray", "M8 × 25 + EPDM", "14", "A4-70", "10 Nm", ""],
            ["Base flange → anchors", "M24 nuts (levelling + top + lock)", f"{M.FL_BASE['n']}", "8.8 HDG anchors", "450 Nm", "after grout cured 7 d"],
            ["Hinge brackets → anchors", "M24 nuts", "4", "8.8 HDG", "350 Nm", ""],
            ["Hand-hole cover", "M8 × 20", "6", "A4-70", "12 Nm", "EPDM gasket"],
            ["Cabinet stand → pads", "M12 anchors", "4", "A4-70", "40 Nm", ""]]
    s.table = rows; s.table_pos = (14, 285); s.table_widths = [62, 64, 10, 40, 34, 70]
    s.notes = ["Torques for lightly oiled zinc-flake threads (μ ≈ 0.12) unless stated; HV sets per EN 14399-4 with the manufacturer's k-class.",
               "Mark every torqued bolt with a torque stripe; record values in the installation report. Re-check all structural joints (blade, hub, yaw, tower) after 50 h and then yearly.",
               "Never re-use M16 / M20 / M24 HV sets that have been fully tightened; replace studs that show thread damage."]
    s.notes_top = (14, 285 - 4.2 * len(rows) - 6)
    return s


# ======================================================================== NS6-910 bought parts
def bought_sheet():
    s = S("NS6-910", "BOUGHT PARTS SPECIFICATION (ENVELOPES AND INTERFACES)", "see lines", "see lines", "–")
    rows = [["Item", "Specification", "Interface", "Candidates / note"],
            ["NS6-911 yaw ring", "4-point ball slewing ring Dpw 360, ext. gear z150 m4, ind. hardened teeth", "inner 16 × M16 PCD 300; outer 16 × M16 PCD 440", "Rollix / Kaydon / IMO; tilt 34.6 kNm s0 ≥ 1.44"],
            ["NS6-912 yaw gearmotor (2)", "0.18 kW, i ≈ 1 680, output ≥ 1 500 Nm static, brake 2 Nm", "flange 4 × M10 on 80 square, pinion z14 m4", "SEW / Bonfiglioli / NORD"],
            ["NS6-913 main bearings (2)", "tapered roller 32028 X (140 × 210 × 45)", "spindle Ø140 f6 / j6", "SKF / FAG / Timken, C3 not needed"],
            ["NS6-914 overspeed sensors (2)", "inductive M18 PNP, −40 °C, IP68", "holder NP1-321", "ifm / Pepperl+Fuchs"],
            ["NS6-915 rotor brake caliper", "spring-applied, power-released, 16 mm disc, 1.5 kNm at r 0.41 m", "4 × M16 on NP1-310", "Svendborg BSFI / Altra / Ringspann"],
            ["Magnets", "200 + 10 × N45SH 30 × 15 × 12, NiCuNi + epoxy", "drawing NP1-220E", "Neo / VAC (non-Asian, doc 23)"],
            ["K1 contactor", "3-pole AC-3 ≥ 63 A 690 V, mirror contacts", "NS6-600", "ABB / Siemens"],
            ["Converter, chopper, modules", "doc 12 SiC rectifier etc., 6 kW firmware", "NS6-620", "in-house (doc 12)"],
            ["Met sensors", "heated cup anemometer + vane, −40 °C", "NS6-720", "Thies / Lufft"],
            ["Yaw encoder", "absolute multi-turn SSI, IP67", "NY-440", "Kübler / Sick"]]
    s.table = rows; s.table_pos = (14, 285); s.table_widths = [44, 120, 80, 120]
    s.notes = ["Envelopes in the CAD model are estimates; replace them with the supplier STEP files before the clash check of the prototype build.",
               "All bought parts: operating −30 °C, survival −40 °C, salt fog C5 (doc 02); certificates 3.1 for structural parts (slewing ring, bearings, bolts)."]
    s.notes_top = (14, 285 - 4.2 * len(rows) - 6)
    iso(s, "NS6-911-O", 20, 60, 80, 70)
    iso(s, "NS6-912-L", 110, 60, 60, 70)
    iso(s, "NS6-915", 180, 60, 60, 70)
    return s


NEW = [rotor_ga, blade_sections, root_insert, mould, root_fixture_sheet, pitch_sheet, spinner_sheet, brackets,
       hinge_sheet, ginpole_sheet, anchor_sheet, cabinet_sheet, cover_sheet, cover_frame_sheet, cabling_sheet,
       fastener_sheet, bought_sheet]
