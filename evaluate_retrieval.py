"""วัดผลการค้นหาของ HybridRAG ทั้ง 3 โหมด (Vector, BM25, Hybrid) ด้วย Hit@3

รัน:  uv run python evaluate_retrieval.py
อ่านคำถามจาก dataset/test_questions.json แล้วบันทึกผลลง dataset/eval_results.md
(ต้องเปิด Ollama และมีโมเดล nomic-embed-text ก่อน)
"""

import json
import re
import sys
from pathlib import Path

from lab_12_hybrid_rag import EMBED_MODEL, HybridRAG, load_chunks

DATASET_DIR = Path("dataset")
QUESTIONS_FILE = DATASET_DIR / "test_questions.json"
RESULTS_FILE = DATASET_DIR / "eval_results.md"
TOP_K = 3
MODES = [("vector", "Vector"), ("bm25", "BM25"), ("hybrid", "Hybrid")]
LANGS = [("en", "ภาษาอังกฤษ"), ("th", "ภาษาไทย")]

# ชื่อฟังก์ชัน/คลาสแรกที่นิยามใน chunk (chunk ของไฟล์ .py แยกทีละฟังก์ชันหรือคลาสอยู่แล้ว)
SYMBOL = re.compile(r"^\s*(?:async\s+)?(?:def|class)\s+(\w+)", re.MULTILINE)


def chunk_symbol(chunk):
    match = SYMBOL.search(chunk)
    return match.group(1) if match else "?"


def score(hits, total):
    return f"{hits}/{total} ({hits / total:.0%})" if total else "-"


def main():
    questions = json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))
    chunks = load_chunks(DATASET_DIR)
    print(f"สร้างดัชนีจาก {len(chunks)} chunk ด้วย {EMBED_MODEL} ...")
    rag = HybridRAG(chunks)

    rows = []  # ผลรายข้อ
    for q in questions:
        results = rag.search(q["question"], top_k=TOP_K)
        found = {mode: [chunk_symbol(c) for c in results[mode]] for mode, _ in MODES}
        hit = {mode: any(name in q["expected"] for name in found[mode]) for mode, _ in MODES}
        rows.append({**q, "found": found, "hit": hit})

    graded = [r for r in rows if r["type"] != "out_of_dataset"]
    summary = []
    for mode, label in MODES:
        cells = [label]
        for lang, _ in LANGS:
            subset = [r for r in graded if r["lang"] == lang]
            cells.append(score(sum(r["hit"][mode] for r in subset), len(subset)))
        cells.append(score(sum(r["hit"][mode] for r in graded), len(graded)))
        summary.append(cells)

    header = ["โหมด"] + [f"Hit@{TOP_K} {name}" for _, name in LANGS] + ["รวม"]
    table = [header] + summary
    widths = [max(len(row[i]) for row in table) for i in range(len(header))]
    print()
    for row in table:
        print(" | ".join(cell.ljust(w) for cell, w in zip(row, widths)))
    print(f"\n(ไม่นับคำถามนอก dataset {len(rows) - len(graded)} ข้อ)")

    RESULTS_FILE.write_text(render_markdown(rows, summary, header, len(chunks)), encoding="utf-8")
    print(f"บันทึกผลรายข้อไว้ที่ {RESULTS_FILE.as_posix()}")


def render_markdown(rows, summary, header, n_chunks):
    md = lambda cells: "| " + " | ".join(cells) + " |"
    lines = [
        "# ผลวัดการค้นหา (Hit@3)",
        "",
        f"สร้างโดย `evaluate_retrieval.py` จากคำถาม {len(rows)} ข้อใน `test_questions.json` "
        f"ดัชนีมี {n_chunks} chunk, embedding `{EMBED_MODEL}`",
        "",
        f"Hit@{TOP_K} = สัดส่วนคำถามที่ผลค้นหา {TOP_K} อันดับแรกมีฟังก์ชัน/คลาสที่คาดหวังอย่างน้อยหนึ่งตัว "
        "(ไม่นับคำถามนอก dataset)",
        "",
        "## สรุป",
        "",
        md(header),
        md(["---"] * len(header)),
        *[md(row) for row in summary],
        "",
        "## ผลรายข้อ",
        "",
        "ในแต่ละโหมดแสดงชื่อที่ค้นเจอเรียงตามอันดับ ✅ = เจอตัวที่คาดหวัง ❌ = ไม่เจอ",
        "",
        md(["#", "คำถาม", "ชนิด", "คาดหวัง"] + [label for _, label in MODES]),
        md(["---"] * (4 + len(MODES))),
    ]
    for i, r in enumerate(rows, 1):
        cells = [str(i), r["question"], f'{r["type"]} ({r["lang"]})', ", ".join(r["expected"]) or "(ไม่มี)"]
        for mode, _ in MODES:
            names = ", ".join(r["found"][mode]) or "ไม่พบ"
            mark = "" if r["type"] == "out_of_dataset" else ("✅ " if r["hit"][mode] else "❌ ")
            cells.append(mark + names)
        lines.append(md(cells))
    lines += [
        "",
        "คำถามนอก dataset ไม่มีคำตอบที่ถูก ใช้ดูว่าแต่ละโหมดคืนผลที่ไม่เกี่ยวข้องมาหรือไม่ "
        "(Vector คืนผลเสมอ ส่วน BM25 คืนผลเมื่อมีคำใดคำหนึ่งตรงกัน แม้เป็นคำทั่วไปอย่าง `with` "
        "ที่ตรงกับ `with open(...)` ในโค้ด และคืน \"ไม่พบ\" เมื่อไม่มีคำตรงเลย)",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
