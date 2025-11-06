import csv
import re
from pathlib import Path

# ==============================
# 🔧 Configuration
# ==============================
KIMCHI_PATH = Path("vizia_words/kimchi_words.csv")
TOPIK_PATH = Path("vizia_words/topik_words.csv")
YONSEI_PATH = Path("vizia_words/yonsei_words.csv")
OUTPUT_PATH = Path("master_vocabulary.csv")

DELIMITER = "|"


# ==============================
# 🧠 Helper Functions
# ==============================
def normalize(word: str) -> str:
    """
    Normalize Korean words by removing numeric suffixes such as 01, 1, etc.
    Example:
      '하다01' → '하다'
      '하다1'  → '하다'
      '하다2'  → '하다2' (kept since it's a different group)
    """
    word = word.strip()
    # If the number represents the first variant, strip it; otherwise, keep
    m = re.match(r"^([가-힣]+)(0?1)?$", word)
    if m:
        return m.group(1)
    # Keep any other numeric suffix (e.g., 하다2)
    return re.sub(r"0*(?=\d+$)", "", word)  # normalize trailing numbers


# ==============================
# 📥 Load CSVs
# ==============================
def load_kimchi():
    words = []
    with open(KIMCHI_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=DELIMITER)
        for row in reader:
            words.append(
                {
                    "Word": row["Word"].strip(),
                    "Kimchi Rank": row["Rank"].strip(),
                }
            )
    return words


def load_topik():
    words = []
    with open(TOPIK_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=DELIMITER)
        for row in reader:
            words.append(
                {
                    "Word": row["단어"].strip(),
                    "TOPIK POS": row["품사"].strip(),
                    "TOPIK Definition": row["풀이"].strip(),
                    "TOPIK Level": row["등급"].strip(),
                }
            )
    return words


def load_yonsei():
    words = []
    with open(YONSEI_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=DELIMITER)
        for row in reader:
            words.append(
                {
                    "Word": row["word"].strip(),
                    "Yonsei Book": row["source_book"].strip(),
                }
            )
    return words


# ==============================
# 🔁 Round-Robin Merge
# ==============================
def round_robin_merge(kimchi, topik, yonsei):
    master = []
    seen = set()  # normalized forms
    sources = [kimchi, topik, yonsei]
    source_names = ["Kimchi", "TOPIK", "Yonsei"]

    idx = [0, 0, 0]  # position in each list
    source_count = len(sources)
    turn = 0  # 0=Kimchi, 1=TOPIK, 2=Yonsei

    while idx[2] < len(yonsei):  # stop when Yonsei is fully consumed
        current_list = sources[turn]
        i = idx[turn]

        if i < len(current_list):
            entry = current_list[i]
            word = entry["Word"]
            base = normalize(word)

            # If not seen before, add it
            if base not in seen:
                # Create blank template row
                row = {
                    "Word": word,
                    "Kimchi Rank": "",
                    "TOPIK POS": "",
                    "TOPIK Definition": "",
                    "TOPIK Level": "",
                    "Yonsei Book": "",
                }

                # Merge metadata from all sources
                for src in [kimchi, topik, yonsei]:
                    for w in src:
                        if normalize(w["Word"]) == base:
                            row.update({k: v for k, v in w.items() if k in row})

                master.append(row)
                seen.add(base)

                # Remove duplicates from all lists
                for src_i in range(source_count):
                    sources[src_i] = [
                        w for w in sources[src_i] if normalize(w["Word"]) != base
                    ]

                # Reset indexes because list lengths changed
                idx = [min(i, len(sources[j])) for j, i in enumerate(idx)]

        # Advance the turn and index
        idx[turn] += 1
        turn = (turn + 1) % source_count

    return master


# ==============================
# 💾 Write Output
# ==============================
def write_master(master):
    fieldnames = [
        "Word",
        "Kimchi Rank",
        "TOPIK POS",
        "TOPIK Definition",
        "TOPIK Level",
        "Yonsei Book",
    ]

    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=DELIMITER)
        writer.writeheader()
        for row in master:
            writer.writerow(row)


# ==============================
# 🚀 Main
# ==============================
def main():
    kimchi = load_kimchi()
    topik = load_topik()
    yonsei = load_yonsei()

    master = round_robin_merge(kimchi, topik, yonsei)
    write_master(master)
    print(f"✅ Master vocabulary written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
