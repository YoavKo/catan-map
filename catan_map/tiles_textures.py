"""The "textures" tile set: each tile is filled with a pattern of lines or shapes, so that the tiles can be told apart
when the sheet is printed in grey: trees for wood, dots for sheep, diagonal stalks for wheat, a brick wall for clay,
round stones for ore, dune lines for the desert. No fonts and no external files."""
from __future__ import annotations

from .board import RESOURCE_NAMES
from .tiles_common import HEX_POINTS, TileSet, symbol

GROUND = {"W": "#3c7a45", "S": "#a9d77a", "G": "#f0cf55", "C": "#cf6b49", "O": "#9aa4ae", "D": "#f1e2b6"}
SEA_GROUND, SEA_LINE = "#bfe0f5", "#4f98cf"

# (width, height, drawing) of one repeat of each pattern; the lines are drawn over the ground colour of the tile.
_PATTERNS = {
    # rows of trees: a dark triangle on a short trunk, the rows shifted by half
    "W": (30, 26,
          '<g fill="#1d4a28" stroke="#13341c" stroke-width="1"><path d="M7,12 L12,2 L17,12Z"/><path d="M7,18 L12,8 L17,18Z"/>'
          '<path d="M22,25 L27,15 L32,25Z"/><path d="M-8,25 L-3,15 L2,25Z"/></g>'
          '<path d="M12,18 v5 M27,25 v1 M-3,25 v1" stroke="#13341c" stroke-width="1.6"/>'),
    # white sheep: round bodies with a dark head, scattered in staggered rows
    "S": (34, 30,
          '<g stroke="#4a4a4a" stroke-width="1"><ellipse cx="9" cy="8" rx="6" ry="4.5" fill="#ffffff"/><circle cx="15" cy="7" r="2" fill="#4a4a4a"/>'
          '<ellipse cx="26" cy="23" rx="6" ry="4.5" fill="#ffffff"/><circle cx="32" cy="22" r="2" fill="#4a4a4a"/></g>'
          '<path d="M3,24 l2,-4 l2,4 M18,16 l2,-4 l2,4" stroke="#4d8a2d" stroke-width="1.4" fill="none"/>'),
    # wheat: diagonal stalks, lines at 45 degrees
    "G": (10, 10,
          '<path d="M-2,12 L12,-2 M-2,2 L2,-2 M8,12 L12,8" stroke="#a87a10" stroke-width="2.4" fill="none"/>'),
    # a brick wall: courses with the joints shifted by half a brick
    "C": (40, 20,
          '<path d="M0,0 H40 M0,10 H40 M0,20 H40 M0,0 V10 M20,10 V20" stroke="#f6e3d3" stroke-width="2.6" fill="none"/>'),
    # round stones: circles of different sizes, some with a smaller circle inside
    "O": (44, 40,
          '<g fill="#c6cdd4" stroke="#33404c" stroke-width="2"><circle cx="11" cy="11" r="8"/><circle cx="33" cy="17" r="6"/>'
          '<circle cx="19" cy="31" r="7"/><circle cx="40" cy="36" r="4"/><circle cx="3" cy="35" r="4"/></g>'
          '<g fill="none" stroke="#33404c" stroke-width="1.4"><circle cx="11" cy="11" r="3.2"/><circle cx="19" cy="31" r="2.8"/></g>'),
    # dunes: long flat waves
    "D": (60, 18,
          '<path d="M0,9 q15,-8 30,0 t30,0" stroke="#c9a864" stroke-width="1.8" fill="none"/>'),
}


def _pattern(letter):
    width, height, drawing = _PATTERNS[letter]
    return f'<pattern id="tx-{letter}" width="{width}" height="{height}" patternUnits="userSpaceOnUse">{drawing}</pattern>'


def build():
    defs = "".join(_pattern(letter) for letter in "WSGCOD") + (
        f'<pattern id="tx-sea" width="30" height="24" patternUnits="userSpaceOnUse">'
        f'<path d="M3,8 q6,-7 12,0 t12,0 M-3,20 q6,-7 12,0 t12,0 M15,20 q6,-7 12,0" stroke="{SEA_LINE}" stroke-width="2.2" fill="none" stroke-linecap="round"/></pattern>'
    )
    symbols = tuple(
        symbol(letter, RESOURCE_NAMES.get(letter, "desert"), GROUND[letter],
               f'<rect x="-100" y="-100" width="200" height="200" fill="url(#tx-{letter})"/>')
        for letter in "WSGCOD"
    )
    sea = (
        f'<symbol id="sea" overflow="visible"><polygon points="{HEX_POINTS}" fill="{SEA_GROUND}" stroke="{SEA_GROUND}" stroke-width="1.5"/>'
        f'<polygon points="{HEX_POINTS}" fill="url(#tx-sea)"/><title>sea</title></symbol>'
    )
    return TileSet("textures", "a pattern of lines and shapes on each tile, easy to tell apart in grey", symbols, sea, defs, dict(GROUND))
