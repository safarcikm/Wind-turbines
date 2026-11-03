"""Working prototype W1: parts added to the Rev B fit-check model (doc 17).

The fit-check model (../nacelle_fitcheck/parts.py) holds every nacelle part
from the hub flange to the tower mounting point. W1 adds what is needed to make
the printed nacelle move and sense like the real turbine:

  NW-500  hub (printed twin of the doc 13 ductile iron hub, same interfaces)
  NW-510  pitch bearing twins x 3: outer ring + inner ring with internal gear
          z48 m3, real 25.4 mm steel balls through a filling plug
  NW-520  pitch drive brackets x 3 + bought pitch drive envelopes
          (48 V servo + 1:100 planetary + z14 m3 pinion)
  NW-525  pitch encoder brackets x 3 + absolute encoder envelopes (z16 m3)
  NW-530  blade root stubs x 3 (Ø220, 10 x M16 on PCD 200)
  hub electronics boxes x 3 (pitch controller + supercap module), slip ring
  with integrated rotor encoder at the spindle nose (envelopes)

Frames as in parts.py: spindle frame x rearward from the rotor plane, y lateral,
z up, then to_world(). A blade-axis part is built along +z (s = distance from
the rotor axis) and turned to its pitch axis with blade_axis().
"""
from __future__ import annotations

import math
import os
import sys

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "nacelle_fitcheck"))
sys.path.insert(0, os.path.join(HERE, "..", "nacelle_p1"))
import parts as PT          # noqa: E402
import geometry as G        # noqa: E402
import gears                # noqa: E402

Part, to_world, cyl_x, box = PT.Part, PT.to_world, PT.cyl_x, PT.box
TAP, CLEAR, c = PT.TAP, PT.CLEAR, PT.PRINT_CLEARANCE

BLADE_ANGLES = (90.0, 210.0, 330.0)        # blade 1 up (front view angle from +y towards +z)

HUB = dict(R=220.0, wall=10.0, neck_r=(130.0, 165.0), neck_s0=140.0, seat_s=350.0,
           rear_tube=dict(x=(110.0, 175.0), r=(170.0, 185.0)),
           front=dict(x=(-205.0, -150.0), r=(125.0, 150.0), bolts=dict(n=8, size="M12", pcd=275.0)),
           neck_bolts=dict(n=16, size="M16", pcd=300.0))
PB = dict(dpw=250.0, ball=25.4, n_balls=27,
          outer=dict(s=(350.0, 400.0), r=(127.5, 177.5)),
          inner=dict(s=(352.0, 402.0), r_out=122.5),
          gear=dict(z=48, m=3.0), blade_bolts=dict(n=10, size="M16", pcd=200.0))
DRIVE = dict(pinion_z=14, offset_x=-51.0, pinion_s=(362.0, 392.0), gearbox=dict(d=70.0, s=(233.0, 348.0)),
             motor=dict(d=80.0, s=(103.0, 233.0)), bracket_s=(318.0, 333.0))
ENC = dict(z=16, offset_x=48.0, pinion_s=(365.0, 385.0), body=dict(d=58.0, s=(280.0, 340.0)),
           bracket_s=(340.0, 352.0))


def blade_axis(shape, a_deg):
    """Local blade frame (x = rotor axis, z = blade axis) -> spindle frame for blade at a_deg."""
    return shape.rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), a_deg - 90.0)


def zcyl(r, s0, s1, x=0.0, y=0.0):
    return cq.Solid.makeCylinder(r, s1 - s0, cq.Vector(x, y, s0), cq.Vector(0, 0, 1))


def ring(r0, r1, s0, s1):
    return zcyl(r1, s0, s1).cut(zcyl(r0, s0 - 1, s1 + 1))


def zholes(solid, n, pcd, dia, s0, s1, start=0.0):
    for k in range(n):
        a = math.radians(start + 360.0 * k / n)
        solid = solid.cut(zcyl(dia / 2, s0, s1, pcd / 2 * math.cos(a), pcd / 2 * math.sin(a)))
    return solid


def prism(pts, s0, s1, x=0.0, y=0.0):
    return cq.Workplane("XY", origin=(x, y, s0)).polyline(pts).close().extrude(s1 - s0).val()


# ------------------------------------------------------------------ hub
def hub():
    H = HUB
    rt, fr = H["rear_tube"], H["front"]
    x_cut = rt["x"][0] - 20.0                                  # sphere is trimmed behind this plane
    body = cq.Workplane().sphere(H["R"]).val()
    body = body.cut(box(x_cut, 400, -400, 400, -400, 400))
    for a in BLADE_ANGLES:
        body = body.fuse(blade_axis(zcyl(H["neck_r"][1], H["neck_s0"], H["seat_s"]), a))
    # rear tube + flange in one revolved profile (flange as the corrected dummy hub: Ø470, Ø361 recess)
    rear = [(x_cut - 10, rt["r"][0]), (190.0, rt["r"][0]), (190.0, 180.5), (200.0, 180.5), (200.0, 235.0),
            (175.0, 235.0), (175.0, rt["r"][1]), (x_cut - 10, rt["r"][1])]
    body = body.fuse(PT.revolve(rear))
    body = body.fuse(PT.revolve([(fr["x"][0], fr["r"][0]), (fr["x"][1], fr["r"][0]),
                                 (fr["x"][1], fr["r"][1]), (fr["x"][0], fr["r"][1])])).clean()
    cav = cq.Workplane().sphere(H["R"] - H["wall"]).val().cut(box(x_cut - 10, 400, -400, 400, -400, 400))
    body = body.cut(cav)
    body = body.cut(cyl_x(x_cut - 15, 205.0, rt["r"][0]))      # rear opening to the drum
    body = body.cut(cyl_x(-300.0, -100.0, fr["r"][0]))         # front access opening Ø250
    nb = H["neck_bolts"]
    for a in BLADE_ANGLES:
        cut = zcyl(H["neck_r"][0], 100.0, H["seat_s"] + 1)
        for k in range(nb["n"]):
            q = math.radians(360.0 * k / nb["n"] + 360.0 / nb["n"] / 2)
            cut = cut.fuse(zcyl(TAP["M16"] / 2, H["seat_s"] - 30, H["seat_s"] + 1,
                                nb["pcd"] / 2 * math.cos(q), nb["pcd"] / 2 * math.sin(q)))
        body = body.cut(blade_axis(cut, a))
    body = PT.bolt_holes(body, 12, 400.0, CLEAR["M16"], 170, 205)
    fb = fr["bolts"]
    body = PT.bolt_holes(body, fb["n"], fb["pcd"], TAP["M12"], fr["x"][0] - 1, fr["x"][0] + 25, start=22.5)
    body = body.clean()
    assert body.isValid() and body.Volume() > 0, "hub solid invalid"
    return Part("NW-500_hub", "Hub, printed twin of the EN-GJS-400-18U-LT casting (doc 13)", to_world(body),
                "rotating", "NW-500 (doc 17 §3)", (0.55, 0.6, 0.5), axis=None,
                print_mods=["Ø470 x 760 overall: print in 4 pieces if the printer is smaller (split on the y-z and x-z planes, "
                            "glue + M8 bolted ribs)",
                            "walls 10 as the casting; necks printed r 130 to 165"],
                notes=["interfaces = real hub: 12 x M16 PCD 400 + Ø361 recess to the drum; 16 x M16 PCD 300 per neck "
                       "(pitch bearing outer ring); front opening Ø250 with 8 x M12 PCD 275 (cover or bench drive adapter)"])


# ------------------------------------------------------------ pitch system
def pitch_bearing(a):
    O, I, g = PB["outer"], PB["inner"], PB["gear"]
    s_mid = (O["s"][0] + O["s"][1]) / 2
    rb = PB["ball"] / 2 + 0.2
    groove = cq.Solid.makeTorus(PB["dpw"] / 2, rb, cq.Vector(0, 0, s_mid), cq.Vector(0, 0, 1))
    outer = ring(O["r"][0], O["r"][1], *O["s"]).cut(groove)
    outer = zholes(outer, 16, HUB["neck_bolts"]["pcd"], CLEAR["M16"], O["s"][0] - 1, O["s"][1] + 1,
                   start=360.0 / 32)
    plug_hole = cq.Solid.makeCylinder(PB["ball"] / 2 + 0.5, 80, cq.Vector(0, PB["dpw"] / 2 - 5, s_mid), cq.Vector(0, 1, 0))
    outer = outer.cut(plug_hole)
    plug = cq.Solid.makeCylinder(PB["ball"] / 2 + 0.3, O["r"][1] - O["r"][0] + 2.0,
                                 cq.Vector(0, O["r"][0] - 1.0, s_mid), cq.Vector(0, 1, 0)).cut(groove)
    inner = zcyl(I["r_out"], *I["s"]).cut(groove)
    inner = inner.cut(prism(gears.internal_cutter(g["z"], g["m"]), I["s"][0] - 1, I["s"][1] + 1))
    bb = PB["blade_bolts"]
    inner = zholes(inner, bb["n"], bb["pcd"], TAP["M16"], I["s"][0] - 1, I["s"][1] + 1, start=18.0)
    n = int(a)
    out = [Part(f"NW-510-{n:03d}_pitch_bearing_outer_ring", f"Pitch bearing outer ring, blade at {n}° (printed twin)",
                to_world(blade_axis(outer, a)), "rotating", "NW-510 (doc 17 §3)", (0.8, 0.65, 0.2), axis=None,
                notes=["same envelope and bolt pattern as the doc 13 slewing ring (Ø355 x 50, Dpw 250): swap 1:1",
                       f"{PB['n_balls']} real steel balls Ø25.4 G40 + printed spacers through the filling plug"]),
           Part(f"NW-510-{n:03d}_pitch_bearing_inner_ring", f"Pitch bearing inner ring, internal gear z48 m3, blade at {n}°",
                to_world(blade_axis(inner, a)), "rotating", "NW-510 (doc 17 §3)", (0.85, 0.7, 0.25), axis=None,
                notes=["involute z48 m3, 0.3 mm backlash; 10 x M16 tapped PCD 200 for the blade root"]),
           Part(f"NW-511-{n:03d}_ball_filling_plug", f"Ball filling plug, blade at {n}°", to_world(blade_axis(plug, a)),
                "rotating", "NW-511", (0.9, 0.8, 0.3), axis=None, notes=["held by a Ø4 pin in the real ring; glue or pin in print"])]
    return out


def pitch_drive(a):
    D, g = DRIVE, PB["gear"]
    n = int(a)
    cd = (g["z"] - D["pinion_z"]) * g["m"] / 2
    x0 = -cd                                                   # pinion axis offset towards the front
    # z14 has a tooth centre at 180 deg and the z48 ring a tooth space there: phase 0 meshes
    pin = prism(gears.external(D["pinion_z"], g["m"], phase=0.0), *D["pinion_s"], x=x0)
    pin = pin.fuse(zcyl(12.0, D["gearbox"]["s"][1] - 1, D["pinion_s"][0] + 1, x=x0))
    pin = pin.fuse(zcyl(D["gearbox"]["d"] / 2, *D["gearbox"]["s"], x=x0))
    pin = pin.fuse(zcyl(D["motor"]["d"] / 2, *D["motor"]["s"], x=x0)).clean()
    br = zcyl(HUB["neck_r"][0] - c, *D["bracket_s"])
    br = br.cut(zcyl(D["gearbox"]["d"] / 2 + 1.0, D["bracket_s"][0] - 1, D["bracket_s"][1] + 1, x=x0))
    br = br.cut(zcyl(ENC["body"]["d"] / 2 + 6, D["bracket_s"][0] - 1, D["bracket_s"][1] + 1, x=ENC["offset_x"]))
    for yy in (-85.0, 85.0):                                   # cable / air holes
        br = br.cut(zcyl(18.0, D["bracket_s"][0] - 1, D["bracket_s"][1] + 1, 0.0, yy))
    enc = prism(gears.external(ENC["z"], g["m"], phase=0.0), *ENC["pinion_s"], x=ENC["offset_x"])
    enc = enc.fuse(zcyl(5.0, ENC["body"]["s"][1] - 1, ENC["pinion_s"][0] + 1, x=ENC["offset_x"]))
    enc = enc.fuse(zcyl(ENC["body"]["d"] / 2, *ENC["body"]["s"], x=ENC["offset_x"])).clean()
    return [Part(f"pitch_drive_{n:03d}_envelope", f"Pitch drive: 48 V servo + 1:100 planetary + z14 m3 pinion ({n}°)",
                 to_world(blade_axis(pin, a)), "rotating", "doc 13 §5 / doc 17 §4 (bought)", (0.3, 0.3, 0.6),
                 make_buy="buy (envelope)", axis=None,
                 notes=["motor Ø80 x 130 with brake + encoder, gearbox Ø70 x 115, pinion face 30, centre distance 51"]),
            Part(f"NW-520-{n:03d}_pitch_drive_bracket", f"Pitch drive bracket in the hub neck ({n}°)",
                 to_world(blade_axis(br, a)), "rotating", "NW-520 (doc 17 §3)", (0.3, 0.45, 0.3), axis=None,
                 notes=["15 mm plate, slip fit in the Ø260 neck bore, 3 radial M8 into the neck; gearbox flange 4 x M6",
                        "the cast hub gets a machined pad at the same place: same bracket, steel"]),
            Part(f"pitch_encoder_{n:03d}_envelope", f"Absolute pitch encoder Ø58 with z16 m3 pinion ({n}°)",
                 to_world(blade_axis(enc, a)), "rotating", "doc 13 §5 / doc 17 §5 (bought)", (0.2, 0.2, 0.2),
                 make_buy="buy (envelope)", axis=None, notes=["gear-driven from the ring gear, 1:3 ratio; multiturn SSI or CANopen"])]


def blade_stub(a):
    s0 = PB["inner"]["s"][1]
    st = ring(90.0, 110.0, s0, s0 + 250.0)
    st = zholes(st, PB["blade_bolts"]["n"], PB["blade_bolts"]["pcd"], CLEAR["M16"], s0 - 1, s0 + 40, start=18.0)
    # 0° pitch mark and a 90° feather mark on the stub, for the pitch calibration
    st = st.cut(zcyl(3.0, s0 + 200, s0 + 251, x=-110.0))
    n = int(a)
    return Part(f"NW-530-{n:03d}_blade_root_stub", f"Blade root stub Ø220 x 250 ({n}°)", to_world(blade_axis(st, a)),
                "rotating", "NW-530 (doc 17 §3)", (0.9, 0.9, 0.85), axis=None,
                notes=["W1: printed stub to carry test masses and the pitch marks; real blade root (doc 10) bolts to the same 10 x M16"])


def hub_electronics():
    out = []
    for a in (30.0, 150.0, 270.0):
        b = box(-80.0, 80.0, -60.0, 60.0, 105.0, 175.0)
        out.append(Part(f"hub_electronics_{int(a):03d}_envelope",
                        f"Pitch controller + supercapacitor module box ({int(a)}°)",
                        to_world(blade_axis(b, a)), "rotating", "doc 13 §5 / doc 17 §5 (bought + assembled)",
                        (0.15, 0.35, 0.15), make_buy="buy (envelope)", axis=None,
                        notes=["160 x 120 x 70: 48 V servo drive with STO + 21 x 350 F supercaps (56.7 V), heater pad"]))
    sr = cyl_x(-80.0, 38.0, 50.0)
    out.append(Part("slip_ring_encoder_envelope", "Slip ring with integrated rotor encoder (envelope)", to_world(sr),
                    "stationary", "doc 13 §5 / doc 17 §5 (bought)", (0.2, 0.2, 0.2), make_buy="buy (envelope)",
                    axis="spindle",
                    notes=["stator held in the spindle nose cap, rotor driven by a torque fork from the hub front cover",
                           "48 V 2 x 30 A, CAN FD, 2-channel safety chain, Ethernet; encoder ≥ 1024 ppr"]))
    return out


def yaw_twin():
    """Printed twins of the yaw slewing ring (replace the fit-check envelopes):
    same rings and holes, plus a ball groove for 53 real Ø19.05 balls and a
    filling plug, so the nacelle really turns on the printed adapter."""
    out = []
    groove = cq.Solid.makeTorus(G.YAW["d_pw"] / 2, G.YAW["ball"] / 2 + 0.3, cq.Vector(0, 0, -35.0), cq.Vector(0, 0, 1))
    for p in PT.yaw_parts():
        sol = p.solid.cut(groove)
        if "outer" in p.pid:
            sol = sol.cut(cq.Solid.makeCylinder(G.YAW["ball"] / 2 + 0.5, 140, cq.Vector(G.YAW["d_pw"] / 2 - 5, 0, -35.0),
                                                cq.Vector(1, 0, 0)))
        out.append(Part(p.pid.replace("_envelope", "_twin").replace("yaw_bearing", "NW-430_yaw_bearing"),
                        p.name + " – printed twin with ball groove", sol, p.group, "NW-430 (doc 17 §3)", p.color,
                        axis="yaw", notes=["53 real Ø19.05 G40 balls + printed spacers through the plug at +X; "
                                           "same bolt patterns as the slewing ring, swap 1:1"]))
    return out


def build_w_parts():
    P = [hub()]
    P += yaw_twin()
    for a in BLADE_ANGLES:
        P += pitch_bearing(a)
        P += pitch_drive(a)
        P.append(blade_stub(a))
    P += hub_electronics()
    return P


if __name__ == "__main__":
    for p in build_w_parts():
        bb = p.solid.BoundingBox()
        print(f"{p.pid:45s} {bb.xlen:7.1f} {bb.ylen:7.1f} {bb.zlen:7.1f}  vol {p.solid.Volume() / 1e3:8.1f} cm3")
