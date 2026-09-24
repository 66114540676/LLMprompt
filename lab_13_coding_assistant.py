import ollama

LLM_MODEL = "qwen2.5-coder:7b"

SYSTEM_PROMPT = """You are an expert coding assistant.
- Answer in the same language as the user's question.
- The user message may include reference snippets retrieved from a code database. \
Use them only when they are relevant to the question. If they are not relevant, ignore them and answer from your own knowledge.
- Put all code in fenced Markdown blocks with a language tag, and keep explanations concise."""


def build_messages(prompt, context_list):
    context = "\n\n---\n\n".join(context_list) if context_list else "(none)"
    user_content = f"Reference snippets:\n{context}\n\nQuestion:\n{prompt}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def stream_response(prompt, context_list):
    """ส่งคำตอบออกมาทีละส่วนตามที่โมเดลสร้าง (ใช้กับ st.write_stream)"""
    stream = ollama.chat(
        model=LLM_MODEL,
        messages=build_messages(prompt, context_list),
        stream=True,
    )
    for chunk in stream:
        yield chunk["message"]["content"]


def generate_response(prompt, context_list, mode=None):
    """ตอบทีเดียวทั้งก้อน (`mode` เก็บไว้เพื่อให้โค้ดเก่าเรียกได้ ไม่มีผลต่อคำตอบ
    เพราะโหมดค้นหาถูกเลือกตอนเรียก HybridRAG.search แล้ว)"""
    response = ollama.chat(
        model=LLM_MODEL,
        messages=build_messages(prompt, context_list),
    )
    return response["message"]["content"]