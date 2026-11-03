# Working prototype W1 (printed nacelle and hub with real bought units)

Design document: [docs/17-working-printed-prototype.md](../../docs/17-working-printed-prototype.md).
Builds on the Rev B fit-check model in [../nacelle_fitcheck](../nacelle_fitcheck/) and the
P1 geometry in [../nacelle_p1/geometry.py](../nacelle_p1/geometry.py).

```
pip install cadquery shapely matplotlib
python3 build_w.py      # W1 parts -> out/step, out/stl, NW1-assembly.step, parts-list-w.md, w_check.md, preview-w.png
```

| File | Content |
|---|---|
| `parts_w.py` | Hub NW-500, pitch bearing twins NW-510/511, pitch drive brackets NW-520, blade root stubs NW-530, yaw ring twins NW-430, envelopes of pitch drives, encoders, hub electronics, slip ring |
| `gears.py` | Involute external gears and internal-gear cutters with backlash, for printed functional gears |
| `build_w.py` | Exports, full W1 assembly (Rev B nacelle without the bench dummy hub, plus W1 parts), clash and running-gap check of the new parts |
| `bom_w.csv` | Every bought and swappable unit: W1 choice, later swap, candidate products, frozen interface, automotive verdict |

Same world frame as the fit-check model (X rearward, Y lateral, Z up, origin
on the yaw axis at the bedplate underside): open any files together and they
sit in their assembled positions.
