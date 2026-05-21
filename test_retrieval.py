"""
SPEC-01 Verification: Test retrieval quality with sample queries
"""

from chatbot import retrieve_context

# Test queries in Kannada
test_queries = [
    "ಪ್ರವಾಹ ಸಮಯದಲ್ಲಿ ಏನು ಮಾಡಬೇಕು?",
    "ಭೂಕಂಪ ಬಂದಾಗ ಎಲ್ಲಿ ಹೋಗಬೇಕು?",
    "ಬೆಂಕಿ ಅಪಘಾತದಲ್ಲಿ ಮೊದಲು ಏನು ಮಾಡಬೇಕು?",
    "ನೆರೆ ನೀರು ಬಂದಾಗ ಏನು ಮಾಡಬಾರದು?",
]

print("\n" + "="*70)
print("SPEC-01 RETRIEVAL QUALITY TEST")
print("="*70)

for i, query in enumerate(test_queries, 1):
    print(f"\n🔍 Test Query {i}: {query}")
    print("-" * 70)
    
    context = retrieve_context(query, top_k=3)
    
    # Split context into individual points
    points = context.split("\n\n")
    for j, point in enumerate(points, 1):
        print(f"  [{j}] {point.strip()}")
    
    print()

print("="*70)
print("✅ Retrieval test completed!")
print("="*70)
