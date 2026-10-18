"""Seed codes.

A seed is letters only (A-Z), case-insensitive, 1 to 32 letters. A *seed code* is a seed plus
the options that are not the default, after a "-", so that the code alone reproduces a
whole string::

    KMQXRT            all defaults (the desert in the center)
    KMQXRT-F          the desert anywhere                         (F, E, I, C or R: one of them)
    KMQXRT-E          the desert may only be on the edge
    KMQXRT-A          adjacent 6 and 8 allowed
    KMQXRT-P          the string includes the ports
    KMQXRT-RAP        several: the desert letter, then A, then P

Each flag letter means one thing and appears at most once, so when a code is read the order
of the flags does not matter, and when it is written the order is always the one above.
"""
from __future__ import annotations

import secrets
import string
from dataclasses import dataclass
from typing import Optional

from .codec import CatanMapError

SEED_LENGTH = 3
MAX_SEED_LENGTH = 32

# desert zone <-> its flag letter
# "center" is the default, so its flag changes nothing and is not written back
DESERT_FLAGS = {"free": "F", "edge": "E", "inner": "I", "center": "C", "ring": "R"}
DEFAULT_DESERT = "center"
_FLAG_DESERT = {letter: zone for zone, letter in DESERT_FLAGS.items()}
ADJACENT_FLAG = "A"
PORTS_FLAG = "P"
_DESERT_PHRASES = {
    "free": "anywhere (F)",
    "edge": "on the edge (E)",
    "inner": "inside, off the edge (I)",
    "center": "in the center (C)",
    "ring": "in the ring around the center (R)",
}


class SeedError(CatanMapError):
    """A seed code that cannot be used, or options that contradict it."""


@dataclass(frozen=True)
class SeedCode:
    seed: str                                # uppercase letters
    desert: Optional[str] = None             # None means the default (the center), else a zone name
    allow_adjacent_red: bool = False
    ports: bool = False

    def __str__(self):
        return format_seed_code(self)


def normalize_seed(text):
    """The seed in its one form (uppercase), or SeedError."""
    seed = (text or "").strip()
    if not seed:
        raise SeedError("the seed is empty")
    if len(seed) > MAX_SEED_LENGTH:
        raise SeedError(f"the seed is too long: {len(seed)} letters, at most {MAX_SEED_LENGTH}")
    for char in seed:
        if not (char.isascii() and char.isalpha()):
            hint = " (seeds are letters only, no digits)" if char.isdigit() else ""
            raise SeedError(f"the seed may contain only the letters A-Z, found {char!r}{hint}")
    return seed.upper()


def parse_seed_code(text):
    """Reads "SEED" or "SEED-FLAGS"."""
    text = (text or "").strip()
    seed_text, dash, flag_text = text.partition("-")
    seed = normalize_seed(seed_text)
    if not dash:
        return SeedCode(seed)

    flags = flag_text.upper()
    if not flags:
        raise SeedError("there is nothing after the '-' in the seed code")
    desert, adjacent, ports = None, False, False
    seen = set()
    for letter in flags:
        if letter in seen:
            raise SeedError(f"the flag {letter} appears twice in the seed code")
        seen.add(letter)
        if letter in _FLAG_DESERT:
            if desert is not None:
                raise SeedError(
                    f"only one desert flag is allowed (F, E, I, C or R), found {DESERT_FLAGS[desert]} and {letter}"
                )
            desert = _FLAG_DESERT[letter]
        elif letter == ADJACENT_FLAG:
            adjacent = True
        elif letter == PORTS_FLAG:
            ports = True
        else:
            raise SeedError(
                f"unknown flag {letter!r} in the seed code; the flags are F, E, I, C, R (desert), A and P"
            )
    return SeedCode(seed, desert, adjacent, ports)


def format_seed_code(code):
    """The code in its one written form: the seed, then the desert letter (none for the
    default, the center), A and P."""
    flags = ""
    if code.desert not in (None, DEFAULT_DESERT):
        flags += DESERT_FLAGS[code.desert]
    if code.allow_adjacent_red:
        flags += ADJACENT_FLAG
    if code.ports:
        flags += PORTS_FLAG
    return code.seed + ("-" + flags if flags else "")


def random_seed(length=SEED_LENGTH):
    """A random seed of `length` different letters (3 by default: 15,600 seeds)."""
    if length > len(string.ascii_uppercase):
        raise ValueError(f"a seed of different letters has at most {len(string.ascii_uppercase)} letters")
    return "".join(secrets.SystemRandom().sample(string.ascii_uppercase, length))


def combine(code, desert=None, allow_adjacent_red=False, ports=False):
    """The seed code together with options given separately (for instance on the command
    line). An option may *add* something the code does not say, but it may not *change* what
    the code says: that raises SeedError.

    `desert` is None (not given) or a zone name ("free", "edge", "inner", "center", "ring"). A
    code without a desert letter says nothing about the desert, so the default (the center) applies. `allow_adjacent_red` and `ports` can only be switched on, so
    they cannot contradict a code."""
    if code.desert is not None and desert is not None and desert != code.desert:
        raise SeedError(
            f"the seed code says the desert is {_DESERT_PHRASES[code.desert]}, "
            f"but the desert option {desert!r} was given"
        )
    final_desert = code.desert
    if final_desert is None and desert is not None:
        final_desert = desert
    return SeedCode(
        code.seed,
        final_desert,
        code.allow_adjacent_red or allow_adjacent_red,
        code.ports or ports,
    )
