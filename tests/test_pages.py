import importlib.util
import re
import tempfile
import unittest
from pathlib import Path

from catan_map import generate, render_svg

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("svg_to_pages", ROOT / "scripts" / "svg_to_pages.py")
pages = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pages)

SHEET = (600.0, 600.0)


class Size(unittest.TestCase):
    def test_the_sheet_is_600_mm(self):
        text = render_svg(generate("KMQXRT"), ["KMQXRT"], elements=())
        self.assertEqual(pages.svg_size_mm(text), SHEET)

    def test_units(self):
        self.assertEqual(pages.svg_size_mm('<svg width="60cm" height="30cm">'), (600.0, 300.0))
        self.assertEqual(pages.svg_size_mm('<svg width="2in" height="1in">'), (50.8, 25.4))
        w, h = pages.svg_size_mm('<svg width="96" height="192">')            # pixels
        self.assertAlmostEqual(w, 25.4)
        self.assertAlmostEqual(h, 50.8)

    def test_errors(self):
        for bad in ("not an svg", '<svg viewBox="0 0 10 10">', '<svg width="50%" height="10mm">'):
            with self.assertRaises(pages.PagesError, msg=bad):
                pages.svg_size_mm(bad)


class Plan(unittest.TestCase):
    def test_six_a4_pages_for_the_sheet(self):
        layout = pages.plan(SHEET, "A4", margin=5, pages=6)
        self.assertEqual((layout["cols"] * layout["rows"], layout["pages"]), (6, 6))
        # 2 pages of 29.7 cm cannot hold 60 cm, so it is shrunk: (297 - 10) * 2 / 600
        self.assertAlmostEqual(layout["scale"], 574 / 600, places=4)
        self.assertEqual((layout["cols"], layout["rows"]), (3, 2))
        self.assertFalse(layout["landscape"])

    def test_the_shrunk_sheet_fits_inside_its_pages(self):
        layout = pages.plan(SHEET, "A4", margin=5, pages=6)
        area_w, area_h = layout["area"]
        self.assertLessEqual(SHEET[0] * layout["scale"], layout["cols"] * area_w + 1e-6)
        self.assertLessEqual(SHEET[1] * layout["scale"], layout["rows"] * area_h + 1e-6)

    def test_with_no_margin_it_is_nearly_real_size(self):
        layout = pages.plan(SHEET, "A4", margin=0, pages=6)
        self.assertAlmostEqual(layout["scale"], 594 / 600, places=4)      # 2 x 29.7 cm is 59.4 cm

    def test_real_size_takes_nine_pages(self):
        layout = pages.plan(SHEET, "A4", margin=5, scale=1.0)
        self.assertEqual((layout["cols"], layout["rows"], layout["pages"]), (3, 3, 9))
        self.assertEqual(layout["scale"], 1.0)

    def test_a_smaller_scale_takes_fewer_pages(self):
        half = pages.plan(SHEET, "A4", margin=5, scale=0.5)         # 30 cm: 2 pages across or 1 landscape + 1 portrait...
        self.assertLessEqual(half["pages"], 4)
        self.assertLess(half["pages"], pages.plan(SHEET, "A4", margin=5, scale=1.0)["pages"])

    def test_other_paper_and_page_counts(self):
        self.assertEqual(pages.plan(SHEET, "A3", margin=5, pages=2)["pages"], 2)
        self.assertGreater(pages.plan(SHEET, "A3", margin=5, pages=2)["scale"], pages.plan(SHEET, "A4", margin=5, pages=2)["scale"])

    def test_bad_margins(self):
        with self.assertRaises(pages.PagesError):
            pages.plan(SHEET, "A4", margin=-1)
        with self.assertRaises(pages.PagesError):
            pages.plan(SHEET, "A4", margin=150)


class Html(unittest.TestCase):
    def setUp(self):
        self.layout = pages.plan(SHEET, "A4", margin=5, pages=6)
        self.html = pages.build_html("sheet.svg", SHEET, self.layout, 5)

    def test_one_page_for_each_part(self):
        self.assertEqual(self.html.count('class="page"'), 6)
        self.assertIn("size: 210.0mm 297.0mm", self.html)

    def test_the_parts_are_cut_where_the_printable_areas_end(self):
        area_w, area_h = self.layout["area"]
        offsets = re.findall(r"left:-([\d.]+)mm;top:-([\d.]+)mm", self.html)
        self.assertEqual(len(offsets), 6)
        expected = [(c * area_w, r * area_h) for r in range(2) for c in range(3)]
        for (left, top), (want_left, want_top) in zip(offsets, expected):
            self.assertAlmostEqual(float(left), want_left, places=2)
            self.assertAlmostEqual(float(top), want_top, places=2)

    def test_every_part_shows_the_whole_sheet_at_the_scale(self):
        size = SHEET[0] * self.layout["scale"]
        self.assertEqual(len(re.findall(rf"width:{size:.3f}mm;height:{size:.3f}mm", self.html)), 6)

    def test_marks_and_labels_can_be_left_out(self):
        self.assertIn('class="marks"', self.html)
        self.assertIn("page 1 of 6", self.html)
        plain = pages.build_html("sheet.svg", SHEET, self.layout, 5, marks=False)
        self.assertNotIn('class="marks"', plain)


class MakingAPdf(unittest.TestCase):
    def test_a_real_pdf_with_six_a4_pages(self):
        try:
            chrome = pages.find_chrome()
        except pages.PagesError:
            self.skipTest("no Chrome, Chromium or Edge here")
        with tempfile.TemporaryDirectory() as folder:
            svg = Path(folder) / "sheet.svg"
            svg.write_text(render_svg(generate("KMQXRT", ports=True), ["KMQXRT-P"], "plain", elements=("seed",)), encoding="utf-8")
            out = Path(folder) / "out.pdf"
            layout = pages.make_pdf(svg, out, chrome=chrome)
            data = out.read_bytes()
        self.assertEqual(layout["pages"], 6)
        self.assertTrue(data.startswith(b"%PDF"))
        self.assertEqual(len(re.findall(rb"/Type\s*/Page[^s]", data)), 6)
        self.assertIn(b"/MediaBox", data)

    def test_command_line_errors(self):
        self.assertEqual(pages.main(["/nonexistent/file.svg"]), 2)


if __name__ == "__main__":
    unittest.main()
