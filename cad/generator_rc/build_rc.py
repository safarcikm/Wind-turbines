"""Build the generator Rev C drawing set (doc 23).

    python3 build_rc.py          # out/NP1-generator-RevC.pdf, out/pdf/*.pdf, out/dxf/*.dxf
    python3 build_rc.py --png    # also PNG previews
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

import drawings_rc as D

OUT = Path(__file__).parent / "out"


def main():
    for d in ("pdf", "dxf"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    png = "--png" in sys.argv
    if png:
        (OUT / "png").mkdir(exist_ok=True)
    rows = []
    with PdfPages(OUT / "NP1-generator-RevC.pdf") as book:
        for fn in D.ALL:
            sh = fn()
            fig = sh.render()
            fig.savefig(OUT / "pdf" / f"{sh.number}.pdf")
            if png:
                fig.savefig(OUT / "png" / f"{sh.number}.png", dpi=110)
            book.savefig(fig)
            plt.close(fig)
            sh.to_dxf(OUT / "dxf" / f"{sh.number}.dxf")
            rows.append((sh.number, sh.title, sh.material, sh.mass))
            print(sh.number, sh.title)
    with open(OUT / "drawing-index.md", "w") as f:
        f.write("| Drawing | Title | Material | Mass |\n|---|---|---|---|\n")
        for r in rows:
            f.write("| " + " | ".join(r) + " |\n")


if __name__ == "__main__":
    main()
