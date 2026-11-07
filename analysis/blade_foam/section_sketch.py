"""Doc 41 F03: section of the foam-core blade at r = 1.2 m (to scale except the laminate, drawn 3x thick)."""
from pathlib import Path
import sys, math
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "variant_m8"))
import common as C            # noqa
import blade as BLD           # noqa
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

c, tc = 0.47, 0.26
x, y, xs, up = BLD.outline(c, tc)
fig, ax = plt.subplots(figsize=(11, 4))
k = 3.0    # laminate exaggeration
skin = 0.0012 * k
ax.add_patch(Polygon(np.c_[x, y], closed=True, fc="#e8d27a", ec="none"))             # foam
# webs (biax wrap of the spar block)
for xw in (0.15, 0.45):
    yy = np.interp(xw * c, x[up], y[up])
    ax.add_patch(plt.Rectangle((xw * c - 0.001 * k, -yy), 0.002 * k, 2 * yy, fc="#4c72b0", ec="none"))
# caps (carbon planks)
cap = (xs >= 0.15) & (xs <= 0.45)
for sgn, m in ((1, up), (-1, ~up)):
    xc = x[m & cap]; yc = y[m & cap]
    o = np.argsort(xc); xc, yc = xc[o], yc[o]
    t = 0.0045 * k
    ax.add_patch(Polygon(np.r_[np.c_[xc, yc - sgn * skin], np.c_[xc[::-1], yc[::-1] - sgn * (skin + t)]], closed=True, fc="#222222"))
    ax.plot(xc, yc - sgn * (skin + t + 0.0004 * k), color="#4c72b0", lw=2.2)     # biax wrap under the cap
# outer skin
ax.plot(np.r_[x, x[0]], np.r_[y, y[0]], color="#55a868", lw=3.2)
# TE UD
ax.plot(x[xs > 0.96], y[xs > 0.96], color="#2a6e3f", lw=5)
# LEP
for m in (up, ~up):
    sel = (xs < 0.12) & m
    o = np.argsort(x[sel])
    ax.plot(np.r_[x[sel][o][::-1] if m is up else x[sel][o]], np.r_[y[sel][o][::-1] if m is up else y[sel][o]],
            color="#c44e52", lw=6, alpha=0.8, solid_capstyle="butt")
# conductor groove
ax.add_patch(plt.Circle((0.45 * c + 0.012, 0.0), 0.005, fc="#b55d00"))
notes = [((0.02, 0.05), "LE block (H80)", (0.0, 0.085)),
         ((0.14, 0.0), "spar block (H80)\nwrapped 2 × biax ±45 = webs", (0.02, -0.125)),
         ((0.33, 0.0), "TE block (H80)", (0.33, -0.08)),
         ((0.12, 0.062), "pultruded carbon planks in machined pocket\n4.75 mm at root → 1 mm at r ≈ 2.7 m", (0.17, 0.11)),
         ((0.27, 0.035), "outer skin 2 × triax 800 g/m² (1.2 mm), one-shot infusion", (0.30, 0.09)),
         ((0.005, -0.01), "PU leading-edge protection", (-0.085, -0.075)),
         ((0.46, 0.0), "TE UD strip", (0.44, 0.05)),
         ((0.223, 0.0), "down conductor in groove", (0.25, -0.115))]
for xy, txt, xyt in notes:
    ax.annotate(txt, xy=xy, xytext=xyt, fontsize=8, arrowprops=dict(arrowstyle="-", lw=0.6))
ax.set_aspect("equal"); ax.set_xlim(-0.09, 0.56); ax.set_ylim(-0.14, 0.14); ax.axis("off")
ax.set_title("Foam-core blade section at r = 1.2 m (chord 0.47 m, t/c 26 %); laminate drawn 3× thicker", fontsize=10)
fig.tight_layout(); fig.savefig(HERE / "results" / "F03-section.png", dpi=130)
