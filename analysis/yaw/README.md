# Yaw system sizing (doc 25)

`yaw.py`: tower-top mass and centre of gravity, loads at the yaw bearing and its
three bolted joints, slewing ring static check and friction (models from
`analysis/hub/hub.py`), why controlled slip does not protect anything (reflected
motor inertia, tower torsion), friction pad units (torque band, clamp, DIN 2093
disc spring stack by Almen-László, pad pressure, wear), drives and holding on one
pinion, gear check (ISO 6336 simplified), yaw power and backup battery, cable
twist length. Writes `results/yaw_summary.json`.

Run: `python3 yaw.py` (needs `analysis/hub/results/pitch_duty.json` and the load results).

Assumptions to confirm: pad μ 0.40 ± 20 % with +15 % cold and +15 % breakaway,
wear 0.25 cm³/MJ, 1,500° of yaw travel a day, gearbox back-driving efficiency
0.65, motor inertia 5 × 10⁻⁴ kg m², torsion-rated cables 150 °/m.
