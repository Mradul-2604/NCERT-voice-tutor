"""
Text chunking with overlap for RAG pipeline.
Supports both rule-based and agentic (AI-powered) chunking.
"""

import os
from typing import Dict, List

from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.utils.logger import get_logger

# Load environment variables
load_dotenv()

logger = get_logger(__name__)

# Chunking configuration
CHUNK_SIZE = 800  # characters
CHUNK_OVERLAP = 150  # characters
ENABLE_AGENTIC_CHUNKING = os.getenv("ENABLE_AGENTIC_CHUNKING", "false").lower() == "true"


def chunk_pages(pages_data: List[Dict]) -> List[Dict]:
    """
    Split extracted page texts into overlapping chunks.
    
    Uses hybrid approach if ENABLE_AGENTIC_CHUNKING=true:
    1. Split by paragraphs and detect headings
    2. Use Gemini API to merge related paragraphs
    
    Otherwise uses simple RecursiveCharacterTextSplitter.

    Args:
        pages_data: List of {"page": int, "text": str, "pdf_name": str}

    Returns:
        List of chunk dicts with metadata:
        [{"text": "...", "page": 1, "chunk_id": 0, "pdf_name": "bio.pdf"}, ...]
    """
    if ENABLE_AGENTIC_CHUNKING:
        logger.info("Using agentic chunking (Gemini-powered merging)")
        return _chunk_pages_agentic(pages_data)
    else:
        logger.info("Using rule-based chunking (RecursiveCharacterTextSplitter)")
        return _chunk_pages_simple(pages_data)


def _chunk_pages_simple(pages_data: List[Dict]) -> List[Dict]:
    """Original rule-based chunking approach."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    all_chunks = []
    global_chunk_id = 0

    for page_data in pages_data:
        text = page_data["text"]
        page_num = page_data["page"]
        pdf_name = page_data["pdf_name"]

        if not text.strip():
            continue

        chunks = splitter.split_text(text)

        for chunk_text in chunks:
            all_chunks.append({
                "text": chunk_text,
                "page": page_num,
                "chunk_id": global_chunk_id,
                "pdf_name": pdf_name,
            })
            global_chunk_id += 1

    logger.info(
        f"Created {len(all_chunks)} chunks from {len(pages_data)} pages "
        f"(chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})"
    )

    return all_chunks


def _chunk_pages_agentic(pages_data: List[Dict]) -> List[Dict]:
    """
    Agentic chunking approach:
    1. Detect paragraphs and headings
    2. Use Gemini to merge related paragraphs
    """
    try:
        from backend.rag.agentic_chunker import detect_headings, merge_related_paragraphs
    except ImportError as e:
        logger.error(f"Failed to import agentic_chunker: {e}. Falling back to simple chunking.")
        return _chunk_pages_simple(pages_data)

    all_chunks = []
    global_chunk_id = 0

    for page_data in pages_data:
        text = page_data["text"]
        page_num = page_data["page"]
        pdf_name = page_data["pdf_name"]

        if not text.strip():
            continue

        # Step 1: Detect paragraphs and headings
        structured_paras = detect_headings(text)
        
        # Extract just the text, preserving heading markers
        para_texts = []
        for para in structured_paras:
            if para["is_heading"]:
                # Keep headings attached to next paragraph
                para_texts.append(f"## {para['text']}")
            else:
                para_texts.append(para["text"])
        
        if not para_texts:
            continue

        # Step 2: Merge related paragraphs using Gemini
        try:
            merged_chunks_texts = merge_related_paragraphs(para_texts)
        except Exception as e:
            logger.error(f"Agentic merging failed: {e}. Using paragraphs as-is.")
            merged_chunks_texts = para_texts

        # Convert to chunk dicts
        for chunk_text in merged_chunks_texts:
            all_chunks.append({
                "text": chunk_text,
                "page": page_num,
                "chunk_id": global_chunk_id,
                "pdf_name": pdf_name,
            })
            global_chunk_id += 1

    logger.info(
        f"Created {len(all_chunks)} chunks from {len(pages_data)} pages using agentic chunking"
    )

    return all_chunks
