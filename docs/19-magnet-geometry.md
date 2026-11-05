# 12 kW Wind Turbine for Iceland: Final Magnet Geometry (P1 generator)

Status: **Rev A, proposed for approval** · 2026-11-05  
Owner: Category 4 (Generator) with 10 (Manufacturing and quality)  
Builds on: [06 – Generator round 2](06-generator-round2.md) (frozen electromagnetic design), [14 – Nacelle prototype P1](14-nacelle-prototype-p1.md) (§4.5 magnets, §5.2 air gap budget), [18 – Generator manufacturing](18-generator-manufacturing.md) (§4.3 magnet purchase spec, §6.4 to §6.8 rotor build)  
Analysis: [`analysis/generator/magnets.py`](../analysis/generator/magnets.py) → [`magnets_summary.json`](../analysis/generator/results/magnets_summary.json) (2D nonlinear FEA of 7 magnet shapes, magnet eddy loss, demagnetisation, forces, tolerance scatter)  
Geometry: [`cad/generator_mfg/magnet_geom.py`](../cad/generator_mfg/magnet_geom.py) (all magnet, seat and comb dimensions in this document come from here)  
Pictures: [`cad/generator_mfg/figures_magnets.py`](../cad/generator_mfg/figures_magnets.py) → detail drawings M01 to M10 and isometric views MI01 to MI04; illustrated PDF in the project folder

## Summary

> **Decision proposed: buy flat magnets.** Each pole is made of **four
> identical flat N40UH blocks, 18.75 × 36.90 × 8.20 mm**, two side by side
> and two along the stack, magnetised straight through the 8.20 thickness.
> The same block is used for north and south poles: it is simply turned
> over. This replaces the 168 curved arc segments of doc 18 (two part
> numbers, N and S) with **160 + 8 identical blocks (one part number,
> NP1-220 Rev C)**.

| | Doc 18 arcs (A) | **Final flat blocks (F2t)** | Change |
|---|---|---|---|
| Magnet per pole | 4 arcs 7.20° × 18.35 × 7.70, radial | **2 × 2 blocks 18.75 × 36.90 × 8.20, parallel** | |
| Part numbers | 2 (NP1-220-N, -S) | **1** (NP1-220 Rev C), turned over for S | simpler buying, stock, no mix-ups |
| Pieces per generator | 160 + 8 | 160 + 8 | same |
| Piece mass | 41 g | 43 g | same handling |
| Magnet mass | 6.65 kg | 6.92 kg | +4 % |
| Line EMF, 178 rpm, 100 °C, 28 turns | 387 V | **381 V** | −1.7 %, right on the doc 06 target of 380 V |
| Torque at the same current | 803 Nm | 790 Nm | −1.7 % (≈ +15 W copper loss at rated) |
| Cogging, peak to peak | 1.02 Nm | **0.96 Nm** (0.13 % of rated) | slightly better |
| Torque ripple at load | 1.75 % | 1.56 % | better |
| Line EMF distortion (THD) | 0.50 % | 0.40 % | better |
| Magnet eddy loss, rated | 10.9 W (4 pieces along) | **12.8 W** (2 pieces along) | same order, far below the 40 W budget |
| Demagnetisation margin, worst short circuit at 120 °C | 27.7 % | **32.2 %** | better |
| Worst-case peak line voltage (250 rpm, −40 °C) | ≈ 912 V | ≈ 897 V | lower (more margin on 1200 V parts) |
| Drum seat | Ø618.4 (doc 18) | **Ø620.00 +0.05/0** | seat bored 0.8 mm larger on radius |

Three findings change other documents:

1. **The open eddy-loss check is now done** (doc 14 open point 3, doc 18 M8).
   Magnet eddy loss at rated load is 11 to 13 W for any reasonable
   segmentation, against the 40 W rotor loss assumed in doc 06. **Splitting a
   pole into two blocks side by side cuts the loss by 3.6 ×** (it stops the
   largest current loops), so the flat design needs only **2 blocks along the
   stack** instead of 4 arcs. The magnet order no longer waits for anything.
2. **Doc 18 left out the bond line in the seat diameter.** The magnet seat
   Ø618.4 equals the magnet outer diameter, so the 0.15 mm glass-bead bond line
   would have pushed every magnet 0.15 mm into the sleeve space. The new seat
   Ø620.00 includes the bond line.
3. **A flat block bonded to a round seat has a slightly thicker bond under its
   middle** (0.29 instead of 0.15 mm). This is fine for the adhesive and costs
   nothing measurable; one wide flat block per pole would have needed 0.73 mm
   and lost 6 % EMF, which is why it was rejected.

The flat-block route was chosen over the arcs because it is the **simpler
and more controllable part to buy and inspect** (flat ground faces,
micrometer-checkable, no grinding of radii, no radial-orientation tooling,
one part number), it is **at least as good electrically** once the block is
made 0.5 mm thicker, and it removes the biggest mix-up risk in doc 18 (an
N arc in an S position). Cost was not a criterion (project rule), but flat
blocks are also the cheaper and faster part to source.

![M01-options Four ways to make a pole](../cad/generator_mfg/out/M01-options.svg)

![MI04-compare Arc pole and flat pole](../cad/generator_mfg/out/MI04-compare.svg)

---

## 1. What was fixed before and what was open

From docs 06, 14 and 18: 40 poles, 45 slots, outer rotor, stator tip radius
299.0 mm, mechanical gap 2.0 mm to a 0.5 mm glass-epoxy sleeve (moulded on a
Ø602.0 mandrel, doc 18 §6.7), N40UH magnets 7.70 mm thick, pole span 0.80 of
the 9° pole pitch (7.20°), stack 74 mm, 40 G11 comb bars between the poles,
room-temperature toughened epoxy with 0.15 mm glass beads.

Open before this document:

| # | Open point | Closed by |
|---|---|---|
| 1 | Magnet axial segmentation not confirmed by an eddy-loss calculation (doc 14 open point 3, doc 18 M8) | §3: eddy loss computed for every shape and segmentation |
| 2 | Arcs need two part numbers (doc 18 M7), arc radii and radial orientation are the hardest features to buy and check | §2, §5: flat blocks, one part |
| 3 | Seat diameter did not include the bond line | §4: seat Ø620.00 |
| 4 | Retention and tolerances never written down for the magnet itself | §6, §7 |

## 2. The options compared

Seven shapes were run through the same 2D nonlinear FEA (the doc 05/06 model,
extended so that a magnet of any shape can sit on the fixed mesh). Every case
uses the real P1 radii, the 0.15 mm bond line, the moulded sleeve bore
r 301.0, a magnet inner face at r 301.5 on the pole (or block) centre line, the
drum shell to r 323, the 74 mm stack, magnets at 100 °C and the same stator
current (the doc 06 sizing current, 22.6 A rms with 28 turns).

| Key | Shape | Seat Ø | Magnets | Line EMF | Torque | Cogging p-p | Ripple | Line THD | Eddy loss, 2 / 4 pieces along | Demag margin |
|---|---|---|---|---|---|---|---|---|---|---|
| A | Arc 7.20°, 7.70, radial (doc 18) | 618.70 | 6.65 kg | 387.4 V | 803 Nm | 1.02 Nm | 1.75 % | 0.50 % | 27.4 / 10.9 W | 27.7 % |
| F1 | 1 flat block 37.94 wide, 7.70 | 619.86 | 6.57 kg | 364.3 V | 755 Nm | 1.06 Nm | 1.21 % | 0.25 % | 22.7 / 9.0 W | 28.5 % |
| F2 | 2 flat blocks 18.75 wide, 7.70 | 618.98 | 6.50 kg | 375.5 V | 779 Nm | 1.06 Nm | 1.54 % | 0.36 % | 13.2 / 8.0 W | 31.3 % |
| F3 | 3 flat blocks 12.43 wide, 7.70 | 618.83 | 6.46 kg | 376.2 V | 780 Nm | 1.58 Nm | 1.66 % | 0.44 % | 7.8 / 5.7 W | 30.2 % |
| F2w | 2 blocks 19.70 wide (span 0.84), 7.70 | 619.01 | 6.82 kg | 381.7 V | 792 Nm | **5.40 Nm** | 2.40 % | 0.80 % | 14.3 / 8.4 W | 30.5 % |
| **F2t** | **2 blocks 18.75 wide, 8.20** | **619.98** | **6.92 kg** | **380.8 V** | **790 Nm** | **0.96 Nm** | **1.56 %** | **0.40 %** | **12.8 / 7.7 W** | **32.2 %** |
| F2wt | 2 blocks 19.70 wide, 8.00 | 619.61 | 7.09 kg | 384.9 V | 799 Nm | **5.53 Nm** | 2.40 % | 0.82 % | 14.0 / 8.3 W | 31.0 % |

![Comparison of EMF, cogging and load torque](../analysis/generator/results/magnets_compare.png)

What the table says:

- **Flat blocks lose EMF because they hold less magnet, not because they are
  flat.** With 2 or 3 blocks the loss is the same 3 %: blocks that fit the
  pole at the inner face leave small wedge-shaped gaps towards the drum, so
  2 to 3 % less magnet. One wide block (F1) loses 6 % because its edges stand
  0.6 mm further from the stator.
- **Widening the pole is a trap.** Span 0.84 (F2w, F2wt) wins the EMF back but
  lands on a cogging peak of the 40/45 combination: 5.4 Nm instead of 1 Nm,
  and the ripple and EMF distortion double. The doc 06 span of 0.80 stays.
- **A 0.5 mm thicker block (F2t) wins the EMF back** without touching the
  span, the stator or the winding: 381 V at 28 turns (doc 06 target 380 V),
  cogging and ripple slightly lower than the arcs, best demagnetisation
  margin. It costs 0.27 kg more magnet, 0.8 mm on the seat diameter and
  0.5 mm of drum yoke (13.0 mm left under the seat; the doc 06 FEA used 12 mm).
- **Three blocks (F3)** would cut the eddy loss further but raise cogging
  (1.6 Nm) and give 240 small pieces. No reason to go there.
- **Demagnetisation.** Worst case is the doc 06 transient short circuit (2 ×
  the steady short-circuit current, d-axis, magnets at 120 °C). All flat
  shapes are better than the arcs. Note: in the first run the flat shapes
  showed a false demagnetising peak in mesh elements cut by the slanted block
  sides; the check now uses only elements fully inside a magnet (as for the
  arcs, whose edges follow the mesh).

**Chosen: F2t.** The rest of this document defines it.

## 3. Magnet eddy loss and segmentation (closes doc 14 point 3, doc 18 M8)

Method: time-stepped FEA at rated load over one electrical period (90 steps;
the stator-frame field repeats every 18° of rotation, so 4 periods of the
rotor-frame history are built from it exactly), field history followed in
every magnet node in the rotor frame, eddy current density σ·(−∂A/∂t) with
**zero net current in each piece**, resistivity 1.5 µΩ m. The 2D result is
for infinitely long pieces; the finite length of each piece is applied with
the exact factor for a rectangle in a uniform alternating field (the Prandtl
torsion analogy). The dominant field frequencies seen by the magnets are
44.5, 89, 133.5 and 178 Hz: the 40/45 winding's space harmonics, not slot
ripple, so the skin depth (> 25 mm) is far larger than the magnet and the
resistance-limited method is valid.

| Pieces along the stack | 1 | 2 | 3 | 4 | 6 |
|---|---|---|---|---|---|
| A, arc 38 mm wide | 45.3 W | 27.4 W | 16.7 W | 10.9 W | 5.5 W |
| **F2t, block 18.75 wide** | 15.8 W | **12.8 W** | 10.0 W | 7.7 W | 4.7 W |
| F3, block 12.4 wide | 8.8 W | 7.8 W | 6.7 W | 5.7 W | 4.1 W |

Result: **2 blocks along the stack**, 12.8 W at rated speed and about 25 W at
the 250 rpm design overspeed (loss ∝ speed²). Doc 06 assumed 40 W rotor loss;
the magnets sit on the drum, which is cooled by the outside air, so their
temperature rise from this is a few kelvin. Going to 4 blocks along would
save 5 W for twice the pieces and three shim gaps instead of one, and is not
worth it.

PWM ripple from the SiC active rectifier (doc 12) adds little: with
Ld ≈ 14 mH the switching ripple current is well under 1 A, against 23 A
rated. It is checked on the bench by the magnet temperature probe (doc 15).

## 4. Final geometry

### 4.1 The block NP1-220 Rev C

![M03-block Detail drawing NP1-220 Rev C](../cad/generator_mfg/out/M03-block.svg)

![MI01-block The magnet block in 3D](../cad/generator_mfg/out/MI01-block.svg)

| Feature | Value |
|---|---|
| Size | **18.75 ±0.03 (across) × 36.90 ±0.05 (along) × 8.20 ±0.02 (thickness)** |
| Edges | Chamfer 0.2 to 0.3 × 45° on all 12 edges |
| Faces | N and S faces ground, flatness 0.02, parallelism 0.02; sides square to the N face within 0.05 |
| Magnetisation | Parallel, through the 8.20 thickness, fully saturated; magnetic axis within 2° of the face normal |
| Mass | 43.1 g |
| Count | 160 per generator + 8 spare + 8 test pieces (unmagnetised acceptable) for Q1 |
| Marking | White dot Ø3 on the N face near one corner |

### 4.2 One part, two poles

![M02-flip One magnet, two ways round](../cad/generator_mfg/out/M02-flip.svg)

At an N pole the block goes in **dot up** (N face towards the stator); at an S
pole the same block goes in **dot down** (N face against the drum). This
removes doc 18 M7 completely: one part number, one stock, one spare box.

### 4.3 The pole on the drum

![M04-pole_section Detail of one pole](../cad/generator_mfg/out/M04-pole_section.svg)

| Feature | Value (radii from the generator axis) |
|---|---|
| Pole pitch / span | 9.000° / 7.20° (unchanged); block centre lines at ±1.80° from the pole centre |
| Drum seat | **Ø620.00 +0.05/0**, x 335 to 425, run-out ≤ 0.02 to the cup seats, Ra 3 to 6 µm after grit blasting |
| Bond line | 0.15 at the block corners (0.15 mm glass beads), 0.29 under the block middle |
| Block inner face | r 301.51 at the block centre line, r 301.65 at the block edges |
| Sleeve | Moulded on the Ø602.0 mandrel: 0.51 thick at the block centres, 0.65 at the block edges |
| Gap between the two blocks of a pole | 0.20 at the inner corners, widening to 0.72 at the outer corners (glue) |
| Comb bars NP1-221 | G11, trapezoid 9.60 (inner) to 10.26 (seat side) × 7.0 high × 82.0 long, faces at 2.70° to the bar centre line so they lie flat against the neighbouring blocks |
| End rings NP1-222 | G11, OD Ø620.0 −0.1/−0.2, ID Ø604.0, 8.0 wide, 40 notches for the comb bar ends |
| Axial layout | Block rows x 343.0 to 379.9 and x 380.1 to 417.0, 0.2 mm PTFE shim between rows (removed after cure) |
| Drum yoke under the seat | 13.0 mm (shell OD Ø646 unchanged) |

![M05-comb Comb bar and end rings](../cad/generator_mfg/out/M05-comb.svg)

![M06-layout Where every block goes](../cad/generator_mfg/out/M06-layout.svg)

![MI02-pole One pole pulled apart](../cad/generator_mfg/out/MI02-pole.svg)

![MI03-drum Drum with 160 flat blocks](../cad/generator_mfg/out/MI03-drum.svg)

The two blocks of one pole **push each other apart** (same polarity side by
side), so each one settles against its own comb bar by itself. The comb bars
therefore set the pole position, and the 0.20 mm centre gap fills with glue.

## 5. Flat or arc: buying and making

| Aspect | Arc segments (doc 18) | Flat blocks (final) |
|---|---|---|
| How the maker produces it | Pressed in a radially oriented die (tooling per size) or cut from blocks with much waste; both radii ground with profiled wheels | Sliced from standard pressed and sintered blocks, faces surface ground; no tooling |
| Tolerances commonly held | Thickness ±0.05, radii ±0.05, arc angle ±0.1° | ±0.02 to ±0.05 on every size, flatness 0.02 |
| Magnetisation | "Radial" for a 7.2° segment is in practice parallel along the centre line; needs a shaped fixture | Parallel through thickness, the standard case for every maker |
| Polarity variants | 2 part numbers (curve fits one way only) | 1 part number |
| Coating | Even coat on curved faces is harder; thin arc edges chip | Even coat on flat faces, chamfered edges |
| Incoming inspection | Radius gauges or CMM | Micrometer and go/no-go gauges |
| Typical lead time (sintered NdFeB, custom size) | 6 to 10 weeks incl. tooling and first article | 3 to 6 weeks after drawing approval |
| Number of qualified makers | Fewer (radial tooling) | Many |
| Effect on the machine | Reference | −1.7 % EMF at the same turns (chosen to hit the 380 V target), lower cogging, ripple and THD |

## 6. Retention: what holds the magnets

![M08-forces What holds a magnet](../cad/generator_mfg/out/M08-forces.svg)

| Load (one pole, 4 blocks) | Value (from FEA unless noted) | Carried by |
|---|---|---|
| Centrifugal at 250 rpm | 36 N outwards (hand calculation) | Drum steel (outer rotor) |
| Net magnetic force, no load | 38 N outwards | Drum steel |
| Net magnetic force, rated load | 130 N outwards | Drum steel |
| Tangential, rated load (local peak on one pole) | 87 N | Glue shear and comb bars |
| Tangential, short circuit (4 × torque) | ≈ 260 N | Glue shear and comb bars |
| Differential shrinkage steel/NdFeB, 20 to −40 °C | ≈ 0.02 mm at the block corners | Toughened room-cure glue (qualified on Q1) |

Glue area per pole is 2,770 mm², so the rated shear is 31 kPa and the short
circuit case about 95 kPa, against ≥ 5 MPa adhesive strength at 120 °C: more
than 50 × margin. Every radial load pushes the blocks into the drum, so the
glue never carries a pull-off load. Three independent things keep a block
out of the air gap: the glue, the comb bars and end rings, and the moulded
glass sleeve over all magnets (it also holds the pieces if a block ever
cracks). The thermal-mismatch movement at the block corners is set by the
half-diagonal of the block (20.7 mm), almost the same as the doc 18 arc
(21.5 mm), so the doc 18 adhesive choice and the Q1 cold-cycling test stand
unchanged; Q1 must use real NP1-220 Rev C blocks.

## 7. Tolerances

![M07-stack Radial tolerance stack](../cad/generator_mfg/out/M07-stack.svg)

**Radial.** The sleeve is moulded on the mandrel, so the magnet and bond
scatter only change the sleeve thickness, not the air gap (doc 18 M6). With
seat +0.05/0 on the diameter, bond +0.05/0 and block ±0.02, the inner face at
a block centre lies between r 301.49 and r 301.60: the sleeve is 0.49 to 0.60
at the block centres and up to 0.75 at the block edges, inside the 0.4 to 0.8
range to be qualified on Q1. A drum with a seat smaller than Ø620.00 is
rejected. The doc 14 air gap budget item "magnet thickness and bond line
0.050" drops out of the gap budget (it is replaced by the mandrel and sleeve
bore tolerance already in doc 18 §6.8).

**Across and along.** Block width ±0.03 gives a centre gap between the two
blocks of 0.14 to 0.26 mm (never touching, glue fills it). The comb bar width
±0.05 and the 0.1 mm glue clearance per side keep the pole span within
±0.02°. Block length ±0.05 with the 0.2 mm shim keeps the pole length within
74.0 ±0.15, inside the 74.0 ±0.2 stator stack tolerance.

**Magnetic.** Tolerance study on F2t (pole remanence and position scatter,
cogging over a full slot pitch; the 72° FEA section repeats the scatter
pattern five times, so this is an indication, not a statistical result):

| Case | Cogging p-p |
|---|---|
| Nominal | 0.96 Nm |
| Poles sorted to ±0.5 %, strong next to weak (doc 18 sorting rule) | 1.14 Nm |
| Unsorted, every pole random within ±1.5 % | 2.74 Nm |
| One pole 3 % weak (e.g. a chipped block) | 2.41 Nm |
| Pole centres random within ±0.05° (±0.26 mm at r 301) | 2.35 Nm |
| Pole centres random within ±0.10° (doc 18 pole-map limit) | 8.50 Nm |
| Pole centres random within ±0.25° | 14.8 Nm |

Conclusions:

- **Remanence:** sorting matters. Unsorted pieces (±1.5 %) almost triple the
  cogging; the doc 18 sorting rule (poles within ±0.5 %, strong next to weak)
  keeps it at 1.1 Nm. Keep it.
- **Pole position matters much more than remanence.** At the doc 18 pole-map
  limit of ±0.1° the cogging rises to about 8.5 Nm (1.2 % of rated torque).
  The section model repeats the error pattern five times, which adds the
  errors coherently, so the real value over 40 independent poles is lower,
  but the trend is clear. **Tighten the comb bar placement to ±0.03° (±0.16 mm
  at the seat) and the pole-map acceptance to ±0.05°** (doc 18 §6.4 and §6.6).
  With trapezoid comb bars in notched end rings and blocks that push
  themselves against the bars, ±0.05° is reachable with the aluminium
  indexing template already planned.

## 8. Purchase specification NP1-220 Rev C (send with drawing M03)

| Item | Requirement |
|---|---|
| Part | NP1-220 Rev C magnet block, drawing M03 (doc 19) |
| Material | Sintered NdFeB (GB/T 13560 designation), quote both: **N40EH preferred** (Br ≥ 1.25 T, HcJ ≥ 2,388 kA/m / 30 kOe) and **N40UH accepted** (Br ≥ 1.26 T, HcJ ≥ 1,990 kA/m / 25 kOe), values at 20 °C (§12). Grain-boundary-diffused Dy/Tb grades accepted if they meet all values |
| Export | State country of manufacture, origin of the Dy/Tb, and lead time including any export licence |
| Test data per lot | J-H and B-H demagnetisation curves at 20, 60, 100, 120 and 150 °C on samples from the lot; temperature coefficients of Br and HcJ; density |
| Size | 18.75 ±0.03 × 36.90 ±0.05 × 8.20 ±0.02 mm **including coating**; chamfer 0.2 to 0.3 on all edges; flatness and parallelism of the pole faces 0.02 |
| Magnetisation | Parallel through the 8.20 dimension, fully saturated; deviation of the magnetic axis from the face normal ≤ 2° |
| Uniformity | Magnetic moment (Helmholtz coil) of every piece measured and reported against its serial; all pieces within ±1.5 % of the lot mean |
| Coating | NiCuNi ≥ 15 µm + epoxy ≥ 15 µm; ≥ 500 h neutral salt spray (ISO 9227) without red rust; cross-cut adhesion class 0 to 1; adhesion of the chosen structural adhesive to the coating approved by the adhesive maker |
| Corrosion of the bare alloy | Low-weight-loss grade: PCT 121 °C, 2 bar, 100 % RH, 96 h, weight loss ≤ 5 mg/cm² |
| Marking | White dot Ø3 on the N face, one corner; lot number on every box |
| Quantity | 168 magnetised + 8 test pieces (unmagnetised acceptable) per generator |
| Packaging | Every block in its own non-magnetic spacer, alternating (repelling) layout, steel-shielded box meeting the IATA PI 953 field limit for air freight |
| First article | 5 pieces measured (size, moment, coating thickness, one demagnetisation curve) and approved before the lot is released |
| Documents | Material certificate, per-piece moment list, coating report, salt-spray and PCT reports, RoHS/REACH declaration |

## 9. Incoming inspection and bonding

![M09-inspect Check the magnets when they arrive](../cad/generator_mfg/out/M09-inspect.svg)

Incoming inspection replaces doc 18 §6.5 "receive and sort": count, look
(no chips > 0.5 mm), size with aluminium go/no-go gauges, moment in the
Helmholtz coil (±1.5 % of the lot mean, within ±1 % of the supplier's value),
check the dot is on the N face with the gaussmeter, then **sort into 40 poles
of 4 blocks** with pole sums within ±0.5 %, strong and weak poles alternating.

![M10-bond Glue one pole of blocks](../cad/generator_mfg/out/M10-bond.svg)

Bonding is as doc 18 §6.4 and §6.5 with these changes:

1. Comb bars NP1-221 are trapezoid (wide face on the seat) and their ends sit
   in the notches of the end rings NP1-222; locate notch 1 from hub bolt hole 1.
2. The jig NP1-T02 gets a **Rev C shoe**: a flat POM pocket 18.85 × 37.0 with
   the block held dot up (N poles) or dot down (S poles).
3. Per pole: block 1 against the left comb bar, block 2 next to it (it moves
   against the right bar by itself), PTFE shim 0.2, then blocks 3 and 4 the
   same way, clamp bar on all four until cured.
4. N poles first (all 20, dot up), cure, then S poles (dot down); gaussmeter
   check of every pole before the glue gels.
5. Pole map (doc 18 §6.6) with the pole centre limit tightened to **±0.05°**
   (§7); the axial uniformity check now looks for a dip over the single row
   joint at x 380.
6. Comb bars are placed with the indexing template to **±0.03°** (±0.16 mm).

## 10. Changes to other documents

| Document | Change |
|---|---|
| Doc 14 §4.5 | Magnets are 160 flat blocks NP1-220 Rev C (2 × 2 per pole, 8.20 thick); segmentation confirmed |
| Doc 14 §5.2 | Remove "magnet thickness and bond line 0.050" from the air gap budget (mandrel-moulded sleeve) |
| Doc 14 open point 3 | Closed by §3 |
| Doc 18 §0 table, App. B | Magnets: 160 + 8 flat blocks 43.1 g, 6.92 kg; seat Ø620.00; EMF ≈ 381 V at 100 °C, worst-case peak ≈ 897 V (28 turns) |
| Doc 18 M7, M8 | Closed (one part number; eddy loss done) |
| Doc 18 §4.2 | Comb bars: G11 trapezoid 9.60/10.26 × 7.0 × 82 (NP1-221); end rings NP1-222 with notches |
| Doc 18 §4.3 | Replace by §8 of this document |
| Doc 18 §6.3 | Magnet seat **Ø620.00 +0.05/0** (was Ø618.4) |
| Doc 18 §6.4, §6.5 | As §9 of this document; comb bar placement ±0.03° (was ±0.05°) |
| Doc 18 §6.6 | Pole centre acceptance ±0.05° (was ±0.1°) |
| Doc 06 | Rotor loss 40 W confirmed (magnet eddy 13 W at rated) |
| `cad/nacelle_p1/geometry.py` | `MAGNET` still describes the doc 18 arcs; switch to `magnet_geom.py` values when doc 18 goes to Rev B (after Q1) |

## 11. Open items

| # | Item | Owner | Due |
|---|---|---|---|
| 1 | Approve this magnet definition (flat blocks, F2t) | Martin | Now |
| 2 | Send §8 and drawing M03 for quotation (N40EH and N40UH) to at least three makers, at least one outside China; first article 5 pieces | Cat. 10 | Week 1 |
| 3 | Order 8 test pieces early for the Q1 magnet panels (unmagnetised acceptable) | Cat. 10 | Week 1 |
| 4 | Drawings NP1-221 comb bar, NP1-222 end ring, jig shoe NP1-T02 Rev C; drum drawing NP1-210 seat Ø620.00 | Cat. 4/10 | Week 2 |
| 5 | Update doc 18 to Rev B with §10 (after Q1) | Cat. 10 | Weeks 3 to 8 |
| 6 | Bench check of magnet temperature at rated load (confirms §3) | Cat. 11 | Bench T2 |

## 12. Magnet grade assessment

Question (Martin, 2026-11-05): which grade is best for this generator, which
is easiest to buy, and which is feasible?

### 12.1 What the grade must do

The grade sets two things on the fixed block size: the **EMF** (through the
remanence Br) and the **resistance to demagnetising** in the worst fault
(through the intrinsic coercivity HcJ, which falls as the magnet warms). The
design case is the doc 06 transient short circuit with the magnets at
**120 °C**; a margin of at least **20 %** between the worst field in the
magnet and HcJ is required. 150 °C is run as an extra check, because the
magnet temperature in service is still a model value until the bench test.

Every grade was run on the final F2t geometry with its catalogue minimum
values ([`grades.py`](../analysis/generator/grades.py) →
[`grades_summary.json`](../analysis/generator/results/grades_summary.json)).

![M11-grades Which magnet grade](../cad/generator_mfg/out/M11-grades.svg)

| Grade | Br / HcJ at 20 °C (min) | Line EMF, 8.20 mm block | Block for 380 V | Margin at 120 °C | Margin at 150 °C | Heavy rare earth (Dy/Tb) |
|---|---|---|---|---|---|---|
| N42SH | 1.29 T / 1,592 kA/m | 389 V | 7.4 mm | **2 %** (fails) | −70 % | low, ≈ 2 to 4 % |
| N48SH | 1.37 T / 1,592 kA/m | 409 V | 5.7 mm | **−4 %** (fails) | −81 % | low |
| N38UH | 1.22 T / 1,990 kA/m | 370 V | 9.2 mm | 34 % | 0 % | ≈ 4 to 6 % |
| **N40UH** | 1.26 T / 1,990 kA/m | **381 V** | 8.1 mm | **32 %** | −3 % | ≈ 4 to 6 % (≈ 1 % with GBD) |
| N42UH | 1.28 T / 1,990 kA/m | 386 V | 7.6 mm | 31 % | −4 % | ≈ 4 to 6 % |
| N45UH (GBD) | 1.32 T / 1,990 kA/m | 400 V | 6.4 mm | 31 % | 0 % | ≈ 1 to 2 % Tb |
| N38EH | 1.22 T / 2,388 kA/m | 373 V | 8.9 mm | 50 % | 31 % | ≈ 6 to 9 % |
| **N40EH (GBD)** | 1.25 T / 2,388 kA/m | **381 V** | 8.1 mm | **49 %** | **30 %** | ≈ 1.5 to 3 % Tb |
| N35AH | 1.17 T / 2,786 kA/m | 359 V | 10.3 mm | 61 % | 49 % | ≈ 9 to 12 % |
| SmCo 30H (Sm2Co17) | 1.08 T / 1,990 kA/m | 355 V | 10.9 mm | 64 % | 61 % | none (samarium and cobalt instead) |

"Block for 380 V" is an estimate from the EMF slope found in §2; anything
other than about 8.2 mm means new block, seat and sleeve numbers. Heavy rare
earth contents are typical industry values, not supplier data.

### 12.2 Sourcing (status 2026-11-05)

- **Every grade that passes contains dysprosium or terbium** (or, for SmCo,
  samarium). China's MOFCOM Announcement No. 18 (4 April 2025) puts seven
  medium and heavy rare earths, including Dy, Tb and Sm, **and magnets
  containing them** under export licensing. It has never been suspended:
  each shipment needs a licence, unless the maker holds one of the
  year-long general licences issued since December 2025 (first to JL MAG,
  Zhong Ke San Huan and Yunsheng). Dy and Tb exports are reported at about
  half their earlier level.
- A wider second wave of controls announced in October 2025 was suspended,
  and **that suspension runs out on 10 November 2026**, five days after this
  document. What follows is not known yet, so quotes should state the lead
  time including any export licence.
- **Makers outside China** produce UH and EH grades: in Japan (Shin-Etsu,
  Proterial, TDK), in Germany (VAC) and, since 2025, in Estonia (Neo
  Performance Materials, Narva). They are usually dearer and prefer larger
  orders; 7 kg per generator is small, so a distributor may be needed.
  Their plants also depend partly on Chinese heavy rare earth feed.
- **UH grades are the most common high-temperature grades**: wind, servo and
  traction motors use them, many makers stock the alloy, and N40UH and
  N42UH are standard. **EH grades** are made by fewer makers; N40EH needs
  grain-boundary diffusion (GBD) of terbium, which only the larger makers
  run. **AH and SmCo** are specialist products with few makers, long lead
  times and the highest prices.

### 12.3 Ranking

| Rank | Grade | Best for the turbine | Easy to buy | Feasible for P1 |
|---|---|---|---|---|
| 1 | **N40EH (GBD)** | ★★★★ Same size and EMF as N40UH, safe even at 150 °C | ★★ Larger makers only, Tb content | **Yes: drop-in on the same drawing, ask for it** |
| 2 | **N40UH** | ★★★ Meets the 120 °C case with 32 %, no reserve at 150 °C | ★★★★ Standard grade, many makers | **Yes: current choice, safe fallback** |
| 3 | N38EH | ★★★ Like N40EH but 2 % less EMF (block 8.9 mm or 29 turns) | ★★★ Common EH grade | Yes, with a geometry change |
| 4 | N42UH | ★★★ +1.4 % EMF over N40UH, same margin | ★★★★ | Yes, drop-in (EMF slightly above target) |
| 5 | N45UH (GBD) | ★★ High EMF, but no reserve at 150 °C | ★★ | Only with a thinner block (6.4 mm) |
| 6 | N38UH | ★★ Low EMF | ★★★★ | Needs 9.2 mm block |
| 7 | N35AH | ★★ Very safe, low EMF | ★ | Needs 10.3 mm; long lead time |
| 8 | SmCo 30H | ★★ Most temperature-proof, low EMF, brittle | ★ | Needs 10.9 mm and a new drum seat; costly |
| – | N42SH, N48SH | ✗ Demagnetise in the worst short circuit | ★★★★ | **No** (as doc 06 found for N42SH) |

**Recommendation.** Keep the drawing as it is (8.20 mm) and ask every maker
to quote **N40EH (preferred) and N40UH (accepted)** on the same drawing.
Both give 381 V. N40EH gives 30 % margin even at 150 °C, which covers an
error in the magnet temperature model at no cost in size or EMF. N40UH
meets the 120 °C design case with 32 % margin and is the easier part to
buy. Choose N40EH if a qualified maker can deliver it, with its export
licence, inside the 8 to 12 weeks planned in doc 18; otherwise N40UH. The
bench test (doc 15) measures the real magnet temperature and settles which
grade the production version needs.

## Appendix A. How to rerun

```
cd analysis/generator
python3 magnets.py              # all 7 shapes, ~40 min (2 processes in parallel: A F1 F2 F3 / F2w F2t F2wt)
python3 magnets.py tol F2t      # tolerance scatter on the chosen shape, ~20 min
python3 grades.py               # magnet grade assessment (§12), ~10 min
cd ../../cad/generator_mfg
python3 magnet_geom.py          # final dimensions
python3 figures_magnets.py --png
```
