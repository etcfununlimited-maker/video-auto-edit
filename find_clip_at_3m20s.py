import cv2
import numpy as np
from pathlib import Path

# Let's extract 1 frame from each clip in raw_input to find which one matches movie_frame_3m20s.jpg
target = cv2.imread(r"C:\Users\bhupp\OneDrive\Desktop\ANIRBAN AUTOMATIONS\AUTO EDIT MOVIE\uploads\movie_frame_3m20s.jpg")
target_small = cv2.resize(target, (160, 90))

raw_dir = Path(r"C:\Users\bhupp\OneDrive\Desktop\ANIRBAN AUTOMATIONS\AUTO EDIT MOVIE\raw_input")
matches = []

for f in sorted(raw_dir.iterdir()):
    if f.suffix.lower() not in ['.mov', '.mp4']:
        continue
    cap = cv2.VideoCapture(str(f))
    dur = cap.get(cv2.CAP_PROP_FRAME_COUNT) / (cap.get(cv2.CAP_PROP_FPS) or 30.0)
    for sample_t in [0.5, dur * 0.3, dur * 0.5, dur * 0.8]:
        cap.set(cv2.CAP_PROP_POS_MSEC, sample_t * 1000)
        ret, frame = cap.read()
        if ret and frame is not None:
            frame_resized = cv2.resize(frame, (160, 90))
            diff = np.mean(np.abs(target_small.astype(float) - frame_resized.astype(float)))
            if diff < 45.0:
                matches.append((diff, f.name, sample_t))
    cap.release()

matches.sort()
print("Top 5 matching raw clips for 3m20s:")
for diff, name, t in matches[:5]:
    print(f"  {name} at {t:.1f}s (diff: {diff:.2f})")
