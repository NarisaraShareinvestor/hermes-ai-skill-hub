#!/usr/bin/env python3
"""docling_server.py — HTTP sidecar รอบ Docling layout model สำหรับ Hermes backend.

backend POST ไฟล์ PDF (multipart) มา → คืน bbox ของรูป/กราฟ/ตารางต่อหน้า (normalize 0..1)
ให้ backend crop ด้วย pymupdf. แยกเป็น container ต่างหากเพราะ Docling หนัก (torch+layout model)
+ ช้า — ไม่อยากให้ถ่วง/บวม backend หลัก. โหลด model ครั้งเดียวตอน startup (warm) แล้ว reuse.

รันใน container: uvicorn docling_server:app --host 0.0.0.0 --port 8000
backend เรียกผ่าน hermes_network: http://docling:8000/figures
"""
import os
import tempfile

from fastapi import FastAPI, UploadFile, File, Query

from docling_figures import extract_figures, _get_converter

app = FastAPI(title="Hermes Docling Figures")


@app.on_event("startup")
def _warm():
    try:
        _get_converter()   # โหลด layout model ล่วงหน้า → request แรกไม่ช้า
        print("docling converter warmed", flush=True)
    except Exception as e:
        print(f"warm failed: {e}", flush=True)


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/figures")
async def figures(file: UploadFile = File(...), pages: str = Query("")):
    p0, p1 = 1, 10 ** 9
    if pages:
        if "-" in pages:
            a, b = pages.split("-", 1)
            p0, p1 = int(a), int(b)
        else:
            p0 = p1 = int(pages)
    data = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        f.write(data)
        f.flush()
        try:
            return extract_figures(f.name, p0, p1)
        except Exception as e:
            return {"error": str(e), "page_count": 0, "pages": {}}
