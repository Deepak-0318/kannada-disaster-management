import os
import sys
import fitz  # PyMuPDF
import json
import re

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_FOLDER = os.path.join(ROOT_DIR, "pdf_documents")
OUTPUT_FILE = os.path.join(ROOT_DIR, "pdf_documents.json")


# -----------------------------
# Utility: Basic language detection
# -----------------------------
def detect_language(text):
    # Kannada Unicode range check
    if re.search(r'[\u0C80-\u0CFF]', text):
        return "kannada"
    return "english"


# -----------------------------
# Utility: Basic disaster inference
# -----------------------------
def infer_disaster_type(text):
    text_lower = text.lower()

    disaster_keywords = {
        "flood": ["flood", "flooding"],
        "earthquake": ["earthquake", "seismic"],
        "cyclone": ["cyclone", "storm", "hurricane"],
        "fire": ["fire", "wildfire"],
        "landslide": ["landslide"],
        "tsunami": ["tsunami"],
        "drought": ["drought"],
        "pandemic": ["pandemic", "virus"]
    }

    for disaster, keywords in disaster_keywords.items():
        for word in keywords:
            if word in text_lower:
                return disaster

    return "general"


# -----------------------------
# Extract text
# -----------------------------
def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Failed to open {pdf_path}: {e}")
        return ""

    full_text = ""

    for page in doc:
        try:
            text = page.get_text()

            # Remove weird symbols
            text = re.sub(r'[^\x00-\x7F\u0C80-\u0CFF\s.,!?():;\-]', '', text)

            # Remove excessive whitespace
            text = re.sub(r'\s+', ' ', text)

            full_text += text + "\n"

        except Exception:
            continue

    return full_text.strip()

# -----------------------------
# Main Processor
# -----------------------------
def process_pdfs():
    pdf_docs = []
    doc_id = 10000  # avoid collision

    if not os.path.exists(PDF_FOLDER):
        print(f"PDF folder not found: {PDF_FOLDER}")
        os.makedirs(PDF_FOLDER, exist_ok=True)
        print("Created folder. Add PDFs and re-run.")
        return

    pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.endswith(".pdf")]

    if not pdf_files:
        print("⚠ No PDF files found.")
        return

    for filename in pdf_files:
        file_path = os.path.join(PDF_FOLDER, filename)

        print(f"Processing: {filename}")
        text = extract_text_from_pdf(file_path)

        if len(text) < 100:
            print(f"Skipping {filename} (too little text)")
            continue

        language = detect_language(text)
        disaster_type = infer_disaster_type(text)

        document = {
            "doc_id": doc_id,
            "content": text,
            "disaster_type": disaster_type,
            "language": language,
            "source": filename
        }

        pdf_docs.append(document)
        doc_id += 1

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(pdf_docs, f, ensure_ascii=False, indent=4)

    print(f"\nExtracted {len(pdf_docs)} PDF documents.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        PDF_FOLDER = sys.argv[1]
    process_pdfs()
