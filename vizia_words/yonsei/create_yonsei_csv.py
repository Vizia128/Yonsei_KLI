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
        return (float("inf"), float("inf"))  # put non-matching files last


# === Collect and sort CSV files ===
files = [f for f in os.listdir(input_folder) if f.lower().endswith(".csv")]
files.sort(key=extract_order)

print("📂 Files to merge in order:")
for f in files:
    print("  ", f)

# === Merge all words ===
rows = []
seen = set()  # to track duplicate words

for filename in files:
    input_path = os.path.join(input_folder, filename)
    with open(input_path, newline="", encoding="utf-8") as infile:
        reader = csv.reader(infile)
        for row in reader:
            # Skip empty rows
            if not row:
                continue
            # Get the first cell as the word
            word = row[0].strip()
            if not word or word in seen:
                continue
            seen.add(word)
            rows.append([word, filename])

# === Write final CSV with headers ===
os.makedirs(os.path.dirname(output_file), exist_ok=True)
with open(output_file, "w", newline="", encoding="utf-8") as outfile:
    writer = csv.writer(outfile)
    writer.writerow(["word", "source_book"])  # header
    writer.writerows(rows)

print(f"\n✅ Combined {len(files)} files into {output_file}")
print(f"🧹 Removed duplicates, kept {len(rows)} unique words.")
