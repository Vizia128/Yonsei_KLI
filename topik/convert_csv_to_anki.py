import csv
import re
from pathlib import Path

def clean_korean_word(word):
    """Remove trailing dictionary numbers (e.g., 이런01 -> 이런)."""
    return re.sub(r'\d+$', '', word)

def main():
    script_dir = Path(__file__).parent
    input_file = script_dir / 'my_topik_words_with_audio.csv'
    output_file = script_dir / 'my_topik_words_anki.tsv'

    with open(input_file, mode='r', encoding='utf-8') as infile, \
         open(output_file, mode='w', encoding='utf-8', newline='') as outfile:
        
        reader = csv.reader(infile, delimiter='|')
        writer = csv.writer(outfile, delimiter='\t', lineterminator='\n')
        
        count = 0
        for row in reader:
            if not row or len(row) < 16:
                continue
                
            word_korean = clean_korean_word(row[2].strip())
            word_english = row[6].strip()
            
            chunks_korean = f"{row[7].strip()}|{row[9].strip()}|{row[11].strip()}"
            chunks_english = f"{row[8].strip()}|{row[10].strip()}|{row[12].strip()}"
            chunks_audio = f"[sound:{row[13].strip()}]|[sound:{row[14].strip()}]|[sound:{row[15].strip()}]"
            
            writer.writerow([word_korean, word_english, chunks_korean, chunks_english, chunks_audio])
            count += 1
            
    print(f"Successfully converted {count} rows from {input_file.name} to {output_file.name}")

if __name__ == "__main__":
    main()
