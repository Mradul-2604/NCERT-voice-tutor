"""
TTS Manager — Orchestrates TTS with automatic fallback.
Supports: ElevenLabs (premium) | gTTS (online) | pyttsx3 (offline)
"""

import os
import re
from typing import Dict, Optional

from backend.speech import tts_coqui, tts_gtts, tts_elevenlabs
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def clean_for_tts(text: str) -> str:
    """
    Remove markdown formatting, LaTeX math, and symbols for clean TTS output.
    Converts math symbols to spoken words for natural speech.
    
    Args:
        text: Text with potential markdown/LaTeX formatting
    
    Returns:
        Clean text suitable for speech synthesis
    """
    # Remove citations like (Page 20), (Pages 20, 21), (Pages 20-22)
    text = re.sub(r"\(Page[s]?\s*[\d,\-\s]+\)", "", text)
    
    # Remove bracket citations like [Page 20] or [jesc111.pdf — Page 5]
    text = re.sub(r"\[.*?Page[s]?\s*[\d,\-\s]+\]", "", text)
    
    # Remove LaTeX inline math \( ... \)
    text = re.sub(r"\\\((.*?)\\\)", r"\1", text)
    
    # Remove LaTeX display math \[ ... \]
    text = re.sub(r"\\\[(.*?)\\\]", r"\1", text)
    
    # Remove $...$ math
    text = re.sub(r"\$(.*?)\$", r"\1", text)
    
    # Remove LaTeX commands like \frac{a}{b} -> a divided by b
    text = re.sub(r"\\frac\{(.*?)\}\{(.*?)\}", r"\1 divided by \2", text)
    
    # Remove remaining backslashes (LaTeX leftovers)
    text = text.replace("\\", "")
    
    # Replace math symbols with spoken words
    text = text.replace("^2", " squared")
    text = text.replace("^3", " cubed")
    text = re.sub(r"\^(\w)", r" to the power \1", text)
    text = text.replace("=", " equals ")
    text = text.replace("×", " multiplied by ")
    text = text.replace("÷", " divided by ")
    text = text.replace("≈", " approximately equals ")
    text = text.replace("≠", " is not equal to ")
    text = text.replace("≥", " is greater than or equal to ")
    text = text.replace("≤", " is less than or equal to ")
    text = text.replace(">", " is greater than ")
    text = text.replace("<", " is less than ")
    text = text.replace("∞", " infinity ")
    text = text.replace("π", " pi ")
    text = text.replace("Ω", " ohms ")
    
    # Remove markdown formatting
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)   # **bold**
    text = re.sub(r"\*(.*?)\*", r"\1", text)       # *italic*
    text = re.sub(r"`(.*?)`", r"\1", text)         # `code`
    text = re.sub(r"#{1,6}\s*", "", text)          # # headings
    
    # Remove list markers and bullets
    text = text.replace("•", "")
    text = text.replace("—", " ")
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    
    # Clean up extra whitespace
    text = re.sub(r"\s+", " ", text).strip()
    
    return text


def generate_speech(
    text: str,
    engine: str = "gtts",
    model_key: str = "default",
    speed: float = 1.0,
) -> Dict:
    """
    Generate speech from text with automatic fallback.

    Args:
        text: Text to synthesize (may contain markdown).
        engine: 'elevenlabs', 'gtts', or 'coqui' (pyttsx3).
        model_key: Voice key for the selected engine.
        speed: Speech speed multiplier.

    Returns:
        Dict with keys: audio_path, engine_used, cached
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")

    # Clean markdown formatting for better TTS output
    tts_text = clean_for_tts(text.strip())
    
    logger.info(f"Generating TTS with engine={engine}: {tts_text[:100]}...")

    # ElevenLabs (premium quality)
    if engine == "elevenlabs":
        return _try_elevenlabs(tts_text, voice=model_key)

    # gTTS (online, free)
    if engine == "gtts":
        return _try_gtts(tts_text)

    # pyttsx3 / coqui (offline), fallback to gTTS
    try:
        path = tts_coqui.synthesize(tts_text, model_key=model_key, speed=speed)
        return {
            "audio_path": path,
            "engine_used": "pyttsx3",
            "cached": False,
        }
    except Exception as e:
        logger.warning(f"pyttsx3 TTS failed, falling back to gTTS: {e}")
        return _try_gtts(tts_text)


def _try_gtts(text: str) -> Dict:
    """Attempt gTTS synthesis."""
    try:
        path = tts_gtts.synthesize(text)
        return {
            "audio_path": path,
            "engine_used": "gtts",
            "cached": False,
        }
    except Exception as e:
        logger.error(f"gTTS failed: {e}")
        raise RuntimeError("TTS engine failed. Please try again.") from e


def _try_elevenlabs(text: str, voice: str = "rachel") -> Dict:
    """Attempt ElevenLabs synthesis, fallback to gTTS."""
    try:
        path = tts_elevenlabs.synthesize(text, voice=voice)
        return {
            "audio_path": path,
            "engine_used": "elevenlabs",
            "cached": False,
        }
    except Exception as e:
        logger.warning(f"ElevenLabs failed, falling back to gTTS: {e}")
        return _try_gtts(text)


def get_engine_status() -> Dict:
    """Return availability status of all TTS engines."""
    return {
        "elevenlabs": {
            "available": tts_elevenlabs.is_available(),
            "voices": tts_elevenlabs.get_available_voices() if tts_elevenlabs.is_available() else {},
        },
        "gtts": {
            "available": tts_gtts.is_available(),
        },
        "pyttsx3": {
            "available": tts_coqui.is_available(),
            "models": tts_coqui.get_available_models() if tts_coqui.is_available() else {},
        },
    }
