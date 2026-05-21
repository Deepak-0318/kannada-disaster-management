# Kannada Disaster Management Chatbot

A multilingual RAG-based chatbot for disaster management in Karnataka, supporting voice input/output in Kannada.

## ✨ Features

- **Dual Dataset Knowledge Base:** 13,006 entries from both datasets
- **Flexible Output:** 3-7 actionable points (Emergency: 3, Normal: up to 7)
- **Hybrid Retrieval:** FAISS + BM25 + RRF fusion
- **Deduplication:** Aggressive similarity-based filtering
- **Voice Support:** Speech-to-text (Whisper) and text-to-speech (Edge-TTS)
- **Emergency Detection:** Automatic urgency classification
- **Kannada Language:** Full support for Kannada script

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Build Vector Database
```bash
python build_vector_db.py
```

This will:
- Load both datasets (13,006 entries)
- Generate embeddings (~2 minutes)
- Create FAISS index (19.05 MB)

### 3. Start Application
```bash
python app.py
```

Access at: **http://127.0.0.1:5000**

## 📊 System Architecture

```
User Query (Kannada)
    ↓
[Emergency Detection]
    ↓
[Hybrid Retrieval: FAISS + BM25]
    ↓
[RRF Fusion → 50 candidates]
    ↓
[Deduplication (60% threshold)]
    ↓
[Top 3-7 Unique Results]
    ↓
[Response (Kannada)]
    ↓
[TTS Audio (MP3)]
```

## 📁 Project Structure

```
DisasterChatbot_paper/
├── app.py                          # Flask web server
├── chatbot.py                      # RAG chatbot logic
├── voice_agent.py                  # Voice input/output
├── build_vector_db.py              # Vector DB builder
├── disaster_index.faiss            # FAISS index (19.05 MB)
├── disaster_metadata.json          # Metadata (4.33 MB)
├── dataset/
│   ├── kannada_disaster_7000.jsonl      # 7,000 structured entries
│   └── kannada_disaster_dataset.jsonl   # 6,006 augmented entries
├── static/
│   ├── css/styles.css
│   ├── js/main.js
│   └── temp_*.mp3                  # Generated TTS files
├── templates/
│   └── index.html                  # Web interface
└── tests/
    ├── test_chatbot_quick.py
    ├── test_deduplication.py
    ├── test_multiple_queries.py
    └── test_tts.py
```

## 🎯 API Endpoints

### Text Chat
```bash
POST /api/chat
Content-Type: application/json

{
  "question": "ಪ್ರವಾಹ ಸಮಯದಲ್ಲಿ ಏನು ಮಾಡಬೇಕು?",
  "emergency_mode": "normal"
}
```

**Response:**
```json
{
  "response": "1. ...\n2. ...\n3. ...",
  "mode": "normal",
  "audio_url": "/static/temp_text_response.mp3"
}
```

### Voice Chat
```bash
POST /api/voice
Content-Type: multipart/form-data

file: <audio_file>
is_panic: false
manual_mode: normal
```

## 📝 Example Outputs

### Query 1: Food Storage
```
Input: ಭೂಕಂಪ ನಂತರ ಆಹಾರ ಸಂಗ್ರಹಣೆ ಹೇಗೆ?

Output (7 points):
1. ಮನೆಯಲ್ಲಿ ಒಣ ಆಹಾರ ಸಂಗ್ರಹಣೆ ಮಾಡಬೇಕು
2. ಮನೆಯಲ್ಲಿ ಒಣ ಆಹಾರ ಸಂಗ್ರಹಣೆ ಮಾಡುವುದು ಒಳ್ಳೆಯದು
3. ಆಘಾತಗಳಿಗೆ ಸಿದ್ಧರಿರಿ, ಗಾಯಗೊಂಡವರಿಗೆ ಪ್ರಥಮ ಚಿಕಿತ್ಸೆ ನೀಡಿ
4. ಮಣ್ಣಿನ ಫಲವತ್ತತೆ ಪರಿಶೀಲಿಸಿ, ಸರ್ಕಾರಿ ಸಹಾಯ ಪಡೆಯಿರಿ
5. ಹಿಂದಿರುಗದಿರಿ, ಸಹಾಯಕ್ಕಾಗಿ ಕರೆ ಮಾಡಿ
6. ಲಸಿಕೆ ಪೂರ್ಣಗೊಳಿಸಿ, ಆರೋಗ್ಯ ಪರೀಕ್ಷೆ ಮಾಡಿಸಿ
7. ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ, ನೀರು ಕುಡಿಯಿರಿ
```

### Query 2: Flood Safety (Emergency Mode)
```
Input: ಪ್ರವಾಹ ಸಮಯದಲ್ಲಿ ಏನು ಮಾಡಬೇಕು?

Output (3 points - Emergency):
1. ಪ್ರವಾಹ ನೀರಿನಲ್ಲಿ ನಡೆಯಬೇಡಿ, ವಾಹನ ಚಲಾಯಿಸಬೇಡಿ
2. ತಕ್ಷಣ ಎತ್ತರದ ಸ್ಥಳಕ್ಕೆ ತೆರಳಿ, ವಿದ್ಯುತ್ ಸಂಪರ್ಕ ವಿಚ್ಛಿನ್ನಗೊಳಿಸಿ
3. ಭೂಗರ್ಭದಲ್ಲಿ ಇರಬೇಡಿ, ವಿದ್ಯುತ್ ಸಾಧನಗಳನ್ನು ಮುಟ್ಟಬೇಡಿ
```

## 🧪 Testing

### Run All Tests
```bash
# Test chatbot
python test_chatbot_quick.py

# Test deduplication
python test_deduplication.py

# Test multiple queries
python test_multiple_queries.py

# Test TTS
python test_tts.py
```

## ⚙️ Configuration

### Retrieval Parameters
```python
# chatbot.py
- Emergency mode: top_k = 3
- Normal mode: top_k = 7
- Deduplication threshold: 0.6 (60% similarity)
- Candidate pool: 50 (dense) + 50 (sparse)
- RRF k-value: 60
```

### Voice Recognition
```python
# voice_agent.py
- Model: faster-whisper (small)
- Language: Kannada (kn)
- Beam size: 3
- VAD filter: enabled
- Min audio duration: 0.5 seconds
```

### Text-to-Speech
```python
# app.py
- Engine: Microsoft Edge-TTS
- Voice: kn-IN-SapnaNeural
- Output format: MP3
```

## 📊 Performance

| Metric | Value |
|--------|-------|
| Knowledge Base | 13,006 entries |
| Vector DB Size | 19.05 MB |
| Retrieval Time | 200-400ms |
| Cached Retrieval | 10-50ms |
| TTS Generation | 1-2 seconds |
| Output Points | 3-7 (flexible) |

## 🔧 Troubleshooting

### Issue: No output from chatbot
**Solution:** Rebuild vector database
```bash
python build_vector_db.py
```

### Issue: Voice recognition fails
**Symptoms:** Getting garbage text like "ಸಾರಿಲಿಲಿಲಿ..."
**Solution:** 
- Speak clearly and slowly
- Ensure minimum 0.5 seconds of audio
- Check microphone permissions
- Reduce background noise

### Issue: TTS not working
**Solution:** 
- Check internet connection (Edge-TTS requires internet)
- Verify audio file permissions in `static/` folder
- Check browser console for errors

## 📞 Emergency Numbers

The chatbot includes these emergency contacts:
- **NDRF:** 1070
- **State Disaster Control:** 1077
- **Emergency Service:** 108
- **Fire Service:** 101

## 🎯 Key Features Explained

### 1. Flexible Output (3-7 Points)
- **Emergency Mode:** Returns 3 critical, immediate actions
- **Normal Mode:** Returns up to 7 detailed, comprehensive points
- **Adaptive:** Based on available unique results after deduplication

### 2. Deduplication
- **Jaccard Similarity:** 60% threshold
- **Cascading:** Falls back to 50% → 40% if needed
- **Substring Matching:** Catches near-duplicates
- **Result:** Ensures diverse, non-repetitive advice

### 3. Hybrid Retrieval
- **Dense (FAISS):** Semantic similarity using multilingual-e5-small
- **Sparse (BM25):** Keyword matching for exact terms
- **RRF Fusion:** Combines both for optimal results

### 4. Voice Recognition Improvements
- **Garbage Detection:** Filters out repetitive patterns
- **Minimum Duration:** Requires 0.5s of audio
- **Better Beam Search:** Increased from 1 to 3
- **VAD Parameters:** Improved silence detection

## 📄 License

This project is for educational and disaster management purposes.

## 🤝 Contributing

Contributions welcome! Please:
1. Test your changes
2. Update documentation
3. Follow existing code style

## 📧 Support

For issues or questions, please check:
1. `FINAL_STATUS.md` - Complete implementation details
2. `FIXES_SUMMARY.md` - All fixes and changes
3. Test scripts in the project root

---

**Built with:** Python, Flask, FAISS, Whisper, Edge-TTS, Gemini, SentenceTransformers
