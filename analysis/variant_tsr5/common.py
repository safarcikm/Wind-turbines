"""Shared data for the slow-running variant V5 (doc 26). All other v5 scripts import this."""
from __future__ import annotations
import math, sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
for p in ("rotor", "loads", "blade", "tower", "hub", "yaw", "generator", "power"):
    sys.path.insert(0, str(ROOT / p))
OUT = HERE / "results"
OUT.mkdir(exist_ok=True)

R = 4.15                     # tip radius, Ø8.3 m
TSR = 5.0                    # design TSR of the blade shape (optimum operation at 5.375)
RPM = 110.0                  # rated speed
OMEGA = RPM * math.pi / 30
V_RATED = 10.0
P_SHAFT = 13_600.0
Q_RATED = P_SHAFT / OMEGA    # 1,181 Nm
# speed limits keep the doc 08/11 ratios to rated: trip 210/178, design overspeed 250/178
RPM_TRIP = round(RPM * 210 / 178, 1)       # 129.8
RPM_MAX = round(RPM * 250 / 178, 1)        # 154.5
RPM_MIN = 30.0               # lowest operating speed (cut-in 2.5 m/s at the optimum TSR)
OVERHANG = 0.80              # rotor plane ahead of the yaw axis (doc 13: 0.75, + 46 mm longer generator)


def blade_shape(n=30):
    from bem import Blade
    return Blade(R=R, tsr_design=TSR, cl_design=1.0, n=n)


def Blade5(*a, **kw):
    """Drop-in replacement for bem.Blade inside existing modules: forces the V5 design TSR."""
    from bem import Blade
    kw["tsr_design"] = TSR
    return Blade(*a, **kw)
