"""Manufacturing numbers for the P1 generator (doc 18).

Run:  python3 manufacturing.py   (writes results/manufacturing_summary.json
                                   and results/coil_connection.csv)

Everything here derives from the frozen design (doc 06) and the P1 geometry
(cad/nacelle_p1/geometry.py, doc 14, Rev B in doc 17). It gives the shop the
target values used in doc 18: winding fill check, coil and phase resistance,
copper and wire quantities, coil connection plan, magnet data and handling
forces, expected EMF and test voltages, balance limits.
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent.parent / "cad" / "nacelle_p1"))
from geometry import GEN, MAGNET, RHO  # noqa: E402

OUT = HERE / "results"
OUT.mkdir(exist_ok=True)
MU0 = 4e-7 * math.pi
R = {}

# ------------------------------------------------------------ slot geometry
Q, P2 = GEN["slots"], GEN["poles"]
p = P2 // 2
w_t = GEN["w_t"]
r_top, r_bot = GEN["r_slot_top"], GEN["r_slot_bot"]


def slot_width(r: float) -> float:
    return 2 * math.pi * r / Q - w_t


R["slot"] = dict(width_top_mm=round(slot_width(r_top), 2),
                 width_bottom_mm=round(slot_width(r_bot), 2),
                 depth_mm=GEN["d_slot"], opening_b0_mm=GEN["b0"],
                 tooth_tip_width_mm=round(2 * math.pi * GEN["r_s"] / Q - GEN["b0"], 1),
                 area_mm2=round((slot_width(r_top) + slot_width(r_bot)) / 2 * GEN["d_slot"]))

# ------------------------------------------------------------ winding data
TURNS = GEN["turns_per_coil"]          # 28 (doc 14)
STRANDS, D_BARE = 4, 1.55              # 4 in hand, Ø1.55 mm (doc 14)
D_OVER = 1.66                          # grade 2 max overall diameter (IEC 60317-0-1, ≈1.6 nominal)
PITCH = 1.70                           # practical layer pitch
LINER, SEP = 0.30, 0.25                # slot liner each side; half of a 0.5 mm phase separator
CLEAR_WEDGE = 0.5
A_STRAND = math.pi / 4 * D_BARE ** 2
A_TURN = STRANDS * A_STRAND
I_RATED = 23.2

# Available coil-side region: between tooth flank (+liner) and slot centreline (-separator),
# from slot bottom (+liner) to under the wedge.
r0, r1 = r_bot + LINER, r_top - CLEAR_WEDGE


def half_free(r: float) -> float:
    return slot_width(r) / 2 - LINER - SEP


area_side = sum(half_free(r0 + (i + 0.5) * (r1 - r0) / 400) for i in range(400)) * (r1 - r0) / 400
# Precision layer winding: layers parallel to the tooth flank at PITCH spacing;
# layer j exists where the free half-width >= (j + 1) * PITCH.
positions = 0
layers = []
for j in range(20):
    need = (j + 1) * PITCH
    if half_free(r1) < need:
        break
    # lowest radius where layer fits (half_free increases with r)
    lo, hi = r0, r1
    if half_free(r0) >= need:
        r_start = r0
    else:
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if half_free(mid) < need else (lo, mid)
        r_start = hi
    n = int((r1 - r_start) // PITCH)
    layers.append(n)
    positions += n
need_pos = TURNS * STRANDS
R["fill"] = dict(
    copper_per_coil_side_mm2=round(TURNS * A_TURN, 1),
    free_area_per_coil_side_mm2=round(area_side, 1),
    net_copper_fill_of_slot=round(2 * TURNS * A_TURN / R["slot"]["area_mm2"], 3),
    copper_fill_of_free_area=round(TURNS * A_TURN / area_side, 3),
    layered_positions_available=positions, layered_positions_needed=need_pos,
    layer_turns=layers,
    layered_utilisation=round(need_pos / positions, 3),
    current_density_A_mm2=round(I_RATED / A_TURN, 2),
)
# Random (drop-in) winding: typically ≤ 0.40 copper fill of the free area through a
# narrow opening; the design needs the value above.
R["fill"]["random_dropin_max_copper_fill_typical"] = 0.40

# Mean turn length of a tooth coil: around tooth (+liner) and end caps, plus coil build
END_CAP = 3.0                          # end-cap thickness each end
t_coil = area_side / (r1 - r0)         # mean coil side thickness
inner = 2 * (GEN["stack"] + 2 * END_CAP) + 2 * (w_t + 2 * LINER)
MLT = inner + math.pi * t_coil         # mm
LEAD = 2 * 150.0                       # mm of lead per coil (start + finish)
coil_len_m = (TURNS * MLT + LEAD) / 1000
turns_phase = 15 * TURNS
RHO20 = 0.017241                       # ohm mm2/m
R20_coil = RHO20 * TURNS * MLT / 1000 / A_TURN
R20_phase = RHO20 * turns_phase * MLT / 1000 / A_TURN
alpha = 0.00393
cu_mass = 3 * 15 * coil_len_m * A_TURN * 1e-6 * 8900
R["winding"] = dict(
    turns_per_coil=TURNS, strands_in_hand=STRANDS, strand_bare_mm=D_BARE,
    turn_area_mm2=round(A_TURN, 2), mean_turn_mm=round(MLT, 1),
    wire_per_coil_m_per_strand=round(coil_len_m, 2),
    wire_total_m_per_strand_size=round(45 * coil_len_m * STRANDS),
    copper_kg=round(cu_mass, 1), copper_to_order_kg=round(cu_mass * 1.25, 0),
    R20_coil_mohm=round(R20_coil * 1000, 2),
    R20_phase_ohm=round(R20_phase, 4),
    R20_line_line_ohm=round(2 * R20_phase, 4),
    R75_phase_ohm=round(R20_phase * (1 + alpha * 55), 4),
    copper_loss_75C_W=round(3 * I_RATED ** 2 * R20_phase * (1 + alpha * 55)),
)

# ------------------------------------------------------- coil connection plan
rows = []
for k in range(Q):
    th = (k * p * 360 / Q) % 360
    for name, ax in (("A", 0), ("B", 240), ("C", 120)):
        d = (th - ax + 180) % 360 - 180
        if abs(d) <= 30.01:
            sign = "+"
        elif abs(d) >= 149.99:
            sign = "-"
        else:
            continue
        rows.append(dict(tooth=k + 1, emf_angle_deg=round(th, 1), phase=name, sense=sign))
# Renumber so tooth 1 is the first coil of an A group (+A -A +A pattern, global sign flip)
start = next(r["tooth"] for r in rows if r["phase"] == "A" and r["sense"] == "-"
             and rows[(r["tooth"]) % Q]["phase"] == "A")
plan = []
for i in range(Q):
    r = rows[(start - 1 + i) % Q]
    plan.append(dict(tooth=i + 1, phase=r["phase"],
                     sense="+" if r["sense"] == "-" else "-"))
with open(OUT / "coil_connection.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["tooth", "phase", "sense", "series_position"])
    w.writeheader()
    count = {"A": 0, "B": 0, "C": 0}
    for r in plan:
        count[r["phase"]] += 1
        w.writerow(dict(r, series_position=count[r["phase"]]))
R["connection"] = dict(pattern_first_9=" ".join(r["sense"] + r["phase"] for r in plan[:9]),
                       coils_per_phase=count)

# ------------------------------------------------------------ magnets
arc = math.radians(MAGNET["arc_deg"])
r_in, r_out = MAGNET["r_in"], MAGNET["r_out"]
a_mag = arc / 2 * (r_out ** 2 - r_in ** 2)
vol = a_mag * MAGNET["length"]
face = arc * r_out * MAGNET["length"]  # mm2, face against the drum
B_contact = 1.0                        # T, magnet on thick steel (estimate)
F_steel = B_contact ** 2 * face * 1e-6 / (2 * MU0)
R["magnet"] = dict(
    grade=MAGNET["grade"], count=40 * MAGNET["axial_pieces"], spares=8,
    r_in_mm=r_in, r_out_mm=round(r_out, 1), arc_deg=MAGNET["arc_deg"],
    chord_inner_mm=round(2 * r_in * math.sin(arc / 2), 2),
    chord_outer_mm=round(2 * r_out * math.sin(arc / 2), 2),
    thickness_mm=GEN["hm"], axial_length_mm=round(MAGNET["length"], 2),
    mass_g=round(vol * RHO["ndfeb"] * 1000, 1),
    total_kg=round(160 * vol * RHO["ndfeb"], 2),
    pull_on_steel_N_est=round(F_steel),
    pole_gap_at_r305_mm=round(math.radians(360 / 40 - MAGNET["arc_deg"]) * 305.35, 2),
)

# ------------------------------------------------------- voltage, test values
# Doc 06 round 2: 379 V line at 178 rpm, 29 turns, 69 mm stack, magnets 100 C;
# 890 V peak worst case at 250 rpm, -40 C. EMF scales with turns x stack length.
k_scale = TURNS / 29 * GEN["stack"] / 69.0
BR_TC = -0.0012                        # /K, N40UH typical, confirm with supplier
emf_hot = 379.0 * k_scale
emf_20 = emf_hot * (1 + BR_TC * (20 - 100)) / 1.0
R["voltage"] = dict(
    emf_line_rms_178rpm_100C=round(emf_hot), emf_line_rms_178rpm_20C=round(emf_20),
    emf_constant_V_per_rpm_20C=round(emf_20 / 178, 3),
    worst_peak_250rpm_minus40C=round(890 * k_scale),
    worst_peak_with_27_turns=round(890 * 27 / 29 * GEN["stack"] / 69),
    emf_with_27_turns_100C=round(379.0 * 27 / 29 * GEN["stack"] / 69),
    note="scaled from doc 06; replace with the FEA rerun of the segmented stator",
)
U_N = 630.0                            # max line rms in service (250 rpm cold), for test levels
R["tests"] = dict(
    rated_voltage_for_tests_V=U_N,
    hipot_new_winding_kV_ac_1min=round((2 * U_N + 1000) / 1000, 2),
    hipot_repeat_80pc_kV=round(0.8 * (2 * U_N + 1000) / 1000, 2),
    hipot_dc_equiv_kV=round(1.7 * (2 * U_N + 1000) / 1000, 1),
    winding_peak_max_kV_doc12=1.2,
    pdiv_min_kV_peak=round(1.2 * 1.25 * 1.25, 2),
    surge_kV_peak=3.5, ir_test_V_dc=1000, ir_min_Mohm_40C=1000, pi_min=2.0,
)

# ----------------------------------------------------------- balance
m_rotor = 96.0 + 34.5 + 7.3 + 4.1 + R["magnet"]["total_kg"]
for g, name in ((2.5, "G2.5"), (6.3, "G6.3")):
    e = g / (250 * 2 * math.pi / 60) * 1000      # µm at max service speed
    R.setdefault("balance", {})[name] = dict(e_um=round(e, 1),
                                             U_gmm=round(m_rotor * e))
R["balance"]["rotor_mass_kg"] = round(m_rotor, 1)

# ----------------------------------------------------------- laminations
n_sheets = round(GEN["stack"] * GEN["stacking"] / GEN["lam_thk"])
R["laminations"] = dict(sheets_per_stack=n_sheets, segments=Q,
                        segment_sheets_total=n_sheets * Q,
                        with_5pc_spare=math.ceil(n_sheets * Q * 1.05))

(OUT / "manufacturing_summary.json").write_text(json.dumps(R, indent=2))
print(json.dumps(R, indent=2))
