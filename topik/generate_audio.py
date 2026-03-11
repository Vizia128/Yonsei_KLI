# /// script
# requires-python = "==3.12.*"
# dependencies = [
#     "qwen-tts",
#     "soundfile",
#     "torch @ https://download.pytorch.org/whl/cu121/torch-2.5.1%2Bcu121-cp312-cp312-win_amd64.whl",
#     "torchvision @ https://download.pytorch.org/whl/cu121/torchvision-0.20.1%2Bcu121-cp312-cp312-win_amd64.whl",
#     "torchaudio @ https://download.pytorch.org/whl/cu121/torchaudio-2.5.1%2Bcu121-cp312-cp312-win_amd64.whl",
# ]
# ///
import os
import csv
import torch
import soundfile as sf
from qwen_tts import Qwen3TTSModel
import argparse

def clean_chunk(chunk: str) -> str:
    """Removes '*' from a chunk string."""
    return chunk.replace("*", "")

def main():
    parser = argparse.ArgumentParser(description="Generate audio files for Korean chunks in a CSV using Qwen3-TTS.")
    parser.add_argument("--input", default="topik/my_topik_words.csv", help="Path to input CSV file")
    parser.add_argument("--output", default="topik/my_topik_words_with_audio.csv", help="Path to output CSV file")
    parser.add_argument("--audio-dir", default="topik/audio", help="Directory to save audio files")
    args = parser.parse_args()

    # Create audio directory if it doesn't exist
    os.makedirs(args.audio_dir, exist_ok=True)

    # Initialize model
    print("Loading Qwen3-TTS model...")
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    # Using float16 if flash_attention_2 is not natively supported or if running on consumer GPUs where bfloat16 might be slower/unsupported.
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    
    # Check if flash_attn is available
    try:
        import flash_attn
        attn_implementation = "flash_attention_2" if torch.cuda.is_available() else "eager"
    except ImportError:
        attn_implementation = "eager"

    model = Qwen3TTSModel.from_pretrained(
        "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
        device_map=device,
        dtype=dtype,
        attn_implementation=attn_implementation,
    )
    print("Model loaded successfully.")

    # Initialize a temporary file for writing
    temp_output = args.output + ".tmp"
    
    with open(args.input, "r", encoding="utf-8") as f, \
         open(temp_output, "w", encoding="utf-8", newline="") as f_out:
        
        reader = csv.reader(f, delimiter="|")
        writer = csv.writer(f_out, delimiter="|")
        
        for row_idx, row in enumerate(reader):
            # ... checks ...
            if len(row) < 13:
                writer.writerow(row)
                continue

            audio_paths = []
            
            supported_speakers = model.get_supported_speakers()
            speaker_choice = "Yunseong" if "Yunseong" in supported_speakers else ("Eunji" if "Eunji" in supported_speakers else supported_speakers[0])
            
            for chunk_idx, col_idx in enumerate([7, 9, 11]):
                chunk_kor = clean_chunk(row[col_idx])
                
                if not chunk_kor.strip():
                    audio_paths.append("")
                    continue
                
                audio_filename = f"row{row_idx+1}_chunk{chunk_idx+1}.wav"
                audio_filepath = os.path.join(args.audio_dir, audio_filename)
                
                if not os.path.exists(audio_filepath):
                    print(f"Generating audio for row {row_idx+1}, chunk {chunk_idx+1}: {chunk_kor} with speaker {speaker_choice}")
                    try:
                        wavs, sr = model.generate_custom_voice(
                            text=chunk_kor,
                            language="Korean",
                            speaker=speaker_choice
                        )
                        sf.write(audio_filepath, wavs[0], sr)
                    except Exception as e:
                        import traceback
                        print(f"Error generating audio for {chunk_kor}: {e}")
                        traceback.print_exc()
                        break
                
                audio_paths.append(f"audio/{audio_filename}")
            
            if len(row) % 2 != 0 and len(row) > 13:
                new_row = row[:13] + audio_paths
            else:
                new_row = row[:13] + audio_paths
                
            writer.writerow(new_row)
            # flush so we can see progress in the file
            f_out.flush()

    # Move the temporary output file to the final output file
    if os.path.exists(args.output):
        os.remove(args.output)
    os.rename(temp_output, args.output)
    print("Done!")

if __name__ == "__main__":
    main()
