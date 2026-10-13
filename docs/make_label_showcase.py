"""Draw docs/label-showcase.png: a gallery of label types made by PlantID.

Every label is drawn by the app's own renderer from a spreadsheet row, so the
image stays true to what the app produces. Regenerate after rendering changes:

    python docs/make_label_showcase.py
"""
import io
import sys
from pathlib import Path

import pypdfium2 as pdfium
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "PlantID-LabelDesigner-streamlit" / "streamlit_app.py"
OUTPUT = ROOT / "docs" / "label-showcase.png"
ART = ROOT / "docs" / "showcase-art"  # Illustrations from the PlantID paper figure.

# Load the drawing functions without starting the Streamlit interface.
sys.path.insert(0, str(APP.parent))
source = APP.read_text()
namespace = {"__file__": str(APP)}
exec(compile(source[:source.index("# Streamlit UI")], str(APP), "exec"), namespace)
draw_label = namespace["draw_label_on_canvas"]
wrap_config = namespace["wrap_config"]
WRAP_DEFAULTS = namespace["WRAP_DEFAULTS"]

PAGE_W, PAGE_H = 300, 272  # mm
BACKGROUND = colors.HexColor("#EEF1EC")
INK = colors.HexColor("#1F2A22")
MUTED = colors.HexColor("#5C6B60")
ACCENT = colors.HexColor("#3D7A4E")
GRID = colors.HexColor("#C9D1C6")
PANEL = colors.HexColor("#DDE7D9")
ROW_HIGHLIGHT = colors.HexColor("#E8F2E4")

# One plant drives every label; the tubes add its neighbours in the experiment.
PLANT = {"PlantID": "2026-Exp1_p301_B73-WW", "Experiment": "2026-Exp1", "Plot": "p301",
         "Geno": "B73", "Treatment": "WW"}
TUBES = [{**PLANT, "PlantID": f"2026-Exp1_{plot}_{geno}-WW", "Plot": plot, "Geno": geno}
         for plot, geno in (("p301", "B73"), ("p302", "Mo17"), ("p303", "W22"))]

BASE = dict(code_type="QR", highlight_column=None, label_font="Helvetica", label_font_size=7,
            qr_size=18, barcode_width=25, barcode_height=10, row_height_factor=0.9,
            sidebar_factor=0.1, highlight_padding=4, padding=3, show_border=False,
            show_column_names=True, side_highlight=False, qr_left_offset=3, text_left_offset=0,
            column_label_map={}, highlight_color=colors.black, col_name_width_ratio=0.38,
            code_position="Left", barcode_text_position="Beside barcode",
            barcode_above_columns=[], wrap_tag=None)


def stock(c, x, y, w, h, radius=2.2):
    """White label stock with a soft shadow, behind a drawn label (mm)."""
    c.saveState()
    c.setFillColor(colors.black)
    c.setFillAlpha(0.08)
    c.roundRect((x + 0.6) * mm, (y - 0.8) * mm, w * mm, h * mm, radius * mm, stroke=0, fill=1)
    c.setFillAlpha(1)
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor("#D5DAD3"))
    c.setLineWidth(0.4)
    c.roundRect(x * mm, y * mm, w * mm, h * mm, radius * mm, stroke=1, fill=1)
    c.restoreState()


def label(c, row, x, y, w, h, fields, **design):
    stock(c, x, y, w, h)
    draw_label(c, row, x * mm, y * mm, label_width=w, label_height=h,
               **{**BASE, "visible_columns": fields, "code_column": "PlantID", **design})


def caption(c, x, y, title, detail):
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(x * mm, y * mm, title)
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 7.5)
    c.drawString(x * mm, (y - 4.2) * mm, detail)


def section_heading(c, x, y, text):
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(x * mm, y * mm, text.upper())


def spreadsheet(c, x, top, rows, widths, gutter=7):
    """The example data as it appears in a spreadsheet: a header, the example row,
    and a torn edge below the next rows to show the sheet carries on."""
    header_h, row_h, stub_h = 6, 7.5, 4
    total = gutter + sum(widths)
    bottom = top - header_h - row_h * len(rows) - stub_h
    c.saveState()
    c.setLineWidth(0.5)
    c.setStrokeColor(GRID)
    c.setFillColor(colors.white)
    c.rect(x * mm, bottom * mm, total * mm, (top - bottom) * mm, stroke=1, fill=1)
    c.setFillColor(colors.HexColor("#E3E9E1"))
    c.rect(x * mm, (top - header_h) * mm, total * mm, header_h * mm, stroke=1, fill=1)
    c.setFillColor(ROW_HIGHLIGHT)
    c.rect(x * mm, (top - header_h - row_h) * mm, total * mm, row_h * mm, stroke=0, fill=1)
    for index in range(1, len(rows) + 1):
        y = top - header_h - row_h * index
        c.line(x * mm, y * mm, (x + total) * mm, y * mm)
    left = x + gutter
    for column, width in zip(rows[0], widths):
        c.line(left * mm, bottom * mm, left * mm, top * mm)
        c.setFillColor(MUTED)
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString((left + 2) * mm, (top - 4.2) * mm, column)
        for index, row in enumerate(rows):
            baseline = top - header_h - row_h * index - 5.2
            c.setFillColor(INK if index == 0 else MUTED)
            c.setFillAlpha(1 if index == 0 else 0.8 - 0.3 * (index - 1))
            c.setFont("Helvetica-Bold" if column == "PlantID" and index == 0 else "Helvetica", 9)
            c.drawString((left + 2) * mm, baseline * mm, row[column])
            c.setFillAlpha(1)
        left += width
    c.setFont("Helvetica", 7.5)
    for index in range(len(rows)):  # Spreadsheet row numbers.
        c.setFillColor(ACCENT if index == 0 else MUTED)
        c.drawCentredString((x + gutter / 2) * mm, (top - header_h - row_h * index - 5) * mm, str(index + 1))
    c.setStrokeColor(ACCENT)
    c.setLineWidth(0.9)
    c.rect(x * mm, (top - header_h - row_h) * mm, total * mm, row_h * mm, stroke=1, fill=0)

    # Tear the sheet off just below the last row.
    teeth, depth = 36, 1.4
    edge = bottom + 1.2
    step = total / teeth
    path = c.beginPath()
    path.moveTo((x - 1) * mm, (bottom - 2) * mm)
    path.lineTo((x - 1) * mm, edge * mm)
    for tooth in range(teeth + 1):
        path.lineTo((x + tooth * step) * mm, (edge + (depth if tooth % 2 else 0)) * mm)
    path.lineTo((x + total + 1) * mm, (bottom - 2) * mm)
    path.close()
    c.setFillColor(PANEL)
    c.drawPath(path, stroke=0, fill=1)
    path = c.beginPath()
    path.moveTo(x * mm, edge * mm)
    for tooth in range(1, teeth + 1):
        path.lineTo((x + tooth * step) * mm, (edge + (depth if tooth % 2 else 0)) * mm)
    c.setStrokeColor(GRID)
    c.setLineWidth(0.5)
    c.drawPath(path, stroke=1, fill=0)
    c.restoreState()


def illustration(c, name, center_x, base_y, height, title):
    """One of the paper's drawings of a label in use, with a caption below (mm)."""
    image = ImageReader(str(ART / f"{name}.png"))
    w, h = image.getSize()
    width = height * w / h
    c.drawImage(image, (center_x - width / 2) * mm, base_y * mm, width * mm, height * mm, mask="auto")
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(center_x * mm, (base_y - 5) * mm, title)


def main():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(PAGE_W * mm, PAGE_H * mm))
    c.setFillColor(BACKGROUND)
    c.rect(0, 0, PAGE_W * mm, PAGE_H * mm, stroke=0, fill=1)

    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 17)
    c.drawString(10.5 * mm, 259 * mm, "PlantID Label Designer")
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 9)
    c.drawString(10.5 * mm, 252.5 * mm,
                 "One spreadsheet row per plant becomes a printable label — any size, any fields, "
                 "QR code or barcode, label printer or sheet stock.")

    # The example spreadsheet sits in its own panel, apart from the labels drawn from it.
    c.setFillColor(PANEL)
    c.roundRect(10.3 * mm, 199 * mm, (PAGE_W - 20.6) * mm, 45 * mm, 3 * mm, stroke=0, fill=1)
    section_heading(c, 15, 238.5, "Example spreadsheet · one row per plant")
    # The pot and bag labels call this column "Plant" and the others "Plot", so the header shows both.
    rows = [{("Plant/Plot" if column == "Plot" else column): value for column, value in row.items()}
            for row in TUBES]
    spreadsheet(c, 15, 234, rows, [62, 34, 22, 22, 26])
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(196 * mm, 222.6 * mm, "Row 1 → the labels below")
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 7.5)
    c.drawString(196 * mm, 217.6 * mm, "Every other row prints its own set,")
    c.drawString(196 * mm, 213.6 * mm, "one label per plant or sample.")

    # A connector from the spreadsheet down to the labels.
    c.saveState()
    c.setStrokeColor(ACCENT)
    c.setFillColor(ACCENT)
    c.setLineWidth(1.2)
    c.line(25 * mm, 199 * mm, 25 * mm, 190.5 * mm)
    arrow = c.beginPath()
    arrow.moveTo(22.6 * mm, 191.2 * mm)
    arrow.lineTo(27.4 * mm, 191.2 * mm)
    arrow.lineTo(25 * mm, 187.6 * mm)
    arrow.close()
    c.drawPath(arrow, stroke=0, fill=1)
    c.restoreState()
    section_heading(c, 31, 188.4, "Labels printed from row 1")

    # Loop-lock wrap tag: blank loop area, main label, detachable tear-off.
    tag_x, tag_y, tag_w, tag_h = 10.3, 154, 279.4, 25.4
    stock(c, tag_x, tag_y, tag_w, tag_h, radius=1.2)
    c.saveState()  # The stock's lock slot, for orientation only.
    c.setStrokeColor(colors.HexColor("#B9C1B6"))
    c.setLineWidth(0.6)
    c.roundRect((tag_x + 9) * mm, (tag_y + 8.7) * mm, 22 * mm, 8 * mm, 4 * mm, stroke=1, fill=0)
    c.restoreState()
    wrap = wrap_config({**WRAP_DEFAULTS, "wrap_enabled_check": True, "wrap_custom_fields_check": True,
                        "wrap_text_columns_multiselect": ["Plot", "Geno", "Treatment"],
                        "wrap_qr_size_mm_input": 17.0, "wrap_font_size_input": 8.0},
                       ["Experiment", "Plot", "Geno", "Treatment"], "PlantID")
    draw_label(c, PLANT, tag_x * mm, tag_y * mm, **{
        **BASE, "visible_columns": ["Experiment", "Plot", "Geno", "Treatment"], "code_column": "PlantID",
        "highlight_column": "Plot", "label_width": tag_w, "label_height": tag_h, "qr_size": 19,
        "padding": 3.5, "label_font_size": 8.5, "row_height_factor": 0.95, "col_name_width_ratio": 0.2,
        "wrap_tag": wrap})
    c.saveState()  # Perforation between the main tag and its tear-off.
    c.setStrokeColor(colors.HexColor("#B9C1B6"))
    c.setDash(2, 2)
    tear_x = (tag_x + tag_w - wrap["width"]) * mm
    c.line(tear_x, (tag_y + 1.5) * mm, tear_x, (tag_y + tag_h - 1.5) * mm)
    c.restoreState()
    caption(c, 10.5, 147, "Loop-lock wrap tag with tear-off",
            "11 × 1 in loop-lock strip · blank loop area · tear-off repeats the code and key fields")

    # Greenhouse pot label: a large QR code beside four evenly spaced fields.
    # Pot and bag labels each hold a single plant, so they name the field "Plant" rather than "Plot".
    plant = {**PLANT, "Plant": PLANT["Plot"]}
    label(c, plant, 10.3, 92, 76.2, 38.1, ["Experiment", "Plant", "Geno", "Treatment"],
          qr_size=28, qr_left_offset=4, padding=4.5, label_font_size=9, row_height_factor=0.98,
          col_name_width_ratio=0.43, highlight_column="Plant")
    caption(c, 10.5, 84, "Greenhouse pot label", "QR code beside four fields · 3 × 1.5 in")

    # Sample bag label: barcode with the plant above and the rest below.
    label(c, plant, 99, 92, 101.6, 38.1, ["Plant", "Geno", "Treatment"], code_type="Barcode",
          barcode_width=82, barcode_height=12, barcode_text_position="Above and below barcode",
          barcode_above_columns=["Plant"], label_font_size=8, padding=2, qr_left_offset=9.8,
          highlight_column="Plant", col_name_width_ratio=0.45)
    caption(c, 99, 84, "Sample bag label", "Code 128 barcode with fields above and below · 4 × 1.5 in")

    # Cryovial / microtube labels: each tube shows a different choice of fields.
    tube_designs = (
        dict(fields=["Plot", "Geno"], highlight_column="Plot"),
        dict(fields=["Geno", "Treatment"], code_position="Right"),
        dict(fields=["Plot", "Treatment"], highlight_column="Treatment"),
    )
    for index, (row, design) in enumerate(zip(TUBES, tube_designs)):
        label(c, row, 213, 120 - index * 14, 25, 12, design.pop("fields"), qr_size=10, padding=2.6,
              qr_left_offset=1, label_font_size=7, row_height_factor=0.95, show_column_names=False,
              highlight_padding=3, **design)
    caption(c, 213, 84, "Cryovial and tube labels", "25 × 12 mm · choose the fields per design")

    # The same labels in use.
    c.setStrokeColor(GRID)
    c.setLineWidth(0.5)
    c.line(10.3 * mm, 72 * mm, (PAGE_W - 10.3) * mm, 72 * mm)
    section_heading(c, 10.5, 67, "In use")
    illustration(c, "pot", 48, 18, 44, "On a pot")
    illustration(c, "container", 150, 18, 34, "On a sample container")
    illustration(c, "plant", 251, 18, 52, "Wrapped around a stem")

    c.setFillColor(MUTED)
    c.setFont("Helvetica-Oblique", 7)
    c.drawRightString((PAGE_W - 10.5) * mm, 5 * mm,
                      "Labels drawn by PlantID Label Designer from row 1 · in-use illustrations from the PlantID paper.")
    c.save()

    page = pdfium.PdfDocument(buffer.getvalue())[0]
    page.render(scale=3).to_pil().save(OUTPUT, optimize=True)
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
