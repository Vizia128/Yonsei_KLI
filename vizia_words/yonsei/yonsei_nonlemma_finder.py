import csv
import re
from pathlib import Path

# === CONFIGURATION ===
INPUT_FILE = Path("vizia_words/yonsei_words.csv")
OUTPUT_FILE = Path("vizia_words/yonsei_suspect_words.csv")

# Regex patterns for non-lemma forms or suspicious entries
PARTICLE_PATTERN = re.compile(r"(을|를|이|가|은|는|에|와|과|의|로|에서)$")
POLITE_ENDING_PATTERN = re.compile(r"(요|어요|아요|예요|이에요|세요|했어요|해요)$")
CONJUGATED_VERB_PATTERN = re.compile(r".*(는|은|운|한|던)$")
NON_HANGUL_PATTERN = re.compile(r"[^가-힣]")  # contains digits, symbols, or Latin
SHORT_OR_STRANGE_PATTERN = re.compile(r"^.{1}$")  # single-character words
REPEATED_JAMO_PATTERN = re.compile(r"(.)\1{2,}")  # e.g., ㅋㅋㅋ, ㅎㅎㅎ


def is_suspicious(word: str) -> bool:
    """
    Return True if the word looks non-lemma or malformed.
    """
    w = word.strip()
    if not w:
        return True
    if NON_HANGUL_PATTERN.search(w):
        return True
    if PARTICLE_PATTERN.search(w):
        return True
    if POLITE_ENDING_PATTERN.search(w):
        return True
    if CONJUGATED_VERB_PATTERN.search(w):
        return True
    if SHORT_OR_STRANGE_PATTERN.match(w):
        return True
    if REPEATED_JAMO_PATTERN.search(w):
        return True
    return False


def main():
    if not INPUT_FILE.exists():
        print(f"❌ Input file not found: {INPUT_FILE}")
        return

    suspects = []

    with INPUT_FILE.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="|")
        for row in reader:
            word = row["word"].strip()
            if is_suspicious(word):
                suspects.append(row)

    # Save to output file
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["word", "source_book"], delimiter="|")
        writer.writeheader()
        writer.writerows(suspects)

    print(f"✅ Found {len(suspects)} suspicious entries.")
    print(f"🗂  Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
