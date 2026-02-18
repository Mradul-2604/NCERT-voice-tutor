"""
NCERT Voice Tutor — FastAPI Backend
All API endpoints for PDF upload, RAG Q&A, TTS, and management.
"""

import os
import shutil
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from backend.rag import chunker, embedder, generator, pdf_loader, retriever, vector_store
from backend.speech import tts_manager
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# ─── App Setup ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="NCERT Voice Tutor API",
    description="PDF → RAG → Answer → TTS Voice Tutor",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_DIR = os.path.join(BASE_DIR, "data", "pdfs")
TEXT_DIR = os.path.join(BASE_DIR, "data", "extracted_text")
AUDIO_DIR = os.path.join(BASE_DIR, "data", "audio_outputs")

for d in [PDF_DIR, TEXT_DIR, AUDIO_DIR]:
    os.makedirs(d, exist_ok=True)


# ─── Request / Response Models ───────────────────────────────────────────────

class AskTextRequest(BaseModel):
    question: str
    pdf_filter: Optional[str] = None
    tts_engine: str = "coqui"
    tts_model: str = "tacotron2-DDC"
    speed: float = 1.0


class TTSRequest(BaseModel):
    text: str
    engine: str = "coqui"
    model_key: str = "tacotron2-DDC"
    speed: float = 1.0


# ─── 1. Upload PDF ──────────────────────────────────────────────────────────

@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload a PDF, extract text, chunk, embed, and index into FAISS."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    try:
        # Save uploaded PDF
        pdf_path = os.path.join(PDF_DIR, file.filename)
        with open(pdf_path, "wb") as f:
            content = await file.read()
            f.write(content)

        logger.info(f"PDF saved: {pdf_path}")

        # Extract text
        pages_data = pdf_loader.extract_text_from_pdf(pdf_path)
        if not pages_data:
            raise HTTPException(status_code=400, detail="No text could be extracted from the PDF.")

        # Chunk text
        chunks = chunker.chunk_pages(pages_data)

        # Generate embeddings
        texts = [c["text"] for c in chunks]
        embeddings = embedder.generate_embeddings(texts)

        # Store in FAISS
        vector_store.add_to_index(embeddings, chunks)

        return JSONResponse({
            "message": f"PDF '{file.filename}' uploaded and indexed successfully.",
            "pages_extracted": len(pages_data),
            "chunks_indexed": len(chunks),
            "total_vectors": vector_store.get_index_size(),
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── 2. Ask Question via Text ───────────────────────────────────────────────

@app.post("/ask_text")
async def ask_text(request: AskTextRequest):
    """Answer a text question using RAG pipeline + TTS."""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        # Retrieve relevant chunks
        chunks = retriever.retrieve(
            query=request.question,
            pdf_filter=request.pdf_filter,
        )

        # Generate answer
        answer = generator.generate_answer(
            question=request.question,
            retrieved_chunks=chunks,
        )

        # Generate TTS audio
        tts_result = tts_manager.generate_speech(
            text=answer,
            engine=request.tts_engine,
            model_key=request.tts_model,
            speed=request.speed,
        )

        # Build sources
        sources = [
            {
                "pdf": c.get("pdf_name", ""),
                "page": c.get("page", 0),
                "chunk": c.get("chunk_id", 0),
                "score": c.get("score", 0),
            }
            for c in chunks
        ]

        context_preview = [c.get("text", "") for c in chunks]

        return JSONResponse({
            "question": request.question,
            "answer": answer,
            "sources": sources,
            "context_preview": context_preview,
            "audio_file": tts_result["audio_path"],
            "tts_engine_used": tts_result["engine_used"],
            "audio_cached": tts_result["cached"],
        })

    except Exception as e:
        logger.error(f"ask_text failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# ─── 4. Dedicated TTS Endpoint ──────────────────────────────────────────────

@app.post("/tts_generate")
async def tts_generate(request: TTSRequest):
    """Generate speech from text using TTS (Coqui or gTTS)."""
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    try:
        result = tts_manager.generate_speech(
            text=request.text,
            engine=request.engine,
            model_key=request.model_key,
            speed=request.speed,
        )

        audio_path = result["audio_path"]

        # Return the audio file directly
        if os.path.exists(audio_path):
            media_type = "audio/wav" if audio_path.endswith(".wav") else "audio/mpeg"
            return FileResponse(
                path=audio_path,
                media_type=media_type,
                filename=os.path.basename(audio_path),
            )
        else:
            raise HTTPException(status_code=500, detail="Audio file generation failed.")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"tts_generate failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── 5. Clear Database ──────────────────────────────────────────────────────

@app.post("/clear_db")
async def clear_db():
    """Clear FAISS index, extracted text, and audio outputs."""
    try:
        vector_store.clear_index()

        # Clear extracted text files
        if os.path.exists(TEXT_DIR):
            shutil.rmtree(TEXT_DIR)
            os.makedirs(TEXT_DIR, exist_ok=True)

        # Clear audio outputs
        if os.path.exists(AUDIO_DIR):
            shutil.rmtree(AUDIO_DIR)
            os.makedirs(AUDIO_DIR, exist_ok=True)

        logger.info("Database, extracted texts, and audio outputs cleared.")

        return JSONResponse({
            "message": "Database cleared successfully.",
            "vectors_remaining": vector_store.get_index_size(),
        })

    except Exception as e:
        logger.error(f"clear_db failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── 6. Health Check ────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Health check endpoint."""
    gemini_status = generator.check_gemini_health()
    tts_status = tts_manager.get_engine_status()

    return JSONResponse({
        "status": "ok",
        "index_size": vector_store.get_index_size(),
        "indexed_pdfs": vector_store.get_indexed_pdfs(),
        "gemini": gemini_status,
        "tts_engines": tts_status,
    })


# ─── 7. Serve Audio Files ───────────────────────────────────────────────────

@app.get("/audio/{filename}")
async def serve_audio(filename: str):
    """Serve an audio file from the audio outputs directory."""
    filepath = os.path.join(AUDIO_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Audio file not found.")

    media_type = "audio/wav" if filepath.endswith(".wav") else "audio/mpeg"
    return FileResponse(path=filepath, media_type=media_type, filename=filename)


# ─── 8. List Indexed PDFs ───────────────────────────────────────────────────

@app.get("/pdfs")
async def list_pdfs():
    """List all indexed PDFs."""
    return JSONResponse({
        "pdfs": vector_store.get_indexed_pdfs(),
    })
