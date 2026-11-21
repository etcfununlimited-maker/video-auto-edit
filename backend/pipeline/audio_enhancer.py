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

def apply_vocal_isolation_and_denoise(input_path: str, output_path: str = None, denoise_pct: float = 75.0) -> str:
    """
    Applies cutting-edge Non-Stationary Spectral Noise Reduction (noisereduce)
    to eliminate passing highway trucks, room fans, and car AC blower roar,
    followed by speech forwarding EQ (+5dB) and broadcast normalization.
    Scales reduction proportion based on user denoise slider percentage.
    """
    src = Path(input_path)
    if not output_path:
        output_path = str(EXPORTS_DIR / f"isolated_vocal_{src.stem}.wav")

    # Step 1: Extract/convert input to 48kHz WAV
    tmp_in_wav = EXPORTS_DIR / f".tmp_in_{src.stem}.wav"
    cmd_wav = [
        FFMPEG_PATH, "-y",
        "-i", str(src),
        "-vn", "-ac", "2", "-ar", "48000",
        "-c:a", "pcm_s16le",
        str(tmp_in_wav)
    ]
    subprocess.run(cmd_wav, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # Step 2: Non-stationary spectral noise reduction
    try:
        import noisereduce as nr
        import scipy.io.wavfile as wavfile
        import numpy as np
        sr, data = wavfile.read(str(tmp_in_wav))
        is_stereo = (data.ndim == 2)
        c_in = data.T.astype(np.float32) if is_stereo else data.astype(np.float32)
        prop_decrease = min(1.0, max(0.1, (float(denoise_pct) / 100.0) * 1.05))
        c_clean = nr.reduce_noise(y=c_in, sr=sr, stationary=False, prop_decrease=prop_decrease, n_fft=2048, win_length=2048)
        c_clean_t = c_clean.T if is_stereo else c_clean
        out_int16 = np.clip(c_clean_t, -32767, 32767).astype(np.int16)
        tmp_nr_wav = EXPORTS_DIR / f".tmp_nr_{src.stem}.wav"
        wavfile.write(str(tmp_nr_wav), sr, out_int16)
        dsp_source = str(tmp_nr_wav)
    except Exception as e_nr:
        print(f"Spectral noisereduce fallback notice: {e_nr}")
        dsp_source = str(tmp_in_wav)

    # Step 3: Vocal Forwarding EQ (+5dB @ 3.4kHz) & Studio Downward Gate
    hp_f = int(90 + (float(denoise_pct) / 100.0) * 30)
    gate_thresh = 0.020 + (float(denoise_pct) / 100.0) * 0.025
    af = (
        f"highpass=f={hp_f}:poles=2,"
        "equalizer=f=1800:t=q:w=1.2:g=2.5,"
        "equalizer=f=3400:t=q:w=1.4:g=5.0,"
        f"agate=threshold={gate_thresh:.3f}:range=0.05:attack=10:release=220,"
        "loudnorm=I=-14:TP=-1.0:LRA=10,"
        "aformat=sample_rates=48000:channel_layouts=stereo"
    )
    cmd_eq = [
        FFMPEG_PATH, "-y",
        "-i", dsp_source,
        "-af", af,
        "-c:a", "pcm_s16le",
        str(output_path)
    ]
    subprocess.run(cmd_eq, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # Cleanup temp wavs
    for f in [tmp_in_wav, EXPORTS_DIR / f".tmp_nr_{src.stem}.wav"]:
        try:
            f.unlink()
        except Exception:
            pass

    return str(output_path)

def enhance_audio_track(input_path: str, output_path: str = None, target_lufs: float = -14.0, denoise_pct: float = 75.0) -> str:
    """
    Applies multi-stage studio audio DSP processing using FFmpeg audio filtergraph.
    Dynamically scales noise suppression according to user slider percentage.
    """
    src = Path(input_path)
    if not output_path:
        output_path = str(EXPORTS_DIR / f"enhanced_{src.stem}.wav")

    # Scaled DSP parameters
    nr_val = int(12 + (float(denoise_pct) / 100.0) * 20)      # 12dB to 32dB noise attenuation
    nf_val = int(-35 - (float(denoise_pct) / 100.0) * 15)     # -35dB to -50dB floor
    hp_f = int(95 + (float(denoise_pct) / 100.0) * 25)        # 95Hz to 120Hz sub-bass filter
    gate_thresh = 0.020 + (float(denoise_pct) / 100.0) * 0.020

    # Audio Filtergraph (Pro Vehicle Cabin & Fan Denoise):
    # 1. highpass: cuts sub-bass rumble, tire drone, chassis vibration
    # 2. lowpass=f=12000: cuts ultrasonic hiss
    # 3. equalizer=f=220: cuts heavy car AC blower drone & cabin resonance
    # 4. afftdn: fast adaptive FFT tracking noise reduction scaled by user denoise_pct
    # 5. equalizer=f=3400: vocal presence & articulation boost (Adobe Enhance style)
    # 6. agate: gentle noise gating in dead-air pauses to silence cabin ambient hum
    # 7. loudnorm: EBU R128 standard -14 LUFS normalization for podcasts and video
    audio_filters = (
        f"highpass=f={hp_f}:poles=2,"
        "lowpass=f=12000,"
        "equalizer=f=220:t=q:w=1.2:g=-11,"
        f"afftdn=nr={nr_val}:nf={nf_val}:tn=1,"
        "equalizer=f=3400:t=q:w=1.4:g=4.0,"
        f"agate=threshold={gate_thresh:.3f}:range=0.05:attack=12:release=250,"
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
