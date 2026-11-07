# M8 generator: other magnet blocks (doc 36)

Alternative magnet blocks for the 12 kW M8 generator (doc 35 §4: Ø646 drum, 104 mm stack, 131 rpm, 991 Nm).
Uses the unchanged FEA of `../generator/` (fem.py, magnets.py) and the M8 cooling model of `../variant_m8/`.
Nothing in `../variant_m8/` is changed or overwritten.

```
pip install numpy scipy matplotlib
python3 blocks_m8.py all          # 17 FEA cases (~9 min each, 4 in parallel)
python3 blocks_m8.py table        # results/blocks_summary.json
python3 compare_m8.py A40 W31_12 W33_11 D17_10 D20_10   # results/compare_m8.json
python3 figures_m8mag.py          # results/B01-blocks.png
```

Case keys: REF = M8 baseline N45SH 30x15x12; A40 = N42SH 40x20x7.5 (2 across x 3 along);
G30 = baseline block in N42SH; Wxx_t = one N42SH block xx wide, t thick; Dxx_t = two blocks xx wide across.
