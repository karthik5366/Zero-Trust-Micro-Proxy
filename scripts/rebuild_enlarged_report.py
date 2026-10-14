import os
import docx
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Use the user's latest docx which has their logo already placed on the cover!
base_docx = r"C:\Users\karth\.gemini\antigravity\brain\7e02376d-9810-4e77-b16b-5b859704ee5e\.user_uploaded\media_1791478139454_e75ace7b.docx"
img_dir = r"C:\Users\karth\Downloads\Projects\Zero-Trust-Micro-Proxy\report-images\final"
output_docx = r"C:\Users\karth\Downloads\Projects\Zero-Trust-Micro-Proxy\ZetaShield_Final_Report.docx"

print("Loading base document (with user's logo)...")
doc = docx.Document(base_docx)

# Map all 16 figures with ENLARGED widths (6.2 - 6.4 inches for maximum legibility)
figure_map = {
    4:  ("fig_1_1.png", Inches(6.4)),
    5:  ("fig_1_2.png", Inches(6.4)),
    6:  ("fig_2_1.png", Inches(6.4)),
    8:  ("fig_3_1.png", Inches(6.4)),
    14: ("fig_4_1.png", Inches(6.4)),
    15: ("fig_4_2.png", Inches(6.4)),
    18: ("fig_4_3.png", Inches(6.4)),
    20: ("fig_5_1.png", Inches(6.2)),
    21: ("fig_5_8.png", Inches(6.2)),
    22: ("fig_5_4.png", Inches(6.2)),
    24: ("fig_5_6.png", Inches(6.2)),
    26: ("fig_5_2.png", Inches(6.2)),
    27: ("fig_5_3.png", Inches(6.2)),
    28: ("fig_5_7.png", Inches(6.2)),
    30: ("fig_5_5.png", Inches(6.2)),
    34: ("fig_6_1.png", Inches(6.4)),
}

print("Replacing images in document tables with enlarged, crisp versions...")
for t_idx, (img_name, width) in figure_map.items():
    if t_idx < len(doc.tables):
        table = doc.tables[t_idx]
        cell = table.rows[0].cells[0]
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        img_path = os.path.join(img_dir, img_name)
        if os.path.exists(img_path):
            run = p.add_run()
            run.add_picture(img_path, width=width)
            print(f"Inserted Table {t_idx} -> {img_name} at width {width}")
        else:
            print(f"WARNING: Image not found: {img_path}")

# Remove outer table borders for seamless appearance
def remove_table_borders(table):
    tblPr = table._tbl.tblPr
    tblBorders = OxmlElement('w:tblBorders')
    for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
        border = OxmlElement(f'w:{border_name}')
        border.set(qn('w:val'), 'none')
        tblBorders.append(border)
    tblPr.append(tblBorders)

for t_idx in figure_map.keys():
    if t_idx < len(doc.tables):
        remove_table_borders(doc.tables[t_idx])

print(f"Saving updated document to {output_docx}...")
doc.save(output_docx)
print("DOCX successfully saved with enlarged images and user's logo preserved!")
