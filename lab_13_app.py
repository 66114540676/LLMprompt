import base64
import io
import itertools
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

import streamlit as st

from lab_12_hybrid_rag import EMBED_MODEL, HybridRAG, load_chunks
from lab_13_coding_assistant import LLM_MODEL, stream_response

DATASET_DIR = "dataset"  # โฟลเดอร์ข้อมูลโค้ดที่ใช้เป็นฐานความรู้ของ RAG
RETRIEVAL_MODES = ["Hybrid", "Vector", "BM25"]
RETRIEVAL_CAPTIONS = {
    "Hybrid": "รวมสองวิธีด้วย RRF (แนะนำ)",
    "Vector": "ค้นตามความหมาย",
    "BM25": "ค้นตามคำที่ตรงกัน",
}
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
    "เขียน binary search พร้อมอธิบาย",
    "ทำ decorator ที่ลองใหม่เมื่อเกิด error",
    "ยกตัวอย่าง Observer pattern",
    "สร้างคลาสบัญชีธนาคารที่ถอนเกินยอดไม่ได้",
]

st.set_page_config(page_title="Coding Assistant", page_icon="✨", layout="wide")

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
STYLE_FILE = Path(__file__).parent / "assets" / "style.css"
st.markdown(f"<style>{STYLE_FILE.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


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


CODE_LANGUAGES = {
    ".py": "python", ".js": "javascript", ".ts": "typescript", ".java": "java",
    ".c": "c", ".cpp": "cpp", ".sql": "sql", ".md": "markdown", ".json": "json",
    ".html": "html", ".css": "css",
}


def describe_snippet(snippet):
    """แยกชื่อแท็บ, ชนิด, ภาษา และตัวโค้ด ออกจาก chunk

    chunk จาก dataset ขึ้นต้นด้วย "# <path>" หรือ "# <path> (class X)" ส่วนไฟล์แนบขึ้นต้นด้วย
    "# File: <name>" หรือ "# Image: <name>" (ตัวอย่างใน SAMPLE_DOCS ไม่มีบรรทัดหัว)
    """
    header, _, body = snippet.partition("\n")
    attached = re.match(r"# (File|Image): (.+)", header)
    if attached:
        kind, name = attached.groups()
        lang = "text" if kind == "Image" else CODE_LANGUAGES.get(Path(name).suffix.lower(), "text")
        return {"label": name, "kind": kind.lower(), "lang": lang, "code": body}

    path, owner = None, None
    source_header = re.match(r"# (\S+)(?: \(class (\w+)\))?$", header)
    if source_header:
        path, owner = source_header.groups()
    else:
        body = snippet

    symbol = re.search(r"^\s*(?:async\s+)?(?:def|class)\s+(\w+)", body, re.MULTILINE)
    name = symbol.group(1) if symbol else None
    if owner and name:
        name = f"{owner}.{name}"

    file_name = Path(path).name if path else None
    label = " › ".join(part for part in (file_name, name) if part) or "snippet"
    lang = CODE_LANGUAGES.get(Path(path).suffix.lower(), "text") if path else "python"
    return {"label": label, "kind": "dataset", "lang": lang, "code": body}


def render_sources(snippets, mode=None):
    """แสดงโค้ดอ้างอิงเป็นแท็บแบบ code editor (หนึ่งแท็บต่อหนึ่ง snippet)"""
    if not snippets:
        return
    items = [describe_snippet(s) for s in snippets]
    with st.expander(f"ดูโค้ดอ้างอิง ({len(items)})", expanded=False):
        tabs = st.tabs([item["label"] for item in items])
        rank = 0
        for tab, item in zip(tabs, items):
            with tab:
                st.code(item["code"], language=item["lang"])
                if item["kind"] == "file":
                    st.caption("ไฟล์ที่แนบมากับคำถาม")
                elif item["kind"] == "image":
                    st.caption(f"คำบรรยายรูปที่แนบ โดย {VISION_MODEL}")
                else:
                    rank += 1
                    st.caption(f"ค้นเจอด้วยโหมด {mode} · อันดับ {rank}" if mode else f"อันดับ {rank}")


def message_snippets(msg):
    """คืนรายการ snippet ของข้อความ (แชทเก่ามีแค่ "sources" ที่เป็นข้อความต่อกันด้วย ---)"""
    if "snippets" in msg:
        return msg["snippets"]
    return msg["sources"].split("\n---\n") if msg.get("sources") else []


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
        render_sources(message_snippets(msg), msg.get("mode"))


@st.cache_resource(show_spinner="กำลังสร้างดัชนีเอกสาร...")
def get_rag():
    """สร้าง RAG ครั้งเดียวแล้วใช้ร่วมกันทุกแชท (ไม่ต้อง embed ใหม่ทุกครั้งที่เปิดหน้า)"""
    return HybridRAG(load_chunks(DATASET_DIR) or SAMPLE_DOCS)


@st.cache_data(ttl=15, show_spinner=False)
def ollama_online():
    """เช็กว่า Ollama เปิดอยู่ไหม (แสดงสถานะใน sidebar เท่านั้น ไม่ได้เรียกโมเดล)"""
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=1):
            return True
    except OSError:
        return False


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

    if st.button("+ แชทใหม่", key="new_chat"):
        # ถ้าแชทปัจจุบันยังว่างอยู่ ไม่ต้องสร้างซ้ำ
        if st.session_state.sessions[current_id]["messages"]:
            new_session()
            save_all_sessions(st.session_state.sessions)
        st.rerun()

    st.markdown('<div class="side-label">แชท</div>', unsafe_allow_html=True)

    for s_id, s_data in reversed(list(st.session_state.sessions.items())):
        title = s_data.get("title") or "Chat"  # ชื่อยาวถูกตัดด้วย CSS (ellipsis)
        is_active = s_id == current_id

        col_title, col_del = st.columns([5, 1], gap="small")
        with col_title:
            if st.button(title, key=f"chat_{s_id}", type="primary" if is_active else "secondary"):
                st.session_state.current_session_id = s_id
                st.rerun()
        with col_del:
            if st.button("✕", key=f"del_{s_id}", help="ลบแชทนี้"):
                del st.session_state.sessions[s_id]
                if not st.session_state.sessions:
                    new_session()
                elif is_active:
                    st.session_state.current_session_id = list(st.session_state.sessions.keys())[-1]
                save_all_sessions(st.session_state.sessions)
                st.rerun()

    with st.container(key="settings"):
        st.markdown('<div class="side-label">ตั้งค่า</div>', unsafe_allow_html=True)
        st.radio(
            "โหมดค้นหา",
            RETRIEVAL_MODES,
            captions=[RETRIEVAL_CAPTIONS[m] for m in RETRIEVAL_MODES],
            key="retrieval_mode",
        )

        online = ollama_online()
        st.markdown(
            f'<div class="status"><span class="dot {"on" if online else "off"}"></span>'
            f'{"Ollama เชื่อมต่อแล้ว" if online else "Ollama ไม่ได้เปิด"}</div>',
            unsafe_allow_html=True,
        )
        st.caption(f"โมเดล: `{LLM_MODEL}`  \nEmbedding: `{EMBED_MODEL}`  \nอ่านรูป: `{VISION_MODEL}`")

        if st.session_state.get("confirm_clear"):
            st.caption("ลบแชททั้งหมดถาวร ยืนยันไหม")
            col_yes, col_no = st.columns(2, gap="small")
            if col_yes.button("ลบทั้งหมด", key="clear_yes", type="primary"):
                st.session_state.sessions = {}
                new_session()
                save_all_sessions(st.session_state.sessions)
                st.session_state.confirm_clear = False
                st.rerun()
            if col_no.button("ยกเลิก", key="clear_no"):
                st.session_state.confirm_clear = False
                st.rerun()
        elif st.button("ล้างแชททั้งหมด", key="clear_all"):
            st.session_state.confirm_clear = True
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
        f'<div class="hero-sub">ค้นตัวอย่างจากชุดโค้ดในเครื่อง แนบไฟล์หรือรูป error ได้</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    for i, text in enumerate(SUGGESTIONS):
        st.button(text, key=f"sug_{i}", on_click=set_pending_prompt, args=(text,))

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

        mode = st.session_state.retrieval_mode
        render_sources(context, mode)

    current_messages.append({
        "role": "assistant", "content": response,
        "sources": sources, "snippets": context, "mode": mode,
    })
    st.session_state.sessions[current_id]["messages"] = current_messages
    save_all_sessions(st.session_state.sessions)

    if is_first_message:
        st.rerun()  # อัปเดตชื่อแชทใน sidebar