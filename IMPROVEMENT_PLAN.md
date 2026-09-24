# แผนปรับปรุงโปรเจกต์ Local Coding Assistant

เอกสารนี้แบ่งงานเป็นขั้นตอน แต่ละขั้นมี **เป้าหมาย**, **prompt ที่คัดลอกไปวางได้เลย** (ใช้กับ Claude Code หรือ Copilot Chat ใน VS Code) และ **วิธีตรวจว่าเสร็จจริง**

กฎการใช้งาน

- ทำทีละขั้น ตรวจผ่านแล้วค่อย commit แล้วไปขั้นถัดไป ถ้าขั้นไหนพัง `git checkout .` กลับได้ทันที
- ขั้น 1, 2, 7, 8, 9 จำเป็นต่อการส่งงาน ส่วนขั้น 3–6 เป็นส่วนเพิ่มคุณภาพ ถ้าเวลาน้อยให้ทำขั้น 5 (UI) เป็นอันดับแรกของกลุ่มนี้
- ทุก prompt สั่งให้ AI อ่านไฟล์ก่อนแก้ อย่าตัดส่วนนี้ออก เพราะ AI ไม่รู้โครงสร้างโค้ดของเรา

---

## ขั้น 0 เตรียม git ให้ย้อนกลับได้

ทำเองในเทอร์มินัล (ดูหัวข้อ "อัปขึ้น GitHub" ท้ายไฟล์ถ้ายังไม่ได้ต่อ remote)

```bash
git add .
git commit -m "snapshot before improvements"
```

---

## ขั้น 1 เก็บกวาด dependency และไฟล์ที่ไม่ใช้

**เป้าหมาย** ให้คนอื่น `uv sync` แล้วรันได้ทันที และไม่มีไฟล์ขยะหรือข้อมูลส่วนตัวติดไป

**Prompt**

```text
อ่าน pyproject.toml, lab_12_hybrid_rag.py, lab_13_coding_assistant.py และ lab_13_app.py ก่อน แล้วทำสิ่งต่อไปนี้:

1. หา import ทั้งหมดในไฟล์ .py ทั้งสาม แล้วเทียบกับ dependencies ใน pyproject.toml
   - เพิ่ม package ที่โค้ดใช้แต่ไม่มีใน pyproject (อย่างน้อยต้องมี pypdf)
   - ลบ package ที่ไม่มีโค้ดไหนใช้ (เช่น kuzu)
   - แสดงตารางสรุปว่าเพิ่ม/ลบอะไร เพราะอะไร
2. สร้าง .gitignore ที่ครอบคลุม .venv/, __pycache__/, chat_uploads/, chat_sessions.json, chat_history.json, .DS_Store
3. ใน lab_13_app.py หาปุ่มคำถามแนะนำที่พูดถึง Graph RAG แล้วเปลี่ยนเป็นคำถามที่ตอบได้จาก dataset/sample_code.py จริง
   เช่น "เขียน decorator สำหรับ retry เมื่อเกิด error"
4. อย่าแก้ logic อื่นใด

เสร็จแล้วบอกคำสั่ง uv ที่ฉันต้องรันเพื่ออัปเดต uv.lock
```

**ตรวจ**

```bash
uv sync
rm chat_history.json
uv run streamlit run lab_13_app.py   # แนบไฟล์ PDF ลองดูว่าอ่านได้
```

---

## ขั้น 2 จัดโค้ดให้อ่านง่าย (refactor โดยไม่เปลี่ยนพฤติกรรม)

**เป้าหมาย** ย้ายค่าที่กระจายอยู่ในโค้ดมาไว้ที่เดียว ผู้ตรวจเปิดไฟล์แล้วเข้าใจทันที

**Prompt**

```text
อ่านไฟล์ .py ทั้งสามก่อน แล้ว refactor โดยห้ามเปลี่ยนพฤติกรรมของแอป:

1. สร้างไฟล์ config.py เก็บค่าคงที่ทั้งหมดที่ตอนนี้ hardcode อยู่ ได้แก่
   ชื่อโมเดล (qwen2.5-coder:7b, nomic-embed-text, qwen2.5vl:3b), ค่า RRF k = 60, จำนวนผลต่อโหมด (3),
   ขนาด chunk (1,500 ตัวอักษร, 40 บรรทัด), ขีดจำกัดไฟล์แนบ (6,000 ตัวอักษร), path ของ dataset, chat_sessions.json, chat_uploads/
   ให้ทุกไฟล์ import จาก config.py แทน
2. เพิ่ม type hints และ docstring สั้น ๆ (ภาษาอังกฤษ 1-2 บรรทัด) ให้ทุกฟังก์ชันและคลาสที่ยังไม่มี
3. ใน lab_13_app.py ถ้ามีฟังก์ชันยาวเกิน ~60 บรรทัด ให้แยกเป็นฟังก์ชันย่อยตามหน้าที่
   เช่น render_sidebar(), render_welcome(), render_message(), handle_attachments()
4. ลบโค้ดที่ไม่มีใครเรียกใช้ แต่เก็บ generate_response() ไว้

เสร็จแล้วสรุปเป็นรายการว่าแก้ไฟล์ไหน ตรงไหน และยืนยันว่าไม่มีการเปลี่ยน logic
```

**ตรวจ** รันแอป ถามคำถามเดิม 2–3 ข้อ ผลต้องเหมือนก่อนแก้ สลับโหมดค้นหาได้ครบทั้ง 3 โหมด

---

## ขั้น 3 ให้โมเดลจำบทสนทนาก่อนหน้า

**เป้าหมาย** แก้ข้อจำกัด "โมเดลไม่เห็นข้อความก่อนหน้า" ผู้ใช้ถามต่อได้ เช่น "แก้ให้รองรับ list ว่างด้วย"

**Prompt**

```text
อ่าน lab_13_coding_assistant.py และ lab_13_app.py ก่อน

ตอนนี้ stream_response() ส่งเฉพาะคำถามล่าสุดให้โมเดล ให้แก้เป็น:
1. รับพารามิเตอร์ history (list ของ {"role": "user"|"assistant", "content": str})
2. ส่งไปที่ Ollama ในรูปแบบ messages = [system] + history ล่าสุด N ข้อความ + ข้อความปัจจุบัน
   - N อยู่ใน config.py ชื่อ HISTORY_TURNS ค่าเริ่มต้น 6
   - snippet จาก RAG และเนื้อหาไฟล์แนบ ให้ใส่เฉพาะในข้อความปัจจุบัน ไม่ต้องใส่ซ้ำใน history
   - ถ้า history รวมกันยาวเกิน 8,000 ตัวอักษร ให้ตัดข้อความเก่าที่สุดทิ้งก่อน
3. ใน lab_13_app.py ส่ง history ของแชทปัจจุบันเข้าไป
4. คำค้น RAG ยังใช้เฉพาะคำถามปัจจุบันเหมือนเดิม
5. อย่าเปลี่ยน signature ของ generate_response() เพื่อไม่ให้โค้ดเก่าพัง (ให้ history เป็น optional)
```

**ตรวจ** ถาม "เขียนฟังก์ชัน bubble sort" แล้วตามด้วย "เปลี่ยนให้เรียงจากมากไปน้อย" โมเดลต้องแก้โค้ดเดิมได้ถูก จากนั้นแก้ข้อจำกัดข้อแรกใน README

---

## ขั้น 4 ให้ BM25 ค้นภาษาไทยได้

**เป้าหมาย** แก้ข้อจำกัด "BM25 ค้นคำภาษาไทยไม่ได้"

**Prompt**

```text
อ่าน lab_12_hybrid_rag.py ก่อน โดยเฉพาะฟังก์ชัน tokenizer ที่ใช้กับ BM25

1. เพิ่ม pythainlp เป็น dependency (uv add pythainlp)
2. ในตัว tokenizer ถ้าข้อความมีอักษรไทย (ช่วง Unicode \u0E00-\u0E7F) ให้ตัดคำส่วนที่เป็นไทยด้วย
   pythainlp.tokenize.word_tokenize(engine="newmm") ส่วนภาษาอังกฤษและชื่อตัวแปรยังใช้ logic เดิม
   (regex \w+, แตกคำที่มี _, คง keyword ของโค้ดไว้)
3. เพิ่ม stopwords ภาษาไทยสำหรับฝั่งคำถามเท่านั้น (ใช้ pythainlp.corpus.thai_stopwords)
4. ถ้า import pythainlp ไม่ได้ ให้ fallback เป็นพฤติกรรมเดิมพร้อม warning ไม่ให้แอปพัง
5. เขียนตัวอย่างใน if __name__ == "__main__" แสดงผล tokenize ของ "ฟังก์ชันหาค่าเฉลี่ย add_numbers"
```

**ตรวจ** ในหน้าแอปเลือกโหมด BM25 แล้วถาม "ตรวจสอบอีเมลถูกต้องไหม" ควรเริ่มมีผลออกมา (ขึ้นกับว่า docstring มีคำไทยหรือไม่ ถ้า docstring เป็นอังกฤษทั้งหมด ให้เพิ่มคำอธิบายภาษาไทยใน docstring ของ dataset บางตัว)

---

## ขั้น 5 ปรับ UI ให้สวยและเป็นเอกลักษณ์

### แนวทางการออกแบบ

แอปนี้เป็นผู้ช่วยเขียนโค้ดที่รันในเครื่อง ผู้ใช้คือนักพัฒนาที่นั่งอยู่หน้า editor อยู่แล้ว ดังนั้นแทนที่จะทำหน้าตาแบบแชทบอททั่วไป ให้ยืมภาษาภาพของ **code editor** มาใช้: สีอ้างอิงจาก syntax highlighting และให้ **Sources แสดงเป็นแท็บไฟล์แบบใน editor** ซึ่งเป็นจุดเด่นจุดเดียวของหน้า ส่วนอื่นเรียบและเงียบ

**สี (design tokens)**

| ชื่อ | Hex | ใช้กับ |
|---|---|---|
| `--ink` | `#10151C` | พื้นหลังหลัก (น้ำเงินหมึกเข้ม ไม่ใช่ดำล้วน) |
| `--panel` | `#18202A` | sidebar, บับเบิล, code block |
| `--line` | `#283241` | เส้นขอบ, ตัวคั่น |
| `--text` | `#DCE3EC` | ตัวอักษรหลัก |
| `--muted` | `#8795A8` | ข้อความรอง, placeholder |
| `--keyword` | `#7AA2F7` | สีหลัก: ปุ่ม, ลิงก์, focus ring (สีเดียวกับ keyword ใน editor) |
| `--string` | `#E0AF68` | ใช้เฉพาะแท็บ Sources และชื่อฟังก์ชัน (สีเดียวกับ string) |

**ตัวอักษร** IBM Plex Sans Thai สำหรับข้อความทั้งหมด (ใช้อยู่แล้ว) และ JetBrains Mono เฉพาะโค้ดกับชื่อไฟล์/ฟังก์ชันในแท็บ Sources เท่านั้น ขนาด 15px สำหรับเนื้อหา line-height 1.7 (ภาษาไทยต้องการมากกว่าอังกฤษ) หัวข้อหน้าแรก 28px weight 600

**โครงหน้า**

```
┌─ sidebar ─────┐┌─ main (max-width 820px, ชิดกลาง) ─────────────┐
│ + แชทใหม่     ││                                                │
│               ││  [ข้อความผู้ใช้ บับเบิลชิดขวา ]                  │
│ แชทวันนี้      ││                                                │
│  • bubble...  ││  คำตอบ ชิดซ้าย ไม่มีบับเบิล                      │
│  • retry...   ││  ┌ code block ──────────── [Copy] ┐            │
│               ││  └────────────────────────────────┘            │
│ ─────────     ││  ┌─sample_code.py › retry─┬─ › timer ─┐        │
│ โหมดค้นหา      ││  │ (แท็บ Sources แบบ editor)          │        │
│ ◉ Hybrid      ││  └────────────────────────────────────┘        │
│ โมเดล: qwen.. ││                                                │
│               ││  ┌ ช่องพิมพ์ + ไอคอนแนบไฟล์ ─────────┐           │
└───────────────┘└────────────────────────────────────────────────┘
```

หลักการ

- คำตอบของโมเดลไม่ใส่บับเบิล ปล่อยเป็นเนื้อหาเต็มความกว้าง อ่านโค้ดง่ายกว่า มีแค่ข้อความผู้ใช้ที่เป็นบับเบิล
- หน้าแรก: หัวข้อบอกว่าช่วยอะไรได้ในประโยคเดียว เช่น "ถามเรื่องโค้ด แนบไฟล์ หรือวางรูป error ได้เลย" แล้วตามด้วยคำถามแนะนำ 4 ข้อเป็นรายการที่กดได้ ไม่ต้องทำเป็นการ์ดสี่ใบเท่ากัน
- ใช้ motion จุดเดียว: ตอนเปิดแท็บ Sources ให้เนื้อหาแท็บเลื่อนลงสั้น ๆ (150ms) และเคารพ `prefers-reduced-motion`
- ข้อความ error บอกว่าเกิดอะไรและแก้อย่างไร เช่น "เชื่อมต่อ Ollama ไม่ได้ เปิดโปรแกรม Ollama แล้วกดลองใหม่" ไม่ต้องขอโทษ
- ห้ามใช้ ตัวพิมพ์ใหญ่ทั้งคำเป็นป้ายกำกับ, gradient ตกแต่ง, เงาเดียวกันทุกกล่อง

### Prompt 5.1 ระบบสีและตัวอักษร

```text
อ่าน lab_13_app.py และ .streamlit/config.toml ก่อน โดยเฉพาะส่วน CSS ที่เขียนเอง

1. แยก CSS ทั้งหมดออกไปไว้ที่ assets/style.css แล้วโหลดใน app ด้วย st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
2. นิยาม CSS variables บน :root ตามนี้ แล้วแทนค่าสีที่ hardcode อยู่ทั้งหมดด้วย variable
   --ink #10151C, --panel #18202A, --line #283241, --text #DCE3EC, --muted #8795A8,
   --keyword #7AA2F7, --string #E0AF68
3. อัปเดต .streamlit/config.toml ให้ primaryColor, backgroundColor, secondaryBackgroundColor, textColor ตรงกับ token ข้างบน
4. ฟอนต์: IBM Plex Sans Thai สำหรับทั้งหน้า ขนาด 15px line-height 1.7,
   JetBrains Mono สำหรับ code, pre และ .source-tab เท่านั้น ใส่ fallback stack ทุกตัว
5. ใช้ selector ที่เสถียร: [data-testid="stSidebar"], [data-testid="stChatMessage"], [data-testid="stChatInput"]
   หลีกเลี่ยง class ที่ขึ้นต้นด้วย css- หรือ st-emotion ซึ่งเปลี่ยนทุกเวอร์ชัน
6. ใส่ :focus-visible { outline: 2px solid var(--keyword); outline-offset: 2px } ให้ปุ่มและช่องพิมพ์
```

### Prompt 5.2 ข้อความแชทและ code block

```text
อ่าน lab_13_app.py และ assets/style.css ก่อน

1. ข้อความผู้ใช้: บับเบิลชิดขวา พื้น --panel ขอบ 1px --line มุมโค้ง 14px (มุมขวาล่าง 4px) ความกว้างสูงสุด 75%
2. ข้อความโมเดล: ไม่มีพื้นหลัง ไม่มีบับเบิล ซ่อน avatar ทั้งสองฝั่ง
3. พื้นที่เนื้อหาหลัก max-width 820px ชิดกลาง
4. code block: พื้น --panel ขอบ --line มุมโค้ง 8px padding 14px 16px ขนาดตัวอักษร 13.5px
   ตรวจว่าคำตอบแสดงผ่าน st.markdown ที่ render code fence ได้ และปุ่ม copy ของ Streamlit ยังใช้งานได้
5. ช่องพิมพ์ด้านล่าง: พื้น --panel ขอบ --line ตอน focus ขอบเป็น --keyword
6. ห้ามแก้ logic การส่งข้อความหรือการ stream
```

### Prompt 5.3 แท็บ Sources แบบ editor (จุดเด่นของหน้า)

```text
อ่าน lab_13_app.py และ lab_12_hybrid_rag.py ก่อน ดูว่าตอนนี้ Sources แสดงอย่างไร และ snippet แต่ละชิ้นมีข้อมูลอะไรบ้าง
(ชื่อไฟล์, ชื่อฟังก์ชัน/คลาส, คะแนน, ข้อความ)

เปลี่ยนการแสดง Sources ใต้คำตอบให้เป็นแท็บแบบ code editor:
1. ใช้ st.tabs() หนึ่งแท็บต่อหนึ่ง snippet ชื่อแท็บรูปแบบ "sample_code.py › retry"
   (ถ้า chunk ไม่ได้เก็บชื่อฟังก์ชัน ให้แก้ lab_12_hybrid_rag.py ให้เก็บ metadata ชื่อไฟล์และชื่อฟังก์ชันไว้ตอน chunk ด้วย ast)
2. เนื้อหาแท็บแสดงโค้ดด้วย st.code(language="python") และบรรทัดเล็กสีจางใต้โค้ด: โหมดที่ค้นเจอ และอันดับ
3. ครอบทั้งหมดใน st.expander("ดูโค้ดอ้างอิง (3)") ปิดไว้เป็นค่าเริ่มต้น เลขในวงเล็บคือจำนวน snippet
4. CSS: ชื่อแท็บใช้ JetBrains Mono 12.5px สี --muted, แท็บที่เลือกสี --string และมีเส้นบน 2px สี --string
   (เหมือนแท็บไฟล์ที่เปิดอยู่ใน VS Code) พื้นแท็บ --panel
5. ถ้าไม่มี snippet ที่เกี่ยวข้อง ไม่ต้องแสดง expander
6. motion: ตอนเปิด expander ให้เนื้อหา fade-in 150ms และปิดเมื่อ prefers-reduced-motion: reduce
```

### Prompt 5.4 Sidebar และหน้าแรก

```text
อ่าน lab_13_app.py ก่อน

Sidebar:
1. บนสุดเป็นปุ่ม "+ แชทใหม่" เต็มความกว้าง
2. รายการแชทตัดชื่อให้เหลือบรรทัดเดียว (text-overflow: ellipsis) แชทที่เปิดอยู่มีพื้น --line
   ปุ่มลบแชทแสดงเป็นไอคอนเล็กเมื่อ hover เท่านั้น
3. แยกส่วน Settings ไว้ล่างสุดของ sidebar: โหมดค้นหา (st.radio แนวตั้ง Hybrid / Vector / BM25 พร้อมคำอธิบายสั้นใต้แต่ละตัวเลือกด้วย captions=)
   ชื่อโมเดลที่ใช้ สถานะ Ollama (จุดเขียวถ้าเชื่อมต่อได้ แดงถ้าไม่ได้) และปุ่ม "ล้างแชททั้งหมด" ที่ต้องกดยืนยันอีกครั้ง

หน้าแรก (ตอนแชทยังว่าง):
4. หัวข้อ 28px: "ถามเรื่องโค้ดได้เลย" และบรรทัดรองสี --muted: "ค้นตัวอย่างจากชุดโค้ดในเครื่อง แนบไฟล์หรือรูป error ได้"
5. คำถามแนะนำ 4 ข้อเป็นปุ่มแบบรายการ (ชิดซ้าย เต็มความกว้าง ขอบ --line) ไม่ใช่การ์ดสี่ใบ
   คำถาม: "เขียน binary search พร้อมอธิบาย", "ทำ decorator ที่ลองใหม่เมื่อเกิด error",
   "ยกตัวอย่าง Observer pattern", "สร้างคลาสบัญชีธนาคารที่ถอนเกินยอดไม่ได้"
6. ทั้งหน้าชิดซ้ายภายในกรอบ 820px ไม่ต้องจัดกลาง
```

**ตรวจ UI**

- ลองหน้าจอแคบ (ย่อหน้าต่างเหลือ ~400px) ข้อความต้องไม่ล้นแนวนอน
- ใช้แป้น Tab ไล่ปุ่ม ต้องเห็นกรอบ focus ทุกปุ่ม
- ถ่ายภาพหน้าจอก่อน/หลัง เก็บไว้ใส่ README และใช้ในวิดีโอ

---

## ขั้น 6 แผงเปรียบเทียบผลค้นหา 3 โหมด

**เป้าหมาย** โชว์ว่าทำไมเลือก Hybrid ได้เห็นกับตา ใช้ในวิดีโอได้ดีมาก

**Prompt**

```text
อ่าน lab_12_hybrid_rag.py และ lab_13_app.py ก่อน search() คืนผลทั้ง 3 โหมดอยู่แล้ว

1. ใน sidebar เพิ่ม st.toggle("แสดงการเปรียบเทียบโหมดค้นหา") ค่าเริ่มต้นปิด
2. เมื่อเปิด ใต้คำตอบแต่ละข้อให้แสดง st.columns(3) หัวคอลัมน์ Vector / BM25 / Hybrid
   แต่ละคอลัมน์แสดงชื่อฟังก์ชันของผล 3 อันดับ (JetBrains Mono) ถ้าโหมดไหนไม่มีผลให้แสดง "ไม่พบ" สี --muted
3. ชื่อที่ปรากฏในผล Hybrid ด้วย ให้มีเส้นซ้าย 2px สี --keyword
4. ต้องเก็บผลทั้ง 3 โหมดไว้ใน message ของ chat_sessions.json ด้วย เพื่อให้เปิดแชทเก่าแล้วยังเห็น
   และต้องอ่านไฟล์แชทเก่าที่ไม่มี field นี้ได้โดยไม่ error
```

---

## ขั้น 7 ข้อมูลสำหรับทดสอบระบบ (ของที่ต้องส่ง)

**เป้าหมาย** มีชุดคำถามทดสอบพร้อมคำตอบที่คาดหวัง และสคริปต์วัดผลอัตโนมัติ

**Prompt**

```text
อ่าน dataset/sample_code.py และ lab_12_hybrid_rag.py ก่อน

1. สร้าง dataset/test_questions.json เป็นรายการคำถามทดสอบ 15 ข้อ แต่ละข้อมี
   {"question": ..., "expected": ["ชื่อฟังก์ชันหรือคลาส"], "lang": "th"|"en", "type": "exact"|"concept"|"out_of_dataset"}
   - 5 ข้อภาษาอังกฤษที่ใช้คำตรงกับชื่อฟังก์ชัน
   - 5 ข้อภาษาไทยที่อธิบายแนวคิดโดยไม่เอ่ยชื่อฟังก์ชัน
   - 3 ข้อถามแนวคิดเป็นภาษาอังกฤษ (เช่น Observer pattern → EventEmitter)
   - 2 ข้อที่ไม่มีใน dataset (expected เป็น list ว่าง) เช่น FastAPI endpoint
   ชื่อใน expected ต้องมีอยู่จริงใน sample_code.py
2. สร้าง evaluate_retrieval.py ที่โหลด HybridRAG แล้วรันทุกคำถาม วัด Hit@3 ของแต่ละโหมด
   (ข้อ out_of_dataset ไม่นับ) แล้วพิมพ์ตาราง: โหมด | Hit@3 ภาษาอังกฤษ | Hit@3 ภาษาไทย | รวม
   และบันทึกผลลง dataset/eval_results.md
3. สร้าง dataset/README.md อธิบายว่า dataset มีอะไร 11 หัวข้อ วิธีเพิ่มไฟล์โค้ดของตัวเอง และวิธีรัน evaluate_retrieval.py
```

**ตรวจ**

```bash
uv run python evaluate_retrieval.py
```

ผลที่คาดหวังคือ Hybrid ได้คะแนนรวมสูงสุดหรือเท่ากับโหมดที่ดีที่สุด ถ้าทำขั้น 4 แล้ว BM25 ภาษาไทยควรดีขึ้นจาก 0 เอาตารางนี้ไปใส่ README และวิดีโอได้เลย

---

## ขั้น 8 เติม README ให้ครบ

**Prompt**

```text
อ่าน README.md, PROJECT_SUMMARY.md, pyproject.toml และ dataset/eval_results.md ก่อน

เขียน README.md ใหม่ให้มีหัวข้อตามลำดับนี้ (ภาษาไทย):
1. ชื่อโปรเจกต์และคำอธิบาย 2 บรรทัด + ภาพหน้าจอ (docs/screenshot.png)
2. ลิงก์ส่งงาน: วิดีโอ YouTube, dataset, source code (ใส่ [TODO] ไว้ให้ฉันเติม)
3. สถาปัตยกรรม: แผนภาพ Mermaid แสดง คำถาม → Hybrid RAG (FAISS + BM25 → RRF) → prompt → qwen2.5-coder → Streamlit
4. ความต้องการของระบบ: Python, uv, Ollama, RAM ที่แนะนำ
5. วิธีติดตั้งและรัน ทีละคำสั่ง
6. วิธีใช้งาน: ถามคำถาม, เลือกโหมดค้นหา, แนบไฟล์/รูป, ดู Sources
7. ตัวอย่างคำถาม 3 ข้อจาก test_questions.json พร้อมผลที่ควรได้
8. ผลทดสอบ: ตาราง Hit@3 จาก eval_results.md
9. โครงสร้างไฟล์
10. การแก้ปัญหาที่พบบ่อย (Ollama ไม่เปิด, ไม่มีโมเดล, พอร์ต 8501 ถูกใช้)
11. ข้อจำกัด (อัปเดตให้ตรงกับที่แก้แล้วในขั้น 3 และ 4)

เขียนกระชับ ไม่ต้องใส่ emoji ห้ามอ้างฟีเจอร์ที่โค้ดไม่มี
```

---

## ขั้น 9 ตรวจรอบสุดท้ายก่อนส่ง

**Prompt**

```text
ตรวจโปรเจกต์นี้แบบผู้ตรวจงานที่เพิ่ง clone มา:
1. ทุก import ใน .py มีใน pyproject.toml ครบ
2. ไม่มี path แบบ absolute ของเครื่องฉัน (เช่น C:\Users\...)
3. ไม่มีไฟล์ใน .gitignore หลุดเข้า git (รัน git ls-files ให้ดู)
4. README ไม่มีคำสั่งหรือฟีเจอร์ที่ไม่ตรงกับโค้ด
5. ไม่มี print debug หรือโค้ดที่ comment ทิ้งไว้เป็นก้อน
รายงานเป็นรายการ ปัญหา | ไฟล์ | วิธีแก้ ยังไม่ต้องแก้จนกว่าฉันจะยืนยัน
```

**ตรวจเอง** clone repo ลงโฟลเดอร์ใหม่แล้วรันตาม README ทุกบรรทัด

```bash
cd ~/Desktop
git clone https://github.com/66114540676/LLMprompt.git test-clone
cd test-clone
uv sync
uv run streamlit run lab_13_app.py
```

---

## อัปขึ้น GitHub

repo `66114540676/LLMprompt` มีแค่ README.md ว่าง ๆ จาก "Initial commit" จึงทับได้เลยโดยไม่เสียอะไร รันในโฟลเดอร์ `selected topic in SI mini project`

**ครั้งแรก**

```bash
git init
git add .gitignore
git add .
git status                       # ตรวจว่าไม่มี .venv, __pycache__, chat_sessions.json
git commit -m "Local coding assistant with Hybrid RAG"
git branch -M main
git remote add origin https://github.com/66114540676/LLMprompt.git
git push -u origin main --force  # ทับ README ว่างบน GitHub
```

ถ้าเคยรัน `git init` ไปแล้วและ `git remote add` ขึ้นว่า remote มีอยู่แล้ว ให้ใช้ `git remote set-url origin https://github.com/66114540676/LLMprompt.git` แทน

ถ้าไฟล์ในโฟลเดอร์ที่ควร ignore ถูก add ไปแล้ว (เช่น `.venv`) ให้รัน `git rm -r --cached .venv __pycache__ chat_uploads chat_sessions.json` แล้ว commit ใหม่

เรื่องล็อกอิน: GitHub ไม่รับรหัสผ่านในเทอร์มินัลแล้ว ทางง่ายสุดคือกดปุ่ม Source Control ใน VS Code แล้ว Sign in with GitHub หรือสร้าง Personal Access Token ที่ GitHub → Settings → Developer settings → Tokens แล้วใช้แทนรหัสผ่าน

**เรื่อง branch** ตอนนี้ repo มี 2 branch (`main` และ `project`) ผู้ตรวจที่เปิดลิงก์ repo จะเห็น branch `main` เป็นค่าเริ่มต้น จึงควร push งานไปที่ `main` ถ้าไม่ใช้ `project` แล้ว ลบได้ด้วย `git push origin --delete project`

**หลังแก้แต่ละขั้น**

```bash
git add .
git commit -m "ขั้น 5: ปรับ UI แท็บ Sources แบบ editor"
git push
```

**ลิงก์ที่ใช้ส่ง**

- source code: `https://github.com/66114540676/LLMprompt`
- dataset (static): `https://github.com/66114540676/LLMprompt/tree/main/dataset`
- ถ้าอาจารย์กำหนดให้ส่ง Google Drive: ดาวน์โหลด zip จากปุ่ม Code → Download ZIP บน GitHub (จะได้เฉพาะไฟล์ที่ควรส่ง) แล้วอัปขึ้น Drive ตั้งสิทธิ์ Anyone with the link → Viewer
