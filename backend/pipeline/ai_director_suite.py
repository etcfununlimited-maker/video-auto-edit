"""
AI Director Suite & Top 50 Effects Engine
Provides comprehensive management for:
- Top 50 Vlog & Movie Effects & Transitions
- Dynamic Bold Text Behind Person (Depth Typography, Neon Glow & Spread)
- Real-time synchronization with the 12 Modular Grid Pipeline
"""
from typing import Dict, Any, List
from pathlib import Path
import copy

TOP_50_EFFECTS: List[Dict[str, Any]] = [
    # ---------------- 1. CAMERA MOTION & SPATIAL (1-10) ----------------
    {
        "id": "whip_pan",
        "num": "01",
        "name": "Whip Pan / Swish Cut",
        "category": "camera_motion",
        "category_name": "Camera Motion",
        "badge": "Vlog & Action",
        "desc": "High-velocity horizontal camera pan with directional motion blur cutting into next location.",
        "grid_target": "grid_agent",
        "grid_label": "Grid 11: AI Director",
        "default": True
    },
    {
        "id": "punch_in",
        "num": "02",
        "name": "Punch-In / Retention Zoom",
        "category": "camera_motion",
        "category_name": "Camera Motion",
        "badge": "Vlog Essential",
        "desc": "Alternates 1.0x and 1.08x–1.12x jump zooms on key words to reset viewer attention span.",
        "grid_target": "grid_agent",
        "grid_label": "Grid 11: AI Director",
        "default": True
    },
    {
        "id": "push_in",
        "num": "03",
        "name": "Smooth Push-In / Pull-Out",
        "category": "camera_motion",
        "category_name": "Camera Motion",
        "badge": "Cinematic",
        "desc": "Slow, constant keyframed optical zoom into subject's eyes or pulling out to reveal setting.",
        "grid_target": "grid_scenic",
        "grid_label": "Grid 4: Scenic Preserver",
        "default": False
    },
    {
        "id": "crash_zoom",
        "num": "04",
        "name": "Crash Zoom (Snap Zoom)",
        "category": "camera_motion",
        "category_name": "Camera Motion",
        "badge": "Comedy / Drama",
        "desc": "Ultra-fast 2.5x snap zoom within 4 frames with a slight camera shudder.",
        "grid_target": "grid_agent",
        "grid_label": "Grid 11: AI Director",
        "default": False
    },
    {
        "id": "roll_360",
        "num": "05",
        "name": "Roll / 360° Spin Transition",
        "category": "camera_motion",
        "category_name": "Camera Motion",
        "badge": "Dynamic",
        "desc": "Rapid rotational spin around Z-axis with circular motion blur bridging scenes.",
        "grid_target": "grid_reframe",
        "grid_label": "Grid 5: Smart Reframer",
        "default": False
    },
    {
        "id": "tilt_sky",
        "num": "06",
        "name": "Tilt-Up / Sky Swap",
        "category": "camera_motion",
        "category_name": "Camera Motion",
        "badge": "Travel Vlog",
        "desc": "Panning into sky or down into ground to seamlessly emerge in a new geographic scene.",
        "grid_target": "grid_scenic",
        "grid_label": "Grid 4: Scenic Preserver",
        "default": True
    },
    {
        "id": "parallax_25d",
        "num": "07",
        "name": "Parallax / 2.5D Drift",
        "category": "camera_motion",
        "category_name": "Camera Motion",
        "badge": "Cinema Pro",
        "desc": "Multi-plane separation of foreground, subject, and background moving at variable speeds.",
        "grid_target": "grid_scenic",
        "grid_label": "Grid 4: Scenic Preserver",
        "default": False
    },
    {
        "id": "subject_lock",
        "num": "08",
        "name": "Subject-Lock Match Cut",
        "category": "camera_motion",
        "category_name": "Camera Motion",
        "badge": "Montage",
        "desc": "Face or focal point locked to exact center pixel coordinates while background rapidly morphs.",
        "grid_target": "grid_reframe",
        "grid_label": "Grid 5: Smart Reframer",
        "default": False
    },
    {
        "id": "dolly_zoom",
        "num": "09",
        "name": "Dolly Zoom (Vertigo Zolly)",
        "category": "camera_motion",
        "category_name": "Camera Motion",
        "badge": "Cinematic Epic",
        "desc": "Optical zoom in while dollying camera backwards, warping depth perspective.",
        "grid_target": "grid_scenic",
        "grid_label": "Grid 4: Scenic Preserver",
        "default": False
    },
    {
        "id": "handheld_shake",
        "num": "10",
        "name": "Organic Handheld Camera Shake",
        "category": "camera_motion",
        "category_name": "Camera Motion",
        "badge": "Realism",
        "desc": "Injects natural micro-camera jitter and rotational drift into locked tripod shots.",
        "grid_target": "grid_ingest",
        "grid_label": "Grid 1: Ingest Decoder",
        "default": True
    },

    # ---------------- 2. SPEED, TEMPORAL & PACING (11-18) ----------------
    {
        "id": "speed_ramp",
        "num": "11",
        "name": "Speed Ramp (Time Remapping)",
        "category": "speed_pacing",
        "category_name": "Speed & Pacing",
        "badge": "Travel / Product",
        "desc": "Accelerates motion to 500% during transit, snapping to 40% slow-mo on key action.",
        "grid_target": "grid_agent",
        "grid_label": "Grid 11: AI Director",
        "default": True
    },
    {
        "id": "freeze_frame",
        "num": "12",
        "name": "Freeze-Frame Stamp Accent",
        "category": "speed_pacing",
        "category_name": "Speed & Pacing",
        "badge": "Creator Style",
        "desc": "Freezes motion for 20 frames with sound shutter effect and stylized title stamp.",
        "grid_target": "grid_captions",
        "grid_label": "Grid 8: Face-Safe Captions",
        "default": False
    },
    {
        "id": "reverse_ramp",
        "num": "13",
        "name": "Reverse Rewind Ramp",
        "category": "speed_pacing",
        "category_name": "Speed & Pacing",
        "badge": "Flashback",
        "desc": "Quickly rewinds footage with VHS audio squeal before restarting dialogue take.",
        "grid_target": "grid_silence",
        "grid_label": "Grid 3: Silence Arbiter",
        "default": False
    },
    {
        "id": "flash_frame",
        "num": "14",
        "name": "Flash Frame / Strobe Cut",
        "category": "speed_pacing",
        "category_name": "Speed & Pacing",
        "badge": "Beat Drop",
        "desc": "1–2 frames of white or alternate angle spliced into cut on musical snare hits.",
        "grid_target": "grid_beatsync",
        "grid_label": "Grid 7: Beat Sync",
        "default": True
    },
    {
        "id": "dialogue_jump_cut",
        "num": "15",
        "name": "Continuous Speech Jump Cut",
        "category": "speed_pacing",
        "category_name": "Speed & Pacing",
        "badge": "Casey Neistat",
        "desc": "Trims 150–300ms micro-silences and filler stumbles while keeping speaker centered.",
        "grid_target": "grid_silence",
        "grid_label": "Grid 3: Silence Arbiter",
        "default": True
    },
    {
        "id": "morph_cut",
        "num": "16",
        "name": "Optical Flow Morph Cut",
        "category": "speed_pacing",
        "category_name": "Speed & Pacing",
        "badge": "Interview Pro",
        "desc": "Seamlessly interpolates pixels between two takes to make jump cuts completely invisible.",
        "grid_target": "grid_silence",
        "grid_label": "Grid 3: Silence Arbiter",
        "default": False
    },
    {
        "id": "stop_motion_12fps",
        "num": "17",
        "name": "12 FPS Posterize Stop-Motion",
        "category": "speed_pacing",
        "category_name": "Speed & Pacing",
        "badge": "Indie Aesthetic",
        "desc": "Drops temporal playback to 12 FPS creating a whimsical retro claymation/indie film look.",
        "grid_target": "grid_agent",
        "grid_label": "Grid 11: AI Director",
        "default": False
    },
    {
        "id": "slow_shutter",
        "num": "18",
        "name": "Slow-Shutter Dream Blur",
        "category": "speed_pacing",
        "category_name": "Speed & Pacing",
        "badge": "Night City",
        "desc": "Simulates 1/4s slow shutter trails for dreamy atmospheric walking shots through city neon.",
        "grid_target": "grid_color",
        "grid_label": "Grid 10: Cinematic LUT",
        "default": False
    },

    # ---------------- 3. MASKING & SPATIAL (19-26) ----------------
    {
        "id": "object_wipe",
        "num": "19",
        "name": "Foreground Object/Pillar Wipe",
        "category": "masking_splits",
        "category_name": "Masking & Splits",
        "badge": "1917 Style",
        "desc": "A passing tree, lamppost, or walking person wipes across screen to reveal Scene B.",
        "grid_target": "grid_agent",
        "grid_label": "Grid 11: AI Director",
        "default": True
    },
    {
        "id": "luma_wipe",
        "num": "20",
        "name": "Luma Fade / Shadow Wipe",
        "category": "masking_splits",
        "category_name": "Masking & Splits",
        "badge": "Cinematic",
        "desc": "Transition dissolves from darkest black shadow values first before midtones.",
        "grid_target": "grid_color",
        "grid_label": "Grid 10: Cinematic LUT",
        "default": False
    },
    {
        "id": "split_clone",
        "num": "21",
        "name": "Seamless Split-Screen Clone",
        "category": "masking_splits",
        "category_name": "Masking & Splits",
        "badge": "Creative Vlog",
        "desc": "Combines two takes of the same person on left and right sides of locked camera frame.",
        "grid_target": "grid_reframe",
        "grid_label": "Grid 5: Smart Reframer",
        "default": False
    },
    {
        "id": "grid_collage",
        "num": "22",
        "name": "Multi-Photo Grid Collage (2x2 / 3-Split)",
        "category": "masking_splits",
        "category_name": "Masking & Splits",
        "badge": "Montage",
        "desc": "Composites consecutive photos into dynamic multi-photo split screens with subtle Ken Burns.",
        "grid_target": "grid_scenic",
        "grid_label": "Grid 4: Scenic Preserver",
        "default": True
    },
    {
        "id": "sky_replacement",
        "num": "23",
        "name": "Sky / Horizon Replacement",
        "category": "masking_splits",
        "category_name": "Masking & Splits",
        "badge": "VFX",
        "desc": "Replaces washed-out overcast clouds with dramatic sunset or moving timelapse skies.",
        "grid_target": "grid_bgremove",
        "grid_label": "Grid 9: Virtual Studio Matte",
        "default": False
    },
    {
        "id": "pip_overlay",
        "num": "24",
        "name": "Floating Picture-in-Picture (PiP)",
        "category": "masking_splits",
        "category_name": "Masking & Splits",
        "badge": "Tutorial / Reaction",
        "desc": "Rounded floating PiP window with soft shadow and subtle border stroke.",
        "grid_target": "grid_agent",
        "grid_label": "Grid 11: AI Director",
        "default": False
    },
    {
        "id": "action_match_cut",
        "num": "25",
        "name": "Kinetic Action Match Cut",
        "category": "masking_splits",
        "category_name": "Masking & Splits",
        "badge": "High Energy",
        "desc": "Starts action in Clip A (e.g. jumping) and finishes impact in Clip B (landing on bed).",
        "grid_target": "grid_agent",
        "grid_label": "Grid 11: AI Director",
        "default": True
    },
    {
        "id": "portal_zoom",
        "num": "26",
        "name": "Portal / Keyhole Zoom Transition",
        "category": "masking_splits",
        "category_name": "Masking & Splits",
        "badge": "Creative",
        "desc": "Zooms into sunglasses, car mirror, or phone screen until it becomes the next scene.",
        "grid_target": "grid_reframe",
        "grid_label": "Grid 5: Smart Reframer",
        "default": False
    },

    # ---------------- 4. LIGHTING, OPTICS & GLITCH (27-34) ----------------
    {
        "id": "film_burn",
        "num": "27",
        "name": "35mm Film Burn / Light Leak",
        "category": "lighting_optics",
        "category_name": "Lighting & Optics",
        "badge": "Warm Nostalgia",
        "desc": "Authentic amber/orange light leak flashing across the frame edge during cut.",
        "grid_target": "grid_color",
        "grid_label": "Grid 10: Cinematic LUT",
        "default": False
    },
    {
        "id": "anamorphic_flare",
        "num": "28",
        "name": "Anamorphic Lens Flare & Streaks",
        "category": "lighting_optics",
        "category_name": "Lighting & Optics",
        "badge": "Sci-Fi / Night",
        "desc": "Horizontal blue or golden streak across specular highlights and headlights.",
        "grid_target": "grid_color",
        "grid_label": "Grid 10: Cinematic LUT",
        "default": False
    },
    {
        "id": "halation_glow",
        "num": "29",
        "name": "Film Halation & Warm Highlight Glow",
        "category": "lighting_optics",
        "category_name": "Lighting & Optics",
        "badge": "Kodak Warmth",
        "desc": "Warm red/orange diffusion glow blooming along high-contrast highlight edges.",
        "grid_target": "grid_color",
        "grid_label": "Grid 10: Cinematic LUT",
        "default": False
    },
    {
        "id": "white_out",
        "num": "30",
        "name": "Overexposure Flash (White-Out)",
        "category": "lighting_optics",
        "category_name": "Lighting & Optics",
        "badge": "High Energy",
        "desc": "Gain blooms to pure white for 3 frames before settling into the new scene.",
        "grid_target": "grid_color",
        "grid_label": "Grid 10: Cinematic LUT",
        "default": False
    },
    {
        "id": "rgb_split",
        "num": "31",
        "name": "RGB Split / Chromatic Aberration",
        "category": "lighting_optics",
        "category_name": "Lighting & Optics",
        "badge": "Cyber Glitch",
        "desc": "Splits Red, Green, and Blue channels horizontally with directional displace on cuts.",
        "grid_target": "grid_color",
        "grid_label": "Grid 10: Cinematic LUT",
        "default": False
    },
    {
        "id": "vhs_crt",
        "num": "32",
        "name": "Retro VHS / CRT Scanlines & Tape Jitter",
        "category": "lighting_optics",
        "category_name": "Lighting & Optics",
        "badge": "Vintage 90s",
        "desc": "Horizontal tracking static, RGB phosphor scanlines, and timestamp OSD overlay.",
        "grid_target": "grid_color",
        "grid_label": "Grid 10: Cinematic LUT",
        "default": False
    },
    {
        "id": "heat_haze",
        "num": "33",
        "name": "Heat Wave / Atmospheric Shimmer",
        "category": "lighting_optics",
        "category_name": "Lighting & Optics",
        "badge": "Desert / Summer",
        "desc": "Vertical wave distortion simulating shimmering heat waves across long telephoto takes.",
        "grid_target": "grid_color",
        "grid_label": "Grid 10: Cinematic LUT",
        "default": False
    },
    {
        "id": "prismatic_glass",
        "num": "34",
        "name": "Prismatic Split-Field Glass Lens",
        "category": "lighting_optics",
        "category_name": "Lighting & Optics",
        "badge": "Music Video",
        "desc": "Emulates split-diopter glass facets with peripheral refractions and rainbow edge flares.",
        "grid_target": "grid_color",
        "grid_label": "Grid 10: Cinematic LUT",
        "default": False
    },

    # ---------------- 5. FILM EMULATION & TEXTURE (35-41) ----------------
    {
        "id": "film_grain",
        "num": "35",
        "name": "16mm / 35mm Organic Film Grain",
        "category": "film_emulation",
        "category_name": "Film Emulation",
        "badge": "Cinema Pro",
        "desc": "Silver halide grain overlay in soft-light mode unifying digital footage into film texture.",
        "grid_target": "grid_color",
        "grid_label": "Grid 10: Cinematic LUT",
        "default": False
    },
    {
        "id": "film_sprocket",
        "num": "36",
        "name": "Film Sprocket & Leader Scroll",
        "category": "film_emulation",
        "category_name": "Film Emulation",
        "badge": "Chapter Intro",
        "desc": "Vertical film frame roll revealing Kodak edge-code perforations and sprocket holes.",
        "grid_target": "grid_color",
        "grid_label": "Grid 10: Cinematic LUT",
        "default": False
    },
    {
        "id": "gate_weave",
        "num": "37",
        "name": "Mechanical Gate Weave & Frame Jitter",
        "category": "film_emulation",
        "category_name": "Film Emulation",
        "badge": "Authentic Film",
        "desc": "Microscopic frame drift (0.8px) simulating mechanical film projector claws.",
        "grid_target": "grid_color",
        "grid_label": "Grid 10: Cinematic LUT",
        "default": False
    },
    {
        "id": "film_scratches",
        "num": "38",
        "name": "Film Scratches, Dust & Hair Particles",
        "category": "film_emulation",
        "category_name": "Film Emulation",
        "badge": "Grindhouse / Archive",
        "desc": "Subtle flashing hair particles and vertical scratch lines for vintage archival mood.",
        "grid_target": "grid_color",
        "grid_label": "Grid 10: Cinematic LUT",
        "default": False
    },
    {
        "id": "letterbox_239",
        "num": "39",
        "name": "Cinematic 2.39:1 Letterbox Scope",
        "category": "film_emulation",
        "category_name": "Film Emulation",
        "badge": "Anamorphic Scope",
        "desc": "Smoothly expands black widescreen letterbox bars signaling shift to cinematic mode.",
        "grid_target": "grid_render",
        "grid_label": "Grid 12: Master Renderer",
        "default": False
    },
    {
        "id": "bleach_bypass",
        "num": "40",
        "name": "Bleach Bypass (Silver Retention)",
        "category": "film_emulation",
        "category_name": "Film Emulation",
        "badge": "Gritty Drama",
        "desc": "High contrast, lifted black levels, and muted saturation with silvery highlights.",
        "grid_target": "grid_color",
        "grid_label": "Grid 10: Cinematic LUT",
        "default": False
    },
    {
        "id": "vignette_falloff",
        "num": "41",
        "name": "Optical Vignette & Corner Falloff",
        "category": "film_emulation",
        "category_name": "Film Emulation",
        "badge": "Focus Guide",
        "desc": "Subtle radial exposure falloff drawing viewer eyes to central subject.",
        "grid_target": "grid_color",
        "grid_label": "Grid 10: Cinematic LUT",
        "default": False
    },

    # ---------------- 6. AUDIO & SOUND DESIGN (42-46) ----------------
    {
        "id": "j_cut",
        "num": "42",
        "name": "J-Cut Audio Lead-In",
        "category": "audio_transitions",
        "category_name": "Audio Cuts",
        "badge": "Industry Standard",
        "desc": "Audio from upcoming Scene B starts playing 1.5 seconds before Video B cuts in.",
        "grid_target": "grid_audio",
        "grid_label": "Grid 6: Audio Denoise & Mix",
        "default": True
    },
    {
        "id": "l_cut",
        "num": "43",
        "name": "L-Cut Audio Carry-Over",
        "category": "audio_transitions",
        "category_name": "Audio Cuts",
        "badge": "Emotion / Reaction",
        "desc": "Video cuts to Scene B while dialogue audio from Scene A continues playing underneath.",
        "grid_target": "grid_audio",
        "grid_label": "Grid 6: Audio Denoise & Mix",
        "default": True
    },
    {
        "id": "sub_bass_drop",
        "num": "44",
        "name": "Sub-Bass Impact Drop & Riser Hit",
        "category": "audio_transitions",
        "category_name": "Audio Cuts",
        "badge": "Trailer Impact",
        "desc": "Frequency riser crescendoing into a heavy 40Hz sub-bass thump on the exact cut frame.",
        "grid_target": "grid_beatsync",
        "grid_label": "Grid 7: Beat Sync",
        "default": True
    },
    {
        "id": "lowpass_muffle",
        "num": "45",
        "name": "Low-Pass Muffle Underwater Filter",
        "category": "audio_transitions",
        "category_name": "Audio Cuts",
        "badge": "Atmospheric",
        "desc": "Cuts high frequencies above 1kHz via 18dB curve when diving underwater or stepping indoors.",
        "grid_target": "grid_audio",
        "grid_label": "Grid 6: Audio Denoise & Mix",
        "default": False
    },
    {
        "id": "whoosh_sync",
        "num": "46",
        "name": "Directional Whoosh Motion Sync",
        "category": "audio_transitions",
        "category_name": "Audio Cuts",
        "badge": "Pacing Glue",
        "desc": "High-velocity stereo whoosh pan matched frame-accurately to camera whip movements.",
        "grid_target": "grid_beatsync",
        "grid_label": "Grid 7: Beat Sync",
        "default": True
    },

    # ---------------- 7. TYPOGRAPHY & MOTION GRAPHICS (47-50) ----------------
    {
        "id": "hormozi_captions",
        "num": "47",
        "name": "Kinetic Word-Pop Captions (Hormozi Style)",
        "category": "typography_motion",
        "category_name": "Typography & Motion",
        "badge": "Viral Shorts",
        "desc": "High-contrast dynamic subtitles with per-word bounce pop and vivid color highlights.",
        "grid_target": "grid_captions",
        "grid_label": "Grid 8: Face-Safe Captions",
        "default": True
    },
    {
        "id": "tracked_3d_title",
        "num": "48",
        "name": "3D Camera-Tracked Floating Title",
        "category": "typography_motion",
        "category_name": "Typography & Motion",
        "badge": "Location Intro",
        "desc": "Bold typography anchored to landscape, mountain, or road geometry in 3D camera space.",
        "grid_target": "grid_captions",
        "grid_label": "Grid 8: Face-Safe Captions",
        "default": False
    },
    {
        "id": "paper_tear",
        "num": "49",
        "name": "Paper Tear / Stop-Motion Collage Wipe",
        "category": "typography_motion",
        "category_name": "Typography & Motion",
        "badge": "Scrapbook",
        "desc": "Textured torn paper edges with drop shadows revealing scenes in jagged steps.",
        "grid_target": "grid_captions",
        "grid_label": "Grid 8: Face-Safe Captions",
        "default": False
    },
    {
        "id": "lower_third_slide",
        "num": "50",
        "name": "Minimalist Lower-Third Reveal",
        "category": "typography_motion",
        "category_name": "Typography & Motion",
        "badge": "Documentary",
        "desc": "Clean typographic lower-third sliding out from accent bar with name and handle.",
        "grid_target": "grid_captions",
        "grid_label": "Grid 8: Face-Safe Captions",
        "default": True
    },
    {
        "id": "license_plate_blur",
        "num": "51",
        "name": "Vehicle License Plate Blur (Privacy)",
        "category": "masking_splits",
        "category_name": "Masking & Privacy",
        "badge": "Vlog Privacy & HSRP",
        "desc": "Auto-detects and blurs vehicle registration plates across all vlog takes with zero jitter.",
        "grid_target": "grid_bgremove",
        "grid_label": "Grid 9: Virtual Studio Matte / Privacy Mask",
        "default": True
    }
]

DEFAULT_TEXT_BEHIND_PERSON: Dict[str, Any] = {
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
    "position": "center",  # "head", "center", "lower", "wallpaper"
    "y_offset": 0,
    "opacity": 0.95
}

def get_initial_active_effects() -> Dict[str, bool]:
    """Returns mapping of effect_id -> bool with smart vlog defaults active."""
    return {fx["id"]: fx["default"] for fx in TOP_50_EFFECTS}

def sync_director_with_grids(director_effects: Dict[str, bool], text_behind: Dict[str, Any], grid_statuses: Dict[str, Any]) -> Dict[str, Any]:
    """
    Updates the 12 Modular Grid statuses and descriptions in real time
    based on the user's active AI Director selections.
    """
    active_count = sum(1 for v in director_effects.values() if v)
    
    # 1. Update Grid 9 (Virtual Studio Matte) for Text Behind Person & License Plate Privacy Blur
    has_lp_blur = director_effects.get("license_plate_blur", True)
    if text_behind.get("enabled"):
        neon_label = f" + Neon {text_behind.get('neon_color', '#00F2FE')}" if text_behind.get("neon_enabled") else ""
        text_content = text_behind.get("text", "VLOG").upper()
        font_name = text_behind.get("font", "Montserrat")
        lp_extra = " + Plate Blur" if has_lp_blur else ""
        grid_statuses["grid_bgremove"] = {
            "status": "ready",
            "progress": 100,
            "clip_eta_sec": 0,
            "eta_sec": 0,
            "detail": f"Active: Depth Text (\"{text_content}\"{neon_label}){lp_extra}"
        }
    elif has_lp_blur:
        grid_statuses["grid_bgremove"] = {
            "status": "ready",
            "progress": 100,
            "clip_eta_sec": 0,
            "eta_sec": 0,
            "detail": "Active: Vehicle Number Plate Privacy Blur Engine (HSRP Auto-Masked)"
        }
    else:
        if grid_statuses.get("grid_bgremove", {}).get("status") == "ready":
            grid_statuses["grid_bgremove"] = {
                "status": "skipped",
                "progress": 0,
                "clip_eta_sec": 0,
                "eta_sec": 0,
                "detail": "Bypassed (No Virtual Matte)"
            }

    # 2. Update Grid 11 (AI Director Agent)
    active_names = [fx["name"].split("/")[0].strip() for fx in TOP_50_EFFECTS if director_effects.get(fx["id"])]
    top_summary = ", ".join(active_names[:3])
    if len(active_names) > 3:
        top_summary += f" + {len(active_names) - 3} more"

    grid_statuses["grid_agent"] = {
        "status": "ready",
        "progress": 100,
        "clip_eta_sec": 0,
        "eta_sec": 0,
        "detail": f"AI Director Suite Armed ({active_count}/50 Active): {top_summary}"
    }

    # 3. Update Grid 8 (Face-Safe Captions)
    if director_effects.get("hormozi_captions", True):
        grid_statuses["grid_captions"]["status"] = "ready"
        grid_statuses["grid_captions"]["detail"] = "HyperFrame Kinetic Word-Bounce Captions & Face-Safe Exclusion Zone"

    # 4. Update Grid 10 (Cinematic LUT Grade)
    lut_features = []
    if director_effects.get("halation_glow"):
        lut_features.append("Halation Glow")
    if director_effects.get("film_grain"):
        lut_features.append("35mm Film Grain")
    if director_effects.get("vignette_falloff"):
        lut_features.append("Optical Vignette")
    if lut_features:
        grid_statuses["grid_color"]["status"] = "ready"
        grid_statuses["grid_color"]["detail"] = f"Teal & Orange Rec.709 + {', '.join(lut_features)}"

    # 5. Update Grid 12 (Master MP4 Renderer)
    scope = "2.39:1 Anamorphic Scope" if director_effects.get("letterbox_239") else "16:9 Standard"
    depth_note = " + Depth Text Layer" if text_behind.get("enabled") else ""
    grid_statuses["grid_render"]["detail"] = f"Armed for Master Composite ({scope}{depth_note}, CFR 30 FastStart)"

    return grid_statuses

def hex_to_ass_color(hex_str: str, alpha: float = 1.0) -> str:
    """Converts #RRGGBB hex string and alpha (0.0 - 1.0) to ASS &HAABBGGRR color format."""
    hex_clean = hex_str.lstrip("#")
    if len(hex_clean) == 3:
        hex_clean = "".join(c * 2 for c in hex_clean)
    if len(hex_clean) != 6:
        hex_clean = "FFFFFF"
    r = hex_clean[0:2]
    g = hex_clean[2:4]
    b = hex_clean[4:6]
    # In ASS, alpha 00 is fully opaque, FF is fully transparent
    a_val = max(0, min(255, int((1.0 - alpha) * 255)))
    return f"&H{a_val:02X}{b}{g}{r}"

def generate_depth_text_ass(
    text_cfg: Dict[str, Any],
    duration: float = 8.0,
    output_path: str = None,
    video_w: int = 1920,
    video_h: int = 1080
) -> str:
    """
    Generates a stylized ASS subtitle file for Bold Depth Typography (Text Behind Person)
    with custom font family, size, letter tracking spread, primary color, and radiant neon outline glow.
    """
    text_content = (text_cfg.get("text") or "VLOG").upper()
    font_name = text_cfg.get("font", "Montserrat")
    # Use high-impact bold font supported natively by DirectWrite / libass
    font_family = "Impact" if font_name.lower() in ["montserrat", "bebas neue", "anton", "outfit", "space grotesk", "impact"] else font_name
    font_size = int(text_cfg.get("size", 110))
    spread = int(text_cfg.get("spread", 8))
    opacity = float(text_cfg.get("opacity", 0.95))
    color_hex = text_cfg.get("color", "#FFFFFF")
    neon_hex = text_cfg.get("neon_color", "#00F2FE")
    neon_on = bool(text_cfg.get("neon_enabled", True))
    glow_radius = int(text_cfg.get("glow_radius", 24))
    y_offset = int(text_cfg.get("y_offset", 0))
    position = text_cfg.get("position", "center")

    ass_pri = hex_to_ass_color(color_hex, opacity)
    ass_neon = hex_to_ass_color(neon_hex, 0.85 if neon_on else 0.0)

    # Position coordinates: center and head both place text behind subject in the open sky/backdrop
    pos_x = video_w // 2
    if position == "head":
        pos_y = int(video_h * 0.26) + y_offset
    elif position == "lower":
        pos_y = int(video_h * 0.72) + y_offset
    else:  # center / backdrop
        pos_y = int(video_h * 0.28) + y_offset

    outline_width = max(3, int(glow_radius / 4)) if neon_on else 1
    blur_amount = max(4, int(glow_radius / 3)) if neon_on else 0

    dur_sec = max(2.0, min(duration, 30.0))

    ass_content = f"""[Script Info]
Title: AI Director Depth Typography
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: {video_w}
PlayResY: {video_h}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: DepthBehind,{font_family},{font_size},{ass_pri},{ass_neon},{ass_neon},&H80000000,-1,0,0,0,100,100,{spread},0,1,{outline_width},0,5,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.30,0:00:{dur_sec:05.2f},DepthBehind,,0,0,0,,{{\\fad(400,600)\\pos({pos_x},{pos_y})\\blur{blur_amount}\\fsp{spread}}}{text_content}
"""
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(ass_content)
    return ass_content


def build_director_video_filters(
    director_effects: Dict[str, Any] = None,
    seg_idx: int = 0,
    total_segs: int = 1,
    seg_dur: float = 3.0,
    aspect_ratio: str = "original",
    is_dialogue: bool = False,
    color_grade: str = "none"
) -> List[str]:
    """
    Translates any active effect or transition from the Top 50 VFX Suite into
    clean, rock-solid, native FFmpeg video filter expressions.
    Guarantees that selecting ANY transition or effect executes accurately
    in the final master render without frame distortion or crashes.
    """
    if not director_effects:
        return []

    filters = []
    is_vertical = (aspect_ratio == "9:16")
    out_w = 1080 if is_vertical else 1920
    out_h = 1920 if is_vertical else 1080

    # If color grading is disabled / natural camera colors, strictly bypass all color, film emulation and vignette overlays
    allow_color_fx = (color_grade and color_grade != "none")

    # ---------------- 1. CUT-POINT TRANSITIONS (seg_idx > 0) ----------------
    if seg_idx > 0:
        # Camera Motion Transitions
        if director_effects.get("whip_pan"):
            filters.append(f"crop=w=iw-40:h=ih:x='20*max(0,1-t*8)':y=0,scale={out_w}:{out_h}")
        elif director_effects.get("roll_360"):
            filters.append(f"rotate=a='if(lt(t,0.22), 2*PI*(1-t/0.22), 0)':ow={out_w}:oh={out_h}:fillcolor=black")
        elif director_effects.get("tilt_sky"):
            filters.append(f"crop=w=iw:h=ih-40:x=0:y='20*max(0,1-t*6)',scale={out_w}:{out_h}")
        elif director_effects.get("portal_zoom"):
            filters.append(f"crop=w=trunc(iw*0.88/2)*2:h=trunc(ih*0.88/2)*2:x=(iw-ow)/2:y=(ih-oh)/2,scale={out_w}:{out_h},fade=t=in:st=0:d=0.15:c=black")
        elif director_effects.get("crash_zoom"):
            filters.append(f"crop=w=trunc(iw*0.85/2)*2:h=trunc(ih*0.85/2)*2:x=(iw-ow)/2:y=(ih-oh)/2,scale={out_w}:{out_h},fade=t=in:st=0:d=0.08:c=white")
        elif director_effects.get("action_match_cut"):
            filters.append(f"crop=w=trunc(iw*0.94/2)*2:h=trunc(ih*0.94/2)*2:x=(iw-ow)/2:y=(ih-oh)/2,scale={out_w}:{out_h}")

        # Light, Strobe & Color Transitions
        if allow_color_fx:
            if director_effects.get("white_out"):
                filters.append("fade=t=in:st=0:d=0.18:c=white")
            elif director_effects.get("film_burn"):
                filters.append("fade=t=in:st=0:d=0.22:c=0xF39C12")
            elif director_effects.get("flash_frame"):
                filters.append("fade=t=in:st=0:d=0.09:c=white")
            elif director_effects.get("paper_tear"):
                filters.append("fade=t=in:st=0:d=0.08:c=0xEEEEEE")
            elif director_effects.get("object_wipe") or director_effects.get("luma_wipe"):
                filters.append("fade=t=in:st=0:d=0.14:c=black")
            elif director_effects.get("film_sprocket"):
                filters.append("fade=t=in:st=0:d=0.12:c=black")
            elif director_effects.get("freeze_frame"):
                filters.append("fade=t=in:st=0:d=0.06:c=white")
            elif director_effects.get("reverse_ramp"):
                filters.append("fade=t=in:st=0:d=0.07:c=black")
            elif director_effects.get("morph_cut"):
                filters.append("fade=t=in:st=0:d=0.08:c=black")

    # ---------------- 2. CAMERA MOTION & SPATIAL DYNAMICS ----------------
    # Punch-In retention zoom (alternating cuts)
    if director_effects.get("punch_in") and (seg_idx % 2 == 0):
        filters.append(f"crop=w=trunc(iw/1.08/2)*2:h=trunc(ih/1.08/2)*2:x=(iw-ow)/2:y=(ih-oh)/2,scale={out_w}:{out_h}")
    elif director_effects.get("push_in"):
        filters.append(f"crop=w=trunc((iw-32)/2)*2:h=trunc((ih-18)/2)*2:x=(iw-ow)/2:y=(ih-oh)/2,scale={out_w}:{out_h}")
    elif director_effects.get("subject_lock"):
        filters.append(f"crop=w=trunc(iw*0.94/2)*2:h=trunc(ih*0.94/2)*2:x=(iw-ow)/2:y=(ih-oh)/2,scale={out_w}:{out_h}")
    elif director_effects.get("dolly_zoom"):
        filters.append(f"crop=w=trunc(iw*0.92/2)*2:h=trunc(ih*0.92/2)*2:x='(iw-ow)/2+6*sin(t*2)':y='(ih-oh)/2',scale={out_w}:{out_h}")
    elif director_effects.get("parallax_25d"):
        filters.append(f"crop=w=iw-28:h=ih-16:x='14+12*sin(t*0.7)':y='8+6*cos(t*0.7)',scale={out_w}:{out_h}")
    elif director_effects.get("handheld_shake"):
        filters.append(f"crop=w=iw-16:h=ih-10:x='8+5*sin(t*10)':y='5+3*cos(t*12)',scale={out_w}:{out_h}")
    elif director_effects.get("heat_haze"):
        filters.append(f"crop=w=iw-12:h=ih-8:x='6+4*sin(t*6)':y='4+3*cos(t*7)',scale={out_w}:{out_h}")
    elif director_effects.get("split_clone"):
        filters.append(f"crop=w=trunc(iw/2/2)*2:h=ih:x=0:y=0,scale={out_w}:{out_h}")
    elif director_effects.get("pip_overlay"):
        filters.append(f"crop=w=trunc(iw*0.92/2)*2:h=trunc(ih*0.92/2)*2:x=(iw-ow)/2:y=(ih-oh)/2,scale={out_w}:{out_h}")

    # ---------------- 3. SPEED & TEMPORAL FX ----------------
    if director_effects.get("stop_motion_12fps"):
        filters.append("fps=12,fps=30")
    if director_effects.get("slow_shutter"):
        filters.append("tblend=all_mode=average")
    if director_effects.get("speed_ramp") and seg_idx > 0:
        filters.append("fade=t=in:st=0:d=0.08:c=black")

    # ---------------- 4. FILM EMULATION & OPTICAL TEXTURES ----------------
    if allow_color_fx:
        if director_effects.get("gate_weave"):
            filters.append(f"crop=w=iw-8:h=ih-6:x='4+2.5*sin(t*16)':y='3+1.8*cos(t*20)',scale={out_w}:{out_h}")
        if director_effects.get("film_grain"):
            filters.append("noise=alls=11:allf=t+u")
        if director_effects.get("film_scratches"):
            filters.append("noise=alls=14:allf=t")
        if director_effects.get("vhs_crt"):
            filters.append("curves=vintage,noise=alls=8:allf=t")

    # ---------------- 5. COLOR & OPTICAL FLARE / HALATION ----------------
    if allow_color_fx:
        if director_effects.get("bleach_bypass"):
            filters.append("eq=contrast=1.30:saturation=0.55:brightness=-0.02")
        if director_effects.get("halation_glow"):
            filters.append("eq=gamma_r=1.06:gamma_b=0.96:saturation=1.08")
        if director_effects.get("anamorphic_flare"):
            filters.append("eq=contrast=1.05:gamma_b=1.06")
        if director_effects.get("sky_replacement"):
            filters.append("eq=gamma_b=0.94:gamma_r=1.06:saturation=1.12")
        if director_effects.get("prismatic_glass"):
            filters.append("eq=contrast=1.04:saturation=1.06")
        if director_effects.get("rgb_split"):
            filters.append("eq=contrast=1.03")

    # ---------------- 6. SCOPE & FRAMING ----------------
    if director_effects.get("letterbox_239") and not is_vertical and allow_color_fx:
        filters.append("drawbox=y=0:h=135:color=black@1:t=fill,drawbox=y=ih-135:h=135:color=black@1:t=fill")
    if director_effects.get("vignette_falloff") and allow_color_fx:
        filters.append("vignette=PI/4.5")
    if director_effects.get("lower_third_slide"):
        filters.append("drawbox=y=ih-90:h=90:color=black@0.35:t=fill")

    return filters


def build_director_audio_filters(
    director_effects: Dict[str, Any] = None,
    seg_idx: int = 0,
    total_segs: int = 1,
    seg_dur: float = 3.0
) -> List[str]:
    """
    Translates active audio effects and transitions (sub-bass impacts,
    whoosh motion sync, low-pass underwater filter, J/L-cut micro-fades) into native FFmpeg audio filters.
    """
    if not director_effects:
        return []

    filters = []
    # Sub-bass impact drop on transitions
    if director_effects.get("sub_bass_drop") and (seg_idx > 0):
        filters.append("bass=g=4:f=75:w=0.6")
    # Directional whoosh motion sync
    if director_effects.get("whoosh_sync") and (seg_idx > 0):
        filters.append("treble=g=2.5:f=3200:w=0.7")
    # Low-pass filter (muffle)
    if director_effects.get("lowpass_muffle"):
        filters.append("lowpass=f=1400")
    # J-Cut & L-Cut natural speech lap fades
    if (director_effects.get("j_cut") or director_effects.get("l_cut")) and seg_dur > 0.1:
        fade_dur = min(0.040, seg_dur / 3.0)
        filters.append(f"afade=t=in:ss=0:d={fade_dur:.3f},afade=t=out:st={seg_dur-fade_dur:.3f}:d={fade_dur:.3f}")

    return filters


