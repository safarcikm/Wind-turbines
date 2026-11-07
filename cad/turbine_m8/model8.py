"""M8 12 kW turbine on the 8 m tower: 3D model of every part (doc 37 build book).

    python3 model8.py            -> prints the part list with CAD masses, writes out/model8-parts.json
    import model8; parts = model8.build()   (list of model6.Part, WORLD frame)

Same WORLD frame and the same part builders as cad/turbine_6kw/model6.py (doc 34), which this module
imports and re-points at the M8 results (analysis/variant_m8/results, docs 35-36):

  * rotor: M8 blade Ø8.0 m (bem M8 planform, structure_m8 t/c), root Ø280 with 12 x M16 inserts on PCD 245,
    on the collective-pitch hub of cad/hub_m8 (crank r140, pin plane 150, clash-free 0-92 deg);
  * drivetrain: generator Rev D = Rev C + 2 magnet rows. The fit-check parts (cad/nacelle_fitcheck) are
    stretched 30 mm at spindle x 410 (inside the stack, where spindle, carrier, stack, drum shell and ribs
    are prismatic): everything ahead of x 410 moves 30 mm forward, so the rear spindle flange, the bedplate
    interface, the disc and the calipers stay where they were and the rotor plane sits 780 mm ahead of the
    yaw axis (doc 35 overhang). A third brake caliper sits at 12 o'clock on its own bracket;
  * nacelle: NP8-300 bedplate (NS6 geometry, plates 20/30/10) with the Dpw 410 yaw ring bolt circle;
  * yaw: the doc 25 system with the ring Dpw 410 (z165 m4), everything radial moved out 25 mm;
  * tower: the stiff 8 m tower re-sized with the simulated 8 m loads (tower8_m8.py, stiff_final_sim8).
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import math
import sys
from pathlib import Path

import cadquery as cq
import numpy as np

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "cad" / "turbine_6kw"))
sys.path.insert(0, str(ROOT / "analysis" / "variant_m8"))
sys.path.insert(0, str(ROOT / "analysis" / "rotor"))
import model6 as M6  # noqa: E402

Part, FP, G, YM = M6.Part, M6.FP, M6.G, M6.YM
box, cyl, cyl_x, to_world, rot_x, revolve_x, revolve_z = M6.box, M6.cyl, M6.cyl_x, M6.to_world, M6.rot_x, M6.revolve_x, M6.revolve_z
STEEL, ALU, GRP = M6.STEEL, M6.ALU, M6.GRP

with contextlib.redirect_stdout(io.StringIO()):
    import common as C  # noqa: E402

RES = ROOT / "analysis" / "variant_m8" / "results"
T8 = json.loads((RES / "tower8_m8.json").read_text())
TOWER_KEY = "stiff_final_sim8" if "stiff_final_sim8" in T8["towers"] else "stiff"
BLD = json.loads((RES / "blade_m8.json").read_text())
HY = json.loads((RES / "hub_yaw_m8.json").read_text())
GEN = json.loads((RES / "generator_m8.json").read_text())
BPM = json.loads((RES / "bedplate_m8.json").read_text())["NP8-300 (proposed)"]

DX = -30.0                      # spindle frame: rotor, hub and the front of the generator move 30 mm forward
X_CUT = 410.0                   # stretch plane (spindle frame)
R_ROT = C.R * 1000.0
PB_TOP = 442.0                  # pitch bearing inner ring top face = blade root face (cad/hub_m8)
ROOT_D, ROOT_PCD, ROOT_N = 280.0, 245.0, 12
PITCH_SET = -2.0
M_BLADE = BLD["carbon"]["mass_kg"]

# ------------------------------------------------------------------ tower data -> model6 module constants
M6.T8 = dict(T8, z_pedestal_m=T8.get("z_pedestal_m", 0.20))
M6.TW8 = T8["towers"][TOWER_KEY]
M6.HUB_H = M6.T8["hub_height_m"] * 1000.0
M6.Z_GROUND = M6.RC[2] - M6.HUB_H
M6.Z_BASE = M6.Z_GROUND + M6.T8["z_pedestal_m"] * 1000.0
M6.L_TUBE = M6.Z_TOP_FLANGE - M6.Z_BASE
M6.TG = M6.TW8["tower"]["geometry"]
M6.D_BASE, M6.D_TOP = M6.TG["D_base"] * 1000.0, M6.TG["D_top"] * 1000.0
M6.T_WALL = M6.TG["t_mm"][0]
D_BASE = M6.D_BASE
M6.FL_BASE = dict(od=D_BASE + 200.0, id=D_BASE - 60.0, t=35.0, n=M6.TW8["tower"]["base_flange"]["bolts"], pcd=D_BASE + 100.0, hole=26.0)
M6.HINGE = dict(pin_d=50.0, lug_t=25.0, lug_gap=(-120.0, 120.0), x=-(D_BASE / 2 + 160.0))

# ------------------------------------------------------------------ yaw ring Dpw 410 (hub_yaw_m8: z165 m4, face 60)
YAW_DR = 25.0
G.YAW.update(d_pw=410.0, gear_z=165, inner=dict(id=270.0, od=400.0, pcd=350.0), outer=dict(id=420.0, pcd=490.0))
FP.YAW_DRIVE["r"] = 165 * 4.0 / 2 + 14 * 4.0 / 2              # 358
YM.AD.update(seat_r=(150.0, 275.0), track_r=(275.0, 420.0),
             gussets=dict(YM.AD["gussets"], r=(198.0, 325.0)), ring_bolts=dict(YM.AD["ring_bolts"], pcd=490.0))


def _shift_u(d):
    for k, v in d.items():
        if isinstance(v, dict):
            _shift_u(v)
        elif k == "u":
            d[k] = tuple(x + YAW_DR for x in v) if isinstance(v, tuple) else v + YAW_DR
        elif k == "bolts":
            d[k] = [(u + YAW_DR, w) for u, w in v]


_shift_u(YM.PADU)
_shift_u(YM.LOCK)
YM.ENC["r"] = (165 * 4.0 + YM.ENC["z_pinion"] * 4.0) / 2


def yaw_ring_parts():
    """FP.yaw_parts with the Dpw 410 ring: 16 x M16 on PCD 350 (inner, to the bedplate) and PCD 490 (outer)."""
    Y = G.YAW
    inner = cq.Solid.makeCylinder(Y["inner"]["od"] / 2, Y["height"] - 10, cq.Vector(0, 0, -(Y["height"] - 10)))
    inner = inner.cut(cq.Solid.makeCylinder(Y["inner"]["id"] / 2, 100, cq.Vector(0, 0, -90)))
    inner = M6.zholes(inner, 16, Y["inner"]["pcd"], FP.TAP["M16"], -70, 5, start=360.0 / 32)
    m, z = Y["module"], Y["gear_z"]
    rp, ra, rf = m * z / 2, m * z / 2 + m, m * z / 2 - 1.25 * m
    pts = []
    for k in range(z):
        a0, p = 2 * math.pi * k / z, 2 * math.pi / z
        for frac, r in ((0.0, rf), (0.18, rf), (0.32, ra), (0.68, ra), (0.82, rf)):
            pts.append((r * math.cos(a0 + frac * p), r * math.sin(a0 + frac * p)))
    gear = cq.Workplane("XY", origin=(0, 0, -Y["height"])).polyline(pts).close().extrude(Y["height"] - 10).val()
    gear = gear.cut(cq.Solid.makeCylinder(Y["outer"]["id"] / 2, 100, cq.Vector(0, 0, -90)))
    gear = M6.zholes(gear, 16, Y["outer"]["pcd"], FP.TAP["M16"], -90, 10)
    P = FP.Part
    return [P("yaw_bearing_inner_ring_envelope", "Yaw bearing inner ring", inner, "stationary", "", (0.8, 0.65, 0.2),
              make_buy="buy (envelope)", axis="yaw"),
            P("yaw_bearing_outer_gear_ring_envelope", "Yaw bearing outer ring, gear z165 m4", gear, "tower", "", (0.8, 0.65, 0.2),
              make_buy="buy (envelope)", axis="yaw")]


FP.yaw_parts = yaw_ring_parts


# ================================================================== ROTOR
def _tc(r_m):
    k = (C.R - 0.40) / (3.75 - 0.40)
    pts = [(0.40, 1.00), (0.55, 0.70), (0.775, 0.30), (1.5, 0.25), (2.25, 0.21), (3.2, 0.18)]
    pts = [(0.40 + (r - 0.40) * k, tc) for r, tc in pts] + [(C.R, 0.18)]
    x, y = zip(*pts)
    return float(np.interp(r_m, x, y))


def blade_solid(local=False):
    """M8 blade in the model6 blade-local frame (span +Z from the root face at Z = PB_TOP)."""
    b = C.blade_shape(n=40)
    r = np.array(b.r) * 1000.0
    c = np.array(b.chord) * 1000.0
    tw = np.array(b.twist + b.twist_tip_offset)
    rs = [PB_TOP, 470.0, 520.0, 600.0, 700.0, 820.0, 980.0, 1200.0, 1500.0, 1850.0, 2250.0, 2650.0, 3050.0, 3450.0, 3800.0, 3960.0, R_ROT]
    wires = []
    for x in rs:
        cc, t = float(np.interp(x, r, c)), _tc(x / 1000.0)
        th = float(np.interp(x, r, tw)) + PITCH_SET
        if x <= 470.0:
            cc, t = ROOT_D, 1.0
        pts = M6.airfoil_pts(cc, t)
        a = math.radians(th)
        P = [cq.Vector(-(px * math.cos(a) - py * math.sin(a)), px * math.sin(a) + py * math.cos(a), x) for px, py in pts]
        wires.append(cq.Wire.assembleEdges([cq.Edge.makeSpline(P + [P[0]], periodic=False)]))
    sol = cq.Solid.makeLoft(wires, False)
    return sol.cut(cyl(ROOT_D / 2 - 20.0, 320.0, (0, 0, PB_TOP - 1)))


def insert_solid():
    """NM8-105 root insert: the doc 34 insert scaled 4/3 (Ø32 x 147, M16 internal thread 40 deep)."""
    return M6.insert_solid().scale(4.0 / 3.0)


def blade_place(s, a):
    return M6.blade_place(s, a, x_axis=DX)


def rotor_parts():
    out = []
    bl = blade_solid()
    for i, a in enumerate(M6.BLADE_ANGLES, 1):
        out.append(Part(f"NM8-100-{i}", f"Blade {i} Ø8.0 m (glass/epoxy, carbon UD caps)", to_world(blade_place(bl, a)), "rotor", "#e9e6dc",
                        "NM8-100", "E-glass/epoxy, carbon UD caps, PVC core", mass_kg=M_BLADE, step=9,
                        notes=["one mould for all three; static-moment matched set", "root Ø280, 12 x M16 inserts on PCD 245"]))
    ins = insert_solid()
    ins_all = None
    for k in range(ROOT_N):
        ang = 15.0 + 360.0 / ROOT_N * k
        s = ins.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 1, 0), -90.0)
        s = s.translate(cq.Vector(ROOT_PCD / 2 * math.cos(math.radians(ang)), ROOT_PCD / 2 * math.sin(math.radians(ang)), PB_TOP))
        ins_all = s if ins_all is None else ins_all.fuse(s)
    out.append(Part("NM8-105", "Root insert M16 (12 per blade, bonded)", to_world(blade_place(ins_all, M6.BLADE_ANGLES[0])), "rotor",
                    "#9aa3ab", "NM8-105", "C45E+QT zinc-flake coated", qty=36, rho=None, step=0,
                    notes=["shown on blade 1", "0.78 kg each, included in the blade mass"]))
    return out


# ------------------------------------------------------------------ hub + collective pitch (cad/hub_m8)
def _hub_module():
    saved = {k: sys.modules.pop(k) for k in ("model", "geometry", "collective") if k in sys.modules}
    try:
        spec = importlib.util.spec_from_file_location("model_m8", ROOT / "cad" / "hub_m8" / "model_m8.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.modules.update(saved)


HM = _hub_module()


def spinner_solid():
    """NM8-210 GRP spinner 4 mm: ogive from the nose (x -1050) to r 520 at x -150, cylindrical to the base ring at x 175;
    holes Ø320 around the blade roots (rubber boots)."""
    x0, xm, xb, R = -1050.0, -150.0, 175.0, 520.0
    prof = [(x0, 0.0)]
    for k in range(1, 25):
        f = k / 24
        x = x0 + (xm - x0) * f
        prof.append((x, R * math.sqrt(max(0.0, 1 - (1 - f) ** 2))))
    prof.append((xb, R))
    inner = [(x + 3.0, max(rr - 4.0, 0.0)) for x, rr in prof[1:]]
    poly = prof + [(xb, R - 4.0)] + [(x, rr) for x, rr in inner[::-1][1:] if rr > 0] + [(x0 + 4.0, 0.0)]
    s = revolve_x(poly)
    for a in M6.BLADE_ANGLES:
        s = s.cut(M6.arm_axis(cyl(160.0, 600, (0, 0, 250.0)), a))
    return s


HUB_GROUPS = [  # (prefix, pid, name, material, mass kg (hub_yaw_m8 budget), buy, colour)
    (("hub",), "NM8-200", "Hub weldment: shell Ø530 × 10, 3 necks Ø360, drum flange", "S355NL, welded, stress relieved, machined", 179.8, False, "#6f7f8f"),
    (("bearing_outer", "bearing_inner"), "NM8-250", "Pitch bearings Dpw 300 four-point (3, bought)", "bought: 42CrMo4 rings", 76.2, True, "#c9a13b"),
    (("crank", "pin"), "NM8-260", "Pitch cranks r140 with pins (3)", "42CrMo4+QT / S355 tube", 30.0, False, "#4f6f8f"),
    (("link", "eyes"), "NM8-261", "Pitch links 220 mm with spherical eyes (3)", "S355 / bought rod ends", 4.5, False, "#8f8f6f"),
    (("yoke", "guide_rods"), "NM8-262", "Yoke + 3 guide rods", "S355 plate / C45 chromed rods", 8.0, False, "#9a6a3a"),
    (("cylinder", "cylinder_rod", "motor"), "NM8-270", "Electric pitch cylinder ~28.5 kN rated, 204 mm stroke + motor (bought)", "bought", 14.0, True, "#3a5a9a"),
    (("supercap", "drive"), "NM8-280", "Supercap module + pitch drive/controller (bought)", "bought", 6.5, True, "#2f8f6f"),
    (("nose_housing",), "NM8-290", "Nose frame (actuator + electronics carrier)", "S355 rings + tube struts", 6.0, False, "#7a7a7a"),
]


def hub_parts():
    with contextlib.redirect_stdout(io.StringIO()):
        asm = HM.M.assembly(theta=PITCH_SET, with_context=False)
    out = []
    for pref, pid, nm, mat, mass, buy, col in HUB_GROUPS:
        sol = None
        for n, s, _ in asm:
            if n.startswith("blade_root"):
                continue
            key = n.rsplit("_", 1)[0] if n.split("_")[-1].replace(".", "").replace("-", "").isdigit() else n
            if key in pref:
                s = to_world(s.translate(cq.Vector(DX, 0, 0)))
                sol = s if sol is None else sol.fuse(s)
        out.append(Part(pid, nm, sol, "rotor", col, pid if not buy else "NM8-250", mat, make_buy="buy" if buy else "make",
                        mass_kg=mass, step=8))
    out.append(Part("NM8-210", "Spinner (GRP 4 mm) with blade boots", to_world(spinner_solid().translate(cq.Vector(DX, 0, 0))), "rotor",
                    "#f2f2ee", "NM8-210", "glass/polyester, gelcoat RAL 9010", rho=GRP, step=10))
    return out


# ================================================================== DRIVETRAIN Rev D (stretched fit-check parts)
def to_spindle(s):
    return s.translate(cq.Vector(*[-v for v in FP.RC])).rotate(cq.Vector(0, 0, 0), cq.Vector(0, 1, 0), -FP.TILT)


BIG = 5000.0


def stretch(s_world, keep=False):
    """Lengthen a world-frame part by 30 mm at spindle x = X_CUT (front part forward, gap filled by the section)."""
    s = to_spindle(s_world)
    bb = s.BoundingBox()
    if keep:
        return s_world, "kept"
    if bb.xmax <= X_CUT:
        return to_world(s.translate(cq.Vector(DX, 0, 0))), "moved"
    if bb.xmin >= X_CUT:
        return s_world, "kept"
    front = s.intersect(box(-BIG, X_CUT, -BIG, BIG, -BIG, BIG)).translate(cq.Vector(DX, 0, 0))
    rear = s.intersect(box(X_CUT, BIG, -BIG, BIG, -BIG, BIG))
    sl = s.intersect(box(X_CUT - 0.5, X_CUT, -BIG, BIG, -BIG, BIG))
    k = -DX / 0.5
    mat = cq.Matrix([[k, 0, 0, X_CUT * (1 - k)], [0, 1, 0, 0], [0, 0, 1, 0]])
    fill = sl.transformGeometry(mat)
    return to_world(front.fuse(fill).fuse(rear).clean()), "stretched"


REV_D = {  # pid -> (new pid, name, material)
    "NP1-100": ("NP1-100D", "Spindle Rev D (30 mm longer between the rear seat and the flange)", "42CrMo4+QT forged"),
    "NP1-200C": ("NP1-200D", "Stator carrier Rev D, 45 dovetail grooves, rim 104 mm", "S355J2+N"),
    "NP1-201C": ("NP1-201D", "Stator Rev D: 45 tooth-segment stacks, 104 mm (7 magnet rows)", "M270-35A 0.35 mm, self-bonding"),
    "NP1-203C": ("NP1-203D", "Coils on segments, 45 × 28 turns, 104 mm stack", "Cu enamelled Ø1.55 class 200, NKN 0.30"),
    "NP1-210C": ("NP1-210D", "Rotor drum weldment Rev D (shell +30; Rev C fins and ribs, see NP1-210C)", "S355J2+N"),
    "NP1-220E": ("NP1-220F", "Magnets 280 × N45SH 30×15×12 in 7 rows + comb + sleeve", "NdFeB N45SH"),
    "NS6-610": ("NP1-212C", "Drum rear cover with 24 fan blades (Rev C; blades not modelled)", "EN AW-5083-H111"),
}


def drivetrain_parts():
    out = []
    log = {}
    for p in M6.drivetrain_parts():
        p.solid, how = stretch(p.solid, keep=p.pid.startswith(("NS6-915", "NP1-310")))
        log[p.pid] = how
        if p.pid in REV_D:
            p.pid, p.name, p.material = REV_D[p.pid]
            p.drawing = p.pid if p.pid != "NP1-212C" else "NP1-212C"
        if p.pid.startswith("NS6-91"):
            p.pid = p.pid.replace("NS6-", "NM8-")
            p.drawing = "NM8-910"
        if p.pid == "NM8-915":
            p.name = "Spring-applied brake caliper 4.4 kNm (3 per disc, bought)"
            p.mass_kg = 9.0 * 2
        if p.pid == "NP1-220F":
            p.mass_kg = 280 * 30 * 15 * 12 * 7.6e-6 + 3.5
        out.append(p)
    out += top_caliper()
    return out, log


A_TOP = 135.0      # third caliper position (deg from +y towards +z): clear of the rotor lock at 90 and the side brackets


def top_caliper():
    """Third caliper at 135 deg (upper right seen from upwind; the rotor lock holds 90 deg): the FP caliper envelope
    turned about the spindle axis, on a welded bracket bolted (4 x M16) to the rear face of the bedplate front plate."""
    Cc = FP.CALIPER
    y0, y1 = Cc["r"]
    body = box(Cc["x"][0], Cc["x"][1], y0, y1, -Cc["tang"], Cc["tang"])
    body = body.cut(box(Cc["slot_x"][0], Cc["slot_x"][1], y0 - 10, Cc["slot_r"], -Cc["tang"] - 10, Cc["tang"] + 10))
    body = rot_x(body, A_TOP)
    plate = box(Cc["mount_x"][0], Cc["mount_x"][1], y0, y1, -Cc["tang"], Cc["tang"])
    for yy in (y0 + 30, y1 - 30):
        for zz in (-60.0, 60.0):
            plate = plate.cut(cyl_x(Cc["mount_x"][0] - 1, Cc["mount_x"][1] + 1, FP.TAP["M16"] / 2, yy, zz))
    plate = rot_x(plate, A_TOP)
    xr = 480.0 + BPM["inputs"]["t_front"]
    a = math.radians(A_TOP)
    rad, tan = (math.cos(a), math.sin(a)), (-math.sin(a), math.cos(a))
    e1 = (y0 * rad[0] + 80 * tan[0], y0 * rad[1] + 80 * tan[1])
    e2 = (y0 * rad[0] - 80 * tan[0], y0 * rad[1] - 80 * tan[1])
    poly = [(-140.0, 140.0), (-140.0, 240.0), e2, e1, (-245.0, 240.0), (-245.0, 140.0)]
    web = cq.Workplane("YZ", origin=(xr, 0, 0)).polyline(poly).close().extrude(Cc["mount_x"][0] - xr).val()
    foot = box(xr, xr + 25.0, -245.0, -140.0, 140.0, 230.0)
    for yy in (-225.0, -160.0):
        for zz in (160.0, 210.0):
            foot = foot.cut(cyl_x(xr - 1, xr + 26, FP.CLEAR["M16"] / 2, yy, zz))
    br = plate.fuse(web).fuse(foot).clean()
    return [Part("NM8-915-T", "Spring-applied brake caliper 4.4 kNm, third (bought)", to_world(body), "drivetrain", "#b03a2e", "NM8-910",
                 "bought", make_buy="buy", mass_kg=9.0, step=5),
            Part("NM8-311", "Third caliper bracket (135°)", to_world(br), "drivetrain", "#5d7d5d", "NM8-311",
                 "S355J2+N 25 plate, welded", step=5,
                 notes=["foot 4 x M16 through the bedplate front plate, outside the spindle flange bolts"])]


# ================================================================== NACELLE: NP8-300 bedplate
def _bp_geometry():
    spec = importlib.util.spec_from_file_location("bedplate6_m8cad", ROOT / "analysis" / "turbine_6kw" / "bedplate6.py")
    B6 = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(B6)
    v = dict(BPM["inputs"])
    _, geo = B6.geometry(v)
    return v, dict(side_poly=[list(p) for p in geo["side_poly"]], axis_above_bottom_top=-geo["tb"])


M6.BPI, _GEO = _bp_geometry()
M6.BPJ = dict(BPM, **_GEO)


def bedplate_solid():
    """NP8-300: model6.bedplate_solid with the Dpw 410 ring: 16 x Ø18 on PCD 350, bore Ø270, pad unit holes +25."""
    zh, z_orig = M6.zholes, None

    def zholes(solid, n, pcd, dia, z0, z1, start=0.0, c=(0.0, 0.0)):
        if n == 16 and abs(pcd - 300.0) < 1e-6:
            pcd = G.YAW["inner"]["pcd"]
        return zh(solid, n, pcd, dia, z0, z1, start, c)
    cyl0 = M6.cyl

    def cyl_p(r, h, base, d=(0, 0, 1)):
        if abs(r - 110.0) < 1e-6 and tuple(d) == (0, 0, 1) and base[0] == 0 and base[1] == 0:
            r = 135.0
        elif abs(r - 7.0) < 1e-6 and tuple(d) == (0, 0, 1):
            rr = math.hypot(base[0], base[1])
            k = (rr + YAW_DR) / rr
            base = (base[0] * k, base[1] * k, base[2])
        return cyl0(r, h, base, d)
    M6.zholes, M6.cyl = zholes, cyl_p
    try:
        return M6.bedplate_solid()
    finally:
        M6.zholes, M6.cyl = zh, cyl0


M6.COVER["x_front"] = -400.0     # 15 mm further forward than doc 34 so the side calipers stay inside
M6.COVER["bottom_r"] = 430.0     # bottom opening clears the NY-400 friction track (r 420 with the Dpw 410 ring)


def nacelle_parts():
    ps = M6.nacelle_parts()
    ps[0] = Part("NP8-300", "Bedplate weldment 12 kW NP8 (plates 20 / 30 / 10)", bedplate_solid(), "nacelle", "#5d7d5d", "NP8-300",
                 "S355J2+N plates, stress relieved, machined", step=1)
    return ps


# ================================================================== build
_CACHE = None
STRETCH_LOG = {}


def rename(p):
    if p.pid.startswith("NS6-"):
        p.pid = p.pid.replace("NS6-", "NM8-")
    if p.drawing.startswith("NS6-"):
        p.drawing = p.drawing.replace("NS6-", "NM8-")
    p.name = p.name.replace("Dpw 360 z150", "Dpw 410 z165").replace("6 kW", "12 kW")
    return p


def build(tooling=True):
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    parts = []
    parts += nacelle_parts()
    parts += M6.yaw_parts()
    dt, log = drivetrain_parts()
    STRETCH_LOG.update(log)
    parts += dt
    parts += hub_parts()
    parts += rotor_parts()
    parts += M6.tower_parts()
    if tooling:
        M6.blade_solid = blade_solid
        M6.R_ROOT, M6.R_ROT = PB_TOP, R_ROT
        parts += M6.mould_parts()
    parts = [rename(p) for p in parts]
    for p in parts:
        if p.pid == "NM8-400":
            p.name = f"Tower 8 m, Ø{M6.D_BASE:.0f} → Ø{M6.D_TOP:.0f}, t {M6.TG['t_mm'][0]}/{M6.TG['t_mm'][-1]}, one piece"
        if p.pid in ("NM8-911-I", "NM8-911-O"):
            p.mass_kg = 33.0
        if p.pid.startswith("NM8-912"):
            p.name = p.name.replace("0.18 kW 1:1680, brake 2 Nm", "0.25 kW, output ≥ 2.3 kNm static, brake")
        if p.pid == "NM8-600":
            p.name = "Braking / dump resistor box (vented)"
    _CACHE = parts
    return parts


def main():
    ps = build()
    rows, tot = [], {}
    for p in ps:
        m = p.mass()
        bb = p.solid.BoundingBox()
        rows.append(dict(pid=p.pid, name=p.name, group=p.group, drawing=p.drawing, material=p.material, make_buy=p.make_buy,
                         qty=p.qty, mass_kg=None if m is None else round(m, 2), show=p.show, step=p.step,
                         bbox=[round(bb.xmin), round(bb.xmax), round(bb.ymin), round(bb.ymax), round(bb.zmin), round(bb.zmax)]))
        print(f"{p.pid:14s} {p.name[:62]:62s} {p.group:11s} {'' if m is None else f'{m:8.1f}'}")
        if p.show and m is not None:
            tot[p.group] = tot.get(p.group, 0.0) + m
    head = sum(v for k, v in tot.items() if k in ("nacelle", "yaw", "drivetrain", "rotor")) + next(p.mass() for p in ps if p.pid == "NM8-730")
    print({k: round(v) for k, v in tot.items()}, "head above the tower flange", round(head), "tower", TOWER_KEY)
    print("stretch:", STRETCH_LOG)
    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / "model8-parts.json").write_text(json.dumps(dict(parts=rows, group_mass_kg={k: round(v, 1) for k, v in tot.items()},
                                                                    head_kg=round(head, 1), tower=TOWER_KEY, stretch=STRETCH_LOG), indent=1))


if __name__ == "__main__":
    main()
