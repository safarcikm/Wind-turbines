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
