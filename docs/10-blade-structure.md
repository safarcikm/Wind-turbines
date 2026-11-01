# 12 kW Wind Turbine for Iceland: Blade Materials and Structure

Status: **Draft, revision 1** · 2026-11-01
Owner: Category 2 (Rotor and blades)
Builds on: [03 – Rotor](03-rotor-concept.md), [08 – Load verification](08-load-verification.md), [09 – Tower](09-tower-foundation.md)
Model: [`analysis/blade/blade.py`](../analysis/blade/blade.py)

## Summary

| Item | Recommendation |
|---|---|
| Spar caps | **Carbon fibre UD / epoxy** (standard modulus, pultruded planks or infused) |
| Shell, webs, root | Glass fibre / epoxy (triax shell, biax webs), PET foam core, vacuum infused in heated moulds |
| Blade mass | **≈ 20.5 kg** (glass caps 21.6 kg; doc 07 assumed 20 kg) |
| Flap frequency | **13.2 Hz** at standstill, 13.9 Hz at rated speed: well clear of 3P (8.9 Hz at 178 rpm). Glass caps give 10.2 Hz rotating, only 4 % above the 9.8 Hz target |
| Tip deflection | 0.11 m against 0.89 m tower clearance (glass: 0.22 m) |
| Utilisation | Ultimate 0.47 (SLM), fatigue 0.20, cap buckling 0.99 (this sizes the caps), web shear 0.78 |
| Root | Root Ø 0.22 m (up from 0.19 m), **10 bonded steel inserts M16 10.9** on Ø 190 mm, 61 kN per bolt against 113 kN |
| Erosion and ice | PU leading-edge coating plus a metal erosion shield on the outer third; carbon-fibre or wire heating mats under the surface (R2.8) |
| Lightning | Tip receptor and down conductor; carbon caps bonded to it at several points (LPL I) |

Why carbon although it saves only 1 kg: on a blade this small, most of the
mass is the root and the minimum shell. The thin caps are sized by buckling,
not strength, so carbon cannot be made much thinner than glass. What carbon
buys is **stiffness**: the flap frequency moves from just above 3P to 40 %
above it, and tip deflection halves. That is the quality margin the brief
asks for. Glass caps remain a valid fallback that passes every check.

---

## 1. Material options

| Option | Verdict | Reason |
|---|---|---|
| Glass fibre / epoxy | Valid baseline | Industry standard, tough at −40 °C, well documented fatigue, simple in-house infusion |
| **Glass shell + carbon spar caps** | **Recommended** | Stiffer and slightly lighter; needs lightning bonding of the caps |
| Glass with a recyclable thermoplastic resin | Watch | Tougher and recyclable, but fatigue data is thin; revisit for a later version |
| Wood-epoxy laminate | Rejected | Moisture uptake and freeze–thaw in Icelandic conditions; quality scatter |
| Flax fibre composite | Rejected | Low stiffness, absorbs moisture |
| Aluminium | Rejected | No fatigue limit; cannot survive ~2 × 10⁹ cycles |
| Core: PET foam | Recommended | Does not absorb water, recyclable; balsa rejected (water uptake) |

## 2. Structural concept

- Two shear webs at 15 % and 45 % chord form a box spar; the spar caps sit
  on the shell between them ([sections](../analysis/blade/results/blade_sections.png)).
- Shell: 1 mm glass triax faces on 6 mm PET foam; trailing edge 2 mm glass
  UD strip; webs glass biax on 8 mm foam.
- Thickness: root cylinder at the pitch bearing (r = 0.4 m), 30 % at the
  maximum chord (0.78 m), 25 % at 1.5 m (DU 91-W2-250 class), 21 % at 2.25 m,
  18 % outboard (DU 96-W-180 class).
- Root cylinder wall: 12 mm triax build-up tapering out by r = 0.95 m,
  thickened locally to about 35 mm over the first 150 mm for the inserts.
- 10 % mass allowance for adhesive, paint, leading-edge protection and
  heating, plus 1.5 kg for inserts and fittings.

## 3. Loads and factors

| Load | Value (design, at the root) | Source |
|---|---|---|
| Parked, wind on the blade's flat side (SLM H) | 26.0 kNm | doc 08, γ_f = 3.0 |
| Shutdown, edgewise (SLM G) | 10.4 kNm | doc 08, γ_f = 3.0 |
| Centrifugal at 250 rpm (SLM E) | ≈ 64 kN | γ_f = 3.0 |
| Aeroelastic ultimate (resultant) | 8.5 kNm | doc 08, γ_f = 1.35 |
| Fatigue, damage-equivalent at 10⁷ cycles | flap 3.2 kNm, edge 1.2 kNm | doc 08 |

Material factors are assumptions until the purchased IEC 61400-2:2013 is
checked: 2.2 on the aeroelastic loads (DNV-ST-0376-style product of
factors), 1.35 on the SLM loads (whose γ_f of 3.0 already covers model
uncertainty), 1.96 in fatigue, 1.1 on stiffness, 1.5 on buckling.

## 4. Results

| | Glass caps | Glass, foam-backed caps | **Carbon caps** | Carbon, foam-backed caps |
|---|---|---|---|---|
| Spar cap UD at root | 5.25 mm | 2.25 mm | **4.75 mm** | 1.75 mm |
| Blade mass | 21.6 kg | 20.7 kg | **20.5 kg** | 20.3 kg |
| Static moment about the rotor axis | 29.6 kg·m | 29.1 kg·m | **28.0 kg·m** | 28.4 kg·m |
| Flap frequency, standstill / 178 rpm | 9.3 / 10.2 Hz | 7.5 / 8.6 Hz | **13.2 / 13.9 Hz** | 9.3 / 10.2 Hz |
| Edge frequency | 22.0 Hz | 20.4 Hz | **23.9 Hz** | 21.5 Hz |
| Tip deflection (operating extreme × 1.35, stiffness × 1/1.1) | 0.22 m | 0.31 m | **0.11 m** | 0.20 m |
| Ultimate utilisation (worst) | 0.65 | 1.00 | **0.47** | 0.99 |
| Fatigue utilisation | 0.39 | 0.60 | **0.20** | 0.40 |
| Cap buckling utilisation | 1.00 | 0.37 | **0.99** | 0.41 |
| 3P margin (rotating flap vs 8.9 Hz) | +15 % | **−4 % (fails)** | **+56 %** | +15 % |

Plots: [layup, mass and stiffness](../analysis/blade/results/blade_layup.png).

Foam-backed caps solve buckling and save a little mass, but they make the
blade softer, which removes the frequency margin. Solid carbon caps give the
best stiffness and the lowest strain levels.

**Load feedback:** doc 08 assumed a 6 Hz, 20 kg blade. Rerunning normal
turbulence at 8, 14 and 20 m/s with the carbon blade (13.2 Hz, 20.5 kg)
changed the flap damage-equivalent load by at most 4 % and the peaks by at
most ±8 %. The fatigue margin (utilisation 0.20) covers this.

## 5. Root joint

| Root Ø | Inserts | Bolt load (design) | Bolt capacity |
|---|---|---|---|
| 0.19 m (aerodynamic design) | 10 × M16 on Ø 160 mm, pitch 50 mm | 71 kN | 113 kN |
| **0.22 m (recommended)** | **10 × M16 on Ø 190 mm, pitch 60 mm** | **61 kN** | **113 kN** |

The slightly larger root gives more room between inserts and a stiffer pitch
bearing interface. Its aerodynamic effect is negligible. Insert pull-out
must be confirmed by tests on our own root laminate.

## 6. Manufacturing (in-house)

- Two shell halves vacuum infused in heated composite moulds, webs infused
  separately, bonded with a toughened epoxy adhesive; post-cure.
- Carbon caps as pultruded planks laid into the shell mould (consistent
  fibre straightness and quality), or infused carbon UD.
- Root inserts bonded into the root laminate in a jig to hold bolt-circle
  tolerance.
- Every blade weighed and its static moment measured; blades matched in sets
  of three within 0.5 % (R2.6 and R6.6).
- Quality: ultrasonic inspection of cap and bond lines, coupon tests from
  every batch, full-scale static and fatigue tests (IEC 61400-23) on the
  prototype blades (R2.4).

## 7. Limitations

- Typical material properties from the literature; our own coupon tests
  are needed.
- Simple plate buckling (k = 4 with a 0.8 knock-down); detailed blade FEA
  with buckling eigenvalue analysis comes later.
- The section model ignores camber, twist coupling and shear deformation.
- Aerofoil choice is not frozen (doc 03); the thickness distribution follows
  the shortlist.

## 8. Next steps

1. Coupon tests on the chosen glass, carbon, PET core and adhesive at
   −40 °C and room temperature.
2. Blade FEA (shell model) with buckling, bond-line and root insert checks.
3. Controller design: exclusion zone, constant power above rated, vibration
   trip (doc 09).
4. Moulds and a first prototype blade for static testing.
