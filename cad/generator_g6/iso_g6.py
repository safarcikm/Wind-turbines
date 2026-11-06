"""Isometric views for doc 29 (6 kW generator G6 = Rev C active part without the passive cooling parts).

Run:  python3 iso_g6.py [--png]   -> out/iso/IG01, IG02 *.svg (+ .png)

Reuses the Rev C renderer (cad/generator_rc/iso_rc.py) with the inner fins, outer ribs and
rear-cover fan blades left off: the 6 kW duty does not need them (doc 29 §5).
"""
from __future__ import annotations
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "generator_rc"))
import iso_rc as I  # noqa: E402

OUT = HERE / "out" / "iso"
I.add_fins_ribs = lambda *a, **k: None


def plain_cover(sc, dz=0.0, cut=(0.0, 360.0), layer=0):
    sc.revolve(I.G.REAR_COVER, I.C["al"], cut[0], cut[1], step=5, axial=(I.X0 + dz, -1), layer=layer)


I.add_rear_cover_fan = plain_cover


def ig01_exploded():
    S = I.Svg(1300, 1240, "IG01 Exploded generator G6")
    S.header("IG01  6 kW generator G6 pulled apart (isometric, exploded)",
             "Same stator, magnets and drum as the 12 kW Rev C. No fins, ribs or fan blades; one brake caliper (not drawn).")
    sc = I.Scene()
    DZ_ROTOR, DZ_STATOR, DZ_COVER = 520.0, 230.0, -130.0
    I.add_spindle(sc); I.add_carrier(sc)
    I.add_stator(sc, dz=DZ_STATOR)
    I.add_rotor_rc(sc, dz=DZ_ROTOR)
    plain_cover(sc, dz=DZ_COVER)
    F = I.fit(sc, 340, 90, 640, 1110)
    sc.render(S, *F)
    a = sc.proj((0, 0, I.X0 + DZ_COVER - 480), *F)
    b = sc.proj((0, 0, I.X0 + DZ_ROTOR - 60), *F)
    S.line(a[0], a[1], b[0], b[1], I.C["grey"], 1.5, "16,6,4,6")
    zr = I.X0 + DZ_ROTOR
    I.tag(S, sc, F, I.cyl_pt(323, 120, zr - 330), 300, 230, 4, ["ROTOR drum Ø646 (Rev C,", "fins and ribs left off)"])
    I.tag(S, sc, F, I.cyl_pt(302, 93, zr - 380), 300, 370, None, ["200 N45SH blocks 30×15×12", "same as 12 kW"])
    I.tag(S, sc, F, I.cyl_pt(437, 330, zr - 443), 1040, 380, None, ["brake disc (Rev C),", "1 caliper 1.5 kNm"])
    I.tag(S, sc, F, I.cyl_pt(290, 45, I.X0 + DZ_STATOR - 380), 300, 660, 3, ["STATOR: 45 segments,", "28 turns, same as 12 kW"])
    I.tag(S, sc, F, I.cyl_pt(70, -20, I.X0 - 80), 1040, 580, 1, ["SPINDLE: fixed"])
    I.tag(S, sc, F, I.cyl_pt(228, 330, I.X0 - 430), 1040, 780, 2, ["CARRIER: 45 dovetail", "grooves"])
    I.tag(S, sc, F, I.cyl_pt(300, 157.5, I.X0 + DZ_COVER - 456), 300, 1010, 5, ["plain rear cover", "(no fan blades)"])
    return S


def ig02_assembled():
    S = I.ir04_assembled()
    return S


def main(png=False):
    OUT.mkdir(parents=True, exist_ok=True)
    S = ig01_exploded(); S.save(OUT / "IG01-iso-exploded.svg")
    S = I.ir04_assembled()
    S.save(OUT / "IG02-iso-assembled.svg")
    t = (OUT / "IG02-iso-assembled.svg").read_text()
    for a, b in (("IR04  Generator Rev C assembled", "IG02  6 kW generator G6 assembled"),
                 ("IR04 Assembled generator Rev C", "IG02 Assembled generator G6"),
                 ("36 inner fins (passive cooling)", "no fins or ribs at 6 kW"),
                 ("rear cover + 24 fan blades", "plain rear cover")):
        t = t.replace(a, b)
    (OUT / "IG02-iso-assembled.svg").write_text(t)
    if png:
        import subprocess
        subprocess.run(["node", str(HERE.parent / "generator_mfg" / "render_png.js"), str(OUT)], check=True)


if __name__ == "__main__":
    main("--png" in sys.argv)
