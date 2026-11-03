"""Minimal 2D drafting library: one geometry, two outputs.

* PDF sheet (A3 landscape, ISO-style title block, scaled views) via matplotlib
* DXF (model space, true 1:1 size, one block of entities per view, layers
  OUTLINE / HIDDEN / CENTER / HATCH / DIM / TEXT) via ezdxf, for CAM, laser
  cutting and import into any CAD system.

Dimensions are drawn as plain lines, arrows and text so that they look the
same in both outputs.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import ezdxf
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Polygon as MplPolygon  # noqa: E402

A3 = (420.0, 297.0)
PT_PER_MM = 72 / 25.4
LW = {"OUTLINE": 0.5, "HIDDEN": 0.25, "CENTER": 0.18, "HATCH": 0.13, "DIM": 0.18,
      "TEXT": 0.18, "THIN": 0.25, "FRAME": 0.7, "PHANTOM": 0.25}
LS = {"HIDDEN": (0, (4, 2)), "CENTER": (0, (10, 2, 2, 2)), "PHANTOM": (0, (10, 2, 2, 2, 2, 2))}
DXF_COLOR = {"OUTLINE": 7, "HIDDEN": 8, "CENTER": 1, "HATCH": 9, "DIM": 3, "TEXT": 3,
             "THIN": 7, "PHANTOM": 5}
DXF_LT = {"HIDDEN": "DASHED", "CENTER": "CENTER", "PHANTOM": "PHANTOM"}


@dataclass
class View:
    name: str
    scale: float                     # sheet mm per model mm
    origin: tuple                    # sheet position of model (0, 0)
    ents: list = field(default_factory=list)
    label: bool = True

    # ---- primitives (model coordinates)
    def line(self, p, q, layer="OUTLINE"):
        self.ents.append(("line", (p, q), layer))

    def poly(self, pts, closed=True, layer="OUTLINE", hatch=False, fill=None):
        self.ents.append(("poly", (list(pts), closed, hatch, fill), layer))

    def circle(self, c, r, layer="OUTLINE"):
        self.ents.append(("circle", (c, r), layer))

    def arc(self, c, r, a0, a1, layer="OUTLINE"):
        self.ents.append(("arc", (c, r, a0, a1), layer))

    def text(self, p, s, h=2.5, ha="left", va="bottom", rot=0.0, layer="TEXT"):
        """h is the text height on the sheet in mm."""
        self.ents.append(("text", (p, s, h, ha, va, rot), layer))

    def centerline(self, p, q, ext=4.0):
        d = math.dist(p, q) or 1
        ux, uy = (q[0] - p[0]) / d, (q[1] - p[1]) / d
        e = ext / self.scale
        self.line((p[0] - ux * e, p[1] - uy * e), (q[0] + ux * e, q[1] + uy * e), "CENTER")

    def cross(self, c, size=None):
        s = (size or 3.0 / self.scale)
        self.line((c[0] - s, c[1]), (c[0] + s, c[1]), "CENTER")
        self.line((c[0], c[1] - s), (c[0], c[1] + s), "CENTER")

    # ---- dimensions
    def _arrow(self, tip, ux, uy):
        a = 2.5 / self.scale
        w = 0.7 / self.scale
        bx, by = tip[0] - ux * a, tip[1] - uy * a
        self.ents.append(("poly", ([tip, (bx - uy * w, by + ux * w), (bx + uy * w, by - ux * w)],
                                   True, False, "k"), "DIM"))

    def dim(self, p, q, off, text=None, kind="h", h=2.5, prefix="", suffix="", tpos=0.5):
        """Linear dimension between p and q. kind 'h' measures x, 'v' measures y,
        'a' aligned. off is the offset of the dimension line in sheet mm
        (positive = above / left / left-normal)."""
        o = off / self.scale
        if kind == "h":
            y = (max(p[1], q[1]) if off > 0 else min(p[1], q[1])) + o
            a, b = (p[0], y), (q[0], y)
            val = abs(q[0] - p[0])
            self.line(p, (p[0], y + math.copysign(1.5 / self.scale, o)), "DIM")
            self.line(q, (q[0], y + math.copysign(1.5 / self.scale, o)), "DIM")
        elif kind == "v":
            x = (min(p[0], q[0]) if off > 0 else max(p[0], q[0])) - o
            a, b = (x, p[1]), (x, q[1])
            val = abs(q[1] - p[1])
            self.line(p, (x - math.copysign(1.5 / self.scale, o), p[1]), "DIM")
            self.line(q, (x - math.copysign(1.5 / self.scale, o), q[1]), "DIM")
        else:
            d = math.dist(p, q)
            ux, uy = (q[0] - p[0]) / d, (q[1] - p[1]) / d
            nx, ny = -uy, ux
            a = (p[0] + nx * o, p[1] + ny * o)
            b = (q[0] + nx * o, q[1] + ny * o)
            val = d
            self.line(p, (a[0] + nx * 1.5 / self.scale, a[1] + ny * 1.5 / self.scale), "DIM")
            self.line(q, (b[0] + nx * 1.5 / self.scale, b[1] + ny * 1.5 / self.scale), "DIM")
        self.line(a, b, "DIM")
        d = math.dist(a, b) or 1
        ux, uy = (b[0] - a[0]) / d, (b[1] - a[1]) / d
        self._arrow(a, -ux, -uy)
        self._arrow(b, ux, uy)
        if text is None:
            text = f"{val:.1f}".rstrip("0").rstrip(".")
        text = prefix + text + suffix
        ang = math.degrees(math.atan2(uy, ux))
        if ang > 90.1 or ang < -89.9:
            ang += 180
        m = (a[0] + (b[0] - a[0]) * tpos, a[1] + (b[1] - a[1]) * tpos)
        g = 0.8 / self.scale
        nx, ny = -math.sin(math.radians(ang)), math.cos(math.radians(ang))
        self.text((m[0] + nx * g, m[1] + ny * g), text, h, "center", "bottom", ang, "DIM")

    def ordinate(self, xs, y_feat, y_base, h=2.2, origin=None, up=True, labels=None):
        """Ordinate dimensions along x: tick at each feature x (y_feat may be a list),
        rotated value text above (or below) y_base. Values relative to origin."""
        x0 = xs[0] if origin is None else origin
        sg = 1 if up else -1
        for i, x in enumerate(xs):
            yf = y_feat[i] if isinstance(y_feat, (list, tuple)) else y_feat
            self.line((x, yf + sg * 1.0 / self.scale), (x, y_base), "DIM")
            val = labels[i] if labels else f"{x - x0:.1f}".rstrip("0").rstrip(".")
            self.text((x + 0.0 / self.scale, y_base + sg * 1.0 / self.scale), val, h,
                      "left" if up else "right", "center", 90, "DIM")

    def leader(self, p, q, text, h=2.5):
        """Leader from feature point p to text at q (model coordinates)."""
        self.line(p, q, "DIM")
        d = math.dist(p, q) or 1
        self._arrow(p, (p[0] - q[0]) / d, (p[1] - q[1]) / d)
        ha = "left" if q[0] >= p[0] else "right"
        e = 3.0 / self.scale * (1 if ha == "left" else -1)
        self.line(q, (q[0] + e, q[1]), "DIM")
        self.text((q[0] + e * 1.2, q[1]), text, h, ha, "center", 0, "DIM")

    # ---- composite helpers
    def turned_half_section(self, section, outer, hatch=True, mirror_outline=True):
        """Upper half: hatched section. Lower half: exterior view."""
        self.poly(section, True, "OUTLINE", hatch=hatch)
        if not mirror_outline:
            return
        pts = [(x, -r) for x, r in outer]
        self.poly(pts, False, "OUTLINE")
        rmax = {}
        for x, r in outer:
            rmax[x] = max(rmax.get(x, 0.0), r)
        for x, r in rmax.items():
            self.line((x, 0.0), (x, -r), "OUTLINE")

    def bolt_circle(self, c, pcd, n, d, start=0.0, layer="OUTLINE", skip=()):
        for i in range(n):
            if i in skip:
                continue
            a = math.radians(start + 360.0 * i / n)
            p = (c[0] + pcd / 2 * math.cos(a), c[1] + pcd / 2 * math.sin(a))
            self.circle(p, d / 2, layer)
            self.cross(p, d / 2 + 1.5 / self.scale)
        self.circle(c, pcd / 2, "CENTER")


@dataclass
class Sheet:
    number: str
    title: str
    material: str = ""
    mass: str = ""
    scale_note: str = ""
    rev: str = "B"
    notes: list = field(default_factory=list)
    table: list | None = None            # list of rows (first row = header)
    table_pos: tuple = (12.0, 285.0)
    table_widths: list | None = None
    views: list = field(default_factory=list)
    size: tuple = A3
    notes_top: tuple | None = None       # (x, y top) or None = bottom-left
    notes_wrap: int = 118

    def view(self, name, scale, origin, label=True):
        v = View(name, scale, origin, label=label)
        self.views.append(v)
        return v

    # -------------------------------------------------------------- PDF
    def render(self, fig=None):
        W, H = self.size
        fig = plt.figure(figsize=(W / 25.4, H / 25.4))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, W)
        ax.set_ylim(0, H)
        ax.set_aspect("equal")
        ax.axis("off")
        lw = lambda k: LW.get(k, 0.25) * PT_PER_MM  # noqa: E731
        # frame
        ax.add_patch(plt.Rectangle((10, 10), W - 20, H - 20, fill=False, lw=lw("FRAME")))
        for v in self.views:
            s, (ox, oy) = v.scale, v.origin
            T = lambda p: (ox + p[0] * s, oy + p[1] * s)  # noqa: E731
            for kind, d, layer in v.ents:
                ls = LS.get(layer, "solid")
                if kind == "line":
                    p, q = T(d[0]), T(d[1])
                    ax.plot([p[0], q[0]], [p[1], q[1]], color="k", lw=lw(layer), ls=ls,
                            solid_capstyle="butt")
                elif kind == "poly":
                    pts, closed, hatch, fill = d
                    tp = [T(p) for p in pts]
                    if fill:
                        ax.add_patch(MplPolygon(tp, closed=True, fc=fill, ec=fill, lw=0.1))
                    elif hatch:
                        ax.add_patch(MplPolygon(tp, closed=True, fill=False, hatch="////",
                                                ec="k", lw=lw(layer)))
                    else:
                        ax.add_patch(MplPolygon(tp, closed=closed, fill=False, ec="k",
                                                lw=lw(layer), ls=ls))
                elif kind == "circle":
                    c, r = d
                    ax.add_patch(plt.Circle(T(c), r * s, fill=False, lw=lw(layer), ls=ls))
                elif kind == "arc":
                    c, r, a0, a1 = d
                    from matplotlib.patches import Arc
                    ax.add_patch(Arc(T(c), 2 * r * s, 2 * r * s, theta1=a0, theta2=a1,
                                     lw=lw(layer), ls=ls))
                elif kind == "text":
                    p, txt, h, ha, va, rot = d
                    ax.text(*T(p), txt, fontsize=h * PT_PER_MM / 0.72, ha=ha, va=va,
                            rotation=rot, rotation_mode="anchor", family="DejaVu Sans")
        self._title_block(ax)
        self._notes(ax)
        self._table(ax)
        return fig

    def _title_block(self, ax):
        W, H = self.size
        x0, y0, w, h = W - 10 - 180, 10, 180, 42
        lw = 0.5 * PT_PER_MM
        ax.add_patch(plt.Rectangle((x0, y0), w, h, fill=False, lw=lw))
        for yy in (y0 + 14, y0 + 28):
            ax.plot([x0, x0 + w], [yy, yy], color="k", lw=lw * 0.5)
        for xx in (x0 + 60, x0 + 120):
            ax.plot([xx, xx], [y0, y0 + 28], color="k", lw=lw * 0.5)
        f = lambda mm: mm * PT_PER_MM / 0.72  # noqa: E731
        small = dict(fontsize=f(1.8), color="0.3")
        ax.text(x0 + 2, y0 + 39, "12 kW WIND TURBINE (ICELAND) · NACELLE PROTOTYPE P1", fontsize=f(2.2),
                weight="bold", va="top")
        ax.text(x0 + 2, y0 + 33.5, self.title, fontsize=f(3.2), weight="bold", va="top")
        cells = [
            (x0 + 2, y0 + 25, "DRAWING NO.", self.number),
            (x0 + 62, y0 + 25, "REV / DATE", f"{self.rev} · 2026-11-03"),
            (x0 + 122, y0 + 25, "SCALE (A3)", self.scale_note),
            (x0 + 2, y0 + 11, "MATERIAL", self.material),
            (x0 + 62, y0 + 11, "MASS (CALC.)", self.mass),
            (x0 + 122, y0 + 11, "DRAWN / CHECKED", "Claude / not checked"),
        ]
        for cx, cy, k, val in cells:
            ax.text(cx, cy, k, va="top", **small)
            ax.text(cx, cy - 4.5, val, va="top", fontsize=f(2.3 if len(val) < 34 else 1.8))
        ax.text(x0, y0 + h + 2, "Dimensions mm · ISO 2768-mK · ISO 8015 · first angle projection · "
                "edges broken 0.5 unless stated · NOT CHECKED: prototype release only after review",
                fontsize=f(1.7), color="0.25")

    def _wrap(self):
        lines = []
        for i, n in enumerate(self.notes, 1):
            words, cur, first = n.split(), "", True
            for wd in words:
                if len(cur) + len(wd) + 1 > self.notes_wrap:
                    lines.append((f"{i}." if first else "", cur))
                    cur, first = wd, False
                else:
                    cur = (cur + " " + wd).strip()
            lines.append((f"{i}." if first else "", cur))
        return lines

    def notes_height(self):
        return 3.3 * len(self._wrap()) + 6 if self.notes else 0

    def _notes(self, ax):
        if not self.notes:
            return
        f = lambda mm: mm * PT_PER_MM / 0.72  # noqa: E731
        lines = self._wrap()
        if self.notes_top is None:
            x, y = 14.0, 12.0 + self.notes_height()
        else:
            x, y = self.notes_top
        ax.text(x, y, "NOTES", fontsize=f(2.4), weight="bold", va="top")
        y -= 4.5
        for num, t in lines:
            ax.text(x, y, num, fontsize=f(1.95), va="top")
            ax.text(x + 4.5, y, t, fontsize=f(1.95), va="top")
            y -= 3.3

    def _table(self, ax):
        if not self.table:
            return
        f = lambda mm: mm * PT_PER_MM / 0.72  # noqa: E731
        x0, y = self.table_pos
        widths = self.table_widths or [40] * len(self.table[0])
        rh = 4.2
        for j, row in enumerate(self.table):
            x = x0
            for w, cell in zip(widths, row):
                ax.add_patch(plt.Rectangle((x, y - rh), w, rh, fill=False, lw=0.18 * PT_PER_MM))
                ax.text(x + 1, y - rh / 2, str(cell), fontsize=f(1.9), va="center",
                        weight="bold" if j == 0 else "normal")
                x += w
            y -= rh

    # -------------------------------------------------------------- DXF
    def to_dxf(self, path, view_names=None, gap=100.0):
        doc = ezdxf.new("R2010", setup=True)
        doc.units = ezdxf.units.MM
        for name, col in DXF_COLOR.items():
            if name not in doc.layers:
                doc.layers.add(name, color=col, linetype=DXF_LT.get(name, "Continuous"))
        msp = doc.modelspace()
        xoff = 0.0
        for v in self.views:
            if view_names and v.name not in view_names:
                continue
            xs, ys = [], []
            for kind, d, _ in v.ents:
                if kind == "line":
                    xs += [d[0][0], d[1][0]]
                elif kind == "poly":
                    xs += [p[0] for p in d[0]]
                elif kind in ("circle", "arc"):
                    xs += [d[0][0] - d[1], d[0][0] + d[1]]
            if not xs:
                continue
            dx = xoff - min(xs)
            hs = 1.0 / v.scale
            for kind, d, layer in v.ents:
                at = {"layer": layer}
                if kind == "line":
                    msp.add_line((d[0][0] + dx, d[0][1]), (d[1][0] + dx, d[1][1]), dxfattribs=at)
                elif kind == "poly":
                    pts, closed, hatch, fill = d
                    tp = [(p[0] + dx, p[1]) for p in pts]
                    if fill:
                        h = msp.add_hatch(color=7, dxfattribs={"layer": "DIM"})
                        h.paths.add_polyline_path(tp, is_closed=True)
                        continue
                    msp.add_lwpolyline(tp, close=closed, dxfattribs=at)
                    if hatch:
                        h = msp.add_hatch(dxfattribs={"layer": "HATCH"})
                        h.set_pattern_fill("ANSI31", scale=1.0 * hs)
                        h.paths.add_polyline_path(tp, is_closed=True)
                elif kind == "circle":
                    msp.add_circle((d[0][0] + dx, d[0][1]), d[1], dxfattribs=at)
                elif kind == "arc":
                    msp.add_arc((d[0][0] + dx, d[0][1]), d[1], d[2], d[3], dxfattribs=at)
                elif kind == "text":
                    p, txt, h, ha, va, rot = d
                    t = msp.add_text(txt, height=h * hs, rotation=rot, dxfattribs=at)
                    al = {("left", "bottom"): "BOTTOM_LEFT", ("center", "bottom"): "BOTTOM_CENTER",
                          ("right", "bottom"): "BOTTOM_RIGHT", ("left", "center"): "MIDDLE_LEFT",
                          ("center", "center"): "MIDDLE_CENTER", ("right", "center"): "MIDDLE_RIGHT",
                          ("left", "top"): "TOP_LEFT", ("center", "top"): "TOP_CENTER",
                          ("right", "top"): "TOP_RIGHT"}.get((ha, va), "BOTTOM_LEFT")
                    t.set_placement((p[0] + dx, p[1]), align=ezdxf.enums.TextEntityAlignment[al])
            xoff += max(xs) - min(xs) + gap
        doc.saveas(path)
