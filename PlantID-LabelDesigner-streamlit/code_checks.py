"""Checks that every label's QR code or barcode will print and scan.

Each check covers all rows being printed, so a layout that works for the
preview row but not for a longer value elsewhere in the sheet is caught
before anything is printed.
"""
from functools import lru_cache

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.graphics.barcode import qr
from reportlab.pdfbase.pdfmetrics import stringWidth

from barcodes import symbol_modules

# Level M recovers from about 15% damage, for tags handled in greenhouses and fields.
QR_ERROR_CORRECTION = 'M'
# Below this, like a barcode's narrowest bar, scanners cannot read the code.
MIN_QR_MODULE_MM = 0.25
# Phone cameras and 203 dpi printers are only reliable with about three dots.
GOOD_QR_MODULE_MM = 0.35


@lru_cache(maxsize=100_000)
def qr_modules(value):
    """Width of a value's QR code in squares, including its blank border."""
    widget = qr.QrCodeWidget(value, barLevel=QR_ERROR_CORRECTION)
    widget.qr.make()
    return widget.qr.getModuleCount() + 2 * widget.barBorder


def _labels(count, total):
    return "every label" if count == total else f"{count} of {total} labels"


def _rows(row_numbers):
    shown = ", ".join(str(row) for row in row_numbers[:5])
    return f"row {shown}" if len(row_numbers) == 1 else f"rows {shown}" + (", …" if len(row_numbers) > 5 else "")


def code_problems(values, row_numbers, code_type, width_mm, height_mm,
                  qr_size=0, bar_mm=None, column="code", name=None):
    """(problems, cautions) for the codes on every label. Problems stop some
    codes printing or scanning: blank values, characters a barcode cannot hold,
    and codes too large for the space or too small to scan. Cautions are codes
    that may scan poorly. Each message names the worst value."""
    name = name or ("QR code" if code_type == "QR" else "barcode")
    values = [str(value) for value in values]
    total = len(values)
    if not total:
        return [], []
    problems, cautions = [], []

    blank = [row for value, row in zip(values, row_numbers) if not value.strip()]
    if blank:
        problems.append(f"{_labels(len(blank), total).capitalize()} have no {column} value, so their {name} "
                        f"would be empty ({_rows(blank)}). Fill in the values or untick those rows.")

    if code_type == "Barcode":
        unencodable = [(value, row) for value, row in zip(values, row_numbers)
                       if any(ord(char) > 127 for char in value)]
        if unencodable:
            value, row = unencodable[0]
            char = next(char for char in value if ord(char) > 127)
            problems.append(f"{_labels(len(unencodable), total).capitalize()} have characters a barcode cannot "
                            f"hold, such as “{char}” in “{value}” (row {row}). Use a QR code, which can hold "
                            f"any text, or change the values.")
        widths = [(symbol_modules(value) * bar_mm, value, row) for value, row in zip(values, row_numbers)]
        too_wide = [entry for entry in widths if entry[0] > width_mm + 1e-9]
        if too_wide:
            width, value, row = max(too_wide)
            problems.append(f"The {name} is too long to fit on {_labels(len(too_wide), total)}. The longest "
                            f"value, “{value}” (row {row}), needs {width:.1f} mm to scan reliably, but only "
                            f"{width_mm:.1f} mm fits. Use a wider label, a QR code, or shorter code values.")
    elif code_type == "QR":
        room = min(width_mm, height_mm)
        if qr_size > room + 1e-9:
            problems.append(f"The {name} is {qr_size:g} mm but only {room:.1f} mm fits, so it would be cut off. "
                            f"Reduce the QR size or use a larger label.")
        sizes = [(qr_size / qr_modules(value), value, row) for value, row in zip(values, row_numbers)]
        for limit, messages, verdict in ((MIN_QR_MODULE_MM, problems, "too small to scan"),
                                         (GOOD_QR_MODULE_MM, cautions, "small enough that some scanners and "
                                                                       "phone cameras may struggle")):
            small = [entry for entry in sizes if entry[0] < limit]
            if small:
                module_mm, value, row = min(small)
                needed = qr_size * GOOD_QR_MODULE_MM / module_mm
                fix = f"Make it at least {needed:.0f} mm" if needed <= room else "Use a larger label"
                messages.append(f"The {name}'s squares are {verdict} on {_labels(len(small), total)}. The "
                                f"longest value, “{value}” (row {row}), gives {module_mm:.2f} mm squares; "
                                f"{GOOD_QR_MODULE_MM} mm or more is reliable. {fix}, or use shorter code values.")
                break
    return problems, cautions


def draw_code_placeholder(c, x, y, width_pt, height_pt, text):
    """A dashed outline marking where a code that cannot print would go."""
    c.saveState()
    c.setStrokeColor(colors.red)
    c.setFillColor(colors.red)
    c.setLineWidth(0.6)
    c.setDash(2, 2)
    c.rect(x, y, width_pt, height_pt, stroke=1, fill=0)
    size = min(6, height_pt / 2.5)
    while size > 2 and stringWidth(text, "Helvetica", size) > width_pt - 2 * mm:
        size *= 0.9
    c.setFont("Helvetica", size)
    c.drawCentredString(x + width_pt / 2, y + (height_pt - size * 0.7) / 2, text)
    c.restoreState()
