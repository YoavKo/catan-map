"""Drawing a board in the console.

The island with its tokens, and the sea ring around it. A port shows ``3`` (3:1) or the
resource letter (2:1), with an arrow, on the side of the port that faces the island tile it
attaches to; ``~`` is plain water.
"""
from __future__ import annotations

from .board import (
    RING_POSITIONS,
    RING_SIZE,
    THREE_TO_ONE,
    TILE_COUNT,
    TILE_POSITIONS,
    direction,
    port_ring_position,
    port_target_tile,
)

UNICODE_ARROWS = {"E": "→", "W": "←", "NE": "↗", "NW": "↖", "SE": "↘", "SW": "↙"}
ASCII_ARROWS = {"E": ">", "W": "<", "NE": "/", "NW": "\\", "SE": "\\", "SW": "/"}

# ANSI colour of each kind of cell.
COLORS = {
    "W": "32",           # wood: green
    "O": "90",           # ore: grey
    "C": "31",           # clay: red
    "S": "92",           # sheep: light green
    "G": "33",           # grain: yellow
    "D": "38;5;180",     # desert: tan
    "3": "1",            # a 3:1 port: bold
    "~": "34",           # water: blue
}

_COLUMN_OF_X = 3   # a step of 1 in x is 3 characters; a cell is 2 characters wide
_LEFT = 18


def _column(x):
    return _COLUMN_OF_X * x + _LEFT


def _paint(text, key, color):
    if not color:
        return text
    return f"\x1b[{COLORS[key]}m{text}\x1b[0m"


def _port_cells(board, arrows):
    """[(ring position, text, colour key)] for the nine ports."""
    ports = board.effective_ports()
    cells = []
    for slot, port in enumerate(ports.entries):
        position = port_ring_position(slot, ports.shifted)
        tile = port_target_tile(slot, ports.shifted, port.forward)
        way = direction(position, tile)
        label = "3" if port.kind == THREE_TO_ONE else port.kind
        arrow = arrows[way]
        # the arrow goes on the side that faces the tile
        text = (arrow + label) if way in ("W", "NW", "SW") else (label + arrow)
        cells.append((position, text, "3" if port.kind == THREE_TO_ONE else port.kind))
    return cells


def render_board(board, ascii_only=False, color=False):
    """The drawing, as text (no trailing newline)."""
    arrows = ASCII_ARROWS if ascii_only else UNICODE_ARROWS
    rows = {}   # row -> [(column, text, colour key)]

    for tile in range(TILE_COUNT):
        row, x = TILE_POSITIONS[tile]
        token = board.tokens[tile] or " "
        rows.setdefault(row, []).append((_column(x), board.tiles[tile] + token, board.tiles[tile]))

    port_cells = _port_cells(board, arrows)
    by_position = {position: (text, key) for position, text, key in port_cells}
    for position in range(RING_SIZE):
        row, x = RING_POSITIONS[position]
        text, key = by_position.get(position, ("~ ", "~"))
        rows.setdefault(row, []).append((_column(x), text, key))

    lines = []
    for row in sorted(rows):
        line, used = "", 0
        for column, text, key in sorted(rows[row]):
            # only the visible characters are coloured; the padding of a cell stays plain spaces,
            # so that a coloured line has no trailing spaces after the codes are removed
            visible = text.rstrip()
            line += " " * (column - used) + _paint(visible, key, color) + " " * (len(text) - len(visible))
            used = column + len(text)
        lines.append(line.rstrip())

    return "\n".join(lines)
