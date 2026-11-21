/* ==========================================================================
   PREMIERE PRO & INSTAGRAM STUDIO - INTERACTIVE NLE CONTROLLER
   ANIRBAN AUTOMATIONS • STUDIO PRO v2.5
   ========================================================================== */

let activeEditorWorkspace = "editing";
let editorMediaPool = { exported_clips: [], raw_clips: [], music_tracks: [], instagram_filters: [] };
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
let selectedTimelineClipIds = new Set();
let selectedTimelineGap = null;

// Multi-step Undo / Redo History Stack (up to 50 states)
let timelineHistoryStack = [];
let timelineRedoStack = [];

function captureTimelineState(actionName = "Edit") {
    return {
        action: actionName,
        clips: JSON.parse(JSON.stringify(activeTimelineClips)),
        selectedClipId: selectedTimelineClipIndex,
        selectedClipIds: Array.from(selectedTimelineClipIds),
        selectedGap: selectedTimelineGap ? { ...selectedTimelineGap } : null,
        playheadSec: timelinePlayheadSec,
        titleSettings: window.persistedTitleSettings ? { ...window.persistedTitleSettings } : null
    };
}

function pushTimelineHistory(actionName = "Edit") {
    if (timelineHistoryStack.length >= 50) {
        timelineHistoryStack.shift();
    }
    timelineHistoryStack.push(captureTimelineState(actionName));
    timelineRedoStack = []; // new action invalidates redo
    updateUndoRedoButtons();
}

function undoTimelineAction() {
    if (!timelineHistoryStack || timelineHistoryStack.length === 0) {
        showToast("Nothing to undo (Timeline is at initial state)", "info");
        return;
    }
    timelineRedoStack.push(captureTimelineState("Redo"));
    const prevState = timelineHistoryStack.pop();
    activeTimelineClips = prevState.clips;
    selectedTimelineClipIndex = prevState.selectedClipId;
    selectedTimelineClipIds = new Set(prevState.selectedClipIds || (prevState.selectedClipId ? [prevState.selectedClipId] : []));
    selectedTimelineGap = prevState.selectedGap;
    timelinePlayheadSec = prevState.playheadSec;
    if (prevState.titleSettings) {
        window.persistedTitleSettings = prevState.titleSettings;
    }
    renderTimelineTracks();
    seekTimelinePlayhead(timelinePlayheadSec);
    if (selectedTimelineClipIndex) {
        selectTimelineClip(selectedTimelineClipIndex);
    }
    syncProgramOverlays(timelinePlayheadSec);
    updateUndoRedoButtons();
    showToast(`Undo: ${prevState.action} ⎌`, "info");
}

function redoTimelineAction() {
    if (!timelineRedoStack || timelineRedoStack.length === 0) {
        showToast("Nothing to redo", "info");
        return;
    }
    timelineHistoryStack.push(captureTimelineState("Undo"));
    const nextState = timelineRedoStack.pop();
    activeTimelineClips = nextState.clips;
    selectedTimelineClipIndex = nextState.selectedClipId;
    selectedTimelineClipIds = new Set(nextState.selectedClipIds || (nextState.selectedClipId ? [nextState.selectedClipId] : []));
    selectedTimelineGap = nextState.selectedGap;
    timelinePlayheadSec = nextState.playheadSec;
    if (nextState.titleSettings) {
        window.persistedTitleSettings = nextState.titleSettings;
    }
    renderTimelineTracks();
    seekTimelinePlayhead(timelinePlayheadSec);
    if (selectedTimelineClipIndex) {
        selectTimelineClip(selectedTimelineClipIndex);
    }
    syncProgramOverlays(timelinePlayheadSec);
    updateUndoRedoButtons();
    showToast(`Redo: ${nextState.action} ↷`, "info");
}

function updateUndoRedoButtons() {
    const btnUndo = document.getElementById("btn-timeline-undo");
    const btnRedo = document.getElementById("btn-timeline-redo");
    if (btnUndo) {
        btnUndo.disabled = (timelineHistoryStack.length === 0);
        btnUndo.style.opacity = timelineHistoryStack.length > 0 ? "1" : "0.4";
    }
    if (btnRedo) {
        btnRedo.disabled = (timelineRedoStack.length === 0);
        btnRedo.style.opacity = timelineRedoStack.length > 0 ? "1" : "0.4";
    }
}

// Tab switcher between AI Pipeline, Premiere Pro, and AI Director FX Studio
function switchStudioTab(tabId) {
    document.querySelectorAll(".studio-tab-btn").forEach(btn => btn.classList.remove("active"));
    document.querySelectorAll(".workspace-tab").forEach(tab => tab.classList.remove("active"));

    if (tabId === "premiere") {
        const btnPrem = document.getElementById("tab-btn-premiere");
        const wsPrem = document.getElementById("workspace-premiere");
        if (btnPrem) btnPrem.classList.add("active");
        if (wsPrem) wsPrem.classList.add("active");
        initPremiereStudio();
    } else if (tabId === "director") {
        const btnDir = document.getElementById("tab-btn-director");
        const wsDir = document.getElementById("workspace-director");
        if (btnDir) btnDir.classList.add("active");
        if (wsDir) wsDir.classList.add("active");
        if (typeof initDirectorStudio === "function") {
            initDirectorStudio();
        }
    } else {
        const btnAi = document.getElementById("tab-btn-ai");
        const wsAi = document.getElementById("workspace-ai");
        if (btnAi) btnAi.classList.add("active");
        if (wsAi) wsAi.classList.add("active");
    }

    if (window.feather) feather.replace();
}

async function initPremiereStudio() {
    await fetchEditorMediaPool();
    if (typeof loadTranscript === "function") {
        await loadTranscript();
    }
    renderMediaBin("exported");
    renderInstagramFilters();
    renderTimelineRuler();
    renderTimelineTracks();
    updateUndoRedoButtons();

    // Default: populate timeline with 10 clips if empty
    if (activeTimelineClips.length === 0 && ((editorMediaPool.raw_clips && editorMediaPool.raw_clips.length > 0) || (editorMediaPool.exported_clips && editorMediaPool.exported_clips.length > 0))) {
        autoPopulateInitialTimeline();
    }
}

// ----------------- MEDIA BIN & CLIPS FETCH -----------------
async function fetchEditorMediaPool() {
    try {
        const res = await fetch("/api/editor/media-pool");
        const data = await res.json();
        editorMediaPool = data;
        if (!editorMediaPool.music_tracks || editorMediaPool.music_tracks.length === 0) {
            try {
                const resMusic = await fetch("/api/music/tracks");
                const mData = await resMusic.json();
                if (mData && mData.tracks) {
                    editorMediaPool.music_tracks = mData.tracks;
                }
            } catch (err) {}
        }
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
        if (aspect === "9:16") {
            phoneFrame.style.display = "block";
            phoneFrame.style.aspectRatio = "9 / 16";
            phoneFrame.style.maxWidth = "270px";
        } else if (aspect === "1:1") {
            phoneFrame.style.display = "block";
            phoneFrame.style.aspectRatio = "1 / 1";
            phoneFrame.style.maxWidth = "360px";
        } else if (aspect === "4:5") {
            phoneFrame.style.display = "block";
            phoneFrame.style.aspectRatio = "4 / 5";
            phoneFrame.style.maxWidth = "300px";
        } else { // 16:9 widescreen
            phoneFrame.style.display = "none";
        }
    }

    const aspectName = aspect === '9:16' ? 'Instagram Reels / TikTok (9:16)' :
                       aspect === '1:1' ? 'Square Feed (1:1)' :
                       aspect === '4:5' ? 'Instagram Portrait (4:5)' : '16:9 Widescreen';
    showToast(`Sequence Aspect Ratio: ${aspectName}`, "info");
}

// ----------------- MULTI-TRACK TIMELINE CONTROLLER -----------------
function autoPopulateInitialTimeline() {
    loadNClipsMultiTrackSequence(10);
}

function load10ClipsMultiTrackSequence() {
    loadNClipsMultiTrackSequence(10);
}

function loadNClipsMultiTrackSequence(count = 10) {
    if (activeTimelineClips.length > 0) {
        pushTimelineHistory(`Load ${count} Clips Sequence`);
    }
    activeTimelineClips = [];
    selectedTimelineClipIds.clear();
    selectedTimelineClipIndex = null;
    selectedTimelineGap = null;

    let pool = [];
    // Prioritize selected files from sidebar/media pool if any are chosen
    if (typeof selectedFileNames !== 'undefined' && selectedFileNames.size > 0 && editorMediaPool.raw_clips) {
        const selectedPool = editorMediaPool.raw_clips.filter(c => selectedFileNames.has(c.name));
        if (selectedPool.length > 0) {
            pool = selectedPool;
        }
    }
    if (pool.length === 0) {
        pool = (editorMediaPool.raw_clips && editorMediaPool.raw_clips.length >= count)
            ? editorMediaPool.raw_clips
            : (editorMediaPool.raw_clips ? editorMediaPool.raw_clips.concat(editorMediaPool.exported_clips || []) : (editorMediaPool.exported_clips || []));
    }

    const clipsToUse = pool.slice(0, count);
    if (clipsToUse.length === 0) {
        showToast("No clips available in media pool to populate sequence!", "warning");
        return;
    }

    let startSec = 0.0;
    const defaultTitle = (typeof directorTextBehind !== "undefined" && directorTextBehind.text)
        ? directorTextBehind.text
        : "RANN OF KUTCH | BHUJ | SOMNATH VLOG";

    clipsToUse.forEach((c, i) => {
        const isPhoto = /\.(jpe?g|png|heic|webp)$/i.test(c.name || c.path || "");
        const rawDur = parseFloat(c.duration) || 0.0;
        const segDur = isPhoto ? 4.0 : (rawDur > 0 ? rawDur : 4.0);
        const clipId = `v1_clip_${Date.now()}_${i}`;
        const voiceId = `a1_clip_${Date.now()}_${i}`;

        // 1. V1 Master Video Clip
        activeTimelineClips.push({
            id: clipId,
            path: c.path,
            name: c.name,
            track: "V1",
            type: "video",
            timeline_start: startSec,
            in_point: 0.0,
            out_point: segDur,
            duration: segDur,
            speed: 1.0,
            rotation: 0,
            scale: 100,
            posY: 0,
            opacity: 100,
            muted: false,
            url: c.url
        });

        // 2. A1 Voice Dialogue Audio Clip (linked to video clip)
        activeTimelineClips.push({
            id: voiceId,
            linked_video_id: clipId,
            path: c.path,
            name: `Voice: ${c.name}`,
            track: "A1",
            type: "audio_voice",
            timeline_start: startSec,
            in_point: 0.0,
            out_point: segDur,
            duration: segDur,
            volume: 100,
            noise_suppression: 75,
            muted: false,
            solo: false
        });

        startSec += segDur;
    });

    const totalDur = startSec;

    // 3. V3 Title Track Clip: Depth Title e.g. RANN OF KUTCH | BHUJ | SOMNATH VLOG
    activeTimelineClips.push({
        id: `v3_title_${Date.now()}`,
        name: `Title: ${defaultTitle}`,
        text: defaultTitle,
        track: "V3",
        type: "title",
        timeline_start: 0.0,
        in_point: 0.0,
        out_point: Math.min(totalDur, 12.0),
        duration: Math.min(totalDur, 12.0),
        font: "Montserrat",
        size: 55,
        posY: 0,
        scale: 100,
        neon_enabled: true,
        neon_color: "#00F2FE",
        glow_radius: 24,
        muted: false
    });

    // 4. V2 Overlay Track Clip: B-Roll / Visual Overlay cutaway slice on middle clips
    if (clipsToUse.length >= 4) {
        const overlaySource = clipsToUse[Math.min(3, clipsToUse.length - 1)];
        activeTimelineClips.push({
            id: `v2_overlay_${Date.now()}`,
            path: overlaySource.path,
            name: `Overlay: ${overlaySource.name}`,
            track: "V2",
            type: "video_overlay",
            timeline_start: Math.min(8.0, totalDur * 0.3),
            in_point: 0.0,
            out_point: 4.0,
            duration: 4.0,
            scale: 110,
            posY: 0,
            rotation: 0,
            opacity: 90,
            muted: false,
            url: overlaySource.url
        });
    }

    // 5. A2 Music Bed Track: Soundtrack with volume 40% and ducking 75%
    activeTimelineClips.push({
        id: `a2_music_${Date.now()}`,
        name: "Music: Airport_Lounge.mp3",
        path: "Airport_Lounge.mp3",
        url: "/media_raw/MUSIC/Airport_Lounge.mp3",
        track: "A2",
        type: "audio_music",
        timeline_start: 0.0,
        in_point: 0.0,
        out_point: totalDur,
        duration: totalDur,
        volume: 40,
        ducking: 75,
        muted: false,
        solo: false
    });

    renderTimelineTracks();
    seekTimelinePlayhead(0.0);
    showToast(`Loaded ${clipsToUse.length}-Clips Multi-Track Sequence into V1, V2, V3, A1, A2! 🎬`, "success");
}

function loadSelectedClipsToTimeline() {
    const count = (typeof selectedFileNames !== 'undefined' && selectedFileNames.size > 0) ? selectedFileNames.size : 10;
    loadNClipsMultiTrackSequence(count);
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

    const isPhoto = /\.(jpe?g|png|heic|webp)$/i.test(match.name || match.path || "");
    const rawDur = parseFloat(match.duration) || 0.0;
    const dur = isPhoto ? 4.0 : (rawDur > 0 ? rawDur : 4.0);
    const clipId = `clip_${Date.now()}`;
    activeTimelineClips.push({
        id: clipId,
        path: match.path,
        name: match.name,
        track: track,
        timeline_start: startSec,
        in_point: 0.0,
        out_point: dur,
        duration: dur,
        speed: 1.0,
        rotation: 0,
        scale: 100,
        posY: 0,
        opacity: 100,
        volume: 100,
        noise_suppression: 75,
        ducking: 75,
        muted: false,
        url: match.url
    });

    // Also add corresponding voice audio if adding to V1
    if (track === "V1") {
        activeTimelineClips.push({
            id: `a1_voice_${Date.now()}`,
            linked_video_id: clipId,
            path: match.path,
            name: `Voice: ${match.name}`,
            track: "A1",
            type: "audio_voice",
            timeline_start: startSec,
            in_point: 0.0,
            out_point: dur,
            duration: dur,
            volume: 100,
            noise_suppression: 75,
            muted: false
        });
    }

    renderTimelineTracks();
    showToast(`Added '${match.name}' to Timeline Track ${track} 🎬`, "success");
}

function renderTimelineTracks() {
    const tracks = ["V3", "V2", "V1", "A1", "A2"];
    tracks.forEach(trk => {
        const container = document.getElementById(`track-content-${trk}`);
        if (!container) return;

        const clips = activeTimelineClips.filter(c => c.track === trk).sort((a, b) => a.timeline_start - b.timeline_start);
        let trackHtml = "";

        // 1. Initial leading gap if first clip starts after 0.05s
        if (clips.length > 0 && clips[0].timeline_start > 0.05) {
            const gapStart = 0.0;
            const gapEnd = clips[0].timeline_start;
            const gapDur = gapEnd - gapStart;
            const leftPx = 0;
            const widthPx = Math.max(15, gapDur * timelineZoomPxPerSec);
            const isGapSel = selectedTimelineGap && selectedTimelineGap.track === trk && Math.abs(selectedTimelineGap.start - gapStart) < 0.05;
            trackHtml += `
                <div class="timeline-gap-block ${isGapSel ? 'selected' : ''}"
                     id="gap-${trk}-0"
                     style="left: ${leftPx}px; width: ${widthPx}px;"
                     onclick="selectTimelineGap(event, ${gapStart}, ${gapEnd}, '${trk}')"
                     oncontextmenu="showGapContextMenu(event, ${gapStart}, ${gapEnd}, '${trk}')"
                     title="Empty Gap (${gapDur.toFixed(1)}s) - Click to select, Right-click to Ripple Delete">
                    <span class="gap-label">✂️ ${gapDur >= 0.8 ? gapDur.toFixed(1) + 's Gap' : ''}</span>
                </div>
            `;
        }

        // 2. Render clips and intermediate gaps
        for (let i = 0; i < clips.length; i++) {
            const c = clips[i];
            const leftPx = c.timeline_start * timelineZoomPxPerSec;
            const widthPx = Math.max(35, c.duration * timelineZoomPxPerSec);
            const isSelected = (selectedTimelineClipIds && selectedTimelineClipIds.has(c.id)) || selectedTimelineClipIndex === c.id;
            const isMuted = !!c.muted;

            let trackClass = "";
            let badgeText = "";
            let icon = "🎬";

            if (trk === "V3") {
                trackClass = "track-v3";
                icon = "🔤";
                badgeText = `<span class="clip-badge-pill" style="color:#f472b6;">${c.text || c.name}</span>`;
            } else if (trk === "V2") {
                trackClass = "track-v2";
                icon = "🖼️";
                badgeText = `<span class="clip-badge-pill" style="color:#c084fc;">Overlay</span>`;
            } else if (trk === "A1") {
                trackClass = "track-audio track-voice";
                icon = "🎤";
                badgeText = `<span class="clip-badge-pill" style="color:#34d399;">Vol:${c.volume || 100}% Denoise:${c.noise_suppression || 75}%</span>`;
            } else if (trk === "A2") {
                trackClass = "track-audio track-music";
                icon = "🎵";
                badgeText = `<span class="clip-badge-pill" style="color:#a78bfa;">Vol:${c.volume || 40}% Duck:${c.ducking || 75}%</span>`;
            } else {
                trackClass = "track-v1";
                icon = "🎬";
                if (c.rotation) badgeText += `<span class="clip-badge-pill" style="color:#38bdf8;">${c.rotation}°</span>`;
                if (c.speed && c.speed !== 1.0) badgeText += `<span class="clip-badge-pill" style="color:#f59e0b;">${c.speed}x</span>`;
            }

            const muteBtnHtml = `
                <button class="clip-mute-inline-btn" onclick="event.stopPropagation(); toggleClipMute('${c.id}')" title="${isMuted ? 'Unmute Clip' : 'Mute Clip'}">
                    ${isMuted ? '🔇' : 'M'}
                </button>
            `;

            trackHtml += `
                <div class="timeline-clip-block ${trackClass} ${isSelected ? 'selected' : ''} ${isMuted ? 'muted' : ''}"
                     id="timeline-clip-${c.id}"
                     style="left: ${leftPx}px; width: ${widthPx}px; cursor: pointer; pointer-events: auto; z-index: 5;"
                     onmousedown="startClipDrag(event, '${c.id}')"
                     onclick="selectTimelineClip('${c.id}', event)"
                     oncontextmenu="showClipContextMenu(event, '${c.id}')"
                     title="${c.name} (${c.duration.toFixed(1)}s)">
                    <div class="clip-trim-handle-left" onmousedown="startClipTrim(event, '${c.id}', 'left')"></div>
                    <div style="display:flex; align-items:center; gap:4px; overflow:hidden; width:100%; pointer-events:none;">
                        <span style="pointer-events:auto;">${muteBtnHtml}</span>
                        <span style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-weight:600; font-size:10.5px;">${icon} ${c.name}</span>
                        ${badgeText}
                        ${isMuted ? '<span class="clip-badge-pill" style="background:#ef4444; color:#fff; font-weight:700;">MUTED</span>' : ''}
                    </div>
                    <div class="clip-trim-handle-right" onmousedown="startClipTrim(event, '${c.id}', 'right')"></div>
                </div>
            `;

            // Check gap between this clip and next clip
            if (i < clips.length - 1) {
                const nextClip = clips[i + 1];
                const clipEnd = c.timeline_start + c.duration;
                if (nextClip.timeline_start - clipEnd > 0.05) {
                    const gapStart = clipEnd;
                    const gapEnd = nextClip.timeline_start;
                    const gapDur = gapEnd - gapStart;
                    const gapLeftPx = gapStart * timelineZoomPxPerSec;
                    const gapWidthPx = Math.max(15, gapDur * timelineZoomPxPerSec);
                    const isGapSel = selectedTimelineGap && selectedTimelineGap.track === trk && Math.abs(selectedTimelineGap.start - gapStart) < 0.05;
                    trackHtml += `
                        <div class="timeline-gap-block ${isGapSel ? 'selected' : ''}"
                             id="gap-${trk}-${Math.round(gapStart * 100)}"
                             style="left: ${gapLeftPx}px; width: ${gapWidthPx}px;"
                             onclick="selectTimelineGap(event, ${gapStart}, ${gapEnd}, '${trk}')"
                             oncontextmenu="showGapContextMenu(event, ${gapStart}, ${gapEnd}, '${trk}')"
                             title="Empty Gap (${gapDur.toFixed(1)}s) - Click to select, Right-click to Ripple Delete">
                            <span class="gap-label">✂️ ${gapDur >= 0.8 ? gapDur.toFixed(1) + 's Gap' : ''}</span>
                        </div>
                    `;
                }
            }
        }
        container.innerHTML = trackHtml;
    });
}

function selectTimelineGap(event, gapStart, gapEnd, track) {
    if (event) event.stopPropagation();
    selectedTimelineClipIndex = null;
    selectedTimelineGap = { start: gapStart, end: gapEnd, track: track };
    renderTimelineTracks();
    seekTimelinePlayhead(gapStart);
    showToast(`Selected ${(gapEnd - gapStart).toFixed(1)}s Gap on Track ${track}. Press Delete or Right-Click to Ripple Delete ✂️`, "info");
}

function showGapContextMenu(event, gapStart, gapEnd, track) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    removeContextMenu();

    selectedTimelineClipIndex = null;
    selectedTimelineGap = { start: gapStart, end: gapEnd, track: track };
    renderTimelineTracks();

    const gapDur = gapEnd - gapStart;
    const menu = document.createElement("div");
    menu.id = "p-context-menu";
    menu.className = "premiere-context-menu";
    menu.style.left = `${Math.min(window.innerWidth - 260, (event ? event.clientX : 200))}px`;
    menu.style.top = `${Math.min(window.innerHeight - 230, (event ? event.clientY : 200))}px`;

    menu.innerHTML = `
        <div class="premiere-menu-item" style="color:#38bdf8; font-weight:700;" onclick="rippleDeleteGapAt(${gapStart}, ${gapEnd}, '${track}')">
            <span>✂️ Ripple Delete (${gapDur.toFixed(1)}s Gap)</span>
        </div>
        <div class="premiere-menu-item" onclick="rippleDeleteGapAt(${gapStart}, ${gapEnd}, 'ALL')">
            <span>🧲 Ripple Delete Across All Tracks</span>
        </div>
        <div class="premiere-menu-divider"></div>
        <div class="premiere-menu-item" onclick="rippleDeleteAllTimelineGaps()">
            <span>⚡ Close All Sequence Gaps 🧲</span>
        </div>
        <div class="premiere-menu-item" onclick="seekTimelinePlayhead(${gapStart}); removeContextMenu();">
            <span>⏮️ Move Playhead Here (${formatEditorTimecode(gapStart)})</span>
        </div>
    `;

    document.body.appendChild(menu);

    setTimeout(() => {
        document.addEventListener("click", removeContextMenu, { once: true });
        document.addEventListener("contextmenu", removeContextMenu, { once: true });
    }, 50);
}

function rippleDeleteGapAt(gapStart, gapEnd, targetTrack = "V1") {
    removeContextMenu();
    const gapDur = gapEnd - gapStart;
    if (gapDur <= 0.01) return;

    pushTimelineHistory("Ripple Delete Gap");
    // Ripple shift clips on target track (and both V1 & A1 if V1/A1 to keep audio/video locked)
    activeTimelineClips.forEach(c => {
        let shouldShift = false;
        if (targetTrack === "ALL") {
            shouldShift = true;
        } else if (targetTrack === "V1" || targetTrack === "A1") {
            shouldShift = (c.track === "V1" || c.track === "A1");
        } else {
            shouldShift = (c.track === targetTrack);
        }

        if (shouldShift && c.timeline_start >= (gapStart - 0.02)) {
            c.timeline_start = Math.max(0, c.timeline_start - gapDur);
        }
    });

    selectedTimelineGap = null;
    renderTimelineTracks();
    seekTimelinePlayhead(gapStart);
    showToast(`✂️ Ripple Deleted ${gapDur.toFixed(1)}s gap! Clips snapped flush 🧲`, "success");
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

function updatePlayheadVisualOnly(sec) {
    timelinePlayheadSec = Math.max(0, sec);
    const leftPx = 90 + (timelinePlayheadSec * timelineZoomPxPerSec);
    const playhead = document.getElementById("p-timeline-playhead");
    if (playhead) {
        playhead.style.left = `${leftPx}px`;
    }
    const tc = document.getElementById("p-master-timecode");
    if (tc) tc.innerText = formatEditorTimecode(timelinePlayheadSec);
}

function seekTimelinePlayhead(sec) {
    updatePlayheadVisualOnly(sec);
    // Sync Program Monitor video and overlays to the clip present at this time
    syncProgramMonitorToPlayhead();
}

function alignProgramMonitorLayers() {
    const video = document.getElementById("p-program-video");
    const wrapper = video ? video.parentElement : null;
    const depthOverlay = document.getElementById("p-program-depth-overlay");
    const canvas = document.getElementById("p-program-foreground-canvas");
    if (!video || !wrapper) return;

    const vRect = video.getBoundingClientRect();
    const wRect = wrapper.getBoundingClientRect();
    if (vRect.width === 0 || vRect.height === 0) return;

    const top = vRect.top - wRect.top;
    const left = vRect.left - wRect.left;
    const width = vRect.width;
    const height = vRect.height;

    if (canvas) {
        canvas.style.top = `${top}px`;
        canvas.style.left = `${left}px`;
        canvas.style.width = `${width}px`;
        canvas.style.height = `${height}px`;
    }

    if (depthOverlay) {
        depthOverlay.style.top = `${top + (height * 0.07)}px`;
        depthOverlay.style.left = `${left}px`;
        depthOverlay.style.width = `${width}px`;
    }
}

function renderForegroundPersonCutout() {
    const canvas = document.getElementById("p-program-foreground-canvas");
    const video = document.getElementById("p-program-video");
    if (!canvas || !video) return;

    const activeV3 = activeTimelineClips.find(c => c.track === "V3" && timelinePlayheadSec >= c.timeline_start && timelinePlayheadSec < (c.timeline_start + c.duration));
    if (!activeV3 || activeV3.muted) {
        canvas.style.display = "none";
        return;
    }

    if (video.readyState < 2) return;

    canvas.style.display = "block";
    alignProgramMonitorLayers();

    const w = canvas.width = video.videoWidth || 1920;
    const h = canvas.height = video.videoHeight || 1080;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, w, h);

    // Anatomical speaker foreground silhouette mask
    // Isolates speaker's head, face, hair, shoulders and torso
    ctx.save();
    ctx.beginPath();

    const cx = w * 0.54;
    const headTopY = h * 0.16;
    const headCenterY = h * 0.35;
    const headRx = w * 0.17;
    const headRy = h * 0.20;
    const shoulderY = h * 0.53;
    const bottomY = h;

    ctx.moveTo(cx - w * 0.40, bottomY);
    ctx.quadraticCurveTo(cx - w * 0.34, shoulderY + h * 0.12, cx - headRx * 1.35, shoulderY);
    ctx.quadraticCurveTo(cx - headRx * 1.15, headCenterY + headRy * 0.25, cx - headRx, headCenterY);
    ctx.bezierCurveTo(cx - headRx * 0.95, headTopY, cx + headRx * 0.95, headTopY, cx + headRx, headCenterY);
    ctx.quadraticCurveTo(cx + headRx * 1.15, headCenterY + headRy * 0.25, cx + headRx * 1.35, shoulderY);
    ctx.quadraticCurveTo(cx + w * 0.34, shoulderY + h * 0.12, cx + w * 0.40, bottomY);
    ctx.closePath();

    ctx.clip();
    ctx.drawImage(video, 0, 0, w, h);
    ctx.restore();
}

function syncProgramOverlays(sec) {
    // 1. V3 Title Track Overlay (e.g. RANN OF KUTCH | BHUJ | SOMNATH VLOG)
    const depthOverlay = document.getElementById("p-program-depth-overlay");
    const depthTextEl = document.getElementById("p-program-depth-text");
    const activeV3 = activeTimelineClips.find(c => c.track === "V3" && sec >= c.timeline_start && sec < (c.timeline_start + c.duration));

    if (activeV3 && !activeV3.muted && depthOverlay && depthTextEl) {
        depthOverlay.style.display = "flex";
        const titleText = activeV3.text || "RANN OF KUTCH | BHUJ | SOMNATH VLOG";
        const parts = titleText.split("|").map(t => t.trim()).filter(Boolean);
        depthTextEl.innerHTML = parts.join("<br>");
        depthTextEl.style.fontFamily = activeV3.font || "Montserrat";
        const glowRad = activeV3.glow_radius !== undefined ? activeV3.glow_radius : 24;
        const glowCol = activeV3.neon_color || "#00F2FE";
        depthTextEl.style.textShadow = `0 0 10px ${glowCol}, 0 0 20px ${glowCol}, 0 0 ${glowRad}px #00c3ff, 2px 2px 4px rgba(0,0,0,0.9)`;

        const scale = (activeV3.scale || 100) / 100;
        const posY = activeV3.posY || 0;
        depthOverlay.style.transform = `translateY(${posY}px) scale(${scale})`;
        alignProgramMonitorLayers();
    } else if (depthOverlay) {
        depthOverlay.style.display = "none";
    }

    // 2. V2 Video / Graphic Overlay Track
    const v2Video = document.getElementById("p-program-v2-overlay");
    const activeV2 = activeTimelineClips.find(c => c.track === "V2" && sec >= c.timeline_start && sec < (c.timeline_start + c.duration));

    if (activeV2 && !activeV2.muted && v2Video && activeV2.url) {
        v2Video.style.display = "block";
        if (!v2Video.src.includes(encodeURI(activeV2.url))) {
            v2Video.src = activeV2.url;
        }
        const v2Offset = sec - activeV2.timeline_start;
        const targetV2Time = (activeV2.in_point || 0) + v2Offset;
        if (Math.abs(v2Video.currentTime - targetV2Time) > 0.25) {
            v2Video.currentTime = targetV2Time;
        }
        v2Video.style.opacity = (activeV2.opacity !== undefined ? activeV2.opacity : 90) / 100;
        const scale = (activeV2.scale || 100) / 100;
        v2Video.style.transform = `scale(${scale})`;
        if (isTimelinePlaying && v2Video.paused) {
            v2Video.play().catch(() => {});
        }
    } else if (v2Video) {
        v2Video.style.display = "none";
        if (!v2Video.paused) v2Video.pause();
    }

    // 3. Foreground Subject Cutout (Layer 10: In Front of Depth Text)
    renderForegroundPersonCutout();
}

function syncMusicPlayback(forceStart = false) {
    const musicPlayer = document.getElementById("p-timeline-music-player");
    if (!musicPlayer) return;

    const activeA2 = activeTimelineClips.find(c => c.track === "A2" && timelinePlayheadSec >= c.timeline_start && timelinePlayheadSec < (c.timeline_start + c.duration));

    if (activeA2 && !activeA2.muted) {
        const musicSrc = activeA2.url || ("/media_raw/MUSIC/" + (activeA2.path || "Airport_Lounge.mp3"));
        if (!musicPlayer.src.includes("Airport_Lounge.mp3") && !musicPlayer.src.includes(encodeURI(activeA2.path || ""))) {
            musicPlayer.src = musicSrc;
        }

        // Auto-ducking calculations
        const baseVol = (activeA2.volume !== undefined ? activeA2.volume : 40) / 100.0;
        const activeVoice = activeTimelineClips.find(c => c.track === "A1" && timelinePlayheadSec >= c.timeline_start && timelinePlayheadSec < (c.timeline_start + c.duration));
        let duckFactor = 1.0;
        if (activeVoice && !activeVoice.muted) {
            const duckPct = activeA2.ducking !== undefined ? activeA2.ducking : 75;
            duckFactor = Math.max(0.15, (100 - duckPct * 0.75) / 100.0);
        }
        musicPlayer.volume = Math.max(0, Math.min(1, baseVol * duckFactor));

        if (isTimelinePlaying) {
            const musicOffset = timelinePlayheadSec - activeA2.timeline_start;
            if (forceStart || Math.abs(musicPlayer.currentTime - musicOffset) > 0.4) {
                musicPlayer.currentTime = musicOffset;
            }
            if (musicPlayer.paused) {
                musicPlayer.play().catch(e => console.log("Music play audio:", e));
            }
        } else {
            if (!musicPlayer.paused) musicPlayer.pause();
        }
    } else {
        if (!musicPlayer.paused) musicPlayer.pause();
    }
}

function syncProgramMonitorToPlayhead() {
    // Find active V1 clip at playhead time
    const activeClip = activeTimelineClips.find(c => 
        c.track === "V1" && timelinePlayheadSec >= c.timeline_start && timelinePlayheadSec < (c.timeline_start + c.duration)
    );

    const programVideo = document.getElementById("p-program-video");
    if (!programVideo) return;

    if (activeClip && activeClip.url) {
        const offsetInClip = timelinePlayheadSec - activeClip.timeline_start;
        const targetVideoTime = (activeClip.in_point || 0) + offsetInClip;

        if (!programVideo.src.includes(encodeURI(activeClip.url))) {
            programVideo.src = activeClip.url;
            programVideo.load();
        }
        programVideo.currentTime = targetVideoTime;
        programVideo.playbackRate = activeClip.speed || 1.0;
        applyClipVisualTransforms(activeClip);

        // Voice volume & mute from linked A1 clip
        const voiceClip = activeTimelineClips.find(c => c.track === "A1" && Math.abs(c.timeline_start - activeClip.timeline_start) < 0.1);
        if (voiceClip) {
            programVideo.muted = !!voiceClip.muted;
            programVideo.volume = Math.max(0, Math.min(1, (voiceClip.volume !== undefined ? voiceClip.volume : 100) / 100));
        } else {
            programVideo.muted = !!activeClip.muted;
        }

        // HyperFrame 4-Quadrant Dynamic Captions in Program Monitor
        if (typeof projectTranscript !== 'undefined' && projectTranscript.words && typeof renderHyperframeCaptions === 'function') {
            const activeWord = projectTranscript.words.find(w => timelinePlayheadSec >= w.start && timelinePlayheadSec <= w.end);
            renderHyperframeCaptions(activeWord, timelinePlayheadSec, 'p');
        }
    } else {
        if (typeof renderHyperframeCaptions === 'function') {
            renderHyperframeCaptions(null, 0, 'p');
        }
    }

    // Live sync overlays (V3 depth title, V2 overlay) and music
    syncProgramOverlays(timelinePlayheadSec);
    syncMusicPlayback(true);
}

// ----------------- RAZOR CUT TOOL (C) & EDITING TOOLS -----------------
function setEditorTool(tool) {
    activeEditorTool = tool;
    document.querySelectorAll(".tool-btn").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.tool === tool);
    });
    if (tool === "text") {
        setLeftUpperTab("stickers");
        const titleInput = document.getElementById("p-instagram-title-input");
        if (titleInput) titleInput.focus();
    }
    showToast(`Active Tool: ${tool.toUpperCase()} (${tool === 'razor' ? 'Split clip at playhead (C)' : tool === 'ripple' ? 'Ripple Edit (B)' : tool === 'text' ? 'Instagram Typography (T)' : 'Select & Move (V)'})`, "info");
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

    pushTimelineHistory("Razor Cut");
    activeTimelineClips.splice(targetIdx, 1, clipA, clipB);
    renderTimelineTracks();
    showToast(`✂️ Razor Cut executed at ${timelinePlayheadSec.toFixed(2)}s! Split into 2 clips.`, "success");
}

function deleteSelectedTimelineClip() {
    if (selectedTimelineClipIds && selectedTimelineClipIds.size > 1) {
        deleteSelectedTimelineClipsBatch();
        return;
    }
    if (!selectedTimelineClipIndex) return;
    const clip = activeTimelineClips.find(c => c.id === selectedTimelineClipIndex);
    const clipName = clip ? clip.name : "Clip";
    const clipTrack = clip ? clip.track : "V1";
    const clipStart = clip ? clip.timeline_start : 0;
    const clipDur = clip ? clip.duration : 0;

    pushTimelineHistory(`Delete ${clipName}`);
    activeTimelineClips = activeTimelineClips.filter(c => c.id !== selectedTimelineClipIndex);

    // Also remove matching linked audio if on V1/A1
    if (clip && clip.track === "V1") {
        const linkedA1 = activeTimelineClips.find(c => c.track === "A1" && Math.abs(c.timeline_start - clipStart) < 0.1);
        if (linkedA1) {
            activeTimelineClips = activeTimelineClips.filter(c => c.id !== linkedA1.id);
        }
    } else if (clip && clip.track === "A1") {
        const linkedV1 = activeTimelineClips.find(c => c.track === "V1" && Math.abs(c.timeline_start - clipStart) < 0.1);
        if (linkedV1) {
            activeTimelineClips = activeTimelineClips.filter(c => c.id !== linkedV1.id);
        }
    }

    selectedTimelineClipIds.clear();
    selectedTimelineClipIndex = null;
    selectedTimelineGap = { start: clipStart, end: clipStart + clipDur, track: clipTrack };
    renderTimelineTracks();
    showToast(`🗑️ Deleted '${clipName}'. Empty space left in timeline — right-click the gap to Ripple Delete!`, "info");
}

function deleteSelectedTimelineClipsBatch() {
    if (!selectedTimelineClipIds || selectedTimelineClipIds.size === 0) {
        if (selectedTimelineClipIndex) {
            deleteSelectedTimelineClip();
        }
        return;
    }
    const count = selectedTimelineClipIds.size;
    pushTimelineHistory(`Delete ${count} Clips`);
    activeTimelineClips = activeTimelineClips.filter(c => !selectedTimelineClipIds.has(c.id));
    selectedTimelineClipIds.clear();
    selectedTimelineClipIndex = null;
    selectedTimelineGap = null;
    renderTimelineTracks();
    syncProgramMonitorToPlayhead();
    showToast(`🗑️ Deleted ${count} selected clips from timeline! Press Ctrl+Z to undo.`, "success");
}

function clearTimeline() {
    if (!activeTimelineClips || activeTimelineClips.length === 0) {
        showToast("Timeline is already empty!", "info");
        return;
    }
    const count = activeTimelineClips.length;
    pushTimelineHistory("Clear Timeline");
    activeTimelineClips = [];
    selectedTimelineClipIds.clear();
    selectedTimelineClipIndex = null;
    selectedTimelineGap = null;
    timelinePlayheadSec = 0.0;
    renderTimelineTracks();
    syncProgramMonitorToPlayhead();
    showToast(`🗑️ Cleared all ${count} clips from timeline! Press Ctrl+Z to undo.`, "info");
}

function selectAllTimelineClips() {
    if (!activeTimelineClips || activeTimelineClips.length === 0) {
        showToast("Timeline is empty", "info");
        return;
    }
    selectedTimelineGap = null;
    selectedTimelineClipIds = new Set(activeTimelineClips.map(c => c.id));
    selectedTimelineClipIndex = activeTimelineClips[0]?.id || null;
    renderTimelineTracks();
    if (selectedTimelineClipIndex) {
        const clip = activeTimelineClips.find(c => c.id === selectedTimelineClipIndex);
        if (clip) {
            const clipNameEl = document.getElementById("fx-clip-name");
            if (clipNameEl) clipNameEl.innerText = `All Clips Selected (${activeTimelineClips.length})`;
        }
    }
    showToast(`Selected all ${activeTimelineClips.length} clips across timeline (Press Delete / Backspace to remove) ✂️`, "info");
}

function rippleDeleteClip(clipId) {
    removeContextMenu();
    const clip = activeTimelineClips.find(c => c.id === clipId);
    if (!clip) return;
    pushTimelineHistory(`Ripple Delete ${clip.name}`);
    const gapStart = clip.timeline_start;
    const gapDur = clip.duration;
    const track = clip.track;

    activeTimelineClips = activeTimelineClips.filter(c => c.id !== clipId);
    if (track === "V1") {
        activeTimelineClips = activeTimelineClips.filter(c => !(c.track === "A1" && Math.abs(c.timeline_start - gapStart) < 0.1));
    } else if (track === "A1") {
        activeTimelineClips = activeTimelineClips.filter(c => !(c.track === "V1" && Math.abs(c.timeline_start - gapStart) < 0.1));
    }

    activeTimelineClips.forEach(c => {
        if ((c.track === track || ((track === "V1" || track === "A1") && (c.track === "V1" || c.track === "A1"))) && c.timeline_start >= gapStart) {
            c.timeline_start = Math.max(0, c.timeline_start - gapDur);
        }
    });

    selectedTimelineClipIndex = null;
    selectedTimelineGap = null;
    renderTimelineTracks();
    seekTimelinePlayhead(gapStart);
    showToast(`✂️ Ripple deleted '${clip.name}' and closed gap! 🧲`, "success");
}

function applyClipVisualTransforms(clip) {
    const programVideo = document.getElementById("p-program-video");
    if (!programVideo || !clip) return;
    const rot = clip.rotation || 0;
    const scale = (clip.scale || 100) / 100;
    const posY = clip.posY || 0;
    const op = ((clip.opacity !== undefined) ? clip.opacity : 100) / 100;

    programVideo.style.transition = "transform 0.15s ease, opacity 0.15s ease";
    programVideo.style.transform = `translateY(${posY}px) rotate(${rot}deg) scale(${scale})`;
    programVideo.style.opacity = op;
}

function selectTimelineClip(clipId, e = null) {
    selectedTimelineGap = null;
    if (activeEditorTool === "razor") {
        executeRazorCutAtPlayhead();
        return;
    }

    if (e && (e.ctrlKey || e.metaKey || e.shiftKey)) {
        if (selectedTimelineClipIds.has(clipId)) {
            selectedTimelineClipIds.delete(clipId);
            if (selectedTimelineClipIndex === clipId) {
                selectedTimelineClipIndex = Array.from(selectedTimelineClipIds)[0] || null;
            }
        } else {
            selectedTimelineClipIds.add(clipId);
            selectedTimelineClipIndex = clipId;
        }
    } else {
        selectedTimelineClipIds.clear();
        selectedTimelineClipIds.add(clipId);
        selectedTimelineClipIndex = clipId;
    }

    renderTimelineTracks();
    const clip = activeTimelineClips.find(c => c.id === selectedTimelineClipIndex);
    if (!clip) return;

    // Automatically switch to Effect Controls tab so sliders are immediately visible
    setLeftUpperTab("effects");

    // Load universal header
    const clipNameEl = document.getElementById("fx-clip-name");
    const trackBadge = document.getElementById("fx-clip-track-badge");
    const muteBtn = document.getElementById("btn-fx-mute-clip");

    if (clipNameEl) clipNameEl.innerText = clip.name;
    if (trackBadge) {
        trackBadge.innerText = `TRACK ${clip.track}`;
        if (clip.track === "V3") trackBadge.style.background = "#be185d";
        else if (clip.track === "V2") trackBadge.style.background = "#7e22ce";
        else if (clip.track === "A1") trackBadge.style.background = "#065f46";
        else if (clip.track === "A2") trackBadge.style.background = "#3730a3";
        else trackBadge.style.background = "#0284c7";
    }
    if (muteBtn) {
        muteBtn.innerHTML = clip.muted 
            ? `<i data-feather="volume-2"></i> Unmute Clip` 
            : `<i data-feather="volume-x"></i> Mute Clip`;
        muteBtn.style.color = clip.muted ? "#ef4444" : "#cbd5e1";
        muteBtn.style.borderColor = clip.muted ? "#ef4444" : "#475569";
    }

    // Toggle specific effect groups
    const gVoice = document.getElementById("fx-group-voice-audio");
    const gMusic = document.getElementById("fx-group-music-bed");
    const gTitle = document.getElementById("fx-group-title-v3");
    const gMotion = document.getElementById("fx-group-video-motion");
    const gVelocity = document.getElementById("fx-group-velocity");
    const gOpacity = document.getElementById("fx-group-opacity");

    if (clip.track === "A1") {
        if (gVoice) gVoice.style.display = "block";
        if (gMusic) gMusic.style.display = "none";
        if (gTitle) gTitle.style.display = "none";
        if (gMotion) gMotion.style.display = "none";
        if (gVelocity) gVelocity.style.display = "none";
        if (gOpacity) gOpacity.style.display = "none";

        const vSlider = document.getElementById("fx-voice-vol-slider");
        const vVal = document.getElementById("fx-voice-vol-val");
        const nSlider = document.getElementById("fx-noise-slider");
        const nVal = document.getElementById("fx-noise-val");

        clip.volume = clip.volume !== undefined ? clip.volume : 100;
        clip.noise_suppression = clip.noise_suppression !== undefined ? clip.noise_suppression : 75;

        if (vSlider) vSlider.value = clip.volume;
        if (vVal) vVal.innerText = `${clip.volume}%`;
        if (nSlider) nSlider.value = clip.noise_suppression;
        if (nVal) nVal.innerText = `${clip.noise_suppression}%`;
    } else if (clip.track === "A2") {
        if (gVoice) gVoice.style.display = "none";
        if (gMusic) gMusic.style.display = "block";
        if (gTitle) gTitle.style.display = "none";
        if (gMotion) gMotion.style.display = "none";
        if (gVelocity) gVelocity.style.display = "none";
        if (gOpacity) gOpacity.style.display = "none";

        const mSlider = document.getElementById("fx-music-vol-slider");
        const mVal = document.getElementById("fx-music-vol-val");
        const dSlider = document.getElementById("fx-ducking-slider");
        const dVal = document.getElementById("fx-ducking-val");

        clip.volume = clip.volume !== undefined ? clip.volume : 40;
        clip.ducking = clip.ducking !== undefined ? clip.ducking : 75;

        if (mSlider) mSlider.value = clip.volume;
        if (mVal) mVal.innerText = `${clip.volume}%`;
        if (dSlider) dSlider.value = clip.ducking;
        if (dVal) dVal.innerText = `${clip.ducking}%`;

        const musicSel = document.getElementById("fx-music-track-select");
        if (musicSel) {
            const tracks = editorMediaPool.music_tracks || [];
            musicSel.innerHTML = tracks.map(tr => {
                const isSelected = (clip.path === tr.name || clip.name.includes(tr.name) || clip.name.includes(tr.title));
                return `<option value="${tr.name}" ${isSelected ? "selected" : ""}>${tr.title} (${formatTimecode(tr.duration || 0)})</option>`;
            }).join("");
        }
    } else if (clip.track === "V3") {
        if (gVoice) gVoice.style.display = "none";
        if (gMusic) gMusic.style.display = "none";
        if (gTitle) gTitle.style.display = "block";
        if (gMotion) gMotion.style.display = "none";
        if (gVelocity) gVelocity.style.display = "none";
        if (gOpacity) gOpacity.style.display = "none";

        const tInput = document.getElementById("fx-title-text-input");
        const fSelect = document.getElementById("fx-title-font-select");
        const gSlider = document.getElementById("fx-title-glow-slider");
        const gVal = document.getElementById("fx-title-glow-val");
        const posSlider = document.getElementById("fx-title-pos-slider");
        const posVal = document.getElementById("fx-title-pos-val");
        const scaleSlider = document.getElementById("fx-title-scale-slider");
        const scaleVal = document.getElementById("fx-title-scale-val");

        clip.text = clip.text || (typeof directorTextBehind !== "undefined" ? directorTextBehind.text : "RANN OF KUTCH | BHUJ | SOMNATH VLOG");
        clip.font = clip.font || "Montserrat";
        clip.glow_radius = clip.glow_radius || 24;
        clip.posY = clip.posY !== undefined ? clip.posY : 0;
        clip.scale = clip.scale !== undefined ? clip.scale : 100;

        if (tInput) tInput.value = clip.text;
        if (fSelect) fSelect.value = clip.font;
        if (gSlider) gSlider.value = clip.glow_radius;
        if (gVal) gVal.innerText = `${clip.glow_radius}px`;
        if (posSlider) posSlider.value = clip.posY;
        if (posVal) posVal.innerText = `${clip.posY}px`;
        if (scaleSlider) scaleSlider.value = clip.scale;
        if (scaleVal) scaleVal.innerText = `${clip.scale}%`;
    } else { // V1 or V2 video clip
        if (gVoice) gVoice.style.display = "none";
        if (gMusic) gMusic.style.display = "none";
        if (gTitle) gTitle.style.display = "none";
        if (gMotion) gMotion.style.display = "block";
        if (gVelocity) gVelocity.style.display = "block";
        if (gOpacity) gOpacity.style.display = "block";

        clip.scale = clip.scale || 100;
        clip.posY = clip.posY || 0;
        clip.opacity = clip.opacity !== undefined ? clip.opacity : 100;
        clip.speed = clip.speed || 1.0;
        clip.rotation = clip.rotation || 0;

        const spSlider = document.getElementById("fx-speed-slider");
        const spVal = document.getElementById("fx-speed-val");
        if (spSlider) spSlider.value = clip.speed;
        if (spVal) spVal.innerText = `${clip.speed.toFixed(1)}x`;

        const rotSlider = document.getElementById("fx-rot-slider");
        const rotVal = document.getElementById("fx-rot-val");
        if (rotSlider) rotSlider.value = clip.rotation;
        if (rotVal) rotVal.innerText = `${clip.rotation}°`;

        const scSlider = document.getElementById("fx-scale-slider");
        const scVal = document.getElementById("fx-scale-val");
        if (scSlider) scSlider.value = clip.scale;
        if (scVal) scVal.innerText = `${clip.scale}%`;

        const posSlider = document.getElementById("fx-pos-slider");
        const posVal = document.getElementById("fx-pos-val");
        if (posSlider) posSlider.value = clip.posY;
        if (posVal) posVal.innerText = `${clip.posY}`;

        const opSlider = document.getElementById("fx-op-slider");
        const opVal = document.getElementById("fx-op-val");
        if (opSlider) opSlider.value = clip.opacity;
        if (opVal) opVal.innerText = `${clip.opacity}%`;

        applyClipVisualTransforms(clip);
    }

    if (window.feather) feather.replace();
}

function moveSelectedClipTrackUp() {
    if (!selectedTimelineClipIndex) {
        showToast("Select a clip on the timeline first to shift track!", "warning");
        return;
    }
    const clip = activeTimelineClips.find(c => c.id === selectedTimelineClipIndex);
    if (!clip) return;
    
    pushTimelineHistory("Move Track Up");
    if (clip.track === "V1") clip.track = "V2";
    else if (clip.track === "V2") clip.track = "V3";
    else if (clip.track === "A2") clip.track = "A1";
    else {
        showToast("Clip is already on the top track!", "info");
        return;
    }
    renderTimelineTracks();
    selectTimelineClip(clip.id);
    showToast(`Moved '${clip.name}' up to Track ${clip.track} ⬆️`, "success");
}

function moveSelectedClipTrackDown() {
    if (!selectedTimelineClipIndex) {
        showToast("Select a clip on the timeline first to shift track!", "warning");
        return;
    }
    const clip = activeTimelineClips.find(c => c.id === selectedTimelineClipIndex);
    if (!clip) return;

    pushTimelineHistory("Move Track Down");
    if (clip.track === "V3") clip.track = "V2";
    else if (clip.track === "V2") clip.track = "V1";
    else if (clip.track === "A1") clip.track = "A2";
    else {
        showToast("Clip is already on the bottom track!", "info");
        return;
    }
    renderTimelineTracks();
    selectTimelineClip(clip.id);
    showToast(`Moved '${clip.name}' down to Track ${clip.track} ⬇️`, "success");
}

function toggleClipMute(clipId) {
    const clip = activeTimelineClips.find(c => c.id === clipId);
    if (!clip) return;
    clip.muted = !clip.muted;

    // Apply live mute changes to media and overlays
    if (clip.track === "V1") {
        const programVideo = document.getElementById("p-program-video");
        if (programVideo) programVideo.style.opacity = clip.muted ? "0" : ((clip.opacity !== undefined ? clip.opacity : 100) / 100);
    } else if (clip.track === "A1") {
        const programVideo = document.getElementById("p-program-video");
        if (programVideo) programVideo.muted = !!clip.muted;
    } else if (clip.track === "A2") {
        const musicPlayer = document.getElementById("p-timeline-music-player");
        if (musicPlayer) musicPlayer.muted = !!clip.muted;
    } else if (clip.track === "V3" || clip.track === "V2") {
        syncProgramOverlays(timelinePlayheadSec);
    }

    renderTimelineTracks();
    if (selectedTimelineClipIndex === clip.id) {
        selectTimelineClip(clip.id);
    }
    showToast(`Clip '${clip.name}' ${clip.muted ? "Muted 🔇" : "Unmuted 🔊"}`, "info");
}

function toggleSelectedClipMute() {
    if (!selectedTimelineClipIndex) {
        showToast("Select a clip on the timeline first to mute/unmute!", "warning");
        return;
    }
    toggleClipMute(selectedTimelineClipIndex);
}

function updateSelectedVoiceVolume(val) {
    const clip = activeTimelineClips.find(c => c.id === selectedTimelineClipIndex);
    if (!clip) return;
    clip.volume = parseInt(val);
    const badge = document.getElementById("fx-voice-vol-val");
    if (badge) badge.innerText = `${clip.volume}%`;
    const programVideo = document.getElementById("p-program-video");
    if (programVideo && !clip.muted) {
        programVideo.volume = Math.max(0, Math.min(1, clip.volume / 100));
    }
    renderTimelineTracks();
}

function updateSelectedNoiseSuppression(val) {
    const clip = activeTimelineClips.find(c => c.id === selectedTimelineClipIndex);
    if (!clip) return;
    clip.noise_suppression = parseInt(val);
    const badge = document.getElementById("fx-noise-val");
    if (badge) badge.innerText = `${clip.noise_suppression}%`;
    renderTimelineTracks();
}

function updateSelectedMusicVolume(val) {
    const clip = activeTimelineClips.find(c => c.id === selectedTimelineClipIndex);
    if (!clip) return;
    clip.volume = parseInt(val);
    const badge = document.getElementById("fx-music-vol-val");
    if (badge) badge.innerText = `${clip.volume}%`;
    syncMusicPlayback(false);
    renderTimelineTracks();
}

function updateSelectedMusicDucking(val) {
    const clip = activeTimelineClips.find(c => c.id === selectedTimelineClipIndex);
    if (!clip) return;
    clip.ducking = parseInt(val);
    const badge = document.getElementById("fx-ducking-val");
    if (badge) badge.innerText = `${clip.ducking}%`;
    syncMusicPlayback(false);
    renderTimelineTracks();
}

function updateSelectedTitleText(val) {
    const clip = activeTimelineClips.find(c => c.id === selectedTimelineClipIndex);
    if (!clip) return;
    clip.text = val;
    clip.name = `Title: ${val}`;
    syncProgramOverlays(timelinePlayheadSec);
    renderTimelineTracks();
}

function updateSelectedTitleFont(val) {
    const clip = activeTimelineClips.find(c => c.id === selectedTimelineClipIndex);
    if (!clip) return;
    clip.font = val;
    syncProgramOverlays(timelinePlayheadSec);
}

function updateSelectedTitleGlow(val) {
    const clip = activeTimelineClips.find(c => c.id === selectedTimelineClipIndex);
    if (!clip) return;
    clip.glow_radius = parseInt(val);
    const badge = document.getElementById("fx-title-glow-val");
    if (badge) badge.innerText = `${clip.glow_radius}px`;
    syncProgramOverlays(timelinePlayheadSec);
}

function updateSelectedTitlePosY(val) {
    const clip = activeTimelineClips.find(c => c.id === selectedTimelineClipIndex);
    if (!clip) return;
    clip.posY = parseInt(val);
    const badge = document.getElementById("fx-title-pos-val");
    if (badge) badge.innerText = `${clip.posY}px`;
    syncProgramOverlays(timelinePlayheadSec);
}

function updateSelectedTitleScale(val) {
    const clip = activeTimelineClips.find(c => c.id === selectedTimelineClipIndex);
    if (!clip) return;
    clip.scale = parseInt(val);
    const badge = document.getElementById("fx-title-scale-val");
    if (badge) badge.innerText = `${clip.scale}%`;
    syncProgramOverlays(timelinePlayheadSec);
}

async function saveSelectedTitleClip() {
    const clip = activeTimelineClips.find(c => c.id === selectedTimelineClipIndex);
    const textInput = document.getElementById("fx-title-text-input");
    const newText = (textInput && textInput.value.trim()) ? textInput.value.trim() : (clip ? clip.text : "RANN OF KUTCH | BHUJ | SOMNATH VLOG");

    if (clip) {
        clip.text = newText;
        clip.name = `Title: ${newText}`;
    }

    if (typeof directorTextBehind !== "undefined") {
        directorTextBehind.text = newText;
        if (clip) directorTextBehind.y_offset = clip.posY || 0;
        try { localStorage.setItem("anirban_text_behind", JSON.stringify(directorTextBehind)); } catch (e) {}
    }

    const depthInput = document.getElementById("depth-input-text");
    if (depthInput) depthInput.value = newText;
    if (typeof updateLiveDepthTextPreview === "function") updateLiveDepthTextPreview();

    try {
        await fetch("/api/ai-director/text-behind-person", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                text: newText,
                enabled: true,
                position: "head",
                y_offset: clip ? (clip.posY || 0) : 0,
                font: clip ? (clip.font || "Montserrat") : "Montserrat",
                glow_radius: clip ? (clip.glow_radius || 24) : 24
            })
        });
        showToast(`✓ Title saved & registered: "${newText}"`, "success");
    } catch (e) {
        console.error("Error saving title:", e);
    }
    renderTimelineTracks();
}

function updateSelectedClipScale(val) {
    const clip = activeTimelineClips.find(c => c.id === selectedTimelineClipIndex);
    if (!clip) return;
    clip.scale = parseInt(val);
    const badge = document.getElementById("fx-scale-val");
    if (badge) badge.innerText = `${clip.scale}%`;
    applyClipVisualTransforms(clip);
}

function updateSelectedClipPosY(val) {
    const clip = activeTimelineClips.find(c => c.id === selectedTimelineClipIndex);
    if (!clip) return;
    clip.posY = parseInt(val);
    const badge = document.getElementById("fx-pos-val");
    if (badge) badge.innerText = `${clip.posY}`;
    applyClipVisualTransforms(clip);
}

function updateSelectedClipOpacity(val) {
    const clip = activeTimelineClips.find(c => c.id === selectedTimelineClipIndex);
    if (!clip) return;
    clip.opacity = parseInt(val);
    const badge = document.getElementById("fx-op-val");
    if (badge) badge.innerText = `${clip.opacity}%`;
    applyClipVisualTransforms(clip);
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
    applyClipVisualTransforms(clip);
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
    applyClipVisualTransforms(clip);
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
let playbackRafId = null;
let lastRafTime = 0;

function toggleTimelinePlayback() {
    isTimelinePlaying = !isTimelinePlaying;
    const btn = document.getElementById("p-btn-play-pause");
    const programVideo = document.getElementById("p-program-video");
    const musicPlayer = document.getElementById("p-timeline-music-player");
    const v2Video = document.getElementById("p-program-v2-overlay");

    if (isTimelinePlaying) {
        if (btn) btn.innerHTML = `<i data-feather="pause"></i>`;
        
        // Find active V1 clip at playhead
        let activeV1 = activeTimelineClips.find(c => c.track === "V1" && timelinePlayheadSec >= c.timeline_start && timelinePlayheadSec < (c.timeline_start + c.duration));
        if (!activeV1) {
            const firstV1 = activeTimelineClips.filter(c => c.track === "V1").sort((a,b) => a.timeline_start - b.timeline_start)[0];
            if (firstV1) {
                seekTimelinePlayhead(firstV1.timeline_start);
                activeV1 = firstV1;
            }
        }

        if (activeV1 && programVideo) {
            const clipOffset = timelinePlayheadSec - activeV1.timeline_start;
            const targetTime = (activeV1.in_point || 0) + clipOffset;
            
            if (!programVideo.src.includes(encodeURI(activeV1.url))) {
                programVideo.src = activeV1.url;
            }
            if (Math.abs(programVideo.currentTime - targetTime) > 0.15) {
                programVideo.currentTime = targetTime;
            }
            programVideo.playbackRate = activeV1.speed || 1.0;

            const voiceClip = activeTimelineClips.find(c => c.track === "A1" && Math.abs(c.timeline_start - activeV1.timeline_start) < 0.1);
            if (voiceClip) {
                programVideo.muted = !!voiceClip.muted;
                programVideo.volume = Math.max(0, Math.min(1, (voiceClip.volume !== undefined ? voiceClip.volume : 100) / 100));
            } else {
                programVideo.muted = !!activeV1.muted;
            }

            programVideo.play().catch(e => console.log("Program video play:", e));
        }

        // Start music player
        syncMusicPlayback(true);

        // Start overlays
        syncProgramOverlays(timelinePlayheadSec);

        // Start smooth RAF loop
        startSmoothPlaybackLoop();
    } else {
        if (btn) btn.innerHTML = `<i data-feather="play"></i>`;
        if (programVideo) programVideo.pause();
        if (musicPlayer) musicPlayer.pause();
        if (v2Video) v2Video.pause();
        if (playbackRafId) {
            cancelAnimationFrame(playbackRafId);
            playbackRafId = null;
        }
        clearInterval(timelinePlaybackTimer);
        timelinePlaybackTimer = null;
    }

    if (window.feather) feather.replace();
}

function startSmoothPlaybackLoop() {
    if (playbackRafId) cancelAnimationFrame(playbackRafId);
    lastRafTime = performance.now();

    function step() {
        if (!isTimelinePlaying) return;
        const now = performance.now();
        const dt = (now - lastRafTime) / 1000.0;
        lastRafTime = now;

        const programVideo = document.getElementById("p-program-video");
        const activeV1 = activeTimelineClips.find(c => c.track === "V1" && timelinePlayheadSec >= c.timeline_start && timelinePlayheadSec < (c.timeline_start + c.duration));

        if (activeV1 && programVideo && !programVideo.paused && programVideo.readyState >= 2) {
            const currentClipSec = programVideo.currentTime - (activeV1.in_point || 0);
            timelinePlayheadSec = activeV1.timeline_start + currentClipSec;

            // Boundary transition to next clip
            const outPt = activeV1.out_point || activeV1.duration;
            if (programVideo.currentTime >= outPt || currentClipSec >= activeV1.duration) {
                const nextV1 = activeTimelineClips.find(c => c.track === "V1" && c.timeline_start >= (activeV1.timeline_start + activeV1.duration - 0.05));
                if (nextV1) {
                    timelinePlayheadSec = nextV1.timeline_start;
                    programVideo.src = nextV1.url;
                    programVideo.currentTime = nextV1.in_point || 0;
                    programVideo.playbackRate = nextV1.speed || 1.0;
                    applyClipVisualTransforms(nextV1);

                    const voiceClip = activeTimelineClips.find(c => c.track === "A1" && Math.abs(c.timeline_start - nextV1.timeline_start) < 0.1);
                    if (voiceClip) {
                        programVideo.muted = !!voiceClip.muted;
                        programVideo.volume = Math.max(0, Math.min(1, (voiceClip.volume !== undefined ? voiceClip.volume : 100) / 100));
                    }
                    programVideo.play().catch(() => {});
                } else {
                    // Reached end of sequence!
                    toggleTimelinePlayback();
                    seekTimelinePlayhead(0.0);
                    return;
                }
            }
        } else {
            timelinePlayheadSec += dt;
        }

        // Smooth playhead line & timecode visual updates
        updatePlayheadVisualOnly(timelinePlayheadSec);

        // Sync overlays (V3 depth title text & V2 video)
        syncProgramOverlays(timelinePlayheadSec);

        // Sync music
        syncMusicPlayback(false);

        playbackRafId = requestAnimationFrame(step);
    }

    playbackRafId = requestAnimationFrame(step);
}

function stepTimeline(seconds) {
    seekTimelinePlayhead(timelinePlayheadSec + seconds);
}

// ----------------- EXPORT TIMELINE / INSTAGRAM REEL / FAST EXPORT -----------------
async function exportTimelineSequenceFast(overrideRes = null) {
    if (activeTimelineClips.length === 0) {
        showToast("Timeline is empty! Load 10 clips first.", "warning");
        return;
    }

    const resSelect = document.getElementById("p-export-res-select");
    const chosenRes = overrideRes || (resSelect ? resSelect.value : "360p");

    showToast(`⚡ Fast Exporting Multi-Track Sequence (${chosenRes} in &lt;10s)...`, "info");

    const payload = {
        clips: activeTimelineClips.map(c => ({
            id: c.id,
            path: c.path,
            name: c.name,
            track: c.track,
            type: c.type || "video",
            in_point: c.in_point || 0.0,
            out_point: c.out_point || c.duration,
            duration: c.duration,
            speed: c.speed || 1.0,
            rotation: c.rotation || 0,
            scale: c.scale || 100,
            posY: c.posY || 0,
            opacity: c.opacity !== undefined ? c.opacity : 100,
            muted: !!c.muted,
            volume: c.volume !== undefined ? c.volume : 100,
            noise_suppression: c.noise_suppression !== undefined ? c.noise_suppression : 75,
            ducking: c.ducking !== undefined ? c.ducking : 75,
            text: c.text,
            font: c.font || "Montserrat"
        })),
        resolution: chosenRes,
        aspect_ratio: activeEditorAspectRatio,
        instagram_filter: activeInstagramFilter,
        title_text: document.getElementById("p-instagram-title-input") ? document.getElementById("p-instagram-title-input").value : "",
        caption_style: (document.getElementById("chk-burn-captions") && !document.getElementById("chk-burn-captions").checked) 
            ? "none" 
            : (typeof activeCaptionStyle !== "undefined" && activeCaptionStyle 
                ? activeCaptionStyle 
                : (document.getElementById("caption-style-select") ? document.getElementById("caption-style-select").value : "hyperframe_kinetic"))
    };

    try {
        const res = await fetch("/api/editor/export-sequence", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (data.status === "success") {
            showToast(`🚀 Fast Export Complete: ${data.filename}! Playing in Program Monitor.`, "success");

            const programVideo = document.getElementById("p-program-video");
            if (programVideo) {
                programVideo.src = data.url;
                programVideo.play();
            }

            await fetchEditorMediaPool();
            renderMediaBin("exported");

            showCompletionModal({
                duration: "Fast Export (<10s)",
                size: data.filename,
                filename: data.filename,
                url: data.url
            });
        } else {
            showToast("Export failed: " + (data.detail || "Error"), "error");
        }
    } catch (e) {
        console.error("Fast export error:", e);
        showToast("Error exporting timeline sequence", "error");
    }
}

async function exportTimelineSequence() {
    return exportTimelineSequenceFast("1080p");
}

async function exportPremiereProXmlProject() {
    const btn = document.getElementById("btn-export-premiere-xml");
    const origHtml = btn ? btn.innerHTML : "";
    
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<span class="spinner" style="display:inline-block;width:12px;height:12px;border:2px solid #c084fc;border-top-color:transparent;border-radius:50%;animation:spin 0.6s linear infinite;margin-right:4px;"></span> Exporting XML...`;
    }
    
    showToast("Generating Premiere Pro FCP-XML Sequence (4 Tracks: V1, V2, A1, A2)... 📁", "info");
    
    const depthTextInput = document.getElementById("depth-input-text");
    const titleText = (depthTextInput && depthTextInput.value.trim()) 
        ? depthTextInput.value.trim() 
        : ((typeof directorTextBehind !== "undefined" && directorTextBehind.text) ? directorTextBehind.text : "RANN OF KUTCH | BHUJ | SOMNATH VLOG");
        
    const payload = {
        clips: (activeTimelineClips && activeTimelineClips.length > 0) ? activeTimelineClips : null,
        title_text: titleText,
        aspect_ratio: (typeof activeEditorAspectRatio !== "undefined" && activeEditorAspectRatio) ? activeEditorAspectRatio : "16:9",
        ducking_depth_pct: (document.getElementById("slider-ducking-depth")) ? parseFloat(document.getElementById("slider-ducking-depth").value) : 75.0,
        music_track_name: "Airport_Lounge.mp3"
    };

    try {
        const res = await fetch("/api/editor/export-xml", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = origHtml;
        }

        if (data.status === "success") {
            showToast(`✓ Premiere Pro XML ready! (${data.clip_count} clips across V1, V2, V3, A1, A2)`, "success");
            
            // Trigger automatic download of PREMIERE_PRO_PROJECT.xml
            const link = document.createElement("a");
            link.href = data.xml_url;
            link.download = data.filename || "PREMIERE_PRO_PROJECT.xml";
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            // Open Stage 11 modal if present
            const modal = document.getElementById("stage11-xml-ready-modal");
            if (modal) {
                const fnameEl = document.getElementById("stage11-xml-filename");
                if (fnameEl) fnameEl.innerText = data.filename;
                const dlBtn = document.getElementById("stage11-xml-download-btn");
                if (dlBtn) dlBtn.href = data.xml_url;
                const dlSrt = document.getElementById("stage11-srt-download-btn");
                if (dlSrt) dlSrt.href = data.srt_url;
                modal.classList.add("open");
            }
        } else {
            showToast("Failed to export Premiere XML: " + (data.detail || "Error"), "error");
        }
    } catch (err) {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = origHtml;
        }
        console.error("XML Export failed:", err);
        showToast("Error exporting XML: " + err.message, "error");
    }
    if (window.feather) feather.replace();
}

// ----------------- KEYBOARD SHORTCUTS -----------------
window.addEventListener("keydown", (e) => {
    // Only if Premiere tab is active
    const pTab = document.getElementById("workspace-premiere");
    if (!pTab || !pTab.classList.contains("active")) return;

    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;

    // Multi-Step Undo / Redo Shortcuts
    if (e.ctrlKey || e.metaKey) {
        if (e.key.toLowerCase() === "z") {
            e.preventDefault();
            if (e.shiftKey) {
                redoTimelineAction();
            } else {
                undoTimelineAction();
            }
            return;
        } else if (e.key.toLowerCase() === "y") {
            e.preventDefault();
            redoTimelineAction();
            return;
        } else if (e.key.toLowerCase() === "a") {
            e.preventDefault();
            selectAllTimelineClips();
            return;
        }
    }

    if (e.key === " " || e.code === "Space") {
        e.preventDefault();
        toggleTimelinePlayback();
    } else if (e.key.toLowerCase() === "c") {
        setEditorTool("razor");
    } else if (e.key.toLowerCase() === "v") {
        setEditorTool("select");
    } else if (e.key === "Delete" || e.key === "Backspace") {
        if (selectedTimelineGap) {
            e.preventDefault();
            rippleDeleteGapAt(selectedTimelineGap.start, selectedTimelineGap.end, selectedTimelineGap.track);
        } else if (selectedTimelineClipIds && selectedTimelineClipIds.size > 0) {
            e.preventDefault();
            deleteSelectedTimelineClipsBatch();
        } else if (selectedTimelineClipIndex) {
            e.preventDefault();
            if (e.shiftKey) {
                rippleDeleteClip(selectedTimelineClipIndex);
            } else {
                deleteSelectedTimelineClip();
            }
        }
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
    const tabDir = document.getElementById("tab-bin-director");
    const tabMus = document.getElementById("tab-bin-music");

    const viewMedia = document.getElementById("p-bin-media-view");
    const viewFilters = document.getElementById("p-bin-filters-view");
    const viewDirector = document.getElementById("p-bin-director-view");
    const viewMusic = document.getElementById("p-bin-music-view");

    if (tabExp) tabExp.classList.toggle("active", tab === "exported");
    if (tabRaw) tabRaw.classList.toggle("active", tab === "raw");
    if (tabFlt) tabFlt.classList.toggle("active", tab === "filters");
    if (tabDir) tabDir.classList.toggle("active", tab === "director");
    if (tabMus) tabMus.classList.toggle("active", tab === "music");

    if (tab === "filters") {
        if (viewMedia) viewMedia.style.display = "none";
        if (viewFilters) viewFilters.style.display = "grid";
        if (viewDirector) viewDirector.style.display = "none";
        if (viewMusic) viewMusic.style.display = "none";
        renderInstagramFilters();
    } else if (tab === "director") {
        if (viewMedia) viewMedia.style.display = "none";
        if (viewFilters) viewFilters.style.display = "none";
        if (viewDirector) viewDirector.style.display = "block";
        if (viewMusic) viewMusic.style.display = "none";
        if (typeof renderMiniDirectorBin === "function") {
            renderMiniDirectorBin();
        }
    } else if (tab === "music") {
        if (viewMedia) viewMedia.style.display = "none";
        if (viewFilters) viewFilters.style.display = "none";
        if (viewDirector) viewDirector.style.display = "none";
        if (viewMusic) viewMusic.style.display = "block";
        renderMusicBin();
    } else {
        if (viewMedia) viewMedia.style.display = "flex";
        if (viewFilters) viewFilters.style.display = "none";
        if (viewDirector) viewDirector.style.display = "none";
        if (viewMusic) viewMusic.style.display = "none";
        renderMediaBin(tab);
    }
}

let currentPreviewAudio = null;
function previewMusicTrack(url, btnEl) {
    if (currentPreviewAudio && !currentPreviewAudio.paused) {
        currentPreviewAudio.pause();
        currentPreviewAudio.currentTime = 0;
        document.querySelectorAll(".music-preview-btn i").forEach(icon => {
            icon.setAttribute("data-feather", "play");
        });
        if (window.feather) feather.replace();
        if (currentPreviewAudio.src.endsWith(url)) {
            currentPreviewAudio = null;
            return;
        }
    }

    currentPreviewAudio = new Audio(url);
    currentPreviewAudio.volume = 0.5;
    currentPreviewAudio.play().then(() => {
        if (btnEl) {
            const icon = btnEl.querySelector("i");
            if (icon) icon.setAttribute("data-feather", "square");
            if (window.feather) feather.replace();
        }
    }).catch(err => console.log("Audio play failed:", err));

    currentPreviewAudio.onended = () => {
        if (btnEl) {
            const icon = btnEl.querySelector("i");
            if (icon) icon.setAttribute("data-feather", "play");
            if (window.feather) feather.replace();
        }
    };
}

function renderMusicBin() {
    const container = document.getElementById("p-media-bin-music");
    if (!container) return;

    const tracks = editorMediaPool.music_tracks || [];
    if (!tracks || tracks.length === 0) {
        container.innerHTML = `<div style="padding:18px; text-align:center; color:#64748b; font-size:12px;">No music tracks found in raw_input/MUSIC.</div>`;
        return;
    }

    const currentA2 = activeTimelineClips.find(c => c.track === "A2");
    const currentA2Name = currentA2 ? currentA2.name.replace("Music: ", "").trim() : "";

    container.innerHTML = tracks.map(tr => {
        const isActive = (tr.name === currentA2Name || tr.title === currentA2Name);
        return `
            <div class="music-bin-item ${isActive ? 'active' : ''}" id="music-bin-item-${tr.name.replace(/[^a-zA-Z0-9]/g, '_')}">
                <div class="music-bin-left">
                    <button class="music-preview-btn" onclick="previewMusicTrack('${tr.url}', this)" title="Preview Track">
                        <i data-feather="play"></i>
                    </button>
                    <div class="media-bin-info">
                        <div class="media-bin-name" title="${tr.name}">
                            ${isActive ? '🎵 <strong>' : ''}${tr.title}${isActive ? ' (Active)</strong>' : ''}
                        </div>
                        <div class="media-bin-meta">
                            <span><i data-feather="clock"></i> ${formatTimecode(tr.duration || 0)}</span>
                            <span><i data-feather="hard-drive"></i> ${tr.size_mb || 0} MB</span>
                        </div>
                    </div>
                </div>
                <div class="music-bin-actions">
                    <button class="btn btn-sm" onclick="changeSelectedMusicTrack('${tr.name}')" style="background:#4c1d95; color:#c084fc; border:1px solid #7c3aed; padding:3px 7px; font-size:11px; border-radius:4px; cursor:pointer;" title="Set as Main Music Track on A2">
                        Set Active
                    </button>
                    <button class="music-add-btn" onclick="addAnotherMusicClipAtPlayhead('${tr.name}')" title="Insert at Playhead (${formatTimecode(timelinePlayheadSec)})">
                        <i data-feather="plus"></i> Add
                    </button>
                </div>
            </div>
        `;
    }).join("");

    if (window.feather) feather.replace();
}

function changeSelectedMusicTrack(filename) {
    pushTimelineHistory("Change Music Track");
    let targetClip = activeTimelineClips.find(c => c.id === selectedTimelineClipIndex && c.track === "A2");
    if (!targetClip) {
        targetClip = activeTimelineClips.find(c => c.track === "A2");
    }

    if (!targetClip) {
        targetClip = {
            id: `a2_music_${Date.now()}`,
            name: `Music: ${filename}`,
            path: filename,
            url: `/media_raw/MUSIC/${filename}`,
            track: "A2",
            type: "audio_music",
            timeline_start: 0.0,
            in_point: 0.0,
            out_point: 60.0,
            duration: 60.0,
            volume: 40,
            ducking: 75,
            muted: false,
            solo: false
        };
        activeTimelineClips.push(targetClip);
    } else {
        targetClip.name = `Music: ${filename}`;
        targetClip.path = filename;
        targetClip.url = `/media_raw/MUSIC/${filename}`;
    }

    const musicPlayer = document.getElementById("p-timeline-music-player");
    if (musicPlayer) {
        musicPlayer.src = targetClip.url;
        if (isTimelinePlaying) {
            musicPlayer.currentTime = Math.max(0, timelinePlayheadSec - targetClip.timeline_start);
            musicPlayer.play().catch(() => {});
        }
    }

    renderTimelineTracks();
    if (selectedTimelineClipIndex === targetClip.id) {
        selectTimelineClip(targetClip.id);
    }
    renderMusicBin();
    showToast(`Switched music track to "${filename}" 🎵`, "success");
}

function extendMusicToSequenceEnd() {
    pushTimelineHistory("Extend Music to End");
    let clip = activeTimelineClips.find(c => c.id === selectedTimelineClipIndex && c.track === "A2");
    if (!clip) {
        clip = activeTimelineClips.find(c => c.track === "A2");
    }
    if (!clip) {
        showToast("No music track found on A2!", "warning");
        return;
    }

    const v1Clips = activeTimelineClips.filter(c => c.track === "V1" || c.track === "A1");
    let maxEnd = 0.0;
    v1Clips.forEach(c => {
        const cEnd = c.timeline_start + c.duration;
        if (cEnd > maxEnd) maxEnd = cEnd;
    });

    if (maxEnd <= 0) maxEnd = 60.0;
    const newDur = Math.max(clip.duration, maxEnd - clip.timeline_start);
    clip.duration = newDur;
    clip.out_point = newDur;

    renderTimelineTracks();
    showToast(`Music extended to sequence end (${formatTimecode(maxEnd)}) 🎶`, "success");
}

function addAnotherMusicClipAtPlayhead(optionalTrackName = null) {
    pushTimelineHistory("Add Music Clip");
    const tracks = editorMediaPool.music_tracks || [];
    let chosenName = optionalTrackName;
    if (!chosenName) {
        if (tracks.length > 0) {
            chosenName = tracks[Math.floor(Math.random() * tracks.length)].name;
        } else {
            chosenName = "Airport_Lounge.mp3";
        }
    }

    const matched = tracks.find(t => t.name === chosenName);
    const dur = (matched && matched.duration > 0) ? Math.min(matched.duration, 30.0) : 30.0;

    const newClip = {
        id: `a2_music_${Date.now()}`,
        name: `Music: ${chosenName}`,
        path: chosenName,
        url: `/media_raw/MUSIC/${chosenName}`,
        track: "A2",
        type: "audio_music",
        timeline_start: Math.round(timelinePlayheadSec * 100) / 100,
        in_point: 0.0,
        out_point: dur,
        duration: dur,
        volume: 40,
        ducking: 75,
        muted: false,
        solo: false
    };

    activeTimelineClips.push(newClip);
    renderTimelineTracks();
    selectTimelineClip(newClip.id);
    renderMusicBin();
    showToast(`Added '${chosenName}' to A2 at ${formatTimecode(timelinePlayheadSec)} 🎵`, "success");
}

function switchEditorSubTab(subTab) {
    activeEditorWorkspace = subTab;
    document.querySelectorAll(".p-nav-btn").forEach(btn => btn.classList.remove("active"));
    if (window.event && window.event.currentTarget) {
        window.event.currentTarget.classList.add("active");
    }

    if (subTab === "color") {
        setBinTab("filters");
        setLeftUpperTab("stickers");
        showToast("🎨 Workspace: Color & Instagram Filters", "info");
    } else if (subTab === "effects") {
        setLeftUpperTab("effects");
        showToast("⚡ Workspace: Effect Controls & Motion", "info");
    } else if (subTab === "editing") {
        setLeftUpperTab("source");
        setBinTab("exported");
        showToast("🎬 Workspace: Main NLE Editing", "info");
    } else if (subTab === "audio") {
        setLeftUpperTab("source");
        showToast("🔊 Workspace: Multi-Track Audio Mixing", "info");
    }
}

// ----------------- INSTAGRAM LIVE STICKERS & TEXT -----------------
function updateLiveInstagramTitle(text) {
    const banner = document.getElementById("p-ig-live-text-banner");
    if (!banner) return;
    if (text && text.trim().length > 0) {
        banner.innerText = text;
        banner.style.display = "block";
    } else {
        banner.style.display = "none";
    }
}

function addInstagramStickerText(sticker) {
    const input = document.getElementById("p-instagram-title-input");
    if (!input) return;
    input.value += sticker;
    updateLiveInstagramTitle(input.value);
    showToast(`Sticker added: ${sticker.trim()}`, "info");
}

// ----------------- TRACK LOCK / MUTE / SOLO CONTROLLER -----------------
let trackStates = {
    V3: { lock: false, mute: false },
    V2: { lock: false, mute: false },
    V1: { lock: false, mute: false },
    A1: { mute: false, solo: false },
    A2: { mute: false, solo: false }
};

function toggleTrackLock(trk) {
    if (!trackStates[trk]) trackStates[trk] = {};
    trackStates[trk].lock = !trackStates[trk].lock;
    const btn = document.getElementById(`trk-btn-lock-${trk}`);
    if (btn) btn.classList.toggle("active", trackStates[trk].lock);
    showToast(`Track ${trk} ${trackStates[trk].lock ? "Locked 🔒" : "Unlocked 🔓"}`, "info");
}

function toggleTrackMute(trk) {
    if (!trackStates[trk]) trackStates[trk] = {};
    trackStates[trk].mute = !trackStates[trk].mute;
    const btn = document.getElementById(`trk-btn-mute-${trk}`);
    if (btn) btn.classList.toggle("active", trackStates[trk].mute);
    showToast(`Track ${trk} ${trackStates[trk].mute ? "Muted 🔇" : "Unmuted 🔊"}`, "info");
}

function toggleTrackSolo(trk) {
    if (!trackStates[trk]) trackStates[trk] = {};
    trackStates[trk].solo = !trackStates[trk].solo;
    const btn = document.getElementById(`trk-btn-solo-${trk}`);
    if (btn) btn.classList.toggle("active", trackStates[trk].solo);
    showToast(`Track ${trk} ${trackStates[trk].solo ? "Solo Active 🎧" : "Solo Off"}`, "info");
}

// ----------------- INTERACTIVE TIMELINE TRIMMING -----------------
let isTrimming = false;
let trimClipId = null;
let trimEdge = null;
let trimStartX = 0;
let trimOrigIn = 0;
let trimOrigOut = 0;
let trimOrigStart = 0;

function startClipTrim(e, clipId, edge) {
    e.stopPropagation();
    e.preventDefault();
    const clip = activeTimelineClips.find(c => c.id === clipId);
    if (!clip) return;

    pushTimelineHistory("Trim Clip");
    isTrimming = true;
    trimClipId = clipId;
    trimEdge = edge;
    trimStartX = e.clientX;
    trimOrigIn = clip.in_point || 0;
    trimOrigOut = clip.out_point || clip.duration;
    trimOrigStart = clip.timeline_start || 0;

    document.addEventListener("mousemove", onClipTrimMove);
    document.addEventListener("mouseup", onClipTrimEnd);
}

function onClipTrimMove(e) {
    if (!isTrimming) return;
    const clip = activeTimelineClips.find(c => c.id === trimClipId);
    if (!clip) return;

    const deltaPx = e.clientX - trimStartX;
    const deltaSec = deltaPx / timelineZoomPxPerSec;

    if (trimEdge === "left") {
        const newIn = Math.max(0, trimOrigIn + deltaSec);
        const shiftSec = newIn - trimOrigIn;
        if (trimOrigOut - newIn >= 0.5) {
            clip.in_point = newIn;
            clip.timeline_start = trimOrigStart + shiftSec;
            clip.duration = clip.out_point - clip.in_point;
        }
    } else if (trimEdge === "right") {
        const newOut = Math.max((clip.in_point || 0) + 0.5, trimOrigOut + deltaSec);
        clip.out_point = newOut;
        clip.duration = clip.out_point - (clip.in_point || 0);
    }

    renderTimelineTracks();
}

function onClipTrimEnd(e) {
    if (!isTrimming) return;
    isTrimming = false;
    document.removeEventListener("mousemove", onClipTrimMove);
    document.removeEventListener("mouseup", onClipTrimEnd);
    const clip = activeTimelineClips.find(c => c.id === trimClipId);
    if (clip) {
        showToast(`Clip '${clip.name}' trimmed to ${clip.duration.toFixed(1)}s`, "info");
    }
}

// ----------------- INTERACTIVE TIMELINE CLIP DRAGGING & SNAPPING -----------------
let isDraggingClip = false;
let dragClipId = null;
let dragStartX = 0;
let dragOrigStart = 0;
let hasDragged = false;
let dragPreState = null;

function startClipDrag(e, clipId) {
    if (e.button !== 0) return; // Only left-click drags
    if (activeEditorTool === "razor") return; // Razor cut tool has its own click action

    const clip = activeTimelineClips.find(c => c.id === clipId);
    if (!clip) return;

    dragPreState = captureTimelineState("Move Clip");
    isDraggingClip = true;
    hasDragged = false;
    dragClipId = clipId;
    dragStartX = e.clientX;
    dragOrigStart = clip.timeline_start;

    // Keep DOM intact on mousedown so click events and focus are not destroyed
    document.addEventListener("mousemove", onClipDragMove);
    document.addEventListener("mouseup", onClipDragEnd);
}

function onClipDragMove(e) {
    if (!isDraggingClip) return;
    const deltaX = e.clientX - dragStartX;
    if (Math.abs(deltaX) > 3) {
        hasDragged = true;
    }

    const clip = activeTimelineClips.find(c => c.id === dragClipId);
    if (!clip) return;

    const deltaSec = deltaX / timelineZoomPxPerSec;
    let newStartSec = Math.max(0, dragOrigStart + deltaSec);

    // Magnetic Snapping thresholds (~18px snap radius)
    const snapThresholdSec = 18.0 / timelineZoomPxPerSec;
    let isSnapped = false;

    // 1. Snap to 0:00 (Beginning of Timeline)
    if (newStartSec <= snapThresholdSec) {
        newStartSec = 0.0;
        isSnapped = true;
    }

    // 2. Snap to Playhead
    if (Math.abs(newStartSec - timelinePlayheadSec) <= snapThresholdSec) {
        newStartSec = timelinePlayheadSec;
        isSnapped = true;
    }

    // 3. Snap to adjacent clips on the same track
    const otherClips = activeTimelineClips.filter(c => c.id !== dragClipId && c.track === clip.track);
    for (const oc of otherClips) {
        const ocEnd = oc.timeline_start + oc.duration;
        if (Math.abs(newStartSec - ocEnd) <= snapThresholdSec) {
            newStartSec = ocEnd;
            isSnapped = true;
            break;
        }
        const clipEnd = newStartSec + clip.duration;
        if (Math.abs(clipEnd - oc.timeline_start) <= snapThresholdSec) {
            newStartSec = Math.max(0, oc.timeline_start - clip.duration);
            isSnapped = true;
            break;
        }
    }

    clip.timeline_start = newStartSec;

    // Live visual position & snapping border highlight
    const clipEl = document.getElementById(`timeline-clip-${clip.id}`);
    if (clipEl) {
        clipEl.style.left = `${newStartSec * timelineZoomPxPerSec}px`;
        clipEl.style.boxShadow = isSnapped ? "0 0 14px #38bdf8, 0 0 4px #fff" : "0 0 8px rgba(251, 191, 36, 0.6)";
        clipEl.style.borderColor = isSnapped ? "#38bdf8" : "#fbbf24";
    }
}

function onClipDragEnd(e) {
    if (!isDraggingClip) return;
    isDraggingClip = false;
    document.removeEventListener("mousemove", onClipDragMove);
    document.removeEventListener("mouseup", onClipDragEnd);

    const clip = activeTimelineClips.find(c => c.id === dragClipId);
    if (clip) {
        if (!hasDragged) {
            // Clean click without drag: immediately select the clip and open Effect Controls!
            dragPreState = null;
            selectTimelineClip(clip.id);
        } else {
            if (dragPreState) {
                if (timelineHistoryStack.length >= 50) timelineHistoryStack.shift();
                timelineHistoryStack.push(dragPreState);
                timelineRedoStack = [];
                updateUndoRedoButtons();
                dragPreState = null;
            }
            renderTimelineTracks();
            syncProgramMonitorToPlayhead();
            showToast(`Clip positioned at ${formatEditorTimecode(clip.timeline_start)} 🧲`, "info");
        }
    }
}

// ----------------- PREMIERE PRO RIGHT-CLICK CONTEXT MENU -----------------
function showClipContextMenu(e, clipId) {
    e.preventDefault();
    e.stopPropagation();

    selectedTimelineClipIndex = clipId;
    renderTimelineTracks();

    const clip = activeTimelineClips.find(c => c.id === clipId);
    if (!clip) return;

    removeContextMenu();

    const menu = document.createElement("div");
    menu.id = "p-context-menu";
    menu.className = "premiere-context-menu";
    menu.style.left = `${Math.min(window.innerWidth - 230, e.clientX)}px`;
    menu.style.top = `${Math.min(window.innerHeight - 280, e.clientY)}px`;

    menu.innerHTML = `
        <div class="premiere-menu-item" onclick="toggleClipMute('${clip.id}')">
            <span>${clip.muted ? '🔊 Unmute Clip' : '🔇 Mute Clip'}</span>
        </div>
        <div class="premiere-menu-item" onclick="moveSelectedClipTrackUp()">
            <span>⬆️ Move Track Up</span>
        </div>
        <div class="premiere-menu-item" onclick="moveSelectedClipTrackDown()">
            <span>⬇️ Move Track Down</span>
        </div>
        <div class="premiere-menu-divider"></div>
        <div class="premiere-menu-item" onclick="snapClipToBeginning('${clip.id}')">
            <span>⚡ Snap to Beginning (0:00)</span>
        </div>
        <div class="premiere-menu-item" onclick="rippleDeleteLeadingGap('${clip.id}')">
            <span>✂️ Ripple Delete Gap to 0:00</span>
        </div>
        <div class="premiere-menu-item" onclick="closeGapToPrevious('${clip.id}')">
            <span>🧲 Close Gap to Previous Clip</span>
        </div>
        <div class="premiere-menu-divider"></div>
        <div class="premiere-menu-item" onclick="executeRazorCutAtPlayhead()">
            <span>✂️ Split at Playhead (C)</span>
        </div>
        <div class="premiere-menu-item" onclick="duplicateTimelineClip('${clip.id}')">
            <span>📋 Duplicate Clip</span>
        </div>
        <div class="premiere-menu-divider"></div>
        <div class="premiere-menu-item" style="color:#38bdf8;" onclick="rippleDeleteClip('${clip.id}')">
            <span>✂️ Ripple Delete Clip (Shift+Del)</span>
        </div>
        <div class="premiere-menu-item danger" onclick="deleteSelectedTimelineClip()">
            <span>🗑️ Delete Clip (Del - Leaves Gap)</span>
        </div>
    `;

    document.body.appendChild(menu);

    setTimeout(() => {
        document.addEventListener("click", removeContextMenu, { once: true });
        document.addEventListener("contextmenu", removeContextMenu, { once: true });
    }, 50);
}

function showTimelineTrackContextMenu(e) {
    if (e.target.closest(".timeline-clip-block")) return;
    if (e.target.closest(".timeline-gap-block")) return;
    e.preventDefault();

    removeContextMenu();

    const trackElem = e.target.closest(".track-content");
    const trackId = trackElem ? trackElem.id.replace("track-content-", "") : "V1";
    const rect = trackElem ? trackElem.getBoundingClientRect() : e.currentTarget.getBoundingClientRect();
    const clickSec = Math.max(0, (e.clientX - rect.left) / timelineZoomPxPerSec);

    const clipsOnTrack = activeTimelineClips.filter(c => c.track === trackId).sort((a, b) => a.timeline_start - b.timeline_start);
    let gapFound = null;

    if (clipsOnTrack.length > 0) {
        if (clickSec < clipsOnTrack[0].timeline_start) {
            gapFound = { start: 0.0, end: clipsOnTrack[0].timeline_start };
        } else {
            for (let i = 0; i < clipsOnTrack.length - 1; i++) {
                const cEnd = clipsOnTrack[i].timeline_start + clipsOnTrack[i].duration;
                const nStart = clipsOnTrack[i + 1].timeline_start;
                if (cEnd < nStart && clickSec >= cEnd && clickSec <= nStart) {
                    gapFound = { start: cEnd, end: nStart };
                    break;
                }
            }
        }
    }

    const menu = document.createElement("div");
    menu.id = "p-context-menu";
    menu.className = "premiere-context-menu";
    menu.style.left = `${Math.min(window.innerWidth - 240, e.clientX)}px`;
    menu.style.top = `${Math.min(window.innerHeight - 200, e.clientY)}px`;

    let rippleItemHtml = "";
    if (gapFound) {
        const gapDur = gapFound.end - gapFound.start;
        rippleItemHtml = `
            <div class="premiere-menu-item" style="color:#38bdf8; font-weight:700;" onclick="rippleDeleteGapAt(${gapFound.start}, ${gapFound.end}, '${trackId}')">
                <span>✂️ Ripple Delete (${gapDur.toFixed(1)}s Gap)</span>
            </div>
            <div class="premiere-menu-divider"></div>
        `;
    }

    menu.innerHTML = `
        ${rippleItemHtml}
        <div class="premiere-menu-item" onclick="rippleDeleteAllTimelineGaps()">
            <span>⚡ Close All Sequence Gaps 🧲</span>
        </div>
        <div class="premiere-menu-item" onclick="autoPopulateInitialTimeline()">
            <span>🔄 Reset Sequence to Beginning</span>
        </div>
        <div class="premiere-menu-divider"></div>
        <div class="premiere-menu-item" onclick="seekTimelinePlayhead(${clickSec.toFixed(2)}); removeContextMenu();">
            <span>⏮️ Move Playhead Here (${formatEditorTimecode(clickSec)})</span>
        </div>
    `;

    document.body.appendChild(menu);

    setTimeout(() => {
        document.addEventListener("click", removeContextMenu, { once: true });
        document.addEventListener("contextmenu", removeContextMenu, { once: true });
    }, 50);
}

function removeContextMenu() {
    const existing = document.getElementById("p-context-menu");
    if (existing) existing.remove();
}

function snapClipToBeginning(clipId) {
    removeContextMenu();
    const clip = activeTimelineClips.find(c => c.id === clipId);
    if (!clip) return;

    const oldStart = clip.timeline_start;
    const shiftSec = oldStart - 0.0;
    clip.timeline_start = 0.0;

    // Shift all subsequent clips on the same track
    activeTimelineClips.forEach(c => {
        if (c.track === clip.track && c.id !== clip.id && c.timeline_start > oldStart) {
            c.timeline_start = Math.max(0, c.timeline_start - shiftSec);
        }
    });

    renderTimelineTracks();
    seekTimelinePlayhead(0.0);
    showToast(`⚡ Snapped '${clip.name}' to 00:00:00:00!`, "success");
}

function rippleDeleteLeadingGap(clipId) {
    removeContextMenu();
    const clip = activeTimelineClips.find(c => c.id === clipId);
    if (!clip) return;

    const gapSec = clip.timeline_start;
    if (gapSec <= 0.05) {
        showToast("Clip is already at 0:00!", "info");
        return;
    }

    // Shift all clips on this track left by gapSec
    activeTimelineClips.forEach(c => {
        if (c.track === clip.track) {
            c.timeline_start = Math.max(0, c.timeline_start - gapSec);
        }
    });

    renderTimelineTracks();
    seekTimelinePlayhead(0.0);
    showToast(`✂️ Ripple deleted ${gapSec.toFixed(1)}s gap! Snapped to 0:00 🧲`, "success");
}

function closeGapToPrevious(clipId) {
    removeContextMenu();
    const clip = activeTimelineClips.find(c => c.id === clipId);
    if (!clip) return;

    const prevClips = activeTimelineClips.filter(c => c.track === clip.track && c.timeline_start < clip.timeline_start);
    if (prevClips.length === 0) {
        snapClipToBeginning(clipId);
        return;
    }

    prevClips.sort((a, b) => (b.timeline_start + b.duration) - (a.timeline_start + a.duration));
    const lastPrev = prevClips[0];
    const targetStart = lastPrev.timeline_start + lastPrev.duration;

    const oldStart = clip.timeline_start;
    const shiftSec = oldStart - targetStart;
    clip.timeline_start = targetStart;

    activeTimelineClips.forEach(c => {
        if (c.track === clip.track && c.id !== clip.id && c.timeline_start > oldStart) {
            c.timeline_start = Math.max(0, c.timeline_start - shiftSec);
        }
    });

    renderTimelineTracks();
    seekTimelinePlayhead(targetStart);
    showToast(`🧲 Closed gap! Snapped to ${formatEditorTimecode(targetStart)}`, "success");
}

function duplicateTimelineClip(clipId) {
    removeContextMenu();
    const clip = activeTimelineClips.find(c => c.id === clipId);
    if (!clip) return;

    const newClip = {
        ...clip,
        id: `clip_${Date.now()}`,
        timeline_start: clip.timeline_start + clip.duration
    };
    activeTimelineClips.push(newClip);
    renderTimelineTracks();
    showToast(`📋 Duplicated '${clip.name}'`, "success");
}

function rippleDeleteAllTimelineGaps() {
    removeContextMenu();
    if (activeTimelineClips.length === 0) return;

    // Pack all clips on V1 and keep linked A1 synchronized
    const v1Clips = activeTimelineClips.filter(c => c.track === "V1").sort((a, b) => a.timeline_start - b.timeline_start);
    if (v1Clips.length === 0) return;

    let currentHead = 0.0;
    v1Clips.forEach(clip => {
        const origStart = clip.timeline_start;
        clip.timeline_start = currentHead;

        const matchedA1 = activeTimelineClips.find(c => c.track === "A1" && Math.abs(c.timeline_start - origStart) < 0.1);
        if (matchedA1) {
            matchedA1.timeline_start = currentHead;
        }

        currentHead += clip.duration;
    });

    selectedTimelineGap = null;
    renderTimelineTracks();
    seekTimelinePlayhead(0.0);
    showToast("⚡ All timeline gaps closed! Sequence packed seamlessly 🧲", "success");
}

function pad(num) {
    return String(Math.floor(num)).padStart(2, '0');
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

// Explicit Window Bindings for Inline HTML Event Handlers
window.load10ClipsMultiTrackSequence = load10ClipsMultiTrackSequence;
window.autoPopulateInitialTimeline = autoPopulateInitialTimeline;
window.exportTimelineSequenceFast = exportTimelineSequenceFast;
window.exportTimelineSequence = exportTimelineSequence;
window.exportPremiereProXmlProject = exportPremiereProXmlProject;
window.toggleTimelinePlayback = toggleTimelinePlayback;
window.seekTimelinePlayhead = seekTimelinePlayhead;
window.selectTimelineClip = selectTimelineClip;
window.selectTimelineGap = selectTimelineGap;
window.showGapContextMenu = showGapContextMenu;
window.rippleDeleteGapAt = rippleDeleteGapAt;
window.rippleDeleteClip = rippleDeleteClip;
window.toggleClipMute = toggleClipMute;
window.toggleSelectedClipMute = toggleSelectedClipMute;
window.moveSelectedClipTrackUp = moveSelectedClipTrackUp;
window.moveSelectedClipTrackDown = moveSelectedClipTrackDown;
window.updateSelectedVoiceVolume = updateSelectedVoiceVolume;
window.updateSelectedNoiseSuppression = updateSelectedNoiseSuppression;
window.updateSelectedMusicVolume = updateSelectedMusicVolume;
window.updateSelectedMusicDucking = updateSelectedMusicDucking;
window.updateSelectedTitleText = updateSelectedTitleText;
window.updateSelectedTitleFont = updateSelectedTitleFont;
window.updateSelectedTitleGlow = updateSelectedTitleGlow;
window.updateSelectedTitlePosY = updateSelectedTitlePosY;
window.updateSelectedTitleScale = updateSelectedTitleScale;
window.saveSelectedTitleClip = saveSelectedTitleClip;
window.switchStudioTab = switchStudioTab;
window.setLeftUpperTab = setLeftUpperTab;
window.setBinTab = setBinTab;
window.setEditorTool = setEditorTool;
window.setEditorAspect = setEditorAspect;
window.selectInstagramFilter = selectInstagramFilter;
window.updateSelectedClipScale = updateSelectedClipScale;
window.updateSelectedClipPosY = updateSelectedClipPosY;
window.updateSelectedClipOpacity = updateSelectedClipOpacity;
window.updateSelectedClipRotation = updateSelectedClipRotation;
window.setClipRotationPreset = setClipRotationPreset;
window.bakeSelectedTimelineClipMaster = bakeSelectedTimelineClipMaster;
window.updateSelectedClipSpeed = updateSelectedClipSpeed;
window.deleteSelectedTimelineClip = deleteSelectedTimelineClip;
window.rippleDeleteAllTimelineGaps = rippleDeleteAllTimelineGaps;
window.startClipDrag = startClipDrag;
window.startClipTrim = startClipTrim;
window.stepTimeline = stepTimeline;
window.undoTimelineAction = undoTimelineAction;
window.redoTimelineAction = redoTimelineAction;
window.renderMusicBin = renderMusicBin;
window.previewMusicTrack = previewMusicTrack;
window.changeSelectedMusicTrack = changeSelectedMusicTrack;
window.extendMusicToSequenceEnd = extendMusicToSequenceEnd;
window.addAnotherMusicClipAtPlayhead = addAnotherMusicClipAtPlayhead;
window.alignProgramMonitorLayers = alignProgramMonitorLayers;
window.renderForegroundPersonCutout = renderForegroundPersonCutout;
window.selectAllTimelineClips = selectAllTimelineClips;
window.clearTimeline = clearTimeline;
window.deleteSelectedTimelineClipsBatch = deleteSelectedTimelineClipsBatch;
window.loadNClipsMultiTrackSequence = loadNClipsMultiTrackSequence;
window.loadSelectedClipsToTimeline = loadSelectedClipsToTimeline;
window.getActiveTimelineClips = () => activeTimelineClips;
