# Kannada Disaster Management Chatbot

Final demo build for a Kannada disaster-response assistant with text chat, voice input, text-to-speech output, emergency-mode detection, and a GIS shelter dashboard.

## Demo Files

```text
.
├── app.py
├── chatbot.py
├── voice_agent.py
├── build_vector_db.py
├── requirements.txt
├── dataset/
│   ├── kannada_disaster_7000.jsonl
│   ├── kannada_disaster_dataset.jsonl
│   └── shelter_data.json
├── static/
│   ├── css/styles.css
│   └── js/main.js
└── templates/
    └── index.html
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file with:

```text
GEMINI_API_KEY=your_api_key_here
```

## Build Vector Database

Run this once before launching the app:

```bash
python3 build_vector_db.py
```

This generates the ignored runtime files:

```text
disaster_index.faiss
disaster_metadata.json
```

## Run Demo

```bash
python3 app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Notes

- The frontend uses CDN-hosted Leaflet, Font Awesome, and Google Fonts.
- Text-to-speech uses `edge-tts`, which needs internet access at runtime.
- Voice input uses `faster-whisper` and may download/load its model on first use.
