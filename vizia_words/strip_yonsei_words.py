import csv
import re
import random
import os

# === Folder paths ===
input_folder = "vizia_words/yonsei/raw/"
output_folder = "vizia_words/yonsei/clean/"

# Make sure output folder exists
os.makedirs(output_folder, exist_ok=True)

# === Regex patterns ===
patterns_to_remove = [
    r"^\s*\d+\s*$",  # just a number (x)
    r"^\s*\d+\s*과\s*$",  # x과
    r"^\s*\d+\s*항\s*$",  # x항
    r"^\s*\d+\s*<\s*\d+\s*>\s*$",  # x<y>
]

# Words to remove if they appear anywhere in a line
words_to_remove = ["색인", "확장", "대화", "참고", "색인"]

# Hangul consonants only (no vowels)
bare_consonants = {
    "ㅂ",
    "ㅈ",
    "ㄷ",
    "ㄱ",
    "ㅅ",
    "ㅁ",
    "ㄴ",
    "ㅇ",
    "ㄹ",
    "ㅎ",
    "ㅋ",
    "ㅌ",
    "ㅊ",
    "ㅍ",
}


def is_bare_consonant(line):
    """Return True if line is just a bare Hangul consonant."""
    stripped = line.strip()
    return stripped in bare_consonants


def should_remove(line):
    """Check all conditions for removal."""
    line = line.strip()
    if not line:
        return True  # empty line
    if any(word in line for word in words_to_remove):
        return True
    if is_bare_consonant(line):
        return True
    for pat in patterns_to_remove:
        if re.fullmatch(pat, line):
            return True
    return False


# === Process all CSV files ===
for filename in os.listdir(input_folder):
    if not filename.lower().endswith(".csv"):
        continue

    input_path = os.path.join(input_folder, filename)
    output_path = os.path.join(output_folder, filename)

    filtered_rows = []

    # Read and filter CSV
    with open(input_path, newline="", encoding="utf-8") as infile:
        reader = csv.reader(infile)
        for row in reader:
            # Keep row only if at least one cell passes
            if any(not should_remove(cell) for cell in row):
                filtered_rows.append(row)

    # Remove duplicates
    unique_rows = list({tuple(row) for row in filtered_rows})

    # Shuffle
    random.shuffle(unique_rows)

    # Write cleaned CSV
    with open(output_path, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.writer(outfile)
        writer.writerows(unique_rows)

    print(f"✅ Cleaned, deduplicated, and shuffled: {filename}")

print(f"\n🎉 All files processed! Cleaned CSVs saved in: {output_folder}")
