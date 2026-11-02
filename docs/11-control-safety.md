# 12 kW Wind Turbine for Iceland: Control and Safety System

Status: **Draft, revision 1** · 2026-11-02
Owner: Category 8 (Control and safety)
Builds on: [08 – Load verification](08-load-verification.md), [09 – Tower](09-tower-foundation.md), [10 – Blade](10-blade-structure.md)
Model: [`analysis/loads/sim.py`](../analysis/loads/sim.py) (controller as simulated), [`run_dlcs.py final`](../analysis/loads/run_dlcs.py)

## Summary

| Item | Design |
|---|---|
| Architecture | **Two independent systems:** a control system (embedded controller) for normal operation, and a hardwired, fail-safe protection system that can stop the turbine without it |
| Below rated | Variable speed, optimal torque Q = k·ω² (k = 2.49 Nm·s², TSR 6.5, Cp 0.48), with a **speed exclusion zone** around the tower 1P crossing (66–80 rpm on the 18 m tower) |
| Above rated | **Constant power** 13.6 kW shaft (12 kW electrical) and gain-scheduled PI pitch control. Mean power is now on target; doc 08's controller ran 8 % high |
| Storm control | Between 25 and 30 m/s (60 s nacelle wind) speed falls to 75 % and power to 40 %; normal stop above 32 m/s (60 s) or 40 m/s (3 s gust); restart below 25 m/s (10 min) |
| Trips | Overspeed 210 rpm (controller) and 225 rpm (independent hardware relay); side-side 1P vibration (imbalance and ice); overall vibration switch; ice detection; cable twist; watchdog; grid and converter faults |
| Emergency stop | Each blade feathers at 30 °/s on its own stored energy; converter brakes at 1.25 × rated torque into the dump load; spring-applied brake after 1 s |
| Safety integrity | Protection system to ISO 13849-1 **PL d, category 3** (two channels with diagnostics) for overspeed and emergency stop |
| Loads with the final design | All 103 load cases rerun with this controller, the 18 m tower and the carbon-cap blade: ultimate loads within ±13 % of doc 08, fatigue up 5–33 %, every component keeps its margin (section 8) |

---

## 1. Architecture

```
            sensors                        CONTROL SYSTEM (embedded, normal operation)
  rotor speed (encoder) ─┐             ┌─ torque setpoint ──► converter (common front end, doc 02 R7.1)
  pitch angles (3) ──────┤             ├─ pitch setpoints ──► 3 independent pitch drives
  nacelle wind, vane ────┼──► controller ─ yaw commands ────► 2 yaw motors, yaw brake
  2-axis accelerometer ──┤             ├─ heating ─────────► blade heating, generator heaters
  temperatures, power ───┘             └─ status, logs ────► remote monitoring

                                       PROTECTION SYSTEM (hardwired, fail-safe, independent)
  overspeed relay (own sensor on drum teeth) ─┐
  vibration switch (pendulum) ────────────────┤
  e-stop buttons (tower base, nacelle) ───────┼─► safety chain (2 channels) ─► opens: pitch hold power (all 3)
  controller watchdog ────────────────────────┤                              brake release valve
  cable twist limit switch ───────────────────┤                              converter enable
  pitch drive fault / stored-energy low ──────┘
```

- **Fail-safe:** loss of power, a broken wire or a tripped relay leads to
  the safe state. Each pitch drive feathers its blade from its own stored
  energy (supercapacitors or spring), the brake springs apply, and the
  converter switches to dump-load braking.
- **Independence:** the protection system has its own speed sensor and
  logic, so a controller fault cannot disable it. Any single pitch drive
  failure still leaves two blades feathering, which stops the rotor (doc 07).
- **Safety integrity:** the overspeed and emergency stop functions are
  designed to ISO 13849-1 PL d, category 3, which IEC 61400-2 accepts for a
  protection system. Detailed safety analysis (FMEA, PL calculation) is a
  next step.

## 2. Operating states

```
  PARKED ──(wind 60 s > 3 m/s, no faults)──► STARTING ──(rotor > 40 rpm)──► RUNNING
    ▲                                                                       │
    │◄──────── NORMAL STOP (pitch 8 °/s, then brake < 5 rpm) ◄──────────────┤ low wind, storm cut-out,
    │                                                                       │ ice, faults (non-safety)
    │◄──────── EMERGENCY STOP (30 °/s, converter braking, brake) ◄──────────┘ any protection-system trip
  IDLE (feathered, brake off, slow rotation) for high winds with backup power, see 5.3
```

| State | Entry | Action |
|---|---|---|
| Parked | Stop completed, or manual | Blades feathered, brake on, yaw active on backup power (5.3), heaters as needed |
| Starting | 60 s mean wind > 3 m/s for 2 min, all checks passed | Pitch from 90° to fine at 2 °/s, generator connects at 40 rpm |
| Running | Rotor above 40 rpm | Regions 2, 2.5, 3 and storm control (section 3) |
| Normal stop | Wind < 2.5 m/s (10 min), storm cut-out, ice, non-safety fault | Pitch to feather at 8 °/s, generator torque holds speed down, brake below 5 rpm |
| Emergency stop | Any protection-system trip | Section 4 |

## 3. Power and speed control

| Region | Rotor speed | Generator torque | Pitch |
|---|---|---|---|
| 2 (below rated) | 40 rpm to 0.95 × rated | k·ω², k = 2.49 Nm·s² | Fine pitch (0°, −0.5° limit) |
| Exclusion zone | 60·f_tower ± 10 % | Holds the lower edge; crosses with 0.25 × or 2 × the edge torque (3.1) | Fine |
| 2.5 (transition) | 0.95 to 1.0 × rated (169–178 rpm) | Linear ramp to rated torque | Fine |
| 3 (above rated) | 178 rpm | **Constant power**: Q = P_ref / ω, plus 400 Nm per rad/s above 1.05 × reference speed | PI on speed error, gain scheduled |
| Storm (25–30 m/s) | 178 → 134 rpm | Q = P_ref / ω with P_ref 13.6 → 5.4 kW | PI on the reduced speed reference |

**Pitch loop:** PI on rotor speed error, designed for a 3.0 rad/s natural
frequency and 0.7 damping (4.0 rad/s was unstable in simulation). Gains at
the first scheduling point (5.7° pitch): K_p = 15.1° per rad/s,
K_i = 32.4° per rad. The schedule divides both by the pitch sensitivity
ratio: 1.0 at 5.7°, 0.46 at 12.3°, 0.30 at 18.4°, 0.20 at 25.8°
(interpolated from steady BEM, doc 08). Normal pitch rate limit 15 °/s.

**Constant power** removes the 8 % power overshoot of doc 08: in simulation,
mean shaft power at 16 and 22 m/s is 13.6–13.7 kW (target 13.6), against
14.6–14.9 kW before.

### 3.1 Speed exclusion zone

The tower first frequency lies inside the 1P band (doc 09), so the rotor
must not run at 60·f_tower ± 10 %. The controller:

1. In the lower state, follows k·ω² up to the zone's lower edge, then holds
   that speed with a steep torque ramp up to the torque of the upper edge.
2. When the wind can drive the rotor through, it **unloads the generator to
   25 % of the lower-edge torque** until the rotor reaches the upper edge.
3. Going down, it holds the upper edge, then applies **twice the upper-edge
   torque** until the rotor reaches the lower edge.
4. If the wind changes during a crossing, it falls back to the side it came
   from.

Simulated time inside the zone: 5.6 % at 4 m/s, 2.8 % at 6 m/s, 0 above;
no measurable energy loss (doc 09).

**Commissioning:** the tower frequency is measured from a brake-stop ring-down
with the nacelle accelerometer. The controller sets the zone from it and
then tracks the frequency from ambient vibration. If it drifts more than 3 %
(ice, foundation), the zone moves with it and an alarm is raised.

### 3.2 Storm control and cut-out

Instead of a hard cut-out at 25 m/s, the turbine reduces speed and power
between 25 and 30 m/s on the 60 s mean nacelle wind (Icelandic storms are
long; producing through them is valuable, doc 03). In simulation at 27 and
30 m/s, power was 9.8 and 5.8 kW and peak speed 187 and 179 rpm, lower than
at 22 m/s. Normal stop above 32 m/s (60 s) or 40 m/s (3 s gust); restart
once the 10 min mean is below 25 m/s.

## 4. Protection functions

| Function | Sensor | Threshold | Action |
|---|---|---|---|
| Overspeed (controller) | Rotor encoder | 210 rpm (118 %) | Emergency stop |
| **Overspeed (hardware)** | Independent inductive sensor on drum teeth, safety relay | 225 rpm (126 %) | Safety chain opens; design overspeed 250 rpm (doc 08) |
| Side-side 1P vibration (imbalance, ice) | Nacelle accelerometer, 1P amplitude | Equivalent of 0.5 kg·m imbalance, e.g. 0.27 m/s² at 178 rpm (speed-dependent table) | Normal stop, ice check, alarm |
| Overall vibration | Pendulum vibration switch | 0.3 g | Safety chain opens |
| Ice on blades | Power curve deficit + 1P imbalance + temperature/humidity | Power < 75 % of expected for 10 min at < +3 °C, or imbalance trip | Normal stop, blade heating cycle, restart after confirmation |
| Cable twist | Yaw encoder + limit switch | ±2.5 turns (controller untwist), ±3 turns (switch) | Untwist at low wind; switch opens safety chain |
| Pitch system | Pitch drive self-check, stored energy level | Any drive fault or low energy | Emergency stop |
| Grid or converter fault | Converter | Loss of grid, overvoltage, converter fault | Dump load takes the power (R7.3), normal stop; emergency stop if torque is lost |
| Generator overtemperature | Winding sensors | Class B rise limit | Derate, then normal stop (doc 05/06) |
| Watchdog | Controller heartbeat | 0.5 s | Safety chain opens |

**Emergency stop sequence:** pitch drives feather all blades at 30 °/s from
stored energy; the converter brakes at 1.25 × rated torque into the dump
load while it is available; the spring-applied brake engages after 1 s and
holds the rotor (8.7 kNm, doc 07). Loss of generator torque (DLC 2.2) leaves
the pitch system alone to stop the rotor, which it does below 193 rpm (doc 08).

**Periodic tests (automatic):** pitch run on stored energy weekly at low
wind; brake torque test with generator torque weekly; overspeed relay test
at commissioning and yearly service.

## 5. Yaw and parked behaviour

### 5.1 Yaw control

- Nacelle wind vane (heated, ultrasonic preferred for ice).
- Yaw when the 60 s mean error exceeds 8°, or the 10 s mean exceeds 20°;
  yaw rate 0.5 °/s; yaw brake applied when stationary.
- Cable untwist at low wind after ±2.5 turns.

### 5.2 Grid loss

The dump load absorbs the power while the turbine performs a normal stop.
The controller, pitch drives and yaw run from a backup battery.

### 5.3 Parked in storms

Doc 08 found a possible stall-induced vibration of a parked rotor at about
30° yaw error. Until a dynamic stall model clears it, the parked strategy is:

- **Keep yawing to the wind while parked**, on backup power (battery sized
  for 72 h of storm yawing), holding the yaw error under 15°.
- If backup power runs out, release the brake and let the feathered rotor
  idle slowly, which adds aerodynamic damping; the controlled-slip yaw brake
  lets the nacelle weathervane.

## 6. Cold climate functions

- Blade heating (R2.8) runs when the temperature is below +3 °C with
  humidity above 90 %, or after an ice detection; powered from the turbine
  while running and from the grid or battery when parked.
- Generator anti-condensation heating when parked (R4.4), by DC injection
  through the converter.
- Pitch and yaw gear lubricant pre-heating below −20 °C before start.

## 7. Requirements updated

- R3.1: emergency pitch 30 °/s, normal 15 °/s (doc 08, unchanged).
- R6.2 and R6.6: exclusion zone, tower frequency measurement, vibration trip
  (doc 09, implemented here).
- R8.x (control): constant power above rated; storm control 25–30 m/s with
  stop above 32 m/s (60 s) or 40 m/s (3 s); protection system to PL d,
  category 3; hardware overspeed relay at 225 rpm.

## 8. Loads with the final design

All design load cases were rerun with this controller, the 18 m tower
(1.21 Hz, doc 09), the carbon-cap blade (13.2 Hz, 20.5 kg, doc 10), ±0.3°
pitch misalignment, and nine extra normal-turbulence runs at 26, 28 and
30 m/s for storm control (103 runs; `run_dlcs.py final`, results in
[`analysis/loads/results/final/`](../analysis/loads/results/final/)).

| Channel (characteristic) | Doc 08 | Final | Change | Governing case (final) |
|---|---|---|---|---|
| Rotor thrust | 4.91 kN | 4.28 kN | −13 % | 1.3 extreme turbulence, 18 m/s |
| Blade root flap | 4.87 kNm | 5.17 kNm | +6 % | 7.1 parked, blade stuck at fine pitch |
| Blade root resultant | 6.31 kNm | 6.30 kNm | 0 % | 6.x parked, yaw 90° |
| Hub tilt moment | 6.06 kNm | 6.38 kNm | +5 % | 7.1 |
| Hub yaw moment | 5.49 kNm | 5.21 kNm | −5 % | 7.1 |
| Tower base (no tower drag) | 74.2 kNm | 83.7 kNm | +13 % | 1.3, 18 m/s |
| Rotor speed | 231 rpm | 232 rpm | 0 % | 1.3 (design overspeed 250 rpm holds) |
| Ice imbalance | 8.84 kN | 9.05 kN | +2 % | 1.5 |

| Damage-equivalent load (10⁷ cycles) | Doc 08 | Final | Change |
|---|---|---|---|
| Blade flap (m = 10) | 3.19 kNm | 3.40 kNm | +7 % |
| Blade edge (m = 10) | 1.22 kNm | 1.28 kNm | +5 % |
| Rotor thrust (m = 4) | 2.83 kN | 3.19 kN | +13 % |
| Hub tilt (m = 4) | 5.87 kNm | 6.85 kNm | +17 % |
| Hub yaw (m = 4) | 5.88 kNm | 6.81 kNm | +16 % |
| Tower base (m = 4) | 51.1 kNm | 67.8 kNm | +33 % |
| Shaft torque (m = 4) | 1.77 kNm | 1.94 kNm | +10 % |

Mean shaft power by wind speed: 13.5–13.7 kW from 14 to 24 m/s (target
13.6 kW), then 11.9, 8.7 and 6.1 kW at 26, 28 and 30 m/s. Emergency stops
still happen only in extreme turbulence (DLC 1.3), as intended.

**What the changes mean:**
- The fatigue increases come mostly from operating through 26–30 m/s storms
  (not in doc 08) and from the pitch misalignment, plus the softer tower for
  the base moment. All stay within margin: blade fatigue utilisation goes
  from 0.20 to about 0.22 (doc 10); hub and bearing loads remain far below
  bearing ratings (doc 07); tower fatigue damage rises from 0.22 to an
  estimated 0.30 on the 18 m tower (doc 09, damage scales with roughly the
  fourth power of the base DEL ratio 67.8/63).
- Ultimate loads change by −13 % to +13 %. The parked storm still sizes the
  tower and the SLM still sizes the blade, so no component changes size.

**Simulator fix:** the stiffer carbon blade made the explicit blade–tower
coupling in the doc 08 simulator unstable once the rotor stopped. The blade
flap and tower accelerations are now solved together each time step. The
doc 08 baseline case at 14 m/s reproduces within 1.3 %, and the parked
case converges (0.01 s and 0.005 s time steps agree within 2 %).

## 9. Limitations and next steps

- The simulator models fore-aft tower motion only, no yaw dynamics, and no
  converter or grid dynamics. Side-side vibration and the vibration trip
  thresholds come from analysis (doc 09) and must be tuned on the prototype.
- Startup and normal stop sequences are specified but not yet simulated.
- Next steps:
  1. Safety analysis: FMEA of the protection system and a PL calculation.
  2. Power electronics design (category 7): front end, dump load, grid-tie
     and battery modules.
  3. Controller hardware selection and a hardware-in-the-loop test bench
     driven by this simulator.
