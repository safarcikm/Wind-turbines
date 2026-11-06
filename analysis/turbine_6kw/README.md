# 6 kW turbine concept study (doc 28)

Clean-sheet 6 kW machine for Iceland. Question: is variable pitch needed?

| Script | What it does | Output |
|---|---|---|
| `sizing.py` | Runs the doc 27 decision-map model (`analysis/size_tsr_map/model.py`) for 6 kW, rated wind 9–10.5 m/s × TSR 5–6.5, and fixes the chosen rotor | `results/sizing.json`, `results/design.json` |
| `regulation.py` | Same rotor with the doc 03 BEM model: active pitch, stall by speed control (fixed pitch), furling; energy, torque, thrust, runaway, electrical braking, brake stop, parked loads at V_e50 for every yaw error | `results/regulation.json`, `F01`–`F04` figures |

Run in order: `python3 sizing.py` then `python3 regulation.py` (~1.5 min). Needs numpy and matplotlib.

Model limits: steady BEM with 2D Viterna polars. Deep stall at low tip speed ratio is where BEM is weakest; 3D stall delay usually raises the real torque. The doc applies a 1.5× margin on the stall torques for that reason. Parked loads use strip theory without induction, flat plate Cd 1.5 at 90°, cold air 1.35 kg/m³, characteristic values (no partial safety factor).

## Doc 30: complete first-pass design

`python3 design6.py` (after `regulation.py` and `analysis/generator6/g6.py`; needs scipy): SLM loads, blade (doc 10 model), fixed hub, drivetrain reuse check against the 12 kW SLM, yaw ring and yaw-out torque, tower and footings (doc 09 model), electronics ratings. Writes `results/design6.json`, `results/slm_6kw.json`, D01–D02.

## Doc 31: aeroelastic simulation with the stall controller

| Script | What it does | Output |
|---|---|---|
| `sim6.py` | doc 08 simulator (`analysis/loads/sim.py`) with fixed pitch, stall speed control and the K1 resistor + spring brake safety chain | (library) |
| `dlc6.py` | 113 load cases: DLC 1.1/1.3/EOG/ice, loss of torque and e-stop with each stopping system alone, normal stop, parked V_ref at all yaw errors | `results/dlc6/dlc_summary.json`, `ops_loads_6kw_18m.json`, `dlc_raw.json`, `ts_*.npz` |
| `recheck6.py` | reruns the doc 30 blade, hub and tower models with the simulated loads | `results/recheck6.json` |
| `plots6.py` | figures S01–S04 | `results/S0*.png` |

Run `python3 dlc6.py` (~28 min on 4 cores), then `recheck6.py` and `plots6.py`.

## Doc 32: lighter bedplate and brake hold

| Script | What it does | Output |
|---|---|---|
| `bedplate6.py` | plate-by-plate mass and SLM checks of the 12 kW NP1-300 as drawn and the lighter NS6-300; head mass | `results/bedplate6.json`, `results/head6.json` |
| `brake_hold6.py` | parked 50-year storm, yaw lost, 300 s with the brake allowed to slip and K1 closed; brake torque 1.5 kNm and divided by 1.35 / 1.6 | `results/brake_hold6.json` |

Drawings: `cad/turbine_6kw/drawings6.py`. 3D website: `viewer6/`.

## Doc 33: timber blades

| Script | What it does | Output |
|---|---|---|
| `timber6.py` | sizes wood-epoxy blades (moulded veneer shell, carved laminated, carved + carbon strips; Douglas fir and Sitka spruce; three airfoil thicknesses) with the doc 10 section model and the doc 31 loads; aero cost of thicker airfoils; glued-in stud root | `results/timber6.json` |
| `timber6.py 12kw` | same for the 12 kW Ø7.5 m rotor with the doc 08/10 loads | `results/timber12.json` |
| `timber_plots.py` | figures T01–T02 | `results/T0*.png` |

Run after `recheck6.py` (and `analysis/blade/blade.py` for the 12 kW reference), ~10 s each.
