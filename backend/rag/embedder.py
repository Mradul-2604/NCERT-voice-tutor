"""
Embedding generation using sentence-transformers.
Uses the lightweight all-MiniLM-L6-v2 model.
"""

from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer

from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Model selection
MODEL_NAME = "all-MiniLM-L6-v2"

# Singleton model instance
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    """Lazy-load the sentence transformer model."""
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {MODEL_NAME}")
        _model = SentenceTransformer(MODEL_NAME)
        logger.info("Embedding model loaded successfully")
    return _model


def generate_embeddings(texts: List[str]) -> np.ndarray:
    """
    Generate embeddings for a list of texts.

    Args:
        texts: List of text strings to embed.

    Returns:
        numpy array of shape (len(texts), embedding_dim)
    """
    model = _get_model()
    logger.info(f"Generating embeddings for {len(texts)} texts...")
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    logger.info(f"Generated embeddings with shape: {embeddings.shape}")
    return embeddings


def generate_single_embedding(text: str) -> np.ndarray:
    """Generate embedding for a single text query."""
    model = _get_model()
    embedding = model.encode([text], convert_to_numpy=True)
    return embedding
