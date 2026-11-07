# LC8: low-cost 12 kW turbine (doc 38)

Ø8.0 m, 3 blades, **fixed pitch, stall by speed control** (the doc 28/31 S6 method), design TSR 7.5, **178 rpm** =
the Rev C generator's own rated speed, rated 12 kW at 10 m/s. Built on the 6 kW S6 platform (fixed hub, NS6-300
bedplate, Dpw 360 yaw, braking resistor, one caliper).

```
pip install numpy scipy matplotlib
python3 stall12.py 7.0 7.5 8.0 9.0     # doc 28 regulation study at 12 kW (energy, stall torque, stops, parked loads)
cd ../variant_l7 && for t in "7.0 167.0" "7.5 178.0" "8.0 191.0"; do set -- $t; \
  LC_TSR=$1 LC_RPM=$2 LC_OUT=tsr$1 L7_BRAKE=4365 L7_HUB=100 python3 ../low_cost_12kw/blade_e8.py; done; cd -
                                       # doc 10 blade with the 1.10 x 3P frequency rule
python3 concepts.py                    # masses, part costs (doc 27 rates), EUR/MWh: M8 vs LC8
python3 figures_lc8.py                 # F01 TSR sweep, F02 cost breakdown
```

`stall12.py` loads `../turbine_6kw/regulation.py` unchanged with the 12 kW design dictionary.
`blade_e8.py` writes `results/blade_e8_tsr<x>.json` (the TSR 7.0 file was run at 167 rpm).
