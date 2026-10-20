"""The small resource icons (on the port badges, the cost cards and the bank slots), in three sets.

Every icon is drawn around (0, 0) in a box about 26 wide, so any set can take the place of
another. ``simple`` is the look the tool has had so far; ``detailed`` has more shapes in the same
flat style; ``realistic`` has gradients, shading and texture like the realistic tiles. Gradients
are named per icon set (``ic-...``) so that icons of one set can share a drawing.
"""
from __future__ import annotations

import math
import random
import re

# ------------------------------------------------------------------------------------- the logs
# A pile of six logs, as on the wood card: the cut ends face the lower left and are in a triangle (3, 2, 1),
# the bodies go back to the upper right; the pile is drawn from the bottom up, each log over the one below.

LOG_R = 2.8                       # the radius of a cut end
LOG_LENGTH = 13                   # the length of the part of a log that shows: a log is more than twice as long as it is thick
LOG_ANGLE = -25                   # the direction of the logs, in degrees (up to the right)
LOG_ENDS = (                      # drawn from the bottom up, so that a log on top covers the part of the log below it
    (-10.6, 8.0), (-5.0, 8.0), (0.6, 8.0),          # the bottom row, in front
    (-7.8, 3.2), (-2.2, 3.2),                       # the second row
    (-5.0, -1.6),                                   # the top log
)


def _pile_shadow(opacity):
    """The shadow the pile throws on the ground: it lies under the whole base, which is flat under the three
    cut ends and then rises along the bodies of the front logs, so it is two ellipses, one level and one
    turned to the direction of the logs. (A single level one leaves the pile floating above it.)"""
    angle = math.radians(LOG_ANGLE)
    cos, sin = math.cos(angle), math.sin(angle)           # the direction of the logs is (cos, sin); the way down from a log's middle is (-sin, cos)
    bottom = [e for e in LOG_ENDS if e[1] == max(y for _, y in LOG_ENDS)]          # the bottom row
    left, right = min(x for x, _ in bottom), max(x for x, _ in bottom)
    low = bottom[0][1] + LOG_R * cos                                             # the lowest line of the pile
    level = f'<ellipse cx="{(left + right) / 2 + 1.2:.2f}" cy="{low:.2f}" rx="{(right - left) / 2 + 4.2:.2f}" ry="1.9" fill="#000" opacity="{opacity}"/>'
    # along the lower edge of the right-hand log, from its end to its far end
    mid_x = right + 0.5 * LOG_LENGTH * cos - LOG_R * sin
    mid_y = bottom[0][1] + 0.5 * LOG_LENGTH * sin + LOG_R * cos - 0.4
    tail = (f'<ellipse cx="{mid_x:.2f}" cy="{mid_y:.2f}" rx="{LOG_LENGTH / 2 + 0.8:.2f}" ry="1.5" fill="#000" opacity="{opacity}" '
            f'transform="rotate({LOG_ANGLE} {mid_x:.2f} {mid_y:.2f})"/>')
    return level + tail


def _pile_flat(detail):
    """The pile in flat colours (`detail` adds bark lines and the rings of the wood)."""
    parts = [_pile_shadow(0.22)]
    for i, (x, y) in enumerate(LOG_ENDS):
        body = ("#9c4d2b", "#8a4326", "#a4552f")[i % 3]
        parts.append(
            f'<g transform="rotate({LOG_ANGLE} {x} {y})">'
            f'<rect x="{x}" y="{y - LOG_R}" width="{LOG_LENGTH}" height="{2 * LOG_R}" rx="1.2" fill="{body}" stroke="#5a2a14" stroke-width="0.6"/>'
        )
        if detail:
            parts.append(
                f'<path d="M{x + 2},{y - 1.8} h{LOG_LENGTH - 3} M{x + 1.5},{y + 0.4} h{LOG_LENGTH - 2.5} M{x + 2.5},{y + 2.2} h{LOG_LENGTH - 4}" '
                f'stroke="#5a2a14" stroke-width="0.45" opacity="0.7" fill="none" stroke-linecap="round"/>'
            )
        parts.append(f'<ellipse cx="{x}" cy="{y}" rx="1.7" ry="{LOG_R}" fill="#f0d9a6" stroke="#5a2a14" stroke-width="0.7"/>')
        if detail:
            parts.append(
                f'<ellipse cx="{x}" cy="{y}" rx="1.0" ry="1.7" fill="none" stroke="#b98a4e" stroke-width="0.4"/>'
                f'<circle cx="{x}" cy="{y}" r="0.45" fill="#a9763b"/>'
            )
        parts.append('</g>')
    return "".join(parts)


def _pile_realistic():
    """The pile painted: bark with a gradient and grain, pale ends with rings, a shadow under it."""
    rng = random.Random("icon-pile")
    parts = [
        '<defs><linearGradient id="ic-log-body" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#b8643a"/>'
        '<stop offset="0.5" stop-color="#8c4326"/><stop offset="1" stop-color="#5c2a16"/></linearGradient>'
        '<radialGradient id="ic-log-end" cx="0.4" cy="0.4" r="0.8"><stop offset="0" stop-color="#f7e6bd"/>'
        '<stop offset="1" stop-color="#d9b378"/></radialGradient></defs>',
        _pile_shadow(0.3),
    ]
    for x, y in LOG_ENDS:
        lines = []
        for _ in range(6):
            start = 1 + rng.random() * 2                       # along the log, from its end
            length = min(2 + rng.random() * 4, LOG_LENGTH - start - 0.8)       # never past the other end
            lines.append(
                f'<path d="M{x + start:.1f},{y - LOG_R + 0.8 + rng.random() * (2 * LOG_R - 1.6):.1f} h{length:.1f}" '
                f'stroke="#3a1a0c" stroke-width="0.4" opacity="{0.3 + rng.random() * 0.3:.2f}" fill="none" stroke-linecap="round"/>'
            )
        grain = "".join(lines)
        parts.append(
            f'<g transform="rotate({LOG_ANGLE} {x} {y})">'
            f'<rect x="{x}" y="{y - LOG_R}" width="{LOG_LENGTH}" height="{2 * LOG_R}" rx="1.3" fill="url(#ic-log-body)" stroke="#4a2210" stroke-width="0.5"/>'
            f'<rect x="{x + 1.5}" y="{y - LOG_R + 0.5}" width="{LOG_LENGTH - 2.5}" height="0.9" rx="0.45" fill="#e8a77a" opacity="0.45"/>'
            + grain +
            f'<ellipse cx="{x}" cy="{y}" rx="1.8" ry="{LOG_R}" fill="url(#ic-log-end)" stroke="#4a2210" stroke-width="0.6"/>'
            f'<ellipse cx="{x}" cy="{y}" rx="1.2" ry="1.9" fill="none" stroke="#b98a4e" stroke-width="0.32"/>'
            f'<ellipse cx="{x}" cy="{y}" rx="0.6" ry="1.0" fill="none" stroke="#a9763b" stroke-width="0.32"/>'
            f'<circle cx="{x}" cy="{y}" r="0.28" fill="#8a5a28"/>'
            f'</g>'
        )
    return "".join(parts)


# ----------------------------------------------------------------------------- simple (as before)

SIMPLE = {
    "W": _pile_flat(False),
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

# --------------------------------------------------------------------------------------- detailed


def _detailed_sheep():
    wool = "".join(
        f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fbfaf4" stroke="#8f9585" stroke-width="0.9"/>'
        for x, y, r in ((-8.5, 1.5, 4.6), (-5.5, -3.2, 5.2), (-0.5, -5.4, 5.6), (5, -3.6, 5.4), (7, 1.6, 4.6),
                        (-4.5, 4.6, 5), (2.5, 5, 5.2), (0, 0.4, 5.8))
    )
    legs = "".join(
        f'<rect x="{x}" y="6.6" width="2.2" height="6" rx="0.6" fill="#4a4642"/><rect x="{x}" y="11.4" width="2.2" height="1.5" rx="0.5" fill="#26231f"/>'
        for x in (-6.6, -2.8, 2.6, 6.4)
    )
    head = (
        '<ellipse cx="12" cy="-2.6" rx="2.2" ry="1.2" fill="#4a4642" transform="rotate(-30 12 -2.6)"/>'
        '<ellipse cx="11.2" cy="1.8" rx="3.6" ry="4.8" fill="#3b3733" stroke="#1f1c19" stroke-width="0.6"/>'
        '<ellipse cx="12.8" cy="4.2" rx="1.7" ry="1.2" fill="#6a625b"/>'
        '<circle cx="12" cy="0.4" r="0.95" fill="#ffffff"/><circle cx="12.2" cy="0.4" r="0.45" fill="#111"/>'
        '<circle cx="9.2" cy="-2.2" r="2.1" fill="#fbfaf4" stroke="#8f9585" stroke-width="0.7"/>'
    )
    return (
        '<ellipse cx="0" cy="13.2" rx="12" ry="1.6" fill="#000" opacity="0.22"/>'
        + legs + '<circle cx="-12" cy="0.5" r="2.2" fill="#fbfaf4" stroke="#8f9585" stroke-width="0.8"/>' + wool + head
    )


def _detailed_wheat():
    parts = ['<path d="M0,13 Q0.6,4 0,-9" stroke="#a77512" stroke-width="1.8" fill="none" stroke-linecap="round"/>',
             '<path d="M0.4,9 Q7,6 9.5,1.5 Q5,3.5 0.4,6.5 Z" fill="#8fb04a"/>',
             '<path d="M-0.4,11 Q-7,8 -9.2,3.6 Q-4.6,5.6 -0.4,8.5 Z" fill="#7fa13c"/>']
    for k, y in enumerate((-6, -2.4, 1.2, 4.8)):
        for side in (-1, 1):
            parts.append(f'<ellipse cx="{side * 3.3}" cy="{y}" rx="1.9" ry="3.3" fill="#e2ab27" stroke="#a77512" stroke-width="0.55" '
                         f'transform="rotate({side * 32} {side * 3.3} {y})"/>')
            parts.append(f'<line x1="{side * 4.6}" y1="{y - 2.2}" x2="{side * 7.6}" y2="{y - 6}" stroke="#d7b04a" stroke-width="0.5"/>')
    parts.append('<ellipse cx="0" cy="-9.6" rx="1.9" ry="3.5" fill="#e8b830" stroke="#a77512" stroke-width="0.55"/>')
    parts.append('<line x1="0" y1="-12.8" x2="0" y2="-16" stroke="#d7b04a" stroke-width="0.5"/>')
    return "".join(parts)


def _detailed_bricks():
    rows = ((-9, (-11, 0, 11)), (-1, (-16.5, -5.5, 5.5, 16.5)), (7, (-11, 0, 11)))
    parts = []
    shades = ("#cf7455", "#c4634a", "#d98262")
    n = 0
    for y, xs in rows:
        for cx in xs:
            x0 = max(cx - 5.2, -12)
            x1 = min(cx + 5.2, 12)
            if x1 - x0 < 3:
                continue
            fill = shades[n % 3]
            n += 1
            parts.append(f'<rect x="{x0}" y="{y}" width="{x1 - x0}" height="6.4" rx="0.8" fill="{fill}" stroke="#7d3a26" stroke-width="0.7"/>')
            parts.append(f'<rect x="{x0 + 0.4}" y="{y + 0.4}" width="{x1 - x0 - 0.8}" height="1.3" rx="0.5" fill="#f0a085" opacity="0.65"/>')
    return "".join(parts)


def _detailed_rocks():
    return (
        '<ellipse cx="0" cy="11" rx="13" ry="2.2" fill="#000" opacity="0.25"/>'
        '<polygon points="-12.5,10.5 -13.5,3.5 -9,-1.5 -2,-1 1.5,5 1,10.5" fill="#7f8a96" stroke="#3f464e" stroke-width="0.9"/>'
        '<polygon points="-9,-1.5 -2,-1 -5.5,3.2" fill="#c6ced6"/><polygon points="-2,-1 1.5,5 1,10.5 -5.5,3.2" fill="#586370"/>'
        '<path d="M-8,5 l2.5,2 l-1,3" stroke="#3f464e" stroke-width="0.6" fill="none"/>'
        '<polygon points="-0.5,10.5 1,2 6,-6.5 12,-3.5 13.5,5 10.5,10.5" fill="#9aa5b0" stroke="#3f464e" stroke-width="0.9"/>'
        '<polygon points="1,2 6,-6.5 9.5,-4.2 5.5,1" fill="#d3dae1"/><polygon points="9.5,-4.2 12,-3.5 13.5,5 10.5,10.5 7,2" fill="#5f6a75"/>'
        '<polygon points="-5.5,-1 -4.2,-8.5 2,-12 7.5,-8.5 6.5,-2 1,1" fill="#adb7c1" stroke="#3f464e" stroke-width="0.9"/>'
        '<polygon points="-4.2,-8.5 2,-12 3.2,-7.6 -2,-4.2" fill="#e2e8ee"/><polygon points="3.2,-7.6 7.5,-8.5 6.5,-2 1,1 2.2,-4.4" fill="#6a7580"/>'
        '<circle cx="-7" cy="3" r="0.9" fill="#e8c35a"/><circle cx="8.8" cy="2" r="0.8" fill="#9fc6e8"/><circle cx="1.5" cy="-6" r="0.7" fill="#e8c35a"/>'
    )


DETAILED = {"W": _pile_flat(True), "S": _detailed_sheep(), "G": _detailed_wheat(), "C": _detailed_bricks(), "O": _detailed_rocks()}

# -------------------------------------------------------------------------------------- realistic


def _defs(prefix, items):
    return "".join(items).replace("PFX", prefix)


def _realistic_sheep():
    rng = random.Random("icon-sheep")
    curls = "".join(
        f'<path d="M{x},{y} q1.4,-1.6 2.8,0" stroke="#bdb9a8" stroke-width="0.5" fill="none" stroke-linecap="round"/>'
        for x, y in ((-9, 2), (-6, -4), (-1, -7), (4, -5), (7.5, 1), (-5, 5), (2, 6), (0, 1), (-2.5, -2), (4, 2))
    )
    wool = "".join(
        f'<circle cx="{x}" cy="{y}" r="{r}" fill="url(#ic-wool)"/>'
        for x, y, r in ((-8.5, 1.5, 4.7), (-5.5, -3.2, 5.3), (-0.5, -5.4, 5.7), (5, -3.6, 5.5), (7, 1.6, 4.7),
                        (-4.5, 4.6, 5.1), (2.5, 5, 5.3), (0, 0.4, 5.9))
    )
    legs = "".join(
        f'<rect x="{x}" y="6.6" width="2.3" height="6.3" rx="0.8" fill="url(#ic-leg)"/><rect x="{x}" y="11.5" width="2.3" height="1.5" rx="0.6" fill="#1d1a17"/>'
        for x in (-6.6, -2.8, 2.6, 6.4)
    )
    return (
        '<defs><radialGradient id="ic-wool" cx="0.35" cy="0.3" r="0.8"><stop offset="0" stop-color="#ffffff"/><stop offset="0.65" stop-color="#ecebe2"/>'
        '<stop offset="1" stop-color="#b8b5a6"/></radialGradient>'
        '<linearGradient id="ic-leg" x1="0" x2="1"><stop offset="0" stop-color="#5a5550"/><stop offset="1" stop-color="#2c2926"/></linearGradient>'
        '<radialGradient id="ic-face" cx="0.4" cy="0.35" r="0.8"><stop offset="0" stop-color="#6b635b"/><stop offset="1" stop-color="#26231f"/></radialGradient></defs>'
        '<ellipse cx="0.5" cy="13.2" rx="12.5" ry="2" fill="#000" opacity="0.28"/>'
        + legs + '<circle cx="-12" cy="0.5" r="2.3" fill="url(#ic-wool)"/>' + wool + curls +
        '<ellipse cx="0" cy="8" rx="9" ry="2" fill="#6a665a" opacity="0.18"/>'
        '<ellipse cx="12.2" cy="-2.7" rx="2.3" ry="1.2" fill="url(#ic-face)" transform="rotate(-30 12.2 -2.7)"/>'
        '<ellipse cx="11.2" cy="1.8" rx="3.7" ry="4.9" fill="url(#ic-face)"/>'
        '<ellipse cx="12.8" cy="4.3" rx="1.7" ry="1.2" fill="#8a8077"/><ellipse cx="13.2" cy="4" rx="0.4" ry="0.3" fill="#2c2926"/>'
        '<circle cx="12.1" cy="0.4" r="1" fill="#ffffff"/><circle cx="12.3" cy="0.4" r="0.5" fill="#0d0c0b"/><circle cx="12" cy="0.1" r="0.18" fill="#fff"/>'
        '<circle cx="9.2" cy="-2.3" r="2.3" fill="url(#ic-wool)"/>'
    )


def _realistic_wheat():
    parts = ['<defs><linearGradient id="ic-grain" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f6d56a"/><stop offset="0.6" stop-color="#e0a82a"/><stop offset="1" stop-color="#b87c14"/></linearGradient>'
             '<linearGradient id="ic-leaf" x1="0" x2="1"><stop offset="0" stop-color="#a9c95c"/><stop offset="1" stop-color="#5e8a2c"/></linearGradient></defs>',
             '<ellipse cx="1" cy="13" rx="6" ry="1.2" fill="#000" opacity="0.2"/>',
             '<path d="M0,13 Q0.8,4 0,-9" stroke="#a37312" stroke-width="2" fill="none" stroke-linecap="round"/>',
             '<path d="M0.4,9.5 Q7.5,6.5 10,1 Q5,3.5 0.4,6.5 Z" fill="url(#ic-leaf)"/>',
             '<path d="M-0.4,11.5 Q-7.5,8.5 -9.6,3.2 Q-4.8,5.6 -0.4,8.5 Z" fill="url(#ic-leaf)"/>']
    for y in (-6.4, -2.8, 0.8, 4.4):
        for side in (-1, 1):
            parts.append(f'<ellipse cx="{side * 3.4}" cy="{y}" rx="2" ry="3.5" fill="url(#ic-grain)" stroke="#8f5d0e" stroke-width="0.4" '
                         f'transform="rotate({side * 32} {side * 3.4} {y})"/>')
            parts.append(f'<line x1="{side * 4.8}" y1="{y - 2.4}" x2="{side * 8}" y2="{y - 6.4}" stroke="#e6c25a" stroke-width="0.45"/>')
            parts.append(f'<ellipse cx="{side * 3.0}" cy="{y - 0.6}" rx="0.5" ry="1.4" fill="#fff3b0" opacity="0.7" transform="rotate({side * 32} {side * 3.0} {y - 0.6})"/>')
    parts.append('<ellipse cx="0" cy="-10" rx="2" ry="3.7" fill="url(#ic-grain)" stroke="#8f5d0e" stroke-width="0.4"/>')
    parts.append('<line x1="0" y1="-13.3" x2="0" y2="-16.5" stroke="#e6c25a" stroke-width="0.45"/>')
    return "".join(parts)


def _realistic_bricks():
    rng = random.Random("icon-bricks")
    parts = ['<defs><linearGradient id="ic-brick" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e48b6c"/><stop offset="1" stop-color="#b9523a"/></linearGradient></defs>',
             '<ellipse cx="0.5" cy="11.6" rx="13" ry="1.8" fill="#000" opacity="0.25"/>']
    for y, xs in ((-9, (-11, 0, 11)), (-1, (-16.5, -5.5, 5.5, 16.5)), (7, (-11, 0, 11))):
        for cx in xs:
            x0, x1 = max(cx - 5.3, -12.2), min(cx + 5.3, 12.2)
            if x1 - x0 < 3:
                continue
            tone = rng.random() * 0.25
            parts.append(f'<rect x="{x0}" y="{y}" width="{x1 - x0}" height="6.5" rx="0.9" fill="url(#ic-brick)" stroke="#6f3322" stroke-width="0.6"/>')
            parts.append(f'<rect x="{x0}" y="{y}" width="{x1 - x0}" height="6.5" rx="0.9" fill="#3a1608" opacity="{tone:.2f}"/>')
            parts.append(f'<rect x="{x0 + 0.5}" y="{y + 0.4}" width="{x1 - x0 - 1}" height="1.2" rx="0.5" fill="#fff" opacity="0.28"/>')
            for _ in range(3):
                parts.append(f'<circle cx="{x0 + 1 + rng.random() * (x1 - x0 - 2):.1f}" cy="{y + 1.5 + rng.random() * 4:.1f}" r="0.28" fill="#5a2515" opacity="0.5"/>')
    return "".join(parts)


def _realistic_rocks():
    return (
        '<defs><linearGradient id="ic-r1" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#c3ccd5"/><stop offset="1" stop-color="#6a7580"/></linearGradient>'
        '<linearGradient id="ic-r2" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#dfe5eb"/><stop offset="1" stop-color="#7d8894"/></linearGradient></defs>'
        '<ellipse cx="0.5" cy="11.2" rx="14" ry="2.4" fill="#000" opacity="0.32"/>'
        '<polygon points="-12.5,10.5 -13.5,3.5 -9,-1.5 -2,-1 1.5,5 1,10.5" fill="url(#ic-r1)" stroke="#3a4149" stroke-width="0.8"/>'
        '<polygon points="-9,-1.5 -2,-1 -5.5,3.2" fill="#e9eef3" opacity="0.8"/><polygon points="-2,-1 1.5,5 1,10.5 -5.5,3.2" fill="#2c333b" opacity="0.5"/>'
        '<path d="M-8,5 l2.5,2 l-1,3 M-11,6 l1.5,1" stroke="#2c333b" stroke-width="0.5" fill="none"/>'
        '<polygon points="-0.5,10.5 1,2 6,-6.5 12,-3.5 13.5,5 10.5,10.5" fill="url(#ic-r2)" stroke="#3a4149" stroke-width="0.8"/>'
        '<polygon points="1,2 6,-6.5 9.5,-4.2 5.5,1" fill="#f1f5f8" opacity="0.85"/><polygon points="9.5,-4.2 12,-3.5 13.5,5 10.5,10.5 7,2" fill="#2c333b" opacity="0.45"/>'
        '<polygon points="-5.5,-1 -4.2,-8.5 2,-12 7.5,-8.5 6.5,-2 1,1" fill="url(#ic-r1)" stroke="#3a4149" stroke-width="0.8"/>'
        '<polygon points="-4.2,-8.5 2,-12 3.2,-7.6 -2,-4.2" fill="#f4f7fa" opacity="0.9"/><polygon points="3.2,-7.6 7.5,-8.5 6.5,-2 1,1 2.2,-4.4" fill="#2c333b" opacity="0.45"/>'
        '<circle cx="-7" cy="3" r="1" fill="#f0cc66"/><circle cx="-7.3" cy="2.7" r="0.35" fill="#fff6c8"/>'
        '<circle cx="8.8" cy="2" r="0.9" fill="#a8cdee"/><circle cx="1.5" cy="-6" r="0.8" fill="#f0cc66"/>'
        '<path d="M-1,10.5 q1.5,-1.4 3,0 M5,10.5 q1.5,-1.4 3,0" stroke="#7aa05a" stroke-width="0.7" fill="none"/>'
    )


def _split_defs(icons):
    """The icons without their gradient definitions, and the definitions gathered (to go inside one <defs>), so that a
    drawing holds each gradient once however many times the icons are used."""
    bodies, definitions = {}, []
    for kind, svg in icons.items():
        found = re.findall(r"<defs>(.*?)</defs>", svg, re.S)
        definitions.extend(found)
        bodies[kind] = re.sub(r"<defs>.*?</defs>", "", svg, flags=re.S)
    return bodies, "".join(definitions)


REALISTIC, REALISTIC_DEFS = _split_defs(
    {"W": _pile_realistic(), "S": _realistic_sheep(), "G": _realistic_wheat(), "C": _realistic_bricks(), "O": _realistic_rocks()}
)

ICON_SETS = {"simple": SIMPLE, "detailed": DETAILED, "realistic": REALISTIC}
ICON_DEFS = {"simple": "", "detailed": "", "realistic": REALISTIC_DEFS}
ICON_SET_NAMES = tuple(ICON_SETS)
DEFAULT_ICON_SET = "realistic"


def check_icon_set(name):
    """The name of an icon set (the default for None), or CatanMapError."""
    from .codec import CatanMapError

    name = DEFAULT_ICON_SET if name is None else name
    if name not in ICON_SETS:
        raise CatanMapError(f"unknown icon set {name!r}; the icon sets are {', '.join(ICON_SET_NAMES)}")
    return name
