# Changelog

All notable changes to PlantID Label Designer are listed here. The app follows [semantic versioning](https://semver.org). Saved layout files have their own [schema version](README.md#versioning).

## Unreleased

### Added
- **Rename displayed columns** can now leave a column's name blank, so only its value is printed: tick **Hide** beside the column, or type a space as its label.

## 1.0.0

First stable release, accompanying the PlantID paper in the *International Journal of Phenomics*.

### Added
- Excel (`.xlsx`) data files, alongside CSV.
- A one-page start screen: choose your data, then start from defaults, an example layout, or a saved layout.
- One-click **Download labels PDF**, with problems that block export shown beforehand.
- A first-sheet preview and a numbered alignment test page for sheet stock.
- Warnings when text does not fit on a label (checked across every selected row), or when a QR code or barcode is too small to scan reliably.
- A list of any columns a loaded layout refers to that are missing from the data.
- A preset browser dialog with search that stays in view on small screens.
- **Show advanced settings**, gathering the label border, spacing and offset adjustments, and wrap tags.
- Citation information in the app, the README and `CITATION.cff`, and a label gallery in the README.
- Automated tests on GitHub Actions.

### Changed
- Layout files use schema version 1, with descriptive field names. Schema 0 files are converted when loaded. Row ranges, filters, and the first label position are no longer saved in layouts.
- QR codes use error correction level M (about 15% damage tolerance, previously 7%).
- **Code offset from edge** is measured from the label edge for every barcode placement. Schema 0 layouts are adjusted on load so their output is unchanged.
- Version warnings appear only when a layout's schema differs from the app's.
- Dependencies are pinned to tested versions.

### Fixed
- Spreadsheet values are printed exactly as written: IDs keep leading zeros, whole numbers are not shown as `1.0`, and blank cells are not printed as `nan`.
- CSV files saved by Excel on Windows load instead of crashing the app.
- Barcodes beside text are drawn at the chosen width instead of up to 1.7× wider, and always in black.
- Long text is clipped to its label instead of printing onto neighbouring labels.
- Hidden settings loaded from a layout keep their values instead of reverting to defaults.
- The Codespaces dev container installs the app's requirements.

## 0.10

- Text above, below, or on both sides of a barcode.
- Wrap tags with a tear-off section for loop-lock stock.
- Label size presets and sheet stock presets, and a first label position for partly used sheets.
