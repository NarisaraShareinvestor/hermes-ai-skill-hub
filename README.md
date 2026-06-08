# Hermes AI Skill Hub

โปรเจกต์นี้คือระบบ **Enterprise Personal AI Skill Hub** สำหรับงานสาย AI Engineer และรูปแบบการทำงานที่เกี่ยวข้องกับ ShareInvestor / Investor Relations

ระบบนี้ไม่ได้เป็นเพียง Chatbot ทั่วไป แต่เป็นแพลตฟอร์มที่ช่วยให้พนักงานแต่ละคนมี **AI ผู้ช่วยส่วนตัว** และสามารถเปลี่ยน Workflow ที่ใช้ซ้ำบ่อย ๆ ให้กลายเป็น **AI Skill** เพื่อนำกลับมาใช้ซ้ำ แชร์ให้ทีม หรือเผยแพร่ให้ทั้งบริษัทใช้งานได้

---

## แนวคิดของโปรเจกต์

ระบบนี้ออกแบบให้พนักงานแต่ละคนมี **Personal AI Assistant** ของตัวเอง
แต่ละแผนกมี **Department Workspace** หรือพื้นที่ทำงานของทีม
เมื่อมี Skill หรือ Workflow ที่ใช้งานดี สามารถแชร์จากระดับส่วนตัวไปยังระดับทีม และต่อยอดไปเป็น Skill กลางของบริษัทได้

แนวคิดหลักคือ:

```text
Personal AI → Team Skill Library → Company Skill Store
```

หรืออธิบายง่าย ๆ คือ:

1. พนักงานแต่ละคนมี AI ผู้ช่วยส่วนตัว
2. ผู้ใช้สามารถสร้าง Skill จากงานที่ทำซ้ำบ่อย ๆ ได้
3. Skill ที่ดีสามารถแชร์เข้า Team Library ได้
4. Skill ที่ผ่านการตรวจสอบสามารถเผยแพร่เป็น Company Skill ได้
5. สมาชิกในทีมสามารถเลือกติดตั้ง Skill ที่ต้องการไปยังผู้ช่วยส่วนตัวของตัวเองได้

---

## หลักการสำคัญของการแชร์ Skill

ระบบนี้ควรแยกคำว่า **Share, Approve, Install และ Publish** ออกจากกันอย่างชัดเจน

### 1. Share

หมายถึงการส่ง Skill จากระดับส่วนตัวเข้าไปยังทีม เพื่อให้ทีมพิจารณา

ตัวอย่าง:

```text
User สร้าง Skill ส่วนตัว
        ↓
กด Share to Team
        ↓
Skill เข้าสถานะ Pending Team Review
```

การ Share ไม่ได้แปลว่าทุกคนในทีมจะได้ใช้ทันที
แต่เป็นการส่ง Skill เข้าไปให้ทีมตรวจสอบก่อน

---

### 2. Approve

หมายถึงการอนุมัติให้ Skill นั้นเข้าไปอยู่ใน Team Skill Library

ผู้ที่กด Approve ควรเป็น:

* Team Lead
* AI Admin
* Project Owner
* คนที่มีสิทธิ์ดูแล Skill ของทีมนั้น

ตัวอย่าง:

```text
Skill ถูก Share เข้า Team
        ↓
Team Lead ตรวจสอบ
        ↓
กด Approve to Team
        ↓
Skill เข้า Team Skill Library
```

---

### 3. Install

หมายถึงสมาชิกในทีมเลือกนำ Skill ที่อยู่ใน Team Skill Library ไปใช้กับ Personal AI Assistant ของตัวเอง

ตัวอย่าง:

```text
Skill อยู่ใน Team Skill Library
        ↓
สมาชิกในทีมเห็น Skill
        ↓
กด Add to My Assistant
        ↓
Skill ถูกติดตั้งใน Personal AI Assistant ของคนนั้น
```

สมาชิกในทีมไม่จำเป็นต้องรับ Skill ทุกตัว
ใครอยากใช้ก็กดติดตั้ง ใครไม่อยากใช้ก็ไม่ต้องทำอะไร

---

### 4. Publish

หมายถึงการเผยแพร่ Skill จากระดับทีมไปยังระดับบริษัท

ตัวอย่าง:

```text
Team Skill ใช้งานได้ดี
        ↓
กด Submit to Company Review
        ↓
AI Admin หรือผู้ดูแลระบบตรวจสอบ
        ↓
กด Publish
        ↓
Skill เข้า Company Skill Store
```

เมื่อ Skill ถูก Publish แล้ว ทีมอื่นสามารถนำไปใช้ต่อได้

---

## Flow การทำงานของ Skill Sharing

Flow หลักของระบบควรเป็นแบบนี้:

```text
Draft Skill
        ↓
Private Skill
        ↓
Share to Team
        ↓
Pending Team Review
        ↓
Approve to Team
        ↓
Team Skill Library
        ↓
Member installs to Personal Assistant
        ↓
Submit to Company Review
        ↓
Company Published
```

---

## ตัวอย่างการใช้งานจริง

สมมติผู้ใช้สร้าง Skill ชื่อ:

```text
Annual Report Summarizer
```

Flow จะเป็นดังนี้:

1. ผู้ใช้สร้าง Skill ส่วนตัวชื่อ `Annual Report Summarizer`
2. ทดลองใช้กับ Annual Report จริง
3. เห็นว่า Skill ใช้งานดี จึงกด `Share to IR Team`
4. Skill เข้าสถานะ `Pending Team Review`
5. n8n ส่งข้อความแจ้งเตือนไปยัง Telegram Channel
6. Team Lead ตรวจสอบรายละเอียดของ Skill
7. Team Lead กด `Approve to Team`
8. Skill เข้าไปอยู่ใน `IR Team Skill Library`
9. สมาชิกในทีม IR เห็น Skill นี้
10. สมาชิกที่ต้องการใช้งานกด `Add to My Assistant`
11. ถ้า Skill นี้มีประโยชน์กับทีมอื่น สามารถกด `Submit to Company Review`
12. ถ้าผ่านการตรวจสอบ จะถูก Publish ไปยัง `Company Skill Store`

---

## ส่วนประกอบหลักของระบบ

### Personal AI Assistant

ผู้ช่วย AI ส่วนตัวของแต่ละคน ใช้สำหรับทำงานประจำวัน เช่น สรุปเอกสาร เขียนอีเมล ตรวจภาษา หรือเรียกใช้ Skill ที่ติดตั้งไว้

---

### Department Workspace

พื้นที่ทำงานของแต่ละแผนก ใช้สำหรับเก็บ Skill ของทีม เอกสารของทีม และ Workflow ที่เกี่ยวข้องกับงานของแผนกนั้น

---

### Team Skill Library

พื้นที่เก็บ Skill ที่ผ่านการอนุมัติให้ใช้ภายในทีมแล้ว

สมาชิกในทีมสามารถดู ทดลองใช้ และเลือกติดตั้ง Skill เหล่านี้ไปยัง Personal AI Assistant ของตัวเองได้

---

### Company Skill Store

พื้นที่กลางของบริษัทสำหรับเก็บ Skill ที่ผ่านการตรวจสอบแล้ว และสามารถให้หลายทีมใช้งานร่วมกันได้

---

### Skill Registry

ระบบจัดเก็บข้อมูลของ Skill ทั้งหมด เช่น ชื่อ Skill เจ้าของ Skill เวอร์ชัน สถานะ ระดับการมองเห็น และสิทธิ์การใช้งาน

---

### Skill Sharing Workflow

กระบวนการแชร์ Skill จากระดับส่วนตัวไปยังทีม หรือจากทีมไปยังบริษัท

---

### Telegram Approval Channel

ช่องทาง Telegram สำหรับแจ้งเตือนเมื่อมี Skill ใหม่ถูกส่งเข้ามา Review

ตัวอย่างปุ่มใน Telegram:

```text
Approve to Team
Reject
Request Edit
```

หรือในกรณีส่งเข้าระดับบริษัท:

```text
Publish to Company
Reject
Request Edit
```

---

### n8n Automation

ระบบ Automation สำหรับจัดการ Workflow เช่น:

* แจ้งเตือนเมื่อมี Skill ใหม่ถูก Share
* ส่งข้อความไปยัง Telegram
* รับผลการ Approve หรือ Reject
* เปลี่ยนสถานะของ Skill
* แจ้งเตือนเจ้าของ Skill
* ส่ง Skill ที่ผ่านการอนุมัติไปยัง Team Library หรือ Company Skill Store

---

### Hermes Agent / AI Skill Engine

ตัวกลางสำหรับสั่งงาน AI เลือก Skill และประมวลผลคำสั่งต่าง ๆ

Hermes Agent สามารถทำหน้าที่เป็น AI Skill Engine เช่น:

* เข้าใจคำสั่งของผู้ใช้
* เลือก Skill ที่เหมาะสม
* เรียกใช้ Skill
* สรุปผลลัพธ์
* ช่วยตรวจสอบ Skill ก่อนเผยแพร่
* แนะนำว่า Skill ไหนควรแชร์ให้ทีมอื่น

---

## แผนกที่เกี่ยวข้อง

ระบบนี้สามารถแยกการใช้งานตามแผนกได้ เช่น

### IR Team

ทีม Investor Relations ใช้สำหรับ:

* สรุป Annual Report
* สรุป Financial Statement
* สรุป ESG Report
* สร้าง FAQ สำหรับนักลงทุน
* สรุป Company Announcement
* ช่วยตอบคำถามจากเอกสาร IR

ตัวอย่าง Skill:

* Annual Report Summarizer
* Financial Highlight Extractor
* Dividend Policy Finder
* AGM FAQ Generator
* Announcement Summary Bot

---

### Dev Team

ทีมพัฒนา ใช้สำหรับ:

* สรุป Bug
* ตรวจ Code
* สร้าง API Document
* วิเคราะห์ Log
* สร้าง Deployment Checklist

ตัวอย่าง Skill:

* Code Review Assistant
* Bug Summary Assistant
* API Doc Generator
* Log Analyzer
* Deployment Checklist Bot

---

### Content / SEO Team

ทีมคอนเทนต์ ใช้สำหรับ:

* เขียนบทความ SEO
* ตรวจภาษาอังกฤษ
* ปรับ Copy บนเว็บไซต์ IR
* สร้าง Meta Description
* แนะนำ Keyword

ตัวอย่าง Skill:

* SEO IR Article Writer
* Meta Description Generator
* IR Website Copy Reviewer
* Translation EN/TH Assistant
* Keyword Suggestion Bot

---

### QA Team

ทีมทดสอบ ใช้สำหรับ:

* สร้าง Test Case
* สรุป Bug Report
* ช่วยตรวจ Regression Test
* เขียนขั้นตอนการทดสอบ

ตัวอย่าง Skill:

* Test Case Generator
* Bug Reproduction Writer
* UI Checklist Bot
* Regression Test Summary

---

### Sales / Support Team

ทีมขายและซัพพอร์ต ใช้สำหรับ:

* สรุปคำถามลูกค้า
* เขียน Email
* สร้าง FAQ
* สรุป Meeting
* จัดกลุ่ม Lead

ตัวอย่าง Skill:

* Client Email Draft
* FAQ Answer Bot
* Meeting Summary Bot
* Lead Summary Bot

---

## เป้าหมายของ MVP

เวอร์ชันแรกของระบบควรทำให้ผู้ใช้สามารถทำสิ่งเหล่านี้ได้:

1. สร้าง Skill ใหม่ได้
2. ใช้ Skill ที่สร้างไว้ได้
3. แชร์ Skill ให้ทีมของตัวเองได้
4. ให้ Team Lead อนุมัติหรือปฏิเสธ Skill ได้
5. ให้สมาชิกในทีมเลือกติดตั้ง Skill ไปยัง Personal AI Assistant ของตัวเองได้
6. ส่ง Skill ที่ดีเข้าสู่ Company Review ได้
7. อนุมัติหรือปฏิเสธ Skill ผ่าน Telegram ได้
8. เผยแพร่ Skill ที่ผ่านการอนุมัติไปยัง Company Skill Store ได้

---

## สถานะของ Skill

Skill แต่ละตัวควรมีสถานะ เช่น

### Draft

กำลังสร้างหรือแก้ไข ยังไม่พร้อมใช้งานจริง

### Private

ใช้ได้เฉพาะเจ้าของ Skill

### Pending Team Review

ถูกแชร์เข้า Team แล้ว แต่รอ Team Lead หรือ AI Admin ตรวจสอบ

### Team Available

ผ่านการอนุมัติแล้ว และพร้อมใช้งานใน Team Skill Library

### Installed

สมาชิกเลือกติดตั้ง Skill นี้ไปยัง Personal AI Assistant ของตัวเองแล้ว

### Pending Company Review

ถูกส่งจากระดับทีมเข้าสู่การตรวจสอบระดับบริษัท

### Company Published

ผ่านการอนุมัติแล้ว และถูกเผยแพร่ใน Company Skill Store

### Rejected

ไม่ผ่านการอนุมัติ

### Request Edit

ต้องแก้ไขก่อนถึงจะอนุมัติได้

### Deprecated

Skill เก่าที่ไม่แนะนำให้ใช้แล้ว

### Blocked

Skill ที่ถูกปิดใช้งานเพราะมีความเสี่ยงหรือไม่ผ่านเงื่อนไข

---

## ระดับการมองเห็นของ Skill

Skill ควรมีระดับการเข้าถึง เช่น

### Private

ใช้ได้เฉพาะเจ้าของ Skill

### Team

ใช้ได้เฉพาะภายในทีม

### Shared

แชร์ให้ทีมอื่นขอใช้งานได้

### Company

ทุกทีมในบริษัทสามารถใช้งานได้

---

## ปุ่มที่ควรมีในระบบ

### สำหรับเจ้าของ Skill

* Use Skill
* Edit Skill
* Share to Team
* Submit to Company Review
* Delete Draft

### สำหรับ Team Lead หรือ AI Admin

* Approve to Team
* Reject
* Request Edit
* Publish to Company
* Block Skill

### สำหรับสมาชิกในทีม

* Try Skill
* Add to My Assistant
* Remove from My Assistant
* Set as Favorite
* View Details

---

## Tech Stack

* Frontend: HTML ในช่วงแรก และอาจพัฒนาเป็น React ในอนาคต
* Backend: FastAPI
* Database: PostgreSQL
* Automation: n8n
* Notification: Telegram
* AI Engine: Hermes Agent หรือ LLM API
* Deployment: Hostinger VPS + Docker

---

## 🚀 วิธีการเริ่มต้นใช้งาน (Getting Started)

### ขั้นตอนการเตรียมสภาพแวดล้อม

#### 1️⃣ ขั้นที่ 1: ตรวจสอบความต้องการ (Requirements)

ก่อนเริ่มต้น ให้ตรวจสอบว่าเครื่องของคุณมี:

```bash
# ตรวจสอบ Python
python --version
# ต้องเป็น Python 3.8 ขึ้นไป

# ตรวจสอบ Node.js (ถ้าต้องใช้ Frontend)
node --version
npm --version

# ตรวจสอบ PostgreSQL (ถ้าใช้ฐานข้อมูล)
psql --version
```

**ความต้องการทั่วไป:**
- Python 3.8+
- pip (Python Package Manager)
- PostgreSQL 12+
- Node.js 14+ (สำหรับ Frontend)
- npm หรือ yarn
- Docker (ถ้าต้องใช้)
- Git

---

#### 2️⃣ ขั้นที่ 2: Clone Project และตั้งค่าไดเรกทอรี

```bash
# ย้ายไปยังที่ที่คุณต้องการ
cd /path/to/your/projects

# Clone project
git clone <repository-url>
cd hermes-ai-skill-hub

# ดูไฟล์และโฟลเดอร์ที่มี
ls -la
```

**โครงสร้างโฟลเดอร์:**

```
hermes-ai-skill-hub/
├── backend/                    # FastAPI Backend Server
├── data/                       # เก็บข้อมูล Skill (JSON, Database)
├── docs/                       # เอกสารอธิบาย
├── hermes-bridge/              # ตัวเชื่อมระหว่าง Hermes Agent กับ Skill
├── n8n/                        # Automation Workflow (n8n)
├── telegram/                   # Integration Telegram
├── index.html                  # Frontend (HTML)
└── README.md                   # ไฟล์นี้
```

---

#### 3️⃣ ขั้นที่ 3: ติดตั้ง Python Dependencies (Backend)

```bash
# เข้าไปในโฟลเดอร์ Backend
cd backend

# สร้าง Virtual Environment
python -m venv venv

# Activate Virtual Environment
# ถ้าใช้ macOS / Linux:
source venv/bin/activate

# ถ้าใช้ Windows:
venv\Scripts\activate

# ติดตั้ง Dependencies
pip install -r requirements.txt
```

**ถ้ายังไม่มี requirements.txt ให้สร้างดังนี้:**

```bash
# สร้างไฟล์ requirements.txt
cat > requirements.txt << EOF
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.0
psycopg2-binary==2.9.9
python-dotenv==1.0.0
requests==2.31.0
pydantic==2.5.0
EOF

# ติดตั้ง
pip install -r requirements.txt
```

---

#### 4️⃣ ขั้นที่ 4: ตั้งค่า Database (PostgreSQL)

```bash
# เปิด PostgreSQL (ถ้าใช้ Mac)
brew services start postgresql

# เข้า PostgreSQL
psql -U postgres

# สร้างฐานข้อมูล
CREATE DATABASE hermes_db;

# สร้าง User ใหม่ (ถ้าต้องการ)
CREATE USER hermes_user WITH PASSWORD 'your_password';

# ให้สิทธิ์
GRANT ALL PRIVILEGES ON DATABASE hermes_db TO hermes_user;

# ออกจาก PostgreSQL
\q
```

---

#### 5️⃣ ขั้นที่ 5: ตั้งค่าไฟล์ Environment (.env)

```bash
# ย้อนไปยัง Root Directory
cd ..

# สร้างไฟล์ .env
cat > .env << EOF
# Database
DATABASE_URL=postgresql://hermes_user:your_password@localhost:5432/hermes_db

# Backend
BACKEND_URL=http://localhost:8000

# Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHANNEL_ID=your_channel_id

# n8n
N8N_URL=http://localhost:5678

# Hermes Agent
HERMES_API_KEY=your_hermes_api_key
HERMES_BASE_URL=http://localhost:3000
EOF
```

**หมายเหตุ:** 
- ทำเป็นตัวอย่างเท่านั้น ให้เปลี่ยนค่าให้ตรงกับ config จริง
- ไม่ควร commit ไฟล์ .env ลงใน Git

---

#### 6️⃣ ขั้นที่ 6: ติดตั้งและรัน Backend

```bash
# เข้าโฟลเดอร์ backend
cd backend

# Activate Virtual Environment อีกครั้ง (ถ้าจำเป็น)
source venv/bin/activate

# รัน FastAPI Server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# ข้อความที่ปรากฏ:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# INFO:     Application startup complete
```

**Backend เริ่มใช้งานแล้ว** ✅

---

#### 7️⃣ ขั้นที่ 7: ตั้งค่า Frontend (HTML)

```bash
# ย้อนไปยัง Root
cd ..

# ตรวจสอบว่า index.html อยู่ที่
ls -la index.html

# ใช้ Python Simple Server ในการรันเซิร์ฟเวอร์
python -m http.server 8080

# หรือถ้าใช้ macOS ลึก ๆ:
python3 -m http.server 8080
```

**เปิดไปที่:** http://localhost:8080 ในเบราว์เซอร์

---

#### 8️⃣ ขั้นที่ 8: เชื่อมต่อ n8n (Automation)

```bash
# ติดตั้ง n8n globally
npm install -g n8n

# หรือใช้ Docker
docker run -it --rm --name n8n -p 5678:5678 n8nio/n8n

# เปิด n8n ที่
# http://localhost:5678
```

---

#### 9️⃣ ขั้นที่ 9: เชื่อมต่อ Telegram

```bash
# สร้าง Telegram Bot ผ่าน BotFather
# 1. เปิด Telegram ค้นหา @BotFather
# 2. พิมพ์ /start
# 3. พิมพ์ /newbot
# 4. ตั้งชื่อ Bot (เช่น hermes_skill_bot)
# 5. ตั้ง username (เช่น @hermes_skill_bot)
# 6. คัดลอก Token (จะได้ประมาณ 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11)

# นำ Token ไปใส่ใน .env
# TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
```

**สร้าง Telegram Channel:**

```
1. สร้าง Channel ใหม่ (Public หรือ Private)
2. ชื่อ เช่น "hermes-skill-approvals"
3. เพิ่ม Bot เข้าไป
4. คัดลอก Channel ID
5. ใส่ใน .env: TELEGRAM_CHANNEL_ID=-100123456789
```

---

### 🔗 การเชื่อมต่อส่วนต่างๆ

#### ความเชื่อมโยง (Data Flow)

```
Frontend (HTML)
      ↓
Backend (FastAPI) ← Database (PostgreSQL)
      ↓
n8n (Automation)
      ↓
Telegram (Notification)
      ↓
Hermes Agent (AI Engine)
```

#### การส่งข้อมูล

```bash
# 1. Frontend ส่ง Request ไปยัง Backend
curl -X POST http://localhost:8000/api/skills/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Annual Report Summarizer",
    "description": "สรุป Annual Report อัตโนมัติ",
    "owner": "user@example.com"
  }'

# 2. Backend บันทึกลงฐานข้อมูล
# INSERT INTO skills (name, description, owner) VALUES (...)

# 3. n8n รับ Event และส่ง Telegram
# Webhook Event → n8n Trigger → Telegram Bot → Telegram Channel

# 4. Hermes Agent ดึงข้อมูล Skill
curl -X GET http://localhost:8000/api/skills/list
```

---

### ⚙️ คำสั่งที่ใช้บ่อย

#### Backend Commands

```bash
# รัน Backend (Development Mode)
cd backend
source venv/bin/activate
uvicorn main:app --reload

# รัน Backend (Production Mode)
uvicorn main:app --host 0.0.0.0 --port 8000

# รัน Database Migration (ถ้ามี)
alembic upgrade head

# ทดสอบ API
curl http://localhost:8000/api/skills/list

# สร้าง Skill ใหม่
curl -X POST http://localhost:8000/api/skills/create \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Skill","description":"Test"}'
```

#### Database Commands

```bash
# เปิด PostgreSQL
psql -U hermes_user -d hermes_db

# ดูตารางทั้งหมด
\dt

# ดูข้อมูล Skill
SELECT * FROM skills;

# ปิด PostgreSQL
\q
```

#### Frontend Commands

```bash
# รัน Frontend (Development)
python -m http.server 8080

# หรือใช้ Node.js
npx http-server -p 8080

# ทำให้ Access ได้จากทุกที่
python -m http.server 0.0.0.0:8080
```

#### Git Commands

```bash
# ดูสถานะ
git status

# สร้าง Branch ใหม่
git checkout -b feature/new-feature

# Commit เปลี่ยนแปลง
git add .
git commit -m "Add new feature"

# Push ไปยัง Remote
git push origin feature/new-feature

# Merge ลงใน Main
git checkout main
git merge feature/new-feature
git push origin main
```

---

### 📝 ตัวอย่างการใช้งานทั้งระบบ

#### สถานการณ์: สร้าง Skill "Annual Report Summarizer"

**ขั้นที่ 1: เปิดหน้าเว็บ**

```
1. เปิด http://localhost:8080
2. กด "Create New Skill"
```

**ขั้นที่ 2: กรอกข้อมูล Skill**

```
Name: Annual Report Summarizer
Description: สรุป Annual Report อัตโนมัติ
Department: IR Team
Owner: john@example.com
```

**ขั้นที่ 3: Backend บันทึกลงฐานข้อมูล**

```bash
# ลงทะเบียน API
POST /api/skills/create
{
  "name": "Annual Report Summarizer",
  "description": "สรุป Annual Report อัตโนมัติ",
  "department": "ir_team",
  "owner": "john@example.com",
  "status": "private"
}
```

**ขั้นที่ 4: ผู้ใช้ทดสอบใช้ Skill**

```
1. อัปโหลด Annual Report (PDF)
2. Hermes Agent ประมวลผล
3. ได้ผลลัพธ์สรุป
```

**ขั้นที่ 5: แชร์เข้าทีม**

```
1. กด "Share to Team"
2. Status เปลี่ยนเป็น "Pending Team Review"
3. n8n ส่ง Notification ไปยัง Telegram
```

**ขั้นที่ 6: Team Lead อนุมัติ (Telegram)**

```
ใน Telegram Channel:
- [Approve to Team] [Reject] [Request Edit]
- Team Lead กด Approve to Team
- Status เปลี่ยนเป็น "Team Available"
```

**ขั้นที่ 7: สมาชิกเลือกติดตั้ง**

```
1. สมาชิก IR Team เห็น Skill
2. กด "Add to My Assistant"
3. Skill ติดตั้งสำเร็จ
```

**ขั้นที่ 8: ส่งเข้า Company Review**

```
1. ผู้ใช้กด "Submit to Company Review"
2. Status: "Pending Company Review"
3. n8n ส่ง Telegram อีกครั้ง
```

**ขั้นที่ 9: Publish ไปยัง Company Skill Store**

```
AI Admin อนุมัติ
Status: "Company Published"
ทีมอื่นสามารถใช้ Skill นี้ได้
```

---

## เป้าหมายระยะยาว

เป้าหมายของโปรเจกต์นี้คือการสร้างระบบที่ช่วยให้บริษัทสามารถเปลี่ยนงานที่ทำซ้ำบ่อย ๆ ให้กลายเป็น AI Skill ที่นำกลับมาใช้ซ้ำได้ และสามารถแชร์ความรู้ระหว่างทีมได้อย่างปลอดภัย

ระบบนี้จะช่วยให้:

* พนักงานทำงานซ้ำ ๆ ได้น้อยลง
* แต่ละทีมสร้าง Skill ของตัวเองได้
* Skill ที่ดีถูกนำไปใช้ซ้ำได้
* บริษัทมีคลังความรู้และ Workflow กลาง
* การใช้งาน AI มีระบบสิทธิ์และการตรวจสอบ
* AI Engineer สามารถควบคุมคุณภาพของ Skill ได้

แนวคิดหลักคือ:

```text
Personal AI → Team Skill Library → Company Skill Store
```

หรืออธิบายง่าย ๆ คือ:

พนักงานแต่ละคนมี AI ผู้ช่วยส่วนตัว
เมื่อเจอ Workflow ที่ดี สามารถบันทึกเป็น Skill
จากนั้นแชร์ให้ทีมตรวจสอบ
ถ้าทีมอนุมัติ Skill จะเข้า Team Skill Library
สมาชิกในทีมเลือกติดตั้ง Skill ได้เอง
ถ้า Skill นั้นมีประโยชน์กับหลายทีม ก็สามารถเผยแพร่ให้ทั้งบริษัทใช้ต่อได้
