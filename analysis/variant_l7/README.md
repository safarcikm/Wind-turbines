# L7: lightened M8 with TSR 7 (doc 38, stopped) and the TSR sweep

Martin, 2026-11-07, first asked for "a lightweight version of [M8] with much higher TSR", then clarified that he
wants a completely different design focused on low production cost. That design is **LC8** in
[`../low_cost_12kw/`](../low_cost_12kw/) and [doc 38](../../docs/38-low-cost-12kw-lc8.md). This folder keeps the
parts of the lightened-M8 work that doc 38 uses.

```
python3 cp_tables_l7.py   # doc 27 rotor tables extended to design TSR 10 -> results/rotor_tables_ext.json
python3 sweep_l7.py       # TSR 5.5-10 at Ø8.0 m with the doc 27 model -> results/sweep_l7.json/.csv
python3 quiet_l7.py       # rpm-capped "quiet mode" for high-TSR blades -> results/quiet_l7.json
```

L7 itself (Ø8.0 m, TSR 7, 167 rpm, pitch kept) was copied from `../variant_m8/` and run through the rotor, first-pass
blade, generator, power and bedplate scripts before it was stopped (results in `results/`; no aeroelastic run):
blade 21.4 kg, Rev C generator unchanged (hot spot 114 °C at 110 % load), NS6-300 bedplate fits (0.57),
the 8 m tower must get stiffer (724 kg, f1 3.49 Hz) because 1P at 167 rpm is 2.78 Hz.

`common.py` takes `LC_TSR`, `LC_RPM` and `LC_OUT` from the environment so `structure_l7.py` can size blades for other
TSRs (used by `../low_cost_12kw/blade_e8.py`, results in `results/tsr*/`).
