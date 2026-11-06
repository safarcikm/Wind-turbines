# 6 kW Turbine S6: Lighter Bedplate, Brake Decision, Drawing Set and 3D Model

Status: **for review** · 2026-11-06 (Martin: "Can u make the lighter bedplate, keep the current spring and then create a complete drawings/3d model and make it into a website")
Owner: Category 2 (Mechanical), Category 6 (Control and safety)
Builds on: [30 – Design S6](30-6kw-turbine-design-s6.md), [31 – Simulation](31-6kw-simulation-s6.md), [25 – Yaw](25-yaw-system.md)
Analysis: [`analysis/turbine_6kw/bedplate6.py`](../analysis/turbine_6kw/bedplate6.py) → `results/bedplate6.json`, `results/head6.json`; [`brake_hold6.py`](../analysis/turbine_6kw/brake_hold6.py) → `results/brake_hold6.json`
Drawings: [`cad/turbine_6kw/drawings6.py`](../cad/turbine_6kw/drawings6.py) → `cad/turbine_6kw/out/` (PDF, DXF, SVG, PNG)
3D model and drawings website: [`viewer6/`](../viewer6/), published at https://claude.ai/artifact/WBfQKfcMw89RepndbRGqxF

## Summary

| Item | Result |
|---|---|
| Lighter bedplate NS6-300 | **127 kg**, same interfaces as the 12 kW NP1-300. All checks pass with large margin (highest: bottom plate 144 MPa vs 323 allowed). |
| Head mass above the tower flange | **912 kg** (doc 30 used 935 kg; the tower and footings are kept as sized, so they are slightly conservative). |
| 12 kW bedplate NP1-300, as drawn | **333 kg, not 150 kg.** Docs 25 and 30 carried 150 kg. This affects the 12 kW head mass (see §2). |
| Brake spring | **Kept at 1.5 kNm** as Martin asked. The 2.5 kNm change from doc 31 is withdrawn. |
| Yaw-lost 50-year storm with 1.5 kNm | Holds (peak aero 1.45 kNm). If the aero torque is 35–60 % higher than simulated, the rotor creeps a fraction of a turn to two turns in 5 minutes, at most ≈ 20 rpm, against the brake and the closed resistor. No runaway. |
| Drawing set | 10 A3 sheets NS6-000 … NS6-610, revision A. |
| 3D model | Interactive website with the stall controller, part cards and the drawing set built in. |

## 1. Lighter bedplate NS6-300

The 12 kW bedplate (40 mm front and bottom plates, 20 mm sides and rear) was sized for a pitch-regulated 12 kW rotor. The S6 loads are lower (doc 31) and the parked SLM case governs. `bedplate6.py` models the weldment plate by plate, computes mass, and checks the root section, the front plate (spindle flange bolts), the bottom plate (yaw flange bending), the yaw bolts and fatigue at the root with the SLM γ = 3 loads.

| | NP1-300 (12 kW, as drawn) | NS6-300 (6 kW) |
|---|---|---|
| Front plate | 40 | 20, window 300 × 140 |
| Bottom plate (yaw flange) | 40 | 25, rear corners chamfered 150 × 150 |
| Side plates | 20 | 10, lightening holes Ø150 + Ø110 |
| Rear plate | 480 × 290 × 20 | tie 496 × 100 × 10 |
| Gussets | – | 2 × 12, 180 × 180 |
| Rear end x | +330 | +150 |
| **Mass** | **332.8 kg** | **126.7 kg** |
| Root section σ (allow 323 MPa) | 9.6 MPa | 20.8 MPa (0.06) |
| Front plate | 11.1 MPa | 50.7 MPa (0.16) |
| Bottom plate | 46.7 MPa | 144.2 MPa (0.45) |
| Yaw bolts M16 10.9 | 20.1 kN (0.22) | 20.1 kN (0.22) |
| Fatigue at the root | 0.03 | 0.07 |

Mass split NS6-300: front plate 45.2, front pad 7.9, bottom plate 36.3, side plates 26.6, rear tie 3.9, gussets 3.1, welds and bosses 3.7 kg.

Interfaces are unchanged: Ø410 × 10 pad with the Ø200 H7 spigot and 12 × M20 on PCD 350 for the spindle flange; Ø220 bore and 16 × M16 on PCD 300 for the yaw inner ring; side plate outer faces at ±260 for the NP1-420 gearmotor brackets; pad units NY-410, lock pin holder, cable hanger NY-460.

The plate thicknesses are now set by stiffness, flatness and machining, not strength. Before release: an FE stiffness check of the yaw ring seat (flatness 0.05 under load) and of the spindle flange face.

## 2. Head mass, and the 12 kW bedplate mass

| | kg |
|---|---|
| Doc 30 head above the tower flange (with 150 kg bedplate) | 935 |
| Bedplate replaced by NS6-300 | −150 + 127 |
| **S6 head** | **912** |
| S6 head if it had shared NP1-300 as drawn (333 kg) | 1,118 |

**Finding for the 12 kW machine.** The 150 kg used for NP1-300 in docs 25 and 30 was the doc 14 P1 estimate. The bedplate as now drawn (doc 16/17 geometry, 40/40/20 plates) weighs 333 kg. The 12 kW tower-top mass is therefore about 183 kg higher than carried in doc 25 (≈ 1,286 kg instead of 1,103 kg). That raises the yaw ring tilt moment and lowers the tower frequency a little. The 12 kW tower and yaw checks should be rerun, or the 12 kW bedplate should get the same lightening treatment.

## 3. Brake spring kept at 1.5 kNm

Doc 31 found that, in the parked 50-year storm with the yaw system lost (rotor facing the wind), the peak aero torque on the parked rotor is 1.45 kNm against 1.5 kNm of spring brake, and recommended 2.5 kNm. Martin decided to keep 1.5 kNm. `brake_hold6.py` checks what that means: the 50-year storm (V_ref 55 m/s, I 0.11, ρ 1.35) for 300 s with the yaw lost, rotor parked, brake allowed to slip, and K1 closed so the generator brakes into the resistors.

To show the margin, the brake torque was divided by 1.35 and 1.6 (the same as aero torque 35 % and 60 % higher than simulated):

| Brake torque | Parked position | Max speed [rpm] | Turns in 300 s | Blade root flap max [kNm] |
|---|---|---|---|---|
| 1.5 kNm (as built) | yaw error 8°, blade at 60° | 6.0 | 0.0 | 5.8 |
| 1.5 kNm (as built) | facing the wind, blade up | 3.5 | 0.0 | 4.9 |
| 1.5 kNm (as built) | wind from behind | 0.0 | 0.0 | 6.5 |
| 1.5 / 1.35 (aero +35 %) | yaw error 8°, blade at 60° | 10.1 | 0.1 | 5.8 |
| 1.5 / 1.35 (aero +35 %) | facing the wind, blade up | 9.8 | 0.3 | 4.8 |
| 1.5 / 1.35 (aero +35 %) | wind from behind | 0.0 | 0.0 | 6.5 |
| 1.5 / 1.6 (aero +60 %) | yaw error 8°, blade at 60° | 20.5 | 1.4 | 5.8 |
| 1.5 / 1.6 (aero +60 %) | facing the wind, blade up | 18.1 | 2.1 | 4.7 |
| 1.5 / 1.6 (aero +60 %) | wind from behind | 0.0 | 0.0 | 6.5 |

At 1.5 kNm the rotor twitches to a few rpm in the strongest gusts and settles back; it makes no net turn.

What it means in plain terms:

- **Normal storm parking is yawed 90° out.** There the aero torque on the rotor is about 0.1 kNm, so the brake has a large margin. The 1.45 kNm case needs the yaw system to fail (drives, aux battery and pad friction) at the same time as a 50-year storm.
- **With yaw lost, 1.5 kNm still holds** the simulated storm.
- **If the real aero torque is higher**, the rotor does not run away. The brake slips and the resistor loads the generator, so the rotor creeps at a few rpm, at worst around 20 rpm for seconds. The blades and hub see nothing new; the brake pads see some wear.
- **Parking azimuth does not fix it** (the yaw-lost torque is similar for every blade position), and **the lighter bedplate does not change it** (the brake sees rotor torque, not nacelle mass).
- **For long outages** (yaw drives or aux battery out of service in winter), insert the rotor lock pin NP1-320. The safety chain sheet NS6-600 says this, and a brake fault keeps the turbine parked and yawed out until repaired.

So no other change is needed to keep 1.5 kNm. If a later certification body asks for the yaw-lost storm to be held with a margin, the 2.5 kNm spring pack is a drop-in change in the same caliper.

## 4. Drawing set, revision A

`cad/turbine_6kw/drawings6.py` builds the set with the project drafting library (`cad/nacelle_p1/draft.py`). Output in `cad/turbine_6kw/out/`: `NS6-drawing-set.pdf`, and each sheet as PDF, DXF, SVG and PNG.

| Sheet | Title | Mass |
|---|---|---|
| NS6-000 | General arrangement · turbine | ≈ 912 kg head + 1,824 kg tower |
| NS6-001 | Parts list and reused 12 kW drawings | – |
| NS6-010 | General arrangement · nacelle section | ≈ 912 kg above the tower flange |
| NS6-100 | Blade · planform, twist and root | 20.6 kg |
| NS6-200 | Fixed hub weldment | 87 kg (+ 6 kg spinner) |
| NS6-300 | Bedplate weldment 6 kW (light) | 127 kg |
| NS6-400 | Tower 18 m · tilt-up monopole | 1,824 kg |
| NS6-500 | Foundation · spread footing and rock plinth | 9.5–11.4 m³ (soil), 2.0 m³ (rock) |
| NS6-600 | Braking resistor box and safety chain | ≈ 18 kg |
| NS6-610 | G6 plain rear cover (no fan blades) | ≈ 7 kg |

Parts carried over from the 12 kW machine (spindle, generator, disc, caliper, yaw system, electronics) keep their NP1 / NY drawings; NS6-001 lists them. The sheets are marked NOT CHECKED: prototype release only after review, and after the FE checks of the hub arm welds (doc 30 §11) and the bedplate ring seat (§1).

## 5. 3D model website

`viewer6/` is the 6 kW sister of the 12 kW viewer, published as a separate artifact (https://claude.ai/artifact/WBfQKfcMw89RepndbRGqxF). It shows:

- The whole turbine in mm from the design sources: fixed hub with the blades at −2°, G6 generator without ribs and fins, one caliper, NS6-300 bedplate, yaw system, 18 m Ø500 → Ø320 tower, footing, tower-base cabinet with the braking resistor box, and Martin's house for scale.
- The stall controller from docs 28 and 31, driven by a wind direction and speed slider (with gusts): TSR 5.9 to 163.6 rpm, stall control at 6.8 kW shaft (6.0 kW electric), storm ramp 25–30 m/s, storm park above 30 m/s with resistor, brake and yaw 90° out, restart below 22 m/s, 47.5–57.4 rpm skipped.
- Part cards with the drawing number and key data, each with a button to its sheet.
- The full drawing set inside the page (thumbnails, each sheet as a zoomable vector drawing, and the PDF).

## 6. Open items

1. FE stiffness check of the NS6-300 ring seat and spindle flange face.
2. 12 kW: rerun yaw and tower checks with the 333 kg bedplate, or lighten NP1-300 the same way (§2).
3. Tower and footings could be rerun for the 912 kg head; kept as sized (conservative).
4. Supplier choice for the caliper; confirm 1.5 kNm at −30 °C pad friction.
