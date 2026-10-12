"""Start page, export, fine-tuning controls, and scanability warnings."""
import datetime
import io
import json
from pathlib import Path
import unittest

import pandas as pd
import pypdfium2 as pdfium
from streamlit.testing.v1 import AppTest

from data_loading import read_label_csv, read_label_table
from test_layout_schema import LOAD_HOOK

ROOT = Path(__file__).resolve().parent


def start_app():
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30)
    app.run()
    assert not app.exception, app.exception
    return app


def open_designer(layout_choice):
    app = start_app()
    app.radio(key="start_data_choice").set_value("Use the example dataset").run()
    app.radio(key="start_layout_choice").set_value(layout_choice).run()
    app.button(key="start_go_btn").click().run()
    assert not app.exception, app.exception
    return app


def downloads(app):
    return [button.proto.label for button in app.get("download_button")]


class StartPageTests(unittest.TestCase):
    def test_designer_needs_data_before_opening(self):
        app = start_app()
        self.assertTrue(app.button(key="start_go_btn").disabled)
        app.radio(key="start_data_choice").set_value("Use the example dataset").run()
        self.assertFalse(app.button(key="start_go_btn").disabled)
        self.assertTrue(any("34 rows" in message.value for message in app.success))

    def test_defaults_and_examples_open_the_designer(self):
        for choice, printer in (("Start from defaults", "Label printer"),
                                ("Label printer example", "Label printer"),
                                ("Sheet printer example", "Sheet printer")):
            app = open_designer(choice)
            self.assertIsNotNone(app.session_state["df"])
            self.assertEqual(app.session_state["printer_type_select"], printer, choice)
            self.assertEqual(app.session_state["data_source"], "Example dataset")

    def test_loading_a_saved_layout_needs_a_file(self):
        app = start_app()
        app.radio(key="start_data_choice").set_value("Use the example dataset").run()
        app.radio(key="start_layout_choice").set_value("Load a saved layout").run()
        self.assertTrue(app.button(key="start_go_btn").disabled)


class ExcelTests(unittest.TestCase):
    def test_cells_appear_as_shown_in_excel(self):
        workbook = io.BytesIO()
        pd.DataFrame({"PlantID": ["00123", "P2"], "Rep": [1, 2.5],
                      "Sown": [datetime.datetime(2026, 5, 1), None]}).to_excel(workbook, index=False)
        df, error = read_label_table(workbook.getvalue(), "plants.XLSX")
        self.assertIsNone(error)
        self.assertEqual(df.to_dict("records"), [
            {"PlantID": "00123", "Rep": "1", "Sown": "2026-05-01"},
            {"PlantID": "P2", "Rep": "2.5", "Sown": ""},
        ])

    def test_unreadable_workbook_reports_an_error(self):
        self.assertIsNone(read_label_table(b"not a workbook", "plants.xlsx")[0])
        self.assertIsNotNone(read_label_table(b"not a workbook", "plants.xlsx")[1])
        self.assertIsNotNone(read_label_table(b"PlantID\nP1\n", "plants.csv")[0])


class ExportTests(unittest.TestCase):
    def test_label_printer_offers_one_click_download(self):
        app = open_designer("Label printer example")
        self.assertIn("Download labels PDF", downloads(app))
        self.assertNotIn("Download alignment test page", downloads(app))
        self.assertFalse(any(button.label == "Generate Multi-Label PDF" for button in app.button))

    def test_sheet_preview_and_alignment_page(self):
        app = open_designer("Sheet printer example")
        self.assertIn("Download alignment test page", downloads(app))
        app.toggle(key="sheet_preview_toggle").set_value(True).run()
        self.assertFalse(app.exception)
        self.assertTrue(any(image.proto.imgs[0].caption == "First sheet" for image in app.get("imgs")))

    def test_downloaded_pdf_has_every_label(self):
        source = (ROOT / "streamlit_app.py").read_text().replace(
            'st.set_page_config(layout="wide")', LOAD_HOOK, 1) + "\nst.session_state['_pdf'] = labels_pdf()\n"
        app = AppTest.from_string(source, default_timeout=30)
        df = read_label_csv((ROOT / "PV1_metadata.csv").read_bytes())[0]
        app.session_state["df"] = df
        app.session_state["_pending"] = json.loads((ROOT / "example_layout.json").read_text())
        app.run()
        self.assertFalse(app.exception)
        pdf = pdfium.PdfDocument(app.session_state["_pdf"])
        self.assertEqual(len(pdf), len(df))  # Label printer: one label per page.
        self.assertIn(f"Plant: {df.iloc[-1]['Plant']}", pdf[len(df) - 1].get_textpage().get_text_range())

    def test_alignment_page_numbers_every_position(self):
        source = (ROOT / "streamlit_app.py").read_text().replace(
            'st.set_page_config(layout="wide")', LOAD_HOOK, 1) + (
            "\nst.session_state['_alignment'] = alignment_test_pdf(design, sheet, labels_per_sheet)\n")
        app = AppTest.from_string(source, default_timeout=30)
        app.session_state["df"] = read_label_csv((ROOT / "PV1_metadata.csv").read_bytes())[0]
        app.session_state["_pending"] = json.loads((ROOT / "example_sheet_layout.json").read_text())
        app.run()
        app.run()
        self.assertFalse(app.exception)
        pdf = pdfium.PdfDocument(app.session_state["_alignment"])
        self.assertEqual(len(pdf), 1)
        text = pdf[0].get_textpage().get_text_range().split()
        self.assertEqual(text, [str(i) for i in range(1, len(text) + 1)])
        self.assertGreater(len(text), 1)

    def test_overflow_is_found_on_any_row_not_just_the_preview(self):
        source = (ROOT / "streamlit_app.py").read_text() + (
            "\nst.session_state['_overflow'] = find_overflow(df_to_use, design)\n")
        app = AppTest.from_string(source, default_timeout=30)
        app.session_state["df"] = pd.DataFrame({"PlantID": ["P1", "P2", "P3"],
                                                "Note": ["ok", "x" * 120, "ok"]})
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["_overflow"], {"Note"})
        self.assertTrue(any("Some labels have" in warning.value for warning in app.warning))


class FineTuningTests(unittest.TestCase):
    def test_hidden_controls_keep_loaded_values(self):
        app = start_app()
        app.radio(key="start_data_choice").set_value("Use the example dataset").run()
        app.button(key="start_go_btn").click().run()
        self.assertFalse(any(slider.label == "Row height factor" for slider in app.slider))
        app.session_state["qr_left_offset_slider"] = 5
        app.session_state["row_height_factor_slider"] = 1.2
        app.run()
        app.run()
        self.assertEqual(app.session_state["qr_left_offset_slider"], 5)
        app.toggle(key="show_fine_tuning_toggle").set_value(True).run()
        self.assertEqual(app.slider(key="qr_left_offset_slider").value, 5)
        row_height = next(slider for slider in app.slider if slider.label == "Row height factor")
        self.assertEqual(row_height.value, 1.2)


class ScanabilityTests(unittest.TestCase):
    def test_small_qr_codes_warn(self):
        app = open_designer("Label printer example")
        app.number_input(key="qr_size_slider__input").set_value(8).run()
        self.assertTrue(any("squares are" in warning.value for warning in app.warning))
        app.number_input(key="qr_size_slider__input").set_value(18).run()
        self.assertFalse(any("squares are" in warning.value for warning in app.warning))


if __name__ == "__main__":
    unittest.main()
