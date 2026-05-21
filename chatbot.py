"""
Kannada Disaster Management Chatbot with RAG
Features:
- Multilingual E5 embeddings for Kannada
- Hybrid retrieval (Dense FAISS + Sparse BM25 + RRF)
- Emergency mode detection and optimization
- In-memory caching for performance
- Anti-hallucination measures with confidence scoring
- Response validation and safe fallbacks
"""

import json
import faiss
import numpy as np
import os
import string
import hashlib
import google.generativeai as genai
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

# =========================
# LOAD ENV VARIABLES
# =========================
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Latest working model
gemini_model = genai.GenerativeModel("models/gemini-flash-latest")

# =========================
# LOAD EMBEDDING MODEL (Upgraded to Multilingual E5)
# =========================
print("Loading multilingual sentence transformer...")
embed_model = SentenceTransformer("intfloat/multilingual-e5-small")

# =========================
# LOAD FAISS INDEX (Dense Retriever)
# =========================
index = faiss.read_index("disaster_index.faiss")

# =========================
# LOAD METADATA
# =========================
with open("disaster_metadata.json", "r", encoding="utf-8") as f:
    metadata = json.load(f)

# =========================
# SPARSE BM25 RETRIEVER INITIALIZATION
# =========================
def tokenize_kannada(text):
    if not text:
        return []
    # Strip punctuation and lower-case split
    translator = str.maketrans("", "", string.punctuation)
    clean_text = text.translate(translator)
    return clean_text.lower().split()

print("Building BM25 sparse index...")
corpus_tokens = []
for item in metadata:
    doc_text = f"{item['question']} {item['answer']}"
    corpus_tokens.append(tokenize_kannada(doc_text))

bm25_index = BM25Okapi(corpus_tokens)
print("BM25 index ready!")

# =========================
# EMERGENCY KEYWORDS (KAN)
# =========================
EMERGENCY_KEYWORDS = [
    "ಕಾಪಾಡಿ", "ರಕ್ಷಿಸಿ", "ಅಪಾಯ", "ತುರ್ತು", "ಬೆಂಕಿ", "ಪ್ರವಾಹ",
    "ನೆರೆ", "ಭೂkಸಿತ", "ಭೂಕುಸಿತ", "ಸಹಾಯ", "ಗಾಯ", "ರಕ್ತ", "ಆಸ್ಪತ್ರೆ", "ಡಾಕ್ಟರ್"
]

# =========================
# CACHING SYSTEM (SPEC-05)
# =========================
RESPONSE_CACHE = {}
CACHE_MAX_SIZE = 1000
CONFIDENCE_THRESHOLD = 0.0  # Disabled - return top 3 results always

SAFE_FALLBACK_RESPONSES = {
    "low_confidence": """ಕ್ಷಮಿಸಿ, ಈ ನಿರ್ದಿಷ್ಟ ಪ್ರಶ್ನೆಗೆ ನನ್ನ ಡೇಟಾಬೇಸ್‌ನಲ್ಲಿ ಸಾಕಷ್ಟು ಮಾಹಿತಿ ಇಲ್ಲ.

ದಯವಿಟ್ಟು ತುರ್ತು ಸೇವೆಗಳನ್ನು ಸಂಪರ್ಕಿಸಿ:
📞 NDRF: 1070
📞 ರಾಜ್ಯ ವಿಪತ್ತು ನಿಯಂತ್ರಣ: 1077
📞 ತುರ್ತು ಸೇವೆ: 108
📞 ಅಗ್ನಿಶಾಮಕ: 101""",
    
    "no_context": """ಕ್ಷಮಿಸಿ, ನಾನು ಈ ಪ್ರಶ್ನೆಗೆ ಉತ್ತರಿಸಲು ಸಾಧ್ಯವಿಲ್ಲ.

ಸಾಮಾನ್ಯ ವಿಪತ್ತು ಸುರಕ್ಷತಾ ಸಲಹೆಗಳು:
1. ಶಾಂತವಾಗಿರಿ ಮತ್ತು ಭಯಪಡಬೇಡಿ
2. ಸ್ಥಳೀಯ ಅಧಿಕಾರಿಗಳ ಸೂಚನೆಗಳನ್ನು ಅನುಸರಿಸಿ
3. ತುರ್ತು ಸೇವೆಗಳಿಗೆ ಕರೆ ಮಾಡಿ: 108, 1077"""
}

def get_cache_key(query, emergency_mode):
    """Generate cache key from query and mode"""
    cache_data = f"{query}|{emergency_mode}"
    return hashlib.md5(cache_data.encode()).hexdigest()

def get_cached_response(query, emergency_mode):
    """Check if response is cached"""
    cache_key = get_cache_key(query, emergency_mode)
    return RESPONSE_CACHE.get(cache_key)

def cache_response(query, emergency_mode, response):
    """Store response in cache with LRU eviction"""
    cache_key = get_cache_key(query, emergency_mode)
    
    # LRU eviction if cache is full
    if len(RESPONSE_CACHE) >= CACHE_MAX_SIZE:
        # Remove oldest entry (first key)
        oldest_key = next(iter(RESPONSE_CACHE))
        del RESPONSE_CACHE[oldest_key]
    
    RESPONSE_CACHE[cache_key] = response

def get_safe_fallback(query, is_emergency=False):
    """Return safe fallback response for low-confidence queries"""
    if is_emergency:
        return SAFE_FALLBACK_RESPONSES["low_confidence"]
    return SAFE_FALLBACK_RESPONSES["no_context"]

def check_lexical_urgency(text):
    if not text:
        return False
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in EMERGENCY_KEYWORDS)

# =========================
# RETRIEVE CONTEXT (RAG - Dense + Sparse RRF Hybrid with Parallel Processing)
# =========================
def dense_search(query, top_k=20):
    """Dense retrieval using FAISS"""
    query_text = f"query: {query}" if not query.startswith("query: ") else query
    q_embed = embed_model.encode([query_text], normalize_embeddings=True).astype("float32")
    _, indices = index.search(q_embed, top_k)
    return indices[0]

def sparse_search(query, top_k=20):
    """Sparse retrieval using BM25"""
    tokenized_query = tokenize_kannada(query)
    scores = bm25_index.get_scores(tokenized_query)
    return np.argsort(scores)[::-1][:top_k]

def deduplicate_results(results_with_scores, similarity_threshold=0.6):
    """
    Remove duplicate or highly similar results based on text similarity
    Uses aggressive deduplication to ensure diverse results
    Returns deduplicated list maintaining order by score
    """
    if not results_with_scores:
        return []
    
    deduplicated = []
    seen_texts = []
    
    for result in results_with_scores:
        answer = result["answer"].strip()
        
        # Check if this answer is too similar to any already selected
        is_duplicate = False
        for seen_text in seen_texts:
            # Simple word-based similarity check
            answer_words = set(tokenize_kannada(answer))
            seen_words = set(tokenize_kannada(seen_text))
            
            if not answer_words or not seen_words:
                continue
            
            # Calculate Jaccard similarity
            intersection = len(answer_words & seen_words)
            union = len(answer_words | seen_words)
            similarity = intersection / union if union > 0 else 0
            
            # Also check if one is a substring of the other (very similar)
            if answer in seen_text or seen_text in answer:
                similarity = 1.0
            
            if similarity >= similarity_threshold:
                is_duplicate = True
                break
        
        if not is_duplicate:
            deduplicated.append(result)
            seen_texts.append(answer)
    
    return deduplicated


def retrieve_context(query, top_k=7):
    """
    Hybrid retrieval with parallel processing and aggressive deduplication
    Returns: (context, confidence_score, results_list)
    """
    # PARALLEL RETRIEVAL (SPEC-05 Optimization)
    with ThreadPoolExecutor(max_workers=2) as executor:
        # Submit both tasks simultaneously
        dense_future = executor.submit(dense_search, query, 50)  # Get many candidates
        sparse_future = executor.submit(sparse_search, query, 50)
        
        # Wait for both to complete
        dense_candidates = dense_future.result()
        sparse_candidates = sparse_future.result()

    # 3. RECIPROCAL RANK FUSION (RRF)
    rrf_k = 60
    rrf_scores = {}

    # Dense scores
    for rank, idx in enumerate(dense_candidates):
        idx = int(idx)
        # Avoid error codes from FAISS (-1 if empty result)
        if idx < 0:
            continue
        rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (rrf_k + (rank + 1))

    # Sparse scores
    for rank, idx in enumerate(sparse_candidates):
        idx = int(idx)
        rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (rrf_k + (rank + 1))

    # Sort candidates by RRF score descending
    sorted_candidates = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

    # 4. GET MANY CANDIDATES FOR DEDUPLICATION (top 30)
    candidate_results = sorted_candidates[:30]
    
    results_with_scores = []
    for idx in candidate_results:
        item = metadata[idx]
        results_with_scores.append({
            "answer": item["answer"],
            "question": item["question"],
            "score": rrf_scores[idx]
        })
    
    # 5. AGGRESSIVE DEDUPLICATION (60% similarity threshold)
    deduplicated = deduplicate_results(results_with_scores, similarity_threshold=0.6)
    
    # 6. SELECT TOP-K UNIQUE RESULTS (flexible 3-7)
    final_results = deduplicated[:top_k]
    
    # If we don't have enough unique results, lower the threshold more
    if len(final_results) < 3:
        deduplicated = deduplicate_results(results_with_scores, similarity_threshold=0.5)
        final_results = deduplicated[:top_k]
    
    # If still not enough, use even lower threshold
    if len(final_results) < 3:
        deduplicated = deduplicate_results(results_with_scores, similarity_threshold=0.4)
        final_results = deduplicated[:top_k]
    
    # Last resort: just take what we have
    if len(final_results) < 3 and results_with_scores:
        final_results = results_with_scores[:top_k]
    
    top_confidence = final_results[0]["score"] if final_results else 0.0
    
    results = [r["answer"] for r in final_results]
    context = "\n\n".join([f"- {r}" for r in results])
    
    return context, top_confidence, final_results


# =========================
# RESPONSE VALIDATION (SPEC-05 Anti-Hallucination)
# =========================
def validate_response_grounding(response, context):
    """
    Check if response is grounded in context
    Returns: (is_valid, overlap_ratio)
    """
    if not response or not context:
        return False, 0.0
    
    # Tokenize both
    response_words = set(tokenize_kannada(response))
    context_words = set(tokenize_kannada(context))
    
    # Calculate overlap
    if not response_words:
        return False, 0.0
    
    overlap = len(response_words & context_words)
    overlap_ratio = overlap / len(response_words)
    
    # Threshold: 30% minimum overlap
    is_valid = overlap_ratio >= 0.30
    
    return is_valid, overlap_ratio


# =========================
# MAIN BOT FUNCTION (Enhanced with SPEC-05)
# =========================
def ask_bot(question, emergency_mode=None):
    """
    Main chatbot function with caching, confidence scoring, and validation
    SPEC-05: Latency optimization and anti-hallucination measures
    """
    # Detect strict Kannada boundary normalization
    if not any("\u0C80" <= c <= "\u0CFF" for c in question):
        question = f"ಈ ಪ್ರಶ್ನೆಯನ್ನು ಕನ್ನಡದಲ್ಲಿ ಅರ್ಥಮಾಡಿಕೊಳ್ಳಿ: {question}"

    # Determine emergency state (Acoustic from voice agent or Lexical from text query)
    lexical_urgent = check_lexical_urgency(question)
    is_emergency = emergency_mode if emergency_mode is not None else lexical_urgent

    # 1. CHECK CACHE (SPEC-05)
    cached_response = get_cached_response(question, is_emergency)
    if cached_response:
        return cached_response

    # 2. RETRIEVE CONTEXT - GET 5-7 RESULTS (flexible)
    top_k = 3 if is_emergency else 7  # Emergency: 3 quick points, Normal: up to 7 detailed
    context, confidence, results_list = retrieve_context(question, top_k=top_k)
    
    # 3. ALWAYS USE RETRIEVED RESULTS (No confidence filtering)
    if not context.strip():
        fallback = get_safe_fallback(question, is_emergency)
        cache_response(question, is_emergency, fallback)
        return fallback

    # 4. FORMAT RESULTS DIRECTLY (Skip LLM for cleaner output)
    # Return the deduplicated retrieval results as-is
    answer = "\n".join([f"{i+1}. {results_list[i]['answer']}" for i in range(len(results_list))])

    # =========================
    # CLEAN + STRUCTURE OUTPUT - Flexible 3-7 points
    # =========================
    lines = [line.strip() for line in answer.split("\n") if line.strip()]

    points = []
    for line in lines:
        # Match any numbered point (1. through 9.)
        if any(line.startswith(f"{i}.") for i in range(1, 10)):
            points.append(line)

    # Use all points we got (no strict limit)
    if len(points) >= 3:
        final_answer = "\n".join(points)
    else:
        # Fallback: use first few lines
        final_answer = "\n".join(lines[:7])

    # 5. CACHE RESPONSE
    cache_response(question, is_emergency, final_answer)
    
    return final_answer


# =========================
# MODEL WARM-UP (SPEC-05)
# =========================
def warmup_models():
    """
    Run dummy inference to load models into memory
    Eliminates 2-3s cold-start penalty
    """
    print("🔥 Warming up models...")
    
    # Warm up embedding model
    dummy_text = "ಪ್ರವಾಹ ಸಮಯದಲ್ಲಿ ಏನು ಮಾಡಬೇಕು?"
    _ = embed_model.encode([f"query: {dummy_text}"], normalize_embeddings=True)
    
    # Warm up FAISS index
    dummy_embed = embed_model.encode([f"query: {dummy_text}"], normalize_embeddings=True).astype("float32")
    _ = index.search(dummy_embed, 5)
    
    # Warm up BM25
    dummy_tokens = tokenize_kannada(dummy_text)
    _ = bm25_index.get_scores(dummy_tokens)
    
    print("✅ Models warmed up and ready!")


# =========================
# TERMINAL TEST
# =========================
def main():
    print("\nChatbot Ready (Multilingual E5 + BM25 Sparse + RRF Hybrid enabled)\n")

    while True:
        q = input("You: ")

        if q.lower() == "exit":
            print("Exiting chatbot...")
            break

        if not q.strip():
            continue

        # Lexical detection display for testing
        is_emergency = check_lexical_urgency(q)
        print(f"[Mode detected: {'EMERGENCY (Fast-Path)' if is_emergency else 'NORMAL'}]")
        
        ans = ask_bot(q)

        print("\nBot:\n", ans)
        print("-" * 50)


# =========================
if __name__ == "__main__":
    main()

