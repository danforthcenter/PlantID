import unittest

import pypdfium2 as pdfium

from barcodes import bar_width_mm
from code_checks import code_problems
from test_v1_fixes import render

BAR = bar_width_mm(2, 203)


class CodeProblemTests(unittest.TestCase):
    def test_fitting_codes_have_no_problems(self):
        self.assertEqual(code_problems(["Floor-Pot_01", "P1"], [1, 2], "Barcode", 66, 35, bar_mm=BAR), ([], []))
        self.assertEqual(code_problems(["P1"], [1], "QR", 66, 35, qr_size=18), ([], []))
        self.assertEqual(code_problems([], [], "QR", 66, 35, qr_size=1), ([], []))

    def test_blank_values_are_listed_by_row(self):
        problems, _ = code_problems(["A1", "", " ", "B2"], [4, 5, 6, 7], "QR", 66, 35, qr_size=18,
                                    column="PlantID")
        self.assertEqual(problems, ["2 of 4 labels have no PlantID value, so their QR code would be empty "
                                    "(rows 5, 6). Fill in the values or untick those rows."])

    def test_barcode_rejects_characters_it_cannot_hold(self):
        problems, _ = code_problems(["Pot_1", "Pot_é2"], [1, 2], "Barcode", 66, 35, bar_mm=BAR)
        self.assertEqual(len(problems), 1)
        self.assertIn("such as “é” in “Pot_é2” (row 2). Use a QR code", problems[0])

    def test_barcode_too_wide_names_longest_value_and_count(self):
        problems, _ = code_problems(["Floor-Pot_01", "TaGNE_p1_Spring32", "TaGNE_p1_Spring32_tHighN_r1_d17"],
                                    [1, 2, 3], "Barcode", 50, 35, bar_mm=BAR)
        self.assertEqual(problems, [
            "The barcode is too long to fit on 2 of 3 labels. The longest value, "
            "“TaGNE_p1_Spring32_tHighN_r1_d17” (row 3), needs 99.1 mm to scan reliably, but only 50.0 mm "
            "fits. Use a wider label, a QR code, or shorter code values."])

    def test_qr_too_large_or_too_small(self):
        long_id = "TaGNE_p10_Spring32_tTraceN_r2_d17"
        problems, _ = code_problems(["P1"], [1], "QR", 66, 20, qr_size=25)
        self.assertIn("is 25 mm but only 20.0 mm fits", problems[0])
        problems, cautions = code_problems(["P1", long_id], [1, 2], "QR", 66, 35, qr_size=8)
        self.assertIn("too small to scan on 1 of 2 labels", problems[0])
        self.assertIn(f"“{long_id}” (row 2), gives 0.22 mm squares", problems[0])
        self.assertIn("Make it at least 13 mm", problems[0])
        self.assertEqual(cautions, [])
        problems, cautions = code_problems([long_id], [9], "QR", 66, 11, qr_size=10)
        self.assertEqual(problems, [])
        self.assertIn("may struggle on every label", cautions[0])
        self.assertIn("Use a larger label", cautions[0])


class PlaceholderTests(unittest.TestCase):
    def test_placeholder_replaces_code(self):
        base = dict(visible_columns=[], code_column="PlantID", label_width=70, label_height=35,
                    barcode_width=99, barcode_height=10, barcode_bar_mm=BAR, show_border=False,
                    row={"PlantID": "TaGNE_p1_Spring32_tHighN_r1_d17"},
                    code_placeholder="Cannot print: see message above")
        results = render({"barcode": {**base, "code_type": "Barcode"},
                          "qr": {**base, "code_type": "QR", "qr_size": 18}})
        for pdf_bytes, _ in results.values():
            page = pdfium.PdfDocument(pdf_bytes)[0]
            self.assertIn("Cannot print: see message above", page.get_textpage().get_text_range())
            # Only a thin outline and its text are drawn: no bars or QR squares.
            pixels = page.render(scale=2).to_pil().convert("L").getdata()
            self.assertLess(sum(pixel < 128 for pixel in pixels) / len(pixels), 0.01)


if __name__ == "__main__":
    unittest.main()
