import unittest

import pandas as pd
from pandas.testing import assert_frame_equal

from row_selection import build_selection_table, selected_data


class RowSelectionTests(unittest.TestCase):
    def test_uploaded_control_names_are_preserved(self):
        source = pd.DataFrame({
            "Row": [3, 3, 4], "Row (2)": [10, 20, 30],
            "Print": ["yes", "no", "yes"], "Print (2)": [1, 2, 3],
            "PlantID": ["A", "B", "C"],
        })
        original = source.copy(deep=True)
        table, row_column, print_column = build_selection_table(source, source.iloc[1:])
        self.assertTrue(table.columns.is_unique)
        self.assertEqual(table[row_column].tolist(), [2, 3])
        table.loc[1, print_column] = False
        assert_frame_equal(selected_data(table, row_column, print_column), source.iloc[2:])
        assert_frame_equal(source, original)

    def test_noncolliding_columns_and_empty_selection(self):
        source = pd.DataFrame({"PlantID": ["A", "B"]})
        table, row_column, print_column = build_selection_table(source, source)
        self.assertEqual((row_column, print_column), ("Row", "Print"))
        assert_frame_equal(selected_data(table, row_column, print_column), source)
        table[print_column] = False
        assert_frame_equal(selected_data(table, row_column, print_column), source.iloc[:0])

    def test_empty_filtered_data(self):
        source = pd.DataFrame({"Row": [3], "Print": ["original"]})
        table, row_column, print_column = build_selection_table(source, source.iloc[:0])
        assert_frame_equal(selected_data(table, row_column, print_column), source.iloc[:0])


if __name__ == "__main__":
    unittest.main()
