"""S6 6 kW turbine on the 8 m tower: 3D model of every part (doc 34 build book).

    python3 model6.py            -> prints the part list with CAD masses, writes out/model6-parts.json
    import model6; parts = model6.build()   (list of Part, WORLD frame)

WORLD frame (same as cad/nacelle_fitcheck and cad/yaw): X rearward (downwind), Y lateral (left
seen from upwind = +Y), Z up, origin on the yaw axis at the bedplate underside (= yaw bearing top face).
The rotor centre is at X -750, Z 570; the ground is at Z = -7430 (hub height 8.000 m).

Reused 12 kW parts come from their own models unchanged (cad/nacelle_fitcheck/parts.py: spindle, bearings,
generator, disc, caliper bracket, lock; cad/yaw/model.py: yaw ring, adapter, pads, drives, lock, encoder,
hanger). New S6 parts are built here from the doc 30-34 results: blades, root inserts, blade mould set,
hub, spinner, pitch-setting parts, NS6-300 bedplate, nacelle cover and frame, met mast, junction box,
tower 8 m, base hinge, gin pole, foundation with anchor cage, tower base cabinet and resistor box.
"""
from __future__ import annotations

import io
import json
import contextlib
import math
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

import cadquery as cq
import numpy as np

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "cad" / "nacelle_fitcheck"))
sys.path.insert(0, str(ROOT / "cad" / "yaw"))
sys.path.insert(0, str(ROOT / "analysis" / "turbine_6kw"))
import parts as FP  # noqa: E402
import importlib.util  # noqa: E402
with contextlib.redirect_stdout(io.StringIO()):
    _argv = sys.argv; sys.argv = sys.argv[:1]
    import design6 as D6M  # noqa: E402   (its 'model' module is analysis/size_tsr_map/model.py)
    sys.argv = _argv
_spec = importlib.util.spec_from_file_location("yaw_model", ROOT / "cad" / "yaw" / "model.py")
YM = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(YM)
G = FP.G

RES = ROOT / "analysis" / "turbine_6kw" / "results"
D6 = json.loads((RES / "design6.json").read_text())
BPJ = json.loads((RES / "bedplate6.json").read_text())["NS6-300 (6 kW)"]
BPI = BPJ["inputs"]
T8 = json.loads((RES / "tower8.json").read_text())
TW8 = T8["towers"]["stiff"]

STEEL, ALU, GRP, CONC = 7.85e-6, 2.70e-6, 1.85e-6, 2.40e-6     # kg/mm3
RC = FP.RC                       # rotor centre (X, Y, Z)
TILT = FP.TILT
R_ROT = 3000.0
R_ROOT = 280.0                   # blade root face radius
PITCH_SET = -2.0                 # deg, standard blade setting
Z_TOP_FLANGE = -360.0            # tower top flange top face
HUB_H = T8["hub_height_m"] * 1000.0
Z_GROUND = RC[2] - HUB_H         # -7430
Z_BASE = Z_GROUND + T8["z_pedestal_m"] * 1000.0     # base flange underside (pedestal + grout top)
L_TUBE = Z_TOP_FLANGE - Z_BASE   # 6870 incl. flanges
TG = TW8["tower"]["geometry"]
D_BASE, D_TOP = TG["D_base"] * 1000.0, TG["D_top"] * 1000.0
T_WALL = TG["t_mm"][0]
BLADE_ANGLES = (90.0, 210.0, 330.0)     # azimuth in the rotor plane, from +Y towards +Z (blade 1 up)


@dataclass
class Part:
    pid: str                 # drawing number (+ suffix)
    name: str
    solid: cq.Shape
    group: str               # rotor / drivetrain / nacelle / yaw / tower / foundation / electrical / tooling
    color: str
    drawing: str
    material: str = ""
    make_buy: str = "make"
    qty: int = 1
    rho: float | None = STEEL
    mass_kg: float | None = None       # overrides rho x volume (bought parts, GRP lay-ups)
    notes: list = field(default_factory=list)
    show: bool = True                  # in the assembled turbine
    step: int = 0                      # assembly step that installs it

    def mass(self):
        if self.mass_kg is not None:
            return self.mass_kg
        if self.rho is None:
            return None
        return self.solid.Volume() * self.rho


# ------------------------------------------------------------------ helpers
box = FP.box
cyl_x = FP.cyl_x
to_world = FP.to_world


def cyl(r, h, base, d=(0, 0, 1)):
    return cq.Solid.makeCylinder(r, h, cq.Vector(*base), cq.Vector(*d))


def revolve_x(poly):
    return FP.revolve(poly)


def revolve_z(poly):
    return cq.Workplane("XZ").polyline(poly).close().revolve(360, (0, 0, 0), (0, 1, 0)).val()


def rot_x(s, a):                 # about the spindle axis (x) in the spindle frame
    return s.rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), a)


def rot_z(s, a, c=(0, 0, 0)):
    return s.rotate(cq.Vector(*c), cq.Vector(c[0], c[1], c[2] + 1), a)


def zholes(solid, n, pcd, dia, z0, z1, start=0.0, c=(0.0, 0.0)):
    for k in range(n):
        a = math.radians(start + 360.0 * k / n)
        solid = solid.cut(cyl(dia / 2, z1 - z0, (c[0] + pcd / 2 * math.cos(a), c[1] + pcd / 2 * math.sin(a), z0)))
    return solid


def rrect_wire(x, yh, z0, z1, r):
    """Rounded rectangle in the plane X = x: Y in [-yh, yh], Z in [z0, z1], corner radius r."""
    wp = cq.Workplane("YZ", origin=(x, 0, (z0 + z1) / 2)).rect(2 * yh, z1 - z0)
    w = wp.val()
    f = cq.Face.makeFromWires(w)
    f = f.fillet2D(r, f.Vertices())
    return f.outerWire()


# ================================================================== ROTOR
def blade_shape():
    b = D6M.blade_shape(n=40)
    st = D6["blade_stations"]
    r = np.array(st["r"]) * 1000.0
    c = np.array(st["chord"]) * 1000.0
    tc = np.array(st["t_over_c"])
    tw = np.interp(r, np.array(b.r) * 1000.0, np.array(b.twist + b.twist_tip_offset))
    return r, c, tc, tw


def airfoil_pts(chord, tc, n=36, camber=0.035):
    """Closed section (x chordwise from the pitch axis at 30 % c, y thickness), NACA-like with camber;
    blended to a circle of diameter = chord for t/c -> 1 (root)."""
    beta = np.linspace(0, math.pi, n)
    xc = 0.5 * (1 - np.cos(beta))
    t = min(tc, 1.0)
    yt = 5 * t * (0.2969 * np.sqrt(xc) - 0.1260 * xc - 0.3516 * xc ** 2 + 0.2843 * xc ** 3 - 0.1036 * xc ** 4)
    p = 0.4
    yc = np.where(xc < p, camber / p ** 2 * (2 * p * xc - xc ** 2), camber / (1 - p) ** 2 * ((1 - 2 * p) + 2 * p * xc - xc ** 2))
    up = np.stack([xc, yc + yt], 1)
    lo = np.stack([xc, yc - yt], 1)
    pts = np.vstack([up[::-1], lo[1:-1]])            # TE -> LE (upper) -> TE (lower), open TE handled by the loft
    pts = (pts - [0.3, 0.0]) * chord
    # circle blend
    w = float(np.clip((tc - 0.40) / 0.55, 0, 1))
    if w > 0:
        ang = np.linspace(0, 2 * math.pi, len(pts), endpoint=False)
        rr = chord / 2
        circ = np.stack([rr * np.cos(ang) * -1 + 0.2 * chord * 0, rr * np.sin(ang)], 1)
        # orient the circle like the aerofoil list (start at TE = +x, go over the top)
        circ = np.stack([rr * np.cos(ang), rr * np.sin(ang)], 1)
        pts = (1 - w) * pts + w * circ
    return pts


def blade_solid(local=False):
    """Blade in its local frame: span along +Z (radius, root face at Z = R_ROOT), chord along X
    (leading edge towards -X), thickness along Y (suction side +Y = upwind). Twist + pitch about Z."""
    r, c, tc, tw = blade_shape()
    rs = [280.0, 300.0, 340.0, 400.0, 480.0, 560.0, 640.0, 760.0, 900.0, 1100.0, 1350.0, 1600.0, 1900.0, 2200.0, 2500.0, 2750.0, 2950.0, 3000.0]
    wires = []
    for x in rs:
        cc = float(np.interp(x, r, c)); t = float(np.interp(x, r, tc)); th = float(np.interp(x, r, tw)) + PITCH_SET
        if x <= 300:
            cc, t = 220.0, 1.0
        pts = airfoil_pts(cc, t)
        a = math.radians(th)
        P = [(-(px * math.cos(a) - py * math.sin(a)), px * math.sin(a) + py * math.cos(a), x) for px, py in pts]
        P = [cq.Vector(*p) for p in P]
        wires.append(cq.Wire.makePolygon(P + [P[0]]) if False else cq.Wire.assembleEdges([cq.Edge.makeSpline(P + [P[0]], periodic=False)]))
    sol = cq.Solid.makeLoft(wires, False)
    # hollow root (bonded insert ring zone) and the root face
    sol = sol.cut(cyl(75.0, 160.0, (0, 0, R_ROOT - 1)))
    return sol


def insert_solid():
    """NS6-105 root insert: steel sleeve Ø24 x 110 with M12 internal thread 30 deep, 6 grooves."""
    p = [(0, 6.0), (0, 12.0)]
    x = 0.0
    for k in range(6):
        p += [(x + 8, 12.0), (x + 8, 10.5), (x + 13, 10.5), (x + 13, 12.0)]
        x += 13
    p += [(110, 12.0), (110, 0.0), (30, 0.0), (30, 5.1), (0, 5.1)]
    p = [(0.0, 5.1), (0.0, 12.0)] + p[2:-1]
    s = revolve_x([(px, pr) for px, pr in p])
    return s


def blade_place(s, a, x_axis=0.0):
    """Local blade frame -> spindle frame at azimuth a (blade span along the radial direction at a)."""
    # local: span +Z, chord X, thickness Y (upwind). spindle frame: x rearward (downwind), radial in y-z.
    # map local (X, Y, Z) -> spindle (x = -Y, tangential = -X, radial = Z) at azimuth 90 (blade up: radial = +z, tangential = -y)
    s = s.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), 90.0)      # X->Y, Y->-X: chord now along Y, thickness along -X
    s = s.translate(cq.Vector(x_axis, 0, 0))
    return rot_x(s, a - 90.0)


def rotor_parts():
    out = []
    bl = blade_solid()
    ins = insert_solid()
    m_blade = D6["blade"]["glass"]["mass_kg"]
    for i, a in enumerate(BLADE_ANGLES, 1):
        out.append(Part(f"NS6-100-{i}", f"Blade {i} (glass/epoxy, glass UD caps)", to_world(blade_place(bl, a)), "rotor", "#e9e6dc",
                        "NS6-100", "E-glass/epoxy, PVC core", qty=1, mass_kg=m_blade, step=9,
                        notes=["one mould for all three; static-moment matched set"]))
    # inserts of blade 1 only drawn as separate solids (the other blades carry them too)
    pcd = 185.0
    ins_all = None
    for k in range(10):
        ang = 18.0 + 36.0 * k
        s = ins.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 1, 0), -90.0)      # axis +x -> +z (span)
        s = s.translate(cq.Vector(pcd / 2 * math.cos(math.radians(ang)), pcd / 2 * math.sin(math.radians(ang)), R_ROOT))
        ins_all = s if ins_all is None else ins_all.fuse(s)
    out.append(Part("NS6-105", "Root insert M12 (10 per blade, bonded)", to_world(blade_place(ins_all, BLADE_ANGLES[0])), "rotor", "#9aa3ab",
                    "NS6-105", "C45E+QT zinc-flake coated", qty=30, mass_kg=0.33 * 30, step=0, notes=["shown on blade 1"]))
    return out


# ------------------------------------------------------------------ hub NS6-200 (spindle frame, x rearward, rotor plane x = 0)
HUB = dict(shell=(-125.0, 170.0, 178.0, 190.0), front=(-125.0, -115.0), flange=(170.0, 200.0, 180.1, 240.0),
           arm_d=220.0, arm_t=8.0, arm_r=(150.0, 255.0), root=(255.0, 280.0, 75.0, 140.0), root_pcd=185.0)


def arm_axis(s, a):
    """Solid built along +z (radial) at azimuth 90 -> azimuth a."""
    return rot_x(s, a - 90.0)


def hub_solid():
    H = HUB
    x0, x1, ri, ro = H["shell"]
    s = revolve_x([(x0, ri), (x1, ri), (x1, ro), (x0, ro)])
    s = s.fuse(revolve_x([(H["front"][0], 50.0), (H["front"][1], 50.0), (H["front"][1], ro), (H["front"][0], ro)]))
    fx0, fx1, fri, fro = H["flange"]
    fl = revolve_x([(fx0, fri), (fx1, fri), (fx1, fro), (fx0, fro)])
    fl = FP.bolt_holes(fl, 12, 400.0, 17.5, fx0 - 1, fx1 + 1, start=15.0)
    s = s.fuse(fl)
    ro_a, ri_a = H["arm_d"] / 2, H["arm_d"] / 2 - H["arm_t"]
    rf0, rf1, rfi, rfo = H["root"]
    for a in BLADE_ANGLES:
        tube = cyl(ro_a, H["arm_r"][1] - H["arm_r"][0], (0, 0, H["arm_r"][0]))
        fl = cyl(rfo, rf1 - rf0, (0, 0, rf0)).cut(cyl(rfi, 40, (0, 0, rf0 - 5)))
        for k in range(10):                       # arc slots ±2.5° for the M12 studs (pitch setting)
            for dd in np.linspace(-2.5, 2.5, 6):
                ang = math.radians(18.0 + 36.0 * k + dd)
                fl = fl.cut(cyl(6.75, 40, (H["root_pcd"] / 2 * math.cos(ang), H["root_pcd"] / 2 * math.sin(ang), rf0 - 5)))
        s = s.fuse(arm_axis(tube, a)).fuse(arm_axis(fl, a))
    s = s.clean()
    for a in BLADE_ANGLES:
        s = s.cut(arm_axis(cyl(ri_a, H["arm_r"][1] - 120 + 10, (0, 0, 120.0)), a))
    s = s.cut(revolve_x([(x0 + 10, 0), (x1 + 40, 0), (x1 + 40, ri), (x0 + 10, ri)]))
    s = s.cut(revolve_x([(fx0 - 1, 0), (fx1 + 1, 0), (fx1 + 1, fri), (fx0 - 1, fri)]))
    # spinner bracket bosses
    return s


def spinner_solid():
    """NS6-210 GRP spinner, 4 mm, ogive from the nose (x -470) to the base ring (x 195, r 335)."""
    prof = []
    for k in range(25):
        f = k / 24
        x = -470.0 + 665.0 * f
        r = 335.0 * math.sqrt(max(0.0, 1 - (1 - f) ** 2)) if f < 1 else 335.0
        r = max(r, 0.5) if k else 0.0
        prof.append((x, r))
    outer = prof
    inner = [(x + 4 * 0.7, max(rr - 4, 0)) for x, rr in prof]
    poly = outer + [(195.0, 331.0)] + inner[::-1]
    poly = [(x, rr) for x, rr in outer] + [(195.0, 331.0)] + [(x, rr) for x, rr in inner[::-1] if rr > 0] + [(-466.0, 0.0)]
    s = revolve_x(poly)
    for a in BLADE_ANGLES:
        s = s.cut(arm_axis(cyl(122.0, 400, (0, 0, 150.0)), a))
    return s


def spinner_brackets():
    out = None
    for a in BLADE_ANGLES:
        for dz in (-60.0,):
            b = box(-110.0, -70.0, -40.0, 40.0, 0, 6).translate(cq.Vector(0, 0, 0))
            # angle bracket from the front plate edge to the spinner wall, at azimuth a + 60
            b = box(-125.0, -115.0, -30.0, 30.0, 150.0, 262.0)
            b = b.fuse(box(-175.0, -115.0, -30.0, 30.0, 256.0, 262.0))
            b = rot_x(b, a + 60.0 - 90.0)
            out = b if out is None else out.fuse(b)
    return out


def pitch_parts():
    """NS6-130 thick washers (bridge the root-flange slots), NS6-135 pitch gauge (tool)."""
    w = None
    for k in range(10):
        ang = math.radians(18.0 + 36.0 * k)
        c = cyl(14.0, 4.0, (HUB["root_pcd"] / 2 * math.cos(ang), HUB["root_pcd"] / 2 * math.sin(ang), HUB["root"][0] - 4.0))
        c = c.cut(cyl(6.5, 10, (HUB["root_pcd"] / 2 * math.cos(ang), HUB["root_pcd"] / 2 * math.sin(ang), HUB["root"][0] - 6.0)))
        w = c if w is None else w.fuse(c)
    gauge = box(-260.0, 260.0, -20.0, 20.0, 1990.0, 2010.0).fuse(box(-20.0, 20.0, -60.0, -20.0, 1990.0, 2010.0))
    gauge = gauge.fuse(box(-60.0, 60.0, 20.0, 60.0, 1985.0, 2015.0))      # inclinometer seat
    return w, gauge


def hub_parts():
    out = []
    out.append(Part("NS6-200", "Fixed hub weldment", to_world(hub_solid()), "rotor", "#6f7f8f", "NS6-200",
                    "S355NL, welded, stress relieved, machined", step=8))
    out.append(Part("NS6-210", "Spinner (GRP, 4 mm)", to_world(spinner_solid()), "rotor", "#f2f2ee", "NS6-210",
                    "glass/polyester, gelcoat RAL 9010", rho=GRP, step=10))
    out.append(Part("NS6-211", "Spinner brackets (3)", to_world(spinner_brackets()), "rotor", "#6f7f8f", "NS6-210",
                    "S235 galv.", qty=1, step=10))
    w, g = pitch_parts()
    wall = None
    for a in BLADE_ANGLES:
        ww = to_world(arm_axis(w, a))
        wall = ww if wall is None else wall.fuse(ww)
    out.append(Part("NS6-130", "Pitch washer plates 28 × 4 hardened (30)", wall, "rotor", "#c8c8c8", "NS6-130",
                    "C45 hardened 45 HRC, zinc-flake", step=9, qty=1))
    out.append(Part("NS6-135", "Pitch setting gauge (tool)", to_world(blade_place(g, BLADE_ANGLES[0])), "tooling", "#c47d2a", "NS6-130",
                    "Al 6082 + digital inclinometer", rho=ALU, show=False))
    return out


# ------------------------------------------------------------------ blade mould set NS6-110 (tooling, own frame)
def mould_parts():
    """Two GRP mould halves on steel frames, from a CNC-machined plug. Local blade frame (span +Z, chord X,
    thickness Y); laid flat for the drawing/iso: span along X, chord along Y, the parting plane Z = 0."""
    bl = blade_solid()
    bb = bl.BoundingBox()
    flange = 120.0
    x0, x1 = bb.xmin - flange, bb.xmax + flange
    z0, z1 = R_ROOT - 60.0, R_ROT + 80.0
    depth = 140.0
    lower = box(x0, x1, -depth, 0.0, z0, z1).cut(bl)
    upper = box(x0, x1, 0.0, depth, z0, z1).cut(bl)
    # lay flat: span Z -> X, chord X -> Y, thickness Y -> Z
    def flat(s):
        s = s.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 1, 0), 90.0)   # Z -> X?  (x,y,z)->(z,y,-x)
        s = s.rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), 90.0)   # y -> z
        return s
    lower_f = flat(lower)
    upper_f = flat(upper).translate(cq.Vector(0, 0, 900.0))          # shown lifted (open mould)
    # steel frame under the lower half: 2 longitudinal RHS 80x80 + cross members
    lb = lower_f.BoundingBox()
    fr = None
    for y in (lb.ymin + 60, lb.ymax - 140):
        b = box(lb.xmin, lb.xmax, y, y + 80, lb.zmin - 80, lb.zmin)
        fr = b if fr is None else fr.fuse(b)
    for x in np.linspace(lb.xmin, lb.xmax - 80, 6):
        fr = fr.fuse(box(x, x + 80, lb.ymin + 60, lb.ymax - 60, lb.zmin - 160, lb.zmin - 80))
        for y in (lb.ymin + 60, lb.ymax - 140):
            fr = fr.fuse(box(x, x + 80, y, y + 80, lb.zmin - 800, lb.zmin - 160))
    m_half = 2 * (x1 - x0) * (z1 - z0) * 1e-6 * 22.0          # ~22 kg/m2 laminate + gelcoat, ×2 (flange, ribs)
    return [Part("NS6-110-1", "Blade mould, lower (pressure side) half on frame", lower_f, "tooling", "#3d6f9e", "NS6-110",
                 "GRP tooling laminate 12 mm, vinylester tooling gelcoat", mass_kg=m_half, show=False),
            Part("NS6-110-2", "Blade mould, upper (suction side) half", upper_f, "tooling", "#5a8fc0", "NS6-110",
                 "GRP tooling laminate 12 mm", mass_kg=m_half, show=False),
            Part("NS6-110-3", "Mould frame (RHS 80 × 80 × 4)", fr, "tooling", "#555555", "NS6-110",
                 "S235 RHS 80×80×4", rho=None, mass_kg=(fr.Volume() * STEEL) * 0.19, show=False)]


def root_fixture():
    """NS6-115 root insert fixture: steel ring Ø300 × 20 with 10 locating spigots on PCD 185, bolted to the
    mould root end so the inserts are held square while the root is laminated."""
    s = cyl(150.0, 20.0, (0, 0, 0)).cut(cyl(60.0, 30, (0, 0, -5)))
    for k in range(10):
        ang = math.radians(18 + 36 * k)
        s = s.fuse(cyl(5.9, 30.0, (92.5 * math.cos(ang), 92.5 * math.sin(ang), 20.0)))
        s = s.cut(cyl(6.5, 30, (92.5 * math.cos(ang), 92.5 * math.sin(ang), -5)))
    for k in range(4):
        ang = math.radians(45 + 90 * k)
        s = s.cut(cyl(6.6, 30, (130 * math.cos(ang), 130 * math.sin(ang), -5)))
    return Part("NS6-115", "Root insert fixture (tool)", s, "tooling", "#8a6d4b", "NS6-115", "S355, machined", show=False)


# ================================================================== DRIVETRAIN + YAW (reused)
MAT = {"NP1-100": "42CrMo4+QT forged", "NP1-101": "42CrMo4+QT, induction hardened", "NP1-102": "42CrMo4+QT, induction hardened",
       "NP1-200": "S355J2+N", "NP1-201": "M270-35A 0.35 mm, self-bonding", "NP1-202": "1.4404 (non-magnetic)",
       "NP1-203C": "Cu enamelled Ø1.55 class 200, NKN 0.30", "NP1-211-F": "S355J2", "NP1-211-R": "S355J2",
       "NP1-230": "C45E+N 16 mm", "NP1-310": "S355J2+N 25 plate", "NP1-320": "42CrMo4+QT", "NP1-321": "S355J2",
       "NS6-913-F": "bought 32028 X", "NS6-913-R": "bought 32028 X", "NS6-914": "bought M18 PNP", "NS6-915": "bought, spring-applied"}
REUSE_SKIP = ("NP1-110", "NP1-600", "NP1-300", "KMT27", "yaw_brake_caliper", "NP1-400", "tower_top_flange", "_right",
              "yaw_bearing", "yaw_drive", "NP1-420")


def drivetrain_parts():
    out = []
    with contextlib.redirect_stdout(io.StringIO()):
        ps = FP.build_parts()
    colors = {"NP1-100": "#8c8c8c", "NP1-101": "#a0a0a0", "NP1-102": "#a0a0a0", "32028": "#c9a227", "NP1-200": "#4d6a8a",
              "NP1-201": "#3b4a63", "NP1-202": "#b0b0b0", "stator_end": "#b87333", "NP1-210": "#33475b",
              "NP1-211": "#777777", "NP1-212": "#a9b4bf", "NP1-220": "#2b2b2b", "NP1-230": "#9b6a3c", "NP1-320": "#d4a017",
              "NP1-321": "#5d7d5d", "overspeed": "#222222", "brake_caliper": "#b03a2e", "NP1-310": "#5d7d5d"}
    names = {"NP1-212_drum_rear_cover": ("NS6-610", "G6 plain rear cover (no fan blades)", "NS6-610", "EN AW-5083-H111"),
             "NP1-210_rotor_drum": ("NP1-210C", "Rotor drum weldment (G6: no fins, no ribs)", "NP1-210C", "S355J2+N"),
             "NP1-220_magnet_ring": ("NP1-220E", "Magnets 200 × N45SH 30×15×12 + comb + sleeve", "NP1-220E/221C/222C/223C", "NdFeB N45SH")}
    steps = {"NP1-100": 2, "NP1-101": 2, "NP1-102": 2, "32028": 3, "NP1-200": 3, "NP1-201": 3, "stator_key": 3, "NP1-202": 3,
             "stator_end": 3, "NP1-210": 4, "NP1-211": 4, "NP1-212": 4, "NP1-220": 4, "NP1-230": 4, "NP1-320": 5, "NP1-321": 5,
             "overspeed": 5, "brake_caliper": 5, "NP1-310": 5}
    for p in ps:
        if any(k in p.pid for k in REUSE_SKIP):
            continue
        key = next((k for k in colors if p.pid.startswith(k)), None)
        if p.pid in names:
            pid, nm, dwg, mat = names[p.pid]
        else:
            pid = p.pid.split("_")[0] if p.pid.startswith("NP1") else p.pid
            nm, dwg, mat = p.name, (p.pid.split("_")[0] if p.pid.startswith("NP1") else "NS6-910"), ""
        bought = "envelope" in p.pid
        mass = None
        if "caliper" in p.pid and bought:
            mass, nm = 9.0, "Spring-applied caliper, 1.5 kNm pack (bought)"
        if "32028" in p.pid:
            mass = 2.6 if "cone" in p.pid else 1.4
        if "end_winding" in p.pid:
            mass = 10.0
        if "overspeed" in p.pid:
            mass = 0.2
        if "NP1-201" in p.pid:
            mass = None
        out.append(Part(pid + ("" if pid == p.pid else ""), nm, p.solid, "drivetrain", colors.get(key, "#888888"), dwg, mat,
                        make_buy="buy" if bought else "make", rho=STEEL if not bought else None, mass_kg=mass,
                        step=steps.get(key, 4), notes=list(p.notes)))
    # Rev C magnets are 7.6 g/cm3, drum aluminium? no: drum steel. Magnet layer dummy -> magnet mass 200 x 41 g
    ren = [("32028X_front", "NS6-913-F", "Tapered roller bearing 32028 X, front (bought)"),
           ("32028X_rear", "NS6-913-R", "Tapered roller bearing 32028 X, rear (bought)"),
           ("stator_end_winding", "NP1-203C", "Coils on segments, 45 × 28 turns (end windings shown)"),
           ("overspeed_sensor", "NS6-914", "Overspeed sensors M18 inductive (2, bought)"),
           ("brake_caliper", "NS6-915", "Spring-applied brake caliper, 1.5 kNm pack (bought)")]
    for p in out:
        for key, pid, nm in ren:
            if p.pid.startswith(key):
                p.pid, p.name, p.drawing = pid, nm, ("NS6-910" if pid.startswith("NS6-91") else p.drawing)
                if pid.startswith("NS6-91"):
                    p.make_buy = "buy"
        if p.pid == "NP1-211":
            p.pid = "NP1-211-F" if "Front" in p.name else "NP1-211-R"
        if p.pid == "NP1-200":
            p.pid, p.name, p.drawing = "NP1-200C", "Stator carrier with 45 dovetail grooves", "NP1-200C"
        if p.pid == "NP1-201":
            p.pid, p.name, p.drawing = "NP1-201C", "Stator: 45 tooth-segment lamination stacks", "NP1-201C"
        if p.pid == "NP1-203C":
            p.drawing, p.make_buy = "NP1-203C", "make"
        if p.pid in MAT:
            p.material = MAT[p.pid]
    out = [p for p in out if not p.pid.startswith("stator_key")]
    out = merge(out)
    for p in out:
        if p.pid == "NP1-220E":
            p.mass_kg = 200 * 30 * 15 * 12 * 7.6e-6 + 2.5
        if p.pid == "NS6-610":
            p.rho = ALU
    return out


def yaw_parts():
    out = []
    with contextlib.redirect_stdout(io.StringIO()):
        asm = YM.assembly(context=False)
    groups = {}
    for nm, s, col in asm:
        if nm.startswith("tower_flange_stub"):
            continue
        if nm.startswith("NY-410"):
            k = nm[:7]
        elif nm.startswith("NY-420"):
            k = nm.split("_")[0] + "_" + nm.split("_")[1]
        elif nm.startswith("NY-4"):
            k = nm[:6]
        else:
            k = nm
        groups.setdefault(k, []).append((nm, s, col))
    meta = {"NY-400": ("NY-400", "Tower-top adapter with friction track", "S355J2+N weldment", None, 6),
            "NY-410L": ("NY-410", "Friction pad unit (left)", "S355 / DIN 2093 springs / organic pads", 14.0, 1),
            "NY-410R": ("NY-410", "Friction pad unit (right)", "S355 / DIN 2093 springs / organic pads", 14.0, 1),
            "NY-430": ("NY-430", "Yaw lock (screw block)", "42CrMo4 / S355", None, 1),
            "NY-440": ("NY-440", "Yaw encoder + cam limit switch unit", "S355 + absolute encoder + cam switch", 6.0, 1),
            "NY-460": ("NY-460", "Cable hanger tube + loop cleat", "S355 tube 168.3 × 4.5", None, 1),
            "ring_inner": ("NS6-911", "Yaw slewing ring Dpw 360 z150 m4 (inner ring)", "bought: 42CrMo4, induction hardened teeth", 27.5, 1),
            "ring_outer": ("NS6-911", "Yaw slewing ring Dpw 360 z150 m4 (outer gear ring)", "bought", 27.5, 1),
            "yaw_drive_left": ("NS6-912", "Yaw gearmotor 0.18 kW 1:1680, brake 2 Nm (left)", "bought", 19.0, 1),
            "yaw_drive_right": ("NS6-912", "Yaw gearmotor 0.18 kW 1:1680, brake 2 Nm (right)", "bought", 19.0, 1),
            "NY-420_left": ("NP1-420", "Yaw drive bracket (left)", "S355J2+N", None, 1),
            "NY-420_right": ("NP1-420", "Yaw drive bracket (right)", "S355J2+N", None, 1)}
    cols = {"NY-400": "#7f8c99", "NY-410L": "#b8452f", "NY-410R": "#b8452f", "NY-430": "#6d3f8c", "NY-440": "#2f8f8f",
            "NY-460": "#8a6d4b", "ring_inner": "#d4a63a", "ring_outer": "#d4a63a", "yaw_drive_left": "#4b5a9c",
            "yaw_drive_right": "#4b5a9c", "NY-420_left": "#5d7d5d", "NY-420_right": "#5d7d5d"}
    for k, lst in groups.items():
        sol = None
        for nm, s, col in lst:
            if nm == "NY-460_cables":
                continue
            sol = s if sol is None else sol.fuse(s)
        pid, name, mat, mass, step = meta.get(k, (k, k, "", None, 6))
        if k == "NY-400":
            step = 7
        elif k.startswith("ring") or k.startswith("yaw_drive") or k.startswith("NY-420"):
            step = 1
        bought = "bought" in mat
        out.append(Part(pid + ("-L" if k.endswith("L") or k.endswith("left") else "-R" if k.endswith("R") or k.endswith("right") else "")
                        if pid in ("NY-410", "NS6-912", "NP1-420") else (pid + ("-I" if "inner" in k else "-O" if "outer" in k else "")),
                        name, sol, "yaw", cols.get(k, "#888888"), pid, mat, make_buy="buy" if bought else "make",
                        rho=None if (bought or mass) else STEEL, mass_kg=mass, step=step))
    return out


# ================================================================== NACELLE (new)
def bedplate_solid():
    """NS6-300 from analysis/turbine_6kw/bedplate6.json (doc 32)."""
    t = math.radians(TILT)
    B = BPI
    xf, xr = 480.0, 480.0 + B["t_front"]
    tb = -BPJ["axis_above_bottom_top"]
    tbot = B["t_bottom"]
    # front plate (spindle frame) with the Ø410 x 10 pad, spigot bore, bolts, cable holes, window
    fp = box(xf, xr, -B["front_w"] / 2, B["front_w"] / 2, tb - B["t_front"] * math.tan(t) - 30, B["u_top"])
    fp = fp.fuse(cyl_x(470.0, xf + 1, 205.0)).clean()
    fp = fp.cut(cyl_x(460, 560, 100.0))
    fp = FP.bolt_holes(fp, 12, 350.0, 22.0, 460, 560)
    fp = FP.bolt_holes(fp, 2, 290.0, 32.0, 460, 560, angles=(15.0, 195.0))
    fp = fp.cut(box(xf - 20, xr + 20, -150.0, 150.0, tb + 40, tb + 180))
    for yy in (-60.0, 60.0):
        fp = fp.cut(cyl(10.2 / 2, 30, (xf + 10, yy, B["u_top"] - 28)))
    fp = to_world(fp).cut(box(-2000, 2000, -600, 600, -300, tbot))
    # bottom plate (yaw flange)
    bp = box(B["x_bot_front"], B["x_rear"], -B["width"] / 2, B["width"] / 2, 0, tbot)
    for sy in (1, -1):
        tri = cq.Workplane("XY").polyline([(B["x_rear"] - 150, sy * B["width"] / 2), (B["x_rear"] + 1, sy * B["width"] / 2),
                                           (B["x_rear"] + 1, sy * (B["width"] / 2 - 151))]).close().extrude(60).translate((0, 0, -10)).val()
        bp = bp.cut(tri)
    bp = bp.cut(cyl(110.0, 60, (0, 0, -10)))
    bp = zholes(bp, 16, 300.0, 18.0, -10, 50, start=11.25)
    for a in (141.8, -141.8):                         # pad unit bracket bolts, M16 tapped
        for (u, v) in ((340, -60), (340, 60), (420, -60), (420, 60)):
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            xx, yy = u * ca - v * sa, u * sa + v * ca
            if B["x_bot_front"] < xx < B["x_rear"] and abs(yy) < B["width"] / 2:
                bp = bp.cut(cyl(7.0, 60, (xx, yy, -10)))
    # side plates
    sp = [tuple(p) for p in BPJ["side_poly"]]
    sides = None
    for y0, y1 in ((B["width"] / 2 - B["t_side"], B["width"] / 2), (-B["width"] / 2, -B["width"] / 2 + B["t_side"])):
        s = FP._xz_prism(sp, y0, y1)
        for x, z, r in B["holes"]:
            s = s.cut(cyl(r, 40, (x, y0 - 10, z), (0, 1, 0)))
        for x in (-50.0, 50.0):
            for z in (70.0, 140.0):
                s = s.cut(cyl(9.0, 40, (x, y0 - 10, z), (0, 1, 0)))
        sides = s if sides is None else sides.fuse(s)
    rear = box(B["x_rear"] - 10, B["x_rear"], -B["width"] / 2 + B["t_side"], B["width"] / 2 - B["t_side"], tbot, tbot + 100)
    gp = FP._P(xr, tb)
    gus = None
    for y in (-130.0, 130.0):
        g = FP._xz_prism([(gp[0] - 2, tbot), (gp[0] + 180, tbot), (gp[0] - 2, tbot + 180)], y - 6, y + 6)
        gus = g if gus is None else gus.fuse(g)
    return fp.fuse(bp).fuse(sides).fuse(rear).fuse(gus).clean()


COVER = dict(x_front=-385.0, x_rear=520.0, front=(600.0, -200.0, 1040.0, 330.0), rear=(410.0, -200.0, 690.0, 230.0),
             t=4.0, opening_r=338.0, bottom_r=405.0, split_z=330.0)


def cover_solids():
    C = COVER
    def loft(off):
        yf, zf0, zf1, rf = C["front"]
        yr, zr0, zr1, rr = C["rear"]
        w1 = rrect_wire(C["x_front"] + off, yf - off, zf0 + off, zf1 - off, rf - off)
        w2 = rrect_wire(C["x_rear"] - off, yr - off, zr0 + off, zr1 - off, rr - off)
        return cq.Solid.makeLoft([w1, w2], True)
    outer, inner = loft(0.0), loft(C["t"])
    sh = outer.cut(inner)
    # front opening around the drum (spindle axis), bottom opening around the yaw axis (tower adapter)
    sh = sh.cut(to_world(cyl_x(250.0, 500.0, C["opening_r"])))
    sh = sh.cut(cyl(C["bottom_r"], 40, (0, 0, -220)))
    lower = sh.cut(box(-3000, 3000, -3000, 3000, C["split_z"], 5000))
    upper = sh.cut(box(-3000, 3000, -3000, 3000, -5000, C["split_z"]))
    # joint flanges (outward, 30 wide, 6 thick) on the split line
    ring_o = outer.cut(box(-3000, 3000, -3000, 3000, -5000, C["split_z"])).cut(box(-3000, 3000, -3000, 3000, C["split_z"] + 6, 5000))
    fl = ring_o.cut(inner)
    lower = lower.fuse(fl.translate(cq.Vector(0, 0, -6)))
    return lower, upper


def cover_frame():
    """NS6-710: 4 support arms (flat bar 60 × 8) from the bedplate side plates to the lower cover tray,
    plus the rear rail (RHS 40×40×3) carrying the junction box and met mast."""
    out = None
    for sy in (1, -1):
        for x in (-200.0, 80.0):
            b = box(x, x + 50, sy * 260 if sy > 0 else -436, 436 if sy > 0 else -260, 140.0, 146.0)
            out = b if out is None else out.fuse(b)
            out = out.fuse(box(x, x + 50, (430 if sy > 0 else -436), (436 if sy > 0 else -430), -196.0, 146.0))
    rhs = lambda x0, x1, y0, y1, z0, z1: box(x0, x1, y0, y1, z0, z1).cut(box(x0 - 1 if x1 - x0 > 100 else x0 + 3, x1 + 1 if x1 - x0 > 100 else x1 - 3,
                                                                              y0 + 3 if y1 - y0 < 100 else y0 - 1, y1 - 3 if y1 - y0 < 100 else y1 + 1, z0 + 3, z1 - 3))
    out = out.fuse(rhs(150.0, 470.0, -200.0, -160.0, 180.0, 220.0)).fuse(rhs(150.0, 470.0, 160.0, 200.0, 180.0, 220.0))
    out = out.fuse(rhs(430.0, 470.0, -200.0, 200.0, 180.0, 220.0))
    return out


def met_mast():
    m = cyl(21.3, 1150.0, (400.0, 0.0, 200.0))
    m = m.fuse(cyl(40.0, 120.0, (400.0, 0.0, 1350.0)))                      # cup anemometer body
    for k in range(3):
        a = math.radians(120 * k)
        m = m.fuse(cyl(25.0, 20.0, (400.0 + 90 * math.cos(a), 90 * math.sin(a), 1420.0)))
    m = m.fuse(box(380.0, 420.0, -10.0, 10.0, 1220.0, 1250.0)).fuse(box(420.0, 640.0, -3.0, 3.0, 1190.0, 1280.0))   # wind vane
    m = m.fuse(cyl(15.0, 60, (400.0, 0.0, 1480.0)))                          # air terminal base
    m = m.fuse(cyl(6.0, 400, (400.0, 0.0, 1540.0)))                          # air terminal rod
    return m


def junction_box():
    b = box(200.0, 440.0, -170.0, 170.0, 230.0, 380.0)
    b = b.fuse(box(170.0, 200.0, -60.0, 60.0, 260.0, 300.0))
    return b


def nacelle_parts():
    lower, upper = cover_solids()
    return [Part("NS6-300", "Bedplate weldment 6 kW (light)", bedplate_solid(), "nacelle", "#5d7d5d", "NS6-300",
                 "S355J2+N plates, stress relieved, machined", step=1),
            Part("NS6-700-1", "Nacelle cover, lower tray (GRP 5 mm)", lower, "nacelle", "#e8e8e2", "NS6-700",
                 "glass/polyester, gelcoat RAL 9010", rho=GRP, step=6),
            Part("NS6-700-2", "Nacelle cover, upper lid (GRP 5 mm)", upper, "nacelle", "#f3f3ee", "NS6-700",
                 "glass/polyester, gelcoat RAL 9010", rho=GRP, step=11),
            Part("NS6-710", "Cover support arms + rear rail", cover_frame(), "nacelle", "#5d7d5d", "NS6-710", "S235 galv.", step=6),
            Part("NS6-720", "Met mast: anemometer, vane, air terminal", met_mast(), "nacelle", "#555555", "NS6-720",
                 "1.4404 tube 42.4 × 2 + bought sensors", mass_kg=4.5, step=11),
            Part("NS6-730", "Nacelle junction box IP66 (400 × 340 × 150)", junction_box(), "electrical", "#bfbfbf", "NS6-800",
                 "bought: 1.4301 enclosure", mass_kg=9.0, step=6)]


# ================================================================== TOWER + FOUNDATION
FL_BASE = dict(od=D_BASE + 200.0, id=D_BASE - 60.0, t=35.0, n=TW8["tower"]["base_flange"]["bolts"], pcd=D_BASE + 100.0, hole=26.0)
FL_TOP = dict(od=420.0, id=240.0, t=30.0, n=16, pcd=380.0, hole=22.0)
HINGE = dict(pin_d=50.0, lug_t=25.0, lug_gap=(-120.0, 120.0), x=-(D_BASE / 2 + 160.0))   # hinge on the upwind side (-X)


def tower_solid():
    z0, z1 = Z_BASE, Z_TOP_FLANGE
    zb, zt = z0 + FL_BASE["t"], z1 - FL_TOP["t"]
    rb, rt = D_BASE / 2, D_TOP / 2
    t = T_WALL
    def r_at(z):
        return rb + (rt - rb) * (z - zb) / (zt - zb)
    zm = (zb + zt) / 2                                   # can joint: lower can t0, upper can t1 (one piece, butt weld)
    t0, t1 = TG["t_mm"][0], TG["t_mm"][-1]
    shell = revolve_z([(rb - t0, zb), (rb, zb), (r_at(zm), zm), (r_at(zm) - t0, zm)])
    shell = shell.fuse(revolve_z([(r_at(zm) - t1, zm), (r_at(zm), zm), (rt, zt), (rt - t1, zt)]))
    base = revolve_z([(FL_BASE["id"] / 2, z0), (FL_BASE["od"] / 2, z0), (FL_BASE["od"] / 2, zb), (FL_BASE["id"] / 2, zb)])
    base = zholes(base, FL_BASE["n"], FL_BASE["pcd"], FL_BASE["hole"], z0 - 1, zb + 1, start=15.0)
    top = revolve_z([(FL_TOP["id"] / 2, zt), (FL_TOP["od"] / 2, zt), (FL_TOP["od"] / 2, z1), (FL_TOP["id"] / 2, z1)])
    top = zholes(top, FL_TOP["n"], FL_TOP["pcd"], FL_TOP["hole"], zt - 1, z1 + 1, start=11.25)
    s = shell.fuse(base).fuse(top)
    # 8 base gussets (between the hinge lugs and the hand hole they are clocked at 22.5 + 45 k)
    for k in range(8):
        g = FP._xz_prism([(rb - 2, zb), (FL_BASE["od"] / 2 - 10, zb), (rb - 2, zb + 200)], -6.0, 6.0)
        s = s.fuse(rot_z(g, 22.5 + 45 * k))
    # hinge lugs (pair) on the -X side, tilt-up gin pole lugs on the +X side
    for y0 in (HINGE["lug_gap"][0] - HINGE["lug_t"], HINGE["lug_gap"][1]):
        lug = box(HINGE["x"] - 60, -rb + 20, y0, y0 + HINGE["lug_t"], z0, z0 + 160)
        lug = lug.fuse(cyl(60.0, HINGE["lug_t"], (HINGE["x"], y0, z0 + 40), (0, 1, 0)))
        lug = lug.cut(cyl(HINGE["pin_d"] / 2 + 0.5, HINGE["lug_t"] + 2, (HINGE["x"], y0 - 1, z0 + 40), (0, 1, 0)))
        s = s.fuse(lug)
    for y0 in (-145.0, 120.0):
        lug = box(rb - 20, rb + 140, y0, y0 + 25, z0 + 250, z0 + 450)
        lug = lug.cut(cyl(26.0, 27, (rb + 80, y0 - 1, z0 + 350), (0, 1, 0)))
        s = s.fuse(lug)
    # hand hole 150 x 300 on +Y at 600 above the base, with a 15 mm reinforcing frame
    zc = z0 + 700.0
    fr = box(-110, 110, r_at(zc) - 30, r_at(zc) + 15, zc - 185, zc + 185).cut(box(-75, 75, r_at(zc) - 80, r_at(zc) + 40, zc - 150, zc + 150))
    s = s.fuse(fr.cut(cyl(r_at(zc) - t, 400, (0, 0, zc - 200))))
    s = s.cut(box(-75, 75, 0, rb + 50, zc - 150, zc + 150))
    # earthing bosses
    for a in (60.0, 240.0):
        s = s.fuse(rot_z(box(rb - 5, rb + 30, -20, 20, z0 + 300, z0 + 340), a))
    return s.clean()


def handhole_cover():
    zc = Z_BASE + 700.0
    rb, rt = D_BASE / 2, D_TOP / 2
    r = rb + (rt - rb) * (zc - Z_BASE) / (L_TUBE)
    return box(-100, 100, r + 15, r + 21, zc - 175, zc + 175)


def hinge_frame():
    """NS6-410 foundation hinge brackets: two 30 mm plates on a 30 mm base plate, 4 × M24 anchors, pin Ø50."""
    z0 = Z_BASE
    zp = z0 - 30.0                                  # base plate under the hinge (on the pedestal, below the grout line)
    out = box(HINGE["x"] - 140, HINGE["x"] + 90, -230, 230, zp - 30, zp)
    for y0 in (HINGE["lug_gap"][0] - HINGE["lug_t"] - 32, HINGE["lug_gap"][1] + HINGE["lug_t"] + 2):
        pl = box(HINGE["x"] - 90, HINGE["x"] + 60, y0, y0 + 30, zp, z0 + 40)
        pl = pl.fuse(cyl(60.0, 30, (HINGE["x"], y0, z0 + 40), (0, 1, 0)))
        pl = pl.cut(cyl(HINGE["pin_d"] / 2 + 0.5, 32, (HINGE["x"], y0 - 1, z0 + 40), (0, 1, 0)))
        out = out.fuse(pl)
    for (x, y) in ((HINGE["x"] - 100, -190), (HINGE["x"] - 100, 190), (HINGE["x"] + 50, -190), (HINGE["x"] + 50, 190)):
        out = out.cut(cyl(13.0, 50, (x, y, zp - 40)))
    pin = cyl(HINGE["pin_d"] / 2, 2 * (HINGE["lug_gap"][1] + HINGE["lug_t"] + 32) + 60, (HINGE["x"], -(HINGE["lug_gap"][1] + HINGE["lug_t"] + 62), z0 + 40), (0, 1, 0))
    return out, pin


def gin_pole():
    """NS6-420 gin pole (tilt-up tool): tube Ø168.3 × 6.3, 3.0 m, pinned to the tower gin-pole lugs, head with
    two line plates. Shown in the erected (stowed-off) position for the iso; it is removed after erection."""
    rb = D_BASE / 2
    z = Z_BASE + 350.0
    p = cyl(84.15, 3000.0, (rb + 80, 0, z), (1, 0, 0)).cut(cyl(77.85, 3010.0, (rb + 75, 0, z), (1, 0, 0)))
    p = p.fuse(box(rb + 60, rb + 200, -120, 120, z - 90, z + 90).cut(box(rb + 59, rb + 201, -95, 95, z - 91, z + 91)))
    p = p.fuse(box(rb + 2980, rb + 3180, -12, 12, z - 120, z + 120).cut(cyl(20.0, 30, (rb + 3120, -15, z), (0, 1, 0))))
    return p


def foundation_solid(B=None):
    f = TW8["foundations"]["firm soil (dense gravel, moraine)"]
    B = (B or f["B"]) * 1000.0
    d = f["depth"] * 1000.0
    zg = Z_GROUND
    slab = box(-B / 2, B / 2, -B / 2, B / 2, zg - d, zg - d + 600.0)
    ped = box(-600, 600, -600, 600, zg - d + 600.0, zg + 170.0)
    s = slab.fuse(ped)
    s = s.cut(cyl(80.0, 2200, (0, 400.0, zg - 1500.0)).rotate(cq.Vector(0, 400, zg - 400), cq.Vector(1, 400, zg - 400), 0))
    s = s.cut(box(-60, 60, 300, 700, zg - 600, zg + 200))          # cable duct Ø110 x 2 (to the cabinet), shown as a slot
    return s


def anchor_cage():
    zg = Z_GROUND
    n, pcd = FL_BASE["n"], FL_BASE["pcd"]
    zt = Z_BASE + FL_BASE["t"] + 60.0
    zb = zg - 1450.0
    s = None
    for k in range(n):
        a = math.radians(15.0 + 360.0 * k / n)
        b = cyl(12.0, zt - zb, (pcd / 2 * math.cos(a), pcd / 2 * math.sin(a), zb))
        s = b if s is None else s.fuse(b)
    for z in (zb + 30, zg - 250.0):
        ring = revolve_z([(pcd / 2 - 50, z), (pcd / 2 + 50, z), (pcd / 2 + 50, z + 20), (pcd / 2 - 50, z + 20)])
        s = s.fuse(zholes(ring, n, pcd, 26.0, z - 1, z + 21, start=15.0))
    for (x, y) in ((HINGE["x"] - 100, -190), (HINGE["x"] - 100, 190), (HINGE["x"] + 50, -190), (HINGE["x"] + 50, 190)):
        s = s.fuse(cyl(12.0, (Z_BASE - 30) - (zg - 900.0) + 50, (x, y, zg - 900.0)))
    return s


def cabinet():
    """NS6-620 tower base cabinet (IP55, 800 × 600 × 300) on a galvanised stand next to the pedestal,
    with the NS6-600 braking resistor box on the stand (vented, away from the electronics)."""
    zg = Z_GROUND
    x0, y0 = -400.0, 1150.0
    stand = box(x0, x0 + 40, y0, y0 + 40, zg, zg + 1500).fuse(box(x0 + 760, x0 + 800, y0, y0 + 40, zg, zg + 1500))
    stand = stand.fuse(box(x0, x0 + 800, y0, y0 + 40, zg + 400, zg + 440)).fuse(box(x0, x0 + 800, y0, y0 + 40, zg + 1400, zg + 1440))
    cab = box(x0, x0 + 800, y0 + 40, y0 + 340, zg + 600, zg + 1400)
    cab = cab.fuse(box(x0 + 20, x0 + 780, y0 + 340, y0 + 345, zg + 620, zg + 1380))
    res = box(x0 + 820, x0 + 1420, y0 + 40, y0 + 290, zg + 700, zg + 1100)
    for k in range(6):
        res = res.cut(box(x0 + 860 + 90 * k, x0 + 900 + 90 * k, y0 + 280, y0 + 300, zg + 740, zg + 1060))
    res_stand = box(x0 + 820, x0 + 860, y0, y0 + 40, zg, zg + 1150).fuse(box(x0 + 1380, x0 + 1420, y0, y0 + 40, zg, zg + 1150))
    duct = cyl(55.0, 1150.0 - 300, (0, 300.0, zg - 450.0), (0, 1, 0))
    return stand.fuse(res_stand), cab, res, duct


def drop_cable():
    """NS6-800 tower drop cable (4 × 10 mm² + PE, H07RN-F, Ø28) from the hanger loop to the hand hole."""
    zt = YM.HANG["cleat_z"] - 450.0
    zb = Z_BASE + 700.0
    c = cyl(14.0, zt - zb, (-40.0, 0.0, zb))
    c = c.fuse(cyl(14.0, 200.0, (-40.0, 0.0, zb), (0, 1, 0)))
    return c


def tower_parts():
    hf, pin = hinge_frame()
    stand, cab, res, duct = cabinet()
    fnd_m3 = TW8["foundations"]["firm soil (dense gravel, moraine)"]["concrete_m3"]
    return [Part("NS6-400", f"Tower 8 m, Ø{D_BASE:.0f} → Ø{D_TOP:.0f}, t {TG['t_mm'][0]}/{TG['t_mm'][-1]}, one piece", tower_solid(), "tower", "#a7aaa3", "NS6-400",
                 "S355J2+N, hot-dip galvanised", step=0),
            Part("NS6-401", "Hand-hole cover 200 × 350 × 6 with gasket", handhole_cover(), "tower", "#9a9d96", "NS6-400", "S355 galv.", step=12),
            Part("NS6-410", "Base hinge brackets + hinge pin Ø50", hf.fuse(pin), "tower", "#4f5f6f", "NS6-410",
                 "S355J2+N galv.; pin 42CrMo4+QT", step=0),
            Part("NS6-420", "Gin pole 3.0 m (erection tool)", gin_pole(), "tooling", "#d08a2a", "NS6-420", "S355 tube 168.3 × 6.3", show=False),
            Part("NS6-500", "Spread footing (firm ground) with pedestal", foundation_solid(), "foundation", "#c9c6bd", "NS6-500",
                 "C30/37 XF4 air-entrained, B500C", rho=None, mass_kg=fnd_m3 * 2400.0, step=0),
            Part("NS6-510", f"Anchor cage {FL_BASE['n']} × M24 + 4 hinge anchors", anchor_cage(), "foundation", "#7a5c3a", "NS6-510",
                 "M24 8.8 HDG threaded rod, S355 template rings", step=0),
            Part("NS6-620", "Tower base cabinet IP55 800 × 600 × 300 on stand", stand.fuse(cab), "electrical", "#c2c7cc", "NS6-620",
                 "stand S235 galv.; bought enclosure", mass_kg=95.0, step=12),
            Part("NS6-600", "Braking resistor box 3 × 4 Ω (vented)", res, "electrical", "#b7b2a5", "NS6-600", "1.4301 box + steel-grid resistors",
                 mass_kg=18.0, step=12),
            Part("NS6-800", "Drop cable + base duct (cabling route)", drop_cable().fuse(duct), "electrical", "#222222", "NS6-800",
                 "H07RN-F 4G10 + 2 × LiYCY signal; PE duct Ø110", mass_kg=12.0, step=12)]


# ================================================================== build
def merge(parts):
    """Fuse parts that share a pid (one BOM line, several solids)."""
    seen, out = {}, []
    for p in parts:
        if p.pid in seen:
            q = seen[p.pid]
            q.solid = q.solid.fuse(p.solid)
            if q.mass_kg is not None and p.mass_kg is not None:
                q.mass_kg += p.mass_kg
            continue
        seen[p.pid] = p
        out.append(p)
    return out


_CACHE = None


def build(tooling=True):
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    parts = []
    parts += nacelle_parts()
    parts += yaw_parts()
    parts += drivetrain_parts()
    parts += hub_parts()
    parts += rotor_parts()
    parts += tower_parts()
    if tooling:
        parts += mould_parts()
        parts.append(root_fixture())
    _CACHE = parts
    return parts


def main():
    ps = build()
    rows = []
    tot = {}
    for p in ps:
        m = p.mass()
        bb = p.solid.BoundingBox()
        rows.append(dict(pid=p.pid, name=p.name, group=p.group, drawing=p.drawing, material=p.material, make_buy=p.make_buy,
                         qty=p.qty, mass_kg=None if m is None else round(m, 2), show=p.show, step=p.step,
                         bbox=[round(bb.xmin), round(bb.xmax), round(bb.ymin), round(bb.ymax), round(bb.zmin), round(bb.zmax)]))
        print(f"{p.pid:14s} {p.name[:58]:58s} {p.group:11s} {'' if m is None else f'{m:8.1f}'}")
        if p.show and m is not None:
            tot[p.group] = tot.get(p.group, 0.0) + m
    head = sum(v for k, v in tot.items() if k in ("nacelle", "yaw", "drivetrain", "rotor")) + next(p.mass() for p in ps if p.pid == "NS6-730")
    print({k: round(v) for k, v in tot.items()}, "head above the tower flange", round(head))
    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / "model6-parts.json").write_text(json.dumps(dict(parts=rows, group_mass_kg={k: round(v, 1) for k, v in tot.items()}, head_kg=round(head, 1)), indent=1))


if __name__ == "__main__":
    main()
