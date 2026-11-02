# 12 kW Wind Turbine for Iceland: Power Electronics and Power Modules

Status: **Draft, revision 1** · 2026-11-02
Owner: Category 7 (Power electronics and power modules)
Builds on: [02 – Design basis](02-design-basis.md) (R7.1–R7.6), [06 – Generator](06-generator-round2.md), [11 – Control and safety](11-control-safety.md)
Model: [`analysis/power/sizing.py`](../analysis/power/sizing.py)

## Summary

| Item | Recommendation |
|---|---|
| Architecture | **Common front end + three plug-in modules** (R7.1): active rectifier and 750 V DC link with a dump load; an **AC module** that works grid-tie or feeds heaters; an isolated **48 V battery module** |
| Front end | Three-phase active rectifier with **1200 V SiC MOSFETs**, 16 kHz, field-oriented torque control; film DC link capacitors (no electrolytics, for −40 °C and life) |
| DC link | **750 V** nominal; dump load chopper from 820 V, hardware-triggered and independent of the controller |
| Dump load | **20 kW continuous**, 33 Ω, so it never limits a stop; a stop needs about 80 kJ |
| AC module | 12 kW, 3-phase 400 V (1-phase 230 V variant). Grid-tie to EN 50549-1, or grid-forming into resistive heaters (heating use case) using the same hardware |
| Battery module | 12 kW isolated DC/DC (dual active bridge), 750 V ↔ 48 V, up to 250 A, four interleaved 3 kW cells |
| Efficiency (estimate) | Rectifier 98.8 %, AC module 98.5 %, together **97.3 %** (R7.5 asks ≥ 95 %); 12.4 kW net at rated |
| Location | All converters in a heated, ventilated **cabinet at the tower base**; generator cable down the tower with a **dv/dt filter** at the rectifier |
| Annual energy (net, Rayleigh) | 20.8 MWh at V_ave 5 m/s, 42.3 MWh at 7 m/s, 65.6 MWh at 10 m/s |

---

## 1. Generator electrical envelope

From docs 05/06: 40 poles, synchronous inductance 13.95 mH, phase resistance
0.31 Ω (75 °C), line EMF 379 V rms at 178 rpm with hot magnets.

| Operating point | Speed | Frequency | Line EMF | Current | Terminal line peak | DC link needed |
|---|---|---|---|---|---|---|
| Minimum speed (optimal torque) | 40 rpm | 13 Hz | 85 V | 1.2 A | 120 V | 131 V |
| Rated, 13.6 kW | 178 rpm | 59 Hz | 379 V | 20.7 A | 583 V | **642 V** |
| Emergency braking, 1.25 × torque at the peak overspeed seen in simulation | 232 rpm | 77 Hz | 493 V | 25.9 A | 802 V | 882 V with i_d = 0; **≤ 810 V with i_d = −5 A** |
| Open circuit, cold magnets, design overspeed | 250 rpm | 83 Hz | — | 0 | **892 V** | (diodes rectify) |

([Voltage envelope and power curve](../analysis/power/results/power_envelope.png))

Two consequences:
- **Emergency braking needs light field weakening.** At 232 rpm the
  terminal voltage with full braking torque exceeds the 820 V dump-load
  threshold. A d-axis current of about −5 A (total current 26.4 A) brings it
  below 810 V. The rectifier control includes this from the start.
- **Uncontrolled rectification.** If the rectifier stops switching while the
  rotor turns, its diodes rectify the EMF into the DC link: up to 892 V at
  the design overspeed with cold magnets. The dump load chopper must
  therefore work without the controller and without the grid (section 3),
  and all DC parts are rated for at least 1000 V. 1200 V devices keep 26 %
  margin at this worst case, as doc 06 required.

## 2. Front end (R7.1)

| Item | Choice | Reason |
|---|---|---|
| Rectifier | 3-phase 2-level active rectifier, field-oriented control | Precise torque control for the controller (doc 11), sinusoidal currents (lower generator losses and torque ripple), field weakening for emergency braking |
| Devices | 1200 V SiC MOSFET six-pack, ≥ 60 A | Low losses at 16 kHz, good at −40 °C; 2 × margin over the 26 A peak current |
| Alternative rejected | Diode bridge + boost converter | Cheaper, but non-sinusoidal currents (heating, torque ripple at 6× electrical frequency) and no field weakening |
| DC link | 750 V nominal, film capacitors rated 1100 V DC | Above the 642 V the generator needs at rated and the 684 V a 400 V grid inverter needs; film capacitors work at −40 °C and last 20+ years |
| Generator cable | 4 × 6 mm² + PE, 0.6/1 kV, screened, drip loop for yaw (untwist at ±2.5 turns, doc 11) | 26 A max; screened for EMC (R7.6) |
| dv/dt filter | At the rectifier terminals, limiting rise to about 1 kV/µs | SiC switching edges on a 20–25 m cable can double the voltage at the winding (up to about 1.5 kV); the filter keeps the winding below 1.2 kV. Winding insulation qualified to IEC 60034-18-41 for converter-fed machines |
| Surge protection | Type 1+2 SPDs on the generator cable and the grid side at the tower base | LPL I (doc 02) |

## 3. Dump load (R7.3)

| Item | Value |
|---|---|
| Rating | **20 kW continuous** (1.5 × rated shaft power) |
| Resistor | 33 Ω at 820 V, air-cooled, in a separate vented enclosure at the tower base |
| Energy per emergency stop | ≈ 76 kJ (rotor kinetic energy at 232 rpm plus aerodynamic power while feathering) |
| Energy per normal stop on grid loss | ≈ 78 kJ |
| Control | Chopper turns on at 820 V DC by a **hardware comparator powered from the DC link itself**; the controller can also command it. Works with no grid, no controller and no auxiliary supply |

Rating it for continuous full power is a quality choice: if the pitch
system were slow or the grid stayed away, the dump load would never be the
part that limits the stop. The same resistor bank also serves as the
controller's "spare load" while switching between output modules.

## 4. Output modules (R7.2)

### 4.1 AC module: grid-tie or heating

One hardware design, two operating modes:

| Mode | Use | Behaviour |
|---|---|---|
| **Grid-tie** | Grid-connected farms and homes | Grid-following inverter, 12 kW, 3-phase 400 V (17.3 A per phase), LCL filter, interface protection and anti-islanding to EN 50549-1, RCD type B monitoring |
| **Heating** | Homes in areas without geothermal heat, which in Iceland are heated electrically | Grid-forming, feeding standard resistive heaters (immersion heater in a hot-water tank, or radiators) at 400 V AC, power set by the MPPT. Standard AC thermostats and switches work, and no 750 V DC reaches the household |

- **1-phase variant**: 230 V, 52 A at 12 kW. Many rural Icelandic connections
  are still single-phase, and distribution system operators usually limit
  single-phase generation. The single-phase limit has to be confirmed with
  the Icelandic DSOs (RARIK, HS Veitur, Veitur, Orkubú Vestfjarða). Power
  above the export limit goes to the heating mode or the dump load.
- **Grid code**: confirm that the DSOs apply EN 50549-1 and get their
  interface protection settings (TBC, doc 02).

### 4.2 Battery module (off-grid)

- Isolated dual active bridge, 750 V ↔ 48 V nominal (40–60 V window),
  12 kW, up to 250 A, built from **four interleaved 3 kW cells** (smaller
  magnetics; still runs if one cell fails).
- Galvanic isolation keeps the 48 V system safely separated from the
  750 V DC link.
- Charge profile set by the battery management system over CAN. Lithium iron
  phosphate is the recommended chemistry, with heated enclosures because it
  must not be charged below 0 °C.
- The battery feeds the household through a standard off-grid battery
  inverter (bought in; our product is the charger).

### 4.3 Priority logic (hybrid)

The controller sets the MPPT power from the torque curve (doc 11). The
modules then take it in a user-configured order, for example:

1. Battery (off-grid): charge until full.
2. Household consumption (grid-tie, self-consumption).
3. Heating: hot-water tank or space heating up to its thermostat.
4. Grid export, up to the DSO limit.
5. Dump load: anything left over, and always during stops and faults.

## 5. Efficiency and energy

| Stage | Efficiency at rated | Notes |
|---|---|---|
| Generator | 94.7 % | doc 06 losses scaled with speed and current |
| Active rectifier | 98.8 % | Typical SiC losses; replace with datasheet values |
| AC module | 98.5 % | Typical SiC 2-level with LCL filter |
| **Rectifier + AC module** | **97.3 %** | R7.5: ≥ 95 % ✅ |
| Auxiliaries | 120 W | Controller, sensors, cabinet fans |
| **Net output at rated** | **12.4 kW** | Rated wind for 12 kW net: 10.5 m/s |

Net annual energy (Rayleigh, 97 % availability): 20.8 MWh at V_ave 5 m/s,
31.8 at 6, 42.3 at 7, 51.5 at 8 and 65.6 MWh at 10 m/s.

## 6. Cold climate, enclosure and EMC (R7.4, R7.6)

- Cabinet at the tower base: IP55, insulated, with a thermostatic heater
  that brings the electronics above −20 °C before start (R7.4: start at
  −30 °C with self-heating). Heat exchanger with filtered air, salt-mist
  resistant; conformal-coated boards.
- Components rated for −40 °C storage; film capacitors only.
- EMC: screened generator cable, LCL filter on the grid side, common-mode
  chokes, layout to EN 61000-6-2/-4 (R7.6).
- Insulation monitoring on the DC link (IT system); RCD type B on the AC side.

## 7. Requirements status

| Requirement | Status |
|---|---|
| R7.1 common front end | ✅ Active rectifier + 750 V DC link + dump load |
| R7.2 modules | ✅ AC module (grid-tie 1/3-phase and heating), 48 V battery module, priority logic |
| R7.3 dump load | ✅ 20 kW continuous, controller-independent |
| R7.4 cold start | ✅ By design (heated cabinet, film capacitors); to be tested in a climate chamber |
| R7.5 efficiency ≥ 95 % | ✅ 97.3 % estimated; to confirm with datasheet losses and measurement |
| R7.6 EMC | Design measures listed; test in a lab |

## 8. Limitations and next steps

- Losses use typical SiC values, not a chosen device; thermal design of the
  heatsinks follows device selection.
- Icelandic DSO rules (single-phase limit, protection settings) are to be
  confirmed.
- Next steps:
  1. Device selection and loss/thermal design of the front end and AC module.
  2. Control design of the rectifier (current loops, field weakening, DC
     voltage control) in a switching-level simulation.
  3. Ask the Icelandic DSOs for connection rules.
  4. Prototype a 12 kW front end on a motor-generator test bench.
