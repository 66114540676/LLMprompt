# Local Coding Assistant

A chat-style coding assistant that runs entirely on your own machine. It answers coding questions with a local LLM (`qwen2.5-coder:7b` via Ollama) and grounds its answers in a code dataset using Hybrid RAG (vector search + BM25).

- Demo video (YouTube, under 5 min): `<YOUTUBE_LINK>`
- Dataset (static link): `<DATASET_LINK>`
- Source code: `<GOOGLE_DRIVE_OR_GIT_LINK>`

## Features

- Chat UI (Streamlit) with multiple chat sessions saved to `chat_sessions.json`
- Three retrieval modes, selectable in **Settings**:
  - **Vector**: semantic search (FAISS + `nomic-embed-text` embeddings)
  - **BM25**: keyword search
  - **Hybrid** (default): merges Vector and BM25 rankings with Reciprocal Rank Fusion
- **Sources** panel under each answer shows exactly which code snippets were given to the model
- Streaming answers
- Attachments: code/text files and PDFs are added to the model's context; images are described by a vision model first, then passed to the coding model

## Requirements

- Python 3.10 or newer
- [Ollama](https://ollama.com) installed
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Roughly 6 GB of free RAM/VRAM for the 7B model

## How to Run

1. **Start Ollama.** The desktop app runs it in the background; otherwise run `ollama serve` in a separate terminal.

2. **Download the models** (one time):
   ```bash
   ollama pull qwen2.5-coder:7b
   ollama pull nomic-embed-text
   ollama pull qwen2.5vl:3b      # optional, only needed for image attachments
   ```

3. **Install dependencies:**
   ```bash
   uv sync
   ```
   Without uv:
   ```bash
   pip install "streamlit>=1.43" langchain-community faiss-cpu rank_bm25 ollama pypdf
   ```

4. **Launch the app:**
   ```bash
   uv run streamlit run lab_13_app.py
   ```
   Without uv: `streamlit run lab_13_app.py`. The app opens at http://localhost:8501.

The first question is slower because the model has to load into memory.

## How It Works

1. On startup, every file in `dataset/` is split into chunks (Python files by function/class, other files in 40-line blocks) and indexed for both vector search and BM25.
2. When you ask a question, the top 3 chunks are retrieved using the selected mode.
3. The chunks and your question are sent to `qwen2.5-coder:7b`, and the answer streams back. The chunks are listed under **Sources**.

If `dataset/` is missing or empty, three small built-in sample snippets are used instead. After changing files in `dataset/`, restart the app to rebuild the index.

## Project Structure

```
├── lab_13_app.py               # Streamlit UI
├── lab_12_hybrid_rag.py        # Dataset loader + Hybrid RAG (FAISS, BM25, RRF)
├── lab_13_coding_assistant.py  # Prompt + streaming call to Ollama
├── dataset/                    # Code dataset used as the knowledge base
├── .streamlit/config.toml      # Optional dark theme
└── pyproject.toml
```

Created at runtime: `chat_sessions.json` (chat history) and `chat_uploads/` (attached images).

## Using Attachments

Click the paperclip in the input box.

- Text/code: `.py .txt .md .json .csv .js .ts .html .css .java .c .cpp .sql`, plus `.pdf` (text-based PDFs only, not scans). Each file is truncated to 6,000 characters.
- Images: `.png .jpg .jpeg .webp`, read by `qwen2.5vl:3b`.
- An attachment applies only to the message it is sent with.

## Configuration

| Setting | Where |
|---|---|
| Coding model (`LLM_MODEL`) | `lab_13_coding_assistant.py` |
| Embedding model (`EMBED_MODEL`) | `lab_12_hybrid_rag.py` |
| Vision model (`VISION_MODEL`), dataset folder (`DATASET_DIR`) | `lab_13_app.py` |

## Test Data

The dataset is in `dataset/` and also available at the static link above. Example questions to try:

- `<QUESTION_1_ABOUT_YOUR_DATASET>`
- `<QUESTION_2_ABOUT_YOUR_DATASET>`
- `<QUESTION_3_ABOUT_YOUR_DATASET>`

Ask the same question in Vector, BM25 and Hybrid modes and compare the **Sources**.

## Limitations

- Each question is answered on its own; the model does not see earlier messages in the chat.
- BM25 matches exact words and does not handle Thai keywords (Hybrid falls back to vector search).
- Response speed depends on your hardware. Image attachments are slower because two models run in sequence.

## Troubleshooting

| Problem | Fix |
|---|---|
| "เรียกโมเดลไม่สำเร็จ" or connection error | Start Ollama, and check that both `qwen2.5-coder:7b` and `nomic-embed-text` are installed (`ollama list`) |
| Image attachment says the vision model is missing | `ollama pull qwen2.5vl:3b` |
| PDF cannot be read | `pip install pypdf` (or `uv sync`) |
| No paperclip button in the input box | Upgrade Streamlit: `pip install -U streamlit` |
| Very slow answers | Check `ollama ps`; if the model is not fully on GPU, try a smaller model such as `qwen2.5-coder:3b` |