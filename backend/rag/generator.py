"""
Answer generator using Google Gemini API.
Strict context-only generation — no hallucination allowed.
"""

import os
from typing import Dict, List

from dotenv import load_dotenv
import google.generativeai as genai

from backend.utils.logger import get_logger

# Load environment variables from .env file
load_dotenv()

logger = get_logger(__name__)

# Gemini configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEFAULT_MODEL = "gemini-3-flash-preview"

# Strict prompt template
SYSTEM_PROMPT = """You are an NCERT Voice Tutor. You answer questions STRICTLY based on the provided context from NCERT textbooks.

RULES:
1. ONLY use information from the provided context to answer.
2. Do NOT use any outside knowledge.
3. If the answer is NOT found in the context, respond EXACTLY with:
   "Sorry, this is not available in the given NCERT PDF."
4. Always cite the source using page numbers when possible.
5. Keep answers clear, concise, and student-friendly.
6. Format the answer in a way that is easy to read aloud."""

USER_PROMPT_TEMPLATE = """Context from NCERT PDF:
---
{context}
---

Question: {question}

Provide a clear, accurate answer based ONLY on the above context. Include page citations where applicable."""


def _initialize_gemini():
    """Initialize Gemini API with the API key."""
    if not GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY environment variable is not set. "
            "Please set it with your Google AI Studio API key."
        )
    genai.configure(api_key=GEMINI_API_KEY)


def generate_answer(
    question: str,
    retrieved_chunks: List[Dict],
    model: str = DEFAULT_MODEL,
) -> str:
    """
    Generate an answer using Gemini API based on retrieved context.

    Args:
        question: User's question.
        retrieved_chunks: List of chunk dicts with 'text', 'page', 'pdf_name'.
        model: Gemini model name.

    Returns:
        Generated answer string.
    """
    if not retrieved_chunks:
        return "Sorry, this is not available in the given NCERT PDF."

    # Build context string with citations
    context_parts = []
    for chunk in retrieved_chunks:
        source = f"[{chunk.get('pdf_name', 'unknown')} — Page {chunk.get('page', '?')}]"
        context_parts.append(f"{source}\n{chunk['text']}")

    context = "\n\n".join(context_parts)

    user_prompt = USER_PROMPT_TEMPLATE.format(
        context=context, question=question
    )

    # Combine system prompt and user prompt
    full_prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}"

    try:
        # Initialize Gemini API
        _initialize_gemini()

        # Create the model
        gemini_model = genai.GenerativeModel(model)

        # Generate response
        response = gemini_model.generate_content(
            full_prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                top_p=0.9,
                max_output_tokens=2048,
            ),
        )

        answer = response.text.strip()

        if not answer:
            answer = "Sorry, this is not available in the given NCERT PDF."

        logger.info(f"Generated answer ({len(answer)} chars) using model '{model}'")
        return answer

    except ValueError as e:
        # API key not set
        logger.error(f"Gemini API key error: {e}")
        return (
            "Error: GEMINI_API_KEY environment variable is not set. "
            "Please configure your Google AI Studio API key."
        )
    except Exception as e:
        logger.error(f"Gemini API generation failed: {e}")
        error_msg = str(e)
        
        # Provide helpful error messages
        if "API_KEY_INVALID" in error_msg or "invalid API key" in error_msg.lower():
            return (
                "Error: Invalid Gemini API key. "
                "Please check your GEMINI_API_KEY environment variable."
            )
        elif "quota" in error_msg.lower():
            return (
                "Error: Gemini API quota exceeded. "
                "Please check your API usage limits."
            )
        elif "network" in error_msg.lower() or "connection" in error_msg.lower():
            return (
                "Error: Network error connecting to Gemini API. "
                "Please check your internet connection."
            )
        else:
            return f"Error: Failed to generate answer — {error_msg}"


def check_gemini_health() -> Dict:
    """Check if Gemini API is configured and accessible."""
    try:
        if not GEMINI_API_KEY:
            return {
                "status": "error",
                "error": "GEMINI_API_KEY environment variable is not set",
                "configured": False,
            }

        # Initialize and test basic connectivity
        _initialize_gemini()
        
        # Try to list models to verify API key works
        models = genai.list_models()
        available_models = [m.name for m in models if "generateContent" in m.supported_generation_methods]
        
        return {
            "status": "connected",
            "configured": True,
            "model": DEFAULT_MODEL,
            "available_models": available_models[:5],  # Show first 5 models
        }
    except ValueError as e:
        return {
            "status": "error",
            "error": str(e),
            "configured": False,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to connect to Gemini API: {str(e)}",
            "configured": bool(GEMINI_API_KEY),
        }
