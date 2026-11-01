# Blade structural model

Used for [docs/10-blade-structure.md](../../docs/10-blade-structure.md).

```
pip install numpy scipy matplotlib
python3 blade.py      # about a minute; writes results/blade_summary.json and plots
```

- Thin-walled section model on a NACA 4-digit thickness outline blended to
  the root cylinder: spar caps between two shear webs (15 % and 45 % chord),
  sandwich shell panels, trailing edge strip. Gives EA, flap and edge
  stiffness, mass and strains around the perimeter.
- Sizes the spar caps, webs and root wall station by station against the
  SLM and aeroelastic ultimate loads, fatigue, spar cap and panel buckling,
  and web shear. Then checks tip deflection against tower clearance and the
  flap and edge frequencies (beam model with centrifugal stiffening).
- Four material options: glass or carbon spar caps, solid or foam-backed.
- Root joint: number and size of bonded steel inserts.

Material properties are typical characteristic values. Replace them with
coupon test data from our own laminates before detailed design.
