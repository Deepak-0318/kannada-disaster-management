"""
SPEC-05 Verification: Test confidence scoring and safe fallbacks
"""

from chatbot import retrieve_context, ask_bot, CONFIDENCE_THRESHOLD

print("\n" + "="*70)
print("SPEC-05 CONFIDENCE SCORING TEST")
print("="*70)

# Test cases: (query, expected_confidence_level, description)
test_cases = [
    # High confidence queries (disaster-related)
    ("ಪ್ರವಾಹ ಸಮಯದಲ್ಲಿ ಏನು ಮಾಡಬೇಕು?", "high", "Flood safety query"),
    ("ಭೂಕಂಪ ಬಂದಾಗ ಎಲ್ಲಿ ಹೋಗಬೇಕು?", "high", "Earthquake shelter query"),
    ("ಬೆಂಕಿ ಅಪಘಾತದಲ್ಲಿ ಮೊದಲು ಏನು ಮಾಡಬೇಕು?", "high", "Fire emergency query"),
    
    # Low confidence queries (out of domain)
    ("ಅಂಗಡಿಯಲ್ಲಿ ಏನು ಖರೀದಿಸಬೇಕು?", "low", "Shopping query (out of domain)"),
    ("ಇಂದು ಹವಾಮಾನ ಹೇಗಿದೆ?", "low", "Weather query (out of domain)"),
    ("ಕ್ರಿಕೆಟ್ ಪಂದ್ಯದ ಫಲಿತಾಂಶ ಏನು?", "low", "Sports query (out of domain)"),
]

print(f"\n📊 Confidence Threshold: {CONFIDENCE_THRESHOLD}")
print("\n" + "="*70)

for query, expected, description in test_cases:
    print(f"\n🔍 Test: {description}")
    print(f"   Query: {query}")
    print("-" * 70)
    
    # Get context and confidence
    context, confidence = retrieve_context(query, top_k=5)
    
    # Determine if above threshold
    is_confident = confidence >= CONFIDENCE_THRESHOLD
    confidence_level = "high" if is_confident else "low"
    
    # Check if matches expected
    matches = (confidence_level == expected)
    status = "✅ PASS" if matches else "❌ FAIL"
    
    print(f"   Confidence Score: {confidence:.4f}")
    print(f"   Above Threshold:  {is_confident}")
    print(f"   Expected:         {expected}")
    print(f"   Got:              {confidence_level}")
    print(f"   Status:           {status}")
    
    # Test full pipeline with fallback
    print(f"\n   Testing full pipeline...")
    response = ask_bot(query, emergency_mode=False)
    
    # Check if fallback was triggered
    is_fallback = "ಕ್ಷಮಿಸಿ" in response or "ಡೇಟಾಬೇಸ್" in response
    
    if not is_confident and is_fallback:
        print(f"   ✅ Safe fallback triggered correctly")
    elif is_confident and not is_fallback:
        print(f"   ✅ Normal response generated")
    else:
        print(f"   ⚠️  Unexpected behavior")
    
    print()

print("="*70)
print("✅ Confidence scoring test completed!")
print("="*70)
print("\n💡 Key Insights:")
print("   - High confidence: Disaster-related queries")
print("   - Low confidence: Out-of-domain queries trigger safe fallbacks")
print("   - Threshold prevents hallucinations on unknown topics")
print()
