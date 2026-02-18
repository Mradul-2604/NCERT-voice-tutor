# 📚 NCERT Voice Tutor

**PDF → RAG → Answer → TTS Output**

An intelligent voice tutor that lets you upload NCERT PDFs, ask questions via text or voice, and receive spoken answers using high-quality Text-to-Speech.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     STREAMLIT FRONTEND                          │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌───────────┐  │
│  │ PDF      │  │ Text/Voice   │  │ Answer   │  │ Audio     │  │
│  │ Upload   │  │ Question     │  │ Display  │  │ Player    │  │
│  └────┬─────┘  └──────┬───────┘  └────▲─────┘  └─────▲─────┘  │
│       │               │               │              │         │
└───────┼───────────────┼───────────────┼──────────────┼─────────┘
        │               │               │              │
        ▼               ▼               │              │
┌─────────────────────────────────────────────────────────────────┐
│                     FASTAPI BACKEND                             │
│                                                                 │
│  ┌─────────────────────────────────┐                            │
│  │         RAG PIPELINE            │                            │
│  │  PDF → Extract → Chunk → Embed  │                            │
│  │         → FAISS Index           │                            │
│  │  Query → Retrieve → LLM Answer  │                            │
│  └─────────────────────────────────┘                            │
│                                                                 │
│  ┌─────────────────────────────────┐                            │
│  │       SPEECH MODULES            │                            │
│  │  Whisper STT (voice input)      │                            │
│  │  Coqui TTS  (primary output)    │                            │
│  │  gTTS       (fallback output)   │                            │
│  └─────────────────────────────────┘                            │
│                                                                 │
│  ┌──────────┐  ┌────────┐  ┌────────┐                          │
│  │ FAISS    │  │ Gemini │  │ Cache  │                          │
│  │ Index    │  │  API   │  │ Layer  │                          │
│  └──────────┘  └────────┘  └────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📂 Project Structure

```
aivoice/
├── backend/
│   ├── main.py                  # FastAPI app with all endpoints
│   ├── rag/
│   │   ├── pdf_loader.py        # PDF text extraction (pdfplumber)
│   │   ├── chunker.py           # Text chunking with overlap
│   │   ├── embedder.py          # Sentence-transformer embeddings
│   │   ├── vector_store.py      # FAISS index management
│   │   ├── retriever.py         # Similarity search + filtering
│   │   └── generator.py         # Gemini API answer generation
│   ├── speech/
│   │   ├── tts_coqui.py         # Coqui TTS (primary)
│   │   ├── tts_gtts.py          # gTTS (fallback)
│   │   ├── tts_manager.py       # TTS orchestration + caching
│   │   └── stt_whisper.py       # Whisper speech-to-text
│   └── utils/
│       ├── logger.py            # Centralized logging
│       └── cache.py             # Audio hash-based caching
├── frontend/
│   └── app.py                   # Streamlit UI
├── data/
│   ├── pdfs/                    # Uploaded PDFs
│   ├── extracted_text/          # Extracted raw text
│   └── audio_outputs/           # Generated audio files
├── vector_store/
│   └── faiss_index/             # FAISS index files
├── logs/                        # Application logs
├── requirements.txt
└── README.md
```

---

## 🚀 Setup Instructions

### Prerequisites

- Python 3.10+
- pip
- Google Gemini API Key (free from [Google AI Studio](https://aistudio.google.com/app/apikey))

### Step 1: Clone / Navigate to Project

```bash
cd c:\Users\mridu\aivoice
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # macOS/Linux
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note:** Coqui TTS (`TTS` package) may require additional system dependencies. See Troubleshooting below.

### Step 4: Configure Gemini API Key

1. **Get a free API key** from [Google AI Studio](https://aistudio.google.com/app/apikey)
2. **Set the environment variable:**
   ```bash
   # Windows PowerShell
   $env:GEMINI_API_KEY="your-api-key-here"
   
   # Windows CMD
   set GEMINI_API_KEY=your-api-key-here
   
   # Linux/macOS
   export GEMINI_API_KEY=your-api-key-here
   ```

> **Note:** The application will not work without a valid Gemini API key.

### Step 5: Start the Backend

```bash
cd c:\Users\mridu\aivoice
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000

### Step 6: Start the Frontend

Open a **new terminal**:

```bash
cd c:\Users\mridu\aivoice
streamlit run frontend/app.py
```

Frontend will open at: http://localhost:8501

---

## 🎯 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload_pdf` | Upload and index a PDF |
| `POST` | `/ask_text` | Ask a question via text |
| `POST` | `/ask_voice` | Ask a question via voice audio |
| `POST` | `/tts_generate` | Generate speech from text |
| `POST` | `/clear_db` | Clear database and files |
| `GET`  | `/health` | Health check |
| `GET`  | `/pdfs` | List indexed PDFs |
| `GET`  | `/audio/{filename}` | Serve audio file |

---

## 💡 Sample Questions

After uploading an NCERT Biology PDF:

- *"What is photosynthesis?"*
- *"Explain the structure of a cell."*
- *"What are the different types of tissues?"*
- *"Describe the process of digestion in humans."*

---

## 🔊 TTS Details

### Primary: Coqui TTS
- Models: `tacotron2-DDC`, `glow-tts`
- Output: `.wav` format
- Neural voice quality
- First run downloads the model (~200MB)

### Fallback: gTTS
- Uses Google Translate TTS
- Output: `.mp3` format
- Requires internet connection
- Activates automatically if Coqui fails

### Caching
- Audio files are named `audio_{md5_hash}.wav/mp3`
- Same answer text reuses existing audio — no regeneration

---

## 🔧 Troubleshooting

### Coqui TTS Issues

1. **Installation fails:**
   ```bash
   pip install TTS --no-cache-dir
   ```
   On Windows, you may need Visual C++ Build Tools.

2. **Model download hangs:** Check your internet connection. Models are downloaded on first use.

3. **CUDA/GPU errors:** The project uses CPU by default. If you have GPU issues:
   ```bash
   pip install torch --index-url https://download.pytorch.org/whl/cpu
   ```

4. **Coqui fails at runtime:** The system automatically falls back to gTTS. Check logs in `logs/app.log`.

### Gemini API Issues

1. **API Key not set:** Ensure `GEMINI_API_KEY` environment variable is configured.
2. **Invalid API key:** Verify your API key from Google AI Studio is correct.
3. **Quota exceeded:** Check your API usage limits at [Google AI Studio](https://aistudio.google.com/).
4. **Network errors:** Ensure you have a stable internet connection.

### FAISS Issues

1. Use `faiss-cpu` (not `faiss-gpu`) unless you have CUDA.
2. If index fails to load, use the "Clear Database" button and re-upload PDFs.

---

## 🧠 Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI + Uvicorn |
| PDF Parsing | pdfplumber |
| Chunking | LangChain Text Splitters |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector DB | FAISS |
| LLM | Google Gemini API (gemini-1.5-flash) |
| TTS Primary | Coqui TTS |
| TTS Fallback | gTTS |
| STT | OpenAI Whisper |
| Frontend | Streamlit |

---

## 📄 License

This project is for educational purposes.
