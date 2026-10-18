"""Writing a board as a string, and reading one back.

A string has up to three parts, with no spaces:

* tiles    19 letters W O C S G D, row by row (3, 4, 5, 4, 3), left to right;
* tokens   18 symbols from 2345689abc (a = 10, b = 11, c = 12), in the same order,
           skipping the desert;
* ports    optional: an optional leading X (the ring is shifted by one), then 9 port
           symbols, clockwise from the top-left of the sea ring. See board.py.

Two layouts: "s" (sections) writes tiles, then tokens, then ports; "p" (paired) writes
every tile followed by its token (the desert has none), then the ports. With pipes, the
rows are separated by "|" and the parts by ",". The reader ignores "|" and ",", and finds
the layout by itself.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .board import (
    DEFAULT_PORTS,
    DESERT,
    PORT_COUNT,
    PORT_KIND_COUNTS,
    PORT_SYMBOLS,
    ROWS,
    THREE_TO_ONE,
    TILE_COUNT,
    TILE_COUNTS,
    TILE_LETTERS,
    TOKEN_CHARS,
    TOKEN_COUNTS,
    adjacent_low_high_pairs,
    adjacent_red_pairs,
    describe_tile,
    is_corner_slot,
)


class CatanMapError(ValueError):
    """Base class for every error this package raises on bad input."""


class CodecError(CatanMapError):
    """A string that cannot be read; the message says where."""


@dataclass(frozen=True)
class Port:
    kind: str       # "3" for a 3:1 port, or the resource letter of a 2:1 port
    forward: bool   # which of the two island tiles it attaches to (see board.py)


@dataclass(frozen=True)
class Ports:
    entries: Tuple[Port, ...]
    shifted: bool = False

    def __post_init__(self):
        # A port on a corner sea tile has only one way to attach, so its orientation
        # carries no information: keep it in one form, so equal boards compare equal.
        entries = tuple(
            Port(port.kind, False) if is_corner_slot(slot, self.shifted) else port
            for slot, port in enumerate(self.entries)
        )
        object.__setattr__(self, "entries", entries)


@dataclass(frozen=True)
class Board:
    tiles: Tuple[str, ...]                    # 19 letters
    tokens: Tuple[Optional[str], ...]         # 19 entries: a token symbol, or None for the desert
    ports: Optional[Ports] = None             # None: the string had no ports part (default implied)

    def effective_ports(self):
        """The ports of the board: the ones it has, or the default arrangement."""
        return self.ports if self.ports is not None else default_ports()


@dataclass(frozen=True)
class Parsed:
    board: Board
    format: str                  # "s" or "p"
    warnings: Tuple[str, ...]    # things that are allowed but odd, such as touching 6 and 8


# ----------------------------------------------------------------------------- ports


def port_to_symbol(port):
    if port.kind == THREE_TO_ONE:
        return "#" if port.forward else "3"
    return port.kind.upper() if port.forward else port.kind.lower()


def port_from_symbol(symbol):
    if symbol == "3":
        return Port(THREE_TO_ONE, False)
    if symbol == "#":
        return Port(THREE_TO_ONE, True)
    return Port(symbol.upper(), symbol.isupper())


def ports_to_text(ports):
    return ("X" if ports.shifted else "") + "".join(port_to_symbol(p) for p in ports.entries)


def default_ports():
    return Ports(tuple(port_from_symbol(s) for s in DEFAULT_PORTS), False)


# -------------------------------------------------------------------------- writing


def _split_rows(items):
    rows, start = [], 0
    for length in ROWS:
        rows.append(items[start:start + length])
        start += length
    return rows


def serialize(board, fmt="s", pipes=False, include_ports=False):
    """The board as a string. `fmt` is "s" or "p"; with `pipes` the rows are separated by
    "|" and the parts by ",". With `include_ports` the ports part is written (the default
    arrangement if the board has none)."""
    if fmt not in ("s", "p"):
        raise ValueError(f"fmt must be 's' or 'p', not {fmt!r}")
    row_separator, part_separator = ("|", ",") if pipes else ("", "")

    tile_rows = _split_rows(board.tiles)
    token_rows = _split_rows(board.tokens)
    if fmt == "s":
        parts = [
            row_separator.join("".join(row) for row in tile_rows),
            row_separator.join("".join(t for t in row if t is not None) for row in token_rows),
        ]
    else:
        parts = [
            row_separator.join(
                "".join(tile + (token or "") for tile, token in zip(tiles, tokens))
                for tiles, tokens in zip(tile_rows, token_rows)
            )
        ]
    if include_ports:
        parts.append(ports_to_text(board.effective_ports()))
    return part_separator.join(parts)


# -------------------------------------------------------------------------- reading


def _token_error(char, position):
    hint = ""
    if char.isalpha() and char.lower() in "abc" and char.isupper():
        hint = " (the token letters a, b and c are lowercase)"
    return CodecError(
        f"character {position}: {char!r} is not a token; the tokens are 2 3 4 5 6 8 9 "
        f"and a b c for 10, 11, 12{hint}"
    )


def _tile_count_warnings(tiles):
    """Messages for a tile mix that is not the standard one (it is allowed, with a warning)."""
    problems = []
    for letter, wanted in TILE_COUNTS.items():
        found = tiles.count(letter)
        if found != wanted:
            problems.append(f"expected {wanted} {letter} but found {found}")
    return ["unusual tiles: " + "; ".join(problems)] if problems else []


def _token_count_warnings(tokens):
    problems = []
    real = [t for t in tokens if t is not None]
    for symbol, wanted in TOKEN_COUNTS.items():
        found = real.count(symbol)
        if found != wanted:
            problems.append(f"expected {wanted} of {symbol} but found {found}")
    return ["unusual tokens: " + "; ".join(problems)] if problems else []


def _read_ports(rest):
    """`rest` is a list of (character, position). Returns (Ports or None when empty, warnings)."""
    if not rest:
        return None, []
    shifted = rest[0][0] == "X"
    symbols = rest[1:] if shifted else rest
    for char, position in symbols:
        if char == "X":
            raise CodecError(f"character {position}: X is only allowed at the start of the ports part")
        if char not in PORT_SYMBOLS:
            raise CodecError(
                f"character {position}: {char!r} is not a port symbol; the symbols are "
                f"W O C S G (forward) or w o c s g (backward), 3 (3:1) and # (3:1 forward)"
            )
    if len(symbols) != PORT_COUNT:
        raise CodecError(
            f"ports: expected {PORT_COUNT} port symbols{' after the X' if shifted else ''} "
            f"but found {len(symbols)}"
        )
    ports = Ports(tuple(port_from_symbol(char) for char, _ in symbols), shifted)
    found = {}
    for port in ports.entries:
        found[port.kind] = found.get(port.kind, 0) + 1
    warnings = []
    if found != PORT_KIND_COUNTS:
        warnings.append(
            "unusual ports: the standard set is four 3:1 ports and one 2:1 port for each of W, O, C, S, G; "
            f"found {dict(sorted(found.items()))}"
        )
    return ports, warnings


def parse(text):
    """Reads a string in either layout, with or without "|" and "," separators.
    Raises CodecError, naming the character, when it cannot. Returns a Parsed."""
    if not isinstance(text, str):
        raise CodecError("the map must be given as text")
    text = text.strip()
    if not text:
        raise CodecError("the string is empty")

    chars = []   # (character, 1-based position in the text), separators removed
    for position, char in enumerate(text, start=1):
        if char in "|,":
            continue
        if char.isspace():
            raise CodecError(f"character {position}: spaces are not allowed inside the string")
        chars.append((char, position))

    if not chars:
        raise CodecError("the string is empty (it has only separators)")

    if len(chars) >= TILE_COUNT and all(c in TILE_LETTERS for c, _ in chars[:TILE_COUNT]):
        fmt = "s"
        tiles = [c for c, _ in chars[:TILE_COUNT]]
        wanted_tokens = TILE_COUNT - tiles.count(DESERT)
        end = TILE_COUNT + wanted_tokens
        if len(chars) < end:
            raise CodecError(
                f"too short: the {TILE_COUNT} tiles and {wanted_tokens} tokens need {end} "
                f"characters, found {len(chars)}"
            )
        token_chars = chars[TILE_COUNT:end]
        for char, position in token_chars:
            if char not in TOKEN_CHARS:
                raise _token_error(char, position)
        token_iter = iter(c for c, _ in token_chars)
        tokens = [None if t == DESERT else next(token_iter) for t in tiles]
        rest = chars[end:]
    else:
        fmt = "p"
        tiles, tokens, index = [], [], 0
        while len(tiles) < TILE_COUNT:
            if index >= len(chars):
                raise CodecError(
                    f"the string ends too early: tile {len(tiles) + 1} of {TILE_COUNT} is missing"
                )
            char, position = chars[index]
            if char not in TILE_LETTERS:
                raise CodecError(
                    f"character {position}: expected a tile letter (W O C S G D), found {char!r}"
                )
            tiles.append(char)
            index += 1
            if char == DESERT:
                tokens.append(None)
                continue
            if index >= len(chars):
                raise CodecError(f"character {position}: the tile {char} needs a token after it")
            token, token_position = chars[index]
            if token not in TOKEN_CHARS:
                raise _token_error(token, token_position)
            tokens.append(token)
            index += 1
        rest = chars[index:]

    ports, port_warnings = _read_ports(rest)
    board = Board(tuple(tiles), tuple(tokens), ports)

    warnings = (
        _tile_count_warnings(tiles)
        + _token_count_warnings(tokens)
        + port_warnings
        + [
            f"the {tokens[i]} at {describe_tile(i)} touches the {tokens[j]} at {describe_tile(j)}"
            for i, j in adjacent_red_pairs(board.tokens) + adjacent_low_high_pairs(board.tokens)
        ]
    )
    return Parsed(board, fmt, tuple(warnings))
