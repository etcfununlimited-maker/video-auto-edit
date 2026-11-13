"""
Text-Based Video Editing Engine
Synchronizes script document edits with the video timeline.
Deleting words or sentences automatically updates the timeline cuts.
"""

def update_transcript_deletion(words: list[dict], deleted_word_ids: list[int]) -> tuple[list[dict], list[dict]]:
    """
    Updates the deleted state of words and computes the corresponding timeline cut segments.
    """
    deleted_set = set(deleted_word_ids)
    updated_words = []
    
    for w in words:
        w_copy = w.copy()
        if w["id"] in deleted_set:
            w_copy["deleted"] = True
        else:
            w_copy["deleted"] = False
        updated_words.append(w_copy)

    # Compute continuous cut blocks from deleted words
    cuts = []
    in_cut = False
    cut_start = 0.0
    cut_end = 0.0

    for w in updated_words:
        if w["deleted"]:
            if not in_cut:
                in_cut = True
                cut_start = max(0.0, w["start"] - 0.04)  # 40ms lead
            cut_end = w["end"] + 0.04
        else:
            if in_cut:
                in_cut = False
                cuts.append({
                    "start": round(cut_start, 3),
                    "end": round(cut_end, 3),
                    "duration": round(cut_end - cut_start, 3),
                    "type": "text_edit_cut"
                })

    if in_cut:
        cuts.append({
            "start": round(cut_start, 3),
            "end": round(cut_end, 3),
            "duration": round(cut_end - cut_start, 3),
            "type": "text_edit_cut"
        })

    return updated_words, cuts
