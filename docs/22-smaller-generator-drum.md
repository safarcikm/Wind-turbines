# 12 kW Wind Turbine for Iceland: Smaller Generator Drum (Ø490 and Ø290) with 30 × 15 × 12 Magnets

Status: **study** · 2026-11-05 (Martin: "make a version with a drum diameter less then 500mm and less then 300mm, using 30x15x12 blocks and make a document comparing the larger version (with same magnets) also how it will affect the energy output")  
Builds on: [06 – Generator round 2](06-generator-round2.md) (electromagnetic design, losses), [12 – Power electronics](12-power-electronics.md) (efficiency chain, annual energy), [20 – N42SH 30 × 15 × 6 variant](20-magnet-variant-n42sh.md) (the magnet pole used here)  
Analysis: [`analysis/generator/smalldrum.py`](../analysis/generator/smalldrum.py) → `results/small_P1.json`, `small_D490.json`, `small_D290.json`, [`small_summary.json`](../analysis/generator/results/small_summary.json)

## Summary

The turbine rotor turns at 178 rpm at rated wind whatever the generator
looks like. A direct-drive generator's power therefore comes only from its
torque. Torque grows with the **square of the air gap diameter** times the
stack length, and a smaller machine also has room for less copper. Halving
the drum diameter cuts the torque of the same stack length by much more
than half.

| | **Present (doc 20)** | Ø490, full power | Ø490, 74 mm stack | Ø290, full power | Ø290, 74 mm stack |
|---|---|---|---|---|---|
| Drum outside diameter | 646 mm | 490 mm | 490 mm | 290 mm | 290 mm |
| Poles / slots | 40 / 45 | 32 / 36 | 32 / 36 | 16 / 18 | 16 / 18 |
| Stack length | 74 mm | **155 mm** | 74 mm | **1,128 mm** | 74 mm |
| Torque at sizing current | 802 Nm | 802 Nm | 383 Nm | 802 Nm | 53 Nm |
| Rated shaft power | 13.6 kW | 13.6 kW | **6.5 kW** | 13.6 kW | **0.9 kW** |
| Generator efficiency at rated | 93.9 % | 93.8 % | 92.9 % | 91.7 % | 84.7 % |
| 30 × 15 × 6 blocks (magnet mass) | 400 (8.2 kg) | 640 (13.1 kg) | 320 (6.6 kg) | 2,368 (48.5 kg) | 160 (3.3 kg) |
| Active mass (magnet, copper, laminations, drum band) | 89 kg | 122 kg | 61 kg | 326 kg | 23 kg |
| Annual energy at 6 m/s average | 31.6 MWh | 31.5 MWh (−0.1 %) | 22.1 MWh (**−30 %**) | 30.9 MWh (−2 %) | 3.4 MWh (**−89 %**) |
| Annual energy at 8 m/s average | 51.1 MWh | 51.0 MWh (−0.1 %) | 30.9 MWh (**−40 %**) | 50.0 MWh (−2 %) | 4.0 MWh (**−92 %**) |

**What it means:**

- **Under 500 mm (Ø490):** this is **feasible if the stack grows from 74 to
  155 mm**. Energy output is unchanged (−0.1 %). The cost is 60 % more
  magnet (640 blocks), 40 % more laminations, and a drum 81 mm longer, which
  has to fit the nacelle and spindle layout. Keeping the 74 mm stack halves
  the generator: 6.5 kW rated, and 22 to 44 % less energy per year
  depending on the site.
- **Under 300 mm (Ø290):** this is **not workable as a direct-drive 12 kW
  generator**. With a 74 mm stack it is a 0.9 kW generator, about 90 % less
  energy. For full power it would need a 1.13 m long stack with 48 kg of
  magnet and 326 kg of active material, almost four times the present
  machine. The Ø140 main spindle also leaves only 6.5 mm for the stator
  carrier wall, so the slots can only be 30 mm deep. A generator this small
  only makes sense with a gearbox (about 1:15, so the 74 mm Ø290 machine runs at about 2,700 rpm), which is
  a different turbine concept from the direct drive chosen in doc 04.
- **Same magnets, same pole:** both small machines keep the doc 20 pole
  (30 × 15 × 12, about the same pole pitch, rows skewed). Their short-circuit
  margin at 100 °C is 26 to 27 %, against 32 % in the present machine,
  because the smaller machines' fault current is relatively higher. Both are
  still above the 20 % rule at 100 °C.

**Recommendation:** if the present Ø646 drum is too big for the nacelle or
for transport, **Ø490 with a 155 mm stack** is the realistic smaller
generator. It gives the same energy, but it is heavier and longer and needs
a nacelle fit check. A drum under 300 mm cannot give 12 kW in direct drive.

## 1. How the small machines were laid out

Every machine uses the doc 20 rotor pole:

- one 30 mm wide, 12 mm magnet across each pole (two N42SH 30 × 15 × 6 blocks bonded);
- rows of 15 mm blocks along the stack;
- 0.15 bond, 2 mm air gap, 0.5 mm sleeve;
- 9 mm of drum steel under the seat.

The stator keeps:

- the P1's tooth-coil winding family (9 slots per 8 poles);
- the same share of tooth width in the slot pitch;
- the same current density and slot fill (doc 06 sizing point).

| | P1 (present) | Ø490 | Ø290 |
|---|---|---|---|
| Air gap diameter | 600 | 444 | 243 |
| Drum seat | Ø628.0 | Ø472.0 | Ø272.0 |
| Poles / slots | 40 / 45 | 32 / 36 | 16 / 18 |
| Pole pitch at the magnet / pole span | 47.4 / 0.63 | 43.9 / 0.68 | 48.3 / 0.62 |
| Electrical frequency at 178 rpm | 59.3 Hz | 47.5 Hz | 23.7 Hz |
| Slot depth | 65 | 60 | **30** (spindle) |
| Stator bore | Ø437 | Ø292 | **Ø153** (spindle Ø140) |
| Copper area per slot side | 466 mm² | 362 mm² | 194 mm² |

For the Ø290 machine the slots are limited twice. They close up towards
the small inner radius, and the Ø140 main spindle (doc 07) has to pass
through the stator. That leaves 30 mm deep slots, so the Ø290 machine has
only 41 % of the P1's ampere-turns per metre of circumference on top of its
smaller diameter.

## 2. FEA results (per 74 mm of stack, magnets at 100 °C)

| | P1 | Ø490 | Ø290 |
|---|---|---|---|
| Torque at the sizing current density | 760 Nm (2D) | 364 Nm | 50 Nm |
| Torque relative to P1 | 1 | 0.48 | 0.066 |
| Expected from D² × electric loading | 1 | 0.46 | 0.067 |
| Line EMF per turn per coil, 178 rpm | 13.1 V | 8.0 V | 2.0 V |
| Turns per coil for 380 V (74 mm stack) | 29 | 47 | 186 |
| Turns per coil for 380 V (full-power stack) | 29 | 23 | 12 |
| Short-circuit current / sizing current | 1.9 | 2.4 | 5.3 |
| Transient short-circuit margin at 100 °C | 32 % | 26 % | 27 % |

The FEA confirms the simple rule: torque goes with D² times electric
loading. The 2D torques are scaled by the same factor, so that the P1 makes
its doc 06 value of 802 Nm. End effects are left out, which slightly
flatters the short Ø290 stack.

## 3. Two ways to use a smaller drum

**A. Keep 12 kW: lengthen the stack.** The stack length needed is
802 Nm divided by the torque per metre:

- Ø490: 155 mm, which is 10 rows of magnets instead of 5;
- Ø290: 1,128 mm.

Copper loss stays about the same at Ø490 (503 W against 496 W). The end
turns are a smaller share of the longer coils, which balances the longer
stack. At Ø290 copper loss rises to 803 W, and iron loss stays about the
same (more laminations, lower frequency).

**B. Keep the 74 mm stack: the generator caps the power.** The torque at
the same current density is the new limit. The turbine pitches to hold
that power, so rated power falls to 6.5 kW (Ø490) or 0.9 kW (Ø290).

## 4. Energy output

The doc 12 power curve and efficiency chain is used: rotor optimum below
rated, pitch-limited above, active rectifier, grid inverter, 120 W
auxiliaries, Rayleigh wind and 97 % availability. Only the generator's
losses and torque limit change. Net energy per year:

| Average wind speed | 5 m/s | 6 m/s | 7 m/s | 8 m/s | 10 m/s |
|---|---|---|---|---|---|
| Present Ø646, 74 mm (MWh) | 20.7 | 31.6 | 42.0 | 51.1 | 65.1 |
| Ø490, 155 mm | 20.7 (−0.2 %) | 31.5 (−0.1 %) | 41.9 (−0.1 %) | 51.0 (−0.1 %) | 65.0 (−0.1 %) |
| Ø490, 74 mm | 16.2 (−22 %) | 22.1 (−30 %) | 27.0 (−36 %) | 30.9 (−40 %) | 36.2 (−44 %) |
| Ø290, 1,128 mm | 20.3 (−2.0 %) | 30.9 (−2.1 %) | 41.0 (−2.2 %) | 50.0 (−2.3 %) | 63.6 (−2.3 %) |
| Ø290, 74 mm | 2.9 (−86 %) | 3.4 (−89 %) | 3.7 (−91 %) | 4.0 (−92 %) | 4.3 (−93 %) |

The windier the site, the more a power-capped generator loses, because
more of the year is spent above its smaller rated power. Iceland's coastal
and highland sites (7 to 10 m/s) are where the 74 mm Ø490 version loses
most: 36 to 44 %.

## 5. What else changes

| | Ø490, 155 mm | Ø290, 1,128 mm |
|---|---|---|
| Drum | 81 mm longer, Ø490; land and comb bars for 10 rows | 1.1 m long tube; not practical on the hub |
| Spindle and bearings (doc 07) | Stator carrier longer; check that the bearing spacing and the brake disc still fit | Spindle must carry a 1.1 m stator; new layout |
| Winding | 23 turns per coil, 36 coils | 12 turns per coil, 18 coils |
| Cooling | Copper loss about the same, gap area 2.2 × larger: cooler per m² | 1.6 × the present copper loss (803 W), through a Ø153 bore with no room for an air channel |
| Power electronics | Unchanged (same voltage and current class) | Unchanged electrically; 24 Hz at rated |
| Magnets | 640 + 32 blocks, 13.1 kg | 2,368 blocks, 48.5 kg |
| Short-circuit margin at 100 °C | 26 % (above the 20 % rule) | 27 % |

## 6. Open items

| # | Item |
|---|---|
| O1 | If Ø490 is wanted: nacelle and spindle fit check for a 155 mm stack and a drum 81 mm longer (docs 07 and 16), and drum stiffness for 10 rows |
| O2 | What drives the smaller drum: transport size, nacelle cover, weight or cost? With that known, a middle size (for example Ø560 with about a 100 mm stack) may be the better compromise |
| O3 | Full doc 06 thermal check of the chosen size |

## Appendix. How to rerun

```
cd analysis/generator
python3 smalldrum.py fea P1 D490 D290    # FEA, ~5 min each (P1 first) -> results/small_<key>.json
python3 smalldrum.py energy              # losses, power curves and annual energy -> results/small_summary.json
```
