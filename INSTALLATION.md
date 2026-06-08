# 🚀 Hermes AI Skill Hub - Installation Guide

แนวทางการติดตั้ง Hermes AI Skill Hub ให้พร้อมใช้งาน

## ✅ ข้อกำหนดเบื้องต้น (Prerequisites)

ให้ตรวจสอบว่าเครื่องของคุณมี:

- **Python 3.8+** - [Download](https://www.python.org/)
- **PostgreSQL 12+** - [Download](https://www.postgresql.org/download/)
- **Node.js 14+** (Optional สำหรับ Frontend) - [Download](https://nodejs.org/)
- **Docker & Docker Compose** (Optional สำหรับ Full Stack) - [Download](https://www.docker.com/)
- **Git** - [Download](https://git-scm.com/)

### ตรวจสอบเวอร์ชั่น

```bash
python --version      # ต้องเป็น 3.8+
psql --version        # ต้องเป็น 12+
git --version
docker --version      # (optional)
```

---

## 📥 วิธีการติดตั้ง

### ตัวเลือก A: แบบ Traditional (ไม่ใช้ Docker)

#### 1. Clone Repository

```bash
git clone https://github.com/narisarapaewpairee/hermes-ai-skill-hub.git
cd hermes-ai-skill-hub
```

#### 2. รัน Setup Script

```bash
bash setup.sh
```

สคริปต์จะ:
- ✅ สร้าง Virtual Environment
- ✅ ติดตั้ง Dependencies
- ✅ สร้างไฟล์ .env

#### 3. ตั้งค่า PostgreSQL

```bash
# เข้า PostgreSQL
psql -U postgres

# สร้างผู้ใช้ใหม่
CREATE USER hermes_user WITH PASSWORD 'hermes_password';

# สร้างฐานข้อมูล
CREATE DATABASE hermes_db OWNER hermes_user;

# ให้สิทธิ์
GRANT ALL PRIVILEGES ON DATABASE hermes_db TO hermes_user;

# ออก
\q
```

#### 4. ตั้งค่า .env

แก้ไขไฟล์ `.env` ที่ root directory:

```env
# Database
DATABASE_URL=postgresql://hermes_user:hermes_password@localhost:5432/hermes_db

# Backend
BACKEND_URL=http://localhost:8000
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# Telegram (ค่า placeholder)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHANNEL_ID=-100123456789

# Claude API (จำเป็น)
ANTHROPIC_API_KEY=sk-ant-...your_key...

# Environment
ENVIRONMENT=development
DEBUG=True
```

**⚠️ สำคัญ:**
- `ANTHROPIC_API_KEY` - สร้างจาก [console.anthropic.com](https://console.anthropic.com)
- ไม่ควร commit `.env` ลงใน Git

#### 5. Initialize Database

```bash
# Activate virtual environment (ถ้ายังไม่ได้)
source .venv/bin/activate

# รัน initialization script
python backend/init_db.py
```

ผลลัพธ์ที่คาดหวัง:
```
✅ Database tables created successfully!
✅ Added 4 sample skills!
✅ Database is ready!
```

#### 6. รัน Backend Server

```bash
# ยังคงใน virtual environment
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

ให้รอจนเห็น:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

#### 7. รัน Frontend (Terminal ใหม่)

```bash
# ที่ root directory
python -m http.server 8080
```

ให้รอจนเห็น:
```
Serving HTTP on 0.0.0.0 port 8080
```

#### 8. เปิดในเบราว์เซอร์

```
http://localhost:8080
```

---

### ตัวเลือก B: แบบ Docker Compose (Recommended)

#### 1. Clone Repository

```bash
git clone https://github.com/narisarapaewpairee/hermes-ai-skill-hub.git
cd hermes-ai-skill-hub
```

#### 2. ตั้งค่า .env

```bash
cp .env.example .env
# แก้ไข .env ด้วย editor ที่คุณชอบ
```

#### 3. รัน Docker Compose

```bash
docker-compose up -d
```

Docker จะสร้าง containers:
- `hermes_postgres` - PostgreSQL
- `hermes_backend` - FastAPI
- `hermes_n8n` - n8n Workflow
- `hermes_redis` - Redis Cache

#### 4. ตรวจสอบ Containers

```bash
docker-compose ps
```

ควรเห็น:
```
NAME                COMMAND                STATUS
hermes_postgres     postgres               Up
hermes_backend      uvicorn...             Up
hermes_n8n         n8n                    Up
hermes_redis       redis...               Up
```

#### 5. ดูลอก (Optional)

```bash
# Backend logs
docker-compose logs -f backend

# PostgreSQL logs
docker-compose logs -f postgres

# n8n logs
docker-compose logs -f n8n
```

#### 6. เปิดในเบราว์เซอร์

```
Frontend: http://localhost:8080
Backend API: http://localhost:8000
API Docs: http://localhost:8000/docs
n8n: http://localhost:5678
```

---

## 🧪 การทดสอบระบบ

### Test 1: Backend Health Check

```bash
curl http://localhost:8000/health
```

ควรได้:
```json
{"status": "healthy"}
```

### Test 2: ดูรายชื่อ Skills

```bash
curl http://localhost:8000/api/skills/list
```

### Test 3: สร้าง Skill ใหม่

```bash
curl -X POST http://localhost:8000/api/skills/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Skill",
    "description": "ทดสอบ",
    "owner": "test@example.com",
    "department": "ir"
  }'
```

### Test 4: ทดสอบ Hermes Agent

```bash
# ที่ root directory
python -c "
from hermes_bridge.agent import HermesAgent
agent = HermesAgent()
response = agent.chat('สวัสดี ฉันต้องสรุมเอกสาร')
print(response)
"
```

### Test 5: ทดสอบ Telegram Bot

```bash
python -c "
from telegram.bot import TelegramBot
bot = TelegramBot()
result = bot.send_message('🧪 Test message from Hermes')
print('Message sent!' if result else 'Using mock mode')
"
```

---

## 🛑 Troubleshooting

### ❌ Error: "DATABASE_URL not set"

**วิธีแก้:**
```bash
# ตรวจสอบไฟล์ .env อยู่ที่ root directory
ls -la .env

# ตรวจสอบว่า .env มี DATABASE_URL
cat .env | grep DATABASE_URL
```

### ❌ Error: "Connection refused" PostgreSQL

**วิธีแก้:**
```bash
# ตรวจสอบ PostgreSQL ทำงานหรือไม่
ps aux | grep postgres

# หรือเปิด PostgreSQL
brew services start postgresql  # macOS
sudo service postgresql start   # Linux

# ทดสอบเชื่อมต่อ
psql -U hermes_user -d hermes_db
```

### ❌ Error: "Port 8000 already in use"

**วิธีแก้:**
```bash
# ใช้ port อื่น
uvicorn backend.main:app --port 8001

# หรือหาว่าใครใช้ port 8000
lsof -i :8000
```

### ❌ Error: "ModuleNotFoundError: No module named 'anthropic'"

**วิธีแก้:**
```bash
# ตรวจสอบว่า virtual environment active
source .venv/bin/activate

# ติดตั้ง dependencies อีกครั้ง
pip install -r backend/requirements.txt
```

---

## 📊 Architecture ที่ติดตั้งเสร็จ

```
hermes-ai-skill-hub/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── models.py            # Database models
│   ├── schemas.py           # Pydantic schemas
│   ├── database.py          # Database connection
│   ├── init_db.py           # Database initialization
│   └── requirements.txt
├── hermes-bridge/
│   └── agent.py             # Claude Agent
├── telegram/
│   └── bot.py               # Telegram Bot
├── n8n/
│   └── workflows.json       # Workflow definitions
├── frontend/
│   └── index.html           # Web UI
├── docker-compose.yml       # Docker configuration
├── setup.sh                 # Setup script
├── .env                     # Environment variables
└── README.md
```

---

## 🚀 Next Steps

### 1. ตั้งค่า Telegram Bot (Optional)

```bash
# 1. เปิด Telegram → ค้นหา @BotFather
# 2. ส่ง /start
# 3. ส่ง /newbot
# 4. ตั้งชื่อและ username
# 5. คัดลอก token
# 6. ใส่ใน .env: TELEGRAM_BOT_TOKEN=...
```

### 2. ตั้งค่า n8n Workflows

```bash
# เปิด http://localhost:5678
# สร้าง webhook สำหรับ skill review
# ตั้ง cron สำหรับ daily summary
```

### 3. ทดลองสร้าง Skill

```
1. เปิด http://localhost:8080
2. ดูเมนู Dashboard
3. คลิก "Create New Skill"
4. กรอกข้อมูล
5. ทดสอบใช้งาน
```

---

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Anthropic API Documentation](https://docs.anthropic.com/)
- [n8n Documentation](https://docs.n8n.io/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

---

## 💬 Support

หากมีปัญหา:
1. ตรวจสอบ Troubleshooting section
2. ดูลอก: `docker-compose logs`
3. ตรวจสอบ .env configuration
4. ทดสอบ endpoints ด้วย curl

---

## ✅ Checklist เมื่อติดตั้งเสร็จ

- [ ] ✅ Backend ทำงาน (http://localhost:8000/health)
- [ ] ✅ Frontend เปิดได้ (http://localhost:8080)
- [ ] ✅ Database มี sample skills
- [ ] ✅ API endpoints ทำงาน
- [ ] ✅ Hermes Agent ตอบได้
- [ ] ✅ .env มี API keys ทั้งหมด

---

**เสร็จแล้ว! 🎉 Ready to use Hermes AI Skill Hub!**
