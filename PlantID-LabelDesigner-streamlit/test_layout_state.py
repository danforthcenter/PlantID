"""Regression coverage for preset changes followed by ordinary widget edits."""
import json
from pathlib import Path
import unittest

import pandas as pd
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parent


class LayoutStateTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file(str(ROOT / 'streamlit_app.py'), default_timeout=20)
        self.app.session_state['df'] = pd.DataFrame({'PlantID': ['Plant_1']})
        settings = json.loads((ROOT / 'example_sheet_layout.json').read_text())['settings']
        for key, value in settings.items():
            self.app.session_state[key] = value
        self.app.run()
        self.assertFalse(self.app.exception)

    def select_preset(self, query):
        self.app.text_input(key='label_preset_search').set_value(query).run()
        table = next(table for table in self.app.dataframe
                     if 'Product / template' in table.value.columns)
        self.assertEqual(len(table.value), 1)
        # AppTest has no dataframe selection helper; submit the same widget
        # payload as the browser so the real on_select callback runs.
        states = self.app._tree.get_widget_states()
        state = states.widgets.add()
        state.id = table.proto.id
        state.string_value = json.dumps({'selection': {'rows': [0], 'columns': [], 'cells': []}})
        self.app._run(states)
        self.assertFalse(self.app.exception)

    def assert_wristband(self):
        self.assertFalse(self.app.exception)
        self.assertTrue(self.app.session_state['preset_select'].startswith('Wristband Label'))
        self.assertEqual(self.app.session_state['printer_type_select'], 'Label printer')
        self.assertEqual(self.app.session_state['label_width_mm_slider'], 254)
        self.assertEqual(self.app.session_state['label_height_mm_slider'], 25)

    def test_wristband_survives_qr_and_other_edits(self):
        self.select_preset('Wristband')
        # The browser must be told to replace its previous Sheet printer value.
        # A changed default alone leaves an already-mounted radio unchanged;
        # AppTest does not emulate that frontend behavior.
        printer = self.app.radio(key='printer_type_select__layout_0')
        self.assertTrue(printer.proto.set_value)
        self.assertEqual(printer.value, 'Label printer')
        self.assert_wristband()
        self.app.slider(key='qr_size_slider__slider').set_value(15).run()
        self.assert_wristband()
        self.assertEqual(self.app.session_state['qr_size_slider'], 15)
        self.app.number_input(key='qr_size_slider__input').set_value(17).run()
        self.assert_wristband()
        self.app.selectbox(key='code_position_select').set_value('Right').run()
        self.assert_wristband()
        self.app.checkbox(key='add_code_check').uncheck().run()
        self.assert_wristband()
        self.app.run()
        self.assert_wristband()

    def test_switching_sheet_presets_survives_edits(self):
        self.select_preset('Avery 5160')
        sheet = self.app.selectbox(key='sheet_preset_select__layout_0')
        self.assertTrue(sheet.proto.set_value)
        self.app.slider(key='qr_size_slider__slider').set_value(15).run()
        self.assertFalse(self.app.exception)
        self.assertTrue(self.app.session_state['preset_select'].startswith('Avery 5160'))
        self.assertEqual(self.app.session_state['sheet_preset_select'], 'Avery 5160 Address (3 × 10)')

    def test_custom_size_survives_edits(self):
        self.app.radio(key='label_size_mode_select__layout_0').set_value('Custom Size').run()
        self.app.number_input(key='label_width_mm_slider__input').set_value(80.0).run()
        self.app.slider(key='qr_size_slider__slider').set_value(9).run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.session_state['preset_select'], 'Custom')
        self.assertEqual(self.app.session_state['label_width_mm_slider'], 80)
        self.assertEqual(self.app.session_state['printer_type_select'], 'Label printer')


if __name__ == '__main__':
    unittest.main()
