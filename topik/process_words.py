import sys

def main():
    input_file = r"c:\Users\julia\OneDrive\Documents\Yonsei_KLI\topik\topik_words_rich.csv"
    output_file = r"c:\Users\julia\OneDrive\Documents\Yonsei_KLI\topik\my_topik_words.csv"
    
    with open(input_file, "r", encoding="utf-8") as fin, open(output_file, "w", encoding="utf-8", newline="") as fout:
        new_idx = 1
        for line in fin:
            # We want to keep lines that start with a digit
            if line and line[0].isdigit():
                parts = line.split("|")
                # Replace the first number with our new index
                parts[0] = str(new_idx)
                fout.write("|".join(parts))
                new_idx += 1

if __name__ == "__main__":
    main()
