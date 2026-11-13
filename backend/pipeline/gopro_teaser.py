"""
GoPro / YouTube Creator Style 30-Second Summary Video Generator
Assembles an electrifying 30-second teaser trailer of the entire trip:
- 16-18 punchy fast cuts (0.8s - 1.8s each)
- High-energy camera motions (whip zoom-in, zoom-out, pan-left, pan-right, tilt-up, move-down, speed ramp)
- YouTube Create / GoPro style kinetic pop captions with emojis
- Upbeat rhythmic montage sequencing
- Universal MP4 H.264 High Profile Level 4.2 YUV420P for native Windows Media Player playback
"""
import subprocess
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.config import FFMPEG_PATH, RAW_INPUT_DIR, FINAL_EXPORT_DIR, UPLOADS_DIR, EXPORTS_DIR
from backend.pipeline.media_ingest import probe_media
from backend.pipeline.smart_orientation import analyze_clip_orientation

# 30-Second GoPro Shot Blueprint
# (clip_name, start_time, duration, motion_type, caption_text, caption_emoji)
GOPRO_BLUEPRINT = [
    ("IMG_0411.MOV", 0.0, 1.2, "whip_zoom_in", "CHASING HIMACHAL", "🏔️⚡"),
    ("IMG_0412.MOV", 0.0, 1.2, "ken_burns_up", "PACK YOUR BAGS", "🎒✨"),
    ("IMG_E0418.MOV", 128.0, 1.8, "punch_zoom", "RAM DALAL LUXURY BUS", "🚌🔥"),
    ("IMG_0419.MOV", 0.0, 1.5, "drone_ascend", "MORNING VALLEY REVEAL", "🌄🌲"),
    ("IMG_0420.MOV", 2.0, 1.5, "speed_ramp", "SPEEDING INTO THE NIGHT", "🚀💨"),
    ("IMG_0421.MOV", 5.0, 1.6, "whip_pan_right", "HIGHWAY VIBES", "🛣️⚡"),
    ("IMG_0423.MOV", 2.0, 1.6, "zoom_out_reveal", "CABIN COMFORT", "💺✨"),
    ("IMG_E0429.MOV", 15.0, 1.8, "whip_pan_left", "CURVING HIGHWAYS", "🏔️🛣️"),
    ("IMG_0433.MOV", 0.0, 1.5, "drone_fly_through", "HIMALAYAN FOOTHILLS", "🌲⛰️"),
    ("IMG_E0439.MOV", 10.0, 1.8, "punch_zoom", "THE JOURNEY CONTINUES", "🎬🔥"),
    ("IMG_E0441.MOV", 8.0, 1.8, "pan_left", "RISING PEAKS", "❄️🏔️"),
    ("IMG_0445.MOV", 10.0, 1.6, "whip_pan_right", "MOUNTAIN PASS", "💨⛰️"),
    ("IMG_0446.MOV", 5.0, 1.6, "tilt_up", "TALL PINES", "🌲☀️"),
    ("IMG_0461.MOV", 3.0, 1.8, "orbital_sweep", "EPIC ELEVATION", "☁️🏔️"),
    ("IMG_0463.MOV", 0.0, 1.6, "drone_ascend", "VALLEY OF THE GODS", "🌲✨"),
    ("IMG_0466.MOV", 0.0, 1.6, "zoom_in", "RIVER CANYON CROSSING", "🌊🌉"),
    ("IMG_0470.MOV", 0.0, 1.8, "drone_fly_through", "SNOW-CAPPED WONDER", "❄️🔥"),
    ("IMG_0471.MOV", 0.0, 2.8, "slow_cinematic", "RAM DALAL EXPEDITION", "🏔️🎉")
]

def build_motion_filter(motion_type: str, duration: float, is_sideways: bool = False) -> str:
    """
    Constructs dynamic camera motion filter strings for FFmpeg.
    """
    frames = int(duration * 30)
    base_crop = "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080"

    if motion_type == "whip_zoom_in":
        return f"{base_crop},zoompan=z='min(1.0+in*{0.35/frames:.5f},1.35)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps=30"

    elif motion_type == "zoom_out_reveal":
        return f"{base_crop},zoompan=z='max(1.30-in*{0.30/frames:.5f},1.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps=30"

    elif motion_type == "whip_pan_right":
        return f"{base_crop},zoompan=z='1.15':x='(in/{frames})*(iw-iw/zoom)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps=30"

    elif motion_type == "whip_pan_left":
        return f"{base_crop},zoompan=z='1.15':x='(1.0-in/{frames})*(iw-iw/zoom)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps=30"

    elif motion_type == "tilt_up":
        return f"{base_crop},zoompan=z='1.15':x='iw/2-(iw/zoom/2)':y='(1.0-in/{frames})*(ih-ih/zoom)':d={frames}:s=1920x1080:fps=30"

    elif motion_type == "punch_zoom":
        return f"{base_crop},zoompan=z='if(lt(in,10),1.0+in*0.02,1.20)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps=30"

    elif motion_type == "drone_ascend":
        return f"{base_crop},zoompan=z='min(zoom+0.0015,1.20)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)-(in*0.6)':d={frames}:s=1920x1080:fps=30"

    elif motion_type == "drone_fly_through":
        return f"{base_crop},zoompan=z='min(zoom+0.0018,1.25)':x='iw/2-(iw/zoom/2)+sin(in/20)*25':y='ih/2-(ih/zoom/2)-in*0.3':d={frames}:s=1920x1080:fps=30"

    elif motion_type == "orbital_sweep":
        return f"{base_crop},zoompan=z='1.15':x='(in/{frames})*(iw-iw/zoom)':y='ih/2-(ih/zoom/2)+sin(in/25)*15':d={frames}:s=1920x1080:fps=30"

    elif motion_type == "speed_ramp":
        return f"{base_crop},setpts=0.75*PTS"

    else:
        # Default gentle Ken Burns push
        return f"{base_crop},zoompan=z='min(zoom+0.0010,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps=30"

def generate_gopro_teaser_ass(shots_info: list[dict], output_ass_path: str):
    """
    Generates high-energy YouTube Create / GoPro style bouncing yellow & cyan pop captions.
    Includes energetic emojis and glowing outline.
    """
    header = """[Script Info]
Title: GoPro 30s High Energy Teaser
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: GoProTitle,Montserrat Black,72,&H0000FFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,105,105,2,0,1,6,3,2,100,100,85,1
Style: GoProSub,Arial Black,54,&H00FFFF00,&H00FFFF00,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,5,2,2,100,100,35,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    current_time = 0.0

    def fmt_time(t):
        hrs = int(t // 3600)
        mins = int((t % 3600) // 60)
        secs = t % 60
        return f"{hrs:01d}:{mins:02d}:{secs:05.2f}"

    for shot in shots_info:
        dur = shot["duration"]
        start_t = current_time
        end_t = current_time + dur
        current_time = end_t

        title = shot.get("caption_text", "").upper()
        emoji = shot.get("caption_emoji", "")
        if title:
            # ASS kinetic zoom bounce: starts at 85% scale, bounces to 105% in 150ms
            bounce_fx = r"{\t(0,150,\fscx108\fscy108)\t(150,300,\fscx100\fscy100)}"
            events.append(
                f"Dialogue: 0,{fmt_time(start_t)},{fmt_time(end_t)},GoProTitle,,0,0,0,,{bounce_fx}{title} {emoji}"
            )

    with open(output_ass_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events) + "\n")

def build_gopro_30s_summary(
    output_filename: str = "MASTER_GOPRO_30S_SUMMARY.mp4",
    progress_callback = None
) -> str:
    """
    Assembles the complete 30.0s GoPro / YouTube Creator style summary video.
    """
    final_path = FINAL_EXPORT_DIR / output_filename
    temp_segments = []
    concat_lines = []
    shots_info = []

    print("Building GoPro Style 30-Second Teaser...")
    if progress_callback:
        progress_callback(10, "Designing GoPro 30s Kinetic Timeline...")

    # Discover shots: check blueprint first, or dynamically adapt to ANY raw_input clips
    active_shots = []
    for fname, start_s, dur, motion, title, emoji in GOPRO_BLUEPRINT:
        clip_p = RAW_INPUT_DIR / fname
        if clip_p.exists():
            active_shots.append((clip_p, start_s, dur, motion, title, emoji))

    # If fewer than 5 blueprint clips exist, dynamically build a 30s montage from active raw clips!
    if len(active_shots) < 5:
        exts = {".mov", ".mp4", ".m4v"}
        all_raw = sorted([f for f in RAW_INPUT_DIR.iterdir() if f.is_file() and f.suffix.lower() in exts])
        all_raw = [f for f in all_raw if not any(w in f.name.lower() for w in ["test", "sample"])]

        dynamic_motifs = [
            ("whip_zoom_in", "FULL ON THROTTLE", "⚡🚗"),
            ("orbital_sweep", "HIGHWAY EXPEDITION", "🛣️✨"),
            ("speed_ramp", "ROAD TRIP VIBES", "🚀💨"),
            ("drone_fly_through", "INTO THE HORIZON", "🌄🔥"),
            ("punch_zoom", "PURE ENERGY", "🎉💪"),
            ("tilt_up", "NEXT DESTINATION", "📍✨"),
            ("whip_pan_right", "SPEEDING AHEAD", "💨⚡"),
            ("drone_ascend", "PANORAMIC CRUISE", "🏞️🌟"),
            ("zoom_out_reveal", "UNSTOPPABLE", "🌟💪"),
            ("slow_cinematic", "MEMORIES MADE", "🎬❤️")
        ]

        if all_raw:
            num_clips = min(len(all_raw), 14)
            slice_dur = round(30.0 / num_clips, 2)
            active_shots = []
            for i in range(num_clips):
                cp = all_raw[i]
                meta = probe_media(str(cp))
                file_dur = meta.get("duration", 5.0)
                st = 0.5 if file_dur > (slice_dur + 1.0) else 0.0
                m_type, title, emoji = dynamic_motifs[i % len(dynamic_motifs)]
                active_shots.append((cp, st, slice_dur, m_type, title, emoji))

    total_shots = len(active_shots)
    if total_shots == 0:
        raise RuntimeError("No raw video clips found in raw_input/ to generate GoPro teaser.")

    for idx, (clip_p, start_s, dur, motion, title, emoji) in enumerate(active_shots):
        fname = clip_p.name
        pct = int(15 + (idx / total_shots) * 65)
        if progress_callback:
            progress_callback(pct, f"[{idx+1}/{total_shots}] Animating {fname} ({motion})")

        orient_info = analyze_clip_orientation(str(clip_p))
        is_sideways = orient_info.get("use_noautorotate", False)

        seg_out = UPLOADS_DIR / f"gopro_seg_{idx:02d}_{clip_p.stem}.mp4"

        # Motion and orientation filter
        motion_vf = build_motion_filter(motion, dur, is_sideways)
        vf_chain = [
            motion_vf,
            "eq=saturation=1.20:contrast=1.06:brightness=0.01",
            "format=yuv420p"
        ]

        input_flags = ["-noautorotate"] if is_sideways else []

        fade_dur = min(0.040, dur / 3.0)
        fade_out_st = max(0.0, dur - fade_dur)
        af = f"afade=t=in:ss=0:d={fade_dur:.3f},afade=t=out:st={fade_out_st:.3f}:d={fade_dur:.3f},aformat=sample_rates=48000:channel_layouts=stereo"

        cmd = [
            FFMPEG_PATH,
            "-y"
        ] + input_flags + [
            "-ss", f"{start_s:.2f}",
            "-t", f"{dur:.2f}",
            "-i", str(clip_p),
            "-vf", ",".join(vf_chain),
            "-af", af,
            "-r", "30",
            "-fps_mode", "cfr",
            "-c:v", "libx264",
            "-preset", "faster",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-video_track_timescale", "30000",
            "-c:a", "aac",
            "-ar", "48000",
            "-ac", "2",
            "-b:a", "192k",
            "-shortest",
            str(seg_out)
        ]

        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            temp_segments.append(str(seg_out))
            escaped_p = str(seg_out).replace("\\", "/")
            concat_lines.append(f"file '{escaped_p}'")
            shots_info.append({"duration": dur, "caption_text": title, "caption_emoji": emoji})
        except Exception as e:
            print(f"Warning building teaser shot {idx} ({fname}): {e}")

    if not concat_lines:
        raise RuntimeError("No teaser shots could be generated.")

    # Concat all shots
    concat_txt = UPLOADS_DIR / "gopro_teaser_concat.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(concat_lines))

    # Generate ASS bouncing kinetic pop captions
    ass_path = EXPORTS_DIR / "gopro_kinetic_captions.ass"
    generate_gopro_teaser_ass(shots_info, str(ass_path))
    escaped_ass = str(ass_path).replace("\\", "/").replace(":", "\\:")

    if progress_callback:
        progress_callback(85, "Burning YouTube Creator Kinetic Pop Captions...")

    # Final Master Assembly with Burned Kinetic Captions
    cmd_final = [
        FFMPEG_PATH,
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_txt),
        "-vf", f"subtitles='{escaped_ass}',format=yuv420p",
        "-r", "30",
        "-fps_mode", "cfr",
        "-c:v", "libx264",
        "-profile:v", "high",
        "-level", "4.2",
        "-preset", "faster",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-colorspace", "bt709",
        "-color_primaries", "bt709",
        "-color_trc", "bt709",
        "-video_track_timescale", "30000",
        "-c:a", "aac",
        "-ar", "48000",
        "-ac", "2",
        "-b:a", "192k",
        "-movflags", "+faststart",
        str(final_path)
    ]
    subprocess.run(cmd_final, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    if progress_callback:
        progress_callback(100, f"GoPro 30s Master Complete: {output_filename}")

    print(f"GoPro 30-Second Summary Video rendered successfully to: {final_path}")
    return str(final_path)

if __name__ == "__main__":
    build_gopro_30s_summary()
