import json
import faiss
import numpy as np
import os
import google.generativeai as genai
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# =========================
# LOAD ENV VARIABLES
# =========================
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ✅ Latest working model
gemini_model = genai.GenerativeModel("models/gemini-flash-latest")

# =========================
# LOAD EMBEDDING MODEL
# =========================
embed_model = SentenceTransformer("BAAI/bge-base-en-v1.5")

# =========================
# LOAD FAISS INDEX
# =========================
index = faiss.read_index("disaster_index.faiss")

# =========================
# LOAD METADATA
# =========================
with open("disaster_metadata.json", "r", encoding="utf-8") as f:
    metadata = json.load(f)

# =========================
# RETRIEVE CONTEXT (RAG)
# =========================
def retrieve_context(query, top_k=5):
    q_embed = embed_model.encode([query], normalize_embeddings=True).astype("float32")
    D, I = index.search(q_embed, top_k)

    results = []
    for idx in I[0][:3]:
        item = metadata[idx]
        results.append(item["output"])

    return "\n".join(results)

# =========================
# MAIN BOT FUNCTION
# =========================
def ask_bot(question):

    context = retrieve_context(question)

    prompt = f"""
ನೀವು ಒಂದು disaster management assistant.

ನಿಯಮಗಳು (STRICT):
- ಉತ್ತರವನ್ನು ಕನ್ನಡದಲ್ಲಿ ಮಾತ್ರ ಕೊಡಿ
- ಖಂಡಿತವಾಗಿ 5 ಪಾಯಿಂಟ್‌ಗಳು ಮಾತ್ರ ಕೊಡಿ
- ಪ್ರತಿಯೊಂದು ಪಾಯಿಂಟ್ 1 ರಿಂದ 5 ಸಂಖ್ಯೆ ಇರಬೇಕು
- ಪ್ರತಿಯೊಂದು ಪಾಯಿಂಟ್ ಸಂಪೂರ್ಣ ವಾಕ್ಯವಾಗಿರಬೇಕು
- ಯಾವುದೇ ಪಾಯಿಂಟ್ ಅರ್ಧದಲ್ಲಿ ನಿಲ್ಲಬಾರದು
- ಪುನರಾವರ್ತನೆ ಬೇಡ
- ಸರಳ ಮತ್ತು ನೈಸರ್ಗಿಕ ಕನ್ನಡ ಬಳಸಿ

ಸಂದರ್ಭ:
{context}

ಪ್ರಶ್ನೆ:
{question}

ಉತ್ತರ:
1.
2.
3.
4.
5.
"""

    response = gemini_model.generate_content(prompt)
    answer = response.text.strip()

    # =========================
    # CLEAN + STRUCTURE OUTPUT
    # =========================
    lines = [line.strip() for line in answer.split("\n") if line.strip()]

    points = []
    for line in lines:
        if line.startswith(("1", "2", "3", "4", "5")):
            points.append(line)

    # Fallback (rare case)
    if len(points) < 5:
        return "\n".join(lines[:5])

    return "\n".join(points[:5])

# =========================
# TERMINAL TEST
# =========================
def main():
    print("\n🚀 Chatbot Ready\n")

    while True:
        q = input("🧑 You: ")

        if q.lower() == "exit":
            print("👋 Exiting chatbot...")
            break

        if not q.strip():
            continue

        ans = ask_bot(q)

        print("\n🤖 Bot:\n", ans)
        print("-" * 50)

# =========================
if __name__ == "__main__":
    main()