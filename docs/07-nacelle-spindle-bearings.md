# 12 kW Wind Turbine for Iceland: Nacelle, Spindle and Bearings Concept

Status: **Draft, revision 1** · 2026-11-01
Owner: Category 5 (Nacelle, shaft and bearings), with Category 3 (yaw)
Builds on: [03 – Rotor](03-rotor-concept.md), [06 – Generator round 2](06-generator-round2.md)
Model: [`analysis/nacelle/loads.py`](../analysis/nacelle/loads.py)

## Summary

| Item | Recommendation |
|---|---|
| Layout | **Stationary hollow spindle** bolted to a cast bedplate; hub and generator drum turn together on two bearings on the spindle; stator on an aluminium carrier on the spindle |
| Main bearings | **Pair of single-row tapered roller bearings, back-to-back (O), preloaded**, on a 140 mm spindle seat, 240 mm apart |
| Spindle | **42CrMo4+QT, 140 mm OD, 90 mm bore**; stress reserve factor 17, stiffness 480 × the magnetic pull |
| Generator cooling path | Aluminium carrier + **finned aluminium insert in the spindle bore with a small fan**: **0.17 to 0.25 K/W**, meets the 0.40 K/W the generator needs with good margin |
| Mechanical brake | **Two spring-applied, hydraulically released calipers** on a disc at the drum (r = 0.30 m), **8.7 kNm**, about 21 kN clamp force each; plus a rotor lock pin for service |
| Yaw | **Active yaw**: four-point contact slewing ring, two geared motors, spring-applied yaw brake with controlled slip; design tilt moment 18 kNm, holding torque 8 kNm |
| Bedplate | Ductile iron **EN-GJS-400-18U-LT** (impact-tested at low temperature) |
| Tower top mass | **≈ 480 kg** (estimate) |

**Main finding:** with a 90 mm bore needed for cooling air and cables, the
spindle and bearings come out far stronger than the loads require. The
design is stiffness- and cooling-driven, not strength-driven. That is a good
place to be for a 20-year product in Icelandic storms.

---

## 1. Layout

```
  front                                                        rear
  (wind) ->
            blade root
               |
        +------+------+=====================+
        |   HUB with  |   GENERATOR DRUM    |  (rotating: hub + drum + magnets + brake disc)
        |  3 pitch    |  magnets inside     |
        |  drives     |  +---------------+  |
        |             |  |  STATOR       |  |  (stationary, on aluminium carrier)
   =====|==[B1]=======|==|===carrier=====|==|====================[ flange ]====> bedplate -> yaw -> tower
        |   front     |  |  rear brg [B2]|  |   stationary hollow SPINDLE (bore: cooling air + cable conduit)
        +-------------+  +---------------+  |
                      +=====================+--[ rear seal on spindle ]
                                     [ brake calipers on drum disc ]
```

- **Spindle (stationary):** bolted to the bedplate by a flange at the rear.
  Carries both main bearings and the stator carrier.
- **Rotating assembly:** hub (with pitch system) bolted to the generator
  drum. Both turn on bearings B1 and B2, so there is no shaft coupling and
  the 2 mm air gap is set by one pair of bearings.
- **Sealing:** the rotating assembly forms a closed volume around the stator.
  There is one large static seal at the hub, and one rotating seal where the
  drum rear cover meets the spindle. That rear seal is at small diameter,
  which keeps seal speed and wear low.
- **Spindle bore:** two separate channels. A cable conduit carries the pitch
  slip ring and generator cables. A cooling air channel holds a finned
  aluminium insert. The cooling air never enters the sealed generator.

Axial positions used in the model (from rotor centre): front bearing 0.12 m,
rear bearing 0.36 m, drum centre of gravity 0.30 m, stator 0.38 m, yaw axis
0.75 m.

---

## 2. Mass budget (estimate)

| Item | Mass |
|---|---|
| Blades (3 × 20 kg, TBC by layup study) | 60 kg |
| Hub and pitch system | 80 kg |
| Generator rotor drum (yoke, magnets, covers, brake disc) | 60 kg |
| Generator stator with aluminium carrier | 75 kg |
| Spindle | 45 kg |
| Bedplate | 70 kg |
| Yaw system | 45 kg |
| Nacelle cover and electrics | 20 kg |
| Slip ring, sensors, cabling, fan, seals | 25 kg |
| **Tower top total** | **≈ 480 kg** |

Rotor inertia: ≈ 216 kg·m².

---

## 3. Hub loads (concept level)

Quasi-static loads: steady BEM values × 1.5 dynamic factor, plus
first-principles storm, fault, ice and gyroscopic cases. Partial safety
factor 1.35 applied. **These will be replaced by aeroelastic DLC results**
(design basis, section 5).

> **Update (doc 08):** the aeroelastic simulation and the IEC 61400-2
> Simplified Load Model confirm the storm, brake and ice loads below. The
> worst hub moment is 27 % higher (8.2 kNm design) and operating thrust about
> twice these values; spindle and bearings still pass with large margin. See
> [08 – Load verification](08-load-verification.md), section 5.

| Case | What happens | Hub moment | Front bearing | Rear bearing | Axial |
|---|---|---|---|---|---|
| U1 Operating gust | 1.5 × max steady thrust, one-blade aerodynamic imbalance | 2.5 kNm | 10.5 kN | 12.6 kN | 4.3 kN |
| **U2 One blade stuck at fine pitch, parked at V_e1 = 58 m/s** (DLC 7.1) | That blade faces the storm broadside (root flap moment 5.2 kNm) | **6.4 kNm** | **32.2 kN** | **34.8 kN** | 4.7 kN |
| U3 Parked at V_e50 = 77 m/s, wind in rotor plane (DLC 6.2) | In-plane force 8 kN, holding torque 5.8 kNm | 0.2 kNm | 16.8 kN | 5.8 kN | 0 |
| U4 Ice on one blade, operating (DLC 1.5) | 15 kg of ice on one blade (IEC cold climate formula): 12 kN rotating imbalance at 178 rpm | 2.2 kNm | 16.8 kN | 2.5 kN | 4.3 kN |
| U5 Yaw fault at 5°/s, operating | Gyroscopic moment 0.35 kNm | 2.3 kNm | 13.5 kN | 13.1 kN | 4.3 kN |

The **stuck blade case (U2)** drives the bearings and spindle. The **ice
case (U4)** shows why operation with an iced blade must be prevented: the
rotating imbalance is 12 kN. Ice detection with automatic stop (R8.3) is
therefore a structural safety function, not only an energy-yield feature.

---

## 4. Main bearings

### 4.1 Arrangement

Two single-row **tapered roller bearings in back-to-back (O) arrangement**,
preloaded:
- O arrangement gives the widest effective spread for the hub overturning
  moment, which is what holds the air gap.
- Preload removes internal clearance, so the rotor runs true. It also
  avoids roller skidding at low load and low speed, which is common in
  turbulent wind.
- Both bearings share one seat diameter (140 mm), which simplifies
  machining and stock.

Alternatives considered: a single double-row tapered roller bearing (TDO,
more compact but harder to seal and replace) and a deep groove ball plus
spherical roller pair (more tolerant of misalignment, but less stiff).

### 4.2 Life and static safety

| | Front | Rear |
|---|---|---|
| Revolutions in 20 years (V_ave 10 m/s) | 1,407 million | 1,407 million |
| Target L10 (2 × design life, R5.1) | 2,814 million revolutions | 2,814 million revolutions |
| Equivalent dynamic load | 3.0 kN | 0.9 kN |
| **Required dynamic rating C** | **33 kN** | **10 kN** |
| Design static load (worst ultimate) | 32 kN | 35 kN |
| **Required static rating C0** (s0 ≥ 2) | **≥ 65 kN** | **≥ 70 kN** |

Tapered roller bearings with a 140 mm bore have ratings several times higher
than these values. In practice the bearing size is set by the spindle
diameter, and the spindle diameter by the bore it needs (section 5).

The fatigue spectrum uses a simple assumption for turbulence-driven hub
moments (half the steady flap moment as an equivalent cyclic load). Even if
that is off by a factor of 3, the bearings still meet life with large
margin. No life modification credit (a_ISO) is taken.

### 4.3 Cold-climate lubrication and sealing

| Item | Choice |
|---|---|
| Grease | Synthetic base oil (PAO or ester), lithium-complex or polyurea, NLGI 2, rated to −40 °C start-up, with corrosion inhibitors for humid salt air |
| Relubrication | Automatic single-point lubricators with purge path, interval sized for 12-month service (R14.1) |
| Seals (each side) | Triple barrier: outer labyrinth (sheds water and ash), low-temperature HNBR lip seal (−40 °C rated), inner V-ring |
| Drum rear seal | Labyrinth plus low-temperature lip seal on a hardened, chrome-plated spindle sleeve |
| Breather | Desiccant breather on the sealed generator volume |
| Electrical | Grounding brush and insulated sleeve on one bearing, so lightning and converter currents bypass the rolling elements |

---

## 5. Spindle

| Item | Value |
|---|---|
| Material | 42CrMo4+QT (minimum yield 650 MPa in this section size) |
| Outer diameter / bore | 140 mm / 90 mm |
| Design bending moment (worst case, γ = 1.35) | 7.7 kNm |
| Bending stress | 35 MPa |
| Reserve factor on yield (γm = 1.1) | **17** |
| Stiffness at stator vs magnetic pull | 925 kN/mm vs 1.9 kN/mm, **ratio 480** (requirement ≥ 10) |
| Stator sag under its own weight | < 0.001 mm |

The spindle is very lightly stressed. The 90 mm bore is set by the cable
conduit plus cooling air channel, and a thick wall keeps it stiff and
resistant to fatigue at notches (bearing shoulders, flange radius). A lighter
spindle (for example 125/90 mm) is possible later, once aeroelastic loads are
known. That is a cost and mass optimisation, which is deferred.

---

## 6. Generator cooling path through the spindle

The generator thermal model (doc 05 and 06) needs **≤ 0.40 K/W** from the
stator core to outside air through the carrier and spindle.

| Path element | Thermal resistance |
|---|---|
| Aluminium stator carrier, 25 mm thick disc, cast AlSi7Mg (k ≈ 150 W/mK) | 0.048 K/W |
| Two shrink-fit contacts | 0.005 K/W |
| Spindle wall | 0.006 K/W |
| Bore, plain, 10 m/s air | 0.32 K/W → **total 0.38 K/W** (barely meets) |
| **Bore with finned aluminium insert (3 × area), 10 m/s air** | **total 0.17 K/W** |
| Finned insert, 5 m/s air (half fan flow) | total 0.25 K/W |

**Recommendation:** finned insert plus a small ducted fan (≈ 20 to 40 W)
drawing filtered nacelle air through the bore. With the fan at half flow, the
path still has 37 % margin. **If the fan fails**, the controller derates
power based on the winding temperature sensor (R8.1), so a failed fan cannot
overheat the generator.

---

## 7. Mechanical brake

Primary braking is aerodynamic: three **independent** pitch drives, each
with its own stored energy. Any single pitch failure leaves two blades
feathering, which stops the rotor. The mechanical brake is the second,
independent braking system, used for parking and service.

| Requirement | Torque |
|---|---|
| Hold the parked rotor at V_e50 with wind in the rotor plane (DLC 6.2) | 5.8 kNm |
| Hold against one blade stuck at fine pitch (others feathered) | 0.7 kNm |
| All blades at fine pitch, storm (theoretical worst, stalled rotor) | 2.1 kNm |
| **Brake design torque (1.5 × worst)** | **8.7 kNm** |
| Kinetic energy at 250 rpm design overspeed (doc 08) | 74 kJ |

**Concept:** two spring-applied, hydraulically released calipers on a steel
disc at the drum, radius 0.30 m. Each needs about 21 kN clamp force, which is
standard for industrial fail-safe calipers. Springs apply the brake when
power or hydraulics are lost. Brake pads are rated for −40 °C and salt.

**Rotor lock:** a mechanical lock pin into the drum for all service work.
This is required for personnel safety regardless of the brake.

---

## 8. Yaw system

| Item | Value |
|---|---|
| Concept | Active yaw, four-point contact ball slewing ring with internal gear, two geared motors |
| Design tilt moment at the yaw bearing (γ = 1.35) | 18.4 kNm |
| Design yaw holding torque (parked, V_e50 side wind) | 8.0 kNm |
| Nacelle side drag at V_e50 | 5.8 kN |
| Tower top weight | 4.7 kN |
| Yaw rate | 0.5°/s in operation |
| Yaw brake | Spring-applied with **controlled slip** above the holding torque, so extreme side gusts turn the nacelle instead of overloading the tower top |
| Cable twist | Hanging cable loop with automatic untwist after ±3 turns (no slip ring for power) |

---

## 9. Materials for Icelandic conditions

| Part | Material | Why |
|---|---|---|
| Bedplate | Ductile iron EN-GJS-400-18U-LT | Guaranteed impact toughness at low temperature; castable with integral ribs |
| Spindle | 42CrMo4+QT, Charpy tested at −40 °C | Strength and toughness in cold |
| Hub | EN-GJS-400-18U-LT casting | Same as bedplate, complex shape |
| Stator carrier, bore insert | Cast AlSi7Mg / extruded 6082 | High thermal conductivity |
| Fasteners | Hot-dip galvanized 10.9 (structural), A4 stainless with isolation (covers) | R9.2 |
| Nacelle cover | Glass/vinyl-ester composite, UV-stabilised gelcoat | Salt and UV (R9.4) |
| External surfaces | Hot-dip galvanized + duplex paint, C5 very high | R6.5, R9.1 |

---

## 10. Inputs to other categories

| To | Value |
|---|---|
| Tower (cat. 6) | Tower top mass ≈ 480 kg; tilt moment 18.4 kNm; parked horizontal force ≈ 14 kN at V_e50 with side wind (rotor in-plane 8 kN + nacelle 5.8 kN), before tower drag |
| Hub and pitch (cat. 3) | Independent pitch drives confirmed as primary brake; hub casting in EN-GJS-400-18U-LT |
| Control (cat. 8) | Ice detection is safety-critical (12 kN imbalance); fan failure → derate on winding temperature; yaw untwist logic; brake and lock interlocks |
| Generator (cat. 4) | Cooling path 0.17 to 0.25 K/W available (needs ≤ 0.40) |

---

## 11. Next steps

1. ~~Implement the IEC 61400-2 Simplified Load Model as an independent
   cross-check of these loads, then the aeroelastic model.~~ Done in
   [doc 08](08-load-verification.md).
2. Blade structural layup study to confirm the 20 kg blade mass (it drives
   the ice, inertia and gravity loads).
3. Detail design of spindle (shoulders, flange, bore insert) with FEA of
   notches, and of the hub casting.
4. Bearing supplier selection, with grease and seal qualification at −40 °C
   in a climate chamber.
