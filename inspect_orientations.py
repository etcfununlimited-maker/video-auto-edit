import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.pipeline.media_ingest import probe_media
from backend.config import RAW_INPUT_DIR

# Check clips around 0418, 0420, 0421, 0423
for fname in ["IMG_E0418.MOV", "IMG_0419.MOV", "IMG_0420.MOV", "IMG_0421.MOV", "IMG_0423.MOV", "IMG_E0428.MOV"]:
    p = str(RAW_INPUT_DIR / fname)
    m = probe_media(p)
    print(f"{fname:15s}: dur={m.get('duration'):.1f}s res={m.get('width')}x{m.get('height')} rot={m.get('orientation_rotate')}° codec={m.get('codec')}")
