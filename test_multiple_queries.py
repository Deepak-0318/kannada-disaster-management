"""Test multiple queries to verify deduplication"""
from chatbot import ask_bot

queries = [
    "ಭೂಕಂಪ ನಂತರ ಆಹಾರ ಸಂಗ್ರಹಣೆ ಹೇಗೆ?",
    "ಪ್ರವಾಹ ಸಮಯದಲ್ಲಿ ಏನು ಮಾಡಬೇಕು?",
    "ಬೆಂಕಿ ಅಪಘಾತ ಸಮಯದಲ್ಲಿ ಏನು ಮಾಡಬೇಕು?",
]

print("\n" + "="*70)
print("Testing Multiple Queries with Deduplication")
print("="*70)

for i, query in enumerate(queries, 1):
    print(f"\n[Query {i}] {query}")
    print("-" * 70)
    
    try:
        response = ask_bot(query)
        print(response)
        
        # Check uniqueness
        lines = [line.strip() for line in response.strip().split('\n') if line.strip()]
        unique_lines = set(line for line in lines)
        
        if len(unique_lines) == len(lines):
            print(f"✅ All {len(lines)} results are unique")
        else:
            print(f"⚠️ Duplicates found: {len(lines)} total, {len(unique_lines)} unique")
            
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "="*70)
