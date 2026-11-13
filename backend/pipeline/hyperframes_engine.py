"""
HyperFrames Engine - Programmatic HTML / CSS / JavaScript Motion Graphics
Inspired by HeyGen HyperFrames:
Enables code-driven kinetic video overlays, telemetry HUDs, animated lower-thirds,
and dynamic motion graphic cards using standard HTML5, CSS3 Keyframes, and JavaScript.
"""
from typing import Dict, List

HYPERFRAME_PRESETS: List[Dict] = [
    {
        "id": "gopro_telemetry_hud",
        "name": "GoPro Kinetic Action Telemetry HUD",
        "category": "Action & Telemetry",
        "description": "High-octane telemetry HUD with animated speedometer, altitude, GPS coordinates & live recording dot.",
        "html": """<div class="hyperframe-container gopro-hud">
    <div class="hud-top">
        <div class="rec-badge">
            <span class="rec-dot"></span>
            <span class="rec-text">REC • 4K 60FPS</span>
        </div>
        <div class="gps-chip">
            <i class="icon-geo">📍</i>
            <span class="geo-text">32.1024° N, 76.2711° E • KANGRA</span>
        </div>
    </div>
    
    <div class="hud-center-route">
        <span class="route-tag">ROUTE</span>
        <span class="route-path">DELHI ISBT <span class="arrow">➔</span> KANGRA VALLEY</span>
    </div>

    <div class="hud-bottom">
        <div class="gauge-card speed-card">
            <div class="gauge-val" id="speed-display">68</div>
            <div class="gauge-unit">KM / H</div>
            <div class="gauge-bar"><div class="gauge-fill" style="width: 72%;"></div></div>
        </div>
        <div class="gauge-card alt-card">
            <div class="gauge-val" id="alt-display">2,240</div>
            <div class="gauge-unit">ALT (M)</div>
            <div class="gauge-bar"><div class="gauge-fill alt-fill" style="width: 65%;"></div></div>
        </div>
        <div class="gauge-card gforce-card">
            <div class="gauge-val">+1.3</div>
            <div class="gauge-unit">G-FORCE</div>
            <div class="gauge-bar"><div class="gauge-fill g-fill" style="width: 45%;"></div></div>
        </div>
    </div>
</div>""",
        "css": """.hyperframe-container.gopro-hud {
    position: absolute;
    inset: 0;
    pointer-events: none;
    font-family: 'JetBrains Mono', 'Segoe UI', monospace;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 32px 40px;
    box-sizing: border-box;
    color: #ffffff;
}

.hud-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.rec-badge {
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(0, 0, 0, 0.65);
    backdrop-filter: blur(8px);
    padding: 8px 16px;
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.15);
}

.rec-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #ff3344;
    box-shadow: 0 0 12px #ff3344;
    animation: recPulse 1s infinite alternate;
}

@keyframes recPulse {
    from { opacity: 0.4; transform: scale(0.9); }
    to { opacity: 1; transform: scale(1.15); }
}

.rec-text {
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 1px;
}

.gps-chip {
    background: rgba(0, 0, 0, 0.65);
    backdrop-filter: blur(8px);
    padding: 8px 16px;
    border-radius: 20px;
    font-size: 13px;
    border: 1px solid rgba(255, 255, 255, 0.15);
    color: #38bdf8;
    font-weight: 600;
}

.hud-center-route {
    align-self: flex-start;
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.85), rgba(30, 41, 59, 0.75));
    backdrop-filter: blur(12px);
    padding: 10px 20px;
    border-radius: 12px;
    border-left: 4px solid #38bdf8;
    box-shadow: 0 10px 25px rgba(0,0,0,0.4);
    animation: slideInRoute 0.8s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideInRoute {
    from { opacity: 0; transform: translateX(-40px); }
    to { opacity: 1; transform: translateX(0); }
}

.route-tag {
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1.5px;
    color: #38bdf8;
    display: block;
    margin-bottom: 2px;
}

.route-path {
    font-size: 16px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

.hud-bottom {
    display: flex;
    gap: 20px;
}

.gauge-card {
    background: rgba(15, 23, 42, 0.8);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 14px;
    padding: 14px 22px;
    min-width: 130px;
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.4);
    animation: popGauge 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

@keyframes popGauge {
    from { opacity: 0; transform: translateY(30px) scale(0.9); }
    to { opacity: 1; transform: translateY(0) scale(1); }
}

.gauge-val {
    font-size: 32px;
    font-weight: 800;
    line-height: 1;
    color: #38bdf8;
    font-feature-settings: 'tnum';
}

.gauge-unit {
    font-size: 11px;
    font-weight: 700;
    color: #94a3b8;
    margin-top: 4px;
    letter-spacing: 1px;
}

.gauge-bar {
    width: 100%;
    height: 4px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 2px;
    margin-top: 8px;
    overflow: hidden;
}

.gauge-fill {
    height: 100%;
    background: #38bdf8;
    border-radius: 2px;
    transition: width 0.3s ease;
}

.alt-fill { background: #34d399; }
.g-fill { background: #f59e0b; }""",
        "js": """// Live Dynamic Speed & Altitude Counter Animation
(function animateHUD() {
    const speedEl = document.getElementById('speed-display');
    const altEl = document.getElementById('alt-display');
    if (!speedEl || !altEl) return;

    let baseSpeed = 64;
    let baseAlt = 2240;

    setInterval(() => {
        const speedJitter = Math.floor(Math.random() * 9) - 4;
        const currentSpeed = Math.max(45, Math.min(88, baseSpeed + speedJitter));
        speedEl.textContent = currentSpeed;

        const altJitter = Math.floor(Math.random() * 5) - 2;
        baseAlt += altJitter;
        altEl.textContent = baseAlt.toLocaleString();
    }, 400);
})();"""
    },
    {
        "id": "youtube_glass_lowerthird",
        "name": "YouTube Creator Glassmorphism Lower-Third",
        "category": "Creator Branding",
        "description": "Sleek floating glass card with rotating animated gradient border, profile badge & verified tick.",
        "html": """<div class="hyperframe-container lowerthird-container">
    <div class="glass-card">
        <div class="creator-badge">
            <span class="avatar-circle">✈️</span>
            <div class="badge-info">
                <div class="creator-title">
                    <span class="name">ANIRBAN AUTOMATIONS</span>
                    <span class="verified-icon">✓</span>
                </div>
                <div class="creator-sub">HIMACHAL PRADESH ROAD TRIP VLOG</div>
            </div>
        </div>
        <div class="subscribe-chip">
            <span class="sub-dot"></span>
            <span>4K ULTRA HD</span>
        </div>
    </div>
</div>""",
        "css": """.hyperframe-container.lowerthird-container {
    position: absolute;
    inset: 0;
    pointer-events: none;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    display: flex;
    align-items: flex-end;
    padding: 48px;
    box-sizing: border-box;
}

.glass-card {
    display: flex;
    align-items: center;
    gap: 20px;
    padding: 16px 24px;
    background: rgba(15, 23, 42, 0.75);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-radius: 18px;
    border: 1px solid rgba(255, 255, 255, 0.15);
    box-shadow: 0 20px 40px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.2);
    animation: glassSlideUp 0.8s cubic-bezier(0.16, 1, 0.3, 1);
    position: relative;
    overflow: hidden;
}

.glass-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc, #38bdf8);
    background-size: 300% 100%;
    animation: gradientFlow 3s linear infinite;
}

@keyframes gradientFlow {
    0% { background-position: 0% 50%; }
    100% { background-position: 300% 50%; }
}

@keyframes glassSlideUp {
    from { opacity: 0; transform: translateY(40px) scale(0.95); }
    to { opacity: 1; transform: translateY(0) scale(1); }
}

.creator-badge {
    display: flex;
    align-items: center;
    gap: 14px;
}

.avatar-circle {
    width: 44px;
    height: 44px;
    background: linear-gradient(135deg, #38bdf8, #6366f1);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    box-shadow: 0 4px 14px rgba(56, 189, 248, 0.4);
}

.creator-title {
    display: flex;
    align-items: center;
    gap: 6px;
}

.creator-title .name {
    color: #ffffff;
    font-size: 17px;
    font-weight: 800;
    letter-spacing: 0.5px;
}

.verified-icon {
    background: #38bdf8;
    color: #0f172a;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 900;
}

.creator-sub {
    color: #94a3b8;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.8px;
    margin-top: 2px;
}

.subscribe-chip {
    background: rgba(56, 189, 248, 0.15);
    border: 1px solid rgba(56, 189, 248, 0.4);
    color: #38bdf8;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    display: flex;
    align-items: center;
    gap: 6px;
}

.sub-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #38bdf8;
}""",
        "js": """;(function() {
    console.log("HyperFrame YouTube Glass Lower-Third initialized");
})();"""
    },
    {
        "id": "cinematic_expedition_title",
        "name": "Cinematic Minimalist Expedition Title",
        "category": "Cinematic Titles",
        "description": "High-end cinematic title card with expanding letter-spacing, delicate hair-line dividers and film chapter numbering.",
        "html": """<div class="hyperframe-container cinematic-title-container">
    <div class="title-card">
        <div class="chapter-tag">CHAPTER 01 • THE DEPARTURE</div>
        <h1 class="main-heading">EXPEDITION : HIMACHAL</h1>
        <div class="line-divider"></div>
        <div class="meta-row">
            <span>DELHI ISBT KASHMERE GATE</span>
            <span class="sep">•</span>
            <span>AUTONOMOUS MONTAGE</span>
        </div>
    </div>
</div>""",
        "css": """.hyperframe-container.cinematic-title-container {
    position: absolute;
    inset: 0;
    pointer-events: none;
    font-family: 'Plus Jakarta Sans', serif, sans-serif;
    display: flex;
    align-items: center;
    justify-content: center;
    box-sizing: border-box;
    background: radial-gradient(circle at center, rgba(0,0,0,0.3) 0%, rgba(0,0,0,0.6) 100%);
}

.title-card {
    text-align: center;
    color: #ffffff;
    max-width: 800px;
    animation: titleCinematicFade 2.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

@keyframes titleCinematicFade {
    0% { opacity: 0; transform: scale(0.96); letter-spacing: 6px; filter: blur(6px); }
    40% { opacity: 1; filter: blur(0px); }
    100% { opacity: 1; transform: scale(1.02); letter-spacing: 10px; }
}

.chapter-tag {
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 4px;
    color: #f59e0b;
    margin-bottom: 12px;
    text-transform: uppercase;
}

.main-heading {
    font-size: 46px;
    font-weight: 800;
    margin: 0;
    line-height: 1.1;
    text-shadow: 0 10px 30px rgba(0,0,0,0.8);
    background: linear-gradient(180deg, #ffffff 0%, #cbd5e1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.line-divider {
    width: 80px;
    height: 2px;
    background: #f59e0b;
    margin: 18px auto;
    animation: expandLine 1.8s ease-out forwards;
}

@keyframes expandLine {
    from { width: 0px; }
    to { width: 140px; }
}

.meta-row {
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 3px;
    color: #94a3b8;
    text-transform: uppercase;
}

.sep {
    margin: 0 10px;
    color: #f59e0b;
}""",
        "js": """;(function() {
    console.log("Cinematic title HyperFrame initialized");
})();"""
    }
]

def list_hyperframe_presets() -> List[Dict]:
    """Returns all available HyperFrame motion graphic presets."""
    return HYPERFRAME_PRESETS
