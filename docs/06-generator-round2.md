# 12 kW Wind Turbine for Iceland: Generator Simulation Round 2

Status: **Draft, revision 1** · 2026-11-01
Owner: Category 4 (Generator)
Builds on: [05 – Generator FEA and thermal check](05-generator-fea-thermal.md)
Results: [`analysis/generator/results/iter2/`](../analysis/generator/results/iter2/)
(rerun with `python3 run_fea.py iter2 && python3 thermal.py iter2`)

## What changed from round 1

| Item | Round 1 | Round 2 |
|---|---|---|
| Magnet grade | N42SH (Br 1.30 T, Hcj ≥ 1592 kA/m) | **N40UH** (Br 1.26 T, Hcj ≥ 1990 kA/m) |
| Magnet thickness | 7.4 mm | **7.7 mm** (to compensate for lower Br) |
| Slot depth | 60 mm | **65 mm** |
| Cooling | Plain and improved compared | Improved cooling package is the baseline |

Same model, mesh density and load cases as round 1.

## Results

| Check | Round 1 | **Round 2** | Target | Verdict |
|---|---|---|---|---|
| Air gap flux, fundamental | 1.01 T | **0.99 T** | ≈ 1.0 T | ✅ Magnet thickening compensates the weaker grade |
| Line EMF at rated, 29 turns per coil | 386 V | **379 V** | ≈ 380 V | ✅ Turns unchanged |
| Worst-case peak voltage (cold overspeed) | 836 V | **821 V** | < 1000 V | ✅ |
| Line EMF THD | 0.6 % | **0.5 %** | | ✅ |
| Cogging, peak-to-peak | 0.73 Nm | **0.85 Nm (0.12 %)** | < 0.5 % | ✅ |
| Torque ripple at rated | 1.9 % | **1.9 %** | | ✅ |
| Phase current at 802 Nm | 22.7 A | **23.2 A** | | |
| Current density at 802 Nm | 3.32 A/mm² | **3.20 A/mm²** | ≈ 3.0 | ⚠️ Close; see below |
| Copper loss at 75 °C | 533 W | **496 W** | | ✅ Better |
| Efficiency at rated, 75 °C winding | 93.7 % | **93.9 %** | ≥ 93 % | ✅ |
| **Demagnetisation margin**, worst short circuit at 120 °C | 5.7 % | **28.2 %** | ≥ 20 % | ✅ **Fixed** |
| Winding hot spot, hot day, rated | 95 °C | **92 °C** | ≤ 130 °C | ✅ |
| Hot spot, hot day, weak wake | 99 °C | **96 °C** | ≤ 130 °C | ✅ |
| Hot spot, hot day, 110 % overload | 106 °C | **101 °C** | ≤ 130 °C | ✅ |
| Magnets, worst case | 61 °C | **60 °C** | ≤ 100 °C | ✅ |
| Anti-condensation heating | ≈ 30 W | **≈ 30 W** | | ✅ |

**Every check now passes.** The demagnetisation problem from round 1 is
solved with a comfortable margin, and the hottest case has about 30 K of
headroom below the design limit.

## The one remaining gap: current density

Deepening the slots by 5 mm added only 6 % slot area (882 → 932 mm²),
because the slots narrow towards the stator centre. Together with the
slightly weaker magnets, current density came down from 3.32 to 3.20 A/mm²,
not to the 3.0 target.

A more effective lever is a **longer stack**. In the 2D model, torque at a
given current density scales exactly with stack length, so this is a
calculation, not a guess:

| Stack length | Current density at 802 Nm | Copper loss (75 °C) | Efficiency | Extra active mass |
|---|---|---|---|---|
| 69 mm (round 2) | 3.20 A/mm² | 496 W | 93.9 % | – |
| **74 mm** | **≈ 2.98 A/mm²** | **≈ 447 W** | **≈ 94.2 %** | **≈ +5 kg** |

**Recommendation:** fix the stack length at **74 mm**. That meets the
3.0 A/mm² target and gives about 30 W more efficiency margin and a cooler
winding, for about 5 kg. Turns per coil should be checked again
(about 27 to 28 for 380 V with the longer stack).

## Generator data freeze (concept phase)

| Item | Value |
|---|---|
| Topology | Outer-rotor radial flux, surface PM, tooth-coil winding |
| Poles / slots | 40 / 45 |
| Air gap diameter / mechanical gap | 0.60 m / 2.0 mm |
| Stack length | **74 mm** |
| Magnets | **N40UH**, 7.7 mm, 80 % pole arc, segmented, encapsulated |
| Slot depth / slot area | 65 mm / 932 mm² |
| Winding | ≈ 27 to 28 turns per coil (to confirm), 15 coils per phase in series, star, class H, VPI plus potted end windings |
| Rated | 802 Nm design torque, 178 rpm, ≈ 23 A rms, ≈ 380 V line |
| Worst-case voltage | ≈ 820 V peak (cold overspeed) |
| Efficiency | ≈ 94 % at rated |
| Cooling | Aluminium stator carrier into ventilated hollow spindle, internal fan, drum fins and ribs; fully sealed |

## Next steps

1. Magnet eddy loss (to confirm the 40 W rotor loss and the number of
   magnet segments).
2. Mechanical design of stator carrier, spindle, bearings and drum
   (category 5). The thermal model assumes 0.40 K/W from stator to the
   spindle air, so this must be designed to meet it.
3. Stator segment prototype for winding, VPI, potting and thermal tests.
