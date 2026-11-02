"""Nacelle P1 fit-check model: every part as its own 1:1 solid (CadQuery).

All dimensions come from ../nacelle_p1/geometry.py (the P1 single source of
truth) and the P1 drawing notes. Nothing is scaled: a printed part is the size
of the steel part. Where a printed part mates with another printed part on a
fit that is a press or transition fit in steel, the bore is opened by
PRINT_CLEARANCE so the plastic parts can be put together and taken apart by
hand. Every such change is listed in the part's `print_mods` text.

Frames
------
Each drivetrain part is built in the spindle frame of geometry.py
(x rearward along the spindle axis from the rotor plane, z up, y lateral),
then placed in the WORLD frame used by the assembly:
    X rearward (horizontal), Y lateral, Z up, origin on the yaw axis at the
    bedplate underside (= yaw bearing top face).
The spindle axis is tilted 5 deg nose up and the rotor centre is at
X = -750, Z = 570 (drawing NP1-300).

Bought parts (bearings, locknut, yaw bearing, calipers, gearmotors) are
printed as envelopes so the fit can be checked before they arrive; the
bearing envelopes are estimates for a 32028 X and must be replaced by the
supplier drawing (flagged in their notes).
"""
from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass, field

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "nacelle_p1"))
import geometry as G  # noqa: E402

PRINT_CLEARANCE = 0.20       # mm radial, added to printed-on-printed fits
TILT = G.TILT_DEG
RC = (-G.X_YAW, 0.0, G.H_ROTOR + 40.0)   # rotor centre in WORLD (X, Y, Z)

# Tap-drill diameters for tapped holes (printed parts: tap the plastic or use
# a nut behind; the hole position is what the fit check is about).
TAP = {"M8": 6.8, "M10": 8.5, "M12": 10.2, "M16": 14.0, "M20": 17.5}
CLEAR = {"M8": 9.0, "M10": 11.0, "M12": 13.0, "M16": 17.0, "M20": 22.0}


# ============================================================ part container
@dataclass
class Part:
    pid: str                    # file stem, e.g. "NP1-100_spindle"
    name: str
    solid: cq.Shape             # in WORLD frame
    group: str                  # "stationary", "rotating", "bench", "envelope"
    source: str                 # drawing / BOM line
    color: tuple = (0.7, 0.7, 0.7)
    make_buy: str = "make"
    print_mods: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    axis: str | None = "spindle"  # revolved about the spindle axis? (used by the splitter)
    qty: int = 1


# ================================================================== helpers
def revolve(poly):
    """Closed (x, r) section polygon revolved 360 deg about the x axis."""
    pts = []
    for x, r in poly:
        p = (round(float(x), 6), round(float(r), 6))
        if not pts or abs(p[0] - pts[-1][0]) + abs(p[1] - pts[-1][1]) > 1e-6:
            pts.append(p)
    if abs(pts[0][0] - pts[-1][0]) + abs(pts[0][1] - pts[-1][1]) < 1e-6:
        pts = pts[:-1]
    return cq.Workplane("XY").polyline(pts).close().revolve(360, (0, 0, 0), (1, 0, 0)).val()


def cyl_x(x0, x1, r, y=0.0, z=0.0):
    """Cylinder along +x from x0 to x1, radius r, centred at (y, z)."""
    return cq.Solid.makeCylinder(r, x1 - x0, cq.Vector(x0, y, z), cq.Vector(1, 0, 0))


def polar(r, a_deg):
    """Front-view polar position (angle from +y lateral towards +z up)."""
    a = math.radians(a_deg)
    return r * math.cos(a), r * math.sin(a)


def bolt_holes(solid, n, pcd, dia, x0, x1, start=0.0, angles=None):
    angs = angles if angles is not None else [start + 360.0 * k / n for k in range(n)]
    for a in angs:
        y, z = polar(pcd / 2, a)
        solid = solid.cut(cyl_x(x0, x1, dia / 2, y, z))
    return solid


def box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


def to_world(shape):
    """Spindle frame -> WORLD frame (5 deg tilt, rotor centre at RC)."""
    return shape.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 1, 0), TILT).translate(cq.Vector(*RC))


def open_bore(poly, r_old, r_new):
    """Move every polygon vertex at radius r_old to r_new (bore clearance)."""
    return [(x, r_new if abs(r - r_old) < 1e-6 else r) for x, r in poly]


# ======================================================= bearing envelopes
# 32028 X: d 140, D 210, T 45 (cone width B 45, cup width C 34).
# Envelope ESTIMATES (cage and roller outline) until the supplier drawing is in.
CONE_R_LARGE, CONE_R_SMALL = 95.5, 90.5      # cone + rollers + cage envelope
CUP_R_LARGE, CUP_R_SMALL = 96.5, 91.5        # cup raceway
CUP_W = 34.0


def cone_poly(x_large, x_small, bore=70.0):
    s = 1 if x_small > x_large else -1
    rib = 6.0
    return [(x_large, bore), (x_small, bore), (x_small, CONE_R_SMALL - 4.0),
            (x_small - s * 4.0, CONE_R_SMALL), (x_large + s * rib, CONE_R_LARGE),
            (x_large, CONE_R_LARGE)]


def cup_poly(x_back, x_front_large, od=105.0):
    """Cup between its back face (small raceway end) and its front (large end)."""
    return [(x_back, CUP_R_SMALL), (x_back, od), (x_front_large, od), (x_front_large, CUP_R_LARGE)]


# ========================================================== section polygons
# Kept separate so the 2-D assembly check (assembly_check.py) uses exactly
# the geometry the solids are built from.
def sections():
    """Full-scale (x, r) section polygons per axisymmetric part, as drawn."""
    S = {}
    S["NP1-100_spindle"] = G.spindle_section()
    S["NP1-101_front_spacer"] = [(80.0, 70.0), (97.5, 70.0), (97.5, 80.0), (80.0, 80.0)]
    S["NP1-110_cooling_insert"] = [(G.INSERT["x"][0], 17.0), (G.INSERT["x"][1], 17.0),
                                   (G.INSERT["x"][1], 45.0), (G.INSERT["x"][0], 45.0)]
    S["KMT27_locknut_envelope"] = [(52.0, 67.5), (80.0, 67.5), (80.0, 87.0), (52.0, 87.0)]
    # front bearing: large ends face outward (O arrangement)
    S["32028X_front_cone_envelope"] = cone_poly(97.5, 142.5)
    S["32028X_front_cup_envelope"] = cup_poly(142.5, 142.5 - CUP_W)
    S["32028X_rear_cone_envelope"] = cone_poly(382.5, 337.5)
    S["32028X_rear_cup_envelope"] = cup_poly(337.5, 337.5 + CUP_W)
    S["NP1-200_stator_carrier"] = G.CARRIER
    S["NP1-201_stator_core"] = G.STACK_POLY
    S["NP1-202_stator_clamp_ring"] = G.STATOR_RING
    ew = G.END_WINDING
    x0, x1 = G.X_STACK
    S["stator_end_winding_front_envelope"] = [(x0 - ew, 242.0), (x0, 232.0), (x0, 292.0), (x0 - ew, 282.0)]
    S["stator_end_winding_rear_envelope"] = [(x1, 232.0), (x1 + ew, 242.0), (x1 + ew, 282.0), (x1, 292.0)]
    S["NP1-210_rotor_drum"] = None  # union of DRUM_PARTS
    S["NP1-211_front_seal_cover"] = G.SEAL_COVER_FRONT
    S["NP1-211_rear_seal_cover"] = G.SEAL_COVER_REAR
    S["NP1-212_drum_rear_cover"] = None  # cover + seal carrier
    S["NP1-220_magnet_ring"] = [(x0, G.GEN["r_m1"]), (x1, G.GEN["r_m1"]),
                                (x1, G.GEN["r_m2"]), (x0, G.GEN["r_m2"])]
    S["NP1-230_brake_disc"] = G.DISC_POLY
    return S


DUMMY_HUB_AS_DRAWN = {
    "flange": [(175, 180.5), (195, 180.5), (195, 170), (200, 170), (200, 235), (175, 235)],
    "bell": [(25, 155), (175, 155), (175, 170), (25, 170)],
    "front": [(0, 50), (25, 50), (25, 170), (0, 170)],
}
# Drawing NP1-600 puts the Ø340 step at the hub face, where the drum's Ø360
# spigot has to go. Intent per the drawing notes: Ø361 recess at the face.
DUMMY_HUB_FIXED_FLANGE = [(175, 170), (190, 170), (190, 180.5), (200, 180.5), (200, 235), (175, 235)]


# ===================================================================== parts
def build_parts():
    P = []
    S = sections()
    c = PRINT_CLEARANCE
    sp = G.SPINDLE

    # ------------------------------------------------------------ spindle
    s = revolve(S["NP1-100_spindle"])
    s = bolt_holes(s, 12, sp["carrier_bolts"]["pcd"], TAP["M12"], 440 - 1, 440 + sp["carrier_bolts"]["depth"])
    s = bolt_holes(s, 12, sp["bedplate_bolts"]["pcd"], TAP["M20"], 470 - sp["bedplate_bolts"]["depth"], 471)
    s = bolt_holes(s, 2, sp["cable_holes"]["pcd"], sp["cable_holes"]["dia"], 435, 475,
                   angles=sp["cable_holes"]["angles"])
    s = bolt_holes(s, 2, sp["dowels"]["pcd"], sp["dowels"]["dia"], 439, 456, angles=sp["dowels"]["angles"])
    P.append(Part("NP1-100_spindle", "Spindle", to_world(s), "stationary", "NP1-100 / BOM 1",
                  (0.55, 0.57, 0.62),
                  print_mods=["M135x2 thread printed as a plain Ø135 seat (use the locknut envelope)",
                              "tapped holes printed at tap-drill size (M12 Ø10.2, M20 Ø17.5)"]))

    P.append(Part("NP1-101_front_spacer", "Front spacer / seal counterface",
                  to_world(revolve(open_bore(S["NP1-101_front_spacer"], 70.0, 70.0 + c))),
                  "stationary", "NP1-101 / BOM 2", (0.75, 0.75, 0.8),
                  print_mods=[f"bore +{c} mm radial (slides on the printed spindle)"]))

    # cooling insert: shell + centre tube + 16 fins (the 0 and 180 deg fins are the partition)
    ins = G.INSERT
    xa, xb = ins["x"]
    body = cyl_x(xa, xb, 45.0 - c).cut(cyl_x(xa - 1, xb + 1, 45.0 - ins["shell"]))
    body = body.fuse(cyl_x(xa, xb, ins["tube_od"] / 2).cut(cyl_x(xa - 1, xb + 1, ins["tube_id"] / 2)))
    for k in range(ins["fins"]):
        a = 360.0 * k / ins["fins"]
        fin = box(xa, xb, ins["tube_od"] / 2 - 0.5, 45.0 - ins["shell"] + 0.5,
                  -ins["fin_t"] / 2, ins["fin_t"] / 2)
        body = body.fuse(fin.rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), a))
    P.append(Part("NP1-110_cooling_insert", "Spindle cooling insert (finned)", to_world(body.clean()),
                  "stationary", "NP1-110 / BOM 5", (0.85, 0.85, 0.88),
                  print_mods=[f"OD -{c} mm radial (shrink fit in steel, slide fit in print)"]))

    P.append(Part("KMT27_locknut_envelope", "Precision locknut KMT 27 (envelope)",
                  to_world(revolve(open_bore(S["KMT27_locknut_envelope"], 67.5, 67.5 + c))),
                  "stationary", "BOM 4 (bought)", (0.3, 0.3, 0.3), make_buy="buy (envelope)",
                  print_mods=["plain bore, no thread"]))

    # ------------------------------------------------------------ bearings
    for key, label, grp in [("32028X_front_cone_envelope", "Front bearing cone + rollers (envelope)", "stationary"),
                            ("32028X_rear_cone_envelope", "Rear bearing cone + rollers (envelope)", "stationary")]:
        P.append(Part(key, label, to_world(revolve(open_bore(S[key], 70.0, 70.0 + c))), grp,
                      "BOM 3 (bought)", (0.8, 0.65, 0.2), make_buy="buy (envelope)",
                      print_mods=[f"bore +{c} mm radial"],
                      notes=["envelope estimated for 32028 X: replace with the supplier drawing before trusting the carrier-bore check"]))
    for key, label in [("32028X_front_cup_envelope", "Front bearing cup (envelope)"),
                       ("32028X_rear_cup_envelope", "Rear bearing cup (envelope)")]:
        P.append(Part(key, label, to_world(revolve(open_bore(S[key], 105.0, 105.0 - c))), "rotating",
                      "BOM 3 (bought)", (0.8, 0.65, 0.2), make_buy="buy (envelope)",
                      print_mods=[f"OD -{c} mm radial (P7 press fit in steel)"],
                      notes=["raceway estimated: replace with the supplier drawing"]))

    # ------------------------------------------------------------ stator
    car = revolve(S["NP1-200_stator_carrier"])
    car = bolt_holes(car, 12, 240.0, CLEAR["M12"], 410, 445)
    car = bolt_holes(car, 2, 240.0, 10.0, 410, 445, angles=sp["dowels"]["angles"])
    car = bolt_holes(car, 2, 290.0, 28.0, 410, 445, angles=sp["cable_holes"]["angles"])
    car = bolt_holes(car, 12, 418.0, TAP["M8"], 343.0, 343.5 + 20, start=15)
    for a in (90, 210, 330):   # keyways 10 wide x 4 deep in the stack seat
        kw = box(343.0, 417.5, -5.0, 5.0, G.GEN["r_si"] - 4.0, G.GEN["r_si"] + 1.0)
        car = car.cut(kw.rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), a - 90))
    P.append(Part("NP1-200_stator_carrier", "Stator carrier", to_world(car), "stationary",
                  "NP1-200 / BOM 7", (0.45, 0.5, 0.6),
                  print_mods=["M8 clamp-ring holes at tap-drill size Ø6.8"]))

    lam = cq.Workplane("YZ").polyline(G.lamination_outline(n_arc=6)).close().extrude(G.GEN["stack"]).val()
    lam = lam.translate(cq.Vector(G.X_STACK[0], 0, 0))
    lam = lam.cut(cyl_x(G.X_STACK[0] - 1, G.X_STACK[1] + 1, G.GEN["r_si"] + c))
    for a in (90, 210, 330):   # key notches in the lamination bore
        kn = box(G.X_STACK[0] - 1, G.X_STACK[1] + 1, -5.0 - c, 5.0 + c, G.GEN["r_si"] - 1.0, G.GEN["r_si"] + 4.0 + c)
        lam = lam.cut(kn.rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), a - 90))
    P.append(Part("NP1-201_stator_core", "Stator core (bonded lamination stack, 45 slots)", to_world(lam),
                  "stationary", "NP1-201 / BOM 8", (0.35, 0.35, 0.4),
                  print_mods=[f"bore +{c} mm radial (shrink fit in steel)", "printed as one solid stack 74 mm"]))
    for a in (90, 210, 330):
        key = box(343.5, 417.0, -5.0 + c / 2, 5.0 - c / 2,
                  G.GEN["r_si"] - 4.0 + c / 2, G.GEN["r_si"] + 4.0 - c / 2)
        P.append(Part(f"stator_key_{a:03d}", f"Stator key 10x8, 73.5 long (BOM says 90) at {a} deg",
                      to_world(key.rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), a - 90)),
                      "stationary", "BOM 10", (0.6, 0.6, 0.6), make_buy="buy (envelope)", axis=None,
                      print_mods=[f"{c / 2} mm smaller each side", "73.5 mm long to fit the 73.5 mm seat (BOM line 10 says 90)"]))

    ring = revolve(S["NP1-202_stator_clamp_ring"])
    ring = bolt_holes(ring, 12, 418.0, CLEAR["M8"], 330, 345, start=15)
    P.append(Part("NP1-202_stator_clamp_ring", "Stator front clamp ring", to_world(ring), "stationary",
                  "NP1-202 / BOM 9", (0.8, 0.8, 0.82)))
    for key, label in [("stator_end_winding_front_envelope", "End windings, front (envelope)"),
                       ("stator_end_winding_rear_envelope", "End windings, rear (envelope)")]:
        P.append(Part(key, label, to_world(revolve(S[key])), "stationary", "doc 14 4.4 (22 mm overhang estimate)",
                      (0.75, 0.45, 0.2), notes=["space claim of the potted tooth-coil end turns"]))

    # ------------------------------------------------------------ rotor
    drum = None
    for poly in G.DRUM_PARTS.values():
        d = revolve(poly)
        drum = d if drum is None else drum.fuse(d)
    drum = drum.clean()
    D = G.DRUM
    drum = bolt_holes(drum, 12, 400.0, TAP["M16"], 190, 225)
    drum = bolt_holes(drum, 24, 662.0, TAP["M12"], 450, 466,
                      angles=[a for a in range(0, 360, 10) if a % 30 != 0])
    drum = bolt_holes(drum, 12, 662.0, 26.0, 450, 466, angles=list(range(0, 360, 30)))
    drum = bolt_holes(drum, 24, 644.0, TAP["M10"], 450, 466, start=5)
    P.append(Part("NP1-210_rotor_drum", "Rotor drum weldment", to_world(drum), "rotating",
                  "NP1-210 / BOM 15", (0.25, 0.4, 0.6),
                  print_mods=["cup seats Ø210 printed at nominal; the cup envelopes are reduced instead",
                              "tapped holes at tap-drill size"]))

    P.append(Part("NP1-211_front_seal_cover", "Front bearing seal cover", to_world(revolve(S["NP1-211_front_seal_cover"])),
                  "rotating", "NP1-211 / BOM 16", (0.7, 0.7, 0.7)))
    P.append(Part("NP1-211_rear_seal_cover", "Rear bearing seal cover", to_world(revolve(S["NP1-211_rear_seal_cover"])),
                  "rotating", "NP1-211 / BOM 16", (0.7, 0.7, 0.7),
                  notes=["as drawn its Ø152 bore overlaps the Ø155 cone shoulder: see assembly check"]))
    rc_ = revolve(G.REAR_COVER).fuse(revolve(G.REAR_SEAL_CARRIER)).clean()
    rc_ = bolt_holes(rc_, 24, 644.0, CLEAR["M10"], 460, 480, start=5)
    P.append(Part("NP1-212_drum_rear_cover", "Drum rear cover with Ø400 seal carrier", to_world(rc_), "rotating",
                  "NP1-212 / BOM 19", (0.82, 0.84, 0.87)))

    # magnets: ring with the 40 pole pieces as separate bumps is overkill; one
    # ring with 40 grooves between poles shows pole pitch and the 7.2 deg arcs
    mag = revolve(S["NP1-220_magnet_ring"])
    gap_deg = 360.0 / 40 * (1 - G.GEN["alpha_m"])
    for k in range(40):
        a = 360.0 * k / 40
        g = box(G.X_STACK[0] - 1, G.X_STACK[1] + 1, -1, 1, G.GEN["r_m1"] - 1, G.GEN["r_m2"] - 1.0)
        w = 2 * G.GEN["r_m1"] * math.sin(math.radians(gap_deg / 2))
        g = box(G.X_STACK[0] - 1, G.X_STACK[1] + 1, -w / 2, w / 2, G.GEN["r_m1"] - 1, G.GEN["r_m2"] - 1.5)
        mag = mag.cut(g.rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), a))
    P.append(Part("NP1-220_magnet_ring", "Magnet layer, 40 poles (dummy, no magnets)", to_world(mag.clean()),
                  "rotating", "NP1-220 / BOM 22", (0.2, 0.2, 0.25),
                  print_mods=["one ring instead of 160 segments; pole gaps as grooves",
                              "do not put real magnets in a printed drum"]))

    disc = revolve(G.DISC_POLY)
    disc = bolt_holes(disc, 24, 662.0, CLEAR["M12"], 430, 455, angles=[a for a in range(0, 360, 10) if a % 30 != 0])
    disc = bolt_holes(disc, 12, 662.0, 26.0, 430, 455, angles=list(range(0, 360, 30)))
    P.append(Part("NP1-230_brake_disc", "Brake disc Ø800", to_world(disc), "rotating", "NP1-230 / BOM 25",
                  (0.6, 0.3, 0.3)))

    # rotor lock pin (NP1-320), engaged in the lock hole at 0 deg (lateral)
    pin_poly = [(0, 0), (0, 12.5 - c), (40, 12.5 - c), (40, 15), (110, 15), (110, 10), (130, 10), (130, 0)]
    pin = cq.Workplane("XY").polyline(pin_poly).close().revolve(360, (0, 0, 0), (1, 0, 0)).val()
    # pin nose enters from the rear through the disc and ring: nose at x = 435
    pin = pin.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), 180).translate(cq.Vector(435.0 + 40, 0, 0))
    y, z = polar(331.0, 90)
    pin = pin.translate(cq.Vector(0, y, z))
    P.append(Part("NP1-320_lock_pin", "Rotor lock pin Ø25 (engaged)", to_world(pin), "stationary",
                  "NP1-320 / BOM 30", (0.9, 0.6, 0.1), axis=None,
                  print_mods=[f"Ø25 nose -{c} mm radial"],
                  notes=["shown engaged through the disc and drum flange ring at the top (90 deg) lock hole; holder bracket not drawn yet"]))

    # ------------------------------------------------------------ bedplate (WORLD frame)
    P += bedplate_parts()

    # ------------------------------------------------------------ yaw bearing envelopes
    P += yaw_parts()

    # ------------------------------------------------------------ brake caliper space claims
    P += caliper_envelopes()
    P += rotor_caliper_brackets()

    # ------------------------------------------------------------ yaw drives, yaw brake, tower top
    P += yaw_drive_parts()
    P += yaw_brake_parts()
    P += tower_top_parts()

    # ------------------------------------------------------------ bench dummy hub
    hub = None
    for poly in (DUMMY_HUB_FIXED_FLANGE, DUMMY_HUB_AS_DRAWN["bell"], DUMMY_HUB_AS_DRAWN["front"]):
        h = revolve(poly)
        hub = h if hub is None else hub.fuse(h)
    hub = hub.fuse(revolve([(-520, 0), (0, 0), (0, 50), (-520, 50)])).clean()
    hub = bolt_holes(hub, 12, 400.0, CLEAR["M16"], 170, 205)
    P.append(Part("NP1-600_dummy_hub", "Bench dummy hub with Ø100 shaft", to_world(hub), "bench",
                  "NP1-600 / BOM 41", (0.5, 0.6, 0.45),
                  print_mods=["Ø361 recess moved to the hub face (drawing has the step reversed, see assembly check)"]))
    return P


# ------------------------------------------------------------------ bedplate
def _P(s_, u):
    """Spindle-frame (s along axis, u up) -> WORLD (X, Z)."""
    t = math.radians(TILT)
    return (RC[0] + math.cos(t) * s_ + math.sin(t) * u, RC[2] - math.sin(t) * s_ + math.cos(t) * u)


def _xz_prism(pts, y0, y1):
    """Polygon in the WORLD XZ plane extruded from Y = y0 to y1."""
    wp = cq.Workplane("XZ", origin=(0, y1, 0)).polyline(pts).close().extrude(y1 - y0)
    return wp.val()


def bedplate_parts():
    t = math.radians(TILT)
    B = G.BED
    pf_z = _P(476.0, 0)[1]
    tb = -(pf_z - 40.0) / math.cos(t)
    parts = []

    # front plate: box in the spindle frame, then to world
    fp = box(476.0, 476.0 + B["front_plate"], -250.0, 250.0, tb - 40 * math.tan(t) - 2, 250.0)
    fp = fp.cut(cyl_x(470, 520, 100.0 + PRINT_CLEARANCE))
    fp = bolt_holes(fp, 12, 350.0, CLEAR["M20"], 470, 520)
    fp = bolt_holes(fp, 2, 290.0, 32.0, 470, 520, angles=G.SPINDLE["cable_holes"]["angles"])
    fp = to_world(fp).cut(box(-1000, 1000, -400, 400, -200, 40.0))   # trim to the bottom plate top
    parts.append(Part("NP1-300-1_bedplate_front_plate", "Bedplate front plate 40 (square to spindle)", fp,
                      "stationary", "NP1-300 / BOM 28", (0.3, 0.45, 0.3), axis=None,
                      print_mods=[f"Ø200 bore +{PRINT_CLEARANCE} mm radial"],
                      notes=["placed as drawn (front face at x = 476, 6 mm behind the spindle flange face)"]))

    bp = box(B["x_bottom"][0], B["x_bottom"][1], -B["width"] / 2, B["width"] / 2, 0, B["bottom_plate"])
    bp = bp.cut(cq.Solid.makeCylinder(B["yaw_bore"] / 2, 60, cq.Vector(0, 0, -10)))
    for k in range(16):
        a = math.radians(360.0 * k / 16 + 360.0 / 32)
        bp = bp.cut(cq.Solid.makeCylinder(CLEAR["M16"] / 2 + 0.5, 60,
                                          cq.Vector(150 * math.cos(a), 150 * math.sin(a), -10)))
    parts.append(Part("NP1-300-2_bedplate_bottom_plate", "Bedplate bottom plate 40 (yaw flange)", bp,
                      "stationary", "NP1-300 / BOM 28", (0.3, 0.45, 0.3), axis=None))

    front3 = _P(476 + B["front_plate"], tb - 40 * math.tan(t))
    side_pts = [_P(476 + B["front_plate"], 250), (330.0, 330.0), (330.0, 40.0), front3]
    for sgn, nm in ((1, "left"), (-1, "right")):
        y0, y1 = (240.0, 260.0) if sgn > 0 else (-260.0, -240.0)
        sp_ = _xz_prism(side_pts, y0, y1).cut(box(-1000, 1000, -400, 400, -200, 40.0))
        parts.append(Part(f"NP1-300-3_bedplate_side_plate_{nm}", f"Bedplate side plate 20 ({nm})", sp_,
                          "stationary", "NP1-300 / BOM 28", (0.3, 0.45, 0.3), axis=None))
    rp = box(310.0, 330.0, -240.0, 240.0, 40.0, 330.0)
    parts.append(Part("NP1-300-4_bedplate_rear_plate", "Bedplate rear plate 20", rp, "stationary",
                      "NP1-300 / BOM 28", (0.3, 0.45, 0.3), axis=None))
    return parts


def yaw_parts():
    Y = G.YAW
    # inner ring 10 mm shorter at the bottom so it clears the tower-top adapter
    # (outer ring mounting face) while the nacelle yaws
    inner = cq.Solid.makeCylinder(Y["inner"]["od"] / 2, Y["height"] - 10, cq.Vector(0, 0, -(Y["height"] - 10)))
    inner = inner.cut(cq.Solid.makeCylinder(Y["inner"]["id"] / 2 + PRINT_CLEARANCE, 100, cq.Vector(0, 0, -90)))
    for k in range(16):
        a = math.radians(360.0 * k / 16 + 360.0 / 32)
        inner = inner.cut(cq.Solid.makeCylinder(TAP["M16"] / 2, 40, cq.Vector(150 * math.cos(a), 150 * math.sin(a), -35)))
    # outer ring with the external gear z150 m4 (simple trapezoid teeth)
    m, z = Y["module"], Y["gear_z"]
    rp, ra, rf = m * z / 2, m * z / 2 + m, m * z / 2 - 1.25 * m
    pts = []
    for k in range(z):
        a0 = 2 * math.pi * k / z
        p = 2 * math.pi / z
        for frac, r in ((0.0, rf), (0.18, rf), (0.32, ra), (0.68, ra), (0.82, rf)):
            pts.append((r * math.cos(a0 + frac * p), r * math.sin(a0 + frac * p)))
    gear = cq.Workplane("XY", origin=(0, 0, -Y["height"])).polyline(pts).close().extrude(Y["height"] - 10).val()
    gear = gear.cut(cq.Solid.makeCylinder(Y["outer"]["id"] / 2, 100, cq.Vector(0, 0, -90)))
    for k in range(16):
        a = math.radians(360.0 * k / 16)
        gear = gear.cut(cq.Solid.makeCylinder(TAP["M16"] / 2, 100, cq.Vector(220 * math.cos(a), 220 * math.sin(a), -90)))
    note = ["preliminary doc 13 dimensions; the slewing ring supplier drawing replaces this"]
    return [Part("yaw_bearing_inner_ring_envelope", "Yaw bearing inner ring (to bedplate)", inner, "stationary",
                 "BOM 31 (bought)", (0.8, 0.65, 0.2), make_buy="buy (envelope)", axis="yaw", notes=note),
            Part("yaw_bearing_outer_gear_ring_envelope", "Yaw bearing outer ring, gear z150 m4 (to tower)", gear,
                 "tower", "BOM 31 (bought)", (0.8, 0.65, 0.2), make_buy="buy (envelope)", axis="yaw",
                 notes=note + ["16 holes on PCD 440 assumed"])]


def caliper_envelopes():
    """Space claim for the 2 spring-applied calipers (supplier not chosen).
    Generic industrial caliper for a 16 mm disc: 180 tangential x 130 radial x
    140 axial, inner edge 15 mm inside the pad track (r 330), at the two
    lateral positions."""
    out = []
    for sgn, nm in ((1, "left"), (-1, "right")):
        body = box(443.0 - 70, 443.0 + 70, -90, 90, 330.0, 460.0)
        slot = box(431.0, 455.0, -100, 100, 300, 405)
        body = body.cut(slot.translate(cq.Vector(0, 0, 0)))
        # rotate the radial (z) direction to the lateral side
        body = body.rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), -90 * sgn)
        out.append(Part(f"brake_caliper_{nm}_envelope", f"Brake caliper space claim ({nm})", to_world(body),
                        "stationary", "BOM 26 (bought), bracket NP1-310 not drawn", (0.85, 0.2, 0.2),
                        make_buy="buy (envelope)", axis=None,
                        notes=["generic envelope, replace with the chosen caliper's drawing"]))
    return out


# ===================================================== below the bedplate
# Everything from the bedplate down to the tower mounting point. New design
# (not in the P1 drawing set yet): proposed here, sized in doc 16 section 7.
TOWER = dict(
    tube_od=320.0, tube_t=8.0,                 # doc 09 tower top
    flange_od=420.0, flange_id=240.0, flange_t=30.0,
    bolts=dict(n=16, size="M20", pcd=380.0),   # adapter to tower, through bolts + nuts
)
ADAPTER = dict(
    plate_r=(150.0, 420.0), plate_z=(-95.0, -70.0),      # carries the yaw ring and the brake track
    track_r=(340.0, 420.0),                              # yaw brake friction track, both faces
    cone_r_top=(186.0, 198.0), cone_r_bot=(154.0, 166.0),   # inside the PCD 440 bolts so they go in from below
    flange_z=(-360.0, -330.0),
    gussets=dict(n=8, t=12.0, r=(198.0, 315.0), z_low=-200.0),
    ring_bolts=dict(n=16, size="M16", pcd=440.0),        # from below into the yaw outer ring
)
Z_TOWER_FLANGE_TOP = ADAPTER["flange_z"][0]              # tower mounting point


def revolve_z(poly):
    """Closed (r, z) polygon revolved about the yaw (Z) axis."""
    return cq.Workplane("XZ").polyline(poly).close().revolve(360, (0, 0, 0), (0, 1, 0)).val()


def zholes(solid, n, pcd, dia, z0, z1, start=0.0):
    for k in range(n):
        a = math.radians(start + 360.0 * k / n)
        solid = solid.cut(cq.Solid.makeCylinder(dia / 2, z1 - z0, cq.Vector(pcd / 2 * math.cos(a),
                                                                              pcd / 2 * math.sin(a), z0)))
    return solid


def tower_top_parts():
    A, T = ADAPTER, TOWER
    (p0, p1), (z0, z1) = A["plate_r"], A["plate_z"]
    fz0, fz1 = A["flange_z"]
    ad = revolve_z([(p0, z0), (p1, z0), (p1, z1), (p0, z1)])
    ad = ad.fuse(revolve_z([(A["cone_r_top"][0], z0 + 1), (A["cone_r_top"][1], z0 + 1),
                            (A["cone_r_bot"][1], fz1), (A["cone_r_bot"][0], fz1)]))
    ad = ad.fuse(revolve_z([(T["flange_id"] / 2, fz0), (T["flange_od"] / 2, fz0),
                            (T["flange_od"] / 2, fz1), (T["flange_id"] / 2, fz1)]))
    g = A["gussets"]
    tri = [(g["r"][0] - 4, z0 + 1), (g["r"][1], z0 + 1), (g["r"][0] - 4, g["z_low"])]
    for k in range(g["n"]):
        gs = cq.Workplane("XZ").polyline(tri).close().extrude(g["t"] / 2, both=True).val()
        ad = ad.fuse(gs.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), 360.0 * k / g["n"] + 11.25))
    ad = ad.clean()
    ad = zholes(ad, 16, A["ring_bolts"]["pcd"], CLEAR["M16"], z0 - 1, z1 + 1, start=0.0)
    ad = zholes(ad, T["bolts"]["n"], T["bolts"]["pcd"], CLEAR["M20"], fz0 - 1, fz1 + 1, start=11.25)
    # cable / access window in the cone (cable loop inspection)
    win = box(150, 240, -60, 60, -300, -215)
    ad = ad.cut(win)
    adapter = Part("NP1-400_tower_top_adapter", "Tower-top adapter with yaw brake track", ad, "tower",
                   "NP1-400 / BOM 34 (new design, doc 16 section 7)", (0.35, 0.4, 0.45), axis="yaw",
                   notes=["S355J2+N weldment: 25 mm plate Ø840 (yaw ring seat and brake track r 340 to 420), 12 mm cone Ø396 to Ø332, "
                          "30 mm tower flange, 8 gussets kept inside r 315 so the yaw calipers pass",
                          "16 x M16 10.9 up into the yaw outer ring on PCD 440; 16 x M20 10.9 through bolts to the tower on PCD 380",
                          "access window 90 x 85 in the cone for the cable loop"])
    # tower top flange and a 300 mm stub of the Ø320 x 8 tube = the tower mounting point
    tf = revolve_z([(T["flange_id"] / 2, fz0 - T["flange_t"]), (T["flange_od"] / 2, fz0 - T["flange_t"]),
                    (T["flange_od"] / 2, fz0), (T["flange_id"] / 2, fz0)])
    r_o = T["tube_od"] / 2
    tf = tf.fuse(revolve_z([(r_o - T["tube_t"], fz0 - T["flange_t"] - 300), (r_o, fz0 - T["flange_t"] - 300),
                            (r_o, fz0 - T["flange_t"] + 1), (r_o - T["tube_t"], fz0 - T["flange_t"] + 1)])).clean()
    tf = zholes(tf, T["bolts"]["n"], T["bolts"]["pcd"], CLEAR["M20"], fz0 - 40, fz0 + 1, start=11.25)
    stub = Part("tower_top_flange_stub", "Tower top flange + 300 mm of the Ø320 x 8 tube (mounting point)", tf,
                "tower", "doc 09 tower top, flange new (doc 16 section 7)", (0.55, 0.55, 0.5), axis="yaw",
                notes=["tower mounting point: top face of this flange, 360 mm below the bedplate underside",
                       "flange to be added to the doc 09 tower drawings"])
    return [adapter, stub]


def _gear_profile(z, m, phase=0.0):
    ra, rf = m * z / 2 + m, m * z / 2 - 1.25 * m
    pts = []
    p = 2 * math.pi / z
    for k in range(z):
        a0 = p * k + phase
        for frac, r in ((0.0, rf), (0.18, rf), (0.32, ra), (0.68, ra), (0.82, rf)):
            pts.append((r * math.cos(a0 + frac * p), r * math.sin(a0 + frac * p)))
    return pts


YAW_DRIVE = dict(r=328.0, angles=(90.0, -90.0), pinion_z=14, module=4.0, pinion_face=(-65.0, -15.0),
                 gearbox=dict(d=100.0, z=(25.0, 175.0)), motor=dict(d=110.0, z=(175.0, 335.0)))


def yaw_drive_parts():
    Y = YAW_DRIVE
    out = []
    for a in Y["angles"]:
        nm = "left" if a > 0 else "right"
        cx, cy = Y["r"] * math.cos(math.radians(a)), Y["r"] * math.sin(math.radians(a))
        # pinion turned half a tooth so it sits in a gear tooth space at the mesh point
        prof = _gear_profile(Y["pinion_z"], Y["module"], phase=math.radians(a + 180) + math.pi / 14)
        z0, z1 = Y["pinion_face"]
        pin = cq.Workplane("XY", origin=(0, 0, z0)).polyline(prof).close().extrude(z1 - z0).val()
        pin = pin.fuse(cq.Solid.makeCylinder(15.0, Y["gearbox"]["z"][0] - z1 + 1, cq.Vector(0, 0, z1 - 0.5)))
        pin = pin.fuse(cq.Solid.makeCylinder(Y["gearbox"]["d"] / 2, Y["gearbox"]["z"][1] - Y["gearbox"]["z"][0],
                                             cq.Vector(0, 0, Y["gearbox"]["z"][0])))
        pin = pin.fuse(cq.Solid.makeCylinder(Y["motor"]["d"] / 2, Y["motor"]["z"][1] - Y["motor"]["z"][0],
                                             cq.Vector(0, 0, Y["motor"]["z"][0]))).clean()
        out.append(Part(f"yaw_drive_{nm}_envelope", f"Yaw gearmotor 0.18 kW 1:1680 with z14 m4 pinion ({nm})",
                        pin.translate(cq.Vector(cx, cy, 0)), "stationary", "BOM 32 (bought)", (0.3, 0.3, 0.6),
                        make_buy="buy (envelope)", axis=None,
                        notes=["envelope: gearbox Ø100 x 150, motor Ø110 x 160, pinion face 50; replace with supplier drawing",
                               "centre distance 328 = (600 + 56) / 2 to the z150 gear"]))
        # bracket NP1-420: horizontal plate on the bedplate bottom level + web on the side plate
        s = 1 if a > 0 else -1
        hp = box(-90, 90, 260 if s > 0 else -400, 400 if s > 0 else -260, 0, 25)
        hp = hp.cut(cq.Solid.makeCylinder(17.0, 40, cq.Vector(cx, cy, -5)))
        for dx in (-40, 40):          # gearbox flange, 4 x M10
            for dy in (-40, 40):
                hp = hp.cut(cq.Solid.makeCylinder(TAP["M10"] / 2, 40, cq.Vector(cx + dx, cy + dy, -5)))
        web = box(-90, 90, 260 if s > 0 else -275, 275 if s > 0 else -260, 25, 170)
        for dx in (-50, 50):
            for zz in (70, 140):
                web = web.cut(cq.Solid.makeCylinder(CLEAR["M16"] / 2, 30, cq.Vector(dx, 250 if s > 0 else -280, zz),
                                                    cq.Vector(0, 1, 0)))
        out.append(Part(f"NP1-420_yaw_drive_bracket_{nm}", f"Yaw drive bracket ({nm})", hp.fuse(web).clean(),
                        "stationary", "NP1-420 (new, doc 16 section 7)", (0.3, 0.45, 0.3), axis=None,
                        notes=["bolts to the side plate outer face with 4 x M16; gearbox flange on top, pinion below"]))
    return out


YAW_BRAKE = dict(r_pad=(345.0, 415.0), angles=(141.8, -141.8))


def yaw_brake_parts():
    """Two yaw brake calipers with brackets, hanging from the bedplate bottom
    plate at its front corners and gripping the adapter plate edge from outside."""
    out = []
    z0, z1 = ADAPTER["plate_z"]
    for a in YAW_BRAKE["angles"]:
        nm = "left" if a > 0 else "right"
        body = box(330.0, 480.0, -75.0, 75.0, -150.0, 0.0)
        body = body.cut(box(290.0, 445.0, -80.0, 80.0, z0 - 3.0, z1 + 3.0))
        body = body.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), a)
        out.append(Part(f"yaw_brake_caliper_{nm}_envelope", f"Yaw brake caliper + bracket space claim ({nm})", body,
                        "stationary", "BOM 33 (bought), bracket new", (0.85, 0.2, 0.2), make_buy="buy (envelope)",
                        axis=None,
                        notes=["spring-applied, hydraulically released; grips the adapter plate edge (track r 345 to 415) "
                               "from outside; top face bolts under the bedplate bottom plate corner",
                               "envelope 150 x 150 x 150 incl. bracket, 3 mm running gap each side of the plate"]))
    return out


def rotor_caliper_brackets():
    """NP1-310 placeholder brackets: side plate outer face to the caliper space claim."""
    out = []
    for s, nm in ((1, "left"), (-1, "right")):
        b = box(-262.0, -150.0, 260.0 if s > 0 else -330.0, 330.0 if s > 0 else -260.0, 505.0, 635.0)
        for xx in (-195.0, -165.0):
            for zz in (535.0, 605.0):
                b = b.cut(cq.Solid.makeCylinder(CLEAR["M16"] / 2, 100, cq.Vector(xx, -50 if s > 0 else 50, zz),
                                                cq.Vector(0, s, 0)))
        out.append(Part(f"NP1-310_rotor_caliper_bracket_{nm}", f"Rotor brake caliper bracket ({nm}, placeholder)", b,
                        "stationary", "NP1-310 / BOM 29 (placeholder until caliper is chosen)", (0.3, 0.45, 0.3),
                        axis=None, notes=["block bracket 120 x 70 x 130 bolted to the side plate with 4 x M16"]))
    return out


if __name__ == "__main__":
    for p in build_parts():
        bb = p.solid.BoundingBox()
        print(f"{p.pid:45s} {bb.xlen:7.1f} {bb.ylen:7.1f} {bb.zlen:7.1f}  vol {p.solid.Volume() / 1e3:8.1f} cm3")
