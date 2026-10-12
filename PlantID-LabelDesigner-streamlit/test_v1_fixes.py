"""Regression coverage for CSV loading, barcode width, and text overflow."""
from pathlib import Path
import unittest

import pypdfium2 as pdfium
from streamlit.testing.v1 import AppTest

from data_loading import read_label_csv


ROOT = Path(__file__).resolve().parent


class CsvLoadingTests(unittest.TestCase):
    def test_values_are_kept_as_written(self):
        df, error = read_label_csv(b"PlantID,Rep,Note\n00123,1,\n00124,,x\n")
        self.assertIsNone(error)
        self.assertEqual(df.iloc[0].tolist(), ["00123", "1", ""])
        self.assertEqual(df.iloc[1].tolist(), ["00124", "", "x"])

    def test_excel_encodings_and_byte_order_mark(self):
        df, error = read_label_csv("﻿PlantID,Site\nP1,Montréal\n".encode("utf-8"))
        self.assertIsNone(error)
        self.assertEqual(df.columns.tolist(), ["PlantID", "Site"])
        df, error = read_label_csv("PlantID,Temp\nP1,20°C\n".encode("cp1252"))
        self.assertIsNone(error)
        self.assertEqual(df.iloc[0]["Temp"], "20°C")

    def test_unreadable_files_report_an_error(self):
        self.assertIsNotNone(read_label_csv(b"")[1])
        self.assertIsNotNone(read_label_csv(b"PlantID,Rep\n")[1])


# Run against the real app module so the drawing code under test is current.
HARNESS = '''
import io
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
st.session_state["_results"] = {}
for name, kwargs in st.session_state["_cases"].items():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(70 * mm, 35 * mm))
    found = set()
    draw_label_on_canvas(c, pd.Series(kwargs.pop("row")), 0, 0, overflow=found, **kwargs)
    c.save()
    st.session_state["_results"][name] = (buffer.getvalue(), found)
st.stop()
'''


def render(cases):
    source = (ROOT / "streamlit_app.py").read_text()
    source = source.replace("st.set_page_config(layout=\"wide\")", HARNESS, 1)
    app = AppTest.from_string(source, default_timeout=20)
    app.session_state["_cases"] = cases
    app.run()
    assert not app.exception, app.exception
    return app.session_state["_results"]


def ink_extent_mm(pdf_bytes):
    """Leftmost and rightmost columns with dark pixels, in mm."""
    image = pdfium.PdfDocument(pdf_bytes)[0].render(scale=10).to_pil().convert("L")
    width = image.width
    dark = [x for x in range(width) if min(image.crop((x, 0, x + 1, image.height)).getdata()) < 128]
    px_per_mm = width / 70
    return dark[0] / px_per_mm, (dark[-1] + 1) / px_per_mm


class DrawingTests(unittest.TestCase):
    def test_barcode_beside_text_is_drawn_at_requested_width(self):
        base = dict(visible_columns=[], code_column="PlantID", code_type="Barcode",
                    label_width=70, label_height=35, barcode_width=25, barcode_height=10,
                    qr_left_offset=2, show_border=False)
        results = render({"beside": {**base, "row": {"PlantID": "TaGNE_p1_Spring32"}}})
        left, right = ink_extent_mm(results["beside"][0])
        # Bars start after the quiet zone and end before it, inside the 25 mm box.
        self.assertGreaterEqual(left, 2)
        self.assertLessEqual(right, 27.1)

    def test_text_that_does_not_fit_is_reported(self):
        base = dict(visible_columns=["PlantID"], code_column=None, code_type="None",
                    label_width=70, label_height=35)
        results = render({
            "fits": {**base, "row": {"PlantID": "P1"}},
            "too_long": {**base, "row": {"PlantID": "X" * 80}},
            "rows_overlap": {**base, "visible_columns": ["A", "B", "C", "D", "E"],
                             "label_font_size": 14, "row": dict.fromkeys("ABCDE", "1")},
        })
        self.assertEqual(results["fits"][1], set())
        self.assertEqual(results["too_long"][1], {"PlantID"})
        self.assertIn("text rows overlap", results["rows_overlap"][1])

    def test_long_text_is_clipped_to_the_label(self):
        results = render({"too_long": dict(
            visible_columns=["PlantID"], code_column=None, code_type="None",
            label_width=35, label_height=35, show_border=False, row={"PlantID": "X" * 80})})
        _, right = ink_extent_mm(results["too_long"][0])
        self.assertLessEqual(right, 35.1)


if __name__ == "__main__":
    unittest.main()
