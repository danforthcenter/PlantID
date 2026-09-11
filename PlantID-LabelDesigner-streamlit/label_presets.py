"""Label size and sheet stock presets for PlantID Label Designer."""

import re
from fractions import Fraction

UNIT_MM = "Metric (mm)"
UNIT_INCH_FRACTIONAL = "Imperial (inches)"
UNIT_INCH_DECIMAL = "Imperial (inch decimal)"
INCH_TO_MM = 25.4

CUSTOM_SHEET_PRESET = "Custom sheet spacing"


def make_sheet_stock_preset(
    name,
    label_width_in,
    label_height_in,
    columns,
    rows,
    top_margin_in,
    side_margin_in,
    horizontal_pitch_in,
    vertical_pitch_in,
    page_format="Letter",
):
    if page_format == "A4":
        page_width_in, page_height_in = 210 / INCH_TO_MM, 297 / INCH_TO_MM
    elif page_format == "A4 Landscape":
        page_width_in, page_height_in = 297 / INCH_TO_MM, 210 / INCH_TO_MM
    elif page_format == "Letter Landscape":
        page_width_in, page_height_in = 11.0, 8.5
    else:
        page_width_in, page_height_in = 8.5, 11.0

    occupied_width_in = label_width_in + (columns - 1) * horizontal_pitch_in
    occupied_height_in = label_height_in + (rows - 1) * vertical_pitch_in
    right_margin_in = max(0, page_width_in - side_margin_in - occupied_width_in)
    bottom_margin_in = max(0, page_height_in - top_margin_in - occupied_height_in)

    return {
        "name": name,
        "page_format": page_format,
        "label_width_mm": label_width_in * INCH_TO_MM,
        "label_height_mm": label_height_in * INCH_TO_MM,
        "columns": columns,
        "rows": rows,
        "margin_top_mm": top_margin_in * INCH_TO_MM,
        "margin_right_mm": right_margin_in * INCH_TO_MM,
        "margin_bottom_mm": bottom_margin_in * INCH_TO_MM,
        "margin_left_mm": side_margin_in * INCH_TO_MM,
        "gap_horizontal_mm": max(0, horizontal_pitch_in - label_width_in) * INCH_TO_MM,
        "gap_vertical_mm": max(0, vertical_pitch_in - label_height_in) * INCH_TO_MM,
    }


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
    ("PR1MA 119 Tag", 24, 13, 24.01, 13.00, "PR1MA 119 Tag Sheet (7 x 17)"),
    ("PR1MA 85 Tag", 33, 13, 33.00, 13.00, "PR1MA 85 Tag Sheet (5 x 17)"),
    ("PR1MA 52 Tag", 43, 19, 42.93, 19.05, "PR1MA 52 Tag Sheet (4 x 13)"),
    ("PR1MA 30 Tag", 67, 25, 66.67, 25.40, "PR1MA 30 Tag Sheet (3 x 10)"),
    ("PR1MA 12 Tag", 73, 22, 73.15, 22.18, "PR1MA 12 Tag Sheet (2 x 12)"),
    ("PR1MA 192 Half-In Dot", 13, 13, 13.00, 13.00, "PR1MA 192 Half-In Dot Sheet (12 x 16)"),
    (
        "USA Scientific 9187/9125/9145 1.28 x 0.50 in",
        33,
        13,
        1.28 * INCH_TO_MM,
        0.50 * INCH_TO_MM,
        "USA Scientific 1.28 x 0.50 in Laser Sheet (5 x 17)",
    ),
    (
        "USA Scientific 9185/9125/9145 0.94 x 0.50 in",
        24,
        13,
        0.94 * INCH_TO_MM,
        0.50 * INCH_TO_MM,
        "USA Scientific 0.94 x 0.50 in Laser Sheet (7 x 17)",
    ),
    (
        "USA Scientific 9147/9115/9187/9145 1.50 x 0.75 in",
        38,
        19,
        1.50 * INCH_TO_MM,
        0.75 * INCH_TO_MM,
        "USA Scientific 1.50 x 0.75 in Laser Sheet (5 x 12)",
    ),
    (
        "USA Scientific 9164/9145 0.875 x 0.875 in",
        22,
        22,
        0.875 * INCH_TO_MM,
        0.875 * INCH_TO_MM,
        "USA Scientific 0.875 x 0.875 in Laser Sheet (8 x 12)",
    ),
    (
        "USA Scientific 9135/9187 2.50 x 0.50 in",
        64,
        13,
        2.50 * INCH_TO_MM,
        0.50 * INCH_TO_MM,
        "USA Scientific 2.50 x 0.50 in Laser Sheet (3 x 20)",
    ),
    (
        "USA Scientific 9186 0.91 x 0.32 in",
        23,
        8,
        0.91 * INCH_TO_MM,
        0.32 * INCH_TO_MM,
        "USA Scientific 0.91 x 0.32 in Laser Sheet (7 x 22)",
    ),
    (
        "USA Scientific 9184/9187 1.00 x 1.00 in",
        25,
        25,
        1.00 * INCH_TO_MM,
        1.00 * INCH_TO_MM,
        "USA Scientific 1.00 x 1.00 in Laser Sheet (8 x 10)",
    ),
    (
        "USA Scientific 9184 1.625 x 0.625 in",
        41,
        16,
        1.625 * INCH_TO_MM,
        0.625 * INCH_TO_MM,
        "USA Scientific 1.625 x 0.625 in Laser Sheet (4 x 16)",
    ),
    (
        "USA Scientific 9188 2.625 x 0.1875 in",
        67,
        5,
        2.625 * INCH_TO_MM,
        0.1875 * INCH_TO_MM,
        "USA Scientific 2.625 x 0.1875 in Laser Sheet (3 x 33)",
    ),
    (
        "USA Scientific 9115 1.50 x 0.50 in",
        38,
        13,
        1.50 * INCH_TO_MM,
        0.50 * INCH_TO_MM,
        "USA Scientific 1.50 x 0.50 in Laser Sheet (5 x 16)",
    ),
    (
        "USA Scientific 9115 1.05 x 0.50 in",
        27,
        13,
        1.05 * INCH_TO_MM,
        0.50 * INCH_TO_MM,
        "USA Scientific 1.05 x 0.50 in Laser Sheet (6 x 16)",
    ),
    (
        "USA Scientific 9187 1.69 x 0.75 in",
        43,
        19,
        1.69 * INCH_TO_MM,
        0.75 * INCH_TO_MM,
        "USA Scientific 1.69 x 0.75 in Laser Sheet (4 x 13)",
    ),
    (
        "USA Scientific 9188 1.50 x 0.25 in",
        38,
        6,
        1.50 * INCH_TO_MM,
        0.25 * INCH_TO_MM,
        "USA Scientific 1.50 x 0.25 in Laser Sheet (4 x 39)",
    ),
    (
        "USA Scientific 9187 2.625 x 1.00 in",
        67,
        25,
        2.625 * INCH_TO_MM,
        1.00 * INCH_TO_MM,
        "USA Scientific 2.625 x 1.00 in Laser Sheet (3 x 10)",
    ),
    (
        "USA Scientific 9187 1.125 x 1.75 in",
        29,
        44,
        1.125 * INCH_TO_MM,
        1.75 * INCH_TO_MM,
        "USA Scientific 1.125 x 1.75 in Laser Sheet (7 x 6)",
    ),
    (
        "USA Scientific 9187 3.00 x 2.00 in",
        76,
        51,
        3.00 * INCH_TO_MM,
        2.00 * INCH_TO_MM,
        "USA Scientific 3.00 x 2.00 in Laser Sheet (3 x 4 Landscape)",
    ),
    (
        "USA Scientific 9185 Tough-Spot 3/8 in",
        10,
        10,
        0.38 * INCH_TO_MM,
        0.38 * INCH_TO_MM,
        "USA Scientific Tough-Spot 3/8 in Sheet (12 x 16)",
    ),
    (
        "USA Scientific 9185 Tough-Spot 1/2 in",
        13,
        13,
        0.50 * INCH_TO_MM,
        0.50 * INCH_TO_MM,
        "USA Scientific Tough-Spot 1/2 in Sheet (12 x 16)",
    ),
    (
        "USA Scientific 9185 Tough-Spot 3/4 in",
        19,
        19,
        0.75 * INCH_TO_MM,
        0.75 * INCH_TO_MM,
        "USA Scientific Tough-Spot 3/4 in Sheet (9 x 12)",
    ),
    (
        "USA Scientific 9185 Tough-Spot 1.00 in",
        25,
        25,
        1.00 * INCH_TO_MM,
        1.00 * INCH_TO_MM,
        "USA Scientific Tough-Spot 1.00 in Sheet (7 x 9)",
    ),
    (
        "USA Scientific 9185 Tough-Spot 7/16 in",
        11,
        11,
        0.44 * INCH_TO_MM,
        0.44 * INCH_TO_MM,
        "USA Scientific Tough-Spot 7/16 in Sheet (13 x 18)",
    ),
    (
        "Fisherbrand Micryo 15-930-A/B 0.5 x 1 in",
        25,
        13,
        1.00 * INCH_TO_MM,
        0.50 * INCH_TO_MM,
        CUSTOM_SHEET_PRESET,
    ),
    (
        "Fisherbrand Micryo 15-930-C/D 0.5 x 1.25 in",
        32,
        13,
        1.25 * INCH_TO_MM,
        0.50 * INCH_TO_MM,
        CUSTOM_SHEET_PRESET,
    ),
    (
        "Fisherbrand Micryo 15-930-F 0.25 x 1.5 in",
        38,
        6,
        1.50 * INCH_TO_MM,
        0.25 * INCH_TO_MM,
        CUSTOM_SHEET_PRESET,
    ),
    (
        "Fisherbrand Micryo 15-930-E 1 x 2.6 in",
        66,
        25,
        2.60 * INCH_TO_MM,
        1.00 * INCH_TO_MM,
        CUSTOM_SHEET_PRESET,
    ),
    (
        "Fisherbrand Micryo 15-940-B 0.375 in Dot",
        10,
        10,
        0.375 * INCH_TO_MM,
        0.375 * INCH_TO_MM,
        CUSTOM_SHEET_PRESET,
    ),
    (
        "Fisherbrand Micryo 15-940-A 0.5 in Dot",
        13,
        13,
        0.50 * INCH_TO_MM,
        0.50 * INCH_TO_MM,
        CUSTOM_SHEET_PRESET,
    ),
    (
        "Fisherbrand Micryo 15-940-C 0.75 in Dot",
        19,
        19,
        0.75 * INCH_TO_MM,
        0.75 * INCH_TO_MM,
        CUSTOM_SHEET_PRESET,
    ),
]


# Zebra ZipShip North America / Latin America catalog, printed page 34 (PDF page 33).
# Dimensions are width × feed length in inches; these presets describe label
# geometry, not printer compatibility, roll cores, or sheet spacing.
ZEBRA_PRESET_SOURCE = "https://www.zebra.com/content/dam/zebra_dam/en/brochure/portfolio/zipship-brochure-catalog-en-us.pdf"
ZEBRA_LABEL_SIZES = [
    (1, 3, "10010036"), (1.2, 0.85, "10010037"),
    (1.25, 1, "10010038"), (2, 1, "10010039"),
    (2.25, 0.5, "10010040"), (2.25, 0.75, "10015340"),
    (2.25, 1.25, "10015341"), (2.25, 2, "10015342"),
    (2.25, 2.5, "10010041"), (2.25, 3, "10010042"),
    (2.25, 4, "10015343"), (3, 1, "10010043"),
    (3, 2, "10010044"), (4, 1, "10010045"),
    (4, 1.25, "10015349"), (4, 1.5, "10010046"),
    (4, 2, "10010047"), (4, 2.5, "10010048"),
    (4, 3, "10015344"), (4, 4, "10015345"),
    (4, 5, "10015346"), (4, 6, "10010049 / 10015347"),
]
LABEL_PRESETS.extend(
    (f"Zebra Z-Select 4000D {part}", width * INCH_TO_MM,
     height * INCH_TO_MM, width * INCH_TO_MM, height * INCH_TO_MM)
    for width, height, part in ZEBRA_LABEL_SIZES
)

# Common manufacturer formats. Variants that use the same template geometry
# are grouped into one preset so the browser stays useful instead of listing
# every color, adhesive, and package-count SKU separately.
MANUFACTURER_PRESET_SOURCES = {
    "Avery": "https://www.avery.com/templates/category/all-label-templates",
    "DYMO": "https://download.dymo.com/UserManuals/labelwriter%20user%20guides/LWSE450_Tech_Ref/Content/AppendixE.htm",
    "Brother": "https://www.brother-usa.com/-/media/brother/product-catalog-media/documents/2022/07/07/14/16/bro8665-1-ql1100ql1110nwbbrochure-collection-052418-v3.pdf",
    "Brady": "https://catalogs.bradyid.com/data/61123flx/011/html/export/M611%20Label%20Printer%20Brochure.pdf",
    "LabTAG": "https://cdn.labtag.com/wp-content/uploads/Catalogue-2024-EN012024-January-08-2024-web.pdf",
}

# name, width, height; dimensions are inches unless the final value is "mm".
COMMON_MANUFACTURER_LABELS = [
    # Avery sheet-label template families
    ("Avery 5167/5267/8167 Return Address", 1.75, 0.5),
    ("Avery 5195/8195 Return Address", 1.75, 2 / 3),
    ("Avery 5160/5260/8160 Address", 2.625, 1),
    ("Avery 5161/5261/8161 Address", 4, 1),
    ("Avery 5162/5262/8162 Address", 4, 4 / 3),
    ("Avery 5163/5263/8163 Shipping", 4, 2),
    ("Avery 5164/5264/8164 Shipping", 4, 10 / 3),
    ("Avery 5168/5268/8168 Shipping", 3.5, 5),
    ("Avery 5165/5265/8165 Full Sheet Shipping", 8.5, 11),
    ("Avery 5366/8366 File Folder", 3 + 7 / 16, 2 / 3),
    ("Avery 22805 Square", 1.5, 1.5),
    ("Avery 22806 Square", 2, 2),
    ("Avery 22807 Round", 2, 2),
    ("Avery 22830 Round", 2.5, 2.5),
    ("Avery 22804 Oval", 2.5, 1.5),
    ("Avery 36460/36461/22822 Rectangle", 3, 2),

    # DYMO LabelWriter die-cut rolls
    ("DYMO LabelWriter 30252/30320 Address", 1.125, 3.5),
    ("DYMO LabelWriter 30327 File Folder", 9 / 16, 3 + 7 / 16),
    ("DYMO LabelWriter 30332 Multipurpose", 1, 1),
    ("DYMO LabelWriter 30333 Multipurpose", 1, 0.5),
    ("DYMO LabelWriter 30334 Multipurpose", 2.25, 1.25),
    ("DYMO LabelWriter 30335 Multipurpose", 0.5, 0.5),
    ("DYMO LabelWriter 30336 Multipurpose", 1, 2.125),
    ("DYMO LabelWriter 30374 Appointment Business Card", 2.5, 3.5),
    ("DYMO LabelWriter 30365 Name Badge", 2.25, 3.5),
    ("DYMO LabelWriter 30364 Visitor Name Badge", 2 + 5 / 16, 4),
    ("DYMO LabelWriter 30323 Shipping", 2.125, 4),
    ("DYMO LabelWriter 30256 Shipping", 2 + 5 / 16, 4),
    ("DYMO LabelWriter 1744907 Shipping", 4, 6),

    # Brother QL DK die-cut rolls; official metric dimensions are retained.
    ("Brother DK-1201 Standard Address", 29, 90.3, "mm"),
    ("Brother DK-1202 Shipping", 62, 100, "mm"),
    ("Brother DK-1203 File Folder", 17, 87.1, "mm"),
    ("Brother DK-1204 Multipurpose Return Address", 17, 54.3, "mm"),
    ("Brother DK-1208 Large Address", 38, 90.3, "mm"),
    ("Brother DK-1209 Small Address", 28.9, 62, "mm"),
    ("Brother DK-1219 Round", 12, 12, "mm"),
    ("Brother DK-1221 Square", 23, 23, "mm"),
    ("Brother DK-1234 Name Badge", 86, 60, "mm"),
    ("Brother DK-1240 Large Multipurpose", 102, 51, "mm"),
    ("Brother DK-1241 Large Shipping", 102, 152, "mm"),
    ("Brother DK-1247 Extra Large Shipping", 103, 164, "mm"),
    ("Brother DK-3235 Small Removable Food Safety", 54, 29, "mm"),

    # Common laboratory formats represented by current manufacturer catalogs.
    ("Brady M6-203-461 Self-Laminating Cryogenic", 1, 1.75),
    ("LabTAG A4CL-23T1 Cryo-LazrTAG PCR Cryovial", 31.5, 13, "mm"),
    ("LabTAG JTTA-225C1 NitroTAG Cryogenic", 1, 0.375),
]

AVERY_SHEET_PRESET_BY_PRODUCT = {
    "Avery 5167/5267/8167 Return Address": "Avery 5167 Return Address (4 × 20)",
    "Avery 5195/8195 Return Address": "Avery 5195 Return Address (4 × 15)",
    "Avery 5160/5260/8160 Address": "Avery 5160 Address (3 × 10)",
    "Avery 5161/5261/8161 Address": "Avery 5161 Address (2 × 10)",
    "Avery 5162/5262/8162 Address": "Avery 5162 Address (2 × 7)",
    "Avery 5163/5263/8163 Shipping": "Avery 5163 Shipping (2 × 5)",
    "Avery 5164/5264/8164 Shipping": "Avery 5164 Shipping (2 × 3)",
    "Avery 5168/5268/8168 Shipping": "Avery 5168 Shipping (2 × 2)",
    "Avery 5165/5265/8165 Full Sheet Shipping": "Avery 5165 Full Sheet (1 × 1)",
    "Avery 5366/8366 File Folder": "Avery 5366 File Folder (2 × 15)",
    "Avery 22805 Square": "Avery 22805 Square (4 × 6)",
    "Avery 22806 Square": "Avery 22806 Square (3 × 4)",
    "Avery 22807 Round": "Avery 22807 Round (3 × 4)",
    "Avery 22830 Round": "Avery 22830 Round (3 × 3)",
    "Avery 22804 Oval": "Avery 22804 Oval (3 × 6)",
    "Avery 36460/36461/22822 Rectangle": "Avery 22822 Rectangle (2 × 4)",
    "LabTAG A4CL-23T1 Cryo-LazrTAG PCR Cryovial": "LabTAG A4-23 Cryogenic (6 × 21)",
}
KNOWN_SHEET_PRODUCTS_WITH_CUSTOM_SPACING = set()


def _manufacturer_preset(entry):
    name, width, height, *unit = entry
    if unit == ["mm"]:
        width_mm, height_mm = width, height
    else:
        width_mm, height_mm = width * INCH_TO_MM, height * INCH_TO_MM
    sheet_name = AVERY_SHEET_PRESET_BY_PRODUCT.get(name)
    if name in KNOWN_SHEET_PRODUCTS_WITH_CUSTOM_SPACING:
        sheet_name = CUSTOM_SHEET_PRESET
    base = (name, width_mm, height_mm, width_mm, height_mm)
    return base + (sheet_name,) if sheet_name else base


LABEL_PRESETS.extend(_manufacturer_preset(entry) for entry in COMMON_MANUFACTURER_LABELS)


GENERAL_PRESET_DETAILS = {
    "Cryovial": ("Cryovial / Microtube", "Laboratory"),
    "Small Label": ("Small Barcode / Identification", "Barcode / ID"),
    "Wristband Label": ("Wristband", "Wristband"),
    "Small Plant Tag": ("Small Plant Tag", "Plant"),
    "Cryobox / Tube": ("Cryobox / Tube", "Laboratory"),
    "General Purpose": ("General Purpose", "Multipurpose"),
    "Food Label": ("Food / Date Label", "Food safety"),
    "Tag Label": ("Hang Tag", "Tag"),
    "Standard Plant Label": ("Standard Plant Label", "Plant"),
    "Large Field Label": ("Large Field Label", "Plant"),
    "Shipping Label": ("4 × 6-class Shipping Label", "Shipping"),
    "Square Label": ("2 × 2-class Square Label", "Square"),
}


def label_preset_brand(name):
    return next((brand for brand in (
        "USA Scientific", "Fisherbrand", "Brother", "LabTAG", "PR1MA",
        "Zebra", "Avery", "DYMO", "Brady",
    ) if name.startswith(brand + " ")), "General")


def label_preset_category(name):
    """Return a concise use/shape category for browsing and searching."""
    if name in GENERAL_PRESET_DETAILS:
        return GENERAL_PRESET_DETAILS[name][1]
    lowered = name.casefold()
    categories = (
        (("cryo", "pcr", "microtube", "tube"), "Laboratory"),
        (("shipping",), "Shipping"),
        (("return address",), "Return address"),
        (("address",), "Address"),
        (("file folder",), "File folder"),
        (("name badge", "visitor", "business card"), "Badge / card"),
        (("food",), "Food safety"),
        (("round", "dot"), "Round"),
        (("square",), "Square"),
        (("oval",), "Oval"),
        (("plant", "field"), "Plant"),
        (("tag",), "Tag"),
        (("multipurpose", "general purpose"), "Multipurpose"),
    )
    return next((category for terms, category in categories
                 if any(term in lowered for term in terms)), "Specialty")


CATEGORY_SEARCH_ALIASES = {
    "Address": "mailing envelope postal",
    "Return address": "mailing envelope postal",
    "Badge / card": "visitor event credential appointment business card",
    "Barcode / ID": "inventory asset identification barcode qr",
    "Food safety": "food date rotation removable kitchen restaurant",
    "Laboratory": "lab sample vial tube freezer cryogenic cryo PCR",
    "Multipurpose": "general organization identification",
    "Plant": "horticulture nursery garden field plant tag",
    "Round": "circle circular dot sticker",
    "Shipping": "mailing parcel package postage logistics",
    "Square": "sticker",
    "Tag": "hang merchandise retail",
}


def format_preset_inches(value):
    """Prefer familiar catalog fractions without disguising exact metric sizes."""
    value = float(value)
    fraction = Fraction(value).limit_denominator(64)
    if abs(float(fraction) - value) < 1e-6:
        whole, numerator = divmod(fraction.numerator, fraction.denominator)
        if numerator == 0:
            return str(whole)
        if whole:
            return f"{whole} {numerator}/{fraction.denominator}"
        return f"{numerator}/{fraction.denominator}"
    return f"{value:.3f}".rstrip("0").rstrip(".")


def label_preset_title(preset):
    """Consistent exact dimensions in both units, independent of saved option IDs."""
    name, _, _, width, height = preset[:5]
    return (f"{format_preset_inches(width / INCH_TO_MM)} × "
            f"{format_preset_inches(height / INCH_TO_MM)} in"
            f" · {width:g} × {height:g} mm · {name}")


def label_preset_table_row(preset):
    """Readable columns for browsing; saved preset identifiers remain unchanged."""
    name, _, _, width, height = preset[:5]
    brand = label_preset_brand(name)
    product = name if brand == "General" else name[len(brand):].strip()
    if brand == "General":
        product = GENERAL_PRESET_DETAILS.get(name, (name, "Specialty"))[0]
    def display(value):
        return f"{value:.4f}".rstrip("0").rstrip(".")

    return {
        "Size (in)": f"{format_preset_inches(width / INCH_TO_MM)} × "
                     f"{format_preset_inches(height / INCH_TO_MM)}",
        "Size (mm)": f"{display(width)} × {display(height)}",
        "Brand": brand,
        "Type": label_preset_category(name),
        "Product / template": product,
    }


def _normalize_search_text(text):
    text = str(text).casefold().replace("×", "x").replace('"', " in ")
    # Let common SKU spellings match equally: DK1202 / DK-1202 and
    # Z Select / Z-Select, while retaining slashes used in fractions.
    text = re.sub(r"(?<=\w)[-_](?=\w)", "", text)
    return re.sub(r"[^\w./]+", " ", text).strip()


def label_preset_matches(preset, query):
    """Match brand/part words and optional W×H, with inches or mm in any UI mode."""
    query = _normalize_search_text(query)
    number = r"(?:\d+\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?|\.\d+)"
    match = re.search(rf"({number})\s*(?:inches|inch|in|mm)?\s*x\s*({number})\s*(inches|inch|in|mm)?", query)
    if match:
        def parse(value):
            return sum(float(Fraction(part)) for part in value.split())
        try:
            width, height = parse(match[1]), parse(match[2])
        except (ValueError, ZeroDivisionError):
            return False
        unit = "mm" if "mm" in match[0] else match[3]
        scales = [1] if unit == "mm" else [INCH_TO_MM] if unit else [1, INCH_TO_MM]
        if not any(
            (abs(preset[3] - width * scale) <= 0.015 and
             abs(preset[4] - height * scale) <= 0.015) or
            (abs(preset[3] - height * scale) <= 0.015 and
             abs(preset[4] - width * scale) <= 0.015)
            for scale in scales
        ):
            return False
        query = query[:match.start()] + " " + query[match.end():]
    row = label_preset_table_row(preset)
    searchable = _normalize_search_text(" ".join((
        label_preset_title(preset), row["Brand"], row["Type"],
        row["Product / template"], CATEGORY_SEARCH_ALIASES.get(row["Type"], ""),
    )))
    compact_searchable = searchable.replace(" ", "")
    return all(word in searchable or word.replace(" ", "") in compact_searchable
               for word in query.split())


SHEET_STOCK_PRESETS = [
    {
        "name": "PR1MA 119 Tag Sheet (7 x 17)",
        "page_format": "Letter",
        "label_width_mm": 24.01,
        "label_height_mm": 13.00,
        "columns": 7,
        "rows": 17,
        "margin_top_mm": 4.76,
        "margin_right_mm": 14.82,
        "margin_bottom_mm": 5.63,
        "margin_left_mm": 15.01,
        "gap_horizontal_mm": 3.00,
        "gap_vertical_mm": 3.00,
    },
    {
        "name": "PR1MA 85 Tag Sheet (5 x 17)",
        "page_format": "Letter",
        "label_width_mm": 33.00,
        "label_height_mm": 13.00,
        "columns": 5,
        "rows": 17,
        "margin_top_mm": 6.00,
        "margin_right_mm": 19.39,
        "margin_bottom_mm": 4.40,
        "margin_left_mm": 19.51,
        "gap_horizontal_mm": 3.00,
        "gap_vertical_mm": 3.00,
    },
    {
        "name": "PR1MA 52 Tag Sheet (4 x 13)",
        "page_format": "Letter",
        "label_width_mm": 42.93,
        "label_height_mm": 19.05,
        "columns": 4,
        "rows": 13,
        "margin_top_mm": 14.29,
        "margin_right_mm": 18.28,
        "margin_bottom_mm": 17.46,
        "margin_left_mm": 17.46,
        "gap_horizontal_mm": 2.79,
        "gap_vertical_mm": 0.00,
    },
    {
        "name": "PR1MA 30 Tag Sheet (3 x 10)",
        "page_format": "Letter",
        "label_width_mm": 66.67,
        "label_height_mm": 25.40,
        "columns": 3,
        "rows": 10,
        "margin_top_mm": 12.70,
        "margin_right_mm": 4.82,
        "margin_bottom_mm": 12.70,
        "margin_left_mm": 5.57,
        "gap_horizontal_mm": 2.75,
        "gap_vertical_mm": 0.00,
    },
    {
        "name": "PR1MA 12 Tag Sheet (2 x 12)",
        "page_format": "Letter",
        "label_width_mm": 73.15,
        "label_height_mm": 22.18,
        "columns": 2,
        "rows": 12,
        "margin_top_mm": 6.35,
        "margin_right_mm": 21.09,
        "margin_bottom_mm": 6.84,
        "margin_left_mm": 48.51,
        "gap_horizontal_mm": 0.00,
        "gap_vertical_mm": 0.00,
    },
    {
        "name": "PR1MA 192 Half-In Dot Sheet (12 x 16)",
        "page_format": "Letter",
        "label_width_mm": 13.00,
        "label_height_mm": 13.00,
        "columns": 12,
        "rows": 16,
        "margin_top_mm": 13.00,
        "margin_right_mm": 13.39,
        "margin_bottom_mm": 13.40,
        "margin_left_mm": 13.51,
        "gap_horizontal_mm": 3.00,
        "gap_vertical_mm": 3.00,
    },
    make_sheet_stock_preset(
        "USA Scientific 1.28 x 0.50 in Laser Sheet (5 x 17)",
        1.28,
        0.50,
        5,
        17,
        0.24,
        0.77,
        1.40,
        0.63,
    ),
    make_sheet_stock_preset(
        "USA Scientific 0.94 x 0.50 in Laser Sheet (7 x 17)",
        0.94,
        0.50,
        7,
        17,
        0.24,
        0.56,
        1.07,
        0.63,
    ),
    make_sheet_stock_preset(
        "USA Scientific 1.50 x 0.75 in Laser Sheet (5 x 12)",
        1.50,
        0.75,
        5,
        12,
        0.31,
        0.25,
        1.63,
        0.88,
    ),
    make_sheet_stock_preset(
        "USA Scientific 0.875 x 0.875 in Laser Sheet (8 x 12)",
        0.875,
        0.875,
        8,
        12,
        0.25,
        0.28,
        1.00,
        0.88,
    ),
    make_sheet_stock_preset(
        "USA Scientific 2.50 x 0.50 in Laser Sheet (3 x 20)",
        2.50,
        0.50,
        3,
        20,
        0.50,
        0.47,
        2.50,
        0.50,
    ),
    make_sheet_stock_preset(
        "USA Scientific 0.91 x 0.32 in Laser Sheet (7 x 22)",
        0.91,
        0.32,
        7,
        22,
        0.75,
        0.69,
        1.03,
        0.44,
    ),
    make_sheet_stock_preset(
        "USA Scientific 1.00 x 1.00 in Laser Sheet (8 x 10)",
        1.00,
        1.00,
        8,
        10,
        0.50,
        0.25,
        1.00,
        1.00,
    ),
    make_sheet_stock_preset(
        "USA Scientific 1.625 x 0.625 in Laser Sheet (4 x 16)",
        1.625,
        0.625,
        4,
        16,
        0.50,
        0.50,
        1.94,
        0.63,
    ),
    make_sheet_stock_preset(
        "USA Scientific 2.625 x 0.1875 in Laser Sheet (3 x 33)",
        2.625,
        0.1875,
        3,
        33,
        0.4375,
        0.28,
        2.625,
        0.31,
    ),
    make_sheet_stock_preset(
        "USA Scientific 1.50 x 0.50 in Laser Sheet (5 x 16)",
        1.50,
        0.50,
        5,
        16,
        0.56,
        0.22,
        1.63,
        0.63,
    ),
    make_sheet_stock_preset(
        "USA Scientific 1.05 x 0.50 in Laser Sheet (6 x 16)",
        1.05,
        0.50,
        6,
        16,
        0.56,
        0.75,
        1.18,
        0.63,
    ),
    make_sheet_stock_preset(
        "USA Scientific 1.69 x 0.75 in Laser Sheet (4 x 13)",
        1.69,
        0.75,
        4,
        13,
        0.63,
        0.70,
        1.80,
        0.75,
    ),
    make_sheet_stock_preset(
        "USA Scientific 1.50 x 0.25 in Laser Sheet (4 x 39)",
        1.50,
        0.25,
        4,
        39,
        0.62,
        0.50,
        2.00,
        0.25,
    ),
    make_sheet_stock_preset(
        "USA Scientific 2.625 x 1.00 in Laser Sheet (3 x 10)",
        2.625,
        1.00,
        3,
        10,
        0.50,
        0.19,
        2.75,
        1.00,
    ),
    make_sheet_stock_preset(
        "USA Scientific 1.125 x 1.75 in Laser Sheet (7 x 6)",
        1.125,
        1.75,
        7,
        6,
        0.25,
        0.28,
        1.125,
        1.75,
    ),
    make_sheet_stock_preset(
        "USA Scientific 3.00 x 2.00 in Laser Sheet (3 x 4 Landscape)",
        3.00,
        2.00,
        3,
        4,
        0.22,
        1.00,
        3.00,
        2.00,
        page_format="Letter Landscape",
    ),
    make_sheet_stock_preset(
        "USA Scientific Tough-Spot 3/8 in Sheet (12 x 16)",
        0.38,
        0.38,
        12,
        16,
        0.62,
        0.69,
        0.63,
        0.63,
    ),
    make_sheet_stock_preset(
        "USA Scientific Tough-Spot 1/2 in Sheet (12 x 16)",
        0.50,
        0.50,
        12,
        16,
        0.52,
        0.52,
        0.63,
        0.63,
    ),
    make_sheet_stock_preset(
        "USA Scientific Tough-Spot 3/4 in Sheet (9 x 12)",
        0.75,
        0.75,
        9,
        12,
        0.31,
        0.35,
        0.88,
        0.88,
    ),
    make_sheet_stock_preset(
        "USA Scientific Tough-Spot 1.00 in Sheet (7 x 9)",
        1.00,
        1.00,
        7,
        9,
        0.50,
        0.35,
        1.13,
        1.13,
    ),
    make_sheet_stock_preset(
        "USA Scientific Tough-Spot 7/16 in Sheet (13 x 18)",
        0.44,
        0.44,
        13,
        18,
        0.44,
        0.59,
        0.57,
        0.57,
    ),
    make_sheet_stock_preset(
        "Avery 5167 Return Address (4 × 20)",
        1.75, 0.50, 4, 20, 0.50, 0.28125, 2.0625, 0.50,
    ),
    make_sheet_stock_preset(
        "Avery 5195 Return Address (4 × 15)",
        1.75, 2 / 3, 4, 15, 0.50, 0.375, 2.00, 2 / 3,
    ),
    make_sheet_stock_preset(
        "Avery 5160 Address (3 × 10)",
        2.625, 1.00, 3, 10, 0.50, 0.1875, 2.75, 1.00,
    ),
    make_sheet_stock_preset(
        "Avery 5161 Address (2 × 10)",
        4.00, 1.00, 2, 10, 0.50, 0.15625, 4.1875, 1.00,
    ),
    make_sheet_stock_preset(
        "Avery 5162 Address (2 × 7)",
        4.00, 4 / 3, 2, 7, 1 / 3, 0.15625, 4.1875, 1.50,
    ),
    make_sheet_stock_preset(
        "Avery 5163 Shipping (2 × 5)",
        4.00, 2.00, 2, 5, 0.50, 0.15625, 4.1875, 2.00,
    ),
    make_sheet_stock_preset(
        "Avery 5164 Shipping (2 × 3)",
        4.00, 10 / 3, 2, 3, 0.50, 0.15625, 4.1875, 10 / 3,
    ),
    make_sheet_stock_preset(
        "Avery 5168 Shipping (2 × 2)",
        3.50, 5.00, 2, 2, 0.50, 0.50, 4.00, 5.00,
    ),
    make_sheet_stock_preset(
        "Avery 5165 Full Sheet (1 × 1)",
        8.50, 11.00, 1, 1, 0.00, 0.00, 8.50, 11.00,
    ),
    make_sheet_stock_preset(
        "Avery 5366 File Folder (2 × 15)",
        3 + 7 / 16, 2 / 3, 2, 15, 0.50, 0.53125, 4.00, 2 / 3,
    ),
    make_sheet_stock_preset(
        "Avery 22805 Square (4 × 6)",
        1.50, 1.50, 4, 6, 0.50, 0.78125, 1.8125, 1.70,
    ),
    make_sheet_stock_preset(
        "Avery 22806 Square (3 × 4)",
        2.00, 2.00, 3, 4, 0.60, 0.625, 2.625, 2.60,
    ),
    make_sheet_stock_preset(
        "Avery 22807 Round (3 × 4)",
        2.00, 2.00, 3, 4, 0.60, 0.625, 2.625, 2.60,
    ),
    make_sheet_stock_preset(
        "Avery 22830 Round (3 × 3)",
        2.50, 2.50, 3, 3, 0.625, 0.3125, 2.6875, 3.625,
    ),
    make_sheet_stock_preset(
        "Avery 22804 Oval (3 × 6)",
        2.50, 1.50, 3, 6, 0.6875, 0.375, 2.625, 1.625,
    ),
    make_sheet_stock_preset(
        "Avery 22822 Rectangle (2 × 4)",
        3.00, 2.00, 2, 4, 1.3125, 0.85, 3.80, 2.125,
    ),
    make_sheet_stock_preset(
        "LabTAG A4-23 Cryogenic (6 × 21)",
        31.5 / INCH_TO_MM, 13 / INCH_TO_MM, 6, 21,
        12 / INCH_TO_MM, 6.6 / INCH_TO_MM,
        33.02 / INCH_TO_MM, 13 / INCH_TO_MM,
        page_format="A4",
    ),
]

SHEET_STOCK_PRESET_BY_NAME = {
    preset["name"]: preset for preset in SHEET_STOCK_PRESETS
}
