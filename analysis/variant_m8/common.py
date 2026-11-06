"""Shared data for the 12 kW baseline M8 (doc 35): Ø8.0 m, TSR 5.5, 131 rpm. All other m8 scripts import this.

Built from the doc 26 (V5) scripts in analysis/variant_tsr5/; only the inputs differ.
"""
from __future__ import annotations
import math, sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
for p in ("rotor", "loads", "blade", "tower", "hub", "yaw", "generator", "power"):
    sys.path.insert(0, str(ROOT / p))
OUT = HERE / "results"
OUT.mkdir(exist_ok=True)

NAME = "M8"
R = 4.00                     # tip radius, Ø8.0 m (Martin, 2026-11-06)
TSR = 5.5                    # design TSR of the blade shape (optimum operation at 6.0)
RPM = 131.0                  # rated speed: rated power at 10.0 m/s (rpm scan: 125-128 rpm -> 10.5 m/s)
OMEGA = RPM * math.pi / 30
V_RATED = 10.0
P_SHAFT = 13_600.0
Q_RATED = P_SHAFT / OMEGA    # 991 Nm shaft (875 Nm is the 12 kW electrical figure at 131 rpm)
# speed limits keep the doc 08/11 ratios to rated: trip 210/178, design overspeed 250/178
RPM_TRIP = round(RPM * 210 / 178, 1)       # 154.6
RPM_MAX = round(RPM * 250 / 178, 1)        # 184.0
RPM_MIN = 35.0               # lowest operating speed (cut-in 2.5 m/s at the optimum TSR 6.0)

# generator: Rev C with 7 magnet rows instead of 5 (stack 74 -> 104 mm), 28 turns kept
ROWS = 7
L_STACK = 0.104
DL = L_STACK - 0.074         # 30 mm longer stack, drum, carrier and spindle
OVERHANG = 0.78              # rotor plane ahead of the yaw axis (doc 13: 0.75, + 30 mm longer generator)
BLADE_AREA_CUR = 0.849       # m2, current Ø7.5 blade planform (doc 03)


def blade_shape(n=30):
    from bem import Blade
    return Blade(R=R, tsr_design=TSR, cl_design=1.0, n=n)


def Blade8(*a, **kw):
    """Drop-in replacement for bem.Blade inside existing modules: forces the M8 design TSR."""
    from bem import Blade
    kw["tsr_design"] = TSR
    return Blade(*a, **kw)
