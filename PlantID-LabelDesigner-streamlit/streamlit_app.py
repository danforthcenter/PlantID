import streamlit as st
import pandas as pd
import io
import os
import json
import pypdfium2 as pdfium

from reportlab.lib.pagesizes import mm, A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.graphics.barcode import qr
from reportlab.graphics.barcode import code128
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing
from reportlab.pdfbase.pdfmetrics import stringWidth

# ======================================================
# Session state for dataset
# ======================================================
if "df" not in st.session_state:
    st.session_state.df = None
if "data_source" not in st.session_state:
    st.session_state.data_source = None
if "start_selected_source" not in st.session_state:
    st.session_state.start_selected_source = None
if "loaded_template_metadata" not in st.session_state:
    st.session_state.loaded_template_metadata = None

APP_NAME = "PlantID Label Designer"
APP_VERSION = "1.2.0"
TEMPLATE_VERSION = 2
TEMPLATE_DEFAULTS = {
    "split_column_enabled_check": False,
    "split_column_select": None,
    "split_primary_delimiter_input": "_",
    "split_secondary_enabled_check": False,
    "split_secondary_delimiter_input": "-",
    "visible_columns_multiselect": [],
    "rename_columns_check": False,
    "column_label_overrides": {},
    "units_select": "Metric (mm)",
    "preset_select": "Custom",
    "label_width_mm_slider": 70,
    "label_height_mm_slider": 35,
    "label_width_in_slider": 2.75,
    "label_height_in_slider": 1.37,
    "code_type_select": "QR",
    "code_column_select": None,
    "qr_size_slider": 18,
    "barcode_width_slider": 25,
    "barcode_height_slider": 10,
    "qr_left_offset_slider": 2,
    "show_column_names_check": True,
    "row_height_factor_slider": 0.9,
    "text_left_offset_slider": 0,
    "label_font_select": "Helvetica",
    "label_font_size_slider": 7,
    "highlight_column_select": "None",
    "highlight_padding_slider": 2,
    "side_highlight_check": False,
    "sidebar_factor_slider": 0.1,
}
PREFERRED_SPLIT_COLUMNS = ["PlantID", "Plant_ID", "UID", "ID"]


def build_template_payload(label_width_mm=None, label_height_mm=None):
    settings = {
        key: st.session_state.get(key, default)
        for key, default in TEMPLATE_DEFAULTS.items()
    }
    # Save normalized label dimensions so load does not depend on preset display text.
    if label_width_mm is not None and label_height_mm is not None:
        width_mm = float(label_width_mm)
        height_mm = float(label_height_mm)
        settings["preset_select"] = "Custom"
        settings["label_width_mm_slider"] = int(round(width_mm))
        settings["label_height_mm_slider"] = int(round(height_mm))
        settings["label_width_in_slider"] = round(width_mm / 25.4, 3)
        settings["label_height_in_slider"] = round(height_mm / 25.4, 3)
    return {
        "template_version": TEMPLATE_VERSION,
        "app": APP_NAME,
        "app_version": APP_VERSION,
        "settings": settings,
    }


def load_template_payload(uploaded_file):
    if uploaded_file is None:
        return None, "No file selected."
    try:
        raw = uploaded_file.getvalue()
        parsed = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        return None, f"Could not read template file: {exc}"

    if not isinstance(parsed, dict):
        return None, "Template must be a JSON object."

    settings = parsed.get("settings", parsed)
    if not isinstance(settings, dict):
        return None, "Template settings must be a JSON object."

    applied = {}
    for key in TEMPLATE_DEFAULTS:
        if key in settings:
            applied[key] = settings[key]

    if not applied:
        return None, "No supported settings were found in the template."

    for key, value in applied.items():
        st.session_state[key] = value

    st.session_state["loaded_template_metadata"] = {
        "filename": getattr(uploaded_file, "name", "template.json"),
        "app_name": parsed.get("app", APP_NAME),
        "app_version": parsed.get("app_version", "Not recorded"),
        "template_version": parsed.get("template_version", "Not recorded"),
    }

    # Reset dynamic rename inputs so loaded templates repopulate every renamed column.
    for key in list(st.session_state.keys()):
        if str(key).startswith("column_label_override_"):
            del st.session_state[key]

    if isinstance(st.session_state.get("column_label_overrides"), dict):
        for column, label in st.session_state["column_label_overrides"].items():
            st.session_state[f"column_label_override_{column}"] = label

    # Backfill equivalent units and force Custom so loaded dimensions are respected.
    if "label_width_mm_slider" in applied and "label_height_mm_slider" in applied:
        try:
            w_mm = float(applied["label_width_mm_slider"])
            h_mm = float(applied["label_height_mm_slider"])
            st.session_state["label_width_in_slider"] = round(w_mm / 25.4, 3)
            st.session_state["label_height_in_slider"] = round(h_mm / 25.4, 3)
            st.session_state["preset_select"] = "Custom"
        except Exception:
            pass
    elif "label_width_in_slider" in applied and "label_height_in_slider" in applied:
        try:
            w_in = float(applied["label_width_in_slider"])
            h_in = float(applied["label_height_in_slider"])
            st.session_state["label_width_mm_slider"] = int(round(w_in * 25.4))
            st.session_state["label_height_mm_slider"] = int(round(h_in * 25.4))
            st.session_state["preset_select"] = "Custom"
        except Exception:
            pass

    return applied, None


def render_version_footer():
    st.divider()
    loaded_template = st.session_state.get("loaded_template_metadata")
    footer_text = f"{APP_NAME} v{APP_VERSION} | Template JSON schema v{TEMPLATE_VERSION}"

    if loaded_template:
        footer_text += (
            f" | Loaded template: {loaded_template.get('filename', 'template.json')} "
            f"(saved with {loaded_template.get('app_name', APP_NAME)} "
            f"v{loaded_template.get('app_version', 'Not recorded')}, "
            f"JSON schema v{loaded_template.get('template_version', 'Not recorded')})"
        )

    st.caption(footer_text)

    if not loaded_template:
        return

    version_notes = []
    loaded_app_version = loaded_template.get("app_version")
    loaded_template_version = loaded_template.get("template_version")

    if loaded_app_version in (None, "", "Not recorded"):
        version_notes.append("The loaded template does not record an app version.")
    elif loaded_app_version != APP_VERSION:
        version_notes.append(
            f"The loaded template was saved with app version {loaded_app_version}, "
            f"which differs from this app version {APP_VERSION}."
        )

    if isinstance(loaded_template_version, int):
        if loaded_template_version > TEMPLATE_VERSION:
            version_notes.append(
                "The loaded template uses a newer JSON schema than this app, so some settings may not load."
            )
        elif loaded_template_version < TEMPLATE_VERSION:
            version_notes.append(
                "The loaded template uses an older JSON schema than this app."
            )
    elif loaded_template_version not in (None, "", "Not recorded"):
        version_notes.append("The loaded template uses an unrecognized JSON schema value.")

    if version_notes:
        st.caption("Version note: " + " ".join(version_notes))


def ensure_choice(key, options, default):
    if key not in st.session_state:
        st.session_state[key] = default
    if st.session_state[key] not in options:
        st.session_state[key] = default


def ensure_int_range(key, default, min_value, max_value):
    try:
        value = int(st.session_state.get(key, default))
    except Exception:
        value = default
    st.session_state[key] = max(min_value, min(max_value, value))


def ensure_float_range(key, default, min_value, max_value):
    try:
        value = float(st.session_state.get(key, default))
    except Exception:
        value = default
    st.session_state[key] = max(min_value, min(max_value, value))


def ensure_bool(key, default):
    st.session_state[key] = bool(st.session_state.get(key, default))


def ensure_text_value(key, default):
    if key not in st.session_state or st.session_state[key] is None:
        st.session_state[key] = default


def ensure_dict_value(key, default):
    if key not in st.session_state or not isinstance(st.session_state[key], dict):
        st.session_state[key] = dict(default)


def ensure_multiselect_choices(key, options, default):
    if key not in st.session_state:
        st.session_state[key] = default
    st.session_state[key] = [
        value for value in st.session_state[key] if value in options
    ]
    if not st.session_state[key]:
        st.session_state[key] = default


def detect_default_split_column(columns):
    if not columns:
        return None

    for candidate in PREFERRED_SPLIT_COLUMNS:
        if candidate in columns:
            return candidate

    lowered = {column.lower(): column for column in columns}
    for candidate in PREFERRED_SPLIT_COLUMNS:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]

    return columns[0]


def unique_column_name(base_name, existing_columns):
    if base_name not in existing_columns:
        existing_columns.add(base_name)
        return base_name

    suffix = 2
    while f"{base_name}_{suffix}" in existing_columns:
        suffix += 1

    unique_name = f"{base_name}_{suffix}"
    existing_columns.add(unique_name)
    return unique_name


def build_split_dataframe(
    df,
    split_enabled,
    split_column,
    primary_delimiter,
    secondary_split_enabled=False,
    secondary_delimiter="",
):
    if df is None:
        return None, [], []

    result = df.copy()
    if not split_enabled or split_column not in result.columns or not primary_delimiter:
        return result, [], []

    existing_columns = set(result.columns.tolist())
    source_values = result[split_column].apply(
        lambda value: "" if pd.isna(value) else str(value)
    )
    primary_parts_per_row = [
        [part.strip() for part in value.split(primary_delimiter)]
        for value in source_values
    ]

    max_primary_parts = max((len(parts) for parts in primary_parts_per_row), default=0)
    if max_primary_parts <= 1:
        return result, [], []

    primary_columns = []

    for primary_index in range(max_primary_parts):
        column_name = unique_column_name(
            f"{split_column}_split_{primary_index + 1}",
            existing_columns,
        )
        primary_columns.append(column_name)
        result[column_name] = [
            parts[primary_index] if primary_index < len(parts) else ""
            for parts in primary_parts_per_row
        ]

    secondary_columns = []
    if secondary_split_enabled and secondary_delimiter:
        for primary_index, primary_column in enumerate(primary_columns, start=1):
            secondary_parts_per_row = []
            max_secondary_parts = 0

            for value in result[primary_column].tolist():
                if secondary_delimiter in value:
                    secondary_parts = [
                        part.strip() for part in value.split(secondary_delimiter)
                    ]
                else:
                    secondary_parts = [value]
                secondary_parts_per_row.append(secondary_parts)
                if len(secondary_parts) > 1:
                    max_secondary_parts = max(max_secondary_parts, len(secondary_parts))

            if max_secondary_parts <= 1:
                continue

            for secondary_index in range(max_secondary_parts):
                column_name = unique_column_name(
                    f"{split_column}_split_{primary_index}_{secondary_index + 1}",
                    existing_columns,
                )
                secondary_columns.append(column_name)
                result[column_name] = [
                    parts[secondary_index]
                    if len(parts) > 1 and secondary_index < len(parts)
                    else ""
                    for parts in secondary_parts_per_row
                ]

    ordered_columns = []
    for column in df.columns.tolist():
        ordered_columns.append(column)
        if column == split_column:
            ordered_columns.extend(primary_columns)
            ordered_columns.extend(secondary_columns)

    ordered_columns.extend(
        column for column in result.columns.tolist() if column not in ordered_columns
    )

    return result[ordered_columns], primary_columns, secondary_columns

# ======================================================
# Draw a single label directly onto a ReportLab canvas
# ======================================================

def draw_label_on_canvas(
    c,
    df_row,
    x,
    y,
    visible_columns,
    code_column,
    code_type="QR",
    highlight_column=None,
    label_font="Helvetica",
    label_font_size=7,
    label_width=70,
    label_height=35,
    qr_size=18,
    barcode_width=25,
    barcode_height=10,
    row_height_factor=0.9,
    sidebar_factor=0.25,
    highlight_padding=2,
    padding=4,
    show_border=True,
    show_column_names=True,
    side_highlight=False,
    qr_left_offset=2,
    text_left_offset=0,
    column_label_map=None,
):
    def font_variant(base_font, variant):
        variants = {
            "Helvetica": {
                "regular": "Helvetica",
                "bold": "Helvetica-Bold",
                "italic": "Helvetica-Oblique",
                "bold_italic": "Helvetica-BoldOblique",
            },
            "Times-Roman": {
                "regular": "Times-Roman",
                "bold": "Times-Bold",
                "italic": "Times-Italic",
                "bold_italic": "Times-BoldItalic",
            },
            "Courier": {
                "regular": "Courier",
                "bold": "Courier-Bold",
                "italic": "Courier-Oblique",
                "bold_italic": "Courier-BoldOblique",
            },
        }
        return variants.get(base_font, variants["Helvetica"]).get(variant, base_font)

    lw_pt = label_width * mm
    lh_pt = label_height * mm
    pad_pt = padding * mm
    column_label_map = column_label_map or {}

    # ---- 1. Outer border ----
    if show_border:
        c.saveState()
        c.setStrokeColor(colors.lightgrey)
        c.setLineWidth(0.5)
        c.rect(x, y, lw_pt, lh_pt, stroke=1, fill=0)
        c.restoreState()

    # ---- 2. Sidebar Logic (Isolated with saveState) ----
    side_col_width = 0
    if side_highlight and highlight_column:
        side_col_width = lw_pt * sidebar_factor
        col_name = column_label_map.get(highlight_column, highlight_column)
        value = str(df_row[highlight_column])
        font_size = label_font_size

        # Calculate sidebar geometry
        val_w = stringWidth(value, font_variant(label_font, "bold"), font_size) + highlight_padding
        nam_w = stringWidth(f"{col_name}:", font_variant(label_font, "italic"), font_size)
        gap = 1 * mm
        total_h = nam_w + gap + val_w
        sidebar_bottom = y + (lh_pt - total_h) / 2

        # Draw Side Label text
        c.saveState()
        c.setFillColor(colors.black)
        c.setFont(font_variant(label_font, "italic"), font_size)
        c.translate(x + side_col_width / 2, sidebar_bottom + nam_w / 2)
        c.rotate(90)
        c.drawCentredString(0, 0, f"{col_name}:")
        c.restoreState()

        # Draw Side Value Box
        val_rect_y = sidebar_bottom + nam_w + gap
        c.saveState()
        c.setFillColor(colors.black)
        c.rect(x, val_rect_y, side_col_width, val_w, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont(font_variant(label_font, "bold"), font_size)
        c.translate(x + side_col_width / 2, val_rect_y + val_w / 2)
        c.rotate(90)
        c.drawCentredString(0, 0, value)
        c.restoreState()

    # ---- 3. Code (QR/Barcode) Logic ----
    code_x = x + side_col_width + (qr_left_offset * mm)
    text_x = x + side_col_width + pad_pt

    if code_column is not None and code_type != "None":
        val = str(df_row[code_column])
        
        if code_type == "QR":
            qr_pt = qr_size * mm
            code_y = y + (lh_pt - qr_pt) / 2
            qrobj = qr.QrCodeWidget(val)
            b = qrobj.getBounds()
            scale = qr_pt / max(b[2]-b[0], b[3]-b[1])
            d = Drawing(qr_pt, qr_pt, transform=[scale, 0, 0, scale, 0, 0])
            d.add(qrobj)
            renderPDF.draw(d, c, code_x, code_y)
            text_x = code_x + qr_pt + 2 * mm

        elif code_type == "Barcode":
            bw_pt = barcode_width * mm
            bh_pt = barcode_height * mm
            code_y = y + (lh_pt - bh_pt) / 2
            
            # Draw directly to canvas
            bc = code128.Code128(
                val,
                barHeight=bh_pt,
                barWidth=bw_pt / max(len(val) * 11, 1),
                humanReadable=False
            )
            bc.drawOn(c, code_x, code_y)
            text_x = code_x + bw_pt + 2 * mm

    text_x += (text_left_offset * mm)

    # ---- 4. Text Rows Logic ----
    row_count = max(len(visible_columns), 1)
    row_height = ((lh_pt - 2 * pad_pt) / row_count) * row_height_factor
    text_y_start = y + lh_pt - pad_pt - row_height * 0.1
    avail_w = lw_pt - (text_x - x) - pad_pt

    for idx, col_name in enumerate(visible_columns):
        val = str(df_row[col_name])
        display_name = column_label_map.get(col_name, col_name)
        y_pos = text_y_start - idx * row_height
        
        c.saveState()
        if show_column_names:
            c.setFont(font_variant(label_font, "italic"), label_font_size)
            c.setFillColor(colors.black)
            c.drawRightString(text_x + avail_w * 0.35, y_pos, f"{display_name}:")

        if col_name == highlight_column:
            c.setFont(font_variant(label_font, "bold"), label_font_size)
            v_w = stringWidth(val, font_variant(label_font, "bold"), label_font_size) + highlight_padding
            c.setFillColor(colors.black)
            highlight_height = max(6, label_font_size + 2)
            highlight_y = y_pos - (label_font_size * 0.3)
            c.rect(text_x + avail_w * 0.4 - 2, highlight_y, v_w, highlight_height, fill=1)
            c.setFillColor(colors.white)
            c.drawString(text_x + avail_w * 0.4, y_pos, val)
        else:
            c.setFont(font_variant(label_font, "regular"), label_font_size)
            c.setFillColor(colors.black)
            c.drawString(text_x + avail_w * 0.4, y_pos, val)
        c.restoreState()

# ======================================================
# Multi-label PDF sheet
# ======================================================
def generate_sheet_direct(
    df,
    visible_columns,
    code_column,
    code_type,
    highlight_column,
    label_font,
    label_font_size,
    label_width,
    label_height,
    qr_size,
    barcode_width,
    barcode_height,
    row_height_factor,
    sidebar_factor,
    highlight_padding,
    show_border=True,
    show_column_names=True,
    side_highlight=False,
    qr_left_offset=2,
    text_left_offset=0,
    column_label_map=None,
    page_format="LabelPrinter",
    repeat_count=1,
):
    # Page size logic
    if page_format == "A4":
        page_width, page_height = A4
        margin = 5 * mm
    elif page_format == "Letter":
        from reportlab.lib.pagesizes import letter
        page_width, page_height = letter
        margin = 5 * mm
    elif page_format == "LabelPrinter":
        # Exact label size, no margin
        page_width = label_width * mm
        page_height = label_height * mm
        margin = 0
    else:
        page_width, page_height = A4
        margin = 5 * mm

    c = canvas.Canvas("multi_labels.pdf", pagesize=(page_width, page_height))

    x = margin
    y = page_height - label_height * mm - margin

    for _, row in df.iterrows():
        for _ in range(repeat_count):
            draw_label_on_canvas(
                c, row, x, y,
                visible_columns,
                code_column,
                code_type,
                highlight_column,
                label_font,
                label_font_size,
                label_width,
                label_height,
                qr_size,
                barcode_width,
                barcode_height,
                row_height_factor,
                sidebar_factor,
                highlight_padding,
                show_border=show_border,
                show_column_names=show_column_names,
                side_highlight=side_highlight,
                qr_left_offset=qr_left_offset,
                text_left_offset=text_left_offset,
                column_label_map=column_label_map,
            )

            x += label_width * mm + margin
            if x + label_width * mm > page_width:
                x = margin
                y -= label_height * mm + margin
                if y < margin:
                    c.showPage()
                    x = margin
                    y = page_height - label_height * mm - margin

    c.save()
    return "multi_labels.pdf"


# ======================================================
# Streamlit UI
# ======================================================
st.set_page_config(layout="wide")
st.title(APP_NAME)

# ======================
# Start page
# ======================
if st.session_state.df is None:
    st.write(
        "PlantID Label Designer is a Streamlit web application for generating customizable plant sample labels "
        "from a CSV file. Labels can be optionally designed with QR and Barcodes and exported in various sizes "
        "for label or paper printing."
    )
    
    st.info("Choose a CSV or click 'Use default CSV'")
    uploaded_file = st.file_uploader("Browse files", type=["csv"], label_visibility="visible")
    if st.button("Use example CSV", key="use_default_csv_btn"):
        st.session_state.start_selected_source = "Example dataset"

    if uploaded_file is not None:
        st.session_state.start_selected_source = "Uploaded CSV"
    elif st.session_state.start_selected_source == "Uploaded CSV":
        st.session_state.start_selected_source = None

    if st.session_state.start_selected_source == "Uploaded CSV" and uploaded_file is not None:
        st.success(f"Loaded data: Uploaded CSV ({uploaded_file.name})")
    elif st.session_state.start_selected_source == "Example dataset":
        st.success("Loaded data: Example file (PV1_metadata.csv)")

    st.info("Optionally, load a label template saved from a previous session")
    use_template_layout = st.toggle("Use a template layout", value=False, key="use_template_layout_toggle")

    if use_template_layout:
        template_file = st.file_uploader(
            "Choose template file",
            type=["json"],
            key="start_template_file",
        )
        if template_file is not None:
            _, template_error = load_template_payload(template_file)
            if template_error:
                st.error(template_error)
            else:
                st.success(f"Loaded template: {template_file.name}")

    st.info("When ready, click Go.")

    if st.button("Go", key="start_go_btn"):
        if st.session_state.start_selected_source == "Example dataset":
            example_path = os.path.join(os.path.dirname(__file__), "PV1_metadata.csv")
            # Create a simple example if file doesn't exist
            if os.path.exists(example_path):
                st.session_state.df = pd.read_csv(example_path)
            else:
                st.session_state.df = pd.DataFrame({
                    "ID": ["P001", "P002", "P003", "P004"],
                    "Species": ["Arabidopsis", "Arabidopsis", "Wheat", "Maize"],
                    "Genotype": ["Col-0", "Ler", "Bobwhite", "B73"],
                    "Treatment": ["Control", "Salt", "Control", "Drought"]
                })
            st.session_state.data_source = "Example dataset"
            st.rerun()
        elif st.session_state.start_selected_source == "Uploaded CSV" and uploaded_file is not None:
            st.session_state.df = pd.read_csv(uploaded_file)
            st.session_state.data_source = "Uploaded CSV"
            st.rerun()
        else:
            st.error("Select a CSV upload or click 'Use default CSV' before clicking Go.")

    render_version_footer()
    st.stop()

# ==========================================
# Section order containers
# ==========================================
summary_container = st.container()
preview_container = st.container()
filter_container = st.container()
export_container = st.container()

split_column_options = st.session_state.df.columns.tolist()
default_split_column = detect_default_split_column(split_column_options)
ensure_bool("split_column_enabled_check", TEMPLATE_DEFAULTS["split_column_enabled_check"])
ensure_choice("split_column_select", split_column_options, default_split_column)
ensure_text_value(
    "split_primary_delimiter_input",
    TEMPLATE_DEFAULTS["split_primary_delimiter_input"],
)
ensure_bool(
    "split_secondary_enabled_check",
    TEMPLATE_DEFAULTS["split_secondary_enabled_check"],
)
ensure_text_value(
    "split_secondary_delimiter_input",
    TEMPLATE_DEFAULTS["split_secondary_delimiter_input"],
)
ensure_bool("rename_columns_check", TEMPLATE_DEFAULTS["rename_columns_check"])
ensure_dict_value("column_label_overrides", TEMPLATE_DEFAULTS["column_label_overrides"])

active_df, generated_split_columns, generated_secondary_split_columns = build_split_dataframe(
    st.session_state.df,
    st.session_state.get("split_column_enabled_check", False),
    st.session_state.get("split_column_select"),
    st.session_state.get("split_primary_delimiter_input", "_"),
    st.session_state.get("split_secondary_enabled_check", False),
    st.session_state.get("split_secondary_delimiter_input", "-"),
)

with filter_container:
    # ==========================================
    # 3. Filter & Select Rows
    # ==========================================
    st.subheader("3. Filter & Select Rows")

    st.write("Check the **Print** box for rows you want to include in the PDF:")

    table_col, controls_col = st.columns([4, 1])
    with controls_col:
        filter_column_options = ["All Columns"] + active_df.columns.tolist()
        ensure_choice("filter_column_select", filter_column_options, "All Columns")
        filter_col = st.selectbox("Filter in column", filter_column_options, key="filter_column_select")
        search_query = st.text_input("Search rows", placeholder="Type to filter...")

    if search_query:
        if filter_col == "All Columns":
            mask = active_df.astype(str).apply(
                lambda x: x.str.contains(search_query, case=False, na=False)
            ).any(axis=1)
        else:
            mask = active_df[filter_col].astype(str).str.contains(search_query, case=False, na=False)
        filtered_df = active_df[mask].copy()
    else:
        filtered_df = active_df.copy()

    df_for_selection = filtered_df.copy()
    df_for_selection.insert(0, "Print", True)

    with table_col:
        edited_df = st.data_editor(
            df_for_selection,
            column_config={"Print": st.column_config.CheckboxColumn("Print", default=True)},
            disabled=active_df.columns.tolist(),
            use_container_width=True,
            hide_index=True,
            key="editor"
        )

    df_to_use = edited_df[edited_df["Print"] == True].drop(columns=["Print"])

    if df_to_use.empty:
        st.warning("No rows selected for printing. Please filter or check boxes above.")

# ---- Sidebar ----
st.sidebar.title("Label Setup")

# 1. Data Fields Category
with st.sidebar.expander("Data Fields", expanded=True):
    visible_column_options = active_df.columns.tolist()
    visible_column_defaults = (
        visible_column_options[:2]
        if len(visible_column_options) > 1
        else visible_column_options
    )
    ensure_multiselect_choices(
        "visible_columns_multiselect",
        visible_column_options,
        visible_column_defaults,
    )
    visible_columns = st.multiselect(
        "Columns to display",
        visible_column_options,
        key="visible_columns_multiselect",
    )

    split_column_enabled = st.checkbox(
        "Split a column into new fields",
        key="split_column_enabled_check",
        help="Create extra columns from an ID-like field while keeping the original column.",
    )

    if split_column_enabled:
        split_column = st.selectbox(
            "Column to split",
            split_column_options,
            key="split_column_select",
            help="Defaults to the first matching PlantID, Plant_ID, UID, or ID column when available.",
        )
        primary_delimiter = st.text_input(
            "First delimiter",
            key="split_primary_delimiter_input",
            help="Any character or string can be used, for example _, -, /, or |.",
        )
        split_secondary_enabled = st.checkbox(
            "Apply a second delimiter",
            key="split_secondary_enabled_check",
        )
        if split_secondary_enabled:
            secondary_delimiter = st.text_input(
                "Second delimiter",
                key="split_secondary_delimiter_input",
                help="This is applied to any first-pass split values that still contain the second delimiter.",
            )

        if not primary_delimiter:
            st.warning("Enter a first delimiter to generate split columns.")
        elif generated_split_columns:
            st.caption(
                "Generated columns: " + ", ".join(generated_split_columns + generated_secondary_split_columns)
            )
        else:
            st.caption("No new columns were created with the current delimiter settings.")

    row_index = st.number_input(
        "Preview row",
        min_value=1,
        max_value=max(1, len(filtered_df)),
        value=1,
    ) - 1

    if split_column_enabled and generated_split_columns and not filtered_df.empty:
        preview_columns = generated_split_columns + generated_secondary_split_columns
        preview_values = [str(filtered_df.iloc[row_index][split_column])]
        preview_values.extend(
            str(filtered_df.iloc[row_index][column])
            for column in preview_columns
            if str(filtered_df.iloc[row_index][column])
        )
        st.caption(
            "Split preview: " + " | ".join(f'"{value}"' for value in preview_values)
        )
    
    repeat_count = st.number_input(
        "Copies per label",
        min_value=1,
        max_value=100,
        value=1,
        help="How many times each record will be printed."
    )

# 2. Label Size Category
with st.sidebar.expander("Label Size", expanded=False):
    UNIT_MM = "Metric (mm)"
    UNIT_INCH_FRACTIONAL = "Imperial (inches)"
    UNIT_INCH_DECIMAL = "Imperial (inch decimal)"

    unit_options = [UNIT_MM, UNIT_INCH_FRACTIONAL, UNIT_INCH_DECIMAL]
    ensure_choice("units_select", unit_options, TEMPLATE_DEFAULTS["units_select"])
    units = st.selectbox("Units", unit_options, key="units_select")

    LABEL_PRESETS = [
        ("Cryovial", 25, 12, 25, 12),
        ("Small Label", 25, 67, 67, 25),
        ("Wristband Label", 25, 254, 254, 25),
        ("Small Plant Tag", 50, 25, 50, 25),
        ("Cryobox / Tube", 30, 15, 30, 15),
        ("General Purpose", 76, 25, 76, 25),
        ("Food Label", 76, 51, 76, 51),
        ("Tag Label", 57, 102, 57, 102),
        ("Standard Plant Label", 70, 35, 70, 35),
        ("Large Field Label", 90, 45, 90, 45),
        ("Shipping Label", 102, 152, 102, 152),
        ("Square Label", 51, 51, 51, 51),
    ]

    def format_fractional_inches(value_in):
        from fractions import Fraction
        whole = int(value_in)
        frac = Fraction(value_in - whole).limit_denominator(16)
        if frac.numerator == 0: return str(whole)
        if whole == 0: return f"{frac.numerator}/{frac.denominator}"
        return f"{whole} {frac.numerator}/{frac.denominator}"

    def format_preset_label(name, display_w_mm, display_h_mm, units_mode):
        if units_mode == UNIT_MM: return f"{name} ({display_w_mm} × {display_h_mm} mm)"
        w_in, h_in = display_w_mm / 25.4, display_h_mm / 25.4
        if units_mode == UNIT_INCH_FRACTIONAL: return f"{name} ({format_fractional_inches(w_in)} × {format_fractional_inches(h_in)} inches)"
        return f"{name} ({w_in:.3f} × {h_in:.3f} inches)"

    preset_options = ["Custom"] + [format_preset_label(n, w, h, units) for n, w, h, _, _ in LABEL_PRESETS]
    ensure_choice("preset_select", preset_options, TEMPLATE_DEFAULTS["preset_select"])
    preset = st.selectbox("Preset", preset_options, key="preset_select")
    
    if preset == "Custom":
        if units == UNIT_MM:
            ensure_int_range("label_width_mm_slider", TEMPLATE_DEFAULTS["label_width_mm_slider"], 10, 140)
            ensure_int_range("label_height_mm_slider", TEMPLATE_DEFAULTS["label_height_mm_slider"], 10, 140)
            label_width = st.slider("Width (mm)", 10, 140, step=1, key="label_width_mm_slider")
            label_height = st.slider("Height (mm)", 10, 140, step=1, key="label_height_mm_slider")
        else:
            step_in = 1 / 16 if units == UNIT_INCH_FRACTIONAL else 0.01
            ensure_float_range("label_width_in_slider", TEMPLATE_DEFAULTS["label_width_in_slider"], 0.4, 5.5)
            ensure_float_range("label_height_in_slider", TEMPLATE_DEFAULTS["label_height_in_slider"], 0.4, 5.5)
            label_width_in = st.slider("Width (in)", 0.4, 5.5, step=step_in, key="label_width_in_slider")
            label_height_in = st.slider("Height (in)", 0.4, 5.5, step=step_in, key="label_height_in_slider")
            label_width, label_height = label_width_in * 25.4, label_height_in * 25.4
    else:
        label_width, label_height = LABEL_PRESETS[preset_options.index(preset)-1][3:5]

# 3. Code Settings Category
with st.sidebar.expander("Code Settings", expanded=False):
    code_type_options = ["QR", "Barcode", "None"]
    ensure_choice("code_type_select", code_type_options, TEMPLATE_DEFAULTS["code_type_select"])
    code_type = st.selectbox("Code type", code_type_options, key="code_type_select")
    if code_type != "None":
        code_column_options = active_df.columns.tolist()
        ensure_choice("code_column_select", code_column_options, code_column_options[0])
        code_column = st.selectbox("Code column", code_column_options, key="code_column_select")
    else:
        code_column = None

    if code_type == "QR":
        qr_max = max(8, int(label_height - 2))
        ensure_int_range("qr_size_slider", min(18, qr_max), 8, qr_max)
        qr_size = st.slider("QR size (mm)", 8, qr_max, key="qr_size_slider")
        barcode_width = barcode_height = 0
    elif code_type == "Barcode":
        max_barcode_width = max(15, int(label_width - 5))
        max_barcode_height = max(5, int(label_height - 5))
        ensure_int_range("barcode_width_slider", TEMPLATE_DEFAULTS["barcode_width_slider"], 15, max_barcode_width)
        ensure_int_range("barcode_height_slider", TEMPLATE_DEFAULTS["barcode_height_slider"], 5, max_barcode_height)
        barcode_width = st.slider("Barcode width (mm)", 15, max_barcode_width, key="barcode_width_slider")
        barcode_height = st.slider("Barcode height (mm)", 5, max_barcode_height, key="barcode_height_slider")
        qr_size = 0
    else:
        qr_size = barcode_width = barcode_height = 0

    max_qr_left_offset = int(label_width / 2)
    ensure_int_range("qr_left_offset_slider", TEMPLATE_DEFAULTS["qr_left_offset_slider"], 0, max_qr_left_offset)
    qr_left_offset = st.slider("Code left offset (mm)", 0, max_qr_left_offset, key="qr_left_offset_slider")

# 4. Design and Aesthetics Category
with st.sidebar.expander("Design & Aesthetics", expanded=False):
    ensure_bool("show_column_names_check", TEMPLATE_DEFAULTS["show_column_names_check"])
    show_column_names = st.checkbox("Show column names", key="show_column_names_check")
    ensure_float_range("row_height_factor_slider", TEMPLATE_DEFAULTS["row_height_factor_slider"], 0.1, 1.5)
    row_height_factor = st.slider("Row height factor", 0.1, 1.5, key="row_height_factor_slider")
    max_text_left_offset = int(label_width / 2)
    ensure_int_range("text_left_offset_slider", TEMPLATE_DEFAULTS["text_left_offset_slider"], 0, max_text_left_offset)
    text_left_offset = st.slider("Text left offset (mm)", 0, max_text_left_offset, key="text_left_offset_slider")
    label_font_options = ["Helvetica", "Times-Roman", "Courier"]
    ensure_choice("label_font_select", label_font_options, TEMPLATE_DEFAULTS["label_font_select"])
    label_font = st.selectbox("Label font", label_font_options, key="label_font_select")
    ensure_int_range("label_font_size_slider", TEMPLATE_DEFAULTS["label_font_size_slider"], 4, 14)
    label_font_size = st.slider("Label font size (pt)", 4, 14, key="label_font_size_slider")
    highlight_options = ["None"] + active_df.columns.tolist()
    ensure_choice("highlight_column_select", highlight_options, TEMPLATE_DEFAULTS["highlight_column_select"])
    highlight_column = st.selectbox("Highlight column", highlight_options, key="highlight_column_select")
    highlight_column = None if highlight_column == "None" else highlight_column
    rename_columns_enabled = st.checkbox(
        "Rename displayed columns",
        key="rename_columns_check",
        help="Override the labels printed on the preview and exported labels without changing the dataset itself.",
    )
    if rename_columns_enabled:
        column_label_overrides = dict(st.session_state.get("column_label_overrides", {}))
        for column in visible_columns:
            override_key = f"column_label_override_{column}"
            if override_key not in st.session_state:
                st.session_state[override_key] = column_label_overrides.get(column, "")
            override_value = st.text_input(
                f"Display label for {column}",
                key=override_key,
                placeholder=column,
            ).strip()
            if override_value and override_value != column:
                column_label_overrides[column] = override_value
            else:
                column_label_overrides.pop(column, None)
        st.session_state["column_label_overrides"] = column_label_overrides

    if highlight_column:
        ensure_int_range("highlight_padding_slider", TEMPLATE_DEFAULTS["highlight_padding_slider"], 0, 20)
        ensure_bool("side_highlight_check", TEMPLATE_DEFAULTS["side_highlight_check"])
        highlight_padding = st.slider("Highlight padding", 0, 20, key="highlight_padding_slider")
        side_highlight = st.checkbox("Side strip highlight", key="side_highlight_check")
    else:
        highlight_padding = side_highlight = 0

    if side_highlight:
        ensure_float_range("sidebar_factor_slider", TEMPLATE_DEFAULTS["sidebar_factor_slider"], 0.05, 0.5)
        sidebar_factor = st.slider("Sidebar width factor", 0.05, 0.5, key="sidebar_factor_slider")
    else:
        sidebar_factor = 0
    show_border = True
    if rename_columns_enabled:
        column_label_map = {
            column: st.session_state["column_label_overrides"].get(column, column)
            for column in active_df.columns.tolist()
        }
    else:
        column_label_map = {column: column for column in active_df.columns.tolist()}

    template_json = json.dumps(
        build_template_payload(label_width_mm=label_width, label_height_mm=label_height),
        indent=2,
    ).encode("utf-8")
    st.download_button(
        "Save template",
        data=template_json,
        file_name="plantid_label_template.json",
        mime="application/json",
    )

with summary_container:
    # ==========================================
    # 1. Dataset Summary
    # ==========================================
    st.subheader("1. Dataset Summary")
    c1, c2, c3 = st.columns(3)
    c1.metric("Original Rows", len(st.session_state.df))
    c2.metric("Filtered Rows", len(filtered_df))
    c3.metric("Data Source", st.session_state.data_source)

    with st.expander("Dataframe controls"):
        st.warning("This will clear the current dataframe and return you to the start page.")
        if st.button("Clear dataframe and restart"):
            st.session_state.df = None
            st.session_state.data_source = None
            st.rerun()

with preview_container:
    # ==========================================
    # 2. Live Preview
    # ==========================================
    st.subheader("2. Live Preview")
    if not filtered_df.empty:
        buffer = io.BytesIO()
        c_prev = canvas.Canvas(buffer, pagesize=(label_width * mm, label_height * mm))

        draw_label_on_canvas(
            c_prev, filtered_df.iloc[row_index], 0, 0,
            visible_columns, code_column, code_type, highlight_column,
            label_font, label_font_size, label_width, label_height,
            qr_size, barcode_width, barcode_height, row_height_factor,
            sidebar_factor, highlight_padding, show_border=show_border,
            show_column_names=show_column_names, side_highlight=side_highlight,
            qr_left_offset=qr_left_offset, text_left_offset=text_left_offset,
            column_label_map=column_label_map,
        )
        c_prev.save()
        buffer.seek(0)
        st.image(pdfium.PdfDocument(buffer)[0].render(scale=3).to_pil(), caption=f"Previewing Row {row_index + 1}")
    else:
        st.info("No rows match the filter for preview.")

with export_container:
    # ==========================================
    # 4. Export Labels / PDF
    # ==========================================
    st.subheader("4. Export Labels / PDF")
    page_format = st.selectbox("Page size / printer", ["A4", "Letter", "LabelPrinter"], index=2)

    if st.button("Generate Multi-Label PDF"):
        if df_to_use.empty:
            st.error("Cannot generate PDF: No rows selected.")
        else:
            pdf_path = generate_sheet_direct(
                df_to_use, visible_columns, code_column, code_type, highlight_column,
                label_font, label_font_size, label_width, label_height, qr_size,
                barcode_width, barcode_height, row_height_factor, sidebar_factor,
                highlight_padding, show_border, show_column_names, side_highlight,
                qr_left_offset, text_left_offset, column_label_map, page_format, repeat_count
            )
            st.success(f"PDF generated for {len(df_to_use)} unique records ({len(df_to_use)*repeat_count} total labels).")
            st.download_button(
                "Download PDF",
                data=open(pdf_path, "rb"),
                file_name=f"multi_labels_{page_format}.pdf",
                mime="application/pdf"
            )

render_version_footer()
