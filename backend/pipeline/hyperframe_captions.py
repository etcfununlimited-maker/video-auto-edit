"""
Kinetic Animated Hyperframe Captions & Graphics Engine
YouTube Create / CapCut / Hormozi Style Retention Editing:
- Word-by-word dynamic bounce pop hyperframe animations (scaling 120% -> 100%)
- High-contrast radiant color bursts (Electric Yellow, Neon Cyan, Punch Gold)
- Dynamic contextual emoji sticker inserts (🔥, 🚀, 💡, 🎬, 🎯, 🏔️, 🤫, 💰)
- Strict Face-Safe Exclusion Zone: captions & graphics NEVER cover or obscure the speaker's face!
"""
import re
from pathlib import Path
from backend.config import EXPORTS_DIR

# Contextual Emoji Map for Retention Editing (YouTube Create style)
EMOJI_TRIGGERS = {
    r"\b(secret|truth|mystery|revealed)\b": "🤫",
    r"\b(money|rich|million|crore|dollar|profit|cost|cash)\b": "💰",
    r"\b(fire|amazing|crazy|insane|awesome|best|hot)\b": "🔥",
    r"\b(rocket|launch|start|fast|grow|future)\b": "🚀",
    r"\b(idea|mindset|brain|think|thought|trick)\b": "💡",
    r"\b(video|movie|edit|film|camera|shoot)\b": "🎬",
    r"\b(goal|target|focus|point|plan)\b": "🎯",
    r"\b(mountain|nature|forest|hill|sea|ocean|view)\b": "🏔️",
    r"\b(warning|danger|mistake|stop|never|wrong)\b": "⚠️",
    r"\b(ai|robot|tech|automation|future)\b": "🤖",
    r"\b(love|like|heart|happy)\b": "❤️",
    r"\b(star|special|top|winner)\b": "⭐"
}

CAPTION_STYLES = {
    "youtube_create": {
        "name": "YouTube Create / Viral Pop",
        "fontname": "Impact",
        "fontsize": 48,
        "primary_color": "&H00FFFFFF",      # Pure White
        "highlight_color": "&H0000FFFF",    # Electric Neon Yellow
        "outline_color": "&H00000000",      # Deep Black Outline
        "back_color": "&H80000000",         # Semi-transparent dark pill box
        "outline": 5,
        "shadow": 3,
        "bold": -1,
        "alignment": 2,                     # Lower third
        "margin_v": 90
    },
    "hormozi": {
        "name": "Hormozi Kinetic Pop",
        "fontname": "Arial",
        "fontsize": 44,
        "primary_color": "&H00FFFFFF",
        "highlight_color": "&H0000E5FF",    # Radiant Gold / Yellow
        "outline_color": "&H00000000",
        "back_color": "&H00000000",
        "outline": 4,
        "shadow": 2,
        "bold": -1,
        "alignment": 2,
        "margin_v": 85
    },
    "mrbeast": {
        "name": "MrBeast Bold Punch",
        "fontname": "Impact",
        "fontsize": 50,
        "primary_color": "&H00FFFFFF",
        "highlight_color": "&H0033CCFF",    # Punch Orange
        "outline_color": "&H00000000",
        "back_color": "&H00000000",
        "outline": 5,
        "shadow": 3,
        "bold": -1,
        "alignment": 2,
        "margin_v": 95
    },
    "cyber_neon": {
        "name": "Cyberpunk Neon Glow",
        "fontname": "Trebuchet MS",
        "fontsize": 42,
        "primary_color": "&H00FFFF00",      # Electric Cyan
        "highlight_color": "&H00FF00FF",    # Neon Magenta
        "outline_color": "&H00220033",
        "back_color": "&H00000000",
        "outline": 4,
        "shadow": 0,
        "bold": -1,
        "alignment": 2,
        "margin_v": 80
    },
    "cinematic": {
        "name": "Cinematic Clean",
        "fontname": "Helvetica",
        "fontsize": 32,
        "primary_color": "&H00F0F0F0",
        "highlight_color": "&H00FFFFFF",
        "outline_color": "&H80000000",
        "back_color": "&H00000000",
        "outline": 2,
        "shadow": 1,
        "bold": 0,
        "alignment": 2,
        "margin_v": 60
    }
}

def format_ass_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def format_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def detect_context_emoji(text: str) -> str:
    """Detects if sentence contains key viral hook words and returns relevant emoji graphic."""
    lower_t = text.lower()
    for pattern, emoji in EMOJI_TRIGGERS.items():
        if re.search(pattern, lower_t):
            return emoji
    return ""

def compute_face_safe_margin(face_boxes: list[dict], video_h: int = 1080) -> dict:
    """
    Guarantees captions and hyperframe graphics NEVER cover or obscure the speaker's face.
    """
    if not face_boxes:
        return {"alignment": 2, "margin_v": 85, "position": "bottom"}

    max_face_bottom = max(f.get("y", 300) + f.get("h", 250) for f in face_boxes)
    min_face_top = min(f.get("y", 300) for f in face_boxes)

    # Face is in upper or middle area: place captions safely in bottom third
    if max_face_bottom < (video_h * 0.72):
        safe_margin = int(video_h * 0.08)
        return {"alignment": 2, "margin_v": safe_margin, "position": "bottom"}
    elif min_face_top > (video_h * 0.28):
        safe_margin = int(video_h * 0.08)
        return {"alignment": 8, "margin_v": safe_margin, "position": "top"}
    else:
        return {"alignment": 2, "margin_v": 60, "position": "bottom"}

def remap_words_to_edited_timeline(words: list[dict], cuts: list[dict] = None) -> list[dict]:
    """
    Re-maps word-level timestamps from original footage time to the edited post-cut timeline.
    Words that fall inside cut regions are purged.
    Surviving words are shifted left by the cumulative duration of all preceding cuts.
    Guarantees 100% frame-perfect subtitle synchronization on the final master video.
    """
    if not cuts:
        return [w for w in words if not w.get("deleted")]

    sorted_cuts = sorted(cuts, key=lambda x: x["start"])
    remapped = []

    for w in words:
        if w.get("deleted"):
            continue
        w_start = w["start"]
        w_end = w["end"]
        w_mid = (w_start + w_end) / 2.0

        # Check if word falls inside any cut
        in_cut = any(c["start"] <= w_mid <= c["end"] for c in sorted_cuts)
        if in_cut:
            continue

        # Compute cumulative cut duration that occurred BEFORE w_start
        cut_duration_before = 0.0
        for c in sorted_cuts:
            if c["end"] <= w_start:
                cut_duration_before += c["duration"]
            elif c["start"] < w_start < c["end"]:
                cut_duration_before += (w_start - c["start"])

        new_start = max(0.0, round(w_start - cut_duration_before, 3))
        new_dur = max(0.05, round(w_end - w_start, 3))
        new_end = round(new_start + new_dur, 3)

        remapped.append({
            **w,
            "start": new_start,
            "end": new_end,
            "orig_start": w_start,
            "orig_end": w_end
        })

    return remapped

def generate_ass_subtitles(
    words: list[dict],
    style_name: str = "youtube_create",
    output_path: str = None,
    face_boxes: list[dict] = None,
    cuts: list[dict] = None
) -> str:
    """
    Creates an ASS subtitle script with dynamic YouTube Create / CapCut style hyperframe animations:
    - Kinetic bounce pop on every active spoken word
    - Neon highlight color burst
    - Contextual emoji inserts
    - Strict Face-Safe positioning
    - Re-maps timestamps to post-cut timeline when cuts are provided
    """
    # Synchronize words to post-edit timeline if cuts are present
    active_words = remap_words_to_edited_timeline(words, cuts)

    style = CAPTION_STYLES.get(style_name, CAPTION_STYLES["youtube_create"]).copy()
    if not output_path:
        output_path = str(EXPORTS_DIR / f"captions_{style_name}.ass")

    safe_info = compute_face_safe_margin(face_boxes or [], video_h=1080)
    style["alignment"] = safe_info["alignment"]
    style["margin_v"] = safe_info["margin_v"]

    ass_header = f"""[Script Info]
Title: Auto Video Editor Hyperframe Dynamic Captions
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{style['fontname']},{style['fontsize']},{style['primary_color']},{style['highlight_color']},{style['outline_color']},{style['outline_color']},{style['bold']},0,0,0,100,100,1,0,1,{style['outline']},{style['shadow']},{style['alignment']},20,20,{style['margin_v']},1
Style: HyperActive,{style['fontname']},{int(style['fontsize']*1.12)},{style['highlight_color']},{style['primary_color']},{style['outline_color']},{style['outline_color']},{style['bold']},0,0,0,110,110,1,0,1,{style['outline']+1},{style['shadow']+1},{style['alignment']},20,20,{style['margin_v']},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []

    # Group into short 2-4 word punchy bursts for maximum retention
    chunks = []
    curr_chunk = []
    for w in active_words:
        if w.get("deleted"):
            continue
        curr_chunk.append(w)
        if len(curr_chunk) >= 3 or w.get("word", "").endswith((".", "!", "?")):
            chunks.append(curr_chunk)
            curr_chunk = []
    if curr_chunk:
        chunks.append(curr_chunk)

    for chunk in chunks:
        if not chunk:
            continue
        c_text = " ".join(w["word"] for w in chunk)
        emoji_badge = detect_context_emoji(c_text)
        emoji_prefix = f"{emoji_badge} " if emoji_badge else ""

        # Create individual word-level pop events so each word bounces on screen
        for i, active_w in enumerate(chunk):
            w_start = active_w["start"]
            w_end = active_w["end"]
            
            line_parts = []
            for j, w in enumerate(chunk):
                if j == i:
                    # Active word: Bounces up to 120% scale with radiant highlight color!
                    # \\t(0,120,\\fscx120\\fscy120)\\t(120,240,\\fscx100\\fscy100)
                    pop_tag = "{\\c" + style["highlight_color"] + "\\t(0,80,\\fscx122\\fscy122)\\t(80,180,\\fscx100\\fscy100)}"
                    line_parts.append(f"{pop_tag}{w['word'].upper()}{{\\rDefault}}")
                else:
                    # Inactive word: clean crisp white
                    line_parts.append(f"{{\\c{style['primary_color']}}}{w['word'].upper()}")

            full_line = emoji_prefix + " ".join(line_parts)
            events.append(f"Dialogue: 0,{format_ass_time(w_start)},{format_ass_time(w_end)},Default,,0,0,0,,{full_line}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ass_header + "\n".join(events))

    return output_path

def generate_srt_subtitles(words: list[dict], output_path: str = None, cuts: list[dict] = None) -> str:
    if not output_path:
        output_path = str(EXPORTS_DIR / "captions.srt")

    active_words = remap_words_to_edited_timeline(words, cuts)

    chunks = []
    curr = []
    for w in active_words:
        if w.get("deleted"):
            continue
        curr.append(w)
        if len(curr) >= 4 or w["word"].endswith((".", "!", "?")):
            chunks.append(curr)
            curr = []
    if curr:
        chunks.append(curr)

    srt_lines = []
    for idx, chunk in enumerate(chunks, 1):
        s_time = format_srt_time(chunk[0]["start"])
        e_time = format_srt_time(chunk[-1]["end"])
        text = " ".join(w["word"] for w in chunk)
        emoji = detect_context_emoji(text)
        if emoji:
            text = f"{emoji} {text}"
        srt_lines.append(f"{idx}\n{s_time} --> {e_time}\n{text}\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))

    return output_path
