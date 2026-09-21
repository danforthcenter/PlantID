def build_selection_table(active_df, filtered_df):
    """Add editor controls without overwriting any uploaded data fields."""
    table = filtered_df.copy()

    def unused_name(label):
        name = label
        suffix = 2
        while name in table.columns:
            name = f"{label} ({suffix})"
            suffix += 1
        return name

    row_column = unused_name("Row")
    table.insert(0, row_column, [active_df.index.get_loc(idx) + 1 for idx in table.index])
    print_column = unused_name("Print")
    table.insert(0, print_column, True)
    return table, row_column, print_column


def selected_data(edited_df, row_column, print_column):
    """Remove only the editor controls, retaining original data columns."""
    return edited_df.loc[edited_df[print_column] == True].drop(
        columns=[print_column, row_column]
    )
