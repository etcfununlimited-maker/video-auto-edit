"""
Persistent Storage Engine for User Settings & Anirban Preset
Maintains user-customized 50 Effects, Depth Typography, and Pipeline Settings
across browser refreshes and server restarts.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

if getattr(sys, "frozen", False):
    STORAGE_DIR = Path(sys.executable).resolve().parent / "backend" / "storage"
else:
    STORAGE_DIR = Path(__file__).resolve().parent.parent / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

ANIRBAN_PRESET_FILE = STORAGE_DIR / "anirban_preset.json"
USER_SETTINGS_FILE = STORAGE_DIR / "user_settings.json"

DEFAULT_ANIRBAN_EFFECTS = {
    # Camera Motion (10)
    "whip_pan": True,            # #01 ENABLED
    "punch_in": True,            # #02 ENABLED
    "push_in": False,           # #03 BYPASS
    "crash_zoom": False,        # #04 BYPASS
    "roll_360": False,          # #05 BYPASS
    "tilt_sky": True,            # #06 ENABLED
    "parallax_25d": False,      # #07 BYPASS
    "subject_lock": False,      # #08 BYPASS
    "dolly_zoom": False,        # #09 BYPASS
    "handheld_shake": False,    # #10 BYPASS

    # Speed & Pacing (8)
    "speed_ramp": True,          # #11 ENABLED
    "freeze_frame": False,      # #12 BYPASS
    "reverse_ramp": False,      # #13 BYPASS
    "flash_frame": False,       # #14 BYPASS
    "dialogue_jump_cut": True,   # #15 ENABLED
    "morph_cut": False,         # #16 BYPASS
    "stop_motion_12fps": False, # #17 BYPASS
    "slow_shutter": False,      # #18 BYPASS

    # Masking & Splits (8)
    "object_wipe": True,         # #19 ENABLED
    "luma_wipe": False,         # #20 BYPASS
    "split_clone": False,       # #21 BYPASS
    "grid_collage": True,        # #22 ENABLED
    "sky_replacement": False,   # #23 BYPASS
    "pip_overlay": True,         # #24 ENABLED
    "action_match_cut": True,    # #25 ENABLED
    "portal_zoom": False,       # #26 BYPASS

    # Lighting & Optics (8) - ALL BYPASS
    "film_burn": False,         # #27 BYPASS
    "anamorphic_flare": False,  # #28 BYPASS
    "halation_glow": False,     # #29 BYPASS
    "white_out": False,         # #30 BYPASS
    "rgb_split": False,         # #31 BYPASS
    "vhs_crt": False,           # #32 BYPASS
    "heat_haze": False,         # #33 BYPASS
    "prismatic_glass": False,   # #34 BYPASS

    # Film Emulation (7) - ALL BYPASS (No Vignette, No LUT, 100% Authentic Camera Sensor)
    "film_grain": False,        # #35 BYPASS
    "film_sprocket": False,     # #36 BYPASS
    "gate_weave": False,        # #37 BYPASS
    "film_scratches": False,    # #38 BYPASS
    "letterbox_239": False,     # #39 BYPASS
    "bleach_bypass": False,     # #40 BYPASS
    "vignette_falloff": False,  # #41 BYPASS

    # Audio Cuts (5) - ALL BYPASS
    "j_cut": False,             # #42 BYPASS
    "l_cut": False,             # #43 BYPASS
    "sub_bass_drop": False,     # #44 BYPASS
    "lowpass_muffle": False,    # #45 BYPASS
    "whoosh_sync": False,       # #46 BYPASS

    # Typography & Motion (4)
    "hormozi_captions": True,    # #47 ENABLED
    "tracked_3d_title": False,  # #48 BYPASS
    "paper_tear": False,        # #49 BYPASS
    "lower_third_slide": True,   # #50 ENABLED
    "license_plate_blur": True # #51 BYPASS
}

DEFAULT_ANIRBAN_TEXT_BEHIND = {
    "enabled": True,
    "text": "RANN OF KUTCH | BHUJ | SOMNATH VLOG",
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

DEFAULT_ANIRBAN_AUDIO = {
    "music_mood": "sacred_temple",
    "sacred_mode": True,
    "ducking_depth_pct": 75.0,
    "music_level_pct": 60.0,
    "denoise_pct": 90.0
}

def load_anirban_preset() -> Dict[str, Any]:
    """Loads saved Anirban Preset or creates default with 'RANN OF KUTCH' and audio mix."""
    if ANIRBAN_PRESET_FILE.exists():
        try:
            with open(ANIRBAN_PRESET_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "audio_settings" not in data:
                    data["audio_settings"] = DEFAULT_ANIRBAN_AUDIO
                return data
        except Exception:
            pass

    default_data = {
        "name": "Anirban Preset",
        "active_effects": DEFAULT_ANIRBAN_EFFECTS,
        "text_behind_person": DEFAULT_ANIRBAN_TEXT_BEHIND,
        "audio_settings": DEFAULT_ANIRBAN_AUDIO
    }
    save_anirban_preset(default_data["active_effects"], default_data["text_behind_person"], default_data["audio_settings"])
    return default_data

def save_anirban_preset(active_effects: Dict[str, bool], text_behind: Dict[str, Any], audio_settings: Dict[str, Any] = None) -> Dict[str, Any]:
    """Saves the current effects, text-behind, and audio mix settings permanently as Anirban Preset."""
    data = {
        "name": "Anirban Preset",
        "active_effects": active_effects,
        "text_behind_person": text_behind,
        "audio_settings": audio_settings if audio_settings is not None else DEFAULT_ANIRBAN_AUDIO
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
        for k in [
            "color_grade", "caption_style", "aspect_ratio",
            "ai_director_effects", "text_behind_person", "enabled_grids",
            "edit_mode", "render_mode", "language", "script_mode",
            "music_mood", "sacred_mode", "ducking_depth_pct", "music_level_pct", "denoise_pct"
        ]:
            if k in settings:
                data_to_save[k] = settings[k]

        with open(USER_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=2)
    except Exception as e:
        print(f"Error saving user settings: {e}")
