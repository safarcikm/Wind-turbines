# Slow-running variant V5 (doc 26)

Ø8.3 m, 3 blades, design TSR 5, rated 110 rpm, same 13.6 kW shaft / 12 kW electric rating.
Every script reuses the existing project models unchanged and only replaces their inputs.

```
pip install numpy scipy matplotlib
python3 rotor_tsr5.py      # BEM power curves, energy vs current rotor        (~2 min)
python3 structure_v5.py    # SLM loads + blade layup, first pass               (~2 min)
python3 generator_v5.py    # Rev C lengthened to 120 mm stack, losses, cooling
python3 power_v5.py        # converter envelope, net energy with loss chain
python3 dlc_v5.py          # 103 aeroelastic load cases + tower loads          (~30 min on 4 cores)
python3 structure_v5.py dlc   # blade final pass with simulated loads
python3 hub_yaw_v5.py      # pitch bearing, collective, hub, brake, yaw
python3 tower_v5.py        # tower + footings (V5, and current with its real 1,103 kg head)
python3 figures_v5.py      # F01-F04
```

- `common.py`: V5 constants (radius, speeds, overhang) and the TSR 5 blade.
- Results in `results/` (JSON + figures). Time series are not kept.
- The tower frequency used in `dlc_v5.py` (0.97 Hz) is the `tower_v5.py` result
  from the first pass; the loop was run twice.
