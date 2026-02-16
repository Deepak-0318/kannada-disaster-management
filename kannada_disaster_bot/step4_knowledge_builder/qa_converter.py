import json
import os
import sys

# Dataset root (relative to this script)
ROOT_DATASET = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "disaster_dataset"))
INPUT_FILES = [
    os.path.join(ROOT_DATASET, "kannada_disaster_qa.jsonl"),
    os.path.join(ROOT_DATASET, "kannada_disaster_qa.json"),
    os.path.join(ROOT_DATASET, "kannada_disaster_alpaca.json")
]
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "knowledge_base.json")


def iter_records_from_file(path):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        text = f.read().strip()
        if not text:
            return
        # Try JSONL (one JSON object per line)
        lines = [l for l in text.splitlines() if l.strip()]
        if lines and all(l.strip().startswith("{") for l in lines):
            for line in lines:
                try:
                    yield json.loads(line)
                except Exception:
                    continue
            return
        # Otherwise try full JSON (list or dict)
        try:
            data = json.loads(text)
            if isinstance(data, list):
                for item in data:
                    yield item
                return
            if isinstance(data, dict):
                yield data
                return
        except Exception:
            # Fallback: attempt to parse line-by-line
            for line in lines:
                try:
                    yield json.loads(line)
                except Exception:
                    continue


def convert_qa_to_documents():
    knowledge_base = []
    doc_id = 1

    for input_path in INPUT_FILES:
        for record in iter_records_from_file(input_path):
            if not isinstance(record, dict):
                continue

            question = record.get("instruction", "").strip()
            answer = record.get("output", "").strip()
            # Fallback keys
            if not question:
                question = record.get("question", "").strip()
            if not answer:
                answer = record.get("answer", "").strip()

            disaster_type = record.get("disaster_type", "general")
            language = record.get("language", "unknown")
            source = record.get("source", input_path)

            if not question or not answer:
                continue

            content = f"Q: {question}\nA: {answer}"

            document = {
                "doc_id": doc_id,
                "content": content,
                "disaster_type": disaster_type,
                "language": language,
                "source": source
            }

            knowledge_base.append(document)
            doc_id += 1

    # Save output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        json.dump(knowledge_base, out, ensure_ascii=False, indent=4)

    print(f"Conversion complete. Saved {len(knowledge_base)} documents to {OUTPUT_FILE}")


if __name__ == "__main__":
    # Allow passing a single input file on the CLI
    if len(sys.argv) > 1:
        INPUT_FILES = [sys.argv[1]]
    convert_qa_to_documents()
