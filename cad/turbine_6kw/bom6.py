"""S6 bill of materials (doc 34) from the CAD part list plus fasteners, cables and site materials.

    python3 bom6.py      -> out/bom6.csv, out/bom6.json   (run model6.py first)
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "out"

GROUP_ORDER = ["rotor", "drivetrain", "nacelle", "yaw", "electrical", "tower", "foundation", "tooling"]
GROUP_NAME = {"rotor": "A ROTOR", "drivetrain": "B DRIVETRAIN AND GENERATOR G6", "nacelle": "C NACELLE",
              "yaw": "D YAW SYSTEM", "electrical": "E ELECTRICAL", "tower": "F TOWER", "foundation": "G FOUNDATION",
              "tooling": "H TOOLS AND MOULDS", "kit": "J FASTENERS, CABLES, SITE MATERIALS"}
COMBINE = [(r"^(NS6-100)-\d$", "Blade, glass/epoxy, glass UD caps (B1–B3)"), (r"^(NY-410)-[LR]$", "Friction pad unit"),
           (r"^(NS6-912)-[LR]$", "Yaw gearmotor 0.18 kW 1:1680, motor brake 2 Nm"), (r"^(NP1-420)-[LR]$", "Yaw drive bracket"),
           (r"^(NS6-913)-[FR]$", "Tapered roller bearing 32028 X (front + rear)"), (r"^(NS6-911)-[IO]$", "Yaw slewing ring Dpw 360, z150 m4")]
KIT = [("NS6-900-01", "Stud M12 × 75 10.9 zinc-flake + nut + washer (blade roots)", 30, "buy", "10.9 zinc-flake", 0.12),
       ("NS6-900-02", "Bolt M16 × 70 10.9 (hub to drum)", 12, "buy", "10.9 zinc-flake", 0.17),
       ("NS6-900-03", "Bolt M20 × 90 10.9 (spindle to bedplate)", 12, "buy", "10.9 zinc-flake", 0.32),
       ("NS6-900-04", "HV set M16 × 110 10.9 (yaw inner ring)", 16, "buy", "EN 14399-4", 0.26),
       ("NS6-900-05", "Bolt M16 × 70 10.9 (yaw outer ring, pads, caliper)", 28, "buy", "10.9 zinc-flake", 0.17),
       ("NS6-900-06", "HV set M20 × 90 10.9 (adapter to tower)", 16, "buy", "EN 14399-4", 0.40),
       ("NS6-900-07", "Nut M24 8.8 HDG + plate washer (base, hinge)", 3 * 12 + 8, "buy", "8.8 HDG", 0.15),
       ("NS6-900-08", "Small fasteners kit M8–M12 A4 (cover, spinner, mast, cabinet)", 1, "buy", "A4-70", 2.5),
       ("NS6-800-W1", "Cable H07RN-F 4G10 (generator → box)", 3, "buy", "m", 0.6),
       ("NS6-800-W2", "Cable H07RN-F 4G10 (box → loop → hand hole)", 12, "buy", "m", 0.6),
       ("NS6-800-W3", "Cable NYY-J 4 × 10 (hand hole → cabinet)", 4, "buy", "m", 0.5),
       ("NS6-800-W4", "Cable ÖLFLEX 4G1.5 shielded (brake)", 16, "buy", "m", 0.1),
       ("NS6-800-W5", "Cable LiYCY 12 × 0.5 (sensors)", 16, "buy", "m", 0.12),
       ("NS6-800-W6", "Cable ÖLFLEX 7G1.5 (yaw motors)", 16, "buy", "m", 0.15),
       ("NS6-800-W7", "Earthing conductor Cu 50 mm² + ring earth + 2 rods 3 m", 1, "buy", "Cu", 18.0),
       ("NS6-500-M1", "Concrete C30/37 XF4 air-entrained (firm ground)", "5.5 m³", "buy", "ready-mix", None),
       ("NS6-500-M2", "Rebar B500C (mesh Ø16/150 top + bottom, pedestal cage)", 1, "buy", "≈ 420 kg", 420.0),
       ("NS6-500-M3", "Non-shrink grout ≥ 40 MPa, 30 mm under the base flange", "60 l", "buy", "", None),
       ("NS6-600-K1", "Contactor K1 3-pole NC (mirror contacts) + safety relay PL d", 1, "buy", "", 2.0),
       ("NS6-620-PE", "Converter, dump chopper, AC module, 48 V module, controller (doc 12)", 1, "make", "in-house electronics", 45.0)]


def load():
    return json.loads((OUT / "model6-parts.json").read_text())["parts"]


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
        L["qty"] += p["qty"] if not pid.startswith("NS6-105") else 30
        L["mass_total"] += (p["mass_kg"] or 0.0)
    for L in lines.values():
        if L["pid"] == "NS6-911":
            L["qty"] = 1
            L["mass"] = round(L["mass_total"], 1)
        elif L["pid"] == "NS6-105":
            L["qty"] = 30
            L["mass"] = 0.33
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
    with open(OUT / "bom6.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["pos", "pid", "name", "qty", "make_buy", "material", "mass", "drawing"])
        w.writeheader()
        w.writerows(rows)
    (OUT / "bom6.json").write_text(json.dumps(rows, indent=1))
    print(len(rows), "lines")


if __name__ == "__main__":
    main()
