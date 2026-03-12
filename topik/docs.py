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
import inspect
from qwen_tts import Qwen3TTSModel
print(inspect.getdoc(Qwen3TTSModel.generate_voice_design))
