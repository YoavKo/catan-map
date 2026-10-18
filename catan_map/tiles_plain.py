"""The "plain" tile set: one flat colour per tile, nothing drawn on it."""
from __future__ import annotations

from .board import RESOURCE_NAMES
from .tiles_common import HEX_POINTS, TileSet, symbol

GROUND = {"W": "#2f7a3a", "S": "#9bd05a", "G": "#f0c93a", "C": "#c8553a", "O": "#8a949e", "D": "#e6d19a"}
SEA = "#3b8fd0"


def build():
    symbols = tuple(symbol(letter, RESOURCE_NAMES.get(letter, "desert"), GROUND[letter]) for letter in "WSGCOD")
    sea = (
        f'<symbol id="sea" overflow="visible"><polygon points="{HEX_POINTS}" fill="{SEA}" stroke="#2b76b5" '
        f'stroke-width="3" stroke-linejoin="round"/><title>sea</title></symbol>'
    )
    return TileSet("plain", "one flat colour per tile", symbols, sea, "", dict(GROUND))
