"""Doc 33: timber (wood-epoxy) blades for the 6 kW S6 rotor, and a quick look at the 12 kW rotor.

Run:  python3 timber6.py          (6 kW S6, doc 31 loads, writes results/timber6.json, ~10 s)
      python3 timber6.py 12kw     (12 kW Ø7.5 m rotor, doc 08/10 loads, writes results/timber12.json)

Section model and loads are those of the glass blade (analysis/blade/blade.py, docs 10/30/31):
SLM H parked (governing), SLM G edgewise, SLM E centrifugal, aeroelastic extreme, flap/edge DELs.
Two timber constructions are sized station by station:

  shell   moulded hollow shell of wood veneer / epoxy (Gougeon "WEST" method): UD veneer spar caps,
          veneer shell wall, birch plywood shear webs, no foam. Same two-half mould principle as glass.
  carved  laminated lamellae glued into two blank halves, CNC carved outside and hollowed inside to a
          wall thickness t_w (solid where the section is too thin to hollow), then glued together.

Each in Douglas fir (DF) or Sitka spruce (SS), on the S6 planform with the glass blade's thickness
("std": 30 % at max chord) and with thicker inboard airfoils ("thick": 40 % at max chord, 32 % at
mid-span), which is how wooden blades are normally drawn.

Every timber blade gets a glass/epoxy sheath (2 x 300 g/m2) and PU leading-edge protection.
Wood values are characteristic, along the grain, for an epoxy-encapsulated laminate at 12 % moisture
(Gougeon/NASA wood-epoxy data, Spera ch. 8), times K_MOD = 0.80 for moisture up to ~15 %, +40 °C skin
temperature and load duration (Eurocode 5 style). S-N slope m = 13 (29 % of static at 10^7). The doc 31
DELs were rainflowed with m = 10 and are multiplied by K_DEL = 1.3 for m = 13.
They must be replaced by coupon tests of the chosen veneer supply before a design release.
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).parent
MODE_12 = len(sys.argv) > 1 and sys.argv[1] == "12kw"
sys.argv = sys.argv[:1]
if MODE_12:
    sys.path.insert(0, str(HERE.parent / "blade"))
    import blade as BLD  # noqa: E402
    RPM, RPM_MAX, OUT = 178.0, 250.0, HERE / "results"
else:
    import design6 as D  # noqa: E402
    BLD = D.BLD
    RPM, RPM_MAX, OUT = D.RPM, D.RPM_MAX, D.OUT

K_MOD, K_DEL = 0.80, 1.3
WOOD = {
    #     E_span  rho  eps_t   eps_c   m  E_trans  note
    "DF": (15.0e9, 600, 0.0050, 0.0032, 13, 1.6e9, "Douglas fir rotary veneer 2.5 mm / epoxy, ~10 % cross plies"),
    "SS": (11.5e9, 470, 0.0055, 0.0029, 13, 1.2e9, "Sitka spruce veneer / epoxy, ~10 % cross plies"),
}
PLY = (9.0e9, 700, 0.0045, 0.0030, 12, "birch plywood / epoxy webs")
G_PLY, GAMMA_PLY = 0.62e9, 0.0129          # plywood panel shear modulus and characteristic shear strain (8 MPa)
T_WALL_MIN_HALF = 0.0015                    # moulded shell wall 2 x 1.5 mm veneer outside the caps (minimum)
SHEATH = 2 * 0.300 * 1.9                    # kg/m2: glass + epoxy sheath
LEP = 0.35                                  # kg/m2 PU tape/coating, on the leading 15 % of the perimeter
STEP, T_MAX = 0.0005, 0.080
ROOT_BLOCK = (0.30, 0.060)                  # carved builds: first 0.30 m with >= 60 mm wall to seat the glued-in studs
M_ROOT_FITTINGS = 2.5                       # glued-in studs, root end plate


# ------------------------------------------------------------------ geometry
def set_thickness(kind):
    """Thickness distribution in the doc 10 (12 kW) coordinates, scaled to the S6 span as design6.patch_blade."""
    std = [(0.40, 1.00), (0.55, 0.70), (0.775, 0.30), (1.5, 0.25), (2.25, 0.21), (3.2, 0.18)]
    thick = [(0.40, 1.00), (0.55, 0.75), (0.775, 0.40), (1.5, 0.32), (2.25, 0.24), (3.2, 0.19)]
    xthick = [(0.40, 1.00), (0.55, 0.80), (0.775, 0.45), (1.5, 0.38), (2.25, 0.30), (3.2, 0.21)]
    pts = dict(std=std, thick=thick, xthick=xthick)[kind]
    if MODE_12:
        pts = pts + [(3.75, 0.18)]
    else:
        k = (D.R - D.R_HUB) / (3.75 - 0.40)
        pts = [(D.R_HUB + (r - 0.40) * k, tc) for r, tc in pts] + [(D.R, 0.18)]
    x, y = zip(*pts)
    BLD.t_over_c = lambda r: float(np.interp(r, x, y))


def stations():
    r = np.linspace(BLD.R_HUB, BLD.R, 41)
    c = np.interp(r, BLD.BL.r, BLD.BL.chord, left=BLD.BL.chord[0])
    tc = np.array([BLD.t_over_c(x) for x in r])
    return r, c, tc


def perimeter(c, tc):
    x, y = BLD.outline(c, tc)[:2]
    return float(np.sum(np.hypot(np.diff(np.r_[x, x[0]]), np.diff(np.r_[y, y[0]]))))


def set_wood(sp):
    """Swap blade.py's material table and constants for a wood-epoxy shell of species sp."""
    E, rho, et, ec, m, Et, note = WOOD[sp]
    BLD.MAT["UD_wood"] = (E, rho, et * K_MOD, ec * K_MOD, m, note)
    BLD.MAT["triax"] = (E * 0.90, rho, et * K_MOD, ec * K_MOD, m, note + " (shell wall)")
    BLD.MAT["biax"] = (PLY[0], PLY[1], PLY[2] * K_MOD, PLY[3] * K_MOD, PLY[4], PLY[5])
    BLD.E_TRANS.update(UD_wood=Et, triax=Et * 1.5, biax=PLY[0] * 0.6)
    BLD.G_BIAX, BLD.GAMMA_SHEAR = G_PLY, GAMMA_PLY * K_MOD
    BLD.T_SKIN, BLD.T_CORE, BLD.RHO_CORE, BLD.T_CORE_WEB = T_WALL_MIN_HALF, 0.0, 0.0, 0.0
    BLD.T_TE = 0.002                          # glass UD trailing-edge strip kept


def station_loads(r, mu):
    m_park, m_op, m_g = BLD.load_shapes(r, mu)
    L = BLD.LOADS
    om = L["rpm_max"] * math.pi / 30
    N = L["gamma_E"] * np.array([np.sum(mu[i:] * r[i:] * np.gradient(r)[i:]) for i in range(len(r))]) * om ** 2
    V = -np.gradient(m_park * L["SLM_H_flap"], r)
    return [dict(H=L["SLM_H_flap"] * m_park[i], G=L["SLM_G_edge"] * m_g[i], N=N[i], SIM=L["SIM_res"] * m_park[i],
                 DELf=K_DEL * L["DEL_flap"] * m_op[i], DELe=K_DEL * L["DEL_edge"] * m_g[i], V=max(V[i], 1.0))
            for i in range(len(r))], m_op


def common_out(r, c, tc, mu, EIf, EIe, m_op, utils):
    L = BLD.LOADS
    mass = float(np.trapezoid(mu, r)) + M_ROOT_FITTINGS
    sm = float(np.trapezoid(mu * r, r))
    return dict(mass_kg=round(mass, 1), static_moment_kgm=round(sm, 1), r_cog_m=round(sm / (mass - M_ROOT_FITTINGS), 2),
                f_flap_Hz=round(float(BLD.beam_modes(r, EIf, mu)[0]), 1), f_edge_Hz=round(float(BLD.beam_modes(r, EIe, mu)[0]), 1),
                f_flap_rated_Hz=round(float(BLD.beam_modes(r, EIf, mu, rpm=RPM)[0]), 1),
                f_flap_over_3P=round(float(BLD.beam_modes(r, EIf, mu, rpm=RPM)[0]) / (3 * RPM / 60), 2),
                tip_deflection_m=round(BLD.tip_deflection(r, EIf / BLD.GM_STIFF, L["SIM_op_flap"] * m_op), 3),
                max_util={k: round(max(u.get(k, 0) for u in utils), 2) for k in sorted({kk for u in utils for kk in u})},
                governing=max({k: max(u.get(k, 0) for u in utils) for k in {kk for u in utils for kk in u}}.items(), key=lambda kv: kv[1])[0])


# ------------------------------------------------------------------ moulded veneer shell
def thick_wall(s, c, tc, tw):
    """blade.py is a thin-wall model: all laminate sits on the outer surface. Wood laminates are thick
    (20-40 mm caps in a 100 mm deep section), so EA/EI are recomputed with each wall element at its
    mid-thickness (offset inward along the normal) plus its own t^3/12 term. Strains stay evaluated
    at the outer surface. Web height is reduced by the caps."""
    x, y = BLD.outline(c, tc)[:2]
    xn, yn = np.roll(x, -1), np.roll(y, -1)
    ds = np.hypot(xn - x, yn - y)
    xm, ym = 0.5 * (x + xn), 0.5 * (y + yn)
    tx, ty = (xn - x) / ds, (yn - y) / ds
    A2 = np.sum(x * yn - xn * y)
    nx, ny = (-ty, tx) if A2 > 0 else (ty, -tx)              # inward normal
    t = s["t_pt"]; E = s["E_pt"]
    xi, yi = xm + nx * t / 2, ym + ny * t / 2
    EA_s = E * t * ds
    webs = [(xw, max(h - 2 * float(np.max(np.where(s["in_cap"], t, 0))), 0.2 * h)) for xw, h in s["webs"]]
    Ew = BLD.MAT["biax"][0]
    EA = EA_s.sum() + sum(Ew * tw * h for _, h in webs)
    xc = (np.sum(EA_s * xi) + sum(Ew * tw * h * xw for xw, h in webs)) / EA
    yc = np.sum(EA_s * yi) / EA_s.sum()
    own_f = E * ds * t ** 3 / 12 * ny ** 2                     # own bending of near-horizontal faces
    own_e = E * ds * t ** 3 / 12 * (nx ** 2)
    EIf = np.sum(EA_s * (yi - yc) ** 2 + own_f) + sum(Ew * tw * h ** 3 / 12 for _, h in webs)
    EIe = np.sum(EA_s * (xi - xc) ** 2 + own_e) + sum(Ew * tw * h * (xw - xc) ** 2 for xw, h in webs)
    s.update(EA=EA, EIf=EIf, EIe=EIe, xm=xm - xc, ym=ym - yc, EIf_thin=s["EIf"])
    return s


def shell(sp):
    set_wood(sp)
    r, c, tc = stations()
    n = len(r)
    t_cap, t_wall, t_web = np.full(n, 0.001), np.zeros(n), np.full(n, 0.006)
    mu = np.full(n, 6.0)

    def sec(i):
        # the shell wall is solid veneer: blade.py's skin thickness is set per station (no core)
        BLD.T_SKIN = T_WALL_MIN_HALF + 0.5 * t_wall[i]
        return thick_wall(BLD.section(r[i], c[i], tc[i], "UD_wood", t_cap[i], t_web[i], 0.0), c[i], tc[i], t_web[i])

    for _ in range(8):
        M, m_op = station_loads(r, mu)
        utils = []
        for i in range(n):
            while True:
                s = sec(i); s["_t_web"] = t_web[i]
                u = BLD.check_station(s, M[i], "UD_wood")
                worst = max(u, key=u.get)
                if u[worst] <= 1.0 or max(t_cap[i], t_wall[i], t_web[i]) >= T_MAX:
                    break
                if worst == "web_shear":
                    t_web[i] += STEP
                elif tc[i] >= 0.9 or worst.startswith(("buckling_panel", "SLM_G", "SIM_edge")):
                    t_wall[i] += STEP
                else:
                    t_cap[i] += STEP
            utils.append(u)
        t_cap = np.maximum.accumulate(t_cap[::-1])[::-1]
        secs = [sec(i) for i in range(n)]
        mu_new = np.array([s["mass"] for s in secs]) + np.array([perimeter(ci, ti) for ci, ti in zip(c, tc)]) * (SHEATH + 0.15 * LEP)
        if np.max(np.abs(mu_new - mu)) < 0.02:
            mu = mu_new
            break
        mu = mu_new
    EIf = np.array([s["EIf"] for s in secs]); EIe = np.array([s["EIe"] for s in secs])
    out = common_out(r, c, tc, mu, EIf, EIe, m_op, utils)
    out.update(t_cap_max_mm=round(t_cap.max() * 1000, 1), t_wall_extra_max_mm=round(t_wall.max() * 1000, 1),
               t_web_max_mm=round(t_web.max() * 1000, 1),
               stations=dict(r=r.round(3).tolist(), chord=c.round(3).tolist(), t_over_c=tc.round(3).tolist(),
                             t_cap_mm=(t_cap * 1000).round(1).tolist(), t_wall_extra_mm=(t_wall * 1000).round(1).tolist(),
                             mass_per_m=mu.round(2).tolist()))
    return out


# ------------------------------------------------------------------ carved laminated, hollowed
def poly(x, y):
    xn, yn = np.roll(x, -1), np.roll(y, -1)
    cr = x * yn - xn * y
    A2 = cr.sum()
    A = 0.5 * A2
    cx = np.sum((x + xn) * cr) / (3 * A2); cy = np.sum((y + yn) * cr) / (3 * A2)
    Ixx = np.sum((y ** 2 + y * yn + yn ** 2) * cr) / 12; Iyy = np.sum((x ** 2 + x * xn + xn ** 2) * cr) / 12
    return abs(A), cx, cy, abs(Ixx), abs(Iyy), np.sign(A2)


def carved_section(c, tc, t_w, E, rho):
    """Outer outline minus an inner cavity offset by t_w (approximated by a scaled outline)."""
    x, y = BLD.outline(c, tc)[:2]
    A, cx, cy, Ixx0, Iyy0, _ = poly(x, y)
    Ixx, Iyy = Ixx0 - A * cy ** 2, Iyy0 - A * cx ** 2
    thick = c * tc
    hollow = thick - 2 * t_w > 0.25 * thick and (tc >= 0.9 or c - 3 * t_w > 0.3 * c)
    if hollow:
        ci = c - (2.0 if tc >= 0.9 else 3.0) * t_w   # LE and TE keep more wood than the faces
        tci = (thick - 2 * t_w) / ci
        xi, yi = BLD.outline(ci, min(tci, 1.0))[:2]
        xi = xi + (1.0 if tc >= 0.9 else 1.2) * t_w
        Ai, cxi, cyi, Ixxi0, Iyyi0, _ = poly(xi, yi)
        A_s = A - Ai
        cxs = (A * cx - Ai * cxi) / A_s; cys = (A * cy - Ai * cyi) / A_s
        Ixx = (Ixx0 - Ixxi0) - A_s * cys ** 2; Iyy = (Iyy0 - Iyyi0) - A_s * cxs ** 2
        A, cx, cy = A_s, cxs, cys
    per = float(np.sum(np.hypot(np.diff(np.r_[x, x[0]]), np.diff(np.r_[y, y[0]]))))
    return dict(EA=E * A, EIf=E * Ixx, EIe=E * Iyy, mass=rho * A * 1.03 + per * (SHEATH + 0.15 * LEP),
                ymax=float(np.max(np.abs(y - cy))), xmax=float(np.max(np.abs(x - cx))), hollow=hollow)


def carved(sp):
    E, rho, et, ec, m, Et, note = WOOD[sp]
    et, ec = et * K_MOD, ec * K_MOD
    r, c, tc = stations()
    n = len(r)
    t_w = np.where(r < BLD.R_HUB + ROOT_BLOCK[0], ROOT_BLOCK[1], 0.010)
    mu = np.full(n, 8.0)
    fat = 2 * ec * 1e7 ** (-1 / m) / BLD.GM_FAT
    for _ in range(8):
        M, m_op = station_loads(r, mu)
        utils = []
        for i in range(n):
            while True:
                s = carved_section(c[i], tc[i], t_w[i], E, rho)
                kf, ke = s["ymax"] / s["EIf"], s["xmax"] / s["EIe"]
                u = dict(SLM_H=M[i]["H"] * kf / (ec / BLD.GM_ULT_SLM), SLM_G=M[i]["G"] * ke / (ec / BLD.GM_ULT_SLM),
                         SLM_E=M[i]["N"] / s["EA"] / (et / BLD.GM_ULT_SLM),
                         SIM_flap=M[i]["SIM"] * kf / (ec / BLD.GM_ULT_SIM), SIM_edge=M[i]["SIM"] * ke / (ec / BLD.GM_ULT_SIM),
                         fatigue=(M[i]["DELf"] * kf + M[i]["DELe"] * ke) / fat)
                if max(u.values()) <= 1.0 or not s["hollow"]:
                    break
                t_w[i] += STEP
            utils.append(u)
        secs = [carved_section(c[i], tc[i], t_w[i], E, rho) for i in range(n)]
        mu_new = np.array([s["mass"] for s in secs])
        if np.max(np.abs(mu_new - mu)) < 0.02:
            mu = mu_new
            break
        mu = mu_new
    EIf = np.array([s["EIf"] for s in secs]); EIe = np.array([s["EIe"] for s in secs])
    out = common_out(r, c, tc, mu, EIf, EIe, m_op, utils)
    solid_r = r[[not s["hollow"] for s in secs]]
    out.update(t_wall_max_mm=round(t_w.max() * 1000, 1),
               solid_zone_m=[round(float(solid_r.min()), 2), round(float(solid_r.max()), 2)] if len(solid_r) else None,
               stations=dict(r=r.round(3).tolist(), chord=c.round(3).tolist(), t_over_c=tc.round(3).tolist(),
                             t_wall_mm=(t_w * 1000).round(1).tolist(), hollow=[s["hollow"] for s in secs],
                             mass_per_m=mu.round(2).tolist()))
    return out


# ------------------------------------------------------------------ carved wood + carbon strips
CF = (125e9, 1580, 0.0085)                  # pultruded carbon strip: E, rho, characteristic compressive strain
B_CF = 0.25                                 # strip width / chord, one strip in each face over the spar zone
T_W_HYB = 0.015                             # hollowed wall where the section is deep enough


def hybrid(sp):
    """Carved, hollowed wood blade with pultruded carbon strips bonded into routed pockets in both faces
    (under the glass sheath). Wood outer-fibre strain governs (wood fails at ~1/3 of the carbon strain)."""
    E, rho, et, ec, m, Et, note = WOOD[sp]
    et, ec = et * K_MOD, ec * K_MOD
    r, c, tc = stations()
    n = len(r)
    t_cf = np.zeros(n)
    t_w = np.where(r < BLD.R_HUB + ROOT_BLOCK[0], ROOT_BLOCK[1], T_W_HYB)
    mu = np.full(n, 6.0)
    fat = 2 * ec * 1e7 ** (-1 / m) / BLD.GM_FAT

    def sec(i):
        s = carved_section(c[i], tc[i], t_w[i], E, rho)
        b, y = B_CF * c[i], s["ymax"] - t_cf[i] / 2
        EA_cf = CF[0] * 2 * b * t_cf[i]
        s["EIf"] += EA_cf * y ** 2
        s["EIe"] += EA_cf * (0.05 * c[i]) ** 2
        s["EA"] += EA_cf
        s["mass"] += CF[1] * 2 * b * t_cf[i] * 1.1
        return s

    for _ in range(8):
        M, m_op = station_loads(r, mu)
        utils = []
        for i in range(n):
            while True:
                s = sec(i)
                kf, ke = s["ymax"] / s["EIf"], s["xmax"] / s["EIe"]
                u = dict(SLM_H=M[i]["H"] * kf / (ec / BLD.GM_ULT_SLM), SLM_G=M[i]["G"] * ke / (ec / BLD.GM_ULT_SLM),
                         SLM_E=M[i]["N"] / s["EA"] / (et / BLD.GM_ULT_SLM),
                         SIM_flap=M[i]["SIM"] * kf / (ec / BLD.GM_ULT_SIM), SIM_edge=M[i]["SIM"] * ke / (ec / BLD.GM_ULT_SIM),
                         fatigue=(M[i]["DELf"] * kf + M[i]["DELe"] * ke) / fat)
                worst = max(u, key=u.get)
                if u[worst] <= 1.0:
                    break
                if (tc[i] > 0.5 or worst in ("SLM_G", "SIM_edge")) and s["hollow"]:
                    t_w[i] += STEP                   # root tube and edgewise: more wood in the wall
                elif t_cf[i] < 0.012:
                    t_cf[i] += 0.0005
                else:
                    break
            utils.append(u)
        secs = [sec(i) for i in range(n)]
        mu_new = np.array([s["mass"] for s in secs])
        if np.max(np.abs(mu_new - mu)) < 0.02:
            mu = mu_new
            break
        mu = mu_new
    EIf = np.array([s["EIf"] for s in secs]); EIe = np.array([s["EIe"] for s in secs])
    out = common_out(r, c, tc, mu, EIf, EIe, m_op, utils)
    zone = r[t_cf > 0]
    out.update(t_carbon_max_mm=round(t_cf.max() * 1000, 1), t_wall_max_mm=round(t_w.max() * 1000, 1),
               carbon_zone_m=[round(float(zone.min()), 2), round(float(zone.max()), 2)] if len(zone) else None,
               carbon_kg=round(float(np.trapezoid(CF[1] * 2 * B_CF * c * t_cf * 1.1, r)), 2),
               stations=dict(r=r.round(3).tolist(), chord=c.round(3).tolist(), t_over_c=tc.round(3).tolist(),
                             t_carbon_mm=(t_cf * 1000).round(1).tolist(), t_wall_mm=(t_w * 1000).round(1).tolist(), mass_per_m=mu.round(2).tolist()))
    return out


# ------------------------------------------------------------------ aero cost of thicker airfoils
def aero_penalty():
    """Cp at the design tip speed ratio with section drag scaled by the Hoerner form factor
    FF = 1 + 2 t/c + 60 (t/c)^4 relative to the glass blade's thickness. BEM annuli are independent,
    so each annulus takes the torque of the polar that matches its own drag ratio. Lift is left
    unchanged (thick sections also lose some clmax and are more roughness-sensitive: optimistic)."""
    if MODE_12:
        return None
    from bem import CLEAN, Polar, solve
    bl = D.blade_shape(n=30)
    V = 7.0
    om = D.TSR * V / D.R
    ff = lambda t: 1 + 2 * t + 60 * t ** 4
    ratios = np.linspace(1.0, 2.0, 11)
    dQ = []
    for k in ratios:
        p = Polar("scaled", cl0=CLEAN.cl0, cla=CLEAN.cla, clmax=CLEAN.clmax, cd0=CLEAN.cd0 * k, kd=CLEAN.kd * k,
                  cl_cdmin=CLEAN.cl_cdmin, cdmax=CLEAN.cdmax)
        dQ.append(solve(bl, V, om, D.REG["PF"], 1.225, p).dQ)
    dQ = np.array(dQ)
    out = {}
    set_thickness("std"); tc0 = np.array([BLD.t_over_c(x) for x in bl.r])
    base = float(np.sum(dQ[0]))
    for geo in ("std", "thick", "xthick"):
        set_thickness(geo)
        tc = np.array([BLD.t_over_c(x) for x in bl.r])
        k = np.clip(ff(np.minimum(tc, 0.45)) / ff(np.minimum(tc0, 0.45)), 1.0, 2.0)
        q = sum(np.interp(k[j], ratios, dQ[:, j]) for j in range(len(bl.r)))
        out[geo] = dict(cp_ratio=round(float(q / base), 4), tc_at_r=dict(zip([round(float(x), 2) for x in bl.r[::6]], tc[::6].round(3).tolist())))
    return out


# ------------------------------------------------------------------ root joint
def root_joint(M, N, D_root=0.22):
    """Glued-in threaded studs (Gougeon / Riberholt type) in a laminated root, axial force per stud
    against steel (8.8) and bond shear. Bond 6.0 MPa characteristic (Douglas fir / epoxy) x K_MOD / 1.5."""
    out = {}
    Dbc = D_root - 0.04
    for size, As, d in (("M16", 157e-6, 0.016), ("M20", 245e-6, 0.020)):
        Ft_rd = 0.9 * 800e6 * As / 1.25
        for n in (10, 12, 14, 16, 18, 20):
            F = 4 * M / (n * Dbc) + N / n
            pitch = math.pi * Dbc / n
            hit = None
            for l_over_d in (10, 12, 15, 18, 20):
                l = l_over_d * d
                Fb = 6.0e6 * K_MOD / 1.5 * math.pi * (d + 0.002) * l * (1 - 0.0015 * l_over_d)
                if F <= min(Ft_rd, Fb) and pitch >= 2.5 * d:
                    hit = dict(studs=n, bolt_circle_m=round(Dbc, 3), embed_mm=round(l * 1000), F_stud_kN=round(F / 1e3, 1),
                               F_bond_Rd_kN=round(Fb / 1e3, 1), F_t_Rd_kN=round(Ft_rd / 1e3, 1), pitch_mm=round(pitch * 1000))
                    break
            if hit:
                out[size] = hit
                break
    return out


def main():
    if MODE_12:
        base = json.loads((BLD.OUT / "blade_summary.json").read_text())
        out = dict(loads_used_Nm=BLD.LOADS,
                   glass_doc10={k: base["glass"][k] for k in ("mass_kg", "f_flap_Hz", "f_edge_Hz", "f_flap_178rpm_Hz", "tip_deflection_m")},
                   carbon_doc10={k: base["carbon"][k] for k in ("mass_kg", "f_flap_Hz", "f_edge_Hz", "f_flap_178rpm_Hz", "tip_deflection_m")})
        ref_sm = base["carbon"]["static_moment_kgm_about_axis"]
        name = "timber12.json"
    else:
        R6 = json.loads((OUT / "recheck6.json").read_text())
        L = R6["blade"]["loads_used_Nm"]
        D.patch_blade(L)
        g = R6["blade"]["glass"]
        out = dict(loads_used_Nm=L, glass_doc31=dict(mass_kg=g["mass_kg"], static_moment_kgm=g["static_moment_kgm_about_axis"],
                                                     f_flap_Hz=g["f_flap_Hz"], f_edge_Hz=g["f_edge_Hz"], f_flap_rated_Hz=g["f_flap_rpm_Hz"],
                                                     f_flap_over_3P=round(g["f_flap_rpm_Hz"] / (3 * RPM / 60), 2),
                                                     tip_deflection_m=g["tip_deflection_m"]))
        ref_sm = g["static_moment_kgm_about_axis"]
        name = "timber6.json"
    out["factors"] = dict(K_MOD=K_MOD, K_DEL=K_DEL, gamma_m_SLM=BLD.GM_ULT_SLM, gamma_m_SIM=BLD.GM_ULT_SIM, gamma_m_fat=BLD.GM_FAT,
                          wood={k: dict(E_GPa=v[0] / 1e9, rho=v[1], eps_t=v[2], eps_c=v[3], m=v[4], note=v[6]) for k, v in WOOD.items()})
    out["aero"] = aero_penalty()
    for geo in ("std", "thick", "xthick"):
        set_thickness(geo)
        for sp in ("DF", "SS"):
            out[f"shell_{sp}_{geo}"] = shell(sp)
            out[f"carved_{sp}_{geo}"] = carved(sp)
            out[f"hybrid_{sp}_{geo}"] = hybrid(sp)
    w = RPM_MAX * math.pi / 30
    for k in [k for k in out if k.startswith(("shell", "carved", "hybrid"))]:
        v = out[k]
        v["static_moment_ratio_vs_ref"] = round(v["static_moment_kgm"] / ref_sm, 2)
        v["root_joint"] = root_joint(BLD.LOADS["SLM_H_flap"], 3.0 * v["static_moment_kgm"] * w ** 2)
    (OUT / name).write_text(json.dumps(out, indent=1, default=float))
    print(f"{'option':20s} {'kg':>6s} {'Sm':>6s} {'f_fl':>5s} {'f_ed':>5s} {'/3P':>5s} {'tip':>6s} {'max u':>6s} govern  extra")
    for k, v in out.items():
        if isinstance(v, dict) and "mass_kg" in v:
            mu = max(v["max_util"].values()) if "max_util" in v else float("nan")
            ex = {kk: v[kk] for kk in ("t_cap_max_mm", "t_wall_extra_max_mm", "t_web_max_mm", "t_wall_max_mm", "solid_zone_m", "t_carbon_max_mm", "carbon_zone_m", "carbon_kg") if kk in v}
            print(f"{k:20s} {v['mass_kg']:6.1f} {v.get('static_moment_kgm', v.get('static_moment_kgm_about_axis', 0)):6.1f} {v['f_flap_Hz']:5.1f} "
                  f"{v['f_edge_Hz']:5.1f} {v.get('f_flap_over_3P', 0):5.2f} {v['tip_deflection_m']:6.3f} {mu:6.2f} {v.get('governing', '')} {ex}")
            if "root_joint" in v:
                print("    root:", v["root_joint"])


if __name__ == "__main__":
    main()
