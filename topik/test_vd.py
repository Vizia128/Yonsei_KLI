import torch
import soundfile as sf
from qwen_tts import Qwen3TTSModel
device = "cuda:0" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if torch.cuda.is_available() else torch.float32
model = Qwen3TTSModel.from_pretrained(
    "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
    device_map=device,
    dtype=dtype,
    attn_implementation="eager",
)
try:
    wavs, sr = model.generate_voice_design(
        text="안녕하세요.",
        language="Korean",
        instruct="Korean male voice"
    )
    print("YES")
except Exception as e:
    print(e)
