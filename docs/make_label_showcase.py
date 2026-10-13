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
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "PlantID-LabelDesigner-streamlit" / "streamlit_app.py"
OUTPUT = ROOT / "docs" / "label-showcase.png"

# Load the drawing functions without starting the Streamlit interface.
sys.path.insert(0, str(APP.parent))
source = APP.read_text()
namespace = {"__file__": str(APP)}
exec(compile(source[:source.index("# Streamlit UI")], str(APP), "exec"), namespace)
draw_label = namespace["draw_label_on_canvas"]
wrap_config = namespace["wrap_config"]
WRAP_DEFAULTS = namespace["WRAP_DEFAULTS"]

PAGE_W, PAGE_H = 300, 170  # mm
BACKGROUND = colors.HexColor("#EEF1EC")
INK = colors.HexColor("#1F2A22")
MUTED = colors.HexColor("#5C6B60")
ACCENT = colors.HexColor("#3D7A4E")
GRID = colors.HexColor("#C9D1C6")

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


def spreadsheet_row(c, x, top, row, widths):
    """The example data as it appears in a spreadsheet: a header and one row."""
    header_h, row_h = 6, 7.5
    total = sum(widths)
    c.saveState()
    c.setFillColor(colors.white)
    c.setStrokeColor(GRID)
    c.setLineWidth(0.5)
    c.rect(x * mm, (top - header_h - row_h) * mm, total * mm, (header_h + row_h) * mm, stroke=1, fill=1)
    c.setFillColor(colors.HexColor("#E3E9E1"))
    c.rect(x * mm, (top - header_h) * mm, total * mm, header_h * mm, stroke=1, fill=1)
    left = x
    for (column, value), width in zip(row.items(), widths):
        if left > x:
            c.line(left * mm, (top - header_h - row_h) * mm, left * mm, top * mm)
        c.setFillColor(MUTED)
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString((left + 2) * mm, (top - 4.2) * mm, column)
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold" if column == "PlantID" else "Helvetica", 9)
        c.drawString((left + 2) * mm, (top - header_h - 5.2) * mm, value)
        left += width
    c.restoreState()


def main():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(PAGE_W * mm, PAGE_H * mm))
    c.setFillColor(BACKGROUND)
    c.rect(0, 0, PAGE_W * mm, PAGE_H * mm, stroke=0, fill=1)

    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 17)
    c.drawString(10.5 * mm, 157 * mm, "PlantID Label Designer")
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 9)
    c.drawString(10.5 * mm, 150.5 * mm,
                 "One spreadsheet row per plant becomes a printable label — any size, any fields, "
                 "QR code or barcode, label printer or sheet stock.")

    # The pot and bag labels call this column "Plant" and the others "Plot", so the header shows both.
    header = {("Plant/Plot" if column == "Plot" else column): value for column, value in PLANT.items()}
    spreadsheet_row(c, 10.3, 143, header, [62, 34, 22, 22, 26])
    c.setFillColor(MUTED)
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(181 * mm, 133.2 * mm, "→  this row, as each label below")

    # Loop-lock wrap tag: blank loop area, main label, detachable tear-off.
    tag_x, tag_y, tag_w, tag_h = 10.3, 93, 279.4, 25.4
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
    caption(c, 10.5, 86, "Loop-lock wrap tag with tear-off",
            "11 × 1 in loop-lock strip · blank loop area · tear-off repeats the code and key fields")

    # Greenhouse pot label: a large QR code beside four evenly spaced fields.
    # Pot and bag labels each hold a single plant, so they name the field "Plant" rather than "Plot".
    plant = {**PLANT, "Plant": PLANT["Plot"]}
    label(c, plant, 10.3, 32, 76.2, 38.1, ["Experiment", "Plant", "Geno", "Treatment"],
          qr_size=28, qr_left_offset=4, padding=4.5, label_font_size=9, row_height_factor=0.98,
          col_name_width_ratio=0.43, highlight_column="Plant")
    caption(c, 10.5, 24, "Greenhouse pot label", "QR code beside four fields · 3 × 1.5 in")

    # Sample bag label: barcode with the plant above and the rest below.
    label(c, plant, 99, 32, 101.6, 38.1, ["Plant", "Geno", "Treatment"], code_type="Barcode",
          barcode_width=82, barcode_height=12, barcode_text_position="Above and below barcode",
          barcode_above_columns=["Plant"], label_font_size=8, padding=2, qr_left_offset=9.8,
          highlight_column="Plant", col_name_width_ratio=0.45)
    caption(c, 99, 24, "Sample bag label", "Code 128 barcode with fields above and below · 4 × 1.5 in")

    # Cryovial / microtube labels: each tube shows a different choice of fields.
    tube_designs = (
        dict(fields=["Plot", "Geno"], highlight_column="Plot"),
        dict(fields=["Geno", "Treatment"], code_position="Right"),
        dict(fields=["Plot", "Treatment"], highlight_column="Treatment"),
    )
    for index, (row, design) in enumerate(zip(TUBES, tube_designs)):
        label(c, row, 213, 60 - index * 14, 25, 12, design.pop("fields"), qr_size=10, padding=2.6,
              qr_left_offset=1, label_font_size=7, row_height_factor=0.95, show_column_names=False,
              highlight_padding=3, **design)
    caption(c, 213, 24, "Cryovial and tube labels", "25 × 12 mm · choose the fields per design")

    c.setFillColor(MUTED)
    c.setFont("Helvetica-Oblique", 7)
    c.drawRightString((PAGE_W - 10.5) * mm, 8 * mm,
                      "All labels above were drawn by PlantID Label Designer from the example row.")
    c.save()

    page = pdfium.PdfDocument(buffer.getvalue())[0]
    page.render(scale=3).to_pil().save(OUTPUT, optimize=True)
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
