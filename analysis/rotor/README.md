# Rotor concept study model

Steady blade element momentum (BEM) model used for
[docs/03-rotor-concept.md](../../docs/03-rotor-concept.md).

```
pip install numpy matplotlib
python3 study.py      # ~4–5 minutes; writes results/
```

- `bem.py`: aerofoil polar model, blade geometry (Schmitz optimum with a
  linear taper), BEM solver.
- `study.py`: tip speed ratio sweep, power curves for 7.0/7.5/8.0 m rotors,
  annual energy, steady loads, parked broadside estimate.
- `results/`: CSV power curves, blade geometry, plots, `summary.json`.

The polars are generic placeholders. Replace `CLEAN`/`ROUGH` in `bem.py` with
measured or XFOIL polars once the aerofoil is chosen.
