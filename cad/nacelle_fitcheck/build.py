"""Export every nacelle P1 part as its own 1:1 object.

    python3 build.py            # parts + assembly + parts list
    python3 build.py --check    # also run assembly_check.py

out/step/<part>.step   one solid per file, in assembly position (WORLD frame)
out/stl/<part>.stl     same, triangulated for slicing (mm)
out/NP1-fitcheck-assembly.step   all parts as named, coloured objects
out/parts-list.md / .csv         size, volume and filament estimate per part
out/preview.png                  section-free iso preview
"""
from __future__ import annotations

import csv
import os
import sys

import cadquery as cq

import parts as PT

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

# Filament estimate: perimeters + 15 % gyroid gives roughly this solid fraction
# on parts of this size (wall-heavy parts more); PETG density.
FILL_FRACTION = 0.30
RHO_PETG = 1.27   # g/cm3


def main():
    os.makedirs(os.path.join(OUT, "step"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "stl"), exist_ok=True)
    parts = PT.build_parts()
    asm = cq.Assembly(name="NP1_fitcheck")
    rows = []
    for p in parts:
        stem = p.pid
        cq.exporters.export(cq.Workplane().add(p.solid), os.path.join(OUT, "step", stem + ".step"))
        cq.exporters.export(cq.Workplane().add(p.solid), os.path.join(OUT, "stl", stem + ".stl"),
                            tolerance=0.05, angularTolerance=0.1)
        asm.add(p.solid, name=stem, color=cq.Color(*p.color))
        bb = p.solid.BoundingBox()
        dims = sorted([bb.xlen, bb.ylen, bb.zlen], reverse=True)
        vol = p.solid.Volume() / 1000.0
        rows.append(dict(file=stem, name=p.name, group=p.group, make_buy=p.make_buy, source=p.source,
                         size_mm=" x ".join(f"{d:.0f}" for d in dims), volume_cm3=round(vol, 1),
                         filament_kg_est=round(vol * FILL_FRACTION * RHO_PETG / 1000.0, 2),
                         print_mods="; ".join(p.print_mods), notes="; ".join(p.notes)))
        print(f"{stem:45s} {rows[-1]['size_mm']:>18s}  {vol:8.0f} cm3")
    asm.save(os.path.join(OUT, "NP1-fitcheck-assembly.step"))

    with open(os.path.join(OUT, "parts-list.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    tot_v = sum(r["volume_cm3"] for r in rows)
    tot_f = sum(r["filament_kg_est"] for r in rows)
    L = ["# Nacelle P1 fit-check model: parts list (all 1:1)", "",
         f"{len(rows)} objects, solid volume {tot_v / 1000:.0f} L, filament ≈ {tot_f:.0f} kg PETG "
         f"at ~{FILL_FRACTION:.0%} solid fraction. Sizes are the part's bounding box, largest first.", "",
         "| File | Part | Moves | Make/buy | Size mm | Filament kg | Print changes vs steel part |",
         "|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| `{r['file']}` | {r['name']} | {r['group']} | {r['make_buy']} | {r['size_mm']} | "
                 f"{r['filament_kg_est']} | {r['print_mods'] or '–'} |")
    with open(os.path.join(OUT, "parts-list.md"), "w") as f:
        f.write("\n".join(L) + "\n")
    print(f"total {tot_v / 1000:.0f} L solid, ~{tot_f:.0f} kg filament")
    preview(parts)
    return parts


def preview(parts):
    """Section on the vertical mid-plane (Y = 0), one colour per part."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection

    slab = PT.box(-2000, 2000, -0.5, 0.5, -2000, 2000)
    fig, ax = plt.subplots(figsize=(14, 10))
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
    ax.set_xlim(-1300, 500)
    ax.set_ylim(-760, 1000)
    ax.set_aspect("equal")
    ax.grid(alpha=0.2)
    ax.set_xlabel("X rearward from the yaw axis, mm")
    ax.set_ylabel("Z up from the bedplate underside, mm")
    ax.set_title("Nacelle P1 fit-check model down to the tower flange, all parts 1:1, section on the vertical mid-plane")
    fig.savefig(os.path.join(OUT, "preview.png"), dpi=110, bbox_inches="tight")


if __name__ == "__main__":
    ps = main()
    if "--check" in sys.argv:
        import assembly_check
        assembly_check.main(ps)
