"""What every tile set shares: the hexagon, its border, and the shape of a tile set.

Every tile is a pointy-top hexagon of radius 100 centred on (0, 0), so it is 173.2 wide and
200 high. A *tile set* is a look for the whole board: the six land tiles, the sea tile, and
how the number tokens are painted. The board drawing and the ports are the same for every set.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

RADIUS = 100
HALF_WIDTH = 86.603   # RADIUS * sqrt(3) / 2

HEX_POINTS = f"0,-{RADIUS} {HALF_WIDTH},-50 {HALF_WIDTH},50 0,{RADIUS} -{HALF_WIDTH},50 -{HALF_WIDTH},-50"

OUTLINE = "#2b2b2b"
BORDER = "#f3ecd2"     # the off-white edge of a land tile, the space where roads are drawn
BORDER_WIDTH = 9


@dataclass(frozen=True)
class TileSet:
    name: str
    description: str
    symbols: Tuple[str, ...]     # the six land tiles, as <symbol id="tile-W"> ... (W S G C O D)
    sea: str                     # the sea tile, <symbol id="sea">
    defs: str                    # gradients and filters the symbols use ("" if none)
    ground: Dict[str, str]       # the main colour of each tile, W S G C O D (the ring of a port badge)
    token_fill: str = "#f6f0dc"  # the face of a number token
    shadows: bool = False        # whether tokens and port badges cast a small shadow


def symbol(letter, name, ground_fill, art="", overlay="", defs=""):
    """A land tile: the ground, the art clipped to the hexagon, an overlay, the border."""
    return (
        f'<symbol id="tile-{letter}" overflow="visible">{defs}'
        f'<clipPath id="clip-{letter}"><polygon points="{HEX_POINTS}"/></clipPath>'
        f'<polygon points="{HEX_POINTS}" fill="{ground_fill}"/>'
        f'<g clip-path="url(#clip-{letter})">{art}{overlay}</g>'
        f'<polygon points="{HEX_POINTS}" fill="none" stroke="{OUTLINE}" stroke-width="{BORDER_WIDTH + 3}" stroke-linejoin="round"/>'
        f'<polygon points="{HEX_POINTS}" fill="none" stroke="{BORDER}" stroke-width="{BORDER_WIDTH}" stroke-linejoin="round"/>'
        f'<title>{name}</title>'
        f'</symbol>'
    )
