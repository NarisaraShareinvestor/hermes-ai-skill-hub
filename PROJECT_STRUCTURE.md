# 📂 Project Structure

โครงสร้างไฟล์ของ Hermes AI Skill Hub

```
hermes-ai-skill-hub/
│
├── 📄 README.md                    # แนวคิด concept ของระบบ
├── 📄 INSTALLATION.md              # วิธีการติดตั้งแบบละเอียด
├── 📄 QUICKSTART.md                # เริ่มต้นใช้งาน 5 นาที
├── 📄 PROJECT_STRUCTURE.md         # ไฟล์นี้
│
├── 🔧 SETUP FILES
├── setup.sh                        # Setup script (bash)
├── docker-compose.yml              # Docker configuration
├── Dockerfile.backend              # Backend Docker image
│
├── ⚙️ ENVIRONMENT
├── .env                            # Environment variables (ต้องสร้างเอง)
├── .env.example                    # Template สำหรับ .env
├── .gitignore                      # Git ignore rules
│
├── 🧠 BACKEND (FastAPI)
├── backend/
│   ├── main.py                     # FastAPI app & endpoints
│   ├── models.py                   # SQLAlchemy database models
│   │   ├── Skill
│   │   ├── SkillInstallation
│   │   ├── AuditLog
│   │   └── ApprovalQueue
│   ├── schemas.py                  # Pydantic request/response schemas
│   ├── database.py                 # Database connection & session
│   ├── init_db.py                  # Database initialization script
│   └── requirements.txt             # Python dependencies
│
├── 🤖 AI AGENT (Hermes Bridge)
├── hermes-bridge/
│   └── agent.py                    # Claude AI Agent
│       ├── chat()
│       ├── select_skill()
│       ├── generate_skill_prompt()
│       ├── check_permission()
│       └── analyze_feedback()
│
├── 📱 TELEGRAM INTEGRATION
├── telegram/
│   └── bot.py                      # Telegram Bot
│       ├── send_skill_review_notification()
│       ├── send_approval_notification()
│       ├── send_daily_summary()
│       └── send_alert()
│
├── ⚡ N8N WORKFLOWS
├── n8n/
│   └── workflows.json              # Workflow definitions
│       ├── Skill Review Workflow
│       ├── Document Indexing Workflow
│       ├── Daily AI Usage Summary
│       └── Skill Quality Monitor
│
├── 🎨 FRONTEND (HTML/CSS/JS)
├── index.html                      # Web UI (design document)
│
└── 📚 DOCUMENTATION
    ├── docs/
    └── (future documentation)
```

---

## 🔄 API Flow

```
Frontend (index.html)
    ↓ HTTP POST/GET/PUT/DELETE
    ↓
Backend (backend/main.py)
    ↓
    ├── Connect to Database (backend/database.py)
    ├── Use Models (backend/models.py)
    └── Return Response (backend/schemas.py)
    ↓
Hermes Agent (hermes-bridge/agent.py)
    ↓ Uses Claude API
    ↓
Telegram Bot (telegram/bot.py)
    ↓ Sends notifications
    ↓
n8n Workflows (n8n/workflows.json)
    ↓ Automation
    ↓
Database & External APIs
```

---

## 📦 Dependencies

### Python (Backend)

```
fastapi==0.104.1         # Web framework
uvicorn==0.24.0          # ASGI server
sqlalchemy==2.0.0        # ORM
psycopg2-binary==2.9.9   # PostgreSQL adapter
pydantic==2.5.0          # Data validation
anthropic==0.7.1         # Claude API
python-dotenv==1.0.0     # .env support
requests==2.31.0         # HTTP client
alembic==1.13.0          # Database migrations
```

### External Services

```
PostgreSQL 12+           # Database
n8n                      # Workflow automation
Telegram Bot API         # Notifications
Anthropic Claude API     # AI Model
Redis (optional)         # Caching
```

---

## 🗄️ Database Schema

### Main Tables

```sql
-- Skills registry
TABLE skills
  ├── id (PK)
  ├── name (unique)
  ├── description
  ├── owner
  ├── department
  ├── status (enum)
  ├── visibility (enum)
  ├── version
  ├── tags (JSON)
  ├── created_at
  └── updated_at

-- Who installed what
TABLE skill_installations
  ├── id (PK)
  ├── skill_id (FK)
  ├── user_email
  ├── installed_at
  └── is_active

-- Audit trail
TABLE audit_logs
  ├── id (PK)
  ├── action
  ├── skill_id
  ├── user_email
  ├── details (JSON)
  └── created_at

-- Review queue
TABLE approval_queue
  ├── id (PK)
  ├── skill_id (FK)
  ├── approval_type
  ├── status
  ├── submitted_by
  ├── reviewed_by
  ├── telegram_message_id
  └── created_at
```

---

## 🔌 API Endpoints

### Skill Management

```
POST   /api/skills/create              # สร้าง skill
GET    /api/skills/list                # ดูรายชื่อ
GET    /api/skills/{id}                # ดูรายละเอียด
PUT    /api/skills/{id}                # แก้ไข skill
DELETE /api/skills/{id}                # ลบ skill

POST   /api/skills/{id}/share-to-team  # แชร์เข้าทีม
```

### Approval

```
POST   /api/approvals/{id}/action      # อนุมัติ/ปฏิเสธ
GET    /api/approvals/queue            # ดู queue
```

### Installation

```
POST   /api/installations/install      # ติดตั้ง skill
POST   /api/installations/{id}/uninstall
GET    /api/users/{email}/skills       # ดู installed skills
```

### Dashboard

```
GET    /api/dashboard/stats            # สถิติทั่วไป
```

---

## 🚀 Running the System

### Option 1: Traditional

```bash
# Terminal 1 - Backend
source .venv/bin/activate
python -m uvicorn backend.main:app --reload

# Terminal 2 - Frontend
python -m http.server 8080
```

### Option 2: Docker Compose

```bash
docker-compose up -d
```

---

## 🧪 Testing

### Unit Tests (Future)

```
tests/
├── test_backend.py
├── test_agent.py
├── test_telegram.py
└── test_api.py
```

### Manual Testing

```bash
# Health check
curl http://localhost:8000/health

# Create skill
curl -X POST http://localhost:8000/api/skills/create ...

# Test agent
python hermes_bridge/agent.py
```

---

## 📝 File Purposes

| File | Purpose | Owner |
|------|---------|-------|
| main.py | API endpoints & routing | Backend |
| models.py | Database table definitions | Backend |
| schemas.py | Request/response validation | Backend |
| agent.py | AI decision making | Hermes Bridge |
| bot.py | Notifications | Telegram |
| workflows.json | Automation rules | n8n |
| index.html | Web interface | Frontend |

---

## 🔒 Security Considerations

- `backend/models.py` - Handles data persistence & validation
- `.env` - Stores secrets (never commit!)
- `telegram/bot.py` - Validates incoming requests
- `hermes-bridge/agent.py` - Enforces permission checks

---

## 📈 Growth Path

**Current (MVP):**
- Personal AI Assistant ✅
- Skill Creation ✅
- Team Sharing (Pending)
- Approval via Telegram (Setup)

**Phase 2:**
- Company Skill Store
- Version Control
- Analytics Dashboard

**Phase 3:**
- Document Indexing
- Vector Search
- RAG System

---

## 🔗 Related Documentation

- [README.md](README.md) - High-level overview
- [INSTALLATION.md](INSTALLATION.md) - Setup instructions
- [QUICKSTART.md](QUICKSTART.md) - 5-minute start
- Backend API docs: `http://localhost:8000/docs`
