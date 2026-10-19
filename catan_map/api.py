"""One call that does what the command line does: a board from a seed or from a string, and
its text. The command line and the website both use it."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .codec import Board, CatanMapError, parse, serialize
from .generator import generate
from .seed import SeedCode, combine, parse_seed_code, random_seed

FORMATS = {"s": "s", "sections": "s", "p": "p", "paired": "p"}


@dataclass(frozen=True)
class Made:
    board: Board
    code: Optional[SeedCode]        # the seed code, or None when the board was read from a string
    text: str                       # the board as a string, in the format asked for
    warnings: Tuple[str, ...]       # things that are allowed but odd (touching 6 and 8, an unusual mix...)

    @property
    def caption(self):
        """The lines that go under a drawing: the seed code (if any) and the string."""
        return ((str(self.code),) if self.code else ()) + (self.text,)


def make(seed=None, string=None, desert=None, allow_adjacent_red=False, ports=False, fmt="p", pipes=True,
         allow_adjacent_low_high=False, no_same_neighbours=False):
    """A board from a seed code (letters, optionally with -FLAGS), from a string, or, with
    neither, from a new random seed. `desert` is None, "free", "edge", "inner", "center" or
    "ring"; `allow_adjacent_low_high` lets the 2 and 12 touch, `no_same_neighbours` keeps neighbouring
    tiles of one terrain apart; the options may add to a seed code but not change it (SeedError if they do).
    `fmt` is "p" (paired) or "s" (sections), `pipes` writes the | and , separators.
    Raises CatanMapError (a ValueError) for anything it cannot use."""
    if fmt not in FORMATS:
        raise CatanMapError(f"the format must be one of {', '.join(sorted(FORMATS))}, not {fmt!r}")
    fmt = FORMATS[fmt]
    if seed is not None and string is not None:
        raise CatanMapError("give a seed or a string, not both")
    if string is not None:
        if desert is not None or allow_adjacent_red or allow_adjacent_low_high or no_same_neighbours:
            raise CatanMapError(
                "--desert, --allow-adjacent-red, --allow-adjacent-2-12 and --no-same-neighbours only apply "
                "when a board is made from a seed, not with --string"
            )
        parsed = parse(string)
        board = parsed.board
        include_ports = board.ports is not None or ports
        return Made(board, None, serialize(board, fmt, pipes, include_ports), parsed.warnings)
    code = parse_seed_code(seed) if seed is not None else SeedCode(random_seed())
    code = combine(
        code, desert=desert, allow_adjacent_red=allow_adjacent_red, ports=ports,
        allow_adjacent_low_high=allow_adjacent_low_high, no_same_neighbours=no_same_neighbours,
    )
    board = generate(code)
    return Made(board, code, serialize(board, fmt, pipes, code.ports), ())
