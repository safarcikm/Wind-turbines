# 12 kW Wind Turbine for Iceland: Best Magnet Shape for N42SH

Status: **study** · 2026-11-05 (Martin: "What would be the most optimal shape for N42SH, 1. in block shape, 2. in fully custom shape, make a comparison with those and the latest 30x15x12")  
Builds on: [19 – Final magnet geometry](19-magnet-geometry.md) (Rev B, §16 SH feasibility and the 100 °C design basis), [20 – N42SH 30 × 15 × 6 variant](20-magnet-variant-n42sh.md)  
Analysis: [`analysis/generator/optshape.py`](../analysis/generator/optshape.py) → `results/opt_<case>.json`, [`opt_summary.json`](../analysis/generator/results/opt_summary.json) (26 cases, same 2D nonlinear FEA as docs 19 and 20)

## Summary

| | 30 × 15 × 12 (doc 20) | **Best block** | **Best custom shape** |
|---|---|---|---|
| Shape | 30 × 15 × 6 blocks, stacked in pairs | Block **33.2 × 14.8 × 11** (one across, five along) | **Arc segment, parallel magnetised**, R 301.5 / 312.5, 6.12° (32.2 mm chord), 11 thick |
| Line EMF 100 °C, 28 turns (skewed) | 365 V | 379 V | **387 V** |
| Turns per coil for 380 V | 29 | 28 | 28 |
| Copper loss at rated torque vs Rev B | +9 % | ±0 | **−4 %** |
| Transient short circuit margin 100 / 120 °C | 32 / 13 % | 26 / 6 % | 30 / 11 % |
| 20 % margin kept up to | **113 °C** | 106 °C | 110 °C |
| Magnet mass | 8.21 kg | 8.21 kg | 8.11 kg |
| Pieces per generator | 400 | 200 | 160 (4 along) |
| Cogging not skewed (skewed) | 5.4 (0.01) Nm | 1.3 (0.00) Nm | **0.5** (0.00) Nm |
| Drum seat / steel under it | Ø628.0 / 9.0 mm | Ø626.2 / 9.9 mm | Ø625.3 / 10.4 mm, uniform bond |
| Can be bought | catalogue, stock | made to size, simple | made to drawing, tooling and grinding |

**Answers:**

1. **Best block:** the key for N42SH is a narrow, thick pole, and the
   30 × 15 × 12 pair already sits almost at the block optimum for
   demagnetisation. Only one block keeps the existing 28-turn winding: a
   custom-size **33 × 15 × 11 mm** block, one across and five along each
   pole. Compared with 30 × 15 × 12 it brings back 4 % of voltage and 9 %
   of copper loss, gives up 7 K of short-circuit reserve (106 °C against
   113 °C), and as one solid block needs no pair bonding (200 pieces
   instead of 400).
2. **Best custom shape:** a **parallel-magnetised arc segment**, span 0.68
   (6.12°), 11 mm thick, with its back fitted to the round seat. It beats
   every block:
   - 6 % more voltage than 30 × 15 × 12, so 11 % less copper loss than it and 4 % less than Rev B;
   - 20 % margin kept up to 110 °C;
   - so little cogging (0.5 Nm) that the step skew can be left out;
   - 160 pieces and no stacking.

   The price is a custom ground part: tooling, a minimum order, a longer
   lead time and a higher piece price.
3. **Loaf shapes (thinner at the edges) are worse for N42SH:** they lose
   more margin than they gain in smoothness. Radial magnetisation is also
   worse than parallel.

**Recommendation:** if a maker outside Asia will quote it, the custom
parallel arc (§3.2) is the best N42SH rotor. It is better electrically than
Rev B, with only 3 K less short-circuit reserve than 30 × 15 × 12. If only
catalogue or plain made-to-size parts are practical, stay with doc 20's
30 × 15 × 12. The 33 × 15 × 11 block is the in-between choice if the
28-turn winding must stay. None of them meets the original 120 °C design
case, so every N42SH option keeps the 100 °C basis and the conditions of
doc 19 §16.3.

## 1. What was varied

All cases use N42SH catalogue minimum values (Br 1.29 T, HcJ 1,592 kA/m at
20 °C, −0.12 %/K, −0.60 %/K). Stator, 2 mm gap, 0.5 mm sleeve, magnet gap
face at r 301.5 and drum outside r 323 are unchanged. The seat is fitted to
each shape, so a thicker magnet takes drum steel away.

| Family | What it is | Varied |
|---|---|---|
| B | Flat rectangular block, parallel magnetised, one across per pole, five along, on the round seat (bond thicker under the middle) | span 0.63 to 0.80 (width 29.9 to 37.9 mm), thickness 9 to 13 mm |
| AR | Arc segment, radially magnetised (the doc 18 shape) | span 0.72, 0.80; 9, 11 mm |
| AP | Arc segment, parallel magnetised | span 0.63 to 0.80; 10 to 12 mm |
| L | Loaf: arc back, gap face lifted 2 or 4 mm at the edges, parallel magnetised | span 0.80, 0.90; 10 to 12 mm |

For each case the FEA gives:

- line EMF at 100 °C with 28 turns, skewed in 4 rows of 0.25°;
- phase THD;
- cogging at 60 °C, not skewed and skewed;
- demagnetisation margin (worst element against HcJ) for rated load and for steady and 2 × transient short circuit, at 100 and 120 °C;
- the temperature that keeps 20 % margin in the transient short circuit, interpolated from those two results.

## 2. All results

| Case | Span | Thick | Mass | EMF 28 t | Cu loss vs Rev B | Phase THD | Cogging (skewed) | SC margin 100 / 120 °C | 20 % up to |
|---|---|---|---|---|---|---|---|---|---|
| **Blocks** | | | | | | | | | |
| B63_9 | 0.63 | 9 | 6.05 kg | 346 V | +21 % | 1.9 % | 5.7 (0.0) | 28 / 8 % | 108 °C |
| B63_11 | 0.63 | 11 | 7.39 kg | 359 V | +12 % | 2.0 % | 5.5 (0.0) | 31 / 13 % | 112 °C |
| B63_13 | 0.63 | 13 | 8.73 kg | 367 V | +7 % | 2.2 % | 5.4 (0.0) | 32 / 14 % | 114 °C |
| S1d (doc 20) | 0.63 | 12 | 8.21 kg | 365 V | +9 % | 2.2 % | 5.4 (0.0) | 32 / 13 % | 113 °C |
| B68_11 | 0.68 | 11 | 7.98 kg | 374 V | +3 % | 4.6 % | 1.4 (0.0) | 27 / 8 % | 107 °C |
| **B70_11** | 0.70 | 11 | 8.21 kg | 379 V | ±0 | 5.8 % | 1.3 (0.0) | 26 / 6 % | 106 °C |
| B70_12 | 0.70 | 12 | 8.96 kg | 384 V | −2 % | 5.9 % | 1.4 (0.0) | 27 / 7 % | 107 °C |
| B72_9 | 0.72 | 9 | 6.91 kg | 370 V | +6 % | 6.5 % | 3.2 (0.0) | 23 / 2 % | 103 °C |
| B72_11 | 0.72 | 11 | 8.45 kg | 384 V | −2 % | 6.9 % | 3.4 (0.0) | 26 / 6 % | 106 °C |
| B72_13 | 0.72 | 13 | 9.98 kg | 388 V | −4 % | 6.8 % | 3.3 (0.0) | 27 / 7 % | 107 °C |
| B80_9 | 0.80 | 9 | 7.68 kg | 384 V | −2 % | 10.7 % | 0.6 (0.0) | 20 / −1 % | 100 °C |
| B80_11 | 0.80 | 11 | 9.39 kg | 398 V | −9 % | 10.8 % | 0.3 (0.0) | 23 / 2 % | 103 °C |
| B80_13 | 0.80 | 13 | 11.09 kg | 395 V | −7 % | 10.4 % | 0.5 (0.0) | 25 / 5 % | 105 °C |
| **Custom** | | | | | | | | | |
| AP63_12 | 0.63 | 12 | 8.21 kg | 376 V | +2 % | 3.0 % | 7.1 (0.0) | 32 / 13 % | 113 °C |
| **AP68_11** | 0.68 | 11 | 8.11 kg | 387 V | −4 % | 5.9 % | 0.5 (0.0) | 30 / 11 % | 110 °C |
| AP72_11 | 0.72 | 11 | 8.59 kg | 399 V | −9 % | 8.3 % | 6.8 (0.0) | 28 / 9 % | 108 °C |
| AP80_10 | 0.80 | 10 | 8.66 kg | 410 V | −14 % | 11.9 % | 0.4 (0.0) | 25 / 5 % | 104 °C |
| AR72_9 | 0.72 | 9 | 7.01 kg | 388 V | −4 % | 7.6 % | 6.4 (0.0) | 20 / −2 % | 100 °C |
| AR72_11 | 0.72 | 11 | 8.59 kg | 402 V | −10 % | 8.0 % | 6.5 (0.0) | 22 / 1 % | 102 °C |
| AR80_9 | 0.80 | 9 | 7.79 kg | 406 V | −12 % | 11.6 % | 0.5 (0.0) | 20 / −2 % | 100 °C |
| AR80_11 | 0.80 | 11 | 9.55 kg | 419 V | −18 % | 11.5 % | 0.7 (0.0) | 22 / 1 % | 102 °C |
| L80_10_2 | 0.80 | 10 | 8.10 kg | 390 V | −5 % | 8.7 % | 0.9 (0.0) | 22 / 1 % | 102 °C |
| L80_10_4 | 0.80 | 10 | 7.52 kg | 369 V | +6 % | 5.1 % | 0.3 (0.0) | 15 / −8 % | 96 °C |
| L80_12_2 | 0.80 | 12 | 9.86 kg | 401 V | −10 % | 9.0 % | 0.8 (0.0) | 25 / 5 % | 105 °C |
| L80_12_4 | 0.80 | 12 | 9.29 kg | 383 V | −2 % | 5.9 % | 0.6 (0.0) | 19 / −3 % | 99 °C |
| L90_11_4 | 0.90 | 11 | 9.46 kg | 394 V | −7 % | 8.9 % | 0.2 (0.0) | 23 / 2 % | 103 °C |

The copper loss column is the loss at rated torque relative to Rev B.
It scales as (380 V / EMF)², because a weaker magnet needs more
ampere-turns whatever the turn count.

## 3. What the numbers say

### 3.1 Blocks

- **The span sets the trade between voltage and margin.** Going from 0.63
  to 0.80 adds about 10 % EMF but costs about 8 points of short-circuit
  margin (8 K of reserve). In a short circuit the stator's reverse field
  is strongest at the pole edges, and a narrow pole keeps its edges away
  from the neighbouring pole and from the stator's d-axis field.
- **Thickness above 11 mm buys little.** At span 0.63, going from 9 to
  11 mm adds 4 K; going from 11 to 13 mm adds only 2 K, for 1.3 kg more
  magnet and 2 mm less drum steel.
- **The block optimum for N42SH is therefore a narrow pole, 11 to 12 mm
  thick**, which is exactly 30 × 15 × 12 (S1d, 113 °C). Its only weakness
  is 9 % more copper loss and the 29-turn winding.
- **If the 28-turn winding must stay,** the best block is **span 0.70,
  11 mm**: a **33.2 × 14.8 × 11 mm** block, five per pole along the stack.
  - It gives 379 V and Rev B's copper loss with 8.21 kg of magnet, and keeps 20 % margin to 106 °C.
  - It cogs 1.3 Nm unskewed, so the step skew is still advised.
  - It is not a catalogue size, but it is a plain made-to-size block that most makers cut from standard stock without tooling.

### 3.2 Custom shapes

- **Parallel magnetisation beats radial on both counts.** At span 0.72,
  11 mm thick, the parallel arc (AP72_11) gives 399 V with 28 % margin at
  100 °C, against 402 V with 22 % for the radial arc (AR72_11). Parallel
  magnetisation points the material at the pole edges towards the pole
  centre, away from the reverse field.
- **An arc beats a flat block of the same span and thickness.** At span
  0.68, 11 mm thick, the arc (AP68_11) gives 387 V with 30 % margin,
  against 374 V with 27 % for the flat block (B68_11). The arc fills the
  corners that a flat block leaves as a thick bond line, its gap face stays
  at r 301.5 across the whole pole, and the bond is uniform.
- **Loaf shapes are the wrong direction for N42SH.** Thinning the edges
  lowers cogging and THD, but the thin edges are exactly where the short
  circuit demagnetises. Lifting the edges by 4 mm costs 7 to 10 K of
  reserve.
- **AP68_11 is the best balance.**
  - 387 V with 28 turns.
  - Copper loss 4 % below Rev B, 11 % below 30 × 15 × 12.
  - 110 °C reserve, 8.11 kg of magnet.
  - 0.5 Nm cogging unskewed (0.07 % of rated torque). The skew can be dropped, along with the stepped comb bars and the skew template.

  AP63_12 has the same mass and margin as S1d and 3 % more EMF, but it
  still needs 29 turns and skew.

### 3.3 Proposed custom part (AP68_11)

| Item | Value |
|---|---|
| Shape | Arc segment, inner R 301.50, outer R 312.50 (11.0 thick), angle 6.12° (chord 32.2 mm at the inner face) |
| Length | 4 pieces along the stack, 18.4 mm each (eddy loss about 6 W) |
| Grade, magnetisation | N42SH, **parallel** to the segment's centre line, NiCuNi as doc 19 §8 |
| Count | 160 + 8 spares, one part for N and S poles (flipped) |
| Seat | Ø625.3 (uniform 0.15 bond), drum steel under it 10.4 mm |
| Comb bars | Plain straight G11 bars, no skew steps (about 15 mm wide at the gap face) |
| Tolerances (to agree with maker) | Radii ±0.05, thickness ±0.05, angle ±0.05°, length ±0.1 |

Buying a custom arc means:

- grinding fixtures or press tooling;
- a minimum order, typically a few hundred to a few thousand pieces;
- a longer lead time (my guess: 8 to 12 weeks to samples);
- a piece price above plain blocks.

Neo (Narva) and VAC both make arc segments in SH grades. Ask for it as a
second line on the same RFQ.

## 4. Open items

| # | Item |
|---|---|
| O1 | All N42SH options still need the doc 19 §16.3 conditions (bench magnet temperature ≤ 75 °C, temperature watch, no deliberate shorting) |
| O2 | Quote AP68_11 from Neo and VAC (tooling, MOQ, lead time) next to the 30 × 15 × 6 catalogue blocks |
| O3 | If AP68_11 is chosen: geometry module, drawings and a doc 20 style build document; 3D end-effect check |
| O4 | For B70_11 or AP68_11: rerun the full doc 06 load and thermal check (only EMF, cogging and demag were computed here) |

## Appendix. How to rerun

```
cd analysis/generator
python3 optshape.py B70_11 AP68_11 S1d    # one or more cases, ~6 min each -> results/opt_<case>.json
python3 optshape.py table                 # -> results/opt_summary.json and a printed table
```
