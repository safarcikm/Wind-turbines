# 12 kW Wind Turbine for Iceland: Generator Concept Study

Status: **Draft, revision 1** · 2026-11-01
Owner: Category 4 (Generator)
Builds on: [02 – Design basis](02-design-basis.md), [03 – Rotor concept](03-rotor-concept.md)
Model: [`analysis/generator/`](../analysis/generator/)

## Summary

| Decision | Recommendation |
|---|---|
| Topology | **Outer-rotor radial flux, surface NdFeB magnets, iron-cored stator with tooth-coil (concentrated) windings** |
| Size | Air gap diameter **0.60 m**, stack length **~70 mm**, outer diameter **~0.65 m** |
| Poles / slots | **40 poles / 45 slots** (59 Hz at rated, winding factor 0.945, low cogging) |
| Magnets | **N42SH** NdFeB, 7.4 mm thick, segmented, coated and fully encapsulated |
| Current density | **3.0 A/mm²** (deliberately low for a cool winding and long insulation life) |
| Efficiency at rated | **≈ 94.5 %** (meets R4.5, ≥ 93 %) |
| Active mass | **≈ 75 kg** (≈ 6 kg magnets, 21 kg copper, 36 kg laminations, 12 kg rotor yoke) |
| Insulation | Class H materials, designed for class B temperature rise; vacuum-pressure impregnated, then epoxy-potted end windings |
| Generator converter interface | Active (PWM) rectifier; power electronics rated for ≈ 850 V peak worst case |

The outer rotor drum doubles as the generator housing and can bolt directly
to the hub. That gives a compact, sealed unit with the stator fully enclosed,
which suits Icelandic salt, ash and driven snow.

---

## 1. Requirements recap

From the rotor study and design basis:

| Input | Value |
|---|---|
| Rated speed | 178 rpm |
| Rated shaft torque | 729 Nm (sized at 802 Nm, +10 % continuous margin) |
| Shaft power | 13.6 kW |
| Speed range | ≈ 40 to 178 rpm, design overspeed 230 rpm |
| Efficiency | ≥ 93 % at rated (R4.5) |
| Temperature | −30 °C operation, −40 °C survival, +30 °C hot day (R4.1, R4.3) |
| Environment | Salt, condensation, ash, H₂S (R4.2, R4.4) |

---

## 2. Topologies considered

| | A. Outer-rotor radial flux, iron core (**chosen**) | B. Axial flux, double rotor, coreless stator | C. Axial flux, yokeless iron core (YASA type) | D. Inner-rotor radial flux |
|---|---|---|---|---|
| Magnet mass (NdFeB) | **≈ 6 kg** | ≈ 27 kg | ≈ 8 to 10 kg | ≈ 7 kg |
| Active mass | **≈ 75 kg** | ≈ 200 kg (thick rotor disks) | ≈ 70 kg | ≈ 90 kg |
| Outer diameter | **≈ 0.65 m** | ≈ 0.81 m | ≈ 0.55 m | ≈ 0.70 m (with housing) |
| Efficiency | **≈ 94.5 %** | ≈ 94.5 % | ≈ 95 % | ≈ 94 % |
| Cogging torque | Low with 40p/45s and skew | **Zero** | Low to medium | Low with good slot/pole choice |
| Sealing and cooling | **Rotor drum is the enclosure; stator heat goes to drum by air gap and to shaft** | Coils cast in resin: robust but poor heat removal | Complex sealing between two rotors | Classic housing, separate hub |
| Magnetic forces | Radial, balanced | **≈ 25 kN axial pull per disk**, needs stiff disks and careful assembly | Axial pull, balanced | Radial, balanced |
| Manufacturing | Laminations, tooth coils, VPI: established | Simple coils and moulds | Soft magnetic composite cores, complex | Established |
| Maturity in small wind | High (most commercial 5 to 20 kW turbines) | High in DIY, rare in certified products | Low | Medium |

Values for A and B come from the sizing model; values for C and D are
engineering estimates by comparison and were not modelled.

**Why A:**
- It uses **4 to 5 times less magnet material** than the coreless axial
  flux machine. Magnets are one of the few bought parts, so less is better
  for supply security and mass.
- Tower top mass is about **125 kg lower**, which the tower, yaw bearing
  and foundation all benefit from.
- The drum can form a closed, sealed housing that bolts straight onto the
  hub.
- Tooth-coil windings are short, easy to wind precisely in-house, and easy
  to insulate well.

**What B does better:** it has no cogging at all, and coils cast in resin
are very tolerant of humidity. In A, cogging is handled with the slot/pole
choice and magnet skew (section 3.3), and humidity with VPI plus potting
and an anti-condensation strategy (section 4).

C was rejected because soft magnetic composite cores and a sealed
two-rotor housing add risk for little gain. D was rejected because the
same torque needs a larger machine plus a separate housing and hub.

---

## 3. Recommended design

### 3.1 Main dimensions

A diameter sweep (outer-rotor, 30 kA/m electric loading, 0.85 T air gap
flux) shows that a larger diameter gives a shorter, lighter machine with
less magnet material, at almost the same efficiency:

| Air gap diameter | Stack length | Poles/slots | Magnets | Active mass | Efficiency (3.5 A/mm²) |
|---|---|---|---|---|---|
| 0.45 m | 122 mm | 32/36 | 7.7 kg | 84 kg | 94.0 % |
| 0.50 m | 99 mm | 32/36 | 6.9 kg | 80 kg | 94.1 % |
| 0.55 m | 82 mm | 32/36 | 6.3 kg | 77 kg | 94.1 % |
| **0.60 m** | **69 mm** | **40/45** | **5.8 kg** | **68 kg** | **94.2 %** |
| 0.65 m | 59 mm | 40/45 | 5.3 kg | 67 kg | 94.1 % |
| 0.70 m | 50 mm | 40/45 | 4.9 kg | 66 kg | 94.0 % |

Above 0.60 m the gains flatten, while end windings take a growing share of
the copper and the stiffness needed to hold a 2 mm air gap becomes harder
to achieve. **0.60 m** is the balance point.

Lowering the current density from 3.5 to **3.0 A/mm²** (quality-first
choice) adds about 7 kg but cuts copper losses by 70 W, raises efficiency to
94.5 % and lowers winding temperature, which roughly doubles insulation life
for every 10 °C saved.

| Current density | Efficiency | Copper loss | Slot depth | Active mass |
|---|---|---|---|---|
| **3.0 A/mm²** | **94.5 %** | **435 W** | 55 mm | **75 kg** |
| 3.5 A/mm² | 94.2 % | 507 W | 47 mm | 68 kg |
| 4.0 A/mm² | 93.7 % | 579 W | 41 mm | 63 kg |

### 3.2 Electromagnetic summary (recommended design)

| Item | Value |
|---|---|
| Air gap (mechanical) | 2.0 mm |
| Air gap flux density | 0.85 T (flat top), 1.03 T fundamental |
| Tangential stress | 20.6 kPa |
| Electric loading | 30 kA/m |
| Tooth width / slot depth | 22 mm / 55 mm |
| Stator and rotor yoke | 11 to 12 mm each (rotor yoke may be thickened for stiffness) |
| Electrical frequency | 59 Hz rated, 77 Hz at overspeed |
| Laminations | M270-35A (0.35 mm, low loss) |
| Losses at rated | Copper 435 W, iron 200 W, magnet eddy and stray ≈ 110 W, total ≈ 745 W |

### 3.3 Slot/pole choice and cogging

40 poles with 45 slots (the same 9:8 family as 36/32) gives:
- a high fundamental winding factor (0.945);
- a large least common multiple of slots and poles (360), which means
  **inherently low cogging torque**;
- no net unbalanced magnetic pull, since the machine is symmetric
  (5 repeating sections).

Cogging target: **below 0.5 % of rated torque (≈ 3.6 Nm)**, checked by FEA,
with magnet step-skew as a backup measure. Low cogging lets the rotor start
at about 3 m/s, helped by pitching the blades to a starting angle.

### 3.4 Magnets

- **Grade N42SH** (rated to 150 °C, coercivity ≥ 1590 kA/m). Its strength
  rises in the cold: Br ≈ 1.39 T at −40 °C, compared with ≈ 1.18 T at
  100 °C. Design point uses the hot value; voltage limits use the cold value.
- **Demagnetisation check** by FEA for a three-phase terminal short circuit
  at the maximum magnet temperature (target design 100 °C, check at 120 °C).
- **Corrosion protection:** NiCuNi plating plus epoxy coating on each
  magnet, bonded with a cold-rated structural adhesive, then encapsulated
  on the rotor with a glass-epoxy or stainless retaining layer. No bare
  NdFeB is exposed to air.
- Each pole is split into **axial segments** to cut eddy losses.

### 3.5 Voltage and converter interface

| Condition | Line voltage (rms) |
|---|---|
| Rated speed, hot magnets | ≈ 380 V (design choice, set by turns per coil) |
| Overspeed 230 rpm, cold magnets (−40 °C) | ≈ 600 V (≈ 850 V peak) |

The power electronics (category 7) must withstand about 850 V peak on the
generator side, which points to 1200 V class semiconductors. An **active
PWM rectifier** is recommended over a diode rectifier with boost converter.
It controls generator torque directly, gives lower generator losses and
noise, and allows active damping of drivetrain vibration. This is a
proposal for category 7 to confirm.

---

## 4. Built for Icelandic conditions

| Threat | Measure |
|---|---|
| Salt and humid air | Stator fully inside the sealed rotor drum; labyrinth plus lip seals at the shaft; breather with desiccant |
| Condensation when parked | Low-power stator heating by DC injection from the converter (no separate heater needed); temperature and humidity sensor inside |
| Winding insulation | Class H materials (180 °C) designed for class B rise (80 K); vacuum-pressure impregnation, then epoxy potting of end windings; humidity and salt mist qualification (R4.2) |
| Cold (−40 °C) | Adhesives and potting rated for −40 °C thermal cycling; bearing grease and seals rated to −40 °C (category 5) |
| Volcanic ash | No air path through the generator; cooling is through the drum surface (natural convection plus the wind) |
| H₂S near geothermal areas | Tinned copper connections, sealed terminal box, conformal-coated sensors |
| Overspeed and short circuit | Demagnetisation margin (section 3.4), insulation rated for overspeed voltage, rotor retention checked at 1.5 × overspeed |
| Lightning | Insulated bearing or shaft grounding brush to keep lightning and converter currents out of the bearings (category 5 and 6) |

**Cooling check:** about 750 W of losses at rated must leave through the
drum. On a hot calm day (+30 °C) at rated power the wind is at least
10.5 m/s, so the drum is in strong airflow. A thermal network model is the
next step to confirm winding hot spot below 130 °C (class B rise plus
margin within class H).

---

## 5. Integration with hub and nacelle

Proposed layout (to be confirmed in category 5):
- Stationary main shaft (spindle) fixed to the nacelle frame; the stator
  mounts on the spindle.
- Two main bearings on the spindle carry the rotating hub and generator
  drum together.
- Generator drum bolts to the hub flange, so the rotor and hub turn as one
  unit, with no coupling.
- Pitch slip ring and cabling pass through the hollow spindle.
- The mechanical brake disc mounts on the drum.

This is the arrangement used on many direct-drive turbines. It keeps the
2 mm air gap stable because both rotor and stator are referenced to the
same spindle and bearing pair.

---

## 6. Inputs to other categories

| To | Value |
|---|---|
| Nacelle and bearings (cat. 5) | Generator mass ≈ 75 kg active, ≈ 120 to 140 kg with structure (estimate); 2 mm air gap needs bearing and spindle stiffness to hold ≤ 0.2 mm eccentricity; radial magnetic pressure ≈ 37 kN total (balanced, but sensitive to eccentricity) |
| Power electronics (cat. 7) | 3-phase, 59 Hz rated, ≈ 380 V rms line at rated, ≈ 850 V peak worst case; active rectifier proposed; DC injection for stator heating |
| Control (cat. 8) | Torque-speed curve from rotor study; winding and magnet temperature sensing (PT100 in winding, rotor temperature estimated from back-EMF) |
| Manufacturing (cat. 10) | Lamination stamping or laser cutting, tooth-coil winding machine, VPI tank, magnet assembly fixture (strong magnetic forces, safety procedure needed) |

---

## 7. Next steps

1. 2D finite element model (FEMM or similar) of the 40p/45s design: back-EMF,
   cogging, torque ripple, demagnetisation at short circuit.
2. Thermal network model for hot-day and cold-start cases.
3. Spindle, bearing and drum structural design with category 5.
4. Choose winding turns and wire size together with the power electronics
   DC link voltage.
5. Build a short (one-fifth length) stator and rotor segment as an early
   prototype to test winding, VPI, potting and magnet bonding processes.
