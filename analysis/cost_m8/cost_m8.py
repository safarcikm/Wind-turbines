"""Doc 39: bottom-up manufacturing cost of the 12 kW M8 turbine on the 8 m tower (doc 37, bom8.csv).

Run:  python3 cost_m8.py          -> out/39-m8-cost-breakdown.xlsx, out/cost_m8.json

Every line of bom8.csv is costed (material x buy factor x landed price, labour hours x shop rate,
outside services, bought-in price, tooling written off over VOLUME turbines). Lines that the BOM does not
carry but a real build needs (brake release unit, cabinet internals, assembly and test labour, coating,
fixtures) are added and marked "+". The same numbers are written to the workbook as live formulas, so
rates can be changed in the Rates sheet. LC8 (doc 38) is costed as a set of deltas on the same lines.
"""
import json, csv
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.comments import Comment

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"; OUT.mkdir(exist_ok=True)

# ------------------------------------------------------------------ rates (EUR, landed in Iceland, 2026)
RATES = [  # key, value, unit, note
    ("VOLUME", 50, "turbines", "Tooling, moulds and fixtures written off over this many turbines (≈2 years at 25/yr)"),
    ("ISK_PER_EUR", 145, "ISK/€", "Same as doc 27"),
    ("CONTINGENCY", 0.08, "fraction", "Unpriced small items, scrap, rework in a young production line"),
    # labour, fully burdened shop rates (wage + 25 % employer cost + workshop overhead + machine)
    ("R_FAB", 80, "€/h", "Cutting, fitting, welding (EN ISO 9606 welder). Iceland skilled wage ≈ 1.0 M ISK/month"),
    ("R_MACH", 105, "€/h", "CNC turning/milling/boring mill, press shop, incl. machine depreciation"),
    ("R_COMP", 72, "€/h", "Composite lamination, infusion, finishing"),
    ("R_ELEC", 78, "€/h", "Winding, electrical/electronics assembly, HV test"),
    ("R_ASSY", 75, "€/h", "Mechanical assembly, magnet work, factory test, QA"),
    ("R_SITE", 85, "€/h", "Site crew incl. van and travel time"),
    # materials, landed Iceland (EU price + ≈12 % freight and handling)
    ("S355", 1.45, "€/kg", "S355J2+N / S355NL plate"),
    ("S235", 1.50, "€/kg", "S235 sections, RHS, sheet"),
    ("TUBE", 1.75, "€/kg", "S355 structural tube"),
    ("CRMO", 3.20, "€/kg", "42CrMo4+QT bar"),
    ("FORGE", 5.50, "€/kg", "42CrMo4 forged spindle blank, QT, 3.1 cert"),
    ("C45", 1.70, "€/kg", "C45E bar / plate"),
    ("MIX", 2.20, "€/kg", "Mixed steel parts (CrMo pins in S355)"),
    ("SS4404", 7.00, "€/kg", "1.4404 stainless"),
    ("SS4301", 5.50, "€/kg", "1.4301 stainless sheet"),
    ("AL5083", 6.50, "€/kg", "EN AW-5083 plate"),
    ("M270", 4.20, "€/kg", "M270-35A with self-bonding varnish, slit coil"),
    ("CU200", 16.0, "€/kg", "Enamelled Cu Ø1.55 class 200, corona resistant"),
    ("NDFEB", 150.0, "€/kg", "N45SH 30×15×12, coated, magnetised, non-Asian source (Neo Estonia / VAC). RFQs open: ±30 %"),
    ("GLASS", 4.80, "€/kg", "E-glass biax/triax/UD fabrics"),
    ("CARBON", 28.0, "€/kg", "Carbon UD fabric for spar caps"),
    ("EPOXY", 11.0, "€/kg", "Infusion epoxy + structural adhesive"),
    ("CORE", 25.0, "€/kg", "PVC foam core 80 kg/m³, kitted"),
    ("GRP", 5.50, "€/kg", "Glass/polyester hand lay-up incl. gelcoat (covers, spinner)"),
    ("TOOLGRP", 9.00, "€/kg", "Vinylester tooling laminate + tooling gelcoat"),
    ("REBAR", 1.60, "€/kg", "B500C cut and bent, delivered"),
    ("CONC", 310.0, "€/m³", "C30/37 XF4 air-entrained ready-mix, delivered (≈45,000 ISK)"),
    # services
    ("HDG", 0.95, "€/kg", "Hot-dip galvanising (tower needs a ≥ 7 m bath; may mean shipping)"),
    ("C5", 1.10, "€/kg", "C5 3-coat paint (blast, zinc epoxy, PU) — ≈ €25/m² as a per-kg proxy"),
    ("SR", 0.60, "€/kg", "Stress relieving of weldments"),
]
R = {k: v for k, v, *_ in RATES}

# ------------------------------------------------------------------ parts
# fields: pos, pid, name, sub, qty, unit, mb, mat, kg (net each), bf (buy factor), h=(fab,mach,comp,elec,assy,site) each,
#         coat (HDG/C5/''), serv (other services € each), buy (bought-in € each), tool (True -> /VOLUME), note
P = []
def add(pos, pid, name, sub, qty, mat="", kg=0, bf=1.0, h=(0, 0, 0, 0, 0, 0), coat="", serv=0, buy=0, tool=False, note="", unit="pc", mb="make"):
    P.append(dict(pos=pos, pid=pid, name=name, sub=sub, qty=qty, unit=unit, mb=mb, mat=mat, kg=kg, bf=bf,
                  h=tuple(h) + (0,) * (6 - len(h)), coat=coat, serv=serv, buy=buy, tool=tool, note=note))

S_BL, S_HP, S_GEN, S_DT, S_NAC, S_YAW, S_EL, S_TW, S_FA, S_TL, S_FD, S_IN = (
    "1 Blades", "2 Hub and pitch", "3 Generator", "4 Spindle and brake", "5 Nacelle and bedplate", "6 Yaw",
    "7 Electrical and power electronics", "8 Tower", "9 Final assembly and test", "10 Tooling (written off)",
    "11 Foundation (site)", "12 Installation (site)")

# A ROTOR — blade split into its materials; labour on the first line
add("1", "NM8-100", "Blade Ø8.0 m: glass fabrics (≈14.5 kg in the laminate)", S_BL, 3, "GLASS", 14.5, 1.15, (0, 0, 38, 0, 1.5), buy=0,
    note="Labour per blade 38 h: shells, caps, web, infusion, bond, trim, drill, finish; 1.5 h weigh and match set")
add("1", "NM8-100", "Blade: carbon UD spar caps", S_BL, 3, "CARBON", 4.2, 1.10)
add("1", "NM8-100", "Blade: infusion epoxy + bonding paste", S_BL, 3, "EPOXY", 11.0, 1.35, note="35 % lost in flow media and mixing")
add("1", "NM8-100", "Blade: PVC core", S_BL, 3, "CORE", 3.0, 1.30)
add("1+", "NM8-100", "Blade: vacuum consumables, LE erosion tape, topcoat, lightning receptor + down conductor", S_BL, 3, mb="buy",
    buy=370, note="bag film, peel ply, flow mesh, tubing €160; LE protection + topcoat €120; LPS €90")
add("2", "NM8-105", "Root insert M16, bonded (12 per blade)", S_BL, 36, "C45", 0.8, 1.5, (0, 0.35, 0.15), serv=2.5,
    note="CNC lathe with bar feeder; zinc-flake coating €2.5")
add("3", "NM8-200", "Hub weldment S355NL Ø530 × 10, 3 necks, drum flange", S_HP, 1, "S355", 179.8, 1.45, (22, 14), "C5", 350 + 0.6 * 179.8,
    note="rolled shell, necks from plate; NDT €350 + stress relief; boring mill 14 h for 3 neck faces/bores + flange")
add("4", "NM8-210", "Spinner GRP 4 mm with blade boots", S_HP, 1, "GRP", 27.6, 1.20, (0, 0, 14))
add("5", "NM8-250", "Pitch bearings Dpw 300 four-point (3)", S_HP, 1, mb="buy", buy=3 * 950, h=(0, 0, 0, 0, 1.5), note="€950 each, small slewing ring")
add("6", "NM8-260", "Pitch cranks r140 with pins (3)", S_HP, 1, "MIX", 30.0, 1.8, (2, 6), "C5", 120, note="pins induction hardened €120")
add("7", "NM8-261", "Pitch links 220 mm with spherical eyes (3)", S_HP, 1, "S355", 4.5, 1.5, (1, 2), "C5", buy=6 * 45, note="6 rod ends €45")
add("8", "NM8-262", "Yoke + 3 guide rods", S_HP, 1, "S355", 8.0, 1.6, (2, 4), "C5", buy=225, note="3 chromed rods €40, 3 bushings €35")
add("9", "NM8-270", "Electric pitch cylinder 28.5 kN, 204 mm, servo motor", S_HP, 1, mb="buy", buy=3800, h=(0, 0, 0, 0, 1))
add("10", "NM8-280", "Supercap module + pitch drive/controller", S_HP, 1, mb="buy", buy=2600, h=(0, 0, 0, 4),
    note="48 V supercap €900, servo drive €1,000, I/O €400, enclosure €300")
add("11", "NM8-290", "Nose frame (actuator + electronics carrier)", S_HP, 1, "S355", 6.0, 1.4, (5, 1), "C5")
add("+", "—", "Hub and pitch assembly, pitch function test", S_HP, 1, h=(0, 0, 0, 3, 14), buy=120, note="grease, seals, Loctite")

# B DRIVETRAIN AND GENERATOR
add("12", "NM8-311", "Third caliper bracket 135°", S_DT, 1, "S355", 7.0, 1.5, (2.5, 2), "C5")
add("13", "NM8-913", "Tapered roller bearing 32028 X", S_DT, 2, mb="buy", buy=260)
add("14", "NM8-914", "Overspeed sensors M18 (2)", S_DT, 1, mb="buy", buy=140)
add("15", "NM8-915", "Spring-applied caliper 4.8 kNm, hydraulic release", S_DT, 3, mb="buy", buy=1900,
    note="16 kN clamp, −40 °C pads; largest bought-in item per kNm")
add("15+", "—", "Brake release hydraulic unit (pump, accumulator, NC dump valve, hoses) — not in BOM", S_DT, 1, mb="buy", buy=2150,
    h=(0, 0, 0, 3, 3), note="doc 14: calipers are hydraulically released; the unit was not on bom8")
add("16", "NP1-100D", "Spindle Rev D, 42CrMo4+QT forged", S_DT, 1, "FORGE", 59.2, 1.6, (0, 16), serv=320, note="UT €200, MPI €120; turn, grind seats, drill flange")
add("17", "NP1-101", "Front spacer / seal counterface", S_DT, 1, "CRMO", 1.4, 2.5, (0, 1.5), serv=90, note="induction harden + grind")
add("18", "NP1-102", "Rear seal sleeve", S_DT, 1, "CRMO", 1.3, 2.5, (0, 1.5), serv=90)
add("19", "NP1-200D", "Stator carrier Rev D, 45 dovetail grooves", S_GEN, 1, "S355", 45.4, 1.8, (6, 16), serv=0.6 * 45.4,
    note="16 h incl. 45 dovetail grooves (doc 18: wire EDM or broach)")
add("20", "NP1-201D", "Stator laminations: 45 segment stacks, 13,365 sheets", S_GEN, 1, "M270", 71.0, 1.8, (0, 4, 0, 0, 11),
    note="strip utilisation 55 %; progressive die ≈1 s/sheet; bond 45 stacks 0.25 h each")
add("22", "NP1-203D", "Coils: 45 × 28 turns, 4 × Ø1.55 in hand", S_GEN, 1, "CU200", 20.0, 1.25, (0, 0, 0, 21), buy=380,
    note="insulate 45 × 0.15 h + wind 45 × 0.3 h + coil tests; NKN liner, wedges, sleeving €380")
add("22+", "—", "Stator assembly, connection, VPI, potting, final stator tests", S_GEN, 1, h=(0, 0, 0, 22), buy=450,
    note="doc 18 S80–S120; VPI resin + potting compound €450")
add("21", "NP1-202", "Stator front clamp ring 1.4404", S_GEN, 1, "SS4404", 2.2, 2.5, (0, 2))
add("23", "NP1-210D", "Rotor drum weldment Rev D, 36 fins, 48 ribs", S_GEN, 1, "S355", 95.5, 1.6, (18, 12, 0, 0, 1), "C5", 250 + 0.6 * 95.5,
    note="84 cooling fins/ribs drive the 18 h of welding; NDT €250; one set-up on the boring mill; pre-balance 1 h")
add("24", "NP1-211-F", "Front bearing seal cover", S_DT, 1, "S355", 1.5, 2.0, (0, 1.5), "C5")
add("25", "NP1-211-R", "Rear bearing seal cover", S_DT, 1, "S355", 1.4, 2.0, (0, 1.5), "C5")
add("26", "NP1-212C", "Drum rear cover with 24 fan blades, 5083", S_GEN, 1, "AL5083", 7.2, 2.0, (4, 2))
add("27", "NP1-220F", "Magnets 280 × N45SH 30×15×12 (11.3 kg) + comb, end rings, sleeve", S_GEN, 1, "NDFEB", 280 * 0.0405, 1.02, (0, 0, 0, 0, 28),
    buy=350, note="40.5 g each, 2 % spares; flux sort 3 h, insert 280 (2 people) 19 h, pole map 2 h, sleeve 4 h; G11 comb + sleeve €350")
add("28", "NP1-230", "Brake disc Ø880/Ø652, C45E+N 16 mm", S_DT, 1, "C45", 33.6, 2.9, (0.5, 5), note="cut from 0.9 m square: 97 kg plate; face both sides, 12 lock holes")
add("29", "NP1-310", "Rotor brake caliper bracket (left)", S_DT, 1, "S355", 18.1, 1.5, (3, 3), "C5")
add("30", "NP1-320", "Rotor lock pin Ø20", S_DT, 1, "CRMO", 0.5, 2.5, (0, 1), serv=60)
add("31", "NP1-321", "Lock pin holder with 2 sensor seats", S_DT, 1, "S355", 24.5, 1.6, (4, 4), "C5")
add("+", "—", "Generator join on spindle (T01) + generator tests (EMF, hipot, spin)", S_GEN, 1, h=(0, 0, 0, 6, 8))
add("+", "—", "Drivetrain assembly: bearings, seals, disc, calipers, lock pin, sensors", S_DT, 1, h=(0, 0, 0, 1, 10), buy=180, note="shaft seals, grease")

# C NACELLE
add("32", "NM8-700-1", "Nacelle cover, lower tray GRP 5 mm", S_NAC, 1, "GRP", 15.7, 1.20, (0, 0, 10))
add("33", "NM8-700-2", "Nacelle cover, upper lid GRP 5 mm", S_NAC, 1, "GRP", 17.7, 1.20, (0, 0, 11))
add("34", "NM8-710", "Cover support arms + rear rail", S_NAC, 1, "S235", 8.3, 1.3, (5,), "HDG")
add("35", "NM8-720", "Met mast + heated anemometer, vane, air terminal", S_NAC, 1, "SS4404", 4.5, 1.3, (3, 0, 0, 1), buy=1250,
    note="heated cup anemometer + vane (cold climate) €1,170, air terminal €80")
add("36", "NP8-300", "Bedplate weldment NP8 (plates 20/30/10)", S_NAC, 1, "S355", 124.3, 1.45, (16, 10), "C5", 200 + 0.6 * 124.3,
    note="NDT €200, stress relief, machined seats")

# D YAW
add("37", "NM8-911", "Yaw slewing ring Dpw 410, z165 m4", S_YAW, 1, mb="buy", buy=1650)
add("38", "NM8-912", "Yaw gearmotor 0.25 kW, ≥ 2.3 kNm, motor brake", S_YAW, 2, mb="buy", buy=1450, note="cold-climate planetary gearmotor")
add("39", "NP1-420", "Yaw drive bracket", S_YAW, 2, "S355", 7.7, 1.5, (2.5, 2.5), "C5")
add("40", "NY-400", "Tower-top adapter with friction track", S_YAW, 1, "S355", 118.3, 1.5, (14, 10), "C5", 200 + 0.6 * 118.3)
add("41", "NY-410", "Friction pad unit (springs, organic pads)", S_YAW, 2, "S355", 14.0, 1.5, (3, 3), "C5", buy=160)
add("42", "NY-430", "Yaw lock (screw block)", S_YAW, 1, "MIX", 6.5, 1.8, (1, 3), "C5")
add("43", "NY-440", "Yaw encoder + cam limit switch unit", S_YAW, 1, "S355", 6.0, 1.5, (2, 2, 0, 2), "C5", buy=700, note="absolute encoder €380, cam switch €320")
add("44", "NY-460", "Cable hanger tube + loop cleat", S_YAW, 1, "TUBE", 10.0, 1.2, (3,), "HDG")
add("+", "—", "Yaw assembly and function test", S_YAW, 1, h=(0, 0, 0, 1, 6))

# E ELECTRICAL
add("45", "NM8-600", "Braking / dump resistor box 20 kW", S_EL, 1, "SS4301", 8.0, 1.3, (6, 0, 0, 3), buy=750, note="steel-grid resistors 33 Ω 20 kW €750")
add("46", "NM8-620", "Tower base cabinet IP55 800×600×300 on stand", S_EL, 1, "S235", 25.0, 1.3, (4,), "HDG", buy=750)
add("46+", "—", "Cabinet internals: heater, fans, SPD T1+2, breakers, RCD B, meter, 24 V UPS — not in BOM", S_EL, 1, h=(0, 0, 0, 16), buy=2100)
add("47", "NM8-730", "Nacelle junction box IP66 + glands/terminals", S_EL, 1, mb="buy", buy=500, h=(0, 0, 0, 4))
add("48", "NM8-800", "Drop cable route: PE duct Ø110, glands, clamps", S_EL, 1, mb="buy", buy=120)
add("78", "NM8-600-K1", "Contactor K1 NC + safety relay PL d", S_EL, 1, mb="buy", buy=520, h=(0, 0, 0, 2))
add("79a", "NM8-620-PE", "Converter: active rectifier SiC 1200 V, film DC link, sensors, heatsink, PCBs", S_EL, 1, mb="make", buy=1550, h=(0, 0, 0, 10),
    note="SiC six-pack €220, driver €180, film caps €380, sensors €150, heatsink/fans €220, PCBs €250, mech €150")
add("79b", "NM8-620-PE", "dv/dt filter at rectifier", S_EL, 1, mb="buy", buy=450)
add("79c", "NM8-620-PE", "Dump chopper + hardware comparator board", S_EL, 1, buy=280, h=(0, 0, 0, 3))
add("79d", "NM8-620-PE", "AC module 12 kW grid-tie/heating: SiC, LCL filter, EN 50549 relay, 2 contactors", S_EL, 1, buy=2640, h=(0, 0, 0, 12),
    note="LCL inductors €650, interface relay €550, contactors €260, power stage €1,180")
add("79e", "NM8-620-PE", "48 V battery module 12 kW (4 × 3 kW DAB)", S_EL, 1, buy=2470, h=(0, 0, 0, 14),
    note="only needed off-grid: option, not standard (see lever list)")
add("79f", "NM8-620-PE", "Turbine controller board, I/O, comms (4G/Ethernet)", S_EL, 1, buy=950, h=(0, 0, 0, 6), note="software is development, not here")
add("79g", "NM8-620-PE", "Electronics end-of-line load test", S_EL, 1, h=(0, 0, 0, 6))
for pos, pid, name, qty, eur in [("67", "NM8-800-W1", "Cable H07RN-F 4G10 generator → box", 3, 9.5), ("68", "NM8-800-W2", "Cable H07RN-F 4G10 box → loop → hand hole", 12, 9.5),
                                 ("69", "NM8-800-W3", "Cable NYY-J 4×10 hand hole → cabinet", 4, 7.5), ("70", "NM8-800-W4", "Cable ÖLFLEX 4G1.5 shielded (calipers)", 20, 5.5),
                                 ("71", "NM8-800-W5", "Cable LiYCY 12×0.5 (sensors)", 16, 4.2), ("72", "NM8-800-W6", "Cable ÖLFLEX 7G1.5 (yaw motors)", 16, 5.0)]:
    add(pos, pid, name, S_EL, qty, unit="m", mb="buy", buy=eur)
add("73", "NM8-800-W7", "Slip ring 6 power + 6 signal (pitch)", S_HP, 1, mb="buy", buy=850)
add("74", "NM8-800-W8", "Earthing kit Cu 50 mm², ring earth, 2 rods", S_FD, 1, mb="buy", buy=520)

# F TOWER
add("49", "NM8-400", "Tower 8 m Ø400 t10/8, flanges, door, galvanised", S_TW, 1, "S355", 699.8, 1.12, (30, 4), "HDG", 450,
    note="roll 2 cans, long seams, circ seam, 2 flanges, hand-hole frame; NDT €450")
add("50", "NM8-401", "Hand-hole cover with gasket", S_TW, 1, "S355", 3.3, 1.5, (1.5,), "HDG", buy=25)
add("51", "NM8-410", "Base hinge brackets + hinge pin Ø50", S_TW, 1, "MIX", 37.4, 1.5, (6, 3), "HDG")

# J FASTENERS
for pos, pid, name, qty, eur, sub in [("58", "NM8-900-01", "Bolt M16×90 10.9 zinc-flake + washer (blade roots)", 36, 2.2, S_HP),
                                      ("59", "NM8-900-02", "Bolt M16×70 10.9 (hub to drum)", 12, 1.85, S_HP),
                                      ("60", "NM8-900-03", "Bolt M16×80 10.9 (pitch bearing to hub)", 60, 2.0, S_HP),
                                      ("61", "NM8-900-04", "Bolt M20×90 10.9 (spindle to bedplate)", 12, 3.4, S_DT),
                                      ("62", "NM8-900-05", "HV set M16×110 (yaw inner ring)", 16, 3.6, S_YAW),
                                      ("63", "NM8-900-06", "Bolt M16×70 10.9 (yaw outer, pads, calipers, brackets)", 40, 1.85, S_YAW),
                                      ("64", "NM8-900-07", "HV set M20×90 (adapter to tower)", 16, 5.2, S_TW),
                                      ("65", "NM8-900-08", "Nut M24 8.8 HDG + plate washer", 56, 3.2, S_FD),
                                      ("66", "NM8-900-09", "Small fasteners kit M6–M12 A4", 1, 180, S_NAC)]:
    add(pos, pid, name, sub, qty, mb="buy", buy=eur)

# FINAL ASSEMBLY
add("+", "—", "Nacelle final assembly: generator on bedplate, yaw, cover, mast, wiring", S_FA, 1, h=(0, 0, 0, 8, 18))
add("+", "—", "Factory acceptance test (spin on test drive, brake, yaw, safety chain)", S_FA, 1, h=(0, 0, 0, 6, 6))
add("+", "—", "QA inspection, records, CE technical file per unit, labels", S_FA, 1, h=(0, 0, 0, 0, 8), buy=60)
add("+", "—", "Sealants, grease, touch-up paint, packing, transport frame", S_FA, 1, h=(0, 0, 0, 0, 4), buy=350)

# TOOLING (one-off, written off over VOLUME)
add("54", "NM8-110-1", "Blade mould lower half + CNC-milled plug (shared)", S_TL, 1, "TOOLGRP", 118.1, 1.2, (0, 0, 120), buy=14000, tool=True,
    note="plug milled outside €14,000; mould life ≈ 200 pulls ≥ 150 blades for 50 turbines")
add("55", "NM8-110-2", "Blade mould upper half", S_TL, 1, "TOOLGRP", 118.1, 1.2, (0, 0, 110), tool=True)
add("56", "NM8-110-3", "Blade mould frame RHS 80×80×4", S_TL, 1, "S235", 178.6, 1.1, (40,), tool=True)
add("57", "NM8-420", "Gin pole 3.0 m (erection tool)", S_TL, 1, "TUBE", 94.0, 1.15, (12,), "HDG", tool=True)
add("T", "—", "Spinner + nacelle cover plugs and moulds (3 moulds)", S_TL, 1, buy=25000, tool=True)
add("T", "—", "Stator lamination progressive die + bonding fixture T03", S_TL, 1, buy=27500, tool=True)
add("T", "—", "Winding chuck T04, stator stand T05, VPI frame T07, potting moulds T08", S_TL, 1, buy=10000, tool=True)
add("T", "—", "Magnet tools T02, T06 mandrel, T09/T10 flux tester + pole scanner, T01 join guide", S_TL, 1, buy=20000, tool=True)
add("T", "—", "Weld jigs: hub, drum, bedplate, adapter, tower rollers", S_TL, 1, buy=23000, tool=True)
add("T", "—", "Root insert jig, blade drilling and balancing fixtures", S_TL, 1, buy=4000, tool=True)
add("T", "—", "Generator / nacelle test drive and electronics load bench", S_TL, 1, buy=35000, tool=True)

# G FOUNDATION (site)
add("52", "NM8-500", "Spread footing 3.0 × 3.0 m: excavation, formwork, fix rebar, pour, backfill", S_FD, 1, h=(0, 0, 0, 0, 0, 32), buy=1400 + 400 + 650,
    note="excavator 2 days €1,400, formwork €400, pump €650")
add("53", "NM8-510", "Anchor cage 16 × M24 + 4 hinge anchors, template rings", S_FD, 1, "S355", 40.0, 1.5, (8,), "HDG", buy=20 * 38,
    note="20 HDG M24 8.8 rods €38")
add("75", "NM8-500-M1", "Concrete C30/37 XF4", S_FD, 6.2, "CONC", 1, 1.0, unit="m³", mb="buy")
add("76", "NM8-500-M2", "Rebar B500C", S_FD, 1, "REBAR", 460, 1.0, mb="buy")
add("77", "NM8-500-M3", "Non-shrink grout ≥ 40 MPa", S_FD, 70, unit="l", mb="buy", buy=4.0)

# INSTALLATION (site)
add("+", "—", "Transport factory → site (truck with crane)", S_IN, 1, mb="buy", buy=1500)
add("+", "—", "Rotor assembly on ground, tilt-up with gin pole and winch, bolt-up", S_IN, 1, h=(0, 0, 0, 0, 0, 30), buy=600, note="winch/telehandler hire €600")
add("+", "—", "Cabling, commissioning, grid protection test, handover", S_IN, 1, h=(0, 0, 0, 0, 0, 16), buy=800, note="travel and lodging €800")

# ------------------------------------------------------------------ evaluation (mirrors the sheet formulas)
HR = ("R_FAB", "R_MACH", "R_COMP", "R_ELEC", "R_ASSY", "R_SITE")
def evaluate(parts, rates):
    rows = []
    for p in parts:
        f = 1 / rates["VOLUME"] if p["tool"] else 1.0
        mat = p["qty"] * p["kg"] * p["bf"] * rates.get(p["mat"], 0)
        lab = p["qty"] * sum(h * rates[r] for h, r in zip(p["h"], HR))
        srv = p["qty"] * (p["kg"] * rates.get(p["coat"], 0) + p["serv"])
        buy = p["qty"] * p["buy"]
        rows.append(dict(p, f=f, mat=mat * f, lab=lab * f, srv=srv * f, bought=buy * f, total=(mat + lab + srv + buy) * f,
                         hours=[p["qty"] * h * f for h in p["h"]]))
    return rows

def rollup(rows):
    subs = {}
    for r in rows:
        s = subs.setdefault(r["sub"], dict(mat=0, lab=0, srv=0, bought=0, total=0, hours=0))
        for k in ("mat", "lab", "srv", "bought", "total"):
            s[k] += r[k]
        s["hours"] += sum(r["hours"])
    return dict(sorted(subs.items(), key=lambda kv: int(kv[0].split()[0])))

rows = evaluate(P, R)
subs = rollup(rows)
EXW = [s for s in subs if not s.startswith(("11", "12"))]
exw = sum(subs[s]["total"] for s in EXW)
site = sum(subs[s]["total"] for s in subs if s.startswith(("11", "12")))

# ------------------------------------------------------------------ LC8 deltas (doc 38) on the same lines
import copy
def lc8_parts():
    Q = copy.deepcopy(P)
    out = []
    bl = 18.7 / 34.1
    for p in Q:
        n = p["name"]; pid = p["pid"]
        if pid in ("NM8-250", "NM8-260", "NM8-261", "NM8-262", "NM8-270", "NM8-280", "NM8-290", "NM8-800-W7", "NM8-900-03", "NM8-311"):
            continue                                            # no pitch system, no slip ring, no third caliper bracket
        if pid == "NM8-100" and p["mat"]:
            p["kg"] *= bl
            if p["h"][2]: p["h"] = (0, 0, 30, 0, 1.5)           # slimmer blade, same steps
        if pid == "NM8-105": p["qty"] = 30                      # 10 × M16 per blade
        if pid == "NM8-900-01": p["qty"] = 30
        if pid == "NM8-200": p.update(name="Fixed welded hub (S6 scaled) ≈ 98 kg", kg=98.0, h=(14, 6), serv=250 + 0.6 * 98)
        if pid == "NM8-210": p.update(kg=13.9, h=(0, 0, 9))
        if n.startswith("Hub and pitch assembly"): p.update(h=(0, 0, 0, 0, 4), buy=40)
        if pid == "NM8-915": p.update(qty=1, buy=1800)
        if pid == "NP1-200D": p["kg"] = 39.9
        if pid == "NP1-201D": p.update(kg=71.0 * 73 / 104, h=(0, 2.8, 0, 0, 11))
        if pid == "NP1-203D": p["kg"] = 17.0
        if pid == "NP1-210D": p["kg"] = 91.2
        if pid == "NP1-220F": p.update(kg=200 * 0.0405, h=(0, 0, 0, 0, 21), buy=280)
        if pid == "NP8-300": p["kg"] = 122.1
        if pid == "NM8-911": p["buy"] = 1400
        if pid == "NY-400": p["kg"] = 106.7
        if pid == "NM8-110-1": p["kg"] *= 0.8; p["buy"] = 12000
        if pid == "NM8-110-2": p["kg"] *= 0.8
        if n.startswith("Generator / nacelle test"): p["buy"] = 30000
        if n.startswith("Spinner + nacelle"): p["buy"] = 22000
        if n.startswith("Weld jigs"): p["buy"] = 20000
        out.append(p)
    return out

rows_lc = evaluate(lc8_parts(), R)
subs_lc = rollup(rows_lc)
exw_lc = sum(subs_lc[s]["total"] for s in subs_lc if not s.startswith(("11", "12")))
site_lc = sum(subs_lc[s]["total"] for s in subs_lc if s.startswith(("11", "12")))

# volume sensitivity
def at_volume(v):
    rr = dict(R, VOLUME=v)
    rw = evaluate(P, rr)
    return sum(r["total"] for r in rw if not r["sub"].startswith(("11", "12")))
sens = {v: at_volume(v) for v in (10, 25, 50, 100, 200)}
# magnet price sensitivity
mag_sens = {pr: exw + (pr - R["NDFEB"]) * 280 * 0.0405 * 1.02 for pr in (100, 150, 200, 250)}

_ex = [r for r in rows if not r["sub"].startswith(("11", "12"))]
_bl = [r for r in _ex if r["pid"] == "NM8-100"]
_blade = dict(_bl[0], name="Blades (3), all lines NM8-100: labour, glass, carbon, epoxy, core, consumables", total=sum(r["total"] for r in _bl), merged=True)
top = sorted([r for r in _ex if r["pid"] != "NM8-100"] + [_blade], key=lambda r: -r["total"])[:25]
hours = [sum(r["hours"][i] for r in rows if not r["sub"].startswith(("11", "12"))) for i in range(5)]
by_kind = {k: sum(r[k] for r in rows if not r["sub"].startswith(("11", "12"))) for k in ("mat", "lab", "srv", "bought")}

res = dict(exw=exw, site=site, contingency=R["CONTINGENCY"], exw_with_cont=exw * (1 + R["CONTINGENCY"]),
           subs={k: {kk: round(vv) for kk, vv in v.items()} for k, v in subs.items()},
           lc8=dict(exw=exw_lc, site=site_lc, subs={k: round(v["total"]) for k, v in subs_lc.items()}),
           volume_sensitivity=sens, magnet_sensitivity=mag_sens, hours_by_trade=dict(zip(("fab", "mach", "comp", "elec", "assy"), hours)),
           by_kind=by_kind, top=[(r["pos"], r["pid"], r["name"], r["sub"], round(r["total"])) for r in top], n_lines=len(P))
(OUT / "cost_m8.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))

# ------------------------------------------------------------------ workbook
wb = Workbook()
F = "Arial"
fb = Font(name=F, bold=True); fn = Font(name=F); fblue = Font(name=F, color="0000FF"); fgreen = Font(name=F, color="008000")
fhead = Font(name=F, bold=True, color="FFFFFF"); fill_h = PatternFill("solid", fgColor="1F4E78"); fill_y = PatternFill("solid", fgColor="FFFF00")
fill_s = PatternFill("solid", fgColor="DDEBF7"); thin = Side(style="thin", color="BFBFBF")
EUR = '#,##0;(#,##0);"-"'; EUR1 = '#,##0.0;(#,##0.0);"-"'; PCT = '0.0%'

# Rates
ws = wb.active; ws.title = "Rates"
ws["A1"] = "Rate assumptions — 12 kW M8 cost model (doc 39). Blue = input, change freely; every cost recalculates."; ws["A1"].font = fb
for c, t in enumerate(("Key", "Value", "Unit", "Assumption / source"), 1):
    x = ws.cell(row=3, column=c, value=t); x.font = fhead; x.fill = fill_h
for i, (k, v, u, n) in enumerate(RATES, start=4):
    ws.cell(row=i, column=1, value=k).font = fn
    x = ws.cell(row=i, column=2, value=v); x.font = fblue
    if k in ("VOLUME", "NDFEB", "CONTINGENCY"): x.fill = fill_y
    if k == "CONTINGENCY": x.number_format = PCT
    ws.cell(row=i, column=3, value=u).font = fn; ws.cell(row=i, column=4, value=n).font = fn
RLAST = 3 + len(RATES)
RROW = {k: 4 + i for i, (k, *_) in enumerate(RATES)}
ws.column_dimensions["A"].width = 14; ws.column_dimensions["B"].width = 10; ws.column_dimensions["C"].width = 10; ws.column_dimensions["D"].width = 95
ws.cell(row=RLAST + 2, column=1, value="Scope: series manufacturing cost per turbine (material, labour, outside services, bought-in, tooling share). "
        "Excludes development, certification, software, warranty, sales, margin and VAT. Yellow = the three assumptions that move the total most.").font = fn
def rr(k): return f"Rates!$B${RROW[k]}"

# Parts
wp = wb.create_sheet("Parts")
H = ["Pos", "Part no.", "Description", "Subsystem", "Qty", "Unit", "Make/buy", "Material key", "Net kg each", "Buy factor", "€/kg",
     "Material €", "h fab", "h mach", "h comp", "h elec", "h assy", "h site", "Labour €", "Coating", "Coating €", "Other services € each",
     "Bought-in € each", "Tooling?", "Factor", "Cost per turbine €", "ISK per turbine", "Material € pt", "Labour € pt", "Services € pt",
     "Bought € pt", "Hours pt", "Notes / assumption"]
for c, t in enumerate(H, 1):
    x = wp.cell(row=1, column=c, value=t); x.font = fhead; x.fill = fill_h; x.alignment = Alignment(wrap_text=True, vertical="top")
key_rng = f"Rates!$A$4:$A${RLAST}"; val_rng = f"Rates!$B$4:$B${RLAST}"
for i, p in enumerate(P, start=2):
    vals = [p["pos"], p["pid"], p["name"], p["sub"], p["qty"], p["unit"], p["mb"], p["mat"], p["kg"], p["bf"]]
    for c, v in enumerate(vals, 1):
        x = wp.cell(row=i, column=c, value=v); x.font = fblue if c in (5, 9, 10) else fn
    wp.cell(row=i, column=11, value=f'=IF(H{i}="",0,IFERROR(INDEX({val_rng},MATCH(H{i},{key_rng},0)),0))').font = fgreen
    wp.cell(row=i, column=12, value=f"=E{i}*I{i}*J{i}*K{i}")
    for j, h in enumerate(p["h"]):
        wp.cell(row=i, column=13 + j, value=h).font = fblue
    wp.cell(row=i, column=19, value=f"=E{i}*(M{i}*{rr('R_FAB')}+N{i}*{rr('R_MACH')}+O{i}*{rr('R_COMP')}+P{i}*{rr('R_ELEC')}+Q{i}*{rr('R_ASSY')}+R{i}*{rr('R_SITE')})")
    wp.cell(row=i, column=20, value=p["coat"]).font = fblue
    wp.cell(row=i, column=21, value=f'=IF(T{i}="",0,E{i}*I{i}*IFERROR(INDEX({val_rng},MATCH(T{i},{key_rng},0)),0))')
    wp.cell(row=i, column=22, value=round(p["serv"], 2)).font = fblue
    wp.cell(row=i, column=23, value=p["buy"]).font = fblue
    wp.cell(row=i, column=24, value="tooling" if p["tool"] else "").font = fn
    wp.cell(row=i, column=25, value=f'=IF(X{i}="tooling",1/{rr("VOLUME")},1)')
    wp.cell(row=i, column=26, value=f"=(L{i}+S{i}+U{i}+E{i}*V{i}+E{i}*W{i})*Y{i}").font = fb
    wp.cell(row=i, column=27, value=f"=Z{i}*{rr('ISK_PER_EUR')}")
    wp.cell(row=i, column=28, value=f"=L{i}*Y{i}"); wp.cell(row=i, column=29, value=f"=S{i}*Y{i}")
    wp.cell(row=i, column=30, value=f"=(U{i}+E{i}*V{i})*Y{i}"); wp.cell(row=i, column=31, value=f"=E{i}*W{i}*Y{i}")
    wp.cell(row=i, column=32, value=f"=E{i}*SUM(M{i}:R{i})*Y{i}")
    wp.cell(row=i, column=33, value=p["note"]).font = fn
    for c in (11, 12, 19, 21, 22, 23, 26, 27, 28, 29, 30, 31):
        wp.cell(row=i, column=c).number_format = EUR
    wp.cell(row=i, column=25).number_format = "0.000"; wp.cell(row=i, column=32).number_format = EUR1
    for c in range(1, 34):
        if wp.cell(row=i, column=c).font != fb and c not in (5, 9, 10, 11, 13, 14, 15, 16, 17, 18, 20, 22, 23):
            wp.cell(row=i, column=c).font = fb if c == 26 else fn
PL = 1 + len(P)
wp.cell(row=PL + 1, column=3, value="Sum of all lines (ex-works + site)").font = fb
for c in (26, 27, 28, 29, 30, 31, 32):
    L_ = get_column_letter(c)
    x = wp.cell(row=PL + 1, column=c, value=f"=SUM({L_}2:{L_}{PL})"); x.font = fb; x.number_format = EUR
widths = dict(A=5, B=12, C=62, D=26, E=6, F=5, G=7, H=9, I=8, J=6, K=7, L=9, M=6, N=6, O=6, P=6, Q=6, R=6, S=9, T=7, U=8, V=9, W=9, X=8, Y=6, Z=11, AA=12, AB=9, AC=9, AD=9, AE=9, AF=7, AG=70)
for k, v in widths.items(): wp.column_dimensions[k].width = v
wp.freeze_panes = "D2"; wp.auto_filter.ref = f"A1:AG{PL}"

# Summary
wsum = wb.create_sheet("Summary", 0)
wsum["A1"] = "12 kW M8 on 8 m tower — manufacturing cost per turbine (doc 39)"; wsum["A1"].font = Font(name=F, bold=True, size=14)
wsum["A2"] = "Live: all figures are formulas on the Parts and Rates sheets. € unless stated."; wsum["A2"].font = fn
hdr = ["Subsystem", "Material €", "Labour €", "Services €", "Bought-in €", "Total €", "Share of ex-works", "Total ISK", "Labour hours"]
for c, t in enumerate(hdr, 1):
    x = wsum.cell(row=4, column=c, value=t); x.font = fhead; x.fill = fill_h; x.alignment = Alignment(wrap_text=True)
r0 = 5; sub_rows = {}
order = list(subs.keys())
rng = lambda col: f"Parts!${col}$2:${col}${PL}"
for i, s in enumerate(order):
    r = r0 + i if not s.startswith(("11", "12")) else None
    sub_rows[s] = r
ex_list = [s for s in order if not s.startswith(("11", "12"))]
for i, s in enumerate(ex_list):
    r = r0 + i; sub_rows[s] = r
    wsum.cell(row=r, column=1, value=s).font = fn
    for c, col in zip((2, 3, 4, 5), ("AB", "AC", "AD", "AE")):
        x = wsum.cell(row=r, column=c, value=f'=SUMIFS({rng(col)},{rng("D")},$A{r})'); x.number_format = EUR; x.font = fgreen
    wsum.cell(row=r, column=6, value=f"=SUM(B{r}:E{r})").number_format = EUR
    wsum.cell(row=r, column=9, value=f'=SUMIFS({rng("AF")},{rng("D")},$A{r})').number_format = EUR1
rex = r0 + len(ex_list)
for i, s in enumerate(ex_list):
    r = r0 + i
    wsum.cell(row=r, column=7, value=f"=IF($F${rex}=0,0,F{r}/$F${rex})").number_format = PCT
    wsum.cell(row=r, column=8, value=f"=F{r}*{rr('ISK_PER_EUR')}").number_format = EUR
wsum.cell(row=rex, column=1, value="Ex-works turbine (factory gate)").font = fb
for c in range(2, 10):
    L_ = get_column_letter(c)
    if c == 7:
        wsum.cell(row=rex, column=c, value=f"=IF($F${rex}=0,0,F{rex}/$F${rex})").number_format = PCT
    elif c == 8:
        wsum.cell(row=rex, column=c, value=f"=F{rex}*{rr('ISK_PER_EUR')}").number_format = EUR
    else:
        wsum.cell(row=rex, column=c, value=f"=SUM({L_}{r0}:{L_}{rex-1})").number_format = EUR if c != 9 else EUR1
    wsum.cell(row=rex, column=c).font = fb; wsum.cell(row=rex, column=c).fill = fill_s
rc = rex + 1
wsum.cell(row=rc, column=1, value="Contingency on ex-works (Rates!CONTINGENCY)").font = fn
wsum.cell(row=rc, column=6, value=f"=F{rex}*{rr('CONTINGENCY')}").number_format = EUR
wsum.cell(row=rc, column=8, value=f"=F{rc}*{rr('ISK_PER_EUR')}").number_format = EUR
rcx = rc + 1
wsum.cell(row=rcx, column=1, value="Ex-works incl. contingency").font = fb
wsum.cell(row=rcx, column=6, value=f"=F{rex}+F{rc}").number_format = EUR; wsum.cell(row=rcx, column=6).font = fb
wsum.cell(row=rcx, column=8, value=f"=F{rcx}*{rr('ISK_PER_EUR')}").number_format = EUR; wsum.cell(row=rcx, column=8).font = fb
site_list = [s for s in order if s.startswith(("11", "12"))]
rs0 = rcx + 2
for i, s in enumerate(site_list):
    r = rs0 + i
    wsum.cell(row=r, column=1, value=s).font = fn
    for c, col in zip((2, 3, 4, 5), ("AB", "AC", "AD", "AE")):
        x = wsum.cell(row=r, column=c, value=f'=SUMIFS({rng(col)},{rng("D")},$A{r})'); x.number_format = EUR; x.font = fgreen
    wsum.cell(row=r, column=6, value=f"=SUM(B{r}:E{r})").number_format = EUR
    wsum.cell(row=r, column=8, value=f"=F{r}*{rr('ISK_PER_EUR')}").number_format = EUR
    wsum.cell(row=r, column=9, value=f'=SUMIFS({rng("AF")},{rng("D")},$A{r})').number_format = EUR1
rin = rs0 + len(site_list)
wsum.cell(row=rin, column=1, value="Installed on firm ground (ex-works incl. contingency + site)").font = fb
wsum.cell(row=rin, column=6, value=f"=F{rcx}+SUM(F{rs0}:F{rin-1})").number_format = EUR; wsum.cell(row=rin, column=6).font = fb
wsum.cell(row=rin, column=8, value=f"=F{rin}*{rr('ISK_PER_EUR')}").number_format = EUR; wsum.cell(row=rin, column=8).font = fb
wsum.cell(row=rin, column=6).fill = fill_s
rchk = rin + 2
wsum.cell(row=rchk, column=1, value="Check: Parts sheet total minus (ex-works + site), must be 0").font = fn
wsum.cell(row=rchk, column=6, value=f"=ROUND(Parts!Z{PL+1}-F{rex}-SUM(F{rs0}:F{rin-1}),2)").number_format = EUR
rnote = rchk + 2
for k, t in enumerate([
    "Scope: series cost per turbine at the volume in Rates!VOLUME, made in-house in Iceland as far as practical; no development, certification, software, warranty, sales or margin.",
    "Bought-in prices are 2026 list/quote-level estimates, not RFQ results. Magnets (N45SH, non-Asian) are the most uncertain single price: ±30 %.",
    "Site lines (11, 12) are for an 8 m tower on firm ground, tilted up with the gin pole; soft ground adds concrete (doc 37 §3).",
], start=0):
    wsum.cell(row=rnote + k, column=1, value=t).font = fn
for k, v in dict(A=58, B=12, C=12, D=12, E=12, F=12, G=10, H=14, I=10).items(): wsum.column_dimensions[k].width = v

# Drivers (top 25, order fixed at build time)
wd = wb.create_sheet("Top drivers", 1)
wd["A1"] = "Top 25 cost lines per turbine (ex-works). Order set when the file was built; values are live links to Parts."; wd["A1"].font = fb
for c, t in enumerate(("Rank", "Pos", "Part no.", "Description", "Subsystem", "Cost per turbine €", "Share of ex-works", "Cumulative share"), 1):
    x = wd.cell(row=3, column=c, value=t); x.font = fhead; x.fill = fill_h
idx = {id(p): i + 2 for i, p in enumerate(P)}
row_of = {}
for i, p in enumerate(P):
    row_of[(p["pos"], p["pid"], p["name"])] = i + 2
for k, r in enumerate(top, start=1):
    R_ = 3 + k
    wd.cell(row=R_, column=1, value=k).font = fn
    if r.get("merged"):
        for c, v in zip((2, 3, 4, 5), ("1", "NM8-100", r["name"], r["sub"])):
            wd.cell(row=R_, column=c, value=v).font = fn
        x = wd.cell(row=R_, column=6, value=f'=SUMIFS(Parts!$Z$2:$Z${PL},Parts!$B$2:$B${PL},"NM8-100")'); x.font = fgreen; x.number_format = EUR
    else:
        pr = row_of[(r["pos"], r["pid"], r["name"])]
        for c, col in zip((2, 3, 4, 5), ("A", "B", "C", "D")):
            wd.cell(row=R_, column=c, value=f"=Parts!{col}{pr}").font = fgreen
        x = wd.cell(row=R_, column=6, value=f"=Parts!Z{pr}"); x.font = fgreen; x.number_format = EUR
    wd.cell(row=R_, column=7, value=f"=F{R_}/Summary!$F${rex}").number_format = PCT
    wd.cell(row=R_, column=8, value=f"=SUM($F$4:F{R_})/Summary!$F${rex}").number_format = PCT
for k, v in dict(A=6, B=6, C=13, D=70, E=30, F=14, G=12, H=12).items(): wd.column_dimensions[k].width = v

# LC8 comparison (static, from this script)
wl = wb.create_sheet("LC8 comparison")
wl["A1"] = "M8 vs LC8 (doc 38) on the same rates and 8 m tower — values written by cost_m8.py (LC8 = M8 lines with doc 38 deltas)"; wl["A1"].font = fb
for c, t in enumerate(("Subsystem", "M8 €", "LC8 €", "Difference €"), 1):
    x = wl.cell(row=3, column=c, value=t); x.font = fhead; x.fill = fill_h
allsubs = list(subs.keys())
for i, s in enumerate(allsubs, start=4):
    wl.cell(row=i, column=1, value=s).font = fn
    wl.cell(row=i, column=2, value=round(subs[s]["total"])).number_format = EUR
    wl.cell(row=i, column=3, value=round(subs_lc.get(s, {"total": 0})["total"])).number_format = EUR
    wl.cell(row=i, column=4, value=f"=C{i}-B{i}").number_format = EUR
re_ = 4 + len(allsubs)
wl.cell(row=re_, column=1, value="Ex-works (1–10)").font = fb
wl.cell(row=re_, column=2, value=f"=SUM(B4:B{re_-3})").number_format = EUR
wl.cell(row=re_, column=3, value=f"=SUM(C4:C{re_-3})").number_format = EUR
wl.cell(row=re_, column=4, value=f"=C{re_}-B{re_}").number_format = EUR
wl.cell(row=re_ + 2, column=1, value="LC8 on an 8 m tower is not designed: 1P at 178 rpm is 2.97 Hz, on the 8 m tower's 2.78 Hz. Tower and site kept equal here.").font = fn
for k, v in dict(A=40, B=12, C=12, D=14).items(): wl.column_dimensions[k].width = v

fn_x = OUT / "39-m8-cost-breakdown.xlsx"
wb.save(fn_x)
print(json.dumps(dict(exw=round(exw), site=round(site), exw_lc8=round(exw_lc), subs={k: round(v["total"]) for k, v in subs.items()},
                      lc8={k: round(v["total"]) for k, v in subs_lc.items()}, sens={k: round(v) for k, v in sens.items()},
                      kind={k: round(v) for k, v in by_kind.items()}, hours=[round(h) for h in hours], n=len(P)), indent=1, ensure_ascii=False))
for r in top: print(f'{r["total"]:8.0f}  {r["pos"]:4s} {r["pid"]:11s} {r["name"][:70]}')
