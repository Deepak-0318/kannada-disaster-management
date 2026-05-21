/* ==========================================================================
   INTERACTIVE JS CONTROLLER - KANADA DISASTER EOC SUITE
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

    // ------------------------------------------
    // DOM Elements
    // ------------------------------------------
    const body = document.body;
    const timeString = document.getElementById("time-string");
    const systemModeBadge = document.getElementById("system-mode-badge");
    const modeText = document.getElementById("mode-text");
    
    // Chat & Input Elements
    const chatMessages = document.getElementById("chat-messages");
    const textInput = document.getElementById("text-input");
    const btnSend = document.getElementById("btn-send");
    const btnRecord = document.getElementById("btn-record");
    const btnModeNormal = document.getElementById("btn-mode-normal");
    const btnModeEmergency = document.getElementById("btn-mode-emergency");
    
    // Visualizer Elements
    const visualizerBox = document.getElementById("visualizer-box");
    const waveCanvas = document.getElementById("wave-canvas");
    const canvasCtx = waveCanvas.getContext("2d");
    const recordingTimer = document.getElementById("recording-timer");
    const panicAcousticBadge = document.getElementById("panic-acoustic-badge");
    
    // Audio Player
    const audioPlayer = document.getElementById("audio-player");
    
    // Shelter Feed
    const shelterFeed = document.getElementById("shelter-feed");

    // ------------------------------------------
    // 1. LIVE EOC CLOCK
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
    // 2. SYSTEM STATE CONTROL
    // ------------------------------------------
    function setSystemMode(mode) {
        currentMode = mode;
        if (mode === "emergency") {
            body.classList.add("emergency-active");
            btnModeEmergency.classList.add("active");
            btnModeNormal.classList.remove("active");
            systemModeBadge.style.borderColor = "hsla(346, 84%, 61%, 0.4)";
            modeText.textContent = "ತುರ್ತು ಮೋಡ್ (EMERGENCY ACTIVE)";
        } else {
            body.classList.remove("emergency-active");
            btnModeNormal.classList.add("active");
            btnModeEmergency.classList.remove("active");
            systemModeBadge.style.borderColor = "hsla(142, 70%, 45%, 0.4)";
            modeText.textContent = "ಸಾಮಾನ್ಯ ಮೋಡ್ (NORMAL)";
        }
    }

    btnModeNormal.addEventListener("click", () => setSystemMode("normal"));
    btnModeEmergency.addEventListener("click", () => setSystemMode("emergency"));

    // ------------------------------------------
    // 3. INTERACTIVE GIS RELIEF SHELTERS MAP (Leaflet.js)
    // ------------------------------------------
    // Coordinate center of Karnataka: 14.5° N, 75.7° E
    const map = L.map('gis-map', {
        zoomControl: false,
        attributionControl: false
    }).setView([14.5, 75.7], 6.5);

    // Dark-themed tiles cartodb
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 19
    }).addTo(map);

    // Custom pins for camps
    const greenIcon = new L.Icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
        iconSize: [20, 32],
        iconAnchor: [10, 32],
        popupAnchor: [1, -34],
        shadowSize: [32, 32]
    });

    const redIcon = new L.Icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
        iconSize: [20, 32],
        iconAnchor: [10, 32],
        popupAnchor: [1, -34],
        shadowSize: [32, 32]
    });

    let shelterMarkers = {};
    let activeSheltersData = [];

    // Load Shelter Data from Flask
    async function loadShelters() {
        try {
            const response = await fetch("/api/shelters");
            const shelters = await response.json();
            activeSheltersData = shelters;
            
            // Clear Skeleton
            shelterFeed.innerHTML = "";

            shelters.forEach(camp => {
                const icon = camp.status === "OPEN" ? greenIcon : redIcon;
                
                // Add marker
                const marker = L.marker([camp.lat, camp.lng], { icon: icon }).addTo(map);
                
                // Popup HTML
                const popupContent = `
                    <div style="font-family: var(--font-body);">
                        <h4 style="margin:0 0 4px 0; color: #f8fafc; font-size:0.85rem;">${camp.name_kn}</h4>
                        <p style="margin:0 0 2px 0; font-size:0.7rem; color: #94a3b8;">District: ${camp.district}</p>
                        <p style="margin:0; font-size:0.7rem; color: ${camp.status === 'OPEN' ? '#22c55e' : '#f43f5e'}; font-weight:700;">
                            Status: ${camp.status} (${camp.capacity_used}/${camp.capacity_max})
                        </p>
                    </div>
                `;
                marker.bindPopup(popupContent);
                shelterMarkers[camp.id] = marker;

                // Render Card in Feed
                const card = document.createElement("div");
                card.className = "shelter-item";
                card.id = `camp-card-${camp.id}`;
                
                const percent = Math.min(100, Math.round((camp.capacity_used / camp.capacity_max) * 100));
                
                card.innerHTML = `
                    <div class="shelter-item-header">
                        <h4>${camp.name_kn}</h4>
                        <span class="status-pill ${camp.status.toLowerCase()}">${camp.status}</span>
                    </div>
                    <div class="shelter-item-details">
                        <span>ಜಿಲ್ಲೆ: ${camp.district_kn}</span>
                        <span>ಸಾಮರ್ಥ್ಯ: ${camp.capacity_used}/${camp.capacity_max}</span>
                    </div>
                    <div class="shelter-capacity-bar">
                        <div class="shelter-capacity-fill" style="width: ${percent}%; background-color: ${camp.status === 'OPEN' ? 'var(--color-normal)' : 'var(--color-emergency)'}"></div>
                    </div>
                `;

                // Card Click Zoom and Select
                card.addEventListener("click", () => {
                    // Zoom map to marker
                    map.setView([camp.lat, camp.lng], 10);
                    marker.openPopup();
                    
                    // Highlight card
                    document.querySelectorAll(".shelter-item").forEach(c => c.classList.remove("selected-item"));
                    card.classList.add("selected-item");
                });

                shelterFeed.appendChild(card);
            });
        } catch (error) {
            console.error("Error loading shelters:", error);
            shelterFeed.innerHTML = `<div class="shelter-skeleton" style="color: var(--color-emergency);">ಸಂಪರ್ಕ ದೋಷ: ಮ್ಯಾಪ್ ಲೋಡ್ ಮಾಡಲು ಸಾಧ್ಯವಿಲ್ಲ.</div>`;
        }
    }
    
    loadShelters();

    // ------------------------------------------
    // 4. CHAT HISTORY UI HANDLERS
    // ------------------------------------------
    function appendMessage(role, text, isEmergencyBubble = false) {
        const messageDiv = document.createElement("div");
        messageDiv.className = `chat-message ${role}`;
        if (role === "bot" && isEmergencyBubble) {
            messageDiv.classList.add("emergency-bubble");
        }
        
        const avatarIcon = role === "bot" ? "fa-user-shield" : "fa-user";
        const now = new Date();
        const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
        
        messageDiv.innerHTML = `
            <div class="chat-avatar">
                <i class="fa-solid ${avatarIcon}"></i>
            </div>
            <div class="chat-bubble">
                ${text.replace(/\n/g, "<br>")}
                <div class="timestamp">${timeStr}</div>
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function showTypingIndicator() {
        const typingDiv = document.createElement("div");
        typingDiv.className = "chat-message bot typing-indicator-msg";
        typingDiv.innerHTML = `
            <div class="chat-avatar">
                <i class="fa-solid fa-user-shield"></i>
            </div>
            <div class="chat-bubble" style="padding: 0.6rem 1rem;">
                <span class="pulse-dot" style="margin-right:2px; display:inline-block; width:6px; height:6px; background:#60a5fa; border-radius:50%; animation: flashBlink 0.6s infinite alternate;"></span>
                <span class="pulse-dot" style="margin-right:2px; display:inline-block; width:6px; height:6px; background:#60a5fa; border-radius:50%; animation: flashBlink 0.6s infinite alternate; animation-delay:0.2s;"></span>
                <span class="pulse-dot" style="display:inline-block; width:6px; height:6px; background:#60a5fa; border-radius:50%; animation: flashBlink 0.6s infinite alternate; animation-delay:0.4s;"></span>
            </div>
        `;
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return typingDiv;
    }

    // ------------------------------------------
    // 5. TEXT SEND PIPELINE
    // ------------------------------------------
    async function sendTextQuery(text) {
        if (!text.trim()) return;
        
        appendMessage("user", text);
        textInput.value = "";
        
        const indicator = showTypingIndicator();

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question: text, emergency_mode: currentMode })
            });

            const data = await response.json();
            indicator.remove();
            
            // Adjust visual EOC mode if the response triggers emergency
            if (data.mode === "emergency") {
                setSystemMode("emergency");
            } else {
                setSystemMode("normal");
            }
            
            appendMessage("bot", data.response, data.mode === "emergency");
            
            // TTS Response playback
            if (data.audio_url) {
                audioPlayer.src = data.audio_url;
                audioPlayer.play();
            }

        } catch (error) {
            console.error("Chat error:", error);
            indicator.remove();
            appendMessage("bot", "ಕ್ಷಮಿಸಿ, ಪ್ರತಿಕ್ರಿಯೆ ಪಡೆಯಲು ಸರ್ವರ್ ತಲುಪಲು ಸಾಧ್ಯವಾಗಿಲ್ಲ.");
        }
    }

    btnSend.addEventListener("click", () => {
        sendTextQuery(textInput.value);
    });

    textInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            sendTextQuery(textInput.value);
        }
    });

    // Quick trigger prompts
    document.querySelectorAll(".trigger-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const query = btn.getAttribute("data-query");
            sendTextQuery(query);
        });
    });

    // ------------------------------------------
    // 6. NATIVE MICROPHONE RECORDING & CANVAS VISUALIZER
    // ------------------------------------------
    function resizeCanvas() {
        waveCanvas.width = visualizerBox.offsetWidth;
        waveCanvas.height = 60;
    }
    window.addEventListener("resize", resizeCanvas);

    // Live Canvas Oscilloscope Visualizer
    function drawVisualizer() {
        drawVisual = requestAnimationFrame(drawVisualizer);
        analyser.getByteTimeDomainData(dataArray);

        canvasCtx.fillStyle = 'rgba(15, 23, 42, 0.4)';
        canvasCtx.fillRect(0, 0, waveCanvas.width, waveCanvas.height);

        canvasCtx.lineWidth = 2.5;
        // Adjust line color dynamically based on EOC state or live volume
        canvasCtx.strokeStyle = currentMode === "emergency" ? 'rgb(244, 63, 94)' : 'rgb(34, 197, 94)';

        canvasCtx.beginPath();
        let sliceWidth = waveCanvas.width * 1.0 / dataArray.length;
        let x = 0;

        for (let i = 0; i < dataArray.length; i++) {
            let v = dataArray[i] / 128.0;
            let y = v * waveCanvas.height / 2;

            if (i === 0) {
                canvasCtx.moveTo(x, y);
            } else {
                canvasCtx.lineTo(x, y);
            }

            x += sliceWidth;
        }

        canvasCtx.lineTo(waveCanvas.width, waveCanvas.height / 2);
        canvasCtx.stroke();

        // Calculate active RMS volume in real-time
        let sumSquares = 0;
        for (let i = 0; i < dataArray.length; i++) {
            let normalizedVal = (dataArray[i] - 128) / 128.0; // from -1.0 to 1.0
            sumSquares += normalizedVal * normalizedVal;
        }
        let currentRms = Math.sqrt(sumSquares / dataArray.length);
        if (currentRms > clientRmsMax) {
            clientRmsMax = currentRms;
        }

        // Live Voice Stress Panic trigger detection
        if (clientRmsMax > PANIC_VOLUME_THRESHOLD) {
            panicAcousticBadge.classList.remove("hidden");
            setSystemMode("emergency"); // Force immediate EOC visual upgrade to Emergency
        }
    }

    // Toggle Microphone recording
    async function startRecording() {
        audioChunks = [];
        clientRmsMax = 0;
        panicAcousticBadge.classList.add("hidden");
        
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            // Build Audio Context nodes
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const source = audioContext.createMediaStreamSource(stream);
            analyser = audioContext.createAnalyser();
            analyser.fftSize = 512;
            source.connect(analyser);
            
            const bufferLength = analyser.frequencyBinCount;
            dataArray = new Uint8Array(bufferLength);

            // Configure Media Recorder
            mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
            
            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                // Terminate visualizer
                cancelAnimationFrame(drawVisual);
                audioContext.close();
                stream.getTracks().forEach(track => track.stop());
                
                // Submit audio data
                await uploadVoiceBlob();
            };

            // Start visual feedback
            visualizerBox.classList.add("active");
            btnRecord.classList.add("recording");
            resizeCanvas();
            drawVisualizer();

            // Timer
            recordStartTime = Date.now();
            recordingTimer.textContent = "0.0s";
            recordingTimerInterval = setInterval(() => {
                let seconds = ((Date.now() - recordStartTime) / 1000).toFixed(1);
                recordingTimer.textContent = `${seconds}s`;
            }, 100);

            mediaRecorder.start(250); // Capture data chunks every 250ms

        } catch (error) {
            console.error("Recording initialization failed:", error);
            alert("ಮೈಕ್ರೋಫೋನ್ ಅನುಮತಿ ಸಿಕ್ಕಿಲ್ಲ. ದಯವಿಟ್ಟು ಅನುಮತಿ ನೀಡಿ.");
        }
    }

    function stopRecording() {
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
    // 7. VOICE UPLOAD & SPEECH-RAG RESPONSE PIPELINE
    // ------------------------------------------
    async function uploadVoiceBlob() {
        if (audioChunks.length === 0) return;

        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append("file", audioBlob, "voice.webm");
        
        // Pass emergency context
        formData.append("is_panic", clientRmsMax > PANIC_VOLUME_THRESHOLD ? "true" : "false");
        formData.append("manual_mode", currentMode);

        const indicator = showTypingIndicator();

        try {
            const response = await fetch("/api/voice", {
                method: "POST",
                body: formData
            });

            const data = await response.json();
            indicator.remove();

            if (!data.transcript) {
                appendMessage("bot", "ಕ್ಷಮಿಸಿ, ನಿಮ್ಮ ಧ್ವನಿ ಸರಿಯಾಗಿ ಸ್ಪಷ್ಟವಾಗಿ ಕೇಳಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೊಮ್ಮೆ ಪ್ರಯತ್ನಿಸಿ.");
                return;
            }

            // Append Transcript and response
            appendMessage("user", `🎙️ [ಧ್ವನಿ ಪ್ರಶ‍್ನೆ]: ${data.transcript}`);
            
            // Adjust visual EOC mode depending on backend return state
            if (data.mode === "emergency") {
                setSystemMode("emergency");
            } else {
                setSystemMode("normal");
            }

            appendMessage("bot", data.response, data.mode === "emergency");

            // Play synthesized response audio
            if (data.audio_url) {
                audioPlayer.src = `${data.audio_url}?t=${Date.now()}`; // Prevent browser audio cache issues
                audioPlayer.play();
            }

        } catch (error) {
            console.error("Voice process error:", error);
            indicator.remove();
            appendMessage("bot", "ಧ್ವನಿ ಸಂಸ್ಕರಿಸುವಲ್ಲಿ ಸರ್ವರ್ ತೋಷ ಸಂಭವಿಸಿದೆ.");
        }
    }
});
