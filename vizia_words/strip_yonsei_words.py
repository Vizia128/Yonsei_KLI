import csv
import re
import random

# === File paths ===
input_file = "vizia_words/yonsei/1-1.csv"
output_file = "vizia_words/yonsei/1-1_clean.csv"

# === Regex patterns ===
patterns_to_remove = [
    r"^\s*\d+\s*$",  # just a number (x)
    r"^\s*\d+\s*과\s*$",  # x과
    r"^\s*\d+\s*항\s*$",  # x항
    r"^\s*\d+\s*<\s*\d+\s*>\s*$",  # x<y>
]

# Words to remove if they appear anywhere in a line
words_to_remove = ["확장", "대화", "참고", "색인"]

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


# === Read CSV and filter rows ===
filtered_rows = []
with open(input_file, newline="", encoding="utf-8") as infile:
    reader = csv.reader(infile)
    for row in reader:
        # Keep row only if at least one cell passes
        if any(not should_remove(cell) for cell in row):
            filtered_rows.append(row)

# === Remove duplicates ===
# Convert each row to tuple for deduplication
unique_rows = list({tuple(row) for row in filtered_rows})

# === Randomize order ===
random.shuffle(unique_rows)

# === Write cleaned CSV ===
with open(output_file, "w", newline="", encoding="utf-8") as outfile:
    writer = csv.writer(outfile)
    writer.writerows(unique_rows)

print(f"✅ Cleaned, deduplicated, and shuffled CSV written to: {output_file}")
