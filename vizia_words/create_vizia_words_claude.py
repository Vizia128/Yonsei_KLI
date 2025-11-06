import csv
import re
from pathlib import Path
from collections import deque, defaultdict


def parse_word_number(word):
    """
    Parse word into base and number.
    Examples:
    - '하다' -> ('하다', None)
    - '하다1' -> ('하다', 1)
    - '하다01' -> ('하다', 1)
    - '하다02' -> ('하다', 2)
    """
    match = re.match(r"^(.*?)0*(\d+)$", word)
    if match:
        base, num = match.groups()
        if num == "1":
            return (word, None)  # treat as unnumbered
        return (base, int(num))
    return (word, None)


def normalize_word(word):
    """
    Normalize word to standard form.
    - '하다', '하다1', '하다01' all become '하다1'
    - '하다2', '하다02' both become '하다2'
    - '스케이트' stays '스케이트'
    """
    base, num = parse_word_number(word)
    if num is None:
        # Check if this is truly standalone or should be treated as #1
        # We'll handle this in the grouping phase
        return word
    return f"{base}{num}"


def group_words_by_base(word_list):
    """
    Group words by their base form to determine which should be numbered.
    Returns a mapping from original word to normalized form.
    """
    # First pass: collect all words by base
    base_groups = defaultdict(list)
    for item in word_list:
        word = item["word"]
        base, num = parse_word_number(word)
        base_groups[base].append((word, num))

    # Second pass: determine normalization
    normalization_map = {}
    for base, words in base_groups.items():
        nums = [num for _, num in words if num is not None]

        if nums:  # If any numbered version exists
            # All versions of this base should be numbered
            for word, num in words:
                if num is None:
                    normalization_map[word] = f"{base}1"
                else:
                    normalization_map[word] = f"{base}{num}"
        else:
            # No numbered versions, keep as-is
            for word, _ in words:
                normalization_map[word] = word

    return normalization_map


def load_kimchi_words(filepath):
    """Load kimchi_words.csv and return list of dicts."""
    words = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="|")
        for row in reader:
            words.append({"word": row["Word"].strip(), "rank": row["Rank"].strip()})
    return words


def load_topik_words(filepath):
    """Load topik_words.csv and return list of dicts."""
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
    """Load yonsei_words.csv and return list of dicts."""
    words = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="|")
        for row in reader:
            words.append(
                {"word": row["word"].strip(), "book": row["source_book"].strip()}
            )
    return words


def build_normalization_maps(kimchi_list, topik_list, yonsei_list):
    """Build normalization maps for each list."""
    all_words = kimchi_list + topik_list + yonsei_list
    return group_words_by_base(all_words)


def build_lookup_maps(kimchi_list, topik_list, yonsei_list, norm_map):
    """Build hash maps for O(1) lookups by normalized word."""
    kimchi_map = {}
    topik_map = {}
    yonsei_map = {}

    for item in kimchi_list:
        normalized = norm_map[item["word"]]
        if normalized not in kimchi_map:
            kimchi_map[normalized] = item

    for item in topik_list:
        normalized = norm_map[item["word"]]
        if normalized not in topik_map:
            topik_map[normalized] = item

    for item in yonsei_list:
        normalized = norm_map[item["word"]]
        if normalized not in yonsei_map:
            yonsei_map[normalized] = item

    return kimchi_map, topik_map, yonsei_map


def merge_vocabularies(kimchi_list, topik_list, yonsei_list, norm_map):
    """
    Merge three vocabulary lists using round-robin selection.
    Stop when Yonsei list is exhausted.
    """
    master_list = []
    seen_normalized = set()

    # Use deques for O(1) pop from front
    kimchi = deque(kimchi_list)
    topik = deque(topik_list)
    yonsei = deque(yonsei_list)

    # Build lookup maps for O(1) access
    kimchi_map, topik_map, yonsei_map = build_lookup_maps(
        kimchi_list, topik_list, yonsei_list, norm_map
    )

    # Round-robin: Kimchi -> TOPIK -> Yonsei
    while yonsei:
        # 1. Try Kimchi
        while kimchi:
            word_data = kimchi.popleft()
            normalized = norm_map[word_data["word"]]

            if normalized not in seen_normalized:
                seen_normalized.add(normalized)

                # O(1) lookups in maps
                topik_match = topik_map.get(normalized)
                yonsei_match = yonsei_map.get(normalized)

                # Add to master list using the first-seen form
                master_list.append(
                    {
                        "word": word_data["word"],
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

        # 2. Try TOPIK
        while topik:
            word_data = topik.popleft()
            normalized = norm_map[word_data["word"]]

            if normalized not in seen_normalized:
                seen_normalized.add(normalized)

                # O(1) lookups
                kimchi_match = kimchi_map.get(normalized)
                yonsei_match = yonsei_map.get(normalized)

                # Add to master list
                master_list.append(
                    {
                        "word": word_data["word"],
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

        # 3. Try Yonsei (this determines when to stop)
        while yonsei:
            word_data = yonsei.popleft()
            normalized = norm_map[word_data["word"]]

            if normalized not in seen_normalized:
                seen_normalized.add(normalized)

                # O(1) lookups
                kimchi_match = kimchi_map.get(normalized)
                topik_match = topik_map.get(normalized)

                # Add to master list
                master_list.append(
                    {
                        "word": word_data["word"],
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


def write_master_vocabulary(master_list, output_path):
    """Write the master vocabulary list to CSV with pipe delimiter."""
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


def main():
    # Define input file paths
    base_path = Path("vizia_words")
    kimchi_path = base_path / "kimchi_words.csv"
    topik_path = base_path / "topik_words.csv"
    yonsei_path = base_path / "yonsei_words.csv"
    output_path = base_path / "vizia_words.csv"

    # Load all vocabulary lists
    print("Loading vocabulary lists...")
    kimchi_words = load_kimchi_words(kimchi_path)
    topik_words = load_topik_words(topik_path)
    yonsei_words = load_yonsei_words(yonsei_path)

    print(f"Loaded {len(kimchi_words)} Kimchi words")
    print(f"Loaded {len(topik_words)} TOPIK words")
    print(f"Loaded {len(yonsei_words)} Yonsei words")

    # Build normalization map
    print("\nBuilding normalization map...")
    norm_map = build_normalization_maps(kimchi_words, topik_words, yonsei_words)

    # Merge vocabularies
    print("Merging vocabularies using round-robin method...")
    master_list = merge_vocabularies(kimchi_words, topik_words, yonsei_words, norm_map)

    # Write output
    print(f"\nWriting {len(master_list)} unique words to {output_path}")
    write_master_vocabulary(master_list, output_path)

    print("Done!")


if __name__ == "__main__":
    main()
