import os
import numpy as np
import faiss
import pickle

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

EMBEDDINGS_FILE = os.path.join(ROOT_DIR, "chunk_embeddings.npy")
METADATA_FILE = os.path.join(ROOT_DIR, "chunk_metadata.pkl")

FAISS_INDEX_FILE = os.path.join(ROOT_DIR, "faiss_index.bin")
FAISS_METADATA_FILE = os.path.join(ROOT_DIR, "faiss_metadata.pkl")


def build_faiss_index():
    print("Loading embeddings...")
    embeddings = np.load(EMBEDDINGS_FILE)

    print(f"Embedding shape: {embeddings.shape}")

    dimension = embeddings.shape[1]

    print("Creating FAISS index...")
    index = faiss.IndexFlatL2(dimension)

    index.add(embeddings)

    print(f"Total vectors indexed: {index.ntotal}")

    print("Saving FAISS index...")
    faiss.write_index(index, FAISS_INDEX_FILE)

    print("Saving metadata...")
    with open(METADATA_FILE, "rb") as f:
        metadata = pickle.load(f)

    with open(FAISS_METADATA_FILE, "wb") as f:
        pickle.dump(metadata, f)

    print("FAISS index built and saved.")


if __name__ == "__main__":
    build_faiss_index()
