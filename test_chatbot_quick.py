"""Quick test of chatbot functionality"""
from chatbot import ask_bot

print("\n" + "="*60)
print("Testing Chatbot with Top 3 Results")
print("="*60 + "\n")

# Test query
query = "ಪ್ರವಾಹ ಸಮಯದಲ್ಲಿ ಏನು ಮಾಡಬೇಕು?"
print(f"Query: {query}\n")

try:
    response = ask_bot(query)
    print("Response:")
    print(response)
    print("\n" + "="*60)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
