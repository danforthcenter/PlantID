import unittest

from label_presets import (
    COMMON_MANUFACTURER_LABELS,
    LABEL_PRESETS,
    MANUFACTURER_PRESET_SOURCES,
    SHEET_STOCK_PRESET_BY_NAME,
    CUSTOM_SHEET_PRESET,
    ZEBRA_LABEL_SIZES,
    label_preset_matches,
    label_preset_table_row,
    label_preset_title,
)


class LabelPresetSearchTests(unittest.TestCase):
    def matches(self, query):
        return [p for p in LABEL_PRESETS if label_preset_matches(p, query)]

    def test_brand_and_part_search(self):
        self.assertEqual(len(self.matches('ZEBRA')), 22)
        self.assertEqual(len(self.matches('10010047')), 1)
        self.assertTrue(self.matches('USA Scientific'))
        self.assertTrue(self.matches('PR1MA'))

    def test_equivalent_dimensions(self):
        expected = self.matches('Zebra 4x2')
        self.assertEqual(len(expected), 1)
        for query in ['zebra 4 × 2 in', 'Zebra 4.0x2.00',
                      'Zebra 101.6 x 50.8 mm', 'Zebra 4" x 2"']:
            self.assertEqual(self.matches(query), expected, query)
        self.assertEqual(expected[0][3:5], (101.6, 50.8))
        self.assertIn('4 × 2 in · 101.6 × 50.8 mm', label_preset_title(expected[0]))

    def test_fractional_dimensions(self):
        self.assertEqual(self.matches('Zebra 2 1/4 x 1 1/4'),
                         self.matches('Zebra 2.25x1.25'))
        self.assertTrue(self.matches('Zebra 2.25x1.25'))

    def test_empty_invalid_and_no_results(self):
        self.assertEqual(self.matches('  '), LABEL_PRESETS)
        for query in ['nonexistent brand', 'Zebra 40x20', 'Zebra 4x2 mm', '1/0 x 2']:
            self.assertEqual(self.matches(query), [], query)

    def test_zebra_dimensions_and_roll_stock(self):
        presets = self.matches('Zebra')
        self.assertEqual(len(ZEBRA_LABEL_SIZES), len(presets))
        for preset, (width, height, part) in zip(presets, ZEBRA_LABEL_SIZES):
            self.assertEqual(preset[3:5], (width * 25.4, height * 25.4))
            self.assertEqual(len(preset), 5)

    def test_common_manufacturers_and_label_types_are_searchable(self):
        expected_brands = {"Avery", "DYMO", "Brother", "Brady", "LabTAG"}
        self.assertEqual(set(MANUFACTURER_PRESET_SOURCES), expected_brands)
        self.assertGreaterEqual(len(COMMON_MANUFACTURER_LABELS), 40)
        for brand in expected_brands:
            matches = self.matches(brand)
            self.assertTrue(matches, brand)
            self.assertTrue(all(label_preset_table_row(item)["Brand"] == brand
                                for item in matches))
        for label_type in ("shipping", "address", "file folder", "name badge",
                           "round", "square", "cryogenic"):
            self.assertTrue(self.matches(label_type), label_type)

    def test_common_product_numbers_and_dimensions(self):
        cases = {
            "Avery 5160": (66.675, 25.4),
            "DYMO 30252": (28.575, 88.9),
            "Brother DK-1202": (62, 100),
            "Brady M6-203-461": (25.4, 44.45),
            "LabTAG A4CL-23T1": (31.5, 13),
        }
        for query, dimensions in cases.items():
            matches = self.matches(query)
            self.assertEqual(len(matches), 1, query)
            for actual, expected in zip(matches[0][3:5], dimensions):
                self.assertAlmostEqual(actual, expected)

    def test_preset_names_are_unique(self):
        names = [item[0] for item in LABEL_PRESETS]
        self.assertEqual(len(names), len(set(names)))

    def test_search_accepts_common_sku_spellings_and_rotated_sizes(self):
        self.assertEqual(self.matches("Brother DK1202"),
                         self.matches("Brother DK-1202"))
        self.assertEqual(self.matches("Zebra Z Select 10010043"),
                         self.matches("Zebra Z-Select 10010043"))
        self.assertEqual(self.matches("Avery 4x2"),
                         self.matches("Avery 2x4"))
        self.assertTrue(self.matches("mailing address"))
        self.assertTrue(self.matches("food safety"))

    def test_general_presets_have_clear_browse_names_and_types(self):
        rows = {item[0]: label_preset_table_row(item)
                for item in LABEL_PRESETS if label_preset_table_row(item)["Brand"] == "General"}
        self.assertEqual(rows["Cryovial"]["Type"], "Laboratory")
        self.assertEqual(rows["Shipping Label"]["Type"], "Shipping")
        self.assertEqual(rows["Small Plant Tag"]["Type"], "Plant")
        self.assertIn("Identification", rows["Small Label"]["Product / template"])

    def test_every_sheet_product_has_an_explicit_sheet_mapping(self):
        linked = [item for item in LABEL_PRESETS if len(item) > 5]
        self.assertGreaterEqual(len(linked), 44)
        for item in linked:
            sheet_name = item[5]
            self.assertTrue(
                sheet_name == CUSTOM_SHEET_PRESET or sheet_name in SHEET_STOCK_PRESET_BY_NAME,
                f"Missing sheet stock definition for {item[0]}: {sheet_name}",
            )

    def test_roll_products_do_not_inherit_sheet_layouts_by_size(self):
        for item in LABEL_PRESETS:
            if item[0].startswith(("Zebra ", "DYMO ", "Brother ", "Brady ")):
                self.assertEqual(len(item), 5, item[0])

    def test_common_avery_and_dot_sheets_are_linked(self):
        by_name = {item[0]: item for item in LABEL_PRESETS}
        self.assertEqual(by_name["Avery 5160/5260/8160 Address"][5],
                         "Avery 5160 Address (3 × 10)")
        self.assertEqual(by_name["Avery 22807 Round"][5],
                         "Avery 22807 Round (3 × 4)")
        self.assertEqual(
            by_name["LabTAG A4CL-23T1 Cryo-LazrTAG PCR Cryovial"][5],
            "LabTAG A4-23 Cryogenic (6 × 21)",
        )
        self.assertIn("Sheet", by_name["PR1MA 192 Half-In Dot"][5])
        self.assertEqual(by_name["Fisherbrand Micryo 15-940-A 0.5 in Dot"][5],
                         CUSTOM_SHEET_PRESET)


if __name__ == '__main__':
    unittest.main()
