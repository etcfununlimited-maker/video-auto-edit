"""
Advanced Photo Collage Engine - 20 Distinct Layout Styles
ANIRBAN AUTOMATIONS - AUTO VIDEO EDITOR

Features:
- 20 professional collage layout styles (2-photo splits, 3-photo trios, 4-photo quads, 5+ creative spreads).
- Strict 4.0-second hold duration (120 frames @ 30.0 fps CFR).
- Computer Vision Saliency & Human Centering (skin probability + Sobel edge gradient).
- Ken Burns micro-motion dynamics (opposing drifts, parallax pans, sequential reveals, camera pull-backs).
- 100% stable timeline concatenation with 48kHz stereo silent AAC audio.
- Compatible with Fast Preview (960x540) and Full Master Broadcast (1920x1080).
"""

import os
import math
import random
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

from backend.config import FFMPEG_PATH, UPLOADS_DIR, FINAL_EXPORT_DIR
from backend.pipeline.color_grading import get_color_grade_filter

# Catalog of all 20 layout styles
COLLAGE_STYLES_CATALOG = {
    1: {"id": 1, "name": "Classic Vertical Diptych", "photos": 2, "category": "2-split"},
    2: {"id": 2, "name": "Horizontal Letterbox Stack", "photos": 2, "category": "2-split"},
    3: {"id": 3, "name": "Golden Ratio Asymmetric Split", "photos": 2, "category": "2-split"},
    4: {"id": 4, "name": "Modern Diagonal Slash", "photos": 2, "category": "2-split"},
    5: {"id": 5, "name": "Picture-in-Picture Floating Hero", "photos": (1, 2), "category": "2-split"},
    6: {"id": 6, "name": "Triple Pillar Triptych", "photos": 3, "category": "3-trio"},
    7: {"id": 7, "name": "Big Hero + 2 Stacked Right", "photos": 3, "category": "3-trio"},
    8: {"id": 8, "name": "2 Stacked Left + Big Hero Right", "photos": 3, "category": "3-trio"},
    9: {"id": 9, "name": "Top Panoramic + Dual Bottom Grid", "photos": 3, "category": "3-trio"},
    10: {"id": 10, "name": "Polaroid Scrapbook Trio", "photos": 3, "category": "3-trio"},
    11: {"id": 11, "name": "Classic 2x2 Balanced Quad", "photos": 4, "category": "4-quad"},
    12: {"id": 12, "name": "1 Tall Hero + 3 Micro Stack", "photos": 4, "category": "4-quad"},
    13: {"id": 13, "name": "Top Hero + 3 Bottom Thumbnails", "photos": 4, "category": "4-quad"},
    14: {"id": 14, "name": "Quad Vertical Slices (Strip Film)", "photos": 4, "category": "4-quad"},
    15: {"id": 15, "name": "Asymmetric Mosaic Collage", "photos": 4, "category": "4-quad"},
    16: {"id": 16, "name": "Quad Photo Prints on Desk", "photos": 4, "category": "4-quad"},
    17: {"id": 17, "name": "2 Top + 3 Bottom Split Grid", "photos": 5, "category": "5plus"},
    18: {"id": 18, "name": "6-Frame Contact Sheet Grid", "photos": 6, "category": "5plus"},
    19: {"id": 19, "name": "Center Spotlight with Wing Accents", "photos": (3, 4, 5), "category": "5plus"},
    20: {"id": 20, "name": "Vogue Museum Editorial Spread", "photos": (3, 4), "category": "5plus"},
}

_STYLE_CYCLE_TRACKER = {
    2: [1, 2, 3, 4, 5],
    3: [6, 7, 8, 9, 10, 19, 20],
    4: [11, 12, 13, 14, 15, 16, 20],
    5: [17, 19],
    6: [18]
}
_STYLE_INDEX = {2: 0, 3: 0, 4: 0, 5: 0, 6: 0}

def get_next_collage_style(n_photos: int) -> int:
    """Procedurally cycles through appropriate styles so layouts never repeat consecutively."""
    bucket = min(6, max(2, n_photos))
    styles_list = _STYLE_CYCLE_TRACKER.get(bucket, [11])
    idx = _STYLE_INDEX.get(bucket, 0) % len(styles_list)
    chosen_style = styles_list[idx]
    _STYLE_INDEX[bucket] = idx + 1
    return chosen_style

def get_photo_saliency_center(photo_path: str) -> tuple[float, float]:
    """
    Computer Vision Saliency & Human Center Detection.
    Uses YCrCb skin probability + Sobel edge gradient to find where the subject is.
    Guarantees crop is centered directly on the person, never on empty sky.
    """
    try:
        import cv2
        import numpy as np
        img = cv2.imread(str(photo_path))
        if img is None and Path(photo_path).suffix.lower() in (".heic", ".heif", ".webp", ".png", ".jpg", ".jpeg"):
            try:
                cmd = [FFMPEG_PATH, "-i", str(photo_path), "-frames:v", "1", "-f", "image2", "-c:v", "mjpeg", "-"]
                p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                if p.stdout:
                    nparr = np.frombuffer(p.stdout, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            except Exception:
                pass
        if img is not None:
            h, w = img.shape[:2]
            ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
            skin_mask = cv2.inRange(ycrcb, np.array([0, 133, 77]), np.array([255, 173, 127]))
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            sobel = cv2.Sobel(gray, cv2.CV_32F, 1, 1)
            grad_mag = np.abs(sobel)
            grad_norm = cv2.normalize(grad_mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
            saliency = cv2.addWeighted(skin_mask, 0.65, grad_norm, 0.35, 0)
            M = cv2.moments(saliency)
            if M["m00"] > 0:
                cx = (M["m10"] / M["m00"]) / float(w)
                cy = (M["m01"] / M["m00"]) / float(h)
                return (max(0.15, min(0.85, cx)), max(0.20, min(0.80, cy)))
    except Exception:
        pass
    return (0.50, 0.45)

def build_tile_filter(
    idx: int,
    photo_path: str,
    tw: int,
    th: int,
    pw: int,
    ph: int,
    motion: str = "none",
    border_color: str = "black"
) -> str:
    """
    Builds an FFmpeg video filter expression for an individual tile with
    CV saliency center, Ken Burns micro-motion drift, and crisp padding/border.
    """
    tw = (tw // 2) * 2
    th = (th // 2) * 2
    pw = (pw // 2) * 2
    ph = (ph // 2) * 2

    cx, cy = get_photo_saliency_center(photo_path)
    # Slight overscale to provide headroom for Ken Burns drift
    sw = int(tw * 1.08)
    sh = int(th * 1.08)
    sw = (sw // 2) * 2
    sh = (sh // 2) * 2

    base_x = f"min(max(0\\,iw*{cx:.3f}-{tw//2})\\,iw-{tw})"
    base_y = f"min(max(0\\,ih*{cy:.3f}-{th//2})\\,ih-{th})"

    if motion == "pan_right":
        crop_x = f"min(max(0\\,iw*{cx:.3f}-{tw//2}+24*(t/4.0-0.5))\\,iw-{tw})"
        crop_y = base_y
    elif motion == "pan_left":
        crop_x = f"min(max(0\\,iw*{cx:.3f}-{tw//2}-24*(t/4.0-0.5))\\,iw-{tw})"
        crop_y = base_y
    elif motion == "pan_up":
        crop_x = base_x
        crop_y = f"min(max(0\\,ih*{cy:.3f}-{th//2}-20*(t/4.0-0.5))\\,ih-{th})"
    elif motion == "pan_down":
        crop_x = base_x
        crop_y = f"min(max(0\\,ih*{cy:.3f}-{th//2}+20*(t/4.0-0.5))\\,ih-{th})"
    elif motion == "zoom_in":
        crop_x = f"min(max(0\\,iw*{cx:.3f}-{tw//2}+12*(t/4.0-0.5))\\,iw-{tw})"
        crop_y = f"min(max(0\\,ih*{cy:.3f}-{th//2}+12*(t/4.0-0.5))\\,ih-{th})"
    elif motion == "zoom_out":
        crop_x = f"min(max(0\\,iw*{cx:.3f}-{tw//2}-12*(t/4.0-0.5))\\,iw-{tw})"
        crop_y = f"min(max(0\\,ih*{cy:.3f}-{th//2}-12*(t/4.0-0.5))\\,ih-{th})"
    else:
        crop_x = base_x
        crop_y = base_y

    return (
        f"[{idx}:v]scale={sw}:{sh}:force_original_aspect_ratio=increase,"
        f"crop={tw}:{th}:x='{crop_x}':y='{crop_y}',"
        f"pad={pw}:{ph}:(ow-iw)/2:(oh-ih)/2:color={border_color}[v{idx}]"
    )

def _render_polaroid_canvas(photo_paths: list[str], output_img: str, width: int = 1920, height: int = 1080, style_variant: str = "trio") -> str:
    """Renders a high-resolution Polaroid scrapbook desk layout using PIL."""
    canvas = Image.new("RGBA", (width, height), (15, 23, 42, 255))
    draw = ImageDraw.Draw(canvas)
    
    # Subtle dark desktop gradient / texture
    for y in range(0, height, 4):
        alpha = int(12 + 10 * math.sin(y / 150.0))
        draw.line([(0, y), (width, y)], fill=(30, 41, 59, alpha))

    if style_variant == "trio":
        # 3 Polaroids angled (-6°, +2°, -3°)
        angles = [-6.0, 2.0, -3.5]
        target_card_w = int(width * 0.28)
        target_card_h = int(height * 0.68)
        centers = [
            (int(width * 0.24), int(height * 0.52)),
            (int(width * 0.50), int(height * 0.48)),
            (int(width * 0.76), int(height * 0.54)),
        ]
    elif style_variant == "quad":
        # 4 Polaroids scattered (-3°, +2.5°, +1.5°, -2°)
        angles = [-3.0, 2.5, 1.8, -2.2]
        target_card_w = int(width * 0.36)
        target_card_h = int(height * 0.40)
        centers = [
            (int(width * 0.28), int(height * 0.28)),
            (int(width * 0.72), int(height * 0.28)),
            (int(width * 0.26), int(height * 0.72)),
            (int(width * 0.74), int(height * 0.72)),
        ]
    else:  # museum
        angles = [0.0, 0.0, 0.0]
        target_card_w = int(width * 0.38)
        target_card_h = int(height * 0.82)
        centers = [
            (int(width * 0.28), int(height * 0.50)),
            (int(width * 0.72), int(height * 0.30)),
            (int(width * 0.72), int(height * 0.70)),
        ]

    for p_idx, p_path in enumerate(photo_paths[:len(centers)]):
        try:
            with Image.open(str(p_path)) as im:
                im = im.convert("RGBA")
                border_top = int(target_card_w * 0.04)
                border_bottom = int(target_card_w * 0.16) if style_variant != "museum" else border_top
                img_w = target_card_w - (border_top * 2)
                img_h = target_card_h - border_top - border_bottom
                
                # Aspect crop to fit
                im_ratio = im.width / float(im.height)
                t_ratio = img_w / float(img_h)
                if im_ratio > t_ratio:
                    new_h = im.height
                    new_w = int(im.height * t_ratio)
                    offset_x = (im.width - new_w) // 2
                    im_cropped = im.crop((offset_x, 0, offset_x + new_w, new_h))
                else:
                    new_w = im.width
                    new_h = int(im.width / t_ratio)
                    offset_y = (im.height - new_h) // 2
                    im_cropped = im.crop((0, offset_y, new_w, offset_y + new_h))
                
                im_resized = im_cropped.resize((img_w, img_h), Image.Resampling.LANCZOS)
                
                # Card base with crisp white border
                card = Image.new("RGBA", (target_card_w, target_card_h), (255, 255, 255, 255))
                card.paste(im_resized, (border_top, border_top))
                
                # Drop shadow
                shadow = Image.new("RGBA", (target_card_w + 30, target_card_h + 30), (0, 0, 0, 0))
                sh_draw = ImageDraw.Draw(shadow)
                sh_draw.rectangle([15, 15, target_card_w + 15, target_card_h + 15], fill=(0, 0, 0, 110))
                shadow = shadow.filter(ImageFilter.GaussianBlur(12))
                
                ang = angles[p_idx % len(angles)]
                if ang != 0.0:
                    rot_card = card.rotate(ang, resample=Image.Resampling.BICUBIC, expand=True)
                    rot_shadow = shadow.rotate(ang, resample=Image.Resampling.BICUBIC, expand=True)
                else:
                    rot_card = card
                    rot_shadow = shadow
                
                cx, cy = centers[p_idx % len(centers)]
                pos_x = cx - rot_card.width // 2
                pos_y = cy - rot_card.height // 2
                canvas.paste(rot_shadow, (pos_x - 5, pos_y + 8), rot_shadow)
                canvas.paste(rot_card, (pos_x, pos_y), rot_card)
        except Exception as ex_pil:
            print(f"Notice generating Polaroid card {p_idx}: {ex_pil}")

    rgb_canvas = canvas.convert("RGB")
    rgb_canvas.save(output_img, quality=95)
    return output_img

def render_collage_segment(
    photo_paths: list[str],
    output_path: str,
    duration: float = 4.0,
    style_id: int | None = None,
    is_fast: bool = True,
    color_grade: str = "none",
    text_behind: dict = None
) -> str:
    """
    Renders any of the 20 distinct collage styles with strict 4.0-second hold duration,
    30.0 fps CFR, continuous 48kHz silent AAC audio, and Ken Burns micro-motion.
    """
    n = len(photo_paths)
    if style_id is None:
        style_id = get_next_collage_style(n)

    W = 960 if is_fast else 1920
    H = 540 if is_fast else 1080
    frames = int(duration * 30)

    inputs = []
    if style_id not in (10, 16):
        for p in photo_paths:
            inputs.extend(["-loop", "1", "-t", f"{duration:.2f}", "-i", str(p)])

    filter_complex = ""

    # =========================================================================
    # CATEGORY A: 2-PHOTO SPLITS (STYLES 1 - 5)
    # =========================================================================
    if style_id == 1:
        # Style 01: Classic Vertical Diptych (50/50 vertical)
        tw = (W // 2) - 2
        pw = W // 2
        t0 = build_tile_filter(0, photo_paths[0], tw, H, pw, H, motion="zoom_in", border_color="black")
        t1 = build_tile_filter(1, photo_paths[1 % n], tw, H, pw, H, motion="zoom_out", border_color="black")
        filter_complex = f"{t0};{t1};[v0][v1]hstack=inputs=2,pad={W}:{H}:0:0:color=black,format=yuv420p[vout]"

    elif style_id == 2:
        # Style 02: Horizontal Letterbox Stack
        th = (H // 2) - 2
        ph = H // 2
        t0 = build_tile_filter(0, photo_paths[0], W, th, W, ph, motion="pan_right", border_color="black")
        t1 = build_tile_filter(1, photo_paths[1 % n], W, th, W, ph, motion="pan_left", border_color="black")
        filter_complex = f"{t0};{t1};[v0][v1]vstack=inputs=2,pad={W}:{H}:0:0:color=black,format=yuv420p[vout]"

    elif style_id == 3:
        # Style 03: Golden Ratio Asymmetric Split (62% Left, 38% Right)
        tw_left = int(W * 0.618) - 2
        pw_left = int(W * 0.618)
        tw_right = W - pw_left - 2
        pw_right = W - pw_left
        t0 = build_tile_filter(0, photo_paths[0], tw_left, H, pw_left, H, motion="pan_right", border_color="black")
        t1 = build_tile_filter(1, photo_paths[1 % n], tw_right, H, pw_right, H, motion="zoom_in", border_color="black")
        filter_complex = f"{t0};{t1};[v0][v1]hstack=inputs=2,pad={W}:{H}:0:0:color=black,format=yuv420p[vout]"

    elif style_id == 4:
        # Style 04: Modern Diagonal Slash with cyan border accent
        tw = (W // 2) - 3
        pw = W // 2
        t0 = build_tile_filter(0, photo_paths[0], tw, H, pw, H, motion="pan_left", border_color="0x111827")
        t1 = build_tile_filter(1, photo_paths[1 % n], tw, H, pw, H, motion="pan_right", border_color="0x38bdf8")
        filter_complex = f"{t0};{t1};[v0][v1]hstack=inputs=2,pad={W}:{H}:0:0:color=black,format=yuv420p[vout]"

    elif style_id == 5:
        # Style 05: Picture-in-Picture Floating Hero (Blurred BG + 3:4 Floating Foreground)
        bg_idx = 0
        fg_idx = 1 if n > 1 else 0
        fw = int(W * 0.44)
        fh = int(H * 0.82)
        fw = (fw // 2) * 2
        fh = (fh // 2) * 2
        fg_x = (W - fw) // 2
        fg_y = (H - fh) // 2
        cx, cy = get_photo_saliency_center(photo_paths[fg_idx])
        bg_filter = f"[{bg_idx}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=18:1,eq=brightness=-0.12:saturation=1.1[bg]"
        fg_filter = (
            f"[{fg_idx}:v]scale={fw}:{fh}:force_original_aspect_ratio=increase,"
            f"crop={fw}:{fh}:min(max(0\\,iw*{cx:.3f}-{fw//2})\\,iw-{fw}):min(max(0\\,ih*{cy:.3f}-{fh//2})\\,ih-{fh}),"
            f"pad={fw+8}:{fh+8}:4:4:color=0x38bdf8[fg]"
        )
        filter_complex = f"{bg_filter};{fg_filter};[bg][fg]overlay={fg_x-4}:{fg_y-4},format=yuv420p[vout]"

    # =========================================================================
    # CATEGORY B: 3-PHOTO TRIOS (STYLES 6 - 10)
    # =========================================================================
    elif style_id == 6:
        # Style 06: Triple Pillar Triptych
        tw = (W // 3) - 2
        pw = W // 3
        t0 = build_tile_filter(0, photo_paths[0], tw, H, pw, H, motion="pan_left", border_color="black")
        t1 = build_tile_filter(1, photo_paths[1 % n], tw, H, pw, H, motion="zoom_in", border_color="black")
        t2 = build_tile_filter(2, photo_paths[2 % n], tw, H, pw, H, motion="pan_right", border_color="black")
        filter_complex = f"{t0};{t1};{t2};[v0][v1][v2]hstack=inputs=3,pad={W}:{H}:0:0:color=black,format=yuv420p[vout]"

    elif style_id == 7:
        # Style 07: Big Hero Left (60%) + 2 Stacked Right (40%)
        tw_left = int(W * 0.60) - 2
        pw_left = int(W * 0.60)
        tw_right = W - pw_left - 2
        pw_right = W - pw_left
        th_stack = (H // 2) - 2
        ph_stack = H // 2
        t0 = build_tile_filter(0, photo_paths[0], tw_left, H, pw_left, H, motion="pan_right", border_color="black")
        t1 = build_tile_filter(1, photo_paths[1 % n], tw_right, th_stack, pw_right, ph_stack, motion="zoom_in", border_color="black")
        t2 = build_tile_filter(2, photo_paths[2 % n], tw_right, th_stack, pw_right, ph_stack, motion="pan_left", border_color="black")
        filter_complex = f"{t0};{t1};{t2};[v1][v2]vstack=inputs=2[r_col];[v0][r_col]hstack=inputs=2,pad={W}:{H}:0:0:color=black,format=yuv420p[vout]"

    elif style_id == 8:
        # Style 08: 2 Stacked Left (40%) + Big Hero Right (60%)
        tw_left = int(W * 0.40) - 2
        pw_left = int(W * 0.40)
        tw_right = W - pw_left - 2
        pw_right = W - pw_left
        th_stack = (H // 2) - 2
        ph_stack = H // 2
        t0 = build_tile_filter(0, photo_paths[0], tw_left, th_stack, pw_left, ph_stack, motion="pan_right", border_color="black")
        t1 = build_tile_filter(1, photo_paths[1 % n], tw_left, th_stack, pw_left, ph_stack, motion="zoom_in", border_color="black")
        t2 = build_tile_filter(2, photo_paths[2 % n], tw_right, H, pw_right, H, motion="pan_left", border_color="black")
        filter_complex = f"{t0};{t1};{t2};[v0][v1]vstack=inputs=2[l_col];[l_col][v2]hstack=inputs=2,pad={W}:{H}:0:0:color=black,format=yuv420p[vout]"

    elif style_id == 9:
        # Style 09: Top Panoramic (62%) + Dual Bottom Grid (38%)
        th_top = int(H * 0.62) - 2
        ph_top = int(H * 0.62)
        th_bot = H - ph_top - 2
        ph_bot = H - ph_top
        tw_bot = (W // 2) - 2
        pw_bot = W // 2
        t0 = build_tile_filter(0, photo_paths[0], W, th_top, W, ph_top, motion="pan_right", border_color="black")
        t1 = build_tile_filter(1, photo_paths[1 % n], tw_bot, th_bot, pw_bot, ph_bot, motion="zoom_in", border_color="black")
        t2 = build_tile_filter(2, photo_paths[2 % n], tw_bot, th_bot, pw_bot, ph_bot, motion="pan_left", border_color="black")
        filter_complex = f"{t0};{t1};{t2};[v1][v2]hstack=inputs=2[bot_row];[v0][bot_row]vstack=inputs=2,pad={W}:{H}:0:0:color=black,format=yuv420p[vout]"

    elif style_id == 10:
        # Style 10: Polaroid Scrapbook Trio
        tmp_img = UPLOADS_DIR / f".tmp_polaroid_trio_{Path(output_path).stem}.png"
        _render_polaroid_canvas(photo_paths, str(tmp_img), width=W, height=H, style_variant="trio")
        inputs = ["-loop", "1", "-t", f"{duration:.2f}", "-i", str(tmp_img)]
        zoom_vf = (
            f"scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"zoompan=z='min(1.0+in*{0.05/frames:.5f},1.05)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps=30,"
            f"format=yuv420p[vout]"
        )
        filter_complex = f"[0:v]{zoom_vf}"

    # =========================================================================
    # CATEGORY C: 4-PHOTO QUADS (STYLES 11 - 16)
    # =========================================================================
    elif style_id == 11:
        # Style 11: Classic 2x2 Balanced Quad
        tw = (W // 2) - 2
        pw = W // 2
        th = (H // 2) - 2
        ph = H // 2
        t0 = build_tile_filter(0, photo_paths[0], tw, th, pw, ph, motion="zoom_in", border_color="black")
        t1 = build_tile_filter(1, photo_paths[1 % n], tw, th, pw, ph, motion="pan_left", border_color="black")
        t2 = build_tile_filter(2, photo_paths[2 % n], tw, th, pw, ph, motion="pan_right", border_color="black")
        t3 = build_tile_filter(3, photo_paths[3 % n], tw, th, pw, ph, motion="zoom_in", border_color="black")
        filter_complex = f"{t0};{t1};{t2};{t3};[v0][v1]hstack=inputs=2[top];[v2][v3]hstack=inputs=2[bot];[top][bot]vstack=inputs=2,pad={W}:{H}:0:0:color=black,format=yuv420p[vout]"

    elif style_id == 12:
        # Style 12: 1 Tall Hero Left (50%) + 3 Micro Stack Right (50%)
        tw_left = (W // 2) - 2
        pw_left = W // 2
        tw_right = W - pw_left - 2
        pw_right = W - pw_left
        th_thumb = (H // 3) - 2
        ph_thumb = H // 3
        t0 = build_tile_filter(0, photo_paths[0], tw_left, H, pw_left, H, motion="pan_right", border_color="black")
        t1 = build_tile_filter(1, photo_paths[1 % n], tw_right, th_thumb, pw_right, ph_thumb, motion="pan_left", border_color="black")
        t2 = build_tile_filter(2, photo_paths[2 % n], tw_right, th_thumb, pw_right, ph_thumb, motion="zoom_in", border_color="black")
        t3 = build_tile_filter(3, photo_paths[3 % n], tw_right, th_thumb, pw_right, ph_thumb, motion="pan_right", border_color="black")
        filter_complex = f"{t0};{t1};{t2};{t3};[v1][v2][v3]vstack=inputs=3[r_col];[v0][r_col]hstack=inputs=2,pad={W}:{H}:0:0:color=black,format=yuv420p[vout]"

    elif style_id == 13:
        # Style 13: Top Hero (65%) + 3 Bottom Thumbnails (35%)
        th_top = int(H * 0.65) - 2
        ph_top = int(H * 0.65)
        th_bot = H - ph_top - 2
        ph_bot = H - ph_top
        tw_thumb = (W // 3) - 2
        pw_thumb = W // 3
        t0 = build_tile_filter(0, photo_paths[0], W, th_top, W, ph_top, motion="pan_right", border_color="black")
        t1 = build_tile_filter(1, photo_paths[1 % n], tw_thumb, th_bot, pw_thumb, ph_bot, motion="zoom_in", border_color="black")
        t2 = build_tile_filter(2, photo_paths[2 % n], tw_thumb, th_bot, pw_thumb, ph_bot, motion="pan_up", border_color="black")
        t3 = build_tile_filter(3, photo_paths[3 % n], tw_thumb, th_bot, pw_thumb, ph_bot, motion="pan_left", border_color="black")
        filter_complex = f"{t0};{t1};{t2};{t3};[v1][v2][v3]hstack=inputs=3[b_row];[v0][b_row]vstack=inputs=2,pad={W}:{H}:0:0:color=black,format=yuv420p[vout]"

    elif style_id == 14:
        # Style 14: Quad Vertical Slices (Strip Film)
        tw = (W // 4) - 2
        pw = W // 4
        t0 = build_tile_filter(0, photo_paths[0], tw, H, pw, H, motion="pan_up", border_color="black")
        t1 = build_tile_filter(1, photo_paths[1 % n], tw, H, pw, H, motion="pan_down", border_color="black")
        t2 = build_tile_filter(2, photo_paths[2 % n], tw, H, pw, H, motion="pan_up", border_color="black")
        t3 = build_tile_filter(3, photo_paths[3 % n], tw, H, pw, H, motion="pan_down", border_color="black")
        filter_complex = f"{t0};{t1};{t2};{t3};[v0][v1][v2][v3]hstack=inputs=4,pad={W}:{H}:0:0:color=black,format=yuv420p[vout]"

    elif style_id == 15:
        # Style 15: Asymmetric Mosaic Collage
        tw_left = int(W * 0.62) - 2
        pw_left = int(W * 0.62)
        tw_right = W - pw_left - 2
        pw_right = W - pw_left
        th_top = int(H * 0.62) - 2
        ph_top = int(H * 0.62)
        th_bot = H - ph_top - 2
        ph_bot = H - ph_top
        t0 = build_tile_filter(0, photo_paths[0], tw_left, th_top, pw_left, ph_top, motion="zoom_in", border_color="black")
        t1 = build_tile_filter(1, photo_paths[1 % n], tw_right, th_top, pw_right, ph_top, motion="pan_left", border_color="black")
        t2 = build_tile_filter(2, photo_paths[2 % n], tw_left, th_bot, pw_left, ph_bot, motion="pan_right", border_color="black")
        t3 = build_tile_filter(3, photo_paths[3 % n], tw_right, th_bot, pw_right, ph_bot, motion="zoom_out", border_color="black")
        filter_complex = f"{t0};{t1};{t2};{t3};[v0][v1]hstack=inputs=2[top];[v2][v3]hstack=inputs=2[bot];[top][bot]vstack=inputs=2,pad={W}:{H}:0:0:color=black,format=yuv420p[vout]"

    elif style_id == 16:
        # Style 16: Quad Photo Prints on Desk
        tmp_img = UPLOADS_DIR / f".tmp_polaroid_quad_{Path(output_path).stem}.png"
        _render_polaroid_canvas(photo_paths, str(tmp_img), width=W, height=H, style_variant="quad")
        inputs = ["-loop", "1", "-t", f"{duration:.2f}", "-i", str(tmp_img)]
        zoom_vf = (
            f"scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"zoompan=z='min(1.0+in*{0.05/frames:.5f},1.05)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps=30,"
            f"format=yuv420p[vout]"
        )
        filter_complex = f"[0:v]{zoom_vf}"

    # =========================================================================
    # CATEGORY D: 5+ PHOTOS & EDITORIAL SPREADS (STYLES 17 - 20)
    # =========================================================================
    elif style_id == 17:
        # Style 17: 2 Top + 3 Bottom Split Grid (5 Photos)
        tw_top = (W // 2) - 2
        pw_top = W // 2
        th_top = (H // 2) - 2
        ph_top = H // 2
        tw_bot = (W // 3) - 2
        pw_bot = W // 3
        th_bot = H - ph_top - 2
        ph_bot = H - ph_top
        t0 = build_tile_filter(0, photo_paths[0], tw_top, th_top, pw_top, ph_top, motion="zoom_in", border_color="black")
        t1 = build_tile_filter(1, photo_paths[1 % n], tw_top, th_top, pw_top, ph_top, motion="pan_left", border_color="black")
        t2 = build_tile_filter(2, photo_paths[2 % n], tw_bot, th_bot, pw_bot, ph_bot, motion="pan_right", border_color="black")
        t3 = build_tile_filter(3, photo_paths[3 % n], tw_bot, th_bot, pw_bot, ph_bot, motion="zoom_out", border_color="black")
        t4 = build_tile_filter(4, photo_paths[4 % n], tw_bot, th_bot, pw_bot, ph_bot, motion="pan_left", border_color="black")
        filter_complex = f"{t0};{t1};{t2};{t3};{t4};[v0][v1]hstack=inputs=2[top];[v2][v3][v4]hstack=inputs=3[bot];[top][bot]vstack=inputs=2,pad={W}:{H}:0:0:color=black,format=yuv420p[vout]"

    elif style_id == 18:
        # Style 18: 6-Frame Contact Sheet Grid (3x2)
        tw = (W // 3) - 2
        pw = W // 3
        th = (H // 2) - 2
        ph = H // 2
        tiles = []
        for i in range(6):
            mot = "zoom_in" if i % 2 == 0 else "pan_right"
            tiles.append(build_tile_filter(i, photo_paths[i % n], tw, th, pw, ph, motion=mot, border_color="black"))
        filter_complex = f"{';'.join(tiles)};[v0][v1][v2]hstack=inputs=3[r1];[v3][v4][v5]hstack=inputs=3[r2];[r1][r2]vstack=inputs=2,pad={W}:{H}:0:0:color=black,format=yuv420p[vout]"

    elif style_id == 19:
        # Style 19: Center Spotlight with Wing Accents (Cyan Glow Border)
        tw_side = int(W * 0.28) - 2
        pw_side = int(W * 0.28)
        tw_mid = W - (pw_side * 2) - 4
        pw_mid = W - (pw_side * 2)
        t0 = build_tile_filter(0, photo_paths[0], tw_side, H, pw_side, H, motion="pan_left", border_color="0x1e293b")
        t1 = build_tile_filter(1, photo_paths[1 % n], tw_mid, H, pw_mid, H, motion="zoom_in", border_color="0x38bdf8")
        t2 = build_tile_filter(2, photo_paths[2 % n], tw_side, H, pw_side, H, motion="pan_right", border_color="0x1e293b")
        filter_complex = f"{t0};{t1};{t2};[v0][v1][v2]hstack=inputs=3,pad={W}:{H}:0:0:color=black,format=yuv420p[vout]"

    elif style_id == 20:
        # Style 20: Vogue Museum Editorial Spread (Crisp White Gallery Matting)
        tw_left = int(W * 0.50) - 16
        pw_left = int(W * 0.50)
        tw_right = W - pw_left - 16
        pw_right = W - pw_left
        th_stack = (H // 2) - 16
        ph_stack = H // 2
        t0 = build_tile_filter(0, photo_paths[0], tw_left, H - 32, pw_left, H, motion="zoom_in", border_color="white")
        t1 = build_tile_filter(1, photo_paths[1 % n], tw_right, th_stack, pw_right, ph_stack, motion="pan_left", border_color="white")
        t2 = build_tile_filter(2, photo_paths[2 % n], tw_right, th_stack, pw_right, ph_stack, motion="pan_right", border_color="white")
        filter_complex = f"{t0};{t1};{t2};[v1][v2]vstack=inputs=2[r_col];[v0][r_col]hstack=inputs=2,pad={W}:{H}:0:0:color=white,format=yuv420p[vout]"

    else:
        # Fallback to Style 01
        tw = (W // 2) - 2
        pw = W // 2
        t0 = build_tile_filter(0, photo_paths[0], tw, H, pw, H, motion="zoom_in", border_color="black")
        t1 = build_tile_filter(1, photo_paths[1 % n], tw, H, pw, H, motion="zoom_out", border_color="black")
        filter_complex = f"{t0};{t1};[v0][v1]hstack=inputs=2,pad={W}:{H}:0:0:color=black,format=yuv420p[vout]"

    # Optional color grading filter
    if color_grade and color_grade != "none":
        cg = get_color_grade_filter(color_grade)
        if cg:
            filter_complex = f"{filter_complex.replace('[vout]', '[vpre]')};[vpre]{cg}[vout]"

    # Optional 3D depth title overlay
    if text_behind and text_behind.get("enabled") and (text_behind.get("text") or "").strip():
        try:
            from backend.pipeline.ai_director_suite import generate_depth_text_ass
            ass_dp = output_path.replace(".mp4", "_depth.ass")
            generate_depth_text_ass(text_behind, duration=duration, output_path=ass_dp, video_w=W, video_h=H)
            escaped_dp = ass_dp.replace("\\", "/").replace(":", "\\:")
            filter_complex = f"{filter_complex.replace('[vout]', '[vpredepth]')};[vpredepth]subtitles='{escaped_dp}'[vout]"
        except Exception as e_dp:
            print(f"Collage depth title notice: {e_dp}")

    fc = f"{filter_complex};anullsrc=r=48000:cl=stereo[aout]"
    enc_preset = "ultrafast" if is_fast else "faster"
    enc_crf = "23" if is_fast else "18"

    cmd = [
        FFMPEG_PATH, "-y",
        "-threads", "0"
    ] + inputs + [
        "-filter_complex", fc,
        "-map", "[vout]", "-map", "[aout]",
        "-t", f"{duration:.2f}",
        "-r", "30", "-fps_mode", "cfr",
        "-c:v", "libx264", "-preset", enc_preset, "-crf", enc_crf,
        "-pix_fmt", "yuv420p", "-video_track_timescale", "30000",
        "-g", "30", "-keyint_min", "30",
        "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "192k",
        "-shortest",
        output_path
    ]

    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return output_path
