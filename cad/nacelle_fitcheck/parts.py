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
    inner = cq.Solid.makeCylinder(Y["inner"]["od"] / 2, Y["height"], cq.Vector(0, 0, -Y["height"]))
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


if __name__ == "__main__":
    for p in build_parts():
        bb = p.solid.BoundingBox()
        print(f"{p.pid:45s} {bb.xlen:7.1f} {bb.ylen:7.1f} {bb.zlen:7.1f}  vol {p.solid.Volume() / 1e3:8.1f} cm3")
