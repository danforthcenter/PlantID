"""Read uploaded label data exactly as written in the file."""
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
