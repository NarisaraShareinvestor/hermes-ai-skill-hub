# DocLayout-YOLO figures sidecar — layout model สำหรับฟีเจอร์ "รูปที่เกี่ยวข้อง" ของ Hermes
# แยกจาก backend เพราะ torch + YOLO model หนัก (ไม่อยากบวม/ถ่วง backend หลัก)
FROM python:3.11-slim

WORKDIR /app

# libs สำหรับ opencv (doclayout-yolo) + เรนเดอร์ PDF (pymupdf)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# torch CPU-only (เล็กกว่า default ที่มี CUDA มาก) + doclayout-yolo + เสิร์ฟ
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir \
        doclayout-yolo huggingface_hub pymupdf \
        fastapi "uvicorn[standard]" python-multipart

COPY layout_figures.py layout_server.py /app/

# โหลด YOLO weights ตอน build (ไม่ต้องโหลดตอน runtime)
# || true: ถ้าโหลดพลาด ปล่อยให้ไป fallback โหลดตอน startup แทน (VPS มี internet)
RUN python -c "from layout_figures import _get_model; _get_model()" || true

EXPOSE 8000

CMD ["uvicorn", "layout_server:app", "--host", "0.0.0.0", "--port", "8000"]
