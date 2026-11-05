# Interactive 3D turbine viewer

`index.html` is a single self-contained page (three.js r160 from jsDelivr). Open it in any
modern browser; it needs internet access for the three.js and font downloads only.
`turbine-3d.html` is the same page without the document skeleton (the source published as a
claude.ai Artifact). Edit `turbine-3d.html` and regenerate `index.html` by wrapping it.

What it shows (all dimensions in mm, copied from the design sources):

| Model part | Source |
|---|---|
| Spindle, bearings, drum, magnets (200 × N45SH 30×15×12, 5 skewed rows), stator (45-slot lamination outline), coils, carrier, fins, ribs, disc, rear cover, bedplate, rotor tilt 5°, yaw axis 750 mm | `cad/nacelle_p1/geometry.py` (Rev B nacelle, Rev C generator) |
| Welded hub, pitch bearings, cranks, links, yoke, electric cylinder, nose housing, supercap | `cad/hub_c/model.py`, `analysis/hub/collective.py` (the link/yoke kinematics are ported 1:1, so the yoke moves x −143 → −303 over −2° → 92°) |
| Yaw ring z150 m4, gearmotors z14, friction pad units, NY-400 adapter | `cad/yaw/model.py`, `cad/nacelle_fitcheck/parts.py` |
| Blades: chord, twist, t/c, root Ø220, pitch axis 30 % chord | `analysis/blade/blade.py`, `analysis/rotor/bem.py` |
| Tower 18 m, Ø550 → Ø320 | `analysis/tower` |

Indicative only (not designed yet): spinner shape, nacelle shell, brake caliper envelopes.

Wind: set the heading the wind comes from (0° N, 90° E) and its speed (0–40 m/s), optionally with
gusts. With "Turbine follows wind" on, the doc 11 control logic runs: yaw with an 8° deadband,
start at 3 m/s and stop below 2.5, variable speed at TSR 6.5 with the 66–80 rpm tower exclusion
zone, rated 178 rpm with pitch above 10.75 m/s, storm control 25–30 m/s, storm stop above 32 m/s
(feather at 8 °/s). Power is estimated with Cp 0.48 and the cos³ yaw-error loss.

Controls: Run / Stop (feather at the real 30 °/s), rotor speed 0–250 rpm (slow motion ×0.1 by
default), pitch −2…92°, yaw ±180° or "Follow wind", exploded view, section cut through the rotor
axis, camera presets, hover/click any part for its drawing number and key data.
