import json
from pathlib import Path
import unittest

import pandas as pd
import pypdfium2 as pdfium
from streamlit.testing.v1 import AppTest

from label_presets import GEMPLERS_SHEET_NAME, SHEET_STOCK_PRESET_BY_NAME
import test_layout_state
from wrap_tags import WRAP_DEFAULTS, wrap_config, wrap_layout_error

ROOT = Path(__file__).resolve().parent
# Exercise the actual app's renderer/export functions without importing its UI
# outside a Streamlit session. Capture the results after a normal app run.
CAPTURE = '''
st.session_state['_saved_layout'] = build_template_payload(label_width, label_height)
if not wrap_error:
    st.session_state['_pdf_bytes'] = generate_sheet_direct(
        active_df, visible_columns, code_column, code_type, highlight_column,
        label_font, label_font_size, label_width, label_height, qr_size,
        barcode_width, barcode_height, row_height_factor, sidebar_factor, highlight_padding,
        padding=label_padding, show_border=show_border, show_column_names=show_column_names,
        qr_left_offset=qr_left_offset, text_left_offset=text_left_offset,
        wrap_tag=wrap_tag, page_format=page_format,
        page_margin_top=page_margin_top, page_margin_bottom=page_margin_bottom,
        page_margin_left=page_margin_left, page_margin_right=page_margin_right,
        label_gap_horizontal=label_gap_horizontal, label_gap_vertical=label_gap_vertical,
        sheet_start_slot=sheet_start_slot,
    ).getvalue()
'''


class WrapTagTests(unittest.TestCase):
    select_preset = test_layout_state.LayoutStateTests.select_preset

    def setUp(self):
        self.app = AppTest.from_string((ROOT / 'streamlit_app.py').read_text() + CAPTURE,
                                      default_timeout=20)
        self.data = pd.DataFrame({'PlantID': [f'PLANT-{i:03}' for i in range(1, 10)],
                                  'Genotype': ['Iran5'] * 9, 'Plot': ['177'] * 9})
        self.app.session_state['df'] = self.data
        settings = json.loads((ROOT / 'example_sheet_layout.json').read_text())['settings']
        settings.update(visible_columns_multiselect=['PlantID', 'Genotype', 'Plot'],
                        highlight_column_select='None', label_font_size_slider=7)
        for key, value in settings.items():
            self.app.session_state[key] = value
        self.app.run()
        self.assertFalse(self.app.exception)
        self.select_preset('Gemplers')

    def test_stock_geometry_and_pdf_pagination(self):
        stock = SHEET_STOCK_PRESET_BY_NAME[GEMPLERS_SHEET_NAME]
        self.assertEqual(stock['page_format'], 'Letter Landscape')
        self.assertEqual((stock['columns'], stock['rows']), (1, 8))
        self.assertAlmostEqual(stock['label_width_mm'], 279.4)
        self.assertAlmostEqual(stock['margin_top_mm'], 6.35)
        self.assertAlmostEqual(stock['margin_bottom_mm'], 6.35)
        self.assertTrue(self.app.session_state['wrap_enabled_check'])
        self.assertFalse(self.app.session_state['wrap_custom_fields_check'])
        with pdfium.PdfDocument(self.app.session_state['_pdf_bytes']) as pdf:
            self.assertEqual(len(pdf), 2)
            self.assertEqual(pdf[0].get_size(), (792, 612))
            text = pdf[0].get_textpage().get_text_range()
            self.assertEqual(text.count('PLANT-001'), 2)  # main and tear-off
            self.assertNotIn('PLANT-009', text)
            self.assertIn('PLANT-009', pdf[1].get_textpage().get_text_range())

    def test_barcode_customization_toggle_and_saved_layout(self):
        self.app.selectbox(key='wrap_code_type_select').set_value('Barcode').run()
        self.app.number_input(key='wrap_barcode_width_mm_input').set_value(28.0).run()
        self.app.checkbox(key='wrap_custom_fields_check').check().run()
        self.app.multiselect(key='wrap_text_columns_multiselect').set_value(['Plot', 'Genotype']).run()
        self.app.checkbox(key='add_code_check').uncheck().run()
        self.assertFalse(self.app.exception)
        saved = self.app.session_state['_saved_layout']
        self.app.checkbox(key='wrap_enabled_check').uncheck().run()
        self.app.run()  # hidden-widget cleanup must not lose customization
        self.app.checkbox(key='wrap_enabled_check').check().run()
        self.assertEqual(self.app.session_state['wrap_barcode_width_mm_input'], 28)
        self.assertEqual(self.app.session_state['wrap_text_columns_multiselect'], ['Plot', 'Genotype'])
        # Load through the production importer before the UI is rendered.
        source = (ROOT / 'streamlit_app.py').read_text().replace(
            'st.set_page_config(layout="wide")',
            'apply_template_payload(st.session_state.pop("_pending_test_layout"), fill_missing_defaults=True)\nst.set_page_config(layout="wide")')
        restored = AppTest.from_string(source + CAPTURE, default_timeout=20)
        restored.session_state['df'] = self.data
        restored.session_state['_pending_test_layout'] = saved
        restored.run()
        self.assertFalse(restored.exception)
        self.assertEqual(restored.session_state['wrap_barcode_width_mm_input'], 28)
        self.assertEqual(restored.session_state['wrap_text_columns_multiselect'], ['Plot', 'Genotype'])
        self.assertEqual(restored.session_state['sheet_preset_select'], GEMPLERS_SHEET_NAME)

    def test_default_fields_follow_main_and_custom_fields_are_independent(self):
        self.assertFalse(self.app.session_state['wrap_custom_fields_check'])
        self.assertTrue(self.app.session_state['wrap_use_main_code_check'])
        self.assertEqual(wrap_config(self.app.session_state, ['Plot'], 'PlantID')['columns'], ['Plot'])
        main_fields = next(widget for widget in self.app.multiselect if widget.label == 'Columns to display')
        main_fields.set_value(['Plot', 'Genotype']).run()
        with pdfium.PdfDocument(self.app.session_state['_pdf_bytes']) as pdf:
            text = pdf[0].get_textpage().get_text_range()
            self.assertNotIn('PLANT-001', text)  # Only encoded, not a displayed field now.
            self.assertEqual(text.count('Iran5'), 16)  # Eight main + eight tear-off copies.
        self.app.checkbox(key='wrap_custom_fields_check').check().run()
        self.assertEqual(self.app.session_state['wrap_text_columns_multiselect'], ['Plot', 'Genotype'])
        self.app.multiselect(key='wrap_text_columns_multiselect').set_value(['PlantID']).run()
        self.app.checkbox(key='wrap_custom_fields_check').uncheck().run()
        self.app.run()
        self.app.checkbox(key='wrap_custom_fields_check').check().run()
        self.assertEqual(self.app.session_state['wrap_text_columns_multiselect'], ['PlantID'])
        self.assertFalse(self.app.exception)

    def test_invalid_geometry_blocks_export(self):
        self.app.number_input(key='wrap_tear_width_mm_input').set_value(250.0).run()
        self.assertFalse(self.app.exception)
        self.assertTrue(any('leave room' in error.value for error in self.app.error))
        next(button for button in self.app.button if button.label == 'Generate Multi-Label PDF').click().run()
        self.assertTrue(any('Cannot generate PDF' in error.value for error in self.app.error))

    def test_direct_sheet_selection_enables_wrap(self):
        self.app.checkbox(key='wrap_enabled_check').uncheck().run()
        self.app.selectbox(key='sheet_preset_select__layout_0').set_value('PR1MA 85 Tag Sheet (5 x 17)').run()
        self.app.selectbox(key='sheet_preset_select__layout_0').set_value(GEMPLERS_SHEET_NAME).run()
        self.assertFalse(self.app.exception)
        self.assertTrue(self.app.session_state['wrap_enabled_check'])


class WrapGeometryTests(unittest.TestCase):
    def test_code_and_text_fit_validation(self):
        config = wrap_config({**WRAP_DEFAULTS, 'wrap_enabled_check': True,
                              'wrap_code_column_select': 'PlantID'})
        self.assertIsNone(wrap_layout_error(config, 279.4, 25.4))
        self.assertIn('does not fit', wrap_layout_error({**config, 'qr_size': 30}, 279.4, 25.4))
        self.assertIn('8 mm', wrap_layout_error({**config, 'code_type': 'Barcode',
                                              'barcode_width': 50, 'columns': ['ID']}, 279.4, 25.4))


if __name__ == '__main__':
    unittest.main()
