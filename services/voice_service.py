"""
services/voice_service.py
Production-grade STT / TTS Pipeline
Primary:  Edge-TTS  (kn-IN-SapnaNeural)
Fallback: gTTS      (lang='kn')
Kannada Disaster Management AI System
"""

import asyncio
import hashlib
import logging
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Optional, Tuple

import edge_tts
from faster_whisper import WhisperModel

from config import AUDIO_DIR, TTS_VOICE, WHISPER_MODEL_SIZE

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Whisper STT model  (loaded once at import time)
# ─────────────────────────────────────────────────────────────────────────────

logger.info(f"Loading Whisper model ({WHISPER_MODEL_SIZE})…")
try:
    _whisper = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
    logger.info("Whisper model loaded ✓")
    _whisper_available = True
except Exception as _e:
    logger.error(f"Whisper load failed: {_e}")
    _whisper = None
    _whisper_available = False

MIN_SEGMENT_CONFIDENCE = -1.0
MIN_TRANSCRIPT_CHARS   = 3

# ─────────────────────────────────────────────────────────────────────────────
# Audio validation  (mutagen + size check)  — defined FIRST, used by purge
# ─────────────────────────────────────────────────────────────────────────────

def _validate_audio(path: Path) -> Tuple[bool, int]:
    """
    Returns (is_valid, file_size_bytes).
    A file is valid when:
      - it exists
      - size > 1024 bytes
      - mutagen can parse it as audio
    """
    if not path.exists():
        return False, 0

    size = path.stat().st_size
    if size <= 1024:
        return False, size

    try:
        from mutagen import File as MutagenFile
        audio = MutagenFile(str(path))
        if audio is None:
            logger.debug(f"mutagen returned None for {path.name} — treating as invalid")
            return False, size
        return True, size
    except Exception as e:
        logger.debug(f"mutagen validation failed for {path.name}: {e}")
        return False, size


def _safe_delete(path: Path) -> None:
    try:
        if path.exists():
            path.unlink()
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Startup: purge every broken / 0-byte MP3 from the cache directory
# ─────────────────────────────────────────────────────────────────────────────

def _purge_broken_cache() -> None:
    """Delete any MP3 in AUDIO_DIR that is 0 bytes or fails mutagen validation."""
    if not AUDIO_DIR.exists():
        return
    removed = 0
    for f in AUDIO_DIR.glob("*.mp3"):
        valid, size = _validate_audio(f)
        if not valid:
            try:
                f.unlink()
                removed += 1
                logger.warning(f"Startup cache purge: deleted broken file {f.name} ({size} bytes)")
            except Exception:
                pass
    if removed:
        logger.info(f"Startup cache purge complete — removed {removed} broken file(s)")
    else:
        logger.info("Startup cache purge: no broken files found ✓")


# Run immediately on import so Flask never serves stale 0-byte files
_purge_broken_cache()


# ─────────────────────────────────────────────────────────────────────────────
# Edge-TTS  (primary)
# ─────────────────────────────────────────────────────────────────────────────

async def _edge_tts_async(text: str, output_path: str) -> int:
    """Stream Edge-TTS audio to file. Returns bytes written. Raises on failure."""
    bytes_written = 0
    communicate = edge_tts.Communicate(text, voice=TTS_VOICE)
    with open(output_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
                bytes_written += len(chunk["data"])
    return bytes_written


def _run_edge_tts(text: str, output_path: str) -> int:
    """
    Run Edge-TTS in an isolated thread + event loop.
    Returns bytes written. Propagates any exception to the caller.
    """
    holder: dict = {"bytes": 0, "error": None}

    def _worker():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            holder["bytes"] = loop.run_until_complete(
                _edge_tts_async(text, output_path)
            )
        except Exception as exc:
            holder["error"] = exc
        finally:
            try:
                pending = asyncio.all_tasks(loop)
                for t in pending:
                    t.cancel()
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                pass
            loop.close()

    thread = threading.Thread(target=_worker, daemon=False)
    thread.start()
    thread.join(timeout=30)

    if thread.is_alive():
        raise TimeoutError("Edge-TTS timed out after 30 s")
    if holder["error"] is not None:
        raise holder["error"]
    return holder["bytes"]


# ─────────────────────────────────────────────────────────────────────────────
# gTTS  (fallback)
# ─────────────────────────────────────────────────────────────────────────────

def _run_gtts(text: str, output_path: str) -> int:
    """
    Generate audio with gTTS (Google TTS, lang='kn').
    Returns bytes written. Raises on failure.
    """
    from gtts import gTTS
    tts = gTTS(text=text[:500], lang="kn", slow=False)
    tts.save(output_path)
    size = os.path.getsize(output_path)
    return size


# ─────────────────────────────────────────────────────────────────────────────
# Public API: synthesize_speech
# ─────────────────────────────────────────────────────────────────────────────

def synthesize_speech(text: str) -> Optional[str]:
    """
    Generate TTS audio for Kannada text.

    Strategy:
        1. Check MD5 cache — validate before trusting (purge if broken).
        2. Try Edge-TTS.
        3. On any Edge-TTS failure → try gTTS.
        4. Validate output with mutagen before committing.
        5. Atomic rename tmp → final to prevent partial-file serving.
        6. Return "/static/audio/<hash>.mp3" or None.
    """
    if not text or not text.strip():
        return None

    tts_text  = text.strip()[:800]          # practical limit for both engines
    text_hash = hashlib.md5(tts_text.encode("utf-8")).hexdigest()
    filename  = f"{text_hash}.mp3"
    final_path = AUDIO_DIR / filename

    # ── 1. Cache hit ──────────────────────────────────────────────────────────
    if final_path.exists():
        valid, size = _validate_audio(final_path)
        if valid:
            logger.info(f"TTS cache hit ✓  {filename}  ({size:,} bytes)")
            try:
                os.utime(final_path, None)
            except Exception:
                pass
            return f"/static/audio/{filename}"
        else:
            logger.warning(f"TTS cache poisoned — deleting {filename} ({size} bytes) and regenerating")
            _safe_delete(final_path)

    # ── 2. Generate ───────────────────────────────────────────────────────────
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path   = AUDIO_DIR / f"tmp_{uuid.uuid4().hex}.mp3"
    start_time = time.time()
    engine_used = "none"

    try:
        # ── 2a. Edge-TTS ──────────────────────────────────────────────────────
        try:
            logger.info(f"TTS [Edge] generating  voice={TTS_VOICE}  len={len(tts_text)}  file={filename}")
            bytes_written = _run_edge_tts(tts_text, str(tmp_path))
            elapsed = time.time() - start_time
            valid, size = _validate_audio(tmp_path)

            if valid and bytes_written > 0:
                engine_used = "edge-tts"
                logger.info(f"TTS [Edge] success ✓  {filename}  {size:,} bytes  {elapsed:.2f}s")
            else:
                raise ValueError(
                    f"Edge-TTS produced invalid output: bytes_written={bytes_written}, size={size}"
                )

        except Exception as edge_err:
            elapsed = time.time() - start_time
            is_403 = "403" in str(edge_err) or "WSServerHandshakeError" in type(edge_err).__name__
            log_fn = logger.warning if is_403 else logger.error
            log_fn(
                f"TTS [Edge] failed after {elapsed:.2f}s: {type(edge_err).__name__}: {edge_err}"
            )
            if is_403:
                logger.warning(
                    "Edge-TTS 403 — Microsoft endpoint is rate-limiting this IP. "
                    "Switching to gTTS fallback automatically."
                )
            _safe_delete(tmp_path)

            # ── 2b. gTTS fallback ─────────────────────────────────────────────
            logger.info(f"TTS [gTTS] fallback generating  lang=kn  len={len(tts_text)}  file={filename}")
            fallback_start = time.time()
            try:
                bytes_written = _run_gtts(tts_text, str(tmp_path))
                elapsed_fb = time.time() - fallback_start
                valid, size = _validate_audio(tmp_path)

                if valid and bytes_written > 0:
                    engine_used = "gtts"
                    logger.info(f"TTS [gTTS] success ✓  {filename}  {size:,} bytes  {elapsed_fb:.2f}s")
                else:
                    raise ValueError(
                        f"gTTS produced invalid output: bytes_written={bytes_written}, size={size}"
                    )

            except Exception as gtts_err:
                elapsed_fb = time.time() - fallback_start
                logger.error(f"TTS [gTTS] also failed after {elapsed_fb:.2f}s: {type(gtts_err).__name__}: {gtts_err}")
                _safe_delete(tmp_path)
                return None

        # ── 3. Atomic commit ──────────────────────────────────────────────────
        tmp_path.rename(final_path)
        logger.info(f"TTS committed ✓  engine={engine_used}  path={final_path}  size={size:,} bytes")
        return f"/static/audio/{filename}"

    except Exception as unexpected:
        logger.exception(f"TTS unexpected error: {unexpected}")
        _safe_delete(tmp_path)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# STT: Speech → Text  (Whisper)
# ─────────────────────────────────────────────────────────────────────────────

def _convert_to_wav(input_path: str, output_path: str) -> bool:
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(input_path)
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(output_path, format="wav")
        return True
    except Exception as e:
        logger.warning(f"Audio conversion failed: {e} — using original file")
        return False


def speech_to_text(audio_file: str) -> Tuple[str, float]:
    """
    Transcribe audio to Kannada text using Whisper.
    Returns: (transcript_text, confidence_score 0–1)
    """
    if not _whisper_available:
        logger.error("Whisper model unavailable")
        return "", 0.0

    wav_path  = str(AUDIO_DIR / f"tmp_{uuid.uuid4().hex}.wav")
    converted = _convert_to_wav(audio_file, wav_path)
    process_path = wav_path if converted else audio_file

    try:
        segments, _ = _whisper.transcribe(
            process_path,
            language="kn",
            task="transcribe",
            beam_size=5,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 300},
        )

        valid_segs, conf_sum, seg_count = [], 0.0, 0
        for seg in segments:
            lp = getattr(seg, "avg_logprob", -0.5)
            if lp >= MIN_SEGMENT_CONFIDENCE:
                valid_segs.append(seg.text)
                conf_sum += lp
                seg_count += 1

        transcript = " ".join(valid_segs).strip()
        avg_conf   = (conf_sum / seg_count) if seg_count > 0 else -1.0
        confidence = max(0.0, min(1.0, avg_conf + 1.0))

        if len(transcript) < MIN_TRANSCRIPT_CHARS:
            logger.warning(f"Transcript too short: '{transcript}'")
            return "", 0.0

        logger.info(f"STT ✓  '{transcript[:80]}'  conf={confidence:.2f}")
        return transcript, round(confidence, 2)

    except Exception as e:
        logger.error(f"Whisper transcription error: {e}")
        return "", 0.0
    finally:
        if converted and os.path.exists(wav_path):
            try:
                os.remove(wav_path)
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────────────────────
# Background audio cleanup daemon
# ─────────────────────────────────────────────────────────────────────────────

def start_audio_cleanup_daemon() -> None:
    """Delete audio files older than 24 h every 30 min."""
    def _loop():
        logger.info("Audio cleanup daemon started ✓")
        while True:
            try:
                cutoff = time.time() - 86400
                removed = 0
                if AUDIO_DIR.exists():
                    for f in AUDIO_DIR.glob("*.mp3"):
                        if f.is_file() and f.stat().st_mtime < cutoff:
                            try:
                                f.unlink()
                                removed += 1
                            except Exception:
                                pass
                if removed:
                    logger.info(f"Cleanup daemon: removed {removed} expired file(s)")
            except Exception as e:
                logger.error(f"Cleanup daemon error: {e}")
            time.sleep(1800)

    threading.Thread(target=_loop, daemon=True).start()
