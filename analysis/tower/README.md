# Tower and foundation models

Used for [docs/09-tower-foundation.md](../../docs/09-tower-foundation.md).

```
pip install numpy scipy matplotlib
python3 frequency.py         # Campbell diagram and energy cost of frequency options (~2 min)
python3 run_tower_loads.py   # 132 aeroelastic runs with the 18 m and 24 m towers (~70 min on 4 cores)
python3 tower.py             # sizing, checks and foundations (~4 min), reads results/ops_loads_*.json
```

- `frequency.py`: 1P/3P bands, the options for placing the tower frequency,
  and the annual energy cost of a minimum speed or a speed exclusion zone.
- `tower.py`: beam finite element model of a tapered tubular tower (top mass
  and rotary inertia, foundation rotational spring, optional guy spring);
  load cases (simulation, parked storm with side wind, storm with ice,
  earthquake response spectrum, tilt-up); checks (yield, section class,
  fatigue, frequency, side-side 1P resonance, second mode, flange bolts);
  spread footings for three soil types and a rock-anchored plinth; guyed
  tower sizing for comparison.
- `run_tower_loads.py`: reruns the doc 08 load cases with the chosen towers,
  the speed exclusion zone and ±0.3° pitch misalignment, adds tower drag and
  hub tilt moment, and writes extreme loads and 20-year rainflow spectra.

Soil properties are generic placeholders until site investigations exist.
The simulator models the tower fore-aft mode only; side-side 1P resonance is
checked analytically in `tower.py`.
