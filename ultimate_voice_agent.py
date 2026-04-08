import os
import asyncio
import numpy as np
import sounddevice as sd
import soundfile as sf
from dotenv import load_dotenv
from faster_whisper import WhisperModel
import edge_tts
from chatbot import ask_bot

# =========================
# CONFIG
# =========================
SAMPLE_RATE = 16000
DURATION = 5   # optimal balance

# =========================
# LOAD ENV
# =========================
load_dotenv()

# =========================
# LOAD WHISPER MODEL
# =========================
whisper_model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)

# =========================
# RECORD AUDIO
# =========================
def record_audio():
    print("\n🎤 Speak now...")

    audio = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1
    )
    sd.wait()

    audio = (audio * 32767).astype("int16")
    sf.write("temp.wav", audio, SAMPLE_RATE)

    return "temp.wav"

# =========================
# SPEECH TO TEXT (KAN)
# =========================
def speech_to_text(audio_file):

    try:
        segments, _ = whisper_model.transcribe(
            audio_file,
            language="kn",
            beam_size=5,
            best_of=5,
            temperature=0.0,
            vad_filter=True   # 🔥 removes silence/noise
        )

        text = " ".join([seg.text for seg in segments]).strip()

        # 🔁 fallback if weak detection
        if len(text) < 3:
            segments, _ = whisper_model.transcribe(audio_file)
            text = " ".join([seg.text for seg in segments]).strip()

        if text == "":
            print("⚠️ Could not understand speech")
            return ""

        print("🗣️ You:", text)
        return text

    except Exception as e:
        print("❌ STT Error:", e)
        return ""

# =========================
# TEXT TO SPEECH (KAN)
# =========================
async def speak_async(text):

    try:
        communicate = edge_tts.Communicate(
            text,
            voice="kn-IN-SapnaNeural"  # Kannada voice
        )

        await communicate.save("output.mp3")

        data, samplerate = sf.read("output.mp3")
        sd.play(data, samplerate)
        sd.wait()

    except Exception as e:
        print("❌ TTS Error:", e)

def speak(text):
    asyncio.run(speak_async(text))

# =========================
# MAIN LOOP
# =========================
def main():

    print("\n🚀 Kannada Voice Agent Ready!")
    print("Press ENTER to speak | type 'exit' to quit\n")

    while True:

        user_input = input("👉 Press ENTER... ")

        if user_input.lower() == "exit":
            print("👋 Exiting...")
            break

        # 🎤 RECORD
        audio_file = record_audio()

        # 🧠 STT
        query = speech_to_text(audio_file)

        if not query:
            continue

        # 🤖 RAG + GEMINI
        try:
            response = ask_bot(query)
        except Exception as e:
            print("❌ LLM Error:", e)
            continue

        print("\n🤖 Bot:\n", response)

        # 🔊 SPEAK
        print("🔊 Speaking...\n")
        speak(response)

# =========================
if __name__ == "__main__":
    main()