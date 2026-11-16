"""
Master Feature Movie Assembly Runner
Executes the upgraded Multi-Clip Timeline Sequencer & Stitcher.
Enforces CFR 30.0 fps, smart orientation auto-rotation, 1.8s photo cap,
Two-Pass Retake Arbitration, and YouTube Create Hinglish captions.
"""
import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.config import RAW_INPUT_DIR, SUPPORTED_VIDEO_EXTS
from backend.pipeline.multi_clip_stitcher import build_multi_clip_movie_pipeline

def progress_logger(percent: int, message: str):
    print(f"[{percent:3d}%] {message}", flush=True)

if __name__ == "__main__":
    start_t = time.time()
    clip_files = sorted([str(f) for f in RAW_INPUT_DIR.iterdir() if f.is_file() and f.suffix.lower() in SUPPORTED_VIDEO_EXTS])
    print(f"Found {len(clip_files)} files in raw_input. Starting Assembly...")

    from backend.pipeline.ai_director_suite import DEFAULT_TEXT_BEHIND_PERSON
    master_path = build_multi_clip_movie_pipeline(
        clip_paths=clip_files,
        color_grade="teal_orange",
        aspect_ratio="original",
        caption_style="hyperframe_kinetic",
        output_filename="MASTER_FULL_FEATURE_MOVIE.mp4",
        progress_callback=progress_logger,
        text_behind=DEFAULT_TEXT_BEHIND_PERSON
    )

    elapsed = time.time() - start_t
    print(f"\n==================================================")
    print(f"MASTER FEATURE MOVIE GENERATED IN {elapsed:.1f}s!")
    print(f"Path: {master_path}")
    print(f"==================================================")
