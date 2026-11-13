"""
AI Audio Enhancement & Denoising Engine
Provides studio-grade speech enhancement:
- Background fan/AC hum and hiss reduction
- Room echo attenuation
- Vocal clarity and presence boost
- Broadcast EBU R128 loudness normalization (-14 LUFS)
"""
import subprocess
from pathlib import Path
from backend.config import FFMPEG_PATH, EXPORTS_DIR

def enhance_audio_track(input_path: str, output_path: str = None, target_lufs: float = -14.0) -> str:
    """
    Applies multi-stage studio audio DSP processing using FFmpeg audio filtergraph.
    """
    src = Path(input_path)
    if not output_path:
        output_path = str(EXPORTS_DIR / f"enhanced_{src.stem}.wav")

    # Audio Filtergraph:
    # 1. highpass=f=80: cuts sub-bass rumble, microphone handling noise
    # 2. lowpass=f=12000: cuts ultrasonic hiss
    # 3. afftdn=nr=18:nf=-45:tn=1: fast FFT-based noise reduction for steady hum/fan noise
    # 4. equalizer=f=3200:t=q:w=1.5:g=3.2: vocal presence & articulation boost (Adobe Enhance style)
    # 5. compand: gentle vocal leveling and dynamics compression
    # 6. loudnorm: EBU R128 standard -14 LUFS normalization for podcasts and video
    audio_filters = (
        "highpass=f=80,"
        "lowpass=f=12500,"
        "afftdn=nr=16:nf=-42:tn=1,"
        "equalizer=f=200:t=q:w=1.0:g=1.2,"
        "equalizer=f=3400:t=q:w=1.4:g=3.5,"
        "compand=attacks=0.03:decays=0.2:points=-70/-70|-35/-20|0/-3:gain=2,"
        f"loudnorm=I={target_lufs}:TP=-1.0:LRA=11"
    )

    cmd = [
        FFMPEG_PATH,
        "-y",
        "-i", str(src),
        "-vn",
        "-af", audio_filters,
        "-c:a", "pcm_s16le",
        "-ar", "48000",
        str(output_path)
    ]

    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return str(output_path)

def mux_enhanced_audio(video_path: str, enhanced_audio_path: str, output_path: str = None) -> str:
    """
    Combines enhanced audio with original video without re-encoding video stream.
    """
    src = Path(video_path)
    if not output_path:
        output_path = str(EXPORTS_DIR / f"studio_audio_{src.name}")

    cmd = [
        FFMPEG_PATH,
        "-y",
        "-i", str(src),
        "-i", str(enhanced_audio_path),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "256k",
        str(output_path)
    ]

    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return str(output_path)
