"""
SPEC-05 Verification: Test caching performance
"""

import time
from chatbot import ask_bot

print("\n" + "="*70)
print("SPEC-05 CACHING PERFORMANCE TEST")
print("="*70)

test_queries = [
    "ಪ್ರವಾಹ ಸಮಯದಲ್ಲಿ ಏನು ಮಾಡಬೇಕು?",
    "ಭೂಕಂಪ ಬಂದಾಗ ಎಲ್ಲಿ ಹೋಗಬೇಕು?",
    "ಬೆಂಕಿ ಅಪಘಾತದಲ್ಲಿ ಮೊದಲು ಏನು ಮಾಡಬೇಕು?",
]

print("\n📊 Testing Cache Performance:\n")

for i, query in enumerate(test_queries, 1):
    print(f"Test {i}: {query[:40]}...")
    print("-" * 70)
    
    # First call (cache miss)
    start = time.time()
    response1 = ask_bot(query, emergency_mode=False)
    time1 = (time.time() - start) * 1000
    
    # Second call (cache hit)
    start = time.time()
    response2 = ask_bot(query, emergency_mode=False)
    time2 = (time.time() - start) * 1000
    
    # Third call (cache hit)
    start = time.time()
    response3 = ask_bot(query, emergency_mode=False)
    time3 = (time.time() - start) * 1000
    
    speedup = time1 / time2 if time2 > 0 else 0
    
    print(f"  1st call (cache miss):  {time1:7.2f}ms")
    print(f"  2nd call (cache hit):   {time2:7.2f}ms")
    print(f"  3rd call (cache hit):   {time3:7.2f}ms")
    print(f"  Speedup:                {speedup:.1f}x")
    print(f"  Latency reduction:      {time1 - time2:.2f}ms ({(1 - time2/time1)*100:.1f}%)")
    print()

print("="*70)
print("✅ Cache performance test completed!")
print("="*70)
print("\n💡 Expected Results:")
print("   - 1st call: 1500-2500ms (full pipeline)")
print("   - 2nd call: <1ms (cache hit)")
print("   - Speedup: 1000-2000x")
print()
