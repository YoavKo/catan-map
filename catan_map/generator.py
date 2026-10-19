"""The seeded board generator.

A seed always gives the same board, on any Python version: the only thing taken from the
`random` module is `Random.random()`, whose sequence Python guarantees for a given seed. The
shuffle is written out here (Fisher-Yates) instead of using `random.shuffle`, whose algorithm
Python is free to change.

The draws are made in a fixed order, and the ports come last, so asking for ports never
changes the tiles or the tokens of a seed:

1. the desert's position, chosen among the tiles the desert option allows, then the other
   18 tiles are shuffled over the remaining positions; with no_same_neighbours they are
   placed one by one instead, each from the terrains that do not match a neighbour already
   placed (a shuffle that has no matching neighbours is too rare to wait for: about 1 in
   1,300 with the desert in the center, 1 in 4,000 on the edge);
2. the tokens, shuffled over the 18 non-desert tiles; unless adjacent red numbers are
   allowed, they are shuffled again (the same stream, at most MAX_ATTEMPTS times) until no
   6 or 8 touches another 6 or 8; the 2 and the 12 do not touch each other either, unless
   allow_adjacent_low_high;
3. the ports, only when asked for: whether the ring is shifted, a shuffle of the nine port
   types, then the orientation of every port that is not on a corner.
"""
from __future__ import annotations

import hashlib
import random

from .board import (
    DESERT,
    DESERT_ZONES,
    PORT_COUNT,
    PORT_KIND_COUNTS,
    RESOURCES,
    TILE_COUNT,
    TILE_COUNTS,
    TOKEN_CHARS,
    TOKEN_COUNTS,
    NEIGHBOURS,
    adjacent_low_high_pairs,
    adjacent_red_pairs,
    is_corner_slot,
)
from .codec import Board, CatanMapError, Port, Ports
from .seed import DEFAULT_DESERT, SeedCode, normalize_seed

ALGORITHM = "catan-map-v1"
MAX_ATTEMPTS = 10_000


class GenerationError(CatanMapError):
    pass


class Stream:
    """The random numbers of one seed."""

    def __init__(self, seed):
        number = int.from_bytes(hashlib.sha256(f"{ALGORITHM}:{seed}".encode()).digest(), "big")
        self._random = random.Random(number).random

    def shuffle(self, items):
        """Fisher-Yates, in place, from the end."""
        for i in range(len(items) - 1, 0, -1):
            j = int(self._random() * (i + 1))
            items[i], items[j] = items[j], items[i]

    def pick(self, items):
        return items[int(self._random() * len(items))]

    def chance(self):
        """True or False with equal probability."""
        return self._random() < 0.5


def _place_unlike(stream, desert):
    """The 18 resource tiles placed one by one so that no two neighbours match, or None if
    the search gives up. Each place takes, at random, one of the terrains that are left and do
    not match a neighbour already placed; when none is possible it goes back (depth first), so
    it only fails if there is no arrangement, which does not happen on this board."""
    positions = [i for i in range(TILE_COUNT) if i != desert]
    counts = {letter: TILE_COUNTS[letter] for letter in RESOURCES}
    placed = {}
    steps = 0

    def candidates(i):
        taken = {placed[j] for j in NEIGHBOURS[i] if j in placed}
        options = [letter for letter in RESOURCES if counts[letter] > 0 and letter not in taken]
        stream.shuffle(options)
        return options

    stack = [(0, candidates(positions[0]))]
    while stack:
        index, options = stack[-1]
        position = positions[index]
        if position in placed:                     # going back: take the tile off this place
            counts[placed.pop(position)] += 1
        if not options:
            stack.pop()
            continue
        letter = options.pop()
        placed[position] = letter
        counts[letter] -= 1
        if index + 1 == len(positions):
            return placed
        steps += 1
        if steps > MAX_ATTEMPTS * 10:
            return None
        stack.append((index + 1, candidates(positions[index + 1])))
    return None


def _generate_tiles(stream, zone, no_same_neighbours=False):
    allowed = sorted(DESERT_ZONES[zone])
    desert = stream.pick(allowed)
    if no_same_neighbours:
        placed = _place_unlike(stream, desert)
        if placed is None:
            raise GenerationError("no arrangement without neighbouring tiles of the same terrain was found")
        return tuple(DESERT if i == desert else placed[i] for i in range(TILE_COUNT)), desert
    resources = [letter for letter in RESOURCES for _ in range(TILE_COUNTS[letter])]   # 18 letters
    stream.shuffle(resources)
    letters = iter(resources)
    return tuple(DESERT if i == desert else next(letters) for i in range(TILE_COUNT)), desert


def _generate_tokens(stream, desert, allow_adjacent_red, allow_adjacent_low_high=False):
    symbols = [symbol for symbol in TOKEN_CHARS for _ in range(TOKEN_COUNTS[symbol])]   # 18 symbols
    for _ in range(MAX_ATTEMPTS):
        stream.shuffle(symbols)
        iterator = iter(symbols)
        tokens = tuple(None if i == desert else next(iterator) for i in range(TILE_COUNT))
        if (allow_adjacent_red or not adjacent_red_pairs(tokens)) and (
            allow_adjacent_low_high or not adjacent_low_high_pairs(tokens)
        ):
            return tokens
    raise GenerationError(f"no arrangement without touching 6 and 8 (or 2 and 12) found in {MAX_ATTEMPTS} attempts")


def _generate_ports(stream):
    shifted = stream.chance()
    kinds = [kind for kind, count in PORT_KIND_COUNTS.items() for _ in range(count)]    # 9 kinds
    assert len(kinds) == PORT_COUNT
    stream.shuffle(kinds)
    entries = []
    for slot, kind in enumerate(kinds):
        forward = False if is_corner_slot(slot, shifted) else stream.chance()
        entries.append(Port(kind, forward))
    return Ports(tuple(entries), shifted)


def generate(code, desert=None, allow_adjacent_red=False, ports=False, allow_adjacent_low_high=False,
             no_same_neighbours=False):
    """The board of a seed. `code` is a SeedCode, or a seed as text (letters only); in the
    second case the options are given as arguments, in the first case they come from the code.
    `desert` is None (the default, the center), "free", "edge", "inner", "center" or "ring".
    `allow_adjacent_low_high` lets the 2 and the 12 touch; `no_same_neighbours` keeps any two
    neighbouring tiles from having the same terrain."""
    if not isinstance(code, SeedCode):
        code = SeedCode(
            normalize_seed(code),
            desert,
            allow_adjacent_red,
            ports,
            allow_adjacent_low_high,
            no_same_neighbours,
        )
    zone = code.desert or DEFAULT_DESERT
    if zone not in DESERT_ZONES:
        raise GenerationError(f"unknown desert option {zone!r}")

    stream = Stream(code.seed)
    tiles, desert_tile = _generate_tiles(stream, zone, code.no_same_neighbours)
    tokens = _generate_tokens(stream, desert_tile, code.allow_adjacent_red, code.allow_adjacent_low_high)
    board_ports = _generate_ports(stream) if code.ports else None
    return Board(tiles, tokens, board_ports)
