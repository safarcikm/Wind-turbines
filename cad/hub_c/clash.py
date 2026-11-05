"""Clash check of the doc 24 hub model over the pitch stroke.  python3 clash.py"""
import itertools, json, sys
import model as M
res = {}
for th in (-2.0, 10.0, 30.0, 45.0, 60.0, 80.0, 92.0):
    P = M.assembly(theta=th)
    hits = []
    for (na, sa, _), (nb, sb, _) in itertools.combinations(P, 2):
        # mating pairs that touch by design
        pair = {na.split('_')[0] + '_' + na.split('_')[-1], nb.split('_')[0] + '_' + nb.split('_')[-1]}
        key = tuple(sorted((na, nb)))
        same_blade = na.split('_')[-1] == nb.split('_')[-1]
        mate = (same_blade and {na.rsplit('_', 1)[0], nb.rsplit('_', 1)[0]} in (
            {"bearing_outer", "bearing_inner"}, {"bearing_inner", "blade_root"}, {"bearing_inner", "crank"},
            {"crank", "pin"}, {"pin", "eyes"}, {"link", "eyes"}, {"bearing_outer", "hub"}))
        if mate or {na, nb} in ({"yoke", "cylinder_rod"}, {"yoke", "guide_rods"}, {"cylinder", "nose_housing"},
                                 {"cylinder", "motor"}, {"guide_rods", "nose_housing"}, {"hub", "nose_housing"},
                                 {"hub", "drum"}, {"slip_ring", "drum"}):
            continue
        if (na.startswith("eyes") and nb == "yoke") or (nb.startswith("eyes") and na == "yoke") or (na.startswith("pin") and nb.startswith("eyes") and same_blade):
            continue
        if {na.rsplit('_',1)[0], nb} == {"bearing_outer", "hub"} or {nb.rsplit('_',1)[0], na} == {"bearing_outer", "hub"}:
            continue
        bb = sa.BoundingBox()
        if not bb.isInside(sb.BoundingBox()) and (bb.xmax < sb.BoundingBox().xmin or bb.xmin > sb.BoundingBox().xmax or
                                                   bb.ymax < sb.BoundingBox().ymin or bb.ymin > sb.BoundingBox().ymax or
                                                   bb.zmax < sb.BoundingBox().zmin or bb.zmin > sb.BoundingBox().zmax):
            continue
        v = sa.intersect(sb).Volume()
        if v > 1.0:
            hits.append((na, nb, round(v)))
    res[th] = hits
    print(th, hits, flush=True)
json.dump({str(k): v for k, v in res.items()}, open("out/clash.json", "w"), indent=1)
