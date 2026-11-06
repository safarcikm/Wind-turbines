# 12 kW Wind Turbine for Iceland: Size and TSR Decision Map

Status: **Draft, revision 1** · 2026-11-06
Owner: Category 1 (Systems engineering) and Category 13 (Product and business)
Request (Martin, 2026-11-06): "a comparison of theoretical values for kW output 4–20 kW in 2 kW steps, TSR 4–8, blade speeds, sound levels and annual power output for Iceland (maybe different scenarios). I need a high-level tool to decide which direction to go. It should also have a cost to power output comparison."
Builds on: [03 – Rotor](03-rotor-concept.md), [08 – Loads](08-load-verification.md), [09 – Tower](09-tower-foundation.md), [12 – Power electronics](12-power-electronics.md), [26 – Slow variant V5](26-slow-rotor-variant-v5.md)
Model: [`analysis/size_tsr_map/`](../analysis/size_tsr_map/) · Interactive page: `analysis/size_tsr_map/results/size_tsr_map.html` (also published as an Artifact) · Full table: [`results/grid.csv`](../analysis/size_tsr_map/results/grid.csv), 567 designs

## Summary

The map covers 9 ratings (4–20 kW) × 9 design TSRs (4.0–8.0 in 0.5 steps) × 7 rated wind speeds (9–12 m/s). For each design it gives the rotor diameter, rpm, tip speed, sound power and sound at distance, net annual energy at four Icelandic site types, storm loads, masses and a rough installed cost and cost of energy.

The four things it shows:

1. **TSR does not change energy. Diameter does.** At a fixed rating and rated wind, TSR 4 and TSR 8 give the same diameter within 2 % and the same annual energy within 1 %. TSR only moves the trade between **tip speed** (noise, erosion) and **blade width** (storm loads, mass, cost).
2. **Noise is the binding limit for the current rotor.** With the empirical sound model, the current Ø7.5 m / 178 rpm rotor gives about **47 dB(A) at 60 m** at 8 m/s wind. Our own requirement R2.7 is 45 dB(A). TSR ≤ 5.5 meets it. This needs a measurement before we trust it (±4 dB), but it points the same way as doc 26.
3. **Within the noise and tip-speed limits, the best 12 kW design is about Ø8.0 m, TSR 5.5, ≈ 131–135 rpm**, rated at 10 m/s. That is the "middle option" doc 26 suggested. It gives **+8.5 % energy** at inland sites and is 2.3 dB quieter than the current rotor, for **+14 % installed cost**. Cost of energy is 5 % higher than the current rotor, which breaks the noise target.
4. **Bigger machines are cheaper per kWh.** 20 kW costs about 16 % less per MWh than 12 kW, because control, electronics, installation and the yaw are partly fixed costs. That only matters if the grid connection and customers allow more than 12 kW.

**Recommendation:** keep the 12 kW rating, move the baseline study to **Ø8.0 m, TSR 5.5, ≈ 135 rpm**, and do an early sound measurement on the first prototype. Details and the reasoning are in §6.

---

## 1. How each design is made

Every cell of the map is a full turbine built with the same rules. Nothing is hand-tuned per cell.

**Rotor.** The doc 03 blade rule (Schmitz chord with linear taper, design Cl 1.0, three blades, hub radius scaled with the rotor) is built for each design TSR and solved with the doc 03 BEM model and weathered (rough) polars (`cp_tables.py`). The results are non-dimensional, so one table per TSR serves every size.

**Sizing rule.** The rotor reaches rated shaft power (13.6 kW per 12 kW electrical) at the chosen rated wind, running at its design TSR and maximum rpm: tip speed = TSR × rated wind. Fed with the rated winds the two real designs have, the rule gives **Ø7.53 m** for the current rotor (real 7.5) and **Ø8.24 m** for V5 (real 8.3).

**Operation and energy.** Variable speed at the optimum TSR up to the rpm limit, then constant rpm with pitch, storm ramp 25–30 m/s (doc 11), lowest speed 25 % of rated. Losses: the doc 12/26 chain (generator copper, iron, rotor, rectifier, inverter, auxiliaries) scaled with rating and rated speed. 97 % availability, 1.225 kg/m³.

**Calibration check** (`calibration.json`): the fast model reproduces the doc 26 yearly energy of both designs within **0.6–1.1 %** at 5–8 m/s, and their SLM H parked loads within 1 %.

## 2. Icelandic site scenarios

Weibull wind at the 18 m hub. These are typical values, to be replaced by Veðurstofa or site data for a real customer.

| Scenario | Mean wind | Weibull k | Example |
|---|---|---|---|
| Sheltered valley / farm | 5.0 m/s | 1.8 | farmyard with buildings and trees, inland valley |
| Open inland lowland | 6.0 m/s | 1.9 | open Suðurland farmland |
| Coast / exposed lowland | 7.0 m/s | 2.0 | Reykjanes, Snæfellsnes coast |
| Highland / headland | 8.5 m/s | 2.0 | highland edge, exposed headland |

Not included: icing losses (could be 3–10 % at highland sites) and the 2–3 % gain from cold dense air.

## 3. Sound

Sound power at 8 m/s wind (the IEC 61400-2 reference) uses Hau's empirical rule, **LwA = 50·log10(tip speed) + 10·log10(D) − 4**. Sound pressure at distance uses hemispherical spreading from the 18 m hub and 3 dB/km air absorption. The absolute level is uncertain by about ±4 dB. Differences between designs are far more reliable, because they come from the tip speed term. Tonal noise from the generator and converter is not in the model.

At 8 m/s every rotor still runs below its rpm limit, so its tip speed is its optimum TSR × 8 m/s. That is why TSR, not rating, drives noise:

**12 kW, rated at 10.5 m/s (the current rated wind):**

| TSR | Ø m | rpm | Tip at rated, m/s | LwA, dB(A) | at 60 m | at 100 m | to 40 dB(A) | MWh/yr, inland | Parked blade root, kNm | Torque, Nm | Head, kg | Cost, k€ | €/MWh, inland |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 4.0 | 7.53 | 107 | 42 | 83.8 | 39.7 | 35.3 | 57 m | 29.9 | 66 | 1,219 | 1,475 | 104 | 374 |
| 4.5 | 7.48 | 121 | 47 | 83.7 | 39.6 | 35.3 | 57 m | 30.0 | 52 | 1,076 | 1,355 | 96 | 345 |
| 5.0 | 7.45 | 135 | 52 | 86.9 | 42.8 | 38.5 | 84 m | 30.0 | 42 | 964 | 1,266 | 90 | 323 |
| **5.5** | 7.42 | 149 | 58 | 88.8 | **44.7** | 40.3 | 104 m | 30.0 | 35 | 874 | 1,198 | 86 | 307 |
| 6.0 | 7.42 | 162 | 63 | 90.5 | 46.4 | 42.1 | 127 m | 30.0 | 29 | 800 | 1,143 | 82 | 293 |
| 6.5 (≈ current) | 7.41 | 176 | 68 | 91.3 | 47.2 | 42.9 | 139 m | 30.0 | 25 | 739 | 1,099 | 79 | 283 |
| 7.0 | 7.41 | 189 | 74 | 92.9 | 48.8 | 44.4 | 165 m | 30.0 | 22 | 686 | 1,062 | 77 | 275 |
| 7.5 | 7.42 | 203 | 79 | 94.3 | 50.2 | 45.9 | 193 m | 30.0 | 19 | 641 | 1,031 | 75 | 268 |
| 8.0 | 7.43 | 216 | 84 | 95.7 | 51.6 | 47.3 | 224 m | 30.0 | 17 | 602 | 1,004 | 73 | 262 |

Read across one row of the map and the picture is clear: energy is flat, noise falls by 12 dB from TSR 8 to TSR 4, and the parked blade root moment rises by a factor of 4. Cost per MWh rises as TSR falls, because blades, hub, generator torque, yaw and tower all follow the storm load. The tip speed limit of doc 03 (70 m/s, erosion) rules out TSR ≥ 7 at this rated wind.

Icelandic noise rules (reglugerð 724/2008) need checking for each site type. The project target R2.7 (45 dB(A) at 60 m) is the limit used on the map by default. Both limits can be changed on the page.

## 4. Rating 4–20 kW

**TSR 5.5, rated at 10.5 m/s:**

| kW | Ø m | rpm | LwA | to 40 dB(A) | MWh/yr sheltered | inland | coastal | highland | Head, kg | Cost, k€ | €/kW | €/MWh inland | €/MWh coastal |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 4 | 4.3 | 257 | 86.4 | 79 m | 6.3 | 9.5 | 12.8 | 17.2 | 570 | 48 | 11,937 | 538 | 400 |
| 6 | 5.2 | 210 | 87.3 | 87 m | 9.8 | 14.6 | 19.6 | 26.2 | 740 | 58 | 9,646 | 425 | 317 |
| 8 | 6.1 | 182 | 87.9 | 94 m | 13.3 | 19.7 | 26.3 | 35.2 | 898 | 67 | 8,431 | 367 | 274 |
| 10 | 6.8 | 163 | 88.4 | 99 m | 16.8 | 24.9 | 33.1 | 44.2 | 1,050 | 77 | 7,671 | 331 | 248 |
| 12 | 7.4 | 149 | 88.8 | 104 m | 20.3 | 30.0 | 40.0 | 53.2 | 1,198 | 86 | 7,149 | 307 | 230 |
| 14 | 8.0 | 138 | 89.1 | 108 m | 23.8 | 35.2 | 46.8 | 62.2 | 1,343 | 95 | 6,768 | 289 | 217 |
| 16 | 8.6 | 129 | 89.4 | 112 m | 27.4 | 40.3 | 53.6 | 71.2 | 1,487 | 104 | 6,478 | 276 | 207 |
| 18 | 9.1 | 121 | 89.7 | 115 m | 30.9 | 45.5 | 60.4 | 80.2 | 1,630 | 113 | 6,250 | 265 | 200 |
| 20 | 9.6 | 115 | 89.9 | 118 m | 34.5 | 50.7 | 67.3 | 89.2 | 1,773 | 121 | 6,067 | 257 | 193 |

At a fixed TSR the tip speed is fixed too, so the sound power grows only with 10·log(D): 4 kW to 20 kW is just +3.5 dB. Cost per kW halves from 4 to 20 kW. Below 8 kW the fixed parts (control, electronics, pitch, yaw, installation) dominate. Outside 8–16 kW the mass and cost figures are extrapolations from two 12 kW designs and are less certain.

## 5. Rated wind speed: the extra axis

Martin asked for suggestions. The most useful extra axis is the **rated wind speed**, which sets the diameter for a given rating (specific power). This is what made V5 bigger, not its TSR.

**12 kW, TSR 5.5, change relative to rating at 10.5 m/s:**

| Rated wind | Ø m | Energy, sheltered | inland | coastal | highland | Installed cost |
|---|---|---|---|---|---|---|
| 9.0 m/s | 9.4 | +40 % | +32 % | +25 % | +17 % | +22 % |
| 9.5 m/s | 8.6 | +25 % | +21 % | +17 % | +12 % | +13 % |
| **10.0 m/s** | **8.0** | **+12 %** | **+10 %** | **+8 %** | **+6 %** | **+6 %** |
| 10.5 m/s | 7.4 | 0 | 0 | 0 | 0 | 0 |
| 11.0 m/s | 6.9 | −11 % | −9 % | −8 % | −6 % | −5 % |

A bigger rotor on the same generator pays at sheltered and inland sites and pays least where storms are worst. The page has a rated-wind menu for this axis.

## 6. Decision

### The three 12 kW designs (exact geometry, not the sizing rule)

| Design | Ø | rpm | Tip, m/s | LwA | at 60 m | to 40 dB(A) | MWh/yr: 5 / 6 / 7 / 8.5 m/s | Parked blade root | Head | Tower | Cost | €/MWh: 5 / 6 / 7 / 8.5 m/s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Current | 7.5 m | 178 | 70 | 91.4 | 47.3 | 140 m | 20.7 / 30.5 / 40.5 / 53.8 | 26 kNm | 1,104 kg | 1,941 kg | 79.6 k€ | 413 / 280 / 211 / 159 |
| **Middle M8** | **8.0 m** | **135** | **57** | **89.1** | **45.0** | **108 m** | **22.8 / 33.1 / 43.3 / 56.3** | **44 kNm** | **1,277 kg** | **2,394 kg** | **90.6 k€** | **426 / 294 / 224 / 172** |
| V5 | 8.3 m | 110 | 48 | 87.4 | 43.3 | 88 m | 24.0 / 34.4 / 44.7 / 57.5 | 58 kNm | 1,416 kg | 2,754 kg | 99.4 k€ | 445 / 310 / 239 / 185 |

### Best 12 kW design within tip speed ≤ 70 m/s and ≤ 45 dB(A) at 60 m

| Site | Best cell | €/MWh | Current rotor (breaks noise) |
|---|---|---|---|
| Sheltered 5 m/s | TSR 5.0, rated 9.0 m/s, Ø9.4 m, 92 rpm | 423 | 413 |
| Inland 6 m/s | **TSR 5.5, rated 10.0 m/s, Ø8.0 m, 131 rpm** | 295 | 280 |
| Coastal 7 m/s | **TSR 5.5, rated 10.0 m/s, Ø8.0 m, 131 rpm** | 225 | 211 |
| Highland 8.5 m/s | TSR 5.5, rated 10.5 m/s, Ø7.4 m, 149 rpm | 173 | 159 |

### Recommendation

1. **Direction: Ø8.0 m, TSR 5.5, about 135 rpm, 12 kW.** It is the cheapest energy that meets our own noise target at inland and coastal sites, which are most customers. It is a real compromise between the current rotor and V5: two-thirds of V5's energy gain for about half of its load growth, and the tip speed drops to 57 m/s, which also helps against ash and rain erosion (R2.5).
2. **Measure sound early.** The 2.3 dB that separates the current rotor from the target is inside the model's ±4 dB. A sound measurement on the first prototype (IEC 61400-11 style) decides between the current rotor and M8. If the current rotor measures below 45 dB(A) at 60 m, it stays the cheapest.
3. **Keep the rating at 12 kW for now.** Larger machines are cheaper per kWh, but the map cannot judge grid limits (single-phase DSO limit is still open in doc 12) or what Icelandic customers need. A 16–20 kW model is a business question for category 13.
4. **Do not go below TSR 5** for a general product. Below 5 the storm loads, generator torque and cost rise steeply (TSR 4: +57 % parked blade root moment and +16 % cost against TSR 5) for about 3 dB less noise.
5. **Do not go above TSR 6.5.** Above it the tip speed passes 70 m/s and the rotor gets louder, for a few percent lower cost.

If the direction is accepted, the next step is a full M8 design pass like doc 26 (blade, generator stack, hub, yaw, tower), reusing the doc 26 scripts.

## 7. Cost model (rough)

Installed cost per turbine, in-house manufacture, in EUR. No development, tooling, certification, sales margin or VAT. Use it to compare designs, not to set a price.

| Item | Rate |
|---|---|
| Blades | 70 €/kg (carbon/glass epoxy, labour heavy) |
| Generator | 40 €/kg (magnets, copper) |
| Hub and pitch, yaw | 30 €/kg |
| Spindle, nacelle | 25 €/kg |
| Tower | 6 €/kg |
| Footing | 450 €/m³ |
| Power electronics | 6,000 € + 600 €/kW |
| Control and safety | 6,000 € |
| Installation | 4,000 € + 1 €/kg of head and tower |

Masses come from power laws through the two designed turbines: blade by parked root moment (exponent 0.86), hub + pitch and spindle linear in the parked moment with a fixed part, generator by rated torque (exponent 0.5), tower by base moment (0.96), footing by base moment (0.59). Fixed parts scale with √(kW/12). With these rates the current design comes to about 80 k€ (≈ 11.5 M ISK at 145 ISK/€).

Cost of energy = installed cost × (8.7 % capital recovery, 6 % over 20 years, + 2 % O&M per year) ÷ net annual energy.

## 8. Limits of the model

- Generic aerofoil polars, no Reynolds effect: small rotors (4–6 kW) are slightly optimistic.
- Rayleigh/Weibull winds, not measured site data. Absolute energy ±15 %, ratios between designs much better.
- Sound ±4 dB absolute, no tonal noise.
- Storm loads scale with the parked blade planform, calibrated to SLM H. Seismic and fatigue drivers are not modelled separately.
- Masses and costs outside 8–16 kW are extrapolations.
- Leading-edge erosion is shown only as the tip speed limit. It has no cost in the model, so high-TSR designs look a little better than they are.

## Files

| File | Purpose |
|---|---|
| `cp_tables.py` | BEM tables per design TSR (≈ 5 min) |
| `model.py` | sizing, energy, sound, loads, mass, cost; writes `grid.csv`, `map_data.json`, `calibration.json` |
| `build_page.py`, `page_template.html` | the interactive page `results/size_tsr_map.html` |
