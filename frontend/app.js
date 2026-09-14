let selectedAgent = "auto";
let uploadedDocuments = [];
let checkedSourceIds = new Set();
let initializedDocIds = new Set();
let pinnedNotes = [];


// Audio Overview State
let podcastData = null;
let isPodcastPlaying = false;
let currentSpeechUtterance = null;
let currentLineIndex = 0;

document.addEventListener("DOMContentLoaded", () => {
    initDropZone();
    loadDocuments();
    initChatInput();
    renderPinnedNotes();
});

// Initialize Drag & Drop Upload Zone
function initDropZone() {
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("file-input");

    if (dropZone && fileInput) {
        dropZone.addEventListener("click", () => fileInput.click());

        dropZone.addEventListener("dragover", (e) => {
            e.preventDefault();
            dropZone.style.borderColor = "var(--google-blue)";
        });

        dropZone.addEventListener("dragleave", () => {
            dropZone.style.borderColor = "rgba(168, 199, 250, 0.3)";
        });

        dropZone.addEventListener("drop", (e) => {
            e.preventDefault();
            dropZone.style.borderColor = "rgba(168, 199, 250, 0.3)";
            if (e.dataTransfer.files.length > 0) {
                handleFileUpload(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener("change", (e) => {
            if (e.target.files.length > 0) {
                handleFileUpload(e.target.files[0]);
            }
        });
    }
}

// Select Agent Mode
function selectAgentMode(agentName) {
    selectedAgent = agentName;

    const btns = document.querySelectorAll(".agent-nav-btn");
    btns.forEach(b => {
        if (b.getAttribute("data-agent") === agentName) {
            b.classList.add("active");
        } else {
            b.classList.remove("active");
        }
    });

    const badge = document.getElementById("active-agent-badge");
    const names = {
        "auto": "Auto Synthesizer",
        "DocumentAgent": "Document Agent",
        "ResearchAgent": "Deep Research",
        "SummaryAgent": "Executive Summary",
        "CitationAgent": "Source Audit",
        "ReportAgent": "Report Agent"
    };

    if (badge) {
        badge.innerHTML = `<i data-lucide="sparkles"></i> ${names[agentName] || agentName}`;
        lucide.createIcons();
    }
}

// File Upload Pipeline Visualizer
async function handleFileUpload(file) {
    const timeline = document.getElementById("processing-timeline");
    const fill = document.getElementById("progress-bar-fill");
    const title = document.getElementById("process-step-title");
    const percent = document.getElementById("process-step-percent");

    if (timeline) timeline.style.display = "block";

    if (fill) fill.style.width = "25%";
    if (title) title.innerText = "Step 1: Parsing document file...";
    if (percent) percent.innerText = "25%";
    await sleep(300);

    if (fill) fill.style.width = "60%";
    if (title) title.innerText = "Step 2: Creating overlapping semantic chunks...";
    if (percent) percent.innerText = "60%";

    const formData = new FormData();
    formData.append("file", file);

    try {
        const resp = await fetch("/api/upload", {
            method: "POST",
            body: formData
        });
        const data = await resp.json();

        if (fill) fill.style.width = "100%";
        if (title) title.innerText = "Step 3: Source indexed & ready!";
        if (percent) percent.innerText = "100%";
        await sleep(300);

        loadDocuments();

        setTimeout(() => {
            if (timeline) timeline.style.display = "none";
            if (fill) fill.style.width = "0%";
        }, 1500);

    } catch (err) {
        if (title) title.innerText = "Upload failed!";
        alert("Upload error: " + err.message);
    }
}

// Fetch Document Store & Render Sources List
async function loadDocuments() {
    try {
        const resp = await fetch("/api/documents");
        const data = await resp.json();
        uploadedDocuments = data.documents;

        const docList = document.getElementById("doc-list");
        const docCount = document.getElementById("doc-count");
        const clearAllBtn = document.getElementById("btn-clear-all");

        if (docCount) docCount.innerText = data.total_documents;
        if (clearAllBtn) clearAllBtn.style.display = data.total_documents > 0 ? "flex" : "none";

        // Auto-check newly uploaded documents by default
        uploadedDocuments.forEach(d => {
            if (!initializedDocIds.has(d.file_id)) {
                initializedDocIds.add(d.file_id);
                checkedSourceIds.add(d.file_id);
            }
        });


        if (data.total_documents === 0) {
            checkedSourceIds.clear();
            if (docList) {
                docList.innerHTML = `
                    <div class="empty-state">
                        <i data-lucide="folder-plus" class="empty-icon"></i>
                        <p>No sources uploaded</p>
                        <span>Add PDF, DOCX, CSV or text files to start querying.</span>
                    </div>
                `;
            }
        } else {
            if (docList) {
                docList.innerHTML = data.documents.map(d => {
                    const isChecked = checkedSourceIds.has(d.file_id) ? "checked" : "";
                    return `
                        <div class="source-card-item">
                            <div class="source-left">
                                <input type="checkbox" class="source-checkbox" id="chk-${d.file_id}" ${isChecked} onchange="toggleSourceCheck('${d.file_id}')">
                                <div class="source-info">
                                    <span class="source-title" title="${escapeHtml(d.filename)}">${escapeHtml(d.filename)}</span>
                                    <span class="source-meta">${d.total_pages} pages • ${d.total_chunks} chunks</span>
                                </div>
                            </div>
                            <div class="source-actions">
                                <button onclick="deleteDocument('${d.file_id}')" title="Remove source" class="btn-icon-danger">
                                    <i data-lucide="trash-2" style="width:14px; height:14px;"></i>
                                </button>
                            </div>
                        </div>
                    `;
                }).join("");
            }
        }
        updateSourceScopeBadge();
        lucide.createIcons();
    } catch (err) {
        console.error("Error loading documents:", err);
    }
}

function toggleSourceCheck(fileId) {
    if (checkedSourceIds.has(fileId)) {
        checkedSourceIds.delete(fileId);
    } else {
        checkedSourceIds.add(fileId);
    }
    updateSourceScopeBadge();
}

function toggleSelectAllSources() {
    if (checkedSourceIds.size === uploadedDocuments.length) {
        checkedSourceIds.clear();
    } else {
        uploadedDocuments.forEach(d => checkedSourceIds.add(d.file_id));
    }
    loadDocuments();
}

function getSelectedFileIdsString() {
    return Array.from(checkedSourceIds).join(",");
}

function updateSourceScopeBadge() {
    const textEl = document.getElementById("scope-count-text");
    if (textEl) {
        const count = checkedSourceIds.size;
        textEl.innerText = count === 1 ? "1 source selected" : `${count} sources selected`;
    }
}

async function deleteDocument(fileId) {
    if (!confirm("Are you sure you want to remove this source?")) return;
    try {
        const resp = await fetch(`/api/documents/${fileId}`, { method: "DELETE" });
        const data = await resp.json();
        checkedSourceIds.delete(fileId);
        initializedDocIds.delete(fileId);
        loadDocuments();
    } catch (err) {
        alert("Delete error: " + err.message);
    }
}

async function clearAllDocuments() {
    if (!confirm("Remove all sources from the notebook?")) return;
    try {
        const resp = await fetch("/api/documents", { method: "DELETE" });
        const data = await resp.json();
        checkedSourceIds.clear();
        initializedDocIds.clear();
        loadDocuments();
    } catch (err) {
        alert("Clear error: " + err.message);
    }
}


function initChatInput() {
    const textarea = document.getElementById("chat-input");
    if (textarea) {
        textarea.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
}

function setQuery(text) {
    const textarea = document.getElementById("chat-input");
    if (textarea) {
        textarea.value = text;
        sendMessage();
    }
}

async function sendMessage() {
    const input = document.getElementById("chat-input");
    const query = input.value.trim();

    if (!query) return;

    input.value = "";

    const chatContainer = document.getElementById("chat-messages");
    const welcomeHero = chatContainer.querySelector(".notebook-welcome-hero");
    if (welcomeHero) welcomeHero.remove();

    appendUserMessage(query);

    const botRowId = appendAgentThinkingPlaceholder();

    try {
        const formData = new FormData();
        formData.append("query", query);
        formData.append("agent", selectedAgent);
        formData.append("file_ids", getSelectedFileIdsString());

        const resp = await fetch("/api/chat", {
            method: "POST",
            body: formData
        });

        const data = await resp.json();
        renderAgentResponse(botRowId, data);

    } catch (err) {
        const botBubble = document.getElementById(`${botRowId}-bubble`);
        if (botBubble) {
            botBubble.innerHTML = `<span style="color:var(--google-rose)">Error: ${err.message}</span>`;
        }
    }
}

function appendUserMessage(text) {
    const chatContainer = document.getElementById("chat-messages");
    const row = document.createElement("div");
    row.className = "chat-row user";
    row.innerHTML = `
        <div class="chat-bubble-wrap">
            <div class="chat-bubble">${escapeHtml(text)}</div>
        </div>
        <div class="chat-avatar"><i data-lucide="user"></i></div>
    `;
    chatContainer.appendChild(row);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    lucide.createIcons();
}

function appendAgentThinkingPlaceholder() {
    const chatContainer = document.getElementById("chat-messages");
    const id = "msg-" + Date.now();
    const row = document.createElement("div");
    row.className = "chat-row agent";
    row.id = id;
    row.innerHTML = `
        <div class="chat-avatar"><i data-lucide="sparkles"></i></div>
        <div class="chat-bubble-wrap">
            <div class="chat-bubble" id="${id}-bubble">
                <em style="color:var(--text-muted)">Nexora analyzing selected sources & synthesizing grounded response...</em>
            </div>
        </div>
    `;
    chatContainer.appendChild(row);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    lucide.createIcons();
    return id;
}

function renderAgentResponse(rowId, data) {
    const bubble = document.getElementById(`${rowId}-bubble`);
    if (!bubble) return;

    let thoughtsHtml = "";
    if (data.thoughts && data.thoughts.length > 0) {
        const thoughtsContent = data.thoughts.map(t => `<div>${escapeHtml(t)}</div>`).join("");
        thoughtsHtml = `
            <div class="thought-console">
                <div class="thought-trigger" onclick="toggleThoughts('${rowId}')">
                    <span>🧠 Nexora Reasoning Steps (${data.thoughts.length} steps)</span>

                    <span>▼</span>
                </div>
                <div class="thought-log-body" id="${rowId}-thoughts" style="display:none;">
                    ${thoughtsContent}
                </div>
            </div>
        `;
    }

    const agentRoleHeader = `
        <div class="agent-role-header">
            <i data-lucide="sparkles" style="width:14px; height:14px;"></i>
            <span>${data.agent_used} (${data.agent_role})</span>
        </div>
    `;

    const parsedMarkdown = marked.parse(data.response || "");

    const actionBar = `
        <div class="message-action-bar">
            <button class="btn-action-pin" onclick="pinMessageToStudio('${rowId}')">
                <i data-lucide="bookmark" style="width:13px; height:13px;"></i> Save to Note
            </button>
            <button class="btn-action-pin" onclick="copyMessageText('${rowId}')" style="background:transparent; border-color:var(--border-color); color:var(--text-muted);">
                <i data-lucide="copy" style="width:13px; height:13px;"></i> Copy
            </button>
        </div>
    `;

    bubble.innerHTML = `
        ${thoughtsHtml}
        ${agentRoleHeader}
        <div class="markdown-body" id="${rowId}-content">${parsedMarkdown}</div>
        ${actionBar}
    `;

    const chatContainer = document.getElementById("chat-messages");
    chatContainer.scrollTop = chatContainer.scrollHeight;
    lucide.createIcons();
}

function toggleThoughts(rowId) {
    const el = document.getElementById(`${rowId}-thoughts`);
    if (el) {
        el.style.display = el.style.display === "none" ? "flex" : "none";
    }
}

function copyMessageText(rowId) {
    const el = document.getElementById(`${rowId}-content`);
    if (el) {
        navigator.clipboard.writeText(el.innerText);
        alert("Response copied to clipboard!");
    }
}

// AUDIO OVERVIEW (PODCAST GENERATOR)
async function generateAudioOverview() {
    const btn = document.getElementById("btn-gen-podcast");
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<i data-lucide="loader" class="spin"></i> Generating Deep Dive...`;
    }

    try {
        const formData = new FormData();
        formData.append("file_ids", getSelectedFileIdsString());

        const resp = await fetch("/api/generate-podcast", {
            method: "POST",
            body: formData
        });

        podcastData = await resp.json();

        // Render player box
        const playerBox = document.getElementById("podcast-player");
        const titleEl = document.getElementById("podcast-title");
        const statusEl = document.getElementById("podcast-status");
        const transcriptEl = document.getElementById("podcast-transcript");

        if (titleEl) titleEl.innerText = podcastData.title || "Audio Overview";
        if (statusEl) statusEl.innerText = `${podcastData.dialogue.length} dialogue turns ready`;

        if (transcriptEl) {
            transcriptEl.innerHTML = podcastData.dialogue.map((d, i) => `
                <div class="speech-line" id="speech-line-${i}">
                    <strong>${d.speaker}:</strong> ${escapeHtml(d.text)}
                </div>
            `).join("");
        }

        if (playerBox) playerBox.style.display = "block";
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `<i data-lucide="mic"></i> Regenerate Audio Overview`;
        }
        lucide.createIcons();

    } catch (err) {
        alert("Failed to generate Audio Overview: " + err.message);
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `<i data-lucide="mic"></i> Generate Audio Overview`;
        }
    }
}

function togglePodcastPlayback() {
    if (!podcastData || !podcastData.dialogue) return;

    if (isPodcastPlaying) {
        stopPodcastPlayback();
    } else {
        startPodcastPlayback();
    }
}

function startPodcastPlayback() {
    if (!('speechSynthesis' in window)) {
        alert("Web Speech API is not supported in this browser. Showing script transcript.");
        return;
    }

    isPodcastPlaying = true;
    currentLineIndex = 0;

    const playIcon = document.getElementById("play-icon");
    const statusEl = document.getElementById("podcast-status");
    if (playIcon) playIcon.setAttribute("data-lucide", "pause");
    if (statusEl) statusEl.innerText = "Playing Audio Overview...";
    lucide.createIcons();

    speakNextLine();
}

function speakNextLine() {
    if (!isPodcastPlaying || currentLineIndex >= podcastData.dialogue.length) {
        stopPodcastPlayback();
        return;
    }

    const line = podcastData.dialogue[currentLineIndex];

    // Highlight line in transcript
    document.querySelectorAll(".speech-line").forEach((el, idx) => {
        if (idx === currentLineIndex) el.classList.add("active");
        else el.classList.remove("active");
    });

    const scrollTranscript = document.getElementById("podcast-transcript");
    const activeLine = document.getElementById(`speech-line-${currentLineIndex}`);
    if (scrollTranscript && activeLine) {
        scrollTranscript.scrollTop = activeLine.offsetTop - scrollTranscript.offsetTop;
    }

    const utterance = new SpeechSynthesisUtterance(line.text);

    // Differentiate Alex and Jordan voices by pitch and rate
    if (line.speaker === "Alex") {
        utterance.pitch = 1.1;
        utterance.rate = 1.0;
    } else {
        utterance.pitch = 0.85;
        utterance.rate = 0.95;
    }

    utterance.onend = () => {
        currentLineIndex++;
        if (isPodcastPlaying) {
            speakNextLine();
        }
    };

    utterance.onerror = () => {
        currentLineIndex++;
        if (isPodcastPlaying) {
            speakNextLine();
        }
    };

    currentSpeechUtterance = utterance;
    window.speechSynthesis.speak(utterance);
}

function stopPodcastPlayback() {
    isPodcastPlaying = false;
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
    }

    const playIcon = document.getElementById("play-icon");
    const statusEl = document.getElementById("podcast-status");
    if (playIcon) playIcon.setAttribute("data-lucide", "play");
    if (statusEl) statusEl.innerText = "Paused / Ready";
    lucide.createIcons();
}


// STUDIO ARTIFACT GENERATOR
async function generateStudioArtifact(artifactType) {
    const chatContainer = document.getElementById("chat-messages");
    const welcomeHero = chatContainer.querySelector(".notebook-welcome-hero");
    if (welcomeHero) welcomeHero.remove();

    const botRowId = appendAgentThinkingPlaceholder();

    try {
        const formData = new FormData();
        formData.append("artifact_type", artifactType);
        formData.append("file_ids", getSelectedFileIdsString());

        const resp = await fetch("/api/studio-artifact", {
            method: "POST",
            body: formData
        });

        const data = await resp.json();

        renderAgentResponse(botRowId, {
            agent_used: "Nexora Studio",
            agent_role: "Artifact Composer",
            thoughts: [`Selected active sources payload`, `Generated structured ${artifactType} document`],
            response: data.content
        });

        // Automatically pin to Studio notes!
        pinNoteToStudio(`Artifact: ${artifactType.toUpperCase().replace('_', ' ')}`, data.content);

    } catch (err) {
        const botBubble = document.getElementById(`${botRowId}-bubble`);
        if (botBubble) {
            botBubble.innerHTML = `<span style="color:var(--google-rose)">Error generating artifact: ${err.message}</span>`;
        }
    }
}


// PINNED NOTES STUDIO MANAGEMENT
function pinMessageToStudio(rowId) {
    const el = document.getElementById(`${rowId}-content`);
    if (el) {
        const contentText = el.innerText.substring(0, 300) + (el.innerText.length > 300 ? "..." : "");
        const title = "Saved Insight #" + (pinnedNotes.length + 1);
        pinNoteToStudio(title, contentText);
        alert("Note pinned to Studio!");
    }
}

function pinNoteToStudio(title, content) {
    const newNote = {
        id: "note-" + Date.now(),
        title: title,
        content: content,
        date: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    pinnedNotes.unshift(newNote);
    renderPinnedNotes();
}

function createNewNoteModal() {
    const text = prompt("Enter note title or text to save to Studio:");
    if (text && text.trim()) {
        pinNoteToStudio("Quick Note", text.trim());
    }
}

function deleteNote(noteId) {
    pinnedNotes = pinnedNotes.filter(n => n.id !== noteId);
    renderPinnedNotes();
}

function renderPinnedNotes() {
    const notesGrid = document.getElementById("notes-grid");
    const notesCount = document.getElementById("notes-count");

    if (notesCount) notesCount.innerText = pinnedNotes.length;

    if (!notesGrid) return;

    if (pinnedNotes.length === 0) {
        notesGrid.innerHTML = `
            <div class="empty-state-notes">
                <i data-lucide="bookmark" class="empty-icon-sm"></i>
                <p>No pinned notes yet</p>
                <span>Click "Save to Note" on any chat response to pin it here.</span>
            </div>
        `;
    } else {
        notesGrid.innerHTML = pinnedNotes.map(n => `
            <div class="note-card">
                <div class="note-card-header">
                    <span class="note-card-title">${escapeHtml(n.title)}</span>
                    <button onclick="deleteNote('${n.id}')" title="Delete note" class="btn-icon-danger">
                        <i data-lucide="x" style="width:13px; height:13px;"></i>
                    </button>
                </div>
                <div class="note-card-body">
                    ${escapeHtml(n.content)}
                </div>
                <div class="note-card-footer">
                    <span>${n.date}</span>
                    <span>Pinned</span>
                </div>
            </div>
        `).join("");
    }
    lucide.createIcons();
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function escapeHtml(text) {
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
