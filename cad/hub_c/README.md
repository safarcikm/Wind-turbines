# Hub and collective pitch 3D model (doc 24)

| File | What it does |
|---|---|
| `model.py` | CadQuery parts in the spindle frame: welded hub NH-500W, ungeared pitch bearings, blade root stubs, cranks, links, yoke, guide rods, electric cylinder, motor, supercap and drive envelopes, nose housing, Rev C drum front and slip ring (context). Linkage geometry is imported from `analysis/hub/collective.py` |
| `clash.py` | Pairwise intersection check at 7 pitch angles from −2° to 92°, `out/clash.json` (clean) |
| `render.py` | Small numpy z-buffer renderer (flat shading + outlines) |
| `iso_hub.py` | Isometric views IH01–IH05, `out/iso/*.png` |

Run `python3 clash.py` and `python3 iso_hub.py` (needs cadquery, numpy, matplotlib).
