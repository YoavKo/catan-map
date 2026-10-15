import re
import unittest

from catan_map import generate, parse, render_board
from catan_map.board import TILE_POSITIONS
from catan_map.codec import Board, default_ports

TILES = "WSGOCWSGDOWCSGOCWSG"
TOKENS = "563a4b892c563b9a48"
tokens = iter(TOKENS)
BOARD = Board(tuple(TILES), tuple(None if t == "D" else next(tokens) for t in TILES), None)

UNICODE_DRAWING = """\
         3↘    ~     ↙G    ~
      ~     W5    S6    G3    ↙O
   W→    Oa    C4    Wb    S8    ~
~     G9    D     O2    Wc    C5    ←3
   C→    S6    G3    Ob    C9    ~
      ~     Wa    S4    G8    ↖S
         3↗    ~     ↖3    ~"""

ASCII_DRAWING = """\
         3\\    ~     /G    ~
      ~     W5    S6    G3    /O
   W>    Oa    C4    Wb    S8    ~
~     G9    D     O2    Wc    C5    <3
   C>    S6    G3    Ob    C9    ~
      ~     Wa    S4    G8    \\S
         3/    ~     \\3    ~"""

SHIFTED_DRAWING = """\
         ~     ↙3    ~     ↙G
      W→    W5    S6    G3    ~
   ~     Oa    C4    Wb    S8    ↙O
C→    G9    D     O2    Wc    C5    ~
   ~     S6    G3    Ob    C9    ↖3
      3→    Wa    S4    G8    ~
         ~     ↖3    ~     ↖S"""

ANSI = re.compile(r"\x1b\[[0-9;]*m")


class Drawings(unittest.TestCase):
    def test_unicode_with_the_default_ports(self):
        self.assertEqual(render_board(BOARD), UNICODE_DRAWING)

    def test_ascii_with_the_default_ports(self):
        self.assertEqual(render_board(BOARD, ascii_only=True), ASCII_DRAWING)

    def test_a_string_that_has_the_default_ports_draws_the_same(self):
        self.assertEqual(render_board(Board(BOARD.tiles, BOARD.tokens, default_ports())), UNICODE_DRAWING)

    def test_the_shifted_ring(self):
        shifted = parse("WSGOCWSGDOWCSGOCWSG563a4b892c563b9a48X3gO3s#3cW").board
        self.assertEqual(render_board(shifted), SHIFTED_DRAWING)

    def test_only_the_drawing_is_printed_no_heading_and_no_port_list(self):
        for seed in ("KMQXRT", "AAAAAA", "ZZZZZZ"):
            for ports in (False, True):
                text = render_board(generate(seed, ports=ports))
                self.assertEqual(len(text.split("\n")), 7, seed)
                self.assertNotIn("port", text)
                self.assertNotIn("tile ", text)

    def test_ascii_drawings_use_only_ascii(self):
        for seed in ("KMQXRT", "AAAAAA", "ZZZZZZ"):
            text = render_board(generate(seed, ports=True), ascii_only=True)
            self.assertTrue(text.isascii())

    def test_every_tile_and_token_is_drawn_where_it_belongs(self):
        for seed in ("KMQXRT", "AAAAAA", "ZZZZZZ", "CATAN"):
            board = generate(seed)
            lines = render_board(board).split("\n")
            for tile, (row, x) in enumerate(TILE_POSITIONS):
                column = 3 * x + 18
                cell = lines[row + 1][column:column + 2].ljust(2)
                self.assertEqual(cell, board.tiles[tile] + (board.tokens[tile] or " "), (seed, tile))

    def test_the_nine_ports_are_drawn_each_with_an_arrow(self):
        for seed in ("KMQXRT", "AAAAAA"):
            text = render_board(generate(seed, ports=True))
            sea = [t for line in text.split("\n") for t in line.split() if len(t) == 2 and ("→" in t or "←" in t or "↗" in t or "↖" in t or "↘" in t or "↙" in t)]
            self.assertEqual(len(sea), 9)


class Colours(unittest.TestCase):
    def test_off_by_default(self):
        self.assertNotIn("\x1b", render_board(BOARD))

    def test_with_colour_the_text_is_the_same_once_the_codes_are_removed(self):
        for ascii_only in (False, True):
            plain = render_board(BOARD, ascii_only=ascii_only)
            coloured = render_board(BOARD, ascii_only=ascii_only, color=True)
            self.assertIn("\x1b[", coloured)
            self.assertEqual(ANSI.sub("", coloured), plain)

    def test_each_kind_has_its_colour(self):
        coloured = render_board(BOARD, color=True)
        for code in ("32", "90", "31", "92", "33", "38;5;180", "1", "34"):
            self.assertIn(f"\x1b[{code}m", coloured, code)


if __name__ == "__main__":
    unittest.main()
