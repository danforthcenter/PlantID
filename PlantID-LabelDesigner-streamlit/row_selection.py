def build_selection_table(active_df, shown_df, unticked=()):
    """Add editor controls without overwriting any uploaded data fields.
    Rows whose index is in `unticked` start with Print cleared."""
    table = shown_df.copy()

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
    table.insert(0, print_column, [idx not in unticked for idx in table.index])
    return table, row_column, print_column


def apply_print_edits(unticked, shown_index, edited_rows, print_column):
    """Unticked row indexes after the editor's edits, which are keyed by the
    position of each row in the shown table."""
    unticked = set(unticked)
    for position, change in edited_rows.items():
        if print_column in change:
            index = shown_index[int(position)]
            if change[print_column]:
                unticked.discard(index)
            else:
                unticked.add(index)
    return unticked


def ticked_rows(df, unticked):
    return df.loc[[idx not in unticked for idx in df.index]]
