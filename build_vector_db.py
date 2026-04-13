import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-small-en-v1.5")

data = []
metadata = []

def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]

# Load BOTH datasets
dataset1 = load_jsonl("dataset/kannada_disaster_7000.jsonl")
dataset2 = load_jsonl("dataset/kannada_disaster_dataset.jsonl")

combined = dataset1 + dataset2

print("Total samples:", len(combined))

for item in combined:
    question = item.get("instruction", "")
    answer = item.get("output", "")

    text = question + " " + answer

    data.append(text)

    metadata.append({
        "question": question,
        "answer": answer
    })

# Embeddings
embeddings = model.encode(data, normalize_embeddings=True)
embeddings = np.array(embeddings).astype("float32")

# FAISS
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

faiss.write_index(index, "disaster_index.faiss")

with open("disaster_metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False)

print("Vector DB rebuilt with merged dataset")