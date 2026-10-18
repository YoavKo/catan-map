import os
import tempfile
import unittest
import xml.etree.ElementTree as ET

from catan_map import CatanMapError, generate, parse
from catan_map.render_svg import render_svg
from catan_map.svg_tiles import TILE_SET_NAMES, preview_svg, tile_defs

from tests.test_cli import run

NS = {"s": "http://www.w3.org/2000/svg"}


def uses(root, prefix):
    return [u for u in root.iter("{http://www.w3.org/2000/svg}use") if u.get("href", "").startswith(prefix)]


class RenderSvg(unittest.TestCase):
    def setUp(self):
        self.board = generate("KMQXRT", ports=True)
        self.root = ET.fromstring(render_svg(self.board, ["KMQXRT-P", "ABC"]))

    def test_is_well_formed_svg(self):
        self.assertEqual(self.root.tag, "{http://www.w3.org/2000/svg}svg")

    def test_has_19_land_tiles_with_the_right_kinds(self):
        kinds = [u.get("href")[-1] for u in uses(self.root, "#tile-")]
        self.assertEqual(kinds, list(self.board.tiles))

    def test_has_18_tokens_with_the_right_numbers(self):
        from catan_map.board import TOKEN_VALUES

        group = next(g for g in self.root.iter("{http://www.w3.org/2000/svg}g") if g.get("id") == "tokens")
        numbers = [g.find("s:text", NS).text for g in group.findall("s:g", NS)]
        wanted = [str(TOKEN_VALUES[t]) for t in self.board.tokens if t is not None]
        self.assertEqual(numbers, wanted)

    def test_ring_is_18_sea_tiles_and_9_of_them_are_ports(self):
        water = next(g for g in self.root.iter("{http://www.w3.org/2000/svg}g") if g.get("id") == "water")
        self.assertEqual(len(water), 18)
        self.assertEqual(len(water.findall("s:use", NS)), 9)                # plain sea
        self.assertEqual(len([g for g in water.findall("s:g", NS)]), 9)     # ports

    def test_caption_and_description(self):
        texts = [t.text for t in self.root.findall("s:text", NS)]
        self.assertEqual(texts, ["KMQXRT-P", "ABC"])
        self.assertIn("KMQXRT-P", self.root.find("s:desc", NS).text)

    def test_same_board_gives_the_same_text(self):
        self.assertEqual(render_svg(self.board), render_svg(generate("KMQXRT", ports=True)))

    def test_every_tile_set_is_well_formed_and_complete(self):
        for name in TILE_SET_NAMES:
            ET.fromstring(preview_svg(name))
            defs = ET.fromstring(tile_defs(name).replace("<defs>", '<defs xmlns="http://www.w3.org/2000/svg">', 1))
            symbols = sorted(sym.get("id") for sym in defs.iter("{http://www.w3.org/2000/svg}symbol"))
            self.assertEqual(symbols, sorted(["dock", "sea"] + [f"tile-{c}" for c in "WSGCOD"]), name)

    def test_every_tile_set_draws_a_whole_board(self):
        for name in TILE_SET_NAMES:
            root = ET.fromstring(render_svg(self.board, tiles=name))
            self.assertEqual(len(uses(root, "#tile-")), 19, name)

    def test_the_sets_look_different_and_the_default_is_realistic(self):
        texts = {name: render_svg(self.board, tiles=name) for name in TILE_SET_NAMES}
        self.assertEqual(len(set(texts.values())), 3)
        self.assertEqual(render_svg(self.board), texts["realistic"])
        self.assertLess(len(texts["plain"]), len(texts["basic"]))

    def test_an_unknown_tile_set(self):
        with self.assertRaises(CatanMapError):
            render_svg(self.board, tiles="fancy")

    def test_a_board_that_is_not_the_standard_mix_can_be_drawn(self):
        board = parse("WWWWWWWWWDWWWWWWWWW64b92b485aca538369").board
        root = ET.fromstring(render_svg(board))
        self.assertEqual([u.get("href")[-1] for u in uses(root, "#tile-")].count("W"), 18)


class CommandLine(unittest.TestCase):
    def test_svg_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "board.svg")
            code, out, _ = run("--seed", "KMQXRT", "--svg", path)
            self.assertEqual(code, 0)
            self.assertIn("svg:", out)
            ET.parse(path)

    def test_caption_uses_the_chosen_format(self):
        code, out, _ = run("--seed", "KMQXRT-P", "--svg", "-", "--format", "paired")
        self.assertEqual(code, 0)
        texts = [t.text for t in ET.fromstring(out).findall("s:text", NS)]
        self.assertEqual(texts, ["KMQXRT-P", "C5G8Ga|WbS9W4Wc|CaO3DG3C6|G4O5S2S9|O8SbW6,XO3Gws3#c3"])

    def test_tiles_option(self):
        outputs = {}
        for name in ("basic", "realistic", "plain"):
            code, out, _ = run("--seed", "KMQXRT", "--svg", "-", "--tiles", name)
            self.assertEqual(code, 0)
            ET.fromstring(out)
            outputs[name] = out
        self.assertEqual(len(set(outputs.values())), 3)
        self.assertEqual(run("--seed", "KMQXRT", "--svg", "-")[1], outputs["realistic"])

    def test_tiles_needs_svg(self):
        code, _, err = run("--seed", "KMQXRT", "--tiles", "plain")
        self.assertEqual(code, 2)
        self.assertIn("--svg", err)

    def test_a_non_standard_string_makes_an_svg_with_a_warning(self):
        code, out, err = run("--string", "WWWWWWWWWDWWWWWWWWW64b92b485aca538369", "--svg", "-")
        self.assertEqual(code, 0)
        ET.fromstring(out)
        self.assertIn("warning: unusual tiles", err)

    def test_svg_to_terminal_keeps_stdout_pure(self):
        code, out, err = run("--seed", "KMQXRT", "--svg", "-")
        self.assertEqual(code, 0)
        ET.fromstring(out)
        self.assertIn("seed:", err)

    def test_unwritable_path_is_an_error(self):
        code, _, err = run("--seed", "KMQXRT", "--svg", os.path.join(tempfile.gettempdir(), "no", "such", "x.svg"))
        self.assertEqual(code, 2)
        self.assertIn("cannot write", err)


if __name__ == "__main__":
    unittest.main()
