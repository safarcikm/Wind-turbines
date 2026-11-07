"""Doc 38: blade for the low-cost concept LC8 (Ø8.0 m, TSR 7.5, 178 rpm; also run for TSR 7 and 8): strength AND the 3P frequency rule.

Run:  LC_TSR=8.0 LC_RPM=191.0 LC_OUT=tsr8.0 L7_BRAKE=4365 L7_HUB=100 python3 blade_e8.py [tsr rpm]
      -> results/blade_e8_tsr<x>.json

The doc 10 layup model (analysis/blade/blade.py) sizes the caps by strength and buckling only. A slender
high-TSR blade then lands BELOW 3P (TSR 8: 9.1 Hz rotating vs 3P 9.55 Hz). Doc 10 asks for a rotating flap
frequency >= 1.10 x 3P. Two stiffening levers are searched for the lightest blade that meets it:
  * thicker aerofoils outboard (t/c 18 % -> up to 24 %): spar height grows, EI ~ h^2, little mass;
  * thicker carbon caps (factor on the strength-sized caps).
SLM loads and the first-pass simulated loads come from structure_l7.py (variant_l7/common.py with LC_TSR/LC_RPM).
"""
import json, math, os, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "variant_l7"))
import common as C  # noqa: E402
import structure_l7 as ST  # noqa: E402
import blade as BLD  # noqa: E402

slm = ST.run_slm(16.5, 1.5, float(os.environ.get("L7_HUB", 100.0)) + 92.0)
ult = slm["ultimate_design_values_gamma_3_kN_kNm"]
sl = ST.sim_loads()
LOADS = dict(SLM_H_flap=ult["H_parked"]["M_yB"] * 1e3, SLM_G_edge=ult["G_shutdown"]["M_xB"] * 1e3,
             SIM_res=sl["SIM_res"] * C.blade_shape().solidity_area() / 0.849 / (0.842 / 0.849), SIM_op_flap=sl["SIM_op_flap"],
             DEL_flap=sl["DEL_flap"], DEL_edge=sl["DEL_edge"], rpm_max=C.RPM_MAX, gamma_E=3.0)
ST.patch_blade(LOADS)
tc0 = BLD.t_over_c
_section = BLD.section
F3P = 3 * C.RPM / 60
TARGET = 1.10 * F3P


def run(tc_out, k_cap):
    BLD.t_over_c = lambda r: max(tc0(r), tc_out) if tc0(r) < 0.9 else tc0(r)
    BLD.section = lambda r, c, tc, m, t_cap, *a, **kw: _section(r, c, tc, m, t_cap * k_cap, *a, **kw)
    d = BLD.design("UD_carbon", t_root_wall=0.016)
    f = float(BLD.beam_modes(d["_r"], d["_EIf"], d["_mu"], rpm=C.RPM)[0])
    fe = float(BLD.beam_modes(d["_r"], d["_EIe"], d["_mu"], rpm=C.RPM)[0])
    BLD.section = _section
    return dict(tc_outboard=tc_out, k_cap=k_cap, mass_kg=d["mass_kg"], f_flap_rot_Hz=round(f, 2), f_edge_rot_Hz=round(fe, 2),
                f_over_3P=round(f / F3P, 3), tip_deflection_m=d["tip_deflection_m"], clearance_util=d["clearance_util"],
                r_cog_m=d["r_cog_m"], static_moment=d["static_moment_kgm_about_axis"], max_util=d["max_util"])


rows = [run(tc, k) for tc in (0.18, 0.21, 0.24, 0.27) for k in (1.0, 2.0, 4.0, 6.0, 8.0, 12.0)]
ok = [r for r in rows if r["f_flap_rot_Hz"] >= TARGET and r["clearance_util"] <= 0.6]
best = min(ok, key=lambda r: r["mass_kg"]) if ok else None
out = dict(tsr=C.TSR, rpm=C.RPM, f_3P_Hz=round(F3P, 2), target_Hz=round(TARGET, 2), loads=LOADS, rows=rows, chosen=best,
           slm=ult)
(HERE / "results" / f"blade_e8_tsr{C.TSR}.json").write_text(json.dumps(out, indent=1, default=float))
for r in rows:
    print(r["tc_outboard"], r["k_cap"], r["mass_kg"], r["f_flap_rot_Hz"], r["f_over_3P"], r["clearance_util"])
print("3P", F3P, "target", TARGET, "chosen", best)
