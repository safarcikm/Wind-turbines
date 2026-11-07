# 37 · 12 kW turbine M8 on an 8 m tower: load rerun, final checks and build book

Date 2026-11-07 · drawing set NM8 rev A · status NOT CHECKED (prototype release only after an independent check)

Martin, 2026-11-06: "Ok continue with the 8m design, finish what's missing." Doc 35 §12 sized an 8 m tower for the Ø8.0 m / TSR 5.5 rotor (M8) with loads scaled from 18 m. This doc finishes that design the way doc 34 did for the 6 kW S6: a full aeroelastic load set at 8 m hub height, a controller retune, final checks of blade, spindle, bearings, brake, tower and footing, a clash-checked 3D model, a drawing set, a BOM and a build book.

| Deliverable | File |
|---|---|
| Build book (74 pages A3: summary, part catalogue with an iso view of every part, all drawings, 13 assembly steps, commissioning, open items) | `cad/turbine_m8/out/M8-build-book.pdf` |
| Drawing set NM8 rev A (21 own sheets, PDF/PNG/SVG/DXF) | `cad/turbine_m8/out/NM8-drawing-set.pdf`, `out/{pdf,png,svg,dxf}/` |
| Bill of materials (88 lines incl. fasteners, cables, site materials) | `cad/turbine_m8/out/bom8.csv` |
| Axonometric views: parts, assemblies, 13 assembly steps | `cad/turbine_m8/out/iso/` |
| 3D model and clash check | `cad/turbine_m8/model8.py`, `clash8.py` → `out/model8-parts.json`, `out/clash8.json` |
| Loads at 8 m, controller variants | `analysis/variant_m8/dlc8_m8.py`, `ctrl8_m8.py` → `results/dlc8_m8/`, `results/ctrl8_m8.json` |
| Blade, spindle, tower final | `results/blade_m8_8m.json`, `results/spindle_m8.json`, `results/tower8_m8.json` |

Project files copy: `turbine-12kw-m8/build-book-8m/`.

## 1 · Loads at 8 m hub height

All 103 load cases of doc 35 were rerun at 8 m hub height. Near the ground the wind is rougher: turbulence I15 = 0.24 (+23 %, as in doc 34) and shear exponent 0.25 across a rotor that spans 4–12 m above ground. The tower in the simulation is the stiff 8 m tube (f1 2.7 Hz) with its 3P exclusion zone.

**The 18 m controller does not work at 8 m.** With the doc 35 pitch controller the rotor reached **219.6 rpm** in a turbulent gust, beyond the 184 rpm the generator is rated for (881 V peak). The pitch loop was too soft for the larger gusts. I tuned it on the 8 worst cases (`ctrl8_m8.py`):

| Setting | Trips (of 8 worst cases) | Peak rpm | Power produced, sum of the 8 cases |
|---|---|---|---|
| 18 m controller: pitch ωn 4 rad/s, trip 154.6 rpm, 15 °/s | 8 | 219.6 | 56.8 kW |
| ωn 6 (trip 154.6) | 8 | 163.0 | 21.0 kW |
| ωn 8 (trip 154.6) | 8 | 160.9 | 21.4 kW |
| **ωn 6, trip 165 rpm, 20 °/s (chosen)** | 5 | 170.2 | 75.2 kW |
| ωn 6, trip 170 rpm, 20 °/s | 5 | 185.6 | 78.5 kW |

"Trips" are unintended overspeed stops in normal operation; fewer trips and more power produced are better. A stiffer loop alone (ωn 6–8) stops the overspeed but trips every case at the old 154.6 rpm limit. The chosen setting gives the fewest trips while keeping the peak below 184 rpm. Trip 170 rpm overshoots to 185.6 rpm and is rejected.

**8 m controller (commissioning settings):** pitch loop ωn 6 rad/s, normal pitch rate 20 °/s, overspeed trip 165 rpm. The pitch actuator and its supercap module must be confirmed at 20 °/s on the bench (open item).

Full set with the 8 m controller, design loads (γf included):

| | 18 m tower (doc 35) | 8 m, 18 m controller | **8 m, 8 m controller** |
|---|---|---|---|
| Peak rotor speed | 171.5 rpm | 219.6 rpm | **180.8 rpm** (DLC 1.3, 18 m/s) |
| Rotor thrust | 6.19 kN | 8.85 kN | **6.75 kN** |
| Blade flap moment at root | 11.87 kNm | 13.30 | **13.30 kNm** (+12 %) |
| Tilt moment at hub | 14.36 kNm | 16.01 | **16.01 kNm** (+12 %) |
| Yaw moment | 11.95 kNm | 12.41 | **12.41 kNm** |
| Tower base moment | 150.9 kNm | 69.4 | **68.5 kNm** (short lever) |
| Parked aero torque (design) | 12.58 kNm | 14.30 | **14.30 kNm** |
| Fatigue DEL flap / tilt / thrust | 3.78 / 6.83 kNm / 3.84 kN | — | **5.34 / 9.71 kNm / 5.48 kN** (+41 %, +42 %, +43 %) |

**Remaining trips.** 15 of the normal-operation runs still trip, all at 18–28 m/s or in extreme turbulence (DLC 1.3). Mean output at 18–24 m/s is 11.6–12.3 kW instead of 13.6 kW. Weighted with the highland wind distribution this costs about **2.0 % of annual energy** (54.0 vs 55.1 MWh; the 18 m controller at 8 m would lose 3.7 %). It is the price of the rough wind near the ground and is included in the energy figures below.

## 2 · Blade, spindle, bearings, brake

**Blade** (`structure_m8.py dlc8`, envelope = larger of 18 m and 8 m loads): the doc 35 carbon-cap blade passes unchanged, **34.1 kg**. Fatigue utilisation 0.13, edge 0.29; buckling of the cap at 1.0 governs as before (it is set by the SLM, not by the 8 m loads). One blade design for both towers.

**Spindle and bearings** (doc 14 detail model, `spindle_m8.py`, with the 8 m loads and the 104 mm generator stack of doc 35 that moves the hub flange from station 430 to 460):

| Check | Result |
|---|---|
| Hub bending moment at the flange | 18.2 kNm |
| Spindle static / fatigue reserve | 2.5 / 1.7 |
| Main bearings s0 front / rear | 6.7 / 6.2; axial 3.8; life factor 5.6 |
| Bolted joints, slip factor | hub flange 6.4 (separation 2.3), carrier 1.4, hub–drum 1.7, brake disc 1.7 |

All pass; no change to spindle or bearings.

**Brake.** The parked rotor at 8 m sees more aerodynamic torque (characteristic 10.6 kNm, design 14.3 kNm, vs 9.3 / 12.6 kNm at 18 m). The 3 calipers of doc 35 (13.1 kNm) are not enough. **Raised to 3 × 4.8 kNm = 14.4 kNm**, spring clamp 16.2 kN per caliper at μ 0.4, effective radius 0.37 m. Same caliper family, stronger spring pack. The alternative of 2 × 7.2 kNm (bigger caliper) is listed under decision D2.

**Hub, pitch, yaw.** Hub and pitch (doc 35: crank r140, Dpw 300 pitch bearing) are unchanged; the yaw bearing Dpw 410 stays, because the simulated tilt moment (16 kNm) is far below the SLM value of 52.4 kNm it was sized for.

## 3 · Final 8 m tower and footing

Sized with the 8 m loads and the CAD head mass of **1,362 kg** (the doc 35 list said 1,280; the CAD adds the GRP cover and its arms, the met mast, the junction box and the third caliper bracket).

| | Doc 35 §12 (scaled) | **Final** |
|---|---|---|
| Tube | Ø420 → Ø400, 10 / 8 mm | **Ø400 straight, 10 mm lower can / 8 mm upper, 6.87 m, S355J2+N, galvanised** |
| Mass | 689 kg | **671 kg** (lightest all-8 mm tube 611 kg, rejected: too close to 1P) |
| f1 rigid / soft soil with ice | 3.02 / 2.86 Hz | **2.78 / 2.65 Hz** (window 2.51–5.95 Hz) |
| 3P exclusion zone | 52–66 rpm | **48–61 rpm** (wind 3.4–4.2 m/s; passed under torque) |
| Governing case | earthquake 0.5 g + operation | same, utilisation **0.77** |
| Fatigue damage base / mid height | 0.85 (scaled) | **0.53 / 0.07** (simulated) |
| Base flange | 16 × M24 on 0.52 m | **16 × M24 10.9 on PCD 500**, 202.5 kN per bolt vs 254.2 kN |
| Tilt-up | — | base moment 150 kNm, winch line pull 66 kN (gin pole 0.33 H) |

The SLM tower check gives 1.29; as in doc 09 the SLM is a sensitivity check for the tower, not a design case, and the simulated envelope governs.

**Footings** (C30/37 XF4, B500C, depth 1.6 m): firm ground 3.0 × 3.0 m / 6.2 m³, frost-susceptible silt 3.2 m / 7.0 m³, soft volcanic ash 3.4 m / 7.8 m³, rock plinth with grouted anchors 2.0 m³.

**Energy at 8 m** is as in doc 35 §12 minus the 2 % trip loss above: −16 % highland, −18 % coast, −27 % open inland, −42 % sheltered, compared with the 18 m tower.

## 4 · 3D model and clash check

`model8.py` builds the whole M8 turbine in CadQuery from the existing parts:

- **Generator Rev D:** Rev C stretched by 30 mm for the 7 magnet rows (stack 104 mm, 280 blocks, doc 35). Renamed NP1-100D, 200D, 201D, 203D, 210D, 220F, 212C; sheet NM8-215 lists the changes. Doc 36 (magnet alternatives) may later replace the 280 blocks with 200 longer ones; the drum length is the same.
- **Rotor:** Ø8.0 m carbon-cap blades NM8-100 lofted from the doc 35 geometry, root Ø280 with 12 M16 inserts on PCD 245, hub NM8-200 (doc 35 dimensions) with spinner NM8-210 enlarged to R 520 so it clears the pitch bearings.
- **Bedplate NP8-300** (decision D1) and yaw ring Dpw 410 with gearmotors on r 358.
- **Brake:** third caliper on top at 135° with bracket NM8-311 (at 90° it hit the lock-pin holder).
- **Tower NM8-400**, hinge, foundation and anchor cage.

Fixes found by the clash check and done in the model: the hub rear gussets were shortened to x 199 and a spigot recess cut so the hub sits on the drum flange; the spinner was enlarged; the GRP cover front moved to −400 mm and its lower radius to 430 mm to clear the calipers and the yaw track.

20 contacts remain. They are intended (anchors embedded in concrete, gear mesh, pins in eyes, inserts in the blade, the mast in its junction box) or small overlaps (2–16 cm³) between the GRP cover and the cover arms, the yaw track and the stator flange. The cover is a hand-laminated part and will be trimmed at fit-up; its final cut-outs are an open item.

Masses from the model: rotor 455 kg, drivetrain 440 kg, nacelle 170 kg, yaw 288 kg, electrical 134 kg; head above the tower flange **1,362 kg**; tower with hinge 741 kg.

## 5 · Drawings, BOM, build book

Drawing set NM8 rev A, 21 own sheets: GA on the 8 m tower (000), index (001), BOM (002/003), nacelle (010), rotor (020), blade (100), root insert (105), blade mould set (110), hub (200), spinner (210), generator Rev D change sheet (215), pitch (250), bedplate NP8-300, brake with third caliper (311), yaw ring (911), tower 8 m (400), hinge (410), foundation (500), fasteners and torques (900), bought parts (910). Every sheet has an axonometric inset. Reused sheets (NP1 spindle and seals, Rev C generator, NY yaw parts, cover, electrical) are bound into the book.

The build book follows doc 34: summary, part catalogue with an iso view of every part, all drawings, 13 assembly steps with an iso view each (new parts in colour), torques (M16 10.9 280 Nm, M20 540 Nm, M24 tower base per sheet 900), checks, commissioning with the 8 m controller settings, and the open items below.

## 6 · Decisions still open (from doc 35)

Defaults are used in the model and the drawings:

- **D1** bedplate NP8-300 (136 kg) instead of NP1-300 as drawn (338 kg).
- **D2** brake: now **3 × 4.8 kNm** (14.4 kNm) because of the 8 m tower; alternative 2 × 7.2 kNm with a larger caliper.
- **D3** plain carbon caps on the blade.
- **D4** keep 28 turns.
- **D5** pitch crank radius r140 with the ~27 kN cylinder; the cylinder, crank and spinner are in the clash-checked model and only touch at the intended pin joints.

## 7 · Open items before the prototype release

- FE checks: hub shell and gussets; NP8-300 seat stiffness and flatness; caliper bracket NM8-311.
- GRP cover cut-outs at the yaw track, cover arms and stator flange (2–16 cm³ overlaps in the model).
- Supplier drawings to replace envelopes (yaw ring, gearmotors, bearings, calipers with 4.8 kNm spring), then rerun `clash8.py`.
- Pitch bench test at 20 °/s with the supercap module, and an overspeed test of the 165 rpm trip.
- The 15 remaining high-wind trips (about 2 % of energy): look at gust feed-forward or a rotor-speed set-point reduction above 18 m/s once real site data exist.
- On site: measure tower f1 (must be ≥ 2.6 Hz, else widen the exclusion zone) and log base strain for fatigue in the first winter.
- Site investigation: soil class, frost depth, earthing resistivity; fenced keep-out zone for the 4 m tip clearance.
- Blade first-article static test (SLM × 1.35), insert pull-out tests, mould acceptance.
- All drawings are NOT CHECKED.

## 8 · Rebuilding

```
cd analysis/variant_m8
python3 dlc8_m8.py && python3 ctrl8_m8.py && python3 structure_m8.py dlc8
python3 spindle_m8.py
cd ../../cad/turbine_m8
python3 model8.py && python3 bom8.py
python3 ../../analysis/variant_m8/tower8_m8.py   # uses the CAD head mass
python3 iso8.py all && python3 clash8.py && python3 drawings8.py && python3 buildbook8.py
```
