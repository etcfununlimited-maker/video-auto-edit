# 🎬 AUTO VIDEO EDITOR — ANIRBAN AUTOMATIONS (PRO v3.1.0)

An AI-powered automated video editing studio designed for high-retention content creation, viral social media reframing, intelligent scene preservation, and code-driven motion graphics.

Built specifically to process **standard MP4s, iPhone 16 HEVC / Apple ProRes / HDR footage, Android, and DSLR media** with a unified 12-Grid progress tracking dashboard.

---

## 🚀 Major Release Milestone: What's New in v3.1.0

1. **Premiere Pro & Instagram Multi-Track NLE Studio (V1–V4, A1–A2)**
   - Per-track and per-clip interactive editing: Track V1 (10 Master Video Clips), Track V2 (Title Overlay Graphic), Track V3 (Hormozi Kinetic Dynamic Animated Overlay), Track V4 (Native Editable Title Generator), Track A1 (Voice Dialogue with Denoise & Level Filters), Track A2 (Music Bed with Auto-Ducking Envelopes).
   - Per-clip volume control, mute toggles, noise suppression sliders (0–100%), and interactive track movement.

2. **Automated 1-Click Premiere Pro 2024 / 2025 / 2026 Import Automation**
   - Native Windows automation script (`scripts/import_to_premiere.py`) that focuses running Premiere Pro and executes 1-click import for `PREMIERE_PRO_PROJECT.xml` and `CAPTIONS.srt`.
   - Broadcast-compliant Apple FCP XML (xmeml v4) architecture with strictly monotonic keyframes, stereo output mapping, and frame-accurate timecodes.

3. **Frame-Accurate Hormozi Kinetic Animated Overlay for Premiere Pro**
   - Renders 32-bit transparent QuickTime animation (`PREMIERE_HORMUZI_CAPTIONS.mov`) with alpha channel transparency.
   - Word-by-word bounce pop scaling (135% -> 100%), Electric Yellow active word highlights (`#FFE500`), thick black outline, and face-safe positioning. Composites natively over video in Premiere Pro.

4. **Sequence-Aware Multi-Clip Caption Stitcher**
   - `get_sequence_aligned_words` dynamically pulls exact transcripts for all 10 sequence clips from `.transcript_cache_*.json`.
   - Offsets word timestamps by exact head positions on the timeline, generating frame-accurate `CAPTIONS.srt` matching Clip 1 to Clip 10 with zero drift.

5. **Curated 13-Track Active Royalty-Free Music Library**
   - Active library curated to 13 high-energy tracks: Airport Lounge, B-Roll, Big Rock, Carefree, Cool Rock, Daily Beetle, Funkorama, Life of Riley, Pamgaea, Protofunk, Somewhere Sunny, Upbeat Forever, and Werq.
   - 16 secondary tracks safely archived to `raw_input/MUSIC/library`.

6. **Fast 360p / 260p Proxy Multi-Track Render (<10 mins)**
   - Multi-track timeline preview and fast proxy exports with Clarendon / Instagram color grading.

---

## 🚀 Major Release Milestone: What's New in v3.0.0

1. **Full Feature Movie Timeline Engine (All 304 Clips Assembled)**
   - Automatically sequences all authentic clips across `raw_input/` (73 video takes + 231 photos across 21 computer-vision saliency collages, 94 total timeline elements).
   - Assembles full-length 1 hour 14 minute continuous movie (`01:14:07`) with seamless segment transitions and zero dropped frames.
   - Dynamic multi-clip selection sync between client and server with automatic full-library fallback for Full Movie mode.

2. **100% Uncut Continuous Takes & Frame-Locked Lip Sync**
   - Overhauled spoken retake arbitration in `silence_remover.py` with expanded Hindi/Hinglish particle protection (`"pe hai"`, `"sab kuchh"`, `"usake baad"`), eliminating false cuts.
   - 0.0 ms phase-locked lip sync matching speaking postures across all takes at 30.0 fps CFR.

3. **Studio Vocal Presence & 20% Deeper Zero-Latency Denoise (Grid 6)**
   - Dual-stage noise suppression: 115 Hz highpass, dual notches at 220 Hz and 440 Hz targeting vehicle cabin/blower resonance, 11 kHz lowpass, and non-linear downward expander (8–10 dB pause suppression).
   - Boosted clean speech presence by +3.2 dB (`speech_boost = 1.45`) for crystal-clear vocal presence.

4. **Dynamic Sidechain Music Auto-Ducking (+10% Music Boost)**
   - Background music bed boosted to `music_volume = 0.40`.
   - Vocal-keyed sidechain ducking (6.0:1 ratio, 0.030 threshold, 15ms attack, 550ms release) across 28 multi-track themes.

5. **Face-Safe HyperFrame Kinetic Animated Captions**
   - Dynamic word-bounce subtitles placed strictly outside human face exclusion zones.

6. **Automated Desktop Deliverables**
   - Direct automatic export and mirroring to `Desktop/MASTER_FULL_FEATURE_MOVIE_304_CLIPS.mp4` and `Desktop/MASTER_FULL_FEATURE_MOVIE.mp4`.

---

## 🌟 Previous Highlights (v2.x Series)

1. **Continuous Speech Protection (Strict Dialogue Cadence)**
   - Protects dialogue takes from mid-sentence or mid-phrase cuts.
   - Preserves natural human breathing and conversational cadence intact.
   - Trims only pre-roll lead-in dead air before speech, post-roll camera shut-off silence, and explicit false-start clusters via exact decoded keyframes.

2. **100% Constant Frame Rate (CFR 30.0 fps Lock - Zero Freezing)**
   - Normalizes every timeline segment to strict **CFR 30.0 fps**, timescale `30000`, closed keyframe intervals (`-g 30 -keyint_min 30`), and **48,000 Hz Stereo AAC**.
   - Completely eliminates video decoder freezing, choppy playback, and audio desync.
   - Outputs universal MP4 (H.264 High@L4.2, YUV420P Rec.709, FastStart) for 100% native Windows Media Player and browser compatibility.

3. **Smart Orientation & Ambient Background Fill (0% Sideways Footage)**
   - Allows native container display matrix auto-rotation so iPhone and smartphone footage is never rendered sideways.
   - Automatically detects portrait selfie takes (`1080x1920`) in 16:9 widescreen and renders a high-definition **blurred ambient background composite** with 0% black bars.

4. **Dynamic Multi-Photo Grid Collages**
   - Automatically groups consecutive still photos and Live Photos into dynamic multi-grid collages:
     - **3-Photo Groups:** 3-column vertical split collages (640x1080 each).
     - **4-Photo Groups:** 2x2 multi-grid collages (960x540 each).
     - **2-Photo Groups:** Dual-split vertical panels (960x1080 each).
   - Single photos capped to max 1.8s with smooth Ken Burns zoom.

5. **HyperFrames Motion Graphics Studio (HTML5 / CSS3 / JavaScript)**
   - Inspired by HeyGen HyperFrames: programmatic code-to-video motion graphics.
   - Built-in studio modal with 60 FPS live preview and interactive code editor tabs (`HTML5`, `CSS3 Keyframes`, `JavaScript`).
   - Presets include:
     - **GoPro Action Telemetry HUD:** Live pulsing `REC 4K 60FPS`, GPS coordinates chip, route banner (`DELHI ISBT ➔ KANGRA VALLEY`), dynamic speedometer, altitude, and G-force gauges.
     - **YouTube Creator Glassmorphism Lower-Third:** Frosted glass card with rotating animated gradient border, profile badge, verified checkmark, and 4K Ultra HD chip.
     - **Cinematic Minimalist Expedition Title:** High-end typography with expanding letter-spacing and amber dividers.
   - One-click **Apply to Active Video** overlay directly in the Studio player.

6. **GoPro 30-Second Kinetic Summary & 4K Simulated Drone Reel**
   - Renders fast-paced GoPro style 30-second highlight teasers with speed ramps and kinetic transitions.
   - Simulates 4K aerial drone cinematics from landscape footage with smooth parabolic cruising and tilt.

---

## 🌟 Core Features

1. **Intelligent Scene Detection & Scenic Silence Protection**
   - Categorizes shots into Nature, Sky, Mountains, Roads, or Dialogue.
   - Silences during scenic B-roll are detected and protected, ensuring artistic atmospheric silences are never deleted.

2. **Automatic Silence & Filler Word Removal + Retake Arbiter**
   - Two-Pass Retake Arbitration detects abandoned false starts and preserves only the final, complete take.
   - Word-level 35ms raised-cosine audio micro-fades ensure click-free transitions.

3. **Text-Based Video Timeline Editing**
   - Faster-Whisper neural speech-to-text transcribes speech into an interactive word-by-word script.
   - Click words to jump; strikethrough words to delete them directly from the video timeline.
   - Phonetic travel glossary search & replace (e.g. *Ram Dallar* ➔ *Ram Dalal*).

4. **Face-Safe Captions & Subtitles**
   - Word-by-word dynamic kinetic bouncing animations (Hormozi, MrBeast, Cyberpunk Neon, YouTube Create).
   - Face-safe exclusion zone ensures captions never obscure the speaker's face.

5. **Smart Reframing (Auto-Crop 16:9 to 9:16)**
   - Converts widescreen 16:9 videos into 9:16 vertical format for TikTok, Instagram Reels, and YouTube Shorts.
   - Speaker face-tracking with Exponential Moving Average (EMA) camera smoothing.

6. **AI Audio Enhancement & Denoising**
   - Removes electrical hum, hiss, and handling rumble (<80Hz).
   - Normalizes audio to broadcast standard **-14 LUFS**.
   - Beat sync and 18dB sidechain music auto-ducking.

7. **Cinematic Colour Grading & AI Director Agent**
   - Presets: *Teal & Orange*, *Moody Bleach Bypass*, *Vintage Warm 70s*, *Cyberpunk Neon*, *Clean Documentary*, *Golden Hour Sunset*.
   - Natural language AI Director bar: type edit instructions and the AI orchestrates all timeline edits.

---

## 📁 Folder Structure

```
AUTO EDIT MOVIE/
├── raw_input/             # Raw media (all 45 authentic clips)
├── final_export/          # Completed master edits (MASTER_FULL_FEATURE_MOVIE.mp4)
├── backend/
│   ├── config.py          # System paths, color presets, and grid definitions
│   ├── main.py            # FastAPI REST & WebSocket server
│   └── pipeline/
│       ├── multi_clip_stitcher.py  # Multi-clip timeline sequencer & master stitcher
│       ├── smart_orientation.py   # Container autorotation & blurred ambient fill
│       ├── hyperframes_engine.py  # HTML/CSS/JS HyperFrames engine & presets
│       ├── gopro_teaser.py        # GoPro 30s kinetic summary builder
│       ├── drone_simulator.py     # 4K simulated aerial drone reel
│       ├── silence_remover.py     # Continuous speech protection & retake arbiter
│       ├── transcriber.py         # Faster-Whisper Hinglish STT & glossary
│       ├── hyperframe_captions.py # Kinetic bouncing ASS/SRT caption generator
│       ├── smart_reframer.py      # Face-safe 16:9 to 9:16 vertical reframer
│       ├── audio_enhancer.py      # Vocal EQ, denoiser & -14 LUFS normalizer
│       ├── beat_sync.py           # Soundtrack beat sync & auto-ducking
│       └── color_grading.py       # Cinematic Rec.709 LUT grading
├── frontend/
│   ├── templates/index.html       # Studio Dashboard with HyperFrames Studio Modal
│   └── static/
│       ├── style.css              # Glassmorphic dark styling & HyperFrames styles
│       └── app.js                 # Player controls, WebSockets, HyperFrames engine
├── desktop_launcher.py            # Desktop launcher script
├── run_master_movie_assembly.py   # Master assembly runner
├── run.bat                        # Double-click launcher for Windows
└── README.md
```

---

## 🚀 Quick Start

1. **Launch the Studio:**
   ```bash
   python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
   ```
   Open **`http://localhost:8000/`** in your browser.

2. **Assemble Master Movie:**
   ```bash
   python run_master_movie_assembly.py
   ```
   Exports directly to `final_export/MASTER_FULL_FEATURE_MOVIE.mp4`.
