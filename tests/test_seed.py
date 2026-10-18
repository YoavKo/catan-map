import itertools
import unittest

from catan_map import SeedCode, SeedError, combine, format_seed_code, parse_seed_code, random_seed
from catan_map.seed import normalize_seed


class Seeds(unittest.TestCase):
    def test_case_does_not_matter(self):
        self.assertEqual(normalize_seed("kMqXrT"), "KMQXRT")
        self.assertEqual(parse_seed_code("kmqxrt"), parse_seed_code("KMQXRT"))

    def test_one_to_thirty_two_letters(self):
        self.assertEqual(normalize_seed("A"), "A")
        self.assertEqual(normalize_seed("a" * 32), "A" * 32)
        with self.assertRaises(SeedError):
            normalize_seed("a" * 33)

    def test_only_ascii_letters(self):
        for bad in ("", "  ", "KM2XRT", "KM XRT", "KM-XRT", "KMQXRé", "קמקסרט", "KM_XRT"):
            with self.assertRaises(SeedError, msg=bad):
                normalize_seed(bad)

    def test_digits_get_a_hint(self):
        with self.assertRaises(SeedError) as caught:
            normalize_seed("KM2XRT")
        self.assertIn("no digits", str(caught.exception))

    def test_surrounding_whitespace_is_trimmed(self):
        self.assertEqual(normalize_seed("  kmqxrt\n"), "KMQXRT")


class Codes(unittest.TestCase):
    def test_a_plain_seed_means_all_defaults(self):
        self.assertEqual(parse_seed_code("KMQXRT"), SeedCode("KMQXRT", None, False, False))
        self.assertEqual(str(SeedCode("KMQXRT")), "KMQXRT")

    def test_each_flag(self):
        self.assertEqual(parse_seed_code("KMQXRT-E").desert, "edge")
        self.assertEqual(parse_seed_code("KMQXRT-I").desert, "inner")
        self.assertEqual(parse_seed_code("KMQXRT-C").desert, "center")
        self.assertEqual(parse_seed_code("KMQXRT-R").desert, "ring")
        self.assertTrue(parse_seed_code("KMQXRT-A").allow_adjacent_red)
        self.assertTrue(parse_seed_code("KMQXRT-P").ports)

    def test_the_order_of_the_flags_does_not_matter_and_the_case_neither(self):
        wanted = SeedCode("KMQXRT", "ring", True, True)
        for order in itertools.permutations("RAP"):
            self.assertEqual(parse_seed_code("KMQXRT-" + "".join(order)), wanted)
            self.assertEqual(parse_seed_code("kmqxrt-" + "".join(order).lower()), wanted)

    def test_a_code_is_written_in_one_fixed_order(self):
        for order in itertools.permutations("RAP"):
            self.assertEqual(format_seed_code(parse_seed_code("KMQXRT-" + "".join(order))), "KMQXRT-RAP")
        self.assertEqual(format_seed_code(parse_seed_code("kmqxrt-pe")), "KMQXRT-EP")
        self.assertEqual(format_seed_code(parse_seed_code("kmqxrt-ap")), "KMQXRT-AP")

    def test_the_desert_is_in_the_center_unless_said_otherwise(self):
        self.assertEqual(parse_seed_code("KMQXRT-F").desert, "free")
        self.assertEqual(format_seed_code(parse_seed_code("KMQXRT-F")), "KMQXRT-F")
        self.assertEqual(format_seed_code(parse_seed_code("KMQXRT-C")), "KMQXRT")   # the default is not written
        self.assertEqual(format_seed_code(parse_seed_code("KMQXRT-CP")), "KMQXRT-P")

    def test_writing_and_reading_agree_for_every_combination(self):
        for desert in (None, "free", "edge", "inner", "ring"):
            for adjacent in (False, True):
                for ports in (False, True):
                    code = SeedCode("ABCDEF", desert, adjacent, ports)
                    self.assertEqual(parse_seed_code(format_seed_code(code)), code)

    def test_a_random_seed_has_no_repeated_letter(self):
        for _ in range(500):
            seed = random_seed()
            self.assertEqual(len(set(seed)), 3, seed)
        self.assertEqual(len(set(random_seed(26))), 26)
        with self.assertRaises(ValueError):
            random_seed(27)

    def test_errors(self):
        cases = {
            "KMQXRT-EE": "twice",
            "KMQXRT-EI": "only one desert flag",
            "KMQXRT-CR": "only one desert flag",
            "KMQXRT-X": "unknown flag",
            "KMQXRT-E1": "unknown flag",
            "KMQXRT-": "nothing after",
            "-E": "empty",
            "KMQXRT-AA": "twice",
        }
        for text, fragment in cases.items():
            with self.assertRaises(SeedError, msg=text) as caught:
                parse_seed_code(text)
            self.assertIn(fragment, str(caught.exception), text)


class RandomSeeds(unittest.TestCase):
    def test_three_uppercase_letters(self):
        for _ in range(200):
            seed = random_seed()
            self.assertEqual(len(seed), 3)
            self.assertEqual(normalize_seed(seed), seed)

    def test_other_lengths(self):
        self.assertEqual(len(random_seed()), 3)
        self.assertEqual(len(random_seed(4)), 4)
        self.assertEqual(len(random_seed(10)), 10)

    def test_they_vary(self):
        self.assertGreater(len({random_seed() for _ in range(100)}), 95)


class AddButDoNotChange(unittest.TestCase):
    def test_an_option_may_add_what_the_code_does_not_say(self):
        code = parse_seed_code("KMQXRT")
        self.assertEqual(combine(code, desert="edge"), SeedCode("KMQXRT", "edge"))
        self.assertEqual(combine(code, ports=True, allow_adjacent_red=True), SeedCode("KMQXRT", None, True, True))
        self.assertEqual(combine(code, desert="free"), SeedCode("KMQXRT", "free"))
        self.assertEqual(combine(code), code)

    def test_an_option_that_agrees_is_fine(self):
        code = parse_seed_code("KMQXRT-EAP")
        self.assertEqual(combine(code, desert="edge", allow_adjacent_red=True, ports=True), code)

    def test_flags_in_the_code_stay_when_the_option_is_not_given(self):
        code = parse_seed_code("KMQXRT-RAP")
        self.assertEqual(combine(code), code)

    def test_an_option_that_contradicts_the_code_is_an_error(self):
        for stated, given in (("E", "inner"), ("E", "free"), ("F", "edge"), ("I", "edge"), ("C", "ring"), ("C", "free"), ("R", "center")):
            with self.assertRaises(SeedError, msg=(stated, given)) as caught:
                combine(parse_seed_code("KMQXRT-" + stated), desert=given)
            self.assertIn("seed code says the desert is", str(caught.exception))
            self.assertIn(given, str(caught.exception))

    def test_a_and_p_cannot_contradict_anything(self):
        # they can only be switched on, so combining never removes them
        self.assertTrue(combine(parse_seed_code("KMQXRT-A")).allow_adjacent_red)
        self.assertTrue(combine(parse_seed_code("KMQXRT-P")).ports)


if __name__ == "__main__":
    unittest.main()
