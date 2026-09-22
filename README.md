# PlantID Label Designer 

## Description
PlantID Label Designer is a Streamlit web application for generating customizable plant sample labels. The app allows researchers to visualize, design, and export labels with QR codes, highlighted metadata, and flexible sizing for a variety of use cases including cryovials, plant tags, wrap tags, and more.
It is designed to work both locally and on Streamlit Cloud.

## Try the online version
Try the app directly without installation
https://plantid-label-designer.streamlit.app


<img width="732" height="460" alt="Screenshot 2026-04-13 at 11 32 04" src="https://github.com/user-attachments/assets/b937336e-6740-48e7-ad65-1a57c7b8729d" />


## Installation (Local)
Clone this repository
```bash
git clone https://github.com/danforthcenter/PlantID.git
cd PlantID/PlantID-LabelDesigner-streamlit
```
Install required packages
```bash
pip install -r requirements.txt
```

## Running the app
Run the app locally:
```bash
streamlit run streamlit_app.py
```
Upload a CSV with your plant metadata. Configure label settings. Download the PDF for printing.

## Versioning

| Version | Current |
|---|---|
| App | 0.10 |
| Layout template schema | 0 |

The **app version** reflects the overall release of PlantID Label Designer. The **layout template schema version** is an independent version integer that tracks the structure of saved layout `.json` files. It only increments when a breaking change is made to the layout format (e.g. fields renamed or restructured). When loading a saved layout, the app will warn if the schema versions do not match.

App 0.10 adds barcode text placement above, below, or on both sides of the barcode. Saved layouts include the placement and fields selected above the barcode. Older layouts retain the beside-barcode default; the template schema remains version 0.

### Gemplers loop-lock sheet tags

Choose **Gemplers 151062 Loop-Lock 11 x 1 in (1 x 8)** under **Sheet printer → Sheet stock preset**, or search **Gemplers** in the label preset browser. The preset uses landscape Letter paper, eight 11 × 1-inch strips, ¼-inch top/bottom margins, and no gaps. These dimensions come from the [product specifications](https://gemplers.com/products/laser-strip-loop-lock-tags-11-quot-x-1-quot) and its linked Word template.

Selecting this stock enables **Wrap tag / tear-off**. The right-hand tab defaults to 2¼ inches (57.15 mm). Its displayed fields follow the main tag, and its QR/barcode uses the main tag's code data. Check **Customize tear-off fields** to choose a different set (or no text), or uncheck **Use main tag code data** to encode another column. Code type, size, position, font size, field names, and padding are adjustable independently.

The default blank loop area is 4 inches (101.6 mm), following the supplier's main-text template; adjust it to align the main code/text with your particular cutouts. Main content is clipped to its section and tear-off text wraps/shrinks to fit. All settings are saved in layout JSON. Print at **100% / actual size** and check alignment on plain paper against your stock before a production run.
