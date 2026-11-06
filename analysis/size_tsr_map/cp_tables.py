"""Non-dimensional rotor tables for the size x TSR decision map (doc 27).

Run:  python3 cp_tables.py      (~2-4 min) -> results/rotor_tables.json

For every design TSR (4.0 ... 8.0 in 0.5 steps) the doc 03 blade rule (analysis/rotor/bem.py:
Schmitz chord with linear taper, Cl 1.0, 3 blades) is built and solved with the doc 03 BEM model,
unchanged. Everything is stored per unit radius, so one table serves every rotor size:

  cp_best(lambda), ct_at_best(lambda)  best pitch in [-2, 8] deg at each tip speed ratio
  area_R2      blade planform area / R^2
  cmax_R       max chord / R
  park_M_R3    parked broadside root moment / (q * R^3)  (q = dynamic pressure, doc 03 Cd 1.8)
  park_F_R2    parked broadside force per blade / (q * R^2)

The hub radius scales with the rotor (0.40 m at R 3.75 m), so the tables are exactly size-free
(no Reynolds effect in the doc 03 polars).
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "rotor"))
from bem import Blade, CLEAN, ROUGH, solve  # noqa: E402

OUT = HERE / "results"; OUT.mkdir(exist_ok=True)
TSRS = [4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0]
LAMS = np.round(np.arange(1.5, 14.01, 0.25), 3)
PITCH = np.arange(-2.0, 8.01, 0.5)
R_REF, HUB_FRAC, CD_BROADSIDE = 3.75, 0.40 / 3.75, 1.8


def blade(tsr, R=R_REF):
    return Blade(R=R, r_hub=HUB_FRAC * R, tsr_design=tsr, cl_design=1.0)


def table(tsr):
    b = blade(tsr)
    out = dict(tsr=tsr, area_R2=b.solidity_area() / R_REF ** 2, cmax_R=b.c_max / R_REF,
               croot_R=b.c_root / R_REF)
    dF = CD_BROADSIDE * b.chord * b.dr
    out["park_F_R2"] = float(dF.sum()) / R_REF ** 2
    out["park_M_R3"] = float(np.sum(dF * (b.r - b.r_hub))) / R_REF ** 3
    for pol in (ROUGH, CLEAN):
        cp, ct, pp = [], [], []
        for lam in LAMS:
            best = None
            for p in PITCH:
                r = solve(b, 8.0, lam * 8.0 / R_REF, p, 1.225, pol)
                if best is None or r.cp > best[0]:
                    best = (r.cp, r.ct, p)
            cp.append(round(best[0], 5)); ct.append(round(best[1], 5)); pp.append(best[2])
        i = int(np.argmax(cp))
        out[pol.name] = dict(cp=cp, ct=ct, pitch=pp, cp_max=cp[i], lam_opt=float(LAMS[i]))
    return out


def main():
    res = dict(lams=LAMS.tolist(), tsrs=TSRS, note=__doc__.split("\n\n")[0],
               tables=[table(t) for t in TSRS])
    (OUT / "rotor_tables.json").write_text(json.dumps(res))
    for t in res["tables"]:
        print(t["tsr"], round(t["area_R2"], 4), t["rough"]["cp_max"], t["rough"]["lam_opt"],
              t["clean"]["cp_max"], round(t["park_M_R3"], 4))


if __name__ == "__main__":
    main()
