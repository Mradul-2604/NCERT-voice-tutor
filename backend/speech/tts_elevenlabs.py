"""
ElevenLabs TTS — High-quality Text-to-Speech using ElevenLabs API.
Requires ELEVENLABS_API_KEY environment variable.
"""

import os

import requests
from dotenv import load_dotenv

from backend.utils.cache import AUDIO_DIR, get_audio_filepath
from backend.utils.logger import get_logger

# Load environment variables
load_dotenv()

logger = get_logger(__name__)

# ElevenLabs API configuration
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"

# Available voices (voice_id: display_name)
VOICES = {
    "rachel": "21m00Tcm4TlvDq8ikWAM",      # Rachel - calm, clear
    "adam": "pNInz6obpgDQGcFmaJgB",         # Adam - deep, narration
    "bella": "EXAVITQu4vr4xnSDxMaL",       # Bella - soft, warm
    "josh": "TxGEqnHWrfWFTfGW9XjX",        # Josh - young, dynamic
    "elli": "MF3mGyEYCl7XYWbV9V6O",        # Elli - young female
}

DEFAULT_VOICE = "rachel"
DEFAULT_MODEL = "eleven_multilingual_v2"


def _get_api_key():
    """Read API key fresh from env every time (so .env changes are picked up)."""
    load_dotenv(override=True)
    return os.getenv("ELEVENLABS_API_KEY", "")


def synthesize(
    text: str,
    voice: str = DEFAULT_VOICE,
    model: str = DEFAULT_MODEL,
    stability: float = 0.5,
    similarity: float = 0.75,
) -> str:
    """
    Generate speech using ElevenLabs API.

    Args:
        text: Text to convert to speech.
        voice: Voice name (rachel, adam, bella, josh, elli).
        model: ElevenLabs model ID.
        stability: Voice stability (0-1). Lower = more expressive.
        similarity: Similarity boost (0-1). Higher = closer to original voice.

    Returns:
        Absolute path to the generated .mp3 file.

    Raises:
        ValueError: If API key is not set.
        RuntimeError: If API call fails.
    """
    api_key = _get_api_key()
    if not api_key:
        raise ValueError(
            "ELEVENLABS_API_KEY is not set. "
            "Get your API key from https://elevenlabs.io"
        )

    os.makedirs(AUDIO_DIR, exist_ok=True)
    output_path = get_audio_filepath(text, extension=".mp3")

    # Get voice ID
    voice_id = VOICES.get(voice.lower(), VOICES[DEFAULT_VOICE])

    url = f"{ELEVENLABS_BASE_URL}/text-to-speech/{voice_id}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key,
    }

    payload = {
        "text": text,
        "model_id": model,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity,
        },
    }

    logger.info(f"Generating audio with ElevenLabs (voice={voice}, model={model})")

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)

        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            logger.info(f"ElevenLabs audio saved to: {output_path}")
            return output_path
        elif response.status_code == 401:
            raise ValueError("Invalid ElevenLabs API key.")
        elif response.status_code == 429:
            raise RuntimeError("ElevenLabs API rate limit / quota exceeded.")
        else:
            error_detail = response.text[:200]
            raise RuntimeError(
                f"ElevenLabs API error (status {response.status_code}): {error_detail}"
            )

    except requests.exceptions.Timeout:
        raise RuntimeError("ElevenLabs API request timed out.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Could not connect to ElevenLabs API.")
    except (ValueError, RuntimeError):
        raise
    except Exception as e:
        logger.error(f"ElevenLabs synthesis failed: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        raise


def is_available() -> bool:
    """Check if ElevenLabs API key is configured."""
    return bool(_get_api_key())


def get_available_voices() -> dict:
    """Return available voice options."""
    return {name: name.capitalize() for name in VOICES}
