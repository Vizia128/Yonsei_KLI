import csv
import os
import re

# === Folder and output paths ===
input_folder = "vizia_words/yonsei/clean/"
output_file = "vizia_words/yonsei_words.csv"


# === Helper: extract numeric order from filenames like 1-1.csv ===
def extract_order(filename):
    match = re.match(r"(\d+)-(\d+)\.csv$", filename)
    if match:
        major, minor = map(int, match.groups())
        return (major, minor)
    else:
        return (float("inf"), float("inf"))  # put non-matching files at end


# === Collect CSV files and sort ===
files = [f for f in os.listdir(input_folder) if f.lower().endswith(".csv")]
files.sort(key=extract_order)

print("📂 Files to merge in order:")
for f in files:
    print("  ", f)

# === Merge files ===
all_rows = []
seen = set()

for filename in files:
    path = os.path.join(input_folder, filename)
    with open(path, newline="", encoding="utf-8") as infile:
        reader = csv.reader(infile)
        for row in reader:
            row_tuple = tuple(row)
            if row_tuple not in seen:
                seen.add(row_tuple)
                all_rows.append(row)

# === Write combined CSV ===
os.makedirs(os.path.dirname(output_file), exist_ok=True)
with open(output_file, "w", newline="", encoding="utf-8") as outfile:
    writer = csv.writer(outfile)
    writer.writerows(all_rows)

print(f"\n✅ Combined {len(files)} files into {output_file}")
print(f"🧹 Removed duplicates, kept {len(all_rows)} unique rows.")
