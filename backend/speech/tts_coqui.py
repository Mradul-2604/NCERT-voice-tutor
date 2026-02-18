"""
pyttsx3 — Primary offline Text-to-Speech engine.
Uses the system's built-in speech synthesis (SAPI5 on Windows).
Supports multiple voices and speed control.
"""

import os
from typing import Optional

import pyttsx3

from backend.utils.cache import AUDIO_DIR, get_audio_filepath
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Available voice options
VOICE_MODELS = {
    "default": "Default System Voice",
    "male": "Male Voice",
    "female": "Female Voice",
}

DEFAULT_MODEL_KEY = "default"


def _get_engine(speed: float = 1.0, voice_key: str = "default") -> pyttsx3.Engine:
    """Create a configured pyttsx3 engine instance."""
    engine = pyttsx3.init()

    # Set speech rate (default is ~200 words/min)
    base_rate = 175
    engine.setProperty("rate", int(base_rate * speed))

    # Set volume
    engine.setProperty("volume", 1.0)

    # Select voice
    voices = engine.getProperty("voices")
    if voices:
        if voice_key == "female":
            # Try to find a female voice
            for v in voices:
                if "female" in v.name.lower() or "zira" in v.name.lower():
                    engine.setProperty("voice", v.id)
                    break
        elif voice_key == "male":
            # Try to find a male voice
            for v in voices:
                if "male" in v.name.lower() or "david" in v.name.lower():
                    engine.setProperty("voice", v.id)
                    break
        # "default" uses whatever is already set

    return engine


def synthesize(
    text: str,
    model_key: str = DEFAULT_MODEL_KEY,
    speed: float = 1.0,
) -> str:
    """
    Generate speech audio from text using pyttsx3.

    Args:
        text: Text to convert to speech.
        model_key: Voice key from VOICE_MODELS dict.
        speed: Speech speed multiplier (0.5 to 2.0).

    Returns:
        Absolute path to the generated .wav file.

    Raises:
        Exception: If pyttsx3 fails.
    """
    os.makedirs(AUDIO_DIR, exist_ok=True)

    output_path = get_audio_filepath(text, extension=".wav")

    logger.info(f"Generating audio with pyttsx3 (voice={model_key}, speed={speed})")

    try:
        engine = _get_engine(speed=speed, voice_key=model_key)
        engine.save_to_file(text, output_path)
        engine.runAndWait()
        engine.stop()

        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            logger.info(f"pyttsx3 audio saved to: {output_path}")
            return output_path
        else:
            raise RuntimeError("pyttsx3 produced an empty or missing audio file")

    except Exception as e:
        logger.error(f"pyttsx3 synthesis failed: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        raise


def get_available_models() -> dict:
    """Return available voice options."""
    return VOICE_MODELS.copy()


def get_system_voices() -> list:
    """List all available system voices."""
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        voice_list = [{"id": v.id, "name": v.name} for v in voices]
        engine.stop()
        return voice_list
    except Exception:
        return []


def is_available() -> bool:
    """Check if pyttsx3 is importable and functional."""
    try:
        engine = pyttsx3.init()
        engine.stop()
        return True
    except Exception:
        return False
