"""
User Memory Management
Design: 1 record per user per memory_type เท่านั้น
- PROFILE  → {full_name, department, role, ...}
- CHAT     → {messages: [{role, message, timestamp}, ...]}  (rolling window, max 40)
- CUSTOM   → {notes: [{note, tags, saved_at}, ...]}
- SKILL    → {skill_id, skill_name, used_at, history: [...]}  (last 50 uses)
- PREFERENCE → {prefs: {key: {value, saved_at}}}
- FACT     → {facts: [{fact, saved_at}, ...]}  (สกัดอัตโนมัติจากบทสนทนา, max 100)
- BEHAVIOR → {intents: {label: {count, last_at, examples}},
              pending_suggestion: {...}|None,
              dismissed: [label, ...]}
"""

from sqlalchemy.orm import Session
from models import UserMemory, MemoryType
from datetime import datetime
from typing import Optional, List, Dict, Any

CHAT_MAX_MESSAGES = 40
FACT_MAX = 100
SKILL_HISTORY_MAX = 50
INTENT_EXAMPLES_MAX = 5


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

    # ── SKILL — keeps usage history, not just the last skill ──────────────────
    @staticmethod
    def save_skill_memory(db: Session, user_email: str, skill_id: int, skill_name: str) -> UserMemory:
        existing = UserMemoryManager.get_active_memory(db, user_email, MemoryType.SKILL)
        history = (existing.content.get("history", []) if existing else [])
        history.append({"skill_id": skill_id, "skill_name": skill_name,
                        "used_at": datetime.now().isoformat()})
        history = history[-SKILL_HISTORY_MAX:]
        content = {"skill_id": skill_id, "skill_name": skill_name,
                   "used_at": datetime.now().isoformat(), "history": history}
        return UserMemoryManager._upsert(db, user_email, MemoryType.SKILL, content)

    # ── PREFERENCE — key/value learned preferences ─────────────────────────────
    @staticmethod
    def save_preference(db: Session, user_email: str, key: str, value: Any) -> UserMemory:
        existing = UserMemoryManager.get_active_memory(db, user_email, MemoryType.PREFERENCE)
        prefs = (dict(existing.content.get("prefs", {})) if existing else {})
        prefs[key] = {"value": value, "saved_at": datetime.now().isoformat()}
        return UserMemoryManager._upsert(db, user_email, MemoryType.PREFERENCE, {"prefs": prefs})

    @staticmethod
    def get_preferences(db: Session, user_email: str) -> Dict[str, Any]:
        record = UserMemoryManager.get_active_memory(db, user_email, MemoryType.PREFERENCE)
        if not record:
            return {}
        return {k: v.get("value") for k, v in record.content.get("prefs", {}).items()}

    # ── FACT — long-term facts auto-extracted from conversations ──────────────
    @staticmethod
    def add_facts(db: Session, user_email: str, facts: List[str]) -> Optional[UserMemory]:
        facts = [f.strip() for f in (facts or []) if f and len(f.strip()) > 3]
        if not facts:
            return None
        existing = UserMemoryManager.get_active_memory(db, user_email, MemoryType.FACT)
        stored = (list(existing.content.get("facts", [])) if existing else [])
        known = [s.get("fact", "") for s in stored]
        for fact in facts:
            # Skip near-duplicates (exact or substring either way)
            if any(fact == k or fact in k or k in fact for k in known):
                continue
            stored.append({"fact": fact, "saved_at": datetime.now().isoformat()})
            known.append(fact)
        stored = stored[-FACT_MAX:]
        return UserMemoryManager._upsert(db, user_email, MemoryType.FACT, {"facts": stored})

    @staticmethod
    def get_facts(db: Session, user_email: str) -> List[str]:
        record = UserMemoryManager.get_active_memory(db, user_email, MemoryType.FACT)
        if not record:
            return []
        return [f.get("fact", "") for f in record.content.get("facts", [])]

    # ── TRANSCRIPT — transcript ล่าสุดที่ user ถอดเสียง ────────────────────────
    TRANSCRIPT_MAX_CHARS = 120_000

    @staticmethod
    def save_transcript_memory(db: Session, user_email: str, filename: str, transcript: str) -> UserMemory:
        content = {
            "filename": filename or "",
            "transcript": (transcript or "")[:UserMemoryManager.TRANSCRIPT_MAX_CHARS],
            "saved_at": datetime.now().isoformat(),
        }
        return UserMemoryManager._upsert(db, user_email, MemoryType.TRANSCRIPT, content)

    @staticmethod
    def get_transcript_memory(db: Session, user_email: str) -> Optional[Dict[str, Any]]:
        record = UserMemoryManager.get_active_memory(db, user_email, MemoryType.TRANSCRIPT)
        return dict(record.content) if record else None

    # ── BEHAVIOR — repeated-intent tracking for auto-skill suggestion ─────────
    @staticmethod
    def record_behavior(db: Session, user_email: str, intent_label: str,
                        example: str = "") -> Dict[str, Any]:
        """นับ intent ที่ user ทำซ้ำ คืน entry ของ intent นั้น (มี count ล่าสุด)"""
        existing = UserMemoryManager.get_active_memory(db, user_email, MemoryType.BEHAVIOR)
        content = dict(existing.content) if existing else {}
        intents = dict(content.get("intents", {}))
        entry = dict(intents.get(intent_label, {"count": 0, "examples": []}))
        entry["count"] = entry.get("count", 0) + 1
        entry["last_at"] = datetime.now().isoformat()
        examples = list(entry.get("examples", []))
        if example:
            examples.append(example[:300])
        entry["examples"] = examples[-INTENT_EXAMPLES_MAX:]
        intents[intent_label] = entry
        content["intents"] = intents
        UserMemoryManager._upsert(db, user_email, MemoryType.BEHAVIOR, content)
        return entry

    @staticmethod
    def get_behavior(db: Session, user_email: str) -> Dict[str, Any]:
        record = UserMemoryManager.get_active_memory(db, user_email, MemoryType.BEHAVIOR)
        return dict(record.content) if record else {}

    @staticmethod
    def set_pending_suggestion(db: Session, user_email: str, suggestion: Optional[Dict[str, Any]]) -> None:
        existing = UserMemoryManager.get_active_memory(db, user_email, MemoryType.BEHAVIOR)
        content = dict(existing.content) if existing else {}
        content["pending_suggestion"] = suggestion
        UserMemoryManager._upsert(db, user_email, MemoryType.BEHAVIOR, content)

    @staticmethod
    def dismiss_suggestion(db: Session, user_email: str, intent_label: str) -> None:
        existing = UserMemoryManager.get_active_memory(db, user_email, MemoryType.BEHAVIOR)
        content = dict(existing.content) if existing else {}
        dismissed = list(content.get("dismissed", []))
        if intent_label not in dismissed:
            dismissed.append(intent_label)
        content["dismissed"] = dismissed
        content["pending_suggestion"] = None
        UserMemoryManager._upsert(db, user_email, MemoryType.BEHAVIOR, content)

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
