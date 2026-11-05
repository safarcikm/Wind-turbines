"""Drawing sheets for the yaw system (doc 25). Each function returns a draft.Sheet.

Geometry comes from model.py (single source). Run build.py.
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "nacelle_p1"))
from draft import Sheet  # noqa: E402

import model as M  # noqa: E402

SUM = json.loads((Path(HERE).parent.parent / "analysis" / "yaw" / "results" / "yaw_summary.json").read_text())
MASS = M.masses()
PROJECT = "12 kW WIND TURBINE (ICELAND) · YAW SYSTEM (DOC 25)"
DATE = "2026-11-05"


def sheet(num, ttl, mat, mass, scale):
    return Sheet(num, ttl, mat, mass, scale, rev="A", date=DATE, project=PROJECT)


def rect(v, x0, x1, z0, z1, hatch=False, layer="OUTLINE"):
    v.poly([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], hatch=hatch, layer=layer)


def title(v, x, y, text, h=3.0):
    v.text((x, y), text, h, "left", "bottom")


A, PU, L, E, HG = M.AD, M.PADU, M.LOCK, M.ENC, M.HANG


def adapter_profile():
    (s0, s1), (sz0, sz1) = A["seat_r"], A["seat_z"]
    t0, t1 = A["track_r"]
    tz0, tz1 = A["track_z"]
    plate = [(s0, sz0), (t0, sz0), (t0, tz0), (t1, tz0), (t1, tz1), (s0, tz1)]
    fz0, fz1 = A["flange_z"]
    cone = [(A["cone_top"][0], sz0), (A["cone_top"][1], sz0), (A["cone_bot"][1], fz1), (A["cone_bot"][0], fz1)]
    flange = [(A["flange_r"][0], fz0), (A["flange_r"][1], fz0), (A["flange_r"][1], fz1), (A["flange_r"][0], fz1)]
    g = A["gussets"]
    gus = [(g["r"][0] - 4, sz0), (t0, sz0), (t0, tz0), (g["r"][1], tz0), (g["r"][0] - 4, g["z_low"])]
    return plate, cone, flange, gus


def ring_envelopes(v, mirror=1):
    rect(v, 110 * mirror, 175 * mirror, -60, 0)
    rect(v, 185 * mirror, 304 * mirror, -70, -10)
    v.line((180 * mirror, -35), (180 * mirror, -35), "THIN")
    v.circle((180 * mirror, -35), 9.5, "THIN")


def pad_section(v, mirror=1, hatch=True):
    """Pad unit in its radial plane (u, z)."""
    s = mirror
    b = PU["bracket"]
    rect(v, b["u"][0] * s, b["u"][1] * s, b["z"][0], b["z"][1], hatch)
    up, wb, lo = PU["upper"], PU["web"], PU["lower"]
    uc = (PU["pad"]["u"][0] + PU["pad"]["u"][1]) / 2
    pr = PU["plug"]["d"] / 2
    # C-frame outline (upper jaw + web + lower jaw with the spring bore)
    frame = [(up["u"][0], up["z"][1]), (up["u"][1], up["z"][1]), (up["u"][1], up["z"][0]), (wb["u"][1], up["z"][0]),
             (wb["u"][1], lo["z"][0]), (uc + pr, lo["z"][0]), (uc + pr, PU["piston"]["z"][1]), (uc - pr, PU["piston"]["z"][1]),
             (uc - pr, lo["z"][0]), (lo["u"][0], lo["z"][0]), (lo["u"][0], lo["z"][1]), (wb["u"][0], lo["z"][1]),
             (wb["u"][0], up["z"][0]), (up["u"][0], up["z"][0])]
    v.poly([(x * s, z) for x, z in frame], hatch=hatch)
    tz0, tz1 = A["track_z"]
    pu0, pu1 = PU["pad"]["u"]
    pt, pb = PU["pad"]["t"], PU["pad"]["back"]
    rect(v, pu0 * s, pu1 * s, tz1, tz1 + pt, fill_pad := False)
    rect(v, pu0 * s, pu1 * s, tz1 + pt, tz1 + pt + pb, hatch)
    rect(v, pu0 * s, pu1 * s, tz0 - pt, tz0)
    rect(v, pu0 * s, pu1 * s, tz0 - pt - pb, tz0 - pt, hatch)
    rect(v, (uc - 30) * s, (uc + 30) * s, PU["piston"]["z"][0], PU["piston"]["z"][1], hatch)
    st = PU["stack"]
    n = 8
    hh = (st["z"][1] - st["z"][0]) / n
    for k in range(n):
        z0 = st["z"][0] + k * hh
        if k % 2 == 0:
            v.poly([((uc - 31.5) * s, z0), ((uc - 15.5) * s, z0 + hh), ((uc + 15.5) * s, z0 + hh), ((uc + 31.5) * s, z0)], closed=False)
        else:
            v.poly([((uc - 31.5) * s, z0 + hh), ((uc - 15.5) * s, z0), ((uc + 15.5) * s, z0), ((uc + 31.5) * s, z0 + hh)], closed=False)
    rect(v, (uc - 34) * s, (uc + 34) * s, PU["plug"]["z"][0], PU["plug"]["z"][1], hatch)
    rect(v, (uc - 47) * s, (uc + 47) * s, PU["plug"]["z"][0] - 12, PU["plug"]["z"][0])
    v.centerline((uc * s, PU["plug"]["z"][0] - 20), (uc * s, -15))
    # guide pin (behind the section plane)
    pz = PU["pins"]["z"]
    rect(v, (PU["pins"]["u"] - 12.5) * s, (PU["pins"]["u"] + 12.5) * s, pz[0], pz[1], layer="HIDDEN")
    br = PU["brush"]
    rect(v, br["u"][0] * s, br["u"][1] * s, br["z"][0], br["z"][1])


# ====================================================================== NY-000
def ga():
    s = sheet("NY-000", "YAW SYSTEM · GENERAL ARRANGEMENT", "see parts list",
              f"≈ {SUM['tower_top']['m_tower_side_kg'] + 27.5 + 44 + 15.4 + 4 + 26.4 + 13.4 + 10:.0f} kg (yaw incl. adapter)", "1:5 / 1:8")
    # --- plan view from below (looking up), scale 1:8
    v = s.view("PLAN", 1 / 8, (95, 183))
    title(v, -450, 470, "VIEW FROM ABOVE (bedplate removed) · 1:8 · front of nacelle to the left (−X)", 2.6)
    v.poly([(-330, -260), (330, -260), (330, 260), (-330, 260)], layer="PHANTOM")
    v.circle((0, 0), A["track_r"][1])
    v.circle((0, 0), A["track_r"][0], "HIDDEN")
    v.circle((0, 0), 304)
    v.circle((0, 0), 300, "CENTER")
    v.circle((0, 0), 175)
    v.circle((0, 0), 110)
    v.bolt_circle((0, 0), 300, 16, 17, start=11.25)
    v.centerline((-470, 0), (470, 0))
    v.centerline((0, -470), (0, 470))
    for a in (90, -90):
        c = (328 * math.cos(math.radians(a)), 328 * math.sin(math.radians(a)))
        v.circle(c, 32)
        v.circle(c, 55, "HIDDEN")
        v.text((c[0] + 70, c[1]), "gearmotor", 2.2, "left", "center")
    for a in PU["angles"]:
        t = math.radians(a)
        pts = [(u, w) for u, w in ((315, -85), (440, -85), (440, 85), (315, 85))]
        v.poly([(u * math.cos(t) - w * math.sin(t), u * math.sin(t) + w * math.cos(t)) for u, w in pts])
        c = (380 * math.cos(t), 380 * math.sin(t))
        v.leader(c, (c[0] - 60, c[1] + (90 if a > 0 else -90)), "NY-410", 2.2)
    t = math.radians(L["angle"])
    v.poly([(u * math.cos(t) - w * math.sin(t), u * math.sin(t) + w * math.cos(t))
            for u, w in ((300, -50), (430, -50), (430, 50), (300, 50))])
    v.leader((365 * math.cos(t), 365 * math.sin(t)), (420, 420), "NY-430 lock", 2.2)
    t = math.radians(E["angle"])
    c = (E["r"] * math.cos(t), E["r"] * math.sin(t))
    v.circle(c, 44)
    v.leader(c, (420, -430), "NY-440 encoder", 2.2)
    v.circle((0, 0), HG["od"] / 2, "HIDDEN")
    v.text((-10, -20), "NY-460", 2.0, "right", "top")
    v.text((-430, -300), "bedplate outline 660 × 520 (phantom)", 2.0)
    # --- radial section through the left pad unit, scale 1:5 (u to the right)
    w = s.view("SECTION", 1 / 5, (205, 205))
    title(w, 0, 95, f"SECTION A-A through the pad unit at {PU['angles'][0]}° · 1:5", 2.6)
    plate, cone, flange, gus = adapter_profile()
    for p in (plate, cone, flange):
        w.poly(p, hatch=True)
    w.poly(gus, layer="OUTLINE")
    ring_envelopes(w)
    pad_section(w)
    rect(w, 0, 450, 0, 40, layer="PHANTOM")
    w.text((300, 45), "bedplate bottom plate 40 (NP1-300)", 2.0)
    rect(w, HG["od"] / 2 - HG["t"], HG["od"] / 2, HG["z"][0], HG["z"][1], True)
    w.centerline((0, -380), (0, 70))
    w.text((5, -375), "yaw axis", 2.0)
    w.dim((0, -95), (A["track_r"][1], -95), -55, kind="h", prefix="R")
    w.dim((0, 0), (0, -360), 28, kind="v", text="360 to tower flange")
    w.leader((330, -78), (480, -220), "track 15, faces Ra 1.6, flat 0.1", 2.0)
    w.leader((130, -60), (330, -290), "slewing ring Dpw 360, 53 × Ø19, gear tip R 304", 2.0)
    w.text((215, -330), "NY-400", 2.2)
    s.table = [["Item", "Part", "Qty", "Make/buy", "Mass"],
               ["1", "NY-400 tower-top adapter (S355J2+N weldment)", "1", "make", f"{MASS['NY-400 adapter (incl. tower-side flange)']:.0f} kg"],
               ["2", "Slewing ring Dpw 360, ext. gear z150 m4, ind. hardened teeth", "1", "buy", "≈ 55 kg"],
               ["3", "Gearmotor 0.18 kW 4-pole, 1:1,680 planetary, 2 Nm motor brake", "2", "buy", "≈ 22 kg"],
               ["4", "NP1-420 drive bracket (doc 16)", "2", "make", "7.7 kg"],
               ["5", "NY-410 friction pad unit", "2", "make", "13 kg"],
               ["6", "NY-430 yaw lock", "1", "make", f"{MASS['NY-430 yaw lock']:.1f} kg"],
               ["7", "NY-440 encoder + cam limit switch unit", "1", "make/buy", "6.9 kg"],
               ["8", "NY-460 cable hanger", "1", "make", f"{MASS['NY-460 cable hanger']:.0f} kg"],
               ["9", "Bolts: 16 M16 inner, 16 M16 outer (from below), 16 M20 tower", "48", "buy", ""],
               ["10", "Heated 2D ultrasonic + heated cup/vane on the nacelle mast", "1+1", "buy", ""]]
    s.table_pos = (12, 115)
    s.table_widths = [9, 100, 9, 16, 16]
    s.notes = ["No hydraulics on the yaw system. Holding: 2 spring-applied motor brakes (fail-safe) through the gear train; damping: 2 passive pad units, 2.4 to 3.6 kNm.",
               "Design yaw moment held 8 kNm by ONE pinion (backlash) without friction credit; gearbox static rating ≥ 1,500 Nm output.",
               "All bolts 10.9, preload with calibrated torque, M16 90 kN, M20 110 kN. Grease the ring per supplier (−40 °C synthetic).",
               "Yaw rate 0.5 °/s at 1,500 rpm. One VFD drives both motors; the safety chain opens the brake supply directly."]
    s.notes_top = (12, 62)
    s.notes_wrap = 105
    return s


# ====================================================================== NY-400
def adapter_sheet():
    s = sheet("NY-400", "TOWER-TOP ADAPTER WITH FRICTION TRACK", "S355J2+N plate and tube, weldment",
              f"{MASS['NY-400 adapter (incl. tower-side flange)']:.0f} kg (model)", "1:4")
    v = s.view("SEC", 0.25, (60, 200))
    plate, cone, flange, gus = adapter_profile()
    for p in (plate, cone, flange):
        v.poly(p, hatch=True)
    v.poly(gus)
    v.centerline((0, -390), (0, 30))
    title(v, -40, 90, "HALF SECTION (between gussets) · 1:4", 3.0)
    v.dim((0, -70), (A["track_r"][1], -70), 30, kind="h", prefix="R")
    v.dim((0, -70), (A["track_r"][0], -70), 18, kind="h", prefix="R")
    v.dim((0, -95), (A["seat_r"][0], -95), -12, kind="h", prefix="R")
    v.dim((A["track_r"][1], -70), (A["track_r"][1], -85), -8, kind="v")
    v.dim((A["seat_r"][0], -70), (A["seat_r"][0], -95), 10, kind="v")
    v.dim((A["flange_r"][1], -330), (A["flange_r"][1], -360), -8, kind="v")
    v.dim((A["track_r"][1], -70), (A["track_r"][1], -360), -24, kind="v", text="290")
    v.dim((0, -360), (A["flange_r"][1], -360), -12, kind="h", prefix="R")
    v.dim((0, -360), (A["flange_r"][0], -360), -22, kind="h", prefix="R")
    v.leader((176, -200), (280, -250), "cone t 12, Ø396 → Ø332 outside", 2.0)
    v.leader((260, -110), (330, -160), "8 gussets t 12, at 11.25° + k·45°", 2.0)
    v.leader((220, -82), (330, -20), "16 × Ø17 PCD 440 at 0° + k·22.5° (M16 from below)", 2.0)
    v.leader((190, -345), (330, -300), "16 × Ø22 PCD 380 at 11.25° + k·22.5° (M20)", 2.0)
    v.leader((395, -77), (450, -110), "both faces Ra 1.6, flat 0.1, parallel 0.1", 2.0)
    # plan quarter
    p = s.view("PLAN", 0.25, (290, 170))
    title(p, -40, 420, "PLAN FROM ABOVE · 1:4", 3.0)
    for r in (A["track_r"][1], A["track_r"][0], A["seat_r"][0]):
        p.arc((0, 0), r, 0, 180)
    p.arc((0, 0), 220, 0, 180, "CENTER")
    for k in range(9):
        a = math.radians(22.5 * k)
        p.circle((220 * math.cos(a), 220 * math.sin(a)), 8.5)
    w = A["window"]
    p.centerline((-420, 0), (420, 0))
    p.text((-300, 300), "seat face for the outer ring: flat 0.05, Ra 3.2", 2.0)
    p.text((-300, 270), f"window {w['x'][1]-w['x'][0]:.0f} × {w['z'][1]-w['z'][0]:.0f} in the cone at +X (rear)", 2.0)
    s.notes = ["Weld cone to seat plate and to flange with full-penetration welds (ISO 5817 B), gussets with 5 mm double fillets; stress relieve, then machine seat, track faces and flange in one set-up.",
               "Seat and track are one machined plate: 25 mm blank, track turned to 15 mm (r 250 to 395). Track faces left bare under the pads; all other surfaces C5-VH coating (ISO 12944, zinc-rich primer).",
               "Bolt loads at the SLM tilt moment 34.6 kNm: outer ring 19.1 kN per M16 (preload 90 kN), tower flange 32.0 kN per M20 (preload 110 kN).",
               "Replaces the NP1-400 proposal of doc 16 (25 mm plate to Ø840, 143 kg): track moved in to r 395 and thinned to 15 mm because the pads only clamp 5.3 kN.",
               "Gussets stay inside r 300 and below the track so the lower pad jaws (r ≥ 318) pass all the way round."]
    return s


# ====================================================================== NY-410
def pad_sheet():
    pd = SUM["pads"]
    s = sheet("NY-410", "FRICTION PAD UNIT (PASSIVE, SPRING-LOADED)", "frame S355J2+N, pins 1.4462",
              "13 kg (model)", "1:2")
    v = s.view("SEC", 0.5, (-70, 225))
    title(v, 240, 40, "SECTION IN THE RADIAL PLANE · 1:2", 3.0)
    rect(v, 250, 395, -85, -70, True)
    v.text((260, -95), "track (NY-400)", 2.0, "left", "top")
    pad_section(v)
    uc = 355
    v.dim((PU["bracket"]["u"][0], 0), (PU["bracket"]["u"][1], 0), 12, kind="h")
    v.dim((PU["pad"]["u"][0], -165), (PU["pad"]["u"][1], -165), -16, kind="h")
    v.dim((440, 0), (440, -165), -14, kind="v")
    v.dim((440, -70), (440, -85), -26, kind="v")
    v.leader((uc + 25, -127), (480, -135), "8 × DIN 2093 B 63 in series, preset 7.0 mm → 5.3 kN", 2.0)
    v.leader((uc + 30, -153), (480, -165), "M68 × 2 adjuster + lock nut, set with a load cell", 2.0)
    v.leader((uc + 20, -61), (480, -50), "pad 12 + back plate 6 (both sides)", 2.0)
    v.leader((uc + 20, -40), (480, -20), "guide pins Ø25 f7 (behind), PTFE-lined bushes", 2.0)
    v.leader((400, -78), (480, -92), "lightning contact (Cu braid 50 mm² to bedplate)", 2.0)
    # side view along u (v horizontal)
    w = s.view("SIDE", 0.5, (345, 225))
    title(w, -110, 40, "VIEW FROM OUTSIDE (radial) · 1:2", 3.0)
    b = PU["bracket"]
    rect(w, b["v"][0], b["v"][1], b["z"][0], b["z"][1])
    rect(w, PU["upper"]["v"][0], PU["upper"]["v"][1], PU["upper"]["z"][0], PU["upper"]["z"][1])
    rect(w, PU["web"]["v"][0], PU["web"]["v"][1], PU["web"]["z"][0], PU["web"]["z"][1])
    for vv in PU["pins"]["v"]:
        rect(w, vv - 12.5, vv + 12.5, PU["pins"]["z"][0], PU["pins"]["z"][1], layer="HIDDEN")
    w.dim((b["v"][0], 0), (b["v"][1], 0), 10, kind="h")
    w.dim((PU["pins"]["v"][0], -75), (PU["pins"]["v"][1], -75), -40, kind="h")
    w.dim((PU["web"]["v"][0], -165), (PU["web"]["v"][1], -165), -12, kind="h")
    s.table = [["Item", "Part", "Qty", "Material / spec"],
               ["1", "Bracket 170 × 125 × 20, 4 × Ø17 to the bedplate", "1", "S355J2+N"],
               ["2", "C-frame (upper jaw, web, lower jaw), machined", "1", "S355J2+N"],
               ["3", "Guide pin Ø25 f7 × 55, pressed into item 1", "2", "1.4462 duplex"],
               ["4", "Pad 90 × 60 × 12 on 6 mm back plate", "2", "organic industrial pad, μ 0.40 ± 20 %"],
               ["5", "Piston Ø60 × 10", "1", "1.4462"],
               ["6", "Disc spring DIN 2093 B 63 (63 × 31 × 2.5)", "8", "51CrV4, zinc-flake"],
               ["7", "Adjuster M68 × 2 + lock nut", "1+1", "1.4462"],
               ["8", "Lightning contact block + Cu braid 50 mm²", "1", "CuSn / Cu"]]
    s.table_pos = (12, 115)
    s.table_widths = [9, 80, 9, 60]
    s.notes = [f"Floating C-frame: the springs push the lower pad up; the reaction pulls the frame down onto the upper pad, so both faces clamp {pd['F_clamp_per_unit_kN']:.1f} kN at any pad wear.",
               f"Two units give {pd['T_kNm']['min']:.1f} to {pd['T_kNm']['max']:.1f} kNm (μ 0.32 to 0.48), {pd['T_kNm']['nominal']:.1f} kNm nominal, {pd['T_min_over_op_p95']:.2f} × the 95th percentile operating yaw moment.",
               f"Pad pressure {pd['pad_pressure_MPa']:.2f} MPa, sliding speed {pd['sliding_speed_mm_s']:.1f} mm/s, heat {pd['heat_W']:.0f} W. Estimated wear {pd['wear']['wear_per_pad_20y_mm']:.1f} mm in 20 years of {pd['wear']['usable_mm']:.0f} mm usable (to confirm by test).",
               f"Spring stack at {pd['disc']['s_set_over_h0']:.2f} h0 per disc: one year of wear lowers the clamp by {pd['wear']['clamp_drop_after_1y'] * 100:.0f} %. Re-set at the yearly service (load cell between the pads).",
               "Pad change without lifting the nacelle: back off the adjuster, swing the frame down on the pins, slide the pads out sideways."]
    s.notes_top = (180, 112)
    s.notes_wrap = 70
    return s


# ====================================================================== NY-430
def lock_sheet():
    s = sheet("NY-430", "YAW LOCK (SERVICE)", "housing S355J2+N, block 42CrMo4+QT",
              f"{MASS['NY-430 yaw lock']:.1f} kg (model)", "1:1")
    v = s.view("SEC", 1.0, (-170, 190))
    title(v, 190, 95, "SECTION IN THE RADIAL PLANE (engaged) · 1:1", 3.0)
    h, b = L["housing"], L["block"]
    rect(v, h["u"][0], h["u"][1], h["z"][0], h["z"][1])
    rect(v, h["u"][0], h["u"][1] - 15, -61, -19, layer="HIDDEN")
    rect(v, b["u"][0], b["u"][1], b["z"][0], b["z"][1], True)
    rect(v, b["u"][1], b["u"][1] + 120, -52, -28, layer="OUTLINE")
    rect(v, b["u"][1] + 120, b["u"][1] + 136, -58, -22)
    rect(v, 185, 304, -70, -10, layer="PHANTOM")
    v.text((190, -78), "ring gear z150 m4 (tip R 304)", 2.0, "left", "top")
    rect(v, 150, 395, -95, -70, layer="PHANTOM")
    v.dim((b["u"][0], -20), (b["u"][1], -20), 30, kind="h", tpos=0.4)
    v.dim((h["u"][0], 0), (h["u"][1], 0), 14, kind="h")
    v.dim((b["u"][0], -60), (b["u"][0] + L["travel"], -60), -18, kind="h", text=f"travel {L['travel']:.0f}")
    v.leader((298, -40), (330, 65), "2 teeth, gear-space profile by wire EDM", 2.0)
    v.leader((b["u"][1] + 60, -40), (470, 40), "M24 screw, hex 41, turned by hand", 2.0)
    v.leader((h["u"][1] - 30, -10), (470, 15), "inductive sensor 'lock engaged' → inhibits the yaw drive", 2.0)
    s.notes = ["Use: service only (yaw drives locked out). Turn the nacelle until a tooth space is opposite the block (encoder target), then screw the block in.",
               "Strength: design yaw moment 8 kNm → 26.7 kN at the gear pitch radius on two teeth; tooth root shear and bending of the block S ≥ 3 (42CrMo4+QT, 900 MPa).",
               "The housing bolts to the bedplate underside with 4 × M16 at the rear left corner (38.2°). Grease the slide; boot over the screw."]
    return s


# ====================================================================== NY-440
def encoder_sheet():
    s = sheet("NY-440", "YAW ENCODER AND CAM LIMIT SWITCH UNIT", "bracket S355J2+N, pinion 42CrMo4+QT",
              "6.9 kg incl. instruments", "1:3")
    v = s.view("EL", 1 / 3, (110, 170))
    title(v, -200, 260, "ELEVATION, VIEW TOWARDS THE SIDE PLATE · 1:3", 3.0)
    rect(v, -45, 45, E["face"][0], E["face"][1], True)
    rect(v, -10, 10, E["face"][1], E["encoder"]["z"][0])
    rect(v, -35, 35, -8, 7)
    rect(v, -30, 30, 7, 30)
    rect(v, -29, 29, E["encoder"]["z"][0], E["encoder"]["z"][1])
    rect(v, -40, 40, E["cam"]["z"][0], E["cam"]["z"][1])
    rect(v, -150, 150, -70, -10, layer="PHANTOM")
    v.text((-145, -75), "ring gear (phantom)", 2.0, "left", "top")
    v.centerline((0, -70), (0, 240))
    v.dim((-45, E["face"][0]), (-45, E["face"][1]), 10, kind="v")
    v.dim((-40, E["cam"]["z"][0]), (-40, E["cam"]["z"][1]), 10, kind="v")
    v.dim((-29, E["encoder"]["z"][0]), (-29, E["encoder"]["z"][1]), 22, kind="v")
    v.leader((40, -35), (160, -110), f"pinion z{E['z_pinion']} m4, b 20, scissor (spring-loaded split), no backlash", 2.0)
    v.leader((29, 70), (160, 70), "multiturn absolute encoder, SSI/CANopen, 13 + 12 bit, −40 °C", 2.0)
    v.leader((40, 165), (160, 165), "geared cam limit switch: untwist warning ±2.75, safety ±3 turns", 2.0)
    v.leader((35, 0), (160, -40), "arm 15 mm above the gear, plate bolted to the side plate", 2.0)
    s.notes = [f"Ratio ring/pinion 150/{E['z_pinion']} = {150 / E['z_pinion']:.2f}: ±3 nacelle turns = ±{3 * 150 / E['z_pinion']:.2f} turns at the switch.",
               f"Centre distance {E['r']:.0f} mm at {E['angle']:.0f}° (right side, behind the drive), outside the side plate so the instruments stand beside it.",
               "Cam contacts are positively opened, wired into the hardwired safety chain (PL d). The encoder is only for control (yaw angle, twist count, untwist).",
               "Plausibility: proximity switch at 0° on a ring tooth marker checks the encoder every revolution."]
    return s


# ====================================================================== NY-460
def hanger_sheet():
    cb = SUM["cable"]
    s = sheet("NY-460", "CABLE HANGER AND TWIST LOOP", "tube S355 Ø168.3 × 4.5, flange S355J2+N",
              f"{MASS['NY-460 cable hanger']:.0f} kg (model)", "1:5 / NTS")
    v = s.view("SEC", 0.2, (90, 150))
    title(v, -250, 230, "HANGER IN THE YAW BORE · 1:5", 3.0)
    ro, ri = HG["od"] / 2, HG["od"] / 2 - HG["t"]
    for sg in (1, -1):
        rect(v, sg * ri, sg * ro, HG["z"][0], HG["z"][1], True)
        rect(v, sg * ri, sg * HG["flange"]["od"] / 2, HG["flange"]["z"], HG["flange"]["z"] + HG["flange"]["t"], True)
        rect(v, sg * 110, sg * 175, -60, 0, layer="PHANTOM")
        v.poly([(sg * 154, -330), (sg * 166, -330), (sg * 198, -95), (sg * 186, -95)], layer="PHANTOM")
        rect(v, sg * 110, sg * 330, 0, 40, layer="PHANTOM")
    rect(v, -75, 75, HG["cleat_z"] - 15, HG["cleat_z"] + 15)
    v.centerline((0, -340), (0, 80))
    v.dim((-ro, HG["z"][1]), (ro, HG["z"][1]), 18, kind="h", prefix="Ø", text=f"{HG['od']:.1f}")
    v.dim((ro, HG["z"][1] + 12), (ro, HG["z"][0]), -22, kind="v")
    v.leader((60, HG["cleat_z"]), (200, -330), "cleat bar: 4 cable cleats (rubber-lined)", 2.0)
    v.leader((120, 46), (240, 90), "flange Ø260 × 12 on the bedplate, 4 × M12", 2.0)
    # loop schematic
    w = s.view("LOOP", 1.0, (245, 75))
    title(w, -60, 205, f"TWIST LOOP IN THE TOWER (not to scale)", 3.0)
    rect(w, -20, 20, 0, 190, layer="PHANTOM")
    w.line((-8, 185), (-8, 30), "OUTLINE")
    w.line((8, 185), (8, 30), "OUTLINE")
    w.line((-12, 185), (12, 185))
    w.line((-25, 30), (25, 30))
    w.text((25, 185), "rotating cleat (NY-460), turns with the nacelle", 2.0, "left", "center")
    w.text((25, 108), f"free twist length {cb['chosen_m']:.1f} m (≥ {cb['free_length_m']:.1f} m for ±3 turns at {cb['torsion_deg_per_m']:.0f} °/m)", 2.0, "left", "center")
    w.text((25, 95), "loose PE spacer ring every 2 m, guide ring at mid-length", 2.0, "left", "center")
    w.text((25, 30), "fixed cleat on a tower cross-bar, then cable tray to the base", 2.0, "left", "center")
    s.table = [["Cable (all torsion-rated for wind turbine loops, −40 °C)", "Ø approx."],
               ["Generator 4G6 + screen, 0.6/1 kV (doc 12)", "20 mm"],
               ["48 V auxiliary / backup supply 2 × 10 mm²", "14 mm"],
               ["Safety chain + control signals 12 × 1.0 mm², screened", "12 mm"],
               ["Industrial Ethernet (Cat 6A, torsion) + fibre option", "12 mm"],
               ["Earthing: separate Cu braid via the yaw lightning contact", "–"]]
    s.table_pos = (12, 282)
    s.table_widths = [125, 25]
    s.notes = ["Untwist by the controller at ±2.5 turns when the 10 min mean wind is below 5 m/s; safety chain opens at ±3 turns (NY-440 cam switch).",
               "No slip ring for power (doc 07). Cables leave the bedplate inside the hanger tube, so they never touch the rotating ring or the adapter.",
               "Inspection through the adapter window (NY-400) at every service: sheath wear, cleats, twist count against the encoder."]
    return s


ALL = [ga, adapter_sheet, pad_sheet, lock_sheet, encoder_sheet, hanger_sheet]
