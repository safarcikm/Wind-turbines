# 34 · 6 kW turbine S6 on an 8 m tower: complete mechanical design and build book

Date 2026-11-06 · drawing set NS6 rev B · status NOT CHECKED (prototype release only after an independent check)

Martin asked for the complete mechanical design of the 6 kW S6 with an **8 m tower**, a drawing and an axonometric view of every part, and a full build book, with authority to make the remaining design decisions. This doc summarises the result. The deliverable itself is the build book PDF.

| Deliverable | File |
|---|---|
| Build book (76 pages A3: summary, part catalogue with an iso view of every part, all drawings, 13 assembly steps, commissioning, open items) | `cad/turbine_6kw/out/S6-build-book.pdf` |
| Drawing set rev B (29 own sheets, PDF/PNG/SVG/DXF) | `cad/turbine_6kw/out/NS6-drawing-set.pdf`, `out/{pdf,png,svg,dxf}/` |
| Bill of materials (82 lines incl. fasteners, cables, site materials) | `cad/turbine_6kw/out/bom6.csv` |
| Axonometric views: 60 parts, 7 assemblies, 13 assembly steps | `cad/turbine_6kw/out/iso/` |
| 8 m tower, footing, energy, turbulence, noise | `analysis/turbine_6kw/tower8.py` → `results/tower8.json`, `E01-tower8.png` |

Project files copy: `turbine-6kw/build-book-8m/`.

## 1 · The 8 m tower

Hub height 8.0 m (tower top flange 7.07 m above ground; 0.20 m concrete pedestal; tube 6.87 m).

**Frequency strategy.** At 8 m a soft-stiff tower (f1 between 1P and 3P) is impossible: the window would be 0.75–1.86 Hz and a tube that short and strong enough is far stiffer. The tower is therefore **stiff**: f1 ≥ 1.15 × 1P at 164 rpm = 3.14 Hz. The 3P excitation crosses f1 during start-up, so the controller gets an exclusion zone.

| | Value |
|---|---|
| Tube | Ø460 → Ø320 conical, t 10 mm (lower can) / 8 mm (upper), one piece, S355J2+N, galvanised |
| Mass | 661 kg (CAD with flanges, hinge lugs, hand hole: 698 kg) |
| f1 / f2 | 3.50 Hz rigid base (3.28 Hz soft soil + ice) / 24.0 Hz |
| Exclusion zone | 3P crossing, **59.6–77.0 rpm** (passed under torque, not dwelt in) |
| Governing case | earthquake 0.5 g (ground D) + operation, M_base 238.6 kNm design; utilisation 0.45 |
| Base flange | 12 × M24 10.9 on PCD 560; 184.6 kN per bolt against 254.2 kN |
| Fatigue (turbulence factor 1.23 for 8 m) | damage 0.047 at the base, 0.025 at mid height |
| Tilt-up | base moment 114.7 kNm; winch line pull 50.6 kN with a gin pole 0.33 H |

Head mass used: **983 kg** (CAD), not 912 kg (doc 32 list). The extra is the GRP cover and its arms, the lock-pin holder and the junction box. With 983 kg the first, lighter tower draft (581 kg) dropped to 3.01 Hz, too close to 1P, so the walls went to 10/8.

**Footings** (C30/37 XF4, B500C), depth 1.6 m:

| Ground | Size | Concrete | Bearing |
|---|---|---|---|
| Firm (gravel, moraine) | 2.8 × 2.8 m | 5.5 m³ | 179 / 300 kPa |
| Frost-susceptible silt | 2.9 × 2.9 m | 5.9 m³ | 136 / 150 kPa |
| Soft volcanic ash | 3.1 × 3.1 m | 6.6 m³ | 99 / 100 kPa |
| Rock | plinth 1.6 × 1.6 × 0.8 m, 8 × Ø20 grouted anchors 3 m | 2.0 m³ | 92 kN per anchor |

## 2 · What the lower hub height costs

Log-law shear with site roughness, same 10 m reference climate as doc 28:

| Site | AEP at 18 m | AEP at 8 m | Change | Turbulence |
|---|---|---|---|---|
| Sheltered valley / farm (z0 0.25) | 11.8 MWh | 6.9 MWh | **−42 %** | +23 % |
| Open inland (z0 0.05) | 17.1 MWh | 12.6 MWh | −26 % | +16 % |
| Coast (z0 0.01) | 22.2 MWh | 18.3 MWh | −17 % | +12 % |
| Highland (z0 0.03) | 28.6 MWh | 24.2 MWh | −15 % | +15 % |

Noise: at the same 10 m wind the rotor turns slower at 8 m, so the source is ≈ 3 dB quieter (41.2 vs 44.1 dB(A) at 60 m). At rated it is the same source and the house is slightly closer: 45.5 vs 45.2 dB(A). Lowest blade tip 5.0 m above ground.

Recommendation: offer the 8 m tower for coast, highland and open land, where the loss is 15–26 %. On sheltered sites keep an 18 m option; at 8 m the turbine loses 42 % there and sits in building wakes.

## 3 · Design decisions taken (design authority)

1. **Pitch setting corrected.** Doc 30's wedge shims under the root flange cannot change pitch (they tilt the blade, they do not rotate it). S6 uses ±2.5° arc slots on PCD 185 in the hub root flange, hardened washer plates NS6-130 and an aluminium pitch gauge NS6-135. Factory setting −2.0°.
2. **Hub NS6-200**: shell lengthened to 295 mm so the three arms close on it; Ø220 × 8 arms, root flanges at r 280; 79 kg CAD (87 kg in doc 30).
3. **Nacelle cover NS6-700**: GRP 4 mm in two halves (lower tray, upper lid split at z 330), the generator drum stays outside the cover in free air. Galvanised arms and rear rail NS6-710, met mast NS6-720 with air terminal, junction box NS6-730.
4. **Tower NS6-400**: one piece with a base hinge NS6-410, hand hole and gin-pole lugs. No climbing; service by tilting the tower down with the gin pole NS6-420 and a winch.
5. **Blades**: production glass blades NS6-100 (20.6 kg), with mould set NS6-110 (plug, two halves, frame), root insert NS6-105 (10 per blade, M12) and root fixture NS6-115. Timber blades (doc 33) remain the prototype option.
6. **Drivetrain**: Rev C generator reused unchanged (segmented stator NP1-200C/201C/203C). Spindle cooling insert NP1-110 omitted. Only the left caliper bracket fitted; brake spring stays 1.5 kNm.
7. **Electrical**: braking resistor box NS6-600 and base cabinet NS6-620 on a galvanised stand beside the tower; cable routes, drip loop, earthing and lightning path on NS6-800.

## 4 · Parts and drawings

60 CAD parts in 8 groups (rotor, drivetrain, nacelle, yaw, electrical, tower, foundation, tooling). CAD masses: rotor 162 kg, drivetrain 378 kg, nacelle 168 kg, yaw 266 kg, electrical 134 kg; head above the tower flange **982 kg**; tower 738 kg with hinge and hand-hole cover.

New sheets in rev B: NS6-000 GA on the 8 m tower, 001 index, 002/003 BOM, 020 rotor, 101 blade sections and laminate, 105 root insert, 110 mould set, 115 root fixture, 130 pitch setting, 200 hub rev B, 210 spinner, 310 brackets, 400 tower 8 m, 410 hinge, 420 gin pole, 500 foundation, 510 anchor cage, 620 base cabinet, 700 cover, 710/720/730 cover arms, mast, junction box, 800 cabling, 900 fasteners and torques, 910 bought parts. Updated: 010, 100, 300, 600, 610. Every own sheet carries an axonometric inset. The reused 12 kW sheets (NP1 spindle, seal covers, lock, guide tool; Rev C generator; NY yaw) are bound into the book.

## 5 · Assembly sequence (book §6)

1. Bedplate on the stand; slewing ring, gearmotors, brackets
2. Spindle, front spacer, rear seal sleeve
3. Stator and bearing cones
4. Rotor drum over the stator on the guide tool; disc, seal covers, rear cover
5. Brake caliper, lock pin holder, overspeed sensors
6. Yaw pads, lock, encoder, cable hanger; cover frame, lower tray, junction box
7. Tower-top adapter (nacelle complete for transport)
8. Hub on the drum flange (12 × M16 10.9)
9. Blades with pitch washer plates, set to −2.0°
10. Spinner
11. Upper lid and met mast
12. On site: footing, anchor cage, hinge, tower lying on the hinge, head bolted on
13. Tilt-up, base nuts torqued; cabinet, resistor box, cabling, hand-hole cover

Each step has an iso view (new parts in colour, earlier parts light), instructions, torques and checks.

## 6 · Open items before the prototype release

- FE checks: hub arm-to-shell weld; NS6-300 ring seat stiffness and flatness.
- Stall torque measurement on the prototype, the main design risk of S6.
- Site investigation: soil class (plate-load test on volcanic ash), frost depth, earthing resistivity, obstacles at 8 m.
- Supplier drawings to replace envelopes (slewing ring, gearmotors, bearings, caliper), then rerun the clash check.
- Tower f1 measured on site ≥ 3.1 Hz, otherwise widen the exclusion zone.
- Blade first-article static test (SLM × 1.35), insert pull-out tests, mould acceptance.
- DSO confirmation for 6 kW single phase; IEC 61400-2 route.
- All drawings are NOT CHECKED.

## 7 · Rebuilding

```
cd analysis/turbine_6kw && python3 tower8.py          # needs design6 results (docs 30-32)
cd cad/turbine_6kw
python3 model6.py      # CadQuery model, out/model6-parts.json
python3 bom6.py        # out/bom6.csv/json
python3 iso6.py all    # out/iso/ (parts, assemblies, steps)  ~15 min
python3 drawings6.py   # NS6 rev B sheets + NS6-drawing-set.pdf
python3 buildbook6.py  # out/S6-build-book.pdf (needs reportlab, pypdf)
```

Run `tower8.py` again after `model6.py` if the head mass changes; it takes the larger of the CAD and doc 32 head mass.
