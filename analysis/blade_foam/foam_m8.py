"""Doc 41: CNC-machined foam-core blade, wrapped in glass/carbon, for the 12 kW M8 (Ø8.0 m, 131 rpm, 8 m tower).

Run:  python3 foam_m8.py        (~3 min; writes results/foam_m8.json and results/F01..F02 figures)

Reuses the M8 blade model unchanged (analysis/blade/blade.py patched by analysis/variant_m8/structure_m8.py)
and the final M8 loads (variant_m8/results/blade_m8_8m.json, larger of the 18 m and 8 m DLC runs + SLM).
Only the section is replaced:

  mould blade (doc 10/35)  : sandwich shell (1 mm triax / 6 mm PVC / 1 mm triax), caps between two foam-cored webs,
                             caps sized by panel buckling between the webs
  foam-core blade (doc 41) : machined closed-cell foam core fills the section (or a 25 mm foam wall in the
                             hollowed variant); spar block wrapped in biax (= the two webs + a biax ply under the
                             caps); UD caps in pockets machined into the core; outer triax skin wrapped over all.
                             No panel buckling (the core supports every face); instead face wrinkling on the foam:
                                 sigma_wr = 0.5 (E_f E_c G_c)^(1/3)     (Hoff/Allen lower bound)
                             with the same gamma_m as cap buckling (1.35 SLM route, 1.5 aeroelastic route).
                             Mass adds the core, the resin taken up by the cut foam cells, and the fairing filler
                             a male-tool (bag-side) surface needs; the 1.10 allowance of the mould blade
                             (adhesive, paint, LEP, heating) stays on the laminate.
Root (r < 0.75 m, t/c > 0.5): prefabricated glass root tube with the same 12 x M16 inserts as the mould blade;
the foam there is only a 30 mm mandrel wall.
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "variant_m8"))
import common as C                      # noqa: E402  (adds rotor, loads, blade ... to sys.path)
import blade as BLD                     # noqa: E402
import structure_m8 as SM               # noqa: E402

OUT = HERE / "results"; OUT.mkdir(exist_ok=True)

# ------------------------------------------------------------------ foams (characteristic, supplier data sheets)
FOAMS = {
    #  key        rho   E_c[Pa]  G_c[Pa]  tau_c[Pa] alpha[1/K] T_max_cure  note
    "PVC_H80":  (80,  90e6,   27e6,   1.15e6, 40e-6, 70, "cross-linked PVC (Divinycell H80 / Airex C70.75 class)"),
    "PVC_H100": (100, 135e6,  35e6,   1.60e6, 40e-6, 70, "cross-linked PVC (Divinycell H100 class)"),
    "PET_100":  (105, 100e6,  20e6,   0.95e6, 45e-6, 100, "recyclable PET (Airex T92.100 / ArmaPET Struct GR100 class)"),
    "PET_80":   (80,  75e6,   15e6,   0.70e6, 45e-6, 100, "recyclable PET 80 (lowest cost per m3)"),
    "PVC_H200": (200, 310e6,  73e6,   3.50e6, 40e-6, 70, "cross-linked PVC H200, only as a 20 mm strip under the caps"),
}
CAP_STRIP = 0.020          # depth of the high-density strip under each cap (option)
T_SKIN_OUT = 0.0012        # outer triax wrap (2 x 800 g/m2), replaces the 2 x 1 mm skins of the sandwich shell
T_WRAP_MIN = 0.0010        # biax wrap round the spar block (= each web), min 2 x 600 g/m2
RESIN_UPTAKE = 0.30        # kg/m2 of machined foam surface (cut cells, infusion; PVC/PET 80-100, primed)
FILLER = 0.25              # kg/m2 of wetted surface: fairing filler + primer on the bag-side surface
HOLLOW_WALL = 0.025        # foam wall left in the hollowed variant
ROOT_WALL = 0.030          # foam mandrel wall inside the root tube

CFG = dict(foam="PVC_H80", hollow=False, cap_foam=None, knock=1.0)
CORE_KNOCK = 0.85         # core E and G after moisture + freeze-thaw ageing, until our own coupon data (recommended build)


def poly_area(x, y):
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def section_foam(r, c, tc, cap_mat, t_cap, t_web, t_root, cap_core=False):
    rho_c = FOAMS[CFG["foam"]][0]
    x, y, xs, up = BLD.outline(c, tc)
    xn, yn = np.roll(x, -1), np.roll(y, -1)
    ds = np.hypot(xn - x, yn - y)
    xm, ym = 0.5 * (x + xn), 0.5 * (y + yn)
    root = tc >= 0.5
    in_cap = (xs >= BLD.X_CAP0) & (xs <= BLD.X_CAP1) & (tc < 0.9)
    in_te = xs > 0.96
    Et = BLD.MAT["triax"][0]; Eb = BLD.MAT["biax"][0]
    E = np.full_like(ds, Et); t = np.full_like(ds, T_SKIN_OUT + t_root)
    rho_t = t * BLD.MAT["triax"][1]
    # spar cap: outer skin + UD + biax wrap underneath
    Ec = BLD.MAT[cap_mat][0]
    tw = t_web if tc < 0.9 else 0.0
    E = np.where(in_cap, (Ec * t_cap + Et * (T_SKIN_OUT + t_root) + Eb * tw) / (t_cap + T_SKIN_OUT + t_root + tw), E)
    rho_t = np.where(in_cap, rho_t + t_cap * BLD.MAT[cap_mat][1] + tw * BLD.MAT["biax"][1], rho_t)
    t = np.where(in_cap, t + t_cap + tw, t)
    # trailing edge UD strip (as mould blade)
    E = np.where(in_te, (BLD.MAT["UD_glass"][0] * BLD.T_TE + Et * (T_SKIN_OUT + t_root)) / (BLD.T_TE + T_SKIN_OUT + t_root), E)
    rho_t = np.where(in_te, rho_t + BLD.T_TE * BLD.MAT["UD_glass"][1], rho_t)
    t = np.where(in_te, t + BLD.T_TE, t)
    EA_s = E * t * ds
    webs = []
    if tc < 0.9:
        for xw in (BLD.X_CAP0, BLD.X_CAP1):
            ytw = 5 * min(tc, 0.3) * (0.2969 * math.sqrt(xw) - 0.1260 * xw - 0.3516 * xw ** 2 + 0.2843 * xw ** 3 - 0.1036 * xw ** 4) * c
            webs.append((xw * c, 2 * ytw))
    EA = EA_s.sum() + sum(Eb * tw * h for _, h in webs)
    xc = (np.sum(EA_s * xm) + sum(Eb * tw * h * xw for xw, h in webs)) / EA
    yc = np.sum(EA_s * ym) / EA_s.sum()
    EIf = np.sum(EA_s * (ym - yc) ** 2) + sum(Eb * tw * h ** 3 / 12 for _, h in webs)
    EIe = np.sum(EA_s * (xm - xc) ** 2) + sum(Eb * tw * h * (xw - xc) ** 2 for xw, h in webs)
    # core: inside the laminate, solid or hollowed; root tube region only a mandrel wall
    A_in = max(poly_area(x, y) - np.sum(t * ds) - sum(tw * h for _, h in webs), 0.0)
    perim = float(np.sum(ds))
    if root:
        A_core = min(A_in, perim * ROOT_WALL)
    elif CFG["hollow"]:
        A_core = min(A_in, perim * HOLLOW_WALL + sum(2 * HOLLOW_WALL * h for _, h in webs))
    else:
        A_core = A_in
    cut_surface = perim + sum(2 * h for _, h in webs) + (perim if (CFG["hollow"] or root) and A_core < A_in else 0.0)
    m_lam = (np.sum(rho_t * ds) + sum(BLD.MAT["biax"][1] * tw * h for _, h in webs)) * 1.10
    m_strip = 0.0
    if CFG["cap_foam"] and not root and tc < 0.9:
        m_strip = 2 * CAP_STRIP * (BLD.X_CAP1 - BLD.X_CAP0) * c * (FOAMS[CFG["cap_foam"]][0] - rho_c)
    mass = m_lam + rho_c * A_core + m_strip + RESIN_UPTAKE * cut_surface + FILLER * perim
    h_spar = max([h for _, h in webs], default=c * tc)
    return dict(EA=EA, EIf=EIf, EIe=EIe, mass=mass, xm=xm - xc, ym=ym - yc, in_cap=in_cap, in_te=in_te,
                h_spar=h_spar, b_cap=(BLD.X_CAP1 - BLD.X_CAP0) * c, t_cap=t_cap, E_pt=E, t_pt=t, c=c, tc=tc, webs=webs,
                cap_core=False, m_core=rho_c * A_core + m_strip, root=root,
                m_cap=float(np.sum(np.where(in_cap, t_cap * BLD.MAT[cap_mat][1], 0.0) * ds)),
                m_lam=m_lam, m_uptake=RESIN_UPTAKE * cut_surface, m_filler=FILLER * perim, perim=perim)


_check_orig = BLD.check_station


def check_foam(sec, M, cap_mat):
    u = _check_orig(sec, M, cap_mat)
    u.pop("buckling_cap", None); u.pop("buckling_panel", None)
    _, Ecore, Gcore, tau_c, *_ = FOAMS[CFG["foam"]]
    if sec["root"] or sec["tc"] >= 0.9:
        return u
    cap = sec["in_cap"]; rest = ~cap & ~sec["in_te"]
    def eps_wr(Ef):
        return 0.5 * (Ef * Ecore * Gcore * CFG["knock"] ** 2) ** (1 / 3) / Ef
    for key, mask in (("wrinkling_cap", cap), ("wrinkling_skin", rest)):
        if key == "wrinkling_cap" and CFG["cap_foam"]:
            _, Ecore, Gcore, *_ = FOAMS[CFG["cap_foam"]]
        else:
            _, Ecore, Gcore, *_ = FOAMS[CFG["foam"]]
        Ef = float(np.mean(sec["E_pt"][mask]))
        lim_slm, lim_sim = eps_wr(Ef) / BLD.GM_ULT_SLM, eps_wr(Ef) / BLD.GM_BUCK
        e_slm = np.max(np.abs(BLD.strains(sec, M["H"], 0.0)[mask]))
        e_sim = np.max(np.abs(BLD.strains(sec, M["SIM"], 0.0)[mask]))
        e_g = np.max(np.abs(BLD.strains(sec, 0.0, M["G"])[mask]))
        u[key] = max(e_slm / lim_slm, e_sim / lim_sim, e_g / lim_slm)
    return u


def run(cap_mat, foam, hollow, cap_foam=None, knock=1.0, t_root_wall=0.016):
    CFG.update(foam=foam, hollow=hollow, cap_foam=cap_foam, knock=knock)
    BLD.section, BLD.check_station = section_foam, check_foam
    d = BLD.design(cap_mat, t_root_wall=t_root_wall)
    d["f_flap_rated_Hz"] = round(float(BLD.beam_modes(d["_r"], d["_EIf"], d["_mu"], rpm=C.RPM)[0]), 2)
    d["f_edge_rated_Hz"] = round(float(BLD.beam_modes(d["_r"], d["_EIe"], d["_mu"], rpm=C.RPM)[0]), 2)
    d["f_flap_maxrpm_Hz"] = round(float(BLD.beam_modes(d["_r"], d["_EIf"], d["_mu"], rpm=C.RPM_MAX)[0]), 2)
    # core volume and mass split
    secs = [section_foam(d["_r"][i], d["stations"]["chord"][i], d["stations"]["t_over_c"][i], cap_mat,
                         d["_tcap"][i], d["stations"]["t_web_mm"][i] / 1000, d["stations"]["t_root_extra_mm"][i] / 1000)
            for i in range(len(d["_r"]))]
    m_core = float(np.trapezoid([s["m_core"] for s in secs], d["_r"]))
    integ = lambda k: round(float(np.trapezoid([s[k] for s in secs], d["_r"])), 2)
    d["mass_split_kg"] = dict(core=integ("m_core"), cap_laminate=integ("m_cap"),
                              glass_laminate_incl_10pct=round(integ("m_lam") - integ("m_cap"), 2),
                              resin_uptake=integ("m_uptake"), filler_primer=integ("m_filler"), inserts_fittings=1.5)
    d["wetted_area_m2"] = integ("perim")
    d["core_mass_kg"] = round(m_core, 2)
    d["core_volume_m3"] = round(m_core / FOAMS[foam][0], 4)
    d["cap_UD_mass_kg"] = round(float(np.trapezoid(d["_tcap"] * (BLD.X_CAP1 - BLD.X_CAP0) * np.array(d["stations"]["chord"]) * 2
                                                    * BLD.MAT[cap_mat][1], d["_r"])), 2)
    d["foam"], d["hollow"] = FOAMS[foam][6], hollow
    BLD.section, BLD.check_station = SECTION_MOULD, _check_orig
    return d


SECTION_MOULD = BLD.section


def thermal_check(foam):
    """Skin/core mismatch from post-cure (60 C stress-free) down to -40 C: foam in-plane stress at the interface."""
    rho, Ec, Gc, tau, a_f, Tmax, _ = FOAMS[foam]
    dT = 100.0
    a_skin = {"carbon cap": 0.5e-6, "glass skin": 11e-6}
    return {k: dict(mismatch_strain_pct=round((a_f - a) * dT * 100, 2),
                    foam_stress_MPa=round(Ec * (a_f - a) * dT / 1e6, 2),
                    foam_tensile_strength_MPa=round(2.2 if "H80" in foam else 3.0 if "H100" in foam else 1.6, 2))
            for k, a in a_skin.items()}


def main():
    ref = json.loads((ROOT / "variant_m8" / "results" / "blade_m8_8m.json").read_text())
    loads = ref["loads_used"]
    SM.patch_blade(loads)
    BLD.LOADS = loads
    cases = [
        ("mould_carbon_ref", None),
        ("foam_H80_carbon", ("UD_carbon", "PVC_H80", False)),
        ("foam_H80_glass", ("UD_glass", "PVC_H80", False)),
        ("foam_H100_glass", ("UD_glass", "PVC_H100", False)),
        ("foam_PET100_glass", ("UD_glass", "PET_100", False)),
        ("foam_PET80_glass", ("UD_glass", "PET_80", False)),
        ("foam_H80_glass_hollow", ("UD_glass", "PVC_H80", True)),
        ("foam_H80_carbon_hollow", ("UD_carbon", "PVC_H80", True)),
        ("foam_H100_carbon", ("UD_carbon", "PVC_H100", False)),
        ("foam_PET100_carbon", ("UD_carbon", "PET_100", False)),
        ("foam_H80_carbon_H200strip", ("UD_carbon", "PVC_H80", False, "PVC_H200")),
        ("foam_H80_glass_H200strip", ("UD_glass", "PVC_H80", False, "PVC_H200")),
        ("RECOMMENDED_foam_H80_carbon_aged", ("UD_carbon", "PVC_H80", False, None, CORE_KNOCK)),
    ]
    res, keep = {}, {}
    for name, spec in cases:
        if spec is None:
            d = BLD.design("UD_carbon", t_root_wall=0.016)
            d["f_flap_rated_Hz"] = round(float(BLD.beam_modes(d["_r"], d["_EIf"], d["_mu"], rpm=C.RPM)[0]), 2)
            d["f_edge_rated_Hz"] = round(float(BLD.beam_modes(d["_r"], d["_EIe"], d["_mu"], rpm=C.RPM)[0]), 2)
            d["f_flap_maxrpm_Hz"] = round(float(BLD.beam_modes(d["_r"], d["_EIf"], d["_mu"], rpm=C.RPM_MAX)[0]), 2)
        else:
            d = run(*spec)
        keep[name] = dict(r=d["_r"], mu=d["_mu"], EIf=d["_EIf"], tcap=d["_tcap"])
        for k in ("_r", "_mu", "_EIf", "_EIe", "_tcap", "f_flap_178rpm_Hz", "f_edge_178rpm_Hz"):
            d.pop(k, None)
        d["three_P_rated_Hz"] = round(3 * C.RPM / 60, 2)
        d["flap_over_3P"] = round(d["f_flap_rated_Hz"] / (3 * C.RPM / 60), 2)
        res[name] = d
        if "core_mass_kg" in d:
            d["cap_UD_root_mm"] = d["stations"]["t_cap_mm"][len(d["stations"]["r"]) // 8]
        print(f"{name:26s} {d['mass_kg']:6.2f} kg  S {d['static_moment_kgm_about_axis']:6.2f}  flap {d['f_flap_rated_Hz']:5.2f} Hz"
              f" ({d['flap_over_3P']:.2f}x3P)  tip {d['tip_deflection_m']:.3f} m  core {d.get('core_mass_kg', '-')}"
              f" capUD {d.get('cap_UD_mass_kg','-')} kg"
              f"  maxutil {max(d['max_util'].values()):.2f} {max(d['max_util'], key=d['max_util'].get)}")
    res["thermal_-40C"] = {f: thermal_check(f) for f in ("PVC_H80", "PET_100")}
    res["loads_used"] = loads
    res["assumptions"] = dict(T_SKIN_OUT=T_SKIN_OUT, T_WRAP_MIN=T_WRAP_MIN, RESIN_UPTAKE=RESIN_UPTAKE, FILLER=FILLER,
                              HOLLOW_WALL=HOLLOW_WALL, ROOT_WALL=ROOT_WALL,
                              foams={k: dict(rho=v[0], E_MPa=v[1] / 1e6, G_MPa=v[2] / 1e6, tau_MPa=v[3] / 1e6,
                                             alpha=v[4], T_max_cure_C=v[5], note=v[6]) for k, v in FOAMS.items()})
    (OUT / "foam_m8.json").write_text(json.dumps(res, indent=1))
    plots(keep, res)


def plots(keep, res):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    show = [("mould_carbon_ref", "Mould blade, carbon caps (doc 35)", "k"),
            ("foam_H80_carbon", "Foam core H80, carbon caps", "C3"),
            ("foam_H80_glass", "Foam core H80, glass caps", "C0"),
            ("RECOMMENDED_foam_H80_carbon_aged", "Foam core H80, carbon planks, aged core (recommended)", "C2")]
    fig, ax = plt.subplots(1, 3, figsize=(14, 4.2))
    for k, lab, col in show:
        d = keep[k]
        ax[0].plot(d["r"], d["mu"], col, label=f"{lab}: {res[k]['mass_kg']:.1f} kg")
        ax[1].plot(d["r"], d["tcap"] * 1000, col, label=lab)
        ax[2].semilogy(d["r"], d["EIf"] / 1e3, col, label=f"{lab}: {res[k]['f_flap_rated_Hz']:.1f} Hz")
    ax[0].set_ylabel("Mass per metre [kg/m]"); ax[1].set_ylabel("Spar cap UD thickness [mm]")
    ax[2].set_ylabel("Flap stiffness EI [kNm²]")
    for a in ax:
        a.set_xlabel("Radius [m]"); a.grid(alpha=0.3); a.legend(fontsize=7)
    fig.suptitle("M8 blade: mould-built vs CNC foam-core wrapped (same loads, same outline)")
    fig.tight_layout(); fig.savefig(OUT / "F01-foam-vs-mould.png", dpi=120)


if __name__ == "__main__":
    main()
