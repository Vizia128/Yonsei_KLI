import sys

def main():
    input_file = r"c:\Users\julia\OneDrive\Documents\Yonsei_KLI\topik\topik_words_rich.csv"
    output_file = r"c:\Users\julia\OneDrive\Documents\Yonsei_KLI\topik\my_topik_words.csv"
    
    with open(input_file, "r", encoding="utf-8") as fin, open(output_file, "w", encoding="utf-8", newline="") as fout:
        new_idx = 1
        for line in fin:
            if line.startswith("|"):
                parts = line.split("|")
                if len(parts) > 2:
                    parts[1] = str(new_idx)
                    new_idx += 1
                fout.write("|".join(parts))

if __name__ == "__main__":
    main()
