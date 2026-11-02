# Nacelle P1 fit-check model: parts list (all 1:1)

43 objects, solid volume 153 L, filament ≈ 58 kg PETG at ~30% solid fraction. Sizes are the part's bounding box, largest first.

| File | Part | Moves | Make/buy | Size mm | Filament kg | Print changes vs steel part |
|---|---|---|---|---|---|---|
| `NP1-100_spindle` | Spindle | stationary | make | 451 x 401 x 400 | 2.74 | M135x2 thread printed as a plain Ø135 seat (use the locknut envelope); tapped holes printed at tap-drill size (M12 Ø10.2, M20 Ø17.5) |
| `NP1-101_front_spacer` | Front spacer / seal counterface | stationary | make | 161 x 160 x 31 | 0.03 | bore +0.2 mm radial (slides on the printed spindle) |
| `NP1-110_cooling_insert` | Spindle cooling insert (finned) | stationary | make | 426 x 126 x 90 | 0.35 | OD -0.2 mm radial (shrink fit in steel, slide fit in print) |
| `KMT27_locknut_envelope` | Precision locknut KMT 27 (envelope) | stationary | buy (envelope) | 176 x 174 x 43 | 0.1 | plain bore, no thread |
| `32028X_front_cone_envelope` | Front bearing cone + rollers (envelope) | stationary | buy (envelope) | 191 x 191 x 61 | 0.2 | bore +0.2 mm radial |
| `32028X_rear_cone_envelope` | Rear bearing cone + rollers (envelope) | stationary | buy (envelope) | 191 x 191 x 61 | 0.2 | bore +0.2 mm radial |
| `32028X_front_cup_envelope` | Front bearing cup (envelope) | rotating | buy (envelope) | 212 x 210 x 52 | 0.09 | OD -0.2 mm radial (P7 press fit in steel) |
| `32028X_rear_cup_envelope` | Rear bearing cup (envelope) | rotating | buy (envelope) | 212 x 210 x 52 | 0.09 | OD -0.2 mm radial (P7 press fit in steel) |
| `NP1-200_stator_carrier` | Stator carrier | stationary | make | 456 x 456 x 135 | 1.93 | M8 clamp-ring holes at tap-drill size Ø6.8 |
| `NP1-201_stator_core` | Stator core (bonded lamination stack, 45 slots) | stationary | make | 602 x 598 x 126 | 2.45 | bore +0.2 mm radial (shrink fit in steel); printed as one solid stack 74 mm |
| `stator_key_090` | Stator key 10x8, 73.5 long (BOM says 90) at 90 deg | stationary | buy (envelope) | 74 x 14 x 10 | 0.0 | 0.1 mm smaller each side; 73.5 mm long to fit the 73.5 mm seat (BOM line 10 says 90) |
| `stator_key_210` | Stator key 10x8, 73.5 long (BOM says 90) at 210 deg | stationary | buy (envelope) | 74 x 19 x 12 | 0.0 | 0.1 mm smaller each side; 73.5 mm long to fit the 73.5 mm seat (BOM line 10 says 90) |
| `stator_key_330` | Stator key 10x8, 73.5 long (BOM says 90) at 330 deg | stationary | buy (envelope) | 74 x 19 x 12 | 0.0 | 0.1 mm smaller each side; 73.5 mm long to fit the 73.5 mm seat (BOM line 10 says 90) |
| `NP1-202_stator_clamp_ring` | Stator front clamp ring | stationary | make | 458 x 457 x 48 | 0.11 | – |
| `stator_end_winding_front_envelope` | End windings, front (envelope) | stationary | make | 584 x 582 x 72 | 0.69 | – |
| `stator_end_winding_rear_envelope` | End windings, rear (envelope) | stationary | make | 584 x 582 x 72 | 0.69 | – |
| `NP1-210_rotor_drum` | Rotor drum weldment | rotating | make | 690 x 689 x 412 | 4.6 | cup seats Ø210 printed at nominal; the cup envelopes are reduced instead; tapped holes at tap-drill size |
| `NP1-211_front_seal_cover` | Front bearing seal cover | rotating | make | 240 x 240 x 31 | 0.09 | – |
| `NP1-211_rear_seal_cover` | Rear bearing seal cover | rotating | make | 240 x 240 x 31 | 0.1 | – |
| `NP1-212_drum_rear_cover` | Drum rear cover with Ø400 seal carrier | rotating | make | 690 x 688 x 76 | 1.02 | – |
| `NP1-220_magnet_ring` | Magnet layer, 40 poles (dummy, no magnets) | rotating | make | 622 x 619 x 128 | 0.35 | one ring instead of 160 segments; pole gaps as grooves; do not put real magnets in a printed drum |
| `NP1-230_brake_disc` | Brake disc Ø800 | rotating | make | 800 x 798 x 86 | 1.05 | – |
| `NP1-320_lock_pin` | Rotor lock pin Ø25 (engaged) | stationary | make | 131 x 37 x 30 | 0.03 | Ø25 nose -0.2 mm radial |
| `NP1-300-1_bedplate_front_plate` | Bedplate front plate 40 (square to spindle) | stationary | make | 738 x 500 x 104 | 5.05 | Ø200 bore +0.2 mm radial |
| `NP1-300-2_bedplate_bottom_plate` | Bedplate bottom plate 40 (yaw flange) | stationary | make | 660 x 520 x 40 | 4.59 | – |
| `NP1-300-3_bedplate_side_plate_left` | Bedplate side plate 20 (left) | stationary | make | 734 x 608 x 20 | 2.3 | – |
| `NP1-300-3_bedplate_side_plate_right` | Bedplate side plate 20 (right) | stationary | make | 734 x 608 x 20 | 2.3 | – |
| `NP1-300-4_bedplate_rear_plate` | Bedplate rear plate 20 | stationary | make | 480 x 290 x 20 | 1.06 | – |
| `yaw_bearing_inner_ring_envelope` | Yaw bearing inner ring (to bedplate) | stationary | buy (envelope) | 350 x 350 x 60 | 1.29 | – |
| `yaw_bearing_outer_gear_ring_envelope` | Yaw bearing outer ring, gear z150 m4 (to tower) | tower | buy (envelope) | 608 x 608 x 60 | 3.93 | – |
| `brake_caliper_left_envelope` | Brake caliper space claim (left) | stationary | buy (envelope) | 192 x 155 x 130 | 1.12 | – |
| `brake_caliper_right_envelope` | Brake caliper space claim (right) | stationary | buy (envelope) | 192 x 155 x 130 | 1.12 | – |
| `NP1-310_rotor_caliper_bracket_left` | Rotor brake caliper bracket (left, placeholder) | stationary | make | 130 x 112 x 70 | 0.39 | – |
| `NP1-310_rotor_caliper_bracket_right` | Rotor brake caliper bracket (right, placeholder) | stationary | make | 130 x 112 x 70 | 0.39 | – |
| `yaw_drive_left_envelope` | Yaw gearmotor 0.18 kW 1:1680 with z14 m4 pinion (left) | stationary | buy (envelope) | 400 x 110 x 110 | 1.08 | – |
| `NP1-420_yaw_drive_bracket_left` | Yaw drive bracket (left) | stationary | make | 180 x 170 x 140 | 0.37 | – |
| `yaw_drive_right_envelope` | Yaw gearmotor 0.18 kW 1:1680 with z14 m4 pinion (right) | stationary | buy (envelope) | 400 x 110 x 110 | 1.08 | – |
| `NP1-420_yaw_drive_bracket_right` | Yaw drive bracket (right) | stationary | make | 180 x 170 x 140 | 0.37 | – |
| `yaw_brake_caliper_left_envelope` | Yaw brake caliper + bracket space claim (left) | stationary | buy (envelope) | 211 x 211 x 150 | 1.08 | – |
| `yaw_brake_caliper_right_envelope` | Yaw brake caliper + bracket space claim (right) | stationary | buy (envelope) | 211 x 211 x 150 | 1.08 | – |
| `NP1-400_tower_top_adapter` | Tower-top adapter with yaw brake track | tower | make | 840 x 840 x 290 | 6.94 | – |
| `tower_top_flange_stub` | Tower top flange + 300 mm of the Ø320 x 8 tube (mounting point) | tower | make | 420 x 420 x 330 | 1.89 | – |
| `NP1-600_dummy_hub` | Bench dummy hub with Ø100 shaft | bench | make | 742 x 470 x 470 | 3.94 | Ø361 recess moved to the hub face (drawing has the step reversed, see assembly check) |
