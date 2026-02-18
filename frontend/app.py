"""
NCERT Voice Tutor — Streamlit Frontend
ChatGPT/Gemini-style chat interface.
"""

import os
import requests
import streamlit as st

# ─── Configuration ───────────────────────────────────────────────────────────

API_BASE = "http://localhost:8000"
AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "audio_outputs")

# ─── Page Config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="NCERT Voice Tutor",
    page_icon="",
    layout="centered",
    initial_sidebar_state="auto",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, p, span, div, input, textarea, button, label, h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif;
    }

    /* Hide defaults */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    .block-container {
        padding-top: 1rem;
        padding-bottom: 6rem;
        max-width: 800px;
    }

    /* Brand header */
    .brand {
        text-align: center;
        padding: 2rem 0 0.5rem;
    }
    .brand-name {
        font-size: 1.6rem;
        font-weight: 700;
        color: #e2e8f0;
        letter-spacing: -0.5px;
    }
    .brand-sub {
        font-size: 0.85rem;
        color: #64748b;
        margin-top: 0.25rem;
    }

    /* Chat messages */
    .user-msg {
        background: #2563eb;
        color: #fff;
        border-radius: 18px 18px 4px 18px;
        padding: 12px 18px;
        margin: 0.75rem 0;
        max-width: 80%;
        margin-left: auto;
        font-size: 0.95rem;
        line-height: 1.5;
        word-wrap: break-word;
    }
    .bot-msg {
        background: #1e293b;
        color: #e2e8f0;
        border-radius: 18px 18px 18px 4px;
        padding: 16px 20px;
        margin: 0.75rem 0;
        max-width: 90%;
        font-size: 0.95rem;
        line-height: 1.7;
        word-wrap: break-word;
    }
    .bot-msg strong, .bot-msg b {
        color: #93c5fd;
    }

    /* Source pills */
    .source-pill {
        display: inline-block;
        background: #334155;
        color: #94a3b8;
        border-radius: 6px;
        padding: 4px 10px;
        margin: 3px 4px 3px 0;
        font-size: 0.75rem;
        font-weight: 500;
    }
    .sources-row {
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid #334155;
    }

    /* Upload area */
    .upload-banner {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 2rem 1.5rem;
        text-align: center;
        margin: 1rem 0;
    }
    .upload-banner-title {
        font-size: 1rem;
        font-weight: 600;
        color: #e2e8f0;
        margin-bottom: 0.25rem;
    }
    .upload-banner-sub {
        font-size: 0.8rem;
        color: #64748b;
    }

    /* Chunk preview */
    .chunk-preview {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 12px;
        margin: 6px 0;
        font-size: 0.85rem;
        color: #94a3b8;
        line-height: 1.5;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #0f172a;
    }
    section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
        color: #e2e8f0;
    }

    /* Audio player area */
    .audio-section {
        background: #1e293b;
        border-radius: 10px;
        padding: 12px 16px;
        margin: 8px 0;
    }

    /* Welcome cards */
    .welcome-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin: 1.5rem 0;
    }
    .welcome-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px;
        cursor: default;
        transition: border-color 0.2s;
    }
    .welcome-card:hover {
        border-color: #475569;
    }
    .welcome-card-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #e2e8f0;
        margin-bottom: 4px;
    }
    .welcome-card-desc {
        font-size: 0.78rem;
        color: #64748b;
        line-height: 1.4;
    }
</style>
""", unsafe_allow_html=True)


# ─── Helper Functions ────────────────────────────────────────────────────────

def upload_pdf(file):
    """Upload a PDF to the backend."""
    try:
        files = {"file": (file.name, file.getvalue(), "application/pdf")}
        resp = requests.post(f"{API_BASE}/upload_pdf", files=files, timeout=300)
        return resp.json() if resp.status_code == 200 else {"error": resp.text}
    except Exception as e:
        return {"error": str(e)}


def ask_question(question, pdf_filter=None, tts_engine="gtts", tts_model="default", speed=1.0):
    """Send a text question to the backend."""
    try:
        payload = {
            "question": question,
            "pdf_filter": pdf_filter,
            "tts_engine": tts_engine,
            "tts_model": tts_model,
            "speed": speed,
        }
        resp = requests.post(f"{API_BASE}/ask_text", json=payload, timeout=180)
        return resp.json() if resp.status_code == 200 else {"error": resp.text}
    except Exception as e:
        return {"error": str(e)}


def clear_database():
    """Clear the backend database."""
    try:
        resp = requests.post(f"{API_BASE}/clear_db", timeout=30)
        return resp.json() if resp.status_code == 200 else {"error": resp.text}
    except Exception as e:
        return {"error": str(e)}


def get_indexed_pdfs():
    """Get list of indexed PDFs."""
    try:
        resp = requests.get(f"{API_BASE}/pdfs", timeout=10)
        if resp.status_code == 200:
            return resp.json().get("pdfs", [])
    except Exception:
        pass
    return []


# ─── Session State ───────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pdf_uploaded" not in st.session_state:
    st.session_state.pdf_uploaded = False


# ─── Sidebar (minimal settings) ─────────────────────────────────────────────

with st.sidebar:
    st.markdown("## Settings")

    st.markdown("### TTS Engine")
    tts_engine = st.selectbox(
        "Engine",
        ["gtts", "elevenlabs", "coqui"],
        index=0,
        label_visibility="collapsed",
        help="gTTS: free online | ElevenLabs: premium quality | coqui: offline",
    )

    tts_model = "default"
    if tts_engine == "elevenlabs":
        tts_model = st.selectbox(
            "Voice",
            ["rachel", "adam", "bella", "josh", "elli"],
            index=0,
            help="Rachel: calm | Adam: deep | Bella: warm | Josh: dynamic | Elli: young",
        )
    elif tts_engine == "coqui":
        tts_model = st.selectbox("Voice", ["default", "male", "female"], index=0)


    st.markdown("---")

    if st.button("Clear All", use_container_width=True):
        with st.spinner("Clearing..."):
            clear_database()
        st.session_state.messages = []
        st.rerun()


# ─── Main Area ───────────────────────────────────────────────────────────────

# Brand
st.markdown(
    '<div class="brand">'
    '<div class="brand-name">NCERT Voice Tutor</div>'
    '<div class="brand-sub">Ask questions from your NCERT textbooks</div>'
    '</div>',
    unsafe_allow_html=True,
)

# PDF upload section (always visible)
st.markdown("---")
uploaded_file = st.file_uploader(
    "Upload your NCERT PDF",
    type=["pdf"],
)

if uploaded_file:
    if st.button("Upload & Index", type="primary", use_container_width=True):
        with st.spinner("Extracting and indexing..."):
            result = upload_pdf(uploaded_file)

        if "error" in result:
            st.error(f"Failed: {result['error']}")
        else:
            st.success(
                f"Indexed **{result.get('chunks_indexed', 0)}** chunks "
                f"from **{result.get('pages_extracted', 0)}** pages"
            )
            st.rerun()
st.markdown("---")


# ─── Welcome Screen (when no messages) ──────────────────────────────────────

# Show a subtle prompt when no messages yet
if not st.session_state.messages:
    st.markdown(
        '<p style="text-align:center; color:#64748b; margin-top:3rem;">'
        'Upload a PDF and start asking questions below'
        '</p>',
        unsafe_allow_html=True,
    )


# ─── Chat History ────────────────────────────────────────────────────────────

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-msg">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="bot-msg">{msg["content"]}</div>', unsafe_allow_html=True)

        # Audio
        if msg.get("audio_path") and os.path.exists(msg["audio_path"]):
            with open(msg["audio_path"], "rb") as af:
                audio_bytes = af.read()
            audio_fmt = "audio/wav" if msg["audio_path"].endswith(".wav") else "audio/mp3"
            st.audio(audio_bytes, format=audio_fmt)

        # Sources
        if msg.get("sources"):
            sources_html = '<div class="sources-row">'
            for src in msg["sources"]:
                sources_html += (
                    f'<span class="source-pill">'
                    f'{src.get("pdf", "")} — Page {src.get("page", "?")}'
                    f'</span>'
                )
            sources_html += '</div>'
            st.markdown(sources_html, unsafe_allow_html=True)


# ─── Chat Input ──────────────────────────────────────────────────────────────

question = st.chat_input("Ask a question about your NCERT textbook...")

if question:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": question})
    st.markdown(f'<div class="user-msg">{question}</div>', unsafe_allow_html=True)

    # Get answer
    with st.spinner(""):
        result = ask_question(
            question=question,
            tts_engine=tts_engine,
            tts_model=tts_model,
        )

    if "error" in result:
        error_msg = f"Something went wrong: {result['error']}"
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        st.markdown(f'<div class="bot-msg">{error_msg}</div>', unsafe_allow_html=True)
    else:
        answer = result.get("answer", "No answer generated.")
        audio_path = result.get("audio_file", "")
        sources = result.get("sources", [])

        # Store message
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "audio_path": audio_path,
            "sources": sources,
        })

        # Display
        st.markdown(f'<div class="bot-msg">{answer}</div>', unsafe_allow_html=True)

        # Audio
        if audio_path and os.path.exists(audio_path):
            with open(audio_path, "rb") as af:
                audio_bytes = af.read()
            audio_fmt = "audio/wav" if audio_path.endswith(".wav") else "audio/mp3"
            st.audio(audio_bytes, format=audio_fmt)

        # Sources
        if sources:
            sources_html = '<div class="sources-row">'
            for src in sources:
                sources_html += (
                    f'<span class="source-pill">'
                    f'{src.get("pdf", "")} — Page {src.get("page", "?")}'
                    f'</span>'
                )
            sources_html += '</div>'
            st.markdown(sources_html, unsafe_allow_html=True)
