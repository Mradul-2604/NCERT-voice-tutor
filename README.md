# NCERT Voice Tutor

**PDF → RAG → Answer → TTS Output**

An intelligent voice tutor that lets you upload NCERT PDFs, ask questions in a chat interface, and receive spoken answers using high-quality Text-to-Speech.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     STREAMLIT FRONTEND                          │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌───────────┐  │
│  │ PDF      │  │ Text         │  │ Answer   │  │ Audio     │  │
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
│  │         TTS ENGINES             │                            │
│  │  ElevenLabs  (premium, 5 voices)│                            │
│  │  gTTS        (free, online)     │                            │
│  │  pyttsx3     (offline)          │                            │
│  └─────────────────────────────────┘                            │
│                                                                 │
│  ┌──────────┐  ┌────────┐  ┌────────┐                          │
│  │ FAISS    │  │ Gemini │  │ Cache  │                          │
│  │ Index    │  │  API   │  │ Layer  │                          │
│  └──────────┘  └────────┘  └────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
aivoice/
├── backend/
│   ├── main.py                  # FastAPI app with all endpoints
│   ├── rag/
│   │   ├── pdf_loader.py        # PDF text extraction (pdfplumber)
│   │   ├── chunker.py           # Text chunking (rule-based + agentic)
│   │   ├── agentic_chunker.py   # Gemini-powered paragraph merging
│   │   ├── embedder.py          # Sentence-transformer embeddings
│   │   ├── vector_store.py      # FAISS index management
│   │   ├── retriever.py         # Similarity search + filtering
│   │   └── generator.py         # Gemini API answer generation
│   ├── speech/
│   │   ├── tts_manager.py       # TTS orchestration + fallback
│   │   ├── tts_elevenlabs.py    # ElevenLabs TTS (premium)
│   │   ├── tts_gtts.py          # gTTS (free, online)
│   │   └── tts_coqui.py         # pyttsx3 (offline)
│   └── utils/
│       ├── logger.py            # Centralized logging
│       └── cache.py             # Audio hash-based caching
├── frontend/
│   └── app.py                   # Streamlit chat UI
├── data/
│   ├── pdfs/                    # Uploaded PDFs
│   ├── extracted_text/          # Extracted raw text
│   └── audio_outputs/           # Generated audio files
├── vector_store/
│   └── faiss_index/             # FAISS index files
├── logs/                        # Application logs
├── .env.example                 # Environment variable template
├── requirements.txt
└── README.md
```

---

## Setup Instructions

### Prerequisites

- Python 3.10+
- pip
- Google Gemini API Key (free from [Google AI Studio](https://aistudio.google.com/app/apikey))
- ElevenLabs API Key (optional, for premium TTS from [elevenlabs.io](https://elevenlabs.io))

### Step 1: Clone the Repository

```bash
git clone https://github.com/Mradul-2604/NCERT-voice-tutor.git
cd NCERT-voice-tutor
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

### Step 4: Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
GEMINI_API_KEY=your-gemini-api-key-here
ELEVENLABS_API_KEY=your-elevenlabs-key-here   # optional
ENABLE_AGENTIC_CHUNKING=true                  # or false for simple chunking
```

### Step 5: Start the Backend

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Backend available at: http://localhost:8000

### Step 6: Start the Frontend

Open a **new terminal**:

```bash
streamlit run frontend/app.py
```

Frontend opens at: http://localhost:8501

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload_pdf` | Upload and index a PDF |
| `POST` | `/ask_text` | Ask a question via text |
| `POST` | `/tts_generate` | Generate speech from text |
| `POST` | `/clear_db` | Clear database and files |
| `GET`  | `/health` | Health check |
| `GET`  | `/pdfs` | List indexed PDFs |
| `GET`  | `/audio/{filename}` | Serve audio file |

---

## TTS Engines

### ElevenLabs (Premium)
- 5 voices: Rachel, Adam, Bella, Josh, Elli
- Model: `eleven_multilingual_v2`
- Output: `.mp3` format
- Requires API key

### gTTS (Free, Online)
- Uses Google Translate TTS
- Output: `.mp3` format
- Requires internet connection

### pyttsx3 (Offline)
- Uses system speech engine (SAPI5 on Windows)
- 3 voices: default, male, female
- Output: `.wav` format

### Fallback Chain
```
ElevenLabs → (fails?) → gTTS
pyttsx3    → (fails?) → gTTS
```

### Audio Caching
- Audio files are named `audio_{md5_hash}.wav/mp3`
- Same answer text reuses existing audio — no regeneration

---

## Chunking Modes

| Mode | Config | How it works |
|------|--------|-------------|
| **Rule-based** | `ENABLE_AGENTIC_CHUNKING=false` | Splits every 800 chars with 150 overlap |
| **Agentic** | `ENABLE_AGENTIC_CHUNKING=true` | Gemini merges related paragraphs (max 1200 chars) |

---

## Sample Questions

After uploading an NCERT PDF:

- *"What is photosynthesis?"*
- *"Explain the structure of a cell."*
- *"What are the different types of tissues?"*
- *"Describe the process of digestion in humans."*

---

## Troubleshooting

### Gemini API Issues
1. **API Key not set:** Add `GEMINI_API_KEY` to your `.env` file.
2. **Invalid API key:** Verify at [Google AI Studio](https://aistudio.google.com/).
3. **Quota exceeded:** Check your API usage limits.

### TTS Issues
1. **ElevenLabs not working:** Verify your API key. Falls back to gTTS automatically.
2. **gTTS fails:** Check your internet connection.
3. **pyttsx3 issues:** Falls back to gTTS automatically.

### FAISS Issues
1. Use `faiss-cpu` (not `faiss-gpu`) unless you have CUDA.
2. If index fails to load, use "Clear All" and re-upload PDFs.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI + Uvicorn |
| Frontend | Streamlit |
| PDF Parsing | pdfplumber |
| Chunking | LangChain Text Splitters + Gemini (agentic) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector DB | FAISS (IndexFlatL2) |
| LLM | Google Gemini API |
| TTS Premium | ElevenLabs |
| TTS Free | gTTS |
| TTS Offline | pyttsx3 |

---

## License

This project is for educational purposes.
