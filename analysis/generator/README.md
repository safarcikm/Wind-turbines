# Generator models

Used for [docs/04](../../docs/04-generator-concept.md) and
[docs/05](../../docs/05-generator-fea-thermal.md).

```
pip install numpy scipy matplotlib
python3 sizing.py     # analytical sizing and topology comparison (seconds)
python3 run_fea.py    # 2D nonlinear FEA: no-load, cogging, load, demag (~12 min)
python3 thermal.py    # thermal network, reads results/fea_summary.json
```

- `fem.py`: self-contained 2D magnetostatic FEM (structured polar mesh of one
  periodic section, Newton-Raphson for iron saturation, magnet pattern moved
  on a fixed mesh, Arkkio torque).
- Results land in `results/` (JSON summaries and plots).

## Manufacturing numbers (doc 18)

```
python3 manufacturing.py   # slot fill, coil/phase resistance, coil connection plan,
                           # magnet data, expected EMF, test voltages, balance limits
```

Reads the P1 geometry from `cad/nacelle_p1/geometry.py`; writes
`results/manufacturing_summary.json` and `results/coil_connection.csv`.
No numpy needed.
