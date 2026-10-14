import os
import win32com.client

docx_path = os.path.abspath(r"C:\Users\karth\Downloads\Projects\Zero-Trust-Micro-Proxy\ZetaShield_Final_Report.docx")
pdf_path = os.path.abspath(r"C:\Users\karth\Downloads\Projects\Zero-Trust-Micro-Proxy\ZetaShield_Final_Report.pdf")

print("Launching Microsoft Word in background...")
word = win32com.client.Dispatch("Word.Application")
word.Visible = False
word.DisplayAlerts = False

try:
    print(f"Opening {docx_path}...")
    doc = word.Documents.Open(docx_path)
    
    print("Updating Table of Contents, Figures, and Tables page fields...")
    for toc in doc.TablesOfContents:
        toc.Update()
    for tof in doc.TablesOfFigures:
        tof.Update()
    doc.Fields.Update()
    
    print("Saving updated DOCX...")
    doc.Save()
    
    print(f"Exporting to PDF: {pdf_path}...")
    # 17 = wdFormatPDF
    doc.SaveAs(pdf_path, FileFormat=17)
    print("PDF export successful!")
    
except Exception as e:
    print("Error during Word processing:", e)
finally:
    doc.Close(False)
    word.Quit()
    print("Word application closed.")
