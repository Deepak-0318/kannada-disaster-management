import json

input_file = "dataset/kannada_disaster_7000.jsonl"
output_file = "dataset/formatted_dataset.jsonl"

formatted_data = []

with open(input_file, "r", encoding="utf-8") as f:
    for line in f:
        data = json.loads(line)

        instruction = data.get("instruction", "")
        input_text = data.get("input", "")
        output = data.get("output", "")

        # Combine instruction and input
        if input_text.strip() != "":
            question = instruction + "\n" + input_text
        else:
            question = instruction

        prompt = f"<s>[INST] You are a Kannada disaster management assistant.\n\n{question}\n\n[/INST]\n{output}</s>"

        formatted_data.append({"text": prompt})


with open(output_file, "w", encoding="utf-8") as f:
    for item in formatted_data:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print("Dataset formatting complete")
print("Total samples:", len(formatted_data))