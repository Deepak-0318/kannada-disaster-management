import sounddevice as sd
import scipy.io.wavfile as wav
import whisper
from gtts import gTTS
import streamlit as st

# Load model
whisper_model = whisper.load_model("base")

# 🎤 Record audio
def record_audio(filename="input.wav", duration=5, fs=16000):
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    audio = (audio * 32767).astype("int16")
    wav.write(filename, fs, audio)
    return filename

# 🧠 Speech → Text
def speech_to_text(audio_file):
    result = whisper_model.transcribe(audio_file)
    return result["text"].strip()

# 🔊 Text → Speech
def speak(text):
    tts = gTTS(text=text, lang='kn')
    audio_file = "output.mp3"
    tts.save(audio_file)

    with open(audio_file, "rb") as f:
        audio_bytes = f.read()
        st.audio(audio_bytes, format="audio/mp3")