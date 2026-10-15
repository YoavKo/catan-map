import unittest

from catan_map import CodecError, parse, serialize
from catan_map.board import DEFAULT_PORTS
from catan_map.codec import Board, default_ports, ports_to_text

TILES = "WSGOCWSGDOWCSGOCWSG"     # the desert is tile 8
TOKENS = "563a4b892c563b9a48"
PORTS = "3gO3s#3cW"

EXAMPLES = {
    ("s", False, False): "WSGOCWSGDOWCSGOCWSG563a4b892c563b9a48",
    ("s", True, False): "WSG|OCWS|GDOWC|SGOC|WSG,563|a4b8|92c5|63b9|a48",
    ("p", False, False): "W5S6G3OaC4WbS8G9DO2WcC5S6G3ObC9WaS4G8",
    ("p", True, False): "W5S6G3|OaC4WbS8|G9DO2WcC5|S6G3ObC9|WaS4G8",
    ("s", False, True): "WSGOCWSGDOWCSGOCWSG563a4b892c563b9a483gO3s#3cW",
    ("s", True, True): "WSG|OCWS|GDOWC|SGOC|WSG,563|a4b8|92c5|63b9|a48,3gO3s#3cW",
    ("p", False, True): "W5S6G3OaC4WbS8G9DO2WcC5S6G3ObC9WaS4G83gO3s#3cW",
    ("p", True, True): "W5S6G3|OaC4WbS8|G9DO2WcC5|S6G3ObC9|WaS4G8,3gO3s#3cW",
}
BASE = EXAMPLES[("s", False, False)]


def example_board(with_ports=True):
    tokens = iter(TOKENS)
    return Board(
        tuple(TILES),
        tuple(None if t == "D" else next(tokens) for t in TILES),
        default_ports() if with_ports else None,
    )


class Writing(unittest.TestCase):
    def test_all_eight_forms_of_the_example(self):
        board = example_board()
        for (fmt, pipes, ports), expected in EXAMPLES.items():
            self.assertEqual(serialize(board, fmt, pipes, ports), expected, (fmt, pipes, ports))

    def test_no_spaces_anywhere(self):
        for text in EXAMPLES.values():
            self.assertNotIn(" ", text)

    def test_a_board_without_ports_writes_the_default_when_asked(self):
        self.assertEqual(serialize(example_board(False), "s", False, True), EXAMPLES[("s", False, True)])

    def test_bad_format(self):
        with self.assertRaises(ValueError):
            serialize(example_board(), "x")


class Reading(unittest.TestCase):
    def test_every_form_reads_back_to_the_same_board(self):
        for (fmt, pipes, ports), text in EXAMPLES.items():
            parsed = parse(text)
            self.assertEqual(parsed.format, fmt, text)
            self.assertEqual(parsed.board, example_board(ports), text)

    def test_round_trip_in_every_form(self):
        board = example_board()
        for fmt in "sp":
            for pipes in (False, True):
                for ports in (False, True):
                    text = serialize(board, fmt, pipes, ports)
                    self.assertEqual(serialize(parse(text).board, fmt, pipes, ports), text)

    def test_separators_may_be_anywhere_and_surrounding_whitespace_is_trimmed(self):
        plain = EXAMPLES[("s", False, True)]
        messy = "  " + "|".join(plain[i:i + 5] for i in range(0, len(plain), 5)) + ",\n"
        self.assertEqual(parse(messy).board, example_board())

    def test_the_layouts_are_told_apart_when_the_first_tile_is_the_desert(self):
        # the desert first, then the example's 18 resource tiles and 18 tokens
        board = Board(("D",) + tuple(TILES.replace("D", "")), (None,) + tuple(TOKENS))
        for fmt in "sp":
            parsed = parse(serialize(board, fmt))
            self.assertEqual(parsed.format, fmt)
            self.assertEqual(parsed.board, board)

    def test_ports_with_the_shift(self):
        text = BASE + "X" + PORTS
        parsed = parse(text)
        self.assertTrue(parsed.board.ports.shifted)
        self.assertEqual(serialize(parsed.board, "s", False, True), text)

    def test_a_corner_port_may_be_written_in_either_orientation(self):
        # without the shift, slots 0, 3 and 6 are corners: "#" and "3" are the same there
        self.assertEqual(parse(BASE + "#gO#s#3cW").board.ports, default_ports())
        # a resource port on a corner slot: "G" (forward) and "g" (backward) are the same board
        upper = parse(BASE + "G3O3s#3cW").board
        lower = parse(BASE + "g3O3s#3cW").board
        self.assertEqual(upper, lower)
        # and it is written in the lowercase form
        self.assertEqual(ports_to_text(upper.ports), "g3O3s#3cW")

    def test_a_port_that_is_not_on_a_corner_keeps_its_orientation(self):
        forward = [p.forward for p in default_ports().entries]
        self.assertEqual(forward, [False, False, True, False, False, True, False, False, True])

    def test_the_default_ports_text(self):
        self.assertEqual(ports_to_text(default_ports()), DEFAULT_PORTS)

    def test_touching_red_numbers_are_a_warning_not_an_error(self):
        tokens = list(example_board().tokens)
        # tile 1 has the 6; move the 8 from tile 6 to tile 2, which touches tile 1
        tokens[2], tokens[6] = tokens[6], tokens[2]
        text = serialize(Board(example_board().tiles, tuple(tokens)), "s")
        parsed = parse(text)
        self.assertEqual(parsed.warnings, ("the 6 at row 1, column 2 touches the 8 at row 1, column 3",))
        self.assertEqual(parse(BASE).warnings, ())


class Errors(unittest.TestCase):
    def fails(self, text, *fragments):
        with self.assertRaises(CodecError) as caught:
            parse(text)
        for fragment in fragments:
            self.assertIn(fragment, str(caught.exception))

    def test_empty_or_only_separators(self):
        self.fails("", "empty")
        self.fails("   ", "empty")
        self.fails("|,|", "empty", "separators")

    def test_a_space_inside_names_its_position(self):
        self.fails(BASE[:10] + " " + BASE[10:], "character 11", "spaces")

    def test_wrong_tile_counts(self):
        self.fails("W" + BASE[1:].replace("S", "G", 1), "tiles", "expected 4 S")
        self.fails(BASE.replace("D", "W"), "tiles", "expected 1 D")

    def test_too_short(self):
        self.fails(BASE[:30], "too short")

    def test_a_bad_token_names_its_position(self):
        self.fails(BASE[:19] + "Z" + BASE[20:], "character 20", "not a token")
        self.fails(BASE[:19] + "7" + BASE[20:], "character 20", "not a token")   # there is no 7

    def test_an_uppercase_token_letter_gets_a_hint(self):
        self.fails(BASE[:19] + "C" + BASE[20:], "character 20", "lowercase")

    def test_wrong_token_counts(self):
        self.fails(BASE[:19] + "2" + BASE[20:], "tokens", "expected 2 of 5")

    def test_paired_errors(self):
        paired = EXAMPLES[("p", False, False)]
        self.fails(paired[:2] + "Z" + paired[3:], "character 3", "tile letter")     # a tile position
        self.fails(paired[:3] + "Z" + paired[4:], "character 4", "not a token")     # a token position
        self.fails(paired[:20], "character 20", "needs a token after it")   # cut right after a tile letter
        self.fails(paired[:21], "ends too early", "tile 12 of 19")             # cut after a whole pair
        self.fails(paired[:1] + "W" + paired[2:], "character 2")

    def test_port_errors(self):
        self.fails(BASE + "3gO3s#3c", "ports", "expected 9")
        self.fails(BASE + "3gO3s#3cWW", "expected 9")
        self.fails(BASE + "3gO3s#3cZ", "port symbol")
        self.fails(BASE + "3gO3s#3c3", "ports", "four 3:1")
        self.fails(BASE + "3gO3sX3cW", "X is only allowed at the start")
        self.fails(BASE + "XX3gO3s#3cW", "X is only allowed")
        self.fails(BASE + "X3gO3s#3c", "after the X")

    def test_not_text(self):
        with self.assertRaises(CodecError):
            parse(None)


if __name__ == "__main__":
    unittest.main()
