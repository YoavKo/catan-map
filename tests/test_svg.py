import os
import re
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
            self.assertEqual(symbols, sorted(["dock", "sea", "edge-dark", "edge-light"] + [f"tile-{c}" for c in "WSGCOD"]), name)

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


class Mat(unittest.TestCase):
    def setUp(self):
        self.board = generate("KMQXRT", ports=True)

    def drawing(self, elements=()):
        root = ET.fromstring(render_svg(self.board, ["KMQXRT-P", "C5G8"], elements=elements))
        scale = float(re.search(r"scale\(([\d.]+)\)", next(g for g in root.findall("s:g", NS) if g.find("s:g", NS) is not None and g.find("s:g", NS).get("id") == "water").get("transform")).group(1))
        return root, scale

    def test_the_sheet_is_60_by_60_cm(self):
        root, _ = self.drawing()
        self.assertEqual((root.get("width"), root.get("height"), root.get("viewBox")), ("600mm", "600mm", "0 0 600 600"))

    def test_the_board_fits_550_by_505_mm_and_the_tokens_are_25_mm(self):
        root, scale = self.drawing()
        self.assertAlmostEqual(14 * 86.603 * scale, 550, delta=0.1)            # the board is 550 mm wide
        self.assertLessEqual(1100 * scale, 505)                                # and not higher than 505
        token = next(g for g in root.iter("{http://www.w3.org/2000/svg}g") if g.get("id") == "tokens").find("s:g", NS)
        k = float(re.search(r"scale\(([\d.]+)\)", token.get("transform")).group(1))
        radius = max(float(c.get("r")) for c in token.findall("s:circle", NS))      # the face, not a pip
        self.assertAlmostEqual(2 * radius * k * scale, 25, delta=0.05)         # 25 mm across

    def test_the_cards_come_with_costs_only(self):
        self.assertEqual(len(self.drawing()[0].findall(".//s:g[@class='costs']", NS)), 0)
        root, _ = self.drawing(("costs",))
        self.assertEqual(root.get("width"), "600mm")
        self.assertEqual(len(root.findall(".//s:g[@class='costs']", NS)), 4)

    def test_the_cards_are_turned_to_the_four_sides(self):
        root, _ = self.drawing(("costs",))
        turns = [re.search(r"rotate\((\d+)\)", g.get("transform")).group(1)
                 for g in root.findall("s:g", NS) if g.find("s:g[@class='costs']", NS) is not None]
        self.assertEqual(turns, ["180", "270", "90", "0"])

    def test_a_card_says_what_things_cost(self):
        root, _ = self.drawing(("costs",))
        words = "".join(root.find(".//s:g[@class='costs']", NS).itertext())
        for word in ("BUILDING COSTS", "Road", "[0 VP]", "Settlement", "[1 VP]", "City", "[2 VP]", "Development Card", "[? VP]"):
            self.assertIn(word, words)


class Logo(unittest.TestCase):
    PNG = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d4944415478da63fcffff3f0005fe02fea7d6c5f50000000049454e44ae426082")

    def logo_file(self, folder, name="logo.png", data=None):
        path = os.path.join(folder, name)
        with open(path, "wb") as handle:
            handle.write(self.PNG if data is None else data)
        return path

    def test_the_logo_is_embedded_above_the_bottom_right_card_and_the_seed_is_at_the_top(self):
        with tempfile.TemporaryDirectory() as folder:
            code, out, _ = run("--seed", "KMQXRT", "--svg", "-", "--elements", "logo", "--logo-img", self.logo_file(folder))
        self.assertEqual(code, 0)
        root = ET.fromstring(out)
        self.assertEqual(root.get("width"), "600mm")                       # --elements makes the sheet
        image = root.find("s:image", NS)
        self.assertTrue(image.get("href").startswith("data:image/png;base64,"))
        x, y, w, h = (float(image.get(k)) for k in ("x", "y", "width", "height"))
        self.assertGreater(x, 450)                                           # at the right
        self.assertLessEqual(x + w, 595)
        self.assertGreater(h, 60)
        self.assertEqual(root.findall("s:text", NS), [])                        # no seed or string: they were not asked for

    def test_the_seed_is_big_and_a_long_one_is_shrunk_to_fit_the_width(self):
        def seed_size(seed):
            root = ET.fromstring(render_svg(generate(seed.split("-")[0]), [seed, "C5G8"], elements=("seed",)))
            return float(root.find("s:text", NS).get("font-size"))

        self.assertEqual(seed_size("KMQXRT"), 24)                   # about 4 times the old 6 mm
        self.assertEqual(seed_size("ABC"), 24)
        for seed in ("KMQXRT-EAP", "A" * 32):
            self.assertLess(seed_size(seed), 24)
            self.assertLessEqual(len(seed) * 0.6 * seed_size(seed), 97.5)         # never wider than the space above the card

    def test_without_a_logo_there_is_no_image(self):
        self.assertNotIn("<image", render_svg(generate("KMQXRT"), elements=("costs", "seed")))

    def test_a_missing_or_unsupported_logo_is_an_error(self):
        with tempfile.TemporaryDirectory() as folder:
            code, _, err = run("--seed", "KMQXRT", "--svg", "-", "--elements", "logo", "--logo-img", os.path.join(folder, "none.png"))
            self.assertEqual(code, 2)
            self.assertIn("cannot read the logo", err)
            code, _, err = run("--seed", "KMQXRT", "--svg", "-", "--elements", "logo", "--logo-img", self.logo_file(folder, "logo.bmp"))
            self.assertEqual(code, 2)
            self.assertIn("must be one of", err)

    def test_a_logo_needs_svg(self):
        code, _, err = run("--seed", "KMQXRT", "--logo-img", "x.png")
        self.assertEqual(code, 2)
        self.assertIn("--svg", err)


class StackLayout(unittest.TestCase):
    SCALE = 0.45363
    TEXT = "C5G8Ga|WbS9W4Wc|CaO3DG3C6|G4O5S2S9|O8SbW6,XO3Gws3#c3"

    def layouts(self, seed="KMQXRT-P", string=TEXT):
        from catan_map.render_svg import stack_layout

        for shift in (300 - 300 * self.SCALE, 3 + 250 * self.SCALE):          # centred, and with a bank
            yield shift, stack_layout(seed, string, shift, self.SCALE)

    def test_the_string_is_on_one_line_above_the_seed(self):
        from catan_map.render_svg import _island_edge

        for shift, (seed_size, seed_baseline, size, baseline, top) in self.layouts():
            self.assertLess(baseline, seed_baseline - 0.75 * seed_size)          # above the seed
            self.assertLess(top, baseline)
            left = 594 - 0.6 * size * len(self.TEXT)
            for k in range(11):                                                  # it does not touch the island
                self.assertLess(_island_edge(shift, self.SCALE, baseline - 0.75 * size * k / 10), left)

    def test_the_string_is_as_large_as_it_can_be(self):
        from catan_map.render_svg import STRING_MIN, STRING_SIZE

        for _, (_, _, size, _, _) in self.layouts():
            self.assertGreaterEqual(size, STRING_MIN)
            self.assertLessEqual(size, STRING_SIZE)
        for _, (_, _, size, _, _) in self.layouts(string="C5G8"):                 # a short one gets the full size
            self.assertEqual(size, STRING_SIZE)

    def test_the_string_alone_takes_the_place_of_the_seed(self):
        for _, (_, base, size, baseline, _) in self.layouts(seed=""):
            self.assertEqual(baseline, base)
            self.assertGreater(size, 0)

    def test_the_svg_has_the_seed_and_the_whole_string_in_two_texts(self):
        root = ET.fromstring(render_svg(generate("KMQXRT", ports=True), ["KMQXRT-P", self.TEXT], elements=("seed", "str")))
        self.assertEqual([t.text for t in root.findall("s:text", NS)], ["KMQXRT-P", self.TEXT])


class Elements(unittest.TestCase):
    """--elements: what is on the sheet."""

    def sheet(self, *names, caption=("KMQXRT-P", "C5G8Ga|WbS9"), logo=None):
        return ET.fromstring(render_svg(generate("KMQXRT", ports=True), list(caption), elements=names, logo=logo))

    def test_nothing_unless_asked_for(self):
        root = self.sheet()
        self.assertEqual(root.get("width"), "600mm")
        self.assertEqual(root.findall("s:text", NS), [])
        self.assertEqual(root.findall("s:image", NS), [])
        self.assertEqual(root.findall(".//s:g[@class='costs']", NS), [])
        self.assertEqual(root.findall(".//s:g[@class='bank']", NS), [])

    def test_each_element_on_its_own(self):
        self.assertEqual(len(self.sheet("costs").findall(".//s:g[@class='costs']", NS)), 4)
        self.assertEqual(len(self.sheet("bank").findall(".//s:g[@class='slot']", NS)), 6)
        self.assertEqual([t.text for t in self.sheet("seed").findall("s:text", NS)], ["KMQXRT-P"])
        self.assertEqual([t.text for t in self.sheet("str").findall("s:text", NS)], ["C5G8Ga|WbS9"])
        self.assertEqual(len(self.sheet("logo", logo="data:image/png;base64,AA==").findall("s:image", NS)), 1)

    def test_a_string_given_alone_is_not_taken_for_a_seed(self):
        root = ET.fromstring(render_svg(generate("KMQXRT"), ["C5G8"], elements=("seed", "str")))
        self.assertEqual([t.text for t in root.findall("s:text", NS)], ["C5G8"])      # only the string, once

    def test_without_the_costs_card_the_seed_sits_lower(self):
        with_card = float(self.sheet("costs", "seed").find("s:text", NS).get("y"))
        without = float(self.sheet("seed").find("s:text", NS).get("y"))
        self.assertGreater(without, with_card)

    def test_the_logo_element_needs_an_image_and_unknown_names_are_errors(self):
        with self.assertRaises(CatanMapError):
            self.sheet("logo")
        with self.assertRaises(CatanMapError) as caught:
            self.sheet("seeds")
        self.assertIn("costs, bank, seed, str, logo", str(caught.exception))

    def test_command_line_lists(self):
        def texts(*args):
            code, out, err = run("--seed", "KMQXRT-P", "--svg", "-", *args)
            self.assertEqual(code, 0, err)
            return ET.fromstring(out)

        self.assertEqual(len(texts("--elements", "costs", "bank").findall(".//s:g[@class='costs']", NS)), 4)
        self.assertEqual(len(texts("--elements", "costs,bank").findall(".//s:g[@class='slot']", NS)), 6)    # commas work too
        self.assertEqual(len(texts("--elements", "seed", "str").findall("s:text", NS)), 2)
        bare = texts("--elements")                                                        # no names: the bare sheet
        self.assertEqual(bare.get("width"), "600mm")
        self.assertEqual(bare.findall("s:text", NS), [])
        everything = texts("--elements", "all")
        self.assertEqual(len(everything.findall(".//s:g[@class='costs']", NS)), 4)
        self.assertEqual(len(everything.findall(".//s:g[@class='slot']", NS)), 6)
        self.assertEqual(len(everything.findall("s:text", NS)), 2)
        self.assertEqual(everything.findall("s:image", NS), [])                            # 'all' has a logo only with --logo-img

    def test_command_line_errors(self):
        self.assertEqual(run("--seed", "KMQXRT", "--svg", "-", "--elements", "nonsense")[0], 2)
        code, _, err = run("--seed", "KMQXRT", "--svg", "-", "--elements", "logo")
        self.assertEqual(code, 2)
        self.assertIn("--logo-img", err)
        code, _, err = run("--seed", "KMQXRT", "--svg", "-", "--elements", "costs", "--logo-img", "x.png")
        self.assertEqual(code, 2)
        self.assertIn("includes logo", err)
        code, _, err = run("--seed", "KMQXRT", "--svg", "-", "--logo-img", "x.png")
        self.assertEqual(code, 2)
        self.assertIn("includes logo", err)

    def test_the_old_flags_are_gone(self):
        for flag in ("--mat", "--costs", "--bank"):
            self.assertEqual(run("--seed", "KMQXRT", "--svg", "-", flag)[0], 2, flag)


class FitLogo(unittest.TestCase):
    """The logo is as big as it can be without touching the island or the other things."""

    SCALE = 0.45363

    def shifts(self):
        return {"centred": 300 - 300 * self.SCALE, "with a bank": 3 + 250 * self.SCALE}

    def test_it_clears_the_island_the_top_right_card_and_the_seed_for_any_shape(self):
        from catan_map.render_svg import CARD_BOTTOM, _island_edge, fit_logo

        for name, shift in self.shifts().items():
            for aspect in (0.3, 0.5, 1, 2, 3, 5):
                x, y, w, h = fit_logo(aspect, shift, self.SCALE, 485)
                self.assertAlmostEqual(w / h, aspect, places=3)
                self.assertGreaterEqual(y, CARD_BOTTOM)                       # below the top right card
                self.assertLessEqual(y + h, 485)                              # above the seed
                self.assertLessEqual(x + w, 595)
                for step in range(0, 101):                                    # the island is further left at every height
                    self.assertLess(_island_edge(shift, self.SCALE, y + h * step / 100), x, (name, aspect, step))

    def test_it_is_as_big_as_possible(self):
        from catan_map.render_svg import fit_logo

        shift = self.shifts()["centred"]
        _, _, w, h = fit_logo(1, shift, self.SCALE, 485)
        bigger = fit_logo(1, shift, self.SCALE, 485 + 0.0)
        self.assertEqual((w, h), bigger[2:])
        # a box 1 mm taller (and wider) would not fit
        from catan_map.render_svg import _island_edge, LOGO_GAP
        top = 485 - (h + 1)
        left = 595 - (w + 1)
        worst = max(_island_edge(shift, self.SCALE, top + (h + 1) * s / 40) for s in range(41))
        self.assertTrue(left < worst + LOGO_GAP or top < 125 + LOGO_GAP)

    def test_the_logo_in_the_svg_follows_its_shape(self):
        import struct as _struct

        def with_logo(width, height):
            png = bytes.fromhex("89504e470d0a1a0a0000000d49484452") + _struct.pack(">II", width, height) + b"\x08\x06\x00\x00\x00"
            import base64 as _b64
            uri = "data:image/png;base64," + _b64.b64encode(png).decode()
            root = ET.fromstring(render_svg(generate("KMQXRT"), ["KMQXRT"], elements=("logo",), logo=uri))
            image = root.find("s:image", NS)
            return float(image.get("width")) / float(image.get("height"))

        self.assertAlmostEqual(with_logo(100, 100), 1, places=2)
        self.assertAlmostEqual(with_logo(300, 100), 3, places=2)
        self.assertAlmostEqual(with_logo(100, 250), 0.4, places=2)


class Bank(unittest.TestCase):
    def setUp(self):
        self.board = generate("KMQXRT", ports=True)

    def test_the_bank_has_a_place_for_each_resource_and_the_development_cards(self):
        root = ET.fromstring(render_svg(self.board, ["KMQXRT"], elements=("bank",)))
        self.assertEqual(root.get("width"), "600mm")
        slots = root.findall(".//s:g[@class='bank']/s:g[@class='slot']", NS)
        self.assertEqual([slot.get("data-kind") for slot in slots], ["C", "W", "S", "G", "O", "dev"])
        self.assertEqual(root.findall(".//s:g[@class='bank']//s:text", NS), [])           # no text in the bank
        for slot in slots:                                                               # an outline, with no fill
            self.assertEqual(slot.find("s:rect", NS).get("fill"), "none")

    def test_no_bank_unless_asked(self):
        self.assertNotIn('class="bank"', render_svg(self.board, elements=("costs",)))

    def test_the_slots_are_the_size_of_a_playing_card(self):
        root = ET.fromstring(render_svg(self.board, elements=("bank",)))
        for slot in root.findall(".//s:g[@class='slot']", NS):
            rect = slot.find("s:rect", NS)
            self.assertEqual((float(rect.get("width")), float(rect.get("height"))), (57, 89))     # bridge size, 57 x 89 mm

    def test_the_island_moves_up_to_make_room_and_the_bank_fits_under_it(self):
        from catan_map.render_svg import CARD_MARGIN, MAT_MM
        from catan_map.svg_cards import BANK_BOX, CARD_WIDTH

        x, y, w, h = BANK_BOX
        self.assertGreater(x, CARD_MARGIN + 72)                                  # right of the bottom left card (turned: 72 wide)
        self.assertLess(x + w, MAT_MM - CARD_MARGIN - CARD_WIDTH)                # left of the bottom right card
        self.assertLessEqual(y + h, MAT_MM)
        with_bank = ET.fromstring(render_svg(self.board, elements=("bank",)))
        without = ET.fromstring(render_svg(self.board, elements=()))
        shift = lambda root: float(re.search(r"translate\(300 ([-\d.]+)\)", next(g for g in root.findall("s:g", NS) if g.find("s:g", NS) is not None and g.find("s:g", NS).get("id") == "water").get("transform")).group(1))
        self.assertLess(shift(with_bank), shift(without))                         # moved up
        self.assertGreaterEqual(y, shift(with_bank) + 850 * 0.45363)              # the island ends above the bank
        self.assertAlmostEqual(shift(without), 300 - 300 * 0.45363, delta=0.1)    # without a bank it stays centred

    def test_the_seed_and_string_are_under_the_logo_above_the_bottom_right_card(self):
        root = ET.fromstring(render_svg(self.board, ["KMQXRT-P", "C5G8"], elements=("costs", "seed", "str")))
        texts = root.findall("s:text", NS)
        self.assertEqual([t.text for t in texts], ["KMQXRT-P", "C5G8"])
        for text in texts:
            self.assertEqual(text.get("text-anchor"), "end")
            self.assertGreater(float(text.get("x")), 550)                        # at the right
            self.assertLess(float(text.get("y")), 523)                           # above the card (it starts at 523)

    def test_bank_option(self):
        code, out, _ = run("--seed", "KMQXRT", "--svg", "-", "--elements", "bank")
        self.assertEqual(code, 0)
        self.assertEqual(out.count('class="slot"'), 6)
        self.assertEqual(run("--seed", "KMQXRT", "--elements", "bank")[0], 2)      # needs --svg


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
        for flag in (["--tiles", "plain"], ["--elements"], ["--elements", "costs"]):
            code, _, err = run("--seed", "KMQXRT", *flag)
            self.assertEqual(code, 2, flag)
            self.assertIn("--svg", err)

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
