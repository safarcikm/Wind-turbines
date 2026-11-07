"""Doc 36: M8 generator with the baseline block, N42SH 40x20x7.5 and the best block of the sweep.

Run after blocks_m8.py (all + table):  python3 compare_m8.py [KEY ...]  -> results/compare_m8.json

Losses, efficiency, voltage, demagnetisation, drum, rotor mass and passive cooling for each design,
on the same basis as generator_m8.py (doc 35 §4). The baseline numbers are recomputed with the
same scripts, so differences are like for like.
"""
from __future__ import annotations

import contextlib
import io
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).parent
M8 = HERE.parent / "variant_m8"
sys.path.insert(0, str(M8))
_argv, sys.argv = sys.argv, sys.argv[:1]
import common as C  # noqa: E402
import generator_m8 as GM  # noqa: E402
sys.argv = _argv

OUT = HERE / "results"
RHO_STEEL = 7850.0
R_OUT = 0.323
ETA_M8 = 0.944                 # doc 35 loss-chain generator efficiency at rated (baseline)
V_PK_M8 = 881.0                # doc 35 peak line voltage, -30 °C, design overspeed, at 384.8 V
E_M8 = 384.8
RING = 7.0                     # end ring width each end [mm]


def drum_stability(yoke_mm, hm_mm, L_sh=0.269):
    """generator_m8.drum_stability() with the shell thickness and magnet height of the design."""
    t = yoke_mm / 1000
    r_m = (323.0 + (323.0 - yoke_mm)) / 2 / 1000
    g_eff = 2.0 + hm_mm / 1.05
    ump = 1.9 * (2.0 + 7.5 / 1.05) / g_eff
    b_rms2 = ump * 1e6 * GM.CK.MU0 * (g_eff / 1000) / (math.pi * 0.300 * 0.074)
    k_mag = b_rms2 / (GM.CK.MU0 * g_eff / 1000)
    lam = math.pi * r_m / L_sh
    k = min(210e9 * t / r_m ** 2 * (lam ** 4 / (n * n + lam * lam) ** 2
                                   + t * t / (12 * r_m * r_m * 0.91) * (n * n + lam * lam) ** 2) for n in range(2, 40))
    return round(k / k_mag), round(ump * GM.K_L, 2)


def design(r, ref):
    base_L = GM.losses()                                   # M8 baseline losses (596 / 202 / 30 / 70)
    k_flux = (r["emf_28t_100C_V"] / ref["emf_28t_100C_V"]) ** 2
    L = dict(base_L)
    L["P_cu"] = r["copper_W"]
    L["P_fe"] = round(base_L["P_fe"] * k_flux)
    L["P_rotor"] = round(base_L["P_rotor"] - ref["eddy_W"] + r["eddy_W"])
    total = L["P_cu"] + L["P_fe"] + L["P_rotor"] + L["P_stray"]
    total_ref = ref["copper_W"] + base_L["P_fe"] + base_L["P_rotor"] + base_L["P_stray"]
    eta = ETA_M8 - (total - total_ref) / C.P_SHAFT
    e_t = r["emf_at_turns_V"]
    stab, ump = drum_stability(r["yoke_mm"], r["thick_mm"])
    land = r["rows_mm"] + 2 * RING
    land_ref = ref["rows_mm"] + 2 * RING
    r_s, r_s0 = r["seat_d_mm"] / 2e3, ref["seat_d_mm"] / 2e3
    # drum (outer Ø646 and length kept): a smaller seat leaves more steel under the magnets over the land
    drum_d = RHO_STEEL * math.pi * (r_s0 ** 2 - r_s ** 2) * land / 1e3
    mag_d = r["magnet_kg"] - ref["magnet_kg"]
    with contextlib.redirect_stdout(io.StringIO()):
        cool = run_cooling(L)
    g = cool["configs"]["G_blades_inner_fins_outer_ribs"]["cases"]
    return dict(
        key=r["key"], note=r["note"], grade=r["grade"],
        block=f"{r['width_mm']:g} x {r['l_mm']:g} x {r['thick_mm']:g}", across=r["k_across"], rows=r["rows"],
        pieces=r["pieces"], spares=r["spares"], piece_g=r["piece_g"], magnet_kg=r["magnet_kg"],
        rows_mm=r["rows_mm"], seat_land_mm=round(land, 1), seat_land_vs_M8_mm=round(land - land_ref, 1),
        seat_d_mm=r["seat_d_mm"], drum_yoke_mm=r["yoke_mm"], span=r["span"], skew_step_deg=r["skew_step_deg"],
        turns=r["turns_for_baseline_V"], emf_100C_V=e_t, emf_28t_100C_V=r["emf_28t_100C_V"],
        peak_line_V=round(V_PK_M8 * e_t / E_M8),
        losses_W=dict(copper=L["P_cu"], core=L["P_fe"], rotor=L["P_rotor"], stray=L["P_stray"], total=total),
        efficiency_rated=round(eta, 4),
        cogging_skewed_Nm=r["cogging_skewed_Nm"], cogging_unskewed_Nm=r["cogging_unskewed_Nm"],
        ripple_skewed_pct=r["ripple_skewed_pct"], thd_pct=r["thd_pct"], magnet_eddy_W=r["eddy_W"],
        demag_transient_sc_pct=dict(c100=r["demag_margin_pct"]["100C"]["transient_sc"],
                                    c110=r["demag_margin_pct"]["110C"]["transient_sc"],
                                    c120=r["demag_margin_pct"]["120C"]["transient_sc"]),
        demag_steady_sc_100C_pct=r["demag_margin_pct"]["100C"]["steady_sc"],
        demag_rated_100C_pct=r["demag_margin_pct"]["100C"]["rated"],
        T20_C=r["T20_C"],
        drum_stability=stab, ump_kN_per_mm=ump,
        mass_vs_M8_kg=dict(magnets=round(mag_d, 2), drum=round(drum_d, 1), total=round(mag_d + drum_d, 1)),
        cooling_G=g)


def run_cooling(L):
    """generator_m8.thermal() with this design's losses, written to this folder (baseline file untouched)."""
    C.OUT, C.HERE = OUT, HERE
    (HERE / "results").mkdir(exist_ok=True)
    res = GM.thermal(L)
    return res


def main(keys):
    rows = {r["key"]: r for r in json.loads((OUT / "blocks_summary.json").read_text())}
    ref = rows["REF"]
    out = [design(rows[k], ref) for k in ["REF", *keys]]
    (OUT / "compare_m8.json").write_text(json.dumps(out, indent=1))
    (OUT / "generator_m8_cooling.json").unlink(missing_ok=True)
    for d in out:
        print(json.dumps(d))


if __name__ == "__main__":
    main(sys.argv[1:])
