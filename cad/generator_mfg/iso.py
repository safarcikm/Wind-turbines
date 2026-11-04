"""Small isometric 3D renderer for the doc 18 pictures (pure Python, SVG out).

World axes: X and Y horizontal, Z up. The viewer looks from (+1, +1, +1), so a
point moves right on paper with X - Y and up with Z. Solids are built as shaded
planar faces (revolved profiles, extruded outlines, arc pieces) and drawn back
to front (painter's order). Back faces are culled. Sharp corners and the outline
where a curved surface turns away are drawn as dark edges, which gives the
usual "technical isometric" look.
"""
from __future__ import annotations

import math

COS30 = math.cos(math.radians(30))
VIEW = (1 / math.sqrt(3),) * 3


def _norm(v):
    m = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / m for c in v)


LIGHT = _norm((-0.45, 0.35, 0.82))


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def shade(hexcol, k):
    """k < 1 darkens, k > 1 lightens towards white."""
    h = hexcol.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    if k <= 1:
        r, g, b = (c * k for c in (r, g, b))
    else:
        t = min(k - 1, 1)
        r, g, b = (c + (255 - c) * t for c in (r, g, b))
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(c))) for c in (r, g, b))


# ------------------------------------------------------------ transforms
class Xf:
    """Rigid transform: p_world = R p + t (R orthogonal, rows given)."""

    def __init__(self, R=((1, 0, 0), (0, 1, 0), (0, 0, 1)), t=(0, 0, 0)):
        self.R, self.t = R, t

    def p(self, v):
        R, t = self.R, self.t
        return tuple(R[i][0] * v[0] + R[i][1] * v[1] + R[i][2] * v[2] + t[i] for i in range(3))

    def n(self, v):
        R = self.R
        return _norm(tuple(R[i][0] * v[0] + R[i][1] * v[1] + R[i][2] * v[2] for i in range(3)))

    def then(self, other: "Xf") -> "Xf":
        """Apply self first, then other."""
        R = tuple(tuple(sum(other.R[i][k] * self.R[k][j] for k in range(3)) for j in range(3)) for i in range(3))
        return Xf(R, other.p(self.t))


def rotz(deg, t=(0, 0, 0)):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return Xf(((c, -s, 0), (s, c, 0), (0, 0, 1)), t)


def move(x=0, y=0, z=0):
    return Xf(t=(x, y, z))


# local (u, v, w) -> world: u->X, v->Z, w->Y   (an outline drawn "standing up", extruded backwards)
STAND = Xf(((1, 0, 0), (0, 0, 1), (0, 1, 0)))


def area2(loop):
    return sum(loop[i][0] * loop[(i + 1) % len(loop)][1] - loop[(i + 1) % len(loop)][0] * loop[i][1]
               for i in range(len(loop))) / 2


def corner_deg(a, b, c):
    v1 = (b[0] - a[0], b[1] - a[1])
    v2 = (c[0] - b[0], c[1] - b[1])
    m = math.hypot(*v1) * math.hypot(*v2) or 1
    return math.degrees(math.acos(max(-1, min(1, (v1[0] * v2[0] + v1[1] * v2[1]) / m))))


# ------------------------------------------------------------ scene
class Scene:
    def __init__(self, edge="#2b2b2b", ew=1.1):
        self.faces = []
        self.edge, self.ew = edge, ew

    # one planar face: loops (outer + holes) of world points, outward normal
    def face(self, loops, normal, fill, edges=(), cull=True, layer=0, bias=0.0, op=1.0):
        if cull and dot(normal, VIEW) <= 1e-9:
            return
        pts = loops[0]
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        cz = sum(p[2] for p in pts) / len(pts)
        self.faces.append(dict(layer=layer, d=cx + cy + cz + bias, loops=loops, n=normal, fill=fill,
                               edges=list(edges), op=op))

    def wire(self, pts, color, sw=3, layer=0, bias=0.0):
        """A visible line in space (wire, lead, axis), depth-sorted with the faces."""
        d = sum(p[0] + p[1] + p[2] for p in pts) / len(pts) + bias
        self.faces.append(dict(layer=layer, d=d, wire=pts, color=color, sw=sw))

    # ---------------------------------------------------------- solids
    def revolve(self, prof, fill, th0=0.0, th1=360.0, step=4.0, axial=(0.0, 1.0), xf=Xf(), layer=0,
                corner=20.0, bias=0.0, split=25.0):
        """Revolve a closed (u=axial, r) profile about the Z axis; z = axial[0] + axial[1]*u.
        Partial sweeps get cut faces at th0 and th1 (a cut-away view)."""
        if split:
            fine = []
            for i, p in enumerate(prof):
                q = prof[(i + 1) % len(prof)]
                k = max(1, int(math.hypot(q[0] - p[0], q[1] - p[1]) // split))
                fine += [(p[0] + (q[0] - p[0]) * j / k, p[1] + (q[1] - p[1]) * j / k) for j in range(k)]
            prof = fine
        full = abs(th1 - th0) >= 359.99
        n = max(1, int(math.ceil(abs(th1 - th0) / step)))
        ths = [math.radians(th0 + (th1 - th0) * i / n) for i in range(n + 1)]
        sgn = 1 if area2(prof) > 0 else -1
        z0, zs = axial

        def P(q, th):
            return xf.p((q[1] * math.cos(th), q[1] * math.sin(th), z0 + zs * q[0]))

        m = len(prof)
        for e in range(m):
            p, q = prof[e], prof[(e + 1) % m]
            du, dr = q[0] - p[0], q[1] - p[1]
            nu, nr = (dr * sgn, -du * sgn)
            cp = corner_deg(prof[e - 1], p, q) > corner
            cq = corner_deg(p, q, prof[(e + 2) % m]) > corner
            norms = []
            for i in range(n):
                tm = (ths[i] + ths[i + 1]) / 2
                norms.append(xf.n((nr * math.cos(tm), nr * math.sin(tm), nu * zs)))
            front = [dot(nv, VIEW) > 1e-9 for nv in norms]
            for i in range(n):
                if not front[i]:
                    continue
                a, b = ths[i], ths[i + 1]
                quad = [P(p, a), P(q, a), P(q, b), P(p, b)]
                ed = []
                if cp:
                    ed.append([quad[0], quad[3]])
                if cq:
                    ed.append([quad[1], quad[2]])
                prev = front[i - 1] if (i > 0 or full) else None
                nxt = front[(i + 1) % n] if (i < n - 1 or full) else None
                if prev is False:
                    ed.append([quad[0], quad[1]])
                if nxt is False:
                    ed.append([quad[3], quad[2]])
                if not full and i == 0:
                    ed.append([quad[0], quad[1]])
                if not full and i == n - 1:
                    ed.append([quad[3], quad[2]])
                self.face([quad], norms[i], fill, ed, cull=False, layer=layer, bias=bias)
        if not full:
            for th, s in ((ths[0], -1), (ths[-1], 1)):
                loop = [P(q, th) for q in prof]
                nv = xf.n((-math.sin(th) * s * (1 if th1 > th0 else -1), math.cos(th) * s * (1 if th1 > th0 else -1), 0))
                self.face([loop], nv, shade(fill, 1.25), [loop + [loop[0]]], layer=layer, bias=bias)

    def prism(self, loops2d, w0, w1, fill, xf=Xf(), layer=0, corner=25.0, bias=0.0, cap_fill=None):
        """Extrude 2D loops (outer first, then holes) in local (u, v) along w from w0 to w1."""
        loops = []
        for i, lp in enumerate(loops2d):
            ccw = area2(lp) > 0
            want = (i == 0)
            loops.append(list(lp) if ccw == want else list(reversed(lp)))
        for w, s in ((w0, -1), (w1, 1)):
            L3 = [[xf.p((u, v, w)) for u, v in lp] for lp in loops]
            self.face(L3, xf.n((0, 0, s)), cap_fill or fill, [l + [l[0]] for l in L3], layer=layer, bias=bias)
        for lp in loops:
            m = len(lp)
            norms, quads = [], []
            for e in range(m):
                p, q = lp[e], lp[(e + 1) % m]
                nv = xf.n((q[1] - p[1], -(q[0] - p[0]), 0))
                norms.append(nv)
                quads.append([xf.p((p[0], p[1], w0)), xf.p((q[0], q[1], w0)),
                              xf.p((q[0], q[1], w1)), xf.p((p[0], p[1], w1))])
            front = [dot(nv, VIEW) > 1e-9 for nv in norms]
            for e in range(m):
                if not front[e]:
                    continue
                quad = quads[e]
                ed = [[quad[0], quad[1]], [quad[3], quad[2]]]
                if corner_deg(lp[e - 1], lp[e], lp[(e + 1) % m]) > corner or not front[e - 1]:
                    ed.append([quad[0], quad[3]])
                if corner_deg(lp[e], lp[(e + 1) % m], lp[(e + 2) % m]) > corner or not front[(e + 1) % m]:
                    ed.append([quad[1], quad[2]])
                self.face([quad], norms[e], fill, ed, cull=False, layer=layer, bias=bias)

    def box(self, x0, y0, z0, x1, y1, z1, fill, layer=0, bias=0.0):
        self.prism([[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]], z0, z1, fill, layer=layer, bias=bias)

    def cylinder(self, r, z0, z1, fill, cx=0, cy=0, r_in=0.0, step=6.0, layer=0, bias=0.0):
        prof = [(z0, r_in), (z1, r_in), (z1, r), (z0, r)] if r_in > 0 else [(z0, 0.001), (z1, 0.001), (z1, r), (z0, r)]
        self.revolve(prof, fill, step=step, xf=move(cx, cy, 0), layer=layer, bias=bias)

    # ---------------------------------------------------------- output
    def proj(self, p, ox, oy, s):
        return ox + s * (p[0] - p[1]) * COS30, oy - s * (p[2] - (p[0] + p[1]) * 0.5)

    def render(self, S, ox, oy, s):
        for f in sorted(self.faces, key=lambda f: (f["layer"], f["d"])):
            if "wire" in f:
                pts = " ".join("%.1f,%.1f" % self.proj(p, ox, oy, s) for p in f["wire"])
                S.raw(f'<polyline points="{pts}" fill="none" stroke="{f["color"]}" stroke-width="{f["sw"]}" '
                      f'stroke-linecap="round" stroke-linejoin="round"/>')
                continue
            k = 0.62 + 0.5 * max(0.0, dot(f["n"], LIGHT))
            col = shade(f["fill"], k)
            d = ""
            for lp in f["loops"]:
                d += "M" + " L".join("%.1f,%.1f" % self.proj(p, ox, oy, s) for p in lp) + " Z "
            S.raw(f'<path d="{d}" fill="{col}" fill-rule="evenodd" stroke="{col}" stroke-width="0.7" '
                  f'stroke-linejoin="round"/>')
            if f["edges"]:
                d = ""
                for e in f["edges"]:
                    d += "M" + " L".join("%.1f,%.1f" % self.proj(p, ox, oy, s) for p in e) + " "
                S.raw(f'<path d="{d}" fill="none" stroke="{self.edge}" stroke-width="{self.ew}" '
                      f'stroke-linecap="round"/>')
