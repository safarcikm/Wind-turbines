"""Isometric views for doc 25 (yaw system).

Run:  python3 iso_yaw.py   -> out/iso/IY01..IY05 *.png
"""
from __future__ import annotations

import math
from pathlib import Path

import cadquery as cq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import model as M  # noqa: E402
from render import Renderer  # noqa: E402

OUT = Path(__file__).parent / "out" / "iso"
OUT.mkdir(parents=True, exist_ok=True)


def P(a, u, z, v=0.0):
    """Point at angle a (deg), radius u, tangential v, height z."""
    t = math.radians(a)
    return (u * math.cos(t) - v * math.sin(t), u * math.sin(t) + v * math.cos(t), z)


def save(R, name, title, labels=(), W=2000, H=1400, note=None, margin=150):
    img = R.render(W, H, margin=margin)
    fig = plt.figure(figsize=(W / 150, H / 150), dpi=150)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(img)
    ax.set_axis_off()
    for text, p, dxy in labels:
        q = R.to_px([p], H)[0]
        ax.annotate(text, xy=q, xytext=(q[0] + dxy[0], q[1] + dxy[1]), fontsize=9,
                    arrowprops=dict(arrowstyle="-", lw=0.7, color="#222"), color="#111",
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#999", lw=0.5))
    ax.text(30, 50, title, fontsize=13, weight="bold", color="#111")
    if note:
        ax.text(30, H - 30, note, fontsize=8.5, color="#333")
    fig.savefig(OUT / f"{name}.png", dpi=150)
    plt.close(fig)
    print("written", name, flush=True)


def scene(parts, az, el, skip=(), cut=None, tol=0.8, explode=None):
    R = Renderer(az=az, el=el)
    for i, (n, s, c) in enumerate(parts):
        if any(n.startswith(k) for k in skip):
            continue
        if cut is not None:
            s = s.cut(cut)
        if explode:
            dz = explode(n)
            if dz:
                s = s.translate(cq.Vector(0, 0, dz))
        R.add(s, c, tol=tol, pid=i)
    return R


CTX_KEEP = ("ctx_NP1-300-2",)


def main():
    parts = M.assembly(context=True)
    ctx_skip = [n for n, *_ in parts if n.startswith("ctx_") and not n.startswith(CTX_KEEP)]
    a_pad = M.PADU["angles"][0]
    # IY01 assembled, from the front-left, slightly below the bedplate
    R = scene(parts, az=-150.0, el=18.0, skip=ctx_skip)
    save(R, "IY01-iso-assembled", "IY01  Yaw system under the bedplate (bedplate bottom plate shown)",
         labels=[("NY-410 friction pad unit\n(passive, 3 kNm, no hydraulics)", P(a_pad, 430, -120), (-430, 90)),
                 ("NY-400 tower-top adapter:\nring seat + friction track", P(-150, 395, -78), (-420, 60)),
                 ("slewing ring, outer gear z150 m4", P(-100, 304, -40), (-200, 170)),
                 ("gearmotor 0.18 kW + motor brake", P(-90, 328, 300), (-430, -40)),
                 ("NY-440 encoder + cam limit switch", P(-68, 348, 170), (120, -120)),
                 ("tower flange (mounting point)", (0.0, -210.0, -345.0), (-150, 120)),
                 ("bedplate (context)", (-330.0, -150.0, 40.0), (-300, -150))],
         note="Nacelle cover, generator and rotor not shown. Yaw axis vertical; front of the nacelle to the left.")
    # IY02 exploded
    def ex(n):
        if n in ("NY-400_adapter",):
            return -250
        if n in ("tower_flange_stub",):
            return -450
        if n == "ring_outer":
            return -120
        if n.startswith("NY-460_cables"):
            return 0
        if n.startswith("ctx_"):
            return 260
        if n.startswith("NY-410") and ("pad_lower" in n or "piston" in n or "spring" in n or "plug" in n):
            return -60
        return 120
    R = scene(parts, az=-140.0, el=24.0, skip=ctx_skip + ["NY-460_cables"], explode=ex)
    save(R, "IY02-iso-exploded", "IY02  Exploded: tower side (adapter, outer gear ring) below, nacelle side above",
         labels=[("bedplate", (-330.0, 200.0, 300.0), (-200, -90)),
                 ("inner ring (to the bedplate, 16 × M16 PCD 300)", P(-120, 175, 90), (-520, -60)),
                 ("outer gear ring (to the adapter, 16 × M16 PCD 440)", P(-120, 300, -160), (-560, 40)),
                 ("track 15 mm, r 250–395", P(-160, 380, -320), (-380, 80)),
                 ("8 gussets", P(-101.25, 260, -400), (-200, 160)),
                 ("cable hanger Ø168", (0.0, -84.0, -150.0), (250, 160)),
                 ("NY-430 yaw lock", P(38.2, 400, 70), (200, -120))],
         note="Explode offsets for clarity only. All bolts from below through the adapter or from inside the bedplate.")
    # IY03 pad unit half section (cut through the unit's own radial plane)
    pu_parts = [(n, s, c) for n, s, c in parts if n.startswith("NY-410L") or n in ("NY-400_adapter", "ring_outer")]
    cutbox = cq.Solid.makeBox(1000, 1000, 1000, cq.Vector(-500, 0, -500)).rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), a_pad)
    sector = cq.Solid.makeBox(500, 600, 700, cq.Vector(150, -300, -450)).rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), a_pad)
    R = Renderer(az=a_pad + 60.0, el=14.0)
    for i, (n, s, c) in enumerate(pu_parts):
        s = s.intersect(sector)
        if not n.startswith("NY-410L_bracket") and not n.startswith("NY-410L_pins"):
            s = s.cut(cutbox)
        R.add(s, c, tol=0.3, pid=i)
    save(R, "IY03-iso-pad-unit-section", "IY03  Friction pad unit NY-410, half section (floating C-frame)",
         labels=[("bracket, 4 × M16 into the bedplate", P(a_pad, 430, -10, -60), (120, -110)),
                 ("2 guide pins Ø25 (1.4462), frame floats", P(a_pad, 355, -40, 68), (-420, -120)),
                 ("upper pad 90 × 60 × 12", P(a_pad, 360, -64), (-420, -40)),
                 ("track (adapter)", P(a_pad, 300, -78), (-420, 40)),
                 ("lower pad + piston", P(a_pad, 360, -100), (-420, 110)),
                 ("8 disc springs DIN 2093 B 63\nin series, preset 7.0 mm", P(a_pad, 355, -127), (-420, 220)),
                 ("M68 × 2 adjuster + lock nut", P(a_pad, 355, -168), (180, 150)),
                 ("lightning contact on the track rim", P(a_pad, 400, -78), (200, 60))],
         note="Clamp 5.3 kN per unit, 0.98 MPa on the pads; friction 2.4–3.6 kNm for both units (μ 0.32–0.48).")
    # IY04 lock and encoder from the rear
    keep = ("NY-430", "NY-440", "ring_outer", "NY-400_adapter", "ctx_NP1-300-2", "yaw_drive_right", "NY-420_right")
    sub = [(n, s, c) for n, s, c in parts if n.startswith(keep)]
    clip = cq.Solid.makeBox(900, 1000, 900, cq.Vector(0, -700, -450))
    R = Renderer(az=10.0, el=-12.0)
    for i, (n, s, c) in enumerate(sub):
        R.add(s.intersect(clip), c, tol=0.5, pid=i)
    save(R, "IY04-iso-lock-encoder", "IY04  Rear, from below: yaw lock NY-430 and encoder unit NY-440",
         labels=[("lock block: 2 teeth in the ring gear,\nM24 screw, 'engaged' sensor", P(38.2, 300, -40), (120, -140)),
                 ("encoder pinion z24 m4\n(scissor, no backlash)", P(-68, 348, -35), (-460, 120)),
                 ("multiturn encoder + cam limit switch ±3 turns", P(-68, 348, 170), (-200, -150)),
                 ("right gearmotor", P(-90, 328, 250), (-260, -90))],
         note="Rear part of the yaw system only (X > 0).")
    # IY05 from below
    R = scene(parts, az=-120.0, el=-28.0, skip=ctx_skip)
    save(R, "IY05-iso-from-below", "IY05  From below: adapter cone, gussets, bolt access and cable hanger",
         labels=[("16 × M20 10.9 to the tower", P(-140, 190, -360), (-380, 60)),
                 ("16 × M16 10.9 from below into the outer ring", P(-170, 220, -96), (-460, -90)),
                 ("cable hanger: cables cleated here,\n7.5 m free twist length below", (0.0, 0.0, -290.0), (250, 160)),
                 ("access window", (240.0, 0.0, -255.0), (200, 60)),
                 ("lower jaw with spring stack", P(-141.8, 370, -160), (-300, 120))],
         note="Tower tube below the flange not shown.")


if __name__ == "__main__":
    main()
