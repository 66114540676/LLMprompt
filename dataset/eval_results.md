# ผลวัดการค้นหา (Hit@3)

สร้างโดย `evaluate_retrieval.py` จากคำถาม 15 ข้อใน `test_questions.json` ดัชนีมี 46 chunk, embedding `nomic-embed-text`

Hit@3 = สัดส่วนคำถามที่ผลค้นหา 3 อันดับแรกมีฟังก์ชัน/คลาสที่คาดหวังอย่างน้อยหนึ่งตัว (ไม่นับคำถามนอก dataset)

## สรุป

| โหมด | Hit@3 ภาษาอังกฤษ | Hit@3 ภาษาไทย | รวม |
| --- | --- | --- | --- |
| Vector | 8/8 (100%) | 1/5 (20%) | 9/13 (69%) |
| BM25 | 8/8 (100%) | 0/5 (0%) | 8/13 (62%) |
| Hybrid | 8/8 (100%) | 1/5 (20%) | 9/13 (69%) |

## ผลรายข้อ

ในแต่ละโหมดแสดงชื่อที่ค้นเจอเรียงตามอันดับ ✅ = เจอตัวที่คาดหวัง ❌ = ไม่เจอ

| # | คำถาม | ชนิด | คาดหวัง | Vector | BM25 | Hybrid |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Explain the binary_search function | exact (en) | binary_search | ✅ binary_search, factorial, bubble_sort | ✅ binary_search, percentage_discount, timer | ✅ binary_search, factorial, percentage_discount |
| 2 | How does merge_sort work? | exact (en) | merge_sort | ✅ merge_sort, bubble_sort, quick_sort | ✅ merge_sort, quick_sort, bubble_sort | ✅ merge_sort, bubble_sort, quick_sort |
| 3 | validate_email regex pattern | exact (en) | validate_email | ✅ validate_email, EmailNotifier, create_notifier | ✅ validate_email, create_notifier, EmailNotifier | ✅ validate_email, EmailNotifier, create_notifier |
| 4 | Show me the retry decorator | exact (en) | retry | ✅ retry, memoize, timer | ✅ retry, memoize, timer | ✅ retry, memoize, timer |
| 5 | read_csv_rows with a header row | exact (en) | read_csv_rows | ✅ read_csv_rows, read_json_file, write_json_file | ✅ read_csv_rows, read_json_file, write_json_file | ✅ read_csv_rows, read_json_file, write_json_file |
| 6 | ฟังก์ชันตรวจว่าตัวเลขเป็นจำนวนเฉพาะหรือไม่ | concept (th) | is_prime | ❌ is_palindrome, InsufficientFundsError, read_json_file | ❌ ไม่พบ | ❌ is_palindrome, InsufficientFundsError, read_json_file |
| 7 | หาตัวหารร่วมมากของเลขสองจำนวน | concept (th) | gcd | ❌ is_palindrome, InsufficientFundsError, read_json_file | ❌ ไม่พบ | ❌ is_palindrome, InsufficientFundsError, read_json_file |
| 8 | กลับลำดับตัวอักษรในข้อความจากหลังไปหน้า | concept (th) | reverse_string | ❌ is_palindrome, InsufficientFundsError, read_json_file | ❌ ไม่พบ | ❌ is_palindrome, InsufficientFundsError, read_json_file |
| 9 | โครงสร้างข้อมูลแบบเข้าก่อนออกก่อน | concept (th) | Queue | ❌ is_palindrome, InsufficientFundsError, read_json_file | ❌ ไม่พบ | ❌ is_palindrome, InsufficientFundsError, read_json_file |
| 10 | ป้องกันไม่ให้ถอนเงินเกินยอดคงเหลือในบัญชี | concept (th) | BankAccount, InsufficientFundsError | ✅ is_palindrome, InsufficientFundsError, read_json_file | ❌ ไม่พบ | ✅ is_palindrome, InsufficientFundsError, read_json_file |
| 11 | Example of the observer pattern | concept (en) | EventEmitter | ✅ EventEmitter, Checkout, Config | ✅ EventEmitter, validate_email, create_notifier | ✅ EventEmitter, Checkout, Config |
| 12 | How can I cache a function's results so repeated calls are fast? | concept (en) | memoize | ✅ memoize, timer, retry | ✅ memoize, timer, Checkout | ✅ memoize, timer, retry |
| 13 | Make sure only one instance of a class is ever created | concept (en) | Config | ✅ Config, Node, retry | ✅ Config, Shape, InsufficientFundsError | ✅ Config, Node, InsufficientFundsError |
| 14 | Write a FastAPI endpoint that returns JSON | out_of_dataset (en) | (ไม่มี) | write_json_file, read_json_file, memoize | write_json_file, read_json_file, bubble_sort | write_json_file, read_json_file, memoize |
| 15 | How do I train a neural network with PyTorch? | out_of_dataset (en) | (ไม่มี) | create_notifier, binary_search, Node | write_json_file, read_json_file, read_csv_rows | read_json_file, create_notifier, write_json_file |

คำถามนอก dataset ไม่มีคำตอบที่ถูก ใช้ดูว่าแต่ละโหมดคืนผลที่ไม่เกี่ยวข้องมาหรือไม่ (Vector คืนผลเสมอ ส่วน BM25 คืนผลเมื่อมีคำใดคำหนึ่งตรงกัน แม้เป็นคำทั่วไปอย่าง `with` ที่ตรงกับ `with open(...)` ในโค้ด และคืน "ไม่พบ" เมื่อไม่มีคำตรงเลย)
