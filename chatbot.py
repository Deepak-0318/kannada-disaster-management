import json
import faiss
import numpy as np
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from groq import Groq

# =========================
# LOAD ENV VARIABLES
# =========================
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

client = Groq(api_key=api_key)

# =========================
# LOAD EMBEDDING MODEL
# =========================
embed_model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

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
# CLEAN RESPONSE FUNCTION
# =========================
def clean_response(text):
    lines = text.split("\n")
    cleaned = []

    for line in lines:
        line = line.strip()
        if line and line not in cleaned:
            cleaned.append(line)

    return "\n".join(cleaned)

# =========================
# RETRIEVAL FUNCTION
# =========================
def retrieve_context(query, top_k=5):

    q_embed = embed_model.encode(
        [query],
        normalize_embeddings=True
    ).astype("float32")

    D, I = index.search(q_embed, top_k)

    results = []

    for idx in I[0]:
        item = metadata[idx]
        context_text = f"ಪ್ರಶ್ನೆ: {item['instruction']}\nಉತ್ತರ: {item['output']}"
        results.append(context_text)

    return results

# =========================
# RERANKING FUNCTION
# =========================
def rerank_contexts(query, contexts):

    query_embed = embed_model.encode([query], normalize_embeddings=True)

    scores = []

    for ctx in contexts:
        ctx_embed = embed_model.encode([ctx], normalize_embeddings=True)
        score = np.dot(query_embed, ctx_embed.T)[0][0]
        scores.append(score)

    ranked = [x for _, x in sorted(zip(scores, contexts), reverse=True)]

    # remove duplicates
    unique_contexts = []
    for ctx in ranked:
        if ctx not in unique_contexts:
            unique_contexts.append(ctx)

    return unique_contexts[:3]

# =========================
# ANSWER GENERATION
# =========================
def ask_bot(question):

    contexts = retrieve_context(question)
    best_contexts = rerank_contexts(question, contexts)

    combined_context = "\n\n".join(best_contexts)

    prompt = f"""
You are an expert Kannada disaster management assistant.

STRICT RULES:
- Answer ONLY in Kannada
- Give clear, practical disaster safety steps
- Limit answer to 5–6 important points ONLY
- Avoid repetition completely
- Use simple and natural Kannada

Knowledge:
{combined_context}

User Question:
{question}

Final Answer (concise, step-by-step):
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )

    answer = response.choices[0].message.content.strip()

    return clean_response(answer)

# =========================
# TERMINAL CHAT (OPTIONAL)
# =========================
def main():
    print("\n🚀 Kannada Disaster Chatbot Ready!")
    print("Type 'exit' to quit\n")

    while True:
        user_input = input("🧑 User: ")

        if user_input.lower() == "exit":
            print("👋 Exiting chatbot...")
            break

        response = ask_bot(user_input)

        print("\n🤖 Bot:", response)
        print("-" * 50)

if __name__ == "__main__":
    main()