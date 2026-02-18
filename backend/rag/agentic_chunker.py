"""
Agentic chunking with Gemini API.
Uses AI to intelligently merge related paragraphs for better semantic coherence.
"""

import os
from typing import Dict, List

from dotenv import load_dotenv
import google.generativeai as genai

from backend.utils.logger import get_logger

# Load environment variables
load_dotenv()

logger = get_logger(__name__)

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MERGE_MODEL = "gemini-3-flash-preview"
MAX_CHUNK_SIZE = 1200


def _initialize_gemini():
    """Initialize Gemini API."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")
    genai.configure(api_key=GEMINI_API_KEY)


def should_merge_paragraphs(para1: str, para2: str) -> bool:
    """
    Ask Gemini if two consecutive paragraphs should be merged.
    
    Args:
        para1: First paragraph text
        para2: Second paragraph text
    
    Returns:
        True if paragraphs should be merged, False otherwise
    """
    prompt = f"""Given these consecutive paragraphs from an NCERT textbook:

[Paragraph 1]
{para1}

[Paragraph 2]
{para2}

Are these paragraphs discussing the same topic/concept and should be merged into one chunk?

Answer ONLY with: YES or NO

Answer YES if:
- They discuss the same concept or topic
- Paragraph 2 continues the explanation from Paragraph 1
- They form a coherent unit together

Answer NO if:
- They discuss different topics
- There's a clear topic change
- They are standalone concepts
"""

    try:
        _initialize_gemini()
        model = genai.GenerativeModel(MERGE_MODEL)
        
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.1,  # Low temperature for consistent decisions
                max_output_tokens=10,  # Only need YES/NO
            ),
        )
        
        answer = response.text.strip().upper()
        decision = "YES" in answer
        
        logger.debug(f"Merge decision for paragraphs: {decision}")
        return decision
        
    except Exception as e:
        logger.error(f"Gemini merge decision failed: {e}")
        # Default to not merging on error
        return False


def merge_related_paragraphs(
    paragraphs: List[str],
    max_chunk_size: int = MAX_CHUNK_SIZE
) -> List[str]:
    """
    Use Gemini API to merge semantically related paragraphs.
    
    Args:
        paragraphs: List of paragraph texts
        max_chunk_size: Maximum characters per chunk
    
    Returns:
        List of merged chunk texts
    """
    if not paragraphs:
        return []
    
    if len(paragraphs) == 1:
        return paragraphs
    
    merged_chunks = []
    current_chunk = paragraphs[0]
    
    for i in range(1, len(paragraphs)):
        next_para = paragraphs[i]
        
        # Check size constraint
        potential_merge = f"{current_chunk}\n\n{next_para}"
        if len(potential_merge) > max_chunk_size:
            # Too large, save current and start new
            merged_chunks.append(current_chunk)
            current_chunk = next_para
            continue
        
        # Ask Gemini if they should be merged
        if should_merge_paragraphs(current_chunk, next_para):
            current_chunk = potential_merge
            logger.info(f"Merged paragraphs {i-1} and {i}")
        else:
            # Different topics, save current and start new
            merged_chunks.append(current_chunk)
            current_chunk = next_para
    
    # Add the last chunk
    if current_chunk:
        merged_chunks.append(current_chunk)
    
    logger.info(
        f"Agentic merging: {len(paragraphs)} paragraphs → {len(merged_chunks)} chunks"
    )
    
    return merged_chunks


def detect_headings(text: str) -> List[Dict]:
    """
    Detect headings and split text into structured paragraphs.
    
    Returns:
        List of {"text": str, "is_heading": bool}
    """
    lines = text.split('\n')
    paragraphs = []
    current_para = []
    
    for line in lines:
        stripped = line.strip()
        
        if not stripped:
            # Empty line - end of paragraph
            if current_para:
                para_text = '\n'.join(current_para).strip()
                if para_text:
                    paragraphs.append({
                        "text": para_text,
                        "is_heading": False
                    })
                current_para = []
            continue
        
        # Detect headings
        is_heading = (
            stripped.isupper() or  # ALL CAPS
            len(stripped) < 60 and not stripped.endswith('.') or  # Short line, no period
            any(stripped.startswith(prefix) for prefix in ['Chapter', 'Section', 'CHAPTER', 'SECTION'])
        )
        
        if is_heading and current_para:
            # Save previous paragraph
            para_text = '\n'.join(current_para).strip()
            if para_text:
                paragraphs.append({
                    "text": para_text,
                    "is_heading": False
                })
            current_para = []
            
            # Add heading
            paragraphs.append({
                "text": stripped,
                "is_heading": True
            })
        else:
            current_para.append(line)
    
    # Add any remaining paragraph
    if current_para:
        para_text = '\n'.join(current_para).strip()
        if para_text:
            paragraphs.append({
                "text": para_text,
                "is_heading": False
            })
    
    return paragraphs
