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

PAGE_W, PAGE_H = 300, 186  # mm
BACKGROUND = colors.HexColor("#EEF1EC")
INK = colors.HexColor("#1F2A22")
MUTED = colors.HexColor("#5C6B60")
ACCENT = colors.HexColor("#3D7A4E")

GWAS = {"UUID": "2023-Macomb-GWAS_p177_r2_Iran5", "Geno": "Iran5", "Plot": "177",
        "Rep": "2", "Exp": "2023-Macomb-GWAS"}
FIELD = {"PlantID": "2026-Macomb_p1_tt8tARV1_d3_r1", "Experiment": "2026-Macomb", "Plot": "p1",
         "Geno": "tt8tARV1", "Treatment": "d3", "Rep": "r1"}
POT = {"PlantID": "NSYNC_1_MN106_NM_DL_TN", "Experiment": "NSYNC", "Plant": "1",
       "Geno": "MN106", "Nitrogen": "NM", "Density": "DL", "Heat": "TN"}
TRAY = {"SampleID": "LEAF-0457", "Tray": "T12", "Genotype": "Col-0", "Harvest": "2026-05-14"}
TUBES = [{"PlantID": f"TaGNE_p{n}_d17", "Plant": f"p{n}", "Day": "d17"} for n in (1, 2, 3)]

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


def label(c, row, x, y, w, h, **design):
    stock(c, x, y, w, h)
    draw_label(c, row, x * mm, y * mm, label_width=w, label_height=h,
               **{**BASE, "visible_columns": list(row)[1:], "code_column": list(row)[0], **design})


def caption(c, x, y, title, detail):
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(x * mm, y * mm, title)
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 7.5)
    c.drawString(x * mm, (y - 4.2) * mm, detail)


def main():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(PAGE_W * mm, PAGE_H * mm))
    c.setFillColor(BACKGROUND)
    c.rect(0, 0, PAGE_W * mm, PAGE_H * mm, stroke=0, fill=1)

    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 17)
    c.drawString(10.5 * mm, 174 * mm, "PlantID Label Designer")
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 9)
    c.drawString(10.5 * mm, 167.5 * mm,
                 "One spreadsheet row per plant becomes a printable label — any size, any fields, "
                 "QR code or barcode, label printer or sheet stock.")

    # Loop-lock wrap tag: blank loop area, main label, detachable tear-off.
    tag_x, tag_y, tag_w, tag_h = 10.3, 127, 279.4, 25.4
    stock(c, tag_x, tag_y, tag_w, tag_h, radius=1.2)
    c.saveState()  # The stock's lock slot, for orientation only.
    c.setStrokeColor(colors.HexColor("#B9C1B6"))
    c.setLineWidth(0.6)
    c.roundRect((tag_x + 9) * mm, (tag_y + 8.7) * mm, 22 * mm, 8 * mm, 4 * mm, stroke=1, fill=0)
    c.restoreState()
    wrap = wrap_config({**WRAP_DEFAULTS, "wrap_enabled_check": True, "wrap_custom_fields_check": True,
                        "wrap_text_columns_multiselect": ["Plot", "Geno", "Rep"],
                        "wrap_qr_size_mm_input": 17.0, "wrap_font_size_input": 8.0},
                       ["Geno", "Plot", "Rep", "Exp"], "UUID")
    draw_label(c, GWAS, tag_x * mm, tag_y * mm, **{
        **BASE, "visible_columns": ["Geno", "Plot", "Rep", "Exp"], "code_column": "UUID",
        "highlight_column": "Plot", "label_width": tag_w, "label_height": tag_h, "qr_size": 19,
        "label_font_size": 8.5, "row_height_factor": 0.95, "col_name_width_ratio": 0.2,
        "wrap_tag": wrap})
    c.saveState()  # Perforation between the main tag and its tear-off.
    c.setStrokeColor(colors.HexColor("#B9C1B6"))
    c.setDash(2, 2)
    tear_x = (tag_x + tag_w - wrap["width"]) * mm
    c.line(tear_x, (tag_y + 1.5) * mm, tear_x, (tag_y + tag_h - 1.5) * mm)
    c.restoreState()
    caption(c, 10.5, 120, "Loop-lock wrap tag with tear-off",
            "11 × 1 in loop-lock strip · blank loop area · tear-off repeats the code and key fields")

    # Three 76 × 38 mm designs.
    for index, (row, design, title, detail) in enumerate((
        (FIELD, dict(highlight_column="Plot", side_highlight=True, sidebar_factor=0.11),
         "Field plot tag", "Side strip and inline highlight · 3 × 1.5 in"),
        (POT, dict(highlight_column="Plant", label_font_size=7.5),
         "Greenhouse pot label", "QR code beside six fields · 3 × 1.5 in"),
        (TRAY, dict(code_type="Barcode", barcode_width=60, barcode_height=12,
                    barcode_text_position="Above and below barcode",
                    barcode_above_columns=["Tray"], label_font_size=7, padding=2,
                    qr_left_offset=8, highlight_column="Tray"),
         "Sample tray label", "Code 128 barcode with fields above and below · 3 × 1.5 in"),
    )):
        x = 10.3 + index * 96.7
        label(c, row, x, 68, 76.2, 38.1, **design)
        caption(c, x, 61, title, detail)

    # Cryovial / microtube labels.
    for index, row in enumerate(TUBES):
        label(c, row, 10.3 + index * 29, 36, 25, 12, qr_size=10, padding=1.2, qr_left_offset=1,
              label_font_size=5.5, row_height_factor=1.1, col_name_width_ratio=0.4)
    caption(c, 10.5, 26, "Cryovial and tube labels", "25 × 12 mm · QR code with plant and day")

    # Wristband label printer stock.
    label(c, {"PlantID": "TaGNE_p34_ISU89_tTraceN_r2_d17", "Geno": "ISU89", "Treatment": "tTraceN",
              "Rep": "r2"}, 107, 33, 182.7, 19, qr_size=15, padding=2, qr_left_offset=3,
          label_font_size=7, row_height_factor=1.0, col_name_width_ratio=0.12, highlight_column="Geno")
    caption(c, 107, 26, "Wristband and stake labels",
            "Long narrow stock for label printers · 100+ presets for Zebra, Brother, Avery and more")

    c.setFillColor(MUTED)
    c.setFont("Helvetica-Oblique", 7)
    c.drawRightString((PAGE_W - 10.5) * mm, 8 * mm,
                      "All labels above were drawn by PlantID Label Designer from example data.")
    c.save()

    page = pdfium.PdfDocument(buffer.getvalue())[0]
    page.render(scale=3).to_pil().save(OUTPUT, optimize=True)
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
