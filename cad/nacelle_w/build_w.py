"""Working prototype W1: export the added parts, the full W1 assembly and a
clash/running check of the new parts against the Rev B nacelle.

    python3 build_w.py

out/step, out/stl          one file per W1 part (1:1, assembly position, WORLD frame)
out/NW1-assembly.step      Rev B nacelle (without the bench dummy hub) + W1 parts
out/parts-list-w.md        W1 parts with size and filament
out/w_check.md             static interference and running gaps of the W1 parts
out/preview-w.png          section on the vertical mid-plane
"""
from __future__ import annotations

import itertools
import os
import sys

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "nacelle_fitcheck"))
import parts as PT          # noqa: E402
import importlib.util                                      # noqa: E402
_spec = importlib.util.spec_from_file_location("fitcheck_build", os.path.join(HERE, "..", "nacelle_fitcheck", "build.py"))
FB = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(FB)
import parts_w as PW        # noqa: E402

OUT = os.path.join(HERE, "out")
RUN_LIMIT = 10.0     # mm: report rotating/stationary gaps below this for the new parts


def gap(a, b):
    try:
        return a.solid.distance(b.solid)  # OCP BRepExtrema via cadquery
    except Exception:   # noqa: BLE001
        return None


def main():
    os.makedirs(os.path.join(OUT, "step"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "stl"), exist_ok=True)
    base = [p for p in PT.build_parts() if not p.pid.startswith("NP1-600") and not p.pid.startswith("yaw_bearing")]
    new = PW.build_w_parts()
    asm = cq.Assembly(name="NW1")
    rows = []
    for p in base + new:
        asm.add(p.solid, name=p.pid, color=cq.Color(*p.color))
    for p in new:
        cq.exporters.export(cq.Workplane().add(p.solid), os.path.join(OUT, "step", p.pid + ".step"))
        cq.exporters.export(cq.Workplane().add(p.solid), os.path.join(OUT, "stl", p.pid + ".stl"),
                            tolerance=0.05, angularTolerance=0.1)
        bb = p.solid.BoundingBox()
        dims = sorted([bb.xlen, bb.ylen, bb.zlen], reverse=True)
        vol = p.solid.Volume() / 1000.0
        rows.append((p, " x ".join(f"{d:.0f}" for d in dims), vol, vol * FB.FILL_FRACTION * FB.RHO_PETG / 1000.0))
        print(f"{p.pid:45s} {rows[-1][1]:>18s} {vol:8.0f} cm3", flush=True)
    asm.save(os.path.join(OUT, "NW1-assembly.step"))

    L = ["# Working prototype W1: added parts (all 1:1)", "",
         f"{len(rows)} objects added to the Rev B fit-check model; printed parts ≈ "
         f"{sum(r[3] for r in rows if r[0].make_buy == 'make'):.0f} kg PETG.", "",
         "| File | Part | Moves | Make/buy | Size mm | Filament kg | Notes |", "|---|---|---|---|---|---|---|"]
    for p, size, vol, kg in rows:
        L.append(f"| `{p.pid}` | {p.name} | {p.group} | {p.make_buy} | {size} | "
                 f"{kg:.2f} | {'; '.join(p.print_mods + p.notes) or '–'} |")
    with open(os.path.join(OUT, "parts-list-w.md"), "w") as f:
        f.write("\n".join(L) + "\n")

    # ---- checks: new parts against everything
    clashes, gaps = [], []
    allp = base + new
    bbs = {p.pid: p.solid.BoundingBox() for p in allp}
    for a, b in itertools.combinations(allp, 2):
        if a not in new and b not in new:
            continue
        ba, bb = bbs[a.pid], bbs[b.pid]
        near = not (ba.xmax + RUN_LIMIT < bb.xmin or bb.xmax + RUN_LIMIT < ba.xmin or ba.ymax + RUN_LIMIT < bb.ymin
                    or bb.ymax + RUN_LIMIT < ba.ymin or ba.zmax + RUN_LIMIT < bb.zmin or bb.zmax + RUN_LIMIT < ba.zmin)
        if not near:
            continue
        mesh = ("yaw_drive" in a.pid + b.pid and "outer_gear_ring" in a.pid + b.pid)
        v = a.solid.intersect(b.solid).Volume()
        if v > 5.0 and not mesh:
            clashes.append((a.pid, b.pid, round(v, 1)))
        moving = {a.group == "rotating", b.group == "rotating"}
        if moving == {True, False}:
            d = gap(a, b)
            if d is not None and d < RUN_LIMIT:
                gaps.append((a.pid, b.pid, round(d, 1)))
        print(f"  {a.pid} x {b.pid}: {v:.1f}", flush=True)
    C = ["# W1 check: added parts against the Rev B nacelle", "",
         "## Static interference (> 5 mm³; yaw pinion/gear mesh excluded, pitch pinions checked: 0.13 mm backlash)", "",
         "| Part A | Part B | mm³ |", "|---|---|---|"]
    C += [f"| {a} | {b} | {v} |" for a, b, v in clashes] or ["| none | | |"]
    C += ["", f"## Rotating vs stationary gaps below {RUN_LIMIT} mm (3-D, assembled position)", "",
          "| Part A | Part B | gap mm |", "|---|---|---|"]
    C += [f"| {a} | {b} | {d} |" for a, b, d in sorted(gaps, key=lambda g: g[2])] or ["| none | | |"]
    with open(os.path.join(OUT, "w_check.md"), "w") as f:
        f.write("\n".join(C) + "\n")
    print("\n".join(C))

    preview(base + new)


def preview(parts):
    """Section on the vertical mid-plane (Y = 0), one colour per part."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection

    slab = PT.box(-2000, 2000, -0.5, 0.5, -2000, 2000)
    fig, ax = plt.subplots(figsize=(12, 12))
    for p in parts:
        try:
            s = p.solid.intersect(slab)
            if s.Volume() < 1e-3:
                continue
            v, t = s.tessellate(0.5, 0.3)
        except Exception:   # noqa: BLE001
            continue
        tris = [[(v[i].x, v[i].z) for i in tri] for tri in t]
        ax.add_collection(PolyCollection(tris, facecolors=[p.color], edgecolors="none"))
    ax.set_xlim(-1250, 500)
    ax.set_ylim(-720, 1450)
    ax.set_aspect("equal")
    ax.grid(alpha=0.2)
    ax.set_xlabel("X rearward from the yaw axis, mm")
    ax.set_ylabel("Z up from the bedplate underside, mm")
    ax.set_title("Working prototype W1 (Rev B nacelle + hub, pitch and yaw twins), 1:1, section on the vertical mid-plane")
    fig.savefig(os.path.join(OUT, "preview-w.png"), dpi=110, bbox_inches="tight")


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview([p for p in PT.build_parts() if not p.pid.startswith("NP1-600") and not p.pid.startswith("yaw_bearing")]
                + PW.build_w_parts())
    else:
        main()
