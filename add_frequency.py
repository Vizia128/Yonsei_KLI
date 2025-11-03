import csv
import re

file_path = r"3급/deep_words.csv"
file_path_new = r"3급/words_wf_d.csv"

# Step 1: Load the frequency list
frequency_dict = {}
with open("frequency_list.csv", encoding="utf-8") as f:
    for idx, line in enumerate(f):
        word = line.strip()
        frequency_dict[word] = idx  # index as frequency rank

# Step 2: Process the vocab list and add frequency
updated_rows = []
with open(file_path, encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter="|")
    for row in reader:
        korean_word = row["Korean"]
        # Strip trailing numbers from the Korean word
        korean_word_cleaned = re.sub(r"\d+$", "", korean_word)
        frequency = frequency_dict.get(korean_word_cleaned, 30000)
        row["Frequency"] = frequency
        updated_rows.append(row)

# Step 3: Write the new CSV with the added Frequency column
fieldnames = list(updated_rows[0].keys())
with open(file_path_new, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="|")
    writer.writeheader()
    writer.writerows(updated_rows)

print(f"Done. Output saved to {file_path_new}")
