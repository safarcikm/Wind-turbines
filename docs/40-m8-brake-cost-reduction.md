# 40 · M8 rotor brake: why it costs €10k and how to halve it

Date 2026-11-07 · basis: doc 39 cost model, doc 37 loads (8 m tower) · status: STUDY, decision for Martin

Martin, 2026-11-07: "Ok we need to look into the brake system, this is way too expensive."

| Deliverable | File |
|---|---|
| Stop with all blades stuck at fine pitch; storm with the brake slipping; free idling | `analysis/brake_m8/brake8.py` → `results/brake8.json` |
| Storm slip statistics on all 36 parked cases | `analysis/brake_m8/creep8.py` → `results/creep8.json` |

## Bottom line

**The brake system costs about €10.2k per turbine today.** That is the three calipers (€5.7k), the hydraulic release unit (€2.6k), two brackets (€1.0k), the disc (€0.7k) and cabling.

**One requirement sets the size: holding the parked rotor without any slip at the 50-year gust peak × 1.35.** The other job, stopping the rotor when the pitch system is dead, needs only about half that torque.

**I recommend going back to 2 calipers (9.6 kNm) with a simpler release pack.** That brings the brake to **≈ €6.6k (−€3.6k)** with the same caliper type. Building the two calipers in-house later would take it to **≈ €5.0k (−€5.2k)**.

The price is a change in the storm rule. Today the brake must hold the factored storm torque with no slip. The new rule would be: hold the characteristic storm torque, and allow brief slip at the factored peak. In the simulation a slipping rotor only idles, because a feathered M8 rotor turning freely in the 50-year storm never goes above 34 rpm. You accepted the same principle for the 6 kW S6 (doc 32).

## 1 · What the brake has to do

| Job | Torque needed | Source |
|---|---|---|
| **Stop the rotor alone from the 165 rpm trip with all three blades stuck at fine pitch, converter lost** (R3.8, doc 24) | **≥ 4.8 kNm** to stop; **≥ 7.2 kNm** to stay under the 184 rpm design overspeed | §2 below |
| Hold the parked, feathered rotor in the 50-year storm at the gust peak | 10.6 kNm characteristic, **14.3 kNm design (× 1.35)**. This sets the 3 × 4.8 kNm today | doc 37 §2 |
| Hold the rotor for maintenance at working wind speeds | small; the lock pin NP1-320 takes over | doc 14 |

The storm holding value is a **short gust peak**. The **mean** torque in the worst parked case is 5.7 kNm.

## 2 · Stop with the pitch system dead

The turbine starts at 165 rpm with all blades at 0° and the converter lost, so no generator torque. The brake applies at once. The wind is turbulent at 15, 25 and 32 m/s.

| Brake | Peak rpm (worst wind) | Time to stop | Heat into the disc |
|---|---|---|---|
| 3.6 kNm | **runaway** at 25 and 32 m/s (> 600 rpm) | — | — |
| 4.8 kNm (1 caliper) | 188 rpm | 3.9 s | 251 kJ, +16 K |
| 7.2 kNm | 183 rpm | 1.8 s | +10 K |
| **9.6 kNm (2 calipers)** | **181 rpm** | **1.3 s** | **+10 K** |
| 14.4 kNm (today) | 179 rpm | 0.9 s | +10 K |

Anything from 7.2 kNm up meets R3.8 with the peak below 184 rpm. Generator torque and the NC resistor contactor K1 are left out, and both would help.

## 3 · Storm parking with a smaller brake

- **Free idling.** I ran the feathered rotor with the brake off in the 50-year wind at 6 yaw errors. It **turns at 20–22 rpm on average and never above 34 rpm**. Its blade and tilt loads stay below the locked parked envelope of doc 37:
  - flap 2.5 vs 9.8 kNm
  - edge 7.4 vs 11.4 kNm
  - tilt 3.8 vs 11.9 kNm

  So a brake that slips cannot cause a runaway. The worst outcome is slow idling.
- **Slipping brake, full simulation.** In the 4 worst parked cases, every brake from 4.8 kNm up holds the rotor. It creeps less than 0.02 of a revolution in 300 s.
- **Slip statistics on all 36 parked cases** (locked-rotor torque series, no aero damping, so conservative):

| Brake | Cases where the gust torque exceeds the brake (characteristic) | Time above the brake, worst case | With the × 1.35 factor |
|---|---|---|---|
| 7.2 kNm | 2 of 36 | 27 s of 300 s | 6 cases slip |
| **9.6 kNm** | **1 of 36** | **0.6 s** (≈ 4° of rotation) | 2 cases, 31 s |
| 14.4 kNm | 0 | 0 | 0 |

With 9.6 kNm the rotor holds the characteristic storm, apart from a few degrees once. Under the factored storm it slips for half a minute in the worst yaw case and idles, which §3 shows is harmless.

## 4 · Cost of the layouts (per turbine, doc 39 rates)

| Layout | Calipers | Release | Brackets | Brake system € | Saving |
|---|---|---|---|---|---|
| A · today | 3 × 4.8 kNm bought, €5,700 | hydraulic unit with accumulator, €2,609 | 2, €1,047 | **10,197** | — |
| **B · 2 calipers, simple pack** | 2 × 4.8 kNm bought, €3,800 | DC mini power pack + NC dump valve, no accumulator, ≈ €1,360 | 1, €614 | **≈ 6,600** | **−3,600** |
| C · B with in-house calipers | 2 × in-house: machined body, disc-spring pack, piston, bought pads, ≈ €1,050 each | as B | 1 | **≈ 5,000** | −5,200 |
| D · 1 large caliper 7.2–9.6 kNm | 1 bought ≈ €2,600 | as B | 1 | ≈ 5,400 | −4,800 |

The disc (€731) and cabling (€110) are in every layout.

Notes:

- **B** is the doc 24 two-caliper layout with the stronger 4.8 kNm spring pack. Nothing new is designed except the release pack. Removing the third caliper also lowers the shutdown edge loads (doc 35 D2).
- **C** needs a design, a type test (clamp force, −40 °C, spring fatigue) and a spring-force test fixture (≈ €5k). Calipers are safety parts, so they need a first-article test before series use.
- **D** puts one-sided load on the spindle bearings (≈ 26 kN tangential at the disc) and leaves no redundancy inside the brake. I don't recommend it for M8.
- A **spring-applied caliper with electromagnetic release** (no hydraulics at all) is worth a supplier quote. I have no reliable price for one at 16 kN clamp force.

## 5 · Decision

- **D-B1:** Change the storm-parking rule to "hold the characteristic storm torque; slip allowed under the factored load (free idling ≤ 34 rpm)", and go to 2 × 4.8 kNm with a simple release pack (layout B). **Recommended.**
- D-B2: Keep the current rule and 3 calipers, and only simplify the release pack. Saves ≈ €1.2k.
- After D-B1: start the in-house caliper (layout C) as a series cost-down item.

**Open checks before release:**
- Bracket and bolt check of the 2-caliper layout under 9.6 kNm.
- The release pack's hold-pressure leak-down at −30 °C.
- Rerun the doc 37 shutdown cases (DLC 5.1, 2.3) with 9.6 kNm, which can only lower the loads.
- Supplier confirmation of the 4.8 kNm spring pack.
