"""Interference check of the assembled M8 turbine (all shown parts, pairwise, bbox prefilter) -> out/clash8.json."""
import json, itertools, sys
import model8
ps = [p for p in model8.build(tooling=False) if p.show]
bbs = {p.pid: p.solid.BoundingBox() for p in ps}
hits = []
for a, b in itertools.combinations(ps, 2):
    A, B = bbs[a.pid], bbs[b.pid]
    if A.xmax < B.xmin or B.xmax < A.xmin or A.ymax < B.ymin or B.ymax < A.ymin or A.zmax < B.zmin or B.zmax < A.zmin:
        continue
    try:
        v = a.solid.intersect(b.solid).Volume()
    except Exception as e:
        v = -1
    if v > 1000.0 or v < 0:
        hits.append((a.pid, b.pid, round(v / 1000.0, 1)))
        print(a.pid, b.pid, round(v / 1000.0, 1), "cm3", flush=True)
(model8.HERE / "out" / "clash8.json").write_text(json.dumps(hits, indent=1))
print("done", len(hits))
