from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, Boolean, JSON, SmallInteger
from sqlalchemy.sql import func
from database import Base
from datetime import datetime
import enum


class PresenceStatus(str, enum.Enum):
    ACTIVE  = "active"
    AWAY    = "away"
    BUSY    = "busy"
    OFFLINE = "offline"


class Team(Base):
    __tablename__ = "teams"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    department  = Column(String(100), nullable=True, index=True)
    leader_email = Column(String(255), nullable=True)
    created_at  = Column(DateTime, default=func.now())
    updated_at  = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Team(id={self.id}, name={self.name})>"


class ContactGroup(Base):
    __tablename__ = "contact_groups"

    id           = Column(Integer, primary_key=True, index=True)
    name         = Column(String(255), nullable=False, index=True)
    description  = Column(Text, nullable=True)
    member_emails = Column(JSON, default=list)   # list of email strings
    created_by   = Column(String(255), nullable=True)
    created_at   = Column(DateTime, default=func.now())
    updated_at   = Column(DateTime, default=func.now(), onupdate=func.now())

class SkillStatus(str, enum.Enum):
    DRAFT = "draft"
    PRIVATE = "private"
    PENDING_TEAM_REVIEW = "pending_team_review"
    TEAM_AVAILABLE = "team_available"
    INSTALLED = "installed"
    PENDING_COMPANY_REVIEW = "pending_company_review"
    COMPANY_PUBLISHED = "company_published"
    REJECTED = "rejected"
    REQUEST_EDIT = "request_edit"
    DEPRECATED = "deprecated"
    BLOCKED = "blocked"

class SkillVisibility(str, enum.Enum):
    PRIVATE = "private"
    TEAM = "team"
    SHARED = "shared"
    COMPANY = "company"

class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    owner = Column(String(255), nullable=False, index=True)
    department = Column(String(100), nullable=True, index=True)

    status = Column(Enum(SkillStatus), default=SkillStatus.DRAFT, index=True)
    visibility = Column(Enum(SkillVisibility), default=SkillVisibility.PRIVATE)

    # ข้อมูล Skill
    skill_type = Column(String(50), nullable=True)  # เช่น "summarizer", "generator", "analyzer"
    version = Column(String(20), default="1.0.0")
    tags = Column(JSON, nullable=True)  # เก็บ list tags เช่น ["ir", "financial"]

    # Workflow Data
    workflow_data = Column(JSON, nullable=True)  # เก็บ n8n workflow
    prompt_template = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    shared_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)

    # Reviews
    team_lead = Column(String(255), nullable=True)
    approval_comments = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Usage
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)

    # AI Integration
    uses_claude = Column(Boolean, default=False)
    claude_model = Column(String(50), nullable=True)

    def __repr__(self):
        return f"<Skill(id={self.id}, name={self.name}, status={self.status})>"

class SkillInstallation(Base):
    __tablename__ = "skill_installations"

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, index=True, nullable=False)
    user_email = Column(String(255), index=True, nullable=False)

    installed_at = Column(DateTime, default=func.now())
    uninstalled_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    is_favorite = Column(Boolean, default=False)

    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)

class UserRole(str, enum.Enum):
    ADMIN      = "admin"
    TEAM_LEAD  = "team_lead"
    MEMBER     = "member"

class User(Base):
    __tablename__ = "users"

    email          = Column(String(255), primary_key=True, index=True)
    full_name      = Column(String(255), nullable=True)
    department     = Column(String(100), nullable=True)
    role           = Column(Enum(UserRole), default=UserRole.MEMBER)

    # Telegram linkage
    telegram_chat_id   = Column(String(50), nullable=True, unique=True, index=True)
    telegram_username  = Column(String(100), nullable=True)
    telegram_first_name = Column(String(100), nullable=True)
    telegram_last_name  = Column(String(100), nullable=True)
    is_telegram_linked  = Column(Boolean, default=False)

    # Directory fields
    nickname        = Column(String(100), nullable=True)           # e.g. nickname/display name
    job_title       = Column(String(255), nullable=True)           # e.g. Senior Engineer, Product Owner
    team_id         = Column(Integer, nullable=True, index=True)   # FK → teams.id (manual join)
    presence_status = Column(String(20), default="active")         # active | away | busy | offline

    # Authentication
    password_hash      = Column(String(255), nullable=True)
    password_set       = Column(Boolean, default=False)  # False = ยังไม่ได้ตั้ง password

    # Meta
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_seen  = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User(email={self.email}, role={self.role})>"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(100), nullable=False)
    skill_id = Column(Integer, nullable=True)
    user_email = Column(String(255), nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())

class UserFile(Base):
    """ไฟล์ที่ผู้ใช้อัปโหลดเข้าระบบ"""
    __tablename__ = "user_files"

    id           = Column(Integer, primary_key=True, index=True)
    owner_email  = Column(String(255), index=True, nullable=False)
    original_name = Column(String(500), nullable=False)
    saved_name   = Column(String(500), nullable=False)       # ชื่อไฟล์จริงบน disk
    file_size    = Column(Integer, default=0)                # bytes
    mime_type    = Column(String(100), nullable=True)
    summary      = Column(Text, nullable=True)               # AI summary (lazy)
    created_at   = Column(DateTime, default=func.now())


class UserContact(Base):
    """จำ alias → email ของคนในทีม เช่น คุณเอ → chamai@gmail.com"""
    __tablename__ = "user_contacts"

    id = Column(Integer, primary_key=True, index=True)
    owner_email = Column(String(255), index=True, nullable=False)  # user ที่เป็นเจ้าของ contact book
    alias = Column(String(100), nullable=False)                    # ชื่อเล่น / ชื่อใน meeting
    contact_email = Column(String(255), nullable=False)            # email จริง
    contact_name = Column(String(255), nullable=True)              # ชื่อเต็ม (optional)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ApprovalQueue(Base):
    __tablename__ = "approval_queue"

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, nullable=False, index=True)
    approval_type = Column(String(50), nullable=False)  # team, company
    status = Column(String(50), default="pending")  # pending, approved, rejected
    submitted_by = Column(String(255), nullable=False)
    submitted_at = Column(DateTime, default=func.now())
    reviewed_by = Column(String(255), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    comments = Column(Text, nullable=True)
    telegram_message_id = Column(String(255), nullable=True)  # เก็บ message ID จาก Telegram


class MemoryType(str, enum.Enum):
    PROFILE = "profile"
    SKILL = "skill"
    CHAT = "chat"
    CUSTOM = "custom"
    PREFERENCE = "preference"


class UserMemory(Base):
    """จำข้อมูลเกี่ยวกับ User เช่น ชื่อ, บทบาท, Skill ที่ใช้ล่าสุด, Chat history"""
    __tablename__ = "user_memory"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String(255), index=True, nullable=False)
    memory_type = Column(Enum(MemoryType), nullable=False)  # profile, skill, chat, custom, preference
    content = Column(JSON, nullable=False)  # เก็บข้อมูลเป็น JSON เพื่อความยืดหยุ่น
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
