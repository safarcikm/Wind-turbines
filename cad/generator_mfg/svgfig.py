"""Tiny SVG drawing helper for the doc 18 step-by-step figures (no dependencies)."""
from __future__ import annotations

import math
from pathlib import Path
from xml.sax.saxutils import escape

# Picture palette: one colour per material, used the same way in every figure.
C = dict(
    steel="#b9c0c8", steel_d="#7d8792", cu="#d9822b", cu_l="#f2b26b",
    mag_n="#d9463b", mag_s="#3b6fd1", liner="#f4d35e", resin="#79c37a",
    al="#cfe4f5", grp="#e6cf9f", pps="#5b5b5b", ptfe="#f7f7f7", g10="#a7d08c",
    ink="#222222", grey="#6b6b6b", light="#f3f4f6", ok="#2f9e44", bad="#e03131",
    warn="#f59f00", air="#ffffff", hot="#ff7b39", vac="#9bb7d4",
    ph_a="#8b5a2b", ph_b="#222222", ph_c="#9a9a9a", brass="#d4b24c",
)
FONT = "DejaVu Sans, Arial, Helvetica, sans-serif"


class Svg:
    def __init__(self, w: float, h: float, title: str = ""):
        self.w, self.h = w, h
        self.items: list[str] = []
        self.title = title
        self._uid = 0

    # ------------------------------------------------------------ primitives
    def raw(self, s: str):
        self.items.append(s)

    def rect(self, x, y, w, h, fill="none", stroke=C["ink"], sw=2, rx=0, dash=None, op=1):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" '
                 f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" fill-opacity="{op}"{d}/>')

    def poly(self, pts, fill="none", stroke=C["ink"], sw=2, closed=True, dash=None, op=1):
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        tag = "polygon" if closed else "polyline"
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(f'<{tag} points="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
                 f'stroke-linejoin="round" fill-opacity="{op}"{d}/>')

    def circle(self, cx, cy, r, fill="none", stroke=C["ink"], sw=2, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" '
                 f'stroke-width="{sw}"{d}/>')

    def line(self, x1, y1, x2, y2, stroke=C["ink"], sw=2, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" '
                 f'stroke-width="{sw}" stroke-linecap="round"{d}/>')

    def path(self, d, fill="none", stroke=C["ink"], sw=2):
        self.raw(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
                 f'stroke-linejoin="round" stroke-linecap="round"/>')

    def text(self, x, y, s, size=16, anchor="middle", weight="normal", color=C["ink"], italic=False):
        st = ' font-style="italic"' if italic else ""
        self.raw(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
                 f'text-anchor="{anchor}" font-weight="{weight}" fill="{color}"{st}>{escape(str(s))}</text>')

    def lines(self, x, y, rows, size=15, anchor="middle", weight="normal", color=C["ink"], gap=1.25):
        for i, r in enumerate(rows):
            self.text(x, y + i * size * gap, r, size, anchor, weight, color)

    def arrow(self, x1, y1, x2, y2, color=C["ink"], sw=3, head=12):
        self.line(x1, y1, x2, y2, color, sw)
        a = math.atan2(y2 - y1, x2 - x1)
        p1 = (x2 - head * math.cos(a - 0.45), y2 - head * math.sin(a - 0.45))
        p2 = (x2 - head * math.cos(a + 0.45), y2 - head * math.sin(a + 0.45))
        self.poly([(x2, y2), p1, p2], fill=color, stroke=color, sw=1)

    def dim(self, x1, y1, x2, y2, label, off=0, size=14, color=C["grey"]):
        """Dimension line with arrows at both ends and a centred label."""
        a = math.atan2(y2 - y1, x2 - x1)
        nx, ny = -math.sin(a) * off, math.cos(a) * off
        x1, y1, x2, y2 = x1 + nx, y1 + ny, x2 + nx, y2 + ny
        self.line(x1, y1, x2, y2, color, 1.5)
        for (xa, ya, s) in ((x1, y1, 1), (x2, y2, -1)):
            p1 = (xa + s * 9 * math.cos(a - 0.4), ya + s * 9 * math.sin(a - 0.4))
            p2 = (xa + s * 9 * math.cos(a + 0.4), ya + s * 9 * math.sin(a + 0.4))
            self.poly([(xa, ya), p1, p2], fill=color, stroke=color, sw=1)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        deg = math.degrees(a)
        if deg > 90 or deg < -90:
            deg += 180
        self.raw(f'<g transform="translate({mx:.1f},{my:.1f}) rotate({deg:.1f})">')
        self.rect(-len(label) * size * 0.31 - 3, -size * 0.85, len(label) * size * 0.62 + 6, size * 1.15,
                  fill="white", stroke="none", sw=0)
        self.text(0, 0, label, size, color=color, weight="bold")
        self.raw("</g>")

    def leader(self, x, y, tx, ty, label, size=15, anchor=None, color=C["ink"]):
        self.line(x, y, tx, ty, color, 1.5)
        self.circle(x, y, 3, fill=color, stroke=color, sw=1)
        if anchor is None:
            anchor = "start" if tx >= x else "end"
        dx = 4 if anchor == "start" else -4
        rows = label if isinstance(label, list) else [label]
        self.lines(tx + dx, ty + size * 0.35, rows, size, anchor, color=color)

    def g(self, tx=0, ty=0, rot=0, sc=1):
        self.raw(f'<g transform="translate({tx:.1f},{ty:.1f}) rotate({rot:.2f}) scale({sc})">')

    def end(self):
        self.raw("</g>")

    # ------------------------------------------------------------ pictograms
    def bubble(self, x, y, n, r=17, fill=C["ink"]):
        self.circle(x, y, r, fill=fill, stroke="white", sw=2)
        self.text(x, y + r * 0.38, n, r * 1.1, weight="bold", color="white")

    def tick(self, x, y, r=14):
        self.circle(x, y, r, fill=C["ok"], stroke="none")
        self.path(f"M{x - r * .5:.1f},{y:.1f} L{x - r * .1:.1f},{y + r * .45:.1f} L{x + r * .55:.1f},{y - r * .45:.1f}",
                  stroke="white", sw=r * 0.28)

    def cross(self, x, y, r=14):
        self.circle(x, y, r, fill=C["bad"], stroke="none")
        k = r * 0.45
        self.line(x - k, y - k, x + k, y + k, "white", r * 0.28)
        self.line(x - k, y + k, x + k, y - k, "white", r * 0.28)

    def warn(self, x, y, s=30):
        h = s * 0.87
        self.poly([(x, y - h / 2), (x + s / 2, y + h / 2), (x - s / 2, y + h / 2)], fill=C["warn"], sw=2)
        self.text(x, y + h * 0.38, "!", s * 0.62, weight="bold")

    def clock(self, x, y, r=16, label=""):
        self.circle(x, y, r, fill="white", sw=2)
        self.line(x, y, x, y - r * 0.7, sw=2)
        self.line(x, y, x + r * 0.5, y, sw=2)
        if label:
            self.text(x, y + r + 16, label, 14, weight="bold")

    def thermo(self, x, y, label="", hot=True):
        self.rect(x - 5, y - 30, 10, 34, fill="white", rx=5)
        self.circle(x, y + 8, 8, fill=C["hot"] if hot else C["mag_s"])
        self.rect(x - 2.5, y - 18 if hot else y - 4, 5, 22 if hot else 8, fill=C["hot"] if hot else C["mag_s"],
                  stroke="none")
        if label:
            self.text(x + 12, y, label, 14, "start", "bold")

    def gauge(self, x, y, r=20, label=""):
        self.circle(x, y, r, fill="white", sw=2)
        self.path(f"M{x - r * .7:.1f},{y + r * .3:.1f} A{r * .75:.1f},{r * .75:.1f} 0 0 1 {x + r * .7:.1f},{y + r * .3:.1f}",
                  stroke=C["grey"], sw=2)
        self.line(x, y + r * 0.2, x + r * 0.45, y - r * 0.45, C["bad"], 2.5)
        if label:
            self.text(x, y + r + 16, label, 14, weight="bold")

    def panel(self, x, y, w, h, n, caption, cap_h=58, size=15):
        """Framed step panel: big step number top-left, caption lines underneath."""
        self.rect(x, y, w, h, fill="white", stroke="#c9ced6", sw=2, rx=10)
        self.rect(x, y + h - cap_h, w, cap_h, fill=C["light"], stroke="none", sw=0)
        self.line(x, y + h - cap_h, x + w, y + h - cap_h, "#c9ced6", 1.5)
        if n is not None:
            self.bubble(x + 22, y + 22, n)
        rows = caption if isinstance(caption, list) else [caption]
        top = y + h - cap_h + (cap_h - (len(rows) - 1) * size * 1.25) / 2 + size * 0.35
        self.lines(x + w / 2, top, rows, size)

    def header(self, title, sub=""):
        self.text(20, 34, title, 24, "start", "bold")
        if sub:
            self.text(20, 58, sub, 15, "start", color=C["grey"])

    def legend(self, x, y, entries, size=14, sw=16):
        for i, (col, name) in enumerate(entries):
            self.rect(x, y + i * (sw + 8), sw, sw, fill=col, sw=1.5)
            self.text(x + sw + 8, y + i * (sw + 8) + sw * 0.8, name, size, "start")

    # ------------------------------------------------------------ output
    def svg(self) -> str:
        t = f"<title>{escape(self.title)}</title>" if self.title else ""
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
                f'width="{self.w}" height="{self.h}">{t}'
                f'<rect width="100%" height="100%" fill="white"/>' + "".join(self.items) + "</svg>")

    def save(self, path: Path):
        path.write_text(self.svg())
