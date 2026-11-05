# Yaw system 3D model and drawings (doc 25)

| File | What it does |
|---|---|
| `model.py` | CadQuery parts in the nacelle frame (X rearward, Z up, origin on the yaw axis at the bearing top face): tower-top adapter NY-400, friction pad units NY-410, yaw lock NY-430, encoder unit NY-440, cable hanger NY-460. Reuses the slewing ring and gearmotor envelopes, NP1-420 brackets, bedplate and tower stub from `../nacelle_fitcheck/parts.py`. `python3 model.py` prints the part masses |
| `clash.py` | Every pair at yaw 0° (lock engaged), then all nacelle-side parts through 360° in 10° steps against the tower-side parts (lock retracted). Writes `out/clash.json` (clean) |
| `render.py` | Copy of the numpy z-buffer renderer from `../hub_c` |
| `iso_yaw.py` | Isometric views IY01–IY05, `out/iso/*.png` |
| `drawings.py`, `build.py` | A3 drawing set NY-000, NY-400, NY-410, NY-430, NY-440, NY-460 with `../nacelle_p1/draft.py`: `out/NY-drawing-set.pdf`, `out/pdf/`, 1:1 `out/dxf/`, previews `out/png/` with `--png` |

Run `python3 ../../analysis/yaw/yaw.py` first (the drawings read its summary), then
`python3 build.py --png`, `python3 clash.py` (about 10 minutes) and `python3 iso_yaw.py`.
Needs cadquery, ezdxf, numpy, matplotlib.
