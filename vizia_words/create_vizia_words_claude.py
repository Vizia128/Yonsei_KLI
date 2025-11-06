import csv
import re
from pathlib import Path
from collections import deque, defaultdict


# =======================
#  NORMALIZATION HELPERS
# =======================


def parse_word_number(word):
    """
    Parse a word into (base, num).
    - '하다'    -> ('하다', None)
    - '하다1'   -> ('하다', 1)
    - '하다01'  -> ('하다', 1)
    - '하다02'  -> ('하다', 2)
    """
    m = re.match(r"^(.*?)(\d+)$", word)
    if not m:
        return (word, None)
    base, num_str = m.groups()
    num = int(num_str.lstrip("0") or "0")
    if num == 0:
        return (word, None)
    return (base, num)


def build_topik_based_normalization_map(topik_list):
    """
    Build normalization map based *only* on the TOPIK list.
    If TOPIK starts numbering at 02 or 03, that numbering is preserved.
    """
    base_to_nums = defaultdict(set)
    for item in topik_list:
        word = item["word"]
        base, num = parse_word_number(word)
        if num is not None:
            base_to_nums[base].add(num)

    normalization_map = {}

    # Build normalization for TOPIK itself
    for item in topik_list:
        w = item["word"]
        base, num = parse_word_number(w)
        if base in base_to_nums:
            if num is not None:
                normalization_map[w] = f"{base}{num}"
            else:
                # TOPIK has numbered versions but this one is unnumbered
                # If the lowest existing number > 1 (e.g. only 수2), match the lowest
                lowest = min(base_to_nums[base])
                normalization_map[w] = f"{base}{lowest}"
        else:
            normalization_map[w] = w

    return base_to_nums, normalization_map


def normalize_other_lists(other_lists, base_to_nums):
    """
    Normalize Kimchi/Yonsei words based on the numbering discovered in TOPIK.
    """
    normalization_map = {}
    for word_list in other_lists:
        for item in word_list:
            w = item["word"]
            base, num = parse_word_number(w)
            if base in base_to_nums:
                # Use the lowest number from TOPIK for unnumbered words
                lowest = min(base_to_nums[base])
                normalization_map[w] = f"{base}{num or lowest}"
            else:
                normalization_map[w] = w
    return normalization_map


def build_normalization_maps(kimchi_list, topik_list, yonsei_list):
    base_to_nums, topik_norm = build_topik_based_normalization_map(topik_list)
    other_norm = normalize_other_lists([kimchi_list, yonsei_list], base_to_nums)
    return {**topik_norm, **other_norm}


# =======================
#  CSV LOADERS
# =======================


def load_kimchi_words(filepath):
    words = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="|")
        for row in reader:
            words.append({"word": row["Word"].strip(), "rank": row["Rank"].strip()})
    return words


def load_topik_words(filepath):
    words = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="|")
        for row in reader:
            words.append(
                {
                    "word": row["단어"].strip(),
                    "pos": row["품사"].strip(),
                    "definition": row["풀이"].strip(),
                    "level": row["등급"].strip(),
                }
            )
    return words


def load_yonsei_words(filepath):
    words = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="|")
        for row in reader:
            words.append(
                {"word": row["word"].strip(), "book": row["source_book"].strip()}
            )
    return words


# =======================
#  LOOKUP + MERGE LOGIC
# =======================


def build_lookup_maps(kimchi_list, topik_list, yonsei_list, norm_map):
    kimchi_map, topik_map, yonsei_map = {}, {}, {}

    for item in kimchi_list:
        normalized = norm_map[item["word"]]
        kimchi_map.setdefault(normalized, item)

    for item in topik_list:
        normalized = norm_map[item["word"]]
        topik_map.setdefault(normalized, item)

    for item in yonsei_list:
        normalized = norm_map[item["word"]]
        yonsei_map.setdefault(normalized, item)

    return kimchi_map, topik_map, yonsei_map


def merge_vocabularies(kimchi_list, topik_list, yonsei_list, norm_map):
    master_list = []
    seen_normalized = set()

    kimchi = deque(kimchi_list)
    topik = deque(topik_list)
    yonsei = deque(yonsei_list)

    kimchi_map, topik_map, yonsei_map = build_lookup_maps(
        kimchi_list, topik_list, yonsei_list, norm_map
    )

    while yonsei:
        # Kimchi
        while kimchi:
            word_data = kimchi.popleft()
            normalized = norm_map[word_data["word"]]
            if normalized in seen_normalized:
                continue
            seen_normalized.add(normalized)

            topik_match = topik_map.get(normalized)
            yonsei_match = yonsei_map.get(normalized)

            master_list.append(
                {
                    "word": normalized,
                    "kimchi_rank": word_data["rank"],
                    "topik_pos": topik_match["pos"] if topik_match else "",
                    "topik_definition": (
                        topik_match["definition"] if topik_match else ""
                    ),
                    "topik_level": topik_match["level"] if topik_match else "",
                    "yonsei_book": yonsei_match["book"] if yonsei_match else "",
                }
            )
            break

        if not yonsei:
            break

        # TOPIK
        while topik:
            word_data = topik.popleft()
            normalized = norm_map[word_data["word"]]
            if normalized in seen_normalized:
                continue
            seen_normalized.add(normalized)

            kimchi_match = kimchi_map.get(normalized)
            yonsei_match = yonsei_map.get(normalized)

            master_list.append(
                {
                    "word": normalized,
                    "kimchi_rank": kimchi_match["rank"] if kimchi_match else "",
                    "topik_pos": word_data["pos"],
                    "topik_definition": word_data["definition"],
                    "topik_level": word_data["level"],
                    "yonsei_book": yonsei_match["book"] if yonsei_match else "",
                }
            )
            break

        if not yonsei:
            break

        # Yonsei
        while yonsei:
            word_data = yonsei.popleft()
            normalized = norm_map[word_data["word"]]
            if normalized in seen_normalized:
                continue
            seen_normalized.add(normalized)

            kimchi_match = kimchi_map.get(normalized)
            topik_match = topik_map.get(normalized)

            master_list.append(
                {
                    "word": normalized,
                    "kimchi_rank": kimchi_match["rank"] if kimchi_match else "",
                    "topik_pos": topik_match["pos"] if topik_match else "",
                    "topik_definition": (
                        topik_match["definition"] if topik_match else ""
                    ),
                    "topik_level": topik_match["level"] if topik_match else "",
                    "yonsei_book": word_data["book"],
                }
            )
            break

    return master_list


# =======================
#  OUTPUT
# =======================


def write_master_vocabulary(master_list, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "Word",
            "Kimchi Rank",
            "TOPIK POS",
            "TOPIK Definition",
            "TOPIK Level",
            "Yonsei Book",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="|")
        writer.writeheader()

        for entry in master_list:
            writer.writerow(
                {
                    "Word": entry["word"],
                    "Kimchi Rank": entry["kimchi_rank"],
                    "TOPIK POS": entry["topik_pos"],
                    "TOPIK Definition": entry["topik_definition"],
                    "TOPIK Level": entry["topik_level"],
                    "Yonsei Book": entry["yonsei_book"],
                }
            )


# =======================
#  MAIN
# =======================


def main():
    base_path = Path("vizia_words")
    kimchi_path = base_path / "kimchi_words.csv"
    topik_path = base_path / "topik_words.csv"
    yonsei_path = base_path / "yonsei_words.csv"
    output_path = base_path / "vizia_words.csv"

    print("Loading vocabulary lists...")
    kimchi_words = load_kimchi_words(kimchi_path)
    topik_words = load_topik_words(topik_path)
    yonsei_words = load_yonsei_words(yonsei_path)

    print(f"Loaded {len(kimchi_words)} Kimchi words")
    print(f"Loaded {len(topik_words)} TOPIK words")
    print(f"Loaded {len(yonsei_words)} Yonsei words")

    print("\nBuilding TOPIK-based normalization map...")
    norm_map = build_normalization_maps(kimchi_words, topik_words, yonsei_words)

    print("Merging vocabularies using round-robin method...")
    master_list = merge_vocabularies(kimchi_words, topik_words, yonsei_words, norm_map)

    print(f"\nWriting {len(master_list)} unique words to {output_path}")
    write_master_vocabulary(master_list, output_path)
    print("Done!")


if __name__ == "__main__":
    main()
