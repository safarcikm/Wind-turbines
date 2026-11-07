"""M8 hub and collective pitch (doc 37 §5): the doc 24 model (cad/hub_c/model.py) with the M8 sizes.

Spindle frame as in hub_c: x rearward along the rotor axis from the blade plane, z up, blade 1 up.
Sizes from analysis/variant_m8/hub_yaw_m8.py (doc 35 §5):
  * welded hub shell Ø530 x 10, necks Ø360 x 10, rear flange to the drum unchanged (12 x M16 PCD 400, Ø360 spigot);
  * pitch bearings Dpw 300, balls 30 mm (outer ring r 152.5-205, inner r 110-147.5, 55 mm high);
  * blade root Ø280 (12 x M16 PCD 245 into the inner ring);
  * crank r 140, link eye plane S_P 150 mm from the rotor axis (doc 24: 118), yoke eye R_Y 140 (doc 24: 110),
    link 220 mm, phase 5 deg. Moving the pin plane out to 150 puts the pin (r 15) outside the drum bearing
    housing (r <= 120), so the 140 mm crank does not need the phase shift that would raise the cylinder force.
"""
from __future__ import annotations
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "hub_c"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "analysis", "hub"))
import collective as K  # noqa: E402

K.R_C, K.S_P, K.R_Y, K.L_LINK, K.PHI0 = 140.0, 150.0, 140.0, 220.0, 5.0
K.BETA = K.yoke_eye_angle()

import model as M  # noqa: E402

M.HUB = dict(shell_r=(255.0, 265.0), shell_x=(-276.0, 175.0), rear=dict(x=(175.0, 200.0), r=(170.0, 265.0)),
             front=dict(x=(-288.0, -276.0), r=(190.0, 265.0)), neck_r=(170.0, 180.0), neck_s=(215.0, 360.0),
             flange=dict(s=(360.0, 385.0), r=(156.0, 215.0)))
M.PB = dict(outer=dict(s=(385.0, 440.0), r=(152.5, 205.0)), inner=dict(s=(387.0, 442.0), r=(110.0, 147.5)))
M.CRANK = dict(flange=dict(s=(372.0, 387.0), r=(100.0, 145.0)), tube=dict(s=(196.0, 372.0), r=(100.0, 105.0)),
               lever=dict(s=(176.0, 196.0)), pin_r=15.0)
M.NOSE_X = (-856.0, -288.0)
DX = -50.0   # cylinder, motor, electronics and nose front 50 mm further forward: the yoke reaches x -325 at feather
M.STUB = 300.0
M.GUIDE_ANG = M.guide_angles()

_orig_blade_root = M.blade_root


def blade_root(a, theta):
    """Ø280 root cylinder (wall 20) on the inner ring."""
    import cadquery as cq
    s0 = M.PB["inner"]["s"][1]
    b = M.ring_z(120.0, 140.0, s0, s0 + M.STUB)
    mark = cq.Solid.makeBox(8, 6, M.STUB - 10, cq.Vector(-4, -143, s0 + 5))
    b = b.fuse(mark).rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), theta)
    return M.blade_axis(b, a)


M.blade_root = blade_root
_orig_hub = M.hub


def hub():
    """Doc 24 hub construction with the M8 dimensions (gussets scaled to the larger shell and necks)."""
    import cadquery as cq
    H = M.HUB
    body = M.ring_x(H["shell_r"][0], H["shell_r"][1], *H["shell_x"])
    body = body.fuse(M.ring_x(H["rear"]["r"][0], H["rear"]["r"][1], *H["rear"]["x"]))
    body = body.fuse(M.ring_x(H["front"]["r"][0], H["front"]["r"][1], *H["front"]["x"]))
    for a in M.BLADES:
        neck = M.zcyl(H["neck_r"][1], H["neck_s"][0], H["neck_s"][1])
        fl = M.zcyl(H["flange"]["r"][1], *H["flange"]["s"])
        body = body.fuse(M.blade_axis(neck.fuse(fl), a))
    body = body.cut(M.xcyl(H["shell_r"][0], H["shell_x"][0] + 0.01, H["shell_x"][1] - 0.01))
    for a in M.BLADES:
        bore = M.zcyl(H["neck_r"][0], 150.0, H["neck_s"][1] + 1).fuse(M.zcyl(H["flange"]["r"][0], H["neck_s"][1] - 1,
                                                                                H["flange"]["s"][1] + 1))
        for k in range(20):
            q = math.radians(9.0 + 18.0 * k)
            bore = bore.fuse(M.zcyl(7.0, H["flange"]["s"][1] - 22, H["flange"]["s"][1] + 1, 180 * math.cos(q), 180 * math.sin(q)))
        body = body.cut(M.blade_axis(bore, a))
    for a in M.BLADES:
        for sx in (-1, 1):
            # front gusset 68 long; the rear one stops on the drum flange ring (x 200) so it clears the drum web
            pts = ([(-177.0, 257.0), (-245.0, 257.0), (-177.0, 352.0)] if sx < 0 else
                   [(177.0, 257.0), (199.0, 257.0), (199.0, 300.0), (177.0, 352.0)])
            g = cq.Workplane("XZ", origin=(0, 5.0, 0)).polyline(pts).close().extrude(10.0).val()
            body = body.fuse(M.blade_axis(g, a))
    body = M.holes_x(body, 12, 400.0, 17.0, H["rear"]["x"][0] - 1, H["rear"]["x"][1] + 1, start=15.0)
    body = M.holes_x(body, 12, 450.0, 13.0, H["front"]["x"][0] - 1, H["front"]["x"][1] + 1, start=15.0)
    body = body.cut(M.xcyl(180.5, 194.0, 201.0))        # Ø361 H7 x 5 recess for the drum's Ø360 f7 spigot
    return body.clean()


M.hub = hub


def pitch_bearing(a):
    O, I = M.PB["outer"], M.PB["inner"]
    outer = M.holes_z(M.ring_z(O["r"][0], O["r"][1], *O["s"]), 20, 360.0, 17.0, O["s"][0] - 1, O["s"][1] + 1, 9.0)
    inner = M.holes_z(M.ring_z(I["r"][0], I["r"][1], *I["s"]), 12, 245.0, 17.0, I["s"][0] - 1, I["s"][1] + 1, 15.0)
    return M.blade_axis(outer, a), M.blade_axis(inner, a)


M.pitch_bearing = pitch_bearing


def nose_housing():
    """Doc 24 nose frame stretched forward by 36 mm with the larger shell (front ring and rear ring as before)."""
    return M.nose_housing.__wrapped__() if hasattr(M.nose_housing, "__wrapped__") else _nose()


def _nose():
    """Doc 24 nose frame: rear ring on the Ø380 front opening (12 x M12 PCD 450), front ring 50 mm further forward."""
    fr = M.ring_x(80.0, 128.0, -861.0, -846.0)
    rr = M.ring_x(200.0, 245.0, -302.0, -288.0)
    body = fr.fuse(rr)
    for k in range(4):
        ang = 45.0 + 90.0 * k
        y0, z0 = 222.0 * math.cos(math.radians(ang)), 222.0 * math.sin(math.radians(ang))
        y1, z1 = 105.0 * math.cos(math.radians(ang)), 105.0 * math.sin(math.radians(ang))
        body = body.fuse(M.rod_between((-298.0, y0, z0), (-854.0, y1, z1), 9.0))
    mount = M.ring_x(46.0, 80.0, -766.0, -750.0).fuse(M.ring_x(46.0, 76.0, -400.0, -388.0))
    for k in range(4):
        ang = 45.0 + 90.0 * k
        for xm in (-394.0, -758.0):
            y0, z0 = 75.0 * math.cos(math.radians(ang)), 75.0 * math.sin(math.radians(ang))
            r1 = 105.0 + (222.0 - 105.0) * (xm + 854.0) / (854.0 - 298.0)
            y1, z1 = r1 * math.cos(math.radians(ang)), r1 * math.sin(math.radians(ang))
            body = body.fuse(M.rod_between((xm, y0, z0), (xm, y1, z1), 7.0))
    return body.fuse(mount).clean()


def actuator(theta):
    import cadquery as cq
    xy, _ = K.yoke_x(theta)
    body = M.xcyl(45.0, -755.0, -385.0).fuse(M.xcyl(52.0, -765.0, -740.0)).fuse(M.xcyl(52.0, -400.0, -385.0))
    rod = M.xcyl(16.0, -385.0, xy - M.YOKE_T / 2 - 15)
    motor = M.xcyl(40.0, -740.0, -570.0, 0.0, 100.0)
    belt = cq.Solid.makeBox(28.0, 90.0, 190.0, cq.Vector(-768.0, -45.0, -40.0))
    return body.fuse(belt).clean(), rod, motor


def electronics():
    import cadquery as cq
    sc = cq.Solid.makeBox(230.0, 100.0, 62.0, cq.Vector(-740.0, -50.0, -112.0))
    drv = cq.Solid.makeBox(110.0, 90.0, 45.0, cq.Vector(-510.0, -45.0, -97.0))
    return sc, drv


def guide_rods():
    out = None
    for ang in M.GUIDE_ANG:
        y, z = 75.0 * math.cos(math.radians(ang)), 75.0 * math.sin(math.radians(ang))
        r = M.xcyl(12.5, -785.0, -105.0, y, z)
        out = r if out is None else out.fuse(r)
    return out


M.actuator, M.electronics, M.guide_rods = actuator, electronics, guide_rods
M.nose_housing = _nose

assembly = M.assembly
TH_FINE, TH_FEATHER = K.TH_FINE, K.TH_FEATHER

if __name__ == "__main__":
    for n, s, c in assembly():
        print(n, round(s.Volume() / 1e6, 3), "L", s.isValid())
