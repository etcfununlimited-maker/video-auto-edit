"""
Media Ingestion Engine
Handles MP4, iPhone 16 HEVC / Apple ProRes / HDR / Dolby Vision / MOV, photos, and live media.
Generates browser-compatible proxies and probes metadata.
"""
import os
import subprocess
import json
import cv2
from pathlib import Path
from backend.config import FFMPEG_PATH, UPLOADS_DIR

_PROBE_CACHE = {}

def probe_media(file_path: str) -> dict:
    """
    Extracts deep metadata from media files using FFmpeg / OpenCV.
    Uses in-memory cache to guarantee instantaneous performance on large directories.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Media file not found: {file_path}")

    try:
        mtime = path.stat().st_mtime
        cache_key = (str(path.resolve()), mtime)
        if cache_key in _PROBE_CACHE:
            return dict(_PROBE_CACHE[cache_key])
    except Exception:
        cache_key = None

    meta = {
        "filename": path.name,
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "width": 1920,
        "height": 1080,
        "duration": 0.0,
        "fps": 30.0,
        "codec": "unknown",
        "has_audio": False,
        "audio_codec": "none",
        "is_iphone_media": False,
        "is_hdr": False,
        "orientation_rotate": 0
    }

    # Detect if extension suggests iPhone or HEVC
    lower_name = path.name.lower()
    if any(k in lower_name for k in ["iphone", "img_", "mov"]) or path.suffix.lower() in [".mov", ".heic"]:
        meta["is_iphone_media"] = True

    # Use OpenCV as first fast probe
    try:
        cap = cv2.VideoCapture(str(path))
        if cap.isOpened():
            meta["width"] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
            meta["height"] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080
            meta["fps"] = float(cap.get(cv2.CAP_PROP_FPS)) or 30.0
            total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
            if meta["fps"] > 0:
                meta["duration"] = round(total_frames / meta["fps"], 2)
            cap.release()
    except Exception as e:
        print(f"OpenCV probe warning: {e}")

    # Use FFmpeg to probe audio & codec details
    try:
        cmd = [
            FFMPEG_PATH,
            "-i", str(path),
            "-hide_banner"
        ]
        res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, errors="replace")
        err_out = res.stderr

        if "Audio:" in err_out:
            meta["has_audio"] = True
            for line in err_out.splitlines():
                if "Audio:" in line:
                    meta["audio_codec"] = line.split("Audio:")[1].split(",")[0].strip()

        if "hevc" in err_out.lower() or "h.265" in err_out.lower():
            meta["codec"] = "hevc"
            meta["is_iphone_media"] = True
        elif "h264" in err_out.lower():
            meta["codec"] = "h264"
        elif "prores" in err_out.lower():
            meta["codec"] = "prores"
            meta["is_iphone_media"] = True

        if any(h in err_out.lower() for h in ["bt2020", "smpte2084", "arib-std-b67", "hdr", "hlg", "dolby"]):
            meta["is_hdr"] = True

        # Extract duration from ffmpeg if opencv failed
        if meta["duration"] <= 0.0 and "Duration: " in err_out:
            dur_str = err_out.split("Duration: ")[1].split(",")[0].strip()
            parts = dur_str.split(":")
            if len(parts) == 3:
                h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
                meta["duration"] = round(h * 3600 + m * 60 + s, 2)

    except Exception as e:
        print(f"FFmpeg probe error: {e}")

    if cache_key:
        _PROBE_CACHE[cache_key] = dict(meta)

    return meta

def create_web_preview(input_path: str, output_path: str = None) -> str:
    """
    Transcodes raw iPhone 16 / HEVC / ProRes footage into web-standard H.264 AAC MP4
    with automatic tone-mapping if HDR is present so the HTML5 player displays crisp colors.
    """
    src = Path(input_path)
    if not output_path:
        output_path = str(UPLOADS_DIR / f"preview_{src.stem}.mp4")

    out_p = Path(output_path)
    if out_p.exists() and out_p.stat().st_size > 1024:
        return str(out_p)

    probe = probe_media(str(src))
    
    # Base filter chain: tone-map HDR if needed, scale to 1080p max for fast web preview
    vf = ["scale=w=min(1920\\,iw):h=-2"]
    if probe.get("is_hdr"):
        # FFmpeg tone mapping to standard sRGB / Rec.709
        vf.append("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=2,zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
    else:
        vf.append("format=yuv420p")

    vf_str = ",".join(vf)

    cmd = [
        FFMPEG_PATH,
        "-y",
        "-i", str(src),
        "-vf", vf_str,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        str(out_p)
    ]

    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return str(out_p)
    except Exception as e:
        print(f"Preview transcoding fallback: {e}")
        # If fast transcoding failed, return source if mp4
        if src.suffix.lower() == ".mp4":
            return str(src)
        return str(out_p)
