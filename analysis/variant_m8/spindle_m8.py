"""M8 spindle, main bearings, bolted joints and brake: the doc 14 detail checks (analysis/nacelle/detail.py)
re-run with M8 loads (doc 37 §4).

Run:  python3 spindle_m8.py   (after dlc_m8.py, dlc8_m8.py, structure_m8.py) -> results/spindle_m8.json

detail.py is executed unchanged except for its load block, the flange station and the brake (3 calipers).
Rev D geometry (cad/turbine_m8): the spindle, stator and drum are 30 mm longer at x 410, between the cone shoulder
and the flange, so both bearings keep their doc 14 spacing (span 240 mm, conservative) and the flange fillet moves
from x 430 to x 460 measured from the rotor plane.
Loads: the larger of the 18 m (dlc_m8) and 8 m (dlc8_m8) simulations, scaled from the doc 08/14 values by
the same channel; SLM values from structure_m8.py.
"""
from __future__ import annotations
import json, sys
import common as C

NAC = C.ROOT / "nacelle"
SLM = json.loads((C.OUT / "slm_m8.json").read_text())["ultimate_design_values_gamma_3_kN_kNm"]
CUR = json.loads((C.ROOT / "loads" / "results" / "final" / "dlc_summary.json").read_text())
SIMS = [json.loads((C.OUT / d / "dlc_summary.json").read_text()) for d in ("dlc_m8", "dlc8_m8")
        if (C.OUT / d / "dlc_summary.json").exists()]
HY = json.loads((C.OUT / "hub_yaw_m8.json").read_text())


def env(ch, kind="design"):
    return max(s["ultimate_envelope"][ch][kind] for s in SIMS)


def dels(ch):
    return max(s["fatigue_DEL"][ch]["DEL_1e7"] for s in SIMS)


k_tilt = env("Mtilt") / CUR["ultimate_envelope"]["Mtilt"]["design"]
k_thr = SLM["H_parked"]["F_x_shaft"] / 41.64
k_fat = max(dels("Mtilt") / CUR["fatigue_DEL"]["Mtilt"]["DEL_1e7"], dels("thrust") / CUR["fatigue_DEL"]["thrust"]["DEL_1e7"])
LOADS = dict(
    M_HUB=max(9.8e3 * k_tilt, 9.8e3 * SLM["B_yaw"]["M_shaft"] / 5.35),
    F_STATIC=(41e3 * k_thr, 44e3 * k_thr),
    F_AX_PARKED=SLM["H_parked"]["F_x_shaft"] * 1e3,
    T_RATED=C.Q_RATED * 1.1,
    T_BRAKE=13.1e3,
    T_SLM_G=SLM["G_shutdown"]["M_x_shaft"] * 1e3,
    TILT_YAW=max(HY["yaw"]["M_tilt_kNm"].values()) * 1e3,
)


def main():
    src = (NAC / "detail.py").read_text()
    block_start = src.index("M_HUB = 9.8e3")
    block_end = src.index("REV_20Y = ")
    new_block = "".join(f"{k} = {v!r}\n" for k, v in LOADS.items()) + "T_SC = 4 * T_RATED\n"
    src = src[:block_start] + new_block + src[block_end:]
    rep = [("P_eq = [3.0e3 * 3, 0.92e3 * 3]", f"P_eq = [3.0e3 * 3 * {k_fat:.3f}, 0.92e3 * 3 * {k_fat:.3f}]"),
           ('("flange fillet Ø150 R10 (x 430)", 430, 150, 1.45)', '("flange fillet Ø150 R10 (x 460)", 460, 150, 1.45)'),
           ("F_SHEAR = 15e3", f"F_SHEAR = 15e3 * {k_thr:.3f}"),
           ("T_BRAKE / (2 * 2 * 0.4 * 0.37)", "T_BRAKE / (3 * 2 * 0.4 * 0.37)"),
           ('OUT = HERE / "results"', 'OUT = Path(%r)' % str(C.OUT)),
           ('(OUT / "detail_summary.json")', '(OUT / "spindle_m8_raw.json")'),
           ("print(json.dumps(res, indent=1, ensure_ascii=False))", "")]
    for a, b in rep:
        assert a in src, a
        src = src.replace(a, b)
    g = {"__name__": "detail_m8", "__file__": str(NAC / "detail.py")}
    exec(compile(src, "detail_m8", "exec"), g)
    res = g["res"]
    out = dict(loads_used={k: (round(v / 1e3, 2) if isinstance(v, float) else [round(x / 1e3, 1) for x in v]) for k, v in LOADS.items()},
               load_note="kN / kNm; M_HUB, F_STATIC scaled from doc 14 by the M8/current envelope ratio",
               k_tilt=round(k_tilt, 2), k_thrust=round(k_thr, 2), k_fatigue=round(k_fat, 2),
               bearings=res["bearings"], spindle=res["spindle"], bolted_joints=res["bolted_joints"], brake=res["brake"])
    (C.OUT / "spindle_m8.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    (C.OUT / "spindle_m8_raw.json").unlink(missing_ok=True)
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
