"""
Beat Sync & Music Auto-Ducking Engine
Detects musical tempo and downbeat timestamps for rhythmic video pacing.
Applies real-time auto-ducking to lower music levels when dialogue is active.
"""
import numpy as np
import scipy.io.wavfile as wavfile
import scipy.signal as signal
import subprocess
from pathlib import Path
from backend.config import FFMPEG_PATH, EXPORTS_DIR

def detect_music_beats(music_wav_path: str) -> dict:
    """
    Computes onset strength envelope and detects musical beats and estimated BPM.
    """
    try:
        sr, audio = wavfile.read(music_wav_path)
    except Exception as e:
        print(f"Error reading music wav: {e}")
        return {"bpm": 120, "beats": []}

    if len(audio.shape) > 1:
        audio = audio.mean(axis=1)

    audio = audio.astype(np.float32)
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio /= max_val

    # Downsample to 22050 for faster beat tracking
    hop_length = int(sr * 0.02)  # 20ms
    frames = [np.mean(np.abs(audio[i:i + hop_length])) for i in range(0, len(audio) - hop_length, hop_length)]
    envelope = np.array(frames)

    # Compute first difference for onset flux
    flux = np.diff(envelope)
    flux = np.maximum(0, flux)

    # Find peaks in onset flux
    min_dist_frames = int(0.35 / 0.02)  # max ~170 BPM
    peaks, _ = signal.find_peaks(flux, distance=min_dist_frames, prominence=np.std(flux) * 0.6)

    beat_times = [round(p * 0.02, 2) for p in peaks]

    # Estimate BPM from median beat intervals
    if len(beat_times) >= 2:
        intervals = np.diff(beat_times)
        median_interval = np.median(intervals)
        estimated_bpm = round(60.0 / median_interval) if median_interval > 0 else 120
    else:
        estimated_bpm = 120

    return {
        "bpm": estimated_bpm,
        "total_beats": len(beat_times),
        "beat_timestamps": beat_times
    }

def snap_timeline_to_beats(cut_timestamps: list[float], beat_timestamps: list[float], tolerance: float = 0.25) -> list[float]:
    """
    Snaps video cuts and transitions to the nearest musical beat for rhythm-synced editing.
    """
    if not beat_timestamps:
        return cut_timestamps

    snapped = []
    for cut in cut_timestamps:
        # Find closest beat
        closest = min(beat_timestamps, key=lambda b: abs(b - cut))
        if abs(closest - cut) <= tolerance:
            snapped.append(closest)
        else:
            snapped.append(cut)
    return sorted(list(set(snapped)))

def mix_with_auto_ducking(speech_audio_path: str, music_path: str, output_path: str = None, duck_level_db: float = -18.0) -> str:
    """
    Uses FFmpeg sidechain compression to automatically duck background music
    whenever voice dialogue is detected, with smooth attack and release curves.
    """
    sp_p = Path(speech_audio_path)
    if not output_path:
        output_path = str(EXPORTS_DIR / f"ducked_mix_{sp_p.stem}.wav")

    # Sidechain compressor filtergraph:
    # speech is input 0, music is input 1
    # [1:a][0:a]sidechaincompress=threshold=0.08:ratio=12:attack=20:release=350[ducked_music];
    # [0:a][ducked_music]amix=inputs=2:duration=first[out]
    filtergraph = (
        "[1:a][0:a]sidechaincompress=threshold=0.07:ratio=10:attack=15:release=300[ducked_music];"
        "[0:a]volume=1.0[speech_boost];"
        "[speech_boost][ducked_music]amix=inputs=2:duration=first:dropout_transition=2[out]"
    )

    cmd = [
        FFMPEG_PATH,
        "-y",
        "-i", str(speech_audio_path),
        "-i", str(music_path),
        "-filter_complex", filtergraph,
        "-map", "[out]",
        "-c:a", "pcm_s16le",
        "-ar", "48000",
        str(output_path)
    ]

    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return str(output_path)
