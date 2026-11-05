"""Build the yaw drawing set (doc 25): PDFs, combined PDF, DXF, PNG previews.

    python3 build.py [--png]
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

import drawings

OUT = Path(__file__).parent / "out"


def main():
    (OUT / "pdf").mkdir(parents=True, exist_ok=True)
    (OUT / "dxf").mkdir(parents=True, exist_ok=True)
    png = "--png" in sys.argv
    if png:
        (OUT / "png").mkdir(exist_ok=True)
    index = []
    with PdfPages(OUT / "NY-drawing-set.pdf") as book:
        for fn in drawings.ALL:
            sh = fn()
            fig = sh.render()
            fig.savefig(OUT / "pdf" / f"{sh.number}.pdf")
            if png:
                fig.savefig(OUT / "png" / f"{sh.number}.png", dpi=110)
            book.savefig(fig)
            plt.close(fig)
            sh.to_dxf(OUT / "dxf" / f"{sh.number}.dxf")
            index.append((sh.number, sh.title, sh.material, sh.mass))
            print(sh.number, sh.title)
    with open(OUT / "drawing-index.md", "w") as f:
        f.write("| Drawing | Title | Material | Mass |\n|---|---|---|---|\n")
        for row in index:
            f.write("| " + " | ".join(row) + " |\n")


if __name__ == "__main__":
    main()
