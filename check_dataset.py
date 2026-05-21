"""Check dataset for similar entries"""
import json

# Load dataset
data = []
with open('dataset/kannada_disaster_dataset.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        data.append(json.loads(line))

print(f"Total entries: {len(data)}")

# Check food-related entries
food_related = [d for d in data if 'ಆಹಾರ' in d.get('text', '')]
print(f"\nFood related entries: {len(food_related)}")
print("\nFirst 15 food-related entries:")
for i, d in enumerate(food_related[:15], 1):
    print(f"{i}. {d['text']}")

# Check earthquake entries
earthquake = [d for d in data if 'ಭೂಕಂಪ' in d.get('disaster_type', '')]
print(f"\n\nEarthquake entries: {len(earthquake)}")
print("\nFirst 10 earthquake entries:")
for i, d in enumerate(earthquake[:10], 1):
    print(f"{i}. {d['text']}")
