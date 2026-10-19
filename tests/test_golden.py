"""Fixed seeds with the exact strings they must give.

If one of these fails, the generator now makes a different board for the same seed. That
breaks every seed anyone has shared, so it must never happen by accident: change the
algorithm only together with a new ALGORITHM version (and keep the old one working).
"""
import unittest

from catan_map import generate, serialize

CASES = [
    ("KMQXRT", {}, "CGGWSWWCODGCGOSSOSW58ab94ca33645298b6"),
    ("KMQXRT", {"desert": "free"}, "CGGDWSWWCOGCGOSSOSW2a5ba8456996c433b8"),
    ("KMQXRT", {"desert": "edge"}, "CGDGWSWWCOGCGOSSOSW2a5ba8456996c433b8"),
    ("KMQXRT", {"desert": "center"}, "CGGWSWWCODGCGOSSOSW58ab94ca33645298b6"),
    ("KMQXRT", {"desert": "ring"}, "CGGWSDWWCOGCGOSSOSW2a5ba8456996c433b8"),
    ("KMQXRT", {"desert": "inner"}, "CGGWSDWWCOGCGOSSOSW2a5ba8456996c433b8"),
    ("KMQXRT", {"desert": "free", "allow_adjacent_red": True}, "CGGDWSWWCOGCGOSSOSW956862aa485b943bc3"),
    ("KMQXRT", {"desert": "free", "ports": True}, "CGGDWSWWCOGCGOSSOSW2a5ba8456996c433b8XcgW#3#os3"),
    ("AAAAAA", {"desert": "free"}, "SOWSSOWDCCGCSWWOGGG258443a596ba6bc398"),
    ("ZZZZZZ", {"desert": "free", "ports": True}, "CGDSOGCSGWOCSSGWOWW892bb865a4a395634cX#sG#3#Cow"),
    ("CATAN", {"ports": True, "desert": "ring"}, "SSCOWDWGCGGSOCWSWOG3ab6b894652c9a83543cG3swo##"),
    ("ZZZZZZ", {"desert": "free", "allow_adjacent_low_high": True}, "CGDSOGCSGWOCSSGWOWW5c8528439bb646aa39"),   # the old board of this seed: its 2 and 12 touch
    ("KMQXRT", {"no_same_neighbours": True}, "WGSGSWOWCDCSOWOGCGS3836b4b59a29c6485a"),
    ("KMQXRT", {"no_same_neighbours": True, "ports": True}, "WGSGSWOWCDCSOWOGCGS3836b4b59a29c6485a333w3OcGS"),
    ("ABC", {"no_same_neighbours": True, "desert": "edge", "allow_adjacent_low_high": True}, "WGCGSOWOWGCSCOWGSDS896954ab2cb683a345"),
    ("A", {"desert": "free"}, "OSCWSCGGDSOWWWOGSCGb449536a8b9625ca83"),
    ("PLAYERONE", {"desert": "free", "allow_adjacent_red": True, "ports": True}, "CGCWGDGGWSSSOWOWOSC35245b68bc899364aaX3wCgs##3o"),
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
