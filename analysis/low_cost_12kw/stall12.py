"""Doc 38: fixed-pitch stall-by-speed regulation for a 12 kW Ø8.0 m rotor at high TSR.

Run:  python3 stall12.py [tsr ...]     (~1 min per TSR) -> results/stall12_tsr<x>.json

Reuses the doc 28 study (analysis/turbine_6kw/regulation.py) unchanged: its source is loaded with the
design dictionary replaced by the 12 kW one, so every function (stall schedule, gust torque, stop torque,
runaway, parked strip-theory loads, brake stops) is the doc 28/31 model.
"""
import json, math, sys, types
from pathlib import Path
HERE = Path(__file__).parent
SRC = HERE.parent / "turbine_6kw" / "regulation.py"


RPM_OVERRIDE = {7.5: 178.0}   # LC8: Rev C rated speed (TSR 7.46 at 10 m/s)


def load(tsr, R=4.0, rated=10.0, J=210.0):
    des = dict(P_e=12.0, R=R, tsr=tsr, rpm=RPM_OVERRIDE.get(tsr, round(tsr * rated / R * 30 / math.pi, 1)), rated_wind=rated, J_rotor=J)
    src = SRC.read_text().replace('DES = json.loads((OUT / "design.json").read_text())', f"DES = {des!r}")
    src = src.replace('OUT = HERE / "results"; OUT.mkdir(exist_ok=True)', f'OUT = Path({str(HERE / "results")!r}) / "stall12_tsr{tsr}"; OUT.mkdir(parents=True, exist_ok=True)')
    mod = types.ModuleType(f"reg12_{tsr}")
    mod.__file__ = str(SRC)
    exec(compile(src, str(SRC), "exec"), mod.__dict__)
    return mod


if __name__ == "__main__":
    for t in [float(x) for x in sys.argv[1:]] or [7.0, 8.0]:
        m = load(t)
        m.main()
        r = json.loads((m.OUT / "regulation.json").read_text())
        keep = {k: r[k] for k in ("design", "Q_rated", "rpm_cap", "PF", "fixed_pitch_choice", "aep", "stall_demands",
                                  "pitch_demands", "parked_summary", "thrust", "brake_stop_30ms", "elec_brake")}
        (HERE / "results" / f"stall12_tsr{t}.json").write_text(json.dumps(keep, indent=1, default=float))
