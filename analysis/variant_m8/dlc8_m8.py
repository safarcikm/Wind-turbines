"""M8 on the 8 m tower: aeroelastic design load cases at 8 m hub height (doc 37 §2).

Run:  python3 dlc8_m8.py    (~40 min on 4 cores) -> results/dlc8_m8/dlc_summary.json, ops_loads_m8_8m.json

Same 103-case set, controller and M8 turbine as dlc_m8.py, with what changes near the ground:
  * hub height 8.0 m (wind model Z_HUB, turbulence length scale Lambda1 = 0.7 z -> 5.6 m, as IEC 61400-1);
  * shear exponent 0.25 instead of 0.20 (log law: 0.20 at z0 0.05 m, 0.29 at z0 0.25 m, 8 m height; the rotor
    spans 4-12 m, so the shear across it is strong);
  * turbulence +20 % (I15 0.20 -> 0.24): doc 34/35 log-law estimate of +12...+23 % at 8 m vs 18 m;
  * the stiff 8 m tower of tower8_m8.py: f1 3.0 Hz, modal mass 170 kg, 3P speed exclusion zone 52-66 rpm.
Class S extreme winds (V_ref, V_e50) stay at hub height, as IEC 61400-2 defines them.
"""
from __future__ import annotations
import json, math, sys
import common as C

_ARGS = list(sys.argv)
import dlc_m8 as D  # noqa: E402
import wind as W  # noqa: E402

HUB = 8.0
W.Z_HUB = HUB
W.LAMBDA1 = 0.7 * HUB
W.L_U = 8.1 * W.LAMBDA1
W.L_C = 8.1 * W.LAMBDA1
W.ALPHA = 0.25
W.I15 = 0.24
TW8 = json.loads((C.OUT / "tower8_m8.json").read_text())["towers"]["stiff"]["tower"]
D.TOWER = dict(H=HUB, D_base=TW8["geometry"]["D_base"], D_top=TW8["geometry"]["D_top"], f1=round(TW8["f1_rigid_Hz"], 2),
               m_modal=170.0, levels=(0.0, 0.5))
D.RD.TB_KW = dict(D.RD.TB_KW, hub_height=HUB, f_tower=D.TOWER["f1"], m_tower_modal=D.TOWER["m_modal"],
                  excl_rpm=tuple(TW8["exclusion_zone_rpm"]))
# 8 m controller (doc 37 §2, ctrl8_m8.py): with the 18 m setting (speed loop 4 rad/s, trip 118 % = 154.6 rpm,
# normal pitch rate 15 deg/s) the 8 m turbulence tripped 24 runs and reached 219.6 rpm once (kept in
# dlc_summary_ctrl18.json). Speed loop 6 rad/s, trip 165 rpm (126 %), normal pitch rate 20 deg/s.
CTRL8 = dict(pitch_wn=6.0, rpm_trip=165.0, pitch_rate_normal=20.0)
if "--ctrl18" not in _ARGS:
    D.RD.TB_KW.update(CTRL8)
D.OUT = C.OUT / "dlc8_m8"
D.OUT.mkdir(parents=True, exist_ok=True)
D.RD.OUT = D.OUT
D.W = W


def main():
    D.main()
    src = D.OUT / "ops_loads_m8_18m.json"
    if src.exists():
        s = json.loads(src.read_text())
        s["source"] = "dlc8_m8.py (M8, 8 m hub, stiff tower f1 %.2f Hz, I15 0.24, shear 0.25, 8 m controller)" % D.TOWER["f1"]
        (D.OUT / "ops_loads_m8_8m.json").write_text(json.dumps(s, indent=1))
        src.unlink()


if __name__ == "__main__":
    main()
