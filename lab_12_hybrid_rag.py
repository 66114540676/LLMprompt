import ast
import re
from pathlib import Path

from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from rank_bm25 import BM25Okapi

EMBED_MODEL = "nomic-embed-text"

# ไฟล์ที่โหลดเข้าฐานความรู้ได้ (.py แยกตามฟังก์ชัน/คลาส ส่วนไฟล์อื่นแยกตามจำนวนบรรทัด)
SUPPORTED_SUFFIXES = {".py", ".md", ".txt", ".js", ".ts", ".java", ".c", ".cpp", ".sql"}
# เอกสารประกอบใน dataset/ ที่ไม่ใช่ฐานความรู้ (ถ้าโหลดเข้าไป ผลค้นหาและผลวัดจะเพี้ยน)
EXCLUDED_FILES = {"README.md", "eval_results.md"}
CHUNK_MAX_CHARS = 1500
CHUNK_LINES = 40


# ---------------------------------------------------------------------------
# Tokenizer สำหรับ BM25
# ---------------------------------------------------------------------------
# คำถามทั่วไปที่ไม่ช่วยในการค้นหา (กรองเฉพาะฝั่งคำถาม ไม่แตะเอกสาร
# และไม่ตัดคีย์เวิร์ดของโค้ดอย่าง if / for / in / and / or / not)
QUERY_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "of", "to", "do", "does", "did", "i", "me", "my",
    "you", "your", "how", "what", "which", "when", "can", "could", "it", "that", "this",
    "there", "be", "show", "please",
}


def tokenize(text, is_query=False):
    """แยกคำจากโค้ด: `add_numbers(a, b)` -> add_numbers, add, numbers, a, b

    ของเดิมใช้ split(" ") ทำให้ได้ token เช่น "multiply(a," ซึ่งไม่มีวันตรงกับคำถาม
    """
    tokens = []
    for word in re.findall(r"\w+", text.lower()):
        if is_query and word in QUERY_STOPWORDS:
            continue
        tokens.append(word)
        if "_" in word:
            tokens.extend(part for part in word.split("_") if part)
    return tokens


# ---------------------------------------------------------------------------
# แบ่งไฟล์ใน dataset เป็นชิ้นเล็กๆ (chunk) ก่อนใส่เข้า RAG
# ---------------------------------------------------------------------------
def _chunk_lines(text, name):
    lines = text.splitlines()
    chunks = []
    for i in range(0, len(lines), CHUNK_LINES):
        block = "\n".join(lines[i:i + CHUNK_LINES]).strip()
        if block:
            chunks.append(f"# {name}\n{block}")
    return chunks


def _chunk_python(source, name):
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return _chunk_lines(source, name)

    lines = source.splitlines()

    def segment(node):
        start = min([node.lineno] + [d.lineno for d in node.decorator_list])
        return "\n".join(lines[start - 1:node.end_lineno])

    chunks = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        text = segment(node)
        if isinstance(node, ast.ClassDef) and len(text) > CHUNK_MAX_CHARS:
            # คลาสยาว: แยกเป็นทีละ method
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    chunks.append(f"# {name} (class {node.name})\n{segment(child)}")
        else:
            chunks.append(f"# {name}\n{text}")

    return chunks or _chunk_lines(source, name)


def load_chunks(path="dataset"):
    """อ่านไฟล์ในโฟลเดอร์ (หรือไฟล์เดียว) แล้วคืนรายการ chunk สำหรับสร้าง HybridRAG"""
    root = Path(path)
    if not root.exists():
        return []

    files = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file())
    chunks = []
    for f in files:
        if f.suffix.lower() not in SUPPORTED_SUFFIXES or f.name in EXCLUDED_FILES:
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if f.suffix.lower() == ".py":
            chunks.extend(_chunk_python(text, f.as_posix()))
        else:
            chunks.extend(_chunk_lines(text, f.as_posix()))

    return list(dict.fromkeys(chunks))  # ตัดชิ้นซ้ำ โดยคงลำดับเดิม


# ---------------------------------------------------------------------------
# Hybrid RAG
# ---------------------------------------------------------------------------
class HybridRAG:
    def __init__(self, docs, embeddings=None):
        if not docs:
            raise ValueError("HybridRAG ต้องมีเอกสารอย่างน้อย 1 ชิ้น")
        self.docs = list(docs)
        self.embeddings = embeddings or OllamaEmbeddings(model=EMBED_MODEL)
        self.vector_db = FAISS.from_texts(self.docs, self.embeddings)
        self.bm25 = BM25Okapi([tokenize(doc) for doc in self.docs])

    def _vector_search(self, query, k):
        results = self.vector_db.similarity_search(query, k=k)
        return [doc.page_content for doc in results]

    def _bm25_search(self, query, k):
        scores = self.bm25.get_scores(tokenize(query, is_query=True))
        ranked = sorted(range(len(self.docs)), key=lambda i: scores[i], reverse=True)
        # เอาเฉพาะชิ้นที่มีคำตรงกับคำถามจริง (คะแนน > 0)
        return [self.docs[i] for i in ranked[:k] if scores[i] > 0]

    @staticmethod
    def _fuse(*ranked_lists, rrf_k=60):
        """Reciprocal Rank Fusion: รวมอันดับจากหลายวิธีเข้าด้วยกัน"""
        scores = {}
        for results in ranked_lists:
            for rank, doc in enumerate(results):
                scores[doc] = scores.get(doc, 0.0) + 1.0 / (rrf_k + rank + 1)
        return sorted(scores, key=scores.get, reverse=True)

    def search(self, query, top_k=3):
        """คืนผลของทั้ง 3 วิธี: vector, bm25 และ hybrid (รวมสองวิธีแรกด้วย RRF)"""
        pool = top_k * 2
        vector = self._vector_search(query, pool)
        bm25 = self._bm25_search(query, pool)
        return {
            "vector": vector[:top_k],
            "bm25": bm25[:top_k],
            "hybrid": self._fuse(vector, bm25)[:top_k],
        }