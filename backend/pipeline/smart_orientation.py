"""
Smart Video Orientation Engine
Autodetects whether video clips filmed on smartphones (like iPhone, Android, DSLR)
are landscape widescreen or portrait selfie takes.
- For genuine portrait footage in 16:9 widescreen: Provides blurred ambient background padding (no harsh dead black bars).
- Always allows standard container display matrix auto-rotation so footage is never sideways.
"""
from pathlib import Path
from backend.pipeline.media_ingest import probe_media

def analyze_clip_orientation(video_path: str) -> dict:
    """
    Analyzes metadata to determine orientation after normal container autorotation.
    iPhone and Android smartphones encode rotation matrices that FFmpeg applies automatically.
    """
    meta = probe_media(video_path)
    w = meta.get("width", 1920)
    h = meta.get("height", 1080)

    is_horizontal = (w >= h)
    return {
        "is_horizontal": is_horizontal,
        "use_noautorotate": False,  # Never bypass container rotation matrix
        "vf_mode": "landscape_direct" if is_horizontal else "portrait_blurred_bg",
        "original_w": w,
        "original_h": h
    }

def get_orientation_video_filters(orient_info: dict, target_aspect: str = "16:9") -> tuple[list[str], str]:
    """
    Returns (ffmpeg_input_args, filter_str) appropriate for the detected orientation.
    - If portrait in 16:9: creates blurred background fill so no harsh black bars exist.
    - If landscape in 16:9: scales directly to 1920x1080.
    """
    input_args = []  # Omit -noautorotate so FFmpeg autorotates correctly

    if target_aspect == "9:16":
        # Target 9:16 vertical
        filter_str = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,format=yuv420p"
    else:
        # Target 16:9 horizontal
        if orient_info.get("is_horizontal", True):
            filter_str = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p"
        else:
            # Genuine portrait in 16:9: blurred background composite
            filter_str = (
                "split[fg][bg];"
                "[bg]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,gblur=sigma=25:steps=2,eq=brightness=-0.15[bg_blur];"
                "[fg]scale=1080:1920:force_original_aspect_ratio=decrease[fg_scaled];"
                "[bg_blur][fg_scaled]overlay=(W-w)/2:(H-h)/2,format=yuv420p"
            )

    return input_args, filter_str

