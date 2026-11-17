"""
Persistent Storage Engine for User Settings & Anirban Preset
Maintains user-customized 50 Effects, Depth Typography, and Pipeline Settings
across browser refreshes and server restarts.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any

STORAGE_DIR = Path(__file__).resolve().parent.parent / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

ANIRBAN_PRESET_FILE = STORAGE_DIR / "anirban_preset.json"
USER_SETTINGS_FILE = STORAGE_DIR / "user_settings.json"

DEFAULT_ANIRBAN_EFFECTS = {
    "whip_pan": True,
    "punch_in": True,
    "push_in": True,
    "crash_zoom": False,
    "roll_360": False,
    "tilt_sky": True,
    "parallax_25d": False,
    "subject_lock": False,
    "dolly_zoom": False,
    "handheld_shake": True,
    "speed_ramp": True,
    "freeze_frame": False,
    "reverse_ramp": False,
    "flash_frame": True,
    "dialogue_jump_cut": True,
    "morph_cut": False,
    "stop_motion_12fps": False,
    "slow_shutter": False,
    "object_wipe": True,
    "luma_wipe": False,
    "split_clone": False,
    "grid_collage": True,
    "sky_replacement": False,
    "pip_overlay": False,
    "action_match_cut": True,
    "portal_zoom": False,
    "film_burn": False,
    "anamorphic_flare": False,
    "halation_glow": False,
    "white_out": False,
    "rgb_split": False,
    "vhs_crt": false if False else False,
    "heat_haze": False,
    "prismatic_glass": False,
    "film_grain": False,
    "film_sprocket": False,
    "gate_weave": False,
    "film_scratches": False,
    "letterbox_239": False,
    "bleach_bypass": False,
    "vignette_falloff": False,
    "j_cut": True,
    "l_cut": True,
    "sub_bass_drop": True,
    "lowpass_muffle": False,
    "whoosh_sync": True,
    "hormozi_captions": True,
    "tracked_3d_title": False,
    "paper_tear": False,
    "lower_third_slide": True,
    "license_plate_blur": True
}

DEFAULT_ANIRBAN_TEXT_BEHIND = {
    "enabled": True,
    "text": "RANN OF KUTCH",
    "font": "Montserrat",
    "size": 110,
    "spread": 8,
    "color": "#FFFFFF",
    "neon_enabled": True,
    "neon_color": "#00F2FE",
    "glow_radius": 24,
    "glow_intensity": 1.2,
    "position": "center",
    "y_offset": 0,
    "opacity": 0.95
}

def load_anirban_preset() -> Dict[str, Any]:
    """Loads saved Anirban Preset or creates default with 'RANN OF KUTCH'."""
    if ANIRBAN_PRESET_FILE.exists():
        try:
            with open(ANIRBAN_PRESET_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except Exception:
            pass

    default_data = {
        "name": "Anirban Preset",
        "active_effects": DEFAULT_ANIRBAN_EFFECTS,
        "text_behind_person": DEFAULT_ANIRBAN_TEXT_BEHIND
    }
    save_anirban_preset(default_data["active_effects"], default_data["text_behind_person"])
    return default_data

def save_anirban_preset(active_effects: Dict[str, bool], text_behind: Dict[str, Any]) -> Dict[str, Any]:
    """Saves the current effects and text-behind settings permanently as Anirban Preset."""
    data = {
        "name": "Anirban Preset",
        "active_effects": active_effects,
        "text_behind_person": text_behind
    }
    try:
        with open(ANIRBAN_PRESET_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving Anirban Preset: {e}")
    return data

def load_user_settings() -> Dict[str, Any]:
    """Loads persisted user settings across server restarts."""
    if USER_SETTINGS_FILE.exists():
        try:
            with open(USER_SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_user_settings(settings: Dict[str, Any]) -> None:
    """Persists current project settings to disk."""
    try:
        # Create a clean serializable copy
        data_to_save = {}
        for k in ["color_grade", "caption_style", "aspect_ratio", "ai_director_effects", "text_behind_person", "enabled_grids", "edit_mode", "render_mode", "language", "script_mode"]:
            if k in settings:
                data_to_save[k] = settings[k]

        with open(USER_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=2)
    except Exception as e:
        print(f"Error saving user settings: {e}")
