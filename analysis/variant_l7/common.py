"""Shared data for the lightweight 12 kW variant L7 (doc 38): Ø8.0 m, TSR 7.0, 167 rpm. All other l7 scripts import this.

Copied from the M8 scripts (analysis/variant_m8/, doc 35/37); only the inputs differ.
L7 keeps the M8 diameter (same energy) and raises the design TSR from 5.5 to 7.0: slimmer blades,
lower storm loads, lower torque, so the Rev C generator (5 rows) is used unchanged.
"""
from __future__ import annotations
import math, os, sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
for p in ("rotor", "loads", "blade", "tower", "hub", "yaw", "generator", "power"):
    sys.path.insert(0, str(ROOT / p))
OUT = HERE / "results" / os.environ["LC_OUT"] if os.environ.get("LC_OUT") else HERE / "results"
OUT.mkdir(exist_ok=True)

NAME = "L7"
R = 4.00                     # tip radius, Ø8.0 m (Martin, 2026-11-06)
import os
TSR = float(os.environ.get("LC_TSR", 7.0))   # design TSR of the blade shape (L7: 7.0, optimum operation at 7.25); doc 38 E8 runs with LC_TSR=8
RPM = float(os.environ.get("LC_RPM", 167.0))   # rated speed: tip 70 m/s (project erosion limit, study.py), rated power at 10.0 m/s
OMEGA = RPM * math.pi / 30
V_RATED = 10.0
P_SHAFT = 13_600.0
Q_RATED = P_SHAFT / OMEGA    # 778 Nm shaft (Rev C: 730 Nm at 178 rpm)
# speed limits keep the doc 08/11 ratios to rated: trip 210/178, design overspeed 250/178
RPM_TRIP = round(RPM * 210 / 178, 1)       # 197.0
RPM_MAX = round(RPM * 250 / 178, 1)        # 234.6
RPM_MIN = 43.0               # lowest operating speed (cut-in 2.5 m/s at the optimum TSR 7.25)

# generator: Rev C unchanged, 5 magnet rows, stack 74 mm, 28 turns (778 Nm = 1.066 x Rev C current)
ROWS = 5
L_STACK = 0.074
DL = L_STACK - 0.074         # 0: same stack, drum, carrier and spindle as Rev C
OVERHANG = 0.75              # rotor plane ahead of the yaw axis (doc 13, Rev C generator length)
BLADE_AREA_CUR = 0.849       # m2, current Ø7.5 blade planform (doc 03)


def blade_shape(n=30):
    from bem import Blade
    return Blade(R=R, tsr_design=TSR, cl_design=1.0, n=n)


def Blade8(*a, **kw):
    """Drop-in replacement for bem.Blade inside existing modules: forces the L7 design TSR."""
    from bem import Blade
    kw["tsr_design"] = TSR
    return Blade(*a, **kw)
