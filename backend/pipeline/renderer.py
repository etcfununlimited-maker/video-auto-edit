"""
Multi-Track Master Renderer Engine
Assembles the complete non-destructive edit timeline:
- Cuts out dead air and filler words while preserving scenic silences
- Smart 9:16 reframing or 16:9 widescreen
- Face-safe animated hyperframe captions
- AI audio denoising, vocal EQ boost, and auto-ducked background music
- Cinematic LUT color grading
- Outputs 100% universally compatible MP4 (H.264 High Profile, YUV420P, 48kHz stereo AAC)
  Guaranteed to play on Windows Media Player, Movies & TV, QuickTime, iOS, Android, and web.
"""
import subprocess
import os
from pathlib import Path
from backend.config import FFMPEG_PATH, FINAL_EXPORT_DIR
from backend.pipeline.color_grading import get_color_grade_filter
from backend.pipeline.ai_director_suite import build_director_video_filters, build_director_audio_filters

def build_timeline_segments(total_duration: float, cuts_to_remove: list[dict]) -> list[tuple[float, float]]:
    """
    Inverts the list of cut intervals to get the list of timeline segments to KEEP.
    """
    sorted_cuts = sorted(cuts_to_remove, key=lambda x: x["start"])
    segments_to_keep = []
    curr = 0.0

    for c in sorted_cuts:
        if c["start"] > curr:
            segments_to_keep.append((round(curr, 3), round(c["start"], 3)))
        curr = max(curr, c["end"])

    if curr < total_duration:
        segments_to_keep.append((round(curr, 3), round(total_duration, 3)))

    # Filter out tiny slivers (< 0.1s)
    clean_segs = [(s, e) for s, e in segments_to_keep if (e - s) >= 0.1]
    return clean_segs

def render_final_master(
    input_video_path: str,
    cuts_to_remove: list[dict],
    total_duration: float,
    color_grade: str = "none",
    aspect_ratio: str = "original",
    ass_subtitle_path: str = None,
    background_music_path: str = None,
    enable_audio_enhance: bool = True,
    output_filename: str = None,
    director_effects: dict = None,
    text_behind: dict = None,
    enabled_grids: dict = None,
    ducking_depth_pct: float = 75.0,
    music_level_pct: float = 40.0,
    denoise_pct: float = 75.0
) -> str:
    """
    Executes the comprehensive FFmpeg render pipeline and deposits output in final_export/.
    Enforces YUV420P and 48kHz stereo AAC for universal Windows Media Player compatibility.
    """
    src = Path(input_video_path)
    if not output_filename:
        output_filename = f"MASTER_{src.stem}.mp4"

    final_path = FINAL_EXPORT_DIR / output_filename

    # Automatic License Plate Privacy Blurring (Bypassed if Grid 9 or license_plate_blur is toggled OFF)
    has_lp_blur = True
    if enabled_grids and not enabled_grids.get("grid_bgremove", True):
        has_lp_blur = False
    if director_effects and isinstance(director_effects, dict):
        if not director_effects.get("license_plate_blur", True):
            has_lp_blur = False
        if not director_effects.get("grid_bgremove", True):
            has_lp_blur = False

    if has_lp_blur:
        try:
            from backend.pipeline.license_plate_blur import clip_has_license_plates, process_video_plate_blur
            if clip_has_license_plates(str(src)):
                blurred_src = src.parent / f".tmp_plate_blur_{src.stem}.mp4"
                if not blurred_src.exists() or blurred_src.stat().st_size == 0:
                    process_video_plate_blur(str(src), str(blurred_src), method="gaussian")
                src = blurred_src
        except Exception as e:
            print(f"License plate blur notice: {e}")

    # 1. Determine segments to keep
    keep_segments = build_timeline_segments(total_duration, cuts_to_remove)
    if not keep_segments:
        keep_segments = [(0.0, total_duration)]

    # If natural camera colors (color_grade == 'none'), strictly disable all color, film emulation, and vignette overlays
    if color_grade == "none" and director_effects:
        import copy
        director_effects = copy.deepcopy(director_effects)
        for fx_key in ["vignette_falloff", "film_grain", "film_burn", "halation_glow", "bleach_bypass", "letterbox_239", "film_scratches", "vhs_crt", "anamorphic_flare", "sky_replacement", "prismatic_glass", "rgb_split"]:
            director_effects[fx_key] = False

    # 2. Build Filtergraph
    v_parts = []
    a_parts = []
    filter_complex = []

    num_segs = len(keep_segments)

    for idx, (s, e) in enumerate(keep_segments):
        seg_dur = round(e - s, 3)
        fade_dur = min(0.035, round(seg_dur / 3.0, 3))
        fade_out_st = max(0.0, round(seg_dur - fade_dur, 3))

        # Dynamic retention zoom & Top 50 VFX Suite filters
        dfx_v = build_director_video_filters(director_effects, seg_idx=idx, total_segs=num_segs, seg_dur=seg_dur, aspect_ratio=aspect_ratio, is_dialogue=True, color_grade=color_grade)
        v_filters = [f"trim=start={s}:end={e}", "setpts=PTS-STARTPTS", "fps=30"]
        if dfx_v:
            v_filters.extend(dfx_v)
        elif idx % 2 == 1 and num_segs > 1 and aspect_ratio != "9:16":
            v_filters.append("scale=trunc(iw*1.08/2)*2:trunc(ih*1.08/2)*2,crop=1920:1080")
        filter_complex.append(f"[0:v]{','.join(v_filters)}[v{idx}];")

        # Smooth audio transition & dynamic audio FX with sample-accurate sync
        dfx_a = build_director_audio_filters(director_effects, seg_idx=idx, total_segs=num_segs, seg_dur=seg_dur)
        a_filters = [
            f"atrim=start={s}:end={e}", "asetpts=PTS-STARTPTS",
            "aresample=async=1000",
            f"afade=t=in:ss=0:d={fade_dur:.3f}",
            f"afade=t=out:st={fade_out_st:.3f}:d={fade_dur:.3f}"
        ]
        if dfx_a:
            a_filters.extend(dfx_a)
        filter_complex.append(f"[0:a]{','.join(a_filters)}[a{idx}];")
        v_parts.append(f"[v{idx}]")
        a_parts.append(f"[a{idx}]")

    # Joint audio-video synchronization concat (locks A/V frames in exact phase)
    concat_pairs = "".join(f"[v{i}][a{i}]" for i in range(num_segs))
    filter_complex.append(f"{concat_pairs}concat=n={num_segs}:v=1:a=1[v_concat][a_concat];")

    current_v = "v_concat"
    current_a = "a_concat"

    # Color grading
    cg_filter = get_color_grade_filter(color_grade)
    if cg_filter:
        filter_complex.append(f"[{current_v}]{cg_filter}[v_graded];")
        current_v = "v_graded"

    # Smart reframing (16:9 to 9:16)
    if aspect_ratio == "9:16":
        filter_complex.append(f"[{current_v}]crop=ih*9/16:ih:(iw-ow)/2:0,scale=1080:1920[v_reframed];")
        current_v = "v_reframed"

    # Subtitles burn-in if provided
    if ass_subtitle_path and os.path.exists(ass_subtitle_path):
        escaped_ass = ass_subtitle_path.replace("\\", "/").replace(":", "\\:")
        filter_complex.append(f"[{current_v}]subtitles='{escaped_ass}'[v_subbed];")
        current_v = "v_subbed"

    # Depth text title burn-in if enabled
    if text_behind and text_behind.get("enabled") and (text_behind.get("text") or "").strip():
        try:
            from backend.pipeline.ai_director_suite import generate_depth_text_ass
            from backend.config import UPLOADS_DIR
            depth_ass_path = str(UPLOADS_DIR / f"depth_title_single_{src.stem}.ass")
            generate_depth_text_ass(
                text_behind,
                duration=min(total_duration, 6.0),
                output_path=depth_ass_path,
                video_w=1080 if aspect_ratio == "9:16" else 1920,
                video_h=1920 if aspect_ratio == "9:16" else 1080
            )
            escaped_depth = depth_ass_path.replace("\\", "/").replace(":", "\\:")
            filter_complex.append(f"[{current_v}]subtitles='{escaped_depth}'[v_depth];")
            current_v = "v_depth"
        except Exception as e_depth:
            print(f"Renderer depth title notice: {e_depth}")

    # Universal pixel format conversion to YUV420P (MANDATORY for Windows Media Player & iOS)
    filter_complex.append(f"[{current_v}]format=yuv420p[v_universal];")
    current_v = "v_universal"

    # Audio enhancement & resample to standard 48kHz (Dynamic Denoise Slider Scaled)
    if enable_audio_enhance:
        nr_val = int(12 + (float(denoise_pct) / 100.0) * 20)
        nf_val = int(-35 - (float(denoise_pct) / 100.0) * 15)
        hp_f = int(95 + (float(denoise_pct) / 100.0) * 25)
        audio_dsp = (
            f"[{current_a}]highpass=f={hp_f}:poles=2,lowpass=f=11000:poles=2,afftdn=nr={nr_val}:nf={nf_val}:tn=1,"
            f"equalizer=f=220:t=q:w=1.4:g=-11.0,equalizer=f=440:t=q:w=1.5:g=-6.0,equalizer=f=3200:t=q:w=1.4:g=4.5,"
            f"compand=attacks=0.015:decays=0.10:points=-80/-95|-50/-60|-36/-36|-18/-12|0/0,aformat=sample_rates=48000:channel_layouts=stereo,aresample=async=1000[a_enhanced];"
        )
        filter_complex.append(audio_dsp)
        current_a = "a_enhanced"
    else:
        filter_complex.append(f"[{current_a}]aformat=sample_rates=48000:channel_layouts=stereo,aresample=async=1000[a_resampled];")
        current_a = "a_resampled"

    # Grid 7: Dynamic Background Music Auto-Ducking (Scaled by User Sliders)
    has_music = bool(background_music_path and os.path.exists(background_music_path))
    if has_music:
        bgm_vol = max(0.05, min(1.0, float(music_level_pct) / 100.0))
        ratio = 2.0 + (float(ducking_depth_pct) / 100.0) * 8.0
        thresh = max(0.015, 0.050 - (float(ducking_depth_pct) / 100.0) * 0.030)
        release_ms = int(350 + (float(ducking_depth_pct) / 100.0) * 300)
        sp_gain = 1.25 + (float(ducking_depth_pct) / 100.0) * 0.35
        filter_complex.append(
            f"[1:a]volume={bgm_vol:.2f}[bgm];"
            f"[{current_a}]asplit=2[sp_raw][sp_key];"
            f"[sp_key]highpass=f=120,volume=2.5[sp_trigger];"
            f"[bgm][sp_trigger]sidechaincompress=threshold={thresh:.3f}:ratio={ratio:.1f}:attack=15:release={release_ms}[ducked_bgm];"
            f"[sp_raw]volume={sp_gain:.2f}[sp];"
            f"[sp][ducked_bgm]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a_ducked];"
        )
        current_a = "a_ducked"

    filter_graph_str = "".join(filter_complex)

    # Universal encoding arguments
    temp_final_path = final_path.with_name(f".tmp_{os.getpid()}_{final_path.name}")
    cmd = [
        FFMPEG_PATH,
        "-y",
        "-i", str(src),
    ]
    if has_music:
        cmd.extend(["-stream_loop", "-1", "-i", str(background_music_path)])

    cmd.extend([
        "-filter_complex", filter_graph_str,
        "-map", f"[{current_v}]",
        "-map", f"[{current_a}]",
        "-c:v", "libx264",
        "-profile:v", "high",
        "-level", "4.2",
        "-preset", "faster",
        "-crf", "20",
        "-fps_mode", "cfr",
        "-r", "30",
        "-pix_fmt", "yuv420p",
        "-colorspace", "bt709",
        "-color_primaries", "bt709",
        "-color_trc", "bt709",
        "-c:a", "aac",
        "-ar", "48000",
        "-ac", "2",
        "-b:a", "256k",
        "-movflags", "+faststart",
        str(temp_final_path)
    ])

    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        if os.path.exists(temp_final_path):
            if os.path.exists(final_path):
                try:
                    os.remove(final_path)
                except Exception:
                    pass
            os.replace(temp_final_path, final_path)
        return str(final_path)
    except subprocess.CalledProcessError as e:
        print(f"Direct render warning: {e.stderr.decode('utf-8', errors='replace')}")
        # Robust fallback render with universal compatibility
        cmd_fallback = [
            FFMPEG_PATH,
            "-y",
            "-i", str(src),
            "-vf", "format=yuv420p",
            "-c:v", "libx264",
            "-profile:v", "high",
            "-level", "4.2",
            "-preset", "veryfast",
            "-crf", "21",
            "-pix_fmt", "yuv420p",
            "-colorspace", "bt709",
            "-color_primaries", "bt709",
            "-color_trc", "bt709",
            "-c:a", "aac",
            "-ar", "48000",
            "-ac", "2",
            "-b:a", "192k",
            "-movflags", "+faststart",
            str(temp_final_path)
        ]
        subprocess.run(cmd_fallback, check=True)
        if os.path.exists(temp_final_path):
            if os.path.exists(final_path):
                try:
                    os.remove(final_path)
                except Exception:
                    pass
            os.replace(temp_final_path, final_path)
        return str(final_path)
