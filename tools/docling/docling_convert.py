#!/usr/bin/env python3
"""
docling_convert.py — แปลง PDF (โดยเฉพาะ 56-1 One Report / annual report ที่ layout
multi-column ซับซ้อน) เป็น Markdown สะอาดด้วย Docling (free, local, ไม่เสีย API cost).

ทำไมใช้ Docling: pymupdf4llm อ่านลำดับคอลัมน์ผิด (เอาข้อความคอลัมน์อื่นแทรกกลางประโยค)
Docling ใช้ learned layout model จัด reading-order ถูก แยกคอลัมน์/หัวข้อ/ตาราง/bullet ได้

ข้อแลก: ช้า (~40-50 วิ/หน้า บน CPU) เหมาะกับงาน offline/batch ไม่ใช่ inline ในแชต

ใช้:
    python docling_convert.py INPUT.pdf [-o OUTPUT.md] [--pages 1-20] [--keep-garble]

ตัวอย่าง:
    python docling_convert.py ../../result/ptt-one-report-2025-en.pdf
    python docling_convert.py report.pdf -o report.md --pages 1-50
"""
import argparse
import os
import re
import sys
import time
from pathlib import Path

# เก็บ layout model cache ในเครื่อง (เปลี่ยนได้ผ่าน env HF_HOME)
os.environ.setdefault("HF_HOME", str(Path.home() / ".cache" / "huggingface"))
os.environ.setdefault("OMP_NUM_THREADS", "4")

PAGE_BREAK = "<<<DOCLING_PAGE_BREAK>>>"
IMG_MARK = "[รูป/แผนภาพ]"   # infographic/ภาพ Docling ไม่ดึงตัวเลขในรูป → ใช้ vision/ดูรูปจริงแทน


def _collapse_garble(md: str) -> str:
    """ทิ้ง 'บรรทัดตัวอักษร/สัญลักษณ์เดี่ยว' ที่เกิดจากข้อความแนวตั้ง (side-tab) หรือ bullet
    ถูกอ่านทีละตัว (เช่น 3 . 4 • 1 , 5 6 - 1 2 0). markdown เนื้อจริงไม่มีบรรทัด char เดี่ยว
    → ทิ้งได้หมด. ส่วนที่ต่อกันเป็นคำยาวพอ(รัน <=2 บรรทัด) เก็บไว้เผื่อเป็นคำจริงที่ถูกตัด"""
    out, run = [], []

    def flush():
        if run:
            joined = "".join(c for c in run if c.isalpha())
            if len(joined) > 3 and len(run) <= 2:
                out.append(joined)
            run.clear()

    for ln in md.split("\n"):
        s = ln.strip()
        if len(s) == 1:                 # char เดี่ยวทุกชนิด (ตัวอักษร/เลข/สัญลักษณ์/bullet)
            run.append(s)
            continue
        flush()
        out.append(ln)
    flush()
    return "\n".join(out)


def _post_process(md: str, keep_garble: bool, page_start: int = 1) -> str:
    # ใส่ marker [หน้า N] แทน page-break placeholder (เริ่มนับตาม --pages ถ้ามี)
    parts = md.split(PAGE_BREAK)
    md = "\n\n".join(f"[หน้า {page_start+i}]\n{p.strip()}" for i, p in enumerate(parts) if p.strip())
    if not keep_garble:
        md = _collapse_garble(md)
    md = re.sub(r"[ \t]+\n", "\n", md)          # trailing space
    md = re.sub(r"\n{3,}", "\n\n", md)           # ยุบบรรทัดว่างซ้อน
    md = md.replace("&amp;", "&")                # un-escape ที่เจอบ่อย
    return md.strip()


def convert(pdf_path: Path, page_range, keep_garble: bool) -> str:
    from docling.document_converter import DocumentConverter

    conv = DocumentConverter()
    t0 = time.time()
    kw = {}
    if page_range:
        kw["page_range"] = page_range
    res = conv.convert(str(pdf_path), **kw)
    n = res.document.num_pages()
    md = res.document.export_to_markdown(
        page_break_placeholder=PAGE_BREAK,
        image_placeholder=IMG_MARK,
    )
    md = _post_process(md, keep_garble, page_start=page_range[0] if page_range else 1)
    dt = time.time() - t0
    print(f"✓ {n} หน้า ใน {dt:.0f}s ({dt/max(n,1):.0f}s/หน้า) → {len(md):,} ตัวอักษร", file=sys.stderr)
    return md


def main():
    ap = argparse.ArgumentParser(description="PDF → Markdown สะอาด ด้วย Docling (local, free)")
    ap.add_argument("input", type=Path, help="ไฟล์ PDF")
    ap.add_argument("-o", "--output", type=Path, help="ไฟล์ .md ออก (ดีฟอลต์: ชื่อเดียวกับ input)")
    ap.add_argument("--pages", help="ช่วงหน้า เช่น 1-50 (ดีฟอลต์: ทั้งไฟล์)")
    ap.add_argument("--keep-garble", action="store_true", help="ไม่ทิ้งบรรทัดตัวอักษรเดี่ยว (debug)")
    args = ap.parse_args()

    if not args.input.exists():
        sys.exit(f"ไม่พบไฟล์: {args.input}")

    page_range = None
    if args.pages:
        m = re.match(r"^(\d+)-(\d+)$", args.pages.strip())
        if not m:
            sys.exit("--pages ต้องเป็นรูปแบบ N-M เช่น 1-50")
        page_range = (int(m.group(1)), int(m.group(2)))

    md = convert(args.input, page_range, args.keep_garble)
    out = args.output or args.input.with_suffix(".md")
    out.write_text(md, encoding="utf-8")
    print(f"เขียนแล้ว: {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
