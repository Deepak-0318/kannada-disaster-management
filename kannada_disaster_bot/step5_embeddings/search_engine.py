import os
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

FAISS_INDEX_FILE = os.path.join(ROOT_DIR, "faiss_index.bin")
FAISS_METADATA_FILE = os.path.join(ROOT_DIR, "faiss_metadata.pkl")

MODEL_NAME = "intfloat/multilingual-e5-base"


class SemanticSearchEngine:
    def __init__(self):
        print("Loading embedding model...")
        self.model = SentenceTransformer(MODEL_NAME)

        print("Loading FAISS index...")
        self.index = faiss.read_index(FAISS_INDEX_FILE)

        print("Loading metadata...")
        with open(FAISS_METADATA_FILE, "rb") as f:
            self.metadata = pickle.load(f)

        print("Semantic search engine ready.")

    def search(self, query, top_k=5):
        print(f"\n🔍 Searching for: {query}")

        query_embedding = self.model.encode([query])
        query_embedding = np.array(query_embedding)

        distances, indices = self.index.search(query_embedding, top_k * 3)

        results = []
        seen_contents = set()

        for i, idx in enumerate(indices[0]):
            if idx >= len(self.metadata):
                continue

            chunk_data = self.metadata[idx]
            content = chunk_data["content"]

        # Skip duplicates
            if content in seen_contents:
                continue

        # Skip low quality chunks
            if len(content.strip()) < 60:
                continue

        # Distance threshold (lower = better)
            if distances[0][i] > 0.8:
                continue

            seen_contents.add(content)

            results.append({
                "rank": len(results) + 1,
                "distance": float(distances[0][i]),
                "content": content,
                "disaster_type": chunk_data.get("disaster_type", "general"),
                "source": chunk_data.get("source", "unknown")
            })

            if len(results) == top_k:
                break

        return results



if __name__ == "__main__":
    engine = SemanticSearchEngine()

    while True:
        query = input("\nEnter your query (or type 'exit'): ")
        if query.lower() == "exit":
            break

        results = engine.search(query, top_k=5)

        print("\nTop Results:\n")
        for result in results:
            print(f"Rank: {result['rank']}")
            print(f"Distance: {result['distance']}")
            print(f"Disaster Type: {result['disaster_type']}")
            print(f"Source: {result['source']}")
            print(f"Content Preview: {result['content'][:300]}...")
            print("-" * 80)
