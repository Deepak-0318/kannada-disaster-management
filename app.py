import streamlit as st
from chatbot import ask_bot

st.set_page_config(page_title="Kannada Disaster Chatbot", page_icon="🌊")

st.title("🌊 Kannada Disaster Management Chatbot")
st.markdown("Ask any disaster-related question in Kannada")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
user_input = st.chat_input("Ask in Kannada...")

if user_input:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = ask_bot(user_input)
            st.write(response)

    # Save response
    st.session_state.messages.append({"role": "assistant", "content": response})