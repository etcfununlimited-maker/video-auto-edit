/**
 * AI DIRECTOR FX STUDIO & TOP 50 TRANSITIONS JAVASCRIPT ENGINE
 * ANIRBAN AUTOMATIONS • STUDIO PRO v2.5
 */

let directorCatalog = [];
let directorActiveEffects = {};
let directorTextBehind = {
    enabled: true,
    text: "RANN OF KUTCH | BHUJ | SOMNATH VLOG",
    font: "Montserrat",
    size: 110,
    spread: 8,
    color: "#FFFFFF",
    neon_enabled: true,
    neon_color: "#00F2FE",
    glow_radius: 24,
    glow_intensity: 1.2,
    position: "center",
    y_offset: 0,
    opacity: 0.95
};
let directorActiveCategory = "all";
let directorSearchQuery = "";

// ----------------- INITIALIZATION -----------------
async function initDirectorStudio() {
    try {
        const res = await fetch("/api/ai-director/fx-suite");
        const data = await res.json();
        if (data.catalog) {
            directorCatalog = data.catalog;
            directorActiveEffects = data.active_effects || {};
            directorTextBehind = data.text_behind_person || directorTextBehind;

            // Restore any localStorage user selections if available
            try {
                const localTb = localStorage.getItem("anirban_text_behind");
                if (localTb) {
                    const parsedTb = JSON.parse(localTb);
                    if (parsedTb && parsedTb.text && !parsedTb.text.toUpperCase().includes("EHSAAS")) {
                        directorTextBehind = Object.assign({}, directorTextBehind, parsedTb);
                    }
                }
                const localFx = localStorage.getItem("anirban_active_effects");
                if (localFx) {
                    const parsedFx = JSON.parse(localFx);
                    if (parsedFx && typeof parsedFx === "object") {
                        directorActiveEffects = Object.assign({}, directorActiveEffects, parsedFx);
                    }
                }
                // Ensure License Plate Privacy Blur is permanently armed by default
                if (directorActiveEffects["license_plate_blur"] === undefined) {
                    directorActiveEffects["license_plate_blur"] = true;
                }
            } catch (errLocal) {
                console.warn("Could not read from localStorage:", errLocal);
            }

            renderDepthTextControls();
            updateLiveDepthTextPreview();
            render50EffectsGrid();
            updateDirectorStatBadge();
            renderMiniDirectorBin();
        }
    } catch (e) {
        console.error("Failed to initialize AI Director Studio:", e);
    }
}

// ----------------- DEPTH TEXT BEHIND PERSON CONTROLS -----------------
function renderDepthTextControls() {
    const textInput = document.getElementById("depth-input-text");
    const fontSelect = document.getElementById("depth-select-font");
    const sizeRange = document.getElementById("depth-range-size");
    const sizeVal = document.getElementById("depth-val-size");
    const spreadRange = document.getElementById("depth-range-spread");
    const spreadVal = document.getElementById("depth-val-spread");
    const colorPicker = document.getElementById("depth-picker-color");
    const neonToggle = document.getElementById("depth-toggle-neon");
    const neonPicker = document.getElementById("depth-picker-neon");
    const glowRange = document.getElementById("depth-range-glow");
    const glowVal = document.getElementById("depth-val-glow");
    const opacityRange = document.getElementById("depth-range-opacity");
    const opacityVal = document.getElementById("depth-val-opacity");
    const mainToggle = document.getElementById("depth-main-toggle");

    if (textInput) textInput.value = directorTextBehind.text || "RANN OF KUTCH | BHUJ | SOMNATH VLOG";
    if (fontSelect) fontSelect.value = directorTextBehind.font || "Montserrat";
    if (sizeRange) sizeRange.value = directorTextBehind.size || 110;
    if (sizeVal) sizeVal.innerText = `${directorTextBehind.size || 110}px`;
    if (spreadRange) spreadRange.value = directorTextBehind.spread || 8;
    if (spreadVal) spreadVal.innerText = `${directorTextBehind.spread || 8}px`;
    if (colorPicker) colorPicker.value = directorTextBehind.color || "#FFFFFF";
    if (neonToggle) neonToggle.checked = !!directorTextBehind.neon_enabled;
    if (neonPicker) neonPicker.value = directorTextBehind.neon_color || "#00F2FE";
    if (glowRange) glowRange.value = directorTextBehind.glow_radius || 24;
    if (glowVal) glowVal.innerText = `${directorTextBehind.glow_radius || 24}px`;
    if (opacityRange) opacityRange.value = Math.round((directorTextBehind.opacity || 0.95) * 100);
    if (opacityVal) opacityVal.innerText = `${Math.round((directorTextBehind.opacity || 0.95) * 100)}%`;
    if (mainToggle) mainToggle.checked = !!directorTextBehind.enabled;

    // Position pills
    document.querySelectorAll(".pos-btn").forEach(btn => {
        btn.classList.toggle("active", btn.getAttribute("data-pos") === (directorTextBehind.position || "center"));
    });

    // Swatch selection highlights
    document.querySelectorAll(".swatch-text").forEach(sw => {
        sw.classList.toggle("active", sw.getAttribute("data-color").toLowerCase() === (directorTextBehind.color || "").toLowerCase());
    });
    document.querySelectorAll(".swatch-neon").forEach(sw => {
        sw.classList.toggle("active", sw.getAttribute("data-color").toLowerCase() === (directorTextBehind.neon_color || "").toLowerCase());
    });
}

function updateLiveDepthTextPreview() {
    const previewText = document.getElementById("depth-live-text");
    if (!previewText) return;

    if (!directorTextBehind.enabled) {
        previewText.style.display = "none";
        return;
    }
    previewText.style.display = "block";

    const rawContent = (directorTextBehind.text || "VLOG").trim();
    if (rawContent.includes("|")) {
        previewText.innerHTML = rawContent.split("|").map(s => s.trim().toUpperCase()).join("<br>");
        previewText.style.lineHeight = "1.15";
    } else {
        previewText.innerText = rawContent.toUpperCase();
        previewText.style.lineHeight = "normal";
    }
    previewText.style.fontFamily = `'${directorTextBehind.font}', sans-serif`;
    previewText.style.fontSize = `${directorTextBehind.size}px`;
    previewText.style.letterSpacing = `${directorTextBehind.spread}px`;
    previewText.style.color = directorTextBehind.color;
    previewText.style.opacity = directorTextBehind.opacity;

    // Calculate neon drop shadow & outer glow
    if (directorTextBehind.neon_enabled) {
        const nc = directorTextBehind.neon_color || "#00F2FE";
        const rad = directorTextBehind.glow_radius || 24;
        const halfRad = Math.round(rad * 0.5);
        const doubleRad = Math.round(rad * 1.5);
        previewText.style.textShadow = `
            0 0 ${halfRad}px ${nc},
            0 0 ${rad}px ${nc},
            0 0 ${doubleRad}px ${nc},
            0 0 ${rad * 2}px rgba(0, 242, 254, 0.4)
        `;
        previewText.style.webkitTextStroke = `1px rgba(255, 255, 255, 0.4)`;
    } else {
        previewText.style.textShadow = "0 4px 15px rgba(0, 0, 0, 0.8)";
        previewText.style.webkitTextStroke = "none";
    }

    // Vertical positioning inside the 280px canvas
    const pos = directorTextBehind.position || "center";
    if (pos === "head") {
        previewText.style.top = "18%";
        previewText.style.transform = `translate(-50%, ${directorTextBehind.y_offset || 0}px)`;
    } else if (pos === "lower") {
        previewText.style.top = "70%";
        previewText.style.transform = `translate(-50%, ${directorTextBehind.y_offset || 0}px)`;
    } else if (pos === "wallpaper") {
        previewText.style.top = "42%";
        previewText.style.transform = `translate(-50%, ${directorTextBehind.y_offset || 0}px) scale(1.35)`;
        previewText.style.opacity = Math.min(0.7, (directorTextBehind.opacity || 0.95) * 0.6);
    } else {
        // center
        previewText.style.top = "38%";
        previewText.style.transform = `translate(-50%, ${directorTextBehind.y_offset || 0}px)`;
    }
    previewText.style.left = "50%";

    // Update live video player layer if present
    updateStudioPlayerDepthOverlay();
}

function updateStudioPlayerDepthOverlay() {
    const playerOverlay = document.getElementById("player-depth-text-overlay");
    if (!playerOverlay) return;

    if (!directorTextBehind.enabled) {
        playerOverlay.style.display = "none";
        return;
    }
    playerOverlay.style.display = "flex";
    playerOverlay.innerText = (directorTextBehind.text || "VLOG").toUpperCase();
    playerOverlay.style.fontFamily = `'${directorTextBehind.font}', sans-serif`;
    playerOverlay.style.fontSize = `${Math.round(directorTextBehind.size * 0.75)}px`;
    playerOverlay.style.letterSpacing = `${directorTextBehind.spread}px`;
    playerOverlay.style.color = directorTextBehind.color;
    playerOverlay.style.opacity = directorTextBehind.opacity;

    if (directorTextBehind.neon_enabled) {
        const nc = directorTextBehind.neon_color || "#00F2FE";
        const rad = directorTextBehind.glow_radius || 24;
        playerOverlay.style.textShadow = `0 0 ${rad}px ${nc}, 0 0 ${rad * 2}px ${nc}`;
    } else {
        playerOverlay.style.textShadow = "0 4px 15px rgba(0, 0, 0, 0.9)";
    }
}

// ----------------- DEPTH TEXT EVENT HANDLERS -----------------
async function onDepthTextParamChange(param, value) {
    directorTextBehind[param] = value;

    // If user entered or changed text, automatically ensure effect is enabled so it burns into video
    if (param === "text" && value && value.trim().length > 0) {
        directorTextBehind.enabled = true;
        const mainToggle = document.getElementById("depth-main-toggle");
        if (mainToggle) mainToggle.checked = true;
    }

    try {
        localStorage.setItem("anirban_text_behind", JSON.stringify(directorTextBehind));
    } catch (e) {}

    updateLiveDepthTextPreview();

    // Auto-sync with backend
    try {
        const payload = {};
        payload[param] = value;
        if (directorTextBehind.enabled) {
            payload["enabled"] = true;
        }
        const res = await fetch("/api/ai-director/text-behind-person", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.grid_statuses) {
            syncAiGridCardsFromDirector(data.grid_statuses);
        }
    } catch (e) {
        console.error("Error updating text-behind-person:", e);
    }
}

async function saveDepthTextExplicitly() {
    const textInput = document.getElementById("depth-input-text");
    const saveBtn = document.getElementById("btn-save-depth-title");
    const newText = (textInput && textInput.value.trim()) ? textInput.value.trim() : "RANN OF KUTCH | BHUJ | SOMNATH VLOG";
    
    directorTextBehind.text = newText;
    directorTextBehind.enabled = true;
    
    // Save to localStorage
    try {
        localStorage.setItem("anirban_text_behind", JSON.stringify(directorTextBehind));
    } catch (e) {}

    // Update Live Previews
    updateLiveDepthTextPreview();

    // Synchronize Premiere Pro timeline title clip if present on V3
    if (typeof activeTimelineClips !== "undefined" && Array.isArray(activeTimelineClips)) {
        activeTimelineClips.forEach(c => {
            if (c.track === "V3" || c.type === "title") {
                c.text = newText;
                c.name = `Title: ${newText}`;
            }
        });
        if (typeof renderTimelineTracks === "function") {
            renderTimelineTracks();
        }
    }

    // Persist to backend
    try {
        if (saveBtn) {
            saveBtn.innerHTML = `<i data-feather="check"></i> Saving...`;
            saveBtn.style.background = "#059669";
        }
        const res = await fetch("/api/ai-director/text-behind-person", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(directorTextBehind)
        });
        const data = await res.json();
        if (saveBtn) {
            saveBtn.innerHTML = `<i data-feather="check"></i> Saved!`;
            saveBtn.style.background = "#10b981";
            setTimeout(() => {
                saveBtn.innerHTML = `<i data-feather="save"></i> Save Title`;
                if (window.feather) feather.replace();
            }, 2000);
        }
        showToast(`✓ Title changes registered & saved: "${newText}"`, "success");
    } catch (err) {
        console.error("Error saving title:", err);
        showToast("Error saving title to backend", "error");
    }
    if (window.feather) feather.replace();
}

function setDepthColor(hex) {
    directorTextBehind.color = hex;
    const picker = document.getElementById("depth-picker-color");
    if (picker) picker.value = hex;
    document.querySelectorAll(".swatch-text").forEach(sw => {
        sw.classList.toggle("active", sw.getAttribute("data-color").toLowerCase() === hex.toLowerCase());
    });
    onDepthTextParamChange("color", hex);
}

function setDepthNeonColor(hex) {
    directorTextBehind.neon_color = hex;
    const picker = document.getElementById("depth-picker-neon");
    if (picker) picker.value = hex;
    document.querySelectorAll(".swatch-neon").forEach(sw => {
        sw.classList.toggle("active", sw.getAttribute("data-color").toLowerCase() === hex.toLowerCase());
    });
    onDepthTextParamChange("neon_color", hex);
}

function setDepthPosition(pos) {
    directorTextBehind.position = pos;
    document.querySelectorAll(".pos-btn").forEach(btn => {
        btn.classList.toggle("active", btn.getAttribute("data-pos") === pos);
    });
    onDepthTextParamChange("position", pos);
}

function setDepthPresetText(txt) {
    const input = document.getElementById("depth-input-text");
    if (input) input.value = txt;
    directorTextBehind.enabled = true;
    const mainToggle = document.getElementById("depth-main-toggle");
    if (mainToggle) mainToggle.checked = true;
    onDepthTextParamChange("enabled", true);
    onDepthTextParamChange("text", txt);
}

// ----------------- TOP 50 EFFECTS GRID RENDERING -----------------
function render50EffectsGrid() {
    const gridContainer = document.getElementById("fx-cards-grid");
    if (!gridContainer) return;

    gridContainer.innerHTML = "";

    const filtered = directorCatalog.filter(fx => {
        const matchesCategory = (directorActiveCategory === "all" || fx.category === directorActiveCategory);
        const matchesSearch = !directorSearchQuery || 
            fx.name.toLowerCase().includes(directorSearchQuery.toLowerCase()) ||
            fx.desc.toLowerCase().includes(directorSearchQuery.toLowerCase()) ||
            fx.num.includes(directorSearchQuery);
        return matchesCategory && matchesSearch;
    });

    if (filtered.length === 0) {
        gridContainer.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #64748b;">
                <i data-feather="search" style="width: 32px; height: 32px; margin-bottom: 8px;"></i>
                <p>No effects found matching "${directorSearchQuery}". Try another keyword or clear search.</p>
            </div>
        `;
        if (window.feather) feather.replace();
        return;
    }

    filtered.forEach(fx => {
        const isActive = !!directorActiveEffects[fx.id];
        const card = document.createElement("div");
        card.className = `fx-card ${isActive ? 'active' : ''}`;
        card.id = `fx-card-${fx.id}`;

        card.innerHTML = `
            <div class="fx-card-top">
                <div class="fx-card-num-title">
                    <div class="fx-card-num-row">
                        <span class="fx-num-tag">#${fx.num}</span>
                        <span class="fx-badge">${fx.badge}</span>
                    </div>
                    <h3 class="fx-card-title">${fx.name}</h3>
                </div>
                <label class="switch">
                    <input type="checkbox" id="switch-fx-${fx.id}" ${isActive ? 'checked' : ''} onchange="toggleDirectorEffect('${fx.id}', this.checked)">
                    <span class="slider-switch"></span>
                </label>
            </div>
            <p class="fx-card-desc">${fx.desc}</p>
            <div class="fx-card-footer">
                <span class="fx-grid-target-pill">
                    <i data-feather="check-circle"></i> ${fx.grid_label}
                </span>
                <span style="font-size: 10px; font-weight: 700; color: ${isActive ? '#38bdf8' : '#64748b'};">
                    ${isActive ? 'ENABLED' : 'BYPASS'}
                </span>
            </div>
        `;
        gridContainer.appendChild(card);
    });

    if (window.feather) feather.replace();
}

async function toggleDirectorEffect(effectId, isEnabled) {
    directorActiveEffects[effectId] = isEnabled;
    try {
        localStorage.setItem("anirban_active_effects", JSON.stringify(directorActiveEffects));
    } catch (e) {}

    const card = document.getElementById(`fx-card-${effectId}`);
    if (card) {
        card.classList.toggle("active", isEnabled);
        const footerStatus = card.querySelector(".fx-card-footer span:last-child");
        if (footerStatus) {
            footerStatus.innerText = isEnabled ? "ENABLED" : "BYPASS";
            footerStatus.style.color = isEnabled ? "#38bdf8" : "#64748b";
        }
    }

    updateDirectorStatBadge();
    renderMiniDirectorBin();

    try {
        const res = await fetch("/api/ai-director/fx-suite/toggle", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ effect_id: effectId, enabled: isEnabled })
        });
        const data = await res.json();
        const fxObj = directorCatalog.find(f => f.id === effectId);
        const name = fxObj ? fxObj.name : effectId;
        showToast(`${isEnabled ? '⚡ Armed' : '⚪ Bypassed'}: ${name}`, isEnabled ? "success" : "info");
    } catch (e) {
        console.error("Error toggling effect:", e);
    }
}

function filterEffectsByCategory(cat) {
    directorActiveCategory = cat;
    document.querySelectorAll(".fx-cat-pill").forEach(pill => {
        pill.classList.toggle("active", pill.getAttribute("data-cat") === cat);
    });
    render50EffectsGrid();
}

function filterEffectsBySearch(query) {
    directorSearchQuery = query.trim();
    render50EffectsGrid();
}

async function applyDirectorPreset(presetName) {
    try {
        const res = await fetch("/api/ai-director/apply-preset", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ preset: presetName })
        });
        const data = await res.json();

        if (data.active_effects) {
            directorActiveEffects = data.active_effects;
            if (presetName === "anirban") {
                directorActiveEffects["license_plate_blur"] = true;
            }
            try { localStorage.setItem("anirban_active_effects", JSON.stringify(directorActiveEffects)); } catch (e) {}
        }
        if (data.text_behind_person) {
            directorTextBehind = data.text_behind_person;
            try { localStorage.setItem("anirban_text_behind", JSON.stringify(directorTextBehind)); } catch (e) {}
        }

        // Refresh UI state
        renderDepthTextControls();
        updateLiveDepthTextPreview();
        render50EffectsGrid();
        updateDirectorStatBadge();
        renderMiniDirectorBin();

        const label = presetName === "anirban" ? "⭐ Anirban Preset (Custom Saved 50 Effects + RANN OF KUTCH Depth Title)" :
                      presetName === "vlog" ? "Viral Vlog Creator (TikTok / Shorts)" :
                      presetName === "cinematic" ? "Cinematic Movie (Anamorphic / Halation)" : "All Effects Bypassed";
        showToast(`✨ Preset Applied: ${label} (${data.active_count} active)`, "success");
    } catch (e) {
        console.error("Error applying preset:", e);
    }
}

async function saveCurrentAsAnirbanPreset() {
    try {
        const res = await fetch("/api/ai-director/save-anirban-preset", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });
        const data = await res.json();
        try {
            localStorage.setItem("anirban_active_effects", JSON.stringify(directorActiveEffects));
            localStorage.setItem("anirban_text_behind", JSON.stringify(directorTextBehind));
        } catch (e) {}
        showToast("⭐ Anirban Preset Saved Permanently! Survives all browser refreshes & server restarts.", "success");
    } catch (e) {
        console.error("Error saving Anirban Preset:", e);
        showToast("Failed to save Anirban Preset", "error");
    }
}

function updateDirectorStatBadge() {
    const totalActive = Object.values(directorActiveEffects).filter(Boolean).length;
    const badge = document.getElementById("director-active-stat-count");
    if (badge) {
        badge.innerText = `${totalActive} / 50 Active`;
    }
}

// ----------------- SYNC WITH TAB 1 (12 MODULAR GRIDS) -----------------
function syncAiGridCardsFromDirector(gridStatuses) {
    if (!gridStatuses) return;
    Object.keys(gridStatuses).forEach(gid => {
        const gInfo = gridStatuses[gid];
        const card = document.getElementById(`grid-card-${gid}`);
        if (!card) return;

        const badge = card.querySelector(".grid-status-badge");
        const detail = card.querySelector(".grid-desc");
        const eta = card.querySelector(".grid-eta-val");

        if (badge) {
            badge.innerText = (gInfo.status || "WAITING").toUpperCase();
            badge.className = `grid-status-badge status-${gInfo.status || 'waiting'}`;
        }
        if (detail && gInfo.detail) {
            detail.innerText = gInfo.detail;
        }
        if (eta && gInfo.status === "completed") {
            eta.innerText = "Done";
        } else if (eta && gInfo.status === "ready") {
            eta.innerText = "Ready";
        }
    });
}

// ----------------- MINI DIRECTOR BIN (PREMIERE STUDIO INTEGRATION) -----------------
function renderMiniDirectorBin() {
    const container = document.getElementById("p-bin-director-view");
    if (!container) return;

    const totalActive = Object.values(directorActiveEffects).filter(Boolean).length;
    const isTextOn = directorTextBehind.enabled;

    container.innerHTML = `
        <div class="mini-director-card" style="border-color: #0ea5e9; background: rgba(14, 165, 233, 0.08);">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:12px; font-weight:800; color:#38bdf8;"><i data-feather="sliders" style="width:13px; height:13px;"></i> AI Director Suite</span>
                <span style="font-size:11px; font-weight:700; color:#38bdf8; background:rgba(14,165,233,0.2); padding:2px 7px; border-radius:10px;">${totalActive} Active</span>
            </div>
            <p style="font-size:11px; color:#94a3b8; margin:0;">Direct control of 50+ vlog effects & depth typography.</p>
            <button class="btn btn-primary" style="padding:5px 10px; font-size:11.5px; width:100%; margin-top:4px;" onclick="switchStudioTab('director')">
                <i data-feather="external-link" style="width:12px; height:12px;"></i> Open Full 50-FX Studio
            </button>
        </div>

        <div class="mini-director-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:11.5px; font-weight:700; color:#f1f5f9;">Text Behind Person</span>
                <label class="switch" style="transform:scale(0.8);">
                    <input type="checkbox" ${isTextOn ? 'checked' : ''} onchange="onDepthTextParamChange('enabled', this.checked)">
                    <span class="slider-switch"></span>
                </label>
            </div>
            <div style="display:flex; gap:6px;">
                <input type="text" class="control-input-text" style="font-size:12px; padding:6px 10px; flex:1;" value="${directorTextBehind.text || ''}" oninput="onDepthTextParamChange('text', this.value)">
                <input type="color" style="width:34px; height:32px; border:none; background:none; cursor:pointer;" value="${directorTextBehind.neon_color || '#00F2FE'}" onchange="setDepthNeonColor(this.value)">
            </div>
        </div>

        <div class="mini-director-card">
            <span style="font-size:11px; font-weight:700; color:#94a3b8; text-transform:uppercase;">Quick Presets</span>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; margin-top:4px;">
                <button class="btn btn-secondary" style="font-size:11px; padding:5px 6px; border-color:#38bdf8; color:#38bdf8; font-weight:700;" onclick="applyDirectorPreset('anirban')">⭐ Anirban</button>
                <button class="btn btn-secondary" style="font-size:11px; padding:5px 6px;" onclick="applyDirectorPreset('vlog')">⚡ Viral Vlog</button>
            </div>
            <button class="btn btn-secondary" style="width:100%; font-size:11px; padding:4px 6px; margin-top:4px; border-color:#10b981; color:#34d399;" onclick="saveCurrentAsAnirbanPreset()"><i data-feather="save" style="width:11px; height:11px;"></i> Save as Anirban Preset</button>
        </div>
    `;

    if (window.feather) feather.replace();
}

// Auto-run when DOM ready
document.addEventListener("DOMContentLoaded", () => {
    initDirectorStudio();
});

// Explicit Global Window Bindings
window.saveDepthTextExplicitly = saveDepthTextExplicitly;
window.onDepthTextParamChange = onDepthTextParamChange;
window.setDepthPresetText = setDepthPresetText;
window.setDepthNeonColor = setDepthNeonColor;
window.saveCurrentAsAnirbanPreset = saveCurrentAsAnirbanPreset;
window.applyDirectorPreset = applyDirectorPreset;
