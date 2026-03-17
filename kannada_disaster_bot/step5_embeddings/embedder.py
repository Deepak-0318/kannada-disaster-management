import json
import os
from sentence_transformers import SentenceTransformer
import numpy as np
import pickle

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CHUNKS_FILE = os.path.join(ROOT_DIR, "..", "step4_knowledge_builder", "knowledge_chunks.json")

EMBEDDINGS_FILE = os.path.join(ROOT_DIR, "chunk_embeddings.npy")
METADATA_FILE = os.path.join(ROOT_DIR, "chunk_metadata.pkl")

# Use multilingual model (works for Kannada + English)
MODEL_NAME = "intfloat/multilingual-e5-base"


def generate_embeddings():
    print("Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)

    print("Loading chunks...")
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    texts = [chunk["content"] for chunk in chunks]

    print(f"Generating embeddings for {len(texts)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=True)

    embeddings = np.array(embeddings)

    np.save(EMBEDDINGS_FILE, embeddings)

    # Save metadata
    with open(METADATA_FILE, "wb") as f:
        pickle.dump(chunks, f)

    print("Embeddings generated and saved.")


if __name__ == "__main__":
    generate_embeddings()
