# 12 kW baseline M8 (doc 35)

Ø8.0 m, 3 blades, design TSR 5.5, rated 131 rpm at 10.0 m/s, same 13.6 kW shaft / 12 kW electric rating.
Martin's decision of 2026-11-06 (doc 27 recommendation). Built from the doc 26 scripts in
`../variant_tsr5/`: every script reuses the existing project models unchanged and only replaces their inputs.
Shared constants are in `common.py`.

```
pip install numpy scipy matplotlib
python3 rotor_m8.py        # BEM power curves, energy vs current rotor        (~1.5 min)
python3 generator_m8.py    # Rev C with 7 magnet rows (stack 104 mm), losses, passive cooling
python3 power_m8.py        # converter envelope, net energy with loss chain
python3 structure_m8.py    # SLM loads + blade layup, first pass
python3 dlc_m8.py          # 103 aeroelastic load cases + tower loads          (~40 min on 4 cores)
python3 structure_m8.py dlc   # blade final pass with simulated loads
python3 bedplate_m8.py     # NP1-300 as drawn vs lighter NP8-300 (doc 32 model)
python3 hub_yaw_m8.py      # pitch bearing, collective, hub, brake, yaw
python3 tower_m8.py        # tower + footings (M8, and current with its real 1,286 kg head)
python3 figures_m8.py      # F01-F04
python3 tower8_m8.py       # option: 8 m hub-height tower and energy at 8 m (doc 35 §12), F05
```

Results in `results/` (JSON + figures). Time series are not kept. The tower frequency and head mass
used in `dlc_m8.py` are the `tower_m8.py` / `hub_yaw_m8.py` results of the previous pass.

## 8 m tower build (doc 37)

```
python3 dlc8_m8.py           # 103 cases at 8 m hub height with the 8 m controller   (~40 min)
                             #   --ctrl18 runs the 18 m controller (kept as dlc_summary_ctrl18.json)
python3 ctrl8_m8.py          # controller variants on the 8 worst cases -> results/ctrl8_m8.json
python3 structure_m8.py dlc8 # blade with the larger of the 18 m and 8 m envelopes -> blade_m8_8m.json
python3 spindle_m8.py        # spindle, bearings, bolted joints, brake (doc 14 detail model)
python3 tower8_m8.py         # final 8 m tower with the CAD head mass (run after model8.py)
cd ../../cad/turbine_m8
python3 model8.py && python3 bom8.py && python3 iso8.py all && python3 clash8.py \
  && python3 drawings8.py && python3 buildbook8.py
```
