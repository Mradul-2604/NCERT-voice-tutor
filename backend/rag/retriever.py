"""
Retriever — similarity search with threshold filtering.
Queries FAISS and returns relevant chunks above a quality threshold.
"""

from typing import Dict, List, Optional

import numpy as np

from backend.rag.embedder import generate_single_embedding
from backend.rag.vector_store import search as faiss_search
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Distance threshold: L2 distance below this is considered "relevant"
# For normalized embeddings, typical L2 distances range ~0.5 (very similar) to ~2.0 (unrelated)
RELEVANCE_THRESHOLD = 1.2
DEFAULT_TOP_K = 5


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    threshold: float = RELEVANCE_THRESHOLD,
    pdf_filter: Optional[str] = None,
) -> List[Dict]:
    """
    Retrieve relevant chunks for a given query.

    Args:
        query: User question text.
        top_k: Number of results to retrieve.
        threshold: Maximum L2 distance to consider relevant.
        pdf_filter: If set, only return results from this PDF.

    Returns:
        List of dicts: [{"text": "...", "page": 1, "chunk_id": 0,
                         "pdf_name": "bio.pdf", "score": 0.45}, ...]
    """
    query_embedding = generate_single_embedding(query)

    # Fetch more if filtering by PDF
    fetch_k = top_k * 3 if pdf_filter else top_k

    raw_results = faiss_search(query_embedding, top_k=fetch_k)

    filtered = []
    for metadata, distance in raw_results:
        # Threshold filter
        if distance > threshold:
            continue

        # PDF filter
        if pdf_filter and metadata.get("pdf_name") != pdf_filter:
            continue

        filtered.append({
            **metadata,
            "score": round(distance, 4),
        })

        if len(filtered) >= top_k:
            break

    logger.info(
        f"Retrieved {len(filtered)} relevant chunks for query: "
        f"'{query[:80]}...' (threshold={threshold})"
    )

    return filtered
