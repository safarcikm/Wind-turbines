# Nacelle P1 fit-check model (1:1 printable parts)

Design document: [docs/16-nacelle-fit-check-model.md](../../docs/16-nacelle-fit-check-model.md); geometry Rev B and the working prototype: [docs/17](../../docs/17-working-printed-prototype.md).
Source geometry: [../nacelle_p1/geometry.py](../nacelle_p1/geometry.py) (P1 single source of truth).

```
pip install cadquery shapely matplotlib
python3 build.py            # every part -> out/step, out/stl, assembly STEP, parts list, preview
python3 assembly_check.py   # digital fit check -> out/assembly_check.md / .json (~5 min)
```

| File | Content |
|---|---|
| `parts.py` | Builds each part as a 1:1 CadQuery solid in its assembled position, with bolt holes, keys, cable holes, lock holes |
| `assembly_check.py` | Static interference, rotating-to-stationary running gaps and assembly paths in the doc 14 §7.2 order |
| `build.py` | Exports one STEP and one STL per part, the coloured assembly STEP, `parts-list.md/.csv` and `preview.png` |

Every part is its own object and its own file, at full size, not split.
All files share one frame (X rearward, Y lateral, Z up, origin on the yaw
axis at the bedplate underside), so opening any set of them together shows
them assembled. Rotate each part to its best print orientation in the slicer.

Change a dimension in `../nacelle_p1/geometry.py`, rerun both scripts, and
the printed parts, drawings and checks stay consistent.
