# Dataset

ฐานความรู้ที่ Coding Assistant ใช้ค้นตัวอย่างโค้ดมาประกอบคำตอบ (RAG)

## มีอะไรบ้าง

| ไฟล์ | คืออะไร |
|---|---|
| `sample_code.py` | ตัวอย่างโค้ด Python 46 ฟังก์ชัน/คลาส ทุกตัวมี docstring และแยกกันอิสระ |
| `test_questions.json` | คำถามทดสอบ 15 ข้อ พร้อมชื่อฟังก์ชันที่ควรค้นเจอ |
| `eval_results.md` | ผลวัด Hit@3 ล่าสุด (สร้างโดย `evaluate_retrieval.py`) |

`sample_code.py` ครอบคลุม 11 หัวข้อ

1. คณิตศาสตร์: `add`, `multiply`, `factorial`, `fibonacci`, `gcd`, `is_prime`, `circle_area`
2. สตริง: `reverse_string`, `is_palindrome`, `count_words`, `validate_email`, `slugify`
3. List: `remove_duplicates`, `flatten_list`, `chunk_list`, `word_frequency`
4. ค้นหาและเรียงลำดับ: `binary_search`, `bubble_sort`, `quick_sort`, `merge_sort`
5. โครงสร้างข้อมูล: `Stack`, `Queue`, `Node`, `LinkedList`
6. OOP: `Calculator`, `InsufficientFundsError`, `BankAccount`, `Shape`, `Circle`, `Rectangle`
7. Design pattern: Singleton (`Config`), Factory (`EmailNotifier`, `SMSNotifier`, `create_notifier`), Observer (`EventEmitter`), Strategy (`percentage_discount`, `Checkout`)
8. จัดการไฟล์: `read_json_file`, `write_json_file`, `read_csv_rows`
9. Decorator และ generator: `timer`, `retry`, `memoize`, `fibonacci_generator`
10. จัดการ error: `safe_divide`
11. วันที่: `days_between`

## เพิ่มไฟล์โค้ดของตัวเอง

1. วางไฟล์ไว้ในโฟลเดอร์นี้ (โฟลเดอร์ย่อยได้) นามสกุลที่รองรับ: `.py .md .txt .js .ts .java .c .cpp .sql`
2. รีสตาร์ทแอป ดัชนีสร้างครั้งเดียวตอนเปิดแอป จึงต้องรันใหม่ถึงจะเห็นไฟล์ใหม่

การแบ่งชิ้น (chunk)

- `.py` แยกทีละฟังก์ชันหรือคลาสระดับบนสุด ถ้าคลาสยาวเกิน 1,500 ตัวอักษรจะแยกเป็นทีละ method
- ไฟล์ชนิดอื่นแบ่งทีละ 40 บรรทัด
- `README.md` และ `eval_results.md` ในโฟลเดอร์นี้ไม่ถูกโหลดเข้าฐานความรู้

เขียน docstring ให้ทุกฟังก์ชัน จะช่วยให้ค้นเจอจากคำถามที่ไม่ได้เอ่ยชื่อฟังก์ชันตรง ๆ

## วัดผลการค้นหา

ต้องเปิด Ollama และมีโมเดล `nomic-embed-text` ก่อน แล้วรันที่โฟลเดอร์หลักของโปรเจกต์

```bash
uv run python evaluate_retrieval.py
```

สคริปต์ค้นทุกคำถามใน `test_questions.json` ด้วยทั้ง 3 โหมด พิมพ์ตาราง Hit@3 และบันทึกผลรายข้อลง `eval_results.md`

Hit@3 คือสัดส่วนคำถามที่ผลค้นหา 3 อันดับแรกมีฟังก์ชัน/คลาสที่คาดหวังอย่างน้อยหนึ่งตัว คำถามชนิด `out_of_dataset` ไม่นับคะแนน

รูปแบบคำถามใน `test_questions.json`

```json
{"question": "Show me the retry decorator", "expected": ["retry"], "lang": "en", "type": "exact"}
```

- `expected`: ชื่อฟังก์ชันหรือคลาสใน dataset (ว่างได้ ถ้าเป็นคำถามนอก dataset)
- `lang`: `en` หรือ `th`
- `type`: `exact` (คำตรงกับชื่อฟังก์ชัน), `concept` (อธิบายแนวคิดโดยไม่เอ่ยชื่อ) หรือ `out_of_dataset`
