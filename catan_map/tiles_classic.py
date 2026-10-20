"""The "classic" tile set: the six land tiles are pictures (assets/classic/*.webp, one per tile letter), each with
its own cream border, so nothing is drawn around them. The sea, the tokens and the ports are those of the vector set."""
from __future__ import annotations

import base64
from pathlib import Path

from . import tiles_vector
from .tiles_common import HALF_WIDTH, RADIUS, TileSet

ASSETS = Path(__file__).resolve().parent / "assets" / "classic"


def picture_uri(letter):
    """The picture of the tile `letter` as a data: URI."""
    return "data:image/webp;base64," + base64.b64encode((ASSETS / f"{letter}.webp").read_bytes()).decode("ascii")


def _symbol(letter):
    return (
        f'<symbol id="tile-{letter}" overflow="visible">'
        f'<image x="{-HALF_WIDTH}" y="{-RADIUS}" width="{2 * HALF_WIDTH}" height="{2 * RADIUS}" '
        f'preserveAspectRatio="none" href="{picture_uri(letter)}"/></symbol>'
    )


def build():
    base = tiles_vector.build()
    return TileSet(
        "classic", "pictures of the tiles, each with its own border", tuple(_symbol(letter) for letter in "WSGCOD"),
        base.sea, base.defs, base.ground, token_fill=base.token_fill, shadows=base.shadows, own_edges=True,
    )
