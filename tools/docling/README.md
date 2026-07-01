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

---

## layout_figures.py — ดึง bbox ของกราฟ/ตาราง ด้วย DocLayout-YOLO (ฟีเจอร์ "รูปที่เกี่ยวข้อง")

ใช้กับหน้า dashboard ที่กราฟหลายอันวางบนพื้นหลังเดียวกัน **โดยไม่มีการ์ด** (เช่นหน้า Financial
Highlights) ซึ่ง heuristic เชิงเรขาคณิตของ backend (การ์ดขาว / cluster_drawings) แยกกราฟไม่ได้
(cluster รวมเป็นก้อนเดียว ~90% → ได้เกือบทั้งหน้า). **DocLayout-YOLO** (YOLOv10 เทรนบน DocStructBench,
model `juliozhao/DocLayout-YOLO-DocStructBench`) มี class `figure`/`table` โดยตรง → แยกกราฟแต่ละอัน
ได้แม่นและเร็ว (~0.3-0.5s/หน้า) เช่นตัดโดนัท Sales / Net Income / bar chart แยกกัน, หน้า 18 แยก
Figure 5/6/7 ครบ (Docling รวม Fig6+7).

**ทำไมไม่ใช้ YOLO ล้วน:** YOLO เก่งเฉพาะกราฟ/ตาราง/รูปถ่ายชัดๆ — หน้า infographic ดีไซน์เต็มหน้า /
กล่อง vision / รูป portrait มันคืน 0 figure → **backend fallback ไป heuristic เดิมรายหน้า** (path A
raster + การ์ดขาว/cluster) ดังนั้นได้ทั้งความแม่นของ YOLO บนหน้ากราฟ + ครอบคลุมของ heuristic บนหน้าอื่น.

```bash
tools/docling/.venv/bin/python tools/docling/layout_figures.py FILE.pdf --pages 1-60
# stdout: {"page_count":N,"pages":{"6":[{"type":"figure","conf":0.93,"box":[x0,y0,x1,y1]},...]}}
#   box = normalize 0..1, origin มุมซ้ายบน → backend เอาไป crop ด้วย pymupdf
```

### deploy เป็น sidecar container (production)
YOLO+torch หนัก → แยกเป็น service `doclayout` ใน `docker-compose.prod.yml` (ไม่บวม backend).
backend POST ไฟล์ PDF (multipart) ผ่าน `hermes_network` → sidecar คืน bbox JSON → backend crop ด้วย pymupdf.

ไฟล์: `tools/docling/Dockerfile` (build sidecar, torch CPU-only + doclayout-yolo, pre-download weights),
`layout_server.py` (FastAPI `/figures`, warm model ตอน startup), `layout_figures.py`
(`extract_figures()`: render หน้า → YOLO → filter conf/ขนาด + NMS → normalize box).

**เปิดใช้:**
1. build + start sidecar: `docker-compose -f docker-compose.prod.yml up -d --build doclayout`
   (build ครั้งแรกนาน — โหลด torch + YOLO weights)
2. ตั้ง `DOC_IMG_USE_DOCLING=1` ใน `.env` → `up -d backend` (recreate รับ env ใหม่) + `restart nginx`
3. ปิดกลับ: `DOC_IMG_USE_DOCLING=0` → heuristic เดิม (และถ้า sidecar ล่ม/ช้า backend fallback อัตโนมัติ)

env (ตั้งใน compose แล้ว): `DOC_IMG_DOCLING_URL=http://doclayout:8000/figures`,
`DOC_IMG_DOCLING_MAX_PAGES=60`, `DOC_IMG_DOCLING_TIMEOUT=1800`. tuning YOLO (ใน sidecar):
`LAYOUT_CONF` (0.3), `LAYOUT_MIN_FRAC` (0.05 = ตัดไอคอนเล็ก), `LAYOUT_RENDER_DPI` (150).

**ข้อควรระวัง:** sidecar กิน RAM ตอน inference (จำกัด `mem_limit: 3g`) — เช็ค RAM รวม VPS ว่าพอ;
idle ระหว่างไม่มีงาน สไปก์เฉพาะตอน index เอกสารใหม่. มีผลเฉพาะเอกสารที่อัปใหม่หลังเปิด flag.
