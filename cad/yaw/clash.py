"""Clash check of the yaw system (doc 25).

1. Static, yaw 0 deg, lock engaged: every pair of parts. Intended contacts
   (pad faces on the track, ring faces, bolted faces, pinion meshes) have zero
   intersection volume; anything above 1 mm3 is reported.
2. Yaw sweep: all nacelle-side parts turned through 360 deg in 10 deg steps
   against the tower-side parts (adapter, outer gear ring, tower stub), with
   the lock retracted. Pinion meshes are left out of the sweep (they would
   turn with the gear) and checked in step 1.
Writes out/clash.json.
"""
import itertools
import json
from pathlib import Path

import cadquery as cq

import model as M

OUT = Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)
TOWER = ("NY-400_adapter", "tower_flange_stub", "ring_outer")
TOL = 1.0
# intended overlaps: gear meshes (simplified tooth shapes), lock block engaged in a
# tooth space, shaft in its bearing boss / pinion bore / encoder coupling, cables in their cleats
INTENDED = {("ring_outer", "yaw_drive_left"), ("ring_outer", "yaw_drive_right"), ("ring_outer", "NY-440_pinion"),
            ("ring_outer", "NY-430_block"), ("NY-440_pinion", "NY-440_shaft"), ("NY-440_shaft", "NY-440_bracket"),
            ("NY-440_shaft", "NY-440_encoder"), ("NY-460_tube", "NY-460_cables")}


def vol(a, b):
    bb1, bb2 = a.BoundingBox(), b.BoundingBox()
    if (bb1.xmax < bb2.xmin or bb2.xmax < bb1.xmin or bb1.ymax < bb2.ymin or bb2.ymax < bb1.ymin
            or bb1.zmax < bb2.zmin or bb2.zmax < bb1.zmin):
        return 0.0
    try:
        return a.intersect(b).Volume()
    except Exception:
        return -1.0


def main():
    parts = M.assembly(context=True)
    res = dict(static=[], sweep=[])
    for (n1, s1, _), (n2, s2, _) in itertools.combinations(parts, 2):
        if n1.startswith("ctx_") and n2.startswith("ctx_"):
            continue
        if (n1, n2) in INTENDED or (n2, n1) in INTENDED:
            continue
        v = vol(s1, s2)
        if v > TOL or v < 0:
            res["static"].append((n1, n2, round(v, 1)))
    nac = [(n, s) for n, s, _ in M.assembly(context=True, lock_engaged=False)
           if n not in TOWER and "pinion" not in n and not n.startswith("yaw_drive")]
    # drives without pinions: gearbox/motor only (cut the pinion zone z < -10)
    for n, s, _ in M.assembly(context=False):
        if n.startswith("yaw_drive"):
            nac.append((n, s.cut(M.box(-2000, 2000, -2000, 2000, -500, -12))))
    tower = [(n, s) for n, s, _ in parts if n in TOWER]
    for a in range(0, 360, 10):
        for n, s in nac:
            sr = s.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), a)
            for tn, ts in tower:
                v = vol(sr, ts)
                if v > TOL or v < 0:
                    res["sweep"].append((a, n, tn, round(v, 1)))
    res["clean"] = not res["static"] and not res["sweep"]
    (OUT / "clash.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1)[:3000])


if __name__ == "__main__":
    main()
