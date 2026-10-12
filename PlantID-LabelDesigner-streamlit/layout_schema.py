"""Saved layout files: the v1 schema, and conversion to and from app settings.

App settings use widget keys (``label_width_mm_slider``); layout files use
descriptive nested names (``label.width_mm``) and lowercase option codes, so
the UI can change without breaking saved layouts. Schema 0 files stored the
widget keys directly and are converted on load.
"""
from label_presets import LABEL_PRESETS, SHEET_STOCK_PRESET_BY_NAME, UNIT_MM, UNIT_INCH_DECIMAL, UNIT_INCH_FRACTIONAL

SCHEMA_VERSION = 1

PRINTER_TYPE_SHEET = "Sheet printer"
PRINTER_TYPE_LABEL = "Label printer"
SHEET_SETUP_PRESET = "Sheet stock preset"
SHEET_SETUP_CUSTOM = "Custom Sheet spacing"
LABEL_PRINTER_PAGE_FORMAT = "LabelPrinter"
LABEL_SIZE_CUSTOM = "Custom Size"
LABEL_SIZE_PRESET = "Preset size"
BARCODE_TEXT_BESIDE = "Beside barcode"

LABEL_PRESET_NAMES = {preset[0] for preset in LABEL_PRESETS}

# Print-run choices (row range, filters, first label position) belong to the
# data being printed, not the design, so they are never saved in a layout.
PRINT_RUN_SETTINGS = {
    "row_range_enabled_check", "row_range_start_input", "row_range_end_input",
    "filter_enabled_check", "filter_count_input", "filter_match_mode_select",
    "sheet_start_slot_input",
}

UNITS = {UNIT_MM: "mm", UNIT_INCH_FRACTIONAL: "in_fraction", UNIT_INCH_DECIMAL: "in_decimal"}
LEFT_RIGHT = {"Left": "left", "Right": "right"}
CODE_TYPES = {"QR": "qr", "Barcode": "barcode", "None": "none"}
BARCODE_TEXT = {
    BARCODE_TEXT_BESIDE: "beside", "Above barcode": "above",
    "Below barcode": "below", "Above and below barcode": "above_and_below",
}
HIGHLIGHT_COLORS = {"Black": "black", "White": "white"}
PAGE_FORMATS = {
    "A4": "a4", "A4 Landscape": "a4_landscape",
    "Letter": "letter", "Letter Landscape": "letter_landscape",
}

# (path in the layout file, app setting, option codes or None for plain values)
FIELDS = [
    ("data.fields", "visible_columns_multiselect", None),
    ("data.field_labels_enabled", "rename_columns_check", None),
    ("data.field_labels", "column_label_overrides", None),
    ("data.split.enabled", "split_column_enabled_check", None),
    ("data.split.column", "split_column_select", None),
    ("data.split.delimiter", "split_primary_delimiter_input", None),
    ("data.split.second_delimiter_enabled", "split_secondary_enabled_check", None),
    ("data.split.second_delimiter", "split_secondary_delimiter_input", None),
    ("label.width_mm", "label_width_mm_slider", None),
    ("label.height_mm", "label_height_mm_slider", None),
    ("label.display_units", "units_select", UNITS),
    ("label.padding_mm", "label_padding_slider", None),
    ("label.border", "show_border_check", None),
    ("code.column", "code_column_select", None),
    ("code.position", "code_position_select", LEFT_RIGHT),
    ("code.edge_offset_mm", "qr_left_offset_slider", None),
    ("code.qr_size_mm", "qr_size_slider", None),
    ("code.barcode_width_mm", "barcode_width_slider", None),
    ("code.barcode_height_mm", "barcode_height_slider", None),
    ("code.barcode_text_position", "barcode_text_position_select", BARCODE_TEXT),
    ("code.fields_above_barcode", "barcode_above_columns_multiselect", None),
    ("text.font", "label_font_select", None),
    ("text.font_size_pt", "label_font_size_slider", None),
    ("text.show_field_names", "show_column_names_check", None),
    ("text.field_name_width_pct", "col_name_width_ratio_slider", None),
    ("text.row_spacing", "row_height_factor_slider", None),
    ("text.left_offset_mm", "text_left_offset_slider", None),
    ("highlight.color", "highlight_color_select", HIGHLIGHT_COLORS),
    ("highlight.padding_pt", "highlight_padding_slider", None),
    ("highlight.side_strip", "side_highlight_check", None),
    ("highlight.side_strip_width", "sidebar_factor_slider", None),
    ("wrap_tag.enabled", "wrap_enabled_check", None),
    ("wrap_tag.loop_area_mm", "wrap_leader_mm_input", None),
    ("wrap_tag.tear_off_width_mm", "wrap_tear_width_mm_input", None),
    ("wrap_tag.padding_mm", "wrap_padding_mm_input", None),
    ("wrap_tag.code_type", "wrap_code_type_select", CODE_TYPES),
    ("wrap_tag.use_main_code", "wrap_use_main_code_check", None),
    ("wrap_tag.code_column", "wrap_code_column_select", None),
    ("wrap_tag.code_position", "wrap_code_position_select", LEFT_RIGHT),
    ("wrap_tag.qr_size_mm", "wrap_qr_size_mm_input", None),
    ("wrap_tag.barcode_width_mm", "wrap_barcode_width_mm_input", None),
    ("wrap_tag.barcode_height_mm", "wrap_barcode_height_mm_input", None),
    ("wrap_tag.custom_fields", "wrap_custom_fields_check", None),
    ("wrap_tag.fields", "wrap_text_columns_multiselect", None),
    ("wrap_tag.show_field_names", "wrap_show_names_check", None),
    ("wrap_tag.font_size_pt", "wrap_font_size_input", None),
]

MARGINS = [
    ("top", "page_margin_top_mm_input"), ("right", "page_margin_right_mm_input"),
    ("bottom", "page_margin_bottom_mm_input"), ("left", "page_margin_left_mm_input"),
]
GAPS = [("horizontal", "label_gap_horizontal_mm_input"), ("vertical", "label_gap_vertical_mm_input")]

# Settings naming data columns, how a user would describe them, and when the
# setting is in use (an unused setting naming a missing column is harmless).
COLUMN_SETTINGS = [
    ("visible_columns_multiselect", "displayed fields", lambda s: True),
    ("code_column_select", "code column", lambda s: s.get("add_code_check", True)),
    ("highlight_column_select", "highlight column", lambda s: True),
    ("split_column_select", "column to split", lambda s: s.get("split_column_enabled_check")),
    ("barcode_above_columns_multiselect", "fields above barcode",
     lambda s: s.get("code_type_select") == "Barcode"
     and s.get("barcode_text_position_select") == "Above and below barcode"),
    ("wrap_code_column_select", "tear-off code column",
     lambda s: s.get("wrap_enabled_check") and not s.get("wrap_use_main_code_check", True)),
    ("wrap_text_columns_multiselect", "tear-off fields",
     lambda s: s.get("wrap_enabled_check") and s.get("wrap_custom_fields_check")),
    ("column_label_overrides", "renamed fields", lambda s: s.get("rename_columns_check")),
]


def _get_path(tree, path):
    for part in path.split("."):
        if not isinstance(tree, dict) or part not in tree:
            return None, False
        tree = tree[part]
    return tree, True


def _set_path(tree, path, value):
    *parents, leaf = path.split(".")
    for part in parents:
        tree = tree.setdefault(part, {})
    tree[leaf] = value


def settings_to_layout(settings):
    """Build a v1 layout from app settings (widget key -> value)."""
    # Seed the key order so each section reads top-down in the saved file.
    layout = {"data": {}, "label": {"preset": None}, "code": {"type": None},
              "text": {}, "highlight": {"column": None}}
    for path, key, codes in FIELDS:
        value = settings.get(key)
        _set_path(layout, path, codes.get(value, value) if codes else value)

    code_type = settings.get("code_type_select") if settings.get("add_code_check", True) else "None"
    _set_path(layout, "code.type", CODE_TYPES.get(code_type, "none"))

    highlight = settings.get("highlight_column_select")
    _set_path(layout, "highlight.column", None if highlight in (None, "None") else highlight)

    preset = (settings.get("last_label_preset_name")
              if settings.get("label_size_mode_select") == LABEL_SIZE_PRESET else None)
    _set_path(layout, "label.preset", preset)

    is_sheet = settings.get("printer_type_select") == PRINTER_TYPE_SHEET
    printer = {"type": "sheet" if is_sheet else "label"}
    if is_sheet:
        stock = settings.get("sheet_preset_select")
        use_stock = (settings.get("sheet_setup_select") == SHEET_SETUP_PRESET
                     and stock in SHEET_STOCK_PRESET_BY_NAME)
        printer["sheet_stock"] = stock if use_stock else None
        # Page geometry is kept even for stock, so the layout still prints if
        # a later app version renames or drops that stock preset.
        printer["page_format"] = PAGE_FORMATS.get(settings.get("page_format_select"), "letter")
        printer["margins_mm"] = {side: settings.get(key) for side, key in MARGINS}
        printer["gaps_mm"] = {direction: settings.get(key) for direction, key in GAPS}
    layout["printer"] = printer
    return layout


def layout_to_settings(layout):
    """App settings from a v1 layout. Unknown option codes are left out so
    the app falls back to its defaults."""
    settings = {}
    for path, key, codes in FIELDS:
        value, found = _get_path(layout, path)
        if not found:
            continue
        if codes:
            decoded = {code: option for option, code in codes.items()}
            if value not in decoded:
                continue
            value = decoded[value]
        settings[key] = value

    code_type, found = _get_path(layout, "code.type")
    if found:
        settings["add_code_check"] = code_type in ("qr", "barcode")
        if code_type in ("qr", "barcode"):
            settings["code_type_select"] = "QR" if code_type == "qr" else "Barcode"

    highlight, found = _get_path(layout, "highlight.column")
    if found:
        settings["highlight_column_select"] = highlight or "None"

    preset, found = _get_path(layout, "label.preset")
    if found:
        settings["preset_select"] = "Custom"
        if preset in LABEL_PRESET_NAMES:
            settings["label_size_mode_select"] = LABEL_SIZE_PRESET
            settings["last_label_preset_name"] = preset
        else:
            settings["label_size_mode_select"] = LABEL_SIZE_CUSTOM

    printer = layout.get("printer")
    if isinstance(printer, dict):
        if printer.get("type") == "sheet":
            settings["printer_type_select"] = PRINTER_TYPE_SHEET
            stock = printer.get("sheet_stock")
            if stock in SHEET_STOCK_PRESET_BY_NAME:
                settings["sheet_setup_select"] = SHEET_SETUP_PRESET
                settings["sheet_preset_select"] = stock
            else:
                settings["sheet_setup_select"] = SHEET_SETUP_CUSTOM
            page_formats = {code: option for option, code in PAGE_FORMATS.items()}
            if printer.get("page_format") in page_formats:
                settings["page_format_select"] = page_formats[printer["page_format"]]
            for group, pairs in (("margins_mm", MARGINS), ("gaps_mm", GAPS)):
                values = printer.get(group)
                if isinstance(values, dict):
                    settings.update({key: values[name] for name, key in pairs if name in values})
        else:
            settings["printer_type_select"] = PRINTER_TYPE_LABEL
            settings["page_format_select"] = LABEL_PRINTER_PAGE_FORMAT
    return settings


def migrate_v0_settings(settings):
    """App settings from a schema 0 file, adjusted to v1 behaviour."""
    settings = {key: value for key, value in settings.items() if key not in PRINT_RUN_SETTINGS}
    stacked_barcode = (settings.get("code_type_select") == "Barcode"
                       and settings.get("barcode_text_position_select", BARCODE_TEXT_BESIDE)
                       != BARCODE_TEXT_BESIDE)
    if stacked_barcode:
        # Schema 0 measured the stacked barcode's edge offset from inside the
        # label padding; v1 measures every code position from the label edge.
        try:
            settings["qr_left_offset_slider"] = (settings.get("qr_left_offset_slider", 2)
                                                 + settings.get("label_padding_slider", 4))
        except TypeError:
            pass
    return settings


def read_layout_file(parsed):
    """Return (settings, schema_version, error) for a parsed layout file."""
    if not isinstance(parsed, dict):
        return None, None, "Layout must be a JSON object."
    version = parsed.get("schema_version", parsed.get("template_version", 0))
    if version == 0:
        settings = parsed.get("settings", parsed)
        if not isinstance(settings, dict):
            return None, version, "Layout settings must be a JSON object."
        return migrate_v0_settings(settings), version, None
    if not isinstance(version, int):
        return None, version, f"Unrecognised layout schema version: {version!r}."
    layout = parsed.get("layout")
    if not isinstance(layout, dict):
        return None, version, "Layout file has no layout section."
    # Newer schemas are read as v1 on a best-effort basis; the app warns.
    return layout_to_settings(layout), version, None


def build_layout_file(settings, app_name, app_version):
    return {
        "schema_version": SCHEMA_VERSION,
        "app": app_name,
        "app_version": app_version,
        "layout": settings_to_layout(settings),
    }


def referenced_columns(settings):
    """(description, column) pairs for every data column the settings name."""
    refs = []
    for key, description, in_use in COLUMN_SETTINGS:
        if not in_use(settings):
            continue
        value = settings.get(key)
        if key == "column_label_overrides":
            columns = list(value) if isinstance(value, dict) else []
        elif isinstance(value, list):
            columns = value
        else:
            columns = [] if value in (None, "", "None") else [value]
        refs.extend((description, column) for column in columns)
    return refs
