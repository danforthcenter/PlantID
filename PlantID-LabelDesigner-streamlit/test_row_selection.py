import unittest

import pandas as pd
from pandas.testing import assert_frame_equal

from row_selection import apply_print_edits, build_selection_table, ticked_rows


class RowSelectionTests(unittest.TestCase):
    def test_uploaded_control_names_are_preserved(self):
        source = pd.DataFrame({
            "Row": [3, 3, 4], "Row (2)": [10, 20, 30],
            "Print": ["yes", "no", "yes"], "Print (2)": [1, 2, 3],
            "PlantID": ["A", "B", "C"],
        })
        original = source.copy(deep=True)
        table, row_column, print_column = build_selection_table(source, source.iloc[1:], unticked={1})
        self.assertTrue(table.columns.is_unique)
        self.assertEqual(table[row_column].tolist(), [2, 3])
        self.assertEqual(table[print_column].tolist(), [False, True])
        self.assertEqual((row_column, print_column), ("Row (3)", "Print (3)"))
        assert_frame_equal(ticked_rows(source, {1}), source.iloc[[0, 2]])
        assert_frame_equal(source, original)

    def test_noncolliding_columns_and_empty_selection(self):
        source = pd.DataFrame({"PlantID": ["A", "B"]})
        table, row_column, print_column = build_selection_table(source, source)
        self.assertEqual((row_column, print_column), ("Row", "Print"))
        self.assertEqual(table[print_column].tolist(), [True, True])
        assert_frame_equal(ticked_rows(source, set()), source)
        assert_frame_equal(ticked_rows(source, {0, 1}), source.iloc[:0])

    def test_empty_shown_data(self):
        source = pd.DataFrame({"Row": [3], "Print": ["original"]})
        table, _, _ = build_selection_table(source, source.iloc[:0])
        self.assertTrue(table.empty)

    def test_edits_on_a_search_apply_to_dataset_rows(self):
        # The shown table is a search result: positions 0 and 1 are dataset rows 7 and 9.
        unticked = apply_print_edits({2, 9}, [7, 9], {0: {"Print": False}, 1: {"Print": True}}, "Print")
        self.assertEqual(unticked, {2, 7})
        self.assertEqual(apply_print_edits({2}, [7], {0: {"Other": 1}}, "Print"), {2})


if __name__ == "__main__":
    unittest.main()
