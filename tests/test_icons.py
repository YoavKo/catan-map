import re
import unittest
import xml.etree.ElementTree as ET

from catan_map import CatanMapError, generate, render_svg
from catan_map.icons import DEFAULT_ICON_SET, ICON_DEFS, ICON_SET_NAMES, ICON_SETS, check_icon_set

from tests.test_cli import run

SVG = "http://www.w3.org/2000/svg"


def wrap(body, defs=""):
    return ET.fromstring(f'<svg xmlns="{SVG}"><defs>{defs}</defs>{body}</svg>')


class Sets(unittest.TestCase):
    def test_the_three_sets_and_the_default(self):
        self.assertEqual(ICON_SET_NAMES, ("simple", "detailed", "realistic"))
        self.assertEqual(DEFAULT_ICON_SET, "realistic")
        self.assertEqual(check_icon_set(None), "realistic")
        for name in ICON_SET_NAMES:
            self.assertEqual(check_icon_set(name), name)
        with self.assertRaises(CatanMapError) as caught:
            check_icon_set("fancy")
        self.assertIn("simple, detailed, realistic", str(caught.exception))

    def test_every_set_has_the_five_icons_and_each_is_well_formed(self):
        for name in ICON_SET_NAMES:
            self.assertEqual(sorted(ICON_SETS[name]), sorted("WSGCO"), name)
            for kind, body in ICON_SETS[name].items():
                wrap(body, ICON_DEFS[name])                       # raises if it is not well formed XML

    def test_the_realistic_gradients_are_defined_once_and_every_use_has_a_definition(self):
        defs = ICON_DEFS["realistic"]
        ids = re.findall(r'id="([^"]+)"', defs)
        self.assertEqual(len(ids), len(set(ids)))                  # no gradient is defined twice
        self.assertGreaterEqual(len(ids), 10)
        for kind, body in ICON_SETS["realistic"].items():
            self.assertNotIn("<defs>", body)                       # the definitions are not repeated inside the icons
            for used in re.findall(r"url\(#([^)]+)\)", body):
                self.assertIn(used, ids, (kind, used))

    def test_the_flat_sets_need_no_definitions(self):
        self.assertEqual(ICON_DEFS["simple"], "")
        self.assertEqual(ICON_DEFS["detailed"], "")


class InTheDrawing(unittest.TestCase):
    def setUp(self):
        self.board = generate("KMQXRT", ports=True)

    def drawing(self, **options):
        return render_svg(self.board, elements=("costs", "bank"), **options)

    def test_realistic_is_the_default(self):
        self.assertEqual(self.drawing(), self.drawing(icons="realistic"))
        self.assertNotEqual(self.drawing(), self.drawing(icons="simple"))

    def test_each_gradient_is_in_the_drawing_once_however_many_icons_use_it(self):
        text = self.drawing()
        root = ET.fromstring(text)
        ids = [e.get("id") for e in root.iter() if e.get("id")]
        self.assertEqual(len(ids), len(set(ids)), "an id is used twice")
        self.assertIn("ic-wool", ids)
        self.assertGreater(text.count("url(#ic-wool)"), 20)          # used by the port, the cards and the bank

    def test_the_flat_sets_have_no_icon_gradients(self):
        for name in ("simple", "detailed"):
            self.assertNotIn('id="ic-', self.drawing(icons=name))

    def test_every_set_draws_a_whole_sheet(self):
        for name in ICON_SET_NAMES:
            root = ET.fromstring(self.drawing(icons=name))
            self.assertEqual(len(root.findall(f".//{{{SVG}}}g[@class='slot']")), 6, name)       # the bank
            self.assertEqual(len(root.findall(f".//{{{SVG}}}g[@class='costs']")), 4, name)      # the cards

    def test_the_chips_say_which_resource_they_are(self):
        text = self.drawing()
        self.assertEqual(sorted(set(re.findall(r'data-kind="(\w)"', text))), sorted("WSGCO"))

    def test_the_size_grows_with_the_detail_but_stays_reasonable(self):
        sizes = [len(self.drawing(icons=name)) for name in ICON_SET_NAMES]
        self.assertLess(sizes[0], sizes[1])
        self.assertLess(sizes[1], sizes[2])
        self.assertLess(sizes[2] - sizes[0], 250_000)            # the realistic icons add less than 250 KB to a sheet

    def test_an_unknown_set(self):
        with self.assertRaises(CatanMapError):
            render_svg(self.board, icons="fancy")

    def test_the_command_line(self):
        code, out, _ = run("--seed", "KMQXRT-P", "--svg", "-", "--elements", "costs", "--icons", "simple")
        self.assertEqual(code, 0)
        self.assertNotIn('id="ic-', out)
        code, out, _ = run("--seed", "KMQXRT-P", "--svg", "-", "--elements", "costs")
        self.assertIn('id="ic-wool"', out)                      # realistic by default
        self.assertEqual(run("--seed", "KMQXRT", "--icons", "simple")[0], 2)                 # needs --svg
        self.assertEqual(run("--seed", "KMQXRT", "--svg", "-", "--icons", "fancy")[0], 2)    # not a set


if __name__ == "__main__":
    unittest.main()
