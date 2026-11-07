# 39 · 12 kW M8 on the 8 m tower: manufacturing cost of every part

Date 2026-11-07 · basis: doc 37 build book and `bom8.csv` (88 lines) · status: ESTIMATE, no supplier quotes yet

Martin, 2026-11-07: "Ok now lets do detailed cost of manufacturing. Break down every part so we can then focus on optimising."

| Deliverable | File |
|---|---|
| Cost workbook, live formulas (Summary, Top drivers, Parts, Rates, LC8 comparison) | `analysis/cost_m8/out/39-m8-cost-breakdown.xlsx` |
| Model script (writes the workbook and `out/cost_m8.json`) | `analysis/cost_m8/cost_m8.py` |

Project files copy: `turbine-12kw-m8/cost/`.

## Bottom line

**One M8 turbine costs about €122,000 to make (17.7 M ISK) at the factory gate, €132,000 with 8 % contingency, and about €149,000 installed on firm ground (21.6 M ISK).** That is a series build of 50 turbines, made in Iceland as far as practical.

**About half of it is labour: 767 shop hours per turbine, €63,000.** Bought-in parts are 38 % (€46,000). Raw material is only 7 % (€8,600), and outside services such as galvanising, stress relief and NDT are 3 %. So **cutting hours matters much more than cutting kilograms.** The earlier €/kg cost model (docs 27 and 38) came out lower because it did not count Iceland shop hours properly. Its ranking of M8 against LC8 still holds.

**The four largest subsystems are hub and pitch (€20.7k), electrical and power electronics (€20.4k), generator (€18.2k) and spindle and brake (€16.2k).** Together they are 62 % of the ex-works cost.

## 1 · Rate assumptions

All rates are in the **Rates** sheet. Change one and the whole workbook updates.

| Item | Value | Basis |
|---|---|---|
| Welding, cutting, fitting | €80/h | Iceland skilled wage ≈ 1.0 M ISK/month + 25 % employer cost + workshop overhead |
| CNC machining, press shop | €105/h | including machine depreciation |
| Composites | €72/h | |
| Winding, electrical, electronics | €78/h | |
| Assembly, magnet work, test, QA | €75/h | |
| Site crew | €85/h | including van and travel time |
| Steel S355 plate | €1.45/kg | EU price + ≈ 12 % freight to Iceland |
| 42CrMo4 forged spindle blank | €5.50/kg | QT, 3.1 certificate |
| M270-35A self-bonding | €4.20/kg | 55 % strip use |
| Copper wire, class 200 | €16/kg | |
| **NdFeB N45SH, non-Asian** | **€150/kg** | RFQs are still open: ±30 % |
| Carbon UD / glass / epoxy | €28 / 4.80 / 11 per kg | |
| Concrete C30/37 XF4 | €310/m³ | delivered |
| Galvanising / C5 paint / stress relief | €0.95 / 1.10 / 0.60 per kg | |
| **Tooling write-off** | **50 turbines** | about 2 years at 25 per year |
| Exchange rate | 145 ISK/€ | as in doc 27 |

**Scope.** The figures include material with its scrap (a buy factor on every line), labour, outside services, bought-in parts and a share of the tooling. They leave out development, certification, software, warranty, sales, margin and VAT.

**Lines added to the BOM.** The workbook marks these with "+". The BOM does not list them, but a real build needs them:

- the hydraulic unit that releases the brake calipers (doc 14 makes the calipers hydraulically released)
- the base cabinet internals
- assembly and test labour for each subsystem
- coating
- tooling, fixtures and the test benches

## 2 · Roll-up by subsystem

| Subsystem | Material | Labour | Services | Bought-in | **Total €** | Share | Hours |
|---|---|---|---|---|---|---|---|
| 1 Blades (3) | 1,484 | 10,257 | 90 | 1,110 | **12,941** | 10.6 % | 136 |
| 2 Hub and pitch | 720 | 8,186 | 829 | 10,936 | **20,671** | 17.0 % | 96 |
| 3 Generator | 3,144 | 13,442 | 440 | 1,180 | **18,206** | 14.9 % | 161 |
| 4 Spindle and brake | 832 | 5,972 | 618 | 8,731 | **16,153** | 13.3 % | 64 |
| 5 Nacelle and bedplate | 539 | 4,560 | 419 | 1,430 | **6,948** | 5.7 % | 56 |
| 6 Yaw | 411 | 5,894 | 472 | 5,702 | **12,479** | 10.2 % | 66 |
| 7 Electrical and power electronics | 106 | 6,728 | 24 | 13,510 | **20,367** | 16.7 % | 86 |
| 8 Tower 8 m | 1,267 | 3,735 | 1,153 | 108 | **6,264** | 5.1 % | 44 |
| 9 Final assembly and test | 0 | 3,792 | 0 | 410 | **4,202** | 3.4 % | 50 |
| 10 Tooling (÷ 50) | 61 | 414 | 2 | 3,170 | **3,647** | 3.0 % | 6 |
| **Ex-works** | **8,564** | **62,981** | **4,047** | **46,287** | **121,878** | 100 % | **767** |
| Contingency 8 % | | | | | 9,750 | | |
| **Ex-works with contingency** | | | | | **131,629** | | |
| 11 Foundation, firm ground | 2,745 | 3,360 | 38 | 4,189 | 10,332 | | 40 |
| 12 Transport, erection, commissioning | 0 | 3,910 | 0 | 2,900 | 6,810 | | 46 |
| **Installed** | | | | | **148,771** | | |

Generator magnets count as material. The power electronics count as bought-in components plus in-house assembly hours.

**Hours by trade, per turbine:** welding and fabrication 174 h, machining 156 h, composites 159 h, electrical 154 h, assembly 124 h.

## 3 · The 25 largest lines (ranking)

| # | Part | € per turbine | Cumulative |
|---|---|---|---|
| 1 | Blades NM8-100 (3): 118 h lay-up and finishing, glass, carbon, epoxy | 11,066 | 9 % |
| 2 | Brake calipers 4.8 kNm × 3 (bought) | 5,700 | 14 % |
| 3 | Tower 8 m (30 h welding, galvanised) | 5,071 | 18 % |
| 4 | Hub weldment NM8-200 (22 h welding + 14 h boring mill) | 4,264 | 21 % |
| 5 | Magnets 280 × N45SH, of which **28 h insertion labour** | 4,185 | 25 % |
| 6 | Electric pitch cylinder | 3,875 | 28 % |
| 7 | AC module (grid-tie/heating) | 3,576 | 31 % |
| 8 | 48 V battery module | 3,562 | 34 % |
| 9 | Rotor drum weldment (84 fins and ribs) | 3,409 | 37 % |
| 10 | Base cabinet internals (not in BOM) | 3,348 | 39 % |
| 11 | Bedplate NP8-300 | 3,003 | 42 % |
| 12 | Pitch bearings × 3 | 2,962 | 44 % |
| 13 | Supercap + pitch drive | 2,912 | 47 % |
| 14 | Yaw gearmotors × 2 | 2,900 | 49 % |
| 15 | Tower-top adapter NY-400 | 2,828 | 51 % |
| 16 | Brake release hydraulic unit (not in BOM) | 2,609 | 54 % |
| 17 | Spindle (forged, 16 h machining) | 2,521 | 56 % |
| 18 | Coils (45, 21 h winding) | 2,418 | 58 % |
| 19 | Active rectifier | 2,330 | 60 % |
| 20 | Stator carrier (45 dovetail grooves) | 2,306 | 62 % |
| 21 | Stator assembly, VPI, potting, tests | 2,166 | 63 % |
| 22 | Nacelle final assembly | 1,974 | 65 % |
| 23 | Root inserts × 36 | 1,875 | 66 % |
| 24 | Stator laminations (13,365 sheets) | 1,782 | 68 % |
| 25 | Yaw slewing ring | 1,650 | 69 % |

**These 25 lines make up 69 % of the cost. The other 85 lines make up 31 %.** By function, three groups stand out:

- **Pitch system, about €15k.** Bearings, cylinder, supercap, cranks, links, yoke, nose frame, slip ring, bolts and assembly.
- **Brakes, €8.3k.** Three calipers and their release unit.
- **Power electronics, €14k.** The front end, the two output modules and the controller.

## 4 · Where to optimise (estimated savings per turbine)

| Lever | Saving | What it costs or risks |
|---|---|---|
| **Pitch system → fixed pitch (LC8)** | **≈ −€17k** | A different product: +5.5 dB, more erosion (doc 38) |
| **Labour learning and fixtures**: kitted materials, weld fixtures, pre-cut blade plies, target −20 % hours by unit 50 | **≈ −€12k** | Needs time studies on the prototype build |
| 48 V battery module only for off-grid orders (an option, not standard) | −€3.6k on grid and heating units | None. It is a plug-in module (doc 12) |
| Cast hub EN-GJS-400-18U-LT instead of the welded one | ≈ −€2.5k | Pattern ≈ €15k, foundry outside Iceland |
| Bought PMG wind inverter instead of in-house rectifier + AC module | ≈ −€2.8k | Less control of the heating mode and the safety chain |
| Brake: 2 × 7.2 kNm (D2 alternative), or electromechanical release without hydraulics | −€1.5k to −€3k | Caliper availability for −40 °C |
| Blades: fewer hours per blade (38 → 25 h) | ≈ −€2.8k | Part of the learning-curve lever |
| 21 mm magnet block, 200 pieces (doc 36) | ≈ −€0.8k insertion labour | Decision pending (doc 36) |
| Bolted aluminium fin ring on the drum instead of 84 welded fins | ≈ −€1k | Thermal check |

**What does not help much:**

- **Production volume.** Tooling is only 3 % of the cost. At 10 turbines the cost is €136k, at 25 €126k, at 100 €120k, at 200 €119k.
- **The magnet price.** €100 to €250/kg moves the total by only −€0.6k to +€1.2k, because 11.6 kg of magnet is a small share. The magnet cost is in the handling labour.
- **Steel mass.** All steel material together is under €5k.

## 5 · Comparison with LC8 (doc 38)

I priced LC8 as the same lines, with the doc 38 changes:

- no pitch system and no slip ring
- 18.7 kg blades with 10 inserts each, and a smaller mould
- fixed welded hub of 98 kg
- Rev C generator with 5 rows and 200 magnets
- 1 caliper
- NS6-300 bedplate, yaw ring Dpw 360 and a lighter adapter

Same rates, same tower and same site.

| Subsystem | M8 € | LC8 € | Difference |
|---|---|---|---|
| Blades | 12,941 | 10,264 | −2,677 |
| Hub and pitch | 20,671 | 3,541 | −17,130 |
| Generator | 18,206 | 16,740 | −1,466 |
| Spindle and brake | 16,153 | 11,820 | −4,333 |
| Nacelle, yaw | 19,427 | 19,132 | −295 |
| Electrical | 20,367 | 20,367 | 0 |
| Tower, final assembly, tooling | 14,113 | 13,843 | −270 |
| **Ex-works** | **121,878** | **95,706** | **−26,172 (−21 %)** |

This agrees with doc 38's −23 %. **LC8 has not been designed for the 8 m tower.** At 178 rpm its 1P frequency is 2.97 Hz, right on the tower's 2.78 Hz, so its tower here is only a placeholder.

## 6 · Limits of this estimate

- **Bought-in prices are list-level estimates, not quotes.** In particular: calipers, hydraulic unit, pitch cylinder, slewing rings, gearmotors, magnets and the cold-climate anemometer. Quotes for the top 10 bought items would firm up about 30 % of the total.
- **Hours are engineering estimates for a trained crew.** The first units will take longer. Log real hours on the prototype and put them into the Parts sheet.
- Galvanising the 7 m tower needs a long enough bath, which may mean shipping it. Freight is in the rate, not as a separate line.
- **Not included:** development, the prototype build, certification (IEC 61400-2), software, warranty reserve, sales, margin, VAT, and soft-ground foundations (+0.8 to +1.6 m³ of concrete, doc 37 §3).

## 7 · Rebuilding

```
cd analysis/cost_m8
python3 cost_m8.py      # writes out/39-m8-cost-breakdown.xlsx and out/cost_m8.json
```
To see a change, edit the rates or hours directly in the workbook. To change the model itself, edit the part lines in `cost_m8.py`.
