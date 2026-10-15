"""The seeded board generator.

A seed always gives the same board, on any Python version: the only thing taken from the
`random` module is `Random.random()`, whose sequence Python guarantees for a given seed. The
shuffle is written out here (Fisher-Yates) instead of using `random.shuffle`, whose algorithm
Python is free to change.

The draws are made in a fixed order, and the ports come last, so asking for ports never
changes the tiles or the tokens of a seed:

1. the desert's position, chosen among the tiles the desert option allows, then the other
   18 tiles are shuffled over the remaining positions;
2. the tokens, shuffled over the 18 non-desert tiles; unless adjacent red numbers are
   allowed, they are shuffled again (the same stream, at most MAX_ATTEMPTS times) until no
   6 or 8 touches another 6 or 8;
3. the ports, only when asked for: whether the ring is shifted, a shuffle of the nine port
   types, then the orientation of every port that is not on a corner. Afterwards the ports are
   moved off the desert if needed (a port that would attach to it switches orientation; if a
   corner port would, the ring is shifted), which draws nothing more, so the number of draws
   never depends on where the desert is.
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
    adjacent_red_pairs,
    is_corner_slot,
)
from .codec import Board, CatanMapError, Port, Ports, avoid_desert
from .seed import SeedCode, normalize_seed

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


def _generate_tiles(stream, zone):
    allowed = sorted(DESERT_ZONES[zone])
    desert = stream.pick(allowed)
    resources = [letter for letter in RESOURCES for _ in range(TILE_COUNTS[letter])]   # 18 letters
    stream.shuffle(resources)
    letters = iter(resources)
    return tuple(DESERT if i == desert else next(letters) for i in range(TILE_COUNT)), desert


def _generate_tokens(stream, desert, allow_adjacent_red):
    symbols = [symbol for symbol in TOKEN_CHARS for _ in range(TOKEN_COUNTS[symbol])]   # 18 symbols
    for _ in range(MAX_ATTEMPTS):
        stream.shuffle(symbols)
        iterator = iter(symbols)
        tokens = tuple(None if i == desert else next(iterator) for i in range(TILE_COUNT))
        if allow_adjacent_red or not adjacent_red_pairs(tokens):
            return tokens
    raise GenerationError(f"no arrangement without touching 6 and 8 found in {MAX_ATTEMPTS} attempts")


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


def generate(code, desert=None, allow_adjacent_red=False, ports=False):
    """The board of a seed. `code` is a SeedCode, or a seed as text (letters only); in the
    second case the options are given as arguments, in the first case they come from the code.
    `desert` is "free" (or None), "edge", "inner", "center" or "ring"."""
    if not isinstance(code, SeedCode):
        code = SeedCode(
            normalize_seed(code),
            None if desert in (None, "free") else desert,
            allow_adjacent_red,
            ports,
        )
    zone = code.desert or "free"
    if zone not in DESERT_ZONES:
        raise GenerationError(f"unknown desert option {zone!r}")

    stream = Stream(code.seed)
    tiles, desert_tile = _generate_tiles(stream, zone)
    tokens = _generate_tokens(stream, desert_tile, code.allow_adjacent_red)
    board_ports = avoid_desert(_generate_ports(stream), desert_tile) if code.ports else None
    return Board(tiles, tokens, board_ports)
