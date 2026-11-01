# Generator concept sizing

Analytical sizing used for [docs/04-generator-concept.md](../../docs/04-generator-concept.md).

```
python3 sizing.py     # writes results/summary.json and results/radial_sweep.csv
```

Compares an outer-rotor radial flux machine (diameter sweep) with a coreless
double-rotor axial flux machine at the same torque. Concept level only; the
detailed design needs 2D FEA, a thermal model and structural checks.
