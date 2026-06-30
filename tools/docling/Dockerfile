# Docling figures sidecar — layout model สำหรับฟีเจอร์ "รูปที่เกี่ยวข้อง" ของ Hermes
# แยกจาก backend เพราะ torch + layout model หนัก/ช้า (ไม่อยากบวม/ถ่วง backend หลัก)
FROM python:3.11-slim

WORKDIR /app

# docling ต้องการ libs บางตัวสำหรับเปิด/เรนเดอร์ PDF (pypdfium)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    docling==2.69.1 \
    fastapi "uvicorn[standard]" python-multipart pypdf

# โหลด layout model ตอน build (ไม่ต้องโหลดตอน runtime/ไม่ต้องพึ่ง network ตอนรัน)
# || true: ถ้าโหลดพลาด ปล่อยให้ไป fallback โหลดตอน request แรกแทน (VPS มี internet)
RUN python -c "from docling.utils.model_downloader import download_models; download_models()" || true

COPY docling_figures.py docling_server.py /app/

EXPOSE 8000

CMD ["uvicorn", "docling_server:app", "--host", "0.0.0.0", "--port", "8000"]
