import streamlit as st
import threading
from chatbot import ask_bot
from voice_agent import record_audio, speech_to_text, speak


# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Kannada Disaster Assistant",
    page_icon="🌊",
    layout="centered"
)

# ---------------- HEADER ----------------
st.title("🌊 Kannada Disaster Assistant")
st.caption("Ask your question using text or voice")

# ---------------- SESSION ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- DISPLAY CHAT ----------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ---------------- INPUT MODE ----------------
mode = st.radio(
    "Choose Input Mode:",
    ["💬 Text", "🎤 Voice"],
    horizontal=True
)

# ========================
# TEXT MODE
# ========================
if mode == "💬 Text":

    user_input = st.chat_input("Type your question...")

    if user_input:

        # USER MESSAGE
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.write(user_input)

        # BOT RESPONSE
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = ask_bot(user_input)
                st.write(response)

                # 🔊 Voice output (non-blocking)
                threading.Thread(target=speak, args=(response,), daemon=True).start()

        st.session_state.messages.append({"role": "assistant", "content": response})

# ========================
# VOICE MODE
# ========================
elif mode == "🎤 Voice":

    st.markdown("Click below and speak in Kannada")

    if st.button("🎙️ Start Speaking"):

        with st.spinner("Listening..."):
            audio_file = record_audio()

        with st.spinner("Processing..."):
            query = speech_to_text(audio_file)

        if not query:
            st.warning("Could not understand. Try again.")
        else:
            # USER MESSAGE
            st.session_state.messages.append({"role": "user", "content": query})

            with st.chat_message("user"):
                st.write(query)

            # BOT RESPONSE
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = ask_bot(query)
                    st.write(response)

                    # 🔊 Voice output
                    threading.Thread(target=speak, args=(response,), daemon=True).start()

            st.session_state.messages.append({"role": "assistant", "content": response})

# ---------------- FOOTER ----------------
st.divider()
st.caption("🎯 Kannada Voice AI • Powered by RAG + Gemini")
