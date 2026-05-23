import os
import json
import asyncio
import edge_tts

from flask import (
    Flask,
    render_template,
    request,
    jsonify
)

from chatbot import ask_chatbot
from voice_agent import speech_to_text

# =====================================
# FLASK CONFIG
# =====================================

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)

# =====================================
# CREATE REQUIRED FOLDERS
# =====================================

os.makedirs("static", exist_ok=True)

# =====================================
# TTS FUNCTION
# =====================================

async def synthesize_speech(text, output_path):

    communicate = edge_tts.Communicate(
        text,
        voice="kn-IN-SapnaNeural"
    )

    await communicate.save(output_path)

def run_tts(text, output_path):

    loop = asyncio.new_event_loop()

    asyncio.set_event_loop(loop)

    loop.run_until_complete(
        synthesize_speech(text, output_path)
    )

    loop.close()

# =====================================
# HOME PAGE
# =====================================

@app.route("/")
def home():

    return render_template("index.html")

# =====================================
# TEXT CHAT API
# =====================================

@app.route("/api/chat", methods=["POST"])
def chat_api():

    try:

        data = request.json

        question = data.get("question", "").strip()

        if not question:

            return jsonify({
                "error": "Question missing"
            }), 400

        # Ask chatbot
        response_text = ask_chatbot(question)

        # Generate TTS
        audio_filename = "text_response.mp3"

        audio_path = os.path.join(
            "static",
            audio_filename
        )

        run_tts(response_text, audio_path)

        return jsonify({
            "response": response_text,
            "audio_url": f"/static/{audio_filename}"
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

# =====================================
# VOICE CHAT API
# =====================================

@app.route("/api/voice", methods=["POST"])
def voice_api():

    try:

        audio_file = request.files.get("file")

        if not audio_file:

            return jsonify({
                "error": "No audio uploaded"
            }), 400

        # Save uploaded audio
        upload_path = os.path.join(
            "static",
            "temp_voice.webm"
        )

        audio_file.save(upload_path)

        # Convert speech to text
        transcript = speech_to_text(upload_path)

        if not transcript:

            return jsonify({
                "transcript": "",
                "response": "ಕ್ಷಮಿಸಿ, ಧ್ವನಿ ಸ್ಪಷ್ಟವಾಗಿಲ್ಲ."
            })

        # Ask chatbot
        response_text = ask_chatbot(transcript)

        # Generate TTS
        audio_filename = "voice_response.mp3"

        audio_path = os.path.join(
            "static",
            audio_filename
        )

        run_tts(response_text, audio_path)

        return jsonify({
            "transcript": transcript,
            "response": response_text,
            "audio_url": f"/static/{audio_filename}"
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

# =====================================
# RUN FLASK
# =====================================

if __name__ == "__main__":

    print("\n🚀 Kannada Disaster AI Server Running...")
    print("🌐 http://127.0.0.1:5001\n")

    app.run(
        host="0.0.0.0",
        port=5001,
        debug=True
    )