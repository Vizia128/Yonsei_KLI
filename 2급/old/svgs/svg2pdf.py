import os
import subprocess
import tempfile
from PyPDF2 import PdfMerger
import fitz  # PyMuPDF
import pytesseract
from PIL import Image

# ==== CONFIG ====
INPUT_FOLDER = r"C:\Users\julia\OneDrive\Documents\연세한국어\svgs\part1"
OUTPUT_PDF = r"C:\Users\julia\OneDrive\Documents\연세한국어\svgs\combined.pdf"
INKSCAPE_PATH = r"C:\Program Files\Inkscape\bin\inkscape.exe"  # adjust if needed
# =================

# Step 1: Convert SVGs to PDFs using Inkscape
pdf_files = []
for file in sorted(os.listdir(INPUT_FOLDER)):
    if file.lower().endswith(".svg"):
        svg_path = os.path.join(INPUT_FOLDER, file)
        pdf_path = os.path.join(INPUT_FOLDER, file[:-4] + ".pdf")
        subprocess.run([
            INKSCAPE_PATH,
            svg_path,
            "--export-type=pdf",
            "--export-filename", pdf_path
        ], check=True)
        pdf_files.append(pdf_path)

# Step 2: Merge PDFs into one
merger = PdfMerger()
for pdf in pdf_files:
    merger.append(pdf)
merger.write(OUTPUT_PDF)
merger.close()

print(f"Initial PDF created: {OUTPUT_PDF}")

# Step 3: Check if text is selectable (if not, run OCR)
def pdf_has_text(pdf_path):
    doc = fitz.open(pdf_path)
    for page in doc:
        if page.get_text().strip():
            return True
    return False

if not pdf_has_text(OUTPUT_PDF):
    print("No selectable text found — running OCR...")
    doc = fitz.open(OUTPUT_PDF)
    ocr_pdf = fitz.open()

    for page in doc:
        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        text = pytesseract.image_to_pdf_or_hocr(img, extension='pdf', lang='kor')
        temp_pdf = fitz.open("pdf", text)
        ocr_pdf.insert_pdf(temp_pdf)

    ocr_pdf.save(OUTPUT_PDF)
    print(f"OCR completed. Selectable PDF saved as {OUTPUT_PDF}")
else:
    print("Selectable text detected — no OCR needed.")
