"""Doc 32: dedicated 6 kW bedplate NS6-300 (lighter than the shared 12 kW NP1-300 weldment).

Run: python3 bedplate6.py  -> results/bedplate6.json

Same interfaces as NP1-300 (cad/nacelle_p1/geometry.py BED, doc 14 §4.7; doc 25 yaw parts), so the
spindle, generator, yaw ring, pad units, gearmotor brackets NP1-420 and cable hanger are unchanged:
  * front plate face x 480 on the spindle axis, Ø410 x 10 pad, Ø200 H7 spigot, 12 x M20 PCD 350
  * bottom plate = yaw flange, Ø220 bore, 16 x M16 PCD 300; pad-unit brackets under the front corners
  * side plate outer faces at Y = ±260 (gearmotor brackets NP1-420 bolt there, 4 x M16 at x ±50, z 70/140)
What changes: plate thicknesses (sized here with the 6 kW SLM loads), a shorter rear, a lower side-plate
top line, lightening holes, no rear plate (a 10 mm tie strip instead).
Masses of the 12 kW part are recomputed from its drawing geometry with the same method, because the
150 kg in doc 14 was an early estimate.
"""
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np

HERE = Path(__file__).parent
OUT = HERE / "results"
RHO = 7.85e-6                     # kg/mm3
TILT, X_YAW, H_ROTOR = 5.0, 750.0, 530.0
RC = (-X_YAW, H_ROTOR + 40.0)     # rotor centre, world (X, Z), Z up from the bedplate underside
SLM = json.loads((OUT / "slm_6kw.json").read_text())["ultimate_design_values_gamma_3_kN_kNm"]
FAT = json.loads((OUT / "slm_6kw.json").read_text())["A_fatigue_ranges_kN_kNm"]


def P(s, u):
    t = math.radians(TILT)
    return (RC[0] + math.cos(t) * s + math.sin(t) * u, RC[1] - math.sin(t) * s + math.cos(t) * u)


def area(poly):
    a = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]; x1, y1 = poly[(i + 1) % len(poly)]
        a += x0 * y1 - x1 * y0
    return abs(a) / 2


def geometry(v):
    """Plate list (name, area mm2, thickness mm, count) and key world points for variant dict v."""
    t = math.radians(TILT)
    xf = 480.0
    xr = xf + v["t_front"]
    pf_z = P(xf, 0)[1]
    tb = -(pf_z - v["t_bottom"]) / math.cos(t)            # from the axis down to the bottom plate top
    front_h = v["u_top"] - tb
    front_area = v["front_w"] * front_h - math.pi / 4 * 200 ** 2 - 12 * math.pi / 4 * 22 ** 2 - 2 * math.pi / 4 * 32 ** 2
    front_area -= v.get("front_window", 0.0)                # access / lightening window below the pad
    pad = math.pi / 4 * (410 ** 2 - 200 ** 2)              # Ø410 x 10 pad
    bottom = (v["x_rear"] - v["x_bot_front"]) * v["width"] - math.pi / 4 * 220 ** 2 - 16 * math.pi / 4 * 18 ** 2 - v.get("bottom_cut", 0.0)
    f_top, f_bot = P(xr, v["u_top"]), P(xr, tb - v["t_front"] * math.tan(t))
    side_poly = [f_top, (v["x_rear"], v["z_rear_top"]), (v["x_rear"], v["t_bottom"]), (f_bot[0], v["t_bottom"])]
    side = area(side_poly) - sum(math.pi * h[2] ** 2 for h in v.get("holes", []))
    plates = [("front plate", front_area, v["t_front"], 1), ("front pad", pad, 10.0, 1), ("bottom plate (yaw flange)", bottom, v["t_bottom"], 1),
              ("side plates", side, v["t_side"], 2)]
    if v.get("rear"):
        plates.append(("rear plate", v["rear"][0] * v["rear"][1], v["rear"][2], 1))
    if v.get("gussets"):
        plates.append(("gussets", v["gussets"][0], v["gussets"][1], v["gussets"][2]))
    return plates, dict(tb=tb, f_bot_x=f_bot[0], side_poly=side_poly, front_h=front_h)


def mass(plates, weld_frac=0.03):
    m = {n: round(a * t * c * RHO, 1) for n, a, t, c in plates}
    tot = sum(m.values())
    m["welds, bosses, lifting eyes (+3 %)"] = round(tot * weld_frac, 1)
    return m, round(tot * (1 + weld_frac), 1)


# 12 kW NP1-300 as drawn (cad/nacelle_p1 drawings + cad/nacelle_fitcheck parts.py)
NP1 = dict(t_front=40.0, t_bottom=40.0, t_side=20.0, u_top=250.0, front_w=500.0, width=520.0, x_bot_front=-330.0, x_rear=330.0,
           z_rear_top=330.0, rear=(480.0, 290.0, 20.0))
# 6 kW NS6-300
NS6 = dict(t_front=20.0, t_bottom=25.0, t_side=10.0, front_window=300.0 * 140.0, u_top=230.0, front_w=500.0, width=520.0, x_bot_front=-330.0, x_rear=150.0,
           z_rear_top=200.0, rear=(496.0, 100.0, 10.0),
           bottom_cut=2 * 0.5 * 150 * 150,                     # two rear corner chamfers 150 x 150
           holes=[(-150.0, 360.0, 75.0), (20.0, 260.0, 55.0)],    # lightening holes per side plate (x, z, r)
           gussets=(0.5 * 180 * 180, 12.0, 2))                 # two triangular gussets under the front plate


def section_root(v, geo):
    """Bending section at the front-plate / bottom-plate weld: front plate (flange) + two side plates (webs),
    bending about the lateral (Y) axis; returns W (mm3) at the extreme fibre and the shear area."""
    # side plate root length: from the front plate rear face to where the side plate meets the bottom plate rear
    L = v["x_rear"] - geo["f_bot_x"]
    L_eff = min(L, 450.0)                                     # shear lag: count at most 450 mm of web
    b, tf, tw = v["front_w"], v["t_front"], v["t_side"]
    # x measured rearwards from the front face of the front plate
    parts = [(b * tf, tf / 2, b * tf ** 3 / 12), (2 * tw * L_eff, tf + L_eff / 2, 2 * tw * L_eff ** 3 / 12)]
    A = sum(p[0] for p in parts)
    xc = sum(p[0] * p[1] for p in parts) / A
    I = sum(p[2] + p[0] * (p[1] - xc) ** 2 for p in parts)
    c = max(xc, tf + L_eff - xc)
    return dict(W=I / c, I=I, A_shear=2 * tw * L_eff + b * tf, L_eff=L_eff)


def checks(v, geo, m_ahead=480.0, x_ahead=0.33):
    """Design checks with the 6 kW SLM (gamma included)."""
    fy, gm = 355.0, 1.1
    F_x = SLM["H_parked"]["F_x_shaft"] * 1e3                 # N, parked thrust (largest axial)
    M_sh = max(SLM["B_yaw"]["M_shaft"], SLM["E_max_speed"]["M_shaft"]) * 1e6   # Nmm, shaft bending at the rotor
    T = max(SLM["G_shutdown"]["M_x_shaft"], SLM["F_short_circuit"]["M_x_shaft"]) * 1e6
    W_ahead = 1.35 * m_ahead * 9.81                          # N, rotor + generator + spindle front, factored
    M_flange = M_sh + W_ahead * x_ahead * 1e3                # at the spindle flange
    h_axis = -geo["tb"]                                      # axis height above the bottom plate top, mm
    M_root = F_x * h_axis + M_flange                         # at the front plate / bottom plate weld
    sec = section_root(v, geo)
    s_root = M_root / sec["W"]
    tau = (F_x + W_ahead) / sec["A_shear"]
    s_vm = math.sqrt(s_root ** 2 + 3 * tau ** 2)
    # front plate around the flange: bolt line load carried to the side plates, plate strip between side plates
    n, pcd = 12, 350.0
    Fb = 4 * M_flange / (n * pcd) + F_x / n
    span = v["front_w"] - 2 * v["t_side"]
    q = 4 * Fb / (math.pi * pcd) * 3                         # line load near the top/bottom bolt rows, N/mm (3 bolts per quadrant)
    M_fp = q * (span / 2 - pcd / 2 + 25) ** 2 / 2 + Fb * 30   # strip from the bolt row to the side plate + local bolt bending
    s_front = 6 * M_fp / (pcd / 2 * v["t_front"] ** 2)
    # bottom plate: front-plate line load into the ring bolt circle (lever from the front plate to PCD 300)
    lever = abs(geo["f_bot_x"]) - 150.0
    F_line = M_root / max(sec["L_eff"], 1.0)                 # couple force at the front plate foot
    s_bot = 6 * F_line * lever / (v["width"] * v["t_bottom"] ** 2)
    # yaw ring bolts (unchanged ring, check)
    M_ring = M_root + F_x * v["t_bottom"]
    Fb_ring = 4 * M_ring / (16 * 300.0) - 1.0 * 9.81 * 900 / 16
    # fatigue at the front plate root weld, SLM fatigue ranges, cat 71 cut-off 28.8 MPa / gamma_Mf 1.35
    dM = FAT["dF_x_shaft"] * 1e3 * h_axis + FAT["dM_shaft"] * 1e6
    ds = dM / sec["W"]
    allow = fy / gm
    return dict(M_flange_kNm=round(M_flange / 1e6, 2), M_root_kNm=round(M_root / 1e6, 2), T_kNm=round(T / 1e6, 2),
                root_section=dict(W_cm3=round(sec["W"] / 1e3), sigma_MPa=round(s_root, 1), tau_MPa=round(tau, 1),
                                  vm_MPa=round(s_vm, 1), util=round(s_vm / allow, 2)),
                front_plate=dict(bolt_force_kN=round(Fb / 1e3, 2), sigma_MPa=round(s_front, 1), util=round(s_front / allow, 2)),
                bottom_plate=dict(sigma_MPa=round(s_bot, 1), util=round(s_bot / allow, 2)),
                yaw_bolts=dict(F_bolt_kN=round(Fb_ring / 1e3, 1), F_t_Rd_kN=90.0, util=round(Fb_ring / 90e3, 2)),
                fatigue_root=dict(dsigma_MPa=round(ds, 2), allow_MPa=round(28.8 / 1.35, 1), util=round(ds / (28.8 / 1.35), 2)),
                allow_static_MPa=round(allow))


def main():
    out = {}
    for name, v in (("NP1-300 (12 kW, as drawn)", NP1), ("NS6-300 (6 kW)", NS6)):
        plates, geo = geometry(v)
        m, tot = mass(plates)
        out[name] = dict(inputs=v, masses_kg=m, mass_kg=tot, checks=checks(v, geo),
                         side_poly=[[round(a, 1), round(b, 1)] for a, b in geo["side_poly"]], axis_above_bottom_top=round(-geo["tb"], 1))
    out["saving_kg"] = round(out["NP1-300 (12 kW, as drawn)"]["mass_kg"] - out["NS6-300 (6 kW)"]["mass_kg"], 1)
    (OUT / "bedplate6.json").write_text(json.dumps(out, indent=1))
    # head mass with NS6-300 in place of the shared NP1-300 (doc 30 counted NP1-300 at its 150 kg estimate)
    d6 = json.loads((OUT / "design6.json").read_text())["yaw"]
    m_ns6 = out["NS6-300 (6 kW)"]["mass_kg"]
    m_np1 = out["NP1-300 (12 kW, as drawn)"]["mass_kg"]
    head = dict(doc30_head_kg=d6["m_above_tower_flange_kg"], doc30_bedplate_kg=150.0, NS6_300_kg=m_ns6,
                head_mass_kg=round(d6["m_above_tower_flange_kg"] - 150.0 + m_ns6),
                head_with_shared_NP1_300_as_drawn_kg=round(d6["m_above_tower_flange_kg"] - 150.0 + m_np1))
    (OUT / "head6.json").write_text(json.dumps(head, indent=1))
    out["head"] = head
    (OUT / "bedplate6.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
