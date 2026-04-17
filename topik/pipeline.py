# /// script
# requires-python = "==3.12.*"
# dependencies = [
#     "qwen-tts",
#     "soundfile",
#     "flash-attn",
#     "torch @ https://download.pytorch.org/whl/cu121/torch-2.5.1%2Bcu121-cp312-cp312-linux_x86_64.whl",
#     "torchvision @ https://download.pytorch.org/whl/cu121/torchvision-0.20.1%2Bcu121-cp312-cp312-linux_x86_64.whl",
#     "torchaudio @ https://download.pytorch.org/whl/cu121/torchaudio-2.5.1%2Bcu121-cp312-cp312-linux_x86_64.whl",
# ]
#
# [tool.uv]
# no-build-isolation-package = ["flash-attn"]
# ///
"""
TOPIK Anki Pipeline
===================
Single-call pipeline:
  1. Filter & reindex topik_words_rich.csv → my_topik_words.csv
     (keeps only rows with a non-empty first column)
  2. Generate TTS audio for any rows that don't yet have audio files
     → my_topik_words_with_audio.csv
  3. Convert to Anki TSV format → my_topik_words_anki.tsv

Usage (from project root):
    uv run topik/pipeline.py

    # override default paths:
    uv run topik/pipeline.py \\
        --rich   topik/topik_words_rich.csv \\
        --words  topik/my_topik_words.csv \\
        --audio-dir topik/audio \\
        --anki   topik/my_topik_words_anki.tsv
"""
import argparse
import csv
import os
import re
import sys
import traceback


# ---------------------------------------------------------------------------
# Step 1 — filter & reindex
# ---------------------------------------------------------------------------

def step_filter_reindex(rich_path: str, words_path: str) -> int:
    """Read rich CSV, keep indexed rows, reindex from 1, write words CSV."""
    print(f"[1/3] Filtering {rich_path} → {words_path}")
    rows = []
    with open(rich_path, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="|")
        for row in reader:
            if row and row[0].strip():
                rows.append(row)

    temp = words_path + ".tmp"
    with open(temp, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="|")
        for new_idx, row in enumerate(rows, start=1):
            row[0] = str(new_idx)
            writer.writerow(row)

    if os.path.exists(words_path):
        os.remove(words_path)
    os.rename(temp, words_path)

    print(f"    → {len(rows)} words written.")
    return len(rows)


# ---------------------------------------------------------------------------
# Step 2 — audio generation
# ---------------------------------------------------------------------------

def _audio_paths_for_row(row_num: int, audio_dir: str) -> list[str]:
    """Return the 3 expected audio file paths for a given 1-based row number."""
    return [
        os.path.join(audio_dir, f"row{row_num}_chunk{chunk}.wav")
        for chunk in (1, 2, 3)
    ]


def _all_audio_exist(row_num: int, audio_dir: str) -> bool:
    return all(os.path.exists(p) for p in _audio_paths_for_row(row_num, audio_dir))


def step_generate_audio(words_path: str, audio_csv_path: str, audio_dir: str) -> None:
    """Generate missing audio files and write the with-audio CSV."""
    print(f"[2/3] Generating audio  {words_path} → {audio_csv_path}")
    os.makedirs(audio_dir, exist_ok=True)

    # Read all rows up front so we know which need audio before loading the model.
    with open(words_path, encoding="utf-8") as f:
        rows = list(csv.reader(f, delimiter="|"))

    needs_audio = [
        (row_num, row)
        for row_num, row in enumerate(rows, start=1)
        if not _all_audio_exist(row_num, audio_dir)
    ]

    if needs_audio:
        print(f"    {len(needs_audio)} rows need audio; loading Qwen3-TTS model…")
        import torch
        import soundfile as sf
        from qwen_tts import Qwen3TTSModel

        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        try:
            import flash_attn  # noqa: F401
            attn = "flash_attention_2" if torch.cuda.is_available() else "eager"
        except ImportError:
            attn = "eager"

        model = Qwen3TTSModel.from_pretrained(
            "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
            device_map=device,
            dtype=dtype,
            attn_implementation=attn,
        )
        print("    Model loaded.")
    else:
        model = None
        sf = None
        print("    All audio files already exist — skipping model load.")

    SPEAKERS = ["sohee", "aiden", "vivian"]
    CHUNK_COLS = [7, 9, 11]  # Korean example sentence columns in my_topik_words.csv

    temp = audio_csv_path + ".tmp"
    with open(temp, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.writer(f_out, delimiter="|")

        for row_num, row in enumerate(rows, start=1):
            if len(row) < 13:
                writer.writerow(row)
                f_out.flush()
                continue

            audio_rel_paths = []
            for chunk_idx, col_idx in enumerate(CHUNK_COLS):
                wav_path = os.path.join(audio_dir, f"row{row_num}_chunk{chunk_idx + 1}.wav")
                rel_path = f"audio/row{row_num}_chunk{chunk_idx + 1}.wav"

                if os.path.exists(wav_path):
                    audio_rel_paths.append(rel_path)
                    continue

                text = row[col_idx].replace("*", "").strip()
                if not text:
                    audio_rel_paths.append("")
                    continue

                speaker = SPEAKERS[chunk_idx % len(SPEAKERS)]
                print(f"    row {row_num} chunk {chunk_idx + 1}: '{text}' [{speaker}]")
                try:
                    wavs, sr = model.generate_custom_voice(
                        text=text, language="Korean", speaker=speaker
                    )
                    sf.write(wav_path, wavs[0], sr)
                    audio_rel_paths.append(rel_path)
                except Exception as e:
                    print(f"    ERROR row {row_num} chunk {chunk_idx + 1}: {e}")
                    traceback.print_exc()
                    audio_rel_paths.append("")

            writer.writerow(row[:13] + audio_rel_paths)
            f_out.flush()

    if os.path.exists(audio_csv_path):
        os.remove(audio_csv_path)
    os.rename(temp, audio_csv_path)
    print(f"    → {audio_csv_path} written.")


# ---------------------------------------------------------------------------
# Step 3 — Anki conversion
# ---------------------------------------------------------------------------

def _clean_korean_word(word: str) -> str:
    return re.sub(r"\d+$", "", word.strip())


def step_convert_anki(audio_csv_path: str, anki_tsv_path: str, anki_csv_path: str) -> int:
    """Convert with-audio CSV to Anki TSV (no index) and CSV (with index)."""
    print(f"[3/3] Converting {audio_csv_path} → {anki_tsv_path} + {anki_csv_path}")
    count = 0
    with open(audio_csv_path, encoding="utf-8") as f_in, \
         open(anki_tsv_path, "w", encoding="utf-8", newline="") as f_tsv, \
         open(anki_csv_path, "w", encoding="utf-8", newline="") as f_csv:

        reader = csv.reader(f_in, delimiter="|")
        tsv_writer = csv.writer(f_tsv, delimiter="\t", lineterminator="\n")
        csv_writer = csv.writer(f_csv, delimiter="\t", lineterminator="\n")

        for row in reader:
            if not row or len(row) < 16:
                continue
            count += 1
            word_kor = _clean_korean_word(row[2])
            word_eng = row[6].strip()
            chunks_kor = f"{row[7].strip()}|{row[9].strip()}|{row[11].strip()}"
            chunks_eng = f"{row[8].strip()}|{row[10].strip()}|{row[12].strip()}"
            chunks_audio = "|".join(
                f"[sound:{os.path.basename(row[i].strip())}]"
                for i in (13, 14, 15)
            )
            anki_row = [word_kor, word_eng, chunks_kor, chunks_eng, chunks_audio]
            tsv_writer.writerow(anki_row)
            csv_writer.writerow([count] + anki_row)

    print(f"    → {count} Anki rows written.")
    return count


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="TOPIK → Anki pipeline: filter, generate audio, convert."
    )
    parser.add_argument(
        "--rich", default="topik/topik_words_rich.csv",
        help="Source vocabulary CSV with user-selected index in col 0"
    )
    parser.add_argument(
        "--words", default="topik/my_topik_words.csv",
        help="Filtered & reindexed output"
    )
    parser.add_argument(
        "--audio-csv", default="topik/my_topik_words_with_audio.csv",
        help="Intermediate CSV with audio paths appended"
    )
    parser.add_argument(
        "--audio-dir", default="topik/audio",
        help="Directory for generated WAV files"
    )
    parser.add_argument(
        "--anki", default="topik/my_topik_words_anki.tsv",
        help="Final Anki TSV output"
    )
    parser.add_argument(
        "--anki-csv", default="topik/my_topik_words_anki.csv",
        help="Final Anki CSV output (with sequential index as first column)"
    )
    args = parser.parse_args()

    step_filter_reindex(args.rich, args.words)
    step_generate_audio(args.words, args.audio_csv, args.audio_dir)
    step_convert_anki(args.audio_csv, args.anki, args.anki_csv)

    print("\nDone! Import", args.anki, "into Anki.")


if __name__ == "__main__":
    main()
