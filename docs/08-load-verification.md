# 12 kW Wind Turbine for Iceland: Load Verification

Status: **Draft, revision 1** · 2026-11-01
Owner: Category 2 (Loads and certification), with Category 8 (Control)
Builds on: [02 – Design basis](02-design-basis.md), [03 – Rotor](03-rotor-concept.md), [07 – Nacelle](07-nacelle-spindle-bearings.md)
Models: [`analysis/loads/`](../analysis/loads/)

## Summary

The concept loads from doc 07 were checked two independent ways: with the
IEC 61400-2 Simplified Load Model (SLM) and with an in-house time-domain
aeroelastic simulator running 94 design load cases.

| Question | Answer |
|---|---|
| Do the doc 07 concept loads hold? | **Mostly.** Parked holding torque (5.8 kNm), ice imbalance (12 kN) and parked blade root moment match. The worst hub moment is 27 % higher (8.2 against 6.4 kNm design) and operating thrust about twice the concept value (6.6 against 3.2 kN design) |
| Do nacelle, spindle, bearings and brake pass? | **Yes, with large margin**, under both the simulated loads and the SLM loads (section 5) |
| How do SLM and simulation compare? | Characteristic (unfactored) loads agree within 1.0 to 1.7 ×. The SLM design values are 2 to 6 × higher, mostly because the SLM safety factor is 3.0 against 1.35 |
| What load set should the blades and hub be designed to? | **The envelope of both, so in practice the SLM values (blade root 26 kNm design).** It is certifiable without a validated aeroelastic model, and cost is not the priority |
| What changed in the design basis? | **Design overspeed 230 → 250 rpm**; pitch rate 15 °/s normal and **30 °/s emergency**; converter braking at 1.25 × rated torque on an emergency stop |
| New risks found | Stall-induced vibration of a parked rotor at about 30° yaw error; no frequency gap between 1P and 3P for the tower; power overshoot above rated (controller tuning) |

---

## 1. IEC 61400-2 Simplified Load Model

### 1.1 Method and caveat

The SLM gives closed-form loads for small turbines from a few turbine
parameters (design speed, torque, tip speed ratio, blade mass and area,
V_ave, V_e50). The model in `slm.py` uses equations **reconstructed from NREL
reports** (NREL/TP-5000-83708, NREL/CP-500-33004) and general knowledge of
the standard. **Before certification work, buy IEC 61400-2:2013 and check
every equation.** Load case C (free-yaw tail vane) does not apply to an
actively yawed turbine and is skipped.

Inputs: blade mass 20 kg, blade centre of gravity 1.55 m, projected blade
area 0.85 m², rotor mass 200 kg, design torque 730 Nm at 178 rpm, tip speed
ratio 6.66, maximum speed 250 rpm, V_ave 10 m/s, V_e50 77 m/s.

### 1.2 Results

| SLM case | Load | Characteristic | Design (γ = 3.0) |
|---|---|---|---|
| A Normal operation (fatigue) | Blade flap range ΔM_yB | 1.62 kNm | (fatigue) |
| | Blade edge range ΔM_xB | 0.85 kNm | |
| | Shaft thrust range ΔF_x | 1.94 kN | |
| | Shaft bending range ΔM_shaft | 1.69 kNm | |
| | Cycles in 20 years | 1.87 × 10⁹ | |
| B Yaw error | Blade flap M_yB / shaft bending | 1.03 / 1.78 kNm | 3.10 / 5.35 kNm |
| D Maximum thrust | Shaft thrust F_x | 8.46 kN | 25.4 kN |
| E Maximum speed (250 rpm) | Blade root centrifugal F_zB | 21.3 kN | 63.7 kN |
| F Short circuit | Shaft torque | 1.46 kNm | 4.38 kNm |
| G Shutdown (brake) | Shaft torque / blade edge | 9.46 / 3.46 kNm | 28.4 / 10.4 kNm |
| H Parked at V_e50 | Blade flap M_yB / shaft thrust | 8.67 kNm / 13.9 kN | **26.0 kNm / 41.6 kN** |

---

## 2. Aeroelastic simulator

### 2.1 What it models

No suitable OpenFAST or QBlade model was available in this environment, so
a dedicated simulator was written (`sim.py`, about 500 lines of numpy):

| Part | Model |
|---|---|
| Wind | Kaimal turbulence with IEC exponential coherence on a 9 × 9 grid over the rotor (Veers method), power-law shear α = 0.2. NTM, ETM and EOG from the design basis (Class S, I15 = 0.20, a = 2) |
| Aerodynamics | Unsteady BEM per blade element (16 per blade): Prandtl tip and hub loss, Buhl high-induction correction, first-order dynamic inflow, yaw by wind projection. Polars from `bem.py` with Viterna post-stall and a consistent flat-plate model beyond ±90° |
| Structure | First flap mode of each blade (6 Hz at standstill, Southwell stiffening), tower first fore-aft mode (1.8 Hz, assumed), rigid drivetrain with J = 216 kg m² |
| Control | Torque k·ω² below rated plus a speed-error term above rated; gain-scheduled PI pitch control (dQ/dθ interpolated from BEM); pitch actuator 15 °/s normal, 30 °/s emergency; overspeed trip at 210 rpm; emergency stop with converter braking (1.25 × rated torque) and the mechanical brake after 1 s |
| Faults | Loss of generator torque, pitch runaway of one blade, one blade stuck, ice mass on one blade |
| Post-processing | Ultimate envelope with governing case; rainflow counting, Miner sums and lifetime damage-equivalent loads (DEL) at 10⁷ cycles over a Rayleigh V_ave = 10 m/s distribution (m = 10 for the composite blade, m = 4 for steel) |

### 2.2 Load cases (94 runs)

| DLC | Description | Runs |
|---|---|---|
| 1.1 / 1.2 | Power production in normal turbulence, 4 to 24 m/s in 2 m/s steps, 3 seeds × 600 s | 33 |
| 1.3 | Extreme turbulence at 10.5, 14, 18 and 24 m/s, 2 seeds | 8 |
| 1.4 | Extreme operating gust at 8.5, 12.5 and 25 m/s | 3 |
| 1.5 | Operation with 15.1 kg of ice on one blade (IEC cold climate) at 8 and 12 m/s | 2 |
| 2.1 | Pitch runaway of one blade, then emergency stop, at 12, 18 and 24 m/s | 3 |
| 2.2 | Loss of generator torque, at the EOG peak and in turbulence | 4 |
| 2.3 | Emergency stop with one blade stuck | 2 |
| 5.1 | Emergency stop at 10.5, 18 and 25 m/s | 3 |
| 6.1 / 6.2 | Parked, V_ref = 55 m/s, σ = 0.11 V, ρ = 1.35 kg/m³; azimuth 0/30/60/90°, yaw error 0/8/30/60/90/135/180° | 28 |
| 7.1 | Parked with one blade stuck at fine pitch, 44 m/s, 8 yaw/azimuth combinations | 8 |

### 2.3 Ultimate loads (γ = 1.35)

| Channel | Characteristic | Design | Governing case |
|---|---|---|---|
| Rotor thrust | 4.91 kN | 6.63 kN | 1.3 extreme turbulence, 18 m/s |
| Blade root flap moment | 4.87 kNm | 6.58 kNm | 7.1 stuck blade, parked |
| Blade root in-plane moment¹ | 6.29 kNm | 8.49 kNm | 6.x parked, yaw 90° |
| Blade root resultant | 6.31 kNm | 8.52 kNm | 6.x parked, yaw 90° |
| Hub tilt moment | 6.06 kNm | 8.18 kNm | 7.1 stuck blade, parked |
| Hub yaw moment | 5.49 kNm | 7.41 kNm | 2.1 pitch runaway, 12 m/s |
| Tower base moment² | 74.2 kNm | 100 kNm | 1.1 normal turbulence, 8 m/s |
| Aerodynamic shaft torque (parked) | 5.78 kNm | 7.80 kNm | 6.x parked, yaw 30° |
| Rotor speed | 231 rpm | (250 rpm design) | 1.3 extreme turbulence, 18 m/s |
| Ice imbalance force | 8.84 kN | 11.9 kN | 1.5 ice, 12 m/s |

¹ For a feathered parked blade the in-plane direction is the blade's
structural flapwise (weak) axis. The parked side-wind case therefore loads the
blade root in its weak direction.
² Tower drag and tower shadow are not modelled; the tower stiffness and mass
are assumptions.

### 2.4 Fatigue (lifetime DEL at 10⁷ cycles)

| Channel | m | DEL |
|---|---|---|
| Blade root flap | 10 | 3.19 kNm |
| Blade root edge | 10 | 1.22 kNm |
| Rotor thrust | 4 | 2.83 kN |
| Hub tilt moment | 4 | 5.87 kNm |
| Hub yaw moment | 4 | 5.88 kNm |
| Tower base moment | 4 | 51.1 kNm |
| Shaft torque | 4 | 1.77 kNm |

Example time series: [normal turbulence at 14 m/s](../analysis/loads/results/dlc_ntm14.png),
[emergency stop at 25 m/s](../analysis/loads/results/dlc_estop25.png),
[loss of generator torque at the 25 m/s gust peak](../analysis/loads/results/dlc_losstorque25.png).

### 2.5 Limitations

- No edgewise or torsional blade modes, no tower side-side mode, rigid
  drivetrain. Edgewise loads are therefore gravity plus aerodynamic only.
- Only the longitudinal turbulence component.
- Quasi-steady aerofoil data: **no dynamic stall model**. Parked cases at
  high angle of attack are the least reliable (see 4.3).
- Generic placeholder polars, assumed blade mass (20 kg) and stiffness, and
  assumed tower properties.
- **Not validated.** Before final loads, the same turbine must be run in
  OpenFAST (independent code) and checked against measurements on the
  prototype (IEC 61400-13 load measurements).

---

## 3. Three-way comparison

| Load | Doc 07 concept (design) | Simulation (design, γ 1.35) | SLM (design, γ 3.0) | SLM characteristic vs simulation characteristic |
|---|---|---|---|---|
| Hub moment, worst case | 6.4 kNm (U2) | 8.2 kNm | 5.4 kNm (case B)³ | — |
| Parked holding torque (characteristic) | 5.8 kNm | 5.8 kNm | 1.5 to 9.5 kNm (F, G)⁴ | — |
| Blade root, parked | 7.0 kNm | 8.5 kNm | **26.0 kNm** | 8.67 vs 6.29 kNm (1.4 ×) |
| Rotor thrust, operating | 3.2 kN | 6.6 kN | 25.4 kN | 8.46 vs 4.91 kN (1.7 ×) |
| Rotor thrust, parked | 3.5 kN | 4.7 kN | 41.6 kN | 13.9 vs 3.5 kN (4 ×)⁵ |
| Ice imbalance | 12 kN | 11.9 kN | (not in SLM) | — |

³ The SLM has no stuck-blade case. ⁴ The SLM shutdown case G is the full
brake torque plus design torque. ⁵ The SLM assumes all three blades
broadside to the wind, which a feathered rotor never is.

| Fatigue (DEL at 10⁷) | SLM case A, converted⁷ | Simulation |
|---|---|---|
| Blade flap | 2.74 kNm | 3.19 kNm |
| Blade edge | 1.44 kNm | 1.22 kNm |
| Shaft bending / hub tilt | 6.25 kNm | 5.87 kNm |
| Rotor thrust | 7.2 kN | 2.83 kN |

⁷ Constant-range SLM spectrum at 1.87 × 10⁹ cycles converted to 10⁷ cycles
with the same m.

**Reading the comparison.** The simulation confirms the storm, brake and
ice loads of doc 07. It raises the hub moment by 27 % and the operating
thrust by a factor of two, because turbulence and control dynamics add to the
steady values that doc 07 scaled by 1.5. Both stay far inside the nacelle
margins (section 5). The
SLM characteristic loads are physically similar to the simulation; most of the
difference in design values is the safety factor (3.0 for the SLM, which
covers its simplicity, against 1.35 for a full simulation). Fatigue agrees
well except thrust, where the SLM is conservative.

---

## 4. Findings and design changes

### 4.1 Design overspeed raised to 250 rpm

Extreme turbulence (DLC 1.3) at 14 to 24 m/s pushed the rotor to 231 rpm
before the emergency stop took over, with 30 °/s emergency pitch and
converter braking. That is above the previous 230 rpm design overspeed. The
design overspeed is now **250 rpm** (140 % of rated), which keeps an 8 %
margin over the worst simulated peak. Consequences:

| Item | Effect |
|---|---|
| Generator worst-case voltage (cold magnets) | 821 V × 250/230 ≈ **890 V peak**, still below the 1000 V limit; 1200 V class power devices remain correct |
| Generator rotor retention test | 1.5 × 250 = 375 rpm |
| Brake kinetic energy | 63 → 74 kJ |
| Blade centrifugal load | Included in SLM case E (63.7 kN design at the root) |

### 4.2 Pitch rates and emergency stop

- Normal pitch rate **15 °/s**: lower rates gave overspeed trips in normal
  turbulence (DLC 1.1).
- Emergency pitch rate **30 °/s** (45° in 1.5 s): design basis R3.1 is
  tightened accordingly.
- On an emergency stop the converter applies **1.25 × rated torque** as
  electrical braking while the blades feather. The mechanical brake engages
  after 1 s. Without the converter (loss of torque, DLC 2.2) the pitch system
  alone holds the rotor below 193 rpm.
- Pitch runaway of one blade (DLC 2.1) sets the worst hub yaw moment
  (7.4 kNm design) but does not overspeed the rotor.

### 4.3 Parked rotor at about 30° yaw error: stall-induced vibration risk

In the first run, a parked rotor at 30° yaw error grew unstable vibrations
(loads above 500 kN). Part of this was a polar error (fixed in `bem.py`, see
4.7), but part is physical: on a feathered blade at that yaw angle the
local angle of attack sits in negative stall, where the lift slope is
negative and aerodynamic damping can become negative. The simulator now
excludes structural velocities from the parked inflow, so the reported
parked loads are quasi-static. **This risk is not closed.** Actions:

1. Add a dynamic stall model (Beddoes-Leishman or Øye) and an edgewise mode,
   and rerun DLC 6.x; then check with OpenFAST.
2. Mitigation options to keep in the design: battery-backed yaw so the
   nacelle tracks the wind during grid loss (also required by R3.4), or let
   the rotor idle slowly instead of parking with the brake.

### 4.4 Tower frequency placement

The rotor runs from 40 to 178 rpm, so 1P spans 0.67 to 2.97 Hz and 3P spans
2.0 to 8.9 Hz. **The two bands overlap, so there is no "stiff-soft" window
for the tower.** The assumed 1.8 Hz tower lies inside 1P, and the largest
tower base moment (74 kNm characteristic) comes from normal operation at
8 m/s. Options for the tower study (category 6): a very stiff tower above
about 9.8 Hz, a soft tower below about 0.6 Hz, or a resonance-avoidance
speed band in the controller (common on small variable-speed turbines).
This is the main input to the tower design.

### 4.5 Power above rated (controller tuning)

Mean shaft power above rated is about 14.8 kW against the 13.6 kW target
(8 % high), because the torque law keeps rising with speed above rated.
Constant-power torque control above rated will fix it. This is a control
tuning item (category 8); it does not change the loads materially.

### 4.6 Ice

Operation with 15 kg of ice on one blade gives an 8.8 kN (characteristic)
rotating imbalance, confirming the doc 07 estimate. Ice detection with
automatic stop stays a safety function (R8.3).

### 4.7 Rotor model correction

The aerofoil polars in `analysis/rotor/bem.py` now use a consistent flat-plate
model beyond ±90° and a smooth negative-stall blend from −10° to −20°.
Normal operation does not reach these angles, so the rotor study (doc 03) is
unchanged; the study was rerun to confirm this.

---

## 5. Design load recommendation

| Component | Design to | Status |
|---|---|---|
| Blades and blade root | **Envelope of SLM and simulation**: flap/in-plane root moment 26 kNm, centrifugal 63.7 kN, plus a full-scale static test (IEC 61400-23) | To do (blade structural study) |
| Hub and pitch bearings | Same envelope (3 × 26 kNm blade root moments) | To do |
| Spindle and main bearings | Simulated hub moment scales doc 07 by 1.27: spindle moment ≈ 9.8 kNm, reserve factor on yield ≈ 13; bearing static loads ≈ 41/44 kN (C0 ≥ 90 kN). SLM shaft bending (5.4 kNm) is lower, and its 41.6 kN parked thrust is a small axial load for 140 mm tapered roller bearings. The hub tilt DEL implies a bearing equivalent load about 2 to 3 × the doc 07 assumption, a case doc 07 already showed has large margin | ✅ |
| Brake disc and drum | SLM case G: 28.4 kNm design shaft torque | Check in detail design |
| Tower | Simulation loads plus frequency placement (4.4); add tower drag | To do (tower study) |
| Fatigue | Simulation DELs (2.4); SLM case A as a cross-check | ✅ |

The SLM route allows certification under IEC 61400-2 without a validated
aeroelastic model. Since cost is deferred, designing blades and hub to the
SLM envelope is the low-risk choice. Once OpenFAST and prototype
measurements validate the simulator, the blade and hub can be lightened in
the cost optimisation phase.

---

## 6. Next steps

1. Buy IEC 61400-2:2013 and check the SLM equations in `slm.py`.
2. Blade structural layup study for the SLM envelope: confirm blade mass
   (20 kg assumed), flap frequency (6 Hz assumed) and root design.
3. Tower study with the frequency placement options in 4.4.
4. Dynamic stall and edgewise mode in the simulator, then the parked
   stability check (4.3).
5. OpenFAST model of the same turbine as an independent check.
