"""
HyperFrames Video Burner - Permanently embeds animated/static HyperFrame overlays
into video clips or master movies with broadcast-grade glassmorphism typography.
"""
import subprocess
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from backend.config import FFMPEG_PATH, RAW_INPUT_DIR, FINAL_EXPORT_DIR, UPLOADS_DIR
from backend.pipeline.media_ingest import probe_media

def extract_info_from_html(html_str: str) -> dict:
    """
    Extracts title, subtitle, and action text from HyperFrame HTML snippet.
    """
    title = "Full On Throttle"
    subtitle = "Pushkar and Jaipur Road Trip Vlog"
    action = "Subscribe"

    if not html_str:
        return {"title": title, "subtitle": subtitle, "action_text": action}

    # Match <span class="name">Title</span>
    m_name = re.search(r'class="name"[^>]*>([^<]+)<', html_str, re.IGNORECASE)
    if m_name and m_name.group(1).strip():
        title = m_name.group(1).strip()

    # Match <div class="creator-sub">Subtitle</div>
    m_sub = re.search(r'class="creator-sub"[^>]*>([^<]+)<', html_str, re.IGNORECASE)
    if m_sub and m_sub.group(1).strip():
        subtitle = m_sub.group(1).strip()

    # Match subscribe button text
    m_btn = re.search(r'class="subscribe-chip"[^>]*>.*?<span>([^<]+)<', html_str, re.IGNORECASE | re.DOTALL)
    if m_btn and m_btn.group(1).strip():
        action = m_btn.group(1).strip()

    return {"title": title, "subtitle": subtitle, "action_text": action}

def render_creator_lowerthird_png(
    title: str = "Full On Throttle",
    subtitle: str = "Pushkar and Jaipur Road Trip Vlog",
    action_text: str = "Subscribe",
    output_png_path: str = None
) -> str:
    """
    Renders a pixel-perfect 1920x1080 transparent PNG with YouTube Creator glassmorphism lower-third.
    """
    if output_png_path is None:
        output_png_path = str(UPLOADS_DIR / "hyperframe_lowerthird_overlay.png")

    img = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Card dimensions
    card_x = 70
    card_y = 860
    card_w = 780
    card_h = 124
    radius = 24

    # Outer soft drop shadow (simulated)
    for o in range(6, 0, -2):
        draw.rounded_rectangle(
            [card_x + o, card_y + o, card_x + card_w + o, card_y + card_h + o],
            radius=radius,
            fill=(0, 0, 0, 45)
        )

    # Glass Card Background (deep obsidian navy with high-tech border)
    draw.rounded_rectangle(
        [card_x, card_y, card_x + card_w, card_y + card_h],
        radius=radius,
        fill=(10, 16, 30, 230),
        outline=(56, 189, 248, 140),
        width=2
    )

    # Top frosted highlight line
    draw.line(
        [(card_x + radius, card_y + 1), (card_x + card_w - radius, card_y + 1)],
        fill=(255, 255, 255, 60),
        width=1
    )

    # Avatar Badge Box
    av_x = card_x + 18
    av_y = card_y + 20
    av_s = 84
    draw.rounded_rectangle(
        [av_x, av_y, av_x + av_s, av_y + av_s],
        radius=18,
        fill=(37, 99, 235, 240),
        outline=(96, 165, 250, 200),
        width=2
    )

    # Draw sleek modern camera/airplane vector inside avatar
    # Crisp white playback triangle / wings inside badge
    draw.polygon(
        [
            (av_x + 28, av_y + 24),
            (av_x + av_s - 26, av_y + av_s // 2),
            (av_x + 28, av_y + av_s - 24)
        ],
        fill=(255, 255, 255, 255)
    )

    # Font setup
    font_bold_path = r"C:\Windows\Fonts\segoeuib.ttf"
    font_regular_path = r"C:\Windows\Fonts\segoeui.ttf"
    if not Path(font_bold_path).exists():
        font_bold_path = r"C:\Windows\Fonts\arialbd.ttf"
        font_regular_path = r"C:\Windows\Fonts\arial.ttf"

    font_title = ImageFont.truetype(font_bold_path, 28)
    font_sub = ImageFont.truetype(font_regular_path, 17)
    font_btn = ImageFont.truetype(font_bold_path, 14)

    # Title text
    title_x = av_x + av_s + 20
    title_y = card_y + 26
    draw.text((title_x, title_y), title, fill=(248, 250, 252, 255), font=font_title)

    # Calculate title width for verified badge
    bbox = draw.textbbox((title_x, title_y), title, font=font_title)
    badge_x = bbox[2] + 12
    badge_y = title_y + 5
    badge_r = 11

    # Cyan Verified Badge Circle
    draw.ellipse(
        [badge_x, badge_y, badge_x + (badge_r * 2), badge_y + (badge_r * 2)],
        fill=(14, 165, 233, 255)
    )
    # Checkmark inside badge
    draw.text((badge_x + 5, badge_y + 1), "v", fill=(10, 16, 30, 255), font=font_btn)

    # Subtitle text
    sub_y = card_y + 70
    draw.text((title_x, sub_y), subtitle, fill=(148, 163, 184, 255), font=font_sub)

    # Subscribe / Action Chip
    btn_w = 140
    btn_h = 42
    btn_x = card_x + card_w - btn_w - 22
    btn_y = card_y + (card_h - btn_h) // 2

    draw.rounded_rectangle(
        [btn_x, btn_y, btn_x + btn_w, btn_y + btn_h],
        radius=21,
        fill=(23, 37, 84, 240),
        outline=(56, 189, 248, 180),
        width=1
    )

    # Glowing cyan dot in button
    dot_r = 4
    dot_x = btn_x + 20
    dot_y = btn_y + btn_h // 2
    draw.ellipse(
        [dot_x - dot_r, dot_y - dot_r, dot_x + dot_r, dot_y + dot_r],
        fill=(56, 189, 248, 255)
    )
    draw.text((dot_x + 12, btn_y + 11), action_text, fill=(56, 189, 248, 255), font=font_btn)

    Path(output_png_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_png_path, "PNG")
    return output_png_path

def burn_hyperframe_to_video(
    input_video_path: str,
    output_filename: str = None,
    title: str = "Full On Throttle",
    subtitle: str = "Pushkar and Jaipur Road Trip Vlog",
    action_text: str = "Subscribe",
    start_time: float = 1.5,
    duration: float = 6.0
) -> str:
    """
    Burns the rendered HyperFrame lower-third overlay into the video file with smooth fade transitions.
    """
    in_p = Path(input_video_path)
    if not in_p.exists():
        # Fallback to first video in raw_input
        exts = {".mov", ".mp4", ".m4v"}
        available = sorted([f for f in RAW_INPUT_DIR.iterdir() if f.is_file() and f.suffix.lower() in exts])
        if available:
            in_p = available[0]
        else:
            raise FileNotFoundError(f"Input video not found: {input_video_path}")

    if output_filename is None:
        clean_stem = re.sub(r"[^a-zA-Z0-9_-]", "_", title).upper()
        output_filename = f"MASTER_{clean_stem}_VLOG_HYPERFRAME.mp4"

    out_p = FINAL_EXPORT_DIR / output_filename

    # Step 1: Render transparent PNG
    png_path = UPLOADS_DIR / "hyperframe_burn_overlay.png"
    render_creator_lowerthird_png(
        title=title,
        subtitle=subtitle,
        action_text=action_text,
        output_png_path=str(png_path)
    )

    fade_in_d = 0.5
    fade_out_d = 0.5
    end_time = start_time + duration
    fade_out_st = max(start_time, end_time - fade_out_d)

    # Probe duration to ensure FFmpeg stops exactly when the input video finishes
    meta = probe_media(str(in_p))
    clip_dur = meta.get("duration", 0)

    # Filter complex with smooth alpha fade in/out
    filter_complex = (
        f"[1:v]format=rgba,"
        f"fade=t=in:st={start_time:.2f}:d={fade_in_d:.2f}:alpha=1,"
        f"fade=t=out:st={fade_out_st:.2f}:d={fade_out_d:.2f}:alpha=1[ovl];"
        f"[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p[base];"
        f"[base][ovl]overlay=0:0:enable='between(t,{start_time:.2f},{end_time:.2f})'[outv]"
    )

    cmd = [
        FFMPEG_PATH,
        "-y",
        "-i", str(in_p),
        "-loop", "1",
        "-i", str(png_path),
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "0:a:0?",
        "-shortest",
        "-r", "30",
        "-fps_mode", "cfr",
        "-c:v", "libx264",
        "-preset", "faster",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-colorspace", "bt709",
        "-color_primaries", "bt709",
        "-color_trc", "bt709",
        "-c:a", "aac",
        "-ar", "48000",
        "-ac", "2",
        "-b:a", "192k",
        "-movflags", "+faststart"
    ]

    if clip_dur and clip_dur > 0:
        cmd.extend(["-t", f"{clip_dur:.3f}"])

    cmd.append(str(out_p))

    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return str(out_p)
