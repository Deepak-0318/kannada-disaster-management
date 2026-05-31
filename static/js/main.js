/* ==========================================================================
   INTERACTIVE JS CONTROLLER - KANNADA DISASTER EOC SUITE
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
    
    // ------------------------------------------
    // State Variables
    // ------------------------------------------
    let currentMode = "normal"; // "normal" or "emergency"
    let mediaRecorder = null;
    let audioChunks = [];
    let audioContext = null;
    let analyser = null;
    let dataArray = null;
    let drawVisual = null;
    let recordStartTime = null;
    let recordingTimerInterval = null;
    let clientRmsMax = 0; // Tracks highest RMS during recording to detect panic
    const PANIC_VOLUME_THRESHOLD = 0.18; // Calibrated vocal stress volume threshold

    // Request Concurrency Lock & States
    let isGenerating = false; 
    let analyticsInterval = null;
    let serverHealthInterval = null;

    // Web Speech API Variables
    let recognition = null;
    let recognitionActive = false;
    let webSpeechTranscript = "";
    
    // Global session ID
    const sessionId = "session_" + Math.random().toString(36).substring(2, 10);
    let selectedDistrict = "Bengaluru";

    // Chart.js references
    let severityChart = null;
    let hourlyChart = null;

    // ------------------------------------------
    // DOM Elements
    // ------------------------------------------
    const body = document.body;
    const timeString = document.getElementById("time-string");
    const systemModeBadge = document.getElementById("system-mode-badge");
    const modeText = document.getElementById("mode-text");
    const offlineBadge = document.getElementById("offline-badge");
    const statusBar = document.getElementById("status-bar");
    
    // Server Health Status
    const serverStatusBadge = document.getElementById("server-status-badge");
    const serverStatusDot = document.getElementById("server-status-dot");
    const serverStatusText = document.getElementById("server-status-text");

    // Chat & Input
    const chatMessages = document.getElementById("chat-messages");
    const textInput = document.getElementById("text-input");
    const btnSend = document.getElementById("btn-send");
    const btnRecord = document.getElementById("btn-record");
    const btnStopTts = document.getElementById("btn-stop-tts");
    const btnClearChat = document.getElementById("btn-clear-chat");
    const responseMeta = document.getElementById("response-meta");
    const metaConfidence = document.getElementById("meta-confidence");
    const metaOffline = document.getElementById("meta-offline");
    const metaCitations = document.getElementById("meta-citations");

    // Controls
    const btnModeNormal = document.getElementById("btn-mode-normal");
    const btnModeEmergency = document.getElementById("btn-mode-emergency");
    const btnTheme = document.getElementById("btn-theme");
    
    // Live Alerts
    const alertsList = document.getElementById("alerts-list");
    const alertsTicker = document.getElementById("alerts-ticker");
    const tickerTrack = document.getElementById("ticker-track");
    const tickerClose = document.getElementById("ticker-close");

    // Visualizer Elements
    const visualizerBox = document.getElementById("visualizer-box");
    const waveCanvas = document.getElementById("wave-canvas");
    const canvasCtx = waveCanvas.getContext("2d");
    const recordingTimer = document.getElementById("recording-timer");
    const panicAcousticBadge = document.getElementById("panic-acoustic-badge");
    
    // Audio Player
    const audioPlayer = document.getElementById("audio-player");

    audioPlayer.addEventListener("error", (e) => {
        console.error("AUDIO ERROR:", e);
    });

    audioPlayer.addEventListener("loadeddata", () => {
        console.log("Audio loaded");
    });

    audioPlayer.addEventListener("canplaythrough", () => {
        console.log("Audio ready");
    });
    
    // Shelter Feed
    const shelterFeed = document.getElementById("shelter-feed");

    // Analytics Overlay
    const btnAnalytics = document.getElementById("btn-analytics");
    const analyticsOverlay = document.getElementById("analytics-overlay");
    const btnCloseAnalytics = document.getElementById("btn-close-analytics");
    const btnRefreshAnalytics = document.getElementById("btn-refresh-analytics");
    
    // Analytics Metrics
    const statTotal = document.getElementById("stat-total");
    const statCritical = document.getElementById("stat-critical");
    const statVoice = document.getElementById("stat-voice");
    const statLatency = document.getElementById("stat-latency");
    const chartCategories = document.getElementById("chart-categories");
    const analyticsUptime = document.getElementById("analytics-uptime");

    // Toast Container
    const toastContainer = document.getElementById("toast-container");

    // ------------------------------------------
    // Markdown & Highlight Parser
    // ------------------------------------------
    function formatMarkdown(text) {
        if (!text) return "";
        let html = text;

        // Escape HTML tags to protect EOC systems from cross-site injection
        html = html
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
        
        // Bold: **text** -> <strong>text</strong>
        html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
        
        // Emergency helpline highlights: 1070, 1077, 112, 101, 108, 104
        const emergencyNumbers = ["1070", "1077", "112", "101", "108", "104"];
        emergencyNumbers.forEach(num => {
            const regex = new RegExp(`\\b${num}\\b`, "g");
            html = html.replace(regex, `<span class="helpline-highlight">${num}</span>`);
        });

        // Split into lines for formatting lists
        const lines = html.split("\n");
        let inList = false;
        const formattedLines = [];

        lines.forEach(line => {
            const trimmed = line.trim();
            if (trimmed.startsWith("* ") || trimmed.startsWith("- ")) {
                if (!inList) {
                    formattedLines.push("<ul>");
                    inList = true;
                }
                formattedLines.push(`<li>${trimmed.substring(2)}</li>`);
            } else {
                if (inList) {
                    formattedLines.push("</ul>");
                    inList = false;
                }
                formattedLines.push(line);
            }
        });
        if (inList) {
            formattedLines.push("</ul>");
        }

        return formattedLines.join("\n").replace(/\n/g, "<br>");
    }

    // ------------------------------------------
    // Client-Side Web Audio API Emergency Alarm
    // ------------------------------------------
    function playEmergencyAlarm() {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            
            osc.type = "sine";
            osc.frequency.setValueAtTime(580, ctx.currentTime);
            // Dynamic siren sweep
            osc.frequency.linearRampToValueAtTime(950, ctx.currentTime + 0.25);
            osc.frequency.linearRampToValueAtTime(580, ctx.currentTime + 0.5);
            osc.frequency.linearRampToValueAtTime(950, ctx.currentTime + 0.75);
            osc.frequency.linearRampToValueAtTime(580, ctx.currentTime + 1.0);
            
            gain.gain.setValueAtTime(0, ctx.currentTime);
            gain.gain.linearRampToValueAtTime(0.25, ctx.currentTime + 0.1);
            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 1.2);
            
            osc.connect(gain);
            gain.connect(ctx.destination);
            
            osc.start();
            osc.stop(ctx.currentTime + 1.3);
        } catch (e) {
            console.warn("Audio Context sweep failed:", e);
        }
    }

    // ------------------------------------------
    // Speech Recognition Initialization (Web Speech API)
    // ------------------------------------------
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'kn-IN'; // Kannada locale

        recognition.onstart = () => {
            recognitionActive = true;
            webSpeechTranscript = "";
            textInput.value = "";
            textInput.placeholder = "ಧ್ವನಿ ಆಲಿಸಲಾಗುತ್ತಿದೆ... (Listening...)";
        };

        recognition.onresult = (event) => {
            let interimTranscript = "";
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    webSpeechTranscript += event.results[i][0].transcript;
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }
            const currentDisplay = webSpeechTranscript || interimTranscript;
            textInput.value = currentDisplay;
        };

        recognition.onerror = (event) => {
            console.warn("Speech recognition warning:", event.error);
            if (event.error === "not-allowed") {
                showToast("ಮೈಕ್ರೋಫೋನ್ ಅನುಮತಿ ಅಗತ್ಯವಿದೆ.", "error");
            } else if (event.error !== "no-speech") {
                showToast(`Speech Engine Warning: ${event.error}`, "warning");
            }
        };

        recognition.onend = () => {
            recognitionActive = false;
            textInput.placeholder = "ಇಲ್ಲಿ ಪ್ರಶ್ನೆಯನ್ನು ಕನ್ನಡದಲ್ಲಿ ಟೈಪ್ ಮಾಡಿ...";
            
            // If we captured spoken text, submit it!
            const textToSubmit = webSpeechTranscript.trim() || textInput.value.trim();
            if (textToSubmit) {
                sendTextQuery(textToSubmit, true);
                textInput.value = "";
                webSpeechTranscript = "";
            }
            stopRecording();
        };
    } else {
        console.warn("Web Speech API is not supported. Falling back to server-side Whisper transcription.");
    }

    // ------------------------------------------
    // Toast Notification System
    // ------------------------------------------
    function showToast(message, type = "info") {
        const toast = document.createElement("div");
        toast.className = `toast ${type}`;
        
        let icon = "fa-info-circle";
        if (type === "success") icon = "fa-check-circle";
        if (type === "error") icon = "fa-exclamation-circle";
        if (type === "warning") icon = "fa-exclamation-triangle";

        toast.innerHTML = `
            <span><i class="fa-solid ${icon}"></i> &nbsp;${message}</span>
            <span style="cursor:pointer;margin-left:10px" onclick="this.parentElement.remove()"><i class="fa-solid fa-xmark"></i></span>
        `;
        toastContainer.appendChild(toast);
        setTimeout(() => {
            if (toast && toast.parentElement) toast.remove();
        }, 5000);
    }

    // ------------------------------------------
    // Live EOC Clock
    // ------------------------------------------
    function updateClock() {
        const now = new Date();
        const hrs = String(now.getHours()).padStart(2, '0');
        const mins = String(now.getMinutes()).padStart(2, '0');
        const secs = String(now.getSeconds()).padStart(2, '0');
        timeString.textContent = `${hrs}:${mins}:${secs}`;
    }
    setInterval(updateClock, 1000);
    updateClock();

    // ------------------------------------------
    // Theme Management (Dark / Light)
    // ------------------------------------------
    const savedTheme = localStorage.getItem("theme") || "dark";
    document.documentElement.setAttribute("data-theme", savedTheme);
    updateThemeIcon(savedTheme);

    btnTheme.addEventListener("click", () => {
        const currentTheme = document.documentElement.getAttribute("data-theme");
        const newTheme = currentTheme === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", newTheme);
        localStorage.setItem("theme", newTheme);
        updateThemeIcon(newTheme);
        showToast(`Theme switched to ${newTheme} mode`, "success");
        // Re-render charts with correct text colors if open
        if (!analyticsOverlay.classList.contains("hidden")) {
            loadAnalytics();
        }
    });

    function updateThemeIcon(theme) {
        if (theme === "light") {
            btnTheme.innerHTML = `<i class="fa-solid fa-sun"></i>`;
        } else {
            btnTheme.innerHTML = `<i class="fa-solid fa-moon"></i>`;
        }
    }

    // ------------------------------------------
    // Ticker Close
    // ------------------------------------------
    tickerClose.addEventListener("click", () => {
        alertsTicker.classList.add("hidden");
    });

    // ------------------------------------------
    // System State Control
    // ------------------------------------------
    function setSystemMode(mode) {
        currentMode = mode;
        if (mode === "emergency") {
            body.classList.add("emergency-active");
            btnModeEmergency.classList.add("active");
            btnModeNormal.classList.remove("active");
            statusBar.style.background = "linear-gradient(90deg, var(--color-emergency), #ea580c, var(--color-emergency))";
            systemModeBadge.style.background = "var(--color-emergency-glow)";
            systemModeBadge.style.borderColor = "var(--border-glow-emergency)";
            modeText.textContent = "ತುರ್ತು ಮೋಡ್ (EMERGENCY ACTIVE)";
        } else {
            body.classList.remove("emergency-active");
            btnModeNormal.classList.add("active");
            btnModeEmergency.classList.remove("active");
            statusBar.style.background = "linear-gradient(90deg, var(--color-normal), #2563eb, var(--color-normal))";
            systemModeBadge.style.background = "var(--color-normal-glow)";
            systemModeBadge.style.borderColor = "var(--border-glow-normal)";
            modeText.textContent = "ಸಾಮಾನ್ಯ ಮೋಡ್ (NORMAL)";
        }
    }

    btnModeNormal.addEventListener("click", () => setSystemMode("normal"));
    btnModeEmergency.addEventListener("click", () => setSystemMode("emergency"));

    // ------------------------------------------
    // Bulletproof Shelter Map Setup (Leaflet Dark Mode GIS)
    // ------------------------------------------
    const map = L.map('gis-map', {
        zoomControl: false,
        attributionControl: false
    }).setView([14.5, 75.7], 6.5);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 19
    }).addTo(map);

    // Dynamic Leaflet CSS-Based Pins (100% reliable, zero HTTP request dependencies)
    function createGlowIcon(color) {
        return L.divIcon({
            className: 'custom-map-marker',
            html: `
                <div class="marker-pin" style="background-color: ${color}">
                    <span class="marker-pulse" style="border-color: ${color}"></span>
                </div>
            `,
            iconSize: [16, 16],
            iconAnchor: [8, 8]
        });
    }

    let shelterMarkers = {};

    async function loadShelters() {
        try {
            const response = await fetch("/api/shelters");
            const shelters = await response.json();
            
            // Clear existing markers
            Object.values(shelterMarkers).forEach(marker => map.removeLayer(marker));
            shelterMarkers = {};
            shelterFeed.innerHTML = "";

            shelters.forEach(camp => {
                const markerColor = camp.status === "OPEN" ? "#10b981" : "#ff004c";
                const customIcon = createGlowIcon(markerColor);
                const marker = L.marker([camp.lat, camp.lng], { icon: customIcon }).addTo(map);
                
                const popupContent = `
                    <div style="font-family: var(--font-body); min-width: 170px; color: #f1f5f9; padding: 4px;">
                        <h4 style="margin:0 0 6px 0; color: #f8fafc; font-size:0.85rem; font-weight:700; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:4px;">${camp.name_kn}</h4>
                        <p style="margin:0 0 4px 0; font-size:0.72rem; color: #cbd5e1;">ಜಿಲ್ಲೆ: ${camp.district_kn}</p>
                        <p style="margin:0 0 4px 0; font-size:0.72rem; color: #cbd5e1;">ಸಂಪರ್ಕ: ${camp.contact}</p>
                        <p style="margin:0; font-size:0.72rem; color: ${camp.status === 'OPEN' ? '#10b981' : '#ff004c'}; font-weight:800; display:flex; align-items:center; gap:4px;">
                            <span class="status-dot" style="background:${camp.status === 'OPEN' ? '#10b981' : '#ff004c'}; width:6px; height:6px;"></span>
                            ಸ್ಥಿತಿ: ${camp.status} (${camp.capacity_used}/${camp.capacity_max})
                        </p>
                    </div>
                `;
                marker.bindPopup(popupContent);
                shelterMarkers[camp.id] = marker;

                // Render Card
                const card = document.createElement("div");
                card.className = "shelter-item";
                card.id = `camp-card-${camp.id}`;
                
                const percent = Math.min(100, Math.round((camp.capacity_used / camp.capacity_max) * 100));
                
                card.innerHTML = `
                    <div class="shelter-item-header">
                        <h4>${camp.name_kn}</h4>
                        <span class="status-pill ${camp.status.toLowerCase()}">${camp.status === 'OPEN' ? 'ತೆರೆದಿದೆ' : 'ಭರ್ತಿ'}</span>
                    </div>
                    <div class="shelter-item-details">
                        <span>ಜಿಲ್ಲೆ: ${camp.district_kn}</span>
                        <span>ಸಾಮರ್ಥ್ಯ: ${camp.capacity_used}/${camp.capacity_max}</span>
                    </div>
                    <div class="shelter-capacity-bar">
                        <div class="shelter-capacity-fill" style="width: ${percent}%; background-color: ${camp.status === 'OPEN' ? 'var(--color-normal)' : 'var(--color-emergency)'}"></div>
                    </div>
                `;

                card.addEventListener("click", () => {
                    map.setView([camp.lat, camp.lng], 10);
                    marker.openPopup();
                    document.querySelectorAll(".shelter-item").forEach(c => c.classList.remove("selected-item"));
                    card.classList.add("selected-item");
                    selectedDistrict = camp.district;
                    loadLiveAlerts(camp.district);
                });

                shelterFeed.appendChild(card);
            });
            
            // Ensure map fits container boundaries correctly
            setTimeout(() => { map.invalidateSize(); }, 200);

        } catch (error) {
            console.error("Error loading shelters:", error);
            shelterFeed.innerHTML = `<div class="shelter-skeleton" style="color: var(--color-emergency);">ಸಂಪರ್ಕ ದೋಷ: ಮ್ಯಾಪ್ ಲೋಡ್ ಮಾಡಲು ಸಾಧ್ಯವಿಲ್ಲ.</div>`;
        }
    }
    
    loadShelters();

    // ------------------------------------------
    // Live Alerts Fetching (Dismiss Option & Polling)
    // ------------------------------------------
    async function loadLiveAlerts(district = "") {
        try {
            const url = district ? `/api/alerts?district=${district}` : "/api/alerts";
            const response = await fetch(url);
            const data = await response.json();
            
            alertsList.innerHTML = "";

            if (!data.alerts || data.alerts.length === 0) {
                alertsList.innerHTML = `<div class="alert-skeleton">ಯಾವುದೇ ಹೊಸ ಎಚ್ಚರಿಕೆಗಳಿಲ್ಲ.</div>`;
                return;
            }

            // Fill Ticker
            const tickerText = data.alerts.map(a => `⚠️ [${a.source}] ${a.title} - ${a.description}`).join(" | ");
            tickerTrack.innerHTML = `<span class="ticker-item">${tickerText}</span>`;
            alertsTicker.classList.remove("hidden");

            // Fill Left Card List with Dismiss option
            data.alerts.forEach((alert, idx) => {
                const item = document.createElement("div");
                item.className = "alert-feed-item";
                item.id = `alert-item-${idx}`;
                
                const sev = (alert.severity || "LOW").toLowerCase();
                item.innerHTML = `
                    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom: 3px">
                        <div style="display:flex; align-items:center">
                            <span class="alert-badge ${sev}">${alert.severity_kn || alert.severity}</span>
                            <span class="alert-feed-title">${alert.title}</span>
                        </div>
                        <button class="alert-dismiss-btn" onclick="this.parentElement.parentElement.remove()" title="Dismiss Alert" style="background:transparent;border:none;color:var(--text-muted);cursor:pointer;font-size:0.75rem;transition:color 0.2s">
                            <i class="fa-solid fa-xmark"></i>
                        </button>
                    </div>
                    <div class="alert-feed-desc">${alert.description}</div>
                `;
                alertsList.appendChild(item);
            });
        } catch (error) {
            console.error("Error fetching alerts:", error);
            alertsList.innerHTML = `<div class="alert-skeleton">ಎಚ್ಚರಿಕೆ ಲೋಡ್ ಮಾಡಲು ಸಾಧ್ಯವಾಗಿಲ್ಲ.</div>`;
        }
    }

    loadLiveAlerts();
    // Auto-refresh alerts every 30 seconds for critical safety responsiveness
    setInterval(loadLiveAlerts, 30000);

    // Helper: copy number to clipboard
    window.copyNumber = function(number, btn) {
        navigator.clipboard.writeText(number);
        showToast(`ಸಹಾಯವಾಣಿ ${number} ಕಾಪಿ ಮಾಡಲಾಗಿದೆ!`, "success");
        const originalIcon = btn.innerHTML;
        btn.innerHTML = `<i class="fa-solid fa-check" style="color:var(--color-normal)"></i>`;
        setTimeout(() => btn.innerHTML = originalIcon, 2000);
    }

    // ------------------------------------------
    // Chat History & Bubble Handlers (Copy Action & Markdown)
    // ------------------------------------------
    function appendMessage(role, text, severity = "LOW", isOffline = false) {
        const messageDiv = document.createElement("div");
        messageDiv.className = `chat-message ${role}`;
        
        const avatarIcon = role === "bot" ? "fa-user-shield" : "fa-user";
        const now = new Date();
        const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
        
        const sevClass = (severity || "LOW").toLowerCase();
        const sevLabel = {
            "low": "ಸಾಮಾನ್ಯ (LOW)",
            "medium": "ಮಧ್ಯಮ (MEDIUM)",
            "high": "ಹೆಚ್ಚು (HIGH)",
            "critical": "ತುರ್ತು (CRITICAL)"
        }[sevClass] || "LOW";

        const badgeHtml = role === "bot" ? `<span class="chat-severity-pill ${sevClass}">${sevLabel}</span>` : "";
        const offlineHtml = isOffline ? `<span style="color:var(--sev-critical);font-size:0.6rem;font-weight:bold;margin-right:4px">[OFFLINE FALLBACK]</span>` : "";
        
        // Copy Bubble Response Button
        const copyBtnHtml = role === "bot" ? `
            <button class="bubble-copy-btn" onclick="copyBubbleText(this)" title="ಕಾಪಿ ಮಾಡಿ (Copy Safety Guidance)" style="background:transparent;border:none;color:var(--text-muted);cursor:pointer;font-size:0.75rem;margin-left:8px;transition:color 0.2s">
                <i class="fa-regular fa-copy"></i>
            </button>
        ` : "";

        // Markdown / Helpline highlight formatting
        const parsedText = role === "bot" ? formatMarkdown(text) : text;

        messageDiv.innerHTML = `
            <div class="chat-avatar">
                <i class="fa-solid ${avatarIcon}"></i>
            </div>
            <div class="chat-bubble">
                <div class="bubble-text-content">${parsedText}</div>
                <div class="timestamp">
                    <span>${offlineHtml}${badgeHtml}</span>
                    <span style="display:flex;align-items:center;">${timeStr}${copyBtnHtml}</span>
                </div>
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        
        // Smooth auto-scroll with frame delays to wait for dynamic elements (audio elements / icons)
        setTimeout(() => {
            chatMessages.scrollTo({
                top: chatMessages.scrollHeight,
                behavior: 'smooth'
            });
        }, 80);
    }

    // Global callback for bubble copy button
    window.copyBubbleText = function(btn) {
        const bubble = btn.closest(".chat-bubble");
        const textElement = bubble.querySelector(".bubble-text-content");
        
        // Extract clean text (removing HTML structure but keeping content text)
        const cleanText = textElement.innerText || textElement.textContent;
        navigator.clipboard.writeText(cleanText.trim());
        showToast("ಸುರಕ್ಷತಾ ಸಲಹೆಯನ್ನು ಕಾಪಿ ಮಾಡಲಾಗಿದೆ! (Advice Copied!)", "success");
        
        const originalIcon = btn.innerHTML;
        btn.innerHTML = `<i class="fa-solid fa-check" style="color:var(--color-normal)"></i>`;
        setTimeout(() => btn.innerHTML = originalIcon, 2000);
    };

    function showTypingIndicator() {
        const typingDiv = document.createElement("div");
        typingDiv.className = "chat-message bot typing-indicator-msg";
        typingDiv.innerHTML = `
            <div class="chat-avatar">
                <i class="fa-solid fa-user-shield"></i>
            </div>
            <div class="chat-bubble" style="padding: 0.6rem 1rem;">
                <span class="pulse-dot" style="margin-right:3px; display:inline-block; width:6px; height:6px; background:#60a5fa; border-radius:50%; animation: flashBlink 0.6s infinite alternate;"></span>
                <span class="pulse-dot" style="margin-right:2px; display:inline-block; width:6px; height:6px; background:#60a5fa; border-radius:50%; animation: flashBlink 0.6s infinite alternate; animation-delay:0.2s;"></span>
                <span class="pulse-dot" style="display:inline-block; width:6px; height:6px; background:#60a5fa; border-radius:50%; animation: flashBlink 0.6s infinite alternate; animation-delay:0.4s;"></span>
            </div>
        `;
        chatMessages.appendChild(typingDiv);
        
        setTimeout(() => {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }, 50);
        
        return typingDiv;
    }

    // ------------------------------------------
    // TTS Audio Controls & Lock Cleanups
    // ------------------------------------------
    audioPlayer.addEventListener("play", () => {
        btnStopTts.classList.remove("hidden");
    });
    audioPlayer.addEventListener("ended", () => {
        btnStopTts.classList.add("hidden");
    });
    audioPlayer.addEventListener("pause", () => {
        btnStopTts.classList.add("hidden");
    });
    btnStopTts.addEventListener("click", () => {
        audioPlayer.pause();
        audioPlayer.currentTime = 0;
        showToast("ಧ್ವನಿ ನಿಲ್ಲಿಸಲಾಗಿದೆ (Audio stopped)", "info");
    });

    // ------------------------------------------
    // Text Send Pipeline (Concurrency Locked)
    // ------------------------------------------
    async function sendTextQuery(text, isVoiceTrigger = false) {
        if (!text.trim() || isGenerating) return;
        
        // Acquire Request Concurrency Lock
        isGenerating = true;
        btnSend.disabled = true;
        textInput.disabled = true;
        btnRecord.disabled = true;
        btnSend.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i>`;

        // Preemptively stop ongoing voice speech before starting new query interaction
        audioPlayer.pause();
        audioPlayer.currentTime = 0;
        
        // Append user visual bubble (different icon if spoken)
        const labelPrefix = isVoiceTrigger ? "🎙️ [ಧ್ವನಿ ಪ್ರಶ್ನೆ]: " : "";
        appendMessage("user", `${labelPrefix}${text}`);
        
        const indicator = showTypingIndicator();
        responseMeta.classList.add("hidden");

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    "X-Session-ID": sessionId
                },
                body: JSON.stringify({ 
                    question: text, 
                    district: selectedDistrict
                })
            });

            const data = await response.json();
            indicator.remove();
            
            if (data.error) {
                showToast(data.error, "error");
                appendMessage("bot", "ದೋಷ: ಉತ್ತರ ಪಡೆಯಲು ಸಾಧ್ಯವಾಗಿಲ್ಲ.");
                return;
            }

            // Auto Emergency UI Mode and sweep alarm sound
            if (data.severity === "HIGH" || data.severity === "CRITICAL") {
                setSystemMode("emergency");
                playEmergencyAlarm();
                showToast(`🚨 ALERT: ${data.severity} emergency query detected! Alarm triggered.`, "warning");
            } else {
                setSystemMode("normal");
            }

            // Offline Indicator
            if (data.is_offline) {
                offlineBadge.classList.remove("hidden");
            } else {
                offlineBadge.classList.add("hidden");
            }

            appendMessage("bot", data.response, data.severity, data.is_offline);

            // Populate Metadata panel
            metaConfidence.innerHTML = `<strong>Confidence:</strong> ${Math.round(data.retrieval_confidence * 100)}%`;
            metaOffline.innerHTML = `<strong>Server Mode:</strong> ${data.is_offline ? "Offline Fallback" : "Cloud RAG"}`;
            metaCitations.innerHTML = data.citations && data.citations.length 
                ? `<strong>Source:</strong> ${data.citations.join(", ")}` 
                : "<strong>Source:</strong> General Safety FAQ";
            responseMeta.classList.remove("hidden");

            // Play TTS Voice Output
            if (data.audio_url && data.tts_available !== false) {
                console.log("Audio URL:", data.audio_url);

                audioPlayer.pause();
                audioPlayer.currentTime = 0;

                audioPlayer.src = `${data.audio_url}?t=${Date.now()}`;
                audioPlayer.load();

                try {
                    await audioPlayer.play();
                    console.log("✅ TTS playing");
                } catch (e) {
                    console.error("❌ Audio play failed:", e);
                    showToast("Audio playback failed", "error");
                }
            } else if (data.tts_available === false) {
                showToast("⚠️ TTS unavailable — text response shown above", "warning");
            }

        } catch (error) {
            console.error("Chat error:", error);
            indicator.remove();
            appendMessage("bot", "ಕ್ಷಮಿಸಿ, ಪ್ರತಿಕ್ರಿಯೆ ಪಡೆಯಲು ಸರ್ವರ್ ತಲುಪಲು ಸಾಧ್ಯವಾಗಿಲ್ಲ.");
            showToast("Server connection error", "error");
        } finally {
            // Release Request Concurrency Lock
            isGenerating = false;
            btnSend.disabled = false;
            textInput.disabled = false;
            btnRecord.disabled = false;
            btnSend.innerHTML = `<i class="fa-solid fa-paper-plane"></i>`;
        }
    }

    btnSend.addEventListener("click", () => {
        sendTextQuery(textInput.value);
        textInput.value = "";
    });
    textInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            sendTextQuery(textInput.value);
            textInput.value = "";
        }
    });

    document.querySelectorAll(".trigger-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const query = btn.getAttribute("data-query");
            sendTextQuery(query);
        });
    });

    document.querySelectorAll(".emq-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const query = btn.getAttribute("data-query");
            sendTextQuery(query);
        });
    });

    // ------------------------------------------
    // Voice Recording & Oscilloscope Visualizer
    // ------------------------------------------
    function resizeCanvas() {
        waveCanvas.width = visualizerBox.offsetWidth;
        waveCanvas.height = 64;
    }
    window.addEventListener("resize", resizeCanvas);

    function drawVisualizer() {
        drawVisual = requestAnimationFrame(drawVisualizer);
        analyser.getByteTimeDomainData(dataArray);

        // Dark beautiful canvas background with subtle alpha
        canvasCtx.fillStyle = 'rgba(7, 11, 22, 0.4)';
        canvasCtx.fillRect(0, 0, waveCanvas.width, waveCanvas.height);
        
        // Dynamic Glowing Oscilloscope Line
        canvasCtx.lineWidth = 3;
        canvasCtx.strokeStyle = currentMode === "emergency" ? 'rgb(255, 29, 83)' : 'rgb(16, 185, 129)';
        canvasCtx.shadowBlur = 10;
        canvasCtx.shadowColor = currentMode === "emergency" ? 'rgba(255, 29, 83, 0.6)' : 'rgba(16, 185, 129, 0.6)';

        canvasCtx.beginPath();
        let sliceWidth = waveCanvas.width * 1.0 / dataArray.length;
        let x = 0;

        for (let i = 0; i < dataArray.length; i++) {
            let v = dataArray[i] / 128.0;
            let y = v * waveCanvas.height / 2;
            if (i === 0) canvasCtx.moveTo(x, y);
            else canvasCtx.lineTo(x, y);
            x += sliceWidth;
        }

        canvasCtx.lineTo(waveCanvas.width, waveCanvas.height / 2);
        canvasCtx.stroke();
        
        // Reset shadow for subsequent drawings
        canvasCtx.shadowBlur = 0;

        // Calculate vocal volume RMS
        let sumSquares = 0;
        for (let i = 0; i < dataArray.length; i++) {
            let normalizedVal = (dataArray[i] - 128) / 128.0;
            sumSquares += normalizedVal * normalizedVal;
        }
        let currentRms = Math.sqrt(sumSquares / dataArray.length);
        if (currentRms > clientRmsMax) clientRmsMax = currentRms;

        // Panic Acoustic stress trigger
        if (clientRmsMax > PANIC_VOLUME_THRESHOLD) {
            panicAcousticBadge.classList.remove("hidden");
            setSystemMode("emergency");
        }
    }

    async function startRecording() {
        if (isGenerating) return;
        
        audioChunks = [];
        clientRmsMax = 0;
        panicAcousticBadge.classList.add("hidden");
        webSpeechTranscript = "";
        
        // Stop speech outputs before beginning to capture microphone
        audioPlayer.pause();
        audioPlayer.currentTime = 0;

        try {
            // Request microphone access
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const source = audioContext.createMediaStreamSource(stream);
            analyser = audioContext.createAnalyser();
            analyser.fftSize = 512;
            source.connect(analyser);
            
            const bufferLength = analyser.frequencyBinCount;
            dataArray = new Uint8Array(bufferLength);

            // Setup Backup MediaRecorder for browsers without Web Speech
            mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
            
            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) audioChunks.push(event.data);
            };

            mediaRecorder.onstop = async () => {
                cancelAnimationFrame(drawVisual);
                audioContext.close();
                stream.getTracks().forEach(track => track.stop());
                
                // Fallback STT upload
                if (!webSpeechTranscript && audioChunks.length > 0 && !recognitionActive) {
                    await uploadVoiceBlob();
                }
            };

            visualizerBox.classList.add("active");
            btnRecord.classList.add("recording");
            resizeCanvas();
            drawVisualizer();

            recordStartTime = Date.now();
            recordingTimer.textContent = "0.0s";
            recordingTimerInterval = setInterval(() => {
                let seconds = ((Date.now() - recordStartTime) / 1000).toFixed(1);
                recordingTimer.textContent = `${seconds}s`;
            }, 100);

            // Start BOTH Web Speech Recognition and MediaRecorder
            mediaRecorder.start(250);
            if (recognition) {
                recognition.start();
            } else {
                showToast("ಧ್ವನಿ ರೆಕಾರ್ಡಿಂಗ್ ಪ್ರಾರಂಭವಾಗಿದೆ...", "info");
            }

        } catch (error) {
            console.error("Recording failed:", error);
            showToast("ಮೈಕ್ರೋಫೋನ್ ಅನುಮತಿ ಅಗತ್ಯವಿದೆ.", "error");
            stopRecording(); // Clean up visual button state on permission fail
        }
    }

    function stopRecording() {
        if (recognition && recognitionActive) {
            recognition.stop();
        }
        if (mediaRecorder && mediaRecorder.state !== "inactive") {
            mediaRecorder.stop();
        }
        clearInterval(recordingTimerInterval);
        btnRecord.classList.remove("recording");
        visualizerBox.classList.remove("active");
    }

    btnRecord.addEventListener("click", () => {
        if (!mediaRecorder || mediaRecorder.state === "inactive") {
            startRecording();
        } else {
            stopRecording();
        }
    });

    // ------------------------------------------
    // Backend Audio Fallback Upload (Whisper STT, Concurrency Locked)
    // ------------------------------------------
    async function uploadVoiceBlob() {
        if (audioChunks.length === 0 || isGenerating) return;

        isGenerating = true;
        btnSend.disabled = true;
        textInput.disabled = true;
        btnRecord.disabled = true;
        btnRecord.innerHTML = `<i class="fa-solid fa-spinner fa-spin" style="font-size:1.1rem"></i>`;

        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append("file", audioBlob, "voice.webm");
        formData.append("session_id", sessionId);
        formData.append("district", selectedDistrict);

        const indicator = showTypingIndicator();
        responseMeta.classList.add("hidden");

        try {
            const response = await fetch("/api/voice", {
                method: "POST",
                body: formData
            });

            const data = await response.json();
            indicator.remove();

            if (data.error) {
                showToast(data.error, "error");
                appendMessage("bot", "ದೋಷ: ಧ್ವನಿ ಸಂಸ್ಕರಿಸಲು ಸಾಧ್ಯವಾಗಿಲ್ಲ.");
                return;
            }

            if (!data.transcript) {
                appendMessage("bot", "ಕ್ಷಮಿಸಿ, ನಿಮ್ಮ ಧ್ವನಿ ಸರಿಯಾಗಿ ಸ್ಪಷ್ಟವಾಗಿ ಕೇಳಿಸಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೊಮ್ಮೆ ಪ್ರಯತ್ನಿಸಿ.");
                return;
            }

            // Append transcript
            appendMessage("user", `🎙️ [ಧ್ವನಿ ಪ್ರಶ್ನೆ]: ${data.transcript}`);

            if (data.severity === "HIGH" || data.severity === "CRITICAL") {
                setSystemMode("emergency");
                playEmergencyAlarm();
            } else {
                setSystemMode("normal");
            }

            if (data.is_offline) {
                offlineBadge.classList.remove("hidden");
            } else {
                offlineBadge.classList.add("hidden");
            }

            appendMessage("bot", data.response, data.severity, data.is_offline);

            // Populate Metadata
            metaConfidence.innerHTML = `<strong>Confidence:</strong> ${Math.round(data.retrieval_confidence * 100)}%`;
            metaOffline.innerHTML = `<strong>Server Mode:</strong> ${data.is_offline ? "Offline Fallback" : "Cloud RAG"}`;
            metaCitations.innerHTML = data.citations && data.citations.length 
                ? `<strong>Source:</strong> ${data.citations.join(", ")}` 
                : "<strong>Source:</strong> General Safety FAQ";
            responseMeta.classList.remove("hidden");

            if (data.audio_url && data.tts_available !== false) {
                console.log("Voice Audio URL:", data.audio_url);

                audioPlayer.pause();
                audioPlayer.currentTime = 0;

                audioPlayer.src = `${data.audio_url}?t=${Date.now()}`;
                audioPlayer.load();

                try {
                    await audioPlayer.play();
                    console.log("✅ Voice TTS playing");
                } catch (e) {
                    console.error("❌ Voice playback failed:", e);
                    showToast("Voice playback failed", "error");
                }
            } else if (data.tts_available === false) {
                showToast("⚠️ TTS unavailable — text response shown above", "warning");
            }

        } catch (error) {
            console.error("Voice process error:", error);
            indicator.remove();
            appendMessage("bot", "ಧ್ವನಿ ಸಂಸ್ಕರಿಸುವಲ್ಲಿ ಸರ್ವರ್ ದೋಷ ಸಂಭವಿಸಿದೆ.");
            showToast("Voice upload failed", "error");
        } finally {
            isGenerating = false;
            btnSend.disabled = false;
            textInput.disabled = false;
            btnRecord.disabled = false;
            btnRecord.innerHTML = `<i class="fa-solid fa-microphone"></i>`;
        }
    }

    // ------------------------------------------
    // Analytics Dashboard Implementation
    // ------------------------------------------
    async function loadAnalytics() {
        // Show loading skeletons inside metric cards and charts while fetching
        statTotal.innerHTML = `<div class="skeleton-box" style="height:28px; width:45px"></div>`;
        statCritical.innerHTML = `<div class="skeleton-box" style="height:28px; width:45px"></div>`;
        statVoice.innerHTML = `<div class="skeleton-box" style="height:28px; width:45px"></div>`;
        statLatency.innerHTML = `<div class="skeleton-box" style="height:28px; width:60px"></div>`;
        chartCategories.innerHTML = `
            <div class="skeleton-box" style="height:12px; margin-bottom:10px"></div>
            <div class="skeleton-box" style="height:12px; margin-bottom:10px"></div>
            <div class="skeleton-box" style="height:12px"></div>
        `;

        try {
            const response = await fetch("/api/analytics/stats");
            const data = await response.json();
            
            // Populate card values
            statTotal.textContent = data.total_queries || 0;
            statCritical.textContent = (data.severity_distribution && data.severity_distribution.CRITICAL) || 0;
            statVoice.textContent = data.voice_queries || 0;
            statLatency.textContent = (data.avg_latency_ms || 0) + "ms";
            analyticsUptime.textContent = `Uptime: ${data.uptime || '—'}`;

            // Populate Category Progress Bars
            chartCategories.innerHTML = "";
            if (data.top_categories && data.top_categories.length > 0) {
                const maxCount = Math.max(...data.top_categories.map(c => c.count)) || 1;
                data.top_categories.forEach(cat => {
                    const pct = Math.round((cat.count / maxCount) * 100);
                    const item = document.createElement("div");
                    item.className = "cat-bar-item";
                    item.innerHTML = `
                        <div class="cat-bar-label">
                            <span>${cat.name}</span>
                            <span>${cat.count}</span>
                        </div>
                        <div class="cat-bar-track">
                            <div class="cat-bar-fill" style="width: ${pct}%"></div>
                        </div>
                    `;
                    chartCategories.appendChild(item);
                });
            } else {
                chartCategories.innerHTML = `<div style="font-size:0.75rem;color:var(--text-muted)">ಚಟುವಟಿಕೆ ಇಲ್ಲ.</div>`;
            }

            // Detect Active Theme for styling charts dynamically
            const isLight = document.documentElement.getAttribute("data-theme") === "light";
            const textColor = isLight ? "#1e293b" : "#94a3b8";
            const gridColor = isLight ? "rgba(0,0,0,0.05)" : "rgba(255,255,255,0.05)";

            // Build Charts (Severity Distribution)
            const sevLabels = Object.keys(data.severity_distribution || {});
            const sevValues = Object.values(data.severity_distribution || {});
            
            if (severityChart) severityChart.destroy();
            severityChart = new Chart(document.getElementById("chart-severity"), {
                type: 'doughnut',
                data: {
                    labels: sevLabels,
                    datasets: [{
                        data: sevValues,
                        backgroundColor: ['#10b981', '#eab308', '#f97316', '#ff004c'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { 
                            position: 'bottom', 
                            labels: { color: textColor, boxWidth: 10, font: { family: 'Inter' } } 
                        }
                    }
                }
            });

            // Build Hourly Chart
            const hourlyLabels = (data.hourly_trend || []).map(h => h.hour + ":00");
            const hourlyValues = (data.hourly_trend || []).map(h => h.count);

            if (hourlyChart) hourlyChart.destroy();
            hourlyChart = new Chart(document.getElementById("chart-hourly"), {
                type: 'line',
                data: {
                    labels: hourlyLabels,
                    datasets: [{
                        label: 'Queries',
                        data: hourlyValues,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        fill: true,
                        tension: 0.3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { 
                            grid: { display: false }, 
                            ticks: { color: textColor, font: { family: 'Inter' } } 
                        },
                        y: { 
                            grid: { color: gridColor }, 
                            ticks: { color: textColor, font: { family: 'Inter' } } 
                        }
                    },
                    plugins: { 
                        legend: { display: false } 
                    }
                }
            });

        } catch (error) {
            console.error("Error loading analytics:", error);
            showToast("Failed to load analytics data", "error");
        }
    }

    btnAnalytics.addEventListener("click", () => {
        analyticsOverlay.classList.remove("hidden");
        loadAnalytics();
        
        // Auto-refresh stats dashboard every 30 seconds when opened
        clearInterval(analyticsInterval);
        analyticsInterval = setInterval(loadAnalytics, 30000);
    });

    btnCloseAnalytics.addEventListener("click", () => {
        analyticsOverlay.classList.add("hidden");
        clearInterval(analyticsInterval);
    });

    btnRefreshAnalytics.addEventListener("click", loadAnalytics);

    // ------------------------------------------
    // Server Health Monitor & Reconnect Pipeline
    // ------------------------------------------
    async function checkServerStatus() {
        try {
            const res = await fetch("/api/health");
            const status = await res.json();
            
            if (res.ok && status.status === "ok") {
                serverStatusDot.className = "status-dot green";
                serverStatusText.textContent = "EOC ONLINE";
                serverStatusBadge.title = `FAISS & Groq status: verified.`;
            } else {
                serverStatusDot.className = "status-dot red";
                serverStatusText.textContent = "EOC DEGRADED";
                serverStatusBadge.title = `Degraded state: Verify model keys and vector db.`;
            }
        } catch (err) {
            serverStatusDot.className = "status-dot red";
            serverStatusText.textContent = "EOC OFFLINE";
            serverStatusBadge.title = "No connection. Server down or network error.";
            showToast("ಸಂಪರ್ಕ ಕಡಿತಗೊಂಡಿದೆ. ಮರುಸಂಪರ್ಕಿಸಲಾಗುತ್ತಿದೆ... (Server offline. Reconnecting...)", "error");
        }
    }

    checkServerStatus();
    // Monitor health status every 15 seconds
    serverHealthInterval = setInterval(checkServerStatus, 15000);

    // ------------------------------------------
    // Clear Chat Trigger
    // ------------------------------------------
    if (btnClearChat) {
        btnClearChat.addEventListener("click", () => {
            if (confirm("ಚಾಟ್ ಇತಿಹಾಸವನ್ನು ತೆರವುಗೊಳಿಸಲು ನೀವು ಖಚಿತವಾಗಿ ಬಯಸುವಿರಾ? (Are you sure you want to clear chat?)")) {
                chatMessages.innerHTML = `
                    <div class="chat-message bot">
                        <div class="chat-avatar"><i class="fa-solid fa-user-shield"></i></div>
                        <div class="chat-bubble">
                            ನಮಸ್ಕಾರ, ಕರ್ನಾಟಕ ವಿಪತ್ತು ನಿರ್ವಹಣಾ ಧ್ವನಿ ಸಹಾಯಕಕ್ಕೆ ಸ್ವಾಗತ. ನಾನು ನಿಮಗೆ ಯಾವ ರೀತಿ ಸಹಾಯ ಮಾಡಬಹುದು?
                            <div class="timestamp">ಆನ್ಲೈನ್</div>
                        </div>
                    </div>
                `;
                responseMeta.classList.add("hidden");
                showToast("ಚಾಟ್ ತೆರವುಗೊಳಿಸಲಾಗಿದೆ", "success");
            }
        });
    }

    // ------------------------------------------
    // EOC Hotkeys / Keyboard Shortcuts
    // ------------------------------------------
    document.addEventListener("keydown", (e) => {
        // Esc to close analytics dashboard overlay
        if (e.key === "Escape") {
            if (!analyticsOverlay.classList.contains("hidden")) {
                btnCloseAnalytics.click();
            }
        }
        // Ctrl + M: Toggle microphone recording
        if (e.ctrlKey && e.key.toLowerCase() === "m") {
            e.preventDefault();
            btnRecord.click();
        }
        // Ctrl + L: Clear conversation console
        if (e.ctrlKey && e.key.toLowerCase() === "l") {
            e.preventDefault();
            if (btnClearChat) {
                btnClearChat.click();
            }
        }
    });

});
