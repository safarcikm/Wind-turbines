"""M8 12 kW (8 m tower) bill of materials (doc 37) from the CAD part list plus fasteners, cables and site materials.

    python3 bom8.py      -> out/bom8.csv, out/bom8.json   (run model8.py first)
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "out"

GROUP_ORDER = ["rotor", "drivetrain", "nacelle", "yaw", "electrical", "tower", "foundation", "tooling"]
GROUP_NAME = {"rotor": "A ROTOR", "drivetrain": "B DRIVETRAIN AND GENERATOR REV D", "nacelle": "C NACELLE",
              "yaw": "D YAW SYSTEM", "electrical": "E ELECTRICAL", "tower": "F TOWER", "foundation": "G FOUNDATION",
              "tooling": "H TOOLS AND MOULDS", "kit": "J FASTENERS, CABLES, SITE MATERIALS"}
T8 = json.loads((HERE.parent.parent / "analysis" / "variant_m8" / "results" / "tower8_m8.json").read_text())
_TK = "stiff_final_sim8" if "stiff_final_sim8" in T8["towers"] else "stiff"
FND = T8["towers"][_TK]["foundations"]["firm soil (dense gravel, moraine)"]
N_BASE = T8["towers"][_TK]["tower"]["base_flange"]["bolts"]
COMBINE = [(r"^(NM8-100)-\d$", "Blade Ø8.0 m, glass/epoxy, carbon UD caps (B1–B3)"), (r"^(NY-410)-[LR]$", "Friction pad unit"),
           (r"^(NM8-912)-[LR]$", "Yaw gearmotor 0.25 kW, output ≥ 2.3 kNm static, motor brake"), (r"^(NP1-420)-[LR]$", "Yaw drive bracket"),
           (r"^(NM8-913)-[FR]$", "Tapered roller bearing 32028 X (front + rear)"), (r"^(NM8-911)-[IO]$", "Yaw slewing ring Dpw 410, z165 m4"),
           (r"^(NM8-915)(-T)?$", "Spring-applied brake caliper 4.4 kNm (3 on the disc)")]
KIT = [("NM8-900-01", "Bolt M16 × 90 10.9 zinc-flake + washer (blade roots into the pitch bearing inner rings)", 36, "buy", "10.9 zinc-flake", 0.20),
       ("NM8-900-02", "Bolt M16 × 70 10.9 (hub to drum)", 12, "buy", "10.9 zinc-flake", 0.17),
       ("NM8-900-03", "Bolt M16 × 80 10.9 (pitch bearing outer rings to hub necks, 20 each)", 60, "buy", "10.9 zinc-flake", 0.18),
       ("NM8-900-04", "Bolt M20 × 90 10.9 (spindle to bedplate)", 12, "buy", "10.9 zinc-flake", 0.32),
       ("NM8-900-05", "HV set M16 × 110 10.9 (yaw inner ring, PCD 350)", 16, "buy", "EN 14399-4", 0.26),
       ("NM8-900-06", "Bolt M16 × 70 10.9 (yaw outer ring PCD 490, pads, calipers, brackets)", 40, "buy", "10.9 zinc-flake", 0.17),
       ("NM8-900-07", "HV set M20 × 90 10.9 (adapter to tower)", 16, "buy", "EN 14399-4", 0.40),
       ("NM8-900-08", f"Nut M24 8.8 HDG + plate washer (base {N_BASE} × 3, hinge 8)", 3 * N_BASE + 8, "buy", "8.8 HDG", 0.15),
       ("NM8-900-09", "Small fasteners kit M6–M12 A4 (cover, spinner, mast, nose frame, cabinet)", 1, "buy", "A4-70", 3.0),
       ("NM8-800-W1", "Cable H07RN-F 4G10 (generator → box)", 3, "buy", "m", 0.6),
       ("NM8-800-W2", "Cable H07RN-F 4G10 (box → loop → hand hole)", 12, "buy", "m", 0.6),
       ("NM8-800-W3", "Cable NYY-J 4 × 10 (hand hole → cabinet)", 4, "buy", "m", 0.5),
       ("NM8-800-W4", "Cable ÖLFLEX 4G1.5 shielded (3 brake calipers)", 20, "buy", "m", 0.1),
       ("NM8-800-W5", "Cable LiYCY 12 × 0.5 (sensors)", 16, "buy", "m", 0.12),
       ("NM8-800-W6", "Cable ÖLFLEX 7G1.5 (yaw motors)", 16, "buy", "m", 0.15),
       ("NM8-800-W7", "Slip ring 6 power + 6 signal (pitch supply and bus, in the nose)", 1, "buy", "", 1.5),
       ("NM8-800-W8", "Earthing conductor Cu 50 mm² + ring earth + 2 rods 3 m", 1, "buy", "Cu", 18.0),
       ("NM8-500-M1", "Concrete C30/37 XF4 air-entrained (firm ground)", f"{FND['concrete_m3']:.1f} m³", "buy", "ready-mix", None),
       ("NM8-500-M2", "Rebar B500C (mesh top + bottom, pedestal cage)", 1, "buy", f"≈ {round(FND['concrete_m3'] * 75, -1):.0f} kg",
        round(FND["concrete_m3"] * 75, -1)),
       ("NM8-500-M3", "Non-shrink grout ≥ 40 MPa, 30 mm under the base flange", "70 l", "buy", "", None),
       ("NM8-600-K1", "Contactor K1 3-pole NC (mirror contacts) + safety relay PL d", 1, "buy", "", 2.0),
       ("NM8-620-PE", "Converter 12 kW, dump chopper, AC module, 48 V module, controller (doc 12)", 1, "make", "in-house electronics", 60.0)]

def load():
    return json.loads((OUT / "model8-parts.json").read_text())["parts"]


def bom():
    parts = load()
    lines = {}
    order = []
    for p in parts:
        pid, name = p["pid"], p["name"]
        for pat, nm in COMBINE:
            m = re.match(pat, pid)
            if m:
                pid, name = m.group(1), nm
                break
        key = pid
        if key not in lines:
            lines[key] = dict(pid=pid, name=name, qty=0, make_buy=p["make_buy"], material=p["material"], mass=p["mass_kg"],
                              group=p["group"], drawing=p["drawing"], show=p["show"], mass_total=0.0)
            order.append(key)
        L = lines[key]
        L["qty"] += p["qty"] if pid != "NM8-105" else 36
        L["mass_total"] += (p["mass_kg"] or 0.0)
    for L in lines.values():
        if L["pid"] == "NM8-911":
            L["qty"] = 1
            L["mass"] = round(L["mass_total"], 1)
        elif L["pid"] == "NM8-105":
            L["qty"] = 36
            L["mass"] = 0.78
        elif L["pid"] == "NM8-915":
            L["qty"] = 3
            L["mass"] = 9.0
        else:
            L["mass"] = round(L["mass_total"] / max(L["qty"], 1), 2) if L["mass_total"] else None
    rows = []
    pos = 0
    for g in GROUP_ORDER:
        grp = [lines[k] for k in order if lines[k]["group"] == g]
        rows.append(dict(pos="", pid="", name=GROUP_NAME[g], qty="", make_buy="", material="", mass="", drawing=""))
        for L in sorted(grp, key=lambda x: x["pid"]):
            pos += 1
            rows.append(dict(pos=str(pos), pid=L["pid"], name=L["name"], qty=str(L["qty"]), make_buy=L["make_buy"],
                             material=L["material"], mass="" if L["mass"] is None else f"{L['mass']:.1f}", drawing=L["drawing"]))
    rows.append(dict(pos="", pid="", name=GROUP_NAME["kit"], qty="", make_buy="", material="", mass="", drawing=""))
    for pid, name, qty, mb, mat, m in KIT:
        pos += 1
        rows.append(dict(pos=str(pos), pid=pid, name=name, qty=str(qty), make_buy=mb, material=mat, mass="" if m is None else f"{m:.2f}",
                         drawing=pid.split("-")[0] + "-" + pid.split("-")[1]))
    return rows


def main():
    rows = bom()
    with open(OUT / "bom8.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["pos", "pid", "name", "qty", "make_buy", "material", "mass", "drawing"])
        w.writeheader()
        w.writerows(rows)
    (OUT / "bom8.json").write_text(json.dumps(rows, indent=1))
    print(len(rows), "lines")


if __name__ == "__main__":
    main()
