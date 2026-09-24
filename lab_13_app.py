import base64
import io
import itertools
import json
import os
import time
import urllib.error
import urllib.request

import streamlit as st

from lab_12_hybrid_rag import EMBED_MODEL, HybridRAG, load_chunks
from lab_13_coding_assistant import LLM_MODEL, stream_response

DATASET_DIR = "dataset"  # โฟลเดอร์ข้อมูลโค้ดที่ใช้เป็นฐานความรู้ของ RAG
RETRIEVAL_MODES = ["Vector", "BM25", "Hybrid"]
SAMPLE_DOCS = [  # ใช้ก็ต่อเมื่อไม่พบไฟล์ในโฟลเดอร์ dataset
    "def add(a, b):\n    return a + b",
    "def multiply(a, b):\n    return a * b",
    "class Calculator:\n    def __init__(self):\n        pass",
]
SESSIONS_FILE = "chat_sessions.json"

# --- แนบไฟล์ / รูปภาพ ---
VISION_MODEL = "qwen2.5vl:3b"  # โมเดลอ่านรูป (ต้อง `ollama pull qwen2.5vl:3b` ก่อน)
OLLAMA_URL = "http://localhost:11434"
UPLOAD_DIR = "chat_uploads"
MAX_DOC_CHARS = 6000  # จำกัดความยาวต่อไฟล์ เพื่อไม่ให้ prompt ยาวจนช้า
DOC_TYPES = ["py", "txt", "md", "json", "csv", "js", "ts", "html", "css", "java", "c", "cpp", "sql", "pdf"]
IMAGE_TYPES = ["png", "jpg", "jpeg", "webp"]

SUGGESTIONS = [
    "เขียนฟังก์ชันบวกเลขสองตัว พร้อมอธิบาย",
    "อธิบาย class Calculator ทีละบรรทัด",
    "เขียน unit test ให้ฟังก์ชัน multiply",
    "เขียน decorator สำหรับ retry เมื่อเกิด error",
]

st.set_page_config(page_title="Coding Assistant", page_icon="✨", layout="wide")

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Thai:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg: #0F131A;
    --side: #0B0E14;
    --surface: #171C25;
    --line: #262E3B;
    --text: #E2E8F0;
    --muted: #8390A3;
    --accent: #7F95FF;
    --accent-soft: rgba(127, 149, 255, .14);
    --accent-line: rgba(127, 149, 255, .28);
}

/* ---------- Base ---------- */
.stApp, .stApp p, .stApp li, .stApp label, .stApp button, .stApp textarea,
.stApp input, .stApp h1, .stApp h2, .stApp h3,
.stApp [data-testid="stMarkdownContainer"] {
    font-family: 'IBM Plex Sans Thai', system-ui, sans-serif;
}
.stApp code, .stApp pre, .stApp pre * {
    font-family: 'JetBrains Mono', ui-monospace, monospace;
}
.stApp { background: var(--bg); color: var(--text); }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stAppDeployButton"], #MainMenu, footer { display: none !important; }
.block-container { max-width: 820px; padding-top: 2.5rem; padding-bottom: 8rem; }

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] { background: var(--side); border-right: 1px solid var(--line); }
.brand {
    display: flex; align-items: center; gap: .55rem;
    font-size: 1.15rem; font-weight: 600; letter-spacing: -.01em;
    padding: .25rem 0 1rem;
}
.brand span { color: var(--accent); font-size: 1.3rem; }
.side-label { color: var(--muted); font-size: .8rem; padding: 1.1rem .2rem .35rem; }

[data-testid="stSidebar"] .stButton button {
    width: 100%; justify-content: flex-start; text-align: left;
    background: transparent; color: var(--muted);
    border: 1px solid transparent; border-radius: 10px;
    padding: .45rem .7rem; min-height: 0; font-weight: 400;
    transition: background .15s, color .15s;
}
[data-testid="stSidebar"] .stButton button:hover {
    background: var(--surface); color: var(--text); border-color: transparent;
}
[data-testid="stSidebar"] .stButton button[kind="primary"],
[data-testid="stSidebar"] .stButton button[data-testid="stBaseButton-primary"] {
    background: var(--accent-soft); color: var(--text); border-color: var(--accent-line);
}
.st-key-new_chat button {
    justify-content: center !important;
    background: var(--surface) !important; color: var(--text) !important;
    border: 1px solid var(--line) !important; font-weight: 500 !important;
}
.st-key-new_chat button:hover { border-color: var(--accent) !important; }
[class*="st-key-del_"] button { justify-content: center !important; padding-left: 0 !important; padding-right: 0 !important; }
[class*="st-key-del_"] button:hover { color: #FF7A85 !important; }

[data-testid="stSidebar"] [data-testid="stExpander"] { border: 1px solid var(--line); border-radius: 12px; background: transparent; }

/* ---------- Empty state ---------- */
.hero { text-align: center; padding: 13vh 0 2rem; }
.hero-title { font-size: 2.1rem; font-weight: 600; letter-spacing: -.02em; margin-bottom: .5rem; }
.hero-sub { color: var(--muted); }

[data-testid="stMain"] .stButton button, section.main .stButton button {
    width: 100%; height: 100%; justify-content: flex-start; text-align: left;
    background: var(--surface); color: var(--text);
    border: 1px solid var(--line); border-radius: 14px;
    padding: .9rem 1rem; font-weight: 400; line-height: 1.5;
    transition: border-color .15s, background .15s;
}
[data-testid="stMain"] .stButton button:hover, section.main .stButton button:hover {
    border-color: var(--accent); background: var(--accent-soft); color: var(--text);
}

/* ---------- Messages ---------- */
[data-testid="stChatMessage"] {
    background: transparent; padding: .45rem 0; gap: .8rem; align-items: flex-start;
}
[data-testid="stChatMessageContent"] { line-height: 1.75; }

[data-testid="stChatMessageAvatarAssistant"] {
    background: var(--accent); color: #0B1020; border-radius: 10px;
}
[data-testid="stChatMessageAvatarUser"] { display: none; }

/* ข้อความของผู้ใช้: ชิดขวาเป็นบับเบิล */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    flex-direction: row-reverse;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
    flex: 0 1 auto; width: fit-content; max-width: 80%;
    background: var(--accent-soft); border: 1px solid var(--accent-line);
    border-radius: 18px 18px 4px 18px; padding: .65rem 1rem;
}

/* ---------- Code / sources ---------- */
[data-testid="stCode"], [data-testid="stCodeBlock"] { border: 1px solid var(--line); border-radius: 12px; }
[data-testid="stMain"] [data-testid="stExpander"], section.main [data-testid="stExpander"] {
    border: 1px solid var(--line); border-radius: 12px; background: transparent;
}

/* ---------- Input ---------- */
[data-testid="stBottom"] > div { background: var(--bg); }
[data-testid="stChatInput"] {
    background: var(--surface); border: 1px solid var(--line); border-radius: 18px;
}
[data-testid="stChatInput"] > div { background: transparent; border: none; }
[data-testid="stChatInput"]:focus-within {
    border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft);
}
[data-testid="stChatInput"] textarea { color: var(--text); }

@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def load_all_sessions():
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_all_sessions(sessions):
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)


def new_session():
    """สร้างแชทใหม่ แล้วตั้งเป็นแชทปัจจุบัน"""
    sid = str(time.time_ns())  # ใช้ nanosecond กัน id ซ้ำ
    st.session_state.sessions[sid] = {"title": "New Chat", "messages": []}
    st.session_state.current_session_id = sid


def render_sources(sources):
    if sources:
        with st.expander("Sources"):
            st.code(sources, language="python")


def is_image(name):
    return name.lower().rsplit(".", 1)[-1] in IMAGE_TYPES


def read_document(uploaded):
    """อ่านข้อความจากไฟล์ที่แนบ (ไฟล์ข้อความทั่วไป หรือ PDF)"""
    data = uploaded.getvalue()
    if uploaded.name.lower().endswith(".pdf"):
        try:
            from pypdf import PdfReader
        except ImportError:
            raise RuntimeError("อ่าน PDF ไม่ได้ เพราะยังไม่ได้ติดตั้ง pypdf (รัน `pip install pypdf`)")
        reader = PdfReader(io.BytesIO(data))
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
    else:
        text = data.decode("utf-8", errors="replace")

    text = text.strip()
    if not text:
        raise RuntimeError(f"ไม่พบข้อความในไฟล์ `{uploaded.name}` (ถ้าเป็น PDF สแกน จะอ่านไม่ได้)")
    if len(text) > MAX_DOC_CHARS:
        text = text[:MAX_DOC_CHARS] + "\n... (ตัดส่วนที่เหลือออก)"
    return text


def save_image(uploaded):
    """เก็บรูปลงโฟลเดอร์ เพื่อให้แสดงในประวัติแชทได้"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    path = os.path.join(UPLOAD_DIR, f"{time.time_ns()}_{os.path.basename(uploaded.name)}")
    with open(path, "wb") as f:
        f.write(uploaded.getvalue())
    return path


def describe_image(image_bytes, question):
    """ให้โมเดลอ่านรูป (ผ่าน Ollama) แล้วคืนคำบรรยายเป็นข้อความ"""
    payload = {
        "model": VISION_MODEL,
        "stream": False,
        "messages": [{
            "role": "user",
            "content": (
                "Describe this image in detail. Transcribe any code or text exactly as it appears. "
                f"The user's question about it is: {question}"
            ),
            "images": [base64.b64encode(image_bytes).decode()],
        }],
    }
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read())["message"]["content"].strip()


def stop_with_error(message):
    save_all_sessions(st.session_state.sessions)
    st.error(message)
    st.stop()


def render_message(msg):
    avatar = "✨" if msg["role"] == "assistant" else "🧑‍💻"
    with st.chat_message(msg["role"], avatar=avatar):
        for path in msg.get("images", []):
            if os.path.exists(path):
                try:
                    st.image(path, width=260)
                except Exception:  # ไฟล์รูปเสียหรืออ่านไม่ได้
                    st.caption(f"🖼️ {os.path.basename(path)}")
        if msg.get("files"):
            st.caption("📎 " + ", ".join(msg["files"]))
        st.markdown(msg["content"])
        render_sources(msg.get("sources"))


@st.cache_resource(show_spinner="กำลังสร้างดัชนีเอกสาร...")
def get_rag():
    """สร้าง RAG ครั้งเดียวแล้วใช้ร่วมกันทุกแชท (ไม่ต้อง embed ใหม่ทุกครั้งที่เปิดหน้า)"""
    return HybridRAG(load_chunks(DATASET_DIR) or SAMPLE_DOCS)


def set_pending_prompt(text):
    st.session_state.pending_prompt = text


# ---------------------------------------------------------------------------
# Init state
# ---------------------------------------------------------------------------
if "sessions" not in st.session_state:
    st.session_state.sessions = load_all_sessions()

if not st.session_state.sessions:
    new_session()
    save_all_sessions(st.session_state.sessions)
elif st.session_state.get("current_session_id") not in st.session_state.sessions:
    # เปิดแชทล่าสุดเป็นค่าเริ่มต้น
    st.session_state.current_session_id = list(st.session_state.sessions.keys())[-1]

if "retrieval_mode" not in st.session_state:
    st.session_state.retrieval_mode = "Hybrid"

current_id = st.session_state.current_session_id

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="brand"><span>✦</span>Coding Assistant</div>', unsafe_allow_html=True)

    if st.button("＋  New chat", key="new_chat"):
        # ถ้าแชทปัจจุบันยังว่างอยู่ ไม่ต้องสร้างซ้ำ
        if st.session_state.sessions[current_id]["messages"]:
            new_session()
            save_all_sessions(st.session_state.sessions)
        st.rerun()

    st.markdown('<div class="side-label">Chats</div>', unsafe_allow_html=True)

    for s_id, s_data in reversed(list(st.session_state.sessions.items())):
        title = (s_data.get("title") or "Chat")[:24]
        is_active = s_id == current_id

        col_title, col_del = st.columns([5, 1], gap="small")
        with col_title:
            if st.button(title, key=f"chat_{s_id}", type="primary" if is_active else "secondary"):
                st.session_state.current_session_id = s_id
                st.rerun()
        with col_del:
            if st.button("✕", key=f"del_{s_id}"):
                del st.session_state.sessions[s_id]
                if not st.session_state.sessions:
                    new_session()
                elif is_active:
                    st.session_state.current_session_id = list(st.session_state.sessions.keys())[-1]
                save_all_sessions(st.session_state.sessions)
                st.rerun()

    st.markdown('<div class="side-label">&nbsp;</div>', unsafe_allow_html=True)
    with st.expander("Settings"):
        st.selectbox("Retrieval mode", RETRIEVAL_MODES, key="retrieval_mode")
        st.caption(f"LLM: `{LLM_MODEL}`")
        st.caption(f"Embedding: `{EMBED_MODEL}`")
        st.caption(f"Vision: `{VISION_MODEL}`")
        if st.button("Clear all chats", key="clear_all"):
            st.session_state.sessions = {}
            new_session()
            save_all_sessions(st.session_state.sessions)
            st.rerun()

# ---------------------------------------------------------------------------
# Main chat area
# ---------------------------------------------------------------------------
current_messages = st.session_state.sessions[current_id]["messages"]

# อ่านข้อความจากปุ่มแนะนำ (ถ้ามี) หรือจากช่องพิมพ์
pending = st.session_state.pop("pending_prompt", None)
try:
    typed = st.chat_input(
        "Ask a coding question...",
        accept_file="multiple",
        file_type=DOC_TYPES + IMAGE_TYPES,
    )
except TypeError:  # Streamlit เวอร์ชันเก่าที่ยังไม่มี accept_file
    typed = st.chat_input("Ask a coding question...")

user_prompt, attachments = None, []
if typed:
    if isinstance(typed, str):
        user_prompt = typed
    else:
        user_prompt = (typed.text or "").strip()
        attachments = list(typed.files or [])
        if attachments and not user_prompt:
            user_prompt = "อธิบายไฟล์หรือรูปที่แนบมา"
elif pending:
    user_prompt = pending

if not current_messages and not user_prompt:
    st.markdown(
        f'<div class="hero">'
        f'<div class="hero-title">ถามเรื่องโค้ดได้เลย</div>'
        f'<div class="hero-sub">ทำงานบนเครื่องของคุณด้วย {LLM_MODEL}<br>แนบไฟล์โค้ด, PDF หรือรูปภาพได้ที่ไอคอนคลิปในช่องพิมพ์</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(2)
    for i, text in enumerate(SUGGESTIONS):
        cols[i % 2].button(text, key=f"sug_{i}", on_click=set_pending_prompt, args=(text,))

for msg in current_messages:
    render_message(msg)

if user_prompt:
    images = [f for f in attachments if is_image(f.name)]
    docs = [f for f in attachments if not is_image(f.name)]

    user_msg = {"role": "user", "content": user_prompt}
    if docs:
        user_msg["files"] = [f.name for f in docs]
    if images:
        user_msg["images"] = [save_image(f) for f in images]
    current_messages.append(user_msg)

    is_first_message = len(current_messages) == 1
    if is_first_message:
        short = user_prompt[:28]
        st.session_state.sessions[current_id]["title"] = short + ("…" if len(user_prompt) > 28 else "")

    render_message(user_msg)

    with st.chat_message("assistant", avatar="✨"):
        # 1) อ่านเอกสารที่แนบ
        extra_context = []
        try:
            for f in docs:
                extra_context.append(f"# File: {f.name}\n{read_document(f)}")
        except RuntimeError as e:
            stop_with_error(str(e))

        # 2) ให้โมเดลอ่านรูปที่แนบ
        for f in images:
            try:
                with st.spinner("กำลังอ่านรูปภาพ..."):
                    description = describe_image(f.getvalue(), user_prompt)
            except urllib.error.HTTPError:
                stop_with_error(
                    f"ไม่พบโมเดลอ่านรูป `{VISION_MODEL}` ในเครื่อง\n\n"
                    f"รันคำสั่งนี้ก่อน: `ollama pull {VISION_MODEL}`"
                )
            except OSError:
                stop_with_error("เชื่อมต่อ Ollama ไม่ได้ ตรวจสอบว่า Ollama เปิดอยู่")
            except Exception as e:
                stop_with_error(f"อ่านรูป `{f.name}` ไม่สำเร็จ: {e}")
            extra_context.append(f"# Image: {f.name}\n{description}")

        # 3) ค้นหา + ตอบ (stream จริงจาก Ollama)
        try:
            with st.spinner("กำลังค้นหาและคิดคำตอบ..."):
                retrieved = get_rag().search(user_prompt)
                context = extra_context + retrieved[st.session_state.retrieval_mode.lower()]
                sources = "\n---\n".join(context)
                stream = stream_response(user_prompt, context)
                first_chunk = next(stream, "")  # รอจนโมเดลเริ่มตอบ แล้วค่อยปิด spinner
            response = st.write_stream(itertools.chain([first_chunk], stream))
        except Exception as e:
            stop_with_error(
                f"เรียกโมเดลไม่สำเร็จ: {e}\n\n"
                f"ตรวจสอบว่า Ollama เปิดอยู่ และติดตั้งโมเดล `{LLM_MODEL}` กับ `{EMBED_MODEL}` แล้ว"
            )

        render_sources(sources)

    current_messages.append({"role": "assistant", "content": response, "sources": sources})
    st.session_state.sessions[current_id]["messages"] = current_messages
    save_all_sessions(st.session_state.sessions)

    if is_first_message:
        st.rerun()  # อัปเดตชื่อแชทใน sidebar