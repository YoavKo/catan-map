"""A Settlers of Catan map generator: a seed gives a board, a board is a short string.

    >>> from catan_map import generate, serialize, parse
    >>> board = generate("KMQXRT")
    >>> text = serialize(board)
    >>> parse(text).board == board
    True

The string format, the seed codes and the rules are described in README.md.
"""
from .codec import Board, CatanMapError, CodecError, Parsed, Port, Ports, parse, serialize
from .generator import GenerationError, generate
from .render_text import render_board
from .seed import SeedCode, SeedError, combine, format_seed_code, parse_seed_code, random_seed

__version__ = "1.0.0"

__all__ = [
    "Board", "CatanMapError", "CodecError", "GenerationError", "Parsed", "Port", "Ports", "SeedCode",
    "SeedError", "combine", "format_seed_code", "generate", "parse", "parse_seed_code", "random_seed",
    "render_board", "serialize",
]
