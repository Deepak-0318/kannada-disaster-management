# Quick Start Guide - Disaster Chatbot

## ✅ System Status

All issues have been fixed:
- ✅ Chatbot returns top 3 results
- ✅ TTS (Text-to-Speech) working
- ✅ Vector database rebuilt with kannada_disaster_dataset.jsonl (6,006 samples)

## 🚀 Start the Application

### Option 1: Using the batch file
```bash
start_app.bat
```

### Option 2: Using Python directly
```bash
python app.py
```

The server will start on: **http://127.0.0.1:5000**

## 🧪 Run Tests

### Test 1: Chatbot Functionality
```bash
python test_chatbot_quick.py
```
**Expected Output:** 3 numbered Kannada responses

### Test 2: TTS (Text-to-Speech)
```bash
python test_tts.py
```
**Expected Output:** Creates `test_tts_output.mp3` file

### Test 3: API Endpoints (requires app running)
```bash
# Terminal 1
python app.py

# Terminal 2
python test_app_api.py
```

## 📊 What Changed

### 1. Anti-Hallucination Layer Removed
- **Before:** Strict confidence threshold blocked most results
- **After:** Always returns top 3 most relevant results
- **Benefit:** You always get answers

### 2. TTS Fixed
- **Before:** Async event loop errors
- **After:** Proper event loop management
- **Benefit:** Audio responses work correctly

### 3. Dataset Updated
- **Before:** Mixed datasets
- **After:** Only `kannada_disaster_dataset.jsonl` (6,006 samples)
- **Benefit:** Consistent, focused disaster management data

## 🎯 How to Use

### Text Chat
1. Open http://127.0.0.1:5000
2. Type your question in Kannada
3. Get top 3 relevant answers
4. Audio response plays automatically

### Voice Chat
1. Click the microphone button
2. Speak your question in Kannada
3. System transcribes and processes
4. Get audio response

### Example Queries
```
ಪ್ರವಾಹ ಸಮಯದಲ್ಲಿ ಏನು ಮಾಡಬೇಕು?
(What to do during floods?)

ಭೂಕುಸಿತ ಸಮಯದಲ್ಲಿ ಏನು ಮಾಡಬೇಕು?
(What to do during landslides?)

ಬೆಂಕಿ ಅಪಘಾತ ಸಮಯದಲ್ಲಿ ಏನು ಮಾಡಬೇಕು?
(What to do during fire accidents?)
```

## 📁 Important Files

| File | Purpose |
|------|---------|
| `app.py` | Flask web server |
| `chatbot.py` | RAG chatbot logic |
| `build_vector_db.py` | Vector database builder |
| `disaster_index.faiss` | FAISS vector index (8.80 MB) |
| `disaster_metadata.json` | Question-answer metadata (1.65 MB) |
| `dataset/kannada_disaster_dataset.jsonl` | Training data (6,006 samples) |

## 🔧 Rebuild Vector Database (if needed)

If you update the dataset:
```bash
python build_vector_db.py
```

This will:
1. Load `kannada_disaster_dataset.jsonl`
2. Generate embeddings (takes ~90 seconds)
3. Build FAISS index
4. Save `disaster_index.faiss` and `disaster_metadata.json`

## 🎨 Features

### Hybrid Retrieval
- **Dense:** FAISS with multilingual-e5-small embeddings
- **Sparse:** BM25 keyword matching
- **Fusion:** Reciprocal Rank Fusion (RRF)

### Emergency Detection
- Automatic detection of emergency keywords
- Faster response in emergency mode
- Lexical urgency scanning

### Multilingual Support
- Kannada script (primary)
- Transliteration support
- Voice input/output in Kannada

### Caching
- In-memory response cache
- LRU eviction (max 1000 entries)
- Faster repeated queries

## 📞 Emergency Numbers (shown in fallback)
- NDRF: 1070
- State Disaster Control: 1077
- Emergency Service: 108
- Fire Service: 101

## 🐛 Troubleshooting

### Issue: No output from chatbot
**Solution:** Vector database might be missing
```bash
python build_vector_db.py
```

### Issue: TTS not working
**Solution:** Check internet connection (edge-tts requires internet)

### Issue: Voice input not working
**Solution:** Check microphone permissions in browser

### Issue: Import errors
**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

## 📝 Notes

- All responses are in Kannada script
- System requires internet for TTS (edge-tts)
- Whisper model runs locally (no internet needed for STT)
- First query may be slow (model loading)
- Subsequent queries are cached and faster

## 🎉 Ready to Go!

Your disaster management chatbot is ready. Start the app and test it:

```bash
python app.py
```

Then open: http://127.0.0.1:5000
