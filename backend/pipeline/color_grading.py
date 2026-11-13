"""
Cinematic Color Grading Engine
Applies aesthetic film looks and LUT presets:
- Teal & Orange (Blockbuster look)
- Moody Bleach Bypass (Dramatic tension)
- Vintage Warm 70s (Golden retro film)
- Cyberpunk Neon (Vibrant futuristic)
- Clean Documentary (Crisp natural realism)
- Golden Hour Sunset (Warm amber glow)
- Social Viral Pop (High-contrast mobile)
"""
from backend.config import COLOR_PRESETS

def get_color_grade_filter(preset_key: str = "teal_orange") -> str:
    """
    Returns the FFmpeg video filter string for the chosen color grade preset.
    """
    preset = COLOR_PRESETS.get(preset_key)
    if not preset or not preset.get("eq"):
        return ""
    return preset["eq"]

def list_color_presets() -> list[dict]:
    """
    Returns list of all available color grading presets with metadata.
    """
    res = []
    for k, v in COLOR_PRESETS.items():
        res.append({
            "id": k,
            "name": v["name"],
            "description": v["description"],
            "preview_color": v["preview_color"]
        })
    return res
