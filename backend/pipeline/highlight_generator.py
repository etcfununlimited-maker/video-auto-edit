"""
Automated Highlight Reels & Storyboarding Engine
Analyzes raw footage, identifies high-retention hooks, peaks in speech energy & scenic transitions,
and stitches together condensed 15s / 30s / 60s viral summary clips.
"""
import re
from pathlib import Path

# High-retention viral hook keywords
HOOK_TRIGGERS = {
    "secret", "why", "how", "stop", "never", "always", "truth", "mistake",
    "crazy", "insane", "unbelievable", "best", "worst", "revealed",
    "remember", "listen", "imagine", "watch", "today", "look at this"
}

def score_sentence_virality(sentence: dict) -> float:
    """
    Computes an engagement score (0.0 to 10.0) for a sentence segment.
    """
    text = sentence.get("text", "").lower()
    dur = sentence.get("end", 0) - sentence.get("start", 0)
    words = sentence.get("words", [])

    score = 4.0  # base score

    # Check for hook words
    hook_matches = sum(1 for trigger in HOOK_TRIGGERS if re.search(r'\b' + trigger + r'\b', text))
    score += min(3.5, hook_matches * 1.2)

    # Check if ends with question or exclamation
    if text.endswith("?"):
        score += 1.5
    elif text.endswith("!"):
        score += 1.0

    # Speech velocity (pacing)
    if dur > 0.5:
        wpm = (len(words) / dur) * 60.0
        if 130 <= wpm <= 190:
            score += 1.0  # optimal energetic delivery
        elif wpm > 210:
            score += 0.5

    return round(min(10.0, score), 2)

def generate_highlight_storyboard(sentences: list[dict], scenes: list[dict], target_duration_sec: float = 30.0) -> dict:
    """
    Selects the most captivating dialogue moments and scenic inserts to assemble
    a condensed highlight summary within target_duration_sec.
    """
    scored_sentences = []
    for s in sentences:
        s_score = score_sentence_virality(s)
        scored_sentences.append({
            **s,
            "virality_score": s_score
        })

    # Sort candidates by virality score
    sorted_candidates = sorted(scored_sentences, key=lambda x: x["virality_score"], reverse=True)

    selected_clips = []
    accumulated_time = 0.0

    # Pick top hook (best opening sentence)
    if sorted_candidates:
        hook = sorted_candidates[0]
        selected_clips.append({
            "role": "Hook / Intro",
            "start": hook["start"],
            "end": hook["end"],
            "duration": round(hook["end"] - hook["start"], 2),
            "text": hook["text"],
            "score": hook["virality_score"]
        })
        accumulated_time += hook["end"] - hook["start"]

    # Pick supporting highlights
    for cand in sorted_candidates[1:]:
        cand_dur = cand["end"] - cand["start"]
        if accumulated_time + cand_dur <= target_duration_sec:
            selected_clips.append({
                "role": "Key Moment",
                "start": cand["start"],
                "end": cand["end"],
                "duration": round(cand_dur, 2),
                "text": cand["text"],
                "score": cand["virality_score"]
            })
            accumulated_time += cand_dur

    # Inject scenic B-roll if available
    for sc in scenes:
        if sc.get("is_scenic") and (accumulated_time + min(3.0, sc["duration"]) <= target_duration_sec):
            sc_dur = min(3.0, sc["duration"])
            selected_clips.append({
                "role": "Scenic B-Roll",
                "start": sc["start"],
                "end": round(sc["start"] + sc_dur, 2),
                "duration": round(sc_dur, 2),
                "text": f"[{sc['category'].replace('_', ' ').title()}]",
                "score": 8.5
            })
            accumulated_time += sc_dur

    # Sort chronologically for natural video flow
    selected_clips = sorted(selected_clips, key=lambda x: x["start"])

    return {
        "target_duration": target_duration_sec,
        "actual_duration": round(accumulated_time, 2),
        "total_clips": len(selected_clips),
        "storyboard": selected_clips
    }
