import os
import asyncio
import numpy as np
import sounddevice as sd
import soundfile as sf
from dotenv import load_dotenv
from faster_whisper import WhisperModel
import google.generativeai as genai
import edge_tts
from chatbot import ask_bot

# =========================
# CONFIG
# =========================
SAMPLE_RATE = 16000
DURATION = 7   # instead of 5

# =========================
# LOAD ENV
# =========================
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# =========================
# LOAD WHISPER MODEL
# =========================
whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
transliteration_model = genai.GenerativeModel("models/gemini-flash-latest")


def is_kannada(text):
    for ch in text:
        if "\u0C80" <= ch <= "\u0CFF":
            return True
    return False


def has_long_repetition(text, threshold=6):
    count = 1
    previous = ""

    for ch in text:
        if ch == previous and not ch.isspace():
            count += 1
            if count >= threshold:
                return True
        else:
            count = 1
            previous = ch

    return False


def is_valid_kannada_query(text):
    cleaned = text.strip()
    if not cleaned:
        return False

    if has_long_repetition(cleaned):
        return False

    kannada_chars = [ch for ch in cleaned if "\u0C80" <= ch <= "\u0CFF"]
    alpha_chars = [ch for ch in cleaned if ch.isalpha()]
    words = [word for word in cleaned.split() if word]
    if len(words) < 2:
        return False

    if len(alpha_chars) < 6:
        return False

    if kannada_chars:
        if len(kannada_chars) < 4:
            return False
        if alpha_chars and (len(kannada_chars) / len(alpha_chars)) < 0.35:
            return False

    return True


def transliterate_to_kannada(text):
    if not text or is_kannada(text):
        return text

    try:
        prompt = f"""
Convert the following spoken Kannada text into proper Kannada script.
Return only the Kannada text, with no explanation.

Text:
{text}
"""
        response = transliteration_model.generate_content(prompt)
        converted = response.text.strip()
        if is_kannada(converted):
            return converted
    except Exception as e:
        print("Transliteration fallback error:", e)

    return text


# =========================
# RECORD AUDIO
# =========================
def record_audio():
    print("\nSpeak now...")

    audio = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32"
    )
    sd.wait()

    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val

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
            task="transcribe",
            beam_size=1,
            best_of=1,
            temperature=0.0,
            condition_on_previous_text=False,
            vad_filter=True
        )

        text = " ".join([seg.text for seg in segments]).strip()
        print("DEBUG RAW TEXT:", text)

        if not is_valid_kannada_query(text):
            print("⚠️ Could not understand clearly, retrying...")
            return ""

        text = transliterate_to_kannada(text)

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
            voice="kn-IN-SapnaNeural"
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
    print("\nKannada Voice Agent Ready!")
    print("Press ENTER to speak | type 'exit' to quit\n")

    while True:
        user_input = input("Press ENTER... ")

        if user_input.lower() == "exit":
            print("Exiting...")
            break

        audio_file = record_audio()
        query = speech_to_text(audio_file)

        if not query:
            continue

        try:
            response = ask_bot(query)
        except Exception as e:
            print("❌ LLM Error:", e)
            continue

        print("\nBot:\n", response)
        print("Speaking...\n")
        speak(response)


# =========================
if __name__ == "__main__":
    main()
