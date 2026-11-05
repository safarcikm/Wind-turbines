"""Yaw system 3D model (doc 25): CadQuery solids in the nacelle WORLD frame.

WORLD frame (as cad/nacelle_fitcheck): X rearward, Y to the left, Z up, origin
on the yaw axis at the yaw bearing top face (= bedplate underside). Angles
about Z are measured from +X (rear) towards +Y.

Concept (Martin, 2026-11-05): bought slewing ring with external gear z150 m4
(doc 13 / doc 16 interface kept), two passive spring-loaded friction pad units
on the tower-top track, two gearmotors with spring-applied motor brakes, a
manual yaw lock, a gear-driven encoder + cam limit switch, and a cable hanger
for the twist loop. No hydraulics.

All yaw dimensions live in the dicts below (single source for drawings,
clash check and isometric views). Reused unchanged from the fit-check model:
yaw ring envelopes, gearmotor envelopes, drive brackets NP1-420, bedplate and
tower stub.
"""
from __future__ import annotations

import math
import os
import sys

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "nacelle_fitcheck"))
import parts as FP  # noqa: E402

box = FP.box
RHO = 7.85e-6        # kg/mm3 steel

# ------------------------------------------------------------------ NY-400 adapter
AD = dict(
    seat_r=(150.0, 250.0), seat_z=(-95.0, -70.0),        # ring seat, 25 thick
    track_r=(250.0, 395.0), track_z=(-85.0, -70.0),      # friction track, 15 thick, top flush with the seat
    cone_top=(186.0, 198.0), cone_bot=(154.0, 166.0),    # 12 mm cone
    flange_r=(120.0, 210.0), flange_z=(-360.0, -330.0),  # Ø420 / Ø240 x 30 to the tower flange
    gussets=dict(n=8, t=12.0, r=(198.0, 300.0), z_low=-200.0, start=11.25),
    ring_bolts=dict(n=16, size="M16", pcd=440.0, start=0.0),
    tower_bolts=dict(n=16, size="M20", pcd=380.0, start=11.25),
    window=dict(x=(150.0, 240.0), y=(-60.0, 60.0), z=(-300.0, -215.0)),
)

# ------------------------------------------------------------------ NY-410 friction pad unit
# local frame: u radial (outward), v tangential, z up; placed at angle a
PADU = dict(
    angles=(141.8, -141.8),
    pad=dict(u=(325.0, 385.0), v=(-45.0, 45.0), t=12.0, back=6.0),
    bracket=dict(u=(315.0, 440.0), v=(-85.0, 85.0), z=(-20.0, 0.0), bolts=[(340.0, -60.0), (340.0, 60.0), (420.0, -60.0), (420.0, 60.0)]),
    pins=dict(d=25.0, v=(-68.0, 68.0), u=355.0, z=(-56.0, -20.0)),
    upper=dict(u=(318.0, 430.0), v=(-82.0, 82.0), z=(-52.0, -28.0)),    # upper jaw with guide ears
    web=dict(u=(402.0, 427.0), v=(-45.0, 45.0), z=(-165.0, -28.0)),
    lower=dict(u=(305.0, 427.0), v=(-45.0, 45.0), z=(-165.0, -103.0)),
    piston=dict(d=60.0, z=(-113.0, -103.0)),
    stack=dict(d=63.0, z=(-141.0, -113.0)),              # 8 x DIN 2093 B 63 in series, preset 3.7 mm
    plug=dict(d=68.0, z=(-165.0, -141.0)),               # M68 x 2 adjuster with lock nut
    brush=dict(u=(397.0, 402.0), v=(-15.0, 15.0), z=(-84.0, -71.0)),   # lightning contact on the track rim
)

# ------------------------------------------------------------------ NY-430 yaw lock
LOCK = dict(angle=38.2, block=dict(u=(296.0, 386.0), v=(-30.0, 30.0), z=(-60.0, -20.0)),
            housing=dict(u=(310.0, 430.0), v=(-50.0, 50.0), z=(-68.0, 0.0)), screw_d=24.0, travel=14.0)

# ------------------------------------------------------------------ NY-440 encoder + cam limit switch
ENC = dict(angle=-68.0, z_pinion=24, module=4.0, face=(-45.0, -25.0), r=(600.0 + 96.0) / 2,
           bracket=dict(t=15.0), encoder=dict(d=58.0, z=(30.0, 110.0)), cam=dict(d=80.0, z=(115.0, 215.0)))

# ------------------------------------------------------------------ NY-460 cable hanger
HANG = dict(od=168.3, t=4.5, z=(-290.0, 50.0), flange=dict(od=260.0, t=12.0, z=40.0), cleat_z=-290.0)


def rot(s, a):
    return s.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), a)


def ubox(u, v, z):
    return box(u[0], u[1], v[0], v[1], z[0], z[1])


def revolve_z(poly):
    return FP.revolve_z(poly)


# ============================================================ parts
def adapter():
    A = AD
    (s0, s1), (sz0, sz1) = A["seat_r"], A["seat_z"]
    t0, t1 = A["track_r"]
    tz0, tz1 = A["track_z"]
    prof = [(s0, sz0), (t0, sz0), (t0, tz0), (t1, tz0), (t1, tz1), (s0, tz1)]
    ad = revolve_z(prof)
    fz0, fz1 = A["flange_z"]
    ad = ad.fuse(revolve_z([(A["cone_top"][0], sz0 + 1), (A["cone_top"][1], sz0 + 1),
                            (A["cone_bot"][1], fz1), (A["cone_bot"][0], fz1)]))
    ad = ad.fuse(revolve_z([(A["flange_r"][0], fz0), (A["flange_r"][1], fz0), (A["flange_r"][1], fz1), (A["flange_r"][0], fz1)]))
    g = A["gussets"]
    tri = [(g["r"][0] - 4, sz0 + 1), (g["r"][1], sz0 + 1), (g["r"][1], tz0 + 1), (g["r"][1] - 1, tz0 + 1),
           (g["r"][0] - 4, g["z_low"])]
    tri = [(g["r"][0] - 4, sz0 + 1), (250.0, sz0 + 1), (250.0, tz0 + 1), (g["r"][1], tz0 + 1), (g["r"][0] - 4, g["z_low"])]
    for k in range(g["n"]):
        gs = cq.Workplane("XZ").polyline(tri).close().extrude(g["t"] / 2, both=True).val()
        ad = ad.fuse(rot(gs, g["start"] + 360.0 * k / g["n"]))
    ad = ad.clean()
    rb, tb = A["ring_bolts"], A["tower_bolts"]
    ad = FP.zholes(ad, rb["n"], rb["pcd"], FP.CLEAR["M16"], sz0 - 1, sz1 + 1, start=rb["start"])
    ad = FP.zholes(ad, tb["n"], tb["pcd"], FP.CLEAR["M20"], fz0 - 1, fz1 + 1, start=tb["start"])
    w = A["window"]
    ad = ad.cut(box(w["x"][0], w["x"][1], w["y"][0], w["y"][1], w["z"][0], w["z"][1]))
    return ad


def pad_unit(a):
    P = PADU
    out = {}
    br = ubox(P["bracket"]["u"], P["bracket"]["v"], P["bracket"]["z"])
    for (u, v) in P["bracket"]["bolts"]:
        br = br.cut(cq.Solid.makeCylinder(FP.CLEAR["M16"] / 2, 40, cq.Vector(u, v, -30)))
    pins = None
    for v in P["pins"]["v"]:
        c = cq.Solid.makeCylinder(P["pins"]["d"] / 2, P["pins"]["z"][1] - P["pins"]["z"][0],
                                  cq.Vector(P["pins"]["u"], v, P["pins"]["z"][0]))
        pins = c if pins is None else pins.fuse(c)
    frame = ubox(P["upper"]["u"], P["upper"]["v"], P["upper"]["z"])
    frame = frame.fuse(ubox(P["web"]["u"], P["web"]["v"], P["web"]["z"]))
    frame = frame.fuse(ubox(P["lower"]["u"], P["lower"]["v"], P["lower"]["z"])).clean()
    uc = (P["pad"]["u"][0] + P["pad"]["u"][1]) / 2
    # pocket for the piston + stack + plug
    frame = frame.cut(cq.Solid.makeCylinder(P["plug"]["d"] / 2, P["piston"]["z"][1] - P["plug"]["z"][0] + 12,
                                            cq.Vector(uc, 0, P["plug"]["z"][0] - 11)))
    # guide bores in the ears
    for v in P["pins"]["v"]:
        frame = frame.cut(cq.Solid.makeCylinder(P["pins"]["d"] / 2 + 0.5, 60, cq.Vector(P["pins"]["u"], v, -60)))
    pt, pb = P["pad"]["t"], P["pad"]["back"]
    u, vv = P["pad"]["u"], P["pad"]["v"]
    tz1 = AD["track_z"][1]
    tz0 = AD["track_z"][0]
    upad = ubox(u, vv, (tz1, tz1 + pt))
    uback = ubox(u, vv, (tz1 + pt, tz1 + pt + pb))
    lpad = ubox(u, vv, (tz0 - pt, tz0))
    lback = ubox(u, vv, (tz0 - pt - pb, tz0 - pt))
    piston = cq.Solid.makeCylinder(P["piston"]["d"] / 2, 10, cq.Vector(uc, 0, P["piston"]["z"][0]))
    st = P["stack"]
    stack = cq.Solid.makeCylinder(st["d"] / 2, st["z"][1] - st["z"][0], cq.Vector(uc, 0, st["z"][0]))
    stack = stack.cut(cq.Solid.makeCylinder(31.0 / 2, 60, cq.Vector(uc, 0, st["z"][0] - 5)))
    plug = cq.Solid.makeCylinder(P["plug"]["d"] / 2, P["plug"]["z"][1] - P["plug"]["z"][0], cq.Vector(uc, 0, P["plug"]["z"][0]))
    plug = plug.fuse(cq.Workplane("XY", origin=(uc, 0, P["plug"]["z"][0] - 12)).polygon(6, 95).extrude(12).val())
    brush = ubox(P["brush"]["u"], P["brush"]["v"], P["brush"]["z"])
    for k, s in (("bracket", br), ("pins", pins), ("frame", frame), ("pad_upper", upad.fuse(uback)),
                 ("pad_lower", lpad.fuse(lback)), ("piston", piston), ("spring_stack", stack), ("plug", plug),
                 ("brush", brush)):
        out[k] = rot(s, a)
    return out


def lock():
    L = LOCK
    h = ubox(L["housing"]["u"], L["housing"]["v"], L["housing"]["z"])
    h = h.cut(ubox((L["housing"]["u"][0] - 1, L["housing"]["u"][1] - 15), (-31, 31), (-61, -19)))   # slot for the block
    h = h.cut(cq.Solid.makeCylinder(L["screw_d"] / 2 + 1, 40, cq.Vector(L["housing"]["u"][1] - 20, 0, -40), cq.Vector(1, 0, 0)))
    # block engaged (u0 296) with two tooth tips toward the gear
    b = ubox(L["block"]["u"], L["block"]["v"], L["block"]["z"])
    screw = cq.Solid.makeCylinder(L["screw_d"] / 2, 120, cq.Vector(L["block"]["u"][1], 0, -40), cq.Vector(1, 0, 0))
    screw = screw.fuse(cq.Workplane("YZ", origin=(L["block"]["u"][1] + 120, 0, -40)).polygon(6, 41).extrude(16).val())
    return {k: rot(s, L["angle"]) for k, s in (("housing", h), ("block", b), ("screw", screw))}


def lock_block_retracted():
    L = LOCK
    b = ubox((L["block"]["u"][0] + L["travel"], L["block"]["u"][1] + L["travel"]), L["block"]["v"], L["block"]["z"])
    return rot(b, L["angle"])


def encoder():
    E = ENC
    a = math.radians(E["angle"])
    cx, cy = E["r"] * math.cos(a), E["r"] * math.sin(a)
    prof = FP._gear_profile(E["z_pinion"], E["module"], phase=a + math.pi + math.pi / E["z_pinion"])
    z0, z1 = E["face"]
    pin = cq.Workplane("XY", origin=(0, 0, z0)).polyline(prof).close().extrude(z1 - z0).val()
    shaft = cq.Solid.makeCylinder(10.0, E["encoder"]["z"][0] - z1, cq.Vector(0, 0, z1))
    # bracket: horizontal arm (z -20..-5) with bearing boss, vertical plate up the side plate outer face
    arm = box(-35, 35, -35, 35, -8, 7).fuse(cq.Solid.makeCylinder(30, 23, cq.Vector(0, 0, 7)))
    enc = cq.Solid.makeCylinder(E["encoder"]["d"] / 2, E["encoder"]["z"][1] - E["encoder"]["z"][0], cq.Vector(0, 0, E["encoder"]["z"][0]))
    cam = cq.Solid.makeCylinder(E["cam"]["d"] / 2, E["cam"]["z"][1] - E["cam"]["z"][0], cq.Vector(0, 0, E["cam"]["z"][0]))
    tr = cq.Vector(cx, cy, 0)
    # vertical plate on the side plate (y = -260 face) from the arm up to z 230
    vp = box(cx - 35, cx + 35, -275.0, -260.0, -8.0, 230.0)
    link = box(cx - 35, cx + 35, cy + 30, -274.0, -8.0, 7.0)
    return dict(pinion=pin.translate(tr), shaft=shaft.translate(tr), bracket=arm.translate(tr).fuse(vp).fuse(link).clean(),
                encoder=enc.translate(tr), cam_switch=cam.translate(tr))


def hanger():
    Hh = HANG
    t = cq.Solid.makeCylinder(Hh["od"] / 2, Hh["z"][1] - Hh["z"][0], cq.Vector(0, 0, Hh["z"][0]))
    t = t.cut(cq.Solid.makeCylinder(Hh["od"] / 2 - Hh["t"], 1000, cq.Vector(0, 0, -500)))
    f = cq.Solid.makeCylinder(Hh["flange"]["od"] / 2, Hh["flange"]["t"], cq.Vector(0, 0, Hh["flange"]["z"]))
    f = f.cut(cq.Solid.makeCylinder(Hh["od"] / 2 - Hh["t"], 100, cq.Vector(0, 0, 0)))
    cleat = box(-75, 75, -12, 12, Hh["cleat_z"] - 15, Hh["cleat_z"] + 15)
    cables = None
    for k, (y, d) in enumerate(((-45.0, 20.0), (-15.0, 14.0), (12.0, 12.0), (38.0, 12.0))):
        c = cq.Solid.makeCylinder(d / 2, 700, cq.Vector(-30 + 20 * k, y, Hh["cleat_z"] - 450))
        cables = c if cables is None else cables.fuse(c)
    return dict(tube=t.fuse(f).fuse(cleat).clean(), cables=cables)


COL = dict(adapter="#7f8c99", tower="#9a9a90", ring="#d4a63a", drive="#4b5a9c", bracket="#4f7a4f",
           pad_frame="#b8452f", pad="#2a2a2a", spring="#c9b458", pins="#c8c8c8", lock="#6d3f8c",
           encoder="#2f8f8f", hanger="#8a6d4b", cables="#222222", bedplate="#5d7d5d", brush="#b87333")


def assembly(context=True, lock_engaged=True):
    """List of (name, solid, colour)."""
    out = [("NY-400_adapter", adapter(), COL["adapter"])]
    for p in FP.tower_top_parts():
        if p.pid.startswith("tower_top_flange"):
            out.append(("tower_flange_stub", p.solid, COL["tower"]))
    for p in FP.yaw_parts():
        out.append(("ring_" + ("inner" if "inner" in p.pid else "outer"), p.solid, COL["ring"]))
    for p in FP.yaw_drive_parts():
        if "envelope" in p.pid:
            out.append((p.pid.replace("_envelope", ""), p.solid, COL["drive"]))
        else:
            out.append(("NY-420_" + p.pid.split("_")[-1], p.solid, COL["bracket"]))
    for a in PADU["angles"]:
        nm = "L" if a > 0 else "R"
        for k, s in pad_unit(a).items():
            c = dict(bracket=COL["bracket"], pins=COL["pins"], frame=COL["pad_frame"], pad_upper=COL["pad"],
                     pad_lower=COL["pad"], piston=COL["pins"], spring_stack=COL["spring"], plug=COL["pins"],
                     brush=COL["brush"])[k]
            out.append((f"NY-410{nm}_{k}", s, c))
    for k, s in lock().items():
        if k == "block" and not lock_engaged:
            s = lock_block_retracted()
        out.append((f"NY-430_{k}", s, COL["lock"] if k != "screw" else COL["pins"]))
    for k, s in encoder().items():
        out.append((f"NY-440_{k}", s, COL["encoder"] if k not in ("bracket",) else COL["bracket"]))
    for k, s in hanger().items():
        out.append((f"NY-460_{k}", s, COL["hanger"] if k == "tube" else COL["cables"]))
    if context:
        for p in FP.build_parts():
            if p.pid.startswith("NP1-300"):
                out.append(("ctx_" + p.pid, p.solid, COL["bedplate"]))
    return out


def masses():
    m = {"NY-400 adapter (incl. tower-side flange)": adapter().Volume() * RHO}
    pu = pad_unit(141.8)
    m["NY-410 pad unit (each, steel parts)"] = sum(pu[k].Volume() for k in ("bracket", "pins", "frame", "piston", "spring_stack", "plug")) * RHO + 0.6
    m["NY-430 yaw lock"] = sum(s.Volume() for s in lock().values()) * RHO
    e = encoder()
    m["NY-440 encoder unit (steel bracket + pinion) + 2.5 kg instruments"] = (e["bracket"].Volume() + e["pinion"].Volume() + e["shaft"].Volume()) * RHO + 2.5
    m["NY-460 cable hanger"] = hanger()["tube"].Volume() * RHO
    return m


if __name__ == "__main__":
    for k, v in masses().items():
        print(f"{k:70s} {v:6.1f} kg")
