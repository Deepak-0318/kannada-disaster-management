import os
import json
import asyncio
import numpy as np
import soundfile as sf
import edge_tts
from flask import Flask, render_template, request, jsonify

# Import core chatbot & voice model functions
from chatbot import ask_bot, check_lexical_urgency
from voice_agent import speech_to_text

# ==========================================
# FLASK CONFIGURATION
# ==========================================
app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)

# Ensure static directories exist
os.makedirs("static", exist_ok=True)
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)

# Path to the mock GIS shelter database
SHELTERS_DB_PATH = os.path.join("dataset", "shelter_data.json")

# Calibrated Server-Side RMS stress volume threshold
SERVER_PANIC_THRESHOLD = 0.18

# ==========================================
# SPEECH SYNTHESIS ENGINE (TTS)
# ==========================================
async def synthesize_speech(text, output_path):
    """
    Synthesize speech using Microsoft Edge-TTS with Kannada Sapna voice.
    """
    try:
        communicate = edge_tts.Communicate(
            text,
            voice="kn-IN-SapnaNeural"
        )
        await communicate.save(output_path)
    except Exception as e:
        print(f"❌ Speech Synthesis Error: {e}")

def run_tts_sync(text, output_path):
    """
    Synchronous wrapper for running Edge-TTS in Flask request threads.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    loop.run_until_complete(synthesize_speech(text, output_path))


# ==========================================
# 1. PAGE ROUTER
# ==========================================
@app.route("/")
def index():
    """
    Serve the main EOC control room dashboard.
    """
    return render_template("index.html")


# ==========================================
# 2. GET SHELTERS ROUTE (GIS FEED)
# ==========================================
@app.route("/api/shelters", methods=["GET"])
def get_shelters():
    """
    Return active relief camps across Karnataka.
    """
    try:
        if os.path.exists(SHELTERS_DB_PATH):
            with open(SHELTERS_DB_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return jsonify(data)
        return jsonify([])
    except Exception as e:
        print(f"❌ Map Database Read Error: {e}")
        return jsonify([]), 500


# ==========================================
# 3. TEXT CHAT ROUTE
# ==========================================
@app.route("/api/chat", methods=["POST"])
def api_chat():
    """
    Handle plain text query inputs.
    """
    try:
        data = request.json or {}
        question = data.get("question", "").strip()
        manual_mode = data.get("emergency_mode", "normal")
        
        if not question:
            return jsonify({"error": "No question provided"}), 400

        # Perform lexical urgency scanning
        lexical_urgent = check_lexical_urgency(question)
        is_emergency = (manual_mode == "emergency") or lexical_urgent

        # Query the hybrid-RAG ask_bot engine
        response_text = ask_bot(question, emergency_mode=is_emergency)

        # Synthesize audio file for text replies as well
        tts_filename = "temp_text_response.mp3"
        tts_filepath = os.path.join("static", tts_filename)
        if os.path.exists(tts_filepath):
            try:
                os.remove(tts_filepath)
            except Exception:
                pass
        
        run_tts_sync(response_text, tts_filepath)

        return jsonify({
            "response": response_text,
            "mode": "emergency" if is_emergency else "normal",
            "audio_url": f"/static/{tts_filename}"
        })

    except Exception as e:
        print(f"❌ Text API Error: {e}")
        return jsonify({"error": str(e)}), 500


# ==========================================
# 4. SPEECH-TO-TEXT VOICE RAG ROUTE
# ==========================================
@app.route("/api/voice", methods=["POST"])
def api_voice():
    """
    Handle browser-native voice recording uploads (AJAX blobs).
    """
    audio_file = request.files.get("file")
    client_panic = request.form.get("is_panic") == "true"
    manual_mode = request.form.get("manual_mode", "normal")

    if not audio_file:
        return jsonify({"error": "No audio file provided"}), 400

    # Save uploaded voice blob locally
    upload_path = os.path.join("static", "temp_voice.webm")
    audio_file.save(upload_path)

    # 1. SPEECH TO TEXT TRANSCRIPTION
    # whisper-model (Faster-Whisper) is loaded once when voice_agent module is imported
    transcript = speech_to_text(upload_path)

    if not transcript:
        return jsonify({
            "transcript": "",
            "response": "ಕ್ಷಮಿಸಿ, ಧ್ವನಿ ಅಸ್ಪಷ್ಟವಾಗಿದೆ. ದಯವಿಟ್ಟು ಮತ್ತೊಮ್ಮೆ ಮಾತನಾಡಿ.",
            "mode": manual_mode
        })

    # 2. ACOUSTIC ANALYSIS (FALLBACK SERVER-SIDE CHECK)
    server_panic = False
    try:
        # If the file format can be read by soundfile, measure amplitude energy
        data, samplerate = sf.read(upload_path)
        rms = np.sqrt(np.mean(data**2))
        print(f"DEBUG AUDIO RMS: {rms:.4f}")
        if rms > SERVER_PANIC_THRESHOLD:
            server_panic = True
    except Exception as e:
        # Ignore decoding errors from webm/opus format and rely on client-side analysis
        print(f"DEBUG server RMS check skipped (webm opus format). Using client RMS flag: {client_panic}")

    # 3. SEMANTIC URGENCE CHECK
    lexical_urgent = check_lexical_urgency(transcript)

    # Determine final Emergency State (Acoustic OR Lexical OR Manual Override)
    is_emergency = (manual_mode == "emergency") or client_panic or server_panic or lexical_urgent
    print(f"DEBUG State: Emergency={is_emergency} (ClientPanic={client_panic}, ServerPanic={server_panic}, Lexical={lexical_urgent}, Manual={manual_mode})")

    # 4. CHATBOT QUERY
    response_text = ask_bot(transcript, emergency_mode=is_emergency)

    # 5. TEXT TO SPEECH RESPONSE SYNTHESIS
    tts_filename = "temp_voice_response.mp3"
    tts_filepath = os.path.join("static", tts_filename)
    
    # Try deleting previous static voice response file to prevent file locks
    if os.path.exists(tts_filepath):
        try:
            os.remove(tts_filepath)
        except Exception:
            pass

    run_tts_sync(response_text, tts_filepath)

    return jsonify({
        "transcript": transcript,
        "response": response_text,
        "mode": "emergency" if is_emergency else "normal",
        "audio_url": f"/static/{tts_filename}"
    })


# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    print("\nState Emergency Operations Center Dashboard booting...")
    
    # Warm up models (SPEC-05)
    from chatbot import warmup_models
    warmup_models()
    
    print("Flask server serving on http://127.0.0.1:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=True)
