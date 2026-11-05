"""Doc 24 hub and collective pitch: 3D parts (CadQuery), spindle frame.

Frame: x along the rotor axis, rearward (towards the nacelle) from the blade
plane; y lateral; z up. Blade 1 points up (90 deg). A blade-axis part is built
in the blade-local frame (x = rotor axis, y tangential, z = s, distance from
the rotor axis along the pitch axis) and turned with blade_axis().

Dimensions: docs/24-collective-pitch-hub.md and analysis/hub/collective.py
(linkage geometry is imported from there, so the model follows the sizing).
"""
from __future__ import annotations

import math
import os
import sys

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "analysis", "hub"))
sys.path.insert(0, os.path.join(HERE, "..", "nacelle_p1"))
import collective as K   # noqa: E402  (linkage kinematics)
import geometry as G     # noqa: E402  (drum, spindle: context only)

BLADES = (90.0, 210.0, 330.0)

HUB = dict(shell_r=(220.0, 230.0), shell_x=(-240.0, 175.0), rear=dict(x=(175.0, 200.0), r=(170.0, 235.0)),
           front=dict(x=(-252.0, -240.0), r=(150.0, 230.0)), neck_r=(155.0, 165.0), neck_s=(190.0, 325.0),
           flange=dict(s=(325.0, 350.0), r=(131.0, 180.0)))
PB = dict(outer=dict(s=(350.0, 400.0), r=(127.5, 177.5)), inner=dict(s=(352.0, 402.0), r=(90.0, 122.5)))
CRANK = dict(flange=dict(s=(337.0, 352.0), r=(80.0, 118.0)), tube=dict(s=(164.0, 337.0), r=(80.0, 84.0)),
             lever=dict(s=(144.0, 164.0)), pin_r=15.0)
YOKE_T = 20.0
NOSE_X = (-770.0, -252.0)


def blade_axis(shape, a_deg):
    return shape.rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), a_deg - 90.0)


def zcyl(r, s0, s1, x=0.0, y=0.0):
    return cq.Solid.makeCylinder(r, s1 - s0, cq.Vector(x, y, s0), cq.Vector(0, 0, 1))


def xcyl(r, x0, x1, y=0.0, z=0.0):
    return cq.Solid.makeCylinder(r, x1 - x0, cq.Vector(x0, y, z), cq.Vector(1, 0, 0))


def ring_z(r0, r1, s0, s1):
    return zcyl(r1, s0, s1).cut(zcyl(r0, s0 - 1, s1 + 1))


def ring_x(r0, r1, x0, x1):
    return xcyl(r1, x0, x1).cut(xcyl(r0, x0 - 1, x1 + 1))


def holes_z(solid, n, pcd, d, s0, s1, start=0.0):
    for k in range(n):
        a = math.radians(start + 360.0 * k / n)
        solid = solid.cut(zcyl(d / 2, s0, s1, pcd / 2 * math.cos(a), pcd / 2 * math.sin(a)))
    return solid


def holes_x(solid, n, pcd, d, x0, x1, start=0.0):
    for k in range(n):
        a = math.radians(start + 360.0 * k / n)
        solid = solid.cut(xcyl(d / 2, x0, x1, pcd / 2 * math.cos(a), pcd / 2 * math.sin(a)))
    return solid


def revolve(poly):
    return cq.Workplane("XY").polyline(poly).close().revolve(360, (0, 0, 0), (1, 0, 0)).val()


def stadium(p0, r0, p1, r1, z0, z1):
    """Plate: convex hull of two circles in the local x-y plane, extruded z0..z1."""
    a = zcyl(r0, z0, z1, *p0)
    b = zcyl(r1, z0, z1, *p1)
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    pts = [(p0[0] + nx * r0, p0[1] + ny * r0), (p1[0] + nx * r1, p1[1] + ny * r1),
           (p1[0] - nx * r1, p1[1] - ny * r1), (p0[0] - nx * r0, p0[1] - ny * r0)]
    web = cq.Workplane("XY", origin=(0, 0, z0)).polyline(pts).close().extrude(z1 - z0).val()
    return a.fuse(b).fuse(web).clean()


def rod_between(p, q, r):
    v = cq.Vector(q[0] - p[0], q[1] - p[1], q[2] - p[2])
    return cq.Solid.makeCylinder(r, v.Length, cq.Vector(*p), v.normalized())


# ------------------------------------------------------------------ parts (name, solid, colour, group)
def hub():
    H = HUB
    body = ring_x(H["shell_r"][0], H["shell_r"][1], *H["shell_x"])
    body = body.fuse(ring_x(H["rear"]["r"][0], H["rear"]["r"][1], *H["rear"]["x"]))
    body = body.fuse(ring_x(H["front"]["r"][0], H["front"]["r"][1], *H["front"]["x"]))
    for a in BLADES:
        neck = zcyl(H["neck_r"][1], H["neck_s"][0], H["neck_s"][1])
        fl = zcyl(H["flange"]["r"][1], *H["flange"]["s"])
        body = body.fuse(blade_axis(neck.fuse(fl), a))
    body = body.cut(xcyl(H["shell_r"][0], H["shell_x"][0] + 0.01, H["shell_x"][1] - 0.01))
    for a in BLADES:
        bore = zcyl(H["neck_r"][0], 150.0, H["neck_s"][1] + 1).fuse(zcyl(H["flange"]["r"][0], H["neck_s"][1] - 1,
                                                                        H["flange"]["s"][1] + 1))
        for k in range(16):
            q = math.radians(11.25 + 22.5 * k)
            bore = bore.fuse(zcyl(7.0, H["flange"]["s"][1] - 22, H["flange"]["s"][1] + 1, 150 * math.cos(q), 150 * math.sin(q)))
        body = body.cut(blade_axis(bore, a))
    # gussets: triangular 10 mm plates front and rear of each neck, in the plane of rotor and pitch axes
    for a in BLADES:
        for sx in (-1, 1):
            pts = [(sx * 162.0, 222.0), (sx * 215.0, 222.0), (sx * 162.0, 318.0)]
            g = cq.Workplane("XZ", origin=(0, 5.0, 0)).polyline(pts).close().extrude(10.0).val()
            body = body.fuse(blade_axis(g, a))
    body = holes_x(body, 12, 400.0, 17.0, H["rear"]["x"][0] - 1, H["rear"]["x"][1] + 1, start=15.0)
    body = holes_x(body, 12, 340.0, 13.0, H["front"]["x"][0] - 1, H["front"]["x"][1] + 1, start=15.0)
    return body.clean()


def pitch_bearing(a):
    O, I = PB["outer"], PB["inner"]
    outer = holes_z(ring_z(O["r"][0], O["r"][1], *O["s"]), 16, 300.0, 17.0, O["s"][0] - 1, O["s"][1] + 1, 11.25)
    inner = holes_z(ring_z(I["r"][0], I["r"][1], *I["s"]), 10, 200.0, 17.0, I["s"][0] - 1, I["s"][1] + 1, 18.0)
    return blade_axis(outer, a), blade_axis(inner, a)


STUB = 260.0


def blade_root(a, theta):
    s0 = PB["inner"]["s"][1]
    b = ring_z(90.0, 110.0, s0, s0 + STUB)
    # pitch mark: a flat strip on the leading edge side, turned with the blade
    mark = cq.Solid.makeBox(8, 6, STUB - 10, cq.Vector(-4, -113, s0 + 5))
    b = b.fuse(mark).rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), theta)
    return blade_axis(b, a)


def crank(a, theta):
    C = CRANK
    p = K.pin(theta)                                   # (x, s, y) blade frame of collective.py
    px, py = p[0], p[2]
    fl = holes_z(ring_z(C["flange"]["r"][0], C["flange"]["r"][1], *C["flange"]["s"]), 10, 200.0, 17.0,
                 C["flange"]["s"][0] - 1, C["flange"]["s"][1] + 1, 18.0 + theta - TH0)
    tube = ring_z(C["tube"]["r"][0], C["tube"]["r"][1], *C["tube"]["s"])
    lever = stadium((0.0, 0.0), 84.0, (px, py), 28.0, *C["lever"]["s"])
    lever = lever.cut(zcyl(62.0, C["lever"]["s"][0] - 1, C["lever"]["s"][1] + 1))      # open centre (cables, light)
    pinb = zcyl(C["pin_r"], K.S_P - 30.0, C["lever"]["s"][1] + 5.0, px, py)       # eye sits on the pin below the lever
    return blade_axis(fl.fuse(tube).fuse(lever).clean(), a), blade_axis(pinb, a)


TH0 = 0.0


def link(a, theta):
    p = K.pin(theta)
    _, e = K.yoke_x(theta)
    P = (p[0], p[2], p[1])                             # -> (x, y, s) local cadquery
    E = (e[0], e[2], e[1])
    d0 = tuple(E[i] - P[i] for i in range(3))
    L0 = math.sqrt(sum(c * c for c in d0))
    u0 = tuple(c / L0 for c in d0)
    rod = rod_between(tuple(P[i] + u0[i] * 20 for i in range(3)), tuple(E[i] - u0[i] * 20 for i in range(3)), 15.0)
    eyes = cq.Solid.makeSphere(21.0, cq.Vector(*P)).fuse(cq.Solid.makeSphere(21.0, cq.Vector(*E)))
    # turnbuckle sleeve in the middle
    m = tuple((P[i] + E[i]) / 2 for i in range(3))
    d = tuple(E[i] - P[i] for i in range(3))
    L = math.sqrt(sum(c * c for c in d))
    u = tuple(c / L for c in d)
    q0 = tuple(m[i] - u[i] * 35 for i in range(3))
    q1 = tuple(m[i] + u[i] * 35 for i in range(3))
    tb = rod_between(q0, q1, 21.0)
    return blade_axis(rod.fuse(tb), a), blade_axis(eyes, a)


def yoke(theta):
    xy, e = K.yoke_x(theta)
    body = xcyl(48.0, xy - YOKE_T / 2 - 15, xy + YOKE_T / 2 + 15)
    for a in BLADES:
        arm = stadium((0.0, 0.0), 45.0, (e[2], e[1]), 26.0, 0.0, YOKE_T)     # local (y, s) in XY, thickness along Z
        # (X, Y, Z) -> (x = Z, y = X, z = Y): rotate -90 about Y then -90 about X
        arm = arm.rotate(cq.Vector(0, 0, 0), cq.Vector(1, 1, 1), 120.0)
        arm = arm.translate(cq.Vector(xy - YOKE_T / 2, 0, 0))
        slot = cq.Solid.makeSphere(26.0, cq.Vector(xy, e[2], e[1]))
        body = body.fuse(blade_axis(arm, a)).cut(blade_axis(slot, a))
    for ang in GUIDE_ANG:
        y, z = 75.0 * math.cos(math.radians(ang)), 75.0 * math.sin(math.radians(ang))
        body = body.fuse(xcyl(22.0, xy - 30, xy + 30, y, z)).cut(xcyl(12.6, xy - 31, xy + 31, y, z))
    return body.clean()


def guide_angles():
    _, e = K.yoke_x(K.TH_MID)
    offs = math.degrees(math.atan2(e[1], e[2])) - 90.0           # arm angle relative to the blade direction
    arms = sorted(((a + offs + 90.0) % 360.0) for a in BLADES)
    arms = [math.degrees(math.atan2(math.sin(math.radians(a - 90 + 90)), math.cos(math.radians(a)))) for a in arms]
    return (150.0 + offs, 330.0 + offs)


GUIDE_ANG = guide_angles()


def guide_rods():
    out = None
    for ang in GUIDE_ANG:
        y, z = 75.0 * math.cos(math.radians(ang)), 75.0 * math.sin(math.radians(ang))
        r = xcyl(12.5, -735.0, -105.0, y, z)
        out = r if out is None else out.fuse(r)
    return out


def actuator(theta):
    xy, _ = K.yoke_x(theta)
    body = xcyl(45.0, -705.0, -335.0).fuse(xcyl(52.0, -715.0, -690.0)).fuse(xcyl(52.0, -350.0, -335.0))
    rod = xcyl(16.0, -335.0, xy - YOKE_T / 2 - 15)
    motor = xcyl(40.0, -690.0, -520.0, 0.0, 100.0)
    belt = cq.Solid.makeBox(28.0, 90.0, 190.0, cq.Vector(-718.0, -45.0, -40.0))
    return body.fuse(belt).clean(), rod, motor


def electronics():
    sc = cq.Solid.makeBox(230.0, 100.0, 62.0, cq.Vector(-690.0, -50.0, -112.0))
    drv = cq.Solid.makeBox(110.0, 90.0, 45.0, cq.Vector(-460.0, -45.0, -97.0))
    return sc, drv


def nose_housing():
    """Al 6082 frame: front ring, rear flange ring on the hub front plate, 4 longerons, cylinder mounts."""
    fr = ring_x(80.0, 128.0, -775.0, -760.0)
    rr = ring_x(158.0, 190.0, -266.0, -252.0)
    rr = holes_x(rr, 12, 340.0, 13.0, -267.0, -251.0, start=15.0) if False else rr
    body = fr.fuse(rr)
    for k in range(4):
        ang = 45.0 + 90.0 * k
        y0, z0 = 172.0 * math.cos(math.radians(ang)), 172.0 * math.sin(math.radians(ang))
        y1, z1 = 105.0 * math.cos(math.radians(ang)), 105.0 * math.sin(math.radians(ang))
        body = body.fuse(rod_between((-262.0, y0, z0), (-768.0, y1, z1), 9.0))
    mount = ring_x(46.0, 80.0, -716.0, -700.0).fuse(ring_x(46.0, 76.0, -350.0, -338.0))
    for k in range(4):
        ang = 45.0 + 90.0 * k
        y0, z0 = 75.0 * math.cos(math.radians(ang)), 75.0 * math.sin(math.radians(ang))
        y1, z1 = 110.0 * math.cos(math.radians(ang)), 110.0 * math.sin(math.radians(ang))
        body = body.fuse(rod_between((-344.0, y0, z0), (-344.0, y1, z1), 7.0))
    return body.fuse(mount).clean()


def context():
    """Stationary and generator context: spindle nose, slip ring, drum front (Rev C geometry)."""
    sr = xcyl(50.0, -80.0, 38.0)
    out = dict(slip_ring=sr)
    try:
        drum = None
        for pts in G.DRUM_PARTS.values():
            s = revolve([(x, r) for x, r in pts])
            drum = s if drum is None else drum.fuse(s)
        out["drum"] = drum
    except Exception:
        pass
    return out


COL = dict(hub="#8d949e", flange="#8d949e", bearing_o="#c9a13b", bearing_i="#dcb95a", blade="#ece6d6",
           crank="#3a6ea5", pin="#c0c4ca", link="#2f5d8c", eye="#d0d4da", yoke="#4f86c0", rods="#b8bcc2",
           act="#5b6f86", rod="#d6dade", motor="#33475e", sc="#4f9a5a", drv="#6aa86e", nose="#a9b7c6",
           slip="#57a05f", drum="#b9bec6")


def assembly(theta=K.TH_FINE, blades=BLADES, with_hub=True, with_nose=True, with_context=True):
    """List of (name, solid, colour)."""
    P = []
    if with_hub:
        P.append(("hub", hub(), COL["hub"]))
    for a in blades:
        o, i = pitch_bearing(a)
        P += [(f"bearing_outer_{a:.0f}", o, COL["bearing_o"]), (f"bearing_inner_{a:.0f}", i, COL["bearing_i"])]
        P.append((f"blade_root_{a:.0f}", blade_root(a, theta), COL["blade"]))
        c, pn = crank(a, theta)
        P += [(f"crank_{a:.0f}", c, COL["crank"]), (f"pin_{a:.0f}", pn, COL["pin"])]
        l, ey = link(a, theta)
        P += [(f"link_{a:.0f}", l, COL["link"]), (f"eyes_{a:.0f}", ey, COL["eye"])]
    P.append(("yoke", yoke(theta), COL["yoke"]))
    P.append(("guide_rods", guide_rods(), COL["rods"]))
    b, r, m = actuator(theta)
    P += [("cylinder", b, COL["act"]), ("cylinder_rod", r, COL["rod"]), ("motor", m, COL["motor"])]
    sc, drv = electronics()
    P += [("supercap", sc, COL["sc"]), ("drive", drv, COL["drv"])]
    if with_nose:
        P.append(("nose_housing", nose_housing(), COL["nose"]))
    if with_context:
        for k, v in context().items():
            P.append((k, v, COL["slip"] if k == "slip_ring" else COL["drum"]))
    return P


if __name__ == "__main__":
    for n, s, c in assembly():
        print(n, round(s.Volume() / 1e6, 3), "L", s.isValid())
