#!/usr/bin/env python3
"""layout_server.py — HTTP sidecar รอบ DocLayout-YOLO สำหรับ Hermes backend.

backend POST ไฟล์ PDF (multipart) มา → คืน bbox ของรูป/กราฟ/ตารางต่อหน้า (normalize 0..1)
ให้ backend crop ด้วย pymupdf. แยกเป็น container เพราะ torch + YOLO model หนัก — ไม่ให้ถ่วง backend.
โหลด model ครั้งเดียวตอน startup (warm) แล้ว reuse ทุก request.

รันใน container: uvicorn layout_server:app --host 0.0.0.0 --port 8000
backend เรียกผ่าน hermes_network: http://doclayout:8000/figures
"""
import tempfile

from fastapi import FastAPI, UploadFile, File, Query

from layout_figures import extract_figures, _get_model

app = FastAPI(title="Hermes DocLayout-YOLO Figures")


@app.on_event("startup")
def _warm():
    try:
        _get_model()
        print("doclayout-yolo model warmed", flush=True)
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
