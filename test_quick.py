"""
Quick test to verify the chatbot is working
"""

from chatbot import ask_bot

print("=" * 60)
print("Testing Kannada Disaster Management Chatbot")
print("=" * 60)
print()

# Test query
query = "ಪ್ರವಾಹ ಸಮಯದಲ್ಲಿ ಏನು ಮಾಡಬೇಕು?"
print(f"Query: {query}")
print()

# Get response
print("Getting response...")
response = ask_bot(query, emergency_mode=False)

print()
print("Response:")
print("-" * 60)
print(response)
print("-" * 60)
print()
print("✅ Chatbot is working!")
