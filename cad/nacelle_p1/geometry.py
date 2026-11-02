"""Nacelle prototype P1: single source of truth for all part geometry.

Units: mm, kg. Axial coordinate x runs along the spindle axis, measured
rearward (downwind) from the rotor plane (x = 0 at the blade pitch axes).
r is the radius from the spindle axis. Turned or revolved parts are described
by closed (x, r) section polygons; the drawings, masses and the general
arrangement are all generated from these polygons.

Inputs frozen in earlier design docs:
  doc 06  generator (r_s 299, gap 2.0, sleeve 0.5, magnet 7.7 N40UH, stack 74,
          slot 65 + tip 2 + wedge 2, stator yoke 11.4, tooth 22.3, 40p/45s)
  doc 07  layout (front bearing x 120, rear bearing x 360, stator x 380,
          spindle 140/90 42CrMo4, yaw axis 750 behind the rotor plane)
  doc 08  design loads (spindle moment 9.8 kNm, bearing static 41/44 kN)
  doc 13  hub flange 12 x M16 10.9 on PCD 400, yaw bearing D_pw 360
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

# ----------------------------------------------------------------- materials
RHO = {  # kg/mm^3
    "steel": 7.85e-6,
    "iron_lam": 7.65e-6,
    "ductile_iron": 7.10e-6,
    "aluminium": 2.70e-6,
    "stainless": 7.95e-6,
    "ndfeb": 7.55e-6,
    "copper": 8.90e-6,
}

# ------------------------------------------------------- global arrangement
TILT_DEG = 5.0           # rotor shaft tilt, nose up (blade.py)
X_YAW = 750.0            # yaw axis behind the rotor plane, horizontal (doc 07)
X_HUB_FLANGE = 200.0     # hub rear face = drum front face
X_BRG_FRONT = 120.0      # bearing centres (doc 07)
X_BRG_REAR = 360.0
H_ROTOR = 530.0          # rotor centre height above the yaw bearing top face

# ------------------------------------------------------- generator (doc 06)
GEN = dict(
    poles=40, slots=45,
    r_s=299.0,           # stator outer (tooth tip) radius
    gap=2.0, sleeve=0.5, hm=7.7, h_ry=12.0,
    w_t=22.3, b0=4.0, h_tip=2.0, h_wedge=2.0, d_slot=65.0, h_sy=11.4,
    stack=74.0, alpha_m=0.80,
    lam_thk=0.35, stacking=0.97,
    turns_per_coil=28,   # 27 to 28 per doc 06, confirm with the first coil
)
GEN["r_slot_top"] = GEN["r_s"] - GEN["h_tip"] - GEN["h_wedge"]      # 295
GEN["r_slot_bot"] = GEN["r_slot_top"] - GEN["d_slot"]              # 230
GEN["r_si"] = GEN["r_slot_bot"] - GEN["h_sy"]                      # 218.6
GEN["r_m1"] = GEN["r_s"] + GEN["gap"] + GEN["sleeve"]              # 301.5
GEN["r_m2"] = GEN["r_m1"] + GEN["hm"]                              # 309.2
X_STACK = (343.0, 417.0)                                           # stack, centre 380

# ------------------------------------------------- purchased main bearings
# Tapered roller bearing 32028 X (ISO 355 dimension series 4DC), one per seat.
# Ratings are typical catalogue values for this size: confirm with the
# selected supplier (SKF, Timken, Schaeffler, NSK all list it).
BRG = dict(designation="32028 X", d=140.0, D=210.0, T=45.0, C_kN=280.0, C0_kN=430.0,
           e=0.46, Y=1.3, Y0=0.7, da_min=152.0, Da_max=199.0, mass=4.8)

# ----------------------------------------------------------- spindle NP1-100
SPINDLE_OUTER = [  # (x, r), front to rear
    (40.0, 60.0),     # nose, slip-ring / plenum cap seat (Ø120)
    (52.0, 60.0), (52.0, 67.5),      # thread M135x2 (precision locknut KMT 27)
    (80.0, 67.5), (80.0, 70.0),      # spacer + front cone seat Ø140 f6
    (142.5, 70.0), (142.5, 69.0),    # relief Ø138 between seats
    (337.5, 69.0), (337.5, 70.0),    # rear cone seat Ø140 j6
    (382.5, 70.0), (382.5, 77.5),    # cone abutment shoulder Ø155
    (386.0, 77.5), (386.0, 75.0),    # seal counterface Ø150 h9, Ra 0.4
    (430.0, 75.0),
] + [  # R10 flange fillet
    (430.0 + 10 * math.sin(a), 85.0 - 10 * math.cos(a))
    for a in [i * math.pi / 2 / 6 for i in range(1, 7)]
] + [
    (440.0, 200.0),                  # flange Ø400 (rear drum seal runs on its OD)
    (470.0, 200.0), (470.0, 100.0),  # flange rear face
    (476.0, 100.0), (476.0, 45.0),   # centring spigot Ø200 f7 into bedplate
]
SPINDLE_BORE_R = 45.0                # Ø90 H8 through
SPINDLE = dict(
    x_front=40.0, x_rear=476.0, bore=90.0,
    flange_od=400.0, flange_x=(440.0, 470.0),
    carrier_bolts=dict(n=12, size="M12", pcd=240.0, depth=24.0),
    bedplate_bolts=dict(n=12, size="M20", pcd=350.0, depth=26.0),
    cable_holes=dict(n=2, dia=28.0, pcd=290.0, angles=(15.0, 195.0)),
    dowels=dict(n=2, dia=10.0, pcd=240.0, angles=(45.0, 225.0)),
)

# Front spacer NP1-101 (between locknut and front cone, lip seal counterface)
SPACER = dict(x=(80.0, 97.5), d=140.0, od=160.0)

# ------------------------------------------------------ drum weldment NP1-210
# Each element is a closed (x, r) section polygon (welded, then finish machined).
DRUM_PARTS = {
    "bearing housing": [(92.0, 105.0), (142.5, 105.0), (142.5, 98.0), (337.5, 98.0),
                        (337.5, 105.0), (385.0, 105.0), (385.0, 120.0), (320.0, 120.0),
                        (320.0, 112.0), (225.0, 112.0), (200.0, 112.0), (160.0, 112.0),
                        (160.0, 120.0), (92.0, 120.0)],
    "hub web (inner)": [(195.0, 112.0), (195.0, 180.0), (200.0, 180.0), (200.0, 232.0),
                        (220.0, 232.0), (220.0, 112.0)],
    "web (outer)": [(212.0, 232.0), (220.0, 232.0), (220.0, 312.0), (212.0, 312.0)],
    "shell": [(212.0, 312.0), (335.0, 312.0), (335.0, GEN["r_m2"]), (425.0, GEN["r_m2"]),
              (425.0, 312.0), (451.0, 312.0), (451.0, 318.0), (425.0, 318.0),
              (425.0, 323.0), (335.0, 323.0), (335.0, 318.0), (212.0, 318.0)],
    "rear flange ring": [(451.0, 312.0), (465.0, 312.0), (465.0, 345.0), (451.0, 345.0)],
}
DRUM = dict(
    hub_bolts=dict(n=12, size="M16", pcd=400.0, depth=25.0),   # doc 13, tapped through web
    hub_spigot=360.0,                                          # Ø360 f7 into hub recess
    cup_seat=210.0, cup_fit="P7",
    rear_cover_bolts=dict(n=24, size="M10", pcd=644.0),
    disc_bolts=dict(n=24, size="M12", pcd=662.0),
    lock_holes=dict(n=12, dia=26.0, pcd=662.0, depth=20.0),
)

# Main bearing seal covers NP1-211 (rotating, bolted to the housing ends)
SEAL_COVER_FRONT = [(82.0, 81.0), (92.0, 81.0), (92.0, 120.0), (82.0, 120.0)]
SEAL_COVER_REAR = [(385.0, 76.0), (395.0, 76.0), (395.0, 120.0), (385.0, 120.0)]

# Drum rear cover NP1-212 with seal carrier (Ø400 lip seal on the flange OD)
REAR_COVER = [(465.0, 216.0), (465.0, 345.0), (475.0, 345.0), (475.0, 216.0)]   # 5083 Al
REAR_SEAL_CARRIER = [(450.0, 216.0), (465.0, 216.0), (465.0, 236.0), (450.0, 236.0)]

# Brake disc NP1-230
DISC = dict(x=(435.0, 451.0), id=640.0, od=800.0, pad_r=(345.0, 395.0))
DISC_POLY = [(435.0, 320.0), (451.0, 320.0), (451.0, 400.0), (435.0, 400.0)]

# ------------------------------------------------- stator carrier NP1-200
CARRIER = [
    (343.5, 200.0), (343.5, GEN["r_si"]), (417.0, GEN["r_si"]),   # rim (stack seat)
    (417.0, 228.0), (440.0, 228.0),                               # rear stack stop
    (440.0, 90.0), (415.0, 90.0), (415.0, 200.0),                 # 25 mm web
]
STATOR_RING = [(335.0, 203.0), (343.0, 203.0), (343.0, 229.0), (335.0, 229.0)]  # NP1-202
STACK_POLY = [(X_STACK[0], GEN["r_si"]), (X_STACK[1], GEN["r_si"]),
              (X_STACK[1], GEN["r_s"]), (X_STACK[0], GEN["r_s"])]
END_WINDING = 22.0   # axial overhang of the tooth-coil end turns (estimate)

# Magnet segments NP1-220 (bought): radial arc segments, 4 per pole axially
MAGNET = dict(grade="N40UH", r_in=GEN["r_m1"], r_out=GEN["r_m2"],
              arc_deg=360.0 / 40 * 0.80, axial_pieces=4,
              length=(GEN["stack"] - 3 * 0.2) / 4)   # 0.2 mm glue gaps

# Cooling insert NP1-110 (6082-T6 extrusion), sits in the Ø90 bore
INSERT = dict(od=90.0, shell=4.0, tube_od=40.0, tube_id=34.0, fins=16, fin_t=2.5,
              length=420.0, x=(46.0, 466.0))

# --------------------------------------------------------- bedplate NP1-300
BED = dict(front_plate=40.0, side_plate=20.0, bottom_plate=40.0, rear_plate=20.0,
           width=520.0, x_bottom=(-330.0, 330.0),      # world X about the yaw axis
           top_above_axis=250.0,
           yaw_inner_bolts=dict(n=16, size="M16", pcd=300.0), yaw_bore=220.0)

# Yaw bearing (bought, doc 13): preliminary dimensions, confirm with supplier
YAW = dict(d_pw=360.0, balls=53, ball=19.0, gear_z=150, module=4.0,
           inner=dict(id=220.0, od=350.0, pcd=300.0), outer=dict(id=370.0, pcd=440.0),
           height=70.0, mass=55.0)

# ------------------------------------------------------- bench parts NP1-6xx
DUMMY_HUB = dict(flange_od=470.0, flange_t=25.0, bell_od=340.0, bell_t=15.0,
                 x_front=0.0, front_t=25.0, recess=360.0)
LOAD_SHAFT = dict(d=100.0, x=(-520.0, 0.0), load_brg="22220 E", x_load=-200.0)


# =================================================================== helpers
def poly_area_centroid(poly):
    """Area and centroid of a closed polygon in the (x, r) plane."""
    a = cx = cy = 0.0
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        c = x0 * y1 - x1 * y0
        a += c
        cx += (x0 + x1) * c
        cy += (y0 + y1) * c
    a *= 0.5
    if abs(a) < 1e-12:
        return 0.0, (0.0, 0.0)
    return abs(a), (cx / (6 * a), cy / (6 * a))


def revolved_volume(poly):
    """Pappus: volume of a section polygon revolved about the x axis, mm^3."""
    a, (_, rc) = poly_area_centroid(poly)
    return 2 * math.pi * rc * a


def turned_section(outer, bore_r):
    """Closed section polygon of a part with a plain bore."""
    x0, x1 = outer[0][0], outer[-1][0]
    return [(x0, bore_r)] + outer + [(x1, bore_r)]


def spindle_section():
    return turned_section(SPINDLE_OUTER, SPINDLE_BORE_R)


def lamination_outline(n_arc=6):
    """Outer contour of one stator lamination (teeth and open slots), list of (x, y)."""
    g = GEN
    tau = 2 * math.pi / g["slots"]
    pts = []
    for k in range(g["slots"]):
        th = k * tau                      # slot centre angle
        c, s = math.cos(th), math.sin(th)

        def rot(px, py):
            return (px * c - py * s, px * s + py * c)

        def side(r, sign):
            # point on the tooth flank at radius r, slot-local frame (slot along +x)
            a = sign * tau / 2
            ux, uy = math.cos(a), math.sin(a)
            nx, ny = -math.sin(a), math.cos(a)
            t = math.sqrt(r * r - (g["w_t"] / 2) ** 2)
            w = -sign * g["w_t"] / 2
            return (t * ux + w * nx, t * uy + w * ny)

        y0 = g["b0"] / 2
        r_open = g["r_s"] - g["h_tip"]
        # lower flank (negative side) from tip to bottom, bottom arc, upper flank
        seq = [(math.sqrt(g["r_s"] ** 2 - y0 ** 2), -y0),
               (math.sqrt(r_open ** 2 - y0 ** 2), -y0),
               side(g["r_slot_top"], -1), side(g["r_slot_bot"], -1)]
        a0 = math.atan2(seq[-1][1], seq[-1][0])
        pu = side(g["r_slot_bot"], +1)
        a1 = math.atan2(pu[1], pu[0])
        for i in range(1, n_arc):
            a = a0 + (a1 - a0) * i / n_arc
            seq.append((g["r_slot_bot"] * math.cos(a), g["r_slot_bot"] * math.sin(a)))
        seq += [pu, side(g["r_slot_top"], +1),
                (math.sqrt(r_open ** 2 - y0 ** 2), y0),
                (math.sqrt(g["r_s"] ** 2 - y0 ** 2), y0)]
        pts += [rot(*p) for p in seq]
        # tooth tip arc to the next slot
        a_start = th + math.asin(y0 / g["r_s"])
        a_end = th + tau - math.asin(y0 / g["r_s"])
        for i in range(1, n_arc):
            a = a_start + (a_end - a_start) * i / n_arc
            pts.append((g["r_s"] * math.cos(a), g["r_s"] * math.sin(a)))
    return pts


def lamination_area():
    pts = lamination_outline(n_arc=12)
    a, _ = poly_area_centroid(pts)
    return a - math.pi * GEN["r_si"] ** 2


@dataclass
class MassItem:
    name: str
    mass: float
    note: str = ""


def mass_table():
    st = RHO["steel"]
    items = []
    sp = revolved_volume(spindle_section()) * st
    holes = (12 * math.pi / 4 * 17.5 ** 2 * 26 + 12 * math.pi / 4 * 10.2 ** 2 * 24) * st
    items.append(MassItem("Spindle NP1-100", sp - holes, "42CrMo4+QT"))
    items.append(MassItem("Front spacer NP1-101", math.pi / 4 * (160 ** 2 - 140 ** 2) * 17.5 * st))
    drum = sum(revolved_volume(p) for p in DRUM_PARTS.values()) * st
    items.append(MassItem("Rotor drum weldment NP1-210", drum, "S355J2+N"))
    items.append(MassItem("Seal covers NP1-211 (2)",
                          (revolved_volume(SEAL_COVER_FRONT) + revolved_volume(SEAL_COVER_REAR)) * st))
    items.append(MassItem("Drum rear cover NP1-212",
                          (revolved_volume(REAR_COVER) + revolved_volume(REAR_SEAL_CARRIER)) * RHO["aluminium"],
                          "5083-H111"))
    items.append(MassItem("Brake disc NP1-230", revolved_volume(DISC_POLY) * st))
    mag = 40 * math.radians(MAGNET["arc_deg"]) / 2 * (MAGNET["r_out"] ** 2 - MAGNET["r_in"] ** 2) \
        * GEN["stack"] * RHO["ndfeb"]
    items.append(MassItem("Magnets NP1-220 (160 pcs)", mag, "N40UH"))
    items.append(MassItem("Main bearings 32028 X (2)", 2 * BRG["mass"]))
    items.append(MassItem("Stator carrier NP1-200", revolved_volume(CARRIER) * st, "S355J2+N"))
    lam = lamination_area() * GEN["stack"] * GEN["stacking"] * RHO["iron_lam"]
    items.append(MassItem("Stator core NP1-201 (laminations)", lam, "M270-35A"))
    items.append(MassItem("Stator winding (copper, insulation, potting)", 24.0, "doc 04: 21 kg Cu"))
    items.append(MassItem("Stator clamp ring NP1-202", revolved_volume(STATOR_RING) * RHO["stainless"]))
    ins_area = (math.pi / 4 * (90 ** 2 - 82 ** 2) + math.pi / 4 * (40 ** 2 - 34 ** 2)
                + INSERT["fins"] * INSERT["fin_t"] * (41 - 20))
    items.append(MassItem("Cooling insert NP1-110", ins_area * INSERT["length"] * RHO["aluminium"]))
    return items


if __name__ == "__main__":
    tot = 0
    for it in mass_table():
        print(f"{it.name:48s} {it.mass:7.1f} kg  {it.note}")
        tot += it.mass
    print(f"{'total':48s} {tot:7.1f} kg")
    print("lamination area mm2", round(lamination_area()))
