# CNC foam-core blade for M8 (doc 41)

```
pip install numpy scipy matplotlib
python3 foam_m8.py         # 12 foam-core builds vs the doc 35 mould blade, same loads (~5 s) -> results/foam_m8.json, F01
python3 cost_foam.py       # cost and hours of both routes on the doc 39 rates -> results/cost_foam.json, F02
python3 section_sketch.py  # F03 section drawing
```

`foam_m8.py` reuses `analysis/blade/blade.py` as patched for M8 by `analysis/variant_m8/structure_m8.py` and replaces
only the section (solid machined core, biax-wrapped spar block, caps in pockets, outer skin) and the stability check
(face wrinkling on the foam instead of plate buckling between webs). Loads come from
`variant_m8/results/blade_m8_8m.json`. `cost_foam.py` reads the rates from `analysis/cost_m8/cost_m8.py`.
