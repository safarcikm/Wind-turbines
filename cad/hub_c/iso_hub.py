"""Isometric views for doc 24 (collective pitch, welded hub).

Run:  python3 iso_hub.py   -> out/iso/IH01..IH05 *.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import cadquery as cq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import model as M
K = M.K
from render import Renderer

OUT = Path(__file__).parent / "out" / "iso"
OUT.mkdir(parents=True, exist_ok=True)
CUT_NEAR = cq.Solid.makeBox(2000, 1000, 2000, cq.Vector(-1000, -1000, -1000))   # half section: y < 0 removed


def scene(theta, cut=True, hub=True, nose=True, context=True, only=None, tol=0.6, az=-150.0, el=24.0):
    R = Renderer(az=az, el=el)
    for i, (n, s, c) in enumerate(M.assembly(theta=theta, with_hub=hub, with_nose=nose, with_context=context)):
        if only and not any(n.startswith(o) for o in only):
            continue
        if cut and n.endswith("_210"):
            continue
        if cut and n in ("hub", "nose_housing", "drum"):
            s = s.cut(CUT_NEAR)
        R.add(s, c, tol=tol, pid=i)
    return R


def save(R, name, title, labels=(), W=2000, H=1400, note=None):
    img = R.render(W, H, margin=150)
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


def blade_pt(a, x, y, s):
    """Blade-local (x, y tangential, s) -> spindle frame point for blade at a deg."""
    import math
    t = math.radians(a - 90.0)
    return (x, y * math.cos(t) - s * math.sin(t), y * math.sin(t) + s * math.cos(t))


def lab_common(theta):
    p = K.pin(theta)
    xy, e = K.yoke_x(theta)
    return [
        ("welded S355NL hub\n(half section)", (60.0, 0.0, -225.0), (420, 120)),
        ("pitch bearing Ø355, ungeared", blade_pt(90, -177.0, 0.0, 380.0), (-420, -60)),
        ("crank r 110,\nclamped by the blade studs", blade_pt(90, -84.0, 0.0, 250.0), (-470, -40)),
        ("link + turnbuckle", blade_pt(90, (p[0] + e[0]) / 2, (p[2] + e[2]) / 2, (p[1] + e[1]) / 2), (330, -120)),
        ("yoke (3 arms)", (xy - 25.0, 0.0, 40.0), (-480, -170)),
        ("electric cylinder 25.5 kN\nball screw Ø32 × 5", (-520.0, 0.0, 45.0), (-480, -40)),
        ("48 V servo + brake", (-600.0, 0.0, 140.0), (-420, -380)),
        ("supercap 16.7 F", (-575.0, 0.0, -112.0), (-420, 40)),
        ("drive (STO)", (-405.0, 0.0, -97.0), (200, 150)),
        ("Al nose housing", (-768.0, 0.0, -105.0), (-330, 110)),
        ("generator drum Ø646 (Rev C)", (330.0, 0.0, -318.0), (80, 60)),
        ("slip ring", (-80.0, 0.0, 30.0), (330, 120)),
    ]


def main():
    th_f, th_x = K.TH_FINE, K.TH_FEATHER
    R = scene(th_f, cut=False, az=-135.0, el=26.0)
    save(R, "IH01-iso-assembled", "IH01  Hub, collective pitch and nose housing on the generator drum (fine pitch)",
         labels=[("pitch bearing", blade_pt(90, -177.0, 0.0, 380.0), (-300, -40)),
                 ("welded hub", (-100.0, -163.0, 163.0), (-300, 40)),
                 ("nose housing\n(inside the spinner)", (-600.0, -80.0, 80.0), (-200, -120)),
                 ("drum Ø646 (Rev C)", (300.0, -225.0, 225.0), (80, -80))],
         note="Spinner and blades not shown. Blade roots drawn as Ø220 stubs.")
    R = scene(th_f, cut=True)
    save(R, "IH02-iso-cutaway-fine", "IH02  Cut-away at fine pitch (−2°): yoke rearmost, x −143",
         labels=lab_common(th_f),
         note="Half section (near blade removed). Clash check over −2° to 92°: clean (cad/hub_c/clash.py).")
    R = scene(th_x, cut=True)
    save(R, "IH03-iso-cutaway-feather", "IH03  Cut-away at feather (92°): yoke forward, x −303 (stroke 160 mm)",
         labels=lab_common(th_x)[:5],
         note="Emergency feather: the drive runs this stroke from the supercap in 3.1 s (30 °/s).")
    R = scene(30.0, cut=False, hub=False, nose=False, context=False)
    p = K.pin(30.0)
    save(R, "IH04-iso-mechanism", "IH04  Pitch mechanism alone (30° pitch)",
         labels=[("crank", blade_pt(90, p[0], p[2], 154), (-260, -100)),
                 ("pitch bearing (outer ring to the hub)", blade_pt(210, 0, 0, 375), (-80, 120)),
                 ("guide rods 2 × Ø25", (-600.0, 37.0, -65.0), (-60, 140)),
                 ("yoke", (K.yoke_x(30.0)[0], 0.0, -90.0), (-160, 130))])
    R = Renderer(az=40.0, el=25.0)
    R.add(M.hub(), M.COL["hub"], tol=0.5)
    save(R, "IH05-iso-weldment", "IH05  Welded hub NH-500W from the rear (117 kg calc, 107 kg model)",
         labels=[("rear flange: 12 × M16 PCD 400,\nØ361 recess to the drum", (187.0, 0.0, -200.0), (80, 60)),
                 ("neck Ø330 × 10, full-penetration weld", blade_pt(90, 0, 160, 270), (60, -60)),
                 ("bearing flange 25, 16 × M16 PCD 300", blade_pt(330, 0, 0, 345), (40, 80)),
                 ("gussets", blade_pt(90, 190, 0, 250), (120, -60))])


if __name__ == "__main__":
    main()
