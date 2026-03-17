import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Load embedding model
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

data = []
questions = []

# Load dataset
with open("dataset/kannada_disaster_7000.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        item = json.loads(line)

        question = item["instruction"]
        answer = item["output"]

        text = question + " " + answer

        data.append(text)
        questions.append(item)

print("Loaded samples:", len(data))

# Generate embeddings
embeddings = model.encode(data, normalize_embeddings=True)

embeddings = np.array(embeddings).astype("float32")

# Create FAISS index
dimension = embeddings.shape[1]

index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# Save index
faiss.write_index(index, "disaster_index.faiss")

# Save metadata
with open("disaster_metadata.json", "w", encoding="utf-8") as f:
    json.dump(questions, f, ensure_ascii=False)

print("Vector database built successfully")