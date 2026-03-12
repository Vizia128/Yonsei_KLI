# /// script
# requires-python = "==3.12.*"
# dependencies = [
#     "qwen-tts",
#     "soundfile",
#     "torch @ https://download.pytorch.org/whl/cu121/torch-2.5.1%2Bcu121-cp312-cp312-linux_x86_64.whl",
#     "torchvision @ https://download.pytorch.org/whl/cu121/torchvision-0.20.1%2Bcu121-cp312-cp312-linux_x86_64.whl",
#     "torchaudio @ https://download.pytorch.org/whl/cu121/torchaudio-2.5.1%2Bcu121-cp312-cp312-linux_x86_64.whl",
# ]
# ///
import torch
from qwen_tts import Qwen3TTSModel
import argparse

# Check device and dtype like generate_audio.py
device = "cuda:0" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if torch.cuda.is_available() else torch.float32

model = Qwen3TTSModel.from_pretrained(
    "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
    device_map=device,
    dtype=dtype,
    attn_implementation="eager",
)
speakers = model.get_supported_speakers()
print("=="*20)
print("SUPPORTED SPEAKERS:")
print(speakers)
print("=="*20)

