"""
Natural Language AI Director Agent
Translates conversational user instructions (e.g. "make this 60s for TikTok with teal & orange")
into structured editing operations across the pipeline.
"""
import re

def parse_agent_prompt(prompt: str) -> dict:
    """
    Interprets natural language editing commands and orchestrates timeline parameters.
    """
    p = prompt.lower().strip()

    actions = {
        "aspect_ratio": "original",
        "target_duration": None,
        "remove_silence": True,
        "remove_fillers": True,
        "protect_scenic": True,
        "color_grade": "none",
        "caption_style": "hormozi",
        "audio_enhance": True,
        "beat_sync": False,
        "duck_music": False,
        "is_highlight_reel": False,
        "summary": []
    }

    # 1. Platform / Aspect Ratio / Shorts / TikTok / Reels
    if any(k in p for k in ["tiktok", "reel", "shorts", "vertical", "9:16", "9/16"]):
        actions["aspect_ratio"] = "9:16"
        actions["caption_style"] = "hormozi"
        actions["summary"].append("Auto-crop to 9:16 vertical with face-tracking reframer")

    # 2. Duration / Length
    dur_match = re.search(r'(\d+)\s*(?:seconds|second|sec|s\b)', p)
    if dur_match:
        target_s = float(dur_match.group(1))
        actions["target_duration"] = target_s
        actions["is_highlight_reel"] = True
        actions["summary"].append(f"Condense to {target_s}s highlight reel with peak viral moments")
    elif "highlight" in p or "summary" in p:
        actions["target_duration"] = 30.0
        actions["is_highlight_reel"] = True
        actions["summary"].append("Generate 30s automated highlight reel")

    # 3. Language & Script (English, Hindi, Hinglish)
    if "hinglish" in p:
        actions["language"] = "hinglish"
        actions["summary"].append("Set offline transcription language to Hinglish (Roman Script)")
    elif "hindi" in p or "हिंदी" in p:
        actions["language"] = "hi"
        actions["summary"].append("Set offline transcription language to Hindi (Devanagari)")
    elif "english" in p:
        actions["language"] = "en"
        actions["summary"].append("Set offline transcription language to English")

    # 4. Color Grading
    if "teal" in p or "orange" in p:
        actions["color_grade"] = "teal_orange"
        actions["summary"].append("Apply Hollywood Teal & Orange cinematic look")
    elif "moody" in p or "bleach" in p or "noir" in p:
        actions["color_grade"] = "moody_noir"
        actions["summary"].append("Apply Moody Bleach Bypass color grade")
    elif "vintage" in p or "70s" in p or "retro" in p:
        actions["color_grade"] = "vintage_70s"
        actions["summary"].append("Apply Vintage Warm 70s film grade")
    elif "neon" in p or "cyber" in p:
        actions["color_grade"] = "cyber_neon"
        actions["summary"].append("Apply Cyberpunk Neon aesthetic")
    elif "golden" in p or "sunset" in p:
        actions["color_grade"] = "golden_hour"
        actions["summary"].append("Apply Golden Hour Sunset warmth")
    elif "pop" in p or "viral" in p:
        actions["color_grade"] = "vibrant_pop"
        actions["summary"].append("Apply Social Viral Pop color boost")

    # 4. Captions
    if "mrbeast" in p:
        actions["caption_style"] = "mrbeast"
        actions["summary"].append("Add bold punchy MrBeast-style animated captions")
    elif "cyber" in p:
        actions["caption_style"] = "cyber_neon"
        actions["summary"].append("Add glowing Cyberpunk hyperframe captions")
    elif "cinematic" in p:
        actions["caption_style"] = "cinematic"
        actions["summary"].append("Add clean minimalist cinematic subtitles")
    else:
        actions["caption_style"] = "hormozi"
        actions["summary"].append("Add high-retention Hormozi kinetic word-highlight captions")

    # 5. Beat Sync & Ducking
    if "beat" in p or "rhythm" in p or "music" in p:
        actions["beat_sync"] = True
        actions["duck_music"] = True
        actions["summary"].append("Sync cut transitions to background music BPM & auto-duck volume")

    # 6. Audio Enhancement
    if "audio" in p or "voice" in p or "clean" in p or "denoise" in p:
        actions["audio_enhance"] = True
        actions["summary"].append("Clean background hiss, hum & normalize vocal loudness to -14 LUFS")

    # 7. Scenic Protection (Always on by default)
    actions["summary"].append("Protect scenic B-roll (mountains, roads, sea, nature) from silence cuts")

    # 8. Face Safe Guarantee
    actions["summary"].append("Lock Face-Safe exclusion zone: captions & graphics will NOT obscure face")

    return {
        "status": "ready",
        "user_prompt": prompt,
        "actions": actions,
        "plan_description": " • " + "\n • ".join(actions["summary"])
    }
