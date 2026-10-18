"""The tile sets, the ports, and a preview of them.

A tile set (see tiles_common.TileSet) is chosen by name: "basic" (flat colours and simple
shapes), "realistic" (painted-looking) or "plain" (one flat colour per tile). `tile_defs()`
returns the ``<defs>`` block of a set: one ``<symbol>`` per land tile (``tile-W`` ... ``tile-D``),
the sea (``sea``) and the pier (``dock``), which a board drawing places with ``<use>``.
"""
from __future__ import annotations

from . import tiles_basic, tiles_plain, tiles_realistic
from .codec import CatanMapError
from .tiles_common import BORDER, BORDER_WIDTH, HALF_WIDTH, HEX_POINTS, OUTLINE, RADIUS, TileSet, edge_symbols

__all__ = ["DEFAULT_TILE_SET", "TILE_SET_NAMES", "get_tile_set", "tile_defs", "port_group", "preview_svg", "resource_icon", "bare_icon"]

_BUILDERS = {"basic": tiles_basic.build, "realistic": tiles_realistic.build, "plain": tiles_plain.build}
TILE_SET_NAMES = tuple(_BUILDERS)
DEFAULT_TILE_SET = "realistic"
_cache = {}

# the ring of a clay chip or badge is brick red, whatever the colour of the clay tile
RING_COLOR = {"C": "#b4533a"}
DOCK = {"plank": "#b98a58", "line": "#7a5632", "post": "#5e4026"}


def get_tile_set(name=None):
    """The TileSet called `name` (the default one for None). Built once, then kept."""
    name = DEFAULT_TILE_SET if name is None else name
    if name not in _BUILDERS:
        raise CatanMapError(f"unknown tile set {name!r}; the tile sets are {', '.join(TILE_SET_NAMES)}")
    if name not in _cache:
        _cache[name] = _BUILDERS[name]()
    return _cache[name]


# where each way lies from a sea tile, as a rotation in degrees (SVG turns clockwise)
WAY_ANGLES = {"E": 0, "SE": 60, "SW": 120, "W": 180, "NW": 240, "NE": 300}


def _sea_symbol():
    waves = "".join(
        f'<path d="M{x},{y} q6,-7 12,0 t12,0" stroke="{SEA["wave"]}" stroke-width="3" fill="none" stroke-linecap="round"/>'
        for x, y in ((-60, -42), (22, -58), (-26, 62), (46, 38), (-68, 18))
    )
    return (
        f'<symbol id="sea" overflow="visible">'
        f'<clipPath id="clip-sea"><polygon points="{HEX_POINTS}"/></clipPath>'
        f'<polygon points="{HEX_POINTS}" fill="{SEA["ground"]}"/>'
        f'<g clip-path="url(#clip-sea)">{waves}</g>'
        f'<polygon points="{HEX_POINTS}" fill="none" stroke="{SEA["deep"]}" stroke-width="3" stroke-linejoin="round"/>'
        f'<title>sea</title></symbol>'
    )


def _dock_symbol():
    """Two piers from the middle of the tile to the two corners of its east edge."""
    corners = ((HALF_WIDTH, -50), (HALF_WIDTH, 50))
    piers = "".join(
        f'<line x1="0" y1="0" x2="{x}" y2="{y}" stroke="{DOCK["line"]}" stroke-width="14" stroke-linecap="butt"/>'
        f'<line x1="0" y1="0" x2="{x}" y2="{y}" stroke="{DOCK["plank"]}" stroke-width="9" stroke-linecap="butt"/>'
        for x, y in corners
    )
    posts = "".join(f'<circle cx="{x}" cy="{y}" r="6" fill="{DOCK["post"]}"/>' for x, y in corners)
    return f'<symbol id="dock" overflow="visible">{piers}{posts}</symbol>'


# small icons for the badge of a 2:1 port, drawn around (0, 0) in a box about 20 wide
_PORT_ICONS = {
    "W": (
        '<rect x="-2" y="6" width="4" height="5" fill="#6b4a2b"/>'
        '<polygon points="0,-11 8,0 -8,0" fill="#245c2b"/><polygon points="0,-5 10,7 -10,7" fill="#3f7d43"/>'
    ),
    "S": (
        '<rect x="-7" y="4" width="3" height="7" fill="#3d3a37"/><rect x="3" y="4" width="3" height="7" fill="#3d3a37"/>'
        '<circle cx="-5" cy="0" r="6" fill="#ffffff" stroke="#9aa08f" stroke-width="1.2"/>'
        '<circle cx="1" cy="-3" r="7" fill="#ffffff" stroke="#9aa08f" stroke-width="1.2"/>'
        '<circle cx="6" cy="1" r="6" fill="#ffffff" stroke="#9aa08f" stroke-width="1.2"/>'
        '<ellipse cx="9" cy="-4" rx="3" ry="4" fill="#3d3a37"/>'
    ),
    "G": (
        '<path d="M0,12 L0,-8" stroke="#b07e14" stroke-width="2"/>'
        + "".join(
            f'<ellipse cx="{side * 4.5}" cy="{y}" rx="2.6" ry="5" fill="#d9a521" transform="rotate({side * 30} {side * 4.5} {y})"/>'
            for y in (-3, 3) for side in (-1, 1)
        )
        + '<ellipse cx="0" cy="-9" rx="2.6" ry="5.5" fill="#d9a521"/>'
    ),
    "C": (
        '<rect x="-11" y="-8" width="22" height="8" rx="1.5" fill="#cf7455" stroke="#7d3a26" stroke-width="1.2"/>'
        '<rect x="-11" y="1" width="10" height="8" rx="1.5" fill="#cf7455" stroke="#7d3a26" stroke-width="1.2"/>'
        '<rect x="0" y="1" width="11" height="8" rx="1.5" fill="#cf7455" stroke="#7d3a26" stroke-width="1.2"/>'
    ),
    "O": (
        # a small pile of grey rocks, lit from the top left
        '<ellipse cx="0" cy="10" rx="13" ry="2.5" fill="#000000" opacity="0.25"/>'
        '<polygon points="-12,10 -13,3 -8,-2 -1,-1 2,5 1,10" fill="#7f8a96" stroke="#454d56" stroke-width="1"/>'
        '<polygon points="-8,-2 -1,-1 -5,3" fill="#b7c0c9"/>'
        '<polygon points="-1,-1 2,5 1,10 -5,3" fill="#5f6a75" opacity="0.8"/>'
        '<polygon points="0,10 1,2 6,-6 12,-3 13,5 10,10" fill="#98a3ae" stroke="#454d56" stroke-width="1"/>'
        '<polygon points="1,2 6,-6 9,-4 5,1" fill="#c8d0d8"/>'
        '<polygon points="9,-4 12,-3 13,5 10,10 7,2" fill="#626c77" opacity="0.8"/>'
        '<polygon points="-5,-1 -4,-8 2,-11 7,-8 6,-2 1,1" fill="#aab4be" stroke="#454d56" stroke-width="1"/>'
        '<polygon points="-4,-8 2,-11 3,-7 -2,-4" fill="#d3dae1"/>'
        '<polygon points="3,-7 7,-8 6,-2 1,1 2,-4" fill="#6a7580" opacity="0.8"/>'
    ),
}


def bare_icon(kind, cx, cy, size):
    """The resource's icon alone, with no chip around it, centred on (cx, cy), about `size` wide."""
    return f'<g transform="translate({cx:g} {cy:g}) scale({size / 26:.4f})">{_PORT_ICONS[kind]}</g>'


def resource_icon(kind, x, y, size, tiles=None):
    """A square cream chip with a ring in the resource's colour and the resource's icon
    (the same icon as on its port), top left corner at (x, y), `size` wide."""
    tile_set = get_tile_set(tiles)
    inset = size * 0.09
    return (
        f'<g transform="translate({x:g} {y:g})">'
        f'<rect width="{size:g}" height="{size:g}" rx="{size * 0.16:.2f}" fill="#f6f0dc" stroke="{OUTLINE}" stroke-width="{size * 0.05:.2f}"/>'
        f'<rect x="{inset:.2f}" y="{inset:.2f}" width="{size - 2 * inset:.2f}" height="{size - 2 * inset:.2f}" rx="{size * 0.1:.2f}" '
        f'fill="none" stroke="{RING_COLOR.get(kind, tile_set.ground[kind])}" stroke-width="{size * 0.07:.2f}"/>'
        f'<g transform="translate({size / 2:.2f} {size / 2:.2f}) scale({size * 0.56 / 26:.4f})">{_PORT_ICONS[kind]}</g>'
        f'</g>'
    )


def port_group(kind, way, x=0, y=0, tiles=None):
    """A port sea tile at (x, y): sea, a pier toward the coast (`way`: E, W, NE, NW, SE or
    SW), and a round badge. A 3:1 port shows "3:1"; a 2:1 port shows the resource's icon
    above "2:1", inside a ring of the resource's colour. `kind` is "3" or a resource letter."""
    tile_set = get_tile_set(tiles)
    shadow = '<circle cx="3" cy="4" r="35" fill="#000000" opacity="0.3"/>' if tile_set.shadows else ""
    if kind == "3":
        badge = (
            f'<circle r="35" fill="#f6f0dc" stroke="{OUTLINE}" stroke-width="3"/>'
            f'<text y="9" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="27" '
            f'font-weight="bold" fill="#2b2b2b">3:1</text>'
        )
    else:
        badge = (
            f'<circle r="35" fill="#f6f0dc" stroke="{OUTLINE}" stroke-width="3"/>'
            f'<circle r="31" fill="none" stroke="{RING_COLOR.get(kind, tile_set.ground[kind])}" stroke-width="4"/>'
            f'<g transform="translate(0 -10) scale(1.3)">{_PORT_ICONS[kind]}</g>'
            f'<text y="23" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="18" '
            f'font-weight="bold" fill="#2b2b2b">2:1</text>'
        )
    return (
        f'<g transform="translate({x} {y})">'
        f'<use href="#sea"/>'
        f'<use href="#dock" transform="rotate({WAY_ANGLES[way]})"/>'
        f'{shadow}{badge}'
        f'</g>'
    )


def tile_defs(tiles=None):
    tile_set = get_tile_set(tiles)
    return "<defs>" + tile_set.defs + edge_symbols() + "".join(tile_set.symbols) + tile_set.sea + _dock_symbol() + "</defs>"


def preview_svg(tiles=None):
    """All the tiles, the sea, and the ports of a tile set, to look at the artwork."""
    step = 2 * HALF_WIDTH + 14
    width = step * 7 + 14
    positions = [(letter, 14 + HALF_WIDTH + i * step) for i, letter in enumerate("WSGCOD")]
    uses = (
        "".join(f'<use href="#edge-dark" x="{x}" y="114"/>' for _, x in positions)
        + "".join(f'<use href="#edge-light" x="{x}" y="114"/>' for _, x in positions)
        + "".join(f'<use href="#tile-{letter}" x="{x}" y="114"/>' for letter, x in positions)
        + f'<use href="#sea" x="{14 + HALF_WIDTH + 6 * step}" y="114"/>'
    )
    ports = "".join(
        port_group(kind, way, 14 + HALF_WIDTH + i * step, 342, tiles)
        for i, (kind, way) in enumerate(
            (("3", "E"), ("W", "SE"), ("S", "SW"), ("G", "W"), ("C", "NW"), ("O", "NE"), ("3", "E"))
        )
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} 456" width="{width:.0f}" height="456">'
        f'<rect width="100%" height="100%" fill="#f7f3e3"/>{tile_defs(tiles)}{uses}{ports}</svg>'
    )
