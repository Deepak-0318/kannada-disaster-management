import time
import numpy as np
import chatbot  # Import our upgraded chatbot module

# ==========================================
# EVALUATION TEST SUITE DEFINITION
# ==========================================
# We define a series of test queries across 3 categories: Standard Kannada, English, and Code-Mixed (Kanglish).
# Each query is mapped to a unique substring in the ground-truth answer.
test_cases = [
    # --- Category 1: Standard Kannada ---
    {
        "category": "Standard Kannada",
        "query": "ನೆರೆ ನೀರಿನಲ್ಲಿ ನಡೆಯುವಾಗ ಕೋಲನ್ನು ಬಳಸಬೇಕೆ?",
        "keyword": "ಕೋಲನ್ನು ಬಳಸಬೇಕು"
    },
    {
        "category": "Standard Kannada",
        "query": "ಭೂಕಂಪನದ ಸಮಯದಲ್ಲಿ ಲಿಫ್ಟ್ ಬಳಸಬಹುದೇ?",
        "keyword": "ಲಿಫ್ಟ್ ಬಳಸಬೇಡಿ"
    },
    {
        "category": "Standard Kannada",
        "query": "ಮಿಂಚು ಹೊಡೆಯುವಾಗ ಮರದ ಕೆಳಗೆ ನಿಲ್ಲುವುದು ಸುರಕ್ಷಿತವೇ?",
        "keyword": "ಮರದ ಕೆಳಗೆ ನಿಲ್ಲಬೇಡಿ"
    },
    {
        "category": "Standard Kannada",
        "query": "ಮೊಬೈಲ್ ಫೋನ್‌ಗಳನ್ನು ನೆರೆಯಿಂದ ಹೇಗೆ ರಕ್ಷಿಸಬೇಕು?",
        "keyword": "ವಾಟರ್‌ಪ್ರೂಫ್ ಬ್ಯಾಗ್‌ನಲ್ಲಿ ಇರಿಸಬೇಕು"
    },
    {
        "category": "Standard Kannada",
        "query": "ಸಾಂಕ್ರಾಮಿಕ ಸಮಯದಲ್ಲಿ ಕೈಗಳನ್ನು ತೊಳೆಯುವುದು ಏಕೆ ಮುಖ್ಯ?",
        "keyword": "ಕೈಗಳನ್ನು часто ತೊಳೆಯಿರಿ"
    },

    # --- Category 2: English ---
    {
        "category": "English",
        "query": "Should I use a stick when walking in flood water?",
        "keyword": "ಕೋಲನ್ನು ಬಳಸಬೇಕು"
    },
    {
        "category": "English",
        "query": "Is it safe to use elevator during earthquake?",
        "keyword": "ಲಿಫ್ಟ್ ಬಳಸಬೇಡಿ"
    },
    {
        "category": "English",
        "query": "Can I stand under a tree during lightning?",
        "keyword": "ಮರದ ಕೆಳಗೆ ನಿಲ್ಲಬೇಡಿ"
    },
    {
        "category": "English",
        "query": "How to protect mobile phones from flood water?",
        "keyword": "ವಾಟರ್‌ಪ್ರೂಫ್ ಬ್ಯಾಗ್‌ನಲ್ಲಿ ಇರಿಸಬೇಕು"
    },
    {
        "category": "English",
        "query": "What precautions should be taken after landslide?",
        "keyword": "ಮಳೆ ನೀರಿನ ಹರಿವಿನಿಂದ ದೂರವಿರಿ"
    },

    # --- Category 3: Code-Mixed / Kanglish ---
    {
        "category": "Code-Mixed",
        "query": "flood water nalli nadeyuvaga kolu use madabek?",
        "keyword": "ಕೋಲನ್ನು ಬಳಸಬೇಕು"
    },
    {
        "category": "Code-Mixed",
        "query": "earthquake bandaga lift use madbahuda?",
        "keyword": "ಲಿಫ್ಟ್ ಬಳಸಬೇಡಿ"
    },
    {
        "category": "Code-Mixed",
        "query": "lightning time nalli mara kelage nillbahuda?",
        "keyword": "ಮರದ ಕೆಳಗೆ ನಿಲ್ಲಬೇಡಿ"
    },
    {
        "category": "Code-Mixed",
        "query": "mobile phone neeru beelada hage yelli idabeku?",
        "keyword": "ವಾಟರ್‌ಪ್ರೂಫ್ ಬ್ಯಾಗ್‌ನಲ್ಲಿ ಇರಿಸಬೇಕು"
    },
    {
        "category": "Code-Mixed",
        "query": "corona time nalli yenu precautions togobeku?",
        "keyword": "ಮುಖಕವಚ ಧರಿಸಿ"
    }
]

# Map queries to absolute metadata indexes dynamically by finding the ground-truth answer
print("Mapping evaluation queries to ground-truth documents...")
valid_test_suite = []
for tc in test_cases:
    gt_indices = []
    for idx, item in enumerate(chatbot.metadata):
        if tc["keyword"] in item["answer"] or tc["keyword"] in item["question"]:
            gt_indices.append(idx)
            
    if gt_indices:
        # Use the first matching document as the primary ground truth
        tc["gt_index"] = gt_indices[0]
        tc["all_gt_indices"] = set(gt_indices)
        valid_test_suite.append(tc)
    else:
        print(f"WARNING: Ground truth keyword '{tc['keyword']}' not found in metadata. Skipping.")

print(f"Active Evaluation Suite built with {len(valid_test_suite)} / {len(test_cases)} cases.\n")

# ==========================================
# RETRIEVERS TO EVALUATE
# ==========================================
def evaluate_dense(query, top_k=5):
    # Standard multilingual E5 dense lookup
    if not query.startswith("query: "):
        query_text = f"query: {query}"
    else:
        query_text = query
    q_embed = chatbot.embed_model.encode([query_text], normalize_embeddings=True).astype("float32")
    D, I = chatbot.index.search(q_embed, top_k)
    return [int(idx) for idx in I[0] if idx >= 0]

def evaluate_sparse(query, top_k=5):
    # Standard BM25 lookup
    tokenized_query = chatbot.tokenize_kannada(query)
    scores = chatbot.bm25_index.get_scores(tokenized_query)
    return [int(idx) for idx in np.argsort(scores)[::-1][:top_k]]

def evaluate_hybrid(query, top_k=5):
    # Our RRF Hybrid search pipeline
    if not query.startswith("query: "):
        query_text = f"query: {query}"
    else:
        query_text = query
    
    # Dense search (top 20)
    q_embed = chatbot.embed_model.encode([query_text], normalize_embeddings=True).astype("float32")
    Dense_D, Dense_I = chatbot.index.search(q_embed, 20)
    dense_candidates = Dense_I[0]
    
    # Sparse search (top 20)
    tokenized_query = chatbot.tokenize_kannada(query)
    sparse_scores = chatbot.bm25_index.get_scores(tokenized_query)
    sparse_candidates = np.argsort(sparse_scores)[::-1][:20]
    
    # RRF fusion
    rrf_k = 60
    rrf_scores = {}
    for rank, idx in enumerate(dense_candidates):
        idx = int(idx)
        if idx >= 0:
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (rrf_k + (rank + 1))
            
    for rank, idx in enumerate(sparse_candidates):
        idx = int(idx)
        rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (rrf_k + (rank + 1))
        
    sorted_candidates = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
    return sorted_candidates[:top_k]

# ==========================================
# RUN EVALUATION ENGINE
# ==========================================
retrievers = {
    "Dense (Multilingual-E5)": evaluate_dense,
    "Sparse (BM25)": evaluate_sparse,
    "Hybrid (E5 + BM25 + RRF)": evaluate_hybrid
}

results_summary = {}

for name, retriever_func in retrievers.items():
    print(f"Running evaluation for retriever: '{name}'...")
    hit_at_1 = []
    hit_at_5 = []
    mrr_at_5 = []
    latencies = []
    
    # Categorized metrics
    cat_metrics = {}
    
    for tc in valid_test_suite:
        cat = tc["category"]
        if cat not in cat_metrics:
            cat_metrics[cat] = {"hit_at_5": [], "mrr_at_5": []}
            
        start_time = time.perf_counter()
        retrieved_ids = retriever_func(tc["query"], top_k=5)
        elapsed = (time.perf_counter() - start_time) * 1000.0  # ms
        
        latencies.append(elapsed)
        
        # Calculate Hits
        is_hit_1 = len(retrieved_ids) >= 1 and retrieved_ids[0] in tc["all_gt_indices"]
        is_hit_5 = any(idx in tc["all_gt_indices"] for idx in retrieved_ids)
        
        hit_at_1.append(1.0 if is_hit_1 else 0.0)
        hit_at_5.append(1.0 if is_hit_5 else 0.0)
        cat_metrics[cat]["hit_at_5"].append(1.0 if is_hit_5 else 0.0)
        
        # Calculate MRR@5
        rr = 0.0
        for rank, idx in enumerate(retrieved_ids):
            if idx in tc["all_gt_indices"]:
                rr = 1.0 / (rank + 1)
                break
        mrr_at_5.append(rr)
        cat_metrics[cat]["mrr_at_5"].append(rr)
        
    results_summary[name] = {
        "hit_at_1": np.mean(hit_at_1),
        "hit_at_5": np.mean(hit_at_5),
        "mrr_at_5": np.mean(mrr_at_5),
        "avg_latency_ms": np.mean(latencies),
        "cat_breakdown": {cat: {"hit_at_5": np.mean(metrics["hit_at_5"]), "mrr_at_5": np.mean(metrics["mrr_at_5"])} 
                          for cat, metrics in cat_metrics.items()}
    }

# ==========================================
# EXPORT & DISPLAY RESULTS
# ==========================================
print("\n" + "="*80)
print("              KANNADA DISASTER RAG SYSTEM BENCHMARK REPORT")
print("="*80)
print(f"{'Retriever Configuration':<28} | {'Hit@1':<8} | {'Hit@5':<8} | {'MRR@5':<8} | {'Latency (ms)':<12}")
print("-"*80)
for name, metrics in results_summary.items():
    print(f"{name:<28} | {metrics['hit_at_1']:.4f}   | {metrics['hit_at_5']:.4f}   | {metrics['mrr_at_5']:.4f}   | {metrics['avg_latency_ms']:.2f} ms")
print("="*80)

print("\n" + "="*80)
print("              CATEGORY-WISE RETRIEVAL PERFORMANCE (Hit@5)")
print("="*80)
print(f"{'Retriever Configuration':<28} | {'Kannada Script':<15} | {'English Script':<15} | {'Code-Mixed':<15}")
print("-"*80)
for name, metrics in results_summary.items():
    cb = metrics["cat_breakdown"]
    kan_hit = cb.get("Standard Kannada", {}).get("hit_at_5", 0.0)
    eng_hit = cb.get("English", {}).get("hit_at_5", 0.0)
    mix_hit = cb.get("Code-Mixed", {}).get("hit_at_5", 0.0)
    print(f"{name:<28} | {kan_hit:.4f}         | {eng_hit:.4f}         | {mix_hit:.4f}")
print("="*80)

# LaTeX Table Generation
print("\n" + "% LaTeX Table for Academic Publication:")
print(r"\begin{table}[h]")
print(r"  \centering")
print(r"  \caption{Retrieval Performance of Kannada Disaster RAG Configurations}")
print(r"  \begin{tabular}{lcccc}")
print(r"    \hline")
print(r"    \textbf{Retriever Model} & \textbf{Hit@1} & \textbf{Hit@5} & \textbf{MRR@5} & \textbf{Latency (ms)} \\")
print(r"    \hline")
for name, metrics in results_summary.items():
    cleaned_name = name.replace("&", r"\&")
    print(f"    {cleaned_name:<28} & {metrics['hit_at_1']:.4f} & {metrics['hit_at_5']:.4f} & {metrics['mrr_at_5']:.4f} & {metrics['avg_latency_ms']:.2f} \\")
print(r"    \hline")
print(r"  \end{tabular}")
print(r"\end{table}")
print("="*80 + "\n")
