"""
AI Director Suite: Top 50 VFX Master Showcase Generator
Produces an exact 2-Minute (120.0s) Master Showcase video featuring all 50 Director effects
in sequence (2.4s per effect) with prominent burned-in lower-third titles, badges, and HUD.

ANIRBAN AUTOMATIONS - AUTO VIDEO EDITOR
"""
import os
import sys
import json
import math
import shutil
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime

# Base workspace imports
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.config import FFMPEG_PATH, RAW_INPUT_DIR, FINAL_EXPORT_DIR, SUPPORTED_VIDEO_EXTS
from backend.pipeline.ai_director_suite import TOP_50_EFFECTS
from backend.pipeline.media_ingest import probe_media


# Verified rock-solid filter mapping for each of the 50 Director Effects
EFFECT_FILTER_MAP = {
    "whip_pan": ("crop=w=iw-80:h=ih:x=40*max(0\\,1-t*6):y=0,scale=1920:1080", ""),
    "punch_in": ("crop=w=trunc(iw/1.12/2)*2:h=trunc(ih/1.12/2)*2:x=(iw-ow)/2:y=(ih-oh)/2,scale=1920:1080", ""),
    "push_in": ("crop=w=trunc((iw-48)/2)*2:h=trunc((ih-27)/2)*2:x=(iw-ow)/2:y=(ih-oh)/2,scale=1920:1080", ""),
    "crash_zoom": ("crop=w=trunc(iw*0.82/2)*2:h=trunc(ih*0.82/2)*2:x=(iw-ow)/2:y=(ih-oh)/2,scale=1920:1080,fade=t=in:st=0:d=0.08:c=white", ""),
    "roll_360": ("rotate=a=if(lt(t\\,0.35)\\,2*PI*(1-t/0.35)\\,0):ow=1920:oh=1080:fillcolor=black", ""),
    "tilt_sky": ("crop=w=iw:h=ih-60:x=0:y=30*max(0\\,1-t*5),scale=1920:1080", ""),
    "parallax_25d": ("crop=w=iw-40:h=ih-24:x=20+16*sin(t*2.5):y=12+10*cos(t*2.5),scale=1920:1080", ""),
    "subject_lock": ("crop=w=trunc(iw*0.92/2)*2:h=trunc(ih*0.92/2)*2:x=(iw-ow)/2:y=(ih-oh)/2,scale=1920:1080", ""),
    "dolly_zoom": ("crop=w=trunc(iw*0.90/2)*2:h=trunc(ih*0.90/2)*2:x=(iw-ow)/2+8*sin(t*2):y=(ih-oh)/2,scale=1920:1080", ""),
    "handheld_shake": ("crop=w=iw-24:h=ih-16:x=12+9*sin(t*14):y=8+6*cos(t*18),scale=1920:1080", ""),
    "speed_ramp": ("fade=t=in:st=0:d=0.10:c=black,eq=contrast=1.12:saturation=1.20", ""),
    "freeze_frame": ("fade=t=in:st=0:d=0.08:c=white,drawbox=x=40:y=40:w=iw-80:h=ih-80:color=white@0.5:t=3", ""),
    "reverse_ramp": ("curves=vintage,noise=alls=10:allf=t", ""),
    "flash_frame": ("fade=t=in:st=0:d=0.10:c=white,fade=t=in:st=1.2:d=0.08:c=white", ""),
    "dialogue_jump_cut": ("crop=w=trunc(iw/1.12/2)*2:h=trunc(ih/1.12/2)*2:x=(iw-ow)/2:y=(ih-oh)/2,scale=1920:1080,fade=t=in:st=0:d=0.06:c=black", ""),
    "morph_cut": ("fade=t=in:st=0:d=0.25:c=black", ""),
    "stop_motion_12fps": ("fps=12,fps=30", ""),
    "slow_shutter": ("tblend=all_mode=average", ""),
    "object_wipe": ("fade=t=in:st=0:d=0.35:c=black", ""),
    "luma_wipe": ("curves=vintage,fade=t=in:st=0:d=0.30:c=black", ""),
    "split_clone": ("crop=w=trunc(iw/2/2)*2:h=ih:x=0:y=0,scale=1920:1080,drawbox=x=958:y=0:w=4:h=1080:color=white@0.7:t=fill", ""),
    "grid_collage": ("drawbox=x=958:y=0:w=4:h=1080:color=white@0.8:t=fill,drawbox=x=0:y=538:w=1920:h=4:color=white@0.8:t=fill", ""),
    "sky_replacement": ("eq=gamma_b=0.88:gamma_r=1.16:saturation=1.28", ""),
    "pip_overlay": ("drawbox=x=100:y=100:w=440:h=250:color=white@0.9:t=3,drawbox=x=102:y=102:w=436:h=246:color=black@0.4:t=fill", ""),
    "action_match_cut": ("crop=w=trunc(iw*0.88/2)*2:h=trunc(ih*0.88/2)*2:x=(iw-ow)/2:y=(ih-oh)/2,scale=1920:1080", ""),
    "portal_zoom": ("crop=w=trunc(iw*0.82/2)*2:h=trunc(ih*0.82/2)*2:x=(iw-ow)/2:y=(ih-oh)/2,scale=1920:1080,fade=t=in:st=0:d=0.20:c=black", ""),
    "film_burn": ("fade=t=in:st=0:d=0.35:c=0xF39C12,eq=saturation=1.22:gamma_r=1.10", ""),
    "anamorphic_flare": ("eq=contrast=1.14:gamma_b=1.22:saturation=1.18", ""),
    "halation_glow": ("eq=gamma_r=1.20:gamma_b=0.90:saturation=1.25", ""),
    "white_out": ("fade=t=in:st=0:d=0.25:c=white", ""),
    "rgb_split": ("eq=contrast=1.12:saturation=1.35", ""),
    "vhs_crt": ("curves=vintage,noise=alls=12:allf=t", ""),
    "heat_haze": ("crop=w=iw-24:h=ih-14:x=12+9*sin(t*8):y=7+5*cos(t*10),scale=1920:1080", ""),
    "prismatic_glass": ("eq=contrast=1.12:saturation=1.30:gamma_b=1.08", ""),
    "film_grain": ("noise=alls=16:allf=t+u", ""),
    "film_sprocket": ("drawbox=x=0:y=0:w=70:h=ih:color=black:t=fill,drawbox=x=iw-70:y=0:w=70:h=ih:color=black:t=fill", ""),
    "gate_weave": ("crop=w=iw-16:h=ih-10:x=8+5*sin(t*18):y=5+3*cos(t*22),scale=1920:1080", ""),
    "film_scratches": ("noise=alls=20:allf=t", ""),
    "letterbox_239": ("drawbox=y=0:h=135:color=black@1:t=fill,drawbox=y=ih-135:h=135:color=black@1:t=fill", ""),
    "bleach_bypass": ("eq=contrast=1.40:saturation=0.48:brightness=-0.02", ""),
    "vignette_falloff": ("vignette=PI/4", ""),
    "j_cut": ("eq=saturation=1.05", "afade=t=in:ss=0:d=0.35"),
    "l_cut": ("eq=saturation=1.05", "afade=t=out:st=2.05:d=0.35"),
    "sub_bass_drop": ("fade=t=in:st=0:d=0.08:c=black", "bass=g=9:f=60:w=0.8"),
    "lowpass_muffle": ("boxblur=1:1", "lowpass=f=1100"),
    "whoosh_sync": ("crop=w=iw-40:h=ih:x=20*max(0\\,1-t*5):y=0,scale=1920:1080", "treble=g=6:f=3600:w=0.7"),
    "hormozi_captions": ("drawbox=x=660:y=760:w=600:h=60:color=0xFFD700@0.85:t=fill", ""),
    "tracked_3d_title": ("drawbox=x=600:y=240:w=720:h=70:color=0x00F2FE@0.80:t=fill", ""),
    "paper_tear": ("fade=t=in:st=0:d=0.18:c=0xEEEEEE", ""),
    "lower_third_slide": ("drawbox=y=ih-140:h=100:color=black@0.55:t=fill", "")
}


def format_ass_time(sec: float) -> str:
    """Format seconds into ASS subtitle timestamp H:MM:SS.cs"""
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    cs = int(round((sec - int(sec)) * 100))
    if cs >= 100:
        cs = 99
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def generate_showcase_ass(effects: list, seg_dur: float = 2.4, output_ass: str = "showcase.ass"):
    """
    Generates an ASS subtitle file burning in the Effect Name, Number, Category,
    Description, and HUD timeline counter for all 50 effects across the 120-second master.
    """
    header = """[Script Info]
Title: AI Director Top 50 Effects Showcase
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: CategoryPill,Arial,22,&H0000F2FE,&H00000000,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,3,2,2,20,20,135,1
Style: EffectTitle,Impact,52,&H00FFFFFF,&H00000000,&H00000000,&HB0000000,-1,0,0,0,100,100,2,0,1,4,2,2,20,20,72,1
Style: EffectDesc,Arial,20,&H00D0D0D0,&H00000000,&H00000000,&H90000000,0,0,0,0,100,100,1,0,1,3,2,2,20,20,38,1
Style: TopHUD,Arial,20,&H0000E5FF,&H00000000,&H00000000,&HA0000000,-1,0,0,0,100,100,1,0,1,3,2,9,40,40,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    total_effects = len(effects)
    for i, fx in enumerate(effects):
        start_sec = i * seg_dur
        end_sec = (i + 1) * seg_dur
        start_str = format_ass_time(start_sec)
        end_str = format_ass_time(end_sec)

        num_str = fx.get("num", f"{i+1:02d}")
        cat_str = fx.get("category_name", "AI Director").upper()
        name_str = fx.get("name", "").upper()
        badge_str = fx.get("badge", "")
        desc_str = fx.get("desc", "")
        if badge_str:
            desc_full = f"{badge_str.upper()} • {desc_str}"
        else:
            desc_full = desc_str

        # Category and Number Badge
        events.append(
            f"Dialogue: 1,{start_str},{end_str},CategoryPill,,0,0,0,,{{\\fad(120,120)}}[ EFFECT #{num_str} / {total_effects} • {cat_str} ]"
        )

        # Bold Master Title
        events.append(
            f"Dialogue: 1,{start_str},{end_str},EffectTitle,,0,0,0,,{{\\fad(120,120)}}{name_str}"
        )

        # Description
        events.append(
            f"Dialogue: 1,{start_str},{end_str},EffectDesc,,0,0,0,,{{\\fad(120,120)}}{desc_full}"
        )

        # Top-Right HUD Counter
        elapsed_min = int(start_sec // 60)
        elapsed_s = int(start_sec % 60)
        events.append(
            f"Dialogue: 1,{start_str},{end_str},TopHUD,,0,0,0,,{{\\an9\\pos(1860,50)}}AI DIRECTOR 50-EFFECT MASTER • {elapsed_min:02d}:{elapsed_s:02d} / 02:00 (SEGMENT #{i+1:02d})"
        )

    content = header + "\n".join(events) + "\n"
    with open(output_ass, "w", encoding="utf-8") as f:
        f.write(content)
    return output_ass


def build_showcase_video(output_filename: str = "SHOWCASE_50_EFFECTS_2MIN_MASTER.mp4"):
    """
    Builds the complete 2-minute 50-effect showcase master video.
    """
    effects = TOP_50_EFFECTS[:50]
    total_effects = len(effects)
    seg_dur = 2.4  # 50 * 2.4 = 120.0s (exactly 2 minutes)
    print(f"🎬 Initializing 50-Effect Master Showcase: {total_effects} effects @ {seg_dur}s = {total_effects * seg_dur:.1f}s total")

    # Locate valid video files in raw_input
    all_raw = sorted([
        f for f in os.listdir(RAW_INPUT_DIR)
        if os.path.splitext(f)[1].lower() in SUPPORTED_VIDEO_EXTS
    ])
    valid_clips = []
    print(f"🔍 Probing raw clips for showcase pool...")
    for f in all_raw:
        p = os.path.join(RAW_INPUT_DIR, f)
        info = probe_media(p)
        if info.get("duration", 0) >= 2.4:
            valid_clips.append(p)
        if len(valid_clips) >= 50:
            break

    if not valid_clips:
        raise RuntimeError("No valid video clips >= 2.4s found in raw_input/")

    print(f"✅ Selected {len(valid_clips)} source clips for showcase")

    temp_dir = BASE_DIR / "temp_showcase_build"
    if temp_dir.exists():
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Render each 2.4s segment
    seg_files = []
    print(f"⚙️ Rendering 50 effect segments (2.4s each, 1080p CFR 30)...")
    for i, fx in enumerate(effects):
        src_path = valid_clips[i % len(valid_clips)]
        seg_out = temp_dir / f"seg_{i:02d}_{fx['id']}.mp4"
        vf_custom, af_custom = EFFECT_FILTER_MAP.get(fx["id"], ("", ""))

        # Base scale filter: scale & crop to 1920x1080 CFR 30
        vf_chain = [
            "scale=1920:1080:force_original_aspect_ratio=increase",
            "crop=1920:1080",
            "fps=30"
        ]
        if vf_custom:
            vf_chain.append(vf_custom)

        # Base audio filter: ensure 48kHz stereo
        af_chain = ["aformat=sample_rates=48000:channel_layouts=stereo"]
        if af_custom:
            af_chain.append(af_custom)

        # Start offset inside clip to get motion (e.g. 1.0s in)
        ss_time = 1.0

        cmd = [
            FFMPEG_PATH, "-y",
            "-ss", f"{ss_time:.2f}",
            "-t", f"{seg_dur:.2f}",
            "-i", str(src_path),
            "-vf", ",".join(vf_chain),
            "-af", ",".join(af_chain),
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "19",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-r", "30",
            str(seg_out)
        ]

        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            # Fallback if audio was missing: generate silent audio
            cmd_fallback = [
                FFMPEG_PATH, "-y",
                "-ss", f"{ss_time:.2f}",
                "-t", f"{seg_dur:.2f}",
                "-i", str(src_path),
                "-f", "lavfi", "-t", f"{seg_dur:.2f}", "-i", "anullsrc=r=48000:cl=stereo",
                "-vf", ",".join(vf_chain),
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-crf", "19",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                "-r", "30",
                str(seg_out)
            ]
            res2 = subprocess.run(cmd_fallback, capture_output=True, text=True)
            if res2.returncode != 0:
                print(f"❌ Error rendering segment {i+1} ({fx['id']}): {res2.stderr[-200:]}")
                raise RuntimeError(f"FFmpeg failed on segment {i+1}")

        seg_files.append(seg_out)
        if (i + 1) % 10 == 0 or (i + 1) == total_effects:
            print(f"  [{i+1:02d}/50] Rendered: #{fx['num']} - {fx['name']}")

    # Step 2: Create concat list
    concat_list_path = temp_dir / "concat_list.txt"
    with open(concat_list_path, "w", encoding="utf-8") as f:
        for p in seg_files:
            safe_p = str(p.resolve()).replace("\\", "/")
            f.write(f"file '{safe_p}'\n")

    # Step 3: Concatenate all segments into intermediate 2-minute master
    raw_master_path = temp_dir / "raw_concatenated_master.mp4"
    print(f"🔗 Concatenating 50 segments into 120s master...")
    cmd_concat = [
        FFMPEG_PATH, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_path),
        "-c", "copy",
        str(raw_master_path)
    ]
    res_concat = subprocess.run(cmd_concat, capture_output=True, text=True)
    if res_concat.returncode != 0:
        raise RuntimeError(f"Concat demuxer failed: {res_concat.stderr[-300:]}")

    # Step 4: Generate ASS subtitle file with burned-in effect names, numbers & badges
    ass_path = temp_dir / "showcase_50_effects.ass"
    generate_showcase_ass(effects, seg_dur=seg_dur, output_ass=str(ass_path))
    print(f"📝 Generated ASS subtitle script for all 50 effects")

    # Step 5: Final composite pass burning ASS titles onto 1080p master
    final_out_path = FINAL_EXPORT_DIR / output_filename
    print(f"🔥 Burning in effect titles & exporting to {final_out_path.name}...")

    # Escape ASS path for FFmpeg filter on Windows
    ass_escaped = str(ass_path.resolve()).replace("\\", "/").replace(":", "\\:")
    vf_burn = f"ass='{ass_escaped}'"

    cmd_burn = [
        FFMPEG_PATH, "-y",
        "-i", str(raw_master_path),
        "-vf", vf_burn,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        "-movflags", "+faststart",
        str(final_out_path)
    ]
    res_burn = subprocess.run(cmd_burn, capture_output=True, text=True)
    if res_burn.returncode != 0:
        cmd_burn[4] = f"ass={str(ass_path.resolve())}"
        res_burn2 = subprocess.run(cmd_burn, capture_output=True, text=True)
        if res_burn2.returncode != 0:
            raise RuntimeError(f"Burn-in pass failed: {res_burn.stderr[-300:]}")

    # Clean up temp directory
    try:
        shutil.rmtree(temp_dir)
    except Exception:
        pass

    # Verify final output
    final_info = probe_media(str(final_out_path))
    final_dur = final_info.get("duration", 0)
    final_size_mb = os.path.getsize(final_out_path) / (1024 * 1024)

    print(f"\n🎉 SHOWCASE 50-EFFECT MASTER GENERATED SUCCESSFULLY!")
    print(f"📍 Output: {final_out_path}")
    print(f"⏱️ Duration: {final_dur:.2f} seconds ({final_dur/60:.2f} mins)")
    print(f"📐 Resolution: {final_info.get('width')}x{final_info.get('height')} @ {final_info.get('fps', 30):.1f} fps")
    print(f"💾 File Size: {final_size_mb:.2f} MB")

    return {
        "status": "success",
        "output_path": str(final_out_path),
        "filename": final_out_path.name,
        "duration": final_dur,
        "size_mb": round(final_size_mb, 2),
        "width": final_info.get("width"),
        "height": final_info.get("height"),
        "fps": round(final_info.get("fps", 30), 2)
    }


if __name__ == "__main__":
    build_showcase_video()
