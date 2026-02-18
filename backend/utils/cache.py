"""
Audio caching utility.
Uses MD5 hash of text to create unique filenames.
Avoids regenerating audio for the same answer text.
"""

import hashlib
import os

from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Default audio output directory
AUDIO_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "audio_outputs",
)
os.makedirs(AUDIO_DIR, exist_ok=True)


def text_hash(text: str) -> str:
    """Generate an MD5 hash for the given text."""
    return hashlib.md5(text.strip().encode("utf-8")).hexdigest()


def get_cached_audio_path(text: str, extension: str = ".wav") -> str | None:
    """
    Check if audio for this text already exists in cache.
    Returns the file path if found, else None.
    """
    filename = f"audio_{text_hash(text)}{extension}"
    filepath = os.path.join(AUDIO_DIR, filename)

    if os.path.exists(filepath):
        logger.info(f"Cache HIT for audio: {filename}")
        return filepath

    # Also check the other extension
    alt_ext = ".mp3" if extension == ".wav" else ".wav"
    alt_filename = f"audio_{text_hash(text)}{alt_ext}"
    alt_filepath = os.path.join(AUDIO_DIR, alt_filename)

    if os.path.exists(alt_filepath):
        logger.info(f"Cache HIT (alt format) for audio: {alt_filename}")
        return alt_filepath

    logger.debug(f"Cache MISS for audio: {filename}")
    return None


def get_audio_filepath(text: str, extension: str = ".wav") -> str:
    """
    Generate the target file path for audio output (without checking existence).
    """
    filename = f"audio_{text_hash(text)}{extension}"
    return os.path.join(AUDIO_DIR, filename)
