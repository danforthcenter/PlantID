import io
import itertools
import unittest

import pypdfium2 as pdfium
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

import pandas as pd
from streamlit.testing.v1 import AppTest

from barcodes import (
    QUIET_ZONE_MODULES, bar_width_mm, barcode_width_mm, draw_code128,
    reliable_bar_mm, symbol_modules,
)
from layout_schema import layout_to_settings, settings_to_layout
from test_v1_fixes import ROOT, ink_extent_mm, render


def printed_runs(value, x_mm, bar_mm, dpi, smooth):
    """Lengths of the dark and light runs across a barcode rasterised at the
    printer's resolution, with dots either dark or not as a printer prints them."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(60 * mm, 12 * mm))
    draw_code128(c, value, x_mm * mm, 1 * mm, 50 * mm, 10 * mm, bar_mm)
    c.save()
    page = pdfium.PdfDocument(buffer.getvalue())[0]
    image = page.render(scale=dpi / 72, no_smoothpath=not smooth).to_pil().convert("L")
    row = [image.getpixel((x, image.height // 2)) < 128 for x in range(image.width)]
    first, last = row.index(True), len(row) - row[::-1].index(True)
    return [len(list(run)) for _, run in itertools.groupby(row[first:last])]


class BarcodeSizeTests(unittest.TestCase):
    def test_width_follows_bar_width_and_longest_value(self):
        bar = bar_width_mm(2, 203)
        self.assertAlmostEqual(bar, 0.2502, places=4)
        # Start, 12 characters, checksum and stop make 167 bar widths.
        self.assertEqual(symbol_modules("Array-Pot_01"), 167 + 2 * QUIET_ZONE_MODULES)
        self.assertAlmostEqual(barcode_width_mm(["P1", "Array-Pot_01"], bar), 187 * bar)
        self.assertEqual(barcode_width_mm([], bar), 0)

    def test_bars_print_as_whole_dots(self):
        # Rasterisers darken partly covered dots, so off-grid bars would print a dot wider.
        for dpi, dots in ((203, 2), (300, 3), (203, 1)):
            for x_mm in (1.0, 1.3, 2.71):
                for smooth in (True, False):
                    runs = printed_runs("Floor-Pot_01", x_mm, bar_width_mm(dots, dpi), dpi, smooth)
                    case = (dpi, dots, x_mm, smooth)
                    self.assertEqual(len(runs), 2 * (3 * 14 + 4) - 1, case)  # Three bars a symbol, four in stop.
                    self.assertEqual(sum(runs), 167 * dots, case)
                    self.assertTrue(all(run % dots == 0 for run in runs), case)

    def test_label_keeps_bar_width_and_aligns_to_outer_edge(self):
        bar = bar_width_mm(2, 203)
        width = barcode_width_mm(["Array-Pot_01"], bar)
        base = dict(visible_columns=[], code_column="PlantID", code_type="Barcode",
                    label_width=70, label_height=35, barcode_width=width, barcode_height=10,
                    barcode_bar_mm=bar, qr_left_offset=2, show_border=False)
        results = render({
            "left": {**base, "row": {"PlantID": "Array-Pot_01"}},
            "right_short": {**base, "code_position": "Right", "row": {"PlantID": "P1"}},
        })
        left, right = ink_extent_mm(results["left"][0])
        self.assertAlmostEqual(left, 2 + QUIET_ZONE_MODULES * bar, delta=0.15)
        self.assertAlmostEqual(right - left, 167 * bar, delta=0.15)
        # A shorter value keeps its bar width and ends at the same margin.
        short_left, short_right = ink_extent_mm(results["right_short"][0])
        self.assertAlmostEqual(short_right, 70 - 2 - QUIET_ZONE_MODULES * bar, delta=0.15)
        self.assertAlmostEqual(short_right - short_left, (symbol_modules("P1") - 20) * bar, delta=0.15)

    def test_bars_are_the_fewest_whole_dots_that_scan_reliably(self):
        self.assertEqual(reliable_bar_mm(203), bar_width_mm(2, 203))
        self.assertEqual(reliable_bar_mm(300), bar_width_mm(3, 300))
        self.assertEqual(reliable_bar_mm(600), bar_width_mm(6, 600))

    def test_layout_saves_printer_resolution(self):
        for printer_type in ("Label printer", "Sheet printer"):
            layout = settings_to_layout({"printer_type_select": printer_type, "printer_dpi_select": 300})
            self.assertEqual(layout["printer"]["resolution_dpi"], 300)
            self.assertEqual(layout_to_settings(layout)["printer_dpi_select"], 300)


class BarcodeAppTests(unittest.TestCase):
    def run_app(self, ids):
        app = AppTest.from_string((ROOT / "streamlit_app.py").read_text(), default_timeout=30)
        app.session_state["df"] = pd.DataFrame({"PlantID": ids})
        for key, value in dict(code_type_select="Barcode", code_column_select="PlantID",
                               visible_columns_multiselect=["PlantID"],
                               barcode_text_position_select="Below barcode").items():
            app.session_state[key] = value
        app.run()
        self.assertFalse(app.exception)
        return [error.value for error in app.error], [caption.value for caption in app.caption]

    def test_barcode_that_fits_shows_its_width(self):
        errors, captions = self.run_app(["Floor-Pot_01", "P1"])
        self.assertFalse(errors)
        self.assertTrue(any("Barcode width: 46.8 mm" in caption for caption in captions))

    def test_one_long_value_blocks_the_whole_set(self):
        errors, _ = self.run_app(["Floor-Pot_01", "P1", "TaGNE_p1_Spring32_tHighN_r1_d17"])
        self.assertTrue(any(error.startswith("The barcode is too long to fit on 1 of 3 labels. The longest "
                                             "value, “TaGNE_p1_Spring32_tHighN_r1_d17” (row 3), needs 99.1 mm")
                            for error in errors))
        self.assertIn("Cannot export: Fix the problem with the QR code or barcode shown above the preview.", errors)


if __name__ == "__main__":
    unittest.main()
