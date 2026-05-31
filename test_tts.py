#!/usr/bin/env python
"""
test_tts.py
TTS Pipeline Test Suite — Kannada Disaster Management AI
Run: .venv/bin/python test_tts.py
"""

import asyncio
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
INFO = "\033[94mINFO\033[0m"

results = []

def check(name: str, condition: bool, detail: str = "") -> bool:
    status = PASS if condition else FAIL
    print(f"  [{status}] {name}" + (f"  — {detail}" if detail else ""))
    results.append((name, condition))
    return condition


# ─────────────────────────────────────────────────────────────────────────────
print("\n══════════════════════════════════════════════")
print("  TEST 1 — Edge-TTS direct (expect 403 or OK)")
print("══════════════════════════════════════════════")
try:
    import edge_tts

    async def _edge_test():
        c = edge_tts.Communicate("ನಮಸ್ಕಾರ", voice="kn-IN-SapnaNeural")
        path = "/tmp/test_edge_direct.mp3"
        bw = 0
        with open(path, "wb") as f:
            async for chunk in c.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                    bw += len(chunk["data"])
        return bw, os.path.getsize(path)

    bw, sz = asyncio.run(_edge_test())
    check("Edge-TTS generates audio", bw > 0, f"bytes={bw}, size={sz}")
except Exception as e:
    check("Edge-TTS generates audio", False, str(e)[:120])
    print(f"  [{INFO}] Edge-TTS failed (expected 403) — gTTS fallback will be used")


# ─────────────────────────────────────────────────────────────────────────────
print("\n══════════════════════════════════════════════")
print("  TEST 2 — gTTS fallback")
print("══════════════════════════════════════════════")
GTTS_PATH = "/tmp/test_gtts.mp3"
try:
    from gtts import gTTS
    t0 = time.time()
    gTTS(text="ನೆರೆ ಬಂದಾಗ ಏನು ಮಾಡಬೇಕು", lang="kn", slow=False).save(GTTS_PATH)
    elapsed = time.time() - t0
    sz = os.path.getsize(GTTS_PATH)
    check("gTTS generates audio",     sz > 1024,   f"size={sz:,} bytes")
    check("gTTS completes in <15s",   elapsed < 15, f"elapsed={elapsed:.2f}s")
except Exception as e:
    check("gTTS generates audio",    False, str(e)[:120])
    check("gTTS completes in <15s",  False, "skipped")


# ─────────────────────────────────────────────────────────────────────────────
print("\n══════════════════════════════════════════════")
print("  TEST 3 — mutagen audio validation")
print("══════════════════════════════════════════════")
try:
    from mutagen import File as MutagenFile

    if os.path.exists(GTTS_PATH):
        af = MutagenFile(GTTS_PATH)
        check("mutagen parses valid MP3", af is not None, f"type={type(af).__name__}")
    else:
        check("mutagen parses valid MP3", False, "gTTS file missing")

    zero_path = "/tmp/test_zero.mp3"
    Path(zero_path).write_bytes(b"")
    try:
        af_zero = MutagenFile(zero_path)
        rejected = af_zero is None
    except Exception:
        rejected = True  # mutagen raised — counts as rejection
    check("mutagen rejects 0-byte file", rejected, "correctly rejected")
    os.unlink(zero_path)

except Exception as e:
    check("mutagen parses valid MP3",    False, str(e)[:120])
    check("mutagen rejects 0-byte file", False, "skipped")


# ─────────────────────────────────────────────────────────────────────────────
print("\n══════════════════════════════════════════════")
print("  TEST 4 — _validate_audio() helper")
print("══════════════════════════════════════════════")
try:
    # Import the private helper directly for testing
    import importlib
    vs = importlib.import_module("services.voice_service")
    validate_audio = vs._validate_audio

    v1, s1 = validate_audio(Path(GTTS_PATH))
    check("_validate_audio: valid MP3 → True",     v1 is True,  f"size={s1:,}")

    zero_path = Path("/tmp/test_zero2.mp3")
    zero_path.write_bytes(b"")
    v2, s2 = validate_audio(zero_path)
    check("_validate_audio: 0-byte → False",       v2 is False, f"size={s2}")
    zero_path.unlink(missing_ok=True)

    v3, s3 = validate_audio(Path("/tmp/nonexistent_xyz_abc.mp3"))
    check("_validate_audio: missing file → False", v3 is False, f"size={s3}")

except Exception as e:
    for n in ["valid MP3 → True", "0-byte → False", "missing → False"]:
        check(f"_validate_audio: {n}", False, str(e)[:80])


# ─────────────────────────────────────────────────────────────────────────────
print("\n══════════════════════════════════════════════")
print("  TEST 5 — synthesize_speech() full pipeline")
print("══════════════════════════════════════════════")
try:
    from services.voice_service import synthesize_speech
    from config import AUDIO_DIR

    test_text = "ನೆರೆ ಬಂದಾಗ ಏನು ಮಾಡಬೇಕು"
    t0  = time.time()
    url = synthesize_speech(test_text)
    elapsed = time.time() - t0

    check("synthesize_speech returns a URL",      url is not None, str(url))

    if url:
        audio_path = AUDIO_DIR / Path(url).name
        exists = audio_path.exists()
        size   = audio_path.stat().st_size if exists else 0
        check("audio file exists on disk",        exists,       str(audio_path))
        check("audio file size > 1 KB",           size > 1024,  f"{size:,} bytes")
        check("URL format is /static/audio/…",    url.startswith("/static/audio/"), url)
        check("synthesize_speech completes <30s", elapsed < 30, f"{elapsed:.2f}s")
    else:
        for n in ["file exists", "size > 1KB", "URL format", "time < 30s"]:
            check(n, False, "skipped — no URL returned")

except Exception as e:
    check("synthesize_speech full pipeline", False, str(e)[:120])


# ─────────────────────────────────────────────────────────────────────────────
print("\n══════════════════════════════════════════════")
print("  TEST 6 — cache: second call returns same URL instantly")
print("══════════════════════════════════════════════")
try:
    from services.voice_service import synthesize_speech

    test_text = "ನೆರೆ ಬಂದಾಗ ಏನು ಮಾಡಬೇಕು"
    t0   = time.time()
    url2 = synthesize_speech(test_text)
    elapsed2 = time.time() - t0

    check("cache hit returns a URL",       url2 is not None, str(url2))
    check("cache hit completes in <0.5s",  elapsed2 < 0.5,  f"{elapsed2:.3f}s")

except Exception as e:
    check("cache hit returns a URL",      False, str(e)[:80])
    check("cache hit completes in <0.5s", False, "skipped")


# ─────────────────────────────────────────────────────────────────────────────
print("\n══════════════════════════════════════════════")
print("  TEST 7 — synthesize_speech edge cases → None")
print("══════════════════════════════════════════════")
try:
    from services.voice_service import synthesize_speech
    check("empty string → None",  synthesize_speech("") is None)
    check("None input → None",    synthesize_speech(None) is None)
    check("whitespace → None",    synthesize_speech("   ") is None)
except Exception as e:
    for n in ["empty string", "None input", "whitespace"]:
        check(f"{n} → None", False, str(e)[:80])


# ─────────────────────────────────────────────────────────────────────────────
print("\n══════════════════════════════════════════════")
print("  SUMMARY")
print("══════════════════════════════════════════════")
passed = sum(1 for _, ok in results if ok)
total  = len(results)
print(f"\n  {passed}/{total} tests passed\n")
for name, ok in results:
    mark = "✅" if ok else "❌"
    print(f"  {mark}  {name}")

print()
sys.exit(0 if passed == total else 1)
