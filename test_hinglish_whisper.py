import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.pipeline.transcriber import get_whisper_model
import scipy.io.wavfile as wavfile
import numpy as np

model = get_whisper_model("base")
wav_path = r"C:\Users\bhupp\OneDrive\Desktop\ANIRBAN AUTOMATIONS\AUTO EDIT MOVIE\uploads\IMG_E0418_audio.wav"

sr, audio_data = wavfile.read(wav_path)
if len(audio_data.shape) > 1: audio_data = audio_data.mean(axis=1)
audio_norm = audio_data.astype(np.float32) / 32768.0

# Test with Hinglish Latin prompt
prompt = (
    "Namaste dosto, ye ek Hinglish travel vlog video hai jisme speaker Hindi aur English mix karke bol raha hai. "
    "Keywords: Ram Dalal bus, Manali, ISBT Kashmiri Gate Delhi, Saiyam, Himachal Pradesh, comfortable seat, kafi accha, Jai Gurudev."
)

segments, info = model.transcribe(
    audio_norm,
    beam_size=5,
    word_timestamps=True,
    initial_prompt=prompt,
    task="transcribe"
)

print(f"Detected language: {info.language} (probability: {info.language_probability:.2f})")
print("\n--- SAMPLE SEGMENTS AROUND 30s-60s ---")
for seg in segments:
    if 20.0 <= seg.start <= 70.0:
        print(f"[{seg.start:.1f}s - {seg.end:.1f}s]: {seg.text}")
    elif 110.0 <= seg.start <= 190.0:
        print(f"[{seg.start:.1f}s - {seg.end:.1f}s]: {seg.text}")
