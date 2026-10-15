import random
import unittest
from unittest import mock

from catan_map import GenerationError, SeedCode, generate, parse, serialize
from catan_map.board import DESERT_ZONES, TILE_COUNT, adjacent_red_pairs, is_corner_slot

SEEDS = ["".join(chr(65 + (n // 26 ** i) % 26) for i in range(5)) for n in range(0, 26 ** 5, 26 ** 5 // 400)]


def desert_of(board):
    return board.tiles.index("D")


class Basics(unittest.TestCase):
    def test_the_same_seed_gives_the_same_board(self):
        self.assertEqual(generate("KMQXRT"), generate("KMQXRT"))
        self.assertEqual(generate("kmqxrt"), generate("KMQXRT"))
        self.assertEqual(generate(SeedCode("KMQXRT")), generate("KMQXRT"))

    def test_different_seeds_give_different_boards(self):
        strings = {serialize(generate(seed)) for seed in SEEDS}
        self.assertEqual(len(strings), len(SEEDS))

    def test_every_board_is_valid_and_survives_writing_and_reading(self):
        for seed in SEEDS:
            board = generate(seed, ports=True)
            for fmt in "sp":
                for pipes in (False, True):
                    text = serialize(board, fmt, pipes, True)
                    self.assertEqual(parse(text).board, board, (seed, fmt, pipes))

    def test_options_in_the_code_are_used_when_a_code_is_given(self):
        board = generate(SeedCode("KMQXRT", "center", True, True))
        self.assertEqual(desert_of(board), 9)
        self.assertIsNotNone(board.ports)

    def test_an_unknown_desert_option(self):
        with self.assertRaises(GenerationError):
            generate("KMQXRT", desert="nowhere")

    def test_only_random_dot_random_is_used(self):
        # Python promises only the sequence of random() for a seed, so nothing else may be used
        forbidden = {"shuffle", "choice", "choices", "sample", "randrange", "randint", "uniform", "getrandbits"}
        patches = [
            mock.patch.object(random.Random, name, side_effect=AssertionError(name))
            for name in forbidden if hasattr(random.Random, name)
        ]
        for patch in patches:
            patch.start()
        try:
            with self.assertRaises(AssertionError):      # the guard itself works
                random.Random(1).shuffle([1, 2, 3])
            board = generate("KMQXRT", ports=True, allow_adjacent_red=True)
        finally:
            for patch in patches:
                patch.stop()
        self.assertEqual(len(board.tiles), TILE_COUNT)


class Desert(unittest.TestCase):
    def test_the_desert_stays_in_its_zone(self):
        for zone, tiles in DESERT_ZONES.items():
            for seed in SEEDS:
                self.assertIn(desert_of(generate(seed, desert=zone)), tiles, (zone, seed))

    def test_every_tile_of_a_zone_is_used(self):
        for zone, tiles in DESERT_ZONES.items():
            seen = {desert_of(generate(seed, desert=zone)) for seed in SEEDS}
            self.assertEqual(seen, set(tiles), zone)

    def test_free_is_roughly_uniform(self):
        counts = [0] * TILE_COUNT
        n = 3800
        for i in range(n):
            counts[desert_of(generate(f"SEED{chr(65 + i % 26)}{chr(65 + i // 26 % 26)}{chr(65 + i // 676)}"))] += 1
        expected = n / TILE_COUNT
        for tile, count in enumerate(counts):
            self.assertTrue(0.7 * expected < count < 1.3 * expected, (tile, count, expected))


class RedNumbers(unittest.TestCase):
    def test_a_6_or_8_never_touches_another_by_default(self):
        for seed in SEEDS:
            for zone in DESERT_ZONES:
                self.assertEqual(adjacent_red_pairs(generate(seed, desert=zone).tokens), [], (seed, zone))

    def test_when_allowed_some_boards_do_have_touching_reds(self):
        touching = [seed for seed in SEEDS if adjacent_red_pairs(generate(seed, allow_adjacent_red=True).tokens)]
        self.assertGreater(len(touching), 50)

    def test_the_rule_costs_few_retries(self):
        # the token shuffle is repeated until the rule holds; it should almost always be quick
        calls = []
        original = random.Random.random

        def counting(self):
            calls.append(1)
            return original(self)

        with mock.patch.object(random.Random, "random", counting):
            for seed in SEEDS[:100]:
                generate(seed)
        per_board = len(calls) / 100
        self.assertGreater(per_board, 30)     # at least the desert and the two shuffles: the counter works
        self.assertLess(per_board, 400)


class PortsAreDrawnLast(unittest.TestCase):
    def test_asking_for_ports_never_changes_the_tiles_or_the_tokens(self):
        for seed in SEEDS:
            without, with_ports = generate(seed), generate(seed, ports=True)
            self.assertEqual(without.tiles, with_ports.tiles)
            self.assertEqual(without.tokens, with_ports.tokens)
            self.assertIsNone(without.ports)
            self.assertIsNotNone(with_ports.ports)

    def test_the_ports_are_valid(self):
        for seed in SEEDS:
            ports = generate(seed, ports=True).ports
            kinds = sorted(p.kind for p in ports.entries)
            self.assertEqual("".join(kinds), "".join(sorted("3333WOCSG")))

    def test_corner_ports_are_in_one_form(self):
        for seed in SEEDS:
            ports = generate(seed, ports=True).ports
            for slot, port in enumerate(ports.entries):
                if is_corner_slot(slot, ports.shifted):
                    self.assertFalse(port.forward, (seed, slot))

    def test_both_shifts_and_both_orientations_occur(self):
        boards = [generate(seed, ports=True).ports for seed in SEEDS]
        self.assertEqual({p.shifted for p in boards}, {True, False})
        forward = {port.forward for p in boards for slot, port in enumerate(p.entries) if not is_corner_slot(slot, p.shifted)}
        self.assertEqual(forward, {True, False})

    def test_the_ports_text_of_a_generated_board_reads_back(self):
        for seed in SEEDS[:50]:
            board = generate(seed, ports=True)
            self.assertEqual(parse(serialize(board, "s", False, True)).board.ports, board.ports)


if __name__ == "__main__":
    unittest.main()
