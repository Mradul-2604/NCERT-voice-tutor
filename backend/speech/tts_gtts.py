"""
gTTS — Fallback Text-to-Speech engine using Google Translate TTS.
Activated automatically when Coqui TTS fails.
"""

import os

from gtts import gTTS

from backend.utils.cache import AUDIO_DIR, get_audio_filepath
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def synthesize(text: str, lang: str = "en", slow: bool = False) -> str:
    """
    Generate speech audio from text using gTTS.

    Args:
        text: Text to convert to speech.
        lang: Language code (default: 'en').
        slow: If True, generate slower speech.

    Returns:
        Absolute path to the generated .mp3 file.

    Raises:
        Exception: If gTTS fails.
    """
    os.makedirs(AUDIO_DIR, exist_ok=True)

    output_path = get_audio_filepath(text, extension=".mp3")

    logger.info(f"Generating audio with gTTS (lang={lang}, slow={slow})")

    try:
        tts = gTTS(text=text, lang=lang, slow=slow)
        tts.save(output_path)
        logger.info(f"gTTS audio saved to: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"gTTS synthesis failed: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        raise


def is_available() -> bool:
    """Check if gTTS is importable."""
    try:
        from gtts import gTTS  # noqa: F401
        return True
    except ImportError:
        return False
