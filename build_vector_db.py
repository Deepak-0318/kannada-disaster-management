"""
SPEC-01: Vector Database Builder with Multilingual Indic Embeddings

This script builds a FAISS vector database from Kannada disaster management datasets.
It properly maps different dataset schemas and uses multilingual-e5-small embeddings
optimized for Indic languages.

Features:
- Dual dataset schema support (instruction-output & disaster-type-category-text)
- Proper E5 model prefix formatting (passage: for indexing)
- L2-normalized embeddings for cosine similarity search
- Comprehensive logging and validation

Usage:
    python build_vector_db.py

Outputs:
    - disaster_index.faiss: FAISS vector index
    - disaster_metadata.json: Question-answer metadata
"""

import json
import faiss
import numpy as np
import os
from sentence_transformers import SentenceTransformer
from datetime import datetime

# =========================
# CONFIGURATION
# =========================
EMBEDDING_MODEL = "intfloat/multilingual-e5-small"
DATASET_PATHS = [
    "dataset/kannada_disaster_7000.jsonl",
    "dataset/kannada_disaster_dataset.jsonl"
]
OUTPUT_INDEX = "disaster_index.faiss"
OUTPUT_METADATA = "disaster_metadata.json"

# =========================
# LOAD EMBEDDING MODEL
# =========================
print(f"[{datetime.now().strftime('%H:%M:%S')}] Loading embedding model: {EMBEDDING_MODEL}")
model = SentenceTransformer(EMBEDDING_MODEL)
print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Model loaded (dimension: {model.get_sentence_embedding_dimension()})")

# =========================
# DATA LOADING
# =========================
data = []
metadata = []

def load_jsonl(path):
    """Load JSONL file and return list of JSON objects"""
    if not os.path.exists(path):
        print(f"⚠️  Warning: {path} not found, skipping...")
        return []
    
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]

print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Loading datasets...")

# Load all datasets
all_samples = []
for path in DATASET_PATHS:
    samples = load_jsonl(path)
    all_samples.extend(samples)
    print(f"  ✓ Loaded {len(samples)} samples from {path}")

print(f"[{datetime.now().strftime('%H:%M:%S')}] Total samples loaded: {len(all_samples)}")

# =========================
# SCHEMA MAPPING & PROCESSING
# =========================
print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Processing and mapping schemas...")

skipped_count = 0
dataset1_count = 0
dataset2_count = 0

for item in all_samples:
    question = None
    answer = None
    
    # Dataset 1 schema: instruction-output format
    if "instruction" in item:
        question = item.get("instruction", "").strip()
        answer = item.get("output", "").strip()
        dataset1_count += 1
    
    # Dataset 2 schema: disaster-type-category-text format
    elif "text" in item:
        disaster_type = item.get("disaster_type", "").strip()
        category = item.get("category", "").strip()
        answer = item.get("text", "").strip()
        
        # Construct semantic question in Kannada
        if category == "do":
            category_text = "ಮಾಡಬೇಕು"
        elif category == "dont":
            category_text = "ಮಾಡಬಾರದು"
        else:
            category_text = "ಮಾಡಬೇಕು"  # Default fallback
        
        question = f"{disaster_type} ಸಮಯದಲ್ಲಿ ಏನು {category_text}?"
        dataset2_count += 1
    
    else:
        skipped_count += 1
        continue

    # Validate question and answer
    if not question or not answer:
        skipped_count += 1
        continue

    # Format with E5 passage prefix for optimal retrieval
    text = f"passage: {question} {answer}"

    data.append(text)
    metadata.append({
        "question": question,
        "answer": answer
    })

print(f"  ✓ Dataset 1 (instruction-output): {dataset1_count} samples")
print(f"  ✓ Dataset 2 (disaster-type-text): {dataset2_count} samples")
print(f"  ✓ Valid samples to index: {len(data)}")
print(f"  ⚠️  Skipped samples: {skipped_count}")

# =========================
# EMBEDDING GENERATION
# =========================
print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Generating embeddings...")
print("  (This may take 30-60 seconds on CPU for ~8000 samples)")

embeddings = model.encode(
    data,
    normalize_embeddings=True,  # L2 normalization for cosine similarity
    show_progress_bar=True,
    batch_size=32
)
embeddings = np.array(embeddings).astype("float32")

print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Embeddings generated: shape {embeddings.shape}")

# =========================
# FAISS INDEX CONSTRUCTION
# =========================
print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Building FAISS index...")

dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)  # L2 distance with normalized vectors = cosine similarity
index.add(embeddings)

print(f"  ✓ Index type: IndexFlatL2 (exact search)")
print(f"  ✓ Dimension: {dimension}")
print(f"  ✓ Total vectors: {index.ntotal}")

# =========================
# SAVE OUTPUTS
# =========================
print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Saving outputs...")

faiss.write_index(index, OUTPUT_INDEX)
print(f"  ✓ FAISS index saved: {OUTPUT_INDEX}")

with open(OUTPUT_METADATA, "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)
print(f"  ✓ Metadata saved: {OUTPUT_METADATA}")

# =========================
# VERIFICATION
# =========================
print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Verification:")
print(f"  ✓ Index file size: {os.path.getsize(OUTPUT_INDEX) / 1024 / 1024:.2f} MB")
print(f"  ✓ Metadata file size: {os.path.getsize(OUTPUT_METADATA) / 1024 / 1024:.2f} MB")

# Sample metadata check
if len(metadata) > 0:
    print(f"\n  Sample entry:")
    print(f"    Q: {metadata[0]['question'][:60]}...")
    print(f"    A: {metadata[0]['answer'][:60]}...")

print(f"\n{'='*60}")
print(f"✅ Vector DB rebuilt successfully!")
print(f"   Total entries: {len(data)}")
print(f"   Model: {EMBEDDING_MODEL}")
print(f"   Dimension: {dimension}")
print(f"{'='*60}\n")
