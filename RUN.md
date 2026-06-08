# Hermes AI Skill Hub — วิธีรันระบบ

## สิ่งที่ต้องรัน

| Service | Port | หน้าที่ |
|---------|------|---------|
| Backend (FastAPI) | 8000 | API + Telegram Bot polling |
| Frontend (app.html) | 8080 | Web UI |

---

## 1. เตรียม Environment

```bash
cd /Users/narisarapaewpairee/Projects/hermes-ai-skill-hub

# Activate virtual environment
source .venv/bin/activate
```

---

## 2. รัน Backend

```bash
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

เห็นแบบนี้ถือว่าปกติ:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
🤖 Telegram bot polling started (pid=xxxxx)
```

> **หมายเหตุ:** อย่าใช้ `--reload` เพราะจะทำให้ Telegram bot polling ซ้ำ

---

## 3. รัน Frontend

เปิด terminal ใหม่:

```bash
cd /Users/narisarapaewpairee/Projects/hermes-ai-skill-hub
python3 -m http.server 8080
```

เปิดเบราว์เซอร์:
```
http://localhost:8080/app.html
```

---

## 4. Login

| Email | Password |
|-------|----------|
| narisara.pa@shareinvestor.com | (ตามที่ตั้งไว้) |

---

## 5. Telegram Bot

Bot ทำงานอัตโนมัติเมื่อ backend รันอยู่ ไม่ต้องรันแยก

**เชื่อมต่อครั้งแรก:**
```
/start narisara.pa@shareinvestor.com
```

**Commands:**
```
/skills   — ดู Skill ของคุณ
/store    — ดู Skill Store
```

หรือพิมพ์ข้อความได้เลย เช่น `สร้างรายงานการประชุม`

---

## 6. หยุด Services

```bash
# หยุด backend
pkill -f "uvicorn main:app"

# หยุด frontend
pkill -f "http.server 8080"
```

---

## Troubleshooting

| ปัญหา | วิธีแก้ |
|-------|---------|
| Port 8000 ถูกใช้อยู่ | `pkill -f "uvicorn main:app"` |
| Telegram ไม่ตอบ | ตรวจสอบว่า backend รันอยู่ และเห็น `Telegram bot polling started` |
| Database error | ตรวจสอบ PostgreSQL: `psql -U hermes_user -d hermes_db` |
| Module not found | `pip install -r requirements.txt` |
