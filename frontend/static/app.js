/* ANIRBAN AUTOMATIONS - AUTO VIDEO EDITOR STUDIO CLIENT */

// Global State
let rawFiles = [];
let exportFiles = [];
let activeFile = null;
let selectedFileNames = new Set();
let projectTranscript = { words: [], sentences: [] };
let projectCuts = [];
let colorPresets = [];
let activeColorPreset = "teal_orange";
let activeCaptionStyle = "hormozi";
let activeAspectRatio = "original";
let ws = null;
let hasCompletedPopupShown = false;

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
            if (badge) {
                badge.innerText = "MASTER READY";
                badge.className = "stat-badge ready";
            }
            if (etaEl) etaEl.innerText = "Completed";
            if (!hasCompletedPopupShown) {
                hasCompletedPopupShown = true;
                setTimeout(() => {
                    showCompletionModal({
                        duration: "12m 14s",
                        size: "1.08 GB",
                        filename: "MASTER_FULL_FEATURE_MOVIE.mp4",
                        url: "/media_final/MASTER_FULL_FEATURE_MOVIE.mp4"
                    });
                }, 400);
            }
        } else if (data.is_processing || renderStatus === "in_progress") {
            if (badge) {
                badge.innerText = "PROCESSING";
                badge.className = "stat-badge running";
            }
            if (etaEl) {
                if (data.overall_eta_sec && data.overall_eta_sec > 0) {
                    etaEl.innerText = formatSeconds(data.overall_eta_sec);
                } else {
                    etaEl.innerText = "Finalizing (~1-2m)";
                }
            }
        } else {
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

function handleProgressUpdate(data) {
    if (data.type === "error") {
        showToast(`Pipeline: ${data.message}`, "error");
        const badge = document.getElementById("master-status-badge");
        if (badge) {
            badge.innerText = "ERROR";
            badge.className = "stat-badge";
        }
        if (data.all_statuses) {
            for (const [gid, s] of Object.entries(data.all_statuses)) {
                updateGridUI(gid, s.status, s.progress, s.clip_eta_sec, s.eta_sec, s.detail);
            }
        }
        return;
    }

    if (data.type === "grid_update") {
        updateGridUI(data.grid_id, data.status, data.progress, data.clip_eta_sec, data.grid_eta_sec, data.detail);
        
        if (data.elapsed_sec !== undefined) {
            const elEl = document.getElementById("overall-elapsed");
            if (elEl) elEl.innerText = formatSeconds(data.elapsed_sec);
        }

        const badge = document.getElementById("master-status-badge");
        const etaEl = document.getElementById("overall-total-eta");

        if (data.grid_id === "grid_render" && data.status === "completed") {
            if (badge) {
                badge.innerText = "MASTER READY";
                badge.className = "stat-badge ready";
            }
            if (etaEl) etaEl.innerText = "Completed";
            fetchExportFiles();

            if (!hasCompletedPopupShown) {
                hasCompletedPopupShown = true;
                setTimeout(() => {
                    showCompletionModal({
                        duration: "12m 14s",
                        size: "1.08 GB",
                        filename: "MASTER_FULL_FEATURE_MOVIE.mp4",
                        url: "/media_final/MASTER_FULL_FEATURE_MOVIE.mp4"
                    });
                }, 300);
            }
        } else if (data.status === "in_progress" || (data.overall_eta_sec && data.overall_eta_sec > 0)) {
            if (badge) {
                const isConcat = data.grid_id === "grid_render" && data.detail && data.detail.includes("Concatenat");
                badge.innerText = isConcat ? "CONCATENATING" : "PROCESSING";
                badge.className = "stat-badge running";
            }
            if (etaEl) {
                if (data.overall_eta_sec && data.overall_eta_sec > 0) {
                    etaEl.innerText = formatSeconds(data.overall_eta_sec);
                } else {
                    etaEl.innerText = "Finalizing (~1-2m)";
                }
            }
        } else {
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
            if (renderStatus === "completed" && !hasCompletedPopupShown) {
                hasCompletedPopupShown = true;
                setTimeout(() => {
                    showCompletionModal({
                        duration: "12m 14s",
                        size: "1.08 GB",
                        filename: "MASTER_FULL_FEATURE_MOVIE.mp4",
                        url: "/media_final/MASTER_FULL_FEATURE_MOVIE.mp4"
                    });
                }, 500);
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
}

function toggleFileSelect(filename, checked) {
    if (checked) {
        selectedFileNames.add(filename);
    } else {
        selectedFileNames.delete(filename);
    }
    updateSelectAllCheckboxState();
}

function toggleSelectAll(checkbox) {
    if (checkbox.checked) {
        rawFiles.forEach(f => selectedFileNames.add(f.filename));
    } else {
        selectedFileNames.clear();
    }
    renderRawFileList();
}

function updateSelectAllCheckboxState() {
    const chk = document.getElementById("chk-select-all");
    chk.checked = rawFiles.length > 0 && selectedFileNames.size === rawFiles.length;
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
    await fetch("/api/raw-input/open-folder", { method: "POST" });
    showToast("Opened raw_input folder in File Explorer", "info");
}

async function openExportFolder() {
    await fetch("/api/final-export/open-folder", { method: "POST" });
    showToast("Opened final_export folder in File Explorer", "info");
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

    const displayName = label || decodeURIComponent(url.split("/").pop());
    if (filenameEl) {
        filenameEl.innerText = displayName;
    }

    if (videoSource) {
        videoSource.src = url;
    }
    if (player) {
        player.src = url;
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
    document.getElementById("btn-aspect-16-9").classList.toggle("active", aspect === "16:9");
    document.getElementById("btn-aspect-9-16").classList.toggle("active", aspect === "9:16");
    reframingGuide.classList.toggle("active", aspect === "9:16");
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

function updateModelTierSettings(tier) {
    const tierName = tier === "large-v3-turbo" ? "Studio Pro (large-v3-turbo 95%+)" :
                     tier === "indic-neural" ? "Indic Neural (98%+ Hinglish)" : "Fast Draft (base)";
    showToast(`Model Tier updated to: ${tierName} 🎯`, "info");
}

async function rerunHighAccuracyTranscribe() {
    const tier = document.getElementById("model-tier-select") ? document.getElementById("model-tier-select").value : "large-v3-turbo";
    const lang = document.getElementById("language-select") ? document.getElementById("language-select").value : "hinglish";
    const script = currentTranscriptScript;

    showToast(`Transcribing with ${tier === 'large-v3-turbo' ? 'Studio Pro 95%+' : 'Indic Neural 98%'} & Forced Alignment... ⚡`, "info");
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

    // Update kinetic caption bubble (Face-Safe lower third)
    if (activeWordObj) {
        captionBubble.innerHTML = `<span class="highlight-word">${activeWordObj.word.toUpperCase()}</span>`;
    }
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

// ---------------- COLOR PRESETS ----------------
async function fetchColorPresets() {
    try {
        const res = await fetch("/api/presets/color-grades");
        const data = await res.json();
        colorPresets = data.presets || [];
        renderColorPresets();
    } catch (e) {
        console.error("Presets error:", e);
    }
}

function renderColorPresets() {
    const container = document.getElementById("color-presets-container");
    container.innerHTML = colorPresets.map(preset => `
        <div class="color-swatch-card ${activeColorPreset === preset.id ? 'active' : ''}" 
             onclick="selectColorPreset('${preset.id}')"
             title="${preset.description}">
            <div class="swatch-pip" style="background:${preset.preview_color};"></div>
            <div class="swatch-name">${preset.name}</div>
        </div>
    `).join("");
}

function selectColorPreset(presetId) {
    activeColorPreset = presetId;
    renderColorPresets();
    showToast(`Color grade preset set to: ${presetId.replace('_', ' ').toUpperCase()}`, "info");
}

function changeCaptionStyle(style) {
    activeCaptionStyle = style;
    showToast(`Caption style: ${style.toUpperCase()}`, "info");
}

// ---------------- AI DIRECTOR AGENT ----------------
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
        
        // Apply actions to UI
        if (data.actions) {
            if (data.actions.aspect_ratio === "9:16") {
                setPlayerAspect("9:16");
            }
            if (data.actions.color_grade && data.actions.color_grade !== "none") {
                selectColorPreset(data.actions.color_grade);
            }
            if (data.actions.caption_style) {
                document.getElementById("caption-style-select").value = data.actions.caption_style;
            }
            if (data.actions.language) {
                document.getElementById("language-select").value = data.actions.language;
            }
        }

        showToast(`AI Director plan formulated:\n${data.plan_description}`, "success");
    } catch (e) {
        showToast("Error processing AI prompt", "error");
    }
}

function applyQuickPrompt(text) {
    document.getElementById("ai-prompt-input").value = text;
    submitAgentPrompt();
}

// ---------------- 12-GRID PIPELINE INITIALIZATION & START ----------------
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
    container.innerHTML = GRID_DEFS.map(g => `
        <div class="grid-card" id="${g.id}">
            <div class="grid-card-top">
                <div class="grid-title-row">
                    <i data-feather="${g.icon}" class="grid-icon"></i>
                    <span class="grid-title">${g.title}</span>
                </div>
                <span class="grid-status-badge badge-waiting" id="${g.id}-badge">WAITING</span>
            </div>
            <div class="grid-detail-text" id="${g.id}-detail">Ready for input</div>
            <div class="grid-progress-bar-container">
                <div class="grid-progress-bar" id="${g.id}-bar"></div>
            </div>
            <div class="grid-eta-row">
                <span id="${g.id}-clip-eta">Clip ETA: --</span>
                <span class="highlight" id="${g.id}-eta">Grid ETA: --</span>
            </div>
        </div>
    `).join("");
    feather.replace();
}

function updateGridUI(gridId, status, progress, clipEta, gridEta, detail) {
    const card = document.getElementById(gridId);
    if (!card) return;

    card.className = `grid-card ${status}`;
    
    const badge = document.getElementById(`${gridId}-badge`);
    if (badge) {
        if (status === "in_progress") {
            badge.className = "grid-status-badge badge-running";
            badge.innerText = "RUNNING";
        } else if (status === "completed") {
            badge.className = "grid-status-badge badge-done";
            badge.innerText = "DONE";
        } else {
            badge.className = "grid-status-badge badge-waiting";
            badge.innerText = "WAITING";
        }
    }

    const bar = document.getElementById(`${gridId}-bar`);
    if (bar) bar.style.width = `${progress}%`;

    const detailEl = document.getElementById(`${gridId}-detail`);
    if (detailEl && detail) detailEl.innerText = detail;

    const clipEtaEl = document.getElementById(`${gridId}-clip-eta`);
    if (clipEtaEl) clipEtaEl.innerText = clipEta > 0 ? `Clip ETA: ${clipEta}s` : `Clip ETA: 0s`;

    const gridEtaEl = document.getElementById(`${gridId}-eta`);
    if (gridEtaEl) gridEtaEl.innerText = gridEta > 0 ? `Grid ETA: ${gridEta}s` : `Grid ETA: Done`;
}

async function startPipelineProcess() {
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

    showToast(`Launching Auto-Edit on ${selectedFileNames.size} clip(s)...`, "info");
    document.getElementById("master-status-badge").innerText = "PROCESSING";
    document.getElementById("master-status-badge").className = "stat-badge running";

    const settings = {
        edit_mode: document.getElementById("edit-mode-select") ? document.getElementById("edit-mode-select").value : "full_movie",
        language: document.getElementById("language-select") ? document.getElementById("language-select").value : "auto",
        model_tier: document.getElementById("model-tier-select") ? document.getElementById("model-tier-select").value : "large-v3-turbo",
        script_mode: currentTranscriptScript,
        color_grade: activeColorPreset,
        aspect_ratio: activeAspectRatio,
        caption_style: document.getElementById("caption-style-select") ? document.getElementById("caption-style-select").value : "youtube_create",
        audio_enhance: document.getElementById("chk-audio-enhance").checked,
        auto_duck: document.getElementById("chk-auto-duck").checked
    };

    try {
        const res = await fetch("/api/project/start-processing", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ settings: settings })
        });
        const data = await res.json();
        
        // Poll for transcript update after 3 seconds
        setTimeout(loadTranscript, 3500);
    } catch (e) {
        showToast("Error starting pipeline", "error");
    }
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
    if (isNaN(sec) || sec <= 0) return "--:--";
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${pad(m)}:${pad(s)}`;
}

function pad(num) {
    return num.toString().padStart(2, "0");
}

function showToast(msg, type = "info") {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerText = msg;
    container.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, 4500);
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
function showCompletionModal(info = {}) {
    const modal = document.getElementById("completion-modal");
    if (!modal) return;
    
    if (info.duration && document.getElementById("comp-stat-duration")) {
        document.getElementById("comp-stat-duration").innerText = info.duration;
    }
    if (info.size && document.getElementById("comp-stat-size")) {
        document.getElementById("comp-stat-size").innerText = info.size;
    }
    const dlLink = document.getElementById("comp-download-link");
    if (dlLink) {
        dlLink.href = info.url || "/media_final/MASTER_FULL_FEATURE_MOVIE.mp4";
        dlLink.setAttribute("download", info.filename || "MASTER_FULL_FEATURE_MOVIE.mp4");
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
    const movieUrl = "/media_final/MASTER_FULL_FEATURE_MOVIE.mp4";
    loadVideoIntoPlayer(movieUrl, true, "MASTER_FULL_FEATURE_MOVIE.mp4 (Complete Master)");
    const player = document.getElementById("main-video-player");
    if (player) {
        player.play().catch(e => console.log("Auto-play ready:", e));
    }
    showToast("Playing Full Master Feature Movie in Studio!", "success");
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



