# 12 kW Wind Turbine for Iceland: Nacelle P1 Bench Test Plan

Status: **Draft, revision A** · 2026-11-02
Owner: Category 11 (Testing) with Categories 4, 5 and 8
Test article: [14 – Nacelle prototype P1](14-nacelle-prototype-p1.md)
Rig layout: drawing NP1-620, dummy hub NP1-600 ([drawing set](../cad/nacelle_p1/out/NP1-drawing-set.pdf))

## Summary

The bench drives the P1 nacelle through its hub flange with a motor and
gearbox, loads the generator with a regenerative inverter on a shared DC
bus, and applies hub moments and thrust with a servo-hydraulic load unit.
Ten test blocks, about **10 weeks**, take P1 from incoming inspection to
teardown. Each test has a pass criterion taken from the design documents,
so a failed test points to the document and number that was wrong.

| Block | What it proves | Key pass criterion |
|---|---|---|
| T0 Incoming and build checks | Parts and stator are as drawn | Stack OD run-out ≤ 0.05; insulation and surge pass |
| T1 Static stiffness and air gap | Gap held under load | Gap change ≤ 0.10 mm at 9.8 kNm |
| T2 No-load generator | Magnets and winding as FEA | EMF within ±3 % of doc 06; cogging ≤ 0.5 % |
| T3 Short circuit | Fault currents and magnet margin | Current within ±10 %; EMF change after test ≤ 0.5 % |
| T4 Load and efficiency | Rated power and efficiency | η ≥ 93 % at rated (R4.5) |
| T5 Thermal | Cooling path and fan failure | Hot spot ≤ 130 °C at 110 %; path ≤ 0.40 K/W |
| T6 Combined load running | Bearings, seals, gap under hub moment | Bearing ΔT ≤ 40 K; vibration within limits |
| T7 Brake, lock, yaw | Safety torques | 8.7 kNm brake hold; 8 kNm yaw slip ±15 % |
| T8 Endurance | No early wear-out | 500 h without trend changes |
| T9 Teardown | Inspect everything | No fretting, leaks, magnet damage |
| T10 Cold box (option) | −30 °C start | Seals tight, brake and yaw work |

---

## 1. Objectives and principles

1. **Measure every number the design depends on** (EMF, losses, thermal
   resistance, stiffness, brake torque) and feed it back into the models,
   so that the field prototype runs on validated numbers.
2. **Order tests from safe to severe.** Static before rotating, no-load
   before load, low speed before overspeed, short circuit only after the
   thermal behaviour is known.
3. **Stop rules:** any rub noise, a gap reading below 1.6 mm, bearing
   temperature above 90 °C, winding above 150 °C, vibration above 2 × the
   baseline, or a sudden change in any trend stops the test and triggers
   inspection.

## 2. Bench rig

| Element | Specification |
|---|---|
| Pedestal | Welded steel column on a strong floor or 6 t concrete block, 5° wedge so the spindle is horizontal, axis 1,200 mm above floor; first mode > 25 Hz |
| Drive | 37 kW 4-pole induction motor (240 Nm), 4-quadrant inverter, planetary gearbox i = 6: **1,400 Nm continuous, 247 rpm at base speed, 275 rpm with field weakening** |
| Torque measurement | 2 kNm flange torque transducer, class 0.05, with a disc coupling on each side; speed from the transducer encoder (≥ 1,024 ppr) |
| Generator load | Regenerative PMSM inverter (≥ 20 kVA, 1,200 V class semiconductors, doc 12) on a **DC bus shared with the drive inverter**. Grid draws only the losses (≈ 3 kW at rated). Later, the doc 12 SiC prototype converter replaces it |
| Load unit | 22220 E spherical roller bearing on the dummy hub shaft at x = −200 mm, housing pushed by a vertical servo-hydraulic cylinder (±30 kN) and, for static tests only, an axial cylinder (45 kN). Load cells on both. Max hub moment about the front bearing ≈ 12 kNm |
| Torque arm | 1.0 m arm bolted to the dummy hub bell, with a 15 kN hydraulic cylinder and load cell: static torques up to 15 kNm (brake, lock pin, yaw) |
| Short-circuit switch | 3-pole contactor rated for 125 A peak at 900 V, on the generator terminals, with a hall-effect sensor on each phase |
| Safety | Interlocked enclosure around the rotating parts, emergency stop chain that also trips both inverters and applies the P1 brake, overspeed relay at 260 rpm on the bench encoder, fire extinguisher class B/E |

## 3. Instrumentation

| Quantity | Sensor | Location | Rate |
|---|---|---|---|
| Shaft torque, speed | Torque transducer 2 kNm | Between gearbox and load unit | 10 kHz |
| Electrical power, voltages, currents | Power analyser, 6 channels, 0.05 % | Generator terminals and DC bus | 1 MHz sampling, 10 Hz values |
| Air gap | 4 capacitive gap sensors on tooth tips at 0/90/180/270° | Stator front end | 10 kHz |
| Drum run-out and tilt | 2 eddy-current probes on the drum OD, 1 axial on the disc | Bedplate brackets | 10 kHz |
| Winding temperature | 6 PT100 in slots (P1 parts) + 6 thermocouples on end windings | Stator | 1 Hz |
| Magnet and drum temperature | IR pyrometer through the rear cover port, plus 4 thermocouples on the drum OD | Drum | 1 Hz |
| Bearing temperature | 2 PT100 in the spindle under the cones | Spindle | 1 Hz |
| Cooling path | Air temperature in and out of the insert (4 thermocouples), differential pressure, flow (hot-wire anemometer) | Rear manifold | 1 Hz |
| Carrier and spindle temperature | 6 thermocouples along the heat path (stack ID, web, flange, spindle at 3 positions) | Stator carrier, spindle bore | 1 Hz |
| Vibration | 4 triaxial accelerometers (spindle flange, bedplate front, bedplate rear, pedestal top) | | 20 kHz |
| Strain | 12 strain gauges: 4 on the spindle at the flange fillet, 4 on the drum web, 4 on the bedplate front plate | | 1 kHz |
| Loads | Load cells on cylinders and torque arm | Load unit | 1 kHz |
| Brake | Hydraulic pressure, caliper position switches | Calipers | 1 kHz |
| Ambient | Temperature, humidity | Test hall | 0.1 Hz |

All channels go to one DAQ with a common time base. Raw data and a test
log (who, what configuration, deviations) are kept for every run.

## 4. Test sequence

### T0 Incoming inspection and build checks

| Check | Method | Pass |
|---|---|---|
| Material certificates, Charpy, UT | Paperwork and witness | As NP1-100 notes |
| Dimensions of spindle, drum, carrier | CMM / boring mill probing | Drawing tolerances |
| Lamination stack | OD run-out, length, slot gauge, Franklin test | ≤ 0.05 mm; 74.0 ± 0.2; gauge passes; ≥ 10 Ω·cm² |
| Coils and winding | Resistance per phase (balance), insulation 1 kV, PI, surge test, hipot 2U+1000 V | Imbalance ≤ 1 %; IR ≥ 1 GΩ; PI ≥ 2; no surge waveform difference |
| Magnets | Flux of each piece, pole check after bonding (gaussmeter map) | ±1.5 % per piece; alternating poles |
| Bearings | End play and rolling torque at preload | −0.02 to −0.05 mm; supplier torque window |
| Air gap after assembly | Feelers at 4 × 90°, both ends | 2.0 ± 0.20 mm |
| Balance | In place, with dummy hub | G2.5 at 250 rpm |

### T1 Static stiffness and air gap (rotor locked by the lock pin)

Apply vertical force on the load unit in steps to 30 kN (≈ 12 kNm hub
moment), then axial force to 41.6 kN (SLM H parked thrust), each held
5 minutes, at four rotor positions 90° apart.

| Measure | Pass |
|---|---|
| Air gap change at 9.8 kNm (doc 08 design moment) | ≤ 0.10 mm at every sensor (budget, doc 14 §5.2) |
| Spindle fillet strain | Within ±15 % of the hand calculation (doc 14 §4.1); feeds the P2 FEA |
| Return to zero after unloading | ≤ 0.01 mm gap, ≤ 5 µm/m strain |

### T2 No-load generator tests (generator open circuit)

| Test | Method | Pass |
|---|---|---|
| Back-EMF vs speed | 20 to 250 rpm, record line voltages, cold and warm | Line EMF at 178 rpm within ±3 % of doc 06 (379 V hot); if outside, set turns for the series (27 or 28) |
| EMF waveform | Harmonic analysis | Line THD ≤ 1.5 % |
| Cogging | Turn at 0.2 rpm with a 100 Nm transducer in place of the 2 kNm one | ≤ 0.5 % of rated (≤ 4 Nm peak-to-peak); FEA 0.85 Nm |
| No-load losses | Torque vs speed, open circuit; then with the stator removed (rotor only, separate run or estimate) to split friction and iron loss | Iron loss within ±25 % of FEA (190 W at rated) |
| Bearing and seal drag | Torque at 1 to 10 rpm | Record (input for the control model's start-up) |
| Run-out at speed | Gap sensors 20 to 250 rpm | Dynamic gap variation ≤ 0.10 mm |

### T3 Short circuit and demagnetisation check

1. Steady three-phase short circuit at 50, 100 and 178 rpm, through the
   short-circuit switch, for 5 s each.
2. Transient short circuit from open circuit at 100 rpm, then at 178 rpm
   (the doc 05 worst case is 125.5 A peak with full offset).
3. Repeat the T2 back-EMF test.

| Measure | Pass |
|---|---|
| Steady short-circuit current | Within ±10 % of doc 05 (62.8 A peak) |
| Peak transient current | ≤ 130 A; braking torque peak recorded (input for the hub and drum bolt checks) |
| **EMF change after the tests** | **≤ 0.5 %** (any loss means partial demagnetisation) |

The transient test is done with magnets at room temperature; the 120 °C
worst case stays an analysis result (doc 05) unless the cold-box option
gets a heater.

### T4 Load and efficiency

Torque control by the load inverter, speed by the drive.

| Test | Method | Pass |
|---|---|---|
| Efficiency map | Speed 40 to 200 rpm × torque 10 to 110 % on the control curve and around it; input-output method (IEC 60034-2-1) at thermal equilibrium | **η ≥ 93 % at rated** (R4.5), target 94 % (doc 06) |
| Rated point | 802 Nm, 178 rpm | Phase current within ±5 % of 23.2 A |
| Torque ripple | Torque transducer high-rate data, cross-checked with current | ≤ 3 % (FEA 1.9 %) |
| Losses split | Copper loss from measured resistance and current; the rest is iron, magnet and stray | Within ±25 % of doc 06 (825 W total) |
| Voltage at overspeed | Open circuit at 250 rpm, cold | ≤ 900 V peak (doc 06: ≈ 890 V) |

### T5 Thermal tests

| Test | Method | Pass |
|---|---|---|
| Heat run, rated | 802 Nm, 178 rpm, both fans, until all temperatures change < 1 K/h | Hot spot ≤ 110 °C (doc 06 predicted 92 to 96 °C at +30 °C ambient, correct for hall temperature) |
| Heat run, 110 % | 880 Nm | Hot spot ≤ 130 °C (doc 06: 101 °C) |
| **Cooling path resistance** | From the carrier thermocouples and the air temperatures, with the insert heat flow from the air enthalpy rise | **≤ 0.40 K/W at full flow**; compare with 0.31 to 0.33 K/W (doc 14 §6) |
| One fan off, then both off | During the rated heat run | Winding temperature rise rate recorded; the doc 11 derate keeps the hot spot ≤ 130 °C |
| Anti-condensation heating | DC injection at standstill (doc 04) | ≈ 30 W keeps the winding 5 K above ambient |

### T6 Combined loads while running

Vertical load unit force in steps up to 15 kN (≈ 6 kNm hub moment) and as a
0.5 Hz sine (simulated 1P/3P tilt loads), at 60, 120, 178 and 210 rpm,
generator at rated torque.

| Measure | Pass |
|---|---|
| Air gap (minimum) | ≥ 1.80 mm at all times |
| Bearing temperature | ≤ 40 K above ambient, stable |
| Vibration | Below ISO 10816-21 zone A/B boundary for small turbines; no new frequencies with load |
| Seal leakage | No grease outside the seal covers after 8 h |
| Strain | Spindle and drum web strains for the P2 FEA and fatigue check |

### T7 Brake, rotor lock and yaw

| Test | Method | Pass |
|---|---|---|
| Static brake torque | Brake applied, torque arm load increased until slip | ≥ 8.7 kNm (both calipers); ≥ 4.35 kNm with one caliper (single failure) |
| Brake response | Release pressure dumped, time to full clamp | ≤ 1 s (doc 11: brake after 1 s) |
| Dynamic stop (R5.2) | From 210 and 250 rpm, drive torque off, generator torque off, brake only; inertia emulated by the drive up to its torque limit, plus a full-energy drag test at 60 rpm at reduced pressure | Stops; pad and disc temperatures recorded; energy capacity ≥ 74 kJ (scaled); no fade after 3 stops |
| Lock pin | Torque arm to 8.7 kNm with the pin engaged and the brake released | No permanent set; switch reports engaged |
| Yaw drive | Yaw ±360° at 0.5 °/s on the pedestal | Drive torque ≤ 1.5 kNm, position error ≤ 1° |
| Yaw brake slip | Torque arm on the bedplate (separate arm), slowly to slip | Slip at **8 kNm ±15 %** (R3.7); 0.5 kNm residual drag while yawing |

### T8 Endurance

500 h on a compressed load spectrum built from the doc 08 simulated
operation (Weibull-weighted speed and torque bins), with 2,000 starts and
stops, 200 brake applications and 50 yaw cycles. Every 100 h: vibration
spectrum, bearing temperatures, gap map, grease sample, rolling torque at
standstill, insulation resistance.

| Pass |
|---|
| No upward trend in vibration, bearing temperature or rolling torque beyond ±10 % of the 100 h values |
| Grease: no metal particles above the lab's limit, no water |
| Insulation resistance and PI unchanged |

### T9 Teardown and inspection

Disassemble in reverse order using NP1-T01. Inspect bearing raceways
(fretting, false brinelling, skidding marks), seal lips and counterfaces,
magnet bond and encapsulation, stator wedges and end-winding potting,
carrier bolting face (paste spread, fretting), brake pads and disc,
bolt preloads (measure the loosening torque). Photograph everything.

### T10 Cold box (option)

Insulated tent around the nacelle with a −35 °C refrigeration unit: soak
24 h at −30 °C, then start-up sequence of doc 11 (grease heaters, slow
start), brake and yaw function, seal leakage. This is the first −30 °C
check of seals and grease before the climate chamber tests of R11.3.

## 5. Schedule

| Week | Activity |
|---|---|
| 0 | Review of doc 14 and drawings; long-lead orders |
| 1 to 12 | Manufacture P1 parts; build the bench in parallel |
| 10 to 14 | Stator winding, VPI, T0 stator tests; rotor magnet bonding |
| 13 to 14 | Assembly, T0 build checks, balancing |
| 15 | T1 static, T2 no-load |
| 16 | T3 short circuit, T4 efficiency |
| 17 | T5 thermal |
| 18 | T6 combined loads, T7 brake and yaw |
| 19 to 22 | T8 endurance (500 h) |
| 23 | T9 teardown, report |
| (option) 24 | T10 cold box |

## 6. Outputs

1. Test report with every pass/fail result against this plan.
2. Updated models: generator FEA calibrated to measured EMF and losses,
   thermal model to the measured cooling path, spindle and drum stiffness
   to the strain and gap data.
3. P2 design inputs: measured strains for the cast drum, carrier and
   bedplate, real masses, the decision on the carrier material and the
   fan size.
4. Updated R-requirement status for R4.1, R4.2, R4.5, R5.1 to R5.3, R3.7.

## 7. Safety

- Written magnet handling and assembly procedure (doc 14 §7.2); no people
  with pacemakers or implants in the zone.
- Rotating parts fully guarded; access door interlocked with the drive
  enable and the P1 brake.
- High voltage: generator terminals reach about 900 V peak at 250 rpm open
  circuit. Terminals covered, discharge resistors on the DC bus, lock-out
  procedure before any work on the electrical side.
- Hydraulics: pressure relieved before work on calipers or cylinders.
- Short-circuit tests from a remote control station only.
