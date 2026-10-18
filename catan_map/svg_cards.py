"""The "Building Costs" card, as SVG, in millimetres.

It is drawn upright with its top left corner at (0, 0), CARD_WIDTH by CARD_HEIGHT mm; the board
drawing turns and places four of them in the corners of the mat, one for each side of the table.
Each line reads ``<name> [<points> VP] - <resources>``.
"""
from __future__ import annotations

from .svg_tiles import RING_COLOR, bare_icon, get_tile_set, resource_icon

CARD_WIDTH = 120
CARD_HEIGHT = 72

PAPER = "#efe2b6"
INK = "#2b2118"
BROWN = "#7a5632"
SERIF = "Georgia, 'Times New Roman', serif"

ICON = 11
GAP = 1.4
LEFT = 7
RIGHT = CARD_WIDTH - 7
TITLE_HEIGHT = 16
ROW_HEIGHT = 13.5

# (name, victory points, the cost: W wood, C clay, S sheep, G grain, O ore)
COSTS = (
    ("Road", "0", "CW"),
    ("Settlement", "1", "CWGS"),
    ("City", "2", "GGOOO"),
    ("Development Card", "?", "SGO"),
)


def _icons(cost, top, tiles):
    width = len(cost) * ICON + (len(cost) - 1) * GAP
    return "".join(
        resource_icon(kind, RIGHT - width + i * (ICON + GAP), top, ICON, tiles) for i, kind in enumerate(cost)
    )


def building_costs_card(tiles=None):
    """The card as an SVG group (text), CARD_WIDTH x CARD_HEIGHT mm."""
    parts = [
        f'<rect width="{CARD_WIDTH}" height="{CARD_HEIGHT}" rx="2.8" fill="{PAPER}" stroke="{BROWN}" stroke-width="1"/>',
        f'<rect x="2.3" y="2.3" width="{CARD_WIDTH - 4.6}" height="{CARD_HEIGHT - 4.6}" rx="1.8" fill="none" stroke="{BROWN}" stroke-width="0.45"/>',
        f'<text x="{CARD_WIDTH / 2}" y="12" font-family="{SERIF}" font-size="6.6" font-weight="bold" '
        f'text-anchor="middle" fill="{INK}">BUILDING COSTS</text>',
    ]
    for i, (name, points, cost) in enumerate(COSTS):
        top = TITLE_HEIGHT + i * ROW_HEIGHT
        parts.append(f'<line x1="5" y1="{top}" x2="{CARD_WIDTH - 5}" y2="{top}" stroke="{BROWN}" stroke-width="0.6"/>')
        size = 5.6 if name != "Development Card" else 5.2
        parts.append(
            f'<text x="{LEFT}" y="{top + 8.7:g}" font-family="{SERIF}" font-size="{size}" fill="{INK}">'
            f'<tspan font-weight="bold">{name}</tspan>'
            f'<tspan font-size="{size * 0.78:.2f}"> [{points} VP]</tspan>'
            f'<tspan> -</tspan></text>'
        )
        parts.append(_icons(cost, top + (ROW_HEIGHT - ICON) / 2, tiles))
    return f'<g class="costs">{"".join(parts)}</g>'


# ------------------------------------------------------------------------------------ the bank

# the strip along the bottom edge of the mat, between the two bottom cards: x, y, width, height (mm).
# The island is moved up to make room for it, so that the slots are the size of a playing card.
BANK_BOX = (84, 504, 387, 93)
BANK_RESOURCES = ("C", "W", "S", "G", "O")        # brick, wood, sheep, grain, ore
SLOT_W, SLOT_H = 57, 89        # mm: the size of a card of the bridge size (57 x 89); poker size (63.5 x 88.9) would not fit in a row
DEV_BLUE = "#27407a"


def bank_group(tiles=None):
    """Places for the bank: a slot for each resource and one for the development cards, in a
    strip along the bottom of the mat. A slot is only an outline, in the colour of the resource,
    with the resource's icon, no box around it, in the middle; the cards go on top of it."""
    tile_set = get_tile_set(tiles)
    x0, y0, width, height = BANK_BOX
    pad = 8
    gap = (width - 2 * pad - 6 * SLOT_W) / 5
    top = y0 + (height - SLOT_H) / 2
    icon = 36
    parts = [
        f'<rect x="{x0}" y="{y0}" width="{width}" height="{height}" rx="3" fill="#dde6cc" stroke="{BROWN}" stroke-width="0.5"/>'
    ]
    for i, kind in enumerate(BANK_RESOURCES):
        x = x0 + pad + i * (SLOT_W + gap)
        ring = RING_COLOR.get(kind, tile_set.ground[kind])
        parts.append(
            f'<g class="slot" data-kind="{kind}">'
            f'<rect x="{x:.2f}" y="{top:.2f}" width="{SLOT_W}" height="{SLOT_H}" rx="3.5" fill="none" stroke="{ring}" stroke-width="1.8"/>'
            f'{bare_icon(kind, round(x + SLOT_W / 2, 2), round(top + SLOT_H / 2, 2), icon)}'
            f'</g>'
        )
    x = x0 + pad + 5 * (SLOT_W + gap)
    cx, cy = x + SLOT_W / 2, top + SLOT_H / 2
    deck = "".join(                      # three card backs, one behind the other
        f'<rect x="{cx - 14 + d:.2f}" y="{cy - 19 - d * 0.7:.2f}" width="28" height="38" rx="2.6" fill="{DEV_BLUE}" '
        f'stroke="#f3ecd2" stroke-width="1"/>'
        for d in (6, 3, 0)
    )
    parts.append(
        f'<g class="slot" data-kind="dev">'
        f'<rect x="{x:.2f}" y="{top:.2f}" width="{SLOT_W}" height="{SLOT_H}" rx="3.5" fill="none" stroke="{DEV_BLUE}" stroke-width="1.8"/>'
        f'{deck}</g>'
    )
    return f'<g class="bank">{"".join(parts)}</g>'
