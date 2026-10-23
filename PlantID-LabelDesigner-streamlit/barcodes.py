"""Code 128 barcodes sized in whole printer dots.

Printers can only print whole dots, so a bar 1.5 dots wide prints as a mix of
1- and 2-dot bars that scanners cannot decode. Bars are therefore the fewest
whole dots that scanners read reliably, and each barcode's width follows from
its value.
Printer drivers also darken every dot a bar touches, so bars start on the
printer's dot grid and are inset slightly to stay clear of neighbouring dots.
"""
from functools import lru_cache

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.graphics.barcode import code128

PRINTER_DPI_OPTIONS = [203, 300, 600]
DEFAULT_PRINTER_DPI = 203
# The Code 128 standard's minimum quiet zone, in narrow bar widths.
QUIET_ZONE_MODULES = 10
# Two dots on a 203 dpi thermal printer; narrower bars scan unreliably.
MIN_BARCODE_BAR_MM = 0.25
# Under a tenth of a dot at 203 dpi; keeps each bar edge inside its own dots.
BAR_INSET_MM = 0.01


class _InsetCode128(code128.Code128):
    inset = 0

    def rect(self, x, y, w, h):
        self.canv.rect(x + self.inset, y, w - 2 * self.inset, h, stroke=0, fill=1)


def bar_width_mm(dots, dpi):
    return dots * 25.4 / dpi


def reliable_bar_mm(dpi):
    """Narrowest whole-dot bar at least MIN_BARCODE_BAR_MM wide: 2 dots at 203 dpi,
    3 at 300 dpi and 6 at 600 dpi."""
    dots = 1
    while bar_width_mm(dots, dpi) < MIN_BARCODE_BAR_MM - 0.005:
        dots += 1
    return bar_width_mm(dots, dpi)


@lru_cache(maxsize=100_000)
def symbol_modules(value):
    """Width of a value's barcode in narrow bar widths, including quiet zones."""
    symbol = code128.Code128(str(value), barWidth=1, quiet=False, humanReadable=False)
    return symbol.width + 2 * QUIET_ZONE_MODULES


def barcode_width_mm(values, bar_mm):
    """Width the widest value's barcode needs, or 0 when there are no values."""
    return max((symbol_modules(value) for value in {str(value) for value in values}), default=0) * bar_mm


def draw_code128(c, value, x, y, width_pt, height_pt, bar_mm=None, align="Left"):
    """Draw a barcode in the box at (x, y). With bar_mm the bars keep that width
    and the barcode is aligned in the box; without it the barcode fills the box."""
    value = str(value)
    if bar_mm is None:
        bar_pt = width_pt / symbol_modules(value)
    else:
        bar_pt = bar_mm * mm
    quiet = QUIET_ZONE_MODULES * bar_pt
    symbol = _InsetCode128(value, barWidth=bar_pt, barHeight=height_pt, humanReadable=False,
                           lquiet=quiet, rquiet=quiet)
    if align == "Right":
        x += width_pt - symbol.width
    elif align == "Center":
        x += (width_pt - symbol.width) / 2
    if bar_mm is not None:
        # A bar is whole dots, so a multiple of it is on the page's dot grid.
        x = round(x / bar_pt) * bar_pt
        symbol.inset = BAR_INSET_MM * mm
    c.saveState()
    c.setFillColor(colors.black)  # Bars use the current fill colour.
    symbol.drawOn(c, x, y)
    c.restoreState()
