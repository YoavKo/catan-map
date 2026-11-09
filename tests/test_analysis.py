import unittest

from catan_map import analyze, generate, make, parse

# seed, string, score, passes, violations, equal pairs, pips W/S/G/C/O, best vertex, 10+, 11+, spread, std
CASES = [
    ("JQL", "G8W3O5|C2OaSaW9|W6S4DGbC8|GcS3C5O4|G6WbS9", 14.6, True, [], 1, [13, 12, 13, 10, 10], 11, 6, 3, 3, 0.46),
    ("PLYG", "O5S8W5|ScW3G2G8|C6G9DSbCa|O3W4O9G4|S6WaCb", 9.6, True, [], 0, [12, 13, 13, 10, 10], 11, 9, 3, 3, None),
    ("DECK", "GbC6O5|S8W5C3W4|G9G2DSaWa|O6S3O4G8|C9WbSc", 28.7, True, [], 1, [12, 11, 12, 11, 12], 11, 10, 7, 1, 1.57),
    ("SIP", "C5GcW9|ObS4O6C3|W9G6DSaG8|S2WbC5Sa|W8O4G3", 22.6, True, [], 1, [15, 10, 13, 10, 10], 11, 10, 3, None, None),
    ("CATAN", "S6ScC6|OaW3W4Gb|C5G8DG8S3|O9C9W4S2|WbOaG5", 47.1, False, ["vertex"], 1, [10, 9, 16, 13, 10], 13, 10, 3, 7, 2.98),
]
INNER_OUTER = {"JQL": (0, 6), "PLYG": (1, 8), "DECK": (3, 7), "SIP": (3, 7), "CATAN": (4, 6)}


class Analysis(unittest.TestCase):
    def test_the_reference_boards(self):
        for seed, text, score, passes, violations, equal, pips, best, ge10, ge11, spread, std in CASES:
            with self.subTest(seed=seed):
                made = make(seed)
                self.assertEqual(made.text, text)
                a = made.analysis
                self.assertEqual(a["score"], score)
                self.assertEqual(a["passes_hard"], passes)
                self.assertEqual(a["violations"], violations)
                self.assertEqual(a["equal_pairs"], equal)
                self.assertEqual(list(a["pips"].values()), pips)
                self.assertEqual(a["best_vertex"]["pips"], best)
                self.assertEqual((a["vertices_ge10"], a["vertices_ge11"]), (ge10, ge11))
                self.assertEqual((a["ge10_inner"], a["ge10_outer"]), INNER_OUTER[seed])
                if spread is not None:
                    self.assertEqual(a["pip_spread"], spread)
                if std is not None:
                    self.assertEqual(a["pip_std_vs_fair"], std)
                self.assertEqual(sum(a["pips"].values()), 58)

    def test_labels(self):
        self.assertEqual(analyze(generate("JQL"))["label"], "balanced")
        self.assertEqual(analyze(generate("CATAN"))["label"], "unbalanced")

    def test_the_best_vertex_names_its_tiles(self):
        tiles = analyze(generate("JQL"))["best_vertex"]["tiles"]
        self.assertEqual(len(tiles), 3)
        self.assertTrue(all(len(t) == 2 for t in tiles))

    def test_a_string_with_6_next_to_8_breaks_the_rule(self):
        board = parse("G6W8O5|C2OaSaW9|W6S4DGbC8|GcS3C5O4|G6WbS9").board
        a = analyze(board)
        self.assertIn("6/8", a["violations"])
        self.assertFalse(a["passes_hard"])
        self.assertEqual(a["label"], "unbalanced")

    def test_analysis_does_not_change_the_board(self):
        made = make("KMQXRT")
        before = (made.board, made.text)
        made.analysis
        self.assertEqual((made.board, made.text), before)


if __name__ == "__main__":
    unittest.main()
