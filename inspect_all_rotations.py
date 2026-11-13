import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.config import RAW_INPUT_DIR, SUPPORTED_VIDEO_EXTS
from backend.pipeline.media_ingest import probe_media

for f in sorted(RAW_INPUT_DIR.iterdir()):
    if f.suffix.lower() not in SUPPORTED_VIDEO_EXTS:
        continue
    m = probe_media(str(f))
    w = m.get("width", 0)
    h = m.get("height", 0)
    rot = m.get("orientation_rotate", 0)
    if w < h or rot != 0:
        print(f"{f.name:25s}: {w}x{h} rotate={rot}°")
