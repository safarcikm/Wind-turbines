# Hub, pitch and yaw models (doc 13)

| File | What it does |
|---|---|
| `run_pitch_duty.py` | Runs 28 normal-turbulence cases (4–30 m/s, 2 seeds, 600 s) with the final turbine (doc 11 controller, doc 09 18 m tower, doc 10 blade) in `analysis/loads/sim.py`. Records pitch travel, reversals, time at fine pitch, motion-weighted root moment and centrifugal force, root moment DELs (m = 3, 5) and hub yaw moment percentiles, weighted to 20 years at V_ave 10 m/s. Writes `results/pitch_duty.json` (about 15 minutes on 4 cores) |
| `hub.py` | Sizing: pitch moments (BEM + 360° flat-plate centre of pressure, centrifugal twisting moment), pitch bearing (Hertz static check, ISO 281-style life, friction), pitch drive (torque cases, gear, motor, tooth bending, supercap), hub casting (wall, mass, hub-to-drum bolts), yaw (loads, slewing ring, drives, brake, backup battery), mass and tower frequency effect. Writes `results/hub_summary.json` |

| `collective.py` | Doc 24: collective pitch (crank, link, yoke kinematics), trip and normal forces, electric cylinder, supercap strokes, rejected gas-spring variant, welded hub checks and mass. Writes `results/collective_summary.json` |
| `collective_fig.py` | Doc 24 layout figure, `results/collective_layout.png` |

Run `python3 run_pitch_duty.py` first, then `python3 hub.py`, then `python3 collective.py` and `python3 collective_fig.py`.

Key assumptions (to confirm with suppliers and the purchased IEC 61400-2):
allowable Hertz stress 4,000 MPa, raceway osculation 0.535, ISO 281 rating
× 0.6 for slewing rings, equivalent axial load F + 2.5 M / D_pw, friction
μ 0.006 warm / 0.012 at −30 °C, C_m0 = −0.08, ductile iron fatigue range
55 MPa at 10⁷ cycles (m = 5), 10 mm minimum cast wall.

The tower frequency figures in doc 13, section 8, come from
`analysis/tower/tower.py` (`fe_modes`, `tilt_up_ginpole`) with a 599 kg
tower top and 367 kg m² rocking inertia.
