/* ==========================================================================
   PREMIERE PRO & INSTAGRAM STUDIO - INTERACTIVE NLE CONTROLLER
   ANIRBAN AUTOMATIONS • STUDIO PRO v2.5
   ========================================================================== */

let activeEditorWorkspace = "editing";
let editorMediaPool = { exported_clips: [], raw_clips: [], instagram_filters: [] };
let activeSourceClip = null;
let activeTimelineClips = [];
let activeEditorAspectRatio = "9:16";
let activeInstagramFilter = "clarendon";
let activeEditorTool = "select"; // 'select', 'razor', 'ripple', 'text'
let timelinePlayheadSec = 0.0;
let timelineZoomPxPerSec = 20.0; // 20px per second of footage
let isTimelinePlaying = false;
let timelinePlaybackTimer = null;
let selectedTimelineClipIndex = null;

// Tab switcher between AI Pipeline and Premiere Pro
function switchStudioTab(tabId) {
    document.querySelectorAll(".studio-tab-btn").forEach(btn => btn.classList.remove("active"));
    document.querySelectorAll(".workspace-tab").forEach(tab => tab.classList.remove("active"));

    if (tabId === "premiere") {
        document.getElementById("tab-btn-premiere").classList.add("active");
        document.getElementById("workspace-premiere").classList.add("active");
        initPremiereStudio();
    } else {
        document.getElementById("tab-btn-ai").classList.add("active");
        document.getElementById("workspace-ai").classList.add("active");
    }

    if (window.feather) feather.replace();
}

async function initPremiereStudio() {
    await fetchEditorMediaPool();
    renderMediaBin("exported");
    renderInstagramFilters();
    renderTimelineRuler();
    renderTimelineTracks();

    // Default: populate timeline with output clips if empty
    if (activeTimelineClips.length === 0 && editorMediaPool.exported_clips.length > 0) {
        autoPopulateInitialTimeline();
    }
}

// ----------------- MEDIA BIN & CLIPS FETCH -----------------
async function fetchEditorMediaPool() {
    try {
        const res = await fetch("/api/editor/media-pool");
        const data = await res.json();
        editorMediaPool = data;
    } catch (e) {
        console.error("Error loading editor media pool:", e);
    }
}

function renderMediaBin(category = "exported") {
    const container = document.getElementById("p-media-bin-list");
    if (!container) return;

    const clips = category === "exported" ? editorMediaPool.exported_clips : editorMediaPool.raw_clips;
    
    if (!clips || clips.length === 0) {
        container.innerHTML = `<div style="padding:18px; text-align:center; color:#64748b; font-size:12px;">No ${category} clips found. Render a master first!</div>`;
        return;
    }

    container.innerHTML = clips.map((c, idx) => `
        <div class="media-bin-item ${activeSourceClip && activeSourceClip.path === c.path ? 'active' : ''}" onclick="selectSourceClip('${c.path.replace(/\\/g, '\\\\')}')">
            <div class="media-bin-thumb">
                <i data-feather="film"></i>
            </div>
            <div class="media-bin-info">
                <div class="media-bin-name" title="${c.name}">${c.name}</div>
                <div class="media-bin-meta">
                    <span>${c.duration}s</span>
                    <span>${c.fps} fps</span>
                    <span>${c.size_mb} MB</span>
                </div>
            </div>
            <button class="media-bin-btn-add" onclick="event.stopPropagation(); addClipToTimeline('${c.path.replace(/\\/g, '\\\\')}')" title="Add to Timeline Track V1">
                + Add
            </button>
        </div>
    `).join("");

    if (window.feather) feather.replace();
}

function selectSourceClip(clipPath) {
    const allClips = [...editorMediaPool.exported_clips, ...editorMediaPool.raw_clips];
    const match = allClips.find(c => c.path === clipPath);
    if (!match) return;

    activeSourceClip = match;
    renderMediaBin(match.type === "exported_master" ? "exported" : "raw");

    const player = document.getElementById("p-source-video");
    if (player) {
        player.src = match.url;
        player.load();
    }

    document.getElementById("p-source-title").innerText = match.name;
    document.getElementById("p-source-timecode").innerText = `00:00:00:00 / ${formatEditorTimecode(match.duration)}`;
}

// ----------------- INSTAGRAM FILTERS & PRESETS -----------------
function renderInstagramFilters() {
    const container = document.getElementById("p-instagram-filters-grid") || document.getElementById("p-bin-filters-view");
    if (!container) return;

    const filters = editorMediaPool.instagram_filters || [];
    container.innerHTML = filters.map(f => `
        <div class="ig-filter-card ${activeInstagramFilter === f.id ? 'active' : ''}" onclick="selectInstagramFilter('${f.id}')" title="${f.description}">
            <div class="ig-filter-preview" style="background: ${f.preview_color};">
                ${f.name}
            </div>
            <div class="ig-filter-name">${f.name}</div>
        </div>
    `).join("");
}

function selectInstagramFilter(filterId) {
    activeInstagramFilter = filterId;
    renderInstagramFilters();
    showToast(`Instagram Filter: ${filterId.toUpperCase()} applied to master output! ✨`, "info");
}

function setEditorAspect(aspect) {
    activeEditorAspectRatio = aspect;
    document.querySelectorAll(".p-aspect-btn").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.aspect === aspect);
    });

    const phoneFrame = document.getElementById("p-instagram-phone-frame");
    if (phoneFrame) {
        phoneFrame.classList.toggle("active", aspect === "9:16");
    }

    showToast(`Sequence Aspect Ratio: ${aspect} (${aspect === '9:16' ? 'Instagram Reels / TikTok' : 'Widescreen'})`, "info");
}

// ----------------- MULTI-TRACK TIMELINE CONTROLLER -----------------
function autoPopulateInitialTimeline() {
    activeTimelineClips = [];
    let startSec = 0.0;

    editorMediaPool.exported_clips.forEach((c, i) => {
        const dur = Math.min(c.duration, 15.0);
        activeTimelineClips.push({
            id: `clip_${Date.now()}_${i}`,
            path: c.path,
            name: c.name,
            track: "V1",
            timeline_start: startSec,
            in_point: 0.0,
            out_point: dur,
            duration: dur,
            speed: 1.0,
            rotation: 0,
            url: c.url
        });
        startSec += dur;
    });

    renderTimelineTracks();
    if (activeTimelineClips.length > 0) {
        seekTimelinePlayhead(0.0);
    }
}

function addClipToTimeline(clipPath, track = "V1") {
    const allClips = [...editorMediaPool.exported_clips, ...editorMediaPool.raw_clips];
    const match = allClips.find(c => c.path === clipPath);
    if (!match) return;

    // Calculate current end time of specified track
    const trackClips = activeTimelineClips.filter(c => c.track === track);
    let startSec = 0.0;
    if (trackClips.length > 0) {
        const last = trackClips[trackClips.length - 1];
        startSec = last.timeline_start + last.duration;
    }

    const dur = Math.min(match.duration, 20.0);
    activeTimelineClips.push({
        id: `clip_${Date.now()}`,
        path: match.path,
        name: match.name,
        track: track,
        timeline_start: startSec,
        in_point: 0.0,
        out_point: dur,
        duration: dur,
        speed: 1.0,
        rotation: 0,
        url: match.url
    });

    renderTimelineTracks();
    showToast(`Added '${match.name}' to Timeline Track ${track} 🎬`, "success");
}

function renderTimelineTracks() {
    const tracks = ["V3", "V2", "V1", "A1", "A2"];
    tracks.forEach(trk => {
        const container = document.getElementById(`track-content-${trk}`);
        if (!container) return;

        const clips = activeTimelineClips.filter(c => c.track === trk);
        container.innerHTML = clips.map((c, idx) => {
            const leftPx = c.timeline_start * timelineZoomPxPerSec;
            const widthPx = Math.max(30, c.duration * timelineZoomPxPerSec);
            const isSelected = selectedTimelineClipIndex === c.id;

            let trackClass = "";
            if (trk === "V2") trackClass = "track-v2";
            else if (trk === "V3") trackClass = "track-v3";
            else if (trk.startsWith("A")) trackClass = "track-audio";

            return `
                <div class="timeline-clip-block ${trackClass} ${isSelected ? 'selected' : ''}"
                     id="timeline-clip-${c.id}"
                     style="left: ${leftPx}px; width: ${widthPx}px;"
                     onclick="selectTimelineClip('${c.id}')"
                     title="${c.name} (${c.duration.toFixed(1)}s)">
                    <div class="clip-trim-handle-left" onmousedown="startClipTrim(event, '${c.id}', 'left')"></div>
                    <span style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${c.name}</span>
                    <span style="font-size:9.5px; opacity:0.8;">${c.duration.toFixed(1)}s</span>
                    <div class="clip-trim-handle-right" onmousedown="startClipTrim(event, '${c.id}', 'right')"></div>
                </div>
            `;
        }).join("");
    });
}

function renderTimelineRuler() {
    const ruler = document.getElementById("p-timeline-ruler");
    if (!ruler) return;

    let ticksHtml = "";
    for (let sec = 0; sec <= 300; sec += 5) {
        const left = 90 + (sec * timelineZoomPxPerSec);
        ticksHtml += `<div class="ruler-tick" style="left: ${left}px;">${formatSecondsShort(sec)}</div>`;
    }
    ruler.innerHTML = ticksHtml;

    // Attach click to seek
    ruler.onclick = (e) => {
        const rect = ruler.getBoundingClientRect();
        const clickX = e.clientX - rect.left - 90;
        if (clickX >= 0) {
            const seekSec = Math.max(0, clickX / timelineZoomPxPerSec);
            seekTimelinePlayhead(seekSec);
        }
    };
}

function seekTimelinePlayhead(sec) {
    timelinePlayheadSec = Math.max(0, sec);
    const leftPx = 90 + (timelinePlayheadSec * timelineZoomPxPerSec);
    const playhead = document.getElementById("p-timeline-playhead");
    if (playhead) {
        playhead.style.left = `${leftPx}px`;
    }

    document.getElementById("p-master-timecode").innerText = formatEditorTimecode(timelinePlayheadSec);

    // Sync Program Monitor video to the clip present at this time
    syncProgramMonitorToPlayhead();
}

function syncProgramMonitorToPlayhead() {
    // Find active clip at playhead time
    const activeClip = activeTimelineClips.find(c => 
        timelinePlayheadSec >= c.timeline_start && timelinePlayheadSec < (c.timeline_start + c.duration)
    );

    const programVideo = document.getElementById("p-program-video");
    if (!programVideo) return;

    if (activeClip) {
        const offsetInClip = timelinePlayheadSec - activeClip.timeline_start;
        const targetVideoTime = activeClip.in_point + offsetInClip;

        if (!programVideo.src.includes(encodeURI(activeClip.url))) {
            programVideo.src = activeClip.url;
            programVideo.load();
        }
        programVideo.currentTime = targetVideoTime;
        programVideo.style.transition = "transform 0.2s ease";
        programVideo.style.transform = (activeClip.rotation) ? `rotate(${activeClip.rotation}deg)` : "none";
    }
}

// ----------------- RAZOR CUT TOOL (C) & EDITING TOOLS -----------------
function setEditorTool(tool) {
    activeEditorTool = tool;
    document.querySelectorAll(".tool-btn").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.tool === tool);
    });
    showToast(`Active Tool: ${tool.toUpperCase()} (${tool === 'razor' ? 'Split clip at playhead' : 'Select & move'})`, "info");
}

function executeRazorCutAtPlayhead() {
    // Find which clip is directly under the playhead
    const targetIdx = activeTimelineClips.findIndex(c => 
        timelinePlayheadSec > c.timeline_start && timelinePlayheadSec < (c.timeline_start + c.duration)
    );

    if (targetIdx === -1) {
        showToast("No clip under playhead to cut. Move playhead over a clip first!", "warning");
        return;
    }

    const orig = activeTimelineClips[targetIdx];
    const cutOffset = timelinePlayheadSec - orig.timeline_start;

    // Split into Clip A and Clip B
    const clipA = {
        ...orig,
        id: `clip_${Date.now()}_A`,
        out_point: orig.in_point + cutOffset,
        duration: cutOffset
    };

    const clipB = {
        ...orig,
        id: `clip_${Date.now()}_B`,
        timeline_start: orig.timeline_start + cutOffset,
        in_point: orig.in_point + cutOffset,
        duration: orig.duration - cutOffset
    };

    activeTimelineClips.splice(targetIdx, 1, clipA, clipB);
    renderTimelineTracks();
    showToast(`✂️ Razor Cut executed at ${timelinePlayheadSec.toFixed(2)}s! Split into 2 clips.`, "success");
}

function deleteSelectedTimelineClip() {
    if (!selectedTimelineClipIndex) return;
    activeTimelineClips = activeTimelineClips.filter(c => c.id !== selectedTimelineClipIndex);
    selectedTimelineClipIndex = null;
    renderTimelineTracks();
    showToast("Clip removed from timeline", "info");
}

function selectTimelineClip(clipId) {
    if (activeEditorTool === "razor") {
        executeRazorCutAtPlayhead();
        return;
    }

    selectedTimelineClipIndex = clipId;
    renderTimelineTracks();
    const clip = activeTimelineClips.find(c => c.id === clipId);
    if (clip) {
        // Load into Effect Controls
        document.getElementById("fx-clip-name").innerText = clip.name;
        document.getElementById("fx-speed-slider").value = clip.speed || 1.0;
        document.getElementById("fx-speed-val").innerText = `${(clip.speed || 1.0).toFixed(1)}x`;
        const rot = clip.rotation || 0;
        const rotSlider = document.getElementById("fx-rot-slider");
        const rotVal = document.getElementById("fx-rot-val");
        if (rotSlider) rotSlider.value = rot;
        if (rotVal) rotVal.innerText = `${rot}°`;
        const programVideo = document.getElementById("p-program-video");
        if (programVideo) {
            programVideo.style.transition = "transform 0.2s ease";
            programVideo.style.transform = rot ? `rotate(${rot}deg)` : "none";
        }
    }
}

function updateSelectedClipRotation(val) {
    const clip = activeTimelineClips.find(c => c.id === selectedTimelineClipIndex);
    if (!clip) {
        showToast("Select a clip on the timeline first to rotate!", "warning");
        return;
    }
    clip.rotation = parseInt(val) % 360;
    const rotVal = document.getElementById("fx-rot-val");
    if (rotVal) rotVal.innerText = `${clip.rotation}°`;
    const programVideo = document.getElementById("p-program-video");
    if (programVideo) {
        programVideo.style.transition = "transform 0.15s ease";
        programVideo.style.transform = `rotate(${clip.rotation}deg)`;
    }
}

function setClipRotationPreset(deg) {
    const clip = activeTimelineClips.find(c => c.id === selectedTimelineClipIndex);
    if (!clip) {
        showToast("Select a clip on the timeline first to rotate!", "warning");
        return;
    }
    clip.rotation = parseInt(deg) % 360;
    const rotSlider = document.getElementById("fx-rot-slider");
    const rotVal = document.getElementById("fx-rot-val");
    if (rotSlider) rotSlider.value = clip.rotation;
    if (rotVal) rotVal.innerText = `${clip.rotation}°`;
    const programVideo = document.getElementById("p-program-video");
    if (programVideo) {
        programVideo.style.transition = "transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)";
        programVideo.style.transform = `rotate(${clip.rotation}deg)`;
    }
    showToast(`Orientation spun to ${clip.rotation}° ↷`, "info");
}

async function bakeSelectedTimelineClipMaster() {
    const clip = activeTimelineClips.find(c => c.id === selectedTimelineClipIndex);
    if (!clip) {
        showToast("Select a timeline clip first to bake rotated master!", "warning");
        return;
    }
    const rot = clip.rotation || 0;
    showToast(`Baking rotated master (${rot}°) for ${clip.name}...`, "info");
    try {
        const res = await fetch("/api/project/rotate-clip", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filename: clip.name, degrees: rot })
        });
        const data = await res.json();
        if (data.status === "success") {
            showToast(`✅ Created upright master: ${data.filename}!`, "success");
            clip.rotation = 0;
            clip.name = data.filename;
            clip.url = data.url;
            const rotSlider = document.getElementById("fx-rot-slider");
            const rotVal = document.getElementById("fx-rot-val");
            if (rotSlider) rotSlider.value = 0;
            if (rotVal) rotVal.innerText = "0°";
            const programVideo = document.getElementById("p-program-video");
            if (programVideo) {
                programVideo.style.transform = "none";
                programVideo.src = data.url;
                programVideo.load();
                programVideo.play();
            }
            await fetchEditorMediaPool();
            renderMediaBin("exported");
            renderTimelineTracks();
        } else {
            showToast("Rotation export failed: " + (data.detail || "Error"), "error");
        }
    } catch (e) {
        console.error(e);
        showToast("Failed to bake rotated master: " + e.message, "error");
    }
}

function updateSelectedClipSpeed(val) {
    const clip = activeTimelineClips.find(c => c.id === selectedTimelineClipIndex);
    if (!clip) return;
    clip.speed = parseFloat(val);
    document.getElementById("fx-speed-val").innerText = `${clip.speed.toFixed(1)}x`;
    showToast(`Velocity ramp set to ${clip.speed}x`, "info");
}

// ----------------- TRANSPORT & PLAYBACK CONTROLS -----------------
function toggleTimelinePlayback() {
    isTimelinePlaying = !isTimelinePlaying;
    const btn = document.getElementById("p-btn-play-pause");
    const programVideo = document.getElementById("p-program-video");

    if (isTimelinePlaying) {
        if (btn) btn.innerHTML = `<i data-feather="pause"></i>`;
        if (programVideo) programVideo.play();
        timelinePlaybackTimer = setInterval(() => {
            seekTimelinePlayhead(timelinePlayheadSec + 0.1);
        }, 100);
    } else {
        if (btn) btn.innerHTML = `<i data-feather="play"></i>`;
        if (programVideo) programVideo.pause();
        clearInterval(timelinePlaybackTimer);
    }

    if (window.feather) feather.replace();
}

function stepTimeline(seconds) {
    seekTimelinePlayhead(timelinePlayheadSec + seconds);
}

// ----------------- EXPORT TIMELINE / INSTAGRAM REEL -----------------
async function exportTimelineSequence() {
    if (activeTimelineClips.length === 0) {
        showToast("Timeline is empty! Add clips from the Media Bin first.", "warning");
        return;
    }

    showToast("🎬 Exporting Sequence with Premiere Pro & Instagram Engine...", "info");

    const payload = {
        clips: activeTimelineClips.map(c => ({
            path: c.path,
            in_point: c.in_point,
            out_point: c.out_point,
            speed: c.speed,
            rotation: c.rotation || 0,
            track: c.track
        })),
        aspect_ratio: activeEditorAspectRatio,
        instagram_filter: activeInstagramFilter,
        title_text: document.getElementById("p-instagram-title-input") ? document.getElementById("p-instagram-title-input").value : ""
    };

    try {
        const res = await fetch("/api/editor/export-sequence", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (data.status === "success") {
            showToast(`🚀 Export Finished: ${data.filename}! Playing in Program Monitor.`, "success");
            
            // Play in Program Monitor
            const programVideo = document.getElementById("p-program-video");
            if (programVideo) {
                programVideo.src = data.url;
                programVideo.play();
            }

            // Refresh media pools
            await fetchEditorMediaPool();
            renderMediaBin("exported");

            showCompletionModal({
                duration: "Sequence Master",
                size: data.filename,
                filename: data.filename,
                url: data.url
            });
        } else {
            showToast("Export failed: " + (data.detail || "Unknown error"), "error");
        }
    } catch (e) {
        console.error("Sequence export error:", e);
        showToast("Error exporting timeline sequence", "error");
    }
}

// ----------------- KEYBOARD SHORTCUTS -----------------
window.addEventListener("keydown", (e) => {
    // Only if Premiere tab is active
    const pTab = document.getElementById("workspace-premiere");
    if (!pTab || !pTab.classList.contains("active")) return;

    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;

    if (e.key === " " || e.code === "Space") {
        e.preventDefault();
        toggleTimelinePlayback();
    } else if (e.key.toLowerCase() === "c") {
        setEditorTool("razor");
    } else if (e.key.toLowerCase() === "v") {
        setEditorTool("select");
    } else if (e.key === "Delete" || e.key === "Backspace") {
        deleteSelectedTimelineClip();
    } else if (e.key === "ArrowLeft") {
        stepTimeline(-1.0);
    } else if (e.key === "ArrowRight") {
        stepTimeline(1.0);
    }
});

function setLeftUpperTab(tab) {
    document.querySelectorAll(".panel-tab-header .panel-tab").forEach(t => t.classList.remove("active"));
    const tabSource = document.getElementById("tab-source-monitor");
    const tabEffects = document.getElementById("tab-effect-controls");
    const tabStickers = document.getElementById("tab-ig-stickers");

    const vSource = document.getElementById("p-subview-source");
    const vEffects = document.getElementById("p-subview-effects");
    const vStickers = document.getElementById("p-subview-stickers");

    if (vSource) vSource.style.display = tab === "source" ? "flex" : "none";
    if (vEffects) vEffects.style.display = tab === "effects" ? "flex" : "none";
    if (vStickers) vStickers.style.display = tab === "stickers" ? "flex" : "none";

    if (tab === "source" && tabSource) tabSource.classList.add("active");
    if (tab === "effects" && tabEffects) tabEffects.classList.add("active");
    if (tab === "stickers" && tabStickers) tabStickers.classList.add("active");
}

function setBinTab(tab) {
    const tabExp = document.getElementById("tab-bin-exports");
    const tabRaw = document.getElementById("tab-bin-raws");
    const tabFlt = document.getElementById("tab-bin-filters");

    const viewMedia = document.getElementById("p-bin-media-view");
    const viewFilters = document.getElementById("p-bin-filters-view");

    if (tabExp) tabExp.classList.toggle("active", tab === "exported");
    if (tabRaw) tabRaw.classList.toggle("active", tab === "raw");
    if (tabFlt) tabFlt.classList.toggle("active", tab === "filters");

    if (tab === "filters") {
        if (viewMedia) viewMedia.style.display = "none";
        if (viewFilters) viewFilters.style.display = "grid";
        renderInstagramFilters();
    } else {
        if (viewMedia) viewMedia.style.display = "flex";
        if (viewFilters) viewFilters.style.display = "none";
        renderMediaBin(tab);
    }
}

function switchEditorSubTab(subTab) {
    activeEditorWorkspace = subTab;
    document.querySelectorAll(".p-nav-btn").forEach(btn => btn.classList.remove("active"));
    event.currentTarget.classList.add("active");

    if (subTab === "color") {
        setBinTab("filters");
    } else if (subTab === "effects") {
        setLeftUpperTab("effects");
    } else if (subTab === "editing") {
        setLeftUpperTab("source");
        setBinTab("exported");
    }
}
function formatEditorTimecode(sec) {
    if (isNaN(sec) || sec < 0) sec = 0;
    const h = Math.floor(sec / 3600);
    const m = Math.floor((sec % 3600) / 60);
    const s = Math.floor(sec % 60);
    const f = Math.floor((sec - Math.floor(sec)) * 30);
    return `${pad(h)}:${pad(m)}:${pad(s)}:${pad(f)}`;
}

function formatSecondsShort(sec) {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${pad(m)}:${pad(s)}`;
}
