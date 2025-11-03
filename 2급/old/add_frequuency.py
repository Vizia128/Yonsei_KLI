import csv

# Step 1: Load the frequency list
frequency_dict = {}
with open('frequency_list.csv', encoding='utf-8') as f:
    for idx, line in enumerate(f):
        word = line.strip()
        frequency_dict[word] = idx  # index as frequency rank

# Step 2: Process the vocab list and add frequency
updated_rows = []
with open('2급단어.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter='|')
    for row in reader:
        korean_word = row['Korean']
        frequency = frequency_dict.get(korean_word, -1)
        row['Frequency'] = frequency
        updated_rows.append(row)

# Step 3: Write the new CSV with the added Frequency column
fieldnames = ['Index', 'Korean', 'English', 'Frequency']
with open('2급단어_with_frequency.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='|')
    writer.writeheader()
    writer.writerows(updated_rows)

print("✅ Done. Output saved to '2급단어_with_frequency.csv'")
