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

# Latest working model
gemini_model = genai.GenerativeModel("models/gemini-flash-latest")

# =========================
# LOAD EMBEDDING MODEL
# =========================
embed_model = SentenceTransformer("BAAI/bge-small-en-v1.5", local_files_only=True)

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
    for idx in I[0]:
        item = metadata[idx]
        results.append(item["answer"])

    context = "\n\n".join([f"- {r}" for r in results])
    return context


# =========================
# MAIN BOT FUNCTION
# =========================
def ask_bot(question):
    if not any("\u0C80" <= c <= "\u0CFF" for c in question):
        question = f"ಈ ಪ್ರಶ್ನೆಯನ್ನು ಕನ್ನಡದಲ್ಲಿ ಅರ್ಥಮಾಡಿಕೊಳ್ಳಿ: {question}"

    context = retrieve_context(question)
    if not context.strip():
        context = "ಸಾಮಾನ್ಯ ವಿಪತ್ತು ಸುರಕ್ಷತಾ ಮಾರ್ಗದರ್ಶನ ನೀಡಿರಿ"

    prompt = f"""
ನೀವು ಒಂದು disaster management assistant.

ಕಟ್ಟುನಿಟ್ಟಿನ ನಿಯಮಗಳು:
- ಉತ್ತರ ಕನ್ನಡದಲ್ಲಿ ಮಾತ್ರ ಇರಬೇಕು
- ಕಡ್ಡಾಯವಾಗಿ 5 ಪಾಯಿಂಟ್‌ಗಳು
- 1 ರಿಂದ 5 ಕ್ರಮದಲ್ಲಿ ಸಂಖ್ಯೆ
- ಪ್ರತಿಯೊಂದು ಪಾಯಿಂಟ್ ಪೂರ್ಣ ವಾಕ್ಯವಾಗಿರಬೇಕು
- ಪುನರಾವರ್ತನೆ ಮಾಡಬಾರದು
- ಅರ್ಥಪೂರ್ಣ ಮತ್ತು ಪ್ರಾಯೋಗಿಕ ಸಲಹೆಗಳು ಮಾತ್ರ ಕೊಡಬೇಕು

ಸಂದರ್ಭ ಮಾಹಿತಿ:
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
    print("\nChatbot Ready\n")

    while True:
        q = input("You: ")

        if q.lower() == "exit":
            print("Exiting chatbot...")
            break

        if not q.strip():
            continue

        ans = ask_bot(q)

        print("\nBot:\n", ans)
        print("-" * 50)


# =========================
if __name__ == "__main__":
    main()
