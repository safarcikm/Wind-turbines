"""M8 12 kW build book (doc 37): design summary, part catalogue (axonometric view of every part), the NM8 drawing
set, the reused drawings, the assembly sequence and the erection and commissioning checklist, in one PDF.

    python3 buildbook8.py        -> out/M8-build-book.pdf
Needs: model8.py, bom8.py, iso8.py, drawings8.py outputs. Page helpers come from cad/turbine_6kw/buildbook6.py.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "cad" / "turbine_6kw"))
import buildbook6 as BB  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.pdfgen import canvas  # noqa: E402
from pypdf import PdfReader, PdfWriter  # noqa: E402

W, H, INK, ACC, GREY = BB.W, BB.H, BB.INK, BB.ACC, BB.GREY
paras, table, image, section_divider = BB.paras, BB.table, BB.image, BB.section_divider
OUT = HERE / "out"
ISO = OUT / "iso"
RES = ROOT / "analysis" / "variant_m8" / "results"
T8 = json.loads((RES / "tower8_m8.json").read_text())
TK = "stiff_final_sim8" if "stiff_final_sim8" in T8["towers"] else "stiff"
TW = T8["towers"][TK]["tower"]
FND = T8["towers"][TK]["foundations"]
PARTS = json.loads((OUT / "model8-parts.json").read_text())
BOM = json.loads((OUT / "bom8.json").read_text())
STEPS = json.loads((ISO / "steps" / "steps.json").read_text())
SP = json.loads((RES / "spindle_m8.json").read_text())
HY = json.loads((RES / "hub_yaw_m8.json").read_text())
GEN = json.loads((RES / "generator_m8.json").read_text())
DLC8 = RES / "dlc8_m8" / "dlc_summary.json"
DATE = BB.DATE
PAGE = BB.PAGE


def frame_page(c, title, section=""):
    PAGE[0] += 1
    c.setFillColor(colors.white)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setStrokeColor(INK); c.setLineWidth(0.6)
    c.rect(10 * mm, 10 * mm, W - 20 * mm, H - 20 * mm)
    c.setFont("DVB", 9); c.setFillColor(GREY)
    c.drawString(14 * mm, H - 8 * mm, "12 kW WIND TURBINE M8 · Ø8.0 m · 8 m TOWER · BUILD BOOK rev A")
    c.drawRightString(W - 14 * mm, H - 8 * mm, section)
    c.setFont("DV", 8)
    c.drawString(14 * mm, 5 * mm, f"{DATE} · NOT CHECKED: prototype release only after review (doc 37 §9)")
    c.drawRightString(W - 14 * mm, 5 * mm, f"page {PAGE[0]}")
    if title:
        c.setFont("DVB", 18); c.setFillColor(INK)
        c.drawString(16 * mm, H - 24 * mm, title)


BB.frame_page = frame_page


def cover(c):
    frame_page(c, "", "")
    c.setFillColor(INK); c.setFont("DVB", 30)
    c.drawString(20 * mm, H - 45 * mm, "12 kW Wind Turbine M8")
    c.setFont("DV", 17); c.setFillColor(ACC)
    c.drawString(20 * mm, H - 57 * mm, "Build book · Ø8.0 m rotor · 8 m tower · revision A")
    image(c, ISO / "A01-turbine.png", 230 * mm, 18 * mm, 175 * mm, 260 * mm)
    en = T8["energy"]
    rows = [["Item", "M8 on the 8 m tower"], ["Rated power", "12 kW electric at 10.0 m/s (hub height)"],
            ["Rotor", "Ø8.0 m, 3 glass/epoxy blades with carbon caps, TSR 5.5, 131 rpm, collective pitch"],
            ["Regulation", "variable speed + one electric pitch cylinder (supercap backed); feather in storms"],
            ["Generator", f"Rev D direct-drive PM: Rev C + 2 magnet rows, stack {GEN['geometry']['stack_mm']:.0f} mm, 28 turns"],
            ["Brake", "3 spring-applied calipers, 14.4 kNm, rotor lock pin"],
            ["Hub height", f"8.0 m; lowest blade tip {8.0 - 4.0:.1f} m above ground"],
            ["Tower", f"one-piece tilt-up monopole Ø{TW['geometry']['D_base'] * 1000:.0f} → Ø{TW['geometry']['D_top'] * 1000:.0f}, t {TW['geometry']['t_mm'][0]}/{TW['geometry']['t_mm'][1]}, {TW['mass_kg']:.0f} kg, f1 {TW['f1_rigid_Hz']} Hz"],
            ["Foundation", f"spread footing {FND['firm soil (dense gravel, moraine)']['B']}–{FND['soft volcanic soil (loose ash, pumice sand)']['B']} m square, {FND['firm soil (dense gravel, moraine)']['concrete_m3']}–{FND['soft volcanic soil (loose ash, pumice sand)']['concrete_m3']} m³; rock plinth 2 m³"],
            ["Head mass", f"{PARTS['head_kg']:.0f} kg above the tower flange (CAD, every part)"],
            ["Energy (vs 18 m tower)", " · ".join(f"{k} {v['aep8_kWh'] / 1000:.1f} MWh (−{v['loss_pct']:.0f} %)" for k, v in en.items())]]
    paras(c, [("table", table(rows, [40, 150]))], 20 * mm, 120 * mm, 195 * mm, 100 * mm)
    paras(c, [("p", "Contents: design summary (§1); general arrangement and BOM (§2); part catalogue with an axonometric view of every part (§3); "
                    "the NM8 drawing set rev A (§4); reused drawings (§5); the assembly sequence in 13 steps (§6); erection, commissioning and inspection (§7); open items (§8)."),
              ("p", "Sources: docs 35 and 37, analysis/variant_m8 (dlc8_m8.py, tower8_m8.py, spindle_m8.py, hub_yaw_m8.py, generator_m8.py), cad/turbine_m8 (model8.py, drawings8.py, iso8.py, bom8.py), cad/hub_m8. "
                    "Every number comes from those scripts; re-run them to update the book.")],
          20 * mm, 30 * mm, 195 * mm, 80 * mm)
    c.showPage()


def contents(c, toc):
    frame_page(c, "Contents", "")
    rows = [["§", "Section", "Page"]] + [[a, b, str(p)] for a, b, p in toc]
    paras(c, [("table", table(rows, [14, 160, 18], fs=10))], 20 * mm, 40 * mm, 200 * mm, 225 * mm)
    paras(c, [("h2", "How to use this book"),
              ("li", "Every part has a card in §3 (view, part number, material, mass, drawing). The drawing follows in §4 (new and changed M8 parts) or §5 (reused unchanged)."),
              ("li", "Build in the order of §6. Each step lists the parts, the torques (NM8-900) and the checks that must be signed before the next step."),
              ("li", "Site work (footing, erection, commissioning) is §7. Keep the signed checklists with the turbine file."),
              ("li", "All drawings are NOT CHECKED. Release for the prototype only after the review and the checks of §8.")],
          235 * mm, 40 * mm, 165 * mm, 225 * mm)
    c.showPage()


def summary(c):
    frame_page(c, "1  Design summary: 12 kW M8 on an 8 m tower", "§1 design summary")
    en = T8["energy"]
    rows_e = [["Site (roughness z0)", "Mean wind 18 m → 8 m", "AEP 18 m", "AEP 8 m", "Loss", "Turbulence"]]
    for v in en.values():
        rows_e.append([f"{v['name']} ({v['z0']} m)", f"{v['v18']:.1f} → {v['v8']:.2f} m/s", f"{v['aep18_kWh'] / 1000:.1f} MWh",
                       f"{v['aep8_kWh'] / 1000:.1f} MWh", f"−{v['loss_pct']:.0f} %", f"+{v['turb_increase_pct']:.0f} %"])
    rows_t = [["Tower check", "Value"], ["Shell", f"Ø{TW['geometry']['D_base'] * 1000:.0f} → Ø{TW['geometry']['D_top'] * 1000:.0f}, t {TW['geometry']['t_mm'][0]}/{TW['geometry']['t_mm'][1]}, {TW['mass_kg']:.0f} kg"],
              ["f1 rigid / soft soil + ice", f"{TW['f1_rigid_Hz']} / {TW['f1_soft_ice_Hz']} Hz (window 2.51–5.95)"],
              ["3P exclusion zone", f"{TW['exclusion_zone_rpm'][0]:.0f}–{TW['exclusion_zone_rpm'][1]:.0f} rpm"],
              ["Governing case", f"{TW['governing']}, utilisation {TW['util_max']}"],
              ["Fatigue damage (base)", f"{list(TW['fatigue_damage'].values())[0]:.2f}"],
              ["Base bolts", f"{TW['base_flange']['bolts']} × {TW['base_flange']['size']} on Ø{TW['base_flange']['circle_m'] * 1000:.0f}"],
              ["Tilt-up", f"{TW['tilt_up_base_moment_kNm']} kNm, line pull {TW['winch_line_pull_kN_ginpole_033H']} kN (gin pole 0.33 H)"]]
    sim = ""
    if DLC8.exists():
        d = json.loads(DLC8.read_text())["ultimate_envelope"]
        sim = (f"Simulated at 8 m (103 cases, shear 0.25, turbulence +20 %, stiff tower): Mtilt {d['Mtilt']['design'] / 1e3 if d['Mtilt']['design'] > 1e3 else d['Mtilt']['design']:.1f}, "
               f"thrust {d['thrust']['design'] / 1e3 if d['thrust']['design'] > 1e3 else d['thrust']['design']:.1f} (design values, doc 37 §2).")
    left = [("h2", "What the 8 m tower changes"),
            ("p", "The M8 turbine of doc 35 is unchanged above the yaw bearing except for what the detail design of doc 37 found: the third brake caliper moved to 135° (the rotor lock holds 90°), "
                  "the hub rear gussets were shortened to clear the drum web, the spinner grew to Ø1 040 to enclose the pitch bearings, and the nacelle cover was lengthened 15 mm at the front."),
            ("p", "<b>Tower.</b> A soft-stiff tower is impossible at 8 m, so the tower is <b>stiff</b>: f1 above 1.15 × 1P at 131 rpm and below 3P at rated. "
                  "The 3P excitation crosses f1 at low speed, so the controller passes that speed band under torque."),
            ("table", table(rows_t, [50, 110], fs=8)),
            ("p", "<b>Loads.</b> The whole aeroelastic load set was rerun at 8 m hub height with stronger shear and turbulence and the stiff tower. " + sim +
                  " The 18 m controller tripped often in the stronger turbulence and once reached 220 rpm, so the 8 m controller has a faster speed loop (6 rad/s), a faster normal pitch rate (20°/s) and the trip at 165 rpm; peak 181 rpm (design 184). Blade, spindle, bearings, brake and tower were re-checked with the larger of the 18 m and 8 m envelopes; the brake grows to 14.4 kNm.")]
    paras(c, left, 16 * mm, 20 * mm, 190 * mm, 245 * mm)
    right = [("h2", "Energy at 8 m"),
             ("p", "Slower, more turbulent wind near the ground. Log wind profile per site roughness:"),
             ("table", table(rows_e, [46, 34, 20, 20, 13, 20], fs=7.5)),
             ("li", "Coast, highland and open land lose 16–27 %; a sheltered farm loses 42 % and should use the 18 m tower."),
             ("li", "Safety: lowest blade tip 4.0 m above ground. Fenced keep-out radius 5 m; ice-fall zone 24 m when icing is possible."),
             ("h2", "Decisions used in this book (doc 35 defaults, open for Martin)"),
             ("li", "D1 bedplate NP8-300 (136 kg) instead of NP1-300 (338 kg)."),
             ("li", "D2 three calipers 4.8 kNm (third at 135°) instead of two stronger ones."),
             ("li", "D3 plain carbon caps; D4 keep 28 turns; D5 crank r140 (pin plane moved to 150, clash-free)."),
             ("h2", "Main parts"),
             ("li", f"Blades 3 × {[p for p in PARTS['parts'] if p['pid'] == 'NM8-100-1'][0]['mass_kg']:.1f} kg; hub and pitch 337 kg budget; generator Rev D; NP8-300 bedplate; yaw ring Dpw 410."),
             ("li", f"Spindle reserve {SP['spindle']['static_reserve_min']}, bearing s0 {SP['bearings']['s0_front']}/{SP['bearings']['s0_rear']}, life factor {SP['bearings']['life_factor'][0]}.")]
    paras(c, right, 214 * mm, 20 * mm, 190 * mm, 245 * mm)
    c.showPage()
    frame_page(c, "1  Design summary: figures and masses", "§1 design summary")
    image(c, RES / "F05-tower8.png", 16 * mm, 150 * mm, 200 * mm, 110 * mm)
    image(c, ISO / "A02-head.png", 220 * mm, 140 * mm, 185 * mm, 125 * mm)
    g = PARTS["group_mass_kg"]
    rows = [["Group", "kg (CAD)"]] + [[k, f"{v:.0f}"] for k, v in g.items()] + [["Head above the tower flange", f"{PARTS['head_kg']:.0f}"]]
    paras(c, [("h2", "Mass by group (assembled turbine)"), ("table", table(rows, [70, 30])),
              ("p", "CAD head mass includes every modelled part (cover, frame, adapter, lock holder, junction box, spinner); the doc 35 budget was 1,280 kg. The tower was checked with the larger value.")],
          16 * mm, 20 * mm, 120 * mm, 120 * mm)
    c.showPage()


def catalogue(c):
    cards = []
    for r in BOM:
        if not r["pid"] or r["pid"].startswith(("NM8-900", "NM8-800-W", "NM8-500-M", "NM8-600-K", "NM8-620-PE")):
            continue
        pid = r["pid"]
        img = ISO / "parts" / f"{pid}.png"
        for alt in (f"{pid}-1", f"{pid}-L", f"{pid}-F", f"{pid}-O"):
            if not img.exists():
                img = ISO / "parts" / f"{alt}.png"
        if pid == "NM8-105":
            img = ISO / "X-insert.png"
        cards.append((r, img))
    per = 8
    first = PAGE[0] + 1
    for k in range(0, len(cards), per):
        frame_page(c, "3  Part catalogue (axonometric views)" if k == 0 else "", "§3 part catalogue")
        top = H - (32 if k == 0 else 16) * mm
        cw, ch = (W - 28 * mm) / 4, (top - 14 * mm) / 2
        for j, (r, img) in enumerate(cards[k:k + per]):
            col, row = j % 4, j // 4
            x = 14 * mm + col * cw
            y = top - (row + 1) * ch
            c.setStrokeColor(colors.HexColor("#c7ced5")); c.setLineWidth(0.4)
            c.rect(x + 2 * mm, y + 2 * mm, cw - 4 * mm, ch - 4 * mm)
            image(c, img, x + 5 * mm, y + 32 * mm, cw - 10 * mm, ch - 40 * mm)
            c.setFillColor(ACC); c.setFont("DVB", 11)
            c.drawString(x + 5 * mm, y + 26 * mm, f"{r['pid']}  ×{r['qty']}")
            c.setFillColor(INK)
            paras(c, [("small", f"<b>{r['name']}</b>"), ("small", f"{r['material'] or '–'}"),
                      ("small", f"{r['make_buy']} · {('%s kg each' % r['mass']) if r['mass'] else ''} · drawing {r['drawing']}")],
                  x + 5 * mm, y + 4 * mm, cw - 10 * mm, 21 * mm)
        c.showPage()
    return first


TEXTS = {
    1: ["Set the NP8-300 bedplate upside-down on the assembly stand; check the yaw flange flatness (0.05) and the front-face angle (5.00° ± 0.05°) and record them.",
        "Fit the Dpw 410 slewing ring inner ring: 16 × M16 HV on PCD 350, cross pattern, 280 Nm (soft gearing mark towards the lock side).",
        "Fit the gearmotor brackets NP1-420 and the two gearmotors; set the backlash 0.15–0.30 mm at the soft point with the bracket shims.",
        "Check: ring turns freely by hand with both motor brakes released; record the turning torque."],
    2: ["Clean the spindle flange and pad; fit the Ø200 spigot; 12 × M20 10.9 from inside, 540 Nm in three passes.",
        "Fit the front spacer NP1-101 and rear seal sleeve NP1-102 (heat to 120 °C); cables through the two Ø28 holes before the stator goes on.",
        "Check: flange face square to the yaw axis (5° tilt) within 0.05/400. Spindle Rev D is 30 mm longer: check the length 466 ± 0.1 before fitting."],
    3: ["Assemble the stator Rev D: 45 wound tooth segments (104 mm stacks) slid into the carrier dovetails, clamp ring NP1-202 (doc 18 instructions, Rev C with the Rev D lengths).",
        "Insulation 1 kV, winding resistance balance ≤ 2 %, surge test. Carrier to spindle: 12 × M12, 110 Nm (thermal paste).",
        "Heat the bearing cones (110 °C) and fit them; grease 60 % fill."],
    4: ["Magnet drum: use the drum guide NP1-T01 (lengthened 30 mm) and the magnet safety rules of doc 18 (no steel tools within 1 m, two people). 280 blocks in 7 rows, skew steps ±0.4°.",
        "Lower the drum on the guide screw; set the bearing preload with the KMT 27 locknut (rolling torque 6–8 Nm).",
        "Fit the disc (24 bolts, NM8-900), seal covers and the Rev C rear cover with fan blades. Remove the guide.",
        "Check: air gap ≥ 1.4 mm at 8 positions, drum run-out ≤ 0.2 mm, back-EMF at 60 rpm vs generator_m8 (+3.4 % on Rev C)."],
    5: ["Fit the two side caliper brackets NP1-310 and the third bracket NM8-311 (4 × M16 through the front plate). Fit the three calipers; set pad gaps; check release on 24 V.",
        "Fit the lock pin holder with the two overspeed sensors; test the lock pin in all 12 disc holes.",
        "Check: holding torque test 14.4 kNm (torque arm on the drum), each caliper alone ≥ 4.8 kNm; sensor pulses."],
    6: ["Fit the pad units NY-410 (radius +25), yaw lock NY-430, encoder unit NY-440 and the cable hanger NY-460.",
        "Fit the cover arms, the lower GRP tray, the rear rail and the junction box; wire W1, W4, W5, W6.",
        "Check: pad clamping force, encoder zero at yaw 0°, cam switch at ±2.5 turns."],
    7: ["Lower the nacelle onto the tower-top adapter NY-400 (outer ring 16 × M16 PCD 490, 280 Nm). The nacelle is a transport unit with lifting points on the bedplate.",
        "Check: yaw turns 360° with the drives; pads slip at the doc 25 torque (scaled to the Dpw 410 ring)."],
    8: ["Bench: weld-checked hub NM8-200; fit the three pitch bearings (20 × M16 each, 280 Nm), cranks r140 with pins, links, yoke and guide rods, the cylinder and motor, supercap module and drive, nose frame.",
        "Run the pitch system on the bench from −2° to 92° and back (limit switches, end stops, supercap feather test, time ≤ 4 s).",
        "Fit the hub on the drum spigot (Ø360), 12 × M16 10.9, 280 Nm in 3 passes; mark blade 1 at the lock-pin azimuth; connect the slip ring."],
    9: ["Cylinder at the −2° end stop. Mount B1 on bearing 1, B2, B3 by their static-moment record: 12 × M16 10.9, 280 Nm star pattern.",
        "Check with the inclinometer at r 2 000 that all three blades read −2.0° ± 0.1° (linkage adjusted at the rod ends); tip track ±15 mm."],
    10: ["Fit the three spinner segments with the blade boots (9 brackets, A4 M8, 12 Nm). Check 10 mm clearance to all pitch parts over the full stroke."],
    11: ["Fit the upper cover lid and the met mast; bond the air terminal to the bedplate (50 mm² Cu).",
         "Factory test: pitch, brake, yaw, sensors; record insulation and EMF."],
    12: ["Site: excavate to 1.6 m, blinding, bottom mesh, anchor cage NM8-510 with the template ring (± 3 mm, level ± 1 mm), hinge anchors, ducts, earthing ring.",
         "Pour C30/37 XF4, cure ≥ 7 days. Fit the hinge brackets NM8-410 and levelling nuts; lay the tower on trestles on the hinge pin.",
         "Bolt the head to the tower top (16 × M20 HV, 540 Nm) on the ground; pull W2/W5; rotor locked with B1 up, blades feathered."],
    13: [f"Gin pole and rigging; winch line pull ≈ {TW['winch_line_pull_kN_ginpole_033H']:.0f} kN (use a 2-part or 4-part line); wind below 8 m/s; nobody in the fall zone.",
         "Land on the levelling nuts, fit top nuts, grout 30 mm; after 7 days tension the anchors (NM8-900). Remove the gin pole.",
         "Cabinet, resistor box, cabling W3, earthing ≤ 10 Ω, hand-hole cover. Commissioning checklist §7."]}


def step_pages(c):
    first = PAGE[0] + 1
    for k in range(0, len(STEPS), 2):
        frame_page(c, "6  Assembly sequence" if k == 0 else "", "§6 assembly sequence")
        top = H - (32 if k == 0 else 18) * mm
        for j, st in enumerate(STEPS[k:k + 2]):
            x = 14 * mm + j * (W - 28 * mm) / 2
            w = (W - 28 * mm) / 2 - 6 * mm
            c.setFillColor(ACC); c.setFont("DVB", 14)
            c.drawString(x, top - 6 * mm, f"Step {st['n']}")
            paras(c, [("h2", st["title"])], x + 25 * mm, top - 14 * mm, w - 25 * mm, 14 * mm)
            image(c, ISO / "steps" / f"S{st['n']:02d}.png", x, 95 * mm, w, top - 112 * mm)
            items = [("li", t) for t in TEXTS.get(st["n"], [])]
            items.append(("small", "Parts (new in colour, earlier steps light): " + ", ".join(st["parts"]) + ". Torques: NM8-900."))
            paras(c, items, x, 16 * mm, w, 76 * mm)
        c.showPage()
    return first


def commissioning(c):
    frame_page(c, "7  Erection, commissioning and inspection", "§7 commissioning")
    left = [("h2", "Before power-up"),
            ("li", "All torque stripes present; anchor, adapter, hub, pitch bearing and blade bolt records signed (NM8-900)."),
            ("li", "Tower plumb within 0.3 % in two directions; grout cured; hand-hole cover fitted."),
            ("li", "Earthing ≤ 10 Ω; continuity air terminal → bedplate → pad brush → tower → earth ring ≤ 0.2 Ω; hub bonded across the slip ring."),
            ("li", "Insulation: generator ≥ 100 MΩ at 1 kV; cables ≥ 100 MΩ. Pitch supercap charged, heater on below 0 °C."),
            ("li", "Rotor lock pin out; yaw lock retracted; cover lid closed; nobody inside 24 m."),
            ("h2", "Functional tests (wind below 8 m/s)"),
            ("li", "Safety chain: each trip input (overspeed × 2, E-stop, 24 V loss, vibration, converter fault, pitch fault) feathers the blades on supercap power and drops the brake after the delay; record the stop time."),
            ("li", "Feather on the supercap alone (mains off) from rated speed; brake alone from 100 rpm with the blades at −2°."),
            ("li", "8 m controller settings loaded: speed loop 6 rad/s, normal pitch rate 20°/s, overspeed trip 165 rpm (18 m: 4 rad/s, 15°/s, 155 rpm). Trip checked by lowering the set point (test mode)."),
            ("li", f"Yaw ±360° with the cam stop at ±2.5 turns; exclusion zone {TW['exclusion_zone_rpm'][0]:.0f}–{TW['exclusion_zone_rpm'][1]:.0f} rpm set in the controller (passed under torque)."),
            ("li", "Rotor balance at 120 rpm: nacelle 1P vibration, trial mass to ≤ 0.2 kg·m; pitch angle check (all three within 0.3°) with a camera at the tips."),
            ("li", f"Tower frequency (tap test): f1 must be ≥ {TW['f1_soft_ice_Hz']} Hz; if lower, widen the exclusion zone."),
            ("li", "Power curve: 48 h supervised operation; pitch regulation above 10 m/s; storm feather test on the next windy day.")]
    paras(c, left, 16 * mm, 20 * mm, 190 * mm, 245 * mm)
    rows = [["Interval", "Inspection"], ["50 h", "Re-torque blade root, pitch bearing, hub, adapter and anchor bolts; pitch zero check"],
            ["3 months", "Blades (LE erosion, root cracks), brake pads, pitch linkage play, cover fixings"],
            ["Yearly", "Bolts 10 % sample; pitch bearing grease; cylinder and rod ends; supercap capacity test; slewing ring and yaw gear grease; main bearing grease; earthing; safety chain; brake torque"],
            ["5 years", "Lower the tower: full blade inspection, main bearing play, magnet sleeve, cable loop, pitch bearing play"],
            ["After a storm > 50 m/s or an ice event", "Visual check, pitch and yaw logs, brake slip log"]]
    right = [("h2", "Inspection plan"), ("table", table(rows, [36, 150], fs=8.5)),
             ("h2", "Lowering the tower for service"),
             ("li", "Stop, feather, yaw to the hinge direction, lock the rotor with B1 up, lock the yaw; rig the gin pole and winch; slacken the base nuts on the hinge side last."),
             ("li", "Lower to the trestle: nacelle, hub and pitch system are at working height."),
             ("h2", "Records to keep with the turbine"),
             ("li", "Blade set static moments; magnet certificates; weld and UT records (hub, tower, bedplate, caliper bracket); torque records; commissioning results; f1 measured.")]
    paras(c, right, 214 * mm, 20 * mm, 190 * mm, 245 * mm)
    c.showPage()


def open_items(c):
    frame_page(c, "8  Open items before the prototype release", "§8 open items")
    items = [("li", "Martin's decisions D1–D5 (doc 35): this book uses the recommended defaults."),
             ("li", "FE checks: hub neck-to-shell welds, NP8-300 ring seat and front plate with the third caliper bracket, spindle Rev D flange fillet."),
             ("li", "Supplier drawings replace the envelopes (pitch bearings, cylinder, slewing ring Dpw 410, gearmotors, calipers, main bearings); then rerun clash8.py."),
             ("li", "Blade first-article static test to SLM H × 1.35, insert pull-out, mould acceptance."),
             ("li", "Pitch system bench test (feather on supercap at −30 °C)."),
             ("li", "Site investigation: soil class, frost depth, earthing, obstacle survey at 8 m; snow-drift height under the rotor."),
             ("li", f"Tower frequency on site (≥ {TW['f1_soft_ice_Hz']} Hz) and the fatigue at the base: measured strain on the prototype for one winter."),
             ("li", "Energy at 8 m: the 8 m tower is for open coast, highland and test sites; sheltered sites need the 18 m tower."),
             ("li", "All drawings NOT CHECKED: independent check of every sheet before parts are ordered.")]
    paras(c, items, 16 * mm, 60 * mm, 380 * mm, 190 * mm)
    c.showPage()


REUSED_PDF = [ROOT / "cad" / "nacelle_p1" / "out" / "pdf" / f"{n}.pdf" for n in ("NP1-101", "NP1-211", "NP1-230", "NP1-320", "NP1-T01")] + \
             [ROOT / "cad" / "generator_rc" / "out" / "pdf" / f"{n}.pdf" for n in ("NP1-G00", "NP1-200C", "NP1-201C", "NP1-202", "NP1-203C", "NP1-210C", "NP1-220E", "NP1-221C", "NP1-222C", "NP1-223C")] + \
             [ROOT / "cad" / "yaw" / "out" / "pdf" / f"{n}.pdf" for n in ("NY-000", "NY-400", "NY-410", "NY-430", "NY-440", "NY-460")] + \
             [ROOT / "cad" / "turbine_6kw" / "out" / "pdf" / f"{n}.pdf" for n in ("NS6-420", "NS6-600", "NS6-620", "NS6-700", "NS6-710", "NS6-800")]


def main():
    tmp = OUT / "_book_parts"
    tmp.mkdir(exist_ok=True)
    idx = json.loads((OUT / "drawing-index.json").read_text())
    own = [OUT / "pdf" / f"{r['number']}.pdf" for r in idx]
    ga = [p for p in own if p.stem in ("NM8-000", "NM8-001", "NM8-002", "NM8-003", "NM8-010", "NM8-020")]
    rest = [p for p in own if p not in ga]
    toc_cache = []
    for pass_ in (0, 1):
        PAGE[0] = 0
        toc = []
        c1 = canvas.Canvas(str(tmp / "front.pdf"), pagesize=(W, H))
        cover(c1)
        contents(c1, toc_cache if pass_ else [])
        toc.append(("1", "Design summary: 8 m tower, loads, energy, decisions", PAGE[0] + 1))
        summary(c1)
        c1.save()
        n_front = PAGE[0]
        toc.append(("2", "General arrangement, drawing index, bill of materials", n_front + 2))
        n2 = 1 + len(ga)
        c2 = canvas.Canvas(str(tmp / "cat.pdf"), pagesize=(W, H))
        PAGE[0] = n_front + n2
        toc.append(("3", "Part catalogue: axonometric view of every part", PAGE[0] + 2))
        section_divider(c2, "3  Part catalogue", "Axonometric view, part number, material and mass of every part")
        catalogue(c2)
        c2.save()
        n3 = PAGE[0] - (n_front + n2)
        toc.append(("4", "NM8 drawing set rev A (new and changed parts)", n_front + n2 + n3 + 2))
        n4 = 1 + len(rest)
        toc.append(("5", "Reused drawings (NP1 rev B, generator Rev C, yaw NY, S6 cover/electrical)", n_front + n2 + n3 + n4 + 2))
        n5 = 1 + len([p for p in REUSED_PDF if p.exists()])
        PAGE[0] = n_front + n2 + n3 + n4 + n5
        toc.append(("6", "Assembly sequence (13 steps)", PAGE[0] + 2))
        c3 = canvas.Canvas(str(tmp / "tail.pdf"), pagesize=(W, H))
        section_divider(c3, "6  Assembly sequence", "Workshop steps 1–11, site steps 12–13")
        step_pages(c3)
        toc.append(("7", "Erection, commissioning and inspection", PAGE[0] + 1))
        commissioning(c3)
        toc.append(("8", "Open items before the prototype release", PAGE[0] + 1))
        open_items(c3)
        c3.save()
        toc_cache = toc
        for name, t, sub in (("div2", "2  General arrangement and BOM", "NM8-000 … NM8-020"),
                             ("div4", "4  NM8 drawing set, revision A", "New and changed M8 parts, each with its axonometric view"),
                             ("div5", "5  Reused drawings", "NP1 rev B · generator Rev C (lengths per NM8-215) · yaw NY (radii per NM8-911) · S6 cover and electrical")):
            cd = canvas.Canvas(str(tmp / f"{name}.pdf"), pagesize=(W, H))
            section_divider(cd, t, sub); cd.save()
    w = PdfWriter()

    def add(p):
        for pg in PdfReader(str(p)).pages:
            w.add_page(pg)
    add(tmp / "front.pdf"); add(tmp / "div2.pdf")
    for p in ga:
        add(p)
    add(tmp / "cat.pdf"); add(tmp / "div4.pdf")
    for p in rest:
        add(p)
    add(tmp / "div5.pdf")
    for p in REUSED_PDF:
        if p.exists():
            add(p)
        else:
            print("missing", p)
    add(tmp / "tail.pdf")
    for pg in w.pages:
        bw, bh = float(pg.mediabox.width), float(pg.mediabox.height)
        if abs(bw - W) > 2 or abs(bh - H) > 2:
            pg.scale_by(min(W / bw, H / bh))
    w.add_metadata({"/Title": "12 kW Wind Turbine M8 - Build book rev A (8 m tower)", "/Author": "Claude for Martin (Wind turbine project)"})
    with open(OUT / "M8-build-book.pdf", "wb") as f:
        w.write(f)
    print("pages", len(w.pages), "toc", toc_cache)


if __name__ == "__main__":
    main()
