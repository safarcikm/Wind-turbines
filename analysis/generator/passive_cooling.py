"""Generator Rev C: passive cooling study (doc 23 §4a).

Everything here is passive: no electric fan, no pump, no power. Parts that turn with the rotor
(fins, cover blades) move air only because the rotor turns.

Run:  python3 passive_cooling.py   -> results/passive_cooling.json

Thermal network: doc 06 model (thermal.py) with the Rev C losses, as checks_rc.py.
Fin areas come from the drawn geometry (cad/nacelle_p1/geometry.py, Rev C):
- inner fins: 36 L-shaped 3 mm steel plates in the front cavity, welded to the hub web and the shell bore
  (x 220 to 312, r 262 to 312, plus a web leg x 220 to 250, r 140 to 262); the end windings start at x 321
- rear cover blades: 24 radial blades on NP1-212C (Rev C as drawn)
- outer ribs: 48 axial 4 mm flat bars on the drum outside, x 222 to 430, tips Ø676 (clear of the brake disc at 435)
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.argv = sys.argv[:1]
sys.path.insert(0, str(HERE))
import checks_rc as CK  # noqa: E402
import thermal as TH  # noqa: E402
sys.path.insert(0, str(HERE.parent.parent / "cad" / "nacelle_p1"))
import geometry as G  # noqa: E402

K_STEEL = 50.0
RHO_STEEL = 7850.0


def fin_eff(h, t, H):
    """Straight rectangular fin, adiabatic tip (corrected length)."""
    m = math.sqrt(2 * h / (K_STEEL * t))
    Lc = H + t / 2
    return math.tanh(m * Lc) / (m * Lc)


def inner_area0():
    return math.pi * TH.D_DRUM * (TH.L_DRUM - TH.L) + 2 * math.pi * TH.D_DRUM ** 2 / 4


def outer_area0():
    return math.pi * TH.D_DRUM * TH.L_DRUM + math.pi * TH.D_DRUM ** 2 / 4


def inner_fins(h_int=25.0):
    f = G.ROTOR_FINS
    n, t = f["n"], f["t"] / 1000
    a_plate = ((f["x1"] - f["x0"]) * (f["r1"] - f["r0"]) + (f["leg_x1"] - f["x0"]) * (f["r0"] - f["leg_r0"])) * 1e-6
    area = n * 2 * a_plate                                       # both sides [m2]
    eff = fin_eff(h_int, t, (f["r1"] - f["r0"]) / 1000)
    mass = n * a_plate * t * RHO_STEEL
    return dict(n=n, t_mm=t * 1e3, area_m2=round(area, 3), eff=round(eff, 2), mass_kg=round(mass, 1),
                add=area * eff)


def outer_ribs(n=None, t=None, H=None, h_out=45.0):
    rb = G.DRUM_RIBS
    n = n or rb["n"]
    t = t or rb["t"] / 1000
    H = H or (rb["r_tip"] - 320.5) / 1000                         # mean height over the r 318 / r 323 shell
    Lr = (rb["x1"] - rb["x0"]) / 1000
    area = n * (2 * H + t) * Lr
    eff = fin_eff(h_out, t, H)
    mass = n * H * t * Lr * RHO_STEEL
    return dict(n=n, t_mm=t * 1e3, height_mm=H * 1e3, area_m2=round(area, 3), eff=round(eff, 2),
                mass_kg=round(mass, 1), add=area * eff)


def main():
    CK.thermal()                                  # sets the Rev C module values in thermal.py
    A_in, A_out = inner_area0(), outer_area0()
    blades = 0.07                                 # NP1-212C blades, fin_in share (doc 23 §4)
    fi = inner_fins()
    ro = outer_ribs()
    ro_big = outer_ribs(n=60, H=0.0275)              # tips at Ø696
    f_in = 1 + fi["add"] / A_in
    f_out = 1 + ro["add"] / A_out
    f_out_big = 1 + ro_big["add"] / A_out
    base = dict(support_R=0.33)
    # h_int: inside air coefficient. 15 = smooth drum stirring the air (doc 06), 40 = with blades (doc 06).
    # Inner fins in the front cavity are a rotor-driven impeller too; 25 is a middle estimate for them alone.
    configs = {
        "A_no_cooling_parts": dict(h_int_run=15, fin_in=1.0, fin_out=1.0),
        "B_cover_blades_RevC": dict(h_int_run=40, fin_in=1 + blades, fin_out=1.0),
        "C_inner_fins_only_h15": dict(h_int_run=15, fin_in=f_in, fin_out=1.0),
        "C_inner_fins_only_h25": dict(h_int_run=25, fin_in=f_in, fin_out=1.0),
        "D_outer_ribs_only": dict(h_int_run=15, fin_in=1.0, fin_out=f_out),
        "E_inner_fins_outer_ribs_h25": dict(h_int_run=25, fin_in=f_in, fin_out=f_out),
        "F_blades_inner_fins": dict(h_int_run=40, fin_in=f_in + blades, fin_out=1.0),
        "G_blades_inner_fins_outer_ribs": dict(h_int_run=40, fin_in=f_in + blades, fin_out=f_out),
        "G_if_inside_air_only_h25": dict(h_int_run=25, fin_in=f_in + blades, fin_out=f_out),
        "H_G_with_25mm_ribs": dict(h_int_run=40, fin_in=f_in + blades, fin_out=f_out_big),
    }
    cases = {
        "hot_rated": dict(T_amb=30, V_wind=10.5, solar_W=100),
        "hot_rated_weak_wake": dict(T_amb=30, V_wind=10.5, solar_W=100, induction=0.6),
        "hot_110pct": dict(T_amb=30, V_wind=12.0, load=1.1, solar_W=100),
        "iceland_10C_rated": dict(T_amb=10, V_wind=12.0),
    }
    out = {}
    for cn, cf in configs.items():
        row = {}
        for k, c in cases.items():
            r = TH.solve_case(**c, **base, **cf)
            row[k] = dict(hot=r["T_hotspot"], mag=r["T_rotor_magnets"], air=r["T_internal_air"])
        out[cn] = dict(fin_in=round(cf["fin_in"], 2), fin_out=round(cf["fin_out"], 2), h_int=cf["h_int_run"],
                       cases=row)
    res = dict(parts=dict(inner_fins={k: v for k, v in fi.items() if k != "add"},
                          outer_ribs={k: v for k, v in ro.items() if k != "add"},
                          outer_ribs_big={k: v for k, v in ro_big.items() if k != "add"},
                          inner_area_m2=round(A_in, 3), outer_area_m2=round(A_out, 3)),
               configs=out, limit_hotspot_C=130)
    (HERE / "results" / "passive_cooling.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res["parts"], indent=1))
    for cn, v in out.items():
        print(f"{cn:34s} fi {v['fin_in']:.2f} fo {v['fin_out']:.2f} h {v['h_int']:>3} | " +
              "  ".join(f"{c['hot']:6.1f}/{c['mag']:4.0f}" for c in v["cases"].values()))


if __name__ == "__main__":
    main()
