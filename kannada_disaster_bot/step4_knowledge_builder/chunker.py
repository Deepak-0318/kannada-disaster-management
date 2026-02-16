import json
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_FILE = os.path.join(ROOT_DIR, "knowledge_base_updated.json")
OUTPUT_FILE = os.path.join(ROOT_DIR, "knowledge_chunks.json")

CHUNK_SIZE = 500
CHUNK_OVERLAP = 75


def chunk_documents():
    if not os.path.exists(INPUT_FILE):
        print("knowledge_base_updated.json not found.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        documents = json.load(f)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=75,
        separators=["\n\n", "\n", ".", " ", ""]
    )

    chunked_data = []
    chunk_id = 1
    seen_contents = set()

    for doc in documents:
        chunks = text_splitter.split_text(doc["content"])

        for chunk in chunks:
            cleaned_chunk = chunk.strip()

            # Skip very small chunks
            if len(cleaned_chunk) < 50:
                continue

            # Remove duplicates
            if cleaned_chunk in seen_contents:
                continue

            seen_contents.add(cleaned_chunk)

            chunked_data.append({
                "chunk_id": chunk_id,
                "doc_id": doc["doc_id"],
                "content": cleaned_chunk,
                "disaster_type": doc.get("disaster_type", "general"),
                "language": doc.get("language", "unknown"),
                "source": doc.get("source", "unknown")
            })
            chunk_id += 1

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        json.dump(chunked_data, out, ensure_ascii=False, indent=4)

    print(f"Clean chunking complete. Created {len(chunked_data)} unique chunks.")


if __name__ == "__main__":
    chunk_documents()
