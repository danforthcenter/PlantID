"""Read uploaded label data exactly as written in the file."""
import datetime
import io

import pandas as pd

# utf-8-sig strips the byte-order mark Excel adds; cp1252 covers "CSV" saved
# by Excel on Windows; latin-1 accepts any byte so decoding never fails.
CSV_ENCODINGS = ("utf-8-sig", "cp1252", "latin-1")


def read_label_csv(source):
    """Return (dataframe, error). Every cell is text, so IDs such as 00123 keep
    their leading zeros, integers are not shown as 1.0, and blanks stay blank."""
    raw = source if isinstance(source, bytes) else source.read()
    for encoding in CSV_ENCODINGS:
        try:
            df = pd.read_csv(io.BytesIO(raw), dtype=str, keep_default_na=False,
                             encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
        except (pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
            return None, f"Could not read the CSV file: {exc}"
    if df.empty:
        return None, "The CSV file has no data rows."
    return df, None


def _excel_text(value):
    """Show Excel cells as they appear in the sheet, not as Python values."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, datetime.datetime) and value.time() == datetime.time(0):
        return value.date().isoformat()
    return str(value)


def read_label_excel(raw):
    """Return (dataframe, error) for the first sheet of an .xlsx workbook."""
    try:
        df = pd.read_excel(io.BytesIO(raw), sheet_name=0, dtype=object, engine="openpyxl")
    except Exception as exc:
        return None, f"Could not read the Excel file: {exc}"
    df = df.map(_excel_text)
    df.columns = [_excel_text(column) for column in df.columns]
    if df.empty:
        return None, "The first sheet of the Excel file has no data rows."
    return df, None


def read_label_table(raw, filename):
    """Return (dataframe, error) for an uploaded CSV or Excel file."""
    if str(filename).lower().endswith(".xlsx"):
        return read_label_excel(raw)
    return read_label_csv(raw)
