"""The standard Catan island: its tiles, the zones they fall into, the ring of sea
tiles around it, and the ports.

Tiles are numbered 0-18 in scan order (left to right, top to bottom)::

    row 0:        0  1  2
    row 1:      3  4  5  6
    row 2:    7  8  9 10 11
    row 3:     12 13 14 15
    row 4:       16 17 18

The sea ring has 18 tiles numbered 0-17 clockwise from the top-left corner. Everything
here is plain data and small functions, so that a larger island can be added later by
changing the data.
"""
from __future__ import annotations

ROWS = (3, 4, 5, 4, 3)
TILE_COUNT = sum(ROWS)

# ---------------------------------------------------------------- tiles and tokens

RESOURCES = "WOCSG"
DESERT = "D"
TILE_LETTERS = RESOURCES + DESERT
RESOURCE_NAMES = {"W": "wood", "O": "ore", "C": "clay", "S": "sheep", "G": "grain"}
TILE_COUNTS = {"W": 4, "O": 3, "C": 3, "S": 4, "G": 4, "D": 1}

# Tokens: 2 3 4 5 6 8 9 and a = 10, b = 11, c = 12 (there is no 7).
TOKEN_CHARS = "2345689abc"
TOKEN_VALUES = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "8": 8, "9": 9, "a": 10, "b": 11, "c": 12}
TOKEN_COUNTS = {"2": 1, "3": 2, "4": 2, "5": 2, "6": 2, "8": 2, "9": 2, "a": 2, "b": 2, "c": 1}
RED_TOKENS = ("6", "8")

# Position of every tile as (row, x). x is a doubled horizontal coordinate that centres
# each row: two tiles touch when they are in the same row with |dx| = 2, or in adjacent
# rows with |dx| = 1.
TILE_POSITIONS = tuple(
    (row, 2 * col - (length - 1)) for row, length in enumerate(ROWS) for col in range(length)
)
# (row, column), both counted from 0, for every tile.
TILE_ROW_COL = tuple((row, col) for row, length in enumerate(ROWS) for col in range(length))


def _touch(a, b):
    (row_a, x_a), (row_b, x_b) = a, b
    return (row_a == row_b and abs(x_a - x_b) == 2) or (abs(row_a - row_b) == 1 and abs(x_a - x_b) == 1)


NEIGHBOURS = tuple(
    tuple(j for j, other in enumerate(TILE_POSITIONS) if j != i and _touch(position, other))
    for i, position in enumerate(TILE_POSITIONS)
)

# ---------------------------------------------------------------------- the sea ring

RING_SIZE = 18

# Where each sea tile is, as (row, x); the top sea row is row -1 and the bottom one row 5.
RING_POSITIONS = (
    (-1, -3), (-1, -1), (-1, 1), (-1, 3),                  # 0-3    top, left to right
    (0, 4), (1, 5), (2, 6), (3, 5), (4, 4),                # 4-8    right side, top to bottom
    (5, 3), (5, 1), (5, -1), (5, -3),                      # 9-12   bottom, right to left
    (4, -4), (3, -5), (2, -6), (1, -5), (0, -4),           # 13-17  left side, bottom to top
)

# The island tiles each sea tile touches, in clockwise order. A port on a sea tile that
# touches two island tiles attaches to the first one when it is "backward" and to the
# second one when it is "forward"; a sea tile that touches one tile (a corner) has no choice.
RING_TOUCHES = (
    (0,), (0, 1), (1, 2), (2,),
    (2, 6), (6, 11), (11,), (11, 15), (15, 18),
    (18,), (18, 17), (17, 16), (16,),
    (16, 12), (12, 7), (7,), (7, 3), (3, 0),
)

CORNER_POSITIONS = tuple(p for p in range(RING_SIZE) if len(RING_TOUCHES[p]) == 1)

# ------------------------------------------------------------------------------ zones

EDGE_TILES = frozenset(tile for touches in RING_TOUCHES for tile in touches)
INNER_TILES = frozenset(range(TILE_COUNT)) - EDGE_TILES
CENTER_TILE = TILE_POSITIONS.index((2, 0))
CENTER_TILES = frozenset({CENTER_TILE})
RING_TILES = INNER_TILES - CENTER_TILES

# Where the desert may be (the --desert option); "free" means anywhere.
DESERT_ZONES = {
    "free": frozenset(range(TILE_COUNT)),
    "edge": EDGE_TILES,
    "inner": INNER_TILES,
    "center": CENTER_TILES,
    "ring": RING_TILES,
}

# -------------------------------------------------------------------------------- ports

PORT_COUNT = 9
THREE_TO_ONE = "3"
# The nine ports: four 3:1 and one 2:1 for each resource.
PORT_KIND_COUNTS = {"3": 4, "W": 1, "O": 1, "C": 1, "S": 1, "G": 1}
# Port symbols in a string: an uppercase resource letter is a 2:1 port attached "forward",
# a lowercase one "backward"; "3" is a 3:1 port backward and "#" a 3:1 port forward.
PORT_SYMBOLS = "WOCSGwocsg3#"
DEFAULT_PORTS = "3gO3s#3cW"


def port_ring_position(slot, shifted):
    """The sea tile that port number `slot` (0-8) sits on: every second tile, starting at
    ring tile 0, or at ring tile 1 when the ring is shifted by one."""
    return 2 * slot + (1 if shifted else 0)


def is_corner_slot(slot, shifted):
    return port_ring_position(slot, shifted) in CORNER_POSITIONS


def port_target_tile(slot, shifted, forward):
    """The island tile a port attaches to."""
    touches = RING_TOUCHES[port_ring_position(slot, shifted)]
    return touches[1] if (len(touches) == 2 and forward) else touches[0]


def direction(ring_position, tile):
    """Which way, from a sea tile, an island tile lies: E, W, NE, NW, SE or SW."""
    row, x = RING_POSITIONS[ring_position]
    tile_row, tile_x = TILE_POSITIONS[tile]
    return {(0, 2): "E", (0, -2): "W", (-1, 1): "NE", (-1, -1): "NW", (1, 1): "SE", (1, -1): "SW"}[
        (tile_row - row, tile_x - x)
    ]


# --------------------------------------------------------------------------- red numbers


def adjacent_red_pairs(tokens):
    """Pairs of neighbouring tiles that both carry a 6 or an 8. `tokens` has one entry per
    tile (the token, or None for the desert)."""
    pairs = []
    for i, token in enumerate(tokens):
        if token in RED_TOKENS:
            for j in NEIGHBOURS[i]:
                if j > i and tokens[j] in RED_TOKENS:
                    pairs.append((i, j))
    return pairs


def describe_tile(tile):
    """A tile's place in words, for messages: row 2, column 3 (counted from 1)."""
    row, col = TILE_ROW_COL[tile]
    return f"row {row + 1}, column {col + 1}"
