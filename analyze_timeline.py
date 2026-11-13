import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.config import RAW_INPUT_DIR, SUPPORTED_VIDEO_EXTS
from backend.pipeline.media_ingest import probe_media
from backend.pipeline.multi_clip_stitcher import deduplicate_and_sort_clips

clip_files = sorted([str(f) for f in RAW_INPUT_DIR.iterdir() if f.is_file() and f.suffix.lower() in SUPPORTED_VIDEO_EXTS])
unique_paths = deduplicate_and_sort_clips(clip_files)

print(f"Total Unique Clips: {len(unique_paths)}")
accumulated_time = 0.0

for idx, p in enumerate(unique_paths):
    meta = probe_media(p)
    dur = meta.get("duration", 0.0)
    w = meta.get("width", 0)
    h = meta.get("height", 0)
    rot = meta.get("orientation_rotate", 0)
    fps = meta.get("fps", 0)
    start_t = accumulated_time
    end_t = accumulated_time + dur
    accumulated_time = end_t
    
    # Flag clips around 2m (120s), 3:20m (200s), 3:40m (220s), 4:19m (259s), 5:22m (322s), 10:50m (650s), 12:40m (760s), 25:50m (1550s)
    marker = ""
    if start_t <= 120 <= end_t: marker += " [~2:00m Ram Dalal]"
    if start_t <= 200 <= end_t: marker += " [~3:20m Vertical/Horizontal]"
    if start_t <= 220 <= end_t: marker += " [~3:40m Hinglish No Captions]"
    if start_t <= 259 <= end_t: marker += " [~4:19m Hindi Meaning]"
    if start_t <= 322 <= end_t: marker += " [~5:22m Video Freeze]"
    if start_t <= 650 <= end_t: marker += " [~10:50m Slow Motion Unfreeze]"
    if start_t <= 760 <= end_t: marker += " [~12:40m Audio Desync]"
    if start_t <= 1550 <= end_t: marker += " [~25:50m Zero Audio]"

    print(f"[{idx:02d}] {Path(p).name:15s} | {start_t:6.1f}s - {end_t:6.1f}s ({dur:5.1f}s) | Res: {w}x{h} Rot: {rot}° FPS: {fps}{marker}")
