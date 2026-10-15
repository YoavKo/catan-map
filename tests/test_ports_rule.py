"""The rule: a port may not attach to the desert."""
import random
import unittest
from unittest import mock

from catan_map import CodecError, generate, parse, render_board, serialize
from catan_map.board import DESERT_ZONES, TILE_COUNT, is_corner_slot, port_target_tile
from catan_map.codec import Board, Port, Ports, avoid_desert, default_ports, ports_on_desert, ports_to_text

SEEDS = ["".join(chr(65 + (n // 26 ** i) % 26) for i in range(5)) for n in range(0, 26 ** 5, 26 ** 5 // 300)]
TILES_WITHOUT_DESERT = "WSGOCWSGOWCSGOCWSG" + "W"        # 19 letters with 4 W... (only used to build boards)


def board_with_desert(desert):
    """A valid board (the example's resources and tokens) with the desert on the given tile."""
    letters = list("WSGOCWSGOWCSGOCWSG")                  # the 18 resource tiles of the example
    tokens = list("563a4b892c563b9a48")
    tiles, toks = [], []
    for i in range(TILE_COUNT):
        if i == desert:
            tiles.append("D"); toks.append(None)
        else:
            tiles.append(letters.pop(0)); toks.append(tokens.pop(0))
    return Board(tuple(tiles), tuple(toks))


DEFAULT_TARGETS = {port_target_tile(slot, False, port.forward) for slot, port in enumerate(default_ports().entries)}
DEFAULT_CORNER_TARGETS = {port_target_tile(slot, False, False) for slot in range(9) if is_corner_slot(slot, False)}


class AvoidDesert(unittest.TestCase):
    def test_the_default_ports_attach_to_these_tiles(self):
        self.assertEqual(sorted(DEFAULT_TARGETS), [0, 1, 3, 6, 11, 12, 15, 16, 17])
        self.assertEqual(sorted(DEFAULT_CORNER_TARGETS), [0, 11, 16])

    def test_no_port_attaches_to_the_desert_wherever_it_is(self):
        for desert in range(TILE_COUNT):
            adjusted = avoid_desert(default_ports(), desert)
            self.assertEqual(ports_on_desert(adjusted, desert), [], desert)

    def test_the_default_is_left_alone_when_it_does_not_touch_the_desert(self):
        for desert in range(TILE_COUNT):
            if desert not in DEFAULT_TARGETS:
                self.assertEqual(avoid_desert(default_ports(), desert), default_ports(), desert)

    def test_a_port_that_is_not_on_a_corner_just_switches_orientation(self):
        for desert in (1, 3, 6, 12, 15, 17):
            adjusted = avoid_desert(default_ports(), desert)
            self.assertFalse(adjusted.shifted, desert)
            changed = [k for k, (a, b) in enumerate(zip(default_ports().entries, adjusted.entries)) if a != b]
            self.assertEqual(len(changed), 1, desert)
            slot = changed[0]
            self.assertEqual(adjusted.entries[slot].forward, not default_ports().entries[slot].forward)

    def test_a_corner_port_on_the_desert_shifts_the_ring(self):
        for desert in (0, 11, 16):
            self.assertTrue(avoid_desert(default_ports(), desert).shifted, desert)

    def test_for_any_ports_and_any_desert(self):
        rng = random.Random(7)
        kinds = list("3333WOCSG")
        for _ in range(3000):
            rng.shuffle(kinds)
            shifted = rng.random() < 0.5
            ports = Ports(tuple(Port(k, rng.random() < 0.5) for k in kinds), shifted)
            desert = rng.randrange(TILE_COUNT)
            adjusted = avoid_desert(ports, desert)
            self.assertEqual(ports_on_desert(adjusted, desert), [])
            self.assertEqual(avoid_desert(adjusted, desert), adjusted)                 # nothing left to move
            self.assertEqual([p.kind for p in adjusted.entries], kinds)                # the pieces stay in order
            if not ports_on_desert(ports, desert):
                self.assertEqual(adjusted, ports)                                      # untouched if no conflict


class Reading(unittest.TestCase):
    def test_a_port_on_the_desert_is_an_error_naming_the_character(self):
        board = generate("KMQXRT")                   # the desert is tile 3
        self.assertEqual(board.tiles.index("D"), 3)
        text = serialize(board) + "3gO3s#3cW"        # port 9, "W", forward, attaches to tile 3
        with self.assertRaises(CodecError) as caught:
            parse(text)
        self.assertIn("character 46", str(caught.exception))
        self.assertIn("port 9 ('W')", str(caught.exception))
        self.assertIn("attaches to the desert at row 2, column 1", str(caught.exception))

    def test_a_corner_port_on_the_desert_is_an_error_too(self):
        text = serialize(board_with_desert(0)) + "3gO3s#3cW"       # port 1 is a corner port on tile 0
        with self.assertRaises(CodecError) as caught:
            parse(text)
        self.assertIn("port 1", str(caught.exception))

    def test_the_same_ports_are_fine_when_the_desert_is_elsewhere(self):
        parse(serialize(board_with_desert(8)) + "3gO3s#3cW")

    def test_the_ports_that_avoid_the_desert_are_accepted(self):
        text = serialize(board_with_desert(0))
        with self.assertRaises(CodecError):
            parse(text + "3gO3s#3cW")                      # port 1 is a corner port on tile 0
        fixed = ports_to_text(avoid_desert(default_ports(), 0))
        self.assertTrue(fixed.startswith("X"))             # the ring had to be shifted
        parse(text + fixed)
        # shifting alone is not enough: with the shift port 1 is no longer on a corner
        with self.assertRaises(CodecError):
            parse(text + "X3gO3s#3cW")

    def test_the_rule_applies_to_every_layout(self):
        text = serialize(generate("KMQXRT"), "p", True) + ",3gO3s#3cW"
        with self.assertRaises(CodecError):
            parse(text)


class NoPortsPart(unittest.TestCase):
    def test_the_default_ports_never_attach_to_the_desert(self):
        for desert in range(TILE_COUNT):
            board = board_with_desert(desert)
            self.assertEqual(ports_on_desert(board.effective_ports(), desert), [], desert)

    def test_writing_them_out_gives_a_string_the_reader_accepts(self):
        for desert in range(TILE_COUNT):
            board = board_with_desert(desert)
            text = serialize(board, "s", False, True)
            self.assertEqual(parse(text).board.ports, board.effective_ports(), desert)

    def test_a_board_whose_default_is_untouched_writes_the_plain_default(self):
        self.assertTrue(serialize(board_with_desert(8), "s", False, True).endswith("3gO3s#3cW"))

    def test_the_drawing_says_when_the_ports_were_moved(self):
        self.assertIn("moved off the desert", render_board(board_with_desert(3)))
        self.assertIn("(default arrangement, not in the string)", render_board(board_with_desert(8)))

    def test_no_legend_line_points_at_the_desert(self):
        for desert in range(TILE_COUNT):
            text = render_board(board_with_desert(desert))
            for line in text.split("\n"):
                if line.startswith("port "):
                    tile = int(line.split("-> tile")[1].split("(")[0])
                    self.assertNotEqual(tile, desert, (desert, line))


class Generated(unittest.TestCase):
    def test_no_generated_port_attaches_to_the_desert(self):
        for zone in DESERT_ZONES:
            for seed in SEEDS:
                board = generate(seed, desert=zone, ports=True)
                self.assertEqual(ports_on_desert(board.ports, board.tiles.index("D")), [], (zone, seed))

    def test_generated_strings_are_accepted_by_the_reader(self):
        for seed in SEEDS:
            for zone in ("free", "edge"):
                board = generate(seed, desert=zone, ports=True)
                self.assertEqual(parse(serialize(board, "s", False, True)).board, board)

    def test_the_rule_actually_moved_ports(self):
        # without the rule, some of these boards would have a port on the desert
        from catan_map import generator
        from catan_map.generator import Stream
        moved = 0
        for seed in SEEDS:
            board = generate(seed, desert="edge", ports=True)
            stream = Stream(seed)
            tiles, desert = generator._generate_tiles(stream, "edge")
            generator._generate_tokens(stream, desert, False)
            raw = generator._generate_ports(stream)
            if ports_on_desert(raw, desert):
                moved += 1
                self.assertNotEqual(raw, board.ports)
            else:
                self.assertEqual(raw, board.ports)
        self.assertGreater(moved, 30)

    def test_the_number_of_draws_for_ports_does_not_depend_on_the_desert(self):
        original = random.Random.random
        counter = []

        def counting(self):
            counter.append(1)
            return original(self)

        def draws(seed, zone, ports):
            counter.clear()
            with mock.patch.object(random.Random, "random", counting):
                generate(seed, desert=zone, ports=ports)
            return len(counter)

        for seed in SEEDS[:60]:
            for zone in DESERT_ZONES:
                self.assertEqual(draws(seed, zone, True) - draws(seed, zone, False), 15, (seed, zone))

    def test_asking_for_ports_still_leaves_the_tiles_and_tokens_alone(self):
        for seed in SEEDS:
            for zone in DESERT_ZONES:
                a, b = generate(seed, desert=zone), generate(seed, desert=zone, ports=True)
                self.assertEqual((a.tiles, a.tokens), (b.tiles, b.tokens))


class FromTheCommandLine(unittest.TestCase):
    def run_cli(self, *argv):
        import contextlib, io
        from catan_map import cli
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_ports_added_to_a_string_are_moved_off_the_desert(self):
        text = serialize(generate("KMQXRT"))               # desert on tile 3, which the default ports attach to
        code, out, _ = self.run_cli("--string", text, "--ports")
        self.assertEqual(code, 0)
        written = out.split("string: ")[1].strip()
        # port 9 ("W", forward, on tile 3) switches to backward ("w", on tile 7); the others stay
        self.assertEqual(written, text + "3gO3s#3cw")
        parse(written)                                       # and the reader accepts it

    def test_a_string_with_a_port_on_the_desert_is_an_error(self):
        code, out, err = self.run_cli("--string", serialize(generate("KMQXRT")) + "3gO3s#3cW")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("attaches to the desert", err)


if __name__ == "__main__":
    unittest.main()
