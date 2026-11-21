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

ROCK_AND_HEAVY_BEAT_TRACKS = {
    "Big_Rock", "Cool_Rock", "Funkorama", "Protofunk", "Werq", "Poppers_and_Prosecco"
}

MOOD_TRACK_PREFERENCES = {
    "sacred_temple": [
        # Spiritual, serene, peaceful ambient, acoustic, sublime reverent tones
        'Truth_of_the_Legend', 'Clean_Soul', 'Mining_by_Moonlight', 'Overcast',
        'Airport_Lounge', 'Wallpaper', 'Somewhere_Sunny', 'Dispersion_Relation',
        'Bossa_Antigua', 'District_Four'
    ],
    "calm_travel": [
        'Somewhere_Sunny', 'Life_of_Riley', 'Clean_Soul', 'Carefree', 'Carpe_Diem',
        'Daily_Beetle', 'Bossa_Antigua', 'Airport_Lounge', 'Mining_by_Moonlight', 'Overcast'
    ],
    "scenic_drive": [
        'Call_to_Adventure', 'Daily_Beetle', 'Somewhere_Sunny', 'Clean_Soul',
        'District_Four', 'Airport_Lounge', 'Mining_by_Moonlight', 'Overcast'
    ],
    "energetic_vlog": [
        'Carefree', 'Somewhere_Sunny', 'Life_of_Riley', 'Upbeat_Forever', 'Carpe_Diem',
        'Call_to_Adventure', 'Daily_Beetle', 'Clean_Soul', 'Cool_Rock', 'Big_Rock',
        'Groove_Grove', 'Funkorama', 'Poppers_and_Prosecco', 'Protofunk', 'Feelin_Good', 'Werq',
        'Bossa_Antigua', 'Airport_Lounge', 'District_Four', 'Mining_by_Moonlight', 'Overcast'
    ]
}

def get_available_soundtracks() -> list[Path]:
    """Returns all available royalty-free background music tracks from raw_input/MUSIC."""
    from backend.config import RAW_INPUT_DIR, SAMPLE_MEDIA_DIR
    music_dir = RAW_INPUT_DIR / "MUSIC"
    tracks = []
    if music_dir.exists():
        tracks = sorted(list(music_dir.glob("*.mp3")) + list(music_dir.glob("*.wav")))
    if not tracks and SAMPLE_MEDIA_DIR.exists():
        tracks = sorted(list(SAMPLE_MEDIA_DIR.glob("*.mp3")) + list(SAMPLE_MEDIA_DIR.glob("*.wav")))
    return tracks

def build_movie_soundtrack_bed(
    target_duration: float,
    output_path: str = None,
    mood: str = "sacred_temple",
    sacred_mode: bool = True
) -> str:
    """
    Builds a continuous background music bed matching target_duration by sequencing
    at least 10 (or up to 20+) curated soundtrack tracks with smooth 2.5-second crossfades.
    Supports context-aware mood selection and strict Sacred Mode filtering:
      - 'sacred_temple': Spiritual & temple serenity (Strictly excludes rock/heavy beats)
      - 'calm_travel': Acoustic, gentle, warm travel tones
      - 'scenic_drive': Balanced open highway & landscape exploration
      - 'energetic_vlog': High tempo & beat sync
    """
    tracks = get_available_soundtracks()
    if not tracks:
        return None

    # Filter out rock and heavy beat tracks if sacred_mode is active or sacred_temple mood selected
    if sacred_mode or mood == "sacred_temple":
        filtered_tracks = [t for t in tracks if t.stem not in ROCK_AND_HEAVY_BEAT_TRACKS]
        if filtered_tracks:
            tracks = filtered_tracks

    if not output_path:
        output_path = str(EXPORTS_DIR / f"soundtrack_bed_{int(target_duration)}s.wav")

    by_stem = {t.stem: t for t in tracks}
    preferred_order = MOOD_TRACK_PREFERENCES.get(mood, MOOD_TRACK_PREFERENCES["sacred_temple"])
    ordered_tracks = []

    # 1. Add matching curated tracks for chosen mood
    for name in preferred_order:
        if name in by_stem and (not sacred_mode or name not in ROCK_AND_HEAVY_BEAT_TRACKS):
            ordered_tracks.append(by_stem[name])
    # 2. Add remaining royalty-free tracks
    for t in tracks:
        if t not in ordered_tracks and (not sacred_mode or t.stem not in ROCK_AND_HEAVY_BEAT_TRACKS):
            ordered_tracks.append(t)

    if not ordered_tracks:
        ordered_tracks = tracks

    # If single track or short video (< 90 seconds), loop primary mood track
    if len(ordered_tracks) == 1 or target_duration <= 90:
        sel_track = ordered_tracks[0]
        cmd = [
            FFMPEG_PATH, "-y",
            "-stream_loop", "-1",
            "-i", str(sel_track),
            "-t", f"{target_duration:.2f}",
            "-c:a", "pcm_s16le",
            "-ar", "48000",
            str(output_path)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return str(output_path)

    # Probe duration of tracks and pick enough tracks to cover target_duration
    selected_tracks = []
    track_durs = []
    cum_duration = 0.0
    import re

    idx = 0
    while cum_duration < target_duration:
        t = ordered_tracks[idx % len(ordered_tracks)]
        idx += 1
        res = subprocess.run([FFMPEG_PATH, "-i", str(t)], stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)
        m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
        d = (int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))) if m else 180.0

        selected_tracks.append(t)
        track_durs.append(d)
        cum_duration += (d - 2.5) # with 2.5s crossfade overlap
        if idx >= len(ordered_tracks) * 2:
            break

    # If long feature movie (>= 30 mins) ensure at least 10 tracks are represented
    if target_duration >= 1800 and len(selected_tracks) < 10 and len(ordered_tracks) >= 10:
        for t in ordered_tracks:
            if t not in selected_tracks and len(selected_tracks) < 10:
                selected_tracks.append(t)
                res = subprocess.run([FFMPEG_PATH, "-i", str(t)], stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)
                m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
                d = (int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))) if m else 180.0
                track_durs.append(d)

    # Build FFmpeg filter complex with smooth crossfades
    inputs = []
    for t in selected_tracks:
        inputs.extend(["-i", str(t)])

    filter_parts = []
    for i, d in enumerate(track_durs):
        fade_out_st = max(0.5, d - 2.5)
        filter_parts.append(f"[{i}:a]afade=t=in:st=0:d=2.0,afade=t=out:st={fade_out_st:.2f}:d=2.5[a{i}]")
    concat_in = "".join(f"[a{i}]" for i in range(len(selected_tracks)))
    filter_str = ";".join(filter_parts) + f";{concat_in}concat=n={len(selected_tracks)}:v=0:a=1[outa]"

    cmd = [
        FFMPEG_PATH, "-y",
        *inputs,
        "-filter_complex", filter_str,
        "-map", "[outa]",
        "-t", f"{target_duration:.2f}",
        "-c:a", "pcm_s16le",
        "-ar", "48000",
        str(output_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return str(output_path)

def mix_with_auto_ducking(
    speech_audio_path: str,
    music_path: str,
    output_path: str = None,
    duck_level_db: float = -14.0,
    music_volume: float = None,
    speech_boost: float = None,
    ducking_depth_pct: float = 75.0,
    music_level_pct: float = 40.0
) -> str:
    """
    Uses FFmpeg sidechain compression to automatically duck background music
    whenever voice dialogue is detected, with smooth attack and release curves.
    When dialogue stops (driving pauses, scenic B-roll), music smoothly swells up!
    Supports interactive ducking depth percentage and background music volume sliders.
    """
    sp_p = Path(speech_audio_path)
    if not output_path:
        output_path = str(EXPORTS_DIR / f"ducked_mix_{sp_p.stem}.wav")

    # Scaled parameters from user sliders:
    if music_volume is None:
        music_volume = max(0.05, min(1.0, float(music_level_pct) / 100.0))
    if speech_boost is None:
        speech_boost = 1.25 + (float(ducking_depth_pct) / 100.0) * 0.35

    threshold = max(0.015, 0.050 - (float(ducking_depth_pct) / 100.0) * 0.030)
    ratio = 2.0 + (float(ducking_depth_pct) / 100.0) * 8.0
    release_ms = int(350 + (float(ducking_depth_pct) / 100.0) * 300)

    # Dynamic Breathing Sidechain Compressor:
    # 1. Baseline music volume scaled to user-selected level.
    # 2. Sidechain compressor monitors human vocal frequencies via boosted highpassed key [sp_trigger].
    #    When speech is detected, music decisively ducks according to user ratio & threshold.
    #    When speech pauses, music smoothly swells back up over release_ms.
    # 3. Clean speech is boosted prominently forward and mixed with normalize=0!
    filtergraph = (
        f"[1:a]volume={music_volume:.2f}[bgm];"
        f"[0:a]asplit=2[sp_raw][sp_key];"
        f"[sp_key]highpass=f=120,volume=2.5[sp_trigger];"
        f"[bgm][sp_trigger]sidechaincompress=threshold={threshold:.3f}:ratio={ratio:.1f}:attack=15:release={release_ms}[ducked_bgm];"
        f"[sp_raw]volume={speech_boost:.2f}[sp];"
        f"[sp][ducked_bgm]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[out]"
    )

    cmd = [
        FFMPEG_PATH,
        "-y",
        "-i", str(speech_audio_path),
        "-stream_loop", "-1",
        "-i", str(music_path),
        "-filter_complex", filtergraph,
        "-map", "[out]",
        "-c:a", "pcm_s16le",
        "-ar", "48000",
        str(output_path)
    ]

    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return str(output_path)
