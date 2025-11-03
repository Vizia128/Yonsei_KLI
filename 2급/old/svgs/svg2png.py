import os
import subprocess
from PIL import Image

# ==== CONFIG ====
INPUT_FOLDER = r"C:\Users\julia\OneDrive\Documents\연세한국어\svgs\part1"
OUTPUT_PNG = r"C:\Users\julia\OneDrive\Documents\연세한국어\svgs\combined.png"
INKSCAPE_PATH = r"C:\Program Files\Inkscape\bin\inkscape.exe"  # adjust if needed
DPI = 300  # higher for better quality
# =================

# Step 1: Convert SVGs to PNGs
png_files = []
for file in sorted(os.listdir(INPUT_FOLDER)):
    if file.lower().endswith(".svg"):
        svg_path = os.path.join(INPUT_FOLDER, file)
        png_path = os.path.join(INPUT_FOLDER, file[:-4] + ".png")
        subprocess.run([
            INKSCAPE_PATH,
            svg_path,
            f"--export-type=png",
            f"--export-filename={png_path}",
            f"--export-dpi={DPI}"
        ], check=True)
        png_files.append(png_path)

# Step 2: Combine PNGs vertically
images = [Image.open(p) for p in png_files]
width = max(img.width for img in images)
total_height = sum(img.height for img in images)

combined_img = Image.new("RGB", (width, total_height), (255, 255, 255))

y_offset = 0
for img in images:
    combined_img.paste(img, (0, y_offset))
    y_offset += img.height

combined_img.save(OUTPUT_PNG)
print(f"Combined PNG saved to: {OUTPUT_PNG}")
