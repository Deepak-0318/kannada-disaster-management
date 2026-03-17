import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from step5_embeddings.search_engine import SemanticSearchEngine

# -----------------------------
# Load Ambari Model
# -----------------------------
MODEL_NAME = "CognitiveLab/ambari-7b-instruct"

print("Loading Ambari model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    device_map="auto"
)

print("Ambari loaded.")

# -----------------------------
# Load Semantic Search
# -----------------------------
search_engine = SemanticSearchEngine()


# -----------------------------
# Context Builder
# -----------------------------
def build_context(chunks):
    context_text = ""
    for chunk in chunks:
        context_text += f"\nSource: {chunk['source']}\n"
        context_text += chunk["content"] + "\n"
    return context_text


# -----------------------------
# Generate RAG Response
# -----------------------------
def generate_response(user_query, top_k=5):

    retrieved_chunks = search_engine.search(user_query, top_k=top_k)

    if not retrieved_chunks:
        return "ಕ್ಷಮಿಸಿ, ಸಂಬಂಧಿತ ಮಾಹಿತಿ ದೊರಕಲಿಲ್ಲ."

    context = build_context(retrieved_chunks)

    prompt = f"""
You are a disaster management assistant.

Use ONLY the verified context below to answer the question.
If the answer is not in the context, say:
"I do not have enough verified information."

Context:
{context}

Question:
{user_query}

Answer:
"""

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=250,
            temperature=0.2,
            top_p=0.9
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    final_answer = response.split("Answer:")[-1].strip()

    return final_answer


# -----------------------------
# CLI Test
# -----------------------------
if __name__ == "__main__":
    while True:
        query = input("\nEnter your query (or type 'exit'): ")
        if query.lower() == "exit":
            break

        answer = generate_response(query)
        print("\nFinal Answer:\n")
        print(answer)
        print("-" * 80)
