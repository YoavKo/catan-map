"""The command line: ``python -m catan_map`` or the ``catan-map`` command.

    catan-map                         a random seed: prints the seed and the string
    catan-map --seed KMQXRT           the same seed always gives the same board
    catan-map --string "WSG..."       read a string instead of using a seed
"""
from __future__ import annotations

import sys

if __name__ == "__main__" and not __package__:
    # Started as a file (`python catan_map/cli.py`, `uv run catan_map/cli.py`): the relative
    # imports below need the package, so make it importable and run it as the package instead.
    import os
    import runpy

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    runpy.run_module("catan_map", run_name="__main__", alter_sys=True)
    raise SystemExit

import argparse  # noqa: E402

from .board import DESERT_ZONES
from .codec import CatanMapError, parse, serialize
from .generator import generate
from .render_svg import ELEMENTS, check_elements, logo_data_uri, render_svg
from .svg_tiles import DEFAULT_TILE_SET, TILE_SET_NAMES
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
        "(F E I C R for the desert, A for adjacent 6/8, P for ports), for example KMQXRT-EP. "
        "Without --seed and --string a random seed of 3 different letters is made",
    )
    source.add_argument("--string", metavar="STR", help="read this string (either layout, with or without | and ,)")
    parser.add_argument(
        "--format", choices=sorted(FORMATS), default="p", metavar="s|p",
        help="s (sections: tiles, tokens, ports) or p (paired: each tile followed by its token); "
        "sections and paired also work (default p)",
    )
    parser.add_argument(
        "--no-pipes", action="store_true",
        help="write the string without the | between the rows and the , between the parts "
        "(by default they are written)",
    )
    parser.add_argument(
        "--ports", action="store_true",
        help="include the ports part: random ports when making a board from a seed; the default "
        "ports when reading a string that has none (a string that has ports always keeps them)",
    )
    parser.add_argument("--board", action="store_true", help="draw the board in the console")
    parser.add_argument(
        "--svg", metavar="FILE",
        help="write the board as an SVG image to FILE ('-' prints the SVG to the terminal, and the "
        "seed and string go to stderr)",
    )
    parser.add_argument(
        "--elements", nargs="*", metavar="ELEMENT",
        help="make the SVG a printable 60 x 60 cm sheet (the board 550 x 505 mm, the number tokens 25 mm "
        "across) with these things on it, separated by spaces or commas: "
        "costs (a Building Costs card in each corner), bank (places for the bank along the bottom), "
        "seed (the seed code, big), str (the string, on one line), logo (the --logo-img image, as large as "
        "fits); 'all' means all of them. With no names it is the bare sheet. Needs --svg",
    )
    parser.add_argument(
        "--logo-img", metavar="FILE",
        help="the image (png, jpg, gif, webp or svg) for the logo element; it is embedded in the SVG "
        "(needs --svg and --elements with logo)",
    )
    parser.add_argument(
        "--tiles", choices=TILE_SET_NAMES, metavar="|".join(TILE_SET_NAMES),
        help=f"the look of the tiles in the SVG: basic (flat colours and simple shapes), realistic "
        f"(painted-looking) or plain (one colour per tile); default {DEFAULT_TILE_SET}. Needs --svg",
    )
    parser.add_argument("--color", action="store_true", help="colours in the drawing")
    parser.add_argument("--ascii", action="store_true", help="draw with plain ASCII characters only")
    parser.add_argument(
        "--desert", choices=list(DESERT_ZONES), metavar="free|edge|inner|center|ring",
        help="where the desert is: center (the middle tile, the default), free (anywhere), edge (12 tiles on the coast), "
        "inner (the 7 tiles that do not touch the sea) or ring (the 6 "
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


def _elements(args):
    """The --elements as a tuple of names, or None when the option is not given."""
    if args.elements is None:
        if args.logo_img is not None:
            raise CatanMapError("--logo-img only applies when --elements includes logo")
        return None
    names = [name.strip() for value in args.elements for name in value.split(",") if name.strip()]
    if "all" in names:
        names = [name for name in ELEMENTS if name != "logo" or args.logo_img is not None]
    elements = check_elements(names)
    if "logo" in elements and args.logo_img is None:
        raise CatanMapError("the logo element needs --logo-img FILE")
    if args.logo_img is not None and "logo" not in elements:
        raise CatanMapError("--logo-img only applies when --elements includes logo")
    return elements


def run(args):
    fmt = FORMATS[args.format]
    pipes = not args.no_pipes
    for flag, given in (("--tiles", args.tiles is not None), ("--elements", args.elements is not None),
                        ("--logo-img", args.logo_img is not None)):
        if given and args.svg is None:
            raise CatanMapError(f"{flag} only applies together with --svg")
    elements = _elements(args)
    lines = []
    caption = []

    if args.string is not None:
        if args.desert is not None or args.allow_adjacent_red:
            raise CatanMapError(
                "--desert and --allow-adjacent-red only apply when a board is made from a seed, "
                "not with --string"
            )
        parsed = parse(args.string)
        board = parsed.board
        include_ports = board.ports is not None or args.ports
        lines.append("string: " + serialize(board, fmt, pipes, include_ports))
        caption.append(serialize(board, fmt, pipes, include_ports))
        for warning in parsed.warnings:
            print(f"warning: {warning}", file=sys.stderr)
    else:
        code = parse_seed_code(args.seed) if args.seed is not None else SeedCode(random_seed())
        code = combine(code, desert=args.desert, allow_adjacent_red=args.allow_adjacent_red, ports=args.ports)
        board = generate(code)
        lines.append(f"seed:   {code}")
        lines.append("string: " + serialize(board, fmt, pipes, code.ports))
        caption.extend((str(code), serialize(board, fmt, pipes, code.ports)))

    if args.board:
        ascii_only = args.ascii or not _can_print_arrows()
        lines.append("")
        lines.append(render_board(board, ascii_only=ascii_only, color=args.color))
    logo = logo_data_uri(args.logo_img) if args.logo_img is not None else None
    if args.svg == "-":
        print("\n".join(lines), file=sys.stderr)
        print(render_svg(board, caption, args.tiles, elements, logo), end="")
        return 0
    if args.svg is not None:
        try:
            with open(args.svg, "w", encoding="utf-8") as handle:
                handle.write(render_svg(board, caption, args.tiles, elements, logo))
        except OSError as error:
            raise CatanMapError(f"cannot write {args.svg}: {error.strerror or error}") from error
        lines.append(f"svg:    {args.svg}")
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
