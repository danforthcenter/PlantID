"""Geometry and rendering for the detachable end of a wrap tag (millimetres)."""
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.graphics.barcode import qr, code128
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.utils import simpleSplit

WRAP_DEFAULTS = {
    'wrap_enabled_check': False,
    'wrap_leader_mm_input': 101.6,
    'wrap_tear_width_mm_input': 57.15,
    'wrap_code_type_select': 'QR',
    'wrap_code_column_select': None,
    'wrap_text_columns_multiselect': None,
    'wrap_custom_fields_check': False,
    'wrap_use_main_code_check': True,
    'wrap_qr_size_mm_input': 16.0,
    'wrap_barcode_width_mm_input': 30.0,
    'wrap_barcode_height_mm_input': 12.0,
    'wrap_code_position_select': 'Left',
    'wrap_padding_mm_input': 2.0,
    'wrap_font_size_input': 7.0,
    'wrap_show_names_check': True,
}


def wrap_config(state, main_columns=None, main_code_column=None):
    columns = state.get('wrap_text_columns_multiselect') or []
    if not state.get('wrap_custom_fields_check', False) and main_columns is not None:
        columns = list(main_columns)
    code_column = state.get('wrap_code_column_select')
    if state.get('wrap_use_main_code_check', True) and main_code_column is not None:
        code_column = main_code_column
    return {
        'enabled': state.get('wrap_enabled_check', False),
        'leader': state.get('wrap_leader_mm_input', 101.6),
        'width': state.get('wrap_tear_width_mm_input', 57.15),
        'code_type': state.get('wrap_code_type_select', 'QR'),
        'code_column': code_column,
        'columns': columns,
        'qr_size': state.get('wrap_qr_size_mm_input', 16.0),
        'barcode_width': state.get('wrap_barcode_width_mm_input', 30.0),
        'barcode_height': state.get('wrap_barcode_height_mm_input', 12.0),
        'position': state.get('wrap_code_position_select', 'Left'),
        'padding': state.get('wrap_padding_mm_input', 2.0),
        'font_size': state.get('wrap_font_size_input', 7.0),
        'show_names': state.get('wrap_show_names_check', True),
    }


def wrap_layout_error(config, label_width, label_height):
    if not config or not config['enabled']:
        return None
    if config['width'] <= 0 or config['leader'] < 0 or config['leader'] + config['width'] >= label_width:
        return 'The blank loop area and tear-off width must leave room for the main label.'
    width = config['width'] - 2 * config['padding']
    height = label_height - 2 * config['padding']
    if min(width, height) <= 0:
        return 'Reduce the tear-off padding to leave a printable area.'
    if config['code_type'] != 'None':
        if not config['code_column']:
            return 'Choose a data column for the tear-off code.'
        code_w = config['qr_size'] if config['code_type'] == 'QR' else config['barcode_width']
        code_h = config['qr_size'] if config['code_type'] == 'QR' else config['barcode_height']
        if min(code_w, code_h) <= 0 or code_h > height or code_w > width:
            return 'The tear-off code does not fit. Reduce its size or padding, or increase the section width.'
        if config['columns'] and width - code_w - 2 < 8:
            return 'Leave at least 8 mm beside the tear-off code for identifier text.'
    return None


def clip_region(c, x, y, width, height):
    path = c.beginPath()
    path.rect(x, y, width * mm, height * mm)
    c.clipPath(path, stroke=0, fill=0)


def draw_tear_off(c, row, x, y, height, config, font='Helvetica', labels=None, border=False):
    """Draw within the tear-off only; dimensions include barcode quiet zones."""
    width = config['width']
    padding = config['padding'] * mm
    c.saveState()
    clip_region(c, x, y, width, height)
    if border:
        c.setStrokeColor(colors.lightgrey)
        c.setLineWidth(0.5)
        c.rect(x, y, width * mm, height * mm, stroke=1, fill=0)
    left, right = x + padding, x + width * mm - padding
    if config['code_type'] != 'None':
        value = str(row[config['code_column']])
        is_qr = config['code_type'] == 'QR'
        code_w = (config['qr_size'] if is_qr else config['barcode_width']) * mm
        code_h = (config['qr_size'] if is_qr else config['barcode_height']) * mm
        code_x = left if config['position'] == 'Left' else right - code_w
        code_y = y + (height * mm - code_h) / 2
        if is_qr:
            obj = qr.QrCodeWidget(value)
            bounds = obj.getBounds()
            scale = code_w / (bounds[2] - bounds[0])
            drawing = Drawing(code_w, code_h, transform=[scale, 0, 0, scale, 0, 0])
            drawing.add(obj)
            renderPDF.draw(drawing, c, code_x, code_y)
        else:
            obj = code128.Code128(value, barHeight=code_h, humanReadable=False)
            c.saveState()
            c.translate(code_x, code_y)
            c.scale(code_w / obj.width, 1)
            obj.drawOn(c, 0, 0)
            c.restoreState()
        if config['position'] == 'Left':
            left += code_w + 2 * mm
        else:
            right -= code_w + 2 * mm
    labels = labels or {}
    texts = [(f'{labels.get(col, col)}: ' if config['show_names'] else '') + str(row[col])
             for col in config['columns']]
    if texts:
        available_w, available_h = right - left, height * mm - 2 * padding
        size = config['font_size']
        # Fit identifiers as a block, including long unbroken sample IDs.
        for _ in range(100):
            lines = [line for text in texts for line in (simpleSplit(text, font, size, available_w) or [''])]
            widest = max((stringWidth(line, font, size) for line in lines), default=0)
            if widest <= available_w and len(lines) * size * 1.2 <= available_h:
                break
            size *= 0.95
        c.setFont(font, size)
        c.setFillColor(colors.black)
        baseline = y + (height * mm + len(lines) * size * 1.2) / 2 - size
        for line in lines:
            c.drawString(left, baseline, line)
            baseline -= size * 1.2
    c.restoreState()
