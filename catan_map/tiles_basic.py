"""The "basic" tile set: flat colours and simple shapes."""
from __future__ import annotations

from .board import RESOURCE_NAMES
from .tiles_common import HEX_POINTS, TileSet, symbol

PALETTE = {
    "W": {"ground": "#3f7d43", "dark": "#245c2b", "light": "#5fa05a", "trunk": "#6b4a2b"},
    "S": {"ground": "#9fd36f", "dark": "#6fae45", "light": "#c4e8a0", "wool": "#fbfaf2", "skin": "#3d3a37"},
    "G": {"ground": "#efc63f", "dark": "#c9971b", "light": "#f8de7a", "ear": "#d9a521", "stem": "#b07e14"},
    "C": {"ground": "#8cc63f", "dark": "#a2482f", "light": "#cf7455", "mortar": "#e4a58f", "wall": "#6b3d2a"},
    "O": {"ground": "#7f8a96", "dark": "#58626d", "light": "#a7b1bb", "snow": "#f1f4f7"},
    "D": {"ground": "#e6cf99", "dark": "#c9ae6e", "light": "#f3e4bb", "cactus": "#6f9a58"},
}
SEA = {"ground": "#3b8fd0", "wave": "#6db3e6", "deep": "#2b76b5"}


def _wood(c):
    def pine(x, y, size):
        h, w = 34 * size, 13 * size
        return (
            f'<rect x="{x - 2 * size}" y="{y + h * 0.78}" width="{4 * size}" height="{9 * size}" fill="{c["trunk"]}"/>'
            f'<polygon points="{x},{y - h * 0.5} {x + w},{y + h * 0.28} {x - w},{y + h * 0.28}" fill="{c["dark"]}"/>'
            f'<polygon points="{x},{y - h * 0.15} {x + w * 1.25},{y + h * 0.62} {x - w * 1.25},{y + h * 0.62}" fill="{c["dark"]}"/>'
            f'<polygon points="{x},{y - h * 0.5} {x + w * 0.35},{y - h * 0.05} {x - w * 0.35},{y - h * 0.05}" fill="{c["light"]}"/>'
        )

    return (
        pine(-46, -26, 0.9) + pine(46, -30, 0.8) + pine(-60, 30, 0.8)
        + pine(58, 28, 0.9) + pine(-12, 56, 0.85) + pine(20, -66, 0.7) + pine(-30, -66, 0.7)
    )


def _sheep(c):
    def sheep(x, y, size, flip=1):
        s = size
        legs = "".join(
            f'<rect x="{x + dx * s * flip - 1.6 * s}" y="{y + 8 * s}" width="{3.2 * s}" height="{9 * s}" fill="{c["skin"]}"/>'
            for dx in (-9, -3, 4, 10)
        )
        wool = "".join(
            f'<circle cx="{x + dx * s * flip}" cy="{y + dy * s}" r="{r * s}" fill="{c["wool"]}"/>'
            for dx, dy, r in ((-11, 0, 9), (-3, -5, 10), (6, -2, 10), (13, 3, 8), (-5, 5, 9), (5, 6, 9))
        )
        head = (
            f'<ellipse cx="{x + 20 * s * flip}" cy="{y + 2 * s}" rx="{6 * s}" ry="{7 * s}" fill="{c["skin"]}"/>'
            f'<circle cx="{x + 22 * s * flip}" cy="{y}" r="{1.1 * s}" fill="{c["wool"]}"/>'
        )
        return legs + wool + head

    grass = "".join(
        f'<path d="M{x},{y} l-3,-7 M{x},{y} l0,-9 M{x},{y} l3,-7" stroke="{c["dark"]}" stroke-width="2" '
        f'stroke-linecap="round" fill="none"/>'
        for x, y in ((-60, -4), (62, 6), (-20, 70), (40, -70), (-52, -60), (18, 72))
    )
    return grass + sheep(-30, -38, 0.85, 1) + sheep(34, 40, 0.85, -1)


def _grain(c):
    def stalk(x, y, height, lean):
        top = y - height
        ears = "".join(
            f'<ellipse cx="{x + lean * (1 - k / 5) * 0.5 + side * 5}" cy="{top + k * 8 + (3 if side > 0 else 0)}" '
            f'rx="3.4" ry="7" fill="{c["ear"]}" transform="rotate({side * 28} {x + side * 5} {top + k * 8})"/>'
            for k in range(5)
            for side in (-1, 1)
        )
        return (
            f'<path d="M{x},{y} Q{x + lean * 0.2},{y - height / 2} {x + lean * 0.5},{top}" '
            f'stroke="{c["stem"]}" stroke-width="2.4" fill="none"/>'
            f'<ellipse cx="{x + lean * 0.5}" cy="{top - 6}" rx="3.4" ry="8" fill="{c["ear"]}"/>' + ears
        )

    furrows = "".join(
        f'<path d="M-90,{y} Q0,{y - 12} 90,{y}" stroke="{c["light"]}" stroke-width="3" fill="none"/>'
        for y in (-62, 66, 82)
    )
    return (
        furrows
        + stalk(-62, 8, 44, -6) + stalk(-48, 22, 40, 4) + stalk(-34, -30, 34, -4)
        + stalk(60, 10, 44, 6) + stalk(46, 24, 40, -4) + stalk(34, -34, 34, 4)
        + stalk(-6, 74, 30, 3) + stalk(8, 78, 28, -3)
    )


def _clay(c):
    """A clay quarry seen from above: a pale pink pit with terraced walls, a ring of grass
    with bushes, and red-brown rocky hills around the edge."""
    def hill(x, y, w, h):
        return (
            f'<path d="M{x - w},{y + h * 0.5} Q{x - w * 0.8},{y - h} {x - w * 0.1},{y - h * 0.8} '
            f'Q{x + w * 0.7},{y - h * 1.1} {x + w},{y + h * 0.3} Q{x},{y + h * 0.9} {x - w},{y + h * 0.5} Z" fill="{c["dark"]}"/>'
            f'<path d="M{x - w * 0.7},{y + h * 0.1} Q{x - w * 0.4},{y - h * 0.7} {x + w * 0.1},{y - h * 0.6} '
            f'Q{x + w * 0.5},{y - h * 0.5} {x + w * 0.6},{y} Q{x},{y + h * 0.3} {x - w * 0.7},{y + h * 0.1} Z" fill="{c["light"]}"/>'
        )

    def bush(x, y):
        return f'<circle cx="{x}" cy="{y}" r="6" fill="#3f8a34"/><circle cx="{x - 2}" cy="{y - 2}" r="3.5" fill="#5aa84a"/>'

    hills = "".join(
        hill(x, y, w, h)
        for x, y, w, h in (
            (-30, -80, 44, 24), (34, -82, 42, 24), (-72, -52, 40, 26), (74, -50, 40, 26),
            (-86, -6, 34, 28), (88, 0, 34, 28), (-80, 40, 34, 26), (82, 44, 34, 26),
            (-52, 84, 44, 22), (6, 94, 46, 22), (58, 84, 42, 22),
        )
    )
    pit = (
        f'<path d="M-62,10 Q-66,-28 -30,-42 Q0,-52 30,-42 Q66,-30 62,0 Q60,30 70,46 Q40,70 0,66 '
        f'Q-40,70 -66,46 Q-58,30 -62,10 Z" fill="{c["mortar"]}"/>'
        f'<path d="M-52,-24 Q-30,-52 8,-46 Q46,-42 56,-14" stroke="{c["wall"]}" stroke-width="7" fill="none" stroke-linecap="round"/>'
        f'<path d="M-46,-12 Q-26,-38 8,-34 Q40,-30 48,-8" stroke="{c["wall"]}" stroke-width="5" fill="none" stroke-linecap="round" opacity="0.8"/>'
        f'<path d="M30,56 Q50,40 46,20" stroke="{c["wall"]}" stroke-width="6" fill="none" stroke-linecap="round"/>'
        f'<path d="M-40,40 Q-10,64 30,52" stroke="#ffffff" stroke-width="4" fill="none" opacity="0.35" stroke-linecap="round"/>'
    )
    hut = (
        f'<rect x="-58" y="-2" width="14" height="12" fill="#e3d5bd" stroke="{c["wall"]}" stroke-width="2"/>'
        f'<rect x="-60" y="-5" width="18" height="5" fill="{c["wall"]}"/>'
    )
    bushes = "".join(bush(x, y) for x, y in ((-46, -52), (-22, -58), (40, -56), (54, -42), (-70, 6), (34, 74), (-30, 76)))
    return hills + pit + hut + bushes


def _ore(c):
    def peak(x, y, w, h, snow=True):
        body = f'<polygon points="{x - w},{y} {x},{y - h} {x + w},{y}" fill="{c["dark"]}"/>'
        shade = f'<polygon points="{x},{y - h} {x + w},{y} {x + w * 0.1},{y}" fill="{c["ground"]}" opacity="0.55"/>'
        cap = (
            f'<polygon points="{x},{y - h} {x + w * 0.3},{y - h * 0.62} {x + w * 0.1},{y - h * 0.7} '
            f'{x - w * 0.08},{y - h * 0.58} {x - w * 0.3},{y - h * 0.62}" fill="{c["snow"]}"/>'
            if snow else ""
        )
        return body + shade + cap

    return (
        peak(-48, -24, 34, 46) + peak(46, -30, 28, 36) + peak(-58, 58, 30, 38, snow=False)
        + peak(52, 66, 34, 44) + peak(-4, 76, 22, 28, snow=False)
        + f'<polygon points="-18,-64 -4,-82 10,-64" fill="{c["light"]}"/>'
    )


def _desert(c):
    dunes = "".join(
        f'<path d="M-100,{y} Q-50,{y - 22} 0,{y - 4} T100,{y - 6} L100,120 L-100,120 Z" fill="{shade}"/>'
        for y, shade in ((52, c["light"]), (72, c["dark"]))
    )
    cactus = (
        f'<g fill="{c["cactus"]}">'
        f'<rect x="-45" y="-58" width="9" height="32" rx="4.5"/>'
        f'<rect x="-55" y="-50" width="6" height="14" rx="3"/><rect x="-55" y="-39" width="14" height="5" rx="2.5"/>'
        f'<rect x="-36" y="-46" width="14" height="5" rx="2.5"/><rect x="-26" y="-56" width="5" height="15" rx="2.5"/>'
        f'</g>'
    )
    sun = f'<circle cx="50" cy="-52" r="12" fill="{c["light"]}"/>'
    return sun + cactus + dunes


_ART = {"W": _wood, "S": _sheep, "G": _grain, "C": _clay, "O": _ore, "D": _desert}


def _sea():
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


def build():
    symbols = tuple(
        symbol(letter, RESOURCE_NAMES.get(letter, "desert"), PALETTE[letter]["ground"], _ART[letter](PALETTE[letter]))
        for letter in "WSGCOD"
    )
    return TileSet(
        "basic", "flat colours and simple shapes", symbols, _sea(), "",
        {letter: PALETTE[letter]["ground"] for letter in "WSGCOD"},
    )
