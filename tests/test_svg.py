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
        self.assertEqual(len(set(texts.values())), 4)
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

    def test_a_card_says_what_things_cost_in_hebrew_by_default(self):
        root, _ = self.drawing(("costs",))
        words = "".join(root.find(".//s:g[@class='costs']", NS).itertext())
        for word in ("עלויות בנייה", "דרך", 'נק"נ', "יישוב", "עיר", "קלף התפתחות", "[0 ", "[1 ", "[2 ", "[? "):
            self.assertIn(word, words)
        self.assertNotIn("BUILDING COSTS", words)

    def test_a_card_in_english(self):
        root = ET.fromstring(render_svg(self.board, ["KMQXRT-P", "C5G8"], elements=("costs",), lang="en"))
        words = "".join(root.find(".//s:g[@class='costs']", NS).itertext())
        for word in ("BUILDING COSTS", "Road", "[0 VP]", "Settlement", "[1 VP]", "City", "[2 VP]", "Development Card", "[? VP]"):
            self.assertIn(word, words)
        self.assertNotIn("עלויות", words)

    def test_the_hebrew_card_is_mirrored(self):
        he = ET.fromstring(render_svg(self.board, elements=("costs",), lang="he"))
        en = ET.fromstring(render_svg(self.board, elements=("costs",), lang="en"))
        card = lambda root: root.find(".//s:g[@class='costs']", NS)
        self.assertEqual(card(he).get("data-lang"), "he")
        self.assertEqual(card(en).get("data-lang"), "en")
        he_names = [t for t in card(he).findall("s:text", NS) if t.get("direction") == "rtl"]
        self.assertEqual(len(he_names), 5)                                  # the title and the four lines
        self.assertEqual(len([t for t in card(en).findall("s:text", NS) if t.get("direction")]), 0)
        he_lines = [t for t in he_names if t.get("text-anchor") != "middle"]
        self.assertTrue(all(float(t.get("x")) > 100 for t in he_lines))      # the names start at the right
        en_lines = [t for t in card(en).findall("s:text", NS) if t.get("text-anchor") != "middle"]
        self.assertTrue(all(float(t.get("x")) < 20 for t in en_lines))       # and in English at the left

    def test_the_chips_are_at_the_left_in_hebrew_with_the_first_one_next_to_the_name(self):
        from catan_map.svg_cards import _icons

        def clay_x(svg):
            """The x of the clay chip and of the wood chip in a row of chips."""
            xs = {kind: float(x) for kind, x in re.findall(r'<g class="chip" data-kind="(\w)" transform="translate\(([\d.]+) ', svg)}
            return xs["C"], xs["W"]

        he_clay, he_wood = clay_x(_icons("CW", 0, None, rtl=True))
        en_clay, en_wood = clay_x(_icons("CW", 0, None, rtl=False))
        self.assertLess(max(he_clay, he_wood), 40)                          # Hebrew: at the left
        self.assertGreater(min(en_clay, en_wood), 80)                       # English: at the right
        self.assertGreater(he_clay, he_wood)                                # Hebrew: the first chip (clay) is the rightmost, by the name
        self.assertLess(en_clay, en_wood)                                   # English: the first chip is the leftmost

    def test_an_unknown_language(self):
        with self.assertRaises(CatanMapError):
            render_svg(self.board, elements=("costs",), lang="fr")

    def test_the_language_option_on_the_command_line(self):
        code, out, _ = run("--seed", "KMQXRT", "--svg", "-", "--elements", "costs", "--lang", "en")
        self.assertEqual(code, 0)
        self.assertIn("BUILDING COSTS", out)
        code, out, _ = run("--seed", "KMQXRT", "--svg", "-", "--elements", "costs")
        self.assertIn("עלויות בנייה", out)                                  # Hebrew by default
        self.assertEqual(run("--seed", "KMQXRT", "--lang", "en")[0], 2)      # needs --svg
        self.assertEqual(run("--seed", "KMQXRT", "--svg", "-", "--lang", "fr")[0], 2)

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
        self.assertLessEqual(x + w, 592)
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
                self.assertLessEqual(x + w, 592)
                for step in range(0, 101):                                    # the island is further left at every height
                    self.assertLess(_island_edge(shift, self.SCALE, y + h * step / 100), x, (name, aspect, step))

    def test_it_is_as_big_as_possible(self):
        from catan_map.render_svg import fit_logo

        shift = self.shifts()["centred"]
        _, _, w, h = fit_logo(1, shift, self.SCALE, 485)
        bigger = fit_logo(1, shift, self.SCALE, 485 + 0.0)
        self.assertEqual((w, h), bigger[2:])
        # a box 1 mm taller (and wider) would not fit
        from catan_map.render_svg import _island_edge, LOGO_GAP, CARD_BOTTOM, STACK_RIGHT
        top = 485 - (h + 1)
        left = STACK_RIGHT - (w + 1)
        worst = max(_island_edge(shift, self.SCALE, top + (h + 1) * s / 40) for s in range(41))
        self.assertTrue(left < worst + LOGO_GAP or top < CARD_BOTTOM + LOGO_GAP)

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


class DesertLogo(unittest.TestCase):
    URI = "data:image/png;base64,iVBORw0KGgo="

    def setUp(self):
        self.board = generate("KMQXRT")             # the desert is in the middle

    def images(self, **options):
        root = ET.fromstring(render_svg(self.board, **options))
        group = next((g for g in root.iter("{http://www.w3.org/2000/svg}g") if g.get("id") == "desert-logo"), None)
        return [] if group is None else group.findall("s:image", NS)

    def test_none_without_a_logo(self):
        self.assertEqual(self.images(), [])

    def test_the_logo_is_in_the_middle_of_the_desert_as_big_as_most_of_the_tile(self):
        (image,) = self.images(desert_logo=self.URI)
        x, y, w, h = (float(image.get(k)) for k in ("x", "y", "width", "height"))
        self.assertAlmostEqual(x + w / 2, 0, places=1)                     # the desert is the centre tile: (0, 300) in the board's units
        self.assertAlmostEqual(y + h / 2, 300, places=1)
        self.assertAlmostEqual(w, 62 * 2.4, places=1)                      # 2.4 tokens across (a token is 62 units, the tile 173)
        self.assertEqual(image.get("href"), self.URI)

    def test_on_the_sheet_it_is_60_mm(self):
        root = ET.fromstring(render_svg(self.board, elements=(), desert_logo=self.URI))
        board = next(g for g in root.findall("s:g", NS) if g.find("s:g", NS) is not None and g.find("s:g", NS).get("id") == "water")
        scale = float(re.search(r"scale\(([\d.]+)\)", board.get("transform")).group(1))
        image = next(i for i in root.iter("{http://www.w3.org/2000/svg}image"))
        self.assertAlmostEqual(float(image.get("width")) * scale, 60, delta=0.1)

    def test_it_follows_the_desert_wherever_it_is(self):
        board = generate("KMQXRT", desert="edge")
        root = ET.fromstring(render_svg(board, desert_logo=self.URI))
        group = next(g for g in root.iter("{http://www.w3.org/2000/svg}g") if g.get("id") == "desert-logo")
        (image,) = group.findall("s:image", NS)
        self.assertNotAlmostEqual(float(image.get("x")) + 31, 0, places=0)  # not in the middle any more

    def test_the_command_line(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "logo.png")
            with open(path, "wb") as handle:
                handle.write(bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d4944415478da63fcffff3f0005fe02fea7d6c5f50000000049454e44ae426082"))
            code, out, _ = run("--seed", "KMQXRT", "--svg", "-", "--desert-logo", path)
            self.assertEqual(code, 0)
            self.assertIn('<g id="desert-logo"><image', out)
        self.assertEqual(run("--seed", "KMQXRT", "--desert-logo", "x.png")[0], 2)           # needs --svg
        self.assertEqual(run("--seed", "KMQXRT", "--svg", "-", "--desert-logo", "/nonexistent.png")[0], 2)


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
            self.assertEqual((float(rect.get("width")), float(rect.get("height"))), (54.44, 85))     # the bridge size shortened to 85 mm, same ratio

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
        self.assertGreaterEqual(y, shift(with_bank) + 800 * 0.45363)              # the island ends above the bank
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


class BankWithoutCosts(unittest.TestCase):
    URI = "data:image/png;base64," + "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

    def render(self, elements):
        return ET.fromstring(render_svg(generate("KMQXRT"), ("KMQXRT",), elements=elements, logo=self.URI))

    def test_the_bank_moves_to_the_left_margin_without_the_cost_cards(self):
        with_costs = render_svg(generate("KMQXRT"), elements=("costs", "bank"))
        without = render_svg(generate("KMQXRT"), elements=("bank",))
        self.assertNotIn('<g transform="translate(', with_costs.split('<g class="bank">')[0][-40:])
        self.assertIn('translate(-76 0)"><g class="bank">', without)

    def test_the_logo_stays_clear_of_the_bank(self):
        root = self.render(("bank", "logo"))
        image = next(i for i in root.iter("{http://www.w3.org/2000/svg}image") if i.get("preserveAspectRatio") == "xMaxYMax meet")
        self.assertGreaterEqual(float(image.get("x")), 5 + 387 + 4)             # right of the bank strip (it ends at 392 mm)


class OneBigHexagon(unittest.TestCase):
    def test_the_sea_is_cut_to_a_regular_hexagon(self):
        root = ET.fromstring(render_svg(generate("KMQXRT")))
        svg = "{http://www.w3.org/2000/svg}"
        water = next(g for g in root.iter(svg + "g") if g.get("id") == "water")
        self.assertEqual(water.get("clip-path"), "url(#clip-sea-outline)")
        clip = next(c for c in root.iter(svg + "clipPath") if c.get("id") == "clip-sea-outline")
        points = [tuple(float(v) for v in p.split(",")) for p in clip.find("s:polygon", NS).get("points").split()]
        self.assertEqual(len(points), 6)
        side = [((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5 for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1])]
        self.assertAlmostEqual(max(side), min(side), places=2)                      # regular
        self.assertAlmostEqual(min(p[1] for p in points), -200, places=1)           # the shoulders of the top and bottom sea rows
        self.assertAlmostEqual(max(p[1] for p in points), 800, places=1)

    def test_the_picture_is_smaller_by_the_cut_points(self):
        view = ET.fromstring(render_svg(generate("KMQXRT"))).get("viewBox").split()
        self.assertAlmostEqual(float(view[3]), 1000 + 2 * 24, places=1)             # was 1100 + the margins


class SeaAndFrame(unittest.TestCase):
    def test_the_sea_tiles_have_no_dark_edge(self):
        from catan_map.svg_tiles import TILE_SET_NAMES, tile_defs
        for name in TILE_SET_NAMES:
            sea = re.search(r'<symbol id="sea".*?</symbol>', tile_defs(name), re.S).group(0)
            for stroke in re.findall(r'stroke="(#[0-9a-f]{6})" stroke-width="3"', sea):
                self.assertNotIn(stroke, ("#1a5a94", "#2b76b5"))               # the dark blue edge is gone

    def test_nothing_is_closer_to_the_edge_than_the_frame(self):
        from catan_map.render_svg import FRAME, INSET, MAT_MM
        from catan_map.svg_cards import BANK_BOX
        self.assertEqual(BANK_BOX[1] + BANK_BOX[3], MAT_MM - INSET)
        self.assertEqual((FRAME, INSET), (5, 8))                                   # a 5 mm frame, and 3 mm of space inside it

    def test_the_island_is_in_the_middle_of_what_is_above_the_bank(self):
        from catan_map.render_svg import INSET as FRAME
        from catan_map.svg_cards import BANK_BOX
        root = ET.fromstring(render_svg(generate("KMQXRT"), elements=("bank",)))
        board = next(g for g in root.findall("s:g", NS) if g.find("s:g", NS) is not None and g.find("s:g", NS).get("id") == "water")
        shift, scale = (float(v) for v in re.search(r"translate\(300 ([-\d.]+)\) scale\(([\d.]+)\)", board.get("transform")).groups())
        top, bottom = shift - 200 * scale, shift + 800 * scale
        self.assertAlmostEqual(top - FRAME, BANK_BOX[1] - bottom, delta=0.5)      # as far from the top frame as from the bank


class GoldFrame(unittest.TestCase):
    def test_a_sheet_has_a_gold_frame_5_mm_wide_and_a_screen_image_has_none(self):
        sheet = ET.fromstring(render_svg(generate("KMQXRT"), elements=()))
        frame = next(g for g in sheet.iter("{http://www.w3.org/2000/svg}g") if g.get("id") == "frame")
        path = frame.find("s:path", NS).get("d")
        self.assertIn("M5,5V595H595V5Z", path)                                    # the inner edge: 5 mm from every side
        self.assertNotIn('id="frame"', render_svg(generate("KMQXRT")))


class IllustratedTiles(unittest.TestCase):
    def test_the_tiles_are_pictures_with_their_own_border(self):
        svg = render_svg(generate("KMQXRT"), tiles="illustrated")
        root = ET.fromstring(svg)
        symbols = [s for s in root.iter("{http://www.w3.org/2000/svg}symbol") if s.get("id", "").startswith("tile-")]
        self.assertEqual(len(symbols), 6)
        for symbol in symbols:
            image = symbol.find("s:image", NS)
            self.assertTrue(image.get("href").startswith("data:image/webp;base64,"))
            self.assertAlmostEqual(float(image.get("width")), 173.2, places=1)         # as wide as a hexagon, and 200 high
        edges = next(g for g in root.iter("{http://www.w3.org/2000/svg}g") if g.get("id") == "edges")
        self.assertEqual(len(edges), 0)                                               # no border is drawn round them

    def test_it_is_a_tile_set_of_the_command_line(self):
        code, out, _ = run("--seed", "KMQXRT", "--svg", "-", "--tiles", "illustrated")
        self.assertEqual(code, 0)
        self.assertIn("data:image/webp;base64", out)


class BankPictures(unittest.TestCase):
    def test_with_the_illustrated_tiles_each_slot_has_its_tile_as_a_background(self):
        root = ET.fromstring(render_svg(generate("KMQXRT"), elements=("bank",), tiles="illustrated"))
        slots = [g for g in root.iter("{http://www.w3.org/2000/svg}g") if g.get("class") == "slot"]
        self.assertEqual(len(slots), 6)
        for slot in slots[:5]:
            kind = slot.get("data-kind")
            self.assertEqual(slot.find(".//s:use", NS).get("href"), f"#tile-{kind}")      # under the icon, which is drawn after it
        self.assertIsNone(slots[5].find(".//s:use", NS))                                  # the development cards keep their plain slot

    def test_the_other_tile_sets_have_the_same_pictures_in_their_slots(self):
        for name in ("realistic", "basic", "plain"):
            svg = render_svg(generate("KMQXRT"), elements=("bank",), tiles=name)
            self.assertEqual(svg.count("bank-clip-"), 10, name)                           # five clips, each used once
            self.assertEqual(svg.count("data:image/webp;base64"), 5, name)               # the five pictures, in the slots
