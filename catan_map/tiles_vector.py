"""The "victory" tile set: painted-looking tiles.

Gradients for light and shade, many small shapes (trees, stalks, rocks, tufts) scattered in a
fixed order, and a fine grain on top. The scattering uses a random generator with a fixed
seed, so the drawing is always the same. No fonts and no external files; the grain is an SVG
filter.
"""
from __future__ import annotations

import random

from .board import RESOURCE_NAMES
from .tiles_common import HALF_WIDTH, HEX_POINTS, RADIUS, TileSet, symbol

GROUND = {
    "W": ("#3f7d43", "#1f4a27"), "S": ("#9fd36f", "#6aa043"), "G": ("#efc63f", "#b8861c"),
    "C": ("#8cc63f", "#4f8a2b"), "O": ("#98a3ae", "#5d6772"), "D": ("#e6cf99", "#b99c5d"),
}


# ------------------------------------------------------------------------------ helpers


def _n(value):
    text = f"{value:.1f}"
    if text.endswith(".0"):
        text = text[:-2]
    return "0" if text == "-0" else text


def _rng(name):
    """A random generator that gives the same numbers every time for the same name."""
    return random.Random(f"catan-map-art:{name}").random


def _pick(rng, items):
    return items[int(rng() * len(items))]


def _inside(x, y, margin=0.0):
    return abs(x) <= HALF_WIDTH - margin and abs(y) <= RADIUS - margin - abs(x) * 0.5774


def _scatter(rng, count, spacing, margin=-6.0, keep=None):
    """Up to `count` points inside the hexagon at least `spacing` apart (a little past the
    edge with a negative margin, because the drawing is clipped), skipping where keep(x, y) is
    False. Sorted from top to bottom, so that the ones below are drawn over the ones above."""
    points = []
    for _ in range(count * 60):
        if len(points) >= count:
            break
        x, y = (rng() * 2 - 1) * (HALF_WIDTH + 8), (rng() * 2 - 1) * (RADIUS + 8)
        if not _inside(x, y, margin) or (keep and not keep(x, y)):
            continue
        if any((x - a) ** 2 + (y - b) ** 2 < spacing ** 2 for a, b in points):
            continue
        points.append((x, y))
    return sorted(points, key=lambda p: p[1])


def _perspective(y):
    """Things lower on the tile are a little bigger, as if seen from the front."""
    return 0.8 + (y + RADIUS) / (2 * RADIUS) * 0.45


def _ellipse(x, y, rx, ry, fill, opacity=None, extra=""):
    o = f' opacity="{opacity}"' if opacity is not None else ""
    return f'<ellipse cx="{_n(x)}" cy="{_n(y)}" rx="{_n(rx)}" ry="{_n(ry)}" fill="{fill}"{o}{extra}/>'


def _circle(x, y, r, fill, opacity=None):
    o = f' opacity="{opacity}"' if opacity is not None else ""
    return f'<circle cx="{_n(x)}" cy="{_n(y)}" r="{_n(r)}" fill="{fill}"{o}/>'


def _poly(points, fill, opacity=None, stroke=None):
    o = f' opacity="{opacity}"' if opacity is not None else ""
    s = f' stroke="{stroke}" stroke-width="0.8" stroke-linejoin="round"' if stroke else ""
    return f'<polygon points="{" ".join(f"{_n(x)},{_n(y)}" for x, y in points)}" fill="{fill}"{o}{s}/>'


def _tufts(rng, points, colors, size=1.0):
    """Little blades of grass, as one path per colour."""
    paths = {color: [] for color in colors}
    for x, y in points:
        s = size * _perspective(y)
        lean = (rng() - 0.5) * 3 * s
        paths[_pick(rng, colors)].append(
            f"M{_n(x)},{_n(y)} l{_n(-2.4 * s)},{_n(-5 * s)} M{_n(x)},{_n(y)} l{_n(lean)},{_n(-7.5 * s)} "
            f"M{_n(x)},{_n(y)} l{_n(2.4 * s)},{_n(-5 * s)}"
        )
    return "".join(
        f'<path d="{"".join(parts)}" stroke="{color}" stroke-width="1.3" stroke-linecap="round" fill="none"/>'
        for color, parts in paths.items() if parts
    )


def _blotches(rng, count, colors, size=(7, 16), opacity=0.35):
    """Soft patches of slightly different colour, to break up a flat ground."""
    out = []
    for _ in range(count):
        x, y = (rng() * 2 - 1) * HALF_WIDTH, (rng() * 2 - 1) * RADIUS
        w = size[0] + rng() * (size[1] - size[0])
        out.append(_ellipse(x, y, w, w * (0.45 + rng() * 0.3), _pick(rng, colors), opacity))
    return "".join(out)


def _rock(x, y, w, h, rng, light, mid, dark, glint=None):
    """A faceted rock, lit from the top left."""
    jitter = lambda: 0.85 + rng() * 0.3
    a = (x - w * jitter(), y + h * 0.35)
    b = (x - w * 0.55 * jitter(), y - h * 0.75 * jitter())
    c = (x + w * 0.35 * jitter(), y - h * jitter())
    d = (x + w * jitter(), y - h * 0.15)
    e = (x + w * 0.8 * jitter(), y + h * 0.7)
    f = (x - w * 0.2, y + h * 0.85)
    m = (x + w * 0.05, y - h * 0.1)
    parts = [
        _ellipse(x + w * 0.2, y + h * 0.85, w * 1.05, h * 0.28, "#000000", 0.25),
        _poly([a, b, c, d, e, f], mid, stroke=dark),
        _poly([b, c, m], light),
        _poly([a, b, m], mid, 0.6),
        _poly([c, d, e, m], dark, 0.75),
        _poly([m, e, f], dark, 0.5),
    ]
    if glint:
        parts.append(_poly([(x - w * 0.4, y - h * 0.5), (x - w * 0.1, y - h * 0.62), (x - w * 0.2, y - h * 0.4)], glint, 0.8))
    return "".join(parts)


# ----------------------------------------------------------------------------- the tiles


def _pine(x, y, s, rng):
    dark, mid, light = _pick(rng, (("#14421e", "#256f33", "#3f9648"), ("#18491f", "#2b7a36", "#52a24f"), ("#103a1c", "#1f6330", "#378a45")))
    parts = [
        _ellipse(x + 6 * s, y + 3 * s, 12 * s, 3.8 * s, "#07170b", 0.38),
        f'<rect x="{_n(x - 1.9 * s)}" y="{_n(y - 3 * s)}" width="{_n(3.8 * s)}" height="{_n(9 * s)}" fill="#4a3220"/>',
    ]
    for apex, base, half in ((-36, -15, 8), (-27, -5, 11), (-17, 5, 14)):
        ax, ay, by = x, y + apex * s, y + base * s
        w = half * s * (0.92 + rng() * 0.16)
        parts.append(_poly([(ax, ay), (ax - w, by), (ax, by + 2.5 * s)], light))
        parts.append(_poly([(ax, ay), (ax, by + 2.5 * s), (ax + w, by)], dark))
        parts.append(_poly([(ax, ay), (ax - w * 0.35, by - 4 * s), (ax - w * 0.8, by - 0.5 * s)], mid, 0.55))
    return "".join(parts)


def _broadleaf(x, y, s, rng):
    shade = _pick(rng, (("#1f5d28", "#37803a", "#6db04f"), ("#2a6a2a", "#4a9440", "#8cc65c")))
    return (
        _ellipse(x + 5 * s, y + 3 * s, 13 * s, 4 * s, "#07170b", 0.35)
        + f'<rect x="{_n(x - 1.8 * s)}" y="{_n(y - 8 * s)}" width="{_n(3.6 * s)}" height="{_n(12 * s)}" fill="#5a3d24"/>'
        + _circle(x + 3 * s, y - 16 * s, 11 * s, shade[0])
        + _circle(x - 4 * s, y - 15 * s, 10 * s, shade[1])
        + _circle(x - 1 * s, y - 23 * s, 9 * s, shade[1])
        + _circle(x - 4 * s, y - 24 * s, 5 * s, shade[2], 0.85)
        + _circle(x + 5 * s, y - 14 * s, 6 * s, shade[0], 0.6)
    )


def _wood(rng):
    trees = []
    for x, y in _scatter(rng, 46, 15, margin=-4):
        s = 0.62 * _perspective(y) * (0.85 + rng() * 0.3)
        trees.append(_broadleaf(x, y, s, rng) if rng() < 0.16 else _pine(x, y, s, rng))
    undergrowth = _tufts(rng, _scatter(rng, 60, 8, margin=-2), ("#2d6e30", "#4a8f3e", "#1a4f26"))
    return (
        _blotches(rng, 36, ("#16431f", "#4c8a3c", "#2a6a2d"), (6, 18), 0.4)
        + undergrowth + "".join(trees)
    )


def _sheep(x, y, s, flip, rng):
    f = flip
    legs = "".join(
        f'<rect x="{_n(x + (dx * f) * s - 1.5 * s)}" y="{_n(y + 7 * s)}" width="{_n(3 * s)}" height="{_n(9 * s)}" fill="#34312e"/>'
        for dx in (-9, -3, 5, 11)
    )
    wool = "".join(
        f'<circle cx="{_n(x + dx * f * s)}" cy="{_n(y + dy * s)}" r="{_n(r * s)}" fill="url(#wool)"/>'
        for dx, dy, r in ((-12, 1, 8), (-4, -6, 10), (6, -4, 10), (14, 2, 8), (-6, 5, 9), (4, 6, 9), (0, 0, 9), (-13, -4, 6))
    )
    head = (
        _ellipse(x + 20 * f * s, y + 1 * s, 5.5 * s, 7 * s, "#3a3633")
        + _ellipse(x + 17 * f * s, y - 3 * s, 3 * s, 1.8 * s, "#4a4642")
        + _ellipse(x + 22 * f * s, y - 1 * s, 1 * s, 1 * s, "#f4f0e4")
        + _circle(x + 17 * f * s, y - 6 * s, 3.5 * s, "url(#wool)")
    )
    return _ellipse(x + 2 * f * s, y + 16 * s, 19 * s, 4 * s, "#1c3a0e", 0.4) + legs + wool + head


def _sheep_tile(rng):
    flowers = "".join(
        _circle(x, y, 1.5, _pick(rng, ("#ffffff", "#ffe27a", "#f5b7d2", "#ffffff")))
        for x, y in _scatter(rng, 26, 9, margin=0)
    )
    tufts = _tufts(rng, _scatter(rng, 120, 6.5, margin=-4), ("#5f9a34", "#86c04f", "#487f28", "#a4d46a"))
    sheep = "".join(
        _sheep(x, y, s, flip, rng)
        for x, y, s, flip in ((-34, -42, 0.8, 1), (40, -36, 0.7, -1), (-50, 28, 0.72, 1), (22, 56, 0.85, -1), (-2, -72, 0.6, 1))
    )
    return _blotches(rng, 34, ("#c4e88c", "#78b445", "#a8d874"), (8, 22), 0.4) + tufts + flowers + sheep


def _grain(rng):
    shades = ("#e8b92f", "#d9a21d", "#f2d24f", "#c98f14")
    parts = []
    rows = [-90 + 15 * k for k in range(14)]
    for y in rows:
        s = _perspective(y) * 0.95
        parts.append(f'<rect x="-100" y="{_n(y - 2)}" width="200" height="{_n(8 * s)}" fill="#7a5410" opacity="0.22"/>')
        step = 12 * s
        x = -104 + rng() * step
        while x < 104:
            sx = x + (rng() - 0.5) * 3
            h = (24 + rng() * 8) * s
            lean = (rng() - 0.5) * 7 * s
            top = (sx + lean, y - h)
            color = _pick(rng, shades)
            parts.append(
                f'<path d="M{_n(sx)},{_n(y)} Q{_n(sx + lean * 0.2)},{_n(y - h * 0.55)} {_n(top[0])},{_n(top[1])}" '
                f'stroke="#9a6d14" stroke-width="{_n(1.5 * s)}" fill="none"/>'
            )
            for k in range(4):
                ey = top[1] + k * 4.2 * s
                parts.append(_ellipse(top[0] - 2.6 * s, ey + 1.5 * s, 1.9 * s, 4 * s, color, extra=f' transform="rotate(-24 {_n(top[0] - 2.6 * s)} {_n(ey)})"'))
                parts.append(_ellipse(top[0] + 2.6 * s, ey + 1.5 * s, 1.9 * s, 4 * s, color, extra=f' transform="rotate(24 {_n(top[0] + 2.6 * s)} {_n(ey)})"'))
            parts.append(_ellipse(top[0], top[1] - 3 * s, 2 * s, 5 * s, color))
            parts.append(
                f'<path d="M{_n(top[0])},{_n(top[1] - 6 * s)} l0,{_n(-6 * s)} M{_n(top[0] - 1.5 * s)},{_n(top[1] - 5 * s)} l{_n(-1.5 * s)},{_n(-5 * s)} '
                f'M{_n(top[0] + 1.5 * s)},{_n(top[1] - 5 * s)} l{_n(1.5 * s)},{_n(-5 * s)}" stroke="#f0d36a" stroke-width="0.6" fill="none"/>'
            )
            x += step
    return _blotches(rng, 30, ("#f6dc72", "#c8921a"), (8, 20), 0.3) + "".join(parts)


def _clay(rng):
    pit_mask = lambda x, y: (x / 74) ** 2 + ((y - 10) / 62) ** 2 > 1
    rocks = "".join(
        _rock(x, y, 11 * _perspective(y) * (0.8 + rng() * 0.5), 8 * _perspective(y) * (0.8 + rng() * 0.5), rng,
              "#d88a68", "#b05a3a", "#6e3320")
        for x, y in _scatter(rng, 38, 13, margin=-4, keep=pit_mask)
    )
    grass = _tufts(rng, _scatter(rng, 90, 6, margin=-4, keep=pit_mask), ("#5c9a2c", "#8cc94a", "#3f7a22"))
    bushes = "".join(
        _circle(x, y, 6, "#2f6f2a") + _circle(x - 2, y - 2, 4, "#4f9a3c") + _circle(x - 3, y - 3, 2, "#8cc65c", 0.9)
        for x, y in ((-46, -52), (-22, -60), (42, -56), (54, -40), (-72, 8), (34, 76), (-30, 78), (66, 40))
    )
    pit = (
        '<path d="M-64,10 Q-68,-28 -32,-44 Q0,-54 32,-44 Q68,-32 64,0 Q62,30 72,48 Q40,74 0,68 '
        'Q-40,72 -68,48 Q-60,30 -64,10 Z" fill="url(#clay-pit)" stroke="#8a4a32" stroke-width="2"/>'
    )
    swirls = "".join(
        f'<path d="{d}" stroke="{color}" stroke-width="{w}" fill="none" stroke-linecap="round" opacity="{o}"/>'
        for d, color, w, o in (
            ("M-44,44 Q-10,70 34,52", "#fbe3d6", 4, 0.5),
            ("M-50,20 Q-20,36 6,24 T48,36", "#f3c8b4", 3, 0.5),
            ("M-30,2 Q0,14 30,2", "#c9806a", 2, 0.4),
            ("M-56,34 Q-30,50 -6,44", "#b4684f", 2.5, 0.35),
            ("M10,60 Q40,46 56,22", "#f8d9c9", 3, 0.45),
        )
    )
    walls = "".join(
        f'<path d="{d}" stroke="#4a2a1c" stroke-width="{w + 3}" fill="none" stroke-linecap="round" opacity="0.5" transform="translate(1.5 3)"/>'
        f'<path d="{d}" stroke="#6b3d2a" stroke-width="{w}" fill="none" stroke-linecap="round"/>'
        f'<path d="{d}" stroke="#a8694a" stroke-width="{w * 0.5}" fill="none" stroke-dasharray="5 3" stroke-linecap="round"/>'
        for d, w in (
            ("M-56,-22 Q-32,-52 8,-48 Q46,-44 58,-14", 8),
            ("M-48,-10 Q-26,-38 8,-34 Q40,-30 50,-6", 6),
            ("M34,58 Q54,42 50,20", 7),
            ("M-66,44 Q-50,52 -36,50", 5),
        )
    )
    hut = (
        '<rect x="-60" y="-1" width="15" height="12" fill="#e8dcc4" stroke="#6b3d2a" stroke-width="1.5"/>'
        '<polygon points="-62,-1 -52.5,-8 -43,-1" fill="#8a4a32" stroke="#4a2a1c" stroke-width="1"/>'
        '<rect x="-54" y="4" width="4" height="7" fill="#4a2a1c"/>'
        '<rect x="-40" y="6" width="6" height="5" fill="#a07040" stroke="#5a3a1c" stroke-width="0.8"/>'
        '<rect x="-34" y="8" width="5" height="4" fill="#b8844c" stroke="#5a3a1c" stroke-width="0.8"/>'
    )
    return grass + rocks + bushes + pit + swirls + walls + hut


def _peak(x, base, w, h, rng):
    jx = lambda: (rng() - 0.5) * w * 0.12
    apex = (x + jx(), base - h)
    mid = (x + w * 0.08, base + 3)
    left = [apex, (x - w * 0.25 + jx(), base - h * 0.62), (x - w * 0.5, base - h * 0.42), (x - w * 0.66 + jx(), base - h * 0.2), (x - w, base + 2), mid]
    right = [apex, (x + w * 0.2 + jx(), base - h * 0.58), (x + w * 0.42, base - h * 0.36), (x + w * 0.7 + jx(), base - h * 0.16), (x + w, base + 2), mid]
    ridges = "".join(
        f'<path d="M{_n(apex[0])},{_n(apex[1])} L{_n(px)},{_n(py)}" stroke="#2e353d" stroke-width="1" opacity="0.4" fill="none"/>'
        for px, py in ((x - w * 0.35, base - h * 0.1), (x + w * 0.3, base - h * 0.05), (x - w * 0.12, base))
    )
    snow_l = [apex, (x - w * 0.2, base - h * 0.68), (x - w * 0.1, base - h * 0.7), (x - w * 0.02, base - h * 0.6), (x + 0.0, base - h * 0.68)]
    snow_r = [apex, (x + 0.0, base - h * 0.68), (x + w * 0.1, base - h * 0.6), (x + w * 0.18, base - h * 0.64), (x + w * 0.2, base - h * 0.58)]
    return (
        _ellipse(x + w * 0.3, base + 4, w * 1.1, h * 0.12, "#000000", 0.25)
        + _poly(left, "#8d98a4") + _poly(right, "#4b555f")
        + _poly([apex, (x - w * 0.25, base - h * 0.35), (x - w * 0.05, base)], "#a9b4bf", 0.5)
        + _poly(snow_l, "#f4f7fa") + _poly(snow_r, "#c7d3df") + ridges
    )


def _ore(rng):
    peaks = "".join(
        _peak(x, base, w, h, rng)
        for x, base, w, h in (
            (-4, -30, 34, 46), (-62, -20, 42, 58), (54, -26, 38, 52), (-16, 14, 40, 58),
            (62, 50, 42, 60), (-62, 58, 40, 56), (6, 84, 38, 50), (38, 12, 30, 38),
        )
    )
    scree = "".join(
        _rock(x, y, 4.5 * _perspective(y) * (0.7 + rng() * 0.8), 3.4 * _perspective(y) * (0.7 + rng() * 0.8), rng,
              "#b9c3cc", "#838e99", "#4f5862", glint=_pick(rng, (None, None, "#e8c35a", "#9fc6e8")))
        for x, y in _scatter(rng, 40, 10, margin=-4)
    )
    return _blotches(rng, 26, ("#7d8791", "#aab4be", "#69737d"), (6, 16), 0.35) + peaks + scree


def _saguaro(x, y, s):
    return (
        _ellipse(x + 8 * s, y + 2, 14 * s, 3.4 * s, "#5a4420", 0.3)
        + f'<rect x="{_n(x - 5 * s)}" y="{_n(y - 36 * s)}" width="{_n(10 * s)}" height="{_n(38 * s)}" rx="{_n(5 * s)}" fill="#5f8f4c"/>'
        + f'<rect x="{_n(x)}" y="{_n(y - 36 * s)}" width="{_n(5 * s)}" height="{_n(38 * s)}" rx="{_n(2.5 * s)}" fill="#3f6a34" opacity="0.7"/>'
        + f'<path d="M{_n(x - 5 * s)},{_n(y - 14 * s)} h{_n(-7 * s)} v{_n(-14 * s)}" stroke="#5f8f4c" stroke-width="{_n(5 * s)}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        + f'<path d="M{_n(x + 5 * s)},{_n(y - 20 * s)} h{_n(7 * s)} v{_n(-12 * s)}" stroke="#4f7d3f" stroke-width="{_n(5 * s)}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        + _circle(x - 4 * s, y - 36 * s, 1.6 * s, "#e8587a")
    )


def _desert(rng):
    dunes = []
    for px, yb, h in ((30, -40, 20), (-40, -4, 26), (40, 34, 28), (-30, 66, 30)):
        py = yb - h
        dunes.append(
            f'<path d="M{px - 110},{yb + 8} Q{px - 50},{py + 8} {px},{py} Q{px + 40},{py + 8} {px + 90},{yb + 8} L{px + 90},130 L{px - 110},130 Z" fill="#ecd9a3"/>'
            f'<path d="M{px},{py} Q{px + 24},{py + 10} {px + 58},{yb + 8} Q{px + 26},{yb + 1} {px},{py} Z" fill="#b98f4c" opacity="0.5"/>'
            f'<path d="M{px - 90},{yb + 4} Q{px - 40},{py + 4} {px},{py}" stroke="#fbf0cb" stroke-width="2" fill="none" opacity="0.8"/>'
        )
    ripples = "".join(
        f'<path d="M{_n(x)},{_n(y)} q{_n(4 * _perspective(y))},-2 {_n(8 * _perspective(y))},0" stroke="#a98544" stroke-width="0.9" fill="none" opacity="0.4"/>'
        for x, y in _scatter(rng, 110, 6, margin=-2)
    )
    pebbles = "".join(
        _rock(x, y, 3.2, 2.4, rng, "#d8c08c", "#a8895a", "#6c5530") for x, y in _scatter(rng, 14, 14, margin=-2)
    )
    scrub = _tufts(rng, _scatter(rng, 16, 14, margin=0), ("#9a8a4a", "#7a6a34", "#b3a263"), 1.3)
    return (
        _blotches(rng, 24, ("#f3e4b4", "#cfae6a"), (8, 22), 0.35)
        + "".join(dunes) + ripples + pebbles + scrub + _saguaro(-52, -30, 0.95) + _saguaro(56, 52, 0.6)
        + _circle(52, -58, 10, "#fff3c4", 0.8) + _circle(52, -58, 15, "#fff3c4", 0.25)
    )


_ART = {"W": _wood, "S": _sheep_tile, "G": _grain, "C": _clay, "O": _ore, "D": _desert}

def _shared_defs():
    """Gradients and the grain filter that every tile uses."""
    return (
        f'<radialGradient id="shade" cx="0" cy="0" r="{RADIUS}" gradientUnits="userSpaceOnUse">'
        '<stop offset="0.55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.42"/></radialGradient>'
        '<linearGradient id="light" x1="-100" y1="-100" x2="100" y2="100" gradientUnits="userSpaceOnUse">'
        '<stop offset="0" stop-color="#fff" stop-opacity="0.2"/><stop offset="0.5" stop-color="#fff" stop-opacity="0"/>'
        '<stop offset="1" stop-color="#000" stop-opacity="0.22"/></linearGradient>'
        '<filter id="grain" x="0" y="0" width="100%" height="100%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="7"/>'
        '<feColorMatrix type="matrix" values="0 0 0 0 0.1  0 0 0 0 0.08  0 0 0 0 0.05  0 0 0 2.2 -0.95"/></filter>'
        '<radialGradient id="wool" cx="0.35" cy="0.3" r="0.8"><stop offset="0" stop-color="#ffffff"/>'
        '<stop offset="0.7" stop-color="#ecebe3"/><stop offset="1" stop-color="#bdbcb0"/></radialGradient>'
        '<radialGradient id="clay-pit" cx="0.45" cy="0.4" r="0.7"><stop offset="0" stop-color="#f1b9a0"/>'
        '<stop offset="0.7" stop-color="#dd957b"/><stop offset="1" stop-color="#b8654d"/></radialGradient>'
        '<radialGradient id="token-face" cx="0.38" cy="0.32" r="0.85"><stop offset="0" stop-color="#fffaea"/>'
        '<stop offset="0.75" stop-color="#f1e7c8"/><stop offset="1" stop-color="#d9c89b"/></radialGradient>'
        '<radialGradient id="sea-gradient" cx="0" cy="0" r="100" gradientUnits="userSpaceOnUse">'
        '<stop offset="0" stop-color="#3f95d6"/><stop offset="1" stop-color="#3a8dcf"/></radialGradient>'   # almost flat, so that the sea tiles meet without a seam
    )




def _ground_gradient(letter):
    center, edge = GROUND[letter]
    return (
        f'<radialGradient id="ground-{letter}" cx="0" cy="0" r="{RADIUS}" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0.45" stop-color="{center}"/><stop offset="1" stop-color="{edge}"/></radialGradient>'
    )


_OVERLAY = (
    '<rect x="-100" y="-100" width="200" height="200" fill="url(#shade)"/>'
    '<rect x="-100" y="-100" width="200" height="200" fill="url(#light)"/>'
    '<rect x="-100" y="-100" width="200" height="200" filter="url(#grain)" opacity="0.22"/>'
)


def _sea():
    rng = _rng("sea")
    foam = "".join(
        f'<path d="M{_n(x)},{_n(y)} q5,-6 10,0 t10,0" stroke="#ffffff" stroke-width="{_n(1 + rng() * 1.4)}" '
        f'fill="none" stroke-linecap="round" opacity="{_n(0.18 + rng() * 0.3)}"/>'
        for x, y in _scatter(rng, 44, 14, margin=-4)
    )
    troughs = "".join(
        f'<path d="M{_n(x)},{_n(y)} q7,-5 14,0" stroke="#0f4a80" stroke-width="2" fill="none" stroke-linecap="round" opacity="0.28"/>'
        for x, y in _scatter(rng, 26, 18, margin=-4)
    )
    return (
        f'<symbol id="sea" overflow="visible">'
        f'<clipPath id="clip-sea"><polygon points="{HEX_POINTS}"/></clipPath>'
        f'<polygon points="{HEX_POINTS}" fill="url(#sea-gradient)" stroke="#3d91d2" stroke-width="1.5"/>'
        f'<g clip-path="url(#clip-sea)">{troughs}{foam}'
        f'<rect x="-100" y="-100" width="200" height="200" filter="url(#grain)" opacity="0.22"/></g>'      # no shade or edge line: one continuous sea
        f'<title>sea</title></symbol>'
    )


def build():
    symbols = tuple(
        symbol(
            letter, RESOURCE_NAMES.get(letter, "desert"), f"url(#ground-{letter})",
            _ART[letter](_rng(letter)), _OVERLAY, _ground_gradient(letter),
        )
        for letter in "WSGCOD"
    )
    return TileSet(
        "victory", "painted-looking tiles with light, shade and texture", symbols, _sea(), _shared_defs(),
        {letter: GROUND[letter][0] for letter in "WSGCOD"}, token_fill="url(#token-face)", shadows=True,
    )
