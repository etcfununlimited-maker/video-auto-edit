"""
Configuration settings for AUTO VIDEO EDITOR
ANIRBAN AUTOMATIONS
"""
import os
import sys
from pathlib import Path

# Base Paths
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"
TEMPLATES_DIR = FRONTEND_DIR / "templates"
UPLOADS_DIR = BASE_DIR / "uploads"
EXPORTS_DIR = BASE_DIR / "exports"
SAMPLE_MEDIA_DIR = BASE_DIR / "sample_media"
RAW_INPUT_DIR = BASE_DIR / "raw_input"
MUSIC_DIR = RAW_INPUT_DIR / "MUSIC"
FINAL_EXPORT_DIR = BASE_DIR / "final_export"

# Ensure all runtime and export directories exist automatically on startup
for p in [
    UPLOADS_DIR,
    EXPORTS_DIR,
    SAMPLE_MEDIA_DIR,
    RAW_INPUT_DIR,
    MUSIC_DIR,
    FINAL_EXPORT_DIR,
    FINAL_EXPORT_DIR / "MUSIC",
    FINAL_EXPORT_DIR / "COLLAGES",
    FINAL_EXPORT_DIR / "VERTICAL_FILL",
    FINAL_EXPORT_DIR / "PHOTOS",
    FINAL_EXPORT_DIR / "PHOTO_PROXIES"
]:
    p.mkdir(parents=True, exist_ok=True)

# Resolve FFmpeg and FFprobe binaries
FFMPEG_PATH = None
try:
    import imageio_ffmpeg
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    pass

if not FFMPEG_PATH or not os.path.exists(FFMPEG_PATH):
    import shutil
    FFMPEG_PATH = shutil.which("ffmpeg") or "ffmpeg"

# Supported Media Formats
SUPPORTED_VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv", ".m2ts"}
SUPPORTED_AUDIO_EXTS = {".mp3", ".wav", ".aac", ".m4a", ".flac", ".ogg"}
SUPPORTED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}

# Presets for Color Grading
COLOR_PRESETS = {
    "none": {
        "name": "Standard / Natural",
        "description": "Original raw footage colors with neutral balance",
        "eq": "",
        "lut": None,
        "preview_color": "#9ca3af"
    },
    "teal_orange": {
        "name": "Cinematic Teal & Orange",
        "description": "Hollywood blockbuster look: warm glowing skin tones with deep cyan shadows",
        "eq": "eq=contrast=1.18:brightness=0.01:saturation=1.28,curves=all='0/0 0.5/0.46 1/1':red='0/0 0.5/0.54 1/1':blue='0/0.05 0.5/0.45 1/0.92'",
        "preview_color": "#0ea5e9"
    },
    "moody_noir": {
        "name": "Moody Bleach Bypass",
        "description": "Desaturated, gritty, high-contrast dramatic cinematic look",
        "eq": "eq=contrast=1.35:brightness=-0.03:saturation=0.65",
        "preview_color": "#64748b"
    },
    "vintage_70s": {
        "name": "Vintage Warm 70s",
        "description": "Nostalgic golden retro film aesthetic with gentle fade",
        "eq": "eq=contrast=1.08:brightness=0.04:saturation=1.12,curves=red='0/0.06 1/1':blue='0/0 1/0.85'",
        "preview_color": "#d97706"
    },
    "cyber_neon": {
        "name": "Cyberpunk Neon",
        "description": "Vibrant magenta, electric violet, and deep cobalt highlights",
        "eq": "eq=contrast=1.25:brightness=0.02:saturation=1.55,curves=blue='0/0.08 1/1':red='0/0.04 1/1'",
        "preview_color": "#ec4899"
    },
    "clean_doc": {
        "name": "Clean Documentary",
        "description": "True-to-life studio clarity with boosted micro-contrast and crisp highlights",
        "eq": "eq=contrast=1.06:brightness=0.01:saturation=1.08,unsharp=5:5:0.8:5:5:0.0",
        "preview_color": "#10b981"
    },
    "golden_hour": {
        "name": "Golden Hour Sunset",
        "description": "Lush amber sunlight warmth with soft honey roll-off",
        "eq": "eq=contrast=1.12:brightness=0.03:saturation=1.22,curves=red='0/0.05 0.5/0.56 1/1':green='0/0.02 0.5/0.52 1/1':blue='0/0 0.5/0.46 1/0.9'",
        "preview_color": "#f59e0b"
    },
    "vibrant_pop": {
        "name": "Social Viral Pop",
        "description": "Eye-catching punchy colors optimized for mobile screens (TikTok/Reels)",
        "eq": "eq=contrast=1.15:brightness=0.02:saturation=1.4,unsharp=3:3:0.5:3:3:0.0",
        "preview_color": "#8b5cf6"
    }
}

# Filler Words Dictionary (English, Hindi & Hinglish Code-Mixed)
COMMON_FILLER_WORDS = {
    # English Fillers
    "um", "uh", "umm", "uhh", "er", "ah", "ahh",
    "like", "you know", "i mean", "sort of", "kind of",
    "basically", "literally", "actually", "right",

    # Hinglish & Hindi Fillers (Roman script)
    "matlab", "matlb", "woh", "wo", "woah", "yaani", "yani",
    "kya", "kya kehte hain", "kya bolte", "toh", "haan", "haan toh",
    "achha", "accha", "samjhe", "bhai", "dekho", "jaise ki",

    # Hindi Fillers (Devanagari script)
    "मतलब", "वो", "यानी", "जैसे", "हाँ", "अच्छा", "तो"
}

# Grid Definitions for the Dashboard
WORKFLOW_GRIDS = [
    {
        "id": "grid_ingest",
        "title": "Grid 1: Media Ingest & iPhone 16 Decoder",
        "desc": "Detects MP4 / MOV / HEVC, ProRes, HDR tone-mapping & Live Photos",
        "icon": "film"
    },
    {
        "id": "grid_transcribe",
        "title": "Grid 2: Speech Transcription & Word Timestamps",
        "desc": "Faster-Whisper neural STT with exact millisecond word boundaries",
        "icon": "mic"
    },
    {
        "id": "grid_silence",
        "title": "Grid 3: Silence & Filler Removal + Retake Arbiter",
        "desc": "Purges dead air, stutters, 'um'/'uh', and arbitrates multi-takes",
        "icon": "scissors"
    },
    {
        "id": "grid_scenic",
        "title": "Grid 4: Scenic B-Roll & Visual Scene Preserver",
        "desc": "Detects mountains, sea, forest, roads; preserves visual silences",
        "icon": "image"
    },
    {
        "id": "grid_reframe",
        "title": "Grid 5: Smart Reframer & Face Tracker (9:16)",
        "desc": "Auto-crops 16:9 to 9:16 vertical keeping speaker dynamically centered",
        "icon": "smartphone"
    },
    {
        "id": "grid_audio",
        "title": "Grid 6: AI Audio Enhancer & Denoise",
        "desc": "Removes hum, hiss, echo and normalizes voice to -14 LUFS studio standard",
        "icon": "volume-2"
    },
    {
        "id": "grid_beatsync",
        "title": "Grid 7: Beat Sync & Music Auto-Ducking",
        "desc": "Aligns cuts to BPM downbeats & ducks background audio when talking",
        "icon": "music"
    },
    {
        "id": "grid_captions",
        "title": "Grid 8: Kinetic Animated Hyperframe Captions",
        "desc": "Hormozi / MrBeast dynamic animated word-by-word subtitle styling",
        "icon": "type"
    },
    {
        "id": "grid_bgremove",
        "title": "Grid 9: Background Segmentation & Virtual Studio",
        "desc": "Greenscreen-free subject isolation, background blur & replacement",
        "icon": "layers"
    },
    {
        "id": "grid_color",
        "title": "Grid 10: Cinematic LUT Color Grader",
        "desc": "Teal & Orange, Moody Bleach, Cyberpunk Neon, Vintage 70s grading",
        "icon": "aperture"
    },
    {
        "id": "grid_agent",
        "title": "Grid 11: AI Director Agent (Prompt-to-Edit)",
        "desc": "Natural language prompt orchestration & intelligent timeline assembly",
        "icon": "cpu"
    },
    {
        "id": "grid_render",
        "title": "Grid 12: Final Timeline & Ultra-HD Renderer",
        "desc": "Multi-track timeline compositing, audio crossfades and MP4 master export",
        "icon": "check-circle"
    }
]
