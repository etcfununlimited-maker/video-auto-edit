import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.pipeline.media_ingest import probe_media
from backend.config import UPLOADS_DIR

cur = 0.0
for p in sorted(UPLOADS_DIR.glob('full_movie_seg_*.mp4')):
    m = probe_media(str(p))
    d = m.get('duration', 0)
    w = m.get('width', 0)
    h = m.get('height', 0)
    print(f"{p.name:35s}: {cur:6.1f}s - {cur+d:6.1f}s ({d:5.1f}s) res={w}x{h}")
    cur += d
