"""Balance analysis of a board. It only reads the board: it never takes part in making one.

``analyze(board)`` returns a plain dict (see README or docs); lower ``score`` is more balanced.
"""
from __future__ import annotations

import math
from itertools import combinations

from .board import (
    CENTER_TILE,
    DESERT,
    INNER_TILES,
    LOW_HIGH_TOKENS,
    NEIGHBOURS,
    RED_TOKENS,
    RESOURCES,
    TILE_POSITIONS,
    TILE_ROW_COL,
    TOKEN_VALUES,
)

PIPS = {2: 1, 12: 1, 3: 2, 11: 2, 4: 3, 10: 3, 5: 4, 9: 4, 6: 5, 8: 5}
TOTAL_PIPS = 58
TILES = 19
LAND_TILES = 18
RESOURCE_ORDER = "WSGCO"   # the order of the output
BALANCED_MAX = 30.0
OK_MAX = 45.0
VERTEX_LIMIT = 12

# axial directions, in the order the reference uses
_DIRS = ((1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1))
_SQRT3 = math.sqrt(3)

# axial (q, r) of every tile: r is the row from the middle, x = 2q + r
_AXIAL = tuple(((x - (row - 2)) // 2, row - 2) for row, x in TILE_POSITIONS)
_INDEX = {axial: i for i, axial in enumerate(_AXIAL)}


def _centre(axial):
    q, r = axial
    return _SQRT3 * (q + r / 2), 1.5 * r


def _corners():
    """Every corner touching a land tile: a frozenset of up to 3 axial hexagons (some off the board)."""
    found = {}
    for p in _AXIAL:
        for i in range(6):
            a, b = _DIRS[i], _DIRS[(i + 1) % 6]
            corner = frozenset({p, (p[0] + a[0], p[1] + a[1]), (p[0] + b[0], p[1] + b[1])})
            found.setdefault(corner, None)
    return tuple(found)


_CORNERS = _corners()
_CORNER_TILES = tuple(tuple(sorted(_INDEX[h] for h in corner if h in _INDEX)) for corner in _CORNERS)
_CORNER_POINT = tuple(
    tuple(sum(c) / 3 for c in zip(*(_centre(h) for h in corner))) for corner in _CORNERS
)
_CORNER_SECTOR = tuple(
    int(math.floor(round(math.degrees(math.atan2(y, x)) % 360, 6) / 60)) % 6 for x, y in _CORNER_POINT
)
_NEAR_CENTRE = frozenset(INNER_TILES | {CENTER_TILE}) & frozenset(
    i for i, (q, r) in enumerate(_AXIAL) if max(abs(q), abs(r), abs(q + r)) <= 1
)


def _label(score, passes):
    if passes and score <= BALANCED_MAX:
        return "balanced"
    if passes and score <= OK_MAX:
        return "ok"
    return "unbalanced"


def analyze(board):
    """The balance of `board` as a dict. See the module docstring."""
    tiles, tokens = board.tiles, board.tokens
    number = [TOKEN_VALUES[t] if t is not None else None for t in tokens]
    pips_of = [PIPS[n] if n is not None else 0 for n in number]
    land = [i for i in range(TILES) if tiles[i] != DESERT]

    violations = []
    penalty = 0.0
    equal_pairs = 0

    # neighbouring pairs, each counted once
    low_high_touch = False
    red_touch = False
    same_terrain = 0
    for i in range(TILES):
        for j in NEIGHBOURS[i]:
            if j <= i:
                continue
            a, b = tokens[i], tokens[j]
            if a is not None and b is not None:
                if a in RED_TOKENS and b in RED_TOKENS:
                    red_touch = True
                elif a == b:
                    equal_pairs += 1
                    penalty += 5
                elif {a, b} == set(LOW_HIGH_TOKENS):
                    low_high_touch = True
            if tiles[i] == tiles[j] != DESERT:
                same_terrain += 1
                penalty += 3
    if red_touch:
        violations.append("6/8")
    if low_high_touch:
        violations.append("2-12")
    if any(
        sum(tiles[j] == tiles[i] for j in NEIGHBOURS[i]) >= 2 for i in land
    ):
        violations.append("clump")

    corner_pips = [sum(pips_of[t] for t in ts) for ts in _CORNER_TILES]
    if any(p > VERTEX_LIMIT for p in corner_pips):
        violations.append("vertex")
    penalty += 3 * sum(1 for p in corner_pips if p == VERTEX_LIMIT)

    reds = {r: sum(1 for i in range(TILES) if tiles[i] == r and tokens[i] in RED_TOKENS) for r in RESOURCES}
    if any(n >= 3 for n in reds.values()):
        violations.append("reds")

    counts = {r: sum(1 for t in tiles if t == r) for r in RESOURCES}
    pips = {r: sum(pips_of[i] for i in range(TILES) if tiles[i] == r) for r in RESOURCES}
    fair = {r: TOTAL_PIPS * counts[r] / LAND_TILES for r in RESOURCES}
    penalty += sum(2 * abs(pips[r] - fair[r]) for r in RESOURCES)

    score = round(penalty + 1e-9, 1)
    passes = not violations
    deviations = [pips[r] - fair[r] for r in RESOURCES]
    std = math.sqrt(sum(d * d for d in deviations) / len(deviations))

    order = sorted(range(len(_CORNERS)), key=lambda k: -corner_pips[k])
    best = order[0]
    ge10 = [k for k in range(len(_CORNERS)) if corner_pips[k] >= 10]
    top5 = order[:5]
    distances = [
        math.dist(_CORNER_POINT[a], _CORNER_POINT[b]) for a, b in combinations(top5, 2)
    ]

    return {
        "score": score,
        "passes_hard": passes,
        "label": _label(score, passes),
        "violations": violations,
        "equal_pairs": equal_pairs,
        "pips": {r: pips[r] for r in RESOURCE_ORDER},
        "fair_share": {r: round(fair[r], 2) for r in RESOURCE_ORDER},
        "pip_spread": max(pips.values()) - min(pips.values()),
        "pip_std_vs_fair": round(std, 2),
        "best_vertex": {"pips": corner_pips[best], "tiles": [list(TILE_ROW_COL[t]) for t in _CORNER_TILES[best]]},
        "vertices_ge10": len(ge10),
        "vertices_ge11": sum(1 for k in ge10 if corner_pips[k] >= 11),
        "top5_vertices": [corner_pips[k] for k in top5],
        "sectors_with_ge10": len({_CORNER_SECTOR[k] for k in ge10}),
        "ge10_inner": sum(1 for k in ge10 if sum(t in _NEAR_CENTRE for t in _CORNER_TILES[k]) >= 2),
        "ge10_outer": sum(1 for k in ge10 if sum(t in _NEAR_CENTRE for t in _CORNER_TILES[k]) < 2),
        "top5_mean_dist": round(sum(distances) / len(distances), 2),
    }
