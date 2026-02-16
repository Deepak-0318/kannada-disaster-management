import json
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

QA_FILE = os.path.join(ROOT_DIR, "knowledge_base.json")
PDF_FILE = os.path.join(ROOT_DIR, "pdf_documents.json")
FINAL_OUTPUT = os.path.join(ROOT_DIR, "knowledge_base_updated.json")


def merge_knowledge():
    if not os.path.exists(QA_FILE):
        print("knowledge_base.json not found.")
        return

    with open(QA_FILE, "r", encoding="utf-8") as f:
        qa_data = json.load(f)

    pdf_data = []
    if os.path.exists(PDF_FILE):
        with open(PDF_FILE, "r", encoding="utf-8") as f:
            pdf_data = json.load(f)

    # Prevent duplicates by source
    existing_sources = {doc["source"] for doc in qa_data}

    new_pdf_data = [doc for doc in pdf_data if doc["source"] not in existing_sources]

    merged = qa_data + new_pdf_data

    with open(FINAL_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=4)

    print(f"Final knowledge base created with {len(merged)} documents.")
    print(f"Added {len(new_pdf_data)} new PDF documents.")


if __name__ == "__main__":
    merge_knowledge()
