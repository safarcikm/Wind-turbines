"""Axonometric (isometric-style) views for the S6 build book (doc 34).

    python3 iso6.py [parts|assy|steps|all]     -> out/iso/parts/<pid>.png, out/iso/A*.png, out/iso/steps/S*.png

Every part of model6.build() is rendered alone; the assembly views and the assembly-sequence steps are
rendered from the same solids (numpy z-buffer renderer, render.py).
"""
from __future__ import annotations

import json
import math
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import model6 as M  # noqa: E402
import render as R  # noqa: E402

OUT = HERE / "out" / "iso"
PARTS = None

# ------------------------------------------------------------------ assembly sequence (doc 34 §6)
STEPS = [
    (1, "Bedplate on the stand; yaw slewing ring, gearmotors and their brackets", ["NS6-300", "NS6-911-I", "NS6-911-O", "NS6-912-L", "NS6-912-R", "NP1-420-L", "NP1-420-R"]),
    (2, "Spindle with front spacer and rear seal sleeve bolted to the bedplate front plate", ["NP1-100", "NP1-101", "NP1-102"]),
    (3, "Stator: carrier, wound tooth segments, clamp ring; bearing cones on the spindle", ["NP1-200C", "NP1-201C", "NP1-203C", "NP1-202", "NS6-913-F", "NS6-913-R"]),
    (4, "Rotor drum with magnets lowered over the stator on the guide tool; disc, seal covers, rear cover", ["NP1-210C", "NP1-220E", "NP1-230", "NP1-211-F", "NP1-211-R", "NS6-610"]),
    (5, "Brake caliper on its bracket, lock pin holder with overspeed sensors", ["NP1-310", "NS6-915", "NP1-320", "NP1-321", "NS6-914"]),
    (6, "Yaw pad units, lock, encoder and cable hanger; cover frame, lower cover tray and junction box", ["NY-410-L", "NY-410-R", "NY-430", "NY-440", "NY-460", "NS6-710", "NS6-700-1", "NS6-730"]),
    (7, "Tower-top adapter on the yaw outer ring (nacelle now complete for transport)", ["NY-400"]),
    (8, "Fixed hub on the drum flange (12 × M16 10.9)", ["NS6-200"]),
    (9, "Blades with pitch washer plates, set to −2.0° with the pitch gauge", ["NS6-100-1", "NS6-100-2", "NS6-100-3", "NS6-130", "NS6-105"]),
    (10, "Spinner and its brackets", ["NS6-210", "NS6-211"]),
    (11, "Upper cover lid and met mast", ["NS6-700-2", "NS6-720"]),
    (12, "On site: footing with anchor cage, hinge brackets, tower lying on the hinge; head bolted to the tower top", ["NS6-500", "NS6-510", "NS6-410", "NS6-400"]),
    (13, "Tilt-up with the gin pole and winch, base nuts torqued; cabinet, resistor box, cabling, hand-hole cover", ["NS6-420", "NS6-620", "NS6-600", "NS6-800", "NS6-401"]),
]
NACELLE_GROUPS = ("nacelle", "yaw", "drivetrain", "rotor", "electrical")


def parts():
    global PARTS
    if PARTS is None:
        PARTS = M.build()
    return PARTS


def tol_for(solid):
    bb = solid.BoundingBox()
    L = max(bb.xlen, bb.ylen, bb.zlen)
    return max(0.25, L / 500.0)


def lighten(hexcol, f):
    c = R.hex2rgb(hexcol)
    c = c + (1 - c) * f
    return "#" + "".join(f"{int(round(v * 255)):02x}" for v in c)


def save(img, path, crop=True):
    if crop:
        m = np.any(img < 0.985, axis=2)
        ys, xs = np.nonzero(m)
        if len(xs):
            pad = 20
            img = img[max(ys.min() - pad, 0):ys.max() + pad, max(xs.min() - pad, 0):xs.max() + pad]
    plt.imsave(path, img)


def view_for(p):
    if p.group == "tooling" and p.pid.startswith("NS6-110"):
        return -60.0, 30.0
    if p.pid.startswith("NS6-100") or p.pid in ("NS6-105",):
        return -150.0, 18.0
    return -130.0, 25.0


def render_part(i):
    p = parts()[i]
    az, el = view_for(p)
    r = R.Renderer(az=az, el=el)
    r.add(p.solid, p.color, tol=tol_for(p.solid))
    img = r.render(1100, 820, margin=30)
    save(img, OUT / "parts" / f"{p.pid}.png")
    return p.pid


def render_set(items, path, W=1600, H=1200, az=-130.0, el=25.0, tol=None, ghost=None):
    r = R.Renderer(az=az, el=el)
    for p, col in items:
        r.add(p.solid, col, tol=tol or max(1.0, tol_for(p.solid)))
    img = r.render(W, H, margin=30)
    save(img, path)


def assy():
    ps = parts()
    show = [p for p in ps if p.show]
    head = [p for p in show if p.group in NACELLE_GROUPS and p.pid not in ("NS6-620", "NS6-600", "NS6-800")]
    jobs = []
    # A01 complete turbine with footing
    jobs.append(("A01-turbine", [(p, p.color) for p in show], 1300, 1700, -130.0, 18.0, 6.0))
    # A02 head assembled
    jobs.append(("A02-head", [(p, p.color) for p in head], 1600, 1200, -130.0, 22.0, 2.0))
    # A03 nacelle with the cover lid removed, from the rear-left above
    jobs.append(("A03-nacelle-open", [(p, p.color) for p in head if p.pid not in ("NS6-700-2", "NS6-720", "NS6-105") and not p.pid.startswith("NS6-100")],
                 1600, 1200, -40.0, 30.0, 1.2))
    # A04 rotor (hub, blades, spinner)
    rot = [p for p in show if p.group == "rotor"]
    jobs.append(("A04-rotor", [(p, p.color) for p in rot], 1500, 1300, -150.0, 15.0, 2.0))
    # A05 tower base (hinge, footing, cabinet)
    base = [p for p in ps if p.group in ("foundation",) or p.pid in ("NS6-410", "NS6-620", "NS6-600", "NS6-800", "NS6-401")]
    tw = [p for p in ps if p.pid == "NS6-400"]
    jobs.append(("A05-tower-base", [(p, p.color) for p in base + tw], 1500, 1300, -130.0, 25.0, 4.0))
    # A07 blade mould set (open), A08 exploded nacelle-side drivetrain
    mo = [p for p in ps if p.pid in ("NS6-110-1", "NS6-110-2", "NS6-110-3")]
    jobs.append(("A07-mould", [(p, p.color) for p in mo], 1600, 1000, -60.0, 30.0, 3.0))
    return jobs


def run_job(j):
    name, items, W, H, az, el, tol = j
    if name == "A05-tower-base":
        # clip the tower to the lower 2 m for a readable view
        import cadquery as cq
        z_cut = M.Z_BASE + 2000.0
        new = []
        for p, c in items:
            s = p.solid
            if p.pid in ("NS6-400", "NS6-800"):
                s = s.cut(M.box(-2000, 2000, -2000, 2000, z_cut, 0))
            new.append((type("P", (), dict(solid=s))(), c))
        items = new
    render_set(items, OUT / f"{name}.png", W, H, az, el, tol)
    return name


def extras():
    """Single-item views: one root insert, pitch washer + gauge, blade alone (local frame, lying)."""
    import cadquery as cq
    r = R.Renderer(az=-130.0, el=25.0)
    r.add(M.insert_solid(), "#9aa3ab", tol=0.1)
    save(r.render(1000, 700, margin=30), OUT / "X-insert.png")
    w, g = M.pitch_parts()
    r = R.Renderer(az=-130.0, el=35.0)
    one = M.cyl(14.0, 4.0, (0, 0, 0)).cut(M.cyl(6.5, 10, (0, 0, -3)))
    r.add(one.translate(cq.Vector(0, -120, 1995)), "#c8c8c8", tol=0.2)
    r.add(g, "#c47d2a", tol=0.5)
    save(r.render(1100, 700, margin=30), OUT / "X-pitch.png")
    b = M.blade_solid().rotate(cq.Vector(0, 0, 0), cq.Vector(0, 1, 0), 90.0)
    r = R.Renderer(az=-110.0, el=30.0)
    r.add(b, "#e9e6dc", tol=1.0)
    save(r.render(1600, 700, margin=30), OUT / "X-blade.png")


def tilt_up_view():
    """A06: tower lying on the hinge, head on, gin pole up, before erection (sketch of the rigging)."""
    import cadquery as cq
    ps = parts()
    pick = [p for p in ps if p.show and (p.group in NACELLE_GROUPS or p.pid in ("NS6-400",)) and p.pid not in ("NS6-620", "NS6-600", "NS6-800")]
    hx, hz = M.HINGE["x"], M.Z_BASE + 40.0
    r = R.Renderer(az=-60.0, el=22.0)
    for p in pick:
        s = p.solid.rotate(cq.Vector(hx, 0, hz), cq.Vector(hx, 1, hz), -90.0)
        r.add(s, p.color, tol=6.0)
    for p in ps:
        if p.pid in ("NS6-410", "NS6-500", "NS6-510"):
            r.add(p.solid, p.color, tol=6.0)
        if p.pid == "NS6-420":
            s = p.solid.rotate(cq.Vector(hx, 0, hz), cq.Vector(hx, 1, hz), -90.0)
            r.add(s, p.color, tol=4.0)
    img = r.render(1800, 900, margin=30)
    save(img, OUT / "A06-tilt-up.png")


def steps():
    ps = parts()
    by = {p.pid: p for p in ps}
    done = []
    jobs = []
    for n, title, pids in STEPS:
        new = [by[k] for k in pids if k in by]
        missing = [k for k in pids if k not in by]
        if missing:
            print("step", n, "missing", missing)
        site = n >= 12
        items = []
        for p in done:
            if not site and p.group in ("tower", "foundation"):
                continue
            items.append((p, lighten(p.color, 0.62)))
        items += [(p, p.color) for p in new]
        done += new
        jobs.append((n, items, site))
    return jobs


def run_step(j):
    n, items, site = j
    if site:
        render_set(items, OUT / "steps" / f"S{n:02d}.png", 1200, 1400, -130.0, 20.0, 6.0)
    else:
        render_set(items, OUT / "steps" / f"S{n:02d}.png", 1400, 1100, -130.0, 25.0, 2.0)
    return n


def main(what="all"):
    for d in ("parts", "steps"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    ps = parts()
    if what in ("parts", "all"):
        with Pool(4) as pool:                       # index only: no solids are pickled
            for pid in pool.imap_unordered(render_part, range(len(ps))):
                print("part", pid, flush=True)
    if what in ("assy", "all"):
        for j in assy():
            print("assy", run_job(j), flush=True)
    if what in ("steps", "all"):
        for j in steps():
            print("step", run_step(j), flush=True)
    if what in ("assy", "all", "extras"):
        tilt_up_view()
        extras()
    (OUT / "steps" / "steps.json").write_text(json.dumps([dict(n=n, title=t, parts=p) for n, t, p in STEPS], indent=1))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "all")
