"""
PDF text extraction using pdfplumber.
Extracts text page-by-page and saves raw text to disk.
"""

import os
from typing import Dict, List

import pdfplumber

from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PDF_DIR = os.path.join(BASE_DIR, "data", "pdfs")
TEXT_DIR = os.path.join(BASE_DIR, "data", "extracted_text")

os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(TEXT_DIR, exist_ok=True)


def extract_text_from_pdf(pdf_path: str) -> List[Dict]:
    """
    Extract text from a PDF file page-by-page.

    Returns:
        List of dicts: [{"page": 1, "text": "..."}, ...]
    """
    pages_data = []
    pdf_name = os.path.basename(pdf_path)

    logger.info(f"Extracting text from: {pdf_name}")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text and text.strip():
                    cleaned = _clean_text(text)
                    pages_data.append({
                        "page": i + 1,
                        "text": cleaned,
                        "pdf_name": pdf_name,
                    })

        logger.info(f"Extracted {len(pages_data)} pages from {pdf_name}")

        # Save extracted text to disk
        _save_extracted_text(pdf_name, pages_data)

    except Exception as e:
        logger.error(f"Failed to extract text from {pdf_name}: {e}")
        raise

    return pages_data


def _clean_text(text: str) -> str:
    """Basic text cleaning."""
    # Remove excessive whitespace
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line:
            cleaned_lines.append(line)
    return " ".join(cleaned_lines)


def _save_extracted_text(pdf_name: str, pages_data: List[Dict]) -> str:
    """Save extracted text to a .txt file for reference."""
    txt_filename = pdf_name.replace(".pdf", ".txt").replace(".PDF", ".txt")
    txt_path = os.path.join(TEXT_DIR, txt_filename)

    with open(txt_path, "w", encoding="utf-8") as f:
        for page_data in pages_data:
            f.write(f"\n{'='*60}\n")
            f.write(f"PAGE {page_data['page']}\n")
            f.write(f"{'='*60}\n")
            f.write(page_data["text"])
            f.write("\n")

    logger.info(f"Saved extracted text to: {txt_path}")
    return txt_path
