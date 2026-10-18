#!/usr/bin/env python3
"""Cut a big SVG, such as the 60 x 60 cm sheet, into the pages of one PDF, to print on A4 and tape together.

    python scripts/svg_to_pages.py sheet.svg                  # sheet-pages.pdf: 6 A4 pages, as large as they allow
    python scripts/svg_to_pages.py sheet.svg --scale 1        # real size: as many pages as that takes (9 on A4)
    python scripts/svg_to_pages.py sheet.svg -o out.pdf --margin 0 --no-marks

Each page shows one part of the sheet, and the parts are cut exactly where the printable area of a
page ends, so after the unprinted margins are trimmed (or folded under) the pages meet edge to edge.
Small corner marks and a "column 2, row 1" label sit in the margin to help with the order.

A 60 cm sheet is a little more than six A4 pages can hold at real size: 3 pages of 21 cm make 63 cm, but
2 pages of 29.7 cm make only 59.4 cm, and a printer leaves a margin around every page. So by default the
sheet is shrunk to fit 6 pages (about 96% with 5 mm margins), and --scale 1 gives the real size on 9 pages.

The drawing is done by a browser (Chrome, Chromium or Edge), which keeps the SVG as vectors in the PDF.
Set the CHROME environment variable to its path if it is not found by itself.
"""
from __future__ import annotations

import argparse
import glob
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PAPERS = {"A4": (210.0, 297.0), "A3": (297.0, 420.0), "LETTER": (215.9, 279.4)}
UNITS_MM = {"mm": 1.0, "cm": 10.0, "in": 25.4, "pt": 25.4 / 72, "px": 25.4 / 96, "": 25.4 / 96}


class PagesError(Exception):
    pass


def svg_size_mm(text):
    """(width, height) in millimetres from the <svg> tag's width and height (a bare number is a pixel)."""
    tag = re.search(r"<svg\b[^>]*>", text)
    if not tag:
        raise PagesError("this does not look like an SVG file")
    sizes = []
    for name in ("width", "height"):
        found = re.search(rf'\b{name}\s*=\s*"\s*([\d.]+)\s*([a-z]*)\s*"', tag.group(0))
        if not found or found.group(2) not in UNITS_MM:
            raise PagesError(f"the SVG has no usable {name} (it needs a size such as 600mm)")
        sizes.append(float(found.group(1)) * UNITS_MM[found.group(2)])
    return tuple(sizes)


def plan(sheet, paper, margin=5.0, pages=6, scale=None):
    """How to cut `sheet` (width, height in mm) into pages of `paper` with unprinted `margin`.

    With `scale` None the sheet is made as large as fits in exactly `pages` pages; with a scale
    (1 is real size) the fewest pages that hold it. Returns a dict: scale, cols, rows, landscape,
    page (the paper as laid), area (the printable part of a page), pages."""
    if margin < 0:
        raise PagesError("the margin cannot be negative")
    best = None
    for landscape in (False, True):
        page_w, page_h = PAPERS_SWAPPED(paper, landscape)
        area_w, area_h = page_w - 2 * margin, page_h - 2 * margin
        if area_w <= 0 or area_h <= 0:
            raise PagesError("the margin is too large for the paper")
        if scale is None:
            options = [(c, pages // c) for c in range(1, pages + 1) if pages % c == 0]
            for cols, rows in options:
                s = min(cols * area_w / sheet[0], rows * area_h / sheet[1])
                candidate = dict(scale=s, cols=cols, rows=rows, landscape=landscape, page=(page_w, page_h), area=(area_w, area_h))
                if best is None or s > best["scale"] + 1e-9:
                    best = candidate
        else:
            cols = max(1, math.ceil(sheet[0] * scale / area_w - 1e-9))
            rows = max(1, math.ceil(sheet[1] * scale / area_h - 1e-9))
            candidate = dict(scale=scale, cols=cols, rows=rows, landscape=landscape, page=(page_w, page_h), area=(area_w, area_h))
            if best is None or cols * rows < best["cols"] * best["rows"]:
                best = candidate
    best["pages"] = best["cols"] * best["rows"]
    return best


def PAPERS_SWAPPED(paper, landscape):
    width, height = PAPERS[paper]
    return (height, width) if landscape else (width, height)


def _marks(page, margin, label):
    """Corner marks at the corners of the printable area, and the label under it."""
    w, h = page
    m = margin
    tick = min(3.0, m * 0.8)
    if tick <= 0:
        return ""
    lines = []
    for x in (m, w - m):
        for y in (m, h - m):
            dx = -tick if x == m else tick
            dy = -tick if y == m else tick
            lines.append(f'<line x1="{x}" y1="{y}" x2="{x + dx}" y2="{y}"/><line x1="{x}" y1="{y}" x2="{x}" y2="{y + dy}"/>')
    text = ""
    if m >= 4:
        text = f'<text x="{w / 2}" y="{h - m / 2 + 1}" text-anchor="middle" font-size="2.6" font-family="Arial, sans-serif" fill="#555">{label}</text>'
    return (
        f'<svg class="marks" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}mm" height="{h}mm">'
        f'<g stroke="#000" stroke-width="0.25">{"".join(lines)}</g>{text}</svg>'
    )


def build_html(svg_name, sheet, layout, margin, marks=True):
    """The HTML that a browser prints: one page for each part of the sheet."""
    page_w, page_h = layout["page"]
    area_w, area_h = layout["area"]
    scale = layout["scale"]
    parts = []
    number = 0
    for row in range(layout["rows"]):
        for col in range(layout["cols"]):
            number += 1
            label = f"page {number} of {layout['pages']} · column {col + 1}, row {row + 1}"
            parts.append(
                f'<div class="page"><div class="window">'
                f'<img class="sheet" src="{svg_name}" alt="" style="left:-{col * area_w:.3f}mm;top:-{row * area_h:.3f}mm;'
                f'width:{sheet[0] * scale:.3f}mm;height:{sheet[1] * scale:.3f}mm">'
                f'</div>{_marks((page_w, page_h), margin, label) if marks else ""}</div>'
            )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>pages</title>
<style>
@page {{ size: {page_w}mm {page_h}mm; margin: 0; }}
html, body {{ margin: 0; padding: 0; }}
.page {{ position: relative; width: {page_w}mm; height: {page_h - 0.3}mm; overflow: hidden; break-after: page; }}
.page:last-child {{ break-after: auto; }}
.window {{ position: absolute; left: {margin}mm; top: {margin}mm; width: {area_w}mm; height: {area_h}mm; overflow: hidden; }}
.sheet {{ position: absolute; display: block; max-width: none; }}
.marks {{ position: absolute; left: 0; top: 0; }}
</style></head><body>{"".join(parts)}</body></html>
"""


def find_chrome():
    """A browser that can print to PDF: $CHROME, or Chrome, Chromium, Edge, or a Playwright download."""
    wanted = os.environ.get("CHROME")
    if wanted:
        return wanted
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "microsoft-edge", "msedge"):
        found = shutil.which(name)
        if found:
            return found
    fixed = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    fixed += sorted(glob.glob(os.path.expanduser("~/.cache/ms-playwright/chromium*/*/chrome-headless-shell")))
    fixed += sorted(glob.glob(os.path.expanduser("~/.cache/ms-playwright/chromium*/*/chrome")))
    for path in fixed:
        if os.path.exists(path):
            return path
    raise PagesError("no Chrome, Chromium or Edge found: install one, or set the CHROME environment variable to its path")


def make_pdf(svg_path, pdf_path, paper="A4", margin=5.0, pages=6, scale=None, marks=True, chrome=None):
    """Write the pages of `svg_path` to `pdf_path`. Returns the layout that was used."""
    svg_path, pdf_path = Path(svg_path), Path(pdf_path)
    text = svg_path.read_text(encoding="utf-8")
    sheet = svg_size_mm(text)
    layout = plan(sheet, paper.upper(), margin, pages, scale)
    chrome = chrome or find_chrome()
    with tempfile.TemporaryDirectory() as folder:
        shutil.copyfile(svg_path, Path(folder) / "sheet.svg")
        html = Path(folder) / "pages.html"
        html.write_text(build_html("sheet.svg", sheet, layout, margin, marks), encoding="utf-8")
        out = Path(folder) / "out.pdf"
        command = [chrome, "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                   f"--print-to-pdf={out}", "--virtual-time-budget=20000", html.as_uri()]
        done = subprocess.run(command, capture_output=True, text=True, timeout=180)
        if not out.exists() or out.stat().st_size == 0:
            raise PagesError(f"the browser made no PDF:\n{done.stderr.strip()[-600:]}")
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(out, pdf_path)
    return layout


def main(argv=None):
    parser = argparse.ArgumentParser(description="Cut a big SVG into the pages of one PDF, to print and tape together.")
    parser.add_argument("svg", help="the SVG file, with a size in its width and height (the sheet is 600mm)")
    parser.add_argument("-o", "--output", help="the PDF to write (default: the SVG's name with -pages.pdf)")
    parser.add_argument("--paper", choices=sorted(PAPERS), default="A4", type=str.upper, help="the paper (default A4)")
    parser.add_argument("--pages", type=int, default=6, help="how many pages when the size is chosen to fit (default 6)")
    parser.add_argument("--scale", type=float, help="the size to print at, 1 for real size; then as many pages as it takes")
    parser.add_argument("--margin", type=float, default=5.0, help="the unprinted margin of the printer, in mm (default 5)")
    parser.add_argument("--no-marks", action="store_true", help="no corner marks and page labels")
    args = parser.parse_args(argv)
    output = args.output or str(Path(args.svg).with_suffix("")) + "-pages.pdf"
    try:
        layout = make_pdf(args.svg, output, args.paper, args.margin, args.pages, args.scale, not args.no_marks)
    except (PagesError, OSError, subprocess.SubprocessError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    shape = f"{layout['cols']} across, {layout['rows']} down, {'landscape' if layout['landscape'] else 'portrait'}"
    print(f"{output}: {layout['pages']} pages ({shape}), printed at {layout['scale'] * 100:.1f}% of real size")
    return 0


if __name__ == "__main__":
    sys.exit(main())
