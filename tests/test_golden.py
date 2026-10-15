"""Fixed seeds with the exact strings they must give.

If one of these fails, the generator now makes a different board for the same seed. That
breaks every seed anyone has shared, so it must never happen by accident: change the
algorithm only together with a new ALGORITHM version (and keep the old one working).
"""
import unittest

from catan_map import generate, serialize

CASES = [
    ("KMQXRT", {}, "CGGDWSWWCOGCGOSSOSW2a5ba8456996c433b8"),
    ("KMQXRT", {"desert": "edge"}, "CGDGWSWWCOGCGOSSOSW2a5ba8456996c433b8"),
    ("KMQXRT", {"desert": "center"}, "CGGWSWWCODGCGOSSOSW58ab94ca33645298b6"),
    ("KMQXRT", {"desert": "ring"}, "CGGWSDWWCOGCGOSSOSW2a5ba8456996c433b8"),
    ("KMQXRT", {"desert": "inner"}, "CGGWSDWWCOGCGOSSOSW2a5ba8456996c433b8"),
    ("KMQXRT", {"allow_adjacent_red": True}, "CGGDWSWWCOGCGOSSOSW956862aa485b943bc3"),
    ("KMQXRT", {"ports": True}, "CGGDWSWWCOGCGOSSOSW2a5ba8456996c433b8XcgW#3#os#"),
    ("AAAAAA", {}, "SOWSSOWDCCGCSWWOGGG258443a596ba6bc398"),
    ("ZZZZZZ", {"ports": True}, "CGDSOGCSGWOCSSGWOWW5c8528439bb646aa3933#oc3sWg"),
    ("CATAN", {"ports": True, "desert": "ring"}, "SSCOWDWGCGGSOCWSWOG3ab6b894652c9a83543cG3swo##"),
    ("A", {}, "OSCWSCGGDSOWWWOGSCGb449536a8b9625ca83"),
    ("PLAYERONE", {"allow_adjacent_red": True, "ports": True}, "CGCWGDGGWSSSOWOWOSC35245b68bc899364aaX3wCgs##3o"),
]


class FixedSeeds(unittest.TestCase):
    def test_each_seed_gives_its_string(self):
        for seed, options, expected in CASES:
            board = generate(seed, **options)
            self.assertEqual(serialize(board, "s", False, options.get("ports", False)), expected, (seed, options))

    def test_the_seed_is_case_insensitive_in_the_reference_strings_too(self):
        self.assertEqual(serialize(generate("kmqxrt")), CASES[0][2])


if __name__ == "__main__":
    unittest.main()
