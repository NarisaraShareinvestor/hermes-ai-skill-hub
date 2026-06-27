# Docling PDF → Markdown (local, free)

แปลง PDF ที่ layout ซับซ้อน (56-1 One Report / annual report แบบ multi-column) เป็น
Markdown สะอาด โดยไม่เสีย API cost — รันในเครื่องด้วย Docling (IBM, learned layout model)

## ทำไมต้องใช้ (ไม่ใช้ pymupdf4llm ของแอป)

แอป Hermes ใช้ `pymupdf4llm` + cleanup + vision เฉพาะหน้าเสีย ซึ่ง **เร็ว/เบา/ถูก**
และดีพอกับเอกสารคอลัมน์เดียว (เช่นรายงาน SEO) แต่กับเอกสาร **multi-column** มันอ่าน
ลำดับผิด — เอาข้อความคอลัมน์ข้างๆ มาแทรกกลางประโยค เช่น

> baseline: `...92% crude oil and 44% **2. 2026 Outlook 2.3 Thailand Economic** natural gas imported`
> docling : `...92% crude oil and 44% **natural gas imported. Domestic petroleum distribution...**` ✅

Docling จัด reading-order ถูก แยกคอลัมน์/หัวข้อ/bullet/ตารางได้ → เหมาะกับ 56-1 ที่มีหลาย layout

## ข้อจำกัด (ทำไมเป็น tool offline ไม่ใช่ inline ในแชต)

- **ช้า** ~40-50 วิ/หน้า บน CPU (Mac/VPS ไม่มี GPU) → 233 หน้า ≈ 3 ชม. รันทิ้งไว้ได้
- **infographic/แผนภาพ** → ออกเป็น `[รูป/แผนภาพ]` (ไม่ดึงตัวเลขในรูป) — ตัวเลขในแผนภาพ
  ให้ดูรูปจริง หรือใช้ vision ของแอป
- ข้อความแนวตั้ง (side-tab) อาจเป็นเศษ → tool ตัดให้อัตโนมัติแล้ว

## ติดตั้ง (ครั้งเดียว)

```bash
bash tools/docling/setup.sh
```
รันครั้งแรกจะดาวน์โหลด layout model ลง `~/.cache/huggingface` (ครั้งเดียว)

## ใช้งาน

```bash
source tools/docling/.venv/bin/activate

# ทั้งไฟล์
python tools/docling/docling_convert.py result/ptt-one-report-2025-en.pdf

# กำหนดที่ออก + ช่วงหน้า (แนะนำลองหน้าน้อยๆ ก่อน เพราะช้า)
python tools/docling/docling_convert.py report.pdf -o report.md --pages 1-50
```

ได้ `.md` ที่มี marker `[หน้า N]` ทุกหน้า (ฟอร์แมตเดียวกับที่แอปใช้ → อัปเข้า RAG ได้เลย)

## options

| flag | ความหมาย |
|---|---|
| `-o, --output` | ไฟล์ .md ออก (ดีฟอลต์: ชื่อเดียวกับ PDF) |
| `--pages N-M` | แปลงเฉพาะช่วงหน้า |
| `--keep-garble` | ไม่ตัดบรรทัดตัวอักษรเดี่ยว (ไว้ debug) |
