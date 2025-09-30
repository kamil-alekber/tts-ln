import wave
from piper import PiperVoice
from huggingface_hub import hf_hub_download
import os

def load_voice():
    voice_repo = "rhasspy/piper-voices"
    voice_filename = "en_US-hfc_female-medium.onnx"
    config_filename = "en_US-hfc_female-medium.onnx.json"
    subfolder = "en/en_US/hfc_female/medium"

    voice_path = hf_hub_download(
        repo_id=voice_repo,
        filename=voice_filename,
        subfolder=subfolder,
    )
    
    config_path = hf_hub_download(
        repo_id=voice_repo,
        filename=config_filename,
        subfolder=subfolder,
    )
    return voice_path, config_path


def generate_tts(input_txt: str, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    voice_path, _ = load_voice()
    piper_voice = PiperVoice.load(voice_path)
    
    with wave.open(output_path, "wb") as wav_file:
        piper_voice.synthesize_wav(input_txt, wav_file)

    print(f"Audio synthesis complete! Check {output_path} file.")
