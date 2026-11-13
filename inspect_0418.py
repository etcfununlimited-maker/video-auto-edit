import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.pipeline.transcriber import transcribe_video, extract_audio

clip_path = r"C:\Users\bhupp\OneDrive\Desktop\ANIRBAN AUTOMATIONS\AUTO EDIT MOVIE\raw_input\IMG_E0418.MOV"
wav = extract_audio(clip_path)

# Let's transcribe with auto detection
data_auto = transcribe_video(clip_path, language="auto")
print(f"Auto Detected Language: {data_auto.get('detected_lang')}")
print(f"Total Words: {len(data_auto.get('words', []))}")

# Check words around 38s (2:00 in movie), 118s (3:20 in movie), 138s (3:40 in movie), 177s (4:19 in movie)
# Since IMG_E0418 started at 81.7s in the movie:
# 2:00m in movie = 120s - 81.7s = ~38s in clip
# 3:20m in movie = 200s - 81.7s = ~118s in clip
# 3:40m in movie = 220s - 81.7s = ~138s in clip
# 4:19m in movie = 259s - 81.7s = ~177s in clip

print("\n--- Words around 30s - 50s (~2:00m in movie) ---")
for w in data_auto.get('words', []):
    if 25.0 <= w['start'] <= 60.0:
        print(f"  {w['start']:.2f}s - {w['end']:.2f}s: {w['word']}")

print("\n--- Words around 110s - 150s (~3:20m - 3:40m in movie) ---")
for w in data_auto.get('words', []):
    if 110.0 <= w['start'] <= 160.0:
        print(f"  {w['start']:.2f}s - {w['end']:.2f}s: {w['word']}")

print("\n--- Words around 165s - 196s (~4:19m in movie) ---")
for w in data_auto.get('words', []):
    if 165.0 <= w['start'] <= 196.0:
        print(f"  {w['start']:.2f}s - {w['end']:.2f}s: {w['word']}")
