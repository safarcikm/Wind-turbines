"""Build the P1 drawing set: one PDF per sheet, a combined PDF, DXF files and masses.

    python3 build.py            # writes out/
    python3 build.py --png      # also PNG previews (for review)
"""
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

import drawings
import geometry as G

OUT = Path(__file__).parent / "out"


def main():
    (OUT / "pdf").mkdir(parents=True, exist_ok=True)
    (OUT / "dxf").mkdir(parents=True, exist_ok=True)
    png = "--png" in sys.argv
    if png:
        (OUT / "png").mkdir(exist_ok=True)
    index = []
    with PdfPages(OUT / "NP1-drawing-set.pdf") as book:
        for fn in drawings.ALL:
            sh = fn()
            fig = sh.render()
            name = f"{sh.number}"
            fig.savefig(OUT / "pdf" / f"{name}.pdf")
            if png:
                fig.savefig(OUT / "png" / f"{name}.png", dpi=110)
            book.savefig(fig)
            plt.close(fig)
            sh.to_dxf(OUT / "dxf" / f"{name}.dxf")
            index.append((sh.number, sh.title, sh.material, sh.mass))
            print(f"{sh.number:8s} {sh.title}")
    masses = {it.name: round(it.mass, 2) for it in G.mass_table()}
    masses["total_drivetrain_without_hub"] = round(sum(masses.values()), 1)
    (OUT / "masses.json").write_text(json.dumps(masses, indent=2))
    with open(OUT / "drawing-index.md", "w") as f:
        f.write("| Drawing | Title | Material | Mass |\n|---|---|---|---|\n")
        for row in index:
            f.write("| " + " | ".join(row) + " |\n")


if __name__ == "__main__":
    main()
