import urllib.request
import soundfile as sf
import io
import torch
from qwen_tts import Qwen3TTSModel

device = "cuda:0" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if torch.cuda.is_available() else torch.float32

model = Qwen3TTSModel.from_pretrained(
    "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
    device_map=device,
    dtype=dtype,
    attn_implementation="eager",
)

# Download two Korean audio files for voice cloning
# Let's use two audio samples from the 'zeroth-korean' or 'kss' repo?
url1 = "https://huggingface.co/datasets/Bingsu/zeroth-korean/resolve/main/train_data_01/108/108_001_0001.flac"
url2 = "https://huggingface.co/datasets/Bingsu/zeroth-korean/resolve/main/train_data_01/113/113_001_0001.flac"

# We'll just use urllib + soundfile
req1 = urllib.request.urlopen(url1)
wav1, sr1 = sf.read(io.BytesIO(req1.read()))
sf.write("ref1.wav", wav1, sr1)

req2 = urllib.request.urlopen(url2)
wav2, sr2 = sf.read(io.BytesIO(req2.read()))
sf.write("ref2.wav", wav2, sr2)

wavs, sr = model.generate_voice_clone(
    text="안녕하세요",
    language="Korean",
    ref_audio=["ref1.wav", "ref2.wav"],
    x_vector_only_mode=True
)

sf.write("clone1.wav", wavs[0], sr)
sf.write("clone2.wav", wavs[1], sr)
print("Cloning success!")

