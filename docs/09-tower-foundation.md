# 12 kW Wind Turbine for Iceland: Tower and Foundation Concept

Status: **Draft, revision 1** · 2026-11-01
Owner: Category 6 (Tower and foundation), with Category 8 (Control)
Builds on: [02 – Design basis](02-design-basis.md), [07 – Nacelle](07-nacelle-spindle-bearings.md), [08 – Load verification](08-load-verification.md)
Models: [`analysis/tower/`](../analysis/tower/)

> **Update (doc 13):** the sized hub and pitch system raises the tower top
> from 480 to about 600 kg. 18 m: f1 1.13 Hz (rigid), exclusion zone about
> 62–75 rpm. 24 m: f1 on soft soil with ice is 0.737 Hz against the 0.734 Hz
> limit, so the 24 m tower needs a small stiffening in the next update. Gin
> pole line pull 57 / 73 kN. See [13 – Hub, pitch and yaw](13-hub-pitch-yaw.md), section 8.

## Summary

| Item | Recommendation |
|---|---|
| Tower type | **Standard product: freestanding tapered steel monopole, tilt-up on a base hinge with a removable gin pole. A guyed variant for open farm sites follows later** (decision 2026-11-01, section 6) |
| 18 m tower | Base Ø 550 mm × 10 mm, top Ø 320 mm × 8 mm, two 9 m sections, **≈ 1.9 t** steel |
| 24 m tower | Base Ø 600 mm × 12 mm, top Ø 320 mm × 8 mm, three 8 m sections, **≈ 3.1 t** steel |
| Steel and protection | S355NL (impact tested at −50 °C), EN 1090 EXC3, hot-dip galvanized plus duplex paint (R6.5) |
| What sizes the tower | **The parked storm with side wind at V_e50 = 77 m/s.** Drag on the tower itself is 40 to 50 % of the base moment. A 0.5 g earthquake on soft soil comes close (89 % of storm on 18 m) |
| Frequency strategy | No tower can sit above 1P (it would need > 3.3 Hz). The towers are **"soft-stiff": 1.21 Hz (18 m) and 0.87 Hz (24 m)**, between 1P at minimum speed and 3P at minimum speed. The controller **skips the rotor speeds where 1P crosses the tower frequency** (66–80 rpm on 18 m, 48–58 rpm on 24 m). Energy cost < 0.1 % |
| New requirement | **Rotor imbalance ≤ 0.2 kg·m** and a vibration trip. A 5 × worse imbalance would use the whole 20-year fatigue life of the 18 m tower even with the exclusion zone, and would use it in under a year without the zone |
| Foundations | Spread footings 3.8 to 4.9 m square at 1.6 m frost depth (10 to 15 m³ concrete) on soil; a 1.6 m plinth with 8 grouted rock anchors on rock |
| Tilt-up | Gin pole 6 m (18 m tower) or 8 m (24 m), line pull 52 / 68 kN including a 1.3 dynamic factor; a 2-part reeved hydraulic winch is enough. No crane (R6.4) |
| Requirement changes | R6.2 rewritten for the soft-stiff tower with an exclusion zone; new R6.6 (rotor balance and vibration trip) |

---

## 1. Requirements and inputs

From the design basis (doc 02) and nacelle concept (doc 07):

- Tilt-up tower, **18 m and 24 m** hub height options (R6.4: gin pole and
  winch, no crane).
- Eurocode 3, 7 and 8 with Icelandic annexes plus the IEC 61400-2 load cases
  (R6.1). Hot-dip galvanized plus duplex paint (R6.5).
- Foundations for rock, firm soil, soft volcanic soil and frost-susceptible
  ground (R6.3).
- Tower top mass ≈ 480 kg; parked side force at V_e50 14 kN (rotor in-plane
  8 kN plus nacelle 5.8 kN); top diameter 320 mm for the yaw bearing adapter.
- Original R6.2: tower frequency ±10 % clear of 1P and 3P over the whole
  speed range. **This cannot be met** (section 2) and is revised.

## 2. Frequency placement

The rotor runs from 40 to 178 rpm. 1P spans 0.67 to 2.97 Hz and 3P spans 2.0
to 8.9 Hz, so the two bands overlap and no frequency is clear of both
([Campbell diagram](../analysis/tower/results/campbell.png)).

| Option | Tower frequency | Feasible? | Energy cost |
|---|---|---|---|
| A Stiff-stiff | > 9.8 Hz | No: even without the top mass an 18 m tube would need more than 3 m diameter | — |
| B Soft-soft | < 0.61 Hz | No: storm strength forces a stiffer tube | — |
| C Raise minimum speed to 80 rpm, tower 3.3 to 3.6 Hz | 3.3–3.6 Hz | No: a freestanding or guyed tilt-up tube cannot reach 3.3 Hz (an untapered tube without top mass needs Ø ≥ 1.05 m at 18 m) | 0.1–0.6 % |
| D Tower above 1P, exclusion zone at the 3P crossing | 3.3–4.2 Hz | No, same reason as C | < 0.05 % |
| **E Soft-stiff tower, exclusion zone at the 1P crossing** | **0.73–1.82 Hz** | **Yes**: 18 m at 1.21 Hz, 24 m at 0.87 Hz | **< 0.01 %** (steady power curve) |

In option E, 3P never meets the first tower mode, because 3P at minimum
speed (2.0 Hz) is above the tower frequency with margin. 1P crosses the tower
frequency once, at 73 rpm (18 m) or 52 rpm (24 m), at winds of 4.0 to 4.8 m/s
and 2.9 to 3.5 m/s. The controller holds the rotor at the lower edge of the
zone, then crosses it quickly by unloading the generator (going up) or adding
torque (going down). In the time-domain simulation the rotor spent 5.6 % of
the time inside the zone at 4 m/s, 2.8 % at 6 m/s and none above, with no
measurable loss of power.

The frequency hardly depends on the soil (1.21 Hz on every footing, because
the footings needed for storm overturning are stiff), and ice on the tower
lowers it to 1.09 Hz. **The tower frequency shall be measured at
commissioning** with the nacelle accelerometer, and the controller sets the
zone from the measured value.

## 3. Loads

| Case | 18 m base moment (design) | 24 m base moment (design) | Factor |
|---|---|---|---|
| Operation and faults, aeroelastic simulation (worst: DLC 7.1 parked with one blade stuck at fine pitch; DLC 1.3 extreme turbulence 99 / 137 kNm char.) | 221 kNm | 336 kNm | γ = 1.35 |
| **Parked at V_e50 = 77 m/s, side wind**, ρ = 1.35, tower drag C_f 0.8, IEC gust profile α = 0.11 | **649 kNm** | **1006 kNm** | γ = 1.5 (EN 1990, stricter than IEC 1.35) |
| Parked at V_e1 = 58 m/s with ice (DLC 6.5): 50 mm wet snow on the tower (700 kg/m³), blade area +30 % | 521 kNm | 817 kNm | γ = 1.5 |
| Earthquake 0.5 g, EN 1998-1 type 1, ground type D, 1 % damping (IEC 61400-1 annex C), 4 modes SRSS, plus operating loads | 579 kNm | 763 kNm | γ = 1.0 |
| IEC 61400-2 SLM parked thrust (41.6 kN design) with γ = 3 on tower drag (sensitivity only) | 1248 kNm | 1920 kNm | γ = 3.0 |

Notes:
- The simulation includes the new tower frequency, the exclusion zone,
  ±0.3° pitch misalignment, quasi-static tower drag and the hub tilt moment.
- Tower drag at V_e50 is about 180 kNm characteristic on the 18 m tower,
  42 % of the storm base moment, and 50 % on the 24 m tower. The 77 m/s
  design gust (Class S, doc 02) therefore drives the whole tower and
  foundation.
- **SLM sensitivity:** if a certification body required the SLM thrust and
  a factor of 3 on the tower too, the towers would be at 163 % and 175 %
  utilisation and would need about 1.7 × the section modulus. The SLM tower
  clause has to be checked against the purchased standard (doc 08, next step 1).
  The design here follows the aeroelastic route for the tower.

Bending moment and utilisation along the 18 m tower:
[monopole_18m_moments.png](../analysis/tower/results/monopole_18m_moments.png).

## 4. Tower design and checks

| Check | 18 m | 24 m | Limit |
|---|---|---|---|
| Geometry | Ø 550 → 320 mm, t 10 / 8 mm, 2 × 9 m | Ø 600 → 320 mm, t 12 / 10 / 8 mm, 3 × 8 m | |
| Steel mass (incl. 10 % flanges, hinge, fittings) | 1.94 t | 3.07 t | |
| Strength utilisation (σ / (f_y / 1.1)) | **0.85** (storm) | **0.92** (storm) | ≤ 1.0 |
| Largest D/t | 55 | 51 | ≤ 59.6 (class 3, no local buckling) |
| Fatigue damage, base flange weld (detail 71, γ_Mf 1.35) | 0.22 | 0.32 | ≤ 1.0 |
| Fatigue damage, section flange welds | 0.23 | 0.23 / 0.45 | ≤ 1.0 |
| First frequency (rigid / soft soil with ice) | 1.22 / 1.09 Hz | 0.88 / 0.78 Hz | 0.73–1.82 Hz |
| Second frequency (meets 3P at) | 6.75 Hz (135 rpm) | 4.27 Hz (85 rpm) | see 4.2 |
| Tilt-up utilisation (horizontal, dynamic factor 1.3, 15 m/s wind) | 0.40 | 0.49 | ≤ 1.0 |
| Base flange bolts (to hinge frame) | 24 × M24 10.9 on Ø 650 mm | 32 × M24 10.9 on Ø 700 mm | |
| Section flange bolts | 12 × M24 at 9 m | 20 × M24 at 8 m, 12 × M24 at 16 m | |

Fatigue uses the 20-year rainflow spectrum of the simulated base and flange
moments (DLC 1.1, Rayleigh V_ave = 10 m/s), with the EN 1993-1-9 bilinear
S-N curve. The damage-equivalent base moment (m = 4, 10⁷ cycles) is 63 kNm on
the 18 m tower.

### 4.1 Side-side resonance and rotor balance

The simulator models the fore-aft direction, where the rotor adds strong
aerodynamic damping. Side-side, a rotor mass imbalance drives the tower at
1P with only structural damping (taken as 0.5 %). This was checked
analytically over the rotor speed distribution:

| Rotor imbalance | 18 m, with exclusion zone | 18 m, no zone | 24 m, with zone | 24 m, no zone |
|---|---|---|---|---|
| 0.2 kg·m (balance grade G6.3 plus blade sets matched within 0.5 % static moment) | 0.00 | 0.03 | 0.00 | 0.00 |
| 1.0 kg·m (for example light ice, water in a blade, poor balance) | **1.09** | 23 | 0.02 | 2.6 |

(Fatigue damage at the base over 20 years, V_ave = 6 m/s site; the damage
from passing through the zone is a rough estimate.)

The exclusion zone removes the risk at the design imbalance. A fivefold
imbalance would still use about the whole 20-year fatigue life of the 18 m
tower with the zone, and under a year without it. Therefore:

- **New R6.6:** residual rotor imbalance ≤ 0.2 kg·m (rotor balanced to
  ISO 21940-11 G6.3, blades supplied as sets matched by static moment within
  0.5 %), and a **vibration trip** on the nacelle side-side 1P amplitude,
  set to the level of a 0.5 kg·m imbalance.
- The same trip doubles as ice detection by imbalance (R8.3).
- A passive tuned mass damper in the nacelle is a fallback if prototype
  measurements show lower damping than assumed.

### 4.2 Second tower mode

The second mode meets 3P inside the operating range (135 rpm on 18 m, 85 rpm
on 24 m). With the heavy tower top, that mode moves the top very little
(0.8 % and 1.4 % of the top compliance), and with an assumed 3P thrust
ripple of 5 % the fatigue damage is 0.002 or less. Tower shadow is not in the
simulator, so this must be confirmed with OpenFAST and prototype strain
measurements.

## 5. Foundations

Footing base at 1.6 m (frost depth, to be confirmed per region with local
data). Checks: characteristic storm eccentricity ≤ B/4, no gap under
the worst operating load (e ≤ B/6), design bearing pressure on the effective
area. Soil values are generic placeholders.

| Ground | 18 m tower | 24 m tower | Governing check |
|---|---|---|---|
| Firm soil (dense gravel, moraine), q_Rd 300 kPa | 3.8 m square, 9.5 m³ concrete | 4.4 m square, 12.4 m³ | Overturning (e = B/4) |
| Soft volcanic soil (loose ash, pumice sand), q_Rd 100 kPa | 4.3 m square, 11.9 m³ | 4.9 m square, 15.2 m³ | Bearing |
| Frost-susceptible silt, q_Rd 150 kPa | 4.0 m square, 10.4 m³ | 4.6 m square, 13.5 m³ | Bearing; base below frost depth or insulated (frost-protected shallow foundation) |
| Rock (lava, basalt) | 1.6 × 1.6 × 0.8 m plinth, 8 grouted Ø 28 mm threadbars on Ø 1.2 m, ≥ 3 m bond, 262 kN design each | Same plinth, 8 × Ø 40 mm, 410 kN each | Anchor tension |

All footings are stiff enough that soil stiffness does not change the tower
frequency. Concrete C30/37 with frost resistance (XF4 exposure class) and
air entrainment. The anchor cage and hinge frame are cast in, so one tower
fits every foundation type.

## 6. Freestanding against guyed

| | Freestanding monopole (recommended) | Guyed tube |
|---|---|---|
| 18 m steel | 1.94 t | 1.27 t tube Ø 324 × 8 mm + 84 kg guys (4 × 18 mm wire rope) |
| 24 m steel | 3.07 t | 1.78 t tube Ø 273 × 10 mm + 127 kg guys |
| Frequency | 1.21 / 0.87 Hz | 1.78 / 1.57 Hz, drops to 1.47 / 1.35 Hz with ice and one slack guy. A guyed tube cannot reach 3.3 Hz either, so it needs the same exclusion zone |
| Footprint | One footing, 4 to 5 m | Guy circle 21.6 m (18 m) or 28.8 m (24 m) diameter, 4 anchors with 72–76 kN design uplift each plus a central pad |
| Iceland exposure | Nothing to ice up but the tube | Iced guys add load and can gallop in wet-snow storms; guys need re-tensioning after freeze–thaw; hazard to livestock, snowmobiles and farm machinery |
| Service | Inspect bolts | Inspect bolts, guys, terminations and anchors; re-tension |

**Decision (Martin, 2026-11-01): offer both.** The freestanding monopole is
the standard product. A guyed variant for open farm sites will be designed
later, reusing the same hinge, gin pole, exclusion zone logic and rotor
balance requirement. Its open items are guy icing and galloping, anchor
designs per soil, and re-tensioning after freeze–thaw.

## 7. Tilt-up

- Base hinge on the cast-in hinge frame; gin pole fixed at right angles to
  the tower at the hinge, length 0.33 H (6 m or 8 m), removable and shared by
  installers.
- Line pull with dynamic factor 1.3 and a 15 m/s gust on the rotor: 52 kN
  (18 m) and 68 kN (24 m). With 2-part reeving, a 30 to 35 kN hydraulic or
  tractor-driven winch is enough.
- The tower is a cantilever from the hinge when horizontal, so the lift
  bending moment (309 / 540 kNm) is below the storm design moment.
- Raising and lowering is limited to gusts below 15 m/s (DLC 8.1), with side
  guys or a winch line on each side to control lateral swing.
- After raising, the base flange is bolted (24 or 32 × M24 10.9) and the
  hinge pins carry no load in service.

## 8. Changes to the design basis

- **R6.2 (revised):** the tower first natural frequency shall lie between
  1.1 × 1P at minimum operating speed and 3P at minimum operating speed / 1.1
  (0.73 to 1.82 Hz) in all foundation and ice conditions. The controller
  shall exclude rotor speeds within ±10 % of the speed where 1P equals the
  tower frequency. The tower frequency shall be measured at commissioning to
  set the zone.
- **R6.6 (new):** residual rotor imbalance ≤ 0.2 kg·m (ISO 21940-11 G6.3,
  blades matched by static moment within 0.5 %). A vibration trip on the
  side-side 1P amplitude shall stop the turbine at the equivalent of
  0.5 kg·m.

## 9. Limitations

- Concept-level soil data; each site needs a geotechnical check and the
  regional frost depth.
- The simulator has only the tower fore-aft mode and no tower shadow;
  side-side and second-mode checks are analytical.
- Wind on the tower uses an IEC gust profile and C_f 0.8 without a
  structural dynamic factor (reasonable for a tower at 1 Hz under a 3 s gust,
  to be checked with EN 1991-1-4 c_s c_d).
- Flange, hinge and door-free base details need detailed FEA. Galvanizing
  bath length must fit 9 m sections (TBC with the galvanizer); the steel
  shall have controlled silicon content and the details shall follow
  guidance against liquid metal assisted cracking.

## 10. Next steps

1. ~~Blade structural layup study.~~ Done in [doc 10](10-blade-structure.md):
   20.5 kg carbon-cap blade, flap 13.2 Hz.
2. Controller design: exclusion zone logic, constant power above rated,
   vibration trip and commissioning frequency measurement.
3. Geotechnical data per region (frost depth, typical soils) to fix the
   standard foundation drawings.
4. Detail design of the hinge frame, anchor cage, flanges and gin pole.
