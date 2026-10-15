"""The command line: ``python -m catan_map`` or the ``catan-map`` command.

    catan-map                         a random seed: prints the seed and the string
    catan-map --seed KMQXRT           the same seed always gives the same board
    catan-map --string "WSG..."       read a string instead of using a seed
"""
from __future__ import annotations

import argparse
import sys

from .board import DESERT_ZONES
from .codec import CatanMapError, parse, serialize
from .generator import generate
from .render_text import UNICODE_ARROWS, render_board
from .seed import SeedCode, combine, parse_seed_code, random_seed

FORMATS = {"s": "s", "sections": "s", "p": "p", "paired": "p"}


def build_parser():
    parser = argparse.ArgumentParser(
        prog="catan-map",
        description="Make a random, reproducible Settlers of Catan board from a seed, write it as a "
        "short string, read such a string back, and draw it in the console.",
        epilog="Exit codes: 0 done, 2 bad input (the reason is printed to stderr).",
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--seed", metavar="CODE",
        help="the seed code: letters only, case-insensitive, optionally followed by -FLAGS "
        "(E I C R for the desert, A for adjacent 6/8, P for ports), for example KMQXRT-EP. "
        "Without --seed and --string a random 6-letter seed is made",
    )
    source.add_argument("--string", metavar="STR", help="read this string (either layout, with or without | and ,)")
    parser.add_argument(
        "--format", choices=sorted(FORMATS), default="s", metavar="s|p",
        help="s (sections: tiles, tokens, ports) or p (paired: each tile followed by its token); "
        "sections and paired also work (default s)",
    )
    parser.add_argument("--pipes", action="store_true", help="separate the rows with | and the parts with ,")
    parser.add_argument(
        "--ports", action="store_true",
        help="include the ports part: random ports when making a board from a seed; the default "
        "ports when reading a string that has none (a string that has ports always keeps them). "
        "A port never attaches to the desert: the default ports are moved off it if needed",
    )
    parser.add_argument("--board", action="store_true", help="draw the board in the console")
    parser.add_argument("--color", action="store_true", help="colours in the drawing")
    parser.add_argument("--ascii", action="store_true", help="draw with plain ASCII characters only")
    parser.add_argument(
        "--desert", choices=list(DESERT_ZONES), metavar="free|edge|inner|center|ring",
        help="where the desert may be: free (anywhere, the default), edge (12 tiles on the coast), "
        "inner (the 7 tiles that do not touch the sea), center (the middle tile) or ring (the 6 "
        "tiles around the middle)",
    )
    parser.add_argument(
        "--allow-adjacent-red", action="store_true",
        help="allow a 6 or 8 next to another 6 or 8 (by default they never touch)",
    )
    return parser


def _can_print_arrows():
    """False when the console's encoding cannot show the Unicode arrows (an old Windows console,
    or PYTHONIOENCODING=ascii); a stream that reports no encoding at all (an in-memory buffer)
    can take any text."""
    encoding = getattr(sys.stdout, "encoding", None)
    if encoding is None:
        return True
    try:
        "".join(UNICODE_ARROWS.values()).encode(encoding)
    except (UnicodeEncodeError, LookupError):
        return False
    return True


def run(args):
    fmt = FORMATS[args.format]
    lines = []

    if args.string is not None:
        if args.desert is not None or args.allow_adjacent_red:
            raise CatanMapError(
                "--desert and --allow-adjacent-red only apply when a board is made from a seed, "
                "not with --string"
            )
        parsed = parse(args.string)
        board = parsed.board
        include_ports = board.ports is not None or args.ports
        lines.append("string: " + serialize(board, fmt, args.pipes, include_ports))
        for warning in parsed.warnings:
            print(f"warning: {warning}", file=sys.stderr)
    else:
        code = parse_seed_code(args.seed) if args.seed is not None else SeedCode(random_seed())
        code = combine(code, desert=args.desert, allow_adjacent_red=args.allow_adjacent_red, ports=args.ports)
        board = generate(code)
        lines.append(f"seed:   {code}")
        lines.append("string: " + serialize(board, fmt, args.pipes, code.ports))

    if args.board:
        ascii_only = args.ascii or not _can_print_arrows()
        lines.append("")
        lines.append(render_board(board, ascii_only=ascii_only, color=args.color))
    print("\n".join(lines))
    return 0


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except CatanMapError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
