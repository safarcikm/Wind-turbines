"""Digital fit check of the P1 nacelle, run on the same solids that get printed.

1. Static interference: every pair of parts in their assembled position
   (3-D boolean intersection, bounding-box prefilter).
2. Running clearance: smallest distance between every rotating part and every
   stationary part (rubbing risk).
3. Assembly path: each axisymmetric part is slid along the spindle axis from
   its installation side, in the doc 14 section 7.2 sequence, and its swept
   section is checked against the parts already installed (2-D, exact for
   revolved parts).

Writes out/assembly_check.md and out/assembly_check.json.
"""
from __future__ import annotations

import itertools
import json
import os

from shapely.geometry import Polygon
from shapely.ops import unary_union

import parts as PT
import geometry as G

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

# Contacts that are meant to be there (fits, seats, bolted faces): reported
# only if they overlap by more than the print clearance would explain.
DESIGNED_CONTACT_TOL = 5.0      # mm^3
RUNNING_LIMIT = 3.0             # mm, report rotating/stationary gaps below this


# ------------------------------------------------------------------ 3-D checks
def static_interference(parts):
    res = []
    bbs = {p.pid: p.solid.BoundingBox() for p in parts}
    for a, b in itertools.combinations(parts, 2):
        ba, bb = bbs[a.pid], bbs[b.pid]
        if (ba.xmax < bb.xmin or bb.xmax < ba.xmin or ba.ymax < bb.ymin or bb.ymax < ba.ymin
                or ba.zmax < bb.zmin or bb.zmax < ba.zmin):
            continue
        try:
            v = a.solid.intersect(b.solid).Volume()
        except Exception as e:      # noqa: BLE001
            res.append(dict(a=a.pid, b=b.pid, volume_mm3=None, error=str(e)))
            continue
        print(f"  {a.pid} x {b.pid}: {v:.1f}", flush=True)
        if v > DESIGNED_CONTACT_TOL:
            res.append(dict(a=a.pid, b=b.pid, volume_mm3=round(v, 1)))
    return res


ROTATING_2D = ["NP1-210_rotor_drum", "32028X_front_cup_envelope", "32028X_rear_cup_envelope",
               "NP1-211_front_seal_cover", "NP1-211_rear_seal_cover", "NP1-212_drum_rear_cover",
               "NP1-220_magnet_ring", "NP1-230_brake_disc"]
STATIONARY_2D = ["NP1-100_spindle", "NP1-101_front_spacer", "KMT27_locknut_envelope", "32028X_front_cone_envelope",
                 "32028X_rear_cone_envelope", "NP1-200_stator_carrier", "NP1-201_stator_core",
                 "NP1-202_stator_clamp_ring", "stator_end_winding_front_envelope",
                 "stator_end_winding_rear_envelope", "NP1-300-1_bedplate_front_plate"]


def running_clearance(sec):
    """Smallest gap between rotating and stationary parts, on the revolved
    sections (exact for revolved parts; the bedplate front plate is taken as
    the annulus r 100 to 250 it covers on every radius line)."""
    res = []
    for r in ROTATING_2D:
        for s in STATIONARY_2D:
            d = sec[r].distance(sec[s])
            if d < RUNNING_LIMIT:
                res.append(dict(rotating=r, stationary=s, min_gap_mm=round(d, 2)))
    return sorted(res, key=lambda x: x["min_gap_mm"])


# ------------------------------------------------------------- 2-D assembly path
def poly(p):
    return Polygon(p).buffer(0)


def drum_section():
    return unary_union([poly(p) for p in G.DRUM_PARTS.values()])


def sweep(pg, direction, length=2000.0):
    """Region swept by section pg moving along x into place.
    direction 'front': it arrives from the rotor side (moves +x);
    'rear': it arrives from behind (moves -x)."""
    dx = -length if direction == "front" else length
    from shapely.affinity import translate
    pieces = [pg, translate(pg, dx, 0)]
    geoms = list(pg.geoms) if hasattr(pg, "geoms") else [pg]
    for g in geoms:
        for ring in [g.exterior] + list(g.interiors):
            coords = list(ring.coords)
            for (x0, y0), (x1, y1) in zip(coords[:-1], coords[1:]):
                pieces.append(Polygon([(x0, y0), (x1, y1), (x1 + dx, y1), (x0 + dx, y0)]).buffer(0))
    return unary_union(pieces)


def section_dict():
    S = PT.sections()
    sec = {k: poly(v) for k, v in S.items() if v is not None}
    sec["NP1-210_rotor_drum"] = drum_section()
    sec["NP1-212_drum_rear_cover"] = unary_union([poly(G.REAR_COVER), poly(G.REAR_SEAL_CARRIER)])
    sec["NP1-300-1_bedplate_front_plate"] = poly([(476, 100), (516, 100), (516, 250), (476, 250)])
    sec["NP1-600_dummy_hub (as drawn)"] = unary_union([poly(p) for p in PT.DUMMY_HUB_AS_DRAWN.values()])
    sec["NP1-600_dummy_hub (corrected)"] = unary_union(
        [poly(PT.DUMMY_HUB_FIXED_FLANGE), poly(PT.DUMMY_HUB_AS_DRAWN["bell"]), poly(PT.DUMMY_HUB_AS_DRAWN["front"])])
    return sec


def assembly_path(sec):

    def moving(names):
        return unary_union([sec[n] for n in names])

    # doc 14 section 7.2, sub-assemblies first
    steps = [
        ("1 stator", "stack onto carrier", ["NP1-201_stator_core"], "front", ["NP1-200_stator_carrier"]),
        ("1 stator", "clamp ring", ["NP1-202_stator_clamp_ring"], "front", ["NP1-200_stator_carrier", "NP1-201_stator_core"]),
        ("2 rotor", "front cup into drum", ["32028X_front_cup_envelope"], "front", ["NP1-210_rotor_drum"]),
        ("2 rotor", "rear cup into drum", ["32028X_rear_cup_envelope"], "rear", ["NP1-210_rotor_drum"]),
        ("2 rotor", "brake disc onto drum (from the front)", ["NP1-230_brake_disc"], "front", ["NP1-210_rotor_drum"]),
        ("2 rotor", "brake disc onto drum (from the rear)", ["NP1-230_brake_disc"], "rear", ["NP1-210_rotor_drum"]),
        ("2 rotor", "rear seal cover into drum", ["NP1-211_rear_seal_cover"], "rear", ["NP1-210_rotor_drum"]),
        ("3 spindle", "rear cone onto spindle", ["32028X_rear_cone_envelope"], "front", ["NP1-100_spindle"]),
        ("4 stator on spindle", "stator assembly over the fitted rear cone",
         ["NP1-200_stator_carrier", "NP1-201_stator_core", "NP1-202_stator_clamp_ring",
          "stator_end_winding_front_envelope", "stator_end_winding_rear_envelope"], "front",
         ["NP1-100_spindle", "32028X_rear_cone_envelope"]),
        ("4 alt", "stator assembly BEFORE the rear cone", ["NP1-200_stator_carrier", "NP1-201_stator_core",
                                                           "NP1-202_stator_clamp_ring"], "front", ["NP1-100_spindle"]),
        ("4 alt", "rear cone after the stator", ["32028X_rear_cone_envelope"], "front",
         ["NP1-100_spindle", "NP1-200_stator_carrier"]),
        ("5 drum on spindle", "drum with cups, magnets and rear seal cover",
         ["NP1-210_rotor_drum", "32028X_front_cup_envelope", "32028X_rear_cup_envelope", "NP1-220_magnet_ring",
          "NP1-211_rear_seal_cover"], "front",
         ["NP1-100_spindle", "32028X_rear_cone_envelope", "NP1-200_stator_carrier", "NP1-201_stator_core",
          "NP1-202_stator_clamp_ring", "stator_end_winding_front_envelope", "stator_end_winding_rear_envelope"]),
        ("5 alt", "drum without the rear seal cover", ["NP1-210_rotor_drum", "32028X_front_cup_envelope",
                                                       "32028X_rear_cup_envelope", "NP1-220_magnet_ring"], "front",
         ["NP1-100_spindle", "32028X_rear_cone_envelope", "NP1-200_stator_carrier", "NP1-201_stator_core",
          "NP1-202_stator_clamp_ring", "stator_end_winding_front_envelope", "stator_end_winding_rear_envelope"]),
        ("6 front bearing", "front cone, spacer, locknut", ["32028X_front_cone_envelope"], "front", ["NP1-100_spindle"]),
        ("6 front bearing", "front seal cover", ["NP1-211_front_seal_cover"], "front",
         ["NP1-100_spindle", "NP1-101_front_spacer", "KMT27_locknut_envelope", "32028X_front_cone_envelope"]),
        ("7 rear cover", "rear cover over the spindle flange", ["NP1-212_drum_rear_cover"], "rear",
         ["NP1-100_spindle", "NP1-200_stator_carrier"]),
        ("8 bedplate", "front plate onto the spigot", ["NP1-300-1_bedplate_front_plate"], "rear", ["NP1-100_spindle"]),
        ("9 bench", "dummy hub onto drum (as drawn)", ["NP1-600_dummy_hub (as drawn)"], "front", ["NP1-210_rotor_drum"]),
        ("9 bench", "dummy hub onto drum (corrected recess)", ["NP1-600_dummy_hub (corrected)"], "front",
         ["NP1-210_rotor_drum", "NP1-100_spindle", "NP1-211_front_seal_cover", "KMT27_locknut_envelope"]),
    ]
    out = []
    for stage, what, mov, d, fixed in steps:
        sw = sweep(moving(mov), d)
        hit = []
        for f in fixed:
            a = sw.intersection(sec[f]).area
            if a > 1.0:
                b = sw.intersection(sec[f]).bounds
                hit.append(dict(part=f, overlap_mm2=round(a, 1),
                                x=(round(b[0], 1), round(b[2], 1)), r=(round(b[1], 1), round(b[3], 1))))
        out.append(dict(stage=stage, step=what, from_side=d, ok=not hit, blocked_by=hit))

    # static section overlaps that are not assembly-path related
    static = []
    names = list(sec)
    for a, b in itertools.combinations(names, 2):
        if "dummy_hub" in a and "dummy_hub" in b:
            continue
        ar = sec[a].intersection(sec[b]).area
        if ar > 1.0:
            bb = sec[a].intersection(sec[b]).bounds
            static.append(dict(a=a, b=b, overlap_mm2=round(ar, 1),
                               x=(round(bb[0], 1), round(bb[2], 1)), r=(round(bb[1], 1), round(bb[3], 1))))
    return out, static


def main(parts=None):
    os.makedirs(OUT, exist_ok=True)
    parts = parts or PT.build_parts()
    print("static 3-D interference ...")
    si = static_interference(parts)
    sec = section_dict()
    print("running clearances ...")
    rc = running_clearance(sec)
    print("assembly paths ...")
    ap, st2 = assembly_path(sec)
    res = dict(static_3d=si, running_clearance=rc, assembly_path=ap, static_section=st2,
               limits=dict(designed_contact_mm3=DESIGNED_CONTACT_TOL, running_gap_mm=RUNNING_LIMIT))
    with open(os.path.join(OUT, "assembly_check.json"), "w") as f:
        json.dump(res, f, indent=1)

    L = ["# Nacelle P1 digital fit check", "",
         "Generated by `assembly_check.py` from the same 1:1 solids that are printed. "
         "Bearing, caliper and yaw-bearing envelopes are estimates until supplier drawings arrive.", "",
         "## 1. Static interference in the assembled position (3-D)", "",
         f"Pairs whose solids overlap by more than {DESIGNED_CONTACT_TOL} mm³:", "",
         "| Part A | Part B | Overlap mm³ |", "|---|---|---|"]
    L += [f"| {r['a']} | {r['b']} | {r['volume_mm3']} |" for r in si] or ["| none | | |"]
    L += ["", "## 2. Running clearance, rotating vs stationary (revolved sections)", "",
          f"Gaps below {RUNNING_LIMIT} mm (the air gap is 2.5 mm to the magnet face by design):", "",
          "| Rotating | Stationary | Min gap mm |", "|---|---|---|"]
    L += [f"| {r['rotating']} | {r['stationary']} | {r['min_gap_mm']} |" for r in rc] or ["| none | | |"]
    L += ["", "## 3. Assembly path along the spindle axis (doc 14 §7.2 order)", "",
          "| Stage | Step | Arrives from | Result | Blocked by (x range, r range, overlap mm²) |", "|---|---|---|---|---|"]
    for r in ap:
        b = "; ".join(f"{h['part']} (x {h['x'][0]}–{h['x'][1]}, r {h['r'][0]}–{h['r'][1]}, {h['overlap_mm2']})"
                      for h in r["blocked_by"])
        L.append(f"| {r['stage']} | {r['step']} | {r['from_side']} | {'OK' if r['ok'] else '**BLOCKED**'} | {b} |")
    L += ["", "## 4. Section overlaps in the assembled position (2-D, revolved parts)", "",
          "| Part A | Part B | x range | r range | mm² |", "|---|---|---|---|---|"]
    L += [f"| {r['a']} | {r['b']} | {r['x'][0]}–{r['x'][1]} | {r['r'][0]}–{r['r'][1]} | {r['overlap_mm2']} |"
          for r in st2] or ["| none | | | | |"]
    with open(os.path.join(OUT, "assembly_check.md"), "w") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))
    return res


if __name__ == "__main__":
    main()
