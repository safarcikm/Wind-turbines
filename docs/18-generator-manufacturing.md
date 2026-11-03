# 12 kW Wind Turbine for Iceland: Generator Manufacturing Instructions (P1)

Status: **Draft A, not yet process-qualified** · 2026-11-03
Owner: Category 10 (Manufacturing and quality) with 4 (Generator) and 11 (Testing)
Builds on: [06 – Generator round 2](06-generator-round2.md) (frozen electromagnetic design), [14 – Nacelle prototype P1](14-nacelle-prototype-p1.md) (parts, fits, air gap budget), [17 – Working prototype W1](17-working-printed-prototype.md) (P1 geometry **Rev B** and assembly order), [15 – Bench test plan](15-nacelle-bench-test-plan.md) (T0 to T4)
Shop numbers: [`analysis/generator/manufacturing.py`](../analysis/generator/manufacturing.py) → [`manufacturing_summary.json`](../analysis/generator/results/manufacturing_summary.json), [`coil_connection.csv`](../analysis/generator/results/coil_connection.csv)
Geometry: [`cad/nacelle_p1/geometry.py`](../cad/nacelle_p1/geometry.py) (single source of truth, unchanged by this document)

## Summary

This is the complete instruction set for making the steel P1 generator in
house: the outer-rotor PM generator that replaces W1's printed dummy. It
covers materials and purchasing, the stator (laminations, insulation,
winding, connection, impregnation, potting), the rotor (drum, magnets,
encapsulation), joining both on the spindle, and every inspection and test
up to handover to the bench (doc 15).

| Item | Value (from docs 06, 14, 17) |
|---|---|
| Machine | Outer-rotor radial flux PMSG, 40 poles / 45 slots, tooth-coil (concentrated) double-layer winding, star |
| Stator | Ø598 OD, bore Ø437.2, stack 74.0 mm, M270-35A self-bonding laminations, slot 65 mm deep, 4 mm opening |
| Winding | 45 coils, **28 turns, 4 strands Ø1.55 mm in hand**, class 200 grade 2 wire, 15 coils per phase in series, class H, VPI + potted end windings |
| Rotor | S355J2+N drum, magnet seat Ø618.4, 160 + 8 spare N40UH arc segments (41 g each), 0.5 mm glass-epoxy sleeve, mechanical gap 2.0 mm |
| Mass | Stator ≈ 115 kg (with carrier), rotor ≈ 149 kg (with disc and covers) |
| Expected values | R20 = 0.217 Ω per phase; line EMF ≈ 430 V rms at 178 rpm and 20 °C (scaled, to be replaced by the FEA rerun) |

**One design change is needed before anything can be built** (section 1):
the stator as drawn cannot be wound. The 4 mm slot opening and the 50 %
copper fill required in the free slot space rule out every way of putting
the coils in. This document is written for the recommended fix, a
**segmented stator with one tooth per segment**, where each coil is
precision layer-wound directly on its own tooth and the 45 wound segments
slide into dovetail grooves in the carrier. The magnetic shape (tooth, tips,
slot, yoke, gap) is unchanged; the lamination and carrier drawings change.
The other options are in Appendix C.

**Build in three stages:**

1. **Q1 process qualification article** (5 wound segments in a carrier
   sector plus magnet test panels): proves winding fit, VPI, potting,
   insulation and magnet bonding before any P1 parts are committed
   (section 10). About 6 weeks, in parallel with the magnet order.
2. **P1 stator and rotor** (sections 5 to 7).
3. **Join on the spindle and test** (sections 8 and 9), then hand over to the
   bench plan (doc 15).

Generator ready for the bench about **13 to 14 weeks** after the magnet
order, which matches the doc 14 schedule.

---

## 1. Manufacturability review of the frozen design

Before writing instructions, every part of the doc 06/14 generator was
checked for whether it can be made, inspected and repaired. Findings:

| # | Finding | Consequence | Action in this document |
|---|---|---|---|
| **M1** | **The one-piece stator cannot be wound.** Tooth tips are 37.7 mm wide on a 22.3 mm tooth, with only a 4.0 mm slot opening. A pre-wound coil cannot pass over the tips. Needle winding through 4 mm with 4 strands of Ø1.66 mm (with enamel) is not possible. Hand drop-in, wire by wire through the opening, reaches about 40 % copper fill of the free space at best, and the design needs **49.7 %** (211 mm² of copper per coil side in 425 mm² free). Precision layer winding uses **90 %** of the 125 positions available (layers of 37, 37, 31, 17, 3 turns), which only works when the tooth is free on all sides | Doc 14 stator cannot be built as drawn | **Segmented stator** (section 5). Decision for Martin (Appendix C) |
| M2 | Segmentation means the stack is no longer shrunk onto the carrier with 3 keys | Carrier rim gets 45 dovetail grooves; keys and the Ø437.25 shrink fit go | New drawings NP1-200 Rev C and NP1-201 Rev C (section 5.1) |
| M3 | With segments, each sheet can no longer be rotated by 24° to average sheet thickness (doc 14) | Stack height scatter per segment | Sheets counted and stack measured per segment, ±0.1 mm (section 5.3) |
| M4 | 28 turns (doc 14) versus 27 to 28 (doc 06). Scaling doc 06 to 74 mm gives **392 V line at 100 °C with 28 turns** (target 380 V) and **≈ 920 V peak** at 250 rpm, −40 °C (doc 12 used 892 V). 27 turns gives 378 V and 889 V | Still below the 1100 V DC link capacitors and 1200 V devices, but outside the doc 12 number | Freeze the turn count from the FEA rerun before winding the 45 P1 coils; Q1 coils use 28 (section 5.5) |
| M5 | A hot-cured magnet adhesive (150 °C) locks in shear strain: steel shrinks 1.9 × 10⁻³ more than NdFeB from 120 °C to −40 °C, which is about 0.07 mm over a 38 mm magnet on a 0.15 mm bond line | Bond cracking in cold cycling | **Room-temperature-curing toughened epoxy, post-cure at 80 °C** (section 6.5). In an outer rotor the magnet pull and centrifugal force both push the magnets into the drum, so the bond only carries torque shear (≈ 20 kPa) and must not crack |
| M6 | The 0.5 mm glass-epoxy cover layer, laid by hand, carries the full magnet thickness and bond-line scatter into the air gap (0.05 mm in the budget) | Gap scatter | **Mould the sleeve against a precision non-magnetic mandrel** located on the bearing seats (section 6.7): the sleeve bore becomes a controlled Ø602.0 surface concentric with the bearings |
| M7 | Magnets are arcs, so a piece cannot be flipped to change polarity | Two different parts must be ordered | **NP1-220-N** (north on the concave face) and **NP1-220-S**, 84 of each (section 4.3) |
| M8 | Magnet axial segmentation (4 per pole) still waits for the eddy-loss check (doc 14 open point 3) | Order cannot be placed with confidence | Run the eddy-loss check in week 1; if it changes the count, only the magnet drawing changes |
| M9 | A shrink-fitted one-piece stack could not be repaired; a damaged coil meant a new stator | Service cost over 20 years | Segments can be pulled and replaced **before VPI**; after VPI a damaged coil means re-winding that segment in a stripped stator (section 11) |

M1 is the only show-stopper. M2, M3, M6 and M7 follow from the chosen
fixes; M4, M5 and M8 are decisions or checks with a clear owner.

---

## 2. Facilities, equipment and people

### 2.1 Work areas

| Area | Purpose | Requirements |
|---|---|---|
| **A. Machine shop** | Drum, carrier, rings, tools | Boring mill or vertical lathe (Ø900 swing), CNC mill, wire EDM (carrier grooves), grinding |
| **B. Lamination cell** | Cut, deburr, bond segments | Fibre laser with N₂ assist (P1) or progressive die (series), bonding press with heated platens, fixture NP1-T03 |
| **C. Winding room** | Insulate and wind segments, assemble and connect stator | Clean (no metal grinding nearby), 20 to 25 °C, RH ≤ 60 %, ESD-safe benches, programmable spindle winder with 4-strand tensioner, brazing station |
| **D. Impregnation bay** | VPI, ovens, potting | VPI tank ≥ Ø900 × 600 mm (vacuum ≤ 1 mbar, pressure 6 bar), curing oven ≥ 180 °C with rotisserie, resin storage 5 to 25 °C, extraction ventilation |
| **E. Magnet room** | Magnet storage, flux check, bonding, encapsulation | **No loose steel**, non-magnetic benches (aluminium, wood, composite), floor marking of the 0.5 mT line, pacemaker warning on the door, access list, non-magnetic rotary table |
| **F. Test lab** | Electrical tests | Fenced HV test area to EN 50191 with interlocks and warning lamps, hipot, surge tester, PD detector, micro-ohmmeter, insulation tester, LCR meter |
| **G. Assembly bay** | Joining stator and rotor on the spindle | Overhead crane ≥ 1 t with textile slings, vertical assembly stand with tool NP1-T01, magnetic-hazard zone marking |

### 2.2 Tools and fixtures

| No. | Tool | Purpose |
|---|---|---|
| NP1-T01 | Drum assembly guide (exists in doc 14) | Lowers the magnetised rotor over the stator on the spindle with a screw jack |
| NP1-T02 | Magnet insertion jig (doc 14, detailed in section 6.5) | Slides each magnet into its channel and lowers it under screw control |
| NP1-T03 | Segment bonding fixture (Rev C: for segments) | Stacks and bonds 205 sheets per segment on a precision dovetail and tip gauge |
| NP1-T04 | Segment winding chuck | Holds a segment on the winder spindle by its dovetail, with end-flange guides |
| NP1-T05 | Stator assembly and measuring stand | Carrier on a rotary table with a probe on the tooth tips; inserts segments axially |
| NP1-T06 | Sleeve moulding mandrel | Aluminium, Ø602.0, located on both cup seats; moulds the magnet sleeve |
| NP1-T07 | VPI frame | Lifts and turns the stator in the tank and oven |
| NP1-T08 | Potting moulds | Silicone moulds for front and rear end windings |
| NP1-T09 | Magnet flux tester | Helmholtz coil and fluxmeter, non-magnetic holder |
| NP1-T10 | Pole scanner | Hall probe on an arm over the non-magnetic rotary table, maps the field of every pole |
| NP1-T11 | Non-magnetic hand tools | Titanium, beryllium-copper or austenitic stainless (check with a magnet) tools, brass and plastic shims, G10 gap feelers 1.5 mm |

### 2.3 People

- **Winding and connection:** trained winder; brazing to EN ISO 13585.
- **Magnet work:** at least two trained people, one acting only as safety
  watch. Written procedure signed before each session.
- **HV testing:** electrically skilled person to EN 50110 / EN 50191.
- **Welding:** EN ISO 9606-1 welders, EN ISO 3834-3 quality level,
  NDT level 2 to EN ISO 9712.

### 2.4 Safety rules (all generator work)

| Hazard | Rule |
|---|---|
| **Magnet crushing and pinching** | One magnet piece pulls ≈ 280 N (≈ 28 kg) on thick steel, more on another magnet. Never carry two loose pieces in one hand; keep pieces ≥ 300 mm apart unless in spacers; handle with the jig only near the drum; no rings or watches; cut-resistant gloves and safety glasses (NdFeB chips like glass) |
| **Assembled rotor** | ≈ 27 kN total radial pull on the stator, rising by **1.9 kN per mm** off centre. Only the guided, screw-controlled procedure in section 8 is allowed. Never put hands in the drum when the stator is near it |
| **Medical implants** | Nobody with a pacemaker or ICD in the magnet room or assembly bay; signs at every entrance |
| **Magnetic media and instruments** | Keep phones, cards, watches and instruments outside the 0.5 mT line |
| **Magnet dust** | No grinding or machining of magnets. NdFeB dust is pyrophoric. Broken pieces go into a sealed steel tin under oil, then to the supplier for recycling |
| **HV tests** | Tests only inside the fenced area, two-hand or key interlock, discharge and earth every winding after every test (5 × the test time, then earth stick) |
| **Resins and solvents** | Epoxies sensitise skin: nitrile gloves, sleeves, eye protection, local extraction; read the SDS before first use; no food in areas C, D, E |
| **Hot work** | Ovens up to 180 °C, brazing: heat gloves, fire watch, extinguisher class B and electrical |
| **Lifting** | Textile slings only near the magnetised rotor. Drum with magnets ≈ 105 kg, complete rotor ≈ 150 kg, stator ≈ 115 kg |

---

## 3. Process route and schedule

```
Week:      0    1    2    3    4    5    6    7    8    9   10   11   12   13   14
Decisions  M1/M4/M8
FEA rerun  ■■■
Drawings   ■■■■■■■ (NP1-200/201 Rev C, T03 to T10)
Magnets         ordered ───────────── 8 to 12 weeks ─────────────► in
Q1 article           ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■ (section 10)
Laminations               ■■■■■■■■■■■ cut, bond, inspect
Carrier, drum        ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■ weld, PWHT, machine
Winding                                       ■■■■■■ 45 segments
Stator assy, VPI, pot                                ■■■■■■
Rotor magnets, sleeve                                     ■■■■■■
Join on spindle, tests                                           ■■■■■
```

| Op | Stator track | Op | Rotor track |
|---|---|---|---|
| S10 | Receive and inspect steel coil, wire, insulation, resin | R10 | Drum weldment, NDT, stress relief |
| S20 | Cut segment laminations | R20 | Machine drum in one set-up |
| S30 | Bond segment stacks (45 + 3 spare) | R30 | Pre-balance bare drum (G6.3) |
| S40 | Inspect segments | R40 | Prepare magnet seat, bond pole comb |
| S50 | Machine carrier, dovetail grooves | R50 | Receive, flux test and sort magnets |
| S60 | Insulate segments | R60 | Bond magnets (N poles, then S poles) |
| S70 | Wind coils, test each coil | R70 | Pole map |
| S80 | Assemble segments on carrier, wedges, sensors | R80 | Mould the sleeve with mandrel T06 |
| S90 | Connect, pre-VPI tests | R90 | Rotor inspection, cups, rear seal cover, disc |
| S100 | VPI and cure | | |
| S110 | Pot end windings | | |
| S120 | Final stator tests | | |
| | **Join** | J10 to J60 | Section 8; then tests section 9 |

---

## 4. Materials and purchasing specifications

Every lot needs a 3.1 inspection certificate (EN 10204) unless noted.
Incoming inspection results go into the generator record (section 11).

### 4.1 Electrical steel and stator materials

| Item | Specification | Quantity | Incoming check |
|---|---|---|---|
| Lamination steel | **M270-35A** (EN 10106), 0.35 mm, with **self-bonding varnish** both sides (e.g. "backlack" type), C5/C6 insulation | 9,225 segment sheets (205 × 45) + 5 % + Q1 → order ≈ **0.6 t** of slit coil | Thickness 10 points ±0.02, varnish thickness, supplier Epstein loss ≤ 2.70 W/kg at 1.5 T 50 Hz, bonding test coupon |
| Winding wire | Enamelled round copper **Ø1.55 mm, grade 2, thermal class 200** (polyesterimide + polyamide-imide overcoat), IEC 60317-13; partial-discharge-resistant (corona-resistant) enamel preferred because of converter feed | **25 kg** (20.1 kg in the winding + 25 %), one lot | Diameter bare and overall (max 1.66), elongation ≥ 30 %, breakdown voltage per IEC 60851-5, pinholes |
| Slot liner | Nomex-Kapton-Nomex (NKN), 0.30 mm, class H/200 | 5 m² | Thickness, breakdown |
| Phase separators | NKN 0.25 mm (or 0.5 mm aramid paper) | 2 m² | |
| Slot wedges | Glass-epoxy (G11, class H), profile to suit the wedge seat, 2.0 mm | 45 × 74 mm + spares | Profile gauge |
| End caps | Moulded **PPS GF40** (or PEI), class H, one front and one rear per segment | 96 | Fit on master segment |
| Lead wire | Silicone-insulated tinned flexible copper, 10 mm², 180 °C, 1 kV (or EPR class H) | 15 m | |
| Sleeving and ties | Glass/silicone sleeving class H, polyester-glass lacing cord, glass tape | Kit | |
| Brazing | BCuP-2 (CuP7) rods (flux-free on copper), copper crimp ferrules | Kit | |
| **VPI resin** | Solvent-free **class H epoxy** VPI resin (single component or two-component with long pot life), approved by the wire maker for the enamel; tan δ, viscosity and gel time data | 1 tank fill + 20 kg uptake reserve | Viscosity and gel time on arrival and before each VPI |
| **Potting compound** | Two-component **filled epoxy**, class H, thermal conductivity ≥ 0.8 W/m K, CTE ≤ 35 ppm/K, low exotherm, toughened for −40 °C cycling | ≈ 8 kg + 3 kg Q1 | Mixed sample hardness, gel time |
| Temperature sensors | Thin-film **PT100 class A**, 3-wire, Kapton/glass sleeved, fit 2 mm × 4 mm in the separator gap | 8 (6 used, 2 spare) + 4 for Q1 | Resistance at 0 °C ±0.15 Ω |
| Carrier steel | S355J2+N ring forging or plate, normalised | 1 (≈ 70 kg raw) | Certificate, UT of forging |

### 4.2 Rotor materials

| Item | Specification | Quantity |
|---|---|---|
| Drum shell | **S355J2+N seamless ring-rolled forging** preferred (no longitudinal weld through the magnet yoke); plate-rolled with full-penetration seam acceptable for P1 if 100 % UT | 1 |
| Drum webs, flange ring | S355J2+N plate 8, 20 mm; bearing tube S355J2H | per drawing NP1-210 |
| Pole comb bars | GRP pultruded bar (glass-epoxy, class H), 9.6 × 7.0 mm, 74 mm long; or machined from G11 sheet | 40 + 5 |
| Magnet end rings | G11 rings, front and rear, closing the magnet pack ends | 2 |
| **Magnet adhesive** | Two-component **toughened epoxy, room-temperature cure**, service −40 to +150 °C, Tg ≥ 120 °C after an 80 °C post-cure, lap shear ≥ 15 MPa (23 °C) and ≥ 5 MPa (120 °C) on NiCuNi-epoxy coated NdFeB to grit-blasted steel, with **0.15 mm glass beads** for bond line, approved by the magnet maker for its coating | 1.5 kg incl. Q1 |
| Sleeve fabric | E-glass twill 2 × 100 g/m² (≈ 0.2 mm cured total, layup tuned to 0.4 to 0.6 mm) + glass-scrim peel ply | 3 m² |
| Sleeve resin | Low-viscosity infusion epoxy, RT cure, post-cure 80 °C, Tg ≥ 100 °C | 2 kg |
| Primer | Adhesive maker's primer for steel | |

### 4.3 Magnets NP1-220 (purchase specification)

| Item | Requirement |
|---|---|
| Material | Sintered NdFeB **N40UH** (Br ≥ 1.26 T, HcJ ≥ 1,990 kA/m at 20 °C); batch demagnetisation curves (J-H and B-H) at 20, 60, 100, 120 and 150 °C; temperature coefficients of Br and HcJ stated |
| Shape | Radial arc segment, **R301.5 concave / R309.2 convex, arc 7.20°** (chord 37.86 inside, 38.83 outside), **axial length 18.35**, thickness 7.70 |
| Tolerances | Thickness ±0.03, arc radii ±0.05, length ±0.05, arc angle ±0.05°; edges chamfered 0.2 to 0.3 |
| Magnetisation | **Radial**, fully saturated. Two variants: **NP1-220-N** (north pole on the concave, stator-facing side) and **NP1-220-S**; each piece marked with a coloured dot on the convex face (red = N inside, blue = S inside) |
| Quantity | 84 N + 84 S (80 + 4 spare each), plus 8 test pieces (unmagnetised acceptable) for Q1 bond and salt-mist tests |
| Coating | **NiCuNi** (≥ 15 µm) plus **epoxy top coat** (≥ 15 µm); ≥ 500 h neutral salt spray (ISO 9227) without red rust on test pieces; adhesion approved by the adhesive maker |
| Uniformity | Magnetic moment of every piece measured by the supplier, within **±1.5 %** of the lot mean; data per piece serial |
| Packaging | Individually in non-magnetic spacers, repelling layout, steel-shielded box for air freight (IATA PI 953 field limit) |
| Order note | **Longest lead item, order first** (8 to 12 weeks), after the eddy-loss check (M8) |

### 4.4 Fasteners and bought parts

As doc 14 BOM: bearings 32028 X, KMT 27, seals, M12 10.9 carrier screws with
dowels, M10 10.9 disc screws, M16 10.9 hub screws. All fasteners for the
generator interior **A4-80 stainless** where they sit within 100 mm of a
magnet face (non-magnetic during assembly); 10.9 steel elsewhere.

---

## 5. Stator

### 5.1 Segment and carrier design changes (drawing basis for Rev C)

| Feature | Rev C definition |
|---|---|
| Segment NP1-201 | One tooth (22.3 mm) with tips, plus one slot pitch of yoke (**8.00°**), joints on the slot centre lines in the yoke. Magnetic contour inside the joints is identical to `lamination_outline()` in geometry.py |
| Dovetail foot | Below the yoke, r 218.6 → 212.6 (6 mm deep), 14 mm wide at r 218.6, 60° flanks; the carrier rim OD stays Ø437.2 |
| Carrier NP1-200 | Rim OD Ø437.2 with **45 dovetail grooves**, angular position ±0.01°, radial seat ±0.01 to the bolting face axis; grooves open to the front (x 343.5), closed by the rear stack stop (x 417). The 3 keyways and the shrink fit are removed |
| Joint fit | Foot in groove: 0.01 to 0.03 mm clearance (slides by hand when clean), fixed by VPI resin and clamped axially by NP1-202 |
| Tip seats | Tooth-tip underside carries the 2 mm wedge seat (as Rev B) |
| Air gap budget | Item "stack OD to bore 0.050" becomes "segment tip radius in assembly 0.050": segment tip radius ±0.02, groove seat ±0.01, plus foot clearance taken up by VPI. Total budget unchanged |
| FEA rerun | Model the 45 yoke joints (0.02 mm effective gap each) and a ±0.02 mm random radial scatter of segments; confirm EMF, cogging ≤ 0.5 % and torque ripple. Expected EMF loss < 1 % |

Spare segments: 3, wound and tested. All segments are identical, so any
spare replaces any tooth.

### 5.2 S20 Cut laminations

1. Check the coil certificate and incoming tests (4.1). Mark the rolling
   direction on the coil. Segments are cut with the **tooth axis along the
   rolling direction** (lower loss in the tooth, where flux density is
   highest).
2. **P1 (laser):** fibre laser, nitrogen assist, parameters set on test
   sheets for minimum heat input; cut contour from the Rev C DXF. Burr height
   ≤ **0.02 mm**, measured on 1 in 50 sheets. Do not anneal (it destroys the
   bonding varnish); the laser edge damage is covered by the 1.5 loss build
   factor in doc 05.
3. **Series (later):** progressive die, burr ≤ 0.02 mm, die resharpened by
   burr height.
4. Every 200th sheet: measure tooth width, tip width, dovetail profile with
   the optical comparator or CMM; tolerance ±0.02 mm.
5. Keep sheets flat, dry and free of oil. Stack in bundles of 205 counted by
   weight (≈ 1.1 g per sheet, weigh the bundle, ±1 sheet).

### 5.3 S30 Bond segment stacks (fixture NP1-T03)

1. Clean the fixture: dovetail mandrel, tip locator, release-coated platens.
2. Load **205 sheets**, burrs all in the same direction. Mix sheets from at
   least three positions across the coil width in each segment to average
   thickness (replaces the doc 14 rotation, M3).
3. Close the fixture; apply the varnish maker's bonding cycle (typically
   1 to 3 MPa at 150 to 220 °C for a set time). Record pressure,
   temperature and time.
4. Cool under pressure to below 60 °C, then release.
5. **Stack height 74.0 ±0.1 mm**. If out, add or remove sheets and re-bond
   the next segment; never shim.
6. Mark the segment serial on the yoke back face (laser or vibro-etch, not
   stamping).

### 5.4 S40 Inspect segments

| Check | Method | Accept |
|---|---|---|
| Height | Micrometer at 4 points | 74.0 ±0.1 |
| Squareness of stack to dovetail | Square and feelers | ≤ 0.05 over 74 |
| Tip radius from dovetail datum | Fixture gauge with dial | ±0.02 (key item of the air gap budget) |
| Tooth width, slot flanks | Go/no-go gauge | ±0.03 |
| Bond strength | Peel by hand at one end corner (no delamination); 1 sacrificial segment per batch in a tensile test | ≥ varnish datasheet |
| Interlaminar insulation | 4-wire resistance top-to-bottom of the stack at 1 A DC | ≥ 10 Ω (no through-shorts by burrs) |
| Burrs, steps, loose sheets | Visual, 10× loupe | None at slot flanks and tips |

Make **48 segments** (45 + 3 spare).

### 5.5 S60 Insulate segments

1. Blow off with dry filtered air, wipe flanks with isopropanol.
2. Fit **front and rear end caps** (PPS GF40) onto the tooth ends; they
   round the coil corners (R ≥ 3 mm) and carry the coil 3 mm clear of the
   stack ends.
3. Fold the **NKN 0.30 slot liner** to the slot flank shape (yoke face,
   tooth flank, under the tip) on both sides of the tooth. Liner cuffs 5 mm
   beyond each stack face, folded over the end caps. No liner may cover the
   dovetail or the tip outer surface.
4. Check: no sharp edge reaches wire anywhere; a 1.7 mm dummy wire run
   around the tooth must not catch.

### 5.6 S70 Wind coils (chuck NP1-T04)

**Turn count:** 28 for Q1 and P1 unless the FEA rerun (M4) freezes 27. The
count is set in the winder program and signed off on the traveller.

1. Mount the insulated segment on the chuck by its dovetail. The chuck end
   flanges follow the slot flank and the slot centreline, so the coil
   cannot grow into the neighbour's half-slot (half free width 0.25 mm
   under the separator).
2. Load **4 strands Ø1.55 mm** from four spools of the same wire lot through
   the 4-strand tensioner. Tension **25 to 30 N per strand** (≈ 13 to
   16 MPa, far below the yield of annealed copper). Strands must lie parallel
   and must not cross inside the slot part of the coil.
3. Leave the **start lead 150 mm** long at the rear end (connection side),
   at the slot bottom.
4. Wind **layer by layer**, starting at the tooth flank, outward. The layer
   plan (each turn = 4 strand positions, positions counted along the tooth
   height):

   | Layer (from tooth flank) | Strand positions available | Strand positions used |
   |---|---|---|
   | 1 | 37 | 37 |
   | 2 | 37 | 37 |
   | 3 | 31 | 31 |
   | 4 | 17 | 7 |
   | 5 | 3 | 0 (reserve) |

   (28 turns × 4 strands = 112 positions needed, 125 available.) Layers step outward toward the slot top, where the slot is wider;
   the program steps the traverse limit per layer. Speed ≤ 60 rpm.
5. Finish lead **150 mm** at the rear end. Total wire per coil ≈ **6.6 m per
   strand**.
6. Tie the coil end turns with one turn of glass tape at each end cap; tape
   the leads with glass sleeving, mark the **start lead** with a red tag.
7. Fit the **phase separator** (NKN 0.25) on each coil side face; it is the
   boundary to the neighbouring segment's coil.

**Every coil is wound in the same direction.** Reversal of "−" coils is done
at connection (5.9), so all 48 segments are interchangeable.

### 5.7 Test every coil (before assembly)

| Test | How | Accept |
|---|---|---|
| Strand continuity | Each of the 4 strands separately, micro-ohmmeter | Strand resistances within ±2 % of each other (finds a broken or nicked strand) |
| Coil resistance | 4 strands joined at each end, 4-wire, corrected to 20 °C | **14.5 mΩ ±3 %** (calculated, confirm on Q1), and within ±1 % of the running mean |
| Turns and inter-turn insulation | Surge comparison against the master coil, **3.5 kV peak**, rise time 0.1 to 0.2 µs | Waveform matches master (error area ratio ≤ 5 %); no collapse |
| Coil to core | AC hipot **1.8 kV, 1 min** (80 % of the final test, because not yet impregnated) | No breakdown, leakage stable |
| Dimensions | Coil side envelope gauge (half-slot profile) | Passes freely along the full length |

Record results by segment serial. Failed coils are unwound and rewound on
the same segment after replacing the liner.

### 5.8 S80 Assemble segments onto the carrier (stand NP1-T05)

Prerequisite: carrier NP1-200 Rev C finish-machined, grooves deburred and
measured (groove position ±0.01°, seat radius ±0.01), cleaned, bolting face
protected.

1. Carrier horizontal on the rotary table, front end (x 343.5 side) up,
   rear stack stop down.
2. Fit the **6 PT100 sensors** first to the coil sides that will sit at the
   hottest positions: **slot top (under the wedge), mid-stack**, two per
   phase, spread around the circumference (suggested teeth 2, 17, 32 for
   phase A, and the same pattern shifted to B and C). Sensor leads run with
   the coil leads to the rear.
3. Slide segments axially into their grooves **in tooth order 1 to 45**
   (Appendix A). The coil sides pass the neighbour's coil side with the
   separator between; push with a plastic drift only on the yoke, never on
   the coil. Each segment must seat against the rear stop.
4. After all 45 are in, measure **tooth-tip radius at every tooth**, front
   and rear end, with the probe on the stand: run-out **≤ 0.05 mm** TIR.
   A tooth out of tolerance: change the segment for a spare and recheck.
5. Insert the **slot wedges** axially from the front in every slot.
6. Fit the front clamp ring NP1-202 (A4-80 screws, torque per drawing). It
   clamps the yokes only, not the coils.
7. Check: no coil touches the clamp ring, the carrier web, or the rear stack
   stop; the end windings stay within **x 321 to 439** and **r ≤ 296**.

### 5.9 S90 Connect the winding

Connection plan: [`coil_connection.csv`](../analysis/generator/results/coil_connection.csv),
summarised in Appendix A. Each phase has five groups of three adjacent
coils, **(+, −, +)**, with the groups nine teeth apart. Phases around the
stator: **A, C, B**, A, C, B …

- A "+" coil is connected start → finish in the phase's current direction;
  a "−" coil finish → start.
- Within a group the jumpers are short (adjacent teeth). Between groups the
  jumpers run on a **connection ring** of glass-epoxy at the rear end
  winding, one track per phase.

For each joint:

1. Strip the enamel mechanically (rotary stripper) or by laser over 15 mm;
   **no chemical strippers** (residues attack the VPI resin).
2. Twist the 4 + 4 strands (or the 4 strands plus the jumper) into a copper
   **crimp ferrule**, crimp, then **induction-braze with BCuP-2** (flux-free
   on copper). Joint resistance ≤ that of 20 mm of the coil conductor.
3. Clean, inspect for full fill and no sharp ends, sleeve with class H glass
   sleeving, lace to the connection ring.
4. **Star point**: the three phase ends brazed into one ferrule, insulated
   and fixed on the ring.
5. **Phase leads** U, V, W: brazed to 10 mm² silicone leads, out through the
   two Ø28 holes in the carrier web and spindle flange (doc 14), with a
   strain relief tie on the ring. Tinned lugs at the terminal box (H₂S,
   doc 04).
6. PT100 leads: twisted triples, out through the same holes in a separate
   sleeve.

### 5.10 Pre-VPI tests

| Test | Accept |
|---|---|
| Phase resistance at 20 °C | **0.217 Ω** ±3 % per phase; the three phases within **±1 %** of each other |
| Insulation resistance, 1 kV DC, 1 min | ≥ 500 MΩ (dry, unimpregnated) |
| Surge, phase against phase, 3.5 kV peak | Waveforms match within 5 % (finds a reversed or shorted coil) |
| Polarity check | Low-voltage DC (2 A) into each phase, compass or Hall probe at each tooth tip: pattern **N S N, S N S** … matches Appendix A |
| PT100 | Each sensor reads ambient ±0.5 K |

**This is the last point where a segment can be changed easily.** Do not
start VPI until all pre-VPI tests pass.

### 5.11 S100 Vacuum-pressure impregnation (frame NP1-T07)

1. **Mask** the tooth-tip OD (air gap surface), the carrier bolting face,
   dowel holes, bolt holes, the Ø28 cable holes and lead ends with silicone
   tape and plugs.
2. Weigh the stator (record m₀). Measure **capacitance and tan δ** phase to
   core at 1 kHz (record).
3. **Pre-dry** in the oven: 4 h at 130 °C (removes moisture from liners and
   the winding).
4. Cool to resin temperature (typically 50 to 60 °C) and place in the tank.
5. Vacuum to **≤ 1 mbar** and hold **2 h** (hold until the pressure rise
   test with the pump isolated is < 0.5 mbar in 5 min).
6. Admit resin under vacuum until the stator is covered by **≥ 50 mm**;
   hold under vacuum 15 min.
7. Pressurise with **dry nitrogen to 5 bar**, hold **2 h**.
8. Release, lift, drain 30 min while turning the frame slowly.
9. **Cure rotating** in the oven per the resin datasheet (typically 6 to
   10 h at 150 to 160 °C), turning at 2 to 5 rpm until gelled, so resin
   does not drain from the top slots.
10. Remove masking; clean the tooth tips; no resin build-up on the tip OD
    (max 0.05 mm, check with the stand probe; remove by hand with a plastic
    scraper, never by grinding).
11. Weigh again (m₁): resin uptake **m₁ − m₀ ≈ 3 to 5 kg** (target set on
    Q1). Measure capacitance and tan δ again: capacitance must rise (Q1 sets
    the minimum rise that showed full impregnation in the section cut).

### 5.12 S110 Pot the end windings (moulds NP1-T08)

1. Pre-heat the stator to 60 °C.
2. Fit the front and rear silicone moulds; they define the potting envelope:
   **x 321 to 343 and x 417 to 439, r 232 to 296** (stays inside the stator
   OD, away from the clamp ring bolts and the carrier web).
3. Mix the filled epoxy, **degas** under vacuum, pour slowly from one point
   so air leaves ahead of the front; use a vacuum chamber for the stator if
   available.
4. Cure per datasheet with a slow ramp (≤ 1 K/min) to keep exotherm and
   shrinkage stress low. Demould, deburr, check for voids and cracks.
5. Protect the connection ring joints: they are inside the rear potting.

### 5.13 S120 Final stator tests (doc 15, T0)

All at 20 ±5 °C, results corrected to 20 °C and recorded.

| Test | Standard | Accept |
|---|---|---|
| Phase resistance | 4-wire | 0.217 Ω ±3 %, balance ±1 % (unchanged from pre-VPI) |
| Insulation resistance, 1 kV DC | IEEE 43 | **≥ 1,000 MΩ** at 40 °C equivalent; **PI ≥ 2.0** |
| AC hipot, phases together to core | IEC 60034-1 | **2.3 kV rms, 1 min** (2 U + 1 kV with U = 630 V, the highest rms line voltage at 250 rpm cold). Any repeat test at 80 % (1.8 kV) |
| Hipot, phase to phase | IEC 60034-1 | 2.3 kV rms, 1 min, star point opened if accessible; otherwise surge only |
| Surge, each phase | IEC 60034-15 method | **3.5 kV peak**, phases match within 5 % |
| Partial discharge inception | IEC 60034-18-41 (type I) | **PDIV ≥ 1.9 kV peak** phase to core (1.2 kV winding peak from doc 12 × 1.25 ageing × 1.25 temperature/humidity; confirm the factors in the Q1 qualification) |
| Capacitance and tan δ | 1 kHz | Within the Q1 band |
| Tooth-tip run-out | Stand NP1-T05 | **≤ 0.05 TIR** |
| PT100 | | All 6 + spares read ambient ±0.5 K |
| Visual | | No cracks in potting, no resin on gap or bolting surfaces |
| Mass | | Record (≈ 115 kg with carrier) |

The stator is then stored covered, with a desiccant bag, until joining.

---

## 6. Rotor

### 6.1 R10 Drum weldment NP1-210

Drawing NP1-210 Rev B (doc 17). Process:

1. Shell: seamless ring-rolled forging, or plate-rolled with a full
   penetration longitudinal seam (100 % UT to EN ISO 17640, level 2). Raw
   wall under the magnet zone ≥ 13.8 + 3 mm machining allowance each side.
2. Weld the inner hub web, outer web, bearing tube and rear flange ring in a
   jig that keeps the axis straight. WPS qualified to EN ISO 15614-1,
   preheat as required for the thickness, quality level B to EN ISO 5817.
3. NDT: **100 % MT** of all fillet welds, **100 % UT** of full-penetration
   welds.
4. **Stress relieve**: 580 to 620 °C, 1 h per 25 mm (min 1 h), furnace cool
   to 300 °C. This is essential for holding 0.02 mm after machining.
5. Shot blast Sa 2.5 outside; prime outside only (the inside is machined).

### 6.2 R20 Machine the drum in one set-up

Clamp on the outer web and rough-turn everything, rest 24 h, then
finish-machine **all of these in one set-up**:

| Feature | Size | Tolerance |
|---|---|---|
| Cup seats (front and rear) | Ø210 P7 | Coaxial **0.01** to each other |
| Magnet seat | **Ø618.4**, x 335 to 425 | +0.05/0; run-out **≤ 0.02** to the cup seat axis; Ra ≤ 3.2 |
| Shell bore outside the magnet seat | Ø624 | |
| Hub face and spigot | Ø360 f7, face ⟂ 0.02 | Hub bolts 12 × M16, PCD 400 |
| Rear flange ring face | Ø710 | Face ⟂ 0.03; disc bolts 24 × M10 on PCD 678, rear cover bolts 24 × M10 on PCD 644 |

Measure on the machine before unclamping: cup seat diameters and
coaxiality, magnet seat diameter at 3 axial × 8 angular positions, run-out.
Record the actual **magnet-seat run-out**: it enters the air gap budget
(0.020 allowed).

### 6.3 R30 Pre-balance the bare drum

Balance on a mandrel through the cup seats to **G6.3 at 250 rpm** (residual
≤ 35,700 g·mm for the complete rotor mass of 149 kg; apply proportionally to
the bare drum). Correction by drilling the outer web outside the magnet zone.
Final balance is done with the hub on the bench (G2.5, ≤ 14,200 g·mm, doc 14).
After the magnets are in, the rotor must never go on a balancing machine
with steel parts near the drum bore.

### 6.4 R40 Prepare the magnet seat and fit the pole comb

1. Mask everything except the magnet seat (x 335 to 425).
2. **Grit blast** the seat with clean alumina, Ra 3 to 6 µm. Blow off,
   degrease with acetone, then apply the adhesive maker's primer within
   **4 h** of blasting.
3. Drum on the **non-magnetic rotary table**, axis vertical, **rear end up**
   (open end; the rear cover is not fitted yet).
4. Bond the **40 comb bars** (GRP, 9.6 × 7.0 × 74 mm) at the pole gaps
   using an aluminium indexing template located on the hub spigot: pole
   pitch **9.000°**, bar centre tolerance **±0.05°** (±0.27 mm at r 305).
   Comb bar 1 at the angle marked on the drum from the hub bolt hole 1.
5. Bond the **front G11 end ring** at x 335 to 343 (closes the front end
   of the magnet pack).
6. Cure the comb at room temperature for 24 h.

### 6.5 R50, R60 Receive, sort and bond the magnets (jig NP1-T02)

**Receive and sort (in the magnet room):**

1. Count against the packing list; check the dot colour of every piece
   against its variant label.
2. Measure the magnetic moment of every piece in the **Helmholtz coil**
   (NP1-T09): accept within ±1.5 % of the lot mean, matching the supplier's
   value within ±1 %.
3. Visual: no chips > 0.5 mm, no coating damage. Chipped pieces are
   scrapped (section 2.4), not repaired.
4. **Sort into poles:** 4 pieces per pole so that the 40 pole sums are within
   **±0.5 %** of each other. Then place the poles so that strong and weak
   poles alternate around the drum. Record the piece serials per pole
   position.

**Bond (two people, written procedure signed):**

The jig NP1-T02 is an aluminium carriage that runs on a rail along the drum
axis, indexed on the comb. It holds one magnet in a POM shoe 5 mm off the
seat, slides it axially into its channel and lowers it with a fine-pitch
**austenitic stainless or brass screw** onto the adhesive.

1. Mix adhesive with **0.15 mm glass beads** (1 to 2 % by weight); apply a
   thin, even layer on the seat in the channel, and butter the convex magnet
   face. Respect the pot life; mix only for 4 poles at a time.
2. Order of poles: **first all 20 N poles** (every second channel), then
   cure, then **all 20 S poles**. An S piece entering a channel between two
   N poles is pulled equally from both sides, so the fresh bond carries no
   side load.
3. In each channel place the **rear-most piece first** (deepest, x 398.8
   to 417), against a PTFE stop, then the next three pieces with a
   **0.2 mm PTFE shim** between pieces. Pieces of the same pole **repel
   each other axially**: hold each one with the jig's axial clamp bar until
   the next is down, and leave the clamp bar on the full pole until cure.
4. Lower each piece slowly with the screw; the last 2 mm the pull rises
   steeply, so the screw must stay in control. Squeeze-out is wiped with a
   plastic spatula.
5. Check with the gaussmeter that the pole face reads the right polarity
   (N poles: north on the inside) before the adhesive gels.
6. Cure 24 h at room temperature, remove clamp bars and shims (shims of
   PTFE come out; any that stick stay, they are non-magnetic).
7. After all 40 poles: fit the **rear G11 end ring** (x 417 to 425), then
   **post-cure** the drum at **80 °C for 4 h** (ramp ≤ 1 K/min). N40UH is
   unaffected at 80 °C.

### 6.6 R70 Pole map (scanner NP1-T10)

With the drum on the rotary table, scan the radial field 1.0 mm from the
magnet faces at mid-stack and at both piece ends, 0.1° steps:

| Check | Accept |
|---|---|
| Polarity sequence | Strictly alternating N/S, 40 poles |
| Pole peak and flux (integral) | Each pole within **±2 %** of the mean |
| Pole centre angle | Within **±0.1°** of nominal |
| Axial uniformity | No dip > 5 % over a piece joint (missing or cracked piece) |

Keep the map in the record: it is the reference for the teardown inspection
(doc 15, T9).

### 6.7 R80 Mould the encapsulation sleeve (mandrel NP1-T06)

The sleeve closes the magnet pack and defines the rotor bore.

1. The mandrel is **aluminium** (non-magnetic, no pull), Ø**602.0
   +0/−0.02** at 20 °C, release-coated, with two precision spigots that
   locate in the **front and rear cup seats** of the drum. Its surface is
   therefore concentric with the bearing axis within the mandrel's own
   run-out (≤ 0.01).
2. Wrap the dry glass fabric on the mandrel (layup set on Q1 so the cured
   sleeve is 0.4 to 0.6 mm everywhere), plus a 5 mm overlap onto each G11
   end ring.
3. Lower the mandrel into the drum (axis vertical) with the crane, spigots
   into the cup seats.
4. Seal the ends; **vacuum infuse** the resin from the bottom, vent at the
   top until resin flows clear.
5. Cure 24 h at room temperature, then post-cure **80 °C, 4 h**. Cool the
   assembly: aluminium shrinks more than steel, so the mandrel releases by
   itself; pull it straight out with the crane.
6. Trim flash at the ends. **Nothing on the rotor may be ground or
   machined after the magnets are in.**

### 6.8 R90 Complete the rotor

1. **Inspect the sleeve bore**: diameter at 3 axial × 8 angular positions,
   **Ø602.0 +0.05/−0.02**, run-out to the cup seats **≤ 0.03**; tap-test for
   voids (none > 10 mm). Record.
2. **Press both cups** into the drum (cups cooled to −30 °C or drum warmed
   to 60 °C, do not exceed 80 °C), check seating with a 0.03 feeler.
3. Fit the **rear seal cover NP1-211** with its 195 × 220 × 12 lip seal onto
   the drum housing (Rev B order, doc 17).
4. Slide the **brake disc NP1-230 on from the front** over the Ø646 shell
   (Rev B), 24 × M10 10.9 on PCD 678, torque per drawing.
5. Fit the magnet-zone cover: a POM ring that closes the drum bore for
   storage, with the label **"Magnetised rotor, strong field inside"**.
6. Weigh (≈ 149 kg with disc and covers; record).

---

## 7. Interfaces to check before joining

| Interface | Check | Value |
|---|---|---|
| Stator tip OD to rotor sleeve bore | Calculated gap from measured diameters | **2.0 mm** nominal; minimum calculated radial gap at any point ≥ **1.80 mm** (budget 0.20 worst case, doc 14) |
| Stator bolting face to carrier rim axis | Record from S50 | Within 0.02 |
| Cable path | Leads and PT100 through the Ø28 holes | No sharp edges; grommets fitted |
| Rear seal cover and disc on the drum | Rev B | As section 6.8 |

If the calculated minimum gap is below 1.80 mm, stop and review with
Category 4 before joining.

---

## 8. Joining stator and rotor (assembly bay, magnet hazard)

This follows the Rev B order in doc 17 (§2.1). Steps 1 to 3 have no magnet
hazard; step 4 is the critical step.

| Step | Work |
|---|---|
| J10 | **Spindle prepared** (doc 14 §7.2 step 3): cooling insert shrunk in, PT100s under the cones. Spindle **vertical, nose up**, flange bolted to the assembly stand |
| J20 | **Stator onto the bare spindle**: lower the stator over the nose onto the flange, leads through the Ø28 holes. Thermal paste on the bolting face, 2 dowels, **12 × M12 10.9, 110 Nm** (doc 14) |
| J30 | **Seal sleeve NP1-102** with O-ring onto the Ø155 shoulder; **rear cone** pressed against the sleeve and shoulder (cone heated to 100 °C max, induction heater) |
| J40 | **Rotor over the stator** with guide NP1-T01 (below) |
| J50 | **Front bearing**: front cone, spacer NP1-101, KMT 27 nut; set end play **−0.02 to −0.05 mm**; record rolling torque; **then** the front seal cover (doc 17) |
| J60 | **Rear cover** NP1-212 with the Ø400 seal over the flange; breather; measure the air gap |

### 8.1 J40 Lowering the rotor (written procedure, two people plus a supervisor)

1. Clear the zone: no loose steel within 2 m, pacemaker check, all tools
   non-magnetic (NP1-T11).
2. Fit the guide tool NP1-T01 on the spindle nose. Its guide sleeve centres
   the drum through the front cup seat; the screw jack carries the rotor.
3. Insert **four G10 feelers 1.5 mm** at 90° into the gap entry (tied with
   cord so they can be pulled out later).
4. Lift the rotor (rear end down, magnets towards the stator) with textile
   slings, hand it over to the screw jack above the guide.
5. Lower **by the screw only**. Watch the gap at the four feelers. If any
   feeler becomes tight, **stop** and check the guide; never push sideways
   by hand. The rotor is self-centring only while the guide holds it; any
   offset is pulled further at 1.9 kN per mm.
6. When the rear cup is seated on the rear cone, remove the jack load,
   pull out the feelers.
7. Turn the rotor slowly by hand through one full turn: it must turn freely
   with only the bearing drag and a smooth cogging feel (cogging ≈ 0.85 Nm
   peak-to-peak, barely noticeable). Any rub: lift and inspect.

### 8.2 J60 Air gap measurement

Through the inspection port in the rear cover, with **brass or plastic**
feeler gauges, at **8 positions × 2 axial ends** (turning the rotor by
45° steps), measure the gap between the sleeve and the tooth tips:

| Accept | Value |
|---|---|
| Every reading | ≥ **1.80 mm** |
| Max − min (eccentricity × 2) | ≤ **0.20 mm** |

Record. Then fit the plug in the port.

---

## 9. Generator tests after joining

Done on the assembly stand (no rotation needed) and then on the bench
(doc 15). These are the generator-specific acceptance values.

| Test | When | Accept |
|---|---|---|
| Phase resistance, IR, PI | After joining | As 5.13 |
| AC hipot | Not repeated; if required, 80 % (1.8 kV) | |
| Hand-turn back-EMF polarity | Rotor turned slowly by hand, scope on the phases | Positive sequence defined for the design rotation, three equal phases |
| **Back-EMF** (doc 15, T2) | Bench, 50, 100, 178 rpm, magnets at known temperature | Line EMF **≈ 2.42 V/rpm at 20 °C** (≈ 430 V at 178 rpm; scaled value, replace with the FEA rerun) within **±3 %**; phases within ±1 %; THD ≤ 1.5 % |
| Cogging (T2) | Bench, slow turn, torque transducer | ≤ 0.5 % of rated (≤ 4 Nm) |
| Short circuit and demag check (T3) | Bench | EMF change after test ≤ 0.5 % |
| Load and efficiency (T4) | Bench | η ≥ 93 % at rated |
| Thermal (T5) | Bench | Hot spot ≤ 130 °C at 110 % |

---

## 10. Q1 process qualification (before P1 parts are committed)

Doc 04 already asked for a stator segment trial. With the segmented design
this becomes a short, decisive qualification. Build in weeks 3 to 8 while
the magnets are on order.

| Article | Content |
|---|---|
| Q1-S stator sector | **5 wound segments** (one full group +A −A +A plus one neighbour each side) in a 40° carrier sector of real material, liners, wedges, connection joints, 2 PT100s, VPI and potted like P1 |
| Q1-M magnet panels | 3 flat steel panels with grit blast + primer, each with 4 unmagnetised test pieces bonded and sleeved as P1; 12 single lap-shear coupons |
| Q1-T motorettes | 6 twisted-pair and coil motorettes in the P1 insulation system (IEC 60034-18-21/-41) |

| Test | Accept |
|---|---|
| Winding: all 5 coils wound to the layer plan, coil fit into the sector without force | Yes; record wind time per coil |
| Coil resistance vs calculated | Sets the P1 acceptance mean |
| VPI: section-cut one segment after cure, inspect slot fill | Resin-filled, voids < 5 % of slot area, no dry areas between strands; sets uptake and capacitance-rise targets |
| Potting: 50 thermal cycles −40 / +150 °C | No cracks, no debonding, IR ≥ 1,000 MΩ after cycling |
| PDIV and RPDIV on motorettes, dry and at 90 % RH | Confirms the 1.9 kV peak target |
| Thermal endurance on motorettes (short form) | No early failure versus class H rating |
| Magnet bond lap shear at −40, 23, 120 °C, after 50 cycles | ≥ 15 / 15 / 5 MPa |
| Salt-fog on Q1-M panel, 1,000 h (ISO 9227 NSS) with a scribed sleeve | No corrosion under the sleeve beyond 2 mm from the scribe |
| Sleeve thickness by section | 0.4 to 0.6 mm |

Q1 results go into this document as revision B (targets replaced by
measured values) before the P1 winding starts.

---

## 11. Records, traceability and repair

**Generator record (one per serial):**

- Material certificates: steel coil, wire lot, liner, resin and potting lot,
  magnet lot with per-piece moment, adhesive lot, drum and carrier steel.
- Segment traveller: serial, sheet count, height, tip radius, coil test
  results, position on the carrier.
- Stator: run-out map, pre-VPI and final tests, VPI log (vacuum, pressure,
  temperatures, uptake), potting log.
- Rotor: drum machining record, balance, pole sort table, bonding log
  (who, when, adhesive lot, room temperature and humidity), pole map,
  sleeve bore map.
- Joining: gap readings, bearing end play, rolling torque, torques.

**Repair rules:**

| Fault | Before VPI | After VPI |
|---|---|---|
| Coil failed test | Pull the segment, replace with a spare | Strip the stator (burn-off oven not allowed with bonded segments; chemical/solvent strip) and re-wind affected segments, or replace the stator. This is why all coil tests happen before VPI |
| Magnet cracked or misplaced | Before sleeve: remove by heating the bond to 150 °C locally and replace | After sleeve: return the rotor to the magnet room, cut out the sleeve over the pole, replace, re-sleeve that section and repeat the pole map |
| Sleeve void | Fill by injection with sleeve resin | Same |

---

## 12. Open items

| # | Item | Owner | Due |
|---|---|---|---|
| 1 | **Decision on the stator build route (M1)**: segmented (recommended), open slots with magnetic wedges, or drop-in (Appendix C) | Martin | Before drawings |
| 2 | FEA rerun with segment joints and tolerance scatter; freeze turns (27 or 28) and the expected EMF | Cat. 4 | Week 1 |
| 3 | Magnet eddy-loss check, then place the magnet order | Cat. 4 | Week 1 |
| 4 | Drawings NP1-200 Rev C, NP1-201 Rev C (segment DXF), tools T03 to T10, connection ring | Cat. 4/10 | Weeks 1 to 3 |
| 5 | Choose resin, potting compound and adhesive products; get maker approval for the wire enamel and magnet coating | Cat. 10 | Week 2 |
| 6 | Q1 qualification, revise this document to revision B | Cat. 10/11 | Weeks 3 to 8 |
| 7 | Update doc 12 for the worst-case voltage with the frozen turn count | Cat. 7 | After item 2 |
| 8 | Series route (stamping die, larger VPI batches, automated winding) after P1 | Cat. 10 | After P1 |

---

## Appendix A. Coil connection plan

Teeth are numbered 1 to 45 in the direction of rotation, tooth 1 at the
reference mark on the carrier (12 o'clock, aligned with dowel 1). Full table
with series position: [`coil_connection.csv`](../analysis/generator/results/coil_connection.csv).

| Teeth | Phase and sense |
|---|---|
| 1, 2, 3 | +A, −A, +A |
| 4, 5, 6 | +C, −C, +C |
| 7, 8, 9 | +B, −B, +B |
| 10 to 18, 19 to 27, 28 to 36, 37 to 45 | Same 9-tooth pattern repeated (5 repeats) |

Phase A in series: 1 → 2 (reversed) → 3 → 10 → 11 (reversed) → 12 → 19 →
20 (reversed) → 21 → 28 → 29 (reversed) → 30 → 37 → 38 (reversed) → 39,
then the star point. Phase B starts at tooth 7, phase C at tooth 4, each
with the same pattern. Lead U = phase A start (tooth 1), V = phase B start
(tooth 7), W = phase C start (tooth 4). Confirm the phase sequence at the
hand-turn EMF test and swap V/W at the terminal if the design rotation
gives negative sequence.

## Appendix B. Key numbers for the shop

From [`manufacturing_summary.json`](../analysis/generator/results/manufacturing_summary.json):

| Item | Value |
|---|---|
| Slot width top / bottom / opening | 18.9 / 9.8 / 4.0 mm |
| Free area per coil side / copper | 425 / 211 mm² (fill 0.50) |
| Turn | 4 × Ø1.55 mm = 7.55 mm², 3.07 A/mm² at 23.2 A |
| Mean turn length | 227 mm |
| Wire per coil | 6.6 m per strand; ≈ 1,200 m of Ø1.55 for the stator |
| Copper | 20.1 kg in the winding; order 25 kg |
| Resistance at 20 °C | Coil 14.5 mΩ, phase 0.217 Ω, line to line 0.435 Ω |
| Copper loss at 75 °C, rated | ≈ 430 W |
| Segment sheets | 205 per segment, 9,225 in total (+5 %) |
| Magnet piece | 37.86 × 18.35 × 7.70 mm arc, 40.9 g, 6.55 kg total |
| Pull of one piece on steel | ≈ 280 N |
| Pole gap (comb bar width) at r 305 | 9.6 mm |
| Expected line EMF, 178 rpm | ≈ 392 V at 100 °C, ≈ 430 V at 20 °C (28 turns, scaled) |
| Worst-case peak, 250 rpm, −40 °C | ≈ 920 V (28 turns) / ≈ 890 V (27 turns) |
| Hipot / repeat / surge / PDIV | 2.3 kV / 1.8 kV / 3.5 kV peak / ≥ 1.9 kV peak |
| Balance at 250 rpm | G6.3 ≤ 35,700 g·mm (bare drum stage), G2.5 ≤ 14,200 g·mm (final) |

## Appendix C. Stator build routes compared (decision M1)

| | **A. Segmented stator (recommended)** | B. Open slots + magnetic wedges | C. As drawn, drop-in by hand |
|---|---|---|---|
| Core | 45 bonded tooth segments in dovetail grooves | One-piece bonded ring, tooth tips removed (slot open 18.9 mm) | One-piece bonded ring as doc 14 |
| Coil | Precision layer-wound on each tooth, fill 0.50 achievable | Pre-wound on a former, slid over the parallel tooth; fill 0.50 achievable | Fed wire by wire through 4 mm; ≈ 0.40 fill at best |
| Electromagnetic effect | Same shape; joints cost < 1 % EMF (FEA rerun) | Without tips the gap flux and cogging change; magnetic wedges (μr ≈ 3 to 5) recover most of it; FEA rerun needed | Copper −20 %: current density ≈ 3.8 A/mm², copper loss ≈ +25 %, hot spot ≈ +10 K, η about −0.5 %; or re-design slots |
| Air gap control | Segment tolerance + groove machining (±0.05 total) | One-piece ring, best run-out | One-piece ring |
| Testability, repair | Every coil tested before assembly; segment swap before VPI | Coils tested before fitting | Faults found only on the full stator |
| Long-term risk | Joint fretting prevented by VPI and clamp ring | Magnetic wedges can loosen and break under vibration over 20 years | Insulation damage while forcing wires in |
| Drawing changes | Lamination, carrier | Lamination, wedges | None |

Route A is the industry standard for concentrated-winding machines that need
high fill, and it fits the quality-first rule: every coil is the same,
tested, and the tightest dimensions are machined into a steel carrier, not
built up by hand.
