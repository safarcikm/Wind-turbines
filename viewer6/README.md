# 6 kW turbine S6: interactive 3D model and drawing set

Published as a claude.ai Artifact: https://claude.ai/artifact/WBfQKfcMw89RepndbRGqxF
(sister page of the 12 kW viewer in `viewer/`).

`turbine-3d.html` is the page source without the document skeleton (what is published).
`index.html` is the same page wrapped as a stand-alone file. `drawings` is a link to
`cad/turbine_6kw/out`, so opening `index.html` from a local web server
(`python3 -m http.server` in this folder) also shows the drawing set. The page needs internet
access for three.js (jsDelivr) and the fonts only.

Regenerate the drawings with `python3 cad/turbine_6kw/drawings6.py`, then publish the page with
the 10 PNG sheets (thumbnails), 10 SVG sheets (full view) and the PDF set as supporting files
under `drawings/png/`, `drawings/svg/` and `drawings/NS6-drawing-set.pdf`.

| Model part | Source |
|---|---|
| Spindle, bearings, drum (no ribs or fins), magnets, stator, coils, carrier, disc, plain rear cover, tilt 5°, yaw axis 750 mm | `cad/nacelle_p1/geometry.py` (Rev C generator reused as G6) |
| Fixed hub NS6-200: Ø380 × 12 shell, three Ø220 × 8 arms, Ø280 × 25 root flanges | `cad/turbine_6kw/drawings6.py` |
| Bedplate NS6-300 (127 kg): plates 20 / 25 / 10, side profile, lightening holes, window | `analysis/turbine_6kw/bedplate6.py` → `results/bedplate6.json` |
| Blades R 3.0 m: chord, twist, t/c, root Ø220, set at −2° | `analysis/turbine_6kw/results/design6.json`, `design6.blade_shape()` |
| Yaw ring, gearmotors, pad units, adapter (reused) | `cad/yaw/model.py`, `cad/nacelle_fitcheck/parts.py` |
| Tower 18 m Ø500 → Ø320, f1 0.87 Hz | `results/design6.json` (doc 30) |
| Stall schedule: rpm and shaft power vs wind | `results/regulation.json` `stall_curve` (doc 28, confirmed in doc 31) |

Indicative only: spinner shape, nacelle shell, tower-base cabinet and resistor box envelopes.

Controller in the page: TSR 5.9 up to 163.6 rpm, stall control at 6.8 kW shaft (6.0 kW
electric), storm ramp 25–30 m/s, storm park above 30 m/s (resistor + spring brake, yaw 90° out),
restart below 22 m/s, start at 3 m/s, stop below 2.5 m/s, 47.5–57.4 rpm skipped (tower 1P).
