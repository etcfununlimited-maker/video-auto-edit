"""
PREMIERE PRO FCP-XML (xmeml v4) & SRT PROJECT EXPORTER
======================================================
Generates broadcast-compliant Apple Final Cut Pro XML (xmeml v4) projects
specifically engineered for seamless 1-click import into Adobe Premiere Pro 2024 / 2025 / 2026,
DaVinci Resolve, and Final Cut Pro.
"""

import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from urllib.parse import quote
from backend.config import FINAL_EXPORT_DIR, RAW_INPUT_DIR, UPLOADS_DIR, FFMPEG_PATH
from backend.pipeline.media_ingest import probe_media


def to_pathurl(file_path: str) -> str:
    """Converts a local Windows or POSIX path into a standard file://localhost/ URL for Premiere Pro"""
    p = Path(file_path).resolve()
    clean_p = str(p).replace("\\", "/")
    if not clean_p.startswith("/"):
        clean_p = "/" + clean_p
    # For Windows drive paths /C:/..., quote spaces and special characters while preserving / and :
    encoded = quote(clean_p, safe="/:")
    return f"file://localhost{encoded}"


def render_title_overlay_png(title_text: str, width: int = 1920, height: int = 1080, output_path: str = None) -> str:
    """
    Renders a transparent PNG title overlay for Premiere Pro Track V2 with cyan neon halo glow.
    Stacks multi-line titles with pipe delimiter '|'.
    """
    if not output_path:
        output_path = str(FINAL_EXPORT_DIR / "PREMIERE_TITLE_OVERLAY.png")

    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_path = r"C:\Windows\Fonts\impact.ttf"
    if not Path(font_path).exists():
        font_path = r"C:\Windows\Fonts\arialbd.ttf"

    raw_text = (title_text or "RANN OF KUTCH | BHUJ | SOMNATH VLOG").strip()
    if "|" in raw_text:
        lines = [part.strip().upper() for part in raw_text.split("|") if part.strip()]
    else:
        lines = [raw_text.upper()]

    num_lines = len(lines)
    font_size = 90 if num_lines <= 2 else 72
    font = ImageFont.truetype(font_path, font_size)
    line_height = int(font_size * 1.18)
    start_y = int(height * 0.12)

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = (width - w) // 2
        y = start_y + (i * line_height)

        # Cyan halo glow outline
        for dx in range(-6, 7, 2):
            for dy in range(-6, 7, 2):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), line, font=font, fill=(0, 242, 254, 180))
        # Crisp white center text
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG")
    return str(output_path)


def render_soundtrack_bed_wav(music_track_path: Path, target_duration_sec: float, output_path: str = None) -> str:
    """
    Loops or trims background music into a clean, broadcast-standard 48kHz Stereo WAV for Premiere Pro Track A2.
    Eliminates embedded ID3 JPEG video streams and guarantees exact duration alignment.
    """
    if not output_path:
        output_path = str(FINAL_EXPORT_DIR / "PREMIERE_SOUNDTRACK_BED.wav")

    import subprocess
    cmd = [
        FFMPEG_PATH, "-y",
        "-stream_loop", "-1",
        "-i", str(music_track_path),
        "-t", f"{target_duration_sec:.3f}",
        "-vn",
        "-c:a", "pcm_s16le",
        "-ar", "48000",
        "-ac", "2",
        str(output_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return str(output_path)


def format_srt_time(seconds: float) -> str:
    """Formats float seconds into SRT timestamp format: HH:MM:SS,mmm"""
    if seconds is None or seconds < 0:
        seconds = 0.0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    if ms >= 1000:
        ms = 999
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def get_sequence_aligned_words(clips: list[dict]) -> list[dict]:
    """
    Extracts and timeline-aligns spoken words for each clip in the sequence.
    Offsets each clip's word timestamps to its exact head position on the timeline.
    """
    import json
    aligned_words = []
    current_head = 0.0
    for idx, c in enumerate(clips):
        c_path = c.get("path", "")
        p_obj = Path(c_path)
        stem = p_obj.stem
        dur = float(c.get("duration", 4.0))
        in_pt = float(c.get("in_point", 0.0))
        out_pt = in_pt + dur

        cache_candidates = [
            UPLOADS_DIR / f".transcript_cache_{stem}_roman.json",
            UPLOADS_DIR / f".transcript_cache_{stem}.json"
        ]
        clip_words = []
        for cand in cache_candidates:
            if cand.exists():
                try:
                    with open(cand, "r", encoding="utf-8") as f_c:
                        data = json.load(f_c)
                        if data and "words" in data:
                            clip_words = data["words"]
                            break
                except Exception:
                    pass

        for w in clip_words:
            w_start = float(w.get("start", 0.0))
            w_end = float(w.get("end", w_start + 0.3))
            w_txt = (w.get("word") or w.get("word_roman") or "").strip()
            if not w_txt:
                continue
            if w_end > in_pt and w_start < out_pt:
                t_start = round(current_head + max(0.0, w_start - in_pt), 3)
                t_end = round(current_head + min(dur, w_end - in_pt), 3)
                if t_end > t_start:
                    aligned_words.append({
                        "word": w_txt,
                        "start": t_start,
                        "end": t_end,
                        "clip_idx": idx,
                        "clip_name": p_obj.name
                    })
        current_head += dur
    return aligned_words


def export_project_srt(words: list[dict] = None, output_srt_path: str = None, clips: list[dict] = None) -> str:
    """
    Exports synchronized speech transcript words into a standard .srt subtitle file.
    Groups words into punchy, high-retention 3-4 word chunks respecting clip boundaries.
    """
    if not output_srt_path:
        output_srt_path = str(FINAL_EXPORT_DIR / "CAPTIONS.srt")

    if not words and clips:
        words = get_sequence_aligned_words(clips)

    if not words:
        cache_files = sorted(
            list(UPLOADS_DIR.glob(".transcript_cache_*_roman.json")) + list(UPLOADS_DIR.glob(".transcript_cache_*.json")),
            key=lambda p: p.stat().st_size,
            reverse=True
        )
        if cache_files:
            try:
                import json
                with open(cache_files[0], "r", encoding="utf-8") as f_c:
                    d = json.load(f_c)
                    if d and "words" in d:
                        words = d["words"]
            except Exception:
                pass

    active_words = [w for w in (words or []) if not w.get("deleted")]

    chunks = []
    curr = []
    for w in active_words:
        # Break chunk if crossing into a new clip
        if curr and w.get("clip_idx") is not None and curr[-1].get("clip_idx") is not None and w.get("clip_idx") != curr[-1].get("clip_idx"):
            chunks.append(curr)
            curr = []
        curr.append(w)
        word_txt = w.get("word") or w.get("word_roman") or ""
        if len(curr) >= 4 or word_txt.endswith((".", "!", "?")):
            chunks.append(curr)
            curr = []
    if curr:
        chunks.append(curr)

    srt_blocks = []
    for idx, chunk in enumerate(chunks, 1):
        s_time = format_srt_time(chunk[0].get("start", 0.0))
        e_time = format_srt_time(chunk[-1].get("end", chunk[0].get("start", 0.0) + 1.5))
        text = " ".join((w.get("word") or w.get("word_roman") or "").strip() for w in chunk)
        srt_blocks.append(f"{idx}\n{s_time} --> {e_time}\n{text}\n")

    Path(output_srt_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_blocks))

    return str(output_srt_path)


def render_hormuzi_overlay_mov(
    clips: list[dict],
    width: int = 1920,
    height: int = 1080,
    fps: int = 30,
    output_path: str = None
) -> str:
    """
    Renders an animated transparent QuickTime MOV (QuickTime Animation with 32-bit alpha)
    containing word-by-word bouncing Hormozi kinetic captions.
    Engineered for 1-click native compositing in Adobe Premiere Pro on Track V3!
    """
    if not output_path:
        output_path = str(FINAL_EXPORT_DIR / "PREMIERE_HORMUZI_CAPTIONS.mov")

    from backend.pipeline.hyperframe_captions import generate_ass_subtitles
    import subprocess

    words = get_sequence_aligned_words(clips)
    if not words:
        return ""

    total_sec = sum(float(c.get("duration", 4.0)) for c in clips)
    total_sec = max(2.0, total_sec)

    ass_path = FINAL_EXPORT_DIR / "PREMIERE_HORMUZI_CAPTIONS.ass"
    generate_ass_subtitles(
        words=words,
        style_name="hormozi",
        output_path=str(ass_path),
        cuts=None,
        video_path=None
    )

    escaped_ass = str(ass_path.resolve()).replace("\\", "/").replace(":", r"\:")
    vf_arg = "ass=filename=" + chr(39) + escaped_ass + chr(39) + ":alpha=1"

    cmd = [
        FFMPEG_PATH, "-y",
        "-f", "lavfi", "-i", f"color=c=black@0.0:s={width}x{height}:r={fps}:d={total_sec:.2f},format=rgba",
        "-vf", vf_arg,
        "-c:v", "qtrle",
        "-pix_fmt", "argb",
        str(output_path)
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if res.returncode == 0 and Path(output_path).exists():
            return str(output_path)
    except Exception as e:
        print(f"[render_hormuzi_overlay_mov] Error: {e}")
    return ""


def export_premiere_fcp_xml(
    clips: list[dict],
    output_xml_path: str = None,
    sequence_name: str = "Anirban_Premiere_Master_Sequence",
    fps: int = 30,
    aspect_ratio: str = "16:9",
    title_text: str = "",
    music_track_name: str = "Airport_Lounge.mp3",
    ducking_depth_pct: float = 75.0,
    ensure_min_clips: int = 10
) -> str:
    """
    Generates a full, 100% broadcast-compliant Apple Final Cut Pro XML (xmeml version 4/5)
    file specifically engineered for seamless 1-click import into Adobe Premiere Pro 2024 / 2025 / 2026.
    Includes:
    - Multi-cut video track (V1) with 10 clips
    - Graphic title overlay track (V2) referencing PREMIERE_TITLE_OVERLAY.png
    - Native editable text generator track (V3)
    - Cleaned dialogue track (A1) linked 1:1 with V1, equipped with Studio DeNoise & Audio Levels filters
    - Keyframed background music track (A2) with strictly-monotonic auto-ducking envelopes
    """
    if not output_xml_path:
        output_xml_path = str(FINAL_EXPORT_DIR / "PREMIERE_PRO_PROJECT.xml")

    # Dimensions
    if aspect_ratio == "9:16":
        width, height = 1080, 1920
    else:
        width, height = 1920, 1080

    v1_clips = [c for c in clips if c.get("track") == "V1"]
    if not v1_clips:
        v1_clips = [c for c in clips if not c.get("track") or c.get("track") in ("V1", "V2")]
    if not v1_clips:
        v1_clips = [dict(c) for c in clips]

    # Ensure at least 10 clips if raw_input directory has footage
    if len(v1_clips) < ensure_min_clips and RAW_INPUT_DIR.exists():
        existing_names = {Path(c.get("path", "")).name for c in v1_clips if c.get("path")}
        raw_vids = sorted([
            f for f in RAW_INPUT_DIR.iterdir()
            if f.is_file() and f.suffix.lower() in {".mp4", ".mov", ".m4v", ".avi", ".webm"}
        ])
        for f in raw_vids:
            if f.name not in existing_names:
                v1_clips.append({
                    "id": f"v1_clip_{len(v1_clips)+1}",
                    "path": str(f),
                    "name": f.name,
                    "track": "V1",
                    "in_point": 0.0,
                    "duration": 4.0,
                    "out_point": 4.0,
                    "volume": 100,
                    "noise_suppression": 75,
                    "muted": False
                })
                existing_names.add(f.name)
                if len(v1_clips) >= ensure_min_clips:
                    break

    # Calculate total duration in frames
    total_frames = 0
    for c in v1_clips:
        dur_sec = float(c.get("duration", 4.0))
        total_frames += int(round(dur_sec * fps))
    total_frames = max(fps * 5, total_frames)

    root = ET.Element("xmeml", version="4")
    seq = ET.SubElement(root, "sequence", id="sequence-1")
    ET.SubElement(seq, "name").text = sequence_name
    ET.SubElement(seq, "duration").text = str(total_frames)

    rate = ET.SubElement(seq, "rate")
    ET.SubElement(rate, "timebase").text = str(fps)
    ET.SubElement(rate, "ntsc").text = "FALSE"

    tc = ET.SubElement(seq, "timecode")
    tc_rate = ET.SubElement(tc, "rate")
    ET.SubElement(tc_rate, "timebase").text = str(fps)
    ET.SubElement(tc_rate, "ntsc").text = "FALSE"
    ET.SubElement(tc, "string").text = "00:00:00:00"
    ET.SubElement(tc, "frame").text = "0"
    ET.SubElement(tc, "displayformat").text = "NDF"

    media = ET.SubElement(seq, "media")

    # ================= VIDEO TRACKS =================
    video = ET.SubElement(media, "video")
    v_format = ET.SubElement(video, "format")
    sample_char = ET.SubElement(v_format, "samplecharacteristics")
    sc_rate = ET.SubElement(sample_char, "rate")
    ET.SubElement(sc_rate, "timebase").text = str(fps)
    ET.SubElement(sc_rate, "ntsc").text = "FALSE"
    ET.SubElement(sample_char, "width").text = str(width)
    ET.SubElement(sample_char, "height").text = str(height)
    ET.SubElement(sample_char, "anamorphic").text = "FALSE"
    ET.SubElement(sample_char, "pixelaspectratio").text = "square"
    ET.SubElement(sample_char, "fielddominance").text = "none"
    ET.SubElement(sample_char, "colordepth").text = "24"

    # --- TRACK 1 (V1 Master Video) ---
    track_v1 = ET.SubElement(video, "track")
    ET.SubElement(track_v1, "enabled").text = "TRUE"
    ET.SubElement(track_v1, "locked").text = "FALSE"
    current_head_frame = 0

    # Store clip metadata for linking with audio track
    clip_records = []

    for idx, c in enumerate(v1_clips):
        c_path = c.get("path", "")
        p_obj = Path(c_path)
        if not p_obj.exists():
            if (RAW_INPUT_DIR / p_obj.name).exists():
                p_obj = RAW_INPUT_DIR / p_obj.name
            elif (FINAL_EXPORT_DIR / p_obj.name).exists():
                p_obj = FINAL_EXPORT_DIR / p_obj.name

        meta = probe_media(str(p_obj)) if p_obj.exists() else {}
        file_dur = float(meta.get("duration", 10.0))
        file_frames = max(1, int(round(file_dur * fps)))

        in_sec = float(c.get("in_point", 0.0))
        dur_sec = float(c.get("duration", 4.0))
        out_sec = in_sec + dur_sec

        in_frame = int(round(in_sec * fps))
        out_frame = int(round(out_sec * fps))
        dur_frame = max(1, out_frame - in_frame)

        start_frame = current_head_frame
        end_frame = current_head_frame + dur_frame
        current_head_frame = end_frame

        clip_id_v = f"clipitem-v1-{idx+1}"
        clip_id_a = f"clipitem-a1-{idx+1}"
        file_id = f"file-{idx+1}"
        master_id = f"masterclip-{idx+1}"

        is_muted = bool(c.get("muted", False))
        vol_pct = float(c.get("volume", 100))
        denoise_pct = float(c.get("noise_suppression", 75))

        clip_records.append({
            "idx": idx + 1,
            "p_obj": p_obj,
            "meta": meta,
            "file_id": file_id,
            "master_id": master_id,
            "clip_id_v": clip_id_v,
            "clip_id_a": clip_id_a,
            "start_frame": start_frame,
            "end_frame": end_frame,
            "in_frame": in_frame,
            "out_frame": out_frame,
            "dur_frame": dur_frame,
            "file_frames": file_frames,
            "muted": is_muted,
            "volume": vol_pct,
            "noise_suppression": denoise_pct
        })

        clipitem = ET.SubElement(track_v1, "clipitem", id=clip_id_v)
        ET.SubElement(clipitem, "masterclipid").text = master_id
        ET.SubElement(clipitem, "name").text = p_obj.name
        ET.SubElement(clipitem, "enabled").text = "FALSE" if is_muted else "TRUE"
        ET.SubElement(clipitem, "duration").text = str(dur_frame)

        ci_rate = ET.SubElement(clipitem, "rate")
        ET.SubElement(ci_rate, "timebase").text = str(fps)
        ET.SubElement(ci_rate, "ntsc").text = "FALSE"

        ET.SubElement(clipitem, "start").text = str(start_frame)
        ET.SubElement(clipitem, "end").text = str(end_frame)
        ET.SubElement(clipitem, "in").text = str(in_frame)
        ET.SubElement(clipitem, "out").text = str(out_frame)

        # Full File Element Definition
        file_el = ET.SubElement(clipitem, "file", id=file_id)
        ET.SubElement(file_el, "name").text = p_obj.name
        ET.SubElement(file_el, "pathurl").text = to_pathurl(str(p_obj))

        f_rate = ET.SubElement(file_el, "rate")
        ET.SubElement(f_rate, "timebase").text = str(fps)
        ET.SubElement(f_rate, "ntsc").text = "FALSE"
        ET.SubElement(file_el, "duration").text = str(file_frames)

        f_tc = ET.SubElement(file_el, "timecode")
        f_tc_rate = ET.SubElement(f_tc, "rate")
        ET.SubElement(f_tc_rate, "timebase").text = str(fps)
        ET.SubElement(f_tc_rate, "ntsc").text = "FALSE"
        ET.SubElement(f_tc, "string").text = "00:00:00:00"
        ET.SubElement(f_tc, "frame").text = "0"
        ET.SubElement(f_tc, "displayformat").text = "NDF"

        f_media = ET.SubElement(file_el, "media")
        
        # Video stream
        f_video = ET.SubElement(f_media, "video")
        f_sc = ET.SubElement(f_video, "samplecharacteristics")
        f_sc_r = ET.SubElement(f_sc, "rate")
        ET.SubElement(f_sc_r, "timebase").text = str(fps)
        ET.SubElement(f_sc_r, "ntsc").text = "FALSE"
        ET.SubElement(f_sc, "width").text = str(meta.get("width", width))
        ET.SubElement(f_sc, "height").text = str(meta.get("height", height))
        ET.SubElement(f_sc, "anamorphic").text = "FALSE"
        ET.SubElement(f_sc, "pixelaspectratio").text = "square"
        ET.SubElement(f_sc, "fielddominance").text = "none"

        # Audio stream in file
        f_audio = ET.SubElement(f_media, "audio")
        f_a_sc = ET.SubElement(f_audio, "samplecharacteristics")
        ET.SubElement(f_a_sc, "depth").text = "16"
        ET.SubElement(f_a_sc, "samplerate").text = "48000"
        ET.SubElement(f_audio, "channelcount").text = "2"

        # Sourcetrack on V1
        st = ET.SubElement(clipitem, "sourcetrack")
        ET.SubElement(st, "mediatype").text = "video"

        # Links (Video clip linked to Voice Audio clip)
        l_v = ET.SubElement(clipitem, "link")
        ET.SubElement(l_v, "linkclipref").text = clip_id_v
        ET.SubElement(l_v, "mediatype").text = "video"
        ET.SubElement(l_v, "trackindex").text = "1"
        ET.SubElement(l_v, "clipindex").text = str(idx + 1)

        l_a = ET.SubElement(clipitem, "link")
        ET.SubElement(l_a, "linkclipref").text = clip_id_a
        ET.SubElement(l_a, "mediatype").text = "audio"
        ET.SubElement(l_a, "trackindex").text = "1"
        ET.SubElement(l_a, "clipindex").text = str(idx + 1)
        ET.SubElement(l_a, "groupindex").text = "1"

    # --- TRACK 2 (V2 Title & Text Behind Person Overlay as Graphic clipitem) ---
    clean_title = (title_text or "RANN OF KUTCH | BHUJ | SOMNATH VLOG").strip()
    title_png_path = render_title_overlay_png(clean_title, width, height)
    track_v2 = ET.SubElement(video, "track")
    ET.SubElement(track_v2, "enabled").text = "TRUE"
    ET.SubElement(track_v2, "locked").text = "FALSE"

    title_dur_frames = total_frames
    clipitem_v2 = ET.SubElement(track_v2, "clipitem", id="clipitem-v2-title-1")
    ET.SubElement(clipitem_v2, "masterclipid").text = "masterclip-title-1"
    ET.SubElement(clipitem_v2, "name").text = f"Title: {clean_title}"
    ET.SubElement(clipitem_v2, "enabled").text = "TRUE"
    ET.SubElement(clipitem_v2, "duration").text = str(title_dur_frames)

    ci_rate_v2 = ET.SubElement(clipitem_v2, "rate")
    ET.SubElement(ci_rate_v2, "timebase").text = str(fps)
    ET.SubElement(ci_rate_v2, "ntsc").text = "FALSE"

    ET.SubElement(clipitem_v2, "start").text = "0"
    ET.SubElement(clipitem_v2, "end").text = str(title_dur_frames)
    ET.SubElement(clipitem_v2, "in").text = "0"
    ET.SubElement(clipitem_v2, "out").text = str(title_dur_frames)

    file_v2 = ET.SubElement(clipitem_v2, "file", id="file-title-1")
    ET.SubElement(file_v2, "name").text = Path(title_png_path).name
    ET.SubElement(file_v2, "pathurl").text = to_pathurl(title_png_path)

    f_rate_v2 = ET.SubElement(file_v2, "rate")
    ET.SubElement(f_rate_v2, "timebase").text = str(fps)
    ET.SubElement(f_rate_v2, "ntsc").text = "FALSE"
    ET.SubElement(file_v2, "duration").text = str(title_dur_frames)

    f_tc_v2 = ET.SubElement(file_v2, "timecode")
    f_tc_rate_v2 = ET.SubElement(f_tc_v2, "rate")
    ET.SubElement(f_tc_rate_v2, "timebase").text = str(fps)
    ET.SubElement(f_tc_rate_v2, "ntsc").text = "FALSE"
    ET.SubElement(f_tc_v2, "string").text = "00:00:00:00"
    ET.SubElement(f_tc_v2, "frame").text = "0"
    ET.SubElement(f_tc_v2, "displayformat").text = "NDF"

    f_media_v2 = ET.SubElement(file_v2, "media")
    f_vid_v2 = ET.SubElement(f_media_v2, "video")
    f_sc_v2 = ET.SubElement(f_vid_v2, "samplecharacteristics")
    sc_r_v2 = ET.SubElement(f_sc_v2, "rate")
    ET.SubElement(sc_r_v2, "timebase").text = str(fps)
    ET.SubElement(sc_r_v2, "ntsc").text = "FALSE"
    ET.SubElement(f_sc_v2, "width").text = str(width)
    ET.SubElement(f_sc_v2, "height").text = str(height)
    ET.SubElement(f_sc_v2, "anamorphic").text = "FALSE"
    ET.SubElement(f_sc_v2, "pixelaspectratio").text = "square"
    ET.SubElement(f_sc_v2, "fielddominance").text = "none"

    st_v2 = ET.SubElement(clipitem_v2, "sourcetrack")
    ET.SubElement(st_v2, "mediatype").text = "video"

    # --- TRACK 3 (V3 Hormozi Kinetic Animated Captions Overlay) ---
    track_v3 = ET.SubElement(video, "track")
    ET.SubElement(track_v3, "enabled").text = "TRUE"
    ET.SubElement(track_v3, "locked").text = "FALSE"

    hormuzi_mov_path = render_hormuzi_overlay_mov(v1_clips, width=width, height=height, fps=fps)
    if hormuzi_mov_path and Path(hormuzi_mov_path).exists():
        clipitem_v3 = ET.SubElement(track_v3, "clipitem", id="clipitem-v3-captions-1")
        ET.SubElement(clipitem_v3, "masterclipid").text = "masterclip-captions-1"
        ET.SubElement(clipitem_v3, "name").text = "Captions: Hormozi Kinetic Dynamic Overlay"
        ET.SubElement(clipitem_v3, "enabled").text = "TRUE"
        ET.SubElement(clipitem_v3, "duration").text = str(total_frames)

        ci_rate_v3 = ET.SubElement(clipitem_v3, "rate")
        ET.SubElement(ci_rate_v3, "timebase").text = str(fps)
        ET.SubElement(ci_rate_v3, "ntsc").text = "FALSE"

        ET.SubElement(clipitem_v3, "start").text = "0"
        ET.SubElement(clipitem_v3, "end").text = str(total_frames)
        ET.SubElement(clipitem_v3, "in").text = "0"
        ET.SubElement(clipitem_v3, "out").text = str(total_frames)

        file_v3 = ET.SubElement(clipitem_v3, "file", id="file-captions-1")
        ET.SubElement(file_v3, "name").text = Path(hormuzi_mov_path).name
        ET.SubElement(file_v3, "pathurl").text = to_pathurl(hormuzi_mov_path)

        f_rate_v3 = ET.SubElement(file_v3, "rate")
        ET.SubElement(f_rate_v3, "timebase").text = str(fps)
        ET.SubElement(f_rate_v3, "ntsc").text = "FALSE"
        ET.SubElement(file_v3, "duration").text = str(total_frames)

        f_tc_v3 = ET.SubElement(file_v3, "timecode")
        f_tc_rate_v3 = ET.SubElement(f_tc_v3, "rate")
        ET.SubElement(f_tc_rate_v3, "timebase").text = str(fps)
        ET.SubElement(f_tc_rate_v3, "ntsc").text = "FALSE"
        ET.SubElement(f_tc_v3, "string").text = "00:00:00:00"
        ET.SubElement(f_tc_v3, "frame").text = "0"
        ET.SubElement(f_tc_v3, "displayformat").text = "NDF"

        f_media_v3 = ET.SubElement(file_v3, "media")
        f_vid_v3 = ET.SubElement(f_media_v3, "video")
        f_sc_v3 = ET.SubElement(f_vid_v3, "samplecharacteristics")
        sc_r_v3 = ET.SubElement(f_sc_v3, "rate")
        ET.SubElement(sc_r_v3, "timebase").text = str(fps)
        ET.SubElement(sc_r_v3, "ntsc").text = "FALSE"
        ET.SubElement(f_sc_v3, "width").text = str(width)
        ET.SubElement(f_sc_v3, "height").text = str(height)
        ET.SubElement(f_sc_v3, "anamorphic").text = "FALSE"
        ET.SubElement(f_sc_v3, "pixelaspectratio").text = "square"
        ET.SubElement(f_sc_v3, "fielddominance").text = "none"

        st_v3 = ET.SubElement(clipitem_v3, "sourcetrack")
        ET.SubElement(st_v3, "mediatype").text = "video"

    # --- TRACK 4 (V4 Native Editable Text Generator for Premiere Pro) ---
    track_v4 = ET.SubElement(video, "track")
    ET.SubElement(track_v4, "enabled").text = "TRUE"
    ET.SubElement(track_v4, "locked").text = "FALSE"

    genitem = ET.SubElement(track_v4, "generatoritem", id="text-gen-title-1")
    ET.SubElement(genitem, "name").text = f"Text: {clean_title}"
    ET.SubElement(genitem, "duration").text = str(total_frames)
    g_rate = ET.SubElement(genitem, "rate")
    ET.SubElement(g_rate, "timebase").text = str(fps)
    ET.SubElement(g_rate, "ntsc").text = "FALSE"
    ET.SubElement(genitem, "in").text = "0"
    ET.SubElement(genitem, "out").text = str(min(total_frames, fps * 15))
    ET.SubElement(genitem, "start").text = "0"
    ET.SubElement(genitem, "end").text = str(min(total_frames, fps * 15))
    ET.SubElement(genitem, "enabled").text = "TRUE"

    eff_gen = ET.SubElement(genitem, "effect")
    ET.SubElement(eff_gen, "name").text = "Text"
    ET.SubElement(eff_gen, "effectid").text = "Text"
    ET.SubElement(eff_gen, "effectcategory").text = "generator"
    ET.SubElement(eff_gen, "effecttype").text = "generator"
    ET.SubElement(eff_gen, "mediatype").text = "video"

    p_str = ET.SubElement(eff_gen, "parameter")
    ET.SubElement(p_str, "parameterid").text = "str"
    ET.SubElement(p_str, "name").text = "Text"
    ET.SubElement(p_str, "value").text = clean_title

    p_font = ET.SubElement(eff_gen, "parameter")
    ET.SubElement(p_font, "parameterid").text = "font"
    ET.SubElement(p_font, "name").text = "Font"
    ET.SubElement(p_font, "value").text = "Impact"

    p_size = ET.SubElement(eff_gen, "parameter")
    ET.SubElement(p_size, "parameterid").text = "fontsize"
    ET.SubElement(p_size, "name").text = "Size"
    ET.SubElement(p_size, "value").text = "68"

    # ================= AUDIO TRACKS =================
    audio = ET.SubElement(media, "audio")
    ET.SubElement(audio, "numoutputchannels").text = "2"
    a_format = ET.SubElement(audio, "format")
    a_sc = ET.SubElement(a_format, "samplecharacteristics")
    ET.SubElement(a_sc, "depth").text = "16"
    ET.SubElement(a_sc, "samplerate").text = "48000"

    outputs = ET.SubElement(audio, "outputs")
    for g_idx in [1, 2]:
        grp = ET.SubElement(outputs, "group")
        ET.SubElement(grp, "index").text = str(g_idx)
        ET.SubElement(grp, "allowsmapping").text = "TRUE"

    # --- AUDIO TRACK 1 (A1 Voice Dialogue with DeNoise & Vocal Level per clip) ---
    track_a1 = ET.SubElement(audio, "track")
    ET.SubElement(track_a1, "enabled").text = "TRUE"
    ET.SubElement(track_a1, "locked").text = "FALSE"

    for rec in clip_records:
        clipitem = ET.SubElement(track_a1, "clipitem", id=rec["clip_id_a"])
        ET.SubElement(clipitem, "masterclipid").text = rec["master_id"]
        ET.SubElement(clipitem, "name").text = f"Voice: {rec['p_obj'].name}"
        ET.SubElement(clipitem, "enabled").text = "FALSE" if rec["muted"] else "TRUE"
        ET.SubElement(clipitem, "duration").text = str(rec["dur_frame"])

        ci_rate = ET.SubElement(clipitem, "rate")
        ET.SubElement(ci_rate, "timebase").text = str(fps)
        ET.SubElement(ci_rate, "ntsc").text = "FALSE"

        ET.SubElement(clipitem, "start").text = str(rec["start_frame"])
        ET.SubElement(clipitem, "end").text = str(rec["end_frame"])
        ET.SubElement(clipitem, "in").text = str(rec["in_frame"])
        ET.SubElement(clipitem, "out").text = str(rec["out_frame"])

        # Reference existing file
        file_el = ET.SubElement(clipitem, "file", id=rec["file_id"])

        # Source track mapping
        st = ET.SubElement(clipitem, "sourcetrack")
        ET.SubElement(st, "mediatype").text = "audio"
        ET.SubElement(st, "trackindex").text = "1"

        # Links (Voice audio clip linked to Video clip)
        l_v = ET.SubElement(clipitem, "link")
        ET.SubElement(l_v, "linkclipref").text = rec["clip_id_v"]
        ET.SubElement(l_v, "mediatype").text = "video"
        ET.SubElement(l_v, "trackindex").text = "1"
        ET.SubElement(l_v, "clipindex").text = str(rec["idx"])

        l_a = ET.SubElement(clipitem, "link")
        ET.SubElement(l_a, "linkclipref").text = rec["clip_id_a"]
        ET.SubElement(l_a, "mediatype").text = "audio"
        ET.SubElement(l_a, "trackindex").text = "1"
        ET.SubElement(l_a, "clipindex").text = str(rec["idx"])
        ET.SubElement(l_a, "groupindex").text = "1"

        # 1. Studio DeNoise Audio Filter (Configured per clip)
        f_denoise = ET.SubElement(clipitem, "filter")
        eff_denoise = ET.SubElement(f_denoise, "effect")
        ET.SubElement(eff_denoise, "name").text = "DeNoise"
        ET.SubElement(eff_denoise, "effectid").text = "denoise"
        ET.SubElement(eff_denoise, "effecttype").text = "audio"
        ET.SubElement(eff_denoise, "mediatype").text = "audio"
        param_dn = ET.SubElement(eff_denoise, "parameter")
        ET.SubElement(param_dn, "parameterid").text = "amount"
        ET.SubElement(param_dn, "name").text = "Amount"
        ET.SubElement(param_dn, "value").text = str(round(rec["noise_suppression"], 1))

        # 2. Vocal Gain / Audio Levels Boost (+4dB Vocal Forwarding, modulated by clip volume)
        vol_scalar = 0.0 if rec["muted"] else round(1.45 * (rec["volume"] / 100.0), 3)
        f_vol = ET.SubElement(clipitem, "filter")
        eff_vol = ET.SubElement(f_vol, "effect")
        ET.SubElement(eff_vol, "name").text = "Audio Levels"
        ET.SubElement(eff_vol, "effectid").text = "audiolevels"
        ET.SubElement(eff_vol, "effecttype").text = "audio"
        ET.SubElement(eff_vol, "mediatype").text = "audio"
        param_vol = ET.SubElement(eff_vol, "parameter")
        ET.SubElement(param_vol, "parameterid").text = "level"
        ET.SubElement(param_vol, "name").text = "Level"
        ET.SubElement(param_vol, "valuemin").text = "0"
        ET.SubElement(param_vol, "valuemax").text = "3.98109"
        ET.SubElement(param_vol, "value").text = str(vol_scalar)

    # --- AUDIO TRACK 2 (A2 Soundtrack Bed with Dynamic Auto-Ducking) ---
    music_p = RAW_INPUT_DIR / "MUSIC" / music_track_name
    if not music_p.exists():
        from backend.pipeline.beat_sync import get_available_soundtracks
        avail = get_available_soundtracks()
        if avail:
            music_p = avail[0]

    if music_p.exists():
        track_a2 = ET.SubElement(audio, "track")
        ET.SubElement(track_a2, "enabled").text = "TRUE"
        ET.SubElement(track_a2, "locked").text = "FALSE"

        total_dur_sec = max(1.0, total_frames / float(fps))
        soundtrack_wav_path = render_soundtrack_bed_wav(music_p, total_dur_sec)

        clipitem = ET.SubElement(track_a2, "clipitem", id="clipitem-a2-music-1")
        ET.SubElement(clipitem, "masterclipid").text = "masterclip-music-1"
        ET.SubElement(clipitem, "name").text = f"Music Bed: {music_p.name} (Auto-Ducking)"
        ET.SubElement(clipitem, "enabled").text = "TRUE"
        ET.SubElement(clipitem, "duration").text = str(total_frames)

        ci_rate = ET.SubElement(clipitem, "rate")
        ET.SubElement(ci_rate, "timebase").text = str(fps)
        ET.SubElement(ci_rate, "ntsc").text = "FALSE"

        ET.SubElement(clipitem, "start").text = "0"
        ET.SubElement(clipitem, "end").text = str(total_frames)
        ET.SubElement(clipitem, "in").text = "0"
        ET.SubElement(clipitem, "out").text = str(total_frames)

        file_el = ET.SubElement(clipitem, "file", id="file-music-1")
        ET.SubElement(file_el, "name").text = Path(soundtrack_wav_path).name
        ET.SubElement(file_el, "pathurl").text = to_pathurl(str(soundtrack_wav_path))

        f_rate = ET.SubElement(file_el, "rate")
        ET.SubElement(f_rate, "timebase").text = str(fps)
        ET.SubElement(f_rate, "ntsc").text = "FALSE"
        ET.SubElement(file_el, "duration").text = str(total_frames)

        f_tc_a2 = ET.SubElement(file_el, "timecode")
        f_tc_rate_a2 = ET.SubElement(f_tc_a2, "rate")
        ET.SubElement(f_tc_rate_a2, "timebase").text = str(fps)
        ET.SubElement(f_tc_rate_a2, "ntsc").text = "FALSE"
        ET.SubElement(f_tc_a2, "string").text = "00:00:00:00"
        ET.SubElement(f_tc_a2, "frame").text = "0"
        ET.SubElement(f_tc_a2, "displayformat").text = "NDF"

        f_media = ET.SubElement(file_el, "media")
        f_audio = ET.SubElement(f_media, "audio")
        f_a_sc = ET.SubElement(f_audio, "samplecharacteristics")
        ET.SubElement(f_a_sc, "depth").text = "16"
        ET.SubElement(f_a_sc, "samplerate").text = "48000"
        ET.SubElement(f_audio, "channelcount").text = "2"

        st = ET.SubElement(clipitem, "sourcetrack")
        ET.SubElement(st, "mediatype").text = "audio"
        ET.SubElement(st, "trackindex").text = "1"

        # Grid 7: Breathing Music Ducking Filter with Strictly Monotonic Keyframes
        filt = ET.SubElement(clipitem, "filter")
        eff = ET.SubElement(filt, "effect")
        ET.SubElement(eff, "name").text = "Audio Levels"
        ET.SubElement(eff, "effectid").text = "audiolevels"
        ET.SubElement(eff, "effecttype").text = "audio"
        ET.SubElement(eff, "mediatype").text = "audio"

        param = ET.SubElement(eff, "parameter")
        ET.SubElement(param, "parameterid").text = "level"
        ET.SubElement(param, "name").text = "Level"
        ET.SubElement(param, "valuemin").text = "0"
        ET.SubElement(param, "valuemax").text = "3.98109"

        ducked_val = str(round(max(0.08, 0.22 * (ducking_depth_pct / 75.0)), 3))
        normal_val = "0.70"
        ET.SubElement(param, "value").text = normal_val

        # Build keyframes list with strictly monotonic timestamps (no duplicate `when`)
        kfs = []
        if clip_records and clip_records[0]["start_frame"] == 0:
            kfs.append((0, ducked_val))
        else:
            kfs.append((0, normal_val))

        last_when = 0
        for i, rec in enumerate(clip_records):
            s_f = rec["start_frame"]
            e_f = rec["end_frame"]

            if s_f > 0:
                ramp_down = max(last_when + 1, s_f - 10)
                if ramp_down > last_when:
                    kfs.append((ramp_down, normal_val))
                    last_when = ramp_down
                if s_f > last_when:
                    kfs.append((s_f, ducked_val))
                    last_when = s_f

            if e_f > last_when:
                kfs.append((e_f, ducked_val))
                last_when = e_f

            next_s = clip_records[i + 1]["start_frame"] if i + 1 < len(clip_records) else total_frames
            if next_s > e_f + 5:
                swell_f = min(total_frames, e_f + 15)
                if swell_f > last_when:
                    kfs.append((swell_f, normal_val))
                    last_when = swell_f

        if total_frames > last_when:
            kfs.append((total_frames, normal_val))

        for w_val, v_val in kfs:
            kf = ET.SubElement(param, "keyframe")
            ET.SubElement(kf, "when").text = str(w_val)
            ET.SubElement(kf, "value").text = str(v_val)

    # Export with standard XML header and DOCTYPE for Adobe Premiere Pro
    raw_xml_bytes = ET.tostring(root, encoding="utf-8")
    parsed = minidom.parseString(raw_xml_bytes)
    pretty_body = parsed.documentElement.toprettyxml(indent="  ")

    xml_header = '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n'
    final_xml = xml_header + pretty_body

    Path(output_xml_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_xml_path, "w", encoding="utf-8") as f:
        f.write(final_xml)

    # Automatically generate sequence-aligned CAPTIONS.srt alongside XML
    try:
        srt_sidecar = Path(output_xml_path).parent / "CAPTIONS.srt"
        export_project_srt(clips=v1_clips, output_srt_path=str(srt_sidecar))
    except Exception as srt_err:
        print(f"[export_premiere_fcp_xml] Warning: SRT export failed: {srt_err}")

    return str(output_xml_path)
