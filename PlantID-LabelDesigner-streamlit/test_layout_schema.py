"""Layout file schema v1, schema 0 migration, and loading layouts in the app."""
import json
from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest

from data_loading import read_label_csv
from layout_schema import (
    FIELDS,
    PRINT_RUN_SETTINGS,
    SCHEMA_VERSION,
    build_layout_file,
    read_layout_file,
    referenced_columns,
)
from test_v1_fixes import ink_extent_mm, render

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "test_fixtures"


def read_json(path):
    return json.loads(path.read_text())


class SchemaTests(unittest.TestCase):
    def test_round_trip_keeps_every_saved_setting(self):
        settings = read_layout_file(read_json(ROOT / "example_sheet_layout.json"))[0]
        saved = build_layout_file(settings, "PlantID Label Designer", "test")
        self.assertEqual(saved["schema_version"], SCHEMA_VERSION)
        reloaded, version, error = read_layout_file(json.loads(json.dumps(saved)))
        self.assertIsNone(error)
        self.assertEqual(version, SCHEMA_VERSION)
        self.assertEqual(reloaded, settings)
        for _, key, _ in FIELDS:
            self.assertIn(key, reloaded)

    def test_examples_use_current_schema_and_stable_codes(self):
        for name in ("example_layout.json", "example_sheet_layout.json"):
            parsed = read_json(ROOT / name)
            self.assertEqual(parsed["schema_version"], SCHEMA_VERSION)
            layout = parsed["layout"]
            self.assertIn(layout["code"]["type"], ("qr", "barcode", "none"))
            self.assertIn(layout["printer"]["type"], ("label", "sheet"))
            self.assertNotIn("settings", parsed)
        sheet = read_json(ROOT / "example_sheet_layout.json")["layout"]
        self.assertEqual(sheet["label"]["preset"], "PR1MA 85 Tag")
        self.assertEqual(sheet["printer"]["sheet_stock"], "PR1MA 85 Tag Sheet (5 x 17)")

    def test_print_run_choices_are_not_saved_or_loaded(self):
        v0 = read_json(FIXTURES / "layout_v0_sheet.json")
        v0["settings"].update(row_range_enabled_check=True, filter_enabled_check=True,
                              sheet_start_slot_input=12)
        settings, version, error = read_layout_file(v0)
        self.assertEqual((version, error), (0, None))
        self.assertFalse(PRINT_RUN_SETTINGS & set(settings))
        saved = json.dumps(build_layout_file({**settings, "sheet_start_slot_input": 12}, "x", "x"))
        self.assertNotIn("sheet_start", saved)
        self.assertNotIn("filter", saved)

    def test_stacked_barcode_offset_is_migrated_from_schema_0(self):
        v0 = read_json(FIXTURES / "layout_v0_label.json")
        v0["settings"].update(code_type_select="Barcode", qr_left_offset_slider=2,
                              label_padding_slider=4)
        self.assertEqual(read_layout_file(v0)[0]["qr_left_offset_slider"], 2)
        v0["settings"]["barcode_text_position_select"] = "Below barcode"
        self.assertEqual(read_layout_file(v0)[0]["qr_left_offset_slider"], 6)

    def test_unknown_options_fall_back_and_bad_files_are_rejected(self):
        layout = read_json(ROOT / "example_layout.json")
        layout["layout"]["code"]["position"] = "middle"
        layout["layout"]["label"]["preset"] = "Discontinued label"
        settings, _, error = read_layout_file(layout)
        self.assertIsNone(error)
        self.assertNotIn("code_position_select", settings)
        self.assertEqual(settings["label_size_mode_select"], "Custom Size")
        self.assertIsNotNone(read_layout_file([])[2])
        self.assertIsNotNone(read_layout_file({"schema_version": 1})[2])
        self.assertIsNotNone(read_layout_file({"schema_version": "one", "layout": {}})[2])

    def test_newer_schema_is_read_on_a_best_effort_basis(self):
        layout = read_json(ROOT / "example_layout.json")
        layout["schema_version"] = SCHEMA_VERSION + 1
        layout["layout"]["future_section"] = {"anything": True}
        settings, version, error = read_layout_file(layout)
        self.assertIsNone(error)
        self.assertEqual(version, SCHEMA_VERSION + 1)
        self.assertEqual(settings["label_width_mm_slider"], 70)

    def test_only_columns_in_use_are_reported(self):
        settings = {"visible_columns_multiselect": ["Plot"], "add_code_check": False,
                    "code_column_select": "PlantID", "highlight_column_select": "None",
                    "split_column_enabled_check": False, "split_column_select": "Barcode",
                    "rename_columns_check": True, "column_label_overrides": {"Plot": "P"}}
        self.assertEqual(referenced_columns(settings),
                         [("displayed fields", "Plot"), ("renamed fields", "Plot")])


LOAD_HOOK = (
    'if "_pending" in st.session_state:\n'
    '    apply_template_payload(st.session_state.pop("_pending"), fill_missing_defaults=True)\n'
    'st.set_page_config(layout="wide")'
)
CAPTURE = "\nst.session_state['_saved'] = build_template_payload(label_width, label_height)\n"


def app_with_layout(layout, df):
    source = (ROOT / "streamlit_app.py").read_text().replace(
        'st.set_page_config(layout="wide")', LOAD_HOOK, 1)
    app = AppTest.from_string(source + CAPTURE, default_timeout=30)
    app.session_state["df"] = df
    app.session_state["_pending"] = layout
    app.run()
    app.run()
    assert not app.exception, app.exception
    return app


class AppLayoutTests(unittest.TestCase):
    def setUp(self):
        self.df = read_label_csv((ROOT / "PV1_metadata.csv").read_bytes())[0]

    def test_schema_0_files_save_as_the_v1_examples(self):
        for v0_name, v1_name in (("layout_v0_label.json", "example_layout.json"),
                                 ("layout_v0_sheet.json", "example_sheet_layout.json")):
            app = app_with_layout(read_json(FIXTURES / v0_name), self.df)
            expected = read_json(ROOT / v1_name)
            self.assertEqual(app.session_state["_saved"]["layout"], expected["layout"], v1_name)
            self.assertTrue(any("converted from schema v0" in caption.value for caption in app.caption))

    def test_missing_columns_are_reported_and_can_be_dismissed(self):
        df = self.df.rename(columns={"Geno": "Genotype"})
        app = app_with_layout(read_json(ROOT / "example_layout.json"), df)
        warnings = [warning.value for warning in app.warning if "not in this dataset" in warning.value]
        self.assertEqual(len(warnings), 1)
        self.assertIn("Geno (displayed fields)", warnings[0])
        app.button(key="dismiss_missing_columns_btn").click().run()
        self.assertFalse(any("not in this dataset" in warning.value for warning in app.warning))

    def test_matching_data_shows_no_column_warning(self):
        app = app_with_layout(read_json(ROOT / "example_layout.json"), self.df)
        self.assertFalse(any("not in this dataset" in warning.value for warning in app.warning))


class CodeOffsetTests(unittest.TestCase):
    def test_every_barcode_placement_measures_offset_from_label_edge(self):
        base = dict(visible_columns=[], code_column="PlantID", code_type="Barcode",
                    label_width=70, label_height=35, barcode_width=40, barcode_height=8,
                    qr_left_offset=3, padding=4, show_border=False, row={"PlantID": "P1"})
        results = render({position: {**base, "barcode_text_position": position}
                          for position in ("Beside barcode", "Below barcode")})
        beside = ink_extent_mm(results["Beside barcode"][0])[0]
        below = ink_extent_mm(results["Below barcode"][0])[0]
        self.assertAlmostEqual(beside, below, delta=0.2)


if __name__ == "__main__":
    unittest.main()
