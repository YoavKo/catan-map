"""The "textures" tile set: each tile is filled with a pattern of lines or shapes, so that the tiles can be told apart
when the sheet is printed in grey: trees for wood, dots for sheep, diagonal stalks for wheat, a brick wall for clay,
piles of rocks (the shape of the ore icon) for ore; the desert is one flat colour, and the piers of the ports are black. No fonts and no external files."""
from __future__ import annotations

from .board import RESOURCE_NAMES
from .icons import SIMPLE
from .tiles_common import HEX_POINTS, TileSet, symbol
from .tiles_plain import SEA as SEA_GROUND   # the sea is the colour of the "plain" set's sea

GROUND = {"W": "#2b6336", "S": "#a9d77a", "G": "#f0cf55", "C": "#cf6b49", "O": "#c4cbd2", "D": "#f1e2b6"}
SCALE = 3.6                # the patterns are drawn this much larger than their drawings below: fewer, bigger lines

_ROCKS = SIMPLE["O"].split("/>", 1)[1]      # the ore icon without its shadow: three rocks with dark outlines

# (width, height, drawing) of one repeat of each pattern; the lines are drawn over the ground colour of the tile.
_PATTERNS = {
    # rows of trees: a dark triangle on a short trunk, the rows shifted by half
    "W": (30, 26,
          '<g fill="#a9de7c" stroke="#0e3319" stroke-width="1.2"><path d="M7,12 L12,2 L17,12Z"/><path d="M7,18 L12,8 L17,18Z"/>'
          '<path d="M22,25 L27,15 L32,25Z"/><path d="M-8,25 L-3,15 L2,25Z"/></g>'
          '<path d="M12,18 v5 M27,25 v1 M-3,25 v1" stroke="#0e3319" stroke-width="1.6"/>'),
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
    # ore: the pile of rocks of the ore icon, in staggered rows
    "O": (40, 36,
          f'<g transform="translate(10,10)">{_ROCKS}</g>'
          + "".join(f'<g transform="translate({x},{y})">{_ROCKS}</g>' for x in (-10, 30) for y in (-8, 28))),   # the second pile wraps round the edges
}


_SCALES = {"O": 2.4}       # the rocks are drawn a little smaller than the other patterns: about three piles across a tile
BLACK_DOCK = {"plank": "#111111", "line": "#111111", "post": "#111111"}


def _pattern(letter):
    width, height, drawing = _PATTERNS[letter]
    return (f'<pattern id="tx-{letter}" width="{width}" height="{height}" patternUnits="userSpaceOnUse" '
            f'patternTransform="scale({_SCALES.get(letter, SCALE)})">{drawing}</pattern>')


def build():
    defs = "".join(_pattern(letter) for letter in "WSGCO")
    symbols = tuple(
        symbol(letter, RESOURCE_NAMES.get(letter, "desert"), GROUND[letter],
               f'<rect x="-100" y="-100" width="200" height="200" fill="url(#tx-{letter})"/>' if letter in _PATTERNS else "")
        for letter in "WSGCOD"
    )
    sea = (
        f'<symbol id="sea" overflow="visible"><polygon points="{HEX_POINTS}" fill="{SEA_GROUND}" stroke="{SEA_GROUND}" stroke-width="1.5"/>'
        f'<title>sea</title></symbol>'
    )
    return TileSet("textures", "a pattern of lines and shapes on each tile, easy to tell apart in grey", symbols, sea, defs, dict(GROUND), dock=BLACK_DOCK)
