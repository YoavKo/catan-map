"""Drawing a board as an SVG image.

Hexagons are pointy-top with radius 100, so a step of 1 in the board's x coordinate is half a
hexagon wide, and a row is 1.5 radii lower than the one above. The island, the ring of sea
around it and the ports use the same positions as the console drawing. The output is plain
text and always the same for the same board.
"""
from __future__ import annotations

from xml.sax.saxutils import escape

from .board import (
    RING_POSITIONS,
    RING_SIZE,
    TILE_COUNT,
    RED_TOKENS,
    TILE_POSITIONS,
    TOKEN_VALUES,
    direction,
    port_ring_position,
    port_target_tile,
)
from .svg_tiles import get_tile_set, port_group, tile_defs
from .tiles_common import HALF_WIDTH, OUTLINE, RADIUS

ROW_STEP = RADIUS * 1.5
MARGIN = 24
CAPTION_LINE = 34
BACKGROUND = "#f7f3e3"
TOKEN_RADIUS = 31


def _center(row, x):
    return x * HALF_WIDTH, row * ROW_STEP


def _num(value):
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _token(symbol, x, y, tile_set):
    value = TOKEN_VALUES[symbol]
    red = symbol in RED_TOKENS
    ink = "#c0261d" if red else "#2b2b2b"
    pips = 6 - abs(7 - value)
    pip_x = [(i - (pips - 1) / 2) * 7 for i in range(pips)]
    dots = "".join(f'<circle cx="{_num(dx)}" cy="19" r="2.2" fill="{ink}"/>' for dx in pip_x)
    return (
        f'<g transform="translate({_num(x)} {_num(y)})">'
        + (f'<circle cx="2.5" cy="3.5" r="{TOKEN_RADIUS}" fill="#000000" opacity="0.32"/>' if tile_set.shadows else "")
        + f'<circle r="{TOKEN_RADIUS}" fill="{tile_set.token_fill}" stroke="{OUTLINE}" stroke-width="2.5"/>'
        f'<text y="6" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="{26 if value < 10 else 23}" '
        f'font-weight="bold" fill="{ink}">{value}</text>'
        f'{dots}</g>'
    )


def render_svg(board, caption=(), tiles=None):
    """The board as an SVG document (text). `caption` is lines of text written under it;
    `tiles` is the name of the tile set ("basic", "realistic" or "plain"; the default if None)."""
    tile_set = get_tile_set(tiles)
    ports = board.effective_ports()
    port_at = {}
    for slot, port in enumerate(ports.entries):
        position = port_ring_position(slot, ports.shifted)
        way = direction(position, port_target_tile(slot, ports.shifted, port.forward))
        port_at[position] = (port.kind, way)

    sea = []
    for position in range(RING_SIZE):
        x, y = _center(*RING_POSITIONS[position])
        if position in port_at:
            kind, way = port_at[position]
            sea.append(port_group(kind, way, _num(x), _num(y), tile_set.name))
        else:
            sea.append(f'<use href="#sea" x="{_num(x)}" y="{_num(y)}"/>')

    land, tokens = [], []
    for tile in range(TILE_COUNT):
        x, y = _center(*TILE_POSITIONS[tile])
        land.append(f'<use href="#tile-{board.tiles[tile]}" x="{_num(x)}" y="{_num(y)}"/>')
        if board.tokens[tile] is not None:
            tokens.append(_token(board.tokens[tile], x, y, tile_set))

    left = -(6 * HALF_WIDTH + HALF_WIDTH) - MARGIN
    top = -(ROW_STEP + RADIUS) - MARGIN
    width = 2 * (7 * HALF_WIDTH + MARGIN)
    board_height = (5 * ROW_STEP + RADIUS) - top + MARGIN   # bottom of row 5 plus margin
    height = board_height + (len(caption) * CAPTION_LINE + MARGIN if caption else 0)

    captions = "".join(
        f'<text x="{_num(left + width / 2)}" y="{_num(top + board_height + CAPTION_LINE * (i + 0.6))}" '
        f'text-anchor="middle" font-family="Consolas, Menlo, monospace" font-size="{24 if i == 0 else 18}" '
        f'fill="#2b2b2b">{escape(line)}</text>'
        for i, line in enumerate(caption)
    )
    description = " | ".join(caption) if caption else "A Settlers of Catan board"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{_num(left)} {_num(top)} {_num(width)} {_num(height)}" '
        f'width="{_num(width / 2)}" height="{_num(height / 2)}">'
        f'<title>Catan board</title><desc>{escape(description)}</desc>'
        f'{tile_defs(tile_set.name)}'
        f'<rect x="{_num(left)}" y="{_num(top)}" width="{_num(width)}" height="{_num(height)}" fill="{BACKGROUND}"/>'
        f'<g id="water">{"".join(sea)}</g>'
        f'<g id="land">{"".join(land)}</g>'
        f'<g id="tokens">{"".join(tokens)}</g>'
        f'{captions}</svg>\n'
    )
