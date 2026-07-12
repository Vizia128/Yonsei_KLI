import anthropic
import csv
import time
import json
from pathlib import Path
from typing import List, Dict, Optional
import os

# ===========================
# 🧠 SYSTEM PROMPT (cached)
# ===========================
SYSTEM_PROMPT = """You are a Korean language expert creating vocabulary learning materials. Your task is to provide English translations and practical example phrases for Korean words.

# Input Format
You will receive Korean vocabulary entries in this format:
Word|TOPIK POS|TOPIK Definition

Where:
- Word: The Korean word or phrase
- TOPIK POS: Part of speech (명=noun, 동=verb, 형=adjective, 부=adverb, 의=dependent noun, 대=pronoun, 조=particle, etc.)
- TOPIK Definition: May be Korean definition, English word, Chinese characters, or empty

# Output Format
Return EXACTLY ONE LINE per input entry, formatted as:
Word|English|Korean Chunk 1|English Chunk 1|Korean Chunk 2|English Chunk 2

# Guidelines

## English Translation
- Provide the most common, natural English equivalent
- For verbs: use infinitive form with "to" (e.g., "to kick", "to respect")
- For adjectives: use infinitive form "to be X" (e.g., "to be peaceful")
- For nouns: provide simple translation (e.g., "theater", "energy")
- Keep it concise (typically 1-4 words)

## Korean Chunks (Example Phrases)
Create TWO practical example phrases that:
1. Are natural collocations (phrases Korean speakers actually use)
2. Show different contexts
3. Are short (2-5 words)
4. Are useful for learners
5. Are grammatically correct

## English Chunk Translations
- Translate chunks naturally and idiomatically
- Keep concise and learner-friendly

# Examples

Input: 평화롭다|형||
Output: 평화롭다|to be peaceful|평화로운 마을|peaceful village|평화롭게 지내다|to live peacefully

Input: 상영관|명||
Output: 상영관|theater|영화 상영관|movie theater|상영관을 선택하다|to choose a theater

Input: 결국|부||
Output: 결국|ultimately|결국 성공했다|ultimately succeeded|결국 포기했어요|I gave up in the end

Input: 노약자|명||
Output: 노약자|the old and weak|노약자 좌석|seats for the elderly and weak|노약자를 배려하다|to be considerate of the elderly and weak

Input: 맞다1|동|답이 ~
Output: 맞다1|to be correct|답이 맞다|the answer is correct|맞는 말|correct words

Input: 맞다2|동|손님을 ~
Output: 맞다2|to greet|손님을 맞다|to greet a guest|공항에서 맞다|to meet at the airport

Input: 맞다3|동|매를 ~
Output: 맞다3|to be hit|매를 맞다|to be beaten|비를 맞다|to get rained on

# Important
- Output only pipe-separated values (no extra text, explanations, or numbering)
- Ensure each line corresponds to exactly one input word
"""

# ===========================
# 🔧 CLASS IMPLEMENTATION
# ===========================


class VocabularyProcessor:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the vocabulary processor with Anthropic API."""
        self.client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )
        self.system_prompt = SYSTEM_PROMPT

    def create_batch_request(self, words_batch: List[Dict]) -> str:
        """Create a batch request message for multiple words."""
        user_message = (
            "Process these vocabulary entries (one per line):\n\n"
            "Return one line per word in this format:\n"
            "Word|English|Korean Chunk 1|English Chunk 1|Korean Chunk 2|English Chunk 2\n\n"
            "Entries:\n\n"
        )
        for word_data in words_batch:
            word = word_data["Word"]
            pos = word_data["TOPIK POS"]
            definition = word_data.get("TOPIK Definition", "")
            user_message += f"{word}|{pos}|{definition}\n"
        return user_message.strip()

    def parse_batch_response(
        self, response_text: str, batch: List[Dict]
    ) -> List[Optional[Dict]]:
        """Parse the batch response into individual results using echoed Word matching."""
        lines = [line.strip() for line in response_text.splitlines() if line.strip()]
        results = [None] * len(batch)

        word_to_indices = {}
        for idx, item in enumerate(batch):
            word_text = item["Word"]
            word_to_indices.setdefault(word_text, []).append(idx)

        used_indices = set()

        for line in lines:
            parts = [part.strip() for part in line.split("|")]
            if len(parts) < 6:
                print(f"Warning: Skipped malformed line (too few fields): {line}")
                continue

            word = parts[0]
            # Check for "empty between pipes" case like 아침을|||||
            if all(not part for part in parts[1:]):
                print(f"⚠️ Empty output for word: {word}")
                continue

            if word not in word_to_indices:
                print(f"Warning: Unknown word in output: {word}")
                continue

            target_idx = None
            for i in word_to_indices[word]:
                if i not in used_indices:
                    target_idx = i
                    break
            if target_idx is None:
                continue

            results[target_idx] = {
                "korean": word,
                "english": parts[1],
                "korean_chunk_1": parts[2],
                "english_chunk_1": parts[3],
                "korean_chunk_2": parts[4],
                "english_chunk_2": parts[5],
            }
            used_indices.add(target_idx)

        return results

    def process_batch(
        self, words_batch: List[Dict], retry_count: int = 3
    ) -> List[Optional[Dict]]:
        """Send one batch to the API and parse the result."""
        user_message = self.create_batch_request(words_batch)

        for attempt in range(retry_count):
            try:
                response = self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=3000,
                    temperature=0,
                    system=[
                        {
                            "type": "text",
                            "text": self.system_prompt,
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                    messages=[{"role": "user", "content": user_message}],
                )

                response_text = response.content[0].text
                results = self.parse_batch_response(response_text, words_batch)

                usage = response.usage
                print(
                    f"  Tokens - Input: {usage.input_tokens}, "
                    f"Cache creation: {getattr(usage, 'cache_creation_input_tokens', 0)}, "
                    f"Cache read: {getattr(usage, 'cache_read_input_tokens', 0)}, "
                    f"Output: {usage.output_tokens}"
                )
                return results

            except Exception as e:
                print(f"  Attempt {attempt + 1} failed: {e}")
                if attempt < retry_count - 1:
                    time.sleep(2**attempt)
                else:
                    print(f"  Failed after {retry_count} attempts")
                    return [None] * len(words_batch)

    def append_results_to_csv(self, output_file: str, results: List[Dict]):
        """Append results to CSV file (creates file with header if it doesn't exist)."""
        output_path = Path(output_file)
        file_exists = output_path.exists()

        fieldnames = [
            "Korean",
            "English",
            "Korean Chunk 1",
            "English Chunk 1",
            "Korean Chunk 2",
            "English Chunk 2",
        ]

        with open(output_path, "a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="|")

            # Write header if file is new
            if not file_exists:
                writer.writeheader()

            # Write all results
            for result in results:
                writer.writerow(
                    {
                        "Korean": result["korean"],
                        "English": result["english"],
                        "Korean Chunk 1": result["korean_chunk_1"],
                        "English Chunk 1": result["english_chunk_1"],
                        "Korean Chunk 2": result["korean_chunk_2"],
                        "English Chunk 2": result["english_chunk_2"],
                    }
                )

    def process_file(
        self,
        input_file: str,
        output_file: str,
        batch_size: int = 25,
        test_range: Optional[tuple] = None,
    ):
        """Process the entire vocabulary CSV file in batches."""
        input_path = Path(input_file)
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"Reading input file: {input_file}")
        with open(input_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="|")
            rows = list(reader)

        if test_range is not None:
            start, end = test_range
            original_count = len(rows)
            rows = rows[start:end]
            print(f"TEST MODE: rows {start}-{end} ({len(rows)} of {original_count})")
        else:
            print(f"Found {len(rows)} vocabulary entries")

        print(f"Processing in batches of {batch_size}...\n")

        total_processed = 0
        total_failed = 0
        failed_words = []
        malformed_batch = []

        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            if malformed_batch:
                print(
                    f"Retrying {len(malformed_batch)} malformed entries from last batch..."
                )
                batch = malformed_batch + batch
                malformed_batch = []

            batch_num = i // batch_size + 1
            total_batches = (len(rows) + batch_size - 1) // batch_size
            print(
                f"Processing batch {batch_num}/{total_batches} ({i+1}-{min(i+batch_size, len(rows))})"
            )

            results = self.process_batch(batch)

            # Separate successful and failed results
            successful_results = []
            for j, result in enumerate(results):
                if result and all(result.values()):
                    successful_results.append(result)
                else:
                    malformed_batch.append(batch[j])
                    failed_words.append(batch[j]["Word"])

            # Write successful results immediately
            if successful_results:
                self.append_results_to_csv(output_file, successful_results)
                total_processed += len(successful_results)
                print(f"  ✓ Written {len(successful_results)} entries to {output_file}")

            total_failed = len(failed_words)
            print(f"  Progress: {total_processed} processed, {total_failed} failed")

            if i + batch_size < len(rows):
                time.sleep(1)

        # retry final malformed batch once
        if malformed_batch:
            print(f"\nFinal retry for {len(malformed_batch)} malformed lines...")
            results = self.process_batch(malformed_batch)
            successful_results = []
            for r in results:
                if r and all(r.values()):
                    successful_results.append(r)

            if successful_results:
                self.append_results_to_csv(output_file, successful_results)
                total_processed += len(successful_results)
                print(f"  ✓ Written {len(successful_results)} entries from final retry")

        print(f"\n{'='*60}")
        print("Processing Complete!")
        print(f"{'='*60}")
        print(f"Successfully processed: {total_processed}/{len(rows)} entries")
        print(f"Failed: {len(failed_words)} entries")

        if failed_words:
            print(f"\nFailed words: {', '.join(failed_words[:10])}")
            if len(failed_words) > 10:
                print(f"... and {len(failed_words) - 10} more")

        print(f"\nOutput saved to: {output_file}")


# ===========================
# 🚀 MAIN
# ===========================


def main():
    INPUT_FILE = "vizia_words.csv"
    OUTPUT_FILE = "vizia_words_enhanced.csv"
    BATCH_SIZE = 25
    # TEST_RANGE = (0, 1000)  # set to None for full run
    TEST_RANGE = None

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set.")
        print("Set it using:  set ANTHROPIC_API_KEY=your-key")
        return

    processor = VocabularyProcessor(api_key)
    processor.process_file(INPUT_FILE, OUTPUT_FILE, BATCH_SIZE, test_range=TEST_RANGE)


if __name__ == "__main__":
    main()
