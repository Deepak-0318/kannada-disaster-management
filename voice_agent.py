import asyncio
import numpy as np
import sounddevice as sd
import soundfile as sf
import edge_tts

from faster_whisper import WhisperModel
from chatbot import ask_chatbot

# =====================================
# CONFIG
# =====================================

SAMPLE_RATE = 16000
DURATION = 7

# =====================================
# LOAD WHISPER MODEL
# =====================================

print("Loading Whisper model...")

whisper_model = WhisperModel(
    "small",
    device="cpu",
    compute_type="int8"
)

print("Voice Agent Ready!\n")

# =====================================
# RECORD AUDIO
# =====================================

def record_audio():

    print("\n🎤 Speak now...")

    audio = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32"
    )

    sd.wait()

    # Normalize audio
    max_val = np.max(np.abs(audio))

    if max_val > 0:
        audio = audio / max_val

    audio = (audio * 32767).astype("int16")

    audio_path = "temp.wav"

    sf.write(audio_path, audio, SAMPLE_RATE)

    return audio_path

# =====================================
# SPEECH TO TEXT
# =====================================

def speech_to_text(audio_file):

    try:

        segments, info = whisper_model.transcribe(
            audio_file,
            language="kn",
            task="transcribe",
            beam_size=3,
            vad_filter=True
        )

        text = " ".join(
            [segment.text for segment in segments]
        ).strip()
        
        # If Kannada script missing, try transliteration recovery
        if not any("\u0C80" <= ch <= "\u0CFF" for ch in text):

            transliteration_prompt = f"""
        Convert this Kannada speech transliteration into proper Kannada script.

        Text:
        {text}

        Return ONLY Kannada text.
        """

        try:

            recovered = ask_chatbot(transliteration_prompt)

            if recovered:
                text = recovered.strip()

        except Exception:
            pass

        print(f"\n🗣️ You: {text}")

        return text

    except Exception as e:

        print(f"❌ STT Error: {e}")

        return ""

# =====================================
# TEXT TO SPEECH
# =====================================

async def speak_async(text):

    try:

        communicate = edge_tts.Communicate(
            text,
            voice="kn-IN-SapnaNeural"
        )

        await communicate.save("response.mp3")

        data, samplerate = sf.read("response.mp3")

        sd.play(data, samplerate)

        sd.wait()

    except Exception as e:

        print(f"❌ TTS Error: {e}")

def speak(text):

    asyncio.run(speak_async(text))

# =====================================
# MAIN LOOP
# =====================================

def main():

    print("Press ENTER to speak")
    print("Type 'exit' to quit\n")

    while True:

        user_input = input(">>> ")

        if user_input.lower() == "exit":
            break

        audio_path = record_audio()

        query = speech_to_text(audio_path)

        if not query:
            print("⚠️ Could not understand audio\n")
            continue

        try:

            response = ask_chatbot(query)

            print("\n🤖 Assistant:\n")

            print(response)

            print("\n🔊 Speaking...\n")

            speak(response)

        except Exception as e:

            print(f"❌ Chatbot Error: {e}")

# =====================================

if __name__ == "__main__":

    main()