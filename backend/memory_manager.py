"""
User Memory Management
Design: 1 record per user per memory_type เท่านั้น
- PROFILE  → {full_name, department, role, ...}
- CHAT     → {messages: [{role, message, timestamp}, ...]}  (rolling window, max 20)
- CUSTOM   → {notes: [{note, tags, saved_at}, ...]}
- SKILL    → {skill_id, skill_name, used_at}
- PREFERENCE → {key: value, ...}
"""

from sqlalchemy.orm import Session
from models import UserMemory, MemoryType
from datetime import datetime
from typing import Optional, List, Dict, Any

CHAT_MAX_MESSAGES = 20


class UserMemoryManager:

    # ── Generic upsert (1 record per user per type) ────────────────────────────
    @staticmethod
    def _upsert(db: Session, user_email: str, memory_type: MemoryType, content: Dict[str, Any]) -> UserMemory:
        """UPDATE existing หรือ INSERT ใหม่ถ้ายังไม่มี — ไม่สร้าง duplicate"""
        existing = db.query(UserMemory).filter(
            UserMemory.user_email == user_email,
            UserMemory.memory_type == memory_type,
            UserMemory.is_active == True
        ).first()

        if existing:
            existing.content = content
            db.commit()
            db.refresh(existing)
            return existing

        record = UserMemory(user_email=user_email, memory_type=memory_type, content=content)
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    # ── PROFILE ────────────────────────────────────────────────────────────────
    @staticmethod
    def save_profile_memory(db: Session, user_email: str, full_name: str, department: str, role: str) -> UserMemory:
        content = {"full_name": full_name, "department": department, "role": role,
                   "saved_at": datetime.now().isoformat()}
        return UserMemoryManager._upsert(db, user_email, MemoryType.PROFILE, content)

    @staticmethod
    def correct_profile(db: Session, user_email: str, full_name: str, department: str, role: str, reason: str = "") -> UserMemory:
        content = {"full_name": full_name, "department": department, "role": role,
                   "corrected_by_user": True, "correction_reason": reason,
                   "corrected_at": datetime.now().isoformat()}
        return UserMemoryManager._upsert(db, user_email, MemoryType.PROFILE, content)

    # ── CHAT — array of messages in 1 record ──────────────────────────────────
    @staticmethod
    def save_chat_memory(db: Session, user_email: str, message: str, context: Dict[str, Any]) -> UserMemory:
        """Append message เข้า messages array ใน 1 record — ไม่สร้างใหม่"""
        existing = db.query(UserMemory).filter(
            UserMemory.user_email == user_email,
            UserMemory.memory_type == MemoryType.CHAT,
            UserMemory.is_active == True
        ).first()

        new_entry = {"message": message, "context": context, "timestamp": datetime.now().isoformat()}

        if existing:
            messages = existing.content.get("messages", [])
            messages.append(new_entry)
            # Keep rolling window
            if len(messages) > CHAT_MAX_MESSAGES:
                messages = messages[-CHAT_MAX_MESSAGES:]
            existing.content = {"messages": messages}
            db.commit()
            db.refresh(existing)
            return existing

        record = UserMemory(
            user_email=user_email,
            memory_type=MemoryType.CHAT,
            content={"messages": [new_entry]}
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_chat_history(db: Session, user_email: str) -> List[Dict]:
        """ดึง chat messages ล่าสุด"""
        record = db.query(UserMemory).filter(
            UserMemory.user_email == user_email,
            UserMemory.memory_type == MemoryType.CHAT,
            UserMemory.is_active == True
        ).first()
        if not record:
            return []
        return record.content.get("messages", [])

    # ── CUSTOM — array of notes in 1 record ───────────────────────────────────
    @staticmethod
    def save_custom_memory(db: Session, user_email: str, note: str, tags: Optional[List[str]] = None) -> UserMemory:
        """Append note เข้า notes array ใน 1 record — ไม่สร้างใหม่"""
        existing = db.query(UserMemory).filter(
            UserMemory.user_email == user_email,
            UserMemory.memory_type == MemoryType.CUSTOM,
            UserMemory.is_active == True
        ).first()

        new_note = {"note": note, "tags": tags or [], "saved_at": datetime.now().isoformat()}

        if existing:
            notes = existing.content.get("notes", [])
            notes.append(new_note)
            existing.content = {"notes": notes}
            db.commit()
            db.refresh(existing)
            return existing

        record = UserMemory(
            user_email=user_email,
            memory_type=MemoryType.CUSTOM,
            content={"notes": [new_note]}
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_custom_notes(db: Session, user_email: str) -> List[Dict]:
        """ดึง custom notes ทั้งหมด"""
        record = db.query(UserMemory).filter(
            UserMemory.user_email == user_email,
            UserMemory.memory_type == MemoryType.CUSTOM,
            UserMemory.is_active == True
        ).first()
        if not record:
            return []
        return record.content.get("notes", [])

    # ── SKILL ──────────────────────────────────────────────────────────────────
    @staticmethod
    def save_skill_memory(db: Session, user_email: str, skill_id: int, skill_name: str) -> UserMemory:
        content = {"skill_id": skill_id, "skill_name": skill_name, "used_at": datetime.now().isoformat()}
        return UserMemoryManager._upsert(db, user_email, MemoryType.SKILL, content)

    # ── Generic correct (update existing) ─────────────────────────────────────
    @staticmethod
    def correct_memory(db: Session, user_email: str, memory_type: MemoryType, new_content: Dict[str, Any], reason: str = "") -> UserMemory:
        new_content["corrected_by_user"] = True
        new_content["correction_reason"] = reason
        new_content["corrected_at"] = datetime.now().isoformat()
        return UserMemoryManager._upsert(db, user_email, memory_type, new_content)

    # ── Helpers ────────────────────────────────────────────────────────────────
    @staticmethod
    def get_active_memory(db: Session, user_email: str, memory_type: MemoryType) -> Optional[UserMemory]:
        return db.query(UserMemory).filter(
            UserMemory.user_email == user_email,
            UserMemory.memory_type == memory_type,
            UserMemory.is_active == True
        ).first()

    @staticmethod
    def get_user_memory(db: Session, user_email: str, memory_type: Optional[MemoryType] = None) -> List[UserMemory]:
        query = db.query(UserMemory).filter(
            UserMemory.user_email == user_email,
            UserMemory.is_active == True
        )
        if memory_type:
            query = query.filter(UserMemory.memory_type == memory_type)
        return query.all()

    @staticmethod
    def delete_memory(db: Session, memory_id: int) -> bool:
        memory = db.query(UserMemory).filter(UserMemory.id == memory_id).first()
        if memory:
            memory.is_active = False
            db.commit()
            return True
        return False

    @staticmethod
    def clear_user_memory(db: Session, user_email: str, memory_type: Optional[MemoryType] = None) -> int:
        query = db.query(UserMemory).filter(UserMemory.user_email == user_email)
        if memory_type:
            query = query.filter(UserMemory.memory_type == memory_type)
        count = query.update({"is_active": False})
        db.commit()
        return count

    @staticmethod
    def get_recent_memory(db: Session, user_email: str, memory_type: MemoryType, limit: int = 5) -> List[UserMemory]:
        return db.query(UserMemory).filter(
            UserMemory.user_email == user_email,
            UserMemory.memory_type == memory_type,
            UserMemory.is_active == True
        ).order_by(UserMemory.updated_at.desc()).limit(limit).all()
