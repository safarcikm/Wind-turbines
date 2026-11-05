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

## Magnet geometry study (doc 19)

```
python3 magnets.py              # 11 magnet shapes (arc vs flat blocks): EMF, cogging, ripple,
                                # demag, net force per pole, magnet eddy loss vs segmentation (~40 min)
python3 magnets.py A F2t        # only some shapes (results are merged into the summary)
python3 magnets.py tol F2t      # cogging sensitivity to pole remanence/position scatter
python3 magnets.py C2t          # doc 19 Rev B: 40 x 20 x 7.5 catalogue blocks; also reports the 2-row step skew
python3 grades.py [C2t]         # magnet grade assessment on F2t (default) or another shape
python3 magnets.py quick ...    # coarse mesh for checks
```

Extends `fem.py` (fixed mesh, any magnet shape sampled per element, bond-line
ring, Maxwell-stress force on one pole, rotor-frame eddy-current loss with
zero net current per piece and the rectangle 3D factor). Writes
`results/magnets_summary.json`, `magnets_raw.json`, `magnets_compare.png`,
`magnets_tolerance_<key>.json`.
