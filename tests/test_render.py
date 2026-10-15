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

LEGEND = """\
port 1 (ring  0, corner  ): 3:1       -> tile  0 (row 1, col 1)
port 2 (ring  2, backward): 2:1 grain -> tile  1 (row 1, col 2)
port 3 (ring  4, forward ): 2:1 ore   -> tile  6 (row 2, col 4)
port 4 (ring  6, corner  ): 3:1       -> tile 11 (row 3, col 5)
port 5 (ring  8, backward): 2:1 sheep -> tile 15 (row 4, col 4)
port 6 (ring 10, forward ): 3:1       -> tile 17 (row 5, col 2)
port 7 (ring 12, corner  ): 3:1       -> tile 16 (row 5, col 1)
port 8 (ring 14, backward): 2:1 clay  -> tile 12 (row 4, col 1)
port 9 (ring 16, forward ): 2:1 wood  -> tile  3 (row 2, col 1)"""

ANSI = re.compile(r"\x1b\[[0-9;]*m")


class Drawings(unittest.TestCase):
    def test_unicode_with_the_default_ports(self):
        expected = UNICODE_DRAWING + "\n\nports (default arrangement, not in the string):\n" + LEGEND
        self.assertEqual(render_board(BOARD), expected)

    def test_ascii_with_the_default_ports(self):
        expected = ASCII_DRAWING + "\n\nports (default arrangement, not in the string):\n" + LEGEND
        self.assertEqual(render_board(BOARD, ascii_only=True), expected)

    def test_a_string_that_has_the_default_ports_draws_the_same_but_says_so(self):
        with_ports = Board(BOARD.tiles, BOARD.tokens, default_ports())
        text = render_board(with_ports)
        self.assertTrue(text.startswith(UNICODE_DRAWING))
        self.assertIn("\n\nports:\n" + LEGEND, text)

    def test_the_shifted_ring(self):
        shifted = parse("WSGOCWSGDOWCSGOCWSG563a4b892c563b9a48X3gO3s#3cW").board
        text = render_board(shifted)
        self.assertTrue(text.startswith(SHIFTED_DRAWING))
        self.assertIn("ports (shifted by one, the top-left sea tile is empty):", text)
        self.assertIn("port 1 (ring  1, backward): 3:1", text.replace("non-corner", ""))

    def test_ascii_drawings_use_only_ascii(self):
        for seed in ("KMQXRT", "AAAAAA", "ZZZZZZ"):
            text = render_board(generate(seed, ports=True), ascii_only=True)
            self.assertTrue(text.isascii())

    def test_every_tile_and_token_is_drawn_where_it_belongs(self):
        for seed in ("KMQXRT", "AAAAAA", "ZZZZZZ", "CATAN"):
            board = generate(seed)
            lines = render_board(board).split("\n\n")[0].split("\n")
            for tile, (row, x) in enumerate(TILE_POSITIONS):
                column = 3 * x + 18
                cell = lines[row + 1][column:column + 2].ljust(2)
                self.assertEqual(cell, board.tiles[tile] + (board.tokens[tile] or " "), (seed, tile))

    def test_the_legend_lists_nine_ports(self):
        for seed in ("KMQXRT", "AAAAAA"):
            text = render_board(generate(seed, ports=True))
            self.assertEqual(len(re.findall(r"^port \d \(ring", text, re.M)), 9)


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
