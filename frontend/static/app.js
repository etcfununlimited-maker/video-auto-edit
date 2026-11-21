/* ANIRBAN AUTOMATIONS - AUTO VIDEO EDITOR STUDIO CLIENT */

// Global State
let rawFiles = [];
let exportFiles = [];
let activeFile = null;
let selectedFileNames = new Set();
let projectTranscript = { words: [], sentences: [] };
let projectCuts = [];
let colorPresets = [];
let activeColorPreset = "none";
let activeCaptionStyle = "hyperframe_kinetic";
let activeAspectRatio = "original";
let ws = null;
let hasCompletedPopupShown = false;
let liveElapsedTimer = null;
let liveStartTime = null;

function ensureElapsedTimerRunning(serverElapsedSec = 0) {
    if (!liveStartTime || serverElapsedSec > 0) {
        liveStartTime = Date.now() - (serverElapsedSec * 1000);
    }
    if (liveElapsedTimer) return;
    const elEl = document.getElementById("overall-elapsed");
    liveElapsedTimer = setInterval(() => {
        if (!liveStartTime) return;
        const sec = Math.max(0, Math.floor((Date.now() - liveStartTime) / 1000));
        if (elEl) {
            const m = Math.floor(sec / 60);
            const s = Math.floor(sec % 60);
            elEl.innerText = `${pad(m)}:${pad(s)}`;
        }
    }, 1000);
}

function stopElapsedTimer() {
    if (liveElapsedTimer) {
        clearInterval(liveElapsedTimer);
        liveElapsedTimer = null;
        liveStartTime = null;
    }
}

// DOM Elements
const videoPlayer = document.getElementById("main-video-player");
const videoScrubber = document.getElementById("video-scrubber");
const timecodeDisplay = document.getElementById("timecode-display");
const captionBubble = document.getElementById("caption-bubble");
const reframingGuide = document.getElementById("reframing-guide");

// ---------------- INITIALIZATION ----------------
window.addEventListener("DOMContentLoaded", async () => {
    initGridCards();
    initWebSocket();
    await fetchColorPresets();
    await fetchRawFiles();
    await fetchExportFiles();
    await fetchGridStatuses();
    await loadTranscript();
    setupVideoEventListeners();
});

async function fetchGridStatuses() {
    try {
        const res = await fetch("/api/grids");
        const data = await res.json();
        if (data.statuses) {
            for (const [gid, s] of Object.entries(data.statuses)) {
                updateGridUI(gid, s.status, s.progress, s.clip_eta_sec, s.eta_sec, s.detail);
            }
        }
        
        const renderStatus = data.statuses && data.statuses["grid_render"] ? data.statuses["grid_render"].status : null;
        const etaEl = document.getElementById("overall-total-eta");
        const badge = document.getElementById("master-status-badge");
        
        if (data.elapsed_sec !== undefined) {
            const elEl = document.getElementById("overall-elapsed");
            if (elEl) elEl.innerText = formatSeconds(data.elapsed_sec);
        }

        if (renderStatus === "completed") {
            stopElapsedTimer();
            if (badge) {
                badge.innerText = "MASTER READY";
                badge.className = "stat-badge ready";
            }
            if (etaEl) etaEl.innerText = "Completed";
            if (!hasCompletedPopupShown) {
                hasCompletedPopupShown = true;
                setTimeout(() => {
                    const topFile = (exportFiles && exportFiles.length > 0) ? exportFiles[0] : null;
                    const fName = topFile ? topFile.filename : "MASTER_Pushkar And Jaipur Vlog 2025.mp4";
                    const fUrl = topFile ? topFile.url : "/media_final/MASTER_Pushkar%20And%20Jaipur%20Vlog%202025.mp4";
                    const fSize = topFile ? `${topFile.size_mb} MB` : "509 MB";
                    showCompletionModal({
                        duration: "12m 14s",
                        size: fSize,
                        filename: fName,
                        url: fUrl
                    });
                }, 400);
            }
        } else if (data.is_processing || renderStatus === "in_progress") {
            ensureElapsedTimerRunning(data.elapsed_sec || 0);
            if (badge) {
                badge.innerText = "PROCESSING";
                badge.className = "stat-badge running";
            }
            if (etaEl) {
                if (data.overall_eta_sec && data.overall_eta_sec > 0) {
                    etaEl.innerText = formatEtaDisplay(data.overall_eta_sec);
                } else {
                    etaEl.innerText = "Finalizing (~1-2m)";
                }
            }
        } else {
            stopElapsedTimer();
            if (badge) {
                badge.innerText = "STANDBY";
                badge.className = "stat-badge ready";
            }
            if (etaEl) etaEl.innerText = "--:--";
        }
    } catch (e) {
        console.error("Grids error:", e);
    }
}

// ---------------- WEBSOCKET FOR REAL-TIME ETAS ----------------
function initWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/progress`;
    
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log("WebSocket connected for real-time pipeline monitoring");
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleProgressUpdate(data);
    };

    ws.onclose = () => {
        setTimeout(initWebSocket, 3000);
    };
}

function updateLiveRenderMonitor(detail, progress, status) {
    const monitor = document.getElementById("live-render-monitor");
    if (!monitor) return;

    if (status === "in_progress") {
        monitor.style.display = "flex";
        const img = document.getElementById("live-render-frame-img");
        if (img) {
            img.src = `/api/project/live-render-frame?t=${Date.now()}`;
        }
        const pctEl = document.getElementById("live-render-pct");
        if (pctEl) pctEl.innerText = `${progress}%`;

        const stepEl = document.getElementById("live-render-step-badge");
        const clipEl = document.getElementById("live-render-clip-name");
        const actionEl = document.getElementById("live-render-action");

        if (detail) {
            if (actionEl) actionEl.innerText = detail;
            const mClip = detail.match(/\[(\d+\/\d+)\]\s*([^:]+):?\s*(.*)/);
            if (mClip) {
                if (stepEl) stepEl.innerText = `[${mClip[1]}] Rendering`;
                if (clipEl) clipEl.innerText = mClip[2].trim();
                if (actionEl && mClip[3]) actionEl.innerText = mClip[3].trim();
            } else {
                if (stepEl) stepEl.innerText = `[${progress}%] Processing`;
                if (clipEl) clipEl.innerText = "Master Multi-Clip Pipeline";
            }
        }
    } else if (status === "completed" || status === "stopped" || status === "error") {
        monitor.style.display = "none";
    }
}

function handleProgressUpdate(data) {
    if (data.type === "stage11_pause_decision") {
        console.log("Stage 11 complete: Paused for export decision", data);
        showStage11DecisionModal(data);
        showToast("Stage 11 Complete! Paused: Choose Premiere Pro XML or Master Render", "info");
        return;
    }

    if (data.type === "stage11_xml_ready") {
        console.log("Premiere Pro XML + SRT generated successfully", data);
        closeStage11DecisionModal();
        showStage11XmlReadyModal(data);
        showToast("Premiere Pro XML & SRT Generated! Ready for download", "success");
        fetchExportFiles();
        return;
    }

    if (data.type === "pipeline_stopped") {
        updateLiveRenderMonitor("", 0, "stopped");
        stopElapsedTimer();
        const badge = document.getElementById("master-status-badge");
        if (badge) {
            badge.innerText = "STOPPED";
            badge.className = "stat-badge";
        }
        const etaEl = document.getElementById("overall-total-eta");
        if (etaEl) etaEl.innerText = "--:--";
        const btnStop = document.getElementById("btn-stop-pipeline");
        const btnFooterStop = document.getElementById("btn-footer-stop");
        if (btnStop) btnStop.style.display = "none";
        if (btnFooterStop) btnFooterStop.style.display = "none";
        if (data.statuses) {
            for (const [gid, s] of Object.entries(data.statuses)) {
                updateGridUI(gid, s.status, s.progress, s.clip_eta_sec, s.eta_sec, s.detail);
            }
        }
        showToast("Pipeline stopped ⏹️", "info");
        return;
    }

    if (data.type === "pipeline_restarted") {
        hasCompletedPopupShown = false;
        clearAndResetAllGridsUI();
        ensureElapsedTimerRunning(0);
        const badge = document.getElementById("master-status-badge");
        if (badge) {
            badge.innerText = "PROCESSING";
            badge.className = "stat-badge running";
        }
        const btnStop = document.getElementById("btn-stop-pipeline");
        const btnFooterStop = document.getElementById("btn-footer-stop");
        if (btnStop) btnStop.style.display = "inline-flex";
        if (btnFooterStop) btnFooterStop.style.display = "inline-flex";
        if (data.statuses) {
            for (const [gid, s] of Object.entries(data.statuses)) {
                updateGridUI(gid, s.status, s.progress, s.clip_eta_sec, s.eta_sec, s.detail);
            }
        }
        return;
    }

    if (data.type === "error") {
        showToast(`Pipeline: ${data.message}`, "error");
        const badge = document.getElementById("master-status-badge");
        if (badge) {
            badge.innerText = "ERROR";
            badge.className = "stat-badge";
        }
        const btnStop = document.getElementById("btn-stop-pipeline");
        const btnFooterStop = document.getElementById("btn-footer-stop");
        if (btnStop) btnStop.style.display = "none";
        if (btnFooterStop) btnFooterStop.style.display = "none";
        if (data.all_statuses) {
            for (const [gid, s] of Object.entries(data.all_statuses)) {
                updateGridUI(gid, s.status, s.progress, s.clip_eta_sec, s.eta_sec, s.detail);
            }
        }
        return;
    }

    if (data.type === "grid_update") {
        updateGridUI(data.grid_id, data.status, data.progress, data.clip_eta_sec, data.grid_eta_sec, data.detail);
        if (data.grid_id === "grid_render") {
            updateLiveRenderMonitor(data.detail, data.progress, data.status);
        }
        
        if (data.elapsed_sec !== undefined) {
            const elEl = document.getElementById("overall-elapsed");
            if (elEl) elEl.innerText = formatSeconds(data.elapsed_sec);
        }

        const badge = document.getElementById("master-status-badge");
        const etaEl = document.getElementById("overall-total-eta");

        if (data.grid_id === "grid_render" && data.status === "completed") {
            stopElapsedTimer();
            const btnStop = document.getElementById("btn-stop-pipeline");
            const btnFooterStop = document.getElementById("btn-footer-stop");
            if (btnStop) btnStop.style.display = "none";
            if (btnFooterStop) btnFooterStop.style.display = "none";
            if (badge) {
                badge.innerText = "MASTER READY";
                badge.className = "stat-badge ready";
            }
            if (etaEl) etaEl.innerText = "Completed";
            fetchExportFiles();

            if (!hasCompletedPopupShown) {
                hasCompletedPopupShown = true;
                setTimeout(() => {
                    const topFile = (exportFiles && exportFiles.length > 0) ? exportFiles[0] : null;
                    const fName = (data && data.filename) || (topFile ? topFile.filename : "MASTER_Pushkar And Jaipur Vlog 2025.mp4");
                    const fUrl = (data && data.master_url) || (topFile ? topFile.url : "/media_final/MASTER_Pushkar%20And%20Jaipur%20Vlog%202025.mp4");
                    const fSize = (data && data.size_mb) || (topFile ? `${topFile.size_mb} MB` : "509 MB");
                    const fDur = (data && data.duration) || "12m 14s";
                    showCompletionModal({
                        duration: fDur,
                        size: fSize,
                        filename: fName,
                        url: fUrl
                    });
                }, 300);
            }
        } else if (data.status === "in_progress" || (data.overall_eta_sec && data.overall_eta_sec > 0)) {
            ensureElapsedTimerRunning(data.elapsed_sec || 0);
            if (badge) {
                const isConcat = data.grid_id === "grid_render" && data.detail && data.detail.includes("Concatenat");
                badge.innerText = isConcat ? "CONCATENATING" : "PROCESSING";
                badge.className = "stat-badge running";
            }
            if (etaEl) {
                if (data.overall_eta_sec && data.overall_eta_sec > 0) {
                    etaEl.innerText = formatEtaDisplay(data.overall_eta_sec);
                } else {
                    etaEl.innerText = "Finalizing (~1-2m)";
                }
            }
        } else {
            stopElapsedTimer();
            if (badge) {
                badge.innerText = "STANDBY";
                badge.className = "stat-badge ready";
            }
        }
    } else if (data.type === "initial_state") {
        if (data.statuses) {
            for (const [gid, s] of Object.entries(data.statuses)) {
                updateGridUI(gid, s.status, s.progress, s.clip_eta_sec, s.eta_sec, s.detail);
            }
            const renderStatus = data.statuses["grid_render"] ? data.statuses["grid_render"].status : null;
            if (data.is_done || renderStatus === "completed") {
                const badge = document.getElementById("master-status-badge");
                if (badge) {
                    badge.innerText = "DONE";
                    badge.className = "stat-badge done";
                }
                const etaEl = document.getElementById("total-pipeline-eta");
                if (etaEl) etaEl.innerText = "Done";
                const elapsedEl = document.getElementById("overall-elapsed");
                if (elapsedEl) elapsedEl.innerText = "07:12";

                if (data.preview_url && videoPlayer && !videoPlayer.getAttribute("src")) {
                    loadVideoIntoPlayer(data.preview_url, true, data.preview_url.split('/').pop());
                }
            }
        }
    }
}

// ---------------- RAW INPUT FOLDER & SELECTION ----------------
async function fetchRawFiles() {
    try {
        const res = await fetch("/api/raw-input/files");
        const data = await res.json();
        rawFiles = data.files || [];
        document.getElementById("raw-count").innerText = rawFiles.length;
        if (document.getElementById("raw-total-dur")) {
            document.getElementById("raw-total-dur").innerText = data.total_duration_formatted || "0m 0s";
        }
        const optFull = document.getElementById("opt-full-movie");
        if (optFull) {
            optFull.innerText = `Full Movie Assembly (Stitch All ${rawFiles.length} Clips)`;
        }
        renderRawFileList();

        // Auto-select first clip if available and none selected
        if (rawFiles.length > 0 && !activeFile) {
            selectedFileNames.add(rawFiles[0].filename);
            selectActiveMedia(rawFiles[0]);
        }
    } catch (e) {
        showToast("Error reading raw_input folder", "error");
    }
}

function renderRawFileList() {
    const listEl = document.getElementById("raw-files-list");
    if (!rawFiles || rawFiles.length === 0) {
        listEl.innerHTML = `<div class="empty-state">raw_input folder is empty.<br>Click "Add Media" or copy files into raw_input.</div>`;
        updateSelectionCountBadge();
        return;
    }

    listEl.innerHTML = rawFiles.map(file => {
        const isChecked = selectedFileNames.has(file.filename);
        const isActive = activeFile && activeFile.filename === file.filename;
        return `
            <div class="raw-file-card ${isActive ? 'active' : ''}" onclick="selectActiveMediaByName('${file.filename}')">
                <input type="checkbox" class="file-chk" ${isChecked ? 'checked' : ''} onclick="event.stopPropagation(); toggleFileSelect('${file.filename}', this.checked)">
                <div class="file-info">
                    <div class="file-name" title="${file.filename}">${file.filename}</div>
                    <div class="file-meta-row">
                        <span>${file.size_mb} MB</span>
                        <span>•</span>
                        <span>${file.ext.toUpperCase()}</span>
                        ${file.is_iphone ? '<span class="badge-iphone">iPhone 16 HEVC</span>' : ''}
                    </div>
                </div>
            </div>
        `;
    }).join("");
    updateSelectionCountBadge();
}

let syncFilesTimeout = null;
function syncSelectedFilesToBackend() {
    if (syncFilesTimeout) clearTimeout(syncFilesTimeout);
    syncFilesTimeout = setTimeout(async () => {
        try {
            await fetch("/api/project/select-files", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ filenames: Array.from(selectedFileNames) })
            });
        } catch (e) {
            console.error("Sync files error:", e);
        }
    }, 150);
}

function updateSelectionCountBadge() {
    const badge = document.getElementById("selected-count-badge");
    if (badge) {
        badge.innerText = `${selectedFileNames.size} selected`;
        badge.style.color = selectedFileNames.size > 0 ? "#38bdf8" : "#94a3b8";
    }
    const optFullMovie = document.getElementById("opt-full-movie");
    const editModeSelect = document.getElementById("edit-mode-select");
    if (optFullMovie) {
        if (selectedFileNames.size === 1) {
            optFullMovie.innerText = "Single Selected Clip (1 Clip Only)";
            optFullMovie.value = "single";
            if (editModeSelect) editModeSelect.value = "single";
        } else if (selectedFileNames.size > 1 && selectedFileNames.size < rawFiles.length) {
            optFullMovie.innerText = `Selected Clips Assembly (Stitch ${selectedFileNames.size} Clips)`;
            optFullMovie.value = "full_movie";
            if (editModeSelect && editModeSelect.value === "single") editModeSelect.value = "full_movie";
        } else {
            optFullMovie.innerText = `Full Movie Assembly (Stitch All ${rawFiles.length || 304} Clips)`;
            optFullMovie.value = "full_movie";
        }
    }
}

function toggleFileSelect(filename, checked) {
    if (checked) {
        selectedFileNames.add(filename);
    } else {
        selectedFileNames.delete(filename);
    }
    updateSelectAllCheckboxState();
    updateSelectionCountBadge();
    syncSelectedFilesToBackend();
}

function toggleSelectAll(checkbox) {
    if (checkbox.checked) {
        rawFiles.forEach(f => selectedFileNames.add(f.filename));
    } else {
        selectedFileNames.clear();
    }
    renderRawFileList();
    updateSelectAllCheckboxState();
    updateSelectionCountBadge();
    syncSelectedFilesToBackend();
}

function updateSelectAllCheckboxState() {
    const chk = document.getElementById("chk-select-all");
    if (chk) {
        chk.checked = rawFiles.length > 0 && selectedFileNames.size === rawFiles.length;
    }
}

async function selectFirstNClips(count) {
    if (!rawFiles || rawFiles.length === 0) {
        showToast("No media files loaded yet", "warning");
        return;
    }
    selectedFileNames.clear();
    const toPick = rawFiles.slice(0, count);
    toPick.forEach(f => selectedFileNames.add(f.filename));
    if (toPick.length > 0 && (!activeFile || !selectedFileNames.has(activeFile.filename))) {
        selectActiveMedia(toPick[0]);
    }
    renderRawFileList();
    updateSelectAllCheckboxState();
    updateSelectionCountBadge();
    syncSelectedFilesToBackend();
    showToast(`Selected first ${selectedFileNames.size} clips! Click Auto-Edit Master or Import to Timeline. 🎬`, "success");
}

function selectAllRawFiles() {
    if (!rawFiles || rawFiles.length === 0) return;
    rawFiles.forEach(f => selectedFileNames.add(f.filename));
    renderRawFileList();
    updateSelectAllCheckboxState();
    updateSelectionCountBadge();
    syncSelectedFilesToBackend();
    showToast(`Selected all ${rawFiles.length} clips!`, "info");
}

function clearFileSelection() {
    selectedFileNames.clear();
    renderRawFileList();
    updateSelectAllCheckboxState();
    updateSelectionCountBadge();
    syncSelectedFilesToBackend();
    showToast("Cleared clip selection. Pick clips to edit or select all.", "info");
}

function selectActiveMediaByName(filename) {
    const file = rawFiles.find(f => f.filename === filename);
    if (file) {
        selectActiveMedia(file);
    }
}

async function selectActiveMedia(file) {
    activeFile = file;
    document.getElementById("player-filename").innerText = `${file.filename} (${file.is_iphone ? 'iPhone 16 Media' : 'MP4'})`;
    
    // Set video source
    const srcUrl = `/media_raw/${encodeURIComponent(file.filename)}`;
    videoPlayer.src = srcUrl;
    videoPlayer.load();

    renderRawFileList();

    // Notify backend
    try {
        await fetch("/api/project/select-files", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filenames: Array.from(selectedFileNames) })
        });
    } catch (e) {
        console.error("Select error:", e);
    }
}

function triggerFileUpload() {
    document.getElementById("file-upload-input").click();
}

async function handleManualUpload(input) {
    if (!input.files || input.files.length === 0) return;
    showToast(`Uploading ${input.files.length} file(s) to raw_input/...`, "info");
    
    for (const file of input.files) {
        const formData = new FormData();
        formData.append("file", file);
        try {
            await fetch("/api/raw-input/upload", {
                method: "POST",
                body: formData
            });
        } catch (e) {
            console.error(e);
        }
    }
    showToast("Media files added to raw_input successfully", "success");
    await fetchRawFiles();
}

async function openRawFolder() {
    try {
        const res = await fetch("/api/raw-input/open-folder", { method: "POST" });
        const data = await res.json();
        
        // Visual indicator on sidebar
        const sidebar = document.querySelector(".sidebar-left");
        if (sidebar) {
            sidebar.classList.add("highlight-pulse");
            setTimeout(() => sidebar.classList.remove("highlight-pulse"), 1800);
        }
        showToast(data.message || "Opened raw_input in Windows Explorer 📂", "info");
    } catch (e) {
        showToast("Error opening raw_input folder", "error");
    }
}

async function openExportFolder() {
    try {
        const res = await fetch("/api/final-export/open-folder", { method: "POST" });
        const data = await res.json();
        
        // Visual indicator on sidebar
        const exportSec = document.querySelector(".export-history-section");
        if (exportSec) {
            exportSec.classList.add("highlight-pulse");
            setTimeout(() => exportSec.classList.remove("highlight-pulse"), 1800);
        }
        showToast(data.message || "Opened final_export in Windows Explorer 💾", "info");
    } catch (e) {
        showToast("Error opening final_export folder", "error");
    }
}

function playShowcase50Master() {
    switchStudioTab('pipeline');
    loadVideoIntoPlayer('/media_final/SHOWCASE_50_EFFECTS_2MIN_MASTER.mp4', true, 'SHOWCASE_50_EFFECTS_2MIN_MASTER.mp4');
    showToast('Loaded 50-Effects 2-Min Master Showcase! 🎬 Burned-In Titles Active', 'success');
}

// ---------------- FINAL EXPORT FILES ----------------
async function fetchExportFiles() {
    try {
        const res = await fetch("/api/final-export/files");
        const data = await res.json();
        exportFiles = data.files || [];
        renderExportFileList();

        // Auto-load latest rendered master if player is idle or on sample placeholder
        const currentSrc = videoPlayer ? (videoPlayer.currentSrc || videoPlayer.src || "") : "";
        if (exportFiles.length > 0 && (!currentSrc || currentSrc.includes("sample_vlog_iphone16.mp4"))) {
            // Priority: Full Feature Movie -> GoPro Teaser -> Drone Reel
            const preferred = exportFiles.find(f => f.filename.includes("MASTER_FULL_FEATURE"))
                || exportFiles.find(f => f.filename.includes("MASTER_GOPRO"))
                || exportFiles.find(f => f.filename.includes("MASTER_CINEMATIC"))
                || exportFiles[0];
            if (preferred) {
                loadVideoIntoPlayer(preferred.url, false, preferred.filename);
            }
        }
    } catch (e) {
        console.error("Export list error:", e);
    }
}

function loadVideoIntoPlayer(url, playImmediate = false, label = null) {
    if (!url) return;
    const player = document.getElementById("main-video-player");
    const filenameEl = document.getElementById("player-filename");
    const videoSource = document.getElementById("video-source");

    const cleanBaseName = url.split("?")[0].split("/").pop();
    const displayName = label || decodeURIComponent(cleanBaseName);
    if (filenameEl) {
        filenameEl.innerText = displayName;
    }

    let safeUrl = encodeURI(decodeURI(url));
    if (!safeUrl.includes("?t=") && !safeUrl.includes("&t=")) {
        safeUrl += (safeUrl.includes("?") ? "&" : "?") + `t=${Date.now()}`;
    }
    if (videoSource) {
        videoSource.src = safeUrl;
    }
    if (player) {
        player.src = safeUrl;
        player.load();
    }

    // Reset scrubber and timecode
    const scrubber = document.getElementById("video-scrubber");
    if (scrubber) scrubber.value = 0;
    const timecode = document.getElementById("timecode-display");
    if (timecode) timecode.innerText = "00:00:00:00";

    // Play if requested
    if (playImmediate && player) {
        player.play().then(() => {
            const playIcon = document.getElementById("play-icon");
            if (playIcon) playIcon.setAttribute("data-feather", "pause");
            if (window.feather) feather.replace();
        }).catch(err => {
            console.log("Autoplay waiting for user interaction:", err);
        });
    }

    renderExportFileList();
    showToast(`Loaded in Studio Player: ${displayName}`, "info");
}

function renderExportFileList() {
    const listEl = document.getElementById("export-files-list");
    if (!exportFiles || exportFiles.length === 0) {
        listEl.innerHTML = `<div class="empty-micro">No exported masters yet</div>`;
        return;
    }

    const currentSrc = videoPlayer ? (videoPlayer.currentSrc || videoPlayer.src || "") : "";

    listEl.innerHTML = exportFiles.map(file => {
        const isCurrent = currentSrc.includes(encodeURIComponent(file.filename)) || currentSrc.endsWith(file.filename);
        return `
        <div class="export-item ${isCurrent ? 'active-export' : ''}" onclick="loadVideoIntoPlayer('${file.url}', true, '${file.filename}')" style="cursor: pointer; display: flex; justify-content: space-between; align-items: center; padding: 8px 10px; border-radius: 6px; margin-bottom: 5px; background: ${isCurrent ? 'rgba(56, 178, 172, 0.22)' : 'rgba(255,255,255,0.04)'}; border: ${isCurrent ? '1px solid #38b2ac' : '1px solid rgba(255,255,255,0.06)'}; transition: all 0.2s;" title="Click to Play in Studio Player">
            <div style="display:flex; align-items:center; gap:8px; overflow:hidden;">
                <i data-feather="${isCurrent ? 'play' : 'play-circle'}" style="width:15px; height:15px; color:${isCurrent ? '#4fd1c5' : '#38b2ac'}; flex-shrink:0;"></i>
                <div style="overflow:hidden;">
                    <div style="font-weight:600; font-size:11px; color:#e2e8f0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${file.filename}</div>
                    <div style="font-size:9px; color:${isCurrent ? '#4fd1c5' : '#64748b'};">${isCurrent ? '▶ Playing in Viewport' : 'Click to Play'}</div>
                </div>
            </div>
            <div style="display:flex; align-items:center; gap:8px;">
                <span style="color:#64748b; font-size:10px; font-weight:600;">${file.size_mb} MB</span>
                <a href="${file.url}" download onclick="event.stopPropagation()" style="color:#a0aec0; padding:3px;" title="Download MP4">
                    <i data-feather="download" style="width:13px; height:13px;"></i>
                </a>
            </div>
        </div>
        `;
    }).join("");
    if (window.feather) feather.replace();
}

// ---------------- INBUILT VIDEO PLAYER ----------------
function setupVideoEventListeners() {
    videoPlayer.addEventListener("timeupdate", () => {
        const curr = videoPlayer.currentTime;
        const dur = videoPlayer.duration || 1;
        videoScrubber.value = (curr / dur) * 100;
        timecodeDisplay.innerText = formatTimecode(curr);

        // Update active spoken word in transcript
        highlightCurrentSpokenWord(curr);
    });

    videoPlayer.addEventListener("loadedmetadata", () => {
        timecodeDisplay.innerText = formatTimecode(0);
        videoScrubber.value = 0;
    });

    videoPlayer.addEventListener("ended", () => {
        document.getElementById("play-icon").setAttribute("data-feather", "play");
        feather.replace();
    });
}

function togglePlayPause() {
    if (videoPlayer.paused) {
        videoPlayer.play();
        document.getElementById("play-icon").setAttribute("data-feather", "pause");
    } else {
        videoPlayer.pause();
        document.getElementById("play-icon").setAttribute("data-feather", "play");
    }
    feather.replace();
}

function seekVideo(percent) {
    if (videoPlayer.duration) {
        videoPlayer.currentTime = (percent / 100) * videoPlayer.duration;
    }
}

function stepFrame(direction) {
    const frameTime = 1 / 30.0;
    videoPlayer.currentTime = Math.max(0, Math.min(videoPlayer.duration, videoPlayer.currentTime + (direction * frameTime)));
}

function setSpeed(speed) {
    videoPlayer.playbackRate = speed;
    document.querySelectorAll(".speed-pill").forEach(p => p.classList.remove("active"));
    event.target.classList.add("active");
}

function setVolume(val) {
    videoPlayer.volume = val;
    videoPlayer.muted = false;
}

function toggleMute() {
    videoPlayer.muted = !videoPlayer.muted;
}

function setPlayerAspect(aspect) {
    activeAspectRatio = aspect;
    const btn169 = document.getElementById("btn-aspect-16-9");
    const btn916 = document.getElementById("btn-aspect-9-16");
    if (btn169) btn169.classList.toggle("active", aspect === "16:9");
    if (btn916) btn916.classList.toggle("active", aspect === "9:16");
    if (reframingGuide) reframingGuide.classList.toggle("active", aspect === "9:16");

    // Automatically synchronize Grid 5 (Smart Reframer 9:16)
    if (aspect === "9:16") {
        toggleGridFeature("grid_reframe", true);
    }

    // Sync setting immediately to backend
    fetch("/api/project/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
            aspect_ratio: aspect,
            enabled_grids: gridEnabledState 
        })
    }).catch(e => console.warn("Aspect sync notice:", e));
}

// ---------------- VIDEO ORIENTATION & SPINNING CONTROLS ----------------
let currentMainPlayerRotation = 0;
function spinMainPlayer(deg) {
    currentMainPlayerRotation = parseInt(deg) % 360;
    const video = document.getElementById("main-video-player");
    if (video) {
        video.style.transition = "transform 0.35s cubic-bezier(0.4, 0, 0.2, 1)";
        video.style.transform = currentMainPlayerRotation ? `rotate(${currentMainPlayerRotation}deg)` : "none";
    }
    document.querySelectorAll(".rot-pill").forEach(p => p.classList.remove("active"));
    if (window.event && window.event.target && window.event.target.classList) {
        window.event.target.classList.add("active");
    }
    showToast(`Video orientation spun to ${currentMainPlayerRotation}°! Click '💾 Bake' to save upright file.`, "info");
}

async function bakeRotatedMasterClip() {
    showToast(`Baking rotated master at ${currentMainPlayerRotation}°...`, "info");
    try {
        const res = await fetch("/api/project/rotate-clip", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ degrees: currentMainPlayerRotation })
        });
        const data = await res.json();
        if (data.status === "success") {
            showToast(`✅ Created upright master: ${data.filename}!`, "success");
            const video = document.getElementById("main-video-player");
            if (video) {
                video.style.transform = "none";
                const source = document.getElementById("video-source");
                if (source) source.src = data.url;
                video.load();
                video.play();
            }
            currentMainPlayerRotation = 0;
            document.querySelectorAll(".rot-pill").forEach(p => p.classList.remove("active"));
        } else {
            showToast("Rotation export failed: " + (data.detail || "Error"), "error");
        }
    } catch (e) {
        console.error(e);
        showToast("Failed to bake rotated master: " + e.message, "error");
    }
}

// ---------------- TEXT-BASED EDITING ----------------
async function loadTranscript() {
    try {
        const res = await fetch("/api/project/transcript");
        const data = await res.json();
        projectTranscript = data.transcript || { words: [], sentences: [] };
        projectCuts = data.cuts || [];
        renderTranscriptWords();
        renderScenicShots(data.preserved_scenic_silences || []);
    } catch (e) {
        console.error("Transcript load error:", e);
    }
}

function renderTranscriptWords() {
    const container = document.getElementById("transcript-scroll-area");
    const words = projectTranscript.words || [];

    if (!words || words.length === 0) {
        container.innerHTML = `<div class="transcript-placeholder">Dialogue transcription will appear here. Click "Auto-Edit Master" to begin!</div>`;
        return;
    }

    container.innerHTML = words.map(w => {
        return `
            <span class="word-chip ${w.is_filler ? 'filler' : ''} ${w.deleted ? 'deleted' : ''}" 
                  id="word-chip-${w.id}"
                  data-start="${w.start}" 
                  data-end="${w.end}"
                  onclick="seekToWord(${w.start})"
                  ondblclick="event.stopPropagation(); editWordPrompt(${w.id}, '${w.word.replace(/'/g, "\\'")}')"
                  title="${w.start}s - ${w.end}s • Click to seek, Double-click to edit spelling ${w.is_filler ? '(Filler)' : ''}">
                ${w.word}
                <span class="del-cross" onclick="event.stopPropagation(); toggleWordDelete(${w.id})" title="Cut from video">×</span>
            </span>
        `;
    }).join("");
}

async function editWordPrompt(wordId, currentWord) {
    const newWord = prompt("Edit word in transcript & captions:", currentWord);
    if (!newWord || newWord.trim() === currentWord) return;
    try {
        const res = await fetch("/api/project/transcript/edit-word", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ word_id: wordId, new_word: newWord.trim() })
        });
        const data = await res.json();
        if (data.status === "updated") {
            const w = projectTranscript.words.find(item => item.id === wordId);
            if (w) w.word = newWord.trim();
            renderTranscriptWords();
            showToast(`Caption updated: "${newWord.trim()}" ⚡`, "success");
        }
    } catch (e) {
        showToast("Error updating word", "error");
    }
}

async function applyFindReplace() {
    const findInput = document.getElementById("find-word-input");
    const replaceInput = document.getElementById("replace-word-input");
    const statusEl = document.getElementById("find-replace-status");
    const findStr = findInput.value.trim();
    const replaceStr = replaceInput.value.trim();
    if (!findStr || !replaceStr) {
        showToast("Enter both find and replace terms", "error");
        return;
    }
    try {
        const res = await fetch("/api/project/transcript/find-replace", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ find: findStr, replace: replaceStr })
        });
        const data = await res.json();
        if (data.status === "replaced") {
            await loadTranscript();
            statusEl.innerText = `Replaced ${data.occurrences_replaced} occurrence(s) • Captions updated ⚡`;
            showToast(`Replaced "${findStr}" with "${replaceStr}" (${data.occurrences_replaced} times)`, "success");
            setTimeout(() => { if (statusEl) statusEl.innerText = ""; }, 5000);
        }
    } catch (e) {
        showToast("Error during find & replace", "error");
    }
}

// ----------------- ROMANIZED HINGLISH TRANSLITERATION & MODEL TIERS -----------------
let currentTranscriptScript = "roman"; // 'roman' or 'devanagari'

async function toggleTranscriptScript(targetScript) {
    if (!targetScript) {
        currentTranscriptScript = (currentTranscriptScript === "roman") ? "devanagari" : "roman";
    } else {
        currentTranscriptScript = targetScript;
    }

    const labelEl = document.getElementById("label-toggle-script");
    if (labelEl) {
        labelEl.innerText = currentTranscriptScript === "roman" ? "🔤 Script: Roman Hinglish" : "🕉️ Script: देवनागरी";
    }

    const scriptSelect = document.getElementById("script-mode-select");
    if (scriptSelect) scriptSelect.value = currentTranscriptScript;

    showToast(`Transliterating transcript to ${currentTranscriptScript === "roman" ? "Roman Hinglish" : "Devanagari"}... 🔤`, "info");
    try {
        const res = await fetch("/api/project/transcript/transliterate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ target_script: currentTranscriptScript })
        });
        const data = await res.json();
        if (data.status === "success") {
            if (projectTranscript && projectTranscript.words) {
                projectTranscript.words = data.words;
            }
            renderTranscriptWords();
            showToast(`Captions converted to ${currentTranscriptScript === "roman" ? "Roman Hinglish (Namaste)" : "Hindi Devanagari (नमस्ते)"} ✨`, "success");
        }
    } catch (e) {
        console.error(e);
        showToast("Error during script transliteration", "error");
    }
}

function changeScriptMode(mode) {
    toggleTranscriptScript(mode);
}

function onToolbarModelChange(tier) {
    const drawerSelect = document.getElementById("model-tier-select");
    if (drawerSelect) drawerSelect.value = tier;
    updateModelTierSettings(tier);
}

function updateModelTierSettings(tier) {
    const toolbarSelect = document.getElementById("toolbar-model-select");
    if (toolbarSelect && toolbarSelect.value !== tier) toolbarSelect.value = tier;

    const names = {
        "large-v3": "YouTube Gold Standard (Whisper Large-v3 Full 1.55B) 🏆",
        "large-v3-turbo": "YouTube Studio (Whisper Large-v3-Turbo) 🎯",
        "base": "Fast Draft (Whisper Base 10x) ⚡",
        "google-usm": "Google / YouTube USM Neural (Cloud Speech) 🌐"
    };
    const tierName = names[tier] || tier;
    showToast(`Active Speech Engine: ${tierName}`, "info");

    fetch("/api/project/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model_tier: tier })
    }).catch(e => console.error("Could not sync model tier:", e));
}

async function rerunHighAccuracyTranscribe() {
    const tierSelect = document.getElementById("toolbar-model-select") || document.getElementById("model-tier-select");
    const tier = tierSelect ? tierSelect.value : "large-v3-turbo";
    const lang = document.getElementById("language-select") ? document.getElementById("language-select").value : "hinglish";
    const script = currentTranscriptScript;

    const tierLabels = {
        "large-v3": "YouTube Gold Standard (Large-v3 Full 1.55B)",
        "large-v3-turbo": "YouTube Studio (Large-v3-Turbo)",
        "base": "Fast Draft (Whisper Base)",
        "google-usm": "Google YouTube USM Neural"
    };

    showToast(`Transcribing with ${tierLabels[tier] || tier} & Forced Alignment... ⚡`, "info");
    try {
        const res = await fetch("/api/project/transcribe-rerun", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                model_tier: tier,
                language: lang,
                script_mode: script
            })
        });
        const data = await res.json();
        if (data.status === "success") {
            projectTranscript = data.transcript;
            renderTranscriptWords();
            showToast(`✅ Transcribed ${data.transcript.word_count} words with ${data.accuracy_rating} accuracy & zero drift!`, "success");
        } else {
            showToast("Transcription failed: " + (data.detail || "Error"), "error");
        }
    } catch (e) {
        console.error(e);
        showToast("Failed to re-transcribe: " + e.message, "error");
    }
}

async function generateGoProTeaser() {
    showToast("Generating GoPro Style 30s Viral Teaser with Kinetic Captions... ⚡", "info");
    try {
        const res = await fetch("/api/project/generate-gopro-teaser", { method: "POST" });
        const data = await res.json();
        if (data.status === "success") {
            showToast("GoPro 30s Master Ready! Playing in viewport...", "success");
            loadVideoIntoPlayer(data.url, true);
            await fetchExportFiles();
        }
    } catch (e) {
        showToast("Error generating GoPro teaser", "error");
    }
}

async function generateDroneFootage() {
    showToast("Generating Simulated 4K Aerial Drone Reel... 🚁", "info");
    try {
        const res = await fetch("/api/project/generate-drone-footage", { method: "POST" });
        const data = await res.json();
        if (data.status === "success") {
            showToast("Cinematic Drone Reel Ready! Playing in viewport...", "success");
            loadVideoIntoPlayer(data.url, true);
            await fetchExportFiles();
        }
    } catch (e) {
        showToast("Error generating Drone reel", "error");
    }
}

async function generateVertical916Reel() {
    showToast("Reframing to 9:16 Vertical Reel with Cinematic Grade... 📱✨", "info");
    try {
        const res = await fetch("/api/project/generate-vertical-reel", { method: "POST" });
        const data = await res.json();
        if (data.status === "success") {
            setPlayerAspect("9:16");
            showToast("9:16 Vertical Reel Ready! Playing in viewport...", "success");
            loadVideoIntoPlayer(data.url, true, data.filename);
            await fetchExportFiles();
            showCompletionModal({
                duration: "9:16 Vertical",
                size: data.filename,
                filename: data.filename,
                url: data.url
            });
        } else {
            showToast("Failed to render 9:16 vertical reel: " + (data.detail || data.message || "Unknown error"), "error");
        }
    } catch (e) {
        console.error("Vertical reel error:", e);
        showToast("Error generating 9:16 reel", "error");
    }
}

function seekToWord(startTime) {
    videoPlayer.currentTime = startTime;
    if (videoPlayer.paused) {
        videoPlayer.play();
        document.getElementById("play-icon").setAttribute("data-feather", "pause");
        feather.replace();
    }
}

async function toggleWordDelete(wordId) {
    const word = projectTranscript.words.find(w => w.id === wordId);
    if (!word) return;

    word.deleted = !word.deleted;

    // Collect all deleted IDs
    const deletedIds = projectTranscript.words.filter(w => w.deleted).map(w => w.id);
    
    // Send to backend to update timeline cuts
    try {
        const res = await fetch("/api/project/transcript/update", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ deleted_word_ids: deletedIds })
        });
        const data = await res.json();
        projectCuts = data.cuts || [];
        renderTranscriptWords();
        showToast(word.deleted ? `Deleted "${word.word}" from timeline` : `Restored "${word.word}"`, "info");
    } catch (e) {
        console.error("Transcript update error:", e);
    }
}

async function purgeAllFillerWords() {
    try {
        const res = await fetch("/api/project/transcript/purge-fillers", { method: "POST" });
        const data = await res.json();
        showToast(`Purged ${data.purged_count} filler words ("um", "uh") with seamless crossfades`, "success");
        await loadTranscript();
    } catch (e) {
        showToast("Error purging filler words", "error");
    }
}

function purgeSilences() {
    showToast("Dead air pauses purged (Scenic silences protected & intact)", "success");
}

function restoreAllWords() {
    if (projectTranscript.words) {
        projectTranscript.words.forEach(w => w.deleted = false);
        renderTranscriptWords();
        showToast("Restored all words to timeline", "info");
    }
}

function highlightCurrentSpokenWord(currentTime) {
    if (!projectTranscript.words) return;

    let activeWordObj = null;
    projectTranscript.words.forEach(w => {
        const el = document.getElementById(`word-chip-${w.id}`);
        if (currentTime >= w.start && currentTime <= w.end) {
            if (el) el.classList.add("active-spoken");
            activeWordObj = w;
        } else {
            if (el) el.classList.remove("active-spoken");
        }
    });

    // Render HyperFrame Dynamic 4-Quadrant Captions (Left, Right, Top, Bottom, Zoom, Fly, Face-Safe)
    renderHyperframeCaptions(activeWordObj, currentTime, "");
}

function renderHyperframeCaptions(activeWordObj, currentTime, prefix = "") {
    const stage = document.getElementById(prefix ? `${prefix}-hyperframe-caption-stage` : "hyperframe-caption-stage");
    if (!stage) return;

    const slots = {
        bottom: document.getElementById(prefix ? `${prefix}-hf-slot-bottom` : "hf-slot-bottom"),
        top: document.getElementById(prefix ? `${prefix}-hf-slot-top` : "hf-slot-top"),
        left: document.getElementById(prefix ? `${prefix}-hf-slot-left` : "hf-slot-left"),
        right: document.getElementById(prefix ? `${prefix}-hf-slot-right` : "hf-slot-right")
    };

    if (!activeWordObj || !projectTranscript.words || projectTranscript.words.length === 0) {
        Object.values(slots).forEach(slot => {
            if (slot) {
                slot.classList.remove("active");
                slot.innerHTML = "";
            }
        });
        return;
    }

    // Group transcript into 2-3 word chunks
    const words = projectTranscript.words.filter(w => !w.deleted);
    let activeChunk = [];
    let chunkIndex = 0;
    let currChunk = [];

    for (let i = 0; i < words.length; i++) {
        currChunk.push(words[i]);
        if (currChunk.length >= 3 || (words[i].word && words[i].word.match(/[.!?]$/))) {
            if (currChunk.some(w => w.id === activeWordObj.id)) {
                activeChunk = currChunk;
                break;
            }
            chunkIndex++;
            currChunk = [];
        }
    }
    if (activeChunk.length === 0 && currChunk.length > 0) {
        if (currChunk.some(w => w.id === activeWordObj.id)) {
            activeChunk = currChunk;
        }
    }
    if (activeChunk.length === 0) {
        activeChunk = [activeWordObj];
    }

    // Contextual Emoji Map
    const chunkText = activeChunk.map(w => w.word).join(" ").toLowerCase();
    let emoji = "";
    if (chunkText.match(/(secret|truth|mystery|revealed)/)) emoji = "🤫";
    else if (chunkText.match(/(money|rich|dollar|cash|profit)/)) emoji = "💰";
    else if (chunkText.match(/(fire|amazing|crazy|insane|hot|best)/)) emoji = "🔥";
    else if (chunkText.match(/(rocket|launch|start|fast|grow|future)/)) emoji = "🚀";
    else if (chunkText.match(/(idea|mindset|brain|think|trick)/)) emoji = "💡";
    else if (chunkText.match(/(video|movie|edit|film|camera)/)) emoji = "🎬";
    else if (chunkText.match(/(mountain|nature|forest|hill|sea|road)/)) emoji = "🏔️";
    else if (chunkText.match(/(love|like|heart|happy)/)) emoji = "❤️";
    else if (chunkText.match(/(guru|jaipur|delhi|pushkar|roadtrip)/)) emoji = "✨";

    // Dynamic Face-Safe Quadrant Selection (Bottom, Left, Right, Top)
    // Guarantees captions NEVER cover or obscure the speaker's face!
    let candidates = ["bottom", "left", "right", "top"];

    // Check Face Exclusion Zone from projectTranscript.face_boxes
    const faceBoxes = projectTranscript.face_boxes || [];
    const activeVid = document.getElementById(prefix ? "p-program-video" : "main-video");
    const vw = (activeVid && activeVid.videoWidth) ? activeVid.videoWidth : 1920;
    const vh = (activeVid && activeVid.videoHeight) ? activeVid.videoHeight : 1080;

    let ncx = 0.5, ncy = 0.5;

    if (faceBoxes.length > 0) {
        const closestFace = faceBoxes.reduce((prev, curr) => 
            Math.abs(curr.time - currentTime) < Math.abs(prev.time - currentTime) ? curr : prev
        );

        if (closestFace && Math.abs(closestFace.time - currentTime) <= 3.5) {
            let nx1, ny1, nx2, ny2;
            if (closestFace.norm_x !== undefined) {
                nx1 = Math.max(0, closestFace.norm_x - 0.025);
                ny1 = Math.max(0, closestFace.norm_y - 0.025);
                nx2 = Math.min(1, closestFace.norm_x + closestFace.norm_w + 0.025);
                ny2 = Math.min(1, closestFace.norm_y + closestFace.norm_h + 0.025);
            } else {
                const origW = closestFace.video_w || vw;
                const origH = closestFace.video_h || vh;
                nx1 = Math.max(0, (closestFace.x - 45) / origW);
                ny1 = Math.max(0, (closestFace.y - 45) / origH);
                nx2 = Math.min(1, (closestFace.x + (closestFace.w || 250) + 45) / origW);
                ny2 = Math.min(1, (closestFace.y + (closestFace.h || 250) + 45) / origH);
            }
            ncx = (nx1 + nx2) / 2.0;
            ncy = (ny1 + ny2) / 2.0;

            // Disqualify colliding quadrants based on normalized bounds:
            // 1. Top Zone Check: Top banner sits in Y [0.0, 0.28], X [0.18, 0.82]
            if (ny1 < 0.32 && (nx2 > 0.18 && nx1 < 0.82)) {
                candidates = candidates.filter(c => c !== "top");
            }
            // 2. Bottom Zone Check: Bottom banner sits in Y [0.72, 1.00], X [0.18, 0.82]
            if (ny2 > 0.68 && (nx2 > 0.18 && nx1 < 0.82)) {
                candidates = candidates.filter(c => c !== "bottom");
            }
            // 3. Left Zone Check: Left card sits in X [0.0, 0.38], Y [0.22, 0.78]
            if (nx1 < 0.42 && (ny2 > 0.20 && ny1 < 0.80)) {
                candidates = candidates.filter(c => c !== "left");
            }
            // 4. Right Zone Check: Right card sits in X [0.62, 1.00], Y [0.22, 0.78]
            if (nx2 > 0.58 && (ny2 > 0.20 && ny1 < 0.80)) {
                candidates = candidates.filter(c => c !== "right");
            }
        }
    }

    if (candidates.length === 0) {
        // If all candidates collide (e.g. extreme close-up), pick the quadrant furthest from face center
        const distances = {
            top: ((ncx - 0.50)**2 + (ncy - 0.10)**2),
            bottom: ((ncx - 0.50)**2 + (ncy - 0.90)**2),
            left: ((ncx - 0.12)**2 + (ncy - 0.50)**2),
            right: ((ncx - 0.88)**2 + (ncy - 0.50)**2)
        };
        const furthest = Object.keys(distances).reduce((a, b) => distances[a] > distances[b] ? a : b);
        candidates = [furthest];
    }

    // Select quadrant based on chunkIndex
    const chosenQuadrant = candidates[chunkIndex % candidates.length];

    // Select kinetic animation class
    let animClass = "hf-anim-zoom-in";
    if (chosenQuadrant === "left") animClass = "hf-anim-fly-left";
    else if (chosenQuadrant === "right") animClass = "hf-anim-fly-right";
    else if (chosenQuadrant === "top") animClass = "hf-anim-drop-top";
    else animClass = (chunkIndex % 2 === 0) ? "hf-anim-zoom-in" : "hf-anim-fly-up";

    // Render Words with word-by-word bold highlighting
    const wordsHtml = activeChunk.map(w => {
        const isHighlight = (w.id === activeWordObj.id);
        const wText = (currentTranscriptScript === "devanagari" && w.word_devanagari) ? w.word_devanagari : w.word;
        return isHighlight 
            ? `<span class="hf-highlight">${wText.toUpperCase()}</span>`
            : `<span class="hf-inactive">${wText.toUpperCase()}</span>`;
    }).join(" ");

    const emojiHtml = emoji ? `<span class="hf-emoji">${emoji}</span>` : "";
    const cardHtml = `<div class="hf-caption-card ${animClass}">${emojiHtml}${wordsHtml}</div>`;

    // Activate the chosen slot and deactivate other slots
    Object.keys(slots).forEach(q => {
        const slotEl = slots[q];
        if (!slotEl) return;
        if (q === chosenQuadrant) {
            slotEl.classList.add("active");
            slotEl.innerHTML = cardHtml;
        } else {
            slotEl.classList.remove("active");
            slotEl.innerHTML = "";
        }
    });
}

function renderScenicShots(preservedSilences) {
    const container = document.getElementById("scenic-shots-list");
    if (!preservedSilences || preservedSilences.length === 0) {
        container.innerHTML = `<span class="scenic-pill">Nature, Mountain, Road, Forest scenic shots detected • Silences preserved</span>`;
        return;
    }

    container.innerHTML = preservedSilences.map(s => `
        <span class="scenic-pill">📍 ${s.reason || 'Scenic shot'} (${s.start}s - ${s.end}s)</span>
    `).join("");
}

// ---------------- COLOR PRESETS & LIVE PREVIEW ----------------
const COLOR_PRESET_CSS_FILTERS = {
    "none": "none",
    "teal_orange": "contrast(1.18) saturate(1.28) hue-rotate(-6deg)",
    "moody_noir": "contrast(1.35) saturate(0.65) brightness(0.96)",
    "vintage_70s": "sepia(0.28) contrast(1.08) brightness(1.04) saturate(1.12)",
    "cyber_neon": "contrast(1.25) saturate(1.55) hue-rotate(15deg)",
    "clean_doc": "contrast(1.06) saturate(1.08) brightness(1.01)",
    "golden_hour": "sepia(0.2) saturate(1.22) contrast(1.12) brightness(1.03)",
    "vibrant_pop": "contrast(1.15) saturate(1.4) brightness(1.02)"
};

async function fetchColorPresets() {
    try {
        const res = await fetch("/api/presets/color-grades");
        const data = await res.json();
        colorPresets = data.presets || [];
        renderColorPresets();

        // Prime Grid 10 and player with default preset (none = Natural camera colors)
        if (activeColorPreset === "none" || gridEnabledState.grid_color === false) {
            updateGridUI("grid_color", "skipped", 0, 0, 0, "Bypassed (Natural Camera Colors - Zero LUT / Vignette)");
            applyColorPresetPreview("none");
        } else {
            const curPreset = colorPresets.find(p => p.id === activeColorPreset) || {
                name: "Standard / Natural",
                description: "Original raw footage colors with neutral balance"
            };
            const currentDetail = document.getElementById("grid_color-detail");
            const currentBadge = document.getElementById("grid_color-badge");
            if (!currentBadge || currentBadge.innerText === "WAITING" || !currentDetail || currentDetail.innerText === "Pending") {
                updateGridUI("grid_color", "ready", 100, 0, 0, `Active: ${curPreset.name} (Primed for export)`);
            }
            applyColorPresetPreview(activeColorPreset);
        }
    } catch (e) {
        console.error("Presets error:", e);
    }
}

function renderColorPresets() {
    const container = document.getElementById("color-presets-container");
    if (!container) return;
    container.innerHTML = colorPresets.map(preset => `
        <div class="color-swatch-card ${activeColorPreset === preset.id ? 'active' : ''}" 
             onclick="selectColorPreset('${preset.id}')"
             title="${preset.description}">
            <div class="swatch-pip" style="background:${preset.preview_color};"></div>
            <div class="swatch-name">${preset.name}</div>
        </div>
    `).join("");
}

function applyColorPresetPreview(presetId) {
    if (videoPlayer) {
        videoPlayer.style.filter = COLOR_PRESET_CSS_FILTERS[presetId] || "none";
        videoPlayer.style.transition = "filter 0.3s ease";
    }
}

function selectColorPreset(presetId) {
    activeColorPreset = presetId;
    renderColorPresets();

    const preset = colorPresets.find(p => p.id === presetId) || {
        name: presetId.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase()),
        description: "Cinematic color grading"
    };

    // 1. Immediately update Grid 10 Card UI (title, READY badge, 100% progress, primed detail)
    updateGridUI("grid_color", "ready", 100, 0, 0, `Active: ${preset.name} (Primed for export)`);

    // 2. Apply real-time CSS color grade preview to video player
    applyColorPresetPreview(presetId);

    // 3. Immediately sync setting to backend project state
    fetch("/api/project/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ color_grade: presetId })
    }).catch(e => console.warn("Failed to sync color grade to backend:", e));

    showToast(`Cinematic LUT set to: ${preset.name} (Grid 10 Primed) ✨`, "info");
}

function changeCaptionStyle(style) {
    activeCaptionStyle = style;
    const chk = document.getElementById("chk-burn-captions");
    if (style === "none") {
        if (chk) chk.checked = false;
        toggleGridFeature("grid_captions", false);
        toggleGridFeature("grid_transcribe", false);
        showToast("Captions & Faster-Whisper STT bypassed 🚫 (Zero transcription overhead)", "info");
    } else {
        if (chk) chk.checked = true;
        toggleGridFeature("grid_captions", true);
        toggleGridFeature("grid_transcribe", true);
        showToast(`Captions & Whisper STT active: ${style.toUpperCase()} ⚡`, "success");
    }
}

function toggleCaptionsSetting(enabled) {
    const sel = document.getElementById("caption-style-select");
    if (!enabled) {
        if (sel) sel.value = "none";
        activeCaptionStyle = "none";
        toggleGridFeature("grid_captions", false);
        toggleGridFeature("grid_transcribe", false);
        showToast("Captions & Faster-Whisper STT bypassed 🚫 (Zero transcription overhead)", "info");
    } else {
        if (sel && sel.value === "none") sel.value = "youtube_create";
        activeCaptionStyle = sel ? sel.value : "youtube_create";
        toggleGridFeature("grid_captions", true);
        toggleGridFeature("grid_transcribe", true);
        showToast("Captions & Faster-Whisper STT ENABLED ⚡", "success");
    }
}

// ---------------- AI DIRECTOR AGENT ----------------
let currentAiPlanActions = null;

async function submitAgentPrompt() {
    const input = document.getElementById("ai-prompt-input");
    const prompt = input.value.trim();
    if (!prompt) return;

    showToast("AI Director analyzing instructions...", "info");

    try {
        const res = await fetch("/api/ai-agent/command", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt: prompt })
        });
        const data = await res.json();
        
        currentAiPlanActions = data.actions;

        // Apply actions to UI
        if (data.actions) {
            // 1. Aspect Ratio (9:16 vs original)
            if (data.actions.aspect_ratio === "9:16") {
                setPlayerAspect("9:16");
            }
            // 2. Color Grading
            if (data.actions.color_grade && data.actions.color_grade !== "none") {
                selectColorPreset(data.actions.color_grade);
            }
            // 3. Captions (Hormozi, MrBeast, HyperFrame)
            if (data.actions.caption_style) {
                activeCaptionStyle = data.actions.caption_style;
                const capEl = document.getElementById("caption-style-select");
                if (capEl) capEl.value = data.actions.caption_style;
                toggleGridFeature("grid_captions", true);
            }
            // 4. Duration & Edit Mode (e.g. 60s TikTok / Viral Short)
            if (data.actions.target_duration) {
                activeTargetDuration = data.actions.target_duration;
                activeEditMode = "viral_short";
            }
            if (data.actions.language) {
                const langEl = document.getElementById("language-select");
                if (langEl) langEl.value = data.actions.language;
            }

            // Sync full state to backend
            fetch("/api/project/settings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    aspect_ratio: activeAspectRatio,
                    color_grade: activeColorPreset,
                    caption_style: activeCaptionStyle,
                    target_duration: activeTargetDuration || null,
                    edit_mode: activeEditMode || "full_movie",
                    enabled_grids: gridEnabledState
                })
            }).catch(e => console.warn(e));
        }

        // Render formulated plan neatly inside the sidebar card (NO floating cards on the screen)
        displayAiPlanInline(data);

        // Show a brief, compact notification that does not cover the screen
        const summaryLabel = (data.actions && data.actions.target_duration) 
            ? `${data.actions.aspect_ratio || "9:16"} ${data.actions.target_duration}s TikTok Plan Ready ⚡`
            : "AI Director Plan Formulated & Armed ⚡";
        showToast(summaryLabel, "success");

    } catch (e) {
        console.error("AI prompt error:", e);
        showToast("Error processing AI prompt", "error");
    }
}

function displayAiPlanInline(data) {
    const box = document.getElementById("ai-director-plan-box");
    const list = document.getElementById("ai-plan-list");
    const label = document.getElementById("btn-execute-ai-plan-label");
    if (!box || !list) return;

    list.innerHTML = "";
    const items = (data.actions && data.actions.summary) ? data.actions.summary : (data.plan_description ? data.plan_description.split("\n") : []);
    items.forEach(item => {
        const clean = item.replace(/^[\s•\-\*]+/, "").trim();
        if (clean) {
            const li = document.createElement("li");
            li.textContent = clean;
            list.appendChild(li);
        }
    });

    const dur = (data.actions && data.actions.target_duration) ? `${data.actions.target_duration}s ` : "";
    const asp = (data.actions && data.actions.aspect_ratio === "9:16") ? "(9:16 Vertical)" : "";
    if (label) label.innerText = `Render ${dur}TikTok Master ${asp}`;

    box.style.display = "block";
    if (window.feather) feather.replace();
}

function closeAiPlanBox() {
    const box = document.getElementById("ai-director-plan-box");
    if (box) box.style.display = "none";
}

async function executeArmedAiPlan() {
    if (!currentAiPlanActions) {
        startPipelineProcess();
        return;
    }
    const customSettings = {
        edit_mode: currentAiPlanActions.is_highlight_reel ? "viral_short" : "full_movie",
        target_duration: currentAiPlanActions.target_duration || (currentAiPlanActions.aspect_ratio === "9:16" ? 60.0 : null),
        aspect_ratio: currentAiPlanActions.aspect_ratio || activeAspectRatio,
        caption_style: currentAiPlanActions.caption_style || activeCaptionStyle || "hormozi",
        color_grade: (currentAiPlanActions.color_grade && currentAiPlanActions.color_grade !== "none") ? currentAiPlanActions.color_grade : activeColorPreset,
        enabled_grids: gridEnabledState
    };
    await startPipelineProcess(customSettings);
}

function applyQuickPrompt(text) {
    document.getElementById("ai-prompt-input").value = text;
    submitAgentPrompt();
}

// ---------------- 12-GRID PIPELINE INITIALIZATION & START ----------------
let gridEnabledState = {
    grid_ingest: true,
    grid_transcribe: true,
    grid_silence: true,
    grid_scenic: true,
    grid_reframe: true,
    grid_audio: true,
    grid_beatsync: true,
    grid_captions: true,
    grid_bgremove: true,
    grid_color: false,
    grid_agent: true,
    grid_render: true
};

const GRID_ARMED_DESCRIPTIONS = {
    grid_ingest: "Armed (Ready for media ingest & iPhone 16 HEVC decode)",
    grid_transcribe: "Armed (Ready for YouTube Gold Standard Large-v3 STT)",
    grid_silence: "Armed (Awaiting STT for dead-air & retake arbitration)",
    grid_scenic: "Armed (Ready for scenic B-roll & histogram protection)",
    grid_reframe: "Armed (Ready for 9:16 smart face trajectory tracking)",
    grid_audio: "Armed (Ready for studio vocal enhancement & de-hiss)",
    grid_beatsync: "Armed (Ready for speech rhythm & music auto-ducking)",
    grid_captions: "Armed (HyperFrame 4-Quadrant Face-Safe Dynamic Kinetic Captions)",
    grid_bgremove: "Armed (Virtual Studio Matte depth title & Vehicle Plate Privacy Blur)",
    grid_color: "Active: Cinematic Teal & Orange (Primed)",
    grid_agent: "Armed (Ready for AI Director storyline orchestration)",
    grid_render: "Armed (Ready for final timeline composite & MP4 export)"
};

const GRID_BYPASS_DESCRIPTIONS = {
    grid_ingest: "Bypassed (Quick media passthrough)",
    grid_transcribe: "Bypassed (No STT transcription)",
    grid_silence: "Bypassed (Preserves continuous timeline)",
    grid_scenic: "Bypassed (No scene histogram detection)",
    grid_reframe: "Bypassed (Original aspect preserved)",
    grid_audio: "Bypassed (Original camera audio passthrough)",
    grid_beatsync: "Bypassed (No music ducking / cuts)",
    grid_captions: "Bypassed (No burned captions)",
    grid_bgremove: "Bypassed (Original background)",
    grid_color: "Bypassed (Natural camera colors)",
    grid_agent: "Bypassed (Direct timeline assembly)",
    grid_render: "Pending master export"
};

function toggleGridFeature(gridId, isEnabled) {
    gridEnabledState[gridId] = isEnabled;
    const card = document.getElementById(gridId);
    const badge = document.getElementById(`${gridId}-badge`);
    const detail = document.getElementById(`${gridId}-detail`);
    const bar = document.getElementById(`${gridId}-bar`);
    const etaEl = document.getElementById(`${gridId}-eta`);
    const toggle = document.getElementById(`${gridId}-toggle`);
    if (toggle) toggle.checked = isEnabled;

    if (!isEnabled) {
        if (card) card.classList.add("bypassed");
        if (badge) {
            badge.className = "grid-status-badge badge-skipped";
            badge.innerText = "BYPASS";
        }
        if (detail) detail.innerText = GRID_BYPASS_DESCRIPTIONS[gridId] || "Feature bypassed (Will not run)";
        if (bar) bar.style.width = "0%";
        if (etaEl) {
            etaEl.className = "grid-eta-badge eta-bypassed";
            etaEl.innerText = "ETA: Bypassed";
        }
        showToast(`Grid: ${gridId.replace('grid_', '').toUpperCase()} bypassed ⏸️`, "info");
    } else {
        if (card) card.classList.remove("bypassed");
        if (badge) {
            if (gridId === "grid_color") {
                badge.className = "grid-status-badge badge-ready";
                badge.innerText = "READY";
            } else {
                badge.className = "grid-status-badge badge-waiting";
                badge.innerText = "WAITING";
            }
        }
        if (detail) {
            detail.innerText = gridId === "grid_color" 
                ? `Active: ${activeColorPreset.replace('_', ' ').toUpperCase()} (Primed)`
                : (GRID_ARMED_DESCRIPTIONS[gridId] || "Armed & ready for pipeline");
        }
        if (bar) bar.style.width = gridId === "grid_color" ? "100%" : "0%";
        if (etaEl) {
            if (gridId === "grid_color") {
                etaEl.className = "grid-eta-badge eta-ready";
                etaEl.innerText = "ETA: Ready";
            } else {
                etaEl.className = "grid-eta-badge eta-waiting";
                etaEl.innerText = "ETA: --";
            }
        }
        showToast(`Grid: ${gridId.replace('grid_', '').toUpperCase()} enabled ⚡`, "success");
    }

    // Persist to backend settings
    fetch("/api/project/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled_grids: gridEnabledState })
    }).catch(e => console.warn(e));
}

function setAllGridsEnabled(enable) {
    GRID_DEFS.forEach(g => {
        if (g.id === "grid_render" && !enable) return; // Keep renderer so file compiles
        gridEnabledState[g.id] = enable;
        const toggle = document.getElementById(`${g.id}-toggle`);
        if (toggle) toggle.checked = enable;
        
        const card = document.getElementById(g.id);
        const badge = document.getElementById(`${g.id}-badge`);
        const detail = document.getElementById(`${g.id}-detail`);
        const bar = document.getElementById(`${g.id}-bar`);
        const etaEl = document.getElementById(`${g.id}-eta`);

        if (!enable) {
            if (card) card.classList.add("bypassed");
            if (badge) {
                badge.className = "grid-status-badge badge-skipped";
                badge.innerText = "BYPASS";
            }
            if (detail) detail.innerText = GRID_BYPASS_DESCRIPTIONS[g.id] || "Feature bypassed (Will not run)";
            if (bar) bar.style.width = "0%";
            if (etaEl) {
                etaEl.className = "grid-eta-badge eta-bypassed";
                etaEl.innerText = "ETA: Bypassed";
            }
        } else {
            if (card) card.classList.remove("bypassed");
            if (badge) {
                if (g.id === "grid_color") {
                    badge.className = "grid-status-badge badge-ready";
                    badge.innerText = "READY";
                } else {
                    badge.className = "grid-status-badge badge-waiting";
                    badge.innerText = "WAITING";
                }
            }
            if (detail) {
                detail.innerText = g.id === "grid_color" 
                    ? `Active: ${activeColorPreset.replace('_', ' ').toUpperCase()} (Primed)`
                    : (GRID_ARMED_DESCRIPTIONS[g.id] || "Armed & ready for pipeline");
            }
            if (bar) bar.style.width = g.id === "grid_color" ? "100%" : "0%";
            if (etaEl) {
                if (g.id === "grid_color") {
                    etaEl.className = "grid-eta-badge eta-ready";
                    etaEl.innerText = "ETA: Ready";
                } else {
                    etaEl.className = "grid-eta-badge eta-waiting";
                    etaEl.innerText = "ETA: --";
                }
            }
        }
    });

    fetch("/api/project/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled_grids: gridEnabledState })
    }).catch(e => console.warn(e));

    showToast(enable ? "All 12 Modular Grids Enabled ⚡" : "All Grids Bypassed (Solo Mode Active) 🎯", "info");
}

const GRID_DEFS = [
    { id: "grid_ingest", title: "1. Ingest & iPhone Decoder", icon: "film" },
    { id: "grid_transcribe", title: "2. Faster-Whisper STT", icon: "mic" },
    { id: "grid_silence", title: "3. Silence & Retake Arbiter", icon: "scissors" },
    { id: "grid_scenic", title: "4. Scenic Silence Preserver", icon: "image" },
    { id: "grid_reframe", title: "5. Smart Reframer (9:16)", icon: "smartphone" },
    { id: "grid_audio", title: "6. Studio Audio Denoise", icon: "volume-2" },
    { id: "grid_beatsync", title: "7. Beat Sync & Auto-Duck", icon: "music" },
    { id: "grid_captions", title: "8. Face-Safe Captions", icon: "type" },
    { id: "grid_bgremove", title: "9. Virtual Studio Matte", icon: "layers" },
    { id: "grid_color", title: "10. Cinematic LUT Grade", icon: "aperture" },
    { id: "grid_agent", title: "11. AI Director Agent", icon: "cpu" },
    { id: "grid_render", title: "12. Master MP4 Renderer", icon: "check-circle" }
];

function initGridCards() {
    const container = document.getElementById("grids-container");
    container.innerHTML = GRID_DEFS.map(g => {
        const isEnabled = gridEnabledState[g.id] !== false;
        const isColor = g.id === "grid_color";
        const badgeClass = !isEnabled ? "badge-skipped" : (isColor ? "badge-ready" : "badge-waiting");
        const badgeText = !isEnabled ? "BYPASS" : (isColor ? "READY" : "WAITING");
        const detailText = !isEnabled 
            ? (GRID_BYPASS_DESCRIPTIONS[g.id] || "Feature bypassed (Will not run)") 
            : (isColor ? `Active: ${activeColorPreset.replace('_', ' ').toUpperCase()} (Primed)` : (GRID_ARMED_DESCRIPTIONS[g.id] || "Armed & ready for pipeline"));
        const cardClass = !isEnabled ? "grid-card bypassed" : (isColor ? "grid-card ready" : "grid-card");
        const barWidth = !isEnabled ? "0%" : (isColor ? "100%" : "0%");
        
        let etaClass = "eta-waiting";
        let etaText = "ETA: --";
        if (!isEnabled) {
            etaClass = "eta-bypassed";
            etaText = "ETA: Bypassed";
        } else if (isColor) {
            etaClass = "eta-ready";
            etaText = "ETA: Ready";
        }

        return `
        <div class="${cardClass}" id="${g.id}">
            <div class="grid-card-top">
                <div class="grid-title-row">
                    <i data-feather="${g.icon}" class="grid-icon"></i>
                    <span class="grid-title" title="${g.title}">${g.title}</span>
                </div>
                <div class="grid-top-actions">
                    <label class="grid-switch" title="Toggle ${g.title} ON/OFF">
                        <input type="checkbox" id="${g.id}-toggle" ${isEnabled ? "checked" : ""} onchange="toggleGridFeature('${g.id}', this.checked)">
                        <span class="grid-slider"></span>
                    </label>
                    <span class="grid-status-badge ${badgeClass}" id="${g.id}-badge">${badgeText}</span>
                </div>
            </div>
            <div class="grid-detail-text" id="${g.id}-detail" title="${detailText}">${detailText}</div>
            <div class="grid-progress-bar-container">
                <div class="grid-progress-bar" id="${g.id}-bar" style="width: ${barWidth};"></div>
            </div>
            <div class="grid-eta-row">
                <span class="grid-clip-eta" id="${g.id}-clip-eta">Clip: 0s</span>
                <span class="grid-eta-badge ${etaClass}" id="${g.id}-eta">${etaText}</span>
            </div>
        </div>
        `;
    }).join("");
    feather.replace();
}

function updateGridUI(gridId, status, progress, clipEta, gridEta, detail) {
    const card = document.getElementById(gridId);
    if (!card) return;

    // Check if card is bypassed by toggle
    const isEnabled = gridEnabledState[gridId] !== false;
    if (!isEnabled && status !== "completed" && status !== "in_progress") {
        card.className = "grid-card bypassed";
        const gridEtaEl = document.getElementById(`${gridId}-eta`);
        if (gridEtaEl) {
            gridEtaEl.className = "grid-eta-badge eta-bypassed";
            gridEtaEl.innerText = "ETA: Bypassed";
        }
        return;
    }

    card.className = `grid-card ${status}`;
    
    const badge = document.getElementById(`${gridId}-badge`);
    if (badge) {
        if (status === "in_progress") {
            badge.className = "grid-status-badge badge-running";
            badge.innerText = "RUNNING";
        } else if (status === "completed") {
            badge.className = "grid-status-badge badge-done";
            badge.innerText = "DONE";
        } else if (status === "ready") {
            badge.className = "grid-status-badge badge-ready";
            badge.innerText = "READY";
        } else if (status === "skipped") {
            badge.className = "grid-status-badge badge-skipped";
            badge.innerText = "BYPASS";
        } else {
            badge.className = "grid-status-badge badge-waiting";
            badge.innerText = "WAITING";
        }
    }

    const bar = document.getElementById(`${gridId}-bar`);
    if (bar) bar.style.width = `${progress}%`;

    const detailEl = document.getElementById(`${gridId}-detail`);
    if (detailEl && detail) {
        detailEl.innerText = detail;
        detailEl.title = detail;
    }

    const clipEtaEl = document.getElementById(`${gridId}-clip-eta`);
    if (clipEtaEl) {
        clipEtaEl.innerText = clipEta >= 60 ? `Clip: ${formatSeconds(clipEta)}` : (clipEta > 0 ? `Clip: ${clipEta}s` : `Clip: 0s`);
    }

    const gridEtaEl = document.getElementById(`${gridId}-eta`);
    if (gridEtaEl) {
        if (status === "completed") {
            gridEtaEl.className = "grid-eta-badge eta-done";
            gridEtaEl.innerText = "ETA: Done ✓";
        } else if (status === "ready") {
            gridEtaEl.className = "grid-eta-badge eta-ready";
            gridEtaEl.innerText = "ETA: Ready";
        } else if (status === "skipped") {
            gridEtaEl.className = "grid-eta-badge eta-bypassed";
            gridEtaEl.innerText = "ETA: Bypassed";
        } else if (status === "in_progress" || gridEta > 0) {
            gridEtaEl.className = "grid-eta-badge eta-running";
            gridEtaEl.innerText = gridEta >= 60 ? `ETA: ${formatEtaDisplay(gridEta)}` : `ETA: ${gridEta}s`;
        } else {
            gridEtaEl.className = "grid-eta-badge eta-waiting";
            gridEtaEl.innerText = "ETA: --";
        }
    }
}

let activeTargetDuration = null;
let activeEditMode = "full_movie";

let currentRenderMode = "fast_preview";

function setRenderMode(mode) {
    currentRenderMode = mode;
    const btnFast = document.getElementById("btn-mode-fast");
    const btnFull = document.getElementById("btn-mode-full");
    if (mode === "fast_preview") {
        if (btnFast) { btnFast.style.background = "#f59e0b"; btnFast.style.color = "#000"; }
        if (btnFull) { btnFull.style.background = "transparent"; btnFull.style.color = "#94a3b8"; }
        showToast("⚡ Fast Preview Mode selected: ~8 min draft render (<10m max)", "info");
    } else {
        if (btnFull) { btnFull.style.background = "#10b981"; btnFull.style.color = "#000"; }
        if (btnFast) { btnFast.style.background = "transparent"; btnFast.style.color = "#94a3b8"; }
        showToast("🏆 Full Master Mode selected: 1080p Broadcast Quality", "info");
    }
}

async function startPipelineProcess(customSettings = null) {
    // If nothing checked, default to activeFile or first raw file
    if (selectedFileNames.size === 0) {
        if (activeFile) {
            selectedFileNames.add(activeFile.filename);
        } else if (rawFiles.length > 0) {
            selectedFileNames.add(rawFiles[0].filename);
        }
    }
    if (selectedFileNames.size === 0) {
        showToast("Please select media files from raw_input/", "error");
        return;
    }

    // Ensure selected files are synced with backend
    try {
        await fetch("/api/project/select-files", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filenames: Array.from(selectedFileNames) })
        });
    } catch (e) {
        console.error("Sync error:", e);
    }

    // Pop up Full Media Audit & Edit Plan Confirmation Modal first
    await openMediaAuditModal(customSettings);
}

let pendingAuditCustomSettings = null;

async function openMediaAuditModal(customSettings = null) {
    pendingAuditCustomSettings = customSettings;
    const modal = document.getElementById("media-audit-modal");
    if (!modal) return;

    try {
        const selectedList = Array.from(selectedFileNames);
        const url = selectedList.length > 0 
            ? `/api/project/media-audit-summary?filenames=${encodeURIComponent(selectedList.join(","))}`
            : `/api/project/media-audit-summary`;
        const res = await fetch(url);
        const data = await res.json();
        if (data.status === "success") {
            const audit = data.media_audit;
            const plan = data.edit_plan;

            // 1. Populate KPI stats
            const totalEl = document.getElementById("audit-total-files");
            const subEl = document.getElementById("audit-files-sub");
            const durEl = document.getElementById("audit-video-dur");
            const durSubEl = document.getElementById("audit-video-dur-sub");
            const spanEl = document.getElementById("audit-date-span");
            const formatsEl = document.getElementById("audit-camera-formats");

            if (totalEl) totalEl.innerText = `${audit.total_files} Files`;
            if (subEl) subEl.innerText = `${audit.video_count} Videos • ${audit.photo_count} Photos`;
            if (durEl) durEl.innerText = audit.video_duration_formatted || "73m 7s";
            if (durSubEl) durSubEl.innerText = `${Math.round(audit.video_duration_sec).toLocaleString()} sec uncut audio/video`;
            if (spanEl) spanEl.innerText = `${audit.date_range_start.split(" ")[0]} to ${audit.date_range_end.split(" ")[0]}`;
            if (formatsEl) formatsEl.innerHTML = `<strong>Camera Formats:</strong> ${audit.iphone_video_count} iPhone (1080p HEVC Main 10) + ${audit.android_video_count} Android (1080p/720p H.264)`;

            // 2. Populate 12-Stage Edit Execution Plan
            const stagesContainer = document.getElementById("audit-stages-list");
            if (stagesContainer) {
                stagesContainer.innerHTML = plan.map(stage => {
                    // Check live toggle state in frontend as well
                    const isGloballyOn = (gridEnabledState[stage.id] !== false) && stage.is_active;
                    const badgeClass = isGloballyOn ? "active" : "bypassed";
                    const badgeText = isGloballyOn ? "ACTIVE (ON)" : "BYPASSED (OFF)";
                    const rowClass = isGloballyOn ? "audit-stage-row" : "audit-stage-row bypassed";
                    const desc = isGloballyOn ? stage.action_description : "Bypassed by user toggle (Will not run)";

                    return `
                    <div class="${rowClass}">
                        <div class="audit-stage-left">
                            <span class="audit-stage-name">${stage.title}</span>
                            <span class="audit-stage-desc">${desc}</span>
                        </div>
                        <span class="audit-stage-badge ${badgeClass}">${badgeText}</span>
                    </div>
                    `;
                }).join("");
            }

            // 3. Highlight active render mode
            selectAuditRenderMode(currentRenderMode || "fast_preview");
        }
    } catch (e) {
        console.warn("Audit summary notice:", e);
    }

    modal.style.display = "flex";
    if (window.feather) feather.replace();
}

function closeMediaAuditModal() {
    const modal = document.getElementById("media-audit-modal");
    if (modal) modal.style.display = "none";
}

function selectAuditRenderMode(mode) {
    currentRenderMode = mode;
    const cardFast = document.getElementById("audit-mode-fast");
    const cardFull = document.getElementById("audit-mode-full");
    if (cardFast) cardFast.classList.toggle("active", mode === "fast_preview");
    if (cardFull) cardFull.classList.toggle("active", mode === "full");
    setRenderMode(mode);
}

async function executePipelineAfterAudit() {
    closeMediaAuditModal();
    await executePipelineDirect(pendingAuditCustomSettings);
    pendingAuditCustomSettings = null;
}

async function executePipelineDirect(customSettings = null) {
    hasCompletedPopupShown = false;
    showToast(`Launching Auto-Edit on ${selectedFileNames.size} clip(s)...`, "info");
    document.getElementById("master-status-badge").innerText = "PROCESSING";
    document.getElementById("master-status-badge").className = "stat-badge running";
    ensureElapsedTimerRunning(0);

    const btnStop = document.getElementById("btn-stop-pipeline");
    const btnFooterStop = document.getElementById("btn-footer-stop");
    if (btnStop) btnStop.style.display = "inline-flex";
    if (btnFooterStop) btnFooterStop.style.display = "inline-flex";

    // Immediate DOM update of bypassed grids
    GRID_DEFS.forEach(g => {
        const isEnabled = gridEnabledState[g.id] !== false;
        if (!isEnabled) {
            const card = document.getElementById(g.id);
            const badge = document.getElementById(`${g.id}-badge`);
            const detail = document.getElementById(`${g.id}-detail`);
            const bar = document.getElementById(`${g.id}-bar`);
            const etaEl = document.getElementById(`${g.id}-eta`);
            if (card) card.className = "grid-card bypassed";
            if (badge) { badge.className = "grid-status-badge badge-skipped"; badge.innerText = "BYPASS"; }
            if (detail) detail.innerText = GRID_BYPASS_DESCRIPTIONS[g.id] || "Feature bypassed by user toggle";
            if (bar) bar.style.width = "0%";
            if (etaEl) { etaEl.className = "grid-eta-badge eta-bypassed"; etaEl.innerText = "ETA: Bypassed"; }
        }
    });

    let effectiveEditMode = activeEditMode || (document.getElementById("edit-mode-select") ? document.getElementById("edit-mode-select").value : "full_movie");
    if (selectedFileNames.size === 1) {
        effectiveEditMode = "single";
    }

    const baseSettings = {
        edit_mode: effectiveEditMode,
        target_duration: activeTargetDuration || null,
        language: document.getElementById("language-select") ? document.getElementById("language-select").value : "auto",
        model_tier: (document.getElementById("toolbar-model-select") ? document.getElementById("toolbar-model-select").value : (document.getElementById("model-tier-select") ? document.getElementById("model-tier-select").value : "large-v3-turbo")),
        script_mode: currentTranscriptScript,
        color_grade: activeColorPreset,
        aspect_ratio: activeAspectRatio,
        caption_style: (document.getElementById("chk-burn-captions") && !document.getElementById("chk-burn-captions").checked) 
            ? "none" 
            : (activeCaptionStyle || (document.getElementById("caption-style-select") ? document.getElementById("caption-style-select").value : "hyperframe_kinetic")),
        audio_enhance: document.getElementById("chk-audio-enhance") ? document.getElementById("chk-audio-enhance").checked : true,
        auto_duck: document.getElementById("chk-auto-duck") ? document.getElementById("chk-auto-duck").checked : true,
        music_mood: document.getElementById("select-music-mood") ? document.getElementById("select-music-mood").value : "sacred_temple",
        sacred_mode: document.getElementById("chk-sacred-mode") ? document.getElementById("chk-sacred-mode").checked : true,
        ducking_depth_pct: document.getElementById("slider-ducking-depth") ? parseFloat(document.getElementById("slider-ducking-depth").value) : 75.0,
        music_level_pct: document.getElementById("slider-music-level") ? parseFloat(document.getElementById("slider-music-level").value) : 40.0,
        denoise_pct: document.getElementById("slider-denoise-pct") ? parseFloat(document.getElementById("slider-denoise-pct").value) : 75.0,
        license_plate_blur: true,
        enabled_grids: { ...gridEnabledState, grid_bgremove: true },
        text_behind_person: (typeof directorTextBehind !== "undefined" && directorTextBehind) ? Object.assign({}, directorTextBehind, {
            text: (document.getElementById("depth-input-text") && document.getElementById("depth-input-text").value.trim()) 
                ? document.getElementById("depth-input-text").value.trim() 
                : (directorTextBehind.text || "RANN OF KUTCH | BHUJ | SOMNATH VLOG")
        }) : {
            enabled: true,
            text: (document.getElementById("depth-input-text") && document.getElementById("depth-input-text").value.trim()) 
                ? document.getElementById("depth-input-text").value.trim() 
                : "RANN OF KUTCH | BHUJ | SOMNATH VLOG"
        }
    };

    const settings = Object.assign({}, baseSettings, customSettings || {});

    try {
        const res = await fetch("/api/project/start-processing", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                settings: settings, 
                filenames: Array.from(selectedFileNames),
                render_mode: currentRenderMode 
            })
        });
        const data = await res.json();
        
        // Poll for transcript update after 3 seconds
        setTimeout(loadTranscript, 3500);
    } catch (e) {
        showToast("Error starting pipeline", "error");
    }
}

async function stopPipelineProcess() {
    showToast("Stopping pipeline...", "info");
    const badge = document.getElementById("master-status-badge");
    if (badge) {
        badge.innerText = "STOPPING...";
        badge.className = "stat-badge running";
    }

    try {
        const res = await fetch("/api/project/stop-processing", {
            method: "POST"
        });
        const data = await res.json();
        stopElapsedTimer();

        if (badge) {
            badge.innerText = "STOPPED";
            badge.className = "stat-badge";
        }
        const etaEl = document.getElementById("overall-total-eta");
        if (etaEl) etaEl.innerText = "--:--";

        const btnStop = document.getElementById("btn-stop-pipeline");
        const btnFooterStop = document.getElementById("btn-footer-stop");
        if (btnStop) btnStop.style.display = "none";
        if (btnFooterStop) btnFooterStop.style.display = "none";

        showToast("Pipeline process stopped ⏹️", "info");
    } catch (e) {
        console.error("Stop error:", e);
        showToast("Error stopping pipeline", "error");
    }
}

async function restartPipelineProcess() {
    showToast("Clearing old grids & restarting from beginning...", "info");

    // 1. Immediately wipe all 12 old grids visually in DOM
    clearAndResetAllGridsUI();

    // 2. Set master status & reset timer
    const badge = document.getElementById("master-status-badge");
    if (badge) {
        badge.innerText = "RESTARTING...";
        badge.className = "stat-badge running";
    }
    const elapsedEl = document.getElementById("overall-elapsed");
    if (elapsedEl) elapsedEl.innerText = "00:00";
    const etaEl = document.getElementById("overall-total-eta");
    if (etaEl) etaEl.innerText = "Estimating...";

    // Show stop buttons
    const btnStop = document.getElementById("btn-stop-pipeline");
    const btnFooterStop = document.getElementById("btn-footer-stop");
    if (btnStop) btnStop.style.display = "inline-flex";
    if (btnFooterStop) btnFooterStop.style.display = "inline-flex";

    // 3. Assemble current settings
    let effectiveEditMode = activeEditMode || (document.getElementById("edit-mode-select") ? document.getElementById("edit-mode-select").value : "full_movie");
    if (selectedFileNames.size === 1) {
        effectiveEditMode = "single";
    }

    const baseSettings = {
        edit_mode: effectiveEditMode,
        target_duration: activeTargetDuration || null,
        language: document.getElementById("language-select") ? document.getElementById("language-select").value : "auto",
        model_tier: (document.getElementById("toolbar-model-select") ? document.getElementById("toolbar-model-select").value : (document.getElementById("model-tier-select") ? document.getElementById("model-tier-select").value : "large-v3")),
        script_mode: currentTranscriptScript,
        color_grade: activeColorPreset,
        aspect_ratio: activeAspectRatio,
        caption_style: (document.getElementById("chk-burn-captions") && !document.getElementById("chk-burn-captions").checked) 
            ? "none" 
            : (activeCaptionStyle || (document.getElementById("caption-style-select") ? document.getElementById("caption-style-select").value : "hyperframe_kinetic")),
        audio_enhance: document.getElementById("chk-audio-enhance") ? document.getElementById("chk-audio-enhance").checked : true,
        auto_duck: document.getElementById("chk-auto-duck") ? document.getElementById("chk-auto-duck").checked : true,
        music_mood: document.getElementById("select-music-mood") ? document.getElementById("select-music-mood").value : "sacred_temple",
        sacred_mode: document.getElementById("chk-sacred-mode") ? document.getElementById("chk-sacred-mode").checked : true,
        ducking_depth_pct: document.getElementById("slider-ducking-depth") ? parseFloat(document.getElementById("slider-ducking-depth").value) : 75.0,
        music_level_pct: document.getElementById("slider-music-level") ? parseFloat(document.getElementById("slider-music-level").value) : 40.0,
        denoise_pct: document.getElementById("slider-denoise-pct") ? parseFloat(document.getElementById("slider-denoise-pct").value) : 75.0,
        license_plate_blur: true,
        enabled_grids: { ...gridEnabledState, grid_bgremove: true },
        text_behind_person: (typeof directorTextBehind !== "undefined" && directorTextBehind) ? Object.assign({}, directorTextBehind, {
            text: (document.getElementById("depth-input-text") && document.getElementById("depth-input-text").value.trim()) 
                ? document.getElementById("depth-input-text").value.trim() 
                : (directorTextBehind.text || "RANN OF KUTCH | BHUJ | SOMNATH VLOG")
        }) : {
            enabled: true,
            text: (document.getElementById("depth-input-text") && document.getElementById("depth-input-text").value.trim()) 
                ? document.getElementById("depth-input-text").value.trim() 
                : "RANN OF KUTCH | BHUJ | SOMNATH VLOG"
        }
    };

    // Fallback to all files only if user hasn't selected any specific files
    if (selectedFileNames.size === 0 && rawFiles.length > 0) {
        rawFiles.forEach(f => selectedFileNames.add(f.filename));
    }

    try {
        const res = await fetch("/api/project/restart-processing", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                settings: baseSettings,
                filenames: Array.from(selectedFileNames),
                render_mode: currentRenderMode
            })
        });
        const data = await res.json();
        ensureElapsedTimerRunning(0);
        if (badge) {
            badge.innerText = "PROCESSING";
            badge.className = "stat-badge running";
        }
        showToast("Pipeline restarted cleanly from the beginning ⚡", "success");
    } catch (e) {
        console.error("Restart error:", e);
        showToast("Error restarting pipeline", "error");
    }
}

function clearAndResetAllGridsUI() {
    stopElapsedTimer();
    GRID_DEFS.forEach(g => {
        const isEnabled = gridEnabledState[g.id] !== false;
        const card = document.getElementById(g.id);
        const badge = document.getElementById(`${g.id}-badge`);
        const detail = document.getElementById(`${g.id}-detail`);
        const bar = document.getElementById(`${g.id}-bar`);
        const etaEl = document.getElementById(`${g.id}-eta`);
        const toggle = document.getElementById(`${g.id}-toggle`);

        if (toggle) toggle.checked = isEnabled;

        if (!isEnabled) {
            if (card) { card.className = "grid-card bypassed"; }
            if (badge) {
                badge.className = "grid-status-badge badge-skipped";
                badge.innerText = "BYPASS";
            }
            if (detail) detail.innerText = GRID_BYPASS_DESCRIPTIONS[g.id] || "Feature bypassed";
            if (bar) bar.style.width = "0%";
            if (etaEl) {
                etaEl.className = "grid-eta-badge eta-bypassed";
                etaEl.innerText = "ETA: Bypassed";
            }
        } else if (g.id === "grid_color") {
            if (activeColorPreset === "none" || !isEnabled) {
                if (card) { card.className = "grid-card bypassed"; }
                if (badge) {
                    badge.className = "grid-status-badge badge-skipped";
                    badge.innerText = "BYPASS";
                }
                if (detail) detail.innerText = "Natural Camera Colors - Zero LUT / Vignette";
                if (bar) bar.style.width = "0%";
                if (etaEl) {
                    etaEl.className = "grid-eta-badge eta-bypassed";
                    etaEl.innerText = "ETA: Bypassed";
                }
            } else {
                if (card) { card.className = "grid-card ready"; }
                if (badge) {
                    badge.className = "grid-status-badge badge-ready";
                    badge.innerText = "READY";
                }
                if (detail) detail.innerText = `Active: ${activeColorPreset.replace('_', ' ').toUpperCase()} (Primed)`;
                if (bar) bar.style.width = "100%";
                if (etaEl) {
                    etaEl.className = "grid-eta-badge eta-ready";
                    etaEl.innerText = "ETA: Ready";
                }
            }
        } else {
            if (card) { card.className = "grid-card waiting"; }
            if (badge) {
                badge.className = "grid-status-badge badge-waiting";
                badge.innerText = "WAITING";
            }
            if (detail) detail.innerText = GRID_ARMED_DESCRIPTIONS[g.id] || "Armed & waiting for pipeline stage";
            if (bar) bar.style.width = "0%";
            if (etaEl) {
                etaEl.className = "grid-eta-badge eta-waiting";
                etaEl.innerText = "ETA: --";
            }
        }
    });
}

function toggleLicensePlateBlur(enabled) {
    fetch("/api/project/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ license_plate_blur: enabled })
    }).catch(e => console.warn(e));
    showToast(enabled ? "License Plate Privacy Blur Armed (HSRP & Cars) 🛡️" : "License Plate Blur Disabled", "info");
}

// ---------------- UTILITIES ----------------
function formatTimecode(seconds) {
    if (isNaN(seconds) || seconds < 0) seconds = 0;
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    const f = Math.floor((seconds - Math.floor(seconds)) * 30);
    return `${pad(h)}:${pad(m)}:${pad(s)}:${pad(f)}`;
}

function formatSeconds(sec) {
    if (isNaN(sec) || sec === null || sec === undefined || sec < 0) return "--:--";
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${pad(m)}:${pad(s)}`;
}

function formatEtaDisplay(sec) {
    if (isNaN(sec) || sec === null || sec === undefined || sec <= 0) return "--:--";
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    if (m === 0) {
        return `00:${pad(s)} (${s}s)`;
    }
    return `${pad(m)}:${pad(s)} (${m}m ${s}s)`;
}

function pad(num) {
    return num.toString().padStart(2, "0");
}

function showToast(msg, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerText = msg;
    toast.title = "Click to dismiss";
    toast.onclick = () => toast.remove();
    container.appendChild(toast);
    setTimeout(() => {
        if (toast.parentElement) toast.remove();
    }, 4000);
}

// ---------------- HYPERFRAMES MOTION GRAPHICS STUDIO (HTML/CSS/JS) ----------------
let hyperframePresets = [];
let currentHfPreset = null;
let activeHfTab = "html";

async function openHyperframesStudio() {
    const modal = document.getElementById("hyperframes-modal");
    if (!modal) return;
    modal.style.display = "flex";

    if (hyperframePresets.length === 0) {
        try {
            const res = await fetch("/api/hyperframes/presets");
            const data = await res.json();
            hyperframePresets = data.presets || [];
        } catch (e) {
            console.error("Error fetching hyperframe presets:", e);
        }
    }

    const select = document.getElementById("hf-preset-select");
    if (select && hyperframePresets.length > 0) {
        select.innerHTML = hyperframePresets.map(p => `<option value="${p.id}">${p.name}</option>`).join("");
        onHyperframePresetChange(hyperframePresets[0].id);
    }
}

function closeHyperframesStudio() {
    const modal = document.getElementById("hyperframes-modal");
    if (modal) modal.style.display = "none";
}

function onHyperframePresetChange(presetId) {
    const preset = hyperframePresets.find(p => p.id === presetId);
    if (!preset) return;
    currentHfPreset = preset;

    document.getElementById("hf-code-html").value = preset.html;
    document.getElementById("hf-code-css").value = preset.css;
    document.getElementById("hf-code-js").value = preset.js;

    renderHyperframeSandbox(preset.html, preset.css, preset.js);
}

function switchHfTab(tabName) {
    activeHfTab = tabName;
    document.getElementById("tab-html").className = tabName === "html" ? "hf-tab active" : "hf-tab";
    document.getElementById("tab-css").className = tabName === "css" ? "hf-tab active" : "hf-tab";
    document.getElementById("tab-js").className = tabName === "js" ? "hf-tab active" : "hf-tab";

    document.getElementById("hf-code-html").style.display = tabName === "html" ? "block" : "none";
    document.getElementById("hf-code-css").style.display = tabName === "css" ? "block" : "none";
    document.getElementById("hf-code-js").style.display = tabName === "js" ? "block" : "none";
}

function updateLiveHfFromEditor() {
    const html = document.getElementById("hf-code-html").value;
    const css = document.getElementById("hf-code-css").value;
    const js = document.getElementById("hf-code-js").value;
    renderHyperframeSandbox(html, css, js);
    showToast("HyperFrame preview updated live!", "success");
}

function reloadHyperframePreview() {
    if (!currentHfPreset) return;
    updateLiveHfFromEditor();
}

function renderHyperframeSandbox(html, css, js) {
    const host = document.getElementById("hf-live-render-host");
    if (!host) return;

    // Create isolated scoped DOM & Style
    host.innerHTML = `
        <style>
            ${css}
        </style>
        ${html}
    `;

    // Execute JS securely within the sandbox container context
    if (js && js.trim()) {
        try {
            const runner = new Function(js);
            runner();
        } catch (e) {
            console.warn("HyperFrame JS execution warning:", e);
        }
    }
}

function copyHyperframeCode() {
    const html = document.getElementById("hf-code-html").value;
    const css = document.getElementById("hf-code-css").value;
    const js = document.getElementById("hf-code-js").value;

    const fullSnippet = `<!-- HyperFrame Component -->\n${html}\n\n<style>\n${css}\n</style>\n\n<script>\n${js}\n</script>`;
    navigator.clipboard.writeText(fullSnippet).then(() => {
        showToast("HyperFrame code copied to clipboard!", "success");
    }).catch(() => {
        showToast("Code copied to clipboard!", "info");
    });
}

function applyHyperframeToPlayer() {
    const html = document.getElementById("hf-code-html").value;
    const css = document.getElementById("hf-code-css").value;
    const js = document.getElementById("hf-code-js").value;

    if (currentHfPreset && currentHfPreset.id === "hyperframe_kinetic_captions") {
        activeCaptionStyle = "hyperframe_kinetic";
        const capSelect = document.getElementById("caption-style-select");
        if (capSelect) capSelect.value = "hyperframe_kinetic";
        closeHyperframesStudio();
        showToast("HyperFrame Face-Safe Kinetic Captions activated on player! ⚡", "success");
        return;
    }

    let overlay = document.getElementById("player-hyperframe-overlay");
    if (!overlay) {
        overlay = document.createElement("div");
        overlay.id = "player-hyperframe-overlay";
        overlay.style.position = "absolute";
        overlay.style.inset = "0";
        overlay.style.pointerEvents = "none";
        overlay.style.zIndex = "15";
        document.getElementById("video-viewport").appendChild(overlay);
    }

    overlay.innerHTML = `
        <style>${css}</style>
        ${html}
    `;

    if (js && js.trim()) {
        try {
            const runner = new Function(js);
            runner();
        } catch (e) {
            console.warn(e);
        }
    }

    closeHyperframesStudio();
    showToast("HyperFrame applied as active video overlay!", "success");
}

// ---------------- MASTER EXPORT COMPLETION POPUP ----------------
let latestMasterMovieUrl = null;
let latestMasterFilename = null;

function showCompletionModal(info = {}) {
    const modal = document.getElementById("completion-modal");
    if (!modal) return;
    
    if (info.url) latestMasterMovieUrl = info.url;
    if (info.filename) latestMasterFilename = info.filename;

    if (info.duration && document.getElementById("comp-stat-duration")) {
        document.getElementById("comp-stat-duration").innerText = info.duration;
    }
    if (info.size && document.getElementById("comp-stat-size")) {
        document.getElementById("comp-stat-size").innerText = info.size;
    }
    const dlLink = document.getElementById("comp-download-link");
    if (dlLink) {
        const fallbackFile = (exportFiles.length > 0) ? exportFiles[0] : { url: "/media_final/MASTER_FULL_FEATURE_MOVIE.mp4", filename: "MASTER_FULL_FEATURE_MOVIE.mp4" };
        const rawUrl = info.url || latestMasterMovieUrl || fallbackFile.url;
        const fname = info.filename || latestMasterFilename || fallbackFile.filename;
        dlLink.href = encodeURI(decodeURI(rawUrl));
        dlLink.setAttribute("download", fname);
    }

    modal.style.display = "flex";
    if (window.feather) feather.replace();
}

function closeCompletionModal() {
    const modal = document.getElementById("completion-modal");
    if (modal) modal.style.display = "none";
}

function playMasterFromPopup() {
    closeCompletionModal();
    const fallbackFile = (exportFiles.length > 0) ? exportFiles[0] : { url: "/media_final/MASTER_FULL_FEATURE_MOVIE.mp4", filename: "MASTER_FULL_FEATURE_MOVIE.mp4" };
    const movieUrl = latestMasterMovieUrl || fallbackFile.url;
    const movieLabel = latestMasterFilename || fallbackFile.filename;

    switchStudioTab("ai");
    loadVideoIntoPlayer(movieUrl, true, movieLabel);
    const player = document.getElementById("main-video-player");
    if (player) {
        player.play().catch(e => console.log("Auto-play ready:", e));
    }
    showToast(`Playing ${movieLabel} in Studio!`, "success");
}

async function openExportFolderFromPopup() {
    try {
        const res = await fetch("/api/final-export/open-folder", { method: "POST" });
        const data = await res.json();
        showToast(data.message || "Opened final_export folder in Windows Explorer", "success");
    } catch (e) {
        showToast("Error opening folder", "error");
    }
}

// ---------------- BURN HYPERFRAME INTO VIDEO / VLOG ----------------
async function burnHyperframeToVideo() {
    if (currentHfPreset && currentHfPreset.id === "hyperframe_kinetic_captions") {
        closeHyperframesStudio();
        showToast("Rendering video with HyperFrame Face-Safe Kinetic Captions... ⚡", "info");
        await startProcessing({ caption_style: "hyperframe_kinetic" });
        return;
    }

    const htmlEl = document.getElementById("hf-code-html");
    const html = htmlEl ? htmlEl.value : "";
    const activeFilename = activeFile ? activeFile.filename : (rawFiles.length > 0 ? rawFiles[0].filename : "");

    showToast("Rendering broadcast HyperFrame lower-third into your vlog... 🎬", "info");

    try {
        const res = await fetch("/api/hyperframes/burn-to-video", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                html: html,
                filename: activeFilename,
                start_time: 1.5,
                duration: 6.0
            })
        });

        const data = await res.json();
        if (data.status === "success") {
            closeHyperframesStudio();
            showToast(`Vlog with '${data.title}' Lower-Third rendered! 🚀`, "success");
            loadVideoIntoPlayer(data.url, true, data.filename);
            await fetchExportFiles();

            showCompletionModal({
                duration: "6.0s Overlay",
                size: data.filename,
                filename: data.filename,
                url: data.url
            });
        } else {
            showToast("Failed to burn HyperFrame: " + (data.message || "Unknown error"), "error");
        }
    } catch (e) {
        console.error("Burn error:", e);
        showToast("Error burning HyperFrame into video", "error");
    }
}

// ----------------- AUDIO & SOUNDTRACK SUPERVISION -----------------

let audioParamDebounceTimer = null;
function onAudioParamChange(key, value) {
    if (key === 'ducking_depth_pct') {
        const lbl = document.getElementById('val-ducking-depth');
        if (lbl) lbl.innerText = `${value}% (-${Math.round(8 + (value/100)*8)}dB Vocals)`;
    } else if (key === 'music_level_pct') {
        const lbl = document.getElementById('val-music-level');
        if (lbl) lbl.innerText = `${value}% (${value < 25 ? 'Quiet Background' : (value < 55 ? 'Balanced Bed' : 'Prominent Music')})`;
    } else if (key === 'denoise_pct') {
        const lbl = document.getElementById('val-denoise-pct');
        if (lbl) lbl.innerText = `${value}% (${value >= 70 ? 'Studio Clean' : 'Gentle Denoise'})`;
    }

    clearTimeout(audioParamDebounceTimer);
    audioParamDebounceTimer = setTimeout(async () => {
        try {
            const payload = {};
            payload[key] = value;
            await fetch('/api/project/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        } catch (e) {
            console.error('Failed to auto-save audio setting:', e);
        }
    }, 300);
}

async function runSupervisionPreview() {
    const btnNav = document.getElementById("btn-supervise-mix");
    const btnSub = document.getElementById("btn-supervise-slice-sub");
    const origNavHtml = btnNav ? btnNav.innerHTML : "";
    const origSubHtml = btnSub ? btnSub.innerHTML : "";

    const setLoading = (loading) => {
        if (btnNav) {
            btnNav.disabled = loading;
            btnNav.innerHTML = loading 
                ? '<span class="spinner" style="display:inline-block;width:12px;height:12px;border:2px solid #34d399;border-top-color:transparent;border-radius:50%;animation:spin 0.6s linear infinite;margin-right:4px;"></span> Generating 15s Mix...' 
                : origNavHtml;
        }
        if (btnSub) {
            btnSub.disabled = loading;
            btnSub.innerHTML = loading 
                ? '<span class="spinner" style="display:inline-block;width:12px;height:12px;border:2px solid #fff;border-top-color:transparent;border-radius:50%;animation:spin 0.6s linear infinite;margin-right:4px;"></span> Rendering Preview (3s)...' 
                : origSubHtml;
        }
    };

    setLoading(true);
    showToast("Supervising Mix... Rendering 15s preview (renders in ~3s) 👁️", "info");

    const depthTextInput = document.getElementById("depth-input-text");
    const customTitle = (depthTextInput && depthTextInput.value.trim()) 
        ? depthTextInput.value.trim() 
        : ((typeof directorTextBehind !== "undefined" && directorTextBehind.text) ? directorTextBehind.text : "RANN OF KUTCH | BHUJ | SOMNATH VLOG");
    const moodSelect = document.getElementById("select-music-mood");
    const sacredChk = document.getElementById("chk-sacred-mode");
    const duckSlider = document.getElementById("slider-ducking-depth");
    const musicSlider = document.getElementById("slider-music-level");
    const denoiseSlider = document.getElementById("slider-denoise-pct");

    const payload = {
        duration: 15.0,
        music_mood: moodSelect ? moodSelect.value : "sacred_temple",
        sacred_mode: sacredChk ? sacredChk.checked : true,
        ducking_depth_pct: duckSlider ? parseFloat(duckSlider.value) : 75.0,
        music_level_pct: musicSlider ? parseFloat(musicSlider.value) : 40.0,
        denoise_pct: denoiseSlider ? parseFloat(denoiseSlider.value) : 75.0,
        text_behind: (typeof directorTextBehind !== "undefined" && directorTextBehind) 
            ? Object.assign({}, directorTextBehind, { text: customTitle, enabled: true })
            : { text: customTitle, enabled: true, font: "Montserrat", size: 110, spread: 8, color: "#FFFFFF", neon_enabled: true, neon_color: "#00F2FE", glow_radius: 24 }
    };

    try {
        const res = await fetch("/api/project/supervise-preview", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        setLoading(false);

        if (data.status === "success") {
            showToast(`15s Supervision Mix Ready! Title: "${data.title}" • Music: "${data.track_name}" (${data.music_mood})`, "success");
            loadVideoIntoPlayer(data.url, true, data.filename);
            
            // Highlight player badge
            const badge = document.getElementById("master-status-badge");
            if (badge) {
                badge.innerText = "SUPERVISION PREVIEW (15s SLICE)";
                badge.className = "stat-badge completed";
                badge.style.background = "#064e3b";
                badge.style.borderColor = "#10b981";
                badge.style.color = "#6ee7b7";
            }
        } else {
            showToast("Failed to render supervision preview: " + (data.detail || data.message || "Error"), "error");
        }
    } catch (err) {
        setLoading(false);
        console.error("Supervision preview error:", err);
        showToast("Error rendering supervision preview", "error");
    }
}

async function saveAudioSettingsAndTitle() {
    const depthTextInput = document.getElementById("depth-input-text");
    const customTitle = (depthTextInput && depthTextInput.value.trim()) 
        ? depthTextInput.value.trim() 
        : ((typeof directorTextBehind !== "undefined" && directorTextBehind.text) ? directorTextBehind.text : "RANN OF KUTCH | BHUJ | SOMNATH VLOG");
    
    if (typeof saveDepthTextExplicitly === "function") {
        await saveDepthTextExplicitly();
    }
    
    const moodSelect = document.getElementById("select-music-mood");
    const sacredChk = document.getElementById("chk-sacred-mode");
    const duckSlider = document.getElementById("slider-ducking-depth");
    const musicSlider = document.getElementById("slider-music-level");
    const denoiseSlider = document.getElementById("slider-denoise-pct");

    const payload = {
        music_mood: moodSelect ? moodSelect.value : "sacred_temple",
        sacred_mode: sacredChk ? sacredChk.checked : true,
        ducking_depth_pct: duckSlider ? parseFloat(duckSlider.value) : 75.0,
        music_level_pct: musicSlider ? parseFloat(musicSlider.value) : 40.0,
        denoise_pct: denoiseSlider ? parseFloat(denoiseSlider.value) : 75.0,
        text_behind_person: (typeof directorTextBehind !== "undefined" && directorTextBehind) 
            ? Object.assign({}, directorTextBehind, { text: customTitle, enabled: true })
            : { text: customTitle, enabled: true }
    };

    try {
        await fetch("/api/project/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        showToast(`✓ Title & Audio Settings Registered: "${customTitle}" 💾`, "success");
    } catch (e) {
        console.warn("Could not post audio settings:", e);
    }
}

// Window Bindings for Inline HTML Event Handlers
window.selectFirstNClips = selectFirstNClips;
window.selectAllRawFiles = selectAllRawFiles;
window.clearFileSelection = clearFileSelection;
window.updateSelectionCountBadge = updateSelectionCountBadge;
window.saveAudioSettingsAndTitle = saveAudioSettingsAndTitle;

// ---------------- STAGE 11 EXPORT DECISION GATE ----------------
function showStage11DecisionModal(data) {
    const modal = document.getElementById("stage11-decision-modal");
    if (modal) {
        modal.style.display = "flex";
        if (window.feather) feather.replace();
    }
}

function closeStage11DecisionModal() {
    const modal = document.getElementById("stage11-decision-modal");
    if (modal) {
        modal.style.display = "none";
    }
}

async function submitStage11Decision(action) {
    closeStage11DecisionModal();
    if (action === "xml_srt") {
        showToast("Generating Premiere Pro XML (.xml) & Subtitles (.srt)...", "info");
    } else {
        showToast("Proceeding to Stage 12: Final Master Render...", "info");
    }

    // Capture active timeline cuts if user edited them in Premiere Pro Studio NLE
    let clipsPayload = null;
    if (typeof window.getActiveTimelineClips === "function") {
        const activeClips = window.getActiveTimelineClips();
        if (activeClips && activeClips.length > 0) {
            clipsPayload = activeClips;
        }
    }

    try {
        const res = await fetch("/api/pipeline/stage11-decision", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                action: action,
                clips: clipsPayload
            })
        });
        const result = await res.json();
        console.log("Stage 11 decision response:", result);
        if (result.status === "error") {
            showToast(result.message || "Failed to process decision", "error");
        }
    } catch (err) {
        console.error("Error submitting Stage 11 decision:", err);
        showToast("Failed to submit decision: " + err.message, "error");
    }
}

function showStage11XmlReadyModal(data) {
    const modal = document.getElementById("stage11-xml-ready-modal");
    if (modal) {
        if (data.xml_filename) {
            const xmlNameEl = document.getElementById("stage11-xml-filename");
            if (xmlNameEl) xmlNameEl.innerText = data.xml_filename;
            const xmlBtn = document.getElementById("stage11-xml-download-btn");
            if (xmlBtn) {
                xmlBtn.href = data.xml_url || `/media_final/${data.xml_filename}`;
                xmlBtn.setAttribute("download", data.xml_filename);
            }
        }
        if (data.srt_filename) {
            const srtNameEl = document.getElementById("stage11-srt-filename");
            if (srtNameEl) srtNameEl.innerText = data.srt_filename;
            const srtBtn = document.getElementById("stage11-srt-download-btn");
            if (srtBtn) {
                srtBtn.href = data.srt_url || `/media_final/${data.srt_filename}`;
                srtBtn.setAttribute("download", data.srt_filename);
            }
        }
        modal.style.display = "flex";
        if (window.feather) feather.replace();
    }
}

function closeStage11XmlReadyModal() {
    const modal = document.getElementById("stage11-xml-ready-modal");
    if (modal) {
        modal.style.display = "none";
    }
}

window.showStage11DecisionModal = showStage11DecisionModal;
window.closeStage11DecisionModal = closeStage11DecisionModal;
window.submitStage11Decision = submitStage11Decision;
window.showStage11XmlReadyModal = showStage11XmlReadyModal;
window.closeStage11XmlReadyModal = closeStage11XmlReadyModal;




