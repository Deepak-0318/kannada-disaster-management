import streamlit as st
from chatbot import ask_bot
from voice_utils import record_audio, speech_to_text, speak

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Kannada Disaster Chatbot",
    page_icon="🌊",
    layout="wide"
)

st.title("🌊 Kannada Disaster Management Chatbot")
st.markdown("💬 Ask disaster-related questions in Kannada (Text or Voice)")

# ---------------- SESSION STATE ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- DISPLAY CHAT HISTORY ----------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# ---------------- TEXT INPUT ----------------
user_input = st.chat_input("Type your question in Kannada...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("🤖 Thinking..."):
            response = ask_bot(user_input)
            st.write(response)

            # 🔊 Speak response
            speak(response)

    st.session_state.messages.append({"role": "assistant", "content": response})

# ---------------- VOICE INPUT ----------------
st.divider()
st.subheader("🎤 Voice Interaction")

col1, col2 = st.columns(2)

with col1:
    if st.button("🎙️ Speak Now"):
        with st.spinner("🎤 Recording... Speak clearly"):
            audio_file = record_audio()

        with st.spinner("🧠 Converting speech to text..."):
            query = speech_to_text(audio_file)

        if query.strip() == "":
            st.error("⚠️ Could not detect speech. Try again.")
        else:
            # Show user speech
            st.success(f"🗣️ You said: {query}")

            st.session_state.messages.append({"role": "user", "content": query})

            with st.chat_message("user"):
                st.write(query)

            # Generate response
            with st.chat_message("assistant"):
                with st.spinner("🤖 Thinking..."):
                    response = ask_bot(query)
                    st.write(response)

                    # 🔊 Speak response
                    speak(response)

            st.session_state.messages.append({
                "role": "assistant",
                "content": response
            })

with col2:
    st.info("""
    🎯 **Voice Instructions**
    - Click 🎙️ Speak Now  
    - Speak clearly in Kannada  
    - Wait for response  
    - Bot replies in text + voice  
    """)

# ---------------- FOOTER ----------------
st.divider()
st.caption("🚀 Powered by RAG + FAISS + Groq LLM + Whisper + gTTS")