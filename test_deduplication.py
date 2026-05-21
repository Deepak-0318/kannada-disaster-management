"""Test deduplication functionality"""
from chatbot import ask_bot

print("\n" + "="*60)
print("Testing Deduplication")
print("="*60 + "\n")

# Test query that was showing duplicates
query = "ಭೂಕಂಪ ನಂತರ ಆಹಾರ ಸಂಗ್ರಹಣೆ ಹೇಗೆ?"
print(f"Query: {query}\n")

try:
    response = ask_bot(query)
    print("Response:")
    print(response)
    print("\n" + "="*60)
    
    # Count unique lines
    lines = response.strip().split('\n')
    unique_lines = set(line.strip() for line in lines if line.strip())
    
    print(f"\nTotal lines: {len(lines)}")
    print(f"Unique lines: {len(unique_lines)}")
    
    if len(unique_lines) == len(lines):
        print("✅ All results are unique!")
    else:
        print("⚠️ Some duplicates found")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
