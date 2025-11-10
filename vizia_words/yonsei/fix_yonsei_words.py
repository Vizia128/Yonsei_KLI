import csv
from pathlib import Path

# === FILE PATHS ===
INPUT_FILE = Path("vizia_words/yonsei/yonsei_words_nonlemma.csv")
FIXES_FILE = Path("vizia_words/yonsei/yonsei_word_fixes.csv")
OUTPUT_FILE = Path("vizia_words/yonsei_words.csv")


def load_fixes(path):
    """Load fix mappings from CSV into a dictionary."""
    fixes = {}
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="|")
        for row in reader:
            original = row["word"].strip()
            fixed = row["fixed_word"].strip()
            if original and fixed:
                fixes[original] = fixed
    return fixes


def apply_fixes(input_file, fixes):
    """Apply the fixes to the words."""
    fixed_rows = []
    seen = set()

    with input_file.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=",")
        for row in reader:
            word = row["word"].strip()
            fixed_word = fixes.get(word, word)
            # Avoid duplicates (keep the first occurrence)
            if fixed_word not in seen:
                seen.add(fixed_word)
                row["word"] = fixed_word
                fixed_rows.append(row)
    return fixed_rows


def main():
    if not INPUT_FILE.exists():
        print(f"❌ Input file not found: {INPUT_FILE}")
        return
    if not FIXES_FILE.exists():
        print(f"❌ Fix mapping file not found: {FIXES_FILE}")
        return

    fixes = load_fixes(FIXES_FILE)
    print(f"🧾 Loaded {len(fixes)} fix mappings.")

    fixed_rows = apply_fixes(INPUT_FILE, fixes)
    print(f"✅ Applied fixes to {len(fixed_rows)} entries.")
    print(
        f"🔍 Duplicates automatically removed: {len(fixes) - len(fixed_rows)} potential overlaps handled."
    )

    # Write output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["word", "source_book"], delimiter="|")
        writer.writeheader()
        writer.writerows(fixed_rows)

    print(f"💾 Output saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
