# 12 kW Wind Turbine for Iceland: Nacelle Prototype P1 (Bench Article)

Status: **Draft, revision A, for review before release to manufacture** · 2026-11-02
Owner: Category 5 (Nacelle, shaft and bearings) with Category 4 (Generator) and 11 (Testing)
Builds on: [06 – Generator data freeze](06-generator-round2.md), [07 – Nacelle concept](07-nacelle-spindle-bearings.md),
[08 – Loads](08-load-verification.md), [11 – Control and safety](11-control-safety.md), [13 – Hub, pitch and yaw](13-hub-pitch-yaw.md)
Test plan: [15 – Nacelle bench test plan](15-nacelle-bench-test-plan.md)
Geometry and drawings: [`cad/nacelle_p1/`](../cad/nacelle_p1/) (one parametric source, `python3 build.py`)
Checks: [`analysis/nacelle/detail.py`](../analysis/nacelle/detail.py) → [`results/detail_summary.json`](../analysis/nacelle/results/detail_summary.json)

## Summary

P1 is the first physical nacelle: **spindle, main bearings, complete direct-drive
generator, brake, rotor lock, cooling, bedplate and yaw system**, built to be
driven on a test bench through a dummy hub. It is detailed to manufacturing
level: 17 drawing sheets (PDF set plus true-size DXF for CNC and laser
cutting), a 52-line bill of materials, and an assembly procedure.

| Item | P1 detail design |
|---|---|
| Scope | Everything between the hub flange and the tower top. Hub, pitch system, blades, slip ring and nacelle cover are not in P1 (pitch gets its own rig, doc 13 §11) |
| Main bearings | 2 × **32028 X** tapered roller (140 × 210 × 45), back-to-back, 240 mm spread, preload 2 to 4 kN by a KMT 27 precision nut. Static factor **≈ 10**, L10 **34 ×** the 2 × 20-year target even with 3 × the doc 07 fatigue load |
| Spindle | 42CrMo4+QT forging, Ø140/Ø90, **integral Ø400 flange** that carries both the bedplate and the stator. Static reserve ≥ 4.5 at notches, fatigue reserve 3.0 (conservative). 57 kg |
| Generator | Doc 06 frozen design, unchanged: 40 poles / 45 slots, Ø598 stator, 74 mm stack, N40UH, 2.0 mm gap. **Air gap budget 0.09 mm (RSS), 0.21 mm worst case**, against 0.20 mm allowed |
| Stator carrier | **Steel** (changed from aluminium): keeps the stack tight and centred from −40 °C to +130 °C. Bolted to the spindle flange |
| Cooling path | Finned insert in the spindle bore, **U-flow, two redundant fans**: **0.31 to 0.33 K/W** at 10 to 12 m/s, against ≤ 0.40 K/W (doc 06). Less margin than doc 07's estimate (0.17 to 0.25); measured first on the bench |
| Brake | Disc **Ø800** on the drum rear flange, 2 spring-applied calipers, **14.7 kN** clamp each for 8.7 kNm; 12 lock-pin holes |
| Bedplate | P1: **stress-relieved S355 weldment** with the same interfaces as the planned ductile iron casting |
| Mass | Drivetrain without hub **321 kg**, against ≈ 190 kg in the doc 07 budget for the same scope. Tower top would be **≈ 730 kg**, not 600. Mass reduction is a P2 task (§10) |
| Bench | Motor-gearbox drive with torque transducer, servo-hydraulic load unit on the dummy hub, shared DC bus. Test plan: [doc 15](15-nacelle-bench-test-plan.md) |

**Main findings**

1. **The concept holds up in detail.** Bearings, spindle, bolted joints, brake
   and lock all pass with large margins. Nothing in doc 07 needed a different
   arrangement.
2. **An aluminium stator carrier does not work for an outer-rotor machine in
   Iceland.** The aluminium sits inside the steel stack, so at −40 °C it loses
   about 0.3 mm of fit on Ø437 and the stator can move 0.15 to 0.3 mm in a
   2 mm gap. A steel carrier fixes this. It costs some cooling margin (§6)
   and about 28 kg.
3. **The cooling margin is smaller than doc 07 showed.** Heat must flow along
   the spindle from the flange, so the spindle works as a fin. The path still
   meets the 0.40 K/W target at full fan flow (0.33 K/W), but not at 5 m/s
   (0.41). That is why P1 has two redundant fans, and why the thermal test
   is early in the bench plan.
4. **P1 is heavy.** A machined and fabricated first article is about 130 kg
   heavier than the concept budget. This matters for the 24 m tower, which
   already had no frequency margin (doc 13 §8). The P2 cast and optimised
   parts must remove most of it, and the tower update should not be closed
   until P2 masses are known.

---

## 1. Purpose of P1 and what it must prove

P1 is a **bench article**, not a field turbine. It exists to find problems
cheaply and early, before tooling (casting patterns, stamping dies) and
before a field prototype (R11.1).

| Question P1 answers | Why it matters | Test (doc 15) |
|---|---|---|
| Does the generator meet doc 06: EMF, cogging, efficiency, short-circuit current, demagnetisation margin? | All electrical design is FEA only so far | T2, T3, T4 |
| Does the cooling path hold the winding below 130 °C at rated and 110 %? | Smallest margin in the design (§6) | T5 |
| Is the 2 mm air gap held under the design hub moment? | Rubbing or unbalanced pull would destroy the machine | T1, T6 |
| Do bearings, seals and grease run cool and tight at all speeds? | 20-year life, −40 °C seals | T4, T8 |
| Do brake, lock pin and yaw brake hold their design torques? | Safety functions (R5.2, R3.7) | T7 |
| Can it be built, assembled and taken apart safely with in-house methods? | Product goal: in-house manufacture | Build, T9 |

What P1 deliberately does **not** cover: blades and aerodynamics, pitch
system (own rig), slip ring, nacelle cover and IP54 sealing of the whole
nacelle, grid code testing, and −40 °C cold start of the full nacelle (a
cold-box test is an option, doc 15 T10).

## 2. Configuration and design decisions

| # | Decision | Reason | Effect |
|---|---|---|---|
| D1 | **Steel stator carrier** instead of AlSi7Mg (doc 07) | Al expands twice as much as the laminations: the fit changes by ±0.30 mm on Ø437 between −40 °C and +80 °C | +28 kg; cooling path +0.05 K/W |
| D2 | **Carrier bolted to an integral spindle flange**, not shrunk onto the spindle | The rear bearing housing sits between stator and spindle under the stack, so the carrier can only reach the spindle behind the rear bearing. A flange gives a stiff, removable joint with a large thermal contact face | Spindle needs a Ø400 flange (forging) |
| D3 | **Rear drum seal Ø400 on the flange OD** | Same reason as D2: the rotating rear cover must close around the stationary flange | 3.7 m/s seal speed, still low for HNBR lips |
| D4 | **Brake disc Ø800 at the drum flange ring** (doc 07: disc at r 0.30) | At r 0.30 the calipers clash with the drum; at r 0.37 they straddle the disc outside the drum | Clamp force 14.7 kN per caliper (was 21) |
| D5 | **32028 X bearings, cups P7, cones f6 (front) / j6 (rear)** | Rotating outer-ring load: cups need interference. Stationary inner ring: front cone must slide to set preload, like a vehicle wheel hub | Classic, easy to adjust and service |
| D6 | **U-flow cooling with 2 fans** | Air must enter and leave at the rear: the front of the spindle is inside the sealed hub | Air temperature rise counts; redundancy needed (§6) |
| D7 | **Fabricated drum and bedplate**, stress relieved, machined in one set-up | No pattern lead time; lets strain gauges and FEA set the P2 casting design | Heavier (§9) |
| D8 | **Dummy hub** NP1-600 instead of the ductile iron hub | The hub casting is not designed in detail yet (doc 13 §11); the bench needs a drive shaft and a load point anyway | Same interface: 12 × M16 10.9, PCD 400, Ø360 spigot |
| D9 | **Yaw system included** on a bench pedestal (5° wedge, spindle horizontal) | Yaw bearing, drives and slipping brake (R3.7) can be tested without a tower | Long-lead slewing ring (10 to 16 weeks) |

## 3. Layout and interfaces

Coordinates: x along the spindle axis, rearward from the rotor plane (mm).
The spindle axis is tilted 5° nose up; the yaw axis is 750 mm behind the
rotor centre; the rotor centre is 570 mm above the yaw bearing (drawing
NP1-300).

| x (mm) | Feature |
|---|---|
| 40 | Spindle front face (nose cap, future slip ring) |
| 52 to 80 | Thread M135×2, KMT 27 locknut |
| 80 to 97.5 | Spacer NP1-101 (seal counterface) |
| **97.5 to 142.5** | **Front bearing** (centre 120) |
| 200 | **Hub face**: 12 × M16 10.9 on PCD 400, Ø360 spigot |
| 200 to 220 | Drum hub web |
| **337.5 to 382.5** | **Rear bearing** (centre 360), shoulder Ø155 |
| 343 to 417 | Stator stack and magnets (centre 380), end windings ±22 |
| 415 to 440 | Stator carrier web |
| 435 to 451 | Brake disc |
| 440 to 470 | Spindle flange (Ø400) |
| 450 to 475 | Drum rear cover and Ø400 seal |
| 470 to 476 | Spigot Ø200 into the bedplate front plate |

The general arrangement is drawing **NP1-000**.

## 4. Parts

### 4.1 Spindle NP1-100

Open-die forging, 42CrMo4+QT, Rp0.2 ≥ 650 MPa, Charpy ≥ 27 J at −40 °C,
ultrasonic tested. Turned and ground; both bearing seats and the flange
faces are held to 0.01 to 0.02 mm run-out on the common axis. All
shoulders and fillets are rolled or shot peened. Two radial holes carry
PT100 sensors to the underside of each bearing cone (bench and field
measurement of bearing temperature).

| Section | Design moment | Peak stress (with Kt) | Reserve on yield (γm 1.1) |
|---|---|---|---|
| Rear seat Ø140 | 15.2 kNm | 68 MPa | 8.7 |
| Cone shoulder Ø155/140, R2.5 | 15.5 kNm | 132 MPa (Kt 1.9) | **4.5** |
| Flange fillet Ø150, R10 | 16.2 kNm | 82 MPa (Kt 1.45) | 7.2 |

The moments are conservative: doc 08's 9.8 kNm hub moment plus a 15 kN
shear at full lever arm. Fatigue reserve at the shoulder is 3.0 with 50 %
of the design moment as a 10⁹-cycle amplitude, which is far above the doc
08 fatigue loads.

### 4.2 Main bearings

| | Front | Rear |
|---|---|---|
| Bearing | 32028 X | 32028 X |
| Static design load (doc 08) | 41 kN | 44 kN |
| Static factor C0/P0 (C0 ≈ 430 kN) | **10.5** | **9.8** |
| Equivalent fatigue load (doc 07 × 3) | 9.0 kN | 2.8 kN |
| L10 | 95,000 million rev | very large |
| Required (2 × 20 years) | 2,800 million rev | 2,800 million rev |

The bearing is far bigger than the loads need, because the 90 mm bore for
cooling air and cables sets the spindle diameter (doc 07). Ratings are
typical catalogue values and must be confirmed with the chosen supplier.
P5 precision class (or the supplier's equivalent) is recommended because
bearing run-out enters the air gap budget directly.

**Preload:** cones pressed together by the KMT 27 nut to −0.02 to −0.05 mm
axial end play (2 to 4 kN preload). Measure end play with a dial gauge
before the last turn, then rolling torque without seals, and record both
for every unit. The bearing supplier gives the target rolling torque.

**Sealing:** grease is retained by HNBR lip seals in bolted covers on both
ends of the bearing housing; the front cover adds a V-ring. Each bearing
space has a grease nipple and a purge hole; automatic single-point
lubricators are used in the field (R14.1).

### 4.3 Rotor drum NP1-210

A welded and stress-relieved S355J2+N structure, machined in one set-up:
bearing housing tube (cup seats Ø210 P7), 20 mm hub web with tapped
M16 holes, 8 mm outer web, generator shell (13.8 mm yoke under the magnets,
6 mm elsewhere) and a rear flange ring carrying the rear cover, the brake
disc and the lock holes. Cup seats and magnet seat coaxial within 0.02 mm.
The finished rotor (drum, magnets, disc, dummy hub) is balanced to G2.5.

### 4.4 Stator

> **Update (doc 18, manufacturing):** the one-piece stack below cannot be
> wound (4 mm slot opening, 50 % copper fill needed). Doc 18 recommends a
> segmented stator (45 tooth segments in carrier dovetails) with the same
> magnetic shape; see [18 – Generator manufacturing](18-generator-manufacturing.md).

| Item | Specification |
|---|---|
| Laminations NP1-201 | M270-35A, 0.35 mm, with self-bonding varnish; ≈ 205 sheets; laser cut for P1 (the DXF is the cutting contour); OD run-out ≤ 0.05 after bonding; 3 key notches |
| Stack | 74.0 ± 0.2 mm, bonded on a Ø437.20 mandrel, stacking factor ≥ 0.97, each sheet rotated 24° |
| Carrier NP1-200 | Steel, stack shrunk on (0 to 0.05 mm interference), 3 keys for torque, clamped by the stainless front ring NP1-202 |
| Winding | Tooth coils, double layer, 45 coils, 15 per phase in series, star. **28 turns** per coil, **4 strands in hand of Ø1.55 mm** (7.55 mm², 3.07 A/mm² at 23.2 A) grade 2 enamel class 200. Turns are confirmed by measuring the EMF of the first finished stator (doc 06 said 27 to 28) |
| Insulation | Nomex-Kapton-Nomex slot liner 0.3 mm, glass-epoxy wedges, phase separators; VPI class H epoxy, then potted end windings (R4.2) |
| Sensors | 6 PT100 in slots (2 per phase, at the hottest predicted positions) for the doc 11 derate function, plus 2 spare |
| Leads | Through the two Ø28 holes in the carrier and spindle flange, sealed glands M32 into the bedplate |

### 4.5 Magnets NP1-220

160 radial arc segments (40 poles × 4 axial pieces) of N40UH, 7.70 mm,
arc 7.2°, NiCuNi plus epoxy coating, plus 8 spares. Each piece is flux
checked; batch demagnetisation curves at 20 to 150 °C are required from
the supplier. Magnets are bonded into the drum with a 150 °C structural
epoxy, located by a GRP comb, and covered by a 0.5 mm glass-epoxy layer.
The axial split into 4 pieces is a first choice; the magnet eddy loss study
(doc 06 next steps) may change it before ordering. **Magnets are the longest
lead item and should be ordered first.**

### 4.6 Brake, lock and yaw

| Item | P1 |
|---|---|
| Brake disc NP1-230 | C45E+N, Ø800/Ø640 × 16, 24 × M12 to the drum flange ring; pad track r 345 to 395 |
| Calipers | 2 spring-applied, hydraulically released, ≥ 15 kN clamp, −40 °C pads; the bracket drawing NP1-310 follows the supplier's caliper drawing |
| Energy | 74 kJ from 250 rpm raises the disc bulk temperature by only 7 K |
| Rotor lock NP1-320 | Ø25 pin through the disc into the flange ring; shear 54 MPa at 8.7 kNm; proximity switch "pin engaged" into the safety chain |
| Yaw | As doc 13 (D_pw 360 four-point slewing ring, 2 gearmotors, 2 spring-applied brake calipers with 8 kNm slip). **Change:** the yaw brake ring moves outside the gear (r ≈ 0.38 m) because r 0.24 m sits under the ring; the slip setting stays 8 kNm (≈ 14 kN clamp per caliper). The tower-top adapter NP1-400 is drawn when the slewing ring supplier drawing is in |

### 4.7 Bedplate NP1-300

Front plate 40 mm square to the spindle axis (Ø200 H7 spigot bore, 12 × M20
on PCD 350), bottom plate 40 mm as the yaw flange (16 × M16 on PCD 300),
side plates 20 mm, open top with bolted lid in P1. Front and bottom plates
are machined in one set-up on a 5° fixture.

## 5. Detail checks

All values from [`detail_summary.json`](../analysis/nacelle/results/detail_summary.json).

### 5.1 Bolted joints (minimum preload after tightening scatter, μ 0.12 thread, 90 % utilisation)

| Joint | Bolts | Torque | Slip factor | Separation factor |
|---|---|---|---|---|
| Spindle flange to bedplate | 12 × M20 10.9, PCD 350 | 540 Nm | 9.3 | 4.8 (SLM tilt + parked thrust) |
| Stator carrier to flange (thermal paste, μ 0.1) | 12 × M12 10.9, PCD 240 + 2 dowels | 110 Nm | 1.9 at 4 × rated torque | n/a |
| Hub to drum (doc 13) | 12 × M16 10.9, PCD 400 | 280 Nm | 2.4 at SLM G 28.4 kNm | 9.5 |
| Brake disc to drum | 24 × M12 10.9, PCD 662 | 110 Nm | 2.5 at 28.4 kNm | n/a |

The carrier joint uses dowels as a second load path, because thermal paste
lowers friction. Tightening torques must be checked against the fastener
supplier's friction data (hot-dip galvanised bolts differ).

### 5.2 Air gap budget (radial, mm)

| Contribution | mm |
|---|---|
| Bearing run-out (P5, preloaded) | 0.010 |
| Spindle seats to flange | 0.010 |
| Carrier seat to bolting face | 0.020 |
| Stack OD to bore (laser cut, bonded) | 0.050 |
| Drum cup seats to magnet seat | 0.020 |
| Magnet thickness and bond line | 0.050 |
| Deflection at 9.8 kNm (drum tilt vs stator) | 0.040 |
| Magnetic pull amplification | 0.005 |
| **Worst case sum / RSS** | **0.205 / 0.087** (limit 0.20) |

The statistical value has more than 2 × margin. Stack run-out and magnet
bond line are the largest items, so both get 100 % inspection.

### 5.3 Fits

| Fit | Tolerance | Result |
|---|---|---|
| Cups in drum | Ø210 P7 | 0.006 to 0.079 interference (rotating outer-ring load) |
| Front cone on spindle | Ø140 f6 | 0.018 to 0.068 clearance (slides to set preload; point load) |
| Rear cone on spindle | Ø140 j6 | transition, against shoulder Ø155 |
| Stack on carrier | Ø437.25 +0.05/+0.03 vs Ø437.20 +0.03/0 | 0 to 0.05 interference, steel on steel |
| Cooling insert in bore | Ø90 H8 / +0.06/+0.02 | 0.02 to 0.06 interference (Al tightens when hot) |

## 6. Cooling path

Heat path: stack → steel carrier (rim, 25 mm web) → bolted face with
Al-filled paste → spindle flange → spindle tube, which acts as a fin cooled
by the finned insert. The insert has 16 cells: 8 carry air forward, the
front plenum cap turns it, and 8 return it to the rear manifold. A Ø34
central tube is the cable conduit to the nose.

| Air speed in cells | Flow | Δp | R path | R incl. air heating | Target |
|---|---|---|---|---|---|
| 12 m/s (design point) | 69 m³/h | 310 Pa | 0.29 K/W | **0.31 K/W** | ≤ 0.40 ✅ |
| 10 m/s | 57 m³/h | 215 Pa | 0.30 K/W | 0.33 K/W | ✅ |
| 7 m/s (one fan failed) | 40 m³/h | 105 Pa | 0.33 K/W | 0.37 K/W | ✅ |
| 5 m/s | 29 m³/h | 54 Pa | 0.36 K/W | 0.41 K/W | ❌ marginal |

The largest single elements are the spindle fin (≈ 0.16 K/W) and the
spindle flange (0.08 K/W). **Fans:** two EC radial fans of 70 m³/h at
350 Pa each, in parallel with non-return flaps, so one fan alone gives
about 7 m/s. If both fail, doc 11's derate on winding temperature protects
the generator. The air enters through a G4 and ash pre-filter. These
values come from a 1D fin model; **the bench thermal test (doc 15, T5)
measures the real resistance** before any decision on the P2 carrier.

## 7. Manufacturing and assembly

### 7.1 Manufacturing route and lead times

| Part group | Route | Lead time (estimate) |
|---|---|---|
| Magnets (bought) | Order after eddy-loss check | **8 to 12 weeks** |
| Yaw slewing ring, brake calipers (bought) | Supplier drawings define NP1-310 and NP1-400 | **10 to 16 weeks** |
| Spindle forging | Forge shop, then in-house turning and grinding | 6 to 8 weeks |
| Drum and bedplate weldments | In-house rolling, welding, stress relief, boring mill | 6 to 8 weeks |
| Laminations | Laser cut, bond in fixture NP1-T03 | 3 to 6 weeks |
| Stator winding, VPI | In-house (tooth coil winder, VPI tank) | 3 weeks after stack |
| Bench rig (drive, load unit, pedestal) | Mostly bought plus simple weldments | 6 to 10 weeks, in parallel |

With orders placed in week 1, P1 assembly can start around **week 12 to 14**
and the bench test campaign runs about **10 weeks** (doc 15).

### 7.2 Assembly sequence (summary)

1. **Stator:** cool the carrier, slide the bonded stack on against the rear
   stop, fit keys, clamp ring. Insert slot liners, wind and insert coils,
   connect, test (resistance, insulation, surge), VPI, pot end windings,
   test again.
2. **Rotor:** press both cups into the drum (cups cooled, drum warm). Bond
   magnets pole by pole with the insertion jig NP1-T02 (never by hand near
   steel), alternating N and S, check each pole with a gaussmeter, then the
   glass-epoxy cover layer. Fit the brake disc. Balance later with the hub.
3. **Spindle:** shrink the cooling insert into the bore, fit PT100s, press the
   rear cone against the shoulder, fit the rear seal cover seal surface
   check.
4. **Stator on spindle:** bolt the carrier to the flange with paste, dowels
   and 12 × M12; route leads through the flange.
5. **Drum on spindle (magnet hazard step):** spindle vertical, nose up, guide
   tool NP1-T01 on the nose, drum lowered by screw jack with four G10
   feelers in the gap, until the rear cup seats on the rear cone.
6. **Front bearing:** front cone, spacer, KMT 27 nut; set end play −0.02 to
   −0.05 mm; record rolling torque; fit seal covers, grease.
7. **Rear cover and seal**, breather, then measure the air gap at 4 × 90°
   with feelers through the inspection port.
8. **Bedplate:** bolt the spindle flange (12 × M20, 540 Nm), mount calipers,
   lock pin, fan manifold, hydraulic unit, yaw bearing and drives.
9. **Bench:** set on the pedestal and wedge, bolt the dummy hub, couple the
   drive, balance the rotor in place (G2.5).

**Safety:** the assembled rotor has about 27 kN of radial magnetic
attraction in total, and 1.9 kN per mm of off-centre position. Magnet steps
need a written procedure, trained people, non-magnetic tools and a cleared
zone (pacemaker warning).

## 8. Drawings

Generated by [`cad/nacelle_p1/build.py`](../cad/nacelle_p1/build.py) from
[`geometry.py`](../cad/nacelle_p1/geometry.py). PDF set:
[`NP1-drawing-set.pdf`](../cad/nacelle_p1/out/NP1-drawing-set.pdf); single
sheets in `out/pdf/`, true-size DXF in `out/dxf/` (layer OUTLINE is the
cutting or turning contour).

| Drawing | Title | Material | Mass |
|---|---|---|---|
| NP1-000 | General arrangement, drivetrain section | | ≈ 320 kg |
| NP1-100 | Spindle | 42CrMo4+QT forging | 56.7 kg |
| NP1-101 | Front spacer | 42CrMo4, induction hardened | 0.6 kg |
| NP1-110 | Cooling insert (finned extrusion) | 6082-T6 | 2.6 kg |
| NP1-200 | Stator carrier | S355J2+N | 40.6 kg |
| NP1-201 | Stator lamination (cutting contour) | M270-35A bonded | 48.0 kg stack |
| NP1-202 | Stator clamp ring | 1.4404 | 2.2 kg |
| NP1-210 | Rotor drum weldment | S355J2+N | 96.0 kg |
| NP1-211 | Main bearing seal covers | S355J2 | 4.1 kg |
| NP1-212 | Drum rear cover with seal carrier | 5083-H111 | 7.3 kg |
| NP1-220 | Magnet segment (purchase drawing) | N40UH | 41 g each |
| NP1-230 | Brake disc and lock holes | C45E+N | 22.7 kg |
| NP1-300 | Bedplate weldment | S355J2+N | ≈ 150 kg |
| NP1-320 | Rotor lock pin | 42CrMo4+QT | ≈ 4 kg |
| NP1-600 | Bench dummy hub | S355J2+N | ≈ 75 kg |
| NP1-620 | Bench layout | | |
| NP1-T01 | Drum assembly guide tool | | ≈ 30 kg |

Still to draw, after supplier data: NP1-310 caliper brackets, NP1-400
tower-top adapter, NP1-610 load unit frame, the cooling manifold and the
hydraulic layout. Every sheet is marked **"not checked"**: a second engineer
should check each drawing against this document before release, and
the machine shop should review tolerances against their equipment.

## 9. Bill of materials and mass

Full list: [`cad/nacelle_p1/bom.csv`](../cad/nacelle_p1/bom.csv) (52 lines:
part, quantity, material, make or buy, source, mass, lead time).

| Group | P1 mass | Doc 07 budget |
|---|---|---|
| Spindle | 57 kg | 45 kg |
| Drum, covers, disc, magnets, bearings | 147 kg | 60 kg |
| Stator (carrier, core, winding, ring) | 115 kg | 75 kg |
| Insert and spacer | 3 kg | (misc) |
| **Drivetrain without hub** | **321 kg** | **≈ 190 kg** |
| Bedplate (P1 weldment) | ≈ 150 kg | 70 kg |

The difference comes from conservative fabricated sections (drum housing,
webs and flange ring), the steel carrier, a larger brake disc, and a
generator active mass that is a little above the doc 04 estimate. For the
field turbine this matters: with a 200 kg hub and pitch system (doc 13), a
P1-weight nacelle gives about 730 kg tower top. Doc 13 already showed the
24 m tower has no frequency margin at 600 kg.

## 10. Open points and risks

| # | Item | Plan |
|---|---|---|
| 1 | Tower-top mass 130 to 250 kg over budget if P1 weights carry to the product | P2: cast drum with ribs, FEA-optimised carrier and bedplate in EN-GJS-400-18U-LT, aluminium where thermal expansion allows; target ≤ 230 kg drivetrain. Hold the tower update until P2 masses are known |
| 2 | Cooling margin (0.31 to 0.33 K/W vs 0.40) | Bench T5 first; options if short: bigger insert area, carrier web 35 mm, heat pipe in the web, more fan flow |
| 3 | Magnet segmentation not yet confirmed by an eddy loss calculation | Do before ordering magnets (doc 06 next step 1) |
| 4 | Turns per coil 27 or 28 | Measure EMF of the first stator; spare coils wound with 27 |
| 5 | Bearing ratings and run-out class | Supplier enquiry with the loads in §4.2 |
| 6 | Yaw bearing and caliper interfaces | Supplier drawings, then NP1-310 and NP1-400 |
| 7 | Drum and bedplate stiffness only checked by hand | FEA of drum (ovalisation under unbalanced pull, web stiffness) before release; strain gauges on P1 |
| 8 | Drawings not checked | Independent drawing check before release |

## 11. Next steps

1. Review this document and the drawing set, then release long-lead orders:
   magnets (after the eddy-loss check), slewing ring, calipers, bearings,
   spindle forging.
2. Drum and bedplate FEA (open point 7) and the remaining drawings.
3. Build the bench in parallel with the nacelle (doc 15, section 2).
4. Build, then run the bench campaign in doc 15.
