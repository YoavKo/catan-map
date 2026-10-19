#!/usr/bin/env python3
"""Make docs/icons-comparison.svg: the three icon sets side by side, big and at the size they have on a badge.

    python scripts/make_icon_comparison.py            # writes docs/icons-comparison.svg
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from catan_map.icons import ICON_DEFS, ICON_SETS  # noqa: E402

ROWS = (("W", "Wood (logs)"), ("S", "Sheep"), ("G", "Grain (wheat)"), ("C", "Clay (bricks)"), ("O", "Ore (rocks)"))
COLUMNS = (("simple", "Current (simple)"), ("detailed", "A: detailed, flat"), ("realistic", "B: realistic"))
RING = {"W": "#3f7d43", "S": "#9fd36f", "G": "#efc63f", "C": "#b4533a", "O": "#7f8a96"}

CELL_W, CELL_H = 400, 230
LEFT, TOP = 150, 100


def cell(icons, kind, x, y):
    big = f'<g transform="translate({x + 100} {y + CELL_H / 2}) scale(6.2)">{icons[kind]}</g>'
    badge = (
        f'<g transform="translate({x + 300} {y + CELL_H / 2 - 40})">'
        f'<g transform="scale(1.7)"><circle r="35" fill="#f6f0dc" stroke="#2b2b2b" stroke-width="3"/>'
        f'<circle r="31" fill="none" stroke="{RING[kind]}" stroke-width="4"/>'
        f'<g transform="translate(0 -10) scale(1.3)">{icons[kind]}</g>'
        f'<text y="23" text-anchor="middle" font-family="Arial, sans-serif" font-size="18" font-weight="bold" fill="#2b2b2b">2:1</text></g></g>'
        f'<g transform="translate({x + 300} {y + CELL_H / 2 + 75}) scale(1)">'
        f'<circle r="35" fill="#f6f0dc" stroke="#2b2b2b" stroke-width="3" transform="scale(0.5)"/>'
        f'<g transform="translate(0 -5) scale(0.65)">{icons[kind]}</g></g>'
    )
    return big + badge


def main():
    width = LEFT + CELL_W * len(COLUMNS) + 20
    height = TOP + CELL_H * len(ROWS) + 20
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        '<title>Resource icons: the three sets</title>', '<defs>' + ICON_DEFS['realistic'] + '</defs>',
        f'<rect width="{width}" height="{height}" fill="#f7f3e3"/>',
        '<text x="20" y="34" font-family="Arial, sans-serif" font-size="22" font-weight="bold" fill="#2b2b2b">Resource icons: the current set and two new ones</text>',
        '<text x="20" y="56" font-family="Arial, sans-serif" font-size="13" fill="#555">Each cell: the icon large, as a 2:1 port badge (about 10 mm on a card), and at the small size it has in a cost card chip.</text>',
    ]
    for c, (_, title) in enumerate(COLUMNS):
        parts.append(f'<text x="{LEFT + c * CELL_W + CELL_W / 2}" y="{TOP - 8}" text-anchor="middle" font-family="Arial, sans-serif" font-size="17" font-weight="bold" fill="#16325c">{title}</text>')
    for r, (kind, label) in enumerate(ROWS):
        y = TOP + r * CELL_H
        parts.append(f'<text x="20" y="{y + CELL_H / 2 + 5}" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="#2b2b2b">{label}</text>')
        parts.append(f'<line x1="10" y1="{y}" x2="{width - 10}" y2="{y}" stroke="#d8d2bd"/>')
        for c, (name, _) in enumerate(COLUMNS):
            parts.append(cell(ICON_SETS[name], kind, LEFT + c * CELL_W, y))
    parts.append("</svg>\n")
    out = ROOT / "docs" / "icons-comparison.svg"
    out.write_text("".join(parts), encoding="utf-8")
    print(f"{out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
