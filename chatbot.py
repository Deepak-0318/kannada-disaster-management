import os
import json
import faiss
import numpy as np

from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer

# -----------------------------------
# LOAD ENV
# -----------------------------------

load_dotenv()

# -----------------------------------
# GROQ CLIENT
# -----------------------------------

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

# -----------------------------------
# LOAD EMBEDDING MODEL
# -----------------------------------

print("Loading embedding model...")

embedding_model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# -----------------------------------
# LOAD VECTOR DATABASE
# -----------------------------------

print("Loading vector database...")

index = faiss.read_index(
    "vectorstore/disaster_index.faiss"
)

with open(
    "vectorstore/disaster_metadata.json",
    "r",
    encoding="utf-8"
) as f:

    metadata = json.load(f)

print("Chatbot ready!\n")

# -----------------------------------
# RETRIEVE CONTEXT
# -----------------------------------

def retrieve_context(query, top_k=3):

    query_embedding = embedding_model.encode([query])

    query_embedding = np.array(
        query_embedding
    ).astype("float32")

    distances, indices = index.search(
        query_embedding,
        top_k
    )

    contexts = []

    for idx in indices[0]:

        item = metadata[idx]

        context = f"""
Category: {item['category']}

Question:
{item['question']}

Answer:
{item['answer']}
"""

        contexts.append(context)

    return "\n".join(contexts)

# -----------------------------------
# CHATBOT FUNCTION
# -----------------------------------

def ask_chatbot(user_query):

    retrieved_context = retrieve_context(user_query)

    prompt = f"""
You are a Kannada Disaster Management AI Assistant.

Rules:
- Answer ONLY in Kannada
- Give short practical disaster guidance
- Use simple conversational Kannada
- Avoid fake information
- Prioritize user safety

Retrieved Context:
{retrieved_context}

User Question:
{user_query}

Respond in MAXIMUM 5 short lines.

Format:
- Situation
- 2 or 3 safety steps
- Emergency number

Keep response concise for emergency use.
"""

    completion = client.chat.completions.create(

        model="llama-3.3-70b-versatile",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0.3
    )

    return completion.choices[0].message.content

# -----------------------------------
# MAIN LOOP
# -----------------------------------

if __name__ == "__main__":

    while True:

        query = input("Ask in Kannada: ")

        if query.lower() == "exit":
            break

        try:

            answer = ask_chatbot(query)

            print("\nAssistant:\n")

            print(answer)

            print()

        except Exception as e:

            print("\nERROR:")
            print(e)
            print()