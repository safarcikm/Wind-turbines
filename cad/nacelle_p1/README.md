# Nacelle prototype P1: parametric geometry and drawings

Design document: [docs/14-nacelle-prototype-p1.md](../../docs/14-nacelle-prototype-p1.md).
Bench test plan: [docs/15-nacelle-bench-test-plan.md](../../docs/15-nacelle-bench-test-plan.md).

```
pip install ezdxf matplotlib numpy
python3 geometry.py        # mass table
python3 build.py           # drawings -> out/   (add --png for previews)
python3 ../../analysis/nacelle/detail.py   # detail checks -> analysis/nacelle/results/
```

| File | Content |
|---|---|
| `geometry.py` | Single source of truth: every dimension, section polygon, lamination contour and mass |
| `draft.py` | Small drafting library: one geometry, rendered to A3 PDF and to true-size DXF |
| `drawings.py` | One function per drawing sheet |
| `build.py` | Writes `out/NP1-drawing-set.pdf`, `out/pdf/*.pdf`, `out/dxf/*.dxf`, `out/masses.json`, `out/drawing-index.md` |
| `bom.csv` | Bill of materials (make/buy, source, mass, lead time) |

Change a dimension in `geometry.py`, rerun `build.py` and `detail.py`, and
the drawings, masses and checks stay consistent. DXF files are in model
space at 1:1 (mm) with layers OUTLINE, HIDDEN, CENTER, HATCH, DIM, TEXT;
the OUTLINE layer is the cutting or turning contour.

All sheets are marked "not checked": an independent drawing check is
required before release to manufacture.
