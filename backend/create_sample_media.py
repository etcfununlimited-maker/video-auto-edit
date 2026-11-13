"""
Generates rich sample media (talking head + scenic shots + audio with filler words & silences)
for immediate testing of AUTO VIDEO EDITOR.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import numpy as np
import scipy.io.wavfile as wavfile
import subprocess
from backend.config import FFMPEG_PATH, SAMPLE_MEDIA_DIR, RAW_INPUT_DIR

def generate_demo_video():
    demo_video_path = SAMPLE_MEDIA_DIR / "sample_vlog_iphone16.mp4"
    if demo_video_path.exists() and demo_video_path.stat().st_size > 50000:
        return str(demo_video_path)

    temp_raw = SAMPLE_MEDIA_DIR / "temp_silent.mp4"
    temp_wav = SAMPLE_MEDIA_DIR / "temp_audio.wav"

    fps = 30
    duration_sec = 18
    width, height = 1280, 720
    total_frames = fps * duration_sec

    # 1. Generate video frames
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(temp_raw), fourcc, fps, (width, height))

    for frame_idx in range(total_frames):
        t = frame_idx / fps
        img = np.zeros((height, width, 3), dtype=np.uint8)

        if 0 <= t < 6.0:
            # Segment 1: Talking Speaker (Simulated face/person indoors)
            for y in range(height):
                img[y, :] = [int(35 + (y / height) * 20), int(30 + (y / height) * 15), int(40 + (y / height) * 25)]
            # Draw speaker body & face
            cv2.ellipse(img, (width // 2, height - 80), (180, 240), 0, 0, 360, (70, 70, 80), -1)
            cv2.circle(img, (width // 2, height // 2 - 40), 110, (180, 205, 235), -1)
            cv2.circle(img, (width // 2 - 40, height // 2 - 60), 12, (50, 50, 60), -1)
            cv2.circle(img, (width // 2 + 40, height // 2 - 60), 12, (50, 50, 60), -1)
            mouth_open = int(8 + 8 * np.sin(t * 12))
            cv2.ellipse(img, (width // 2, height // 2 - 10), (25, mouth_open), 0, 0, 360, (50, 50, 140), -1)
            cv2.putText(img, "Dialogue: 'Welcome back... um... let me explain'", (50, 650), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        elif 6.0 <= t < 12.0:
            # Segment 2: Scenic Mountain & Nature B-Roll!
            for y in range(int(height * 0.45)):
                img[y, :] = [240 - int(y * 0.2), 190 - int(y * 0.2), 120]  # rich blue/cyan sky
            for y in range(int(height * 0.45), height):
                img[y, :] = [30, int(120 + (y / height) * 60), 40]  # vibrant green nature/forest
            pts_mountain = np.array([
                [0, int(height * 0.55)],
                [300, int(height * 0.25)],
                [600, int(height * 0.50)],
                [900, int(height * 0.20)],
                [1280, int(height * 0.55)],
                [1280, height],
                [0, height]
            ], np.int32)
            cv2.fillPoly(img, [pts_mountain], (90, 80, 100))
            cv2.putText(img, "SCENIC B-ROLL: Nature & Mountains (Silence Protected)", (50, 650), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        else:
            # Segment 3: Conclusion Dialogue with Retake
            for y in range(height):
                img[y, :] = [45, 40, 55]
            cv2.ellipse(img, (width // 2, height - 80), (180, 240), 0, 0, 360, (70, 70, 80), -1)
            cv2.circle(img, (width // 2, height // 2 - 40), 110, (180, 205, 235), -1)
            cv2.circle(img, (width // 2 - 40, height // 2 - 60), 12, (50, 50, 60), -1)
            cv2.circle(img, (width // 2 + 40, height // 2 - 60), 12, (50, 50, 60), -1)
            mouth_open = int(8 + 8 * np.sin(t * 14))
            cv2.ellipse(img, (width // 2, height // 2 - 10), (25, mouth_open), 0, 0, 360, (50, 50, 140), -1)
            cv2.putText(img, "Dialogue Retake: 'The secret is... wait... The secret is AI!'", (50, 650), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        out.write(img)

    out.release()

    # 2. Generate synthetic audio with scipy
    sr = 44100
    total_audio_samples = sr * duration_sec
    audio_data = np.zeros(total_audio_samples, dtype=np.float32)

    # Segment 1 (0 to 4s): Speech tone with vocal modulation
    t1 = np.linspace(0, 4.0, int(sr * 4.0), endpoint=False)
    audio_data[0:int(sr * 4.0)] = 0.6 * np.sin(2 * np.pi * 320 * t1) * (0.5 + 0.5 * np.sin(2 * np.pi * 5 * t1))

    # Segment 2 (6s to 12s): SCENIC B-ROLL SILENCE (ambient quiet murmur ~ -45dB)
    # The silence detector will find silence here, and scene detector will PROTECT it!

    # Segment 3 (12.5s to 17.5s): Dialogue retake
    t3 = np.linspace(0, 5.0, int(sr * 5.0), endpoint=False)
    audio_data[int(sr * 12.5):int(sr * 17.5)] = 0.65 * np.sin(2 * np.pi * 360 * t3) * (0.5 + 0.5 * np.sin(2 * np.pi * 6 * t3))

    # Convert to 16-bit PCM WAV
    audio_int16 = (audio_data * 32767).astype(np.int16)
    wavfile.write(str(temp_wav), sr, audio_int16)

    # 3. Mux into final MP4
    cmd = [
        FFMPEG_PATH,
        "-y",
        "-i", str(temp_raw),
        "-i", str(temp_wav),
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        str(demo_video_path)
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    # Cleanup temp
    if temp_raw.exists():
        temp_raw.unlink()
    if temp_wav.exists():
        temp_wav.unlink()

    # Copy to raw_input/
    raw_copy = RAW_INPUT_DIR / "sample_vlog_iphone16.mp4"
    import shutil
    shutil.copy2(str(demo_video_path), str(raw_copy))

    print(f"Sample demo video created successfully at: {demo_video_path}")
    return str(demo_video_path)

if __name__ == "__main__":
    generate_demo_video()
