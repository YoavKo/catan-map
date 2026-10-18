import unittest

from catan_map import CatanMapError, SeedError, generate, make, parse, render_svg, serialize


class Make(unittest.TestCase):
    def test_a_seed_gives_the_board_the_code_and_the_text(self):
        made = make("KMQXRT-P")
        self.assertEqual(made.board, generate("KMQXRT", ports=True))
        self.assertEqual(str(made.code), "KMQXRT-P")
        self.assertEqual(made.text, serialize(made.board, "p", True, True))
        self.assertEqual(made.warnings, ())
        self.assertEqual(made.caption, ("KMQXRT-P", made.text))

    def test_options_add_to_the_seed_but_do_not_change_it(self):
        self.assertEqual(str(make("KMQXRT", desert="edge", ports=True, allow_adjacent_red=True).code), "KMQXRT-EAP")
        with self.assertRaises(SeedError):
            make("KMQXRT-E", desert="inner")

    def test_the_format_and_the_pipes(self):
        self.assertEqual(make("KMQXRT", fmt="s", pipes=False).text, serialize(generate("KMQXRT"), "s"))
        self.assertEqual(make("KMQXRT", fmt="paired", pipes=False).text, serialize(generate("KMQXRT"), "p"))
        self.assertIn("|", make("KMQXRT").text)
        with self.assertRaises(CatanMapError):
            make("KMQXRT", fmt="x")

    def test_a_string_is_read_with_its_warnings(self):
        made = make(string="WWWWWWWWWDWWWWWWWWW64b92b485aca538369")
        self.assertIsNone(made.code)
        self.assertEqual(made.board, parse("WWWWWWWWWDWWWWWWWWW64b92b485aca538369").board)
        self.assertTrue(any("unusual tiles" in w for w in made.warnings))
        self.assertEqual(made.caption, (made.text,))                       # no seed line

    def test_a_string_keeps_its_ports_and_can_be_given_the_default_ones(self):
        with_ports = make(string="WSGOCWSGDOWCSGOCWSG563a4b892c563b9a48X3gO3s#3cW", fmt="s", pipes=False)
        self.assertTrue(with_ports.text.endswith("X3gO3s#3cW"))
        self.assertTrue(make(string="WSGOCWSGDOWCSGOCWSG563a4b892c563b9a48", ports=True, fmt="s", pipes=False).text.endswith("3gO3s#3cW"))

    def test_seed_options_do_not_apply_to_a_string(self):
        with self.assertRaises(CatanMapError):
            make(string="WSGOCWSGDOWCSGOCWSG563a4b892c563b9a48", desert="edge")

    def test_a_seed_and_a_string_together_is_an_error(self):
        with self.assertRaises(CatanMapError):
            make("KMQXRT", string="W")

    def test_with_neither_a_random_seed_is_made(self):
        made = make()
        self.assertEqual(len(str(made.code)), 3)
        self.assertEqual(len(set(str(made.code))), 3)

    def test_bad_input_is_a_catan_map_error(self):
        for bad in ({"seed": "K2"}, {"seed": ""}, {"string": "nonsense"}, {"string": ""}):
            with self.assertRaises(CatanMapError, msg=bad):
                make(**bad)

    def test_the_result_can_be_drawn(self):
        made = make("KMQXRT", ports=True)
        self.assertIn("<svg", render_svg(made.board, made.caption))
        self.assertIn('width="600mm"', render_svg(made.board, made.caption, elements=("seed", "str")))


if __name__ == "__main__":
    unittest.main()
