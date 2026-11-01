# Nacelle, spindle and bearings: concept loads

Used for [docs/07-nacelle-spindle-bearings.md](../../docs/07-nacelle-spindle-bearings.md).

```
python3 loads.py      # seconds; uses ../rotor/bem.py and the rotor power curve
```

Quasi-static concept loads (steady BEM × dynamic factor, storm, pitch fault,
ice imbalance, gyroscopic), main bearing reactions and life, spindle stress
and stiffness, brake and yaw sizing, spindle bore cooling path. All mass and
position inputs are listed at the top of `loads.py`.
