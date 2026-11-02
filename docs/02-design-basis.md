# 12 kW Wind Turbine for Iceland: Design Basis and Requirements

Status: **Draft, revision 1** · 2026-11-01
Owner: Category 1 (Systems engineering and requirements)
Builds on: [01 – Project categories](01-project-categories.md)

This document fixes the external conditions the turbine must survive, the
load cases it is designed against, and the top-level requirements for every
category. Every other category designs against this document. Values marked
**(TBC)** are to be confirmed by the data work in section 7.

**Guiding rule (Martin, 2026-11-01): quality first, no shortcuts.** Where
the standard offers a simplified route and a more rigorous route, this
design basis takes the rigorous one.

---

## 1. Standards baseline

| Area | Standard | Use |
|---|---|---|
| Small wind turbine design | **IEC 61400-2:2013** (ed. 3) | Primary design standard, type certification |
| Large turbine methods | IEC 61400-1:2019 (ed. 4) | Borrowed where more rigorous than 61400-2: full aeroelastic load cases, cold climate and ice, earthquake (informative annexes) |
| Cold climate | IEA Wind TCP Task 19 recommended practices | Ice classification, ice loads, ice throw |
| Power performance | IEC 61400-12-1 | Power curve measurement |
| Acoustic noise | IEC 61400-11 | Noise measurement |
| Duration and safety tests | IEC 61400-2 type test clauses | Duration, safety and function, mechanical loads |
| Lightning | IEC 61400-24 | Lightning protection |
| Structures | Eurocodes EN 1990, 1991-1-4 (wind), 1993 (steel), 1997 (geotech), 1998 (seismic), all with Icelandic national annexes (ÍST EN) | Tower and foundation |
| Corrosion | ISO 12944 (2017/2018), ISO 9223 | Coating systems, corrosivity class |
| Grid connection | EN 50549-1 | Grid-tie power module |
| Machinery and electrical | EU Machinery Regulation 2023/1230, Low Voltage Directive, EMC Directive (EN 61000-6-2, -6-4) | CE marking |
| Quality | ISO 9001, EN ISO 3834 (welding) | Production |

**Rigour choices** (no shortcuts):
- Loads are calculated with **full aeroelastic simulation** (OpenFAST or
  QBlade), not only the IEC 61400-2 Simplified Load Model. The Simplified
  Load Model is run in parallel as a cross-check.
- Ice, seismic and fault cases from IEC 61400-1 are added even though
  IEC 61400-2 does not require all of them.
- Component strength is verified by **both** analysis and full-scale test
  (blades, hub, main shaft, tower top).

---

## 2. What the data says about Icelandic conditions

| Topic | Finding | Source |
|---|---|---|
| Extreme wind on mountains | Icelandic Met Office measured 72 m/s on Ásgarðsfjall in Kerlingarfjöll (Jan 2018), described as close to the national record | [Iceland Monitor, 2018](https://icelandmonitor.mbl.is/news/nature_and_travel/2018/01/09/winds_of_72_metres_per_second_in_icelandic_highland/) |
| Extreme wind at a coastal station | 48.9 m/s 10-minute mean at Stórhöfði, Vestmannaeyjar (9 Jan 1990); gusts 38 to 53 m/s across west and north Iceland (3 Feb 1991) | [Veðurstofa Íslands report 98014](https://www.vedur.is/media/vedurstofan/utgafa/greinargerdir/1998/98014.pdf) |
| Gust behaviour | Local terrain affects extreme gusts more than mean wind; extreme value statistics exist for 61 stations | [IMO, EGU 2015](https://meetingorganizer.copernicus.org/EGU2015/EGU2015-6428.pdf) |
| Lowest temperature | −38 °C at Grímsstaðir and Möðrudalur, 21 Jan 1918 | [Grímsstaðir](https://en.wikipedia.org/wiki/Gr%C3%ADmssta%C3%B0ir) |
| Icing type | Mostly in-cloud (rime) icing; wet-snow icing also occurs; freezing rain is very rare. Landsnet has run ice test spans at 61 sites since 1972 | [IWAIS 2022 paper 086](https://www.mcgill.ca/iwais2022/files/iwais2022/paperid086.pdf) |
| Wet snow with wind | Icelandic wet-snow events occur at 10 to 25 m/s wind (much windier than in continental Europe), giving dense (~700 kg/m³) accretion | [NHESS 14, 3031 (2014)](https://nhess.copernicus.org/articles/14/3031/2014/nhess-14-3031-2014.pdf) |
| Seismic | Site study near Húsavík (Tjörnes fracture zone): 0.44 g horizontal and 0.27 g vertical peak ground acceleration, 475-year return period, rock | [Skipulagsstofnun, Bakki EIA appendix 14](https://skipulag.is/media/attachments/Umhverfismat/813/vidauki%2014_%20earthquake%20hazard.pdf) |

**Interpretation:**
- The 72 m/s value is from an exposed mountain summit. No customer will put
  a 12 kW turbine on a mountain summit, but farms below mountains get strong
  downslope gusts. The design must cover lowland and coastal sites in full and
  define a clear site-suitability check for exposed terrain (section 3.3).
- Icelandic wet snow comes **with** strong wind, so ice and high-wind load
  cases must be combined, not treated separately.
- Seismic loads near 0.5 g are relevant in the South Iceland Seismic Zone and
  the Tjörnes fracture zone; the tower top mass makes this a real load case.

---

## 3. External conditions (design envelope)

### 3.1 Wind: IEC 61400-2 Class S definition

IEC Class I (the strongest standard class) has V_ref = 50 m/s. Icelandic
coastal data already approach this, so the turbine is designed to a
**Class S** with margin above Class I.

| Parameter | Symbol | IEC Class I | **This design (Class S)** |
|---|---|---|---|
| Reference wind speed (10-min mean, 50-year, hub height) | V_ref | 50 m/s | **55 m/s** (TBC) |
| Extreme 3 s gust, 50-year | V_e50 | 70 m/s | **77 m/s** (1.4 × V_ref) |
| Extreme 3 s gust, 1-year | V_e1 | 52.5 m/s | **58 m/s** (0.75 × V_e50) |
| Annual average wind speed at hub height | V_ave | 10 m/s | **10 m/s** (fatigue design) |
| Turbulence intensity at 15 m/s | I_15 | 0.18 | **0.20** (TBC; raised for terrain-induced gusts) |
| Wind shear exponent | α | 0.2 | **0.2**, plus check at 0.0 and 0.4 |
| Inflow angle (vertical) | | ±8° | **±8°** (sloping terrain) |
| Extreme direction change | | IEC model | **IEC model** with raised turbulence |

### 3.2 Other environmental conditions

| Parameter | Design value |
|---|---|
| Operating temperature | −30 °C to +30 °C |
| Survival temperature (parked, no power) | **−40 °C** (record −38 °C plus margin) |
| Start-up temperature (cold start of electronics and pitch) | −30 °C, with heaters allowed to pre-warm |
| Air density | 1.20 to 1.35 kg/m³ (power curve at 1.225 and 1.30 reported) |
| Relative humidity | Up to 100 %, condensing, frequent freeze–thaw |
| Corrosivity | **ISO 12944 C5, durability "very high" (> 25 years)** for all external surfaces |
| Geothermal gases | H₂S exposure for electronics and copper near geothermal areas: conformal coating and sealed enclosures |
| Erosion | Volcanic ash and sand at storm wind speeds; blade leading edges, seals and nacelle openings |
| UV | High summer UV for 20 years; all polymers UV-stabilised |
| Rain | Wind-driven horizontal rain; IP rating per section 6.8 |
| Snow | Nacelle and ground enclosures snow-load and drift tolerant; buried ground cabinets not allowed |
| Lightning | IEC 61400-24 **LPL I** (highest level, even though Iceland has few strikes) |
| Seismic | Peak ground acceleration up to **0.5 g** horizontal (TBC from ÍST EN 1998-1 national annex zone map) |
| Ice | See section 3.4 |

### 3.3 Site suitability

The product is certified for any site where a simple site check confirms:
V_ref ≤ 55 m/s, I_15 ≤ 0.20 and inflow ≤ 8°. The installation manual will
include a site check method using Met Office data and terrain category.
Sites outside this (mountain summits, crests directly in downslope wind
paths) need a site-specific load assessment before installation.

### 3.4 Icing

| Parameter | Design value |
|---|---|
| IEA ice class | Design for the most severe class expected at highland sites (TBC from Landsnet test span data and IMO icing maps) |
| Ice types | Rime (in-cloud), wet snow with 10 to 25 m/s wind, freezing rain (rare, but covered) |
| Operation | Turbine stops automatically when ice is detected unless the cold climate package (blade heating) is installed |
| Ice loads | Ice mass on blades per the IEC 61400-1 cold climate annex, applied to all blades (symmetric) and one blade (imbalance), both operating and parked |
| Ice throw | Safety distance shown in the installation manual: 1.5 × (rotor diameter + hub height) while operating with ice, and ice fall zone while parked |

---

## 4. Turbine configuration (fixed for this phase)

| Item | Value |
|---|---|
| Type | Horizontal axis, upwind, 3 blades |
| Rated electrical power | 12 kW at the output terminals of the power module |
| Rotor diameter | **7.5 m** (chosen in the rotor concept study, doc 03) |
| Regulation | **Active pitch**, three independent electric pitch drives with supercapacitor stores (doc 13), with fail-safe return to feather on any power or controller loss |
| Drivetrain | Direct drive, no gearbox |
| Generator | Permanent magnet synchronous, NdFeB magnets |
| Yaw | Active yaw: slewing ring, two gearmotors, spring-applied brake with controlled slip at 8 kNm (doc 13) |
| Brake | Mechanical brake able to stop the rotor from overspeed alone, independent of pitch |
| Tower | Tilt-up freestanding tapered steel monopole (doc 09), 18 m and 24 m hub height options |
| Design life | 20 years, with no structural component replacement |

---

## 5. Design load cases

The design load cases follow IEC 61400-2 with additions from IEC 61400-1.
All are simulated aeroelastically. "Ice" means the IEC 61400-1 cold climate ice mass applied.

| DLC | Situation | Wind condition | Purpose |
|---|---|---|---|
| 1.1 | Power production | Normal turbulence, V_in to V_out | Fatigue |
| 1.2 | Power production | Extreme turbulence | Ultimate |
| 1.3 | Power production | Extreme operating gust, extreme direction change, extreme shear | Ultimate |
| 1.4 | Power production with ice on all blades | Normal turbulence | Fatigue and ultimate |
| 1.5 | Power production with ice on one blade | Normal turbulence | Ultimate, imbalance |
| 2.1 | Power production + control fault (pitch runaway, sensor fault) | Normal turbulence | Ultimate |
| 2.2 | Power production + loss of grid / load | Extreme operating gust | Ultimate |
| 2.3 | Power production + one blade pitch stuck | Normal turbulence | Ultimate |
| 3.1 | Start-up | Gusts at start-up | Fatigue and ultimate |
| 4.1 | Normal shutdown | Extreme operating gust | Ultimate |
| 5.1 | Emergency shutdown (pitch to feather + brake) | Extreme operating gust at rated and cut-out | Ultimate |
| 6.1 | Parked, idling | V_e50 = 77 m/s, all yaw errors | Ultimate |
| 6.2 | Parked, idling, with grid loss (no active yaw) | V_e50, yaw error ±180° | Ultimate |
| 6.3 | Parked, idling | V_e1 with large yaw error | Ultimate |
| 6.4 | Parked | Normal turbulence below V_ref | Fatigue |
| 6.5 | Parked with ice on all blades | V_e1 | Ultimate (combined ice and wind, typical of Icelandic wet snow) |
| 7.1 | Parked + fault (one blade not feathered) | V_e1 | Ultimate |
| 8.1 | Tilt-up / lowering | 15 m/s gusts (installation wind limit, TBC) | Ultimate for tower, hinge, gin pole |
| 8.2 | Transport and handling | Accelerations from road transport | Ultimate |
| 9.1 | Earthquake during operation and parked | Response spectrum per EN 1998 / IEC 61400-1 earthquake annex + operational wind | Ultimate |

**Safety factors:** partial safety factors per IEC 61400-2 for the chosen
route, with no reduction claimed from testing. Material factors per the
relevant Eurocode or IEC 61400-2 material clause, whichever is stricter.

---

## 6. Requirements by category

Each requirement has an ID for traceability. "Shall" is mandatory, "should"
is a target to be confirmed by design studies.

### 6.1 Systems engineering (cat. 1)
- **R1.1** The turbine shall meet IEC 61400-2 type certification for the
  Class S parameters in section 3.1.
- **R1.2** Every requirement in this section shall be traceable to a
  verification method (analysis, test, inspection) and a test report.
- **R1.3** A load and mass budget shall be maintained for rotor, nacelle
  and tower top.

### 6.2 Rotor and blades (cat. 2)
- **R2.1** Rated power shall be reached at a wind speed of **11 m/s or
  lower** (TBC by rotor study), air density 1.225 kg/m³.
- **R2.2** Cut-in wind speed should be **3 m/s or lower**.
- **R2.3** Maximum tip speed shall be limited to keep noise within the
  target in R2.7 and leading edge erosion within the LEP rating; working
  limit 75 m/s.
- **R2.4** Blades shall pass full-scale static test to the design ultimate
  load × test factors and fatigue test to 20-year equivalent loads.
- **R2.5** Leading edge protection shall resist volcanic ash and rain
  erosion for at least 10 years before repair (test method TBC: rain erosion
  per DNV-RP-0171, solid particle erosion per ASTM G76).
- **R2.6** Blade set shall be mass- and moment-balanced; rotor imbalance
  limit to be set from DLC 1.5.
- **R2.7** Acoustic noise should not exceed **45 dB(A) at 60 m** from the
  tower at 8 m/s (TBC against Icelandic noise regulation).
- **R2.8** Cold climate package: blade heating shall prevent ice build-up
  in operation under the design ice class.

### 6.3 Hub, pitch and yaw (cat. 3)
- **R3.1** On any fault, the pitch system shall move all blades at
  **30 °/s** (45° within 1.5 s) to full feather, using stored energy (spring
  or supercapacitor), without grid or controller power. Normal pitch rate
  shall be at least **15 °/s**. (Revised after the rotor study, doc 03, and
  confirmed by load simulation, doc 08.)
- **R3.1a** Design overspeed is **250 rpm** (140 % of rated). The overspeed
  trip is set at 210 rpm; on an emergency stop the converter applies up to
  1.25 × rated torque while the blades feather (doc 08).
- **R3.2** Pitch and yaw mechanisms shall operate at −30 °C and survive
  −40 °C; lubricants and seals rated accordingly.
- **R3.3** Pitch bearings and pitch drive shall be protected against ice
  and driven snow ingress.
- **R3.4** Yaw system shall keep the rotor facing the wind within
  ±10° average error in turbulent wind, and shall be able to hold or
  free-yaw safely during grid loss (DLC 6.2).
- **R3.5** The pitch bearing and grease shall be qualified for oscillating
  duty: 2 million revolutions and 230 million reversals in 20 years, with
  long dwells at the fine-pitch stop under rotating root moment. The
  controller shall make a 0 → 10° lubrication sweep after every 24 h at fine
  pitch (doc 13).
- **R3.6** Each pitch axis shall feather on loss of the safety chain, of
  slip-ring power or of its watchdog, using only its own stored energy, and
  shall report its stored energy for the weekly test (doc 13).
- **R3.7** The yaw brake shall slip above 8 kNm and the yaw drives shall not
  be self-locking, so a side gust cannot overload the gear train or the
  tower top (doc 13).

### 6.4 Generator (cat. 4)
- **R4.1** Generator shall deliver rated power continuously at rated speed
  with winding temperature within insulation class F limits, evaluated at
  class B rise (one class margin).
- **R4.2** Insulation system shall be fully vacuum-pressure impregnated or
  potted; windings shall pass humidity and salt mist tests.
- **R4.3** NdFeB magnets shall be fully coated and encapsulated;
  demagnetisation shall not occur in a terminal short circuit at −30 °C
  or at maximum operating temperature.
- **R4.4** Anti-condensation heating or a sealed design shall prevent
  internal condensation when parked.
- **R4.5** Generator efficiency should be **≥ 93 %** at rated power.

### 6.5 Nacelle, shaft and bearings (cat. 5)
- **R5.1** Main bearings shall have an L10 life of at least **2 × design
  life** under the DLC 1.1 load spectrum.
- **R5.2** Mechanical brake shall stop the rotor from the maximum overspeed
  (pitch failed) and hold it parked at V_e50.
- **R5.3** Nacelle shall be sealed to IP54 overall, with labyrinth seals on
  rotating parts and drained low points.
- **R5.4** Service access to all inspection points shall be possible with
  the turbine lowered.

### 6.6 Tower and foundation (cat. 6)
- **R6.1** Tower and foundation shall be designed to the DLC envelope,
  Eurocode 3 and 7 with Icelandic national annexes, and seismic loads per
  Eurocode 8.
- **R6.2** (Revised in doc 09: the 1P and 3P bands overlap, so no tower can
  clear both.) The tower first natural frequency shall lie between 1.1 × 1P
  at minimum operating speed and 3P at minimum operating speed / 1.1
  (0.73 to 1.82 Hz) in all foundation and ice conditions. The controller
  shall exclude rotor speeds within ±10 % of the speed where 1P equals the
  tower frequency, and the tower frequency shall be measured at
  commissioning to set that zone.
- **R6.3** Foundation designs shall be provided for: rock (rock anchors),
  firm soil, soft volcanic soil, and frost-susceptible ground (frost depth
  per local data).
- **R6.4** Tilt-up shall be possible with a gin pole and winch, no crane.
- **R6.5** All steel shall be hot-dip galvanized (EN ISO 1461) plus a duplex
  paint system meeting C5 very high durability.
- **R6.6** (New, doc 09.) Residual rotor imbalance shall not exceed
  0.2 kg·m (ISO 21940-11 G6.3, blades supplied as sets matched by static
  moment within 0.5 %). A vibration trip on the side-side 1P amplitude shall
  stop the turbine at the equivalent of 0.5 kg·m.

### 6.7 Power electronics and power modules (cat. 7)
- **R7.1** One common front end (rectifier, DC link, MPPT, protection) shall
  serve all power modules.
- **R7.2** Power modules: grid-tie (1-phase and 3-phase, 230/400 V 50 Hz,
  EN 50549-1), battery charger (48 V class), heating (resistive), and hybrid
  priority logic.
- **R7.3** The system shall always have a dump load able to absorb full
  rated power for the time needed to feather and stop the rotor, with no
  grid present.
- **R7.4** Electronics shall start at −30 °C (with self-heating) and survive
  −40 °C unpowered.
- **R7.5** Peak efficiency of front end plus grid-tie module should be
  **≥ 95 %**.
- **R7.6** EMC per EN 61000-6-2 (immunity) and EN 61000-6-4 (emission).

### 6.8 Control, safety and monitoring (cat. 8)
- **R8.1** Safety system shall be independent of the main controller
  (separate hardware, fail-safe), triggering pitch to feather and brake on
  overspeed, excess vibration, controller watchdog or manual stop.
- **R8.2** Control strategy: rated power to 25 m/s, then **gradual power
  reduction** up to a storm cut-out (TBC, around 30 m/s) instead of a hard
  stop, to harvest Iceland's frequent high winds and reduce stop/start
  cycles.
- **R8.3** Ice detection by at least two independent methods (for example
  power curve deviation and nacelle vibration, plus temperature/humidity).
- **R8.4** Remote monitoring over mobile network with local data logging of
  at least 12 months when connectivity is lost.
- **R8.5** Safety-related control functions shall be developed per
  ISO 13849 or IEC 61508 (performance level / SIL from risk assessment).
- **R8.6** Enclosure ratings: nacelle electronics IP66, ground cabinets IP55
  with heating and condensation drain.

### 6.9 Materials, corrosion and environment (cat. 9)
- **R9.1** All external materials and coatings shall meet ISO 12944 C5,
  very high durability, without repainting for 15 years minimum.
- **R9.2** Fasteners shall be hot-dip galvanized (8.8/10.9) or stainless
  A4 with galvanic isolation; no zinc-flake-only fasteners outside.
- **R9.3** All PCBs shall be conformally coated against H₂S, salt and
  condensation.
- **R9.4** All polymers and composites shall be UV-stabilised for 20 years.
- **R9.5** Materials shall keep required toughness at −40 °C (steel impact
  tested at −40 °C, for example S355 grade with suitable Charpy rating,
  TBC).

### 6.10 Manufacturing and quality (cat. 10)
- **R10.1** Production under ISO 9001 with full serial-number traceability
  of all structural and electrical components.
- **R10.2** Welding to EN ISO 3834-2 (comprehensive quality requirements)
  with qualified welders and procedures.
- **R10.3** Every turbine shall pass an end-of-line test (generator, pitch,
  safety chain, power electronics) before shipping.

### 6.11 Testing (cat. 11)
- **R11.1** Prototype shall complete at least **one full Icelandic winter**
  of field testing at an exposed site before release.
- **R11.2** Type tests: power performance (61400-12-1), noise (61400-11),
  duration test, safety and function, mechanical loads.
- **R11.3** Climate chamber testing at −40 °C for electronics, pitch system
  and lubricants before field installation.

### 6.12 Certification (cat. 12)
- **R12.1** Type certificate to IEC 61400-2 from an accredited
  certification body.
- **R12.2** CE marking with full technical file; documentation in Icelandic
  and English.

### 6.13 Installation and service (cat. 14)
- **R14.1** Planned maintenance interval of **12 months** or longer, done in
  summer.
- **R14.2** All replaceable parts shall be replaceable with the turbine
  lowered, using hand tools and a winch.
- **R14.3** Availability target **≥ 97 %**.

---

## 7. Data still needed

| Data | Source | Used for |
|---|---|---|
| 50-year 10-min and gust extremes per station | Icelandic Met Office (Veðurstofa Íslands) station records and extreme value analysis | Confirm V_ref = 55 m/s, site check method |
| Turbulence intensity at farm and coastal sites | IMO 10-min and gust records, own measurement mast | Confirm I_15 = 0.20 |
| Ice loads and frequency | Landsnet test span reports, IMO icing studies | Set ice class and ice mass parameters |
| Seismic zone map | ÍST EN 1998-1 national annex | Confirm 0.5 g |
| Frost depth and soil types | Vegagerðin, geotechnical data | Foundation designs |
| Noise limits | Icelandic noise regulation | Confirm R2.7 |
| Grid connection rules | RARIK, HS Veitur, Veitur, Orkubú Vestfjarða | Grid-tie module |

## 8. Next steps

1. Request Met Office extreme wind and turbulence data and Landsnet icing
   data (section 7).
2. Rotor concept study: diameter 7 to 8 m, aerofoil family, tip speed,
   pitch range (category 2 and 3).
3. Generator concept study: axial flux vs outer-rotor radial flux at the
   rotor speed from step 2 (category 4).
4. First aeroelastic model and load run on DLC 1.1, 6.1 and 6.5 to size the
   rotor and tower.
