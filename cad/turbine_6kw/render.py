"""Small z-buffer renderer for isometric views of CadQuery solids (numpy, PNG out).

Each solid is tessellated, projected orthographically and rasterised with a
depth buffer, flat shading and a light outline pass (depth, normal and part
edges), which gives a technical isometric look with correct hidden surfaces.
"""
from __future__ import annotations

import math

import numpy as np


def hex2rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float) / 255.0


def view_basis(az_deg, el_deg):
    """Camera looking towards -d, with d = direction from the scene to the eye."""
    az, el = math.radians(az_deg), math.radians(el_deg)
    d = np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])
    up = np.array([0.0, 0.0, 1.0])
    r = np.cross(up, d)
    r /= np.linalg.norm(r)
    u = np.cross(d, r)
    return r, u, d


class Renderer:
    def __init__(self, az=-135.0, el=30.0, light=(-0.3, 0.5, 0.8)):
        self.r, self.u, self.d = view_basis(az, el)
        L = -0.35 * self.r + 0.45 * self.u + 0.82 * self.d      # light from the upper left of the viewer
        self.L = L / np.linalg.norm(L)
        self.meshes = []

    def add(self, solid, color, tol=0.6, alpha=1.0, pid=None):
        vs, tris = solid.tessellate(tol, 0.3)
        V = np.array([(v.x, v.y, v.z) for v in vs], float)
        T = np.array(tris, int)
        if len(T) == 0:
            return
        self.meshes.append((V, T, hex2rgb(color), pid if pid is not None else len(self.meshes)))

    def project(self, P):
        P = np.atleast_2d(P)
        return np.stack([P @ self.r, P @ self.u, P @ self.d], axis=1)

    def render(self, W=1800, H=1300, margin=40, bg=(1, 1, 1), fit=None):
        allp = np.vstack([self.project(V) for V, *_ in self.meshes])
        lo, hi = allp[:, :2].min(0), allp[:, :2].max(0)
        if fit is not None:
            lo, hi = np.array(fit[0]), np.array(fit[1])
        s = min((W - 2 * margin) / (hi[0] - lo[0]), (H - 2 * margin) / (hi[1] - lo[1]))
        self.s, self.lo = s, lo
        self.off = np.array([(W - s * (hi[0] - lo[0])) / 2, (H - s * (hi[1] - lo[1])) / 2])
        img = np.ones((H, W, 3)) * np.array(bg)
        zb = np.full((H, W), -np.inf)
        idb = np.full((H, W), -1, int)
        nb = np.zeros((H, W, 3))
        for V, T, col, pid in self.meshes:
            Q = self.project(V)
            X = (Q[:, 0] - lo[0]) * s + self.off[0]
            Y = H - ((Q[:, 1] - lo[1]) * s + self.off[1])
            Z = Q[:, 2]
            a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
            n = np.cross(b - a, c - a)
            nn = np.linalg.norm(n, axis=1)
            ok = nn > 1e-12
            n[ok] /= nn[ok, None]
            facing = n @ self.d
            n[facing < 0] *= -1                         # two-sided
            lam = np.clip(n @ self.L, 0, 1)
            shade = 0.42 + 0.58 * lam
            for k in np.nonzero(ok)[0]:
                i0, i1, i2 = T[k]
                xs = np.array([X[i0], X[i1], X[i2]])
                ys = np.array([Y[i0], Y[i1], Y[i2]])
                x0, x1 = max(int(xs.min()), 0), min(int(xs.max()) + 1, W - 1)
                y0, y1 = max(int(ys.min()), 0), min(int(ys.max()) + 1, H - 1)
                if x1 < x0 or y1 < y0:
                    continue
                gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
                den = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
                if abs(den) < 1e-9:
                    continue
                w0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / den
                w1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / den
                w2 = 1 - w0 - w1
                m = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
                if not m.any():
                    continue
                z = w0 * Z[i0] + w1 * Z[i1] + w2 * Z[i2]
                sub = zb[y0:y1 + 1, x0:x1 + 1]
                upd = m & (z > sub)
                if not upd.any():
                    continue
                sub[upd] = z[upd]
                img[y0:y1 + 1, x0:x1 + 1][upd] = col * shade[k]
                idb[y0:y1 + 1, x0:x1 + 1][upd] = pid
                nb[y0:y1 + 1, x0:x1 + 1][upd] = n[k]
        # outlines: part changes, normal creases, depth jumps
        edge = np.zeros((H, W), bool)
        for dy, dx in ((0, 1), (1, 0)):
            a_id, b_id = idb[:H - dy, :W - dx], idb[dy:, dx:]
            e = a_id != b_id
            na, nb2 = nb[:H - dy, :W - dx], nb[dy:, dx:]
            e |= (np.sum(na * nb2, axis=2) < 0.80) & (a_id >= 0)
            za, zb2 = zb[:H - dy, :W - dx], zb[dy:, dx:]
            fin = np.isfinite(za) & np.isfinite(zb2)
            e |= fin & (np.abs(za - zb2) > 6.0 / s * 3)
            edge[:H - dy, :W - dx] |= e
        img[edge] = img[edge] * 0.25
        return np.clip(img, 0, 1)

    def to_px(self, P, H):
        Q = self.project(np.array(P, float))
        X = (Q[:, 0] - self.lo[0]) * self.s + self.off[0]
        Y = H - ((Q[:, 1] - self.lo[1]) * self.s + self.off[1])
        return np.stack([X, Y], 1)
