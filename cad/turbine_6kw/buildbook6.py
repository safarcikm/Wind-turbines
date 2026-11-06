"""S6 build book (doc 34): one PDF with the design summary, part catalogue (axonometric view of every
part), all drawings (S6 rev B + reused 12 kW sheets), the assembly sequence and the erection and
commissioning checklist.

    python3 buildbook6.py        -> out/S6-build-book.pdf
Needs: model6.py (out/model6-parts.json), bom6.py, iso6.py (out/iso), drawings6.py (out/pdf).
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path

import matplotlib
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Frame, Paragraph, Table, TableStyle, KeepInFrame

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
OUT = HERE / "out"
ISO = OUT / "iso"
RES = ROOT / "analysis" / "turbine_6kw" / "results"
FONTS = Path(matplotlib.__file__).parent / "mpl-data" / "fonts" / "ttf"
pdfmetrics.registerFont(TTFont("DV", str(FONTS / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DVB", str(FONTS / "DejaVuSans-Bold.ttf")))
W, H = 420 * mm, 297 * mm
INK = colors.HexColor("#1d2a36")
ACC = colors.HexColor("#2f6db5")
GREY = colors.HexColor("#6b7680")

ST = dict(
    h1=ParagraphStyle("h1", fontName="DVB", fontSize=20, leading=24, textColor=INK, spaceAfter=6),
    h2=ParagraphStyle("h2", fontName="DVB", fontSize=13, leading=16, textColor=INK, spaceBefore=6, spaceAfter=4),
    p=ParagraphStyle("p", fontName="DV", fontSize=9.5, leading=13, textColor=INK, spaceAfter=4),
    small=ParagraphStyle("s", fontName="DV", fontSize=8, leading=10.5, textColor=INK),
    li=ParagraphStyle("li", fontName="DV", fontSize=9.5, leading=13, textColor=INK, leftIndent=10, bulletIndent=0, spaceAfter=2),
)

T8 = json.loads((RES / "tower8.json").read_text())
TW = T8["towers"]["stiff"]["tower"]
FND = T8["towers"]["stiff"]["foundations"]
PARTS = json.loads((OUT / "model6-parts.json").read_text())
BOM = json.loads((OUT / "bom6.json").read_text())
STEPS = json.loads((ISO / "steps" / "steps.json").read_text())
DATE = "2026-11-06"

# ----------------------------------------------------------------------------- page helpers
PAGE = [0]
TOC = []


def frame_page(c, title, section=""):
    PAGE[0] += 1
    c.setFillColor(colors.white)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setStrokeColor(INK); c.setLineWidth(0.6)
    c.rect(10 * mm, 10 * mm, W - 20 * mm, H - 20 * mm)
    c.setFont("DVB", 9); c.setFillColor(GREY)
    c.drawString(14 * mm, H - 8 * mm, "6 kW WIND TURBINE S6 · 8 m TOWER · BUILD BOOK rev B")
    c.drawRightString(W - 14 * mm, H - 8 * mm, section)
    c.setFont("DV", 8)
    c.drawString(14 * mm, 5 * mm, f"{DATE} · NOT CHECKED: prototype release only after review (doc 34 §8)")
    c.drawRightString(W - 14 * mm, 5 * mm, f"page {PAGE[0]}")
    if title:
        c.setFont("DVB", 18); c.setFillColor(INK)
        c.drawString(16 * mm, H - 24 * mm, title)


def paras(c, items, x, y, w, h):
    f = Frame(x, y, w, h, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, showBoundary=0)
    story = []
    for kind, txt in items:
        if kind == "li":
            story.append(Paragraph(txt, ST["li"], bulletText="•"))
        elif kind == "table":
            story.append(txt)
        else:
            story.append(Paragraph(txt, ST[kind]))
    f.addFromList([KeepInFrame(w, h, story, mode="shrink")], c)


def table(rows, widths, fs=8.5, head=True):
    t = Table([[Paragraph(str(x), ParagraphStyle("t", fontName="DVB" if (head and i == 0) else "DV", fontSize=fs, leading=fs * 1.25, textColor=INK))
                for x in r] for i, r in enumerate(rows)], colWidths=[w * mm for w in widths])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#9aa4ad")),
                           ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef4") if head else colors.white),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5)]))
    return t


def image(c, path, x, y, w, h):
    path = Path(path)
    if not path.exists():
        c.setFont("DV", 8); c.drawString(x, y + h / 2, f"[missing {path.name}]")
        return
    ir = ImageReader(str(path))
    iw, ih = ir.getSize()
    k = min(w / iw, h / ih)
    c.drawImage(ir, x + (w - iw * k) / 2, y + (h - ih * k) / 2, iw * k, ih * k, mask="auto")


# ----------------------------------------------------------------------------- pages
def cover(c):
    frame_page(c, "", "")
    c.setFillColor(INK); c.setFont("DVB", 30)
    c.drawString(20 * mm, H - 45 * mm, "6 kW Wind Turbine S6")
    c.setFont("DV", 17); c.setFillColor(ACC)
    c.drawString(20 * mm, H - 57 * mm, "Build book · 8 m tower · revision B")
    image(c, ISO / "A01-turbine.png", 230 * mm, 18 * mm, 175 * mm, 260 * mm)
    head = PARTS["head_kg"]
    rows = [["Item", "S6 on the 8 m tower"], ["Rated power", "6 kW electric at ≈ 9.7 m/s (hub height)"], ["Rotor", "Ø6.0 m, 3 glass/epoxy blades, TSR 5.5, fixed pitch −2°"],
            ["Regulation", "stall by speed (converter), storm ramp 25–30 m/s, yaw 90° out in storms"],
            ["Generator", "G6 = Rev C direct-drive PM (no fins/ribs), one 1.5 kNm spring brake + K1 braking resistor"],
            ["Hub height", "8.0 m; rotor tip 5.0 m above ground"],
            ["Tower", f"one-piece tilt-up monopole Ø460 → Ø320, t 10/8, {TW['mass_kg']:.0f} kg, f1 {TW['f1_rigid_Hz']} Hz"],
            ["Foundation", f"spread footing {FND['firm soil (dense gravel, moraine)']['B']}–{FND['soft volcanic soil (loose ash, pumice sand)']['B']} m square, {FND['firm soil (dense gravel, moraine)']['concrete_m3']}–{FND['soft volcanic soil (loose ash, pumice sand)']['concrete_m3']} m³; rock plinth 2 m³"],
            ["Head mass", f"{head:.0f} kg above the tower flange (CAD, every part)"],
            ["Energy (vs 18 m tower)", " · ".join(f"{k} {v['aep8_kWh'] / 1000:.1f} MWh (−{v['loss_pct']:.0f} %)" for k, v in T8["energy"].items())]]
    paras(c, [("table", table(rows, [40, 150]))], 20 * mm, 120 * mm, 195 * mm, 100 * mm)
    paras(c, [("p", "Contents of this book: design summary for the 8 m tower (§1); general arrangement and BOM (§2); part catalogue with an axonometric view of every part (§3); "
                    "the S6 drawing set rev B (§4); the reused 12 kW drawings (§5); the assembly sequence in 13 steps (§6); erection, commissioning and inspection (§7); open items (§8)."),
              ("p", "Sources: docs 28–34, analysis/turbine_6kw (tower8.py, design6.py, sim6.py), cad/turbine_6kw (model6.py, drawings6.py, iso6.py, bom6.py). "
                    "Every number in this book comes from those scripts; re-run them to update the book.")],
          20 * mm, 30 * mm, 195 * mm, 80 * mm)
    c.showPage()


def contents(c, toc):
    frame_page(c, "Contents", "")
    rows = [["§", "Section", "Page"]] + [[a, b, str(p)] for a, b, p in toc]
    paras(c, [("table", table(rows, [14, 160, 18], fs=10))], 20 * mm, 40 * mm, 200 * mm, 225 * mm)
    paras(c, [("h2", "How to use this book"),
              ("li", "Every part has a card in §3 (axonometric view, part number, material, mass, drawing). The drawing follows in §4 (new S6 parts) or §5 (12 kW parts reused unchanged)."),
              ("li", "Build in the order of §6. Each step lists the parts, the fasteners and torques (NS6-900) and the checks that must be signed before the next step."),
              ("li", "Site work (footing, erection, commissioning) is §7. Keep the signed checklists with the turbine file."),
              ("li", "All drawings are NOT CHECKED. Release for the prototype only after the review and the FE checks listed in §8.")],
          235 * mm, 40 * mm, 165 * mm, 225 * mm)
    c.showPage()


def summary(c):
    frame_page(c, "1  Design summary: S6 on an 8 m tower", "§1 design summary")
    en = T8["energy"]; nz = T8["noise"]
    rows_e = [["Site (roughness z0)", "Mean wind 18 m → 8 m", "AEP 18 m", "AEP 8 m", "Loss", "Turbulence 18 → 8 m"]]
    for k, v in en.items():
        rows_e.append([f"{v['name']} ({v['z0']} m)", f"{v['v18']:.1f} → {v['v8']:.2f} m/s", f"{v['aep18_kWh'] / 1000:.1f} MWh", f"{v['aep8_kWh'] / 1000:.1f} MWh",
                       f"−{v['loss_pct']:.0f} %", f"{v['I18']:.3f} → {v['I8']:.3f} (+{v['turb_increase_pct']:.0f} %)"])
    t18 = T8["tower18"]
    rows_t = [["", "18 m tower (rev A)", "8 m tower (rev B)"],
              ["Concept", "soft-stiff, 2 sections", "stiff, one piece"],
              ["Shell", "Ø500 → Ø320, t 10/8", f"Ø{TW['geometry']['D_base'] * 1000:.0f} → Ø320, t {TW['geometry']['t_mm'][0]}/{TW['geometry']['t_mm'][1]}"],
              ["Mass", f"{t18['mass_kg']:.0f} kg", f"{TW['mass_kg']:.0f} kg"],
              ["f1 rigid / soft soil + ice", f"{t18['f1_rigid_Hz']} / {t18['f1_soft_ice_Hz']} Hz", f"{TW['f1_rigid_Hz']} / {TW['f1_soft_ice_Hz']} Hz"],
              ["Speed exclusion zone", f"{t18['exclusion_zone_rpm'][0]}–{t18['exclusion_zone_rpm'][1]} rpm (1P)", f"{TW['exclusion_zone_rpm'][0]}–{TW['exclusion_zone_rpm'][1]} rpm (3P)"],
              ["Governing case, use", f"{t18['governing']}, {t18['util_max']}", f"{TW['governing']}, {TW['util_max']}"],
              ["Base design moment", f"{t18['M_base_design_kNm']['parked V_e50']} kNm", f"{TW['base_flange']['M_design_kNm']} kNm"],
              ["Base bolts", "24 × M24 PCD 600", f"{TW['base_flange']['bolts']} × M24 PCD {TW['base_flange']['circle_m'] * 1000:.0f}"],
              ["Footing firm / soft", "3.8 / 4.2 m, 9.5 / 11.4 m³", f"{FND['firm soil (dense gravel, moraine)']['B']} / {FND['soft volcanic soil (loose ash, pumice sand)']['B']} m, {FND['firm soil (dense gravel, moraine)']['concrete_m3']} / {FND['soft volcanic soil (loose ash, pumice sand)']['concrete_m3']} m³"],
              ["Tilt-up", "6 m gin pole, 68 kN", f"3 m gin pole, ≈ {TW['winch_line_pull_kN_ginpole_033H'] * 0.33 * 6.87 / 3.0:.0f} kN, or a 3 t truck crane"]]
    left = [("h2", "What changed with the 8 m tower"),
            ("p", f"<b>Tower.</b> At 8 m a soft-stiff tower (first frequency between 1P at 41 rpm and 3P at 41 rpm, as the 18 m tower) is not possible: "
                  f"the head is {PARTS['head_kg']:.0f} kg on a 6.9 m tube, and a tube slim enough to be that soft fails in strength. The tower is therefore <b>stiff</b>: "
                  f"f1 is kept 15 % above 1P at full speed (2.73 Hz × 1.15 = 3.14 Hz). The 3P excitation still crosses f1 at low speed, so the controller skips "
                  f"{TW['exclusion_zone_rpm'][0]:.0f}–{TW['exclusion_zone_rpm'][1]:.0f} rpm (3.4–4.4 m/s wind), in the same way it skipped the 1P zone of the 18 m tower."),
            ("table", table(rows_t, [44, 52, 58], fs=8)),
            ("p", "<b>Loads.</b> The extreme winds stay at the class S hub-height values (IEC 61400-2 defines them at hub height), so no credit is taken for the lower wind near the ground. "
                  "Earthquake (0.5 g, ground D) now governs the tower, because the stiff tower sits on the plateau of the response spectrum. "
                  f"Fatigue spectra were increased by the higher turbulence (× {T8['fatigue_turbulence_factor']}); tower fatigue damage {list(TW['fatigue_damage'].values())[0]} at the base.")]
    paras(c, left, 16 * mm, 20 * mm, 190 * mm, 245 * mm)
    right = [("h2", "Energy, turbulence and noise at 8 m"),
             ("p", "The wind is slower and more turbulent near the ground. With the log wind profile for each site roughness, the hub-height mean wind drops 10–19 % and the energy 15–42 %:"),
             ("table", table(rows_e, [46, 34, 20, 20, 13, 44], fs=7.5)),
             ("li", "Coast, highland and open land lose 15–26 %. A sheltered farm site loses 42 % and is not a good place for an 8 m tower."),
             ("li", "Turbulence intensity rises 12–23 %. Blade and tower fatigue were checked with the higher value; both stay far below their limits (doc 31 margins ≥ 3×)."),
             ("li", f"Noise: at the same wind at 10 m (8 m/s), the rotor turns slower at 8 m: sound power {nz['inland']['8m']['LwA']} vs {nz['inland']['18m']['LwA']} dB(A), "
                    f"{nz['inland']['8m']['SPL60']} vs {nz['inland']['18m']['SPL60']} dB(A) at 60 m. At rated speed the source is the same and the receiver is a little closer: "
                    f"{nz['inland']['rated_any_height']['SPL60_8m']} vs {nz['inland']['rated_any_height']['SPL60_18m']} dB(A) at 60 m. Less masking wind noise at the house is the practical difference."),
             ("li", "Safety: the lowest blade tip is 5.0 m above ground. Fence or mark a 4 m radius round the tower; keep the 21 m ice-fall zone when icing is possible."),
             ("li", "Siting: the rotor works in the wake of buildings and shelter belts; place it ≥ 20 obstacle heights upwind of them in the main wind directions."),
             ("h2", "Design decisions taken for this book (design authority)"),
             ("li", "Pitch setting by ±2.5° arc slots in the hub root flange (doc 30's wedge shims could not change pitch); gauge NS6-135."),
             ("li", "Hub shell lengthened to 295 mm so the arms close on it; hub 79 kg (CAD)."),
             ("li", "GRP nacelle cover in two halves, drum outside (free-air cooling), met mast with air terminal on the rear rail."),
             ("li", "Tower one piece with base hinge, hand hole and gin-pole lugs; no climbing, service by tilting down."),
             ("li", "Spindle cooling insert NP1-110 left out (G6 runs without forced cooling, doc 29)."),
             ("li", "Only the left caliper bracket NP1-310 fitted; braking resistor box and base cabinet on a stand beside the tower.")]
    paras(c, right, 214 * mm, 20 * mm, 190 * mm, 245 * mm)
    c.showPage()
    frame_page(c, "1  Design summary: figures and masses", "§1 design summary")
    image(c, RES / "E01-tower8.png", 16 * mm, 150 * mm, 200 * mm, 110 * mm)
    image(c, ISO / "A02-head.png", 220 * mm, 140 * mm, 185 * mm, 125 * mm)
    g = PARTS["group_mass_kg"]
    rows = [["Group", "kg (CAD)"]] + [[k, f"{v:.0f}"] for k, v in g.items()] + [["Head above the tower flange", f"{PARTS['head_kg']:.0f}"]]
    paras(c, [("h2", "Mass by group (assembled turbine)"), ("table", table(rows, [70, 30])),
              ("p", "The head is 70 kg heavier than the doc 32 list (912 kg): the GRP cover and its arms (63 kg vs 20 kg allowed), the lock-pin holder and the junction box. The tower was sized with the CAD value.")],
          16 * mm, 20 * mm, 120 * mm, 120 * mm)
    paras(c, [("h2", "Checks carried over unchanged"),
              ("li", "Blade, hub, drivetrain, bedplate and yaw: doc 30–32 checks (SLM, simulated loads) do not depend on tower height; the higher turbulence adds ≤ 20 % to fatigue ranges where the margins are ≥ 3×."),
              ("li", "Brake 1.5 kNm and the K1 resistor chain: doc 32 §3; unchanged."),
              ("li", "Yaw-out storm parking: doc 30 §5; the parked yaw moment is unchanged."),
              ("li", "Generator G6 thermal: doc 29; unchanged (lower mean wind only helps).")],
          150 * mm, 20 * mm, 250 * mm, 110 * mm)
    c.showPage()


def catalogue(c):
    """§3: part cards, 8 per page (4 × 2), every BOM line with a CAD solid."""
    by = {p["pid"]: p for p in PARTS["parts"]}
    cards = []
    for r in BOM:
        if not r["pid"] or r["pid"].startswith(("NS6-900", "NS6-800-W", "NS6-500-M", "NS6-600-K", "NS6-620-PE")):
            continue
        pid = r["pid"]
        img = ISO / "parts" / f"{pid}.png"
        for alt in (f"{pid}-1", f"{pid}-L", f"{pid}-F", f"{pid}-O"):
            if not img.exists():
                img = ISO / "parts" / f"{alt}.png"
        if pid == "NS6-105":
            img = ISO / "X-insert.png"
        if pid == "NS6-130":
            img = ISO / "X-pitch.png"
        cards.append((r, img))
    for p in PARTS["parts"]:          # tooling + parts not in BOM as own line
        pass
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


def step_pages(c):
    texts = {
        1: ["Set the NS6-300 bedplate upside-down on the assembly stand; check the yaw flange flatness (0.05) and the front-face angle (5.00° ± 0.05°) and record them.",
            "Fit the yaw slewing ring inner ring to the bedplate: 16 × M16 HV, cross pattern, 250 Nm (soft gearing mark towards the lock side).",
            "Fit the gearmotor brackets NP1-420 (4 × M16, 195 Nm) and the two gearmotors (4 × M10, 49 Nm). Set the backlash with the brackets' shims: 0.15–0.30 mm at the soft point.",
            "Check: ring turns freely by hand with both motor brakes released; record the turning torque."],
        2: ["Clean the spindle flange and the Ø410 pad; fit the Ø200 spigot; insert 12 × M20 10.9 from inside and torque to 540 Nm in three passes.",
            "Fit the front spacer NP1-101 and rear seal sleeve NP1-102 (heat to 120 °C), cables through the two Ø28 holes before the stator goes on.",
            "Check: flange face square to the yaw axis (5° tilt) within 0.05/400 with the bedplate level."],
        3: ["Assemble the stator: 45 wound tooth segments NP1-203C slid into the carrier dovetails NP1-200C, clamp ring NP1-202 (doc 18, Rev C instructions).",
            "Insulation test 1 kV, winding resistance balance ≤ 2 %, surge test (doc 18 G07). Bolt the stator carrier to the spindle: 12 × M12, 110 Nm.",
            "Heat the bearing cones (110 °C, induction) and fit them on the spindle seats; pack grease (Mobilith SHC 220, 60 % fill)."],
        4: ["The drum with the magnets is the dangerous step: use the drum assembly guide NP1-T01 and the magnet safety rules of doc 18 (no steel tools within 1 m, two people).",
            "Lower the drum with cups and seals onto the bearings on the guide screw; set the bearing preload with the KMT 27 locknut (rolling torque 6–8 Nm).",
            "Fit the brake disc (12 × M12, 110 Nm), the front and rear seal covers and the plain rear cover NS6-610 (24 × M8, 20 Nm). Remove the guide.",
            "Check: air gap ≥ 1.4 mm all round (feeler at 8 positions), drum run-out ≤ 0.2 mm, no rubbing when turned by hand; back-EMF test at 60 rpm."],
        5: ["Fit the caliper bracket NP1-310 (left only) and the spring caliper; set the pad gap per the supplier; check the release with the 24 V supply.",
            "Fit the lock-pin holder with the two overspeed sensors (3 mm from the disc); test the lock pin in all 12 holes.",
            "Check: brake holding torque test 1.5 kNm (torque arm on the drum) and overspeed sensor pulses (24 per turn)."],
        6: ["Fit the two yaw pad units NY-410 (preset spring stack 3.7 mm), the yaw lock NY-430, the encoder unit NY-440 and the cable hanger NY-460.",
            "Fit the cover arms NS6-710, the lower GRP tray NS6-700-1 on rubber mounts, the rear rail and the junction box NS6-730; wire W1, W4, W5, W6 to the box.",
            "Check: pad clamping force (spring compression), encoder zero at yaw 0°, cam switch at ±2.5 turns."],
        7: ["Lower the nacelle onto the tower-top adapter NY-400 (outer ring 16 × M16, 250 Nm). The nacelle is now a transport unit (≈ 790 kg) with lifting points on the bedplate.",
            "Check: yaw turns 360° with the drives, pads slip at 4–5 kNm (spring balance on a 1 m lever)."],
        8: ["Fit the hub NS6-200 on the drum spigot, 12 × M16 10.9, 250 Nm in 3 passes, cross pattern. Mark arm 1 at the lock-pin azimuth.",
            "Check: hub face run-out ≤ 0.3 mm at the root flanges."],
        9: ["Screw the M12 studs into the blade inserts (Loctite 270, 40 Nm). Mount B1 on arm 1, B2, B3 by their static-moment record.",
            "Fit washer plates; set each blade to −2.0° ± 0.1° with the pitch gauge NS6-135 at r = 2 000 mm; torque 95 Nm + 90° in a star pattern; re-check pitch.",
            "Check: blade tip track within ±15 mm; rotor turns freely."],
        10: ["Fit the three spinner brackets and the spinner (3 × M8 with rubber washers, 12 Nm). Check 5 mm clearance to the drum front web."],
        11: ["Fit the upper cover lid (14 × M8, EPDM gasket) and the met mast with anemometer, vane and air terminal; bond the air terminal to the bedplate (50 mm² Cu).",
             "Factory test: spin the rotor with a drive on the hub (doc 15 bench) or leave to site; record insulation, brake, yaw, sensor function."],
        12: ["Site: excavate to 1.6 m, blinding, place the bottom mesh, the anchor cage NS6-510 with the template ring (± 3 mm, level ± 1 mm) and the hinge anchors; ducts; earthing ring.",
             "Pour the footing C30/37 XF4, cure ≥ 7 days. Fit the hinge brackets NS6-410 and the levelling nuts. Lay the tower on trestles with the base lugs on the hinge pin.",
             "Bolt the head to the tower top flange on the ground (16 × M20 HV, 450 Nm); pull W2 and W5 through the tower; lock the rotor with blade B1 up."],
        13: ["Fit the gin pole NS6-420 and the rigging; pull the tower up with the winch in wind below 10 m/s; nobody in the fall zone.",
             "Land the base flange on the levelling nuts, fit the top nuts, grout (30 mm, ≥ 40 MPa), after 7 days torque the anchors to 450 Nm. Remove the gin pole.",
             "Set the cabinet stand, cabinet and resistor box; connect W3, earthing (≤ 10 Ω), hand-hole cover. Go to the commissioning checklist (§7)."]}
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
            items = [("li", t) for t in texts.get(st["n"], [])]
            items.append(("small", "Parts (new in colour, earlier steps light): " + ", ".join(st["parts"]) + ". Torques: NS6-900."))
            paras(c, items, x, 16 * mm, w, 76 * mm)
        c.showPage()
    return first


def commissioning(c):
    frame_page(c, "7  Erection, commissioning and inspection", "§7 commissioning")
    left = [("h2", "Before power-up"),
            ("li", "All torque stripes present; anchor, adapter, hub and blade bolt records signed (NS6-900)."),
            ("li", "Tower plumb within 0.3 % (25 mm at the top) in two directions; grout cured; hand-hole cover fitted."),
            ("li", "Earthing ≤ 10 Ω measured; continuity air terminal → bedplate → pad brush → tower → earth ring ≤ 0.2 Ω."),
            ("li", "Insulation: generator phases to earth ≥ 100 MΩ at 1 kV; cables W2/W3 ≥ 100 MΩ."),
            ("li", "Rotor lock pin out; yaw lock retracted; cover lid closed; nobody inside 21 m."),
            ("h2", "Functional tests (wind below 8 m/s)"),
            ("li", "Safety chain: each trip input (overspeed sensors × 2, E-stop, 24 V loss, vibration, converter fault) closes K1 and drops the brake together; record the stop time."),
            ("li", "Brake only (K1 forced open) and resistor only (brake held off) stops from 100 rpm: both stop or crawl as doc 31."),
            ("li", "Overspeed trip at 189 rpm checked by lowering the set point to 60 rpm (test mode)."),
            ("li", f"Yaw: ±360° with the cable cam stop at ±2.5 turns; yaw-out 90° in ≤ 3 min on the aux battery; exclusion zone {TW['exclusion_zone_rpm'][0]:.0f}–{TW['exclusion_zone_rpm'][1]:.0f} rpm set in the controller."),
            ("li", "Rotor balance: run at 120 rpm, measure the nacelle 1P vibration; add trial mass to reach ≤ 0.2 kg·m (doc 09 R6.6)."),
            ("li", "Tower frequency: tap test or run-up; f1 must be ≥ 3.1 Hz (record; if lower, widen the exclusion zone)."),
            ("li", "Power curve and stall controller: 48 h supervised operation with storm ramp and yaw-out tested on the next windy day.")]
    paras(c, left, 16 * mm, 20 * mm, 190 * mm, 245 * mm)
    rows = [["Interval", "Inspection"], ["50 h", "Re-torque blade studs, hub bolts, adapter bolts, anchors; re-check pitch and track"],
            ["3 months", "Visual blades (LE erosion, cracks at the root), brake pad wear, cover fixings"],
            ["Yearly", "All structural bolts 10 % sample at 90 % torque; pad units spring gap; slewing ring grease (2 shots); yaw gear grease; bearing grease 30 g; earthing; safety chain test; brake torque test"],
            ["5 years", "Lower the tower: full blade inspection, bearing play, magnet-sleeve inspection, cable loop wear"],
            ["After a storm > 50 m/s or an ice event", "Visual check, yaw-out log, brake slip log (doc 32 §3)"]]
    right = [("h2", "Inspection plan"), ("table", table(rows, [36, 150], fs=8.5)),
             ("h2", "Lowering the tower for service"),
             ("li", "Stop, yaw to the hinge direction, lock the rotor with B1 up, lock the yaw; rig the gin pole and winch; slacken the base nuts on the hinge side last."),
             ("li", "Lower to the trestle (head 1.0 m above ground); nacelle and rotor are at working height."),
             ("h2", "Records to keep with the turbine"),
             ("li", "Blade set static moments and masses; magnet batch certificates; weld and UT records (hub, tower, bedplate); torque records; commissioning test results; f1 measured.")]
    paras(c, right, 214 * mm, 20 * mm, 190 * mm, 245 * mm)
    c.showPage()


def open_items(c):
    frame_page(c, "8  Open items before the prototype release", "§8 open items")
    items = [("li", "FE checks: hub arm-to-shell weld (doc 30 §11); NS6-300 ring seat stiffness and flatness (doc 32 §1)."),
             ("li", "Stall torque measurement on the prototype (docs 28/29): the main design risk of S6."),
             ("li", "Site investigation: soil class (plate-load test on volcanic ash), frost depth, earthing resistivity, local obstacle survey at 8 m."),
             ("li", "Supplier drawings replace the envelopes: slewing ring, gearmotors, bearings, caliper (NS6-910); then rerun the clash check."),
             ("li", "Tower frequency on site (≥ 3.1 Hz); if lower, the exclusion zone in the controller is widened."),
             ("li", "Blade: first-article static test to SLM H × 1.35, insert pull-out tests, mould acceptance against the plug templates."),
             ("li", "Icelandic DSO: confirm 6 kW single-phase connection (doc 12)."),
             ("li", "Certification route (IEC 61400-2 type test) and the energy loss at 8 m on low-wind sites: offer the 8 m tower for coast, highland and open land; keep an 18 m option for sheltered sites."),
             ("li", "All drawings NOT CHECKED: an independent check of every sheet before the prototype parts are ordered.")]
    paras(c, items, 16 * mm, 60 * mm, 380 * mm, 190 * mm)
    c.showPage()


def section_divider(c, title, sub):
    frame_page(c, "", "")
    c.setFillColor(INK); c.setFont("DVB", 26)
    c.drawString(30 * mm, H / 2 + 10 * mm, title)
    c.setFont("DV", 13); c.setFillColor(GREY)
    c.drawString(30 * mm, H / 2 - 4 * mm, sub)
    c.showPage()


# ----------------------------------------------------------------------------- assemble
REUSED_PDF = [ROOT / "cad" / "nacelle_p1" / "out" / "pdf" / f"{n}.pdf" for n in ("NP1-100", "NP1-101", "NP1-211", "NP1-230", "NP1-320", "NP1-T01")] + \
             [ROOT / "cad" / "generator_rc" / "out" / "pdf" / f"{n}.pdf" for n in ("NP1-G00", "NP1-200C", "NP1-201C", "NP1-202", "NP1-203C", "NP1-210C", "NP1-220E", "NP1-221C", "NP1-222C", "NP1-223C")] + \
             [ROOT / "cad" / "yaw" / "out" / "pdf" / f"{n}.pdf" for n in ("NY-000", "NY-400", "NY-410", "NY-430", "NY-440", "NY-460")]


def own_sheets():
    idx = json.loads((OUT / "drawing-index.json").read_text())
    return [OUT / "pdf" / f"{r['number']}.pdf" for r in idx]


def main():
    tmp = OUT / "_book_parts"
    tmp.mkdir(exist_ok=True)
    own = own_sheets()
    ga = [p for p in own if p.stem in ("NS6-000", "NS6-001", "NS6-002", "NS6-003", "NS6-010", "NS6-020")]
    rest = [p for p in own if p not in ga]
    # page bookkeeping: front matter is built twice (first pass counts pages)
    for pass_ in (0, 1):
        PAGE[0] = 0
        toc = []
        c1 = canvas.Canvas(str(tmp / "front.pdf"), pagesize=(W, H))
        cover(c1)
        contents(c1, TOC_CACHE if pass_ else [])
        toc.append(("1", "Design summary: 8 m tower, energy, turbulence, noise, decisions", PAGE[0] + 1))
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
        toc.append(("4", "S6 drawing set rev B (new and changed parts)", n_front + n2 + n3 + 2))
        n4 = 1 + len(rest)
        toc.append(("5", "Reused 12 kW drawings (NP1 rev B, generator Rev C, yaw NY)", n_front + n2 + n3 + n4 + 2))
        n5 = 1 + len(REUSED_PDF)
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
        globals()["TOC_CACHE"] = toc
        # dividers
        for name, t, sub in (("div2", "2  General arrangement and BOM", "NS6-000 … NS6-020"),
                             ("div4", "4  S6 drawing set, revision B", "New and changed S6 parts, each with its axonometric view"),
                             ("div5", "5  Reused 12 kW drawings", "Spindle, bearings, seals, disc, lock (NP1 rev B) · generator Rev C (G6: no fins, ribs, fan blades) · yaw system NY")):
            cd = canvas.Canvas(str(tmp / f"{name}.pdf"), pagesize=(W, H))
            section_divider(cd, t, sub); cd.save()
    w = PdfWriter()
    def add(p):
        r = PdfReader(str(p))
        for pg in r.pages:
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
    # A3 landscape everywhere: scale any page that is not 420 x 297
    for pg in w.pages:
        bw, bh = float(pg.mediabox.width), float(pg.mediabox.height)
        if abs(bw - W) > 2 or abs(bh - H) > 2:
            k = min(W / bw, H / bh)
            pg.scale_by(k)
    w.add_metadata({"/Title": "6 kW Wind Turbine S6 - Build book rev B (8 m tower)", "/Author": "Claude for Martin (Wind turbine project)"})
    with open(OUT / "S6-build-book.pdf", "wb") as f:
        w.write(f)
    print("pages", len(w.pages), "toc", TOC_CACHE)


TOC_CACHE = []

if __name__ == "__main__":
    main()
