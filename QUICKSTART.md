# ⚡ Quick Start - Hermes AI Skill Hub

เริ่มต้นใช้งาน Hermes AI Skill Hub ใน 5 นาที

---

## 🚀 1️⃣ Clone & Setup (2 นาที)

```bash
# Clone project
git clone https://github.com/narisarapaewpairee/hermes-ai-skill-hub.git
cd hermes-ai-skill-hub

# รัน setup script
bash setup.sh
```

---

## ⚙️ 2️⃣ Configure .env (1 นาที)

```bash
# แก้ไข .env ด้วย editor ที่คุณชอบ
# อย่างน้อยต้องมี:
# - DATABASE_URL (PostgreSQL)
# - ANTHROPIC_API_KEY (Claude API)

nano .env
```

**ค่า Minimal ที่ต้องมี:**
```env
DATABASE_URL=postgresql://hermes_user:hermes_password@localhost:5432/hermes_db
ANTHROPIC_API_KEY=sk-ant-...your_key...
```

---

## 🗄️ 3️⃣ Initialize Database (1 นาที)

```bash
# Activate virtual environment
source .venv/bin/activate

# Initialize database
python backend/init_db.py
```

ควรเห็น:
```
✅ Database tables created successfully!
✅ Added 4 sample skills!
✅ Database is ready!
```

---

## 🚀 4️⃣ Run System (1 นาที)

### Terminal 1 - Backend Server

```bash
source .venv/bin/activate
python -m uvicorn backend.main:app --reload
```

ให้รอจนเห็น:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Terminal 2 - Frontend Server

```bash
cd /path/to/hermes-ai-skill-hub
python -m http.server 8080
```

ให้รอจนเห็น:
```
Serving HTTP on 0.0.0.0 port 8080
```

---

## ✅ 5️⃣ Verify Installation

### Open Browser

```
http://localhost:8080
```

### Test Backend API

```bash
# Health check
curl http://localhost:8000/health

# Get skills
curl http://localhost:8000/api/skills/list

# API docs
curl http://localhost:8000/docs
```

---

## 📝 Create Your First Skill

### ผ่าน API

```bash
curl -X POST http://localhost:8000/api/skills/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My First Skill",
    "description": "My awesome skill",
    "owner": "you@example.com",
    "department": "ir"
  }'
```

---

## 🧪 Test Hermes Agent

```python
from hermes_bridge.agent import HermesAgent

agent = HermesAgent()
response = agent.chat(
    "สรุม Annual Report",
    user_context={"email": "you@example.com", "department": "ir"}
)
print(response)
```

---

## 🛑 Troubleshooting

| Problem | Solution |
|---------|----------|
| Database error | ตรวจสอบ PostgreSQL ทำงาน: `psql -U hermes_user -d hermes_db` |
| Port 8000 busy | ใช้ port อื่น: `uvicorn backend.main:app --port 8001` |
| API key error | ตรวจสอบ ANTHROPIC_API_KEY ใน .env |
| Module not found | รัน: `pip install -r backend/requirements.txt` |

---

## 📚 Next Steps

1. **อ่าน Documentation**
   - [README.md](README.md) - สำหรับเข้าใจ concept
   - [INSTALLATION.md](INSTALLATION.md) - สำหรับ setup ละเอียด

2. **ตั้งค่า Telegram** (Optional)
   - สร้าง Bot ที่ [@BotFather](https://t.me/BotFather)
   - ใส่ token ใน .env

3. **ตั้งค่า n8n** (Optional)
   - เปิด http://localhost:5678
   - สร้าง workflows สำหรับ approval

4. **สร้าง Skills**
   - ทำให้ตรงกับ workflow ทีมของคุณ
   - Share ให้ทีมใช้ต่อ

---

## 🎯 Goals เสร็จแล้ว

✅ Backend FastAPI ทำงาน  
✅ Database PostgreSQL เตรียมพร้อม  
✅ Frontend เปิดได้  
✅ Hermes Agent พร้อม  
✅ Telegram Bot พร้อม (mock mode)  
✅ API documentation พร้อม  

---

**🎉 Ready to use! Enjoy Hermes AI Skill Hub!**
