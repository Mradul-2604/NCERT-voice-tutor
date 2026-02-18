"""
FAISS vector store management.
Handles index creation, adding embeddings, saving/loading, and clearing.
Stores metadata (page, chunk_id, pdf_name) alongside the FAISS index.
"""

import json
import os
from typing import Dict, List, Tuple

import faiss
import numpy as np

from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FAISS_DIR = os.path.join(BASE_DIR, "vector_store", "faiss_index")
INDEX_PATH = os.path.join(FAISS_DIR, "index.faiss")
METADATA_PATH = os.path.join(FAISS_DIR, "metadata.json")

os.makedirs(FAISS_DIR, exist_ok=True)

# Module state
_index: faiss.IndexFlatL2 | None = None
_metadata: List[Dict] = []


def _ensure_loaded():
    """Load index and metadata from disk if not already in memory."""
    global _index, _metadata
    if _index is None:
        if os.path.exists(INDEX_PATH) and os.path.exists(METADATA_PATH):
            _index = faiss.read_index(INDEX_PATH)
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                _metadata = json.load(f)
            logger.info(
                f"Loaded FAISS index with {_index.ntotal} vectors and "
                f"{len(_metadata)} metadata entries"
            )
        else:
            logger.info("No existing FAISS index found; will create on first add.")


def add_to_index(embeddings: np.ndarray, chunks_metadata: List[Dict]):
    """
    Add embeddings and their metadata to the FAISS index.

    Args:
        embeddings: numpy array of shape (n, dim)
        chunks_metadata: list of dicts with keys: text, page, chunk_id, pdf_name
    """
    global _index, _metadata
    _ensure_loaded()

    dim = embeddings.shape[1]

    if _index is None:
        _index = faiss.IndexFlatL2(dim)
        _metadata = []
        logger.info(f"Created new FAISS index with dimension {dim}")

    _index.add(embeddings.astype(np.float32))
    _metadata.extend(chunks_metadata)

    # Persist to disk
    _save()

    logger.info(
        f"Added {len(chunks_metadata)} vectors. "
        f"Total vectors in index: {_index.ntotal}"
    )


def search(query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[Dict, float]]:
    """
    Search the FAISS index for nearest neighbors.

    Returns:
        List of (metadata_dict, distance) tuples, sorted by distance ascending.
    """
    _ensure_loaded()

    if _index is None or _index.ntotal == 0:
        logger.warning("FAISS index is empty — cannot search.")
        return []

    distances, indices = _index.search(query_embedding.astype(np.float32), top_k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue
        if idx < len(_metadata):
            results.append((_metadata[idx], float(dist)))

    logger.info(f"Search returned {len(results)} results (top_k={top_k})")
    return results


def get_index_size() -> int:
    """Return total number of vectors in the index."""
    _ensure_loaded()
    return _index.ntotal if _index else 0


def get_indexed_pdfs() -> List[str]:
    """Return list of unique PDF names in the index."""
    _ensure_loaded()
    if not _metadata:
        return []
    return list(set(m.get("pdf_name", "") for m in _metadata))


def clear_index():
    """Delete the FAISS index and metadata from disk and memory."""
    global _index, _metadata
    _index = None
    _metadata = []

    for path in [INDEX_PATH, METADATA_PATH]:
        if os.path.exists(path):
            os.remove(path)

    logger.info("FAISS index and metadata cleared.")


def _save():
    """Persist index and metadata to disk."""
    if _index is not None:
        faiss.write_index(_index, INDEX_PATH)
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(_metadata, f, ensure_ascii=False, indent=2)
    logger.debug("FAISS index and metadata saved to disk.")
