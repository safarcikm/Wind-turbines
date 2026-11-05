# 12 kW Wind Turbine for Iceland: Hub, Pitch and Yaw Systems

Status: **Draft, revision 1** · 2026-11-02
Owner: Category 3 (Hub, pitch and yaw)
Builds on: [02 – Design basis](02-design-basis.md), [07 – Nacelle](07-nacelle-spindle-bearings.md),
[08 – Load verification](08-load-verification.md), [10 – Blade structure](10-blade-structure.md),
[11 – Control and safety](11-control-safety.md)
Models: [`analysis/hub/run_pitch_duty.py`](../analysis/hub/run_pitch_duty.py) (duty simulation),
[`analysis/hub/hub.py`](../analysis/hub/hub.py) (sizing)

## Summary

| Item | Recommendation |
|---|---|
| Pitch concept | **Three independent electric pitch drives**, each with its own supercapacitor store and drive controller in the hub. Hydraulics, worm slew drives and a collective push rod were rejected (section 2) |
| Pitch bearing | **Four-point contact ball slewing ring**: pitch diameter 250 mm, 27 balls of 25.4 mm, outer Ø 355 mm, height 50 mm, about 21 kg. Induction-hardened 42CrMo4 rings, **internal gear on the blade-side (inner) ring** so the gear sits inside the sealed hub |
| Pitch drive | 48 V servo motor (≈ 0.4 kW, 2 Nm peak) with spring-applied holding brake, 1:100 planetary gearbox, 14-tooth pinion on a 48-tooth module 3 internal ring gear (1:343 total). **510 Nm peak at the bearing, 30 °/s**. Absolute encoder on the blade ring, limit switches at −2° and 91°, rubber end stops at −3° and 93° |
| Stored energy | One **supercapacitor module per axis** (21 × 350 F, 56.7 V, 16.7 F): **14 full emergency strokes** at −30 °C at end of life, against 2 required |
| Pitch axis | At **30 % chord**, the centre of the doc 10 box spar (webs at 15 % and 45 %) |
| Hub | **EN-GJS-400-18U-LT ductile iron casting**: central sphere R 0.22 m with three necks, 10 mm wall (castability, not strength), about **90 kg** |
| Hub to generator | **12 × M16 10.9** preloaded on a 400 mm bolt circle, slip-resistant joint (2.1 × margin on the 28.4 kNm SLM shutdown torque) |
| Yaw bearing | Four-point contact slewing ring, pitch diameter 360 mm, 53 balls of 19 mm, **external gear**, on the 320 mm tower-top adapter (static factor 1.9 on the SLM case) |
| Yaw drives | **Two planetary gearmotors**, 0.18 kW, not self-locking, torque-controlled by inverter; 0.5 °/s |
| Yaw brake | **Two spring-applied, hydraulically released calipers** on a brake ring, sharing the rotor-brake hydraulic unit: **8 kNm holding, slipping above that** (controlled slip, doc 07), 0.5 kNm residual drag while yawing |
| Mass | **Hub and pitch system ≈ 200 kg**, against 80 kg in the doc 07 budget. Tower top ≈ 600 kg instead of 480 kg (section 7) |

**Main findings**

1. **The pitch bearing is set by the SLM parked case, not by fatigue.** The
   26 kNm SLM root moment needs a 250 mm bearing with 25.4 mm balls. The
   simulated pitch duty uses less than 1 % of its rated life.
2. **Bearing friction is most of the pitch torque.** Aerodynamic and
   centrifugal twisting moments are below 100 Nm. Friction at −30 °C under
   the shutdown moment is about 350 Nm. Cold grease is therefore the design
   case for the motor, and lubricant heating before a cold start (doc 11)
   matters.
3. **The pitch system is very active above rated.** It travels about
   9,000° per hour and makes 230 million reversals in 20 years. Below rated,
   the blades sit at the fine-pitch stop 56 % of production time. The real
   bearing risk is **standstill marks and wear from small oscillations**,
   not rolling fatigue. This needs grease selection, a daily lubrication
   sweep and a test (new requirement R3.5).
4. **Doc 07 underestimated the hub and pitch system by about 120 kg.** On the
   18 m tower, f1 drops from 1.22 to 1.13 Hz and the speed exclusion zone
   moves from 66–80 rpm to about 62–75 rpm. On the 24 m tower on soft soil
   with ice, f1 is now 0.737 Hz, just above the 0.734 Hz limit. The 24 m
   tower needs a small stiffening in the next tower update (section 7).

---

## 1. Requirements and inputs

| Source | Requirement or input |
|---|---|
| R3.1 | Emergency feather at 30 °/s (45° in 1.5 s) from stored energy, without grid or controller; normal rate ≥ 15 °/s |
| R3.1a | Design overspeed 250 rpm, overspeed trip 210 rpm |
| R3.2 | Pitch and yaw operate at −30 °C, survive −40 °C |
| R3.3 | Pitch bearings and drives protected from ice and driven snow |
| R3.4 | Yaw error ≤ 10° average; hold or free-yaw safely on grid loss (DLC 6.2) |
| Doc 08 | Hub and pitch bearings to the **envelope of SLM and simulation**: root moment 26 kNm (SLM H), centrifugal 63.7 kN (SLM E), shutdown edge moment 10.4 kNm and shaft torque 28.4 kNm (SLM G), all γ_f = 3.0 |
| Doc 10 | Blade root Ø 0.22 m, 10 × M16 inserts on a 190 mm bolt circle, root at r = 0.40 m, blade 20.5 kg |
| Doc 11 | Pitch PI controller, 15 °/s normal limit; independent safety chain opens the pitch hold power; weekly stored-energy pitch test; yaw 0.5 °/s, keep yawing to the wind while parked (72 h backup) |

## 2. Pitch concept

| | **A. Electric, independent, supercaps (chosen)** | B. Hydraulic with accumulators | C. Worm slewing drives | D. Collective push rod through the spindle |
|---|---|---|---|---|
| Fail-safe feather | Each axis feathers from its own supercap; a single failure leaves two blades | Accumulators; proven in large turbines | Same as A, but self-locking worm means a jammed drive can't be back-driven | One actuator for all blades: a single failure loses aerodynamic braking (conflicts with doc 07 and doc 11) |
| −40 °C | Electronics and supercaps need heater pads; otherwise fine | Oil viscosity and seal leaks are the main cold problem | Fine, but efficiency drops to about 25–35 % in cold | Fine |
| Ice and salt | Gear and drive fully inside the hub | Rotary union, hoses, leaks inside the spinner | Sealed unit, but exposed at the blade root | Spindle bore is already used for cooling air and cables (doc 07) |
| Control quality | Precise, no backlash with preloaded pinion | Good | Backlash and low stiffness for 230 million reversals | Collective only, no individual pitch control later |
| Service | Swap a drive module; diagnostics from the controller | Oil changes, leak checks | Swap the unit | Simple |

**A** is the recommendation. It meets R3.1 per blade, keeps everything
inside the sealed hub, and leaves room for individual pitch control to
reduce loads later.

**Fail-safe chain:** the hardwired safety chain (doc 11) passes through the
slip ring to each pitch drive. If it opens, or the slip ring power is lost,
or the drive's own watchdog trips, the drive feathers its blade at 30 °/s on
supercap power alone. It stops on the 91° limit switch, and the holding
brake sets. No software is in this path except the drive's own fixed
sequence, which is certified with the safety system (ISO 13849, PL d).

## 3. Pitch moments

Model: steady BEM loading from the rotor model, a 360° flat-plate centre of
pressure model after stall, C_m0 = −0.08, centrifugal twisting moment from
the blade's mass distribution (chordwise mass radius of gyration 0.22 c).
Positive means toward feather. Values are for the 30 % chord pitch axis.

| Case | Aerodynamic | Centrifugal twisting | Comment |
|---|---|---|---|
| Operation 12–25 m/s at rated speed | +7 to +9 Nm | −6 to −11 Nm | Nearly balanced, tiny |
| Emergency feather at 250 rpm, 25 m/s, from 20° to 90° | +38 Nm at 25°, −73 Nm at 90° | −24 Nm peak | Worst moment against feathering: **−64 Nm** |
| Parked, feathered, V_e50 = 77 m/s, any direction | ±294 Nm (worst with the wind from about 130°) | 0 | Sets the **holding brake: 440 Nm** (1.5 ×) |
| Blade inertia about the pitch axis | 0.11 kg m² | | Negligible next to the reflected motor inertia (29 kg m²) |

Moving the axis to 25 % chord raises the feather moment to −91 Nm and the
storm moment to 344 Nm. Moving it to 35 % lowers them to −37 and 245 Nm.
None of these change the design, because friction dominates.

## 4. Pitch bearing

### 4.1 Static (Hertz contact), allowable 4,000 MPa

| Load case at the blade root | Most loaded ball | Contact stress | Static factor | Required |
|---|---|---|---|---|
| **SLM H parked, 26.0 kNm** (γ 3.0) | 25.3 kN | 3,637 MPa | **1.33** | 1.25 |
| SLM G shutdown edge moment 10.4 kNm + centrifugal | 10.6 kN | 2,719 MPa | 3.2 | 1.25 |
| SLM E overspeed centrifugal 63.7 kN | 3.3 kN | 1,852 MPa | 10 | 1.25 |
| Simulated envelope 8.5 kNm (γ 1.35) | 9.3 kN | 2,608 MPa | 3.6 | 1.5 |

Static factor here is the load ratio, (4,000 / p)³. Twenty candidate sizes
were checked (pitch diameter 200 to 300 mm, balls 15.9 to 25.4 mm). The
250 mm × 25.4 mm bearing is the smallest one that passes with the blade bolt
circle (190 mm) inside the inner ring.

### 4.2 Life

| Item | Value |
|---|---|
| Pitch travel in 20 years (simulated, V_ave 10 m/s) | **2.0 million bearing revolutions** (≈ 9,000 °/h above rated) |
| Reversals in 20 years | **229 million** |
| Motion-weighted equivalent root moment / centrifugal force | 1.09 kNm / 11.0 kN |
| Equivalent axial load (F + 2.5 M / D_pw) | 21.9 kN |
| Dynamic rating C_a (ISO 281 thrust ball at 45°, × 0.6 for slewing ring practice) | 138 kN |
| **L10** | **247 million revolutions, against 4.0 million required** (2 × life) |

### 4.3 Standstill and small-oscillation wear (the real risk)

Below rated the blade sits at the fine-pitch stop for long periods while the
rotor turns, so the root moment rocks the balls at one spot (false
brinelling). Above rated the controller makes many small reversals. Both
wear out the grease film and mark the raceways long before rolling fatigue
does. Measures:

- Grease for oscillating slewing rings with good fretting resistance and
  −40 °C pumpability (synthetic base oil, lithium-complex or calcium
  sulphonate). The same grease is used on the gear.
- **Lubrication sweep:** after every 24 h at fine pitch, the controller pitches
  the blades 0 → 10° → 0 at low wind (energy loss negligible).
- Automatic single-point lubricator per bearing and gear, 12-month service
  interval, with a purge path.
- Bearing supplier to confirm with an oscillation test (new R3.5) and a
  supplier calculation to NREL DG03 / their own method.

### 4.4 Friction torque

Rolling friction (Rothe Erde-style formula for four-point contact) plus two
lip seals:

| | Warm (μ 0.006) | −30 °C (μ 0.012, stiff seals) |
|---|---|---|
| Emergency feather, SLM G edge moment + centrifugal at 210 rpm | 166 Nm | **347 Nm** |
| Emergency feather, simulated e-stop moment | 73 Nm | 160 Nm |
| Normal pitching, mean / equivalent load | 34 / 37 Nm | 82 / 88 Nm |

### 4.5 Sealing (R3.3)

Double lip seals on both bearing gaps (HNBR, −40 °C rated), plus a moulded
EPDM **boot** between the spinner and the blade root that sheds water, snow
and ash before it reaches the seals. The gear and pinion sit inside the
hub, which is closed and has a desiccant breather.

## 5. Pitch drive

| Torque case at the bearing | Torque |
|---|---|
| **Emergency feather at −30 °C, SLM G moment** (friction + 1.35 × aerodynamic) | 433 Nm |
| Emergency feather at −30 °C, simulated e-stop | 247 Nm |
| Normal pitching, −30 °C, equivalent load (motor thermal) | 91 Nm |
| Acceleration to 30 °/s in 0.2 s (reflected motor inertia) | 77 Nm |
| **Peak (design)** | **510 Nm** |
| Storm holding (1.5 × 294 Nm, friction ignored) | 440 Nm |

| Element | Selection |
|---|---|
| Ring gear / pinion | Module 3, 48 / 14 teeth (1:3.43), face 30 mm, induction hardened; Lewis bending 337 MPa at peak, against 450 MPa |
| Gearbox | Planetary 1:100, low-backlash, low-temperature grease |
| Motor | 48 V PMSM servo, 1,710 rpm at 30 °/s, **2.1 Nm peak** (cold efficiency 0.73), 0.36 Nm continuous, ≈ 0.4 kW. Spring-applied holding brake ≥ 1.3 Nm |
| Drive controller | In the hub, one per axis, with its own safety logic (STO input from the safety chain, fixed feather sequence, watchdog) |
| Energy store | 21 × 2.7 V / 350 F supercaps in series (56.7 V, 16.7 F), active balancing, heater pad. One emergency stroke needs 1.2 kJ, two strokes at end of life 3.1 kJ; the module holds 21 kJ between 56 and 24 V |
| Sensors | Absolute encoder on the blade ring (gear-driven), motor encoder, limit switches at −2° (fine) and 91° (feather), rubber end stops at −3° and 93° |
| Time to feather | 3 s from fine pitch to 90° at 30 °/s; 45° in 1.5 s (R3.1) |

**Power and data to the hub:** a slip ring at the spindle nose (doc 07
cable conduit) carries 48 V DC for the pitch drives, a fieldbus, and the
two-channel safety chain. Blade heating (R2.8) also needs power through the
slip ring; its rating waits for the ice protection design (category 2).

## 6. Hub

| Item | Value |
|---|---|
| Material | EN-GJS-400-18U-LT (Charpy tested at −20 °C, as the bedplate) |
| Shape | Central sphere R 0.22 m, three necks Ø 0.33 m (bearing seat face at r = 0.35 m), front access opening Ø 0.25 m with cover, rear flange to the drum |
| Wall | **10 mm** minimum sound wall for a sand casting of this size. Neck stresses at 10 mm: static 55 MPa against 218 MPa (SLM 26 kNm + 63.7 kN, K_t 1.5); fatigue range 18 MPa against 55 MPa (root moment DEL m = 5 of 3.0 kNm, K_t 2.5, × 2) |
| Mass | Shell 55 kg + pitch flanges 19 kg + rear flange 11 kg + ribs 6 kg = **≈ 90 kg** |
| Hub-to-drum joint | Loads: hub moment 8.6 kNm, shaft torque 28.4 kNm (SLM G), thrust 41.6 kN (SLM H). **12 × M16 10.9** on Ø 400 mm, preload 110 kN, blasted faces μ 0.3: slip capacity 292 kN against 142 kN demand; tension 10.6 kN per bolt |
| Spinner | Glass/vinyl-ester nose cone on the hub front, same material as the nacelle cover, with the blade boots |
| Lightning | Blade down-conductor → bonded strap across the pitch bearing → hub → spark gap or brush to the spindle (doc 07), so lightning current never passes through the pitch or main bearing races |

The hub is lightly stressed, like the spindle in doc 07: its wall is set by
casting practice and by stiffness for the pitch bearing seat (flatness under
the 26 kNm moment, to be checked in the casting FEA).

## 7. Yaw system

> **Update (doc 25):** the yaw brake is now two passive spring-loaded friction
> pad units (3 kNm) and the drives hold with spring-applied motor brakes. The
> hydraulic controlled-slip calipers and R3.7 below are replaced. The bearing
> check is redone at 34.6 kNm with a 1,103 kg tower top. See
> [25 – Yaw system](25-yaw-system.md).

### 7.1 Loads at the yaw bearing

| Case | Tilt moment | Axial | Radial |
|---|---|---|---|
| **SLM H parked thrust 41.6 kN at 0.40 m + SLM shaft moment + rotor overhang** | **24.3 kNm** | 6.7 kN | 41.6 kN |
| Simulated envelope (γ 1.35) | 13.2 kNm | 6.7 kN | 5.8 kN |

Doc 07 had 18.4 kNm. The SLM thrust case now sets the bearing.

### 7.2 Components

| Item | Selection |
|---|---|
| Yaw bearing | Four-point contact ball slewing ring, D_pw 360 mm, 53 × 19 mm balls, external gear (z 150, module 4). Static: 3,217 MPa, factor 1.9 against 1.0 on SLM design loads |
| Friction torque | 103 Nm warm, 231 Nm at −30 °C |
| Operating yaw moment (simulated) | Mean ≤ 14 Nm, 95th percentile 1.6 kNm |
| Drive torque requirement | Friction + residual brake 0.5 kNm + half the 95th percentile ≈ **1.5 kNm**; above that the drives yield and the gust is taken by the brake |
| Yaw drives | 2 × 0.18 kW planetary gearmotors (1:1,680), pinion z 14; not self-locking, so the gear train can't be overloaded by a gust while the inverter limits torque |
| Yaw brake | 2 spring-applied, hydraulically released calipers on a brake ring r 0.24 m, total clamp 42 kN, **slip setting 8 kNm** (≥ doc 07 holding torque and the 7.0 kNm simulated design yaw moment). Controlled pressure gives 0.5 kNm drag while yawing |
| Cable twist | Hanging loop, untwist at ±2.5 turns, switch at ±3 turns (doc 11) |
| Service | Yaw lock pin |

### 7.3 Backup power for parked yawing

Doc 11 keeps the rotor facing the wind while parked in storms, for 72 h on
backup power. Assuming 20 % yaw duty in a storm (120 W) and 54 W base load
(controller, sensors, idle pitch drives, heated vane), that is **5.6 kWh**,
so about **8.4 kWh installed** (48 V LiFePO4, heated, × 1.5 for cold and
ageing). Off-grid systems can share their main battery. For grid-tie
systems this is a large extra. If the dynamic stall check (doc 08, open
item) clears the parked vibration, 24 h is enough (≈ 2.8 kWh installed).

## 8. Effect of the heavier rotor on the rest of the turbine

| Item | Doc 07 / 09 | Now |
|---|---|---|
| Hub and pitch system | 80 kg | **≈ 200 kg** (hub 90, three pitch axes 34 kg each, spinner and slip ring 8) |
| Tower top | 480 kg | **≈ 600 kg** |
| Rotor inertia | 216 kg m² | +7.5 kg m² (+3 %, negligible for control) |
| 18 m tower f1 (rigid / soft soil with ice) | 1.22 / 1.09 Hz | **1.13 / 1.03 Hz**; exclusion zone ≈ 62–75 rpm |
| 24 m tower f1 (rigid / soft soil with ice) | 0.88 / 0.78 Hz | **0.82 / 0.737 Hz**, against a lower limit of 0.734 Hz: **no margin** |
| Gin pole line pull, 18 m / 24 m | 52 / 68 kN | 57 / 73 kN |
| Main bearings and spindle | | +1.2 kN weight, negligible against the 41/44 kN design loads |

Actions:

1. Next tower update: stiffen the 24 m tower (for example a 10 mm top
   section) or raise the minimum operating speed, and move the exclusion
   zone setting in the controller.
2. Next load rerun: tower-top mass 600 kg and the new tower frequencies. The
   fatigue loads change little, because the tower is still in the same
   soft-stiff band.
3. Mass reduction is possible later (a thinner hub with FEA, smaller
   pitch bearing once IEC 61400-2 SLM equations are confirmed), but is not
   a goal now.

## 9. Cold climate (R3.2)

| Item | Measure |
|---|---|
| Grease in pitch and yaw bearings, gears and gearboxes | Synthetic, −40 °C rated; heater pads on pitch gearboxes and supercaps, heated before start below −20 °C (doc 11) |
| Motor sizing | At −30 °C friction (μ 0.012) and gearbox efficiency 0.75 |
| Supercaps | Capacitance falls and resistance rises in cold; 14 strokes at end of life covers this; heater pad keeps them above −25 °C |
| Seals and boots | HNBR / EPDM, −40 °C rated |
| Hub casting | EN-GJS-400-18U-LT, impact tested |
| Test | Climate chamber test of a full pitch axis at −40 °C (R11.3) |

## 10. Requirements updated

- **R3.1** confirmed by sizing: 30 °/s feather at −30 °C against 510 Nm.
- **New R3.5** The pitch bearing and grease shall be qualified for
  oscillating duty: 2 million revolutions and 230 million reversals in 20
  years, long dwells at the fine-pitch stop under rotating root moment.
  The controller shall make a 0 → 10° lubrication sweep after every 24 h at
  fine pitch.
- **New R3.6** Each pitch axis shall feather on loss of the safety chain,
  of slip-ring power, or of its watchdog, using only its own stored energy,
  and shall report its stored energy for the weekly test (doc 11).
- **New R3.7** The yaw brake shall slip above 8 kNm and the yaw drives
  shall not be self-locking, so a side gust cannot overload the gear train
  or the tower top.

## 11. Open points and next steps

1. Supplier enquiry for the pitch and yaw slewing rings (static, life,
   oscillation, grease) and for the pitch servo and gearbox.
2. Hub casting FEA (stiffness of the bearing seats, neck radii), casting
   simulation, then a pattern.
3. Rating of the slip ring once the blade heating power is known.
4. Tower update for the 600 kg tower top (section 8) and a load rerun.
5. Pitch axis prototype test: endurance on an oscillation rig, −40 °C
   start, emergency feather on supercaps.
