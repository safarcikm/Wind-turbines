"""Doc 40: how much rotor brake does the M8 on the 8 m tower really need?

Run:  python3 brake8.py   (~10 min on 4 cores) -> results/brake8.json

Same simulator, turbine and 8 m wind model as dlc8_m8.py (doc 37). Three questions:
  A  Storm hold with a SLIPPING brake: parked rotor, feathered, 50-year wind V_ref 55 m/s, the worst yaw/azimuth
     cases of the doc 37 parked set, converter lost (no generator torque, conservative: K1 resistor ignored).
     Brake 4.8 / 7.2 / 9.6 / 14.4 kNm. Output: how far and how fast the rotor creeps, blade loads.
  B  Free idling in the storm (feathered, brake off) as doc 11 IDLE mode: rotor speed and loads.
  C  R3.8 stop with ALL blades stuck at fine pitch (pitch system dead) from the 165 rpm trip, converter lost,
     wind 15 / 25 / 32 m/s: does the brake alone stop the rotor, how long, how much heat into the disc.
"""
from __future__ import annotations
import json, math, sys, multiprocessing as mp
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "variant_m8"))
sys.argv = [sys.argv[0]]
import dlc8_m8  # noqa: E402,F401  (sets 8 m wind model and the 8 m controller on D.RD.TB_KW)
import dlc_m8 as D  # noqa: E402
import numpy as np  # noqa: E402
import sim  # noqa: E402

OUT = HERE / "results"; OUT.mkdir(exist_ok=True)
V_REF = 55.0
BRAKES = (4800.0, 7200.0, 9600.0, 14400.0)
STORM = [(30, 60), (90, 0), (135, 0), (60, 0)]          # (yaw error deg, azimuth deg): worst positive-torque cases of doc 37
DISC = dict(m=33.6, c=470.0)                             # brake disc C45, J/kgK


def tb(**kw):
    return sim.Turbine(**dict(D.RD.TB_KW, brake_delay=0.0, **kw))


def storm(args):
    brake, yaw, az, idle = args
    t = tb(brake_torque=brake)
    f = D.RD.turbulent_field(V_REF, 0.11 * V_REF, T=300, dt=0.05, seed=700 + az + yaw)   # same seeds as doc 37
    if idle:
        sc = sim.Scenario("idle", 300, f, yaw=yaw, park_azimuth=az, idle=True, rho=1.35)
    else:
        sc = sim.Scenario("slip", 300, f, yaw=yaw, park_azimuth=az, rho=1.35, init_rpm=0.0, init_pitch=90.0,
                          events={"estop_t": 0.0, "loss_of_torque_t": 0.0})
    r = sim.simulate(t, sc)
    m = r["t"] > 5
    revs = float(np.trapezoid(r["rpm"][m], r["t"][m]) / 60)
    return dict(case="idle" if idle else "slip", brake_Nm=brake, yaw=yaw, az=az, max_rpm=round(float(r["rpm"].max()), 1),
                mean_rpm=round(float(r["rpm"][m].mean()), 2), revs_300s=round(revs, 2),
                Qaero_max=round(float(r["Qaero"].max())), Mflap_max=round(float(np.abs(r["Mflap0"]).max())),
                Medge_max=round(float(np.abs(r["Medge0"]).max())), Mtilt_max=round(float(np.abs(r["Mtilt"]).max())),
                thrust_max=round(float(r["thrust"].max())))


def stop(args):
    brake, V = args
    t = tb(brake_torque=brake, pitch_rate_emergency=0.0, pitch_rate_normal=0.0)   # pitch dead: blades stay where they are
    f = D.RD.turbulent_field(V, 0.11 * V, T=60, dt=0.05, seed=900 + int(V))
    sc = sim.Scenario("stuckfine", 60, f, init_rpm=165.0, init_pitch=0.0,
                      events={"estop_t": 0.0, "loss_of_torque_t": 0.0})
    r = sim.simulate(t, sc)
    om = r["rpm"] * math.pi / 30
    stopped = np.nonzero(r["rpm"] < 0.5)[0]
    t_stop = float(r["t"][stopped[0]]) if len(stopped) else None
    dt = r["t"][1] - r["t"][0]
    E = float(np.sum(brake * om) * dt)                    # heat into the disc while slipping (upper bound)
    return dict(case="stop_stuck_fine", brake_Nm=brake, V=V, max_rpm=round(float(r["rpm"].max()), 1), t_stop_s=t_stop,
                end_rpm=round(float(r["rpm"][-1]), 1), Qaero_max=round(float(r["Qaero"].max())),
                heat_kJ=round(E / 1e3), disc_dT_K=round(E / (DISC["m"] * DISC["c"]), 1),
                Medge_max=round(float(np.abs(r["Medge0"]).max())), Mflap_max=round(float(np.abs(r["Mflap0"]).max())))


if __name__ == "__main__":
    jobs_s = [(b, y, a, False) for b in BRAKES for (y, a) in STORM] + [(0.0, y, a, True) for (y, a) in STORM + [(0, 0), (8, 0)]]
    jobs_c = [(b, V) for b in BRAKES + (3600.0,) for V in (15.0, 25.0, 32.0)]
    with mp.Pool(4) as p:
        res_c = p.map(stop, jobs_c)
        for r in res_c: print(r)
        res_s = p.map(storm, jobs_s, chunksize=1)
    for r in res_s: print(r)
    (OUT / "brake8.json").write_text(json.dumps(dict(storm=res_s, stop=res_c), indent=1))
