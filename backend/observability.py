"""Self-Improving Platform — Observability, Monitoring, Self-Improvement engine.

ปรัชญา (ปลอดภัย): Observe → Analyze → Improve → Report → Human Review → Deploy
Hermes **ไม่แก้ production เองอัตโนมัติ** — ทุกข้อเสนอ (guidance/ticket/skill) ถูกสร้าง
เป็น draft/inactive จนกว่า AI Engineer จะกดอนุมัติใน dashboard

โครงสร้าง 1 ไฟล์ (เลียนแบบสไตล์ main.py):
- โมเดล 6 ตัว (String columns ล้วน — ไม่ใช้ PG native enum เพื่อเลี่ยงปัญหา ALTER TYPE)
- telemetry helper (best-effort, ใช้ session ของตัวเอง, ห้าม raise เข้า hot path)
- monitor (เช็ค threshold → สร้าง SystemAlert)
- nightly engine (รวบรวม 24 ชม. → LLM RCA → ImprovementReport + Ticket + Opportunity)
- scheduler (APScheduler: nightly 00:00 Asia/Bangkok + monitor ทุก N นาที)
"""
import os
import json
from datetime import datetime, timedelta

from sqlalchemy import (Column, Integer, String, Text, DateTime, Boolean, JSON,
                        Float, Index, func)
from sqlalchemy.orm import Session

from database import Base, SessionLocal

# ── เวลาไทย ───────────────────────────────────────────────────────────────────
BANGKOK_OFFSET = timedelta(hours=7)


def now_bkk() -> datetime:
    return datetime.utcnow() + BANGKOK_OFFSET


def today_bkk_str() -> str:
    return now_bkk().strftime("%Y-%m-%d")


# ── ราคา gpt-4o-mini (ต่อ 1M tokens): input $0.15, output $0.60 ────────────────
_COST_IN_PER_TOKEN = 0.15 / 1_000_000
_COST_OUT_PER_TOKEN = 0.60 / 1_000_000


def estimate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    return (prompt_tokens or 0) * _COST_IN_PER_TOKEN + (completion_tokens or 0) * _COST_OUT_PER_TOKEN


# ── ราคาถอดเสียง (ต่อนาที): whisper-1 = $0.006, gpt-4o-transcribe = $0.006 ──────
# โหมด dual ถอด 2 รอบต่อ chunk (diarize + whisper) → ~$0.012/นาที
# โหมด single ใช้โมเดลเดียว → ~$0.006/นาที
_AUDIO_COST_PER_MIN_SINGLE = 0.006
_AUDIO_COST_PER_MIN_DUAL   = 0.012


def estimate_audio_cost(duration_seconds: float, dual: bool = True) -> float:
    """ประเมินค่าถอดเสียงจากความยาวเสียง (วินาที)."""
    minutes = max(float(duration_seconds or 0), 0) / 60.0
    rate = _AUDIO_COST_PER_MIN_DUAL if dual else _AUDIO_COST_PER_MIN_SINGLE
    return round(minutes * rate, 4)


# ── สตริงที่ _claude_chat คืนเมื่อ "พัง" (ไม่ raise) — ต้องนับเป็น error ───────
_ERROR_PREFIXES = ("OpenAI Error:", "⚠️")


def reply_is_error(text: str) -> bool:
    t = (text or "").strip()
    return any(t.startswith(p) for p in _ERROR_PREFIXES)


# ══════════════════════════════════════════════════════════════════════════════
# MODELS
# ══════════════════════════════════════════════════════════════════════════════

class TelemetryEvent(Base):
    """บันทึกทุก LLM call — แกนของ Observe."""
    __tablename__ = "telemetry_events"

    id            = Column(Integer, primary_key=True, index=True)
    created_at    = Column(DateTime, default=func.now(), index=True)
    user_email    = Column(String(255), index=True, nullable=True)
    request_kind  = Column(String(50), index=True)   # chat | run_skill | meeting_* | ...
    skill_id      = Column(Integer, nullable=True, index=True)
    skill_name    = Column(String(255), nullable=True)
    status        = Column(String(10), index=True)   # ok | error
    error_type    = Column(String(120), nullable=True, index=True)
    latency_ms    = Column(Integer, nullable=True)
    model         = Column(String(50), nullable=True)
    prompt_tokens     = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens      = Column(Integer, default=0)
    est_cost_usd  = Column(Float, default=0.0)
    meta          = Column(JSON, nullable=True)


class FeedbackEvent(Base):
    """👍/👎 บนคำตอบบอท."""
    __tablename__ = "feedback_events"

    id          = Column(Integer, primary_key=True, index=True)
    created_at  = Column(DateTime, default=func.now(), index=True)
    user_email  = Column(String(255), index=True)
    rating      = Column(Integer)                    # +1 / -1
    skill_id    = Column(Integer, nullable=True)
    skill_name  = Column(String(255), nullable=True)
    message_ref = Column(String(64), nullable=True)
    comment     = Column(Text, nullable=True)
    meta        = Column(JSON, nullable=True)


class SystemAlert(Base):
    """แจ้งเตือนเหตุผิดปกติ — โผล่ใน dashboard."""
    __tablename__ = "system_alerts"

    id           = Column(Integer, primary_key=True, index=True)
    created_at   = Column(DateTime, default=func.now(), index=True)
    severity     = Column(String(20), index=True)    # info | warning | critical
    alert_type   = Column(String(60), index=True)
    message      = Column(Text)
    metric_value = Column(Float, nullable=True)
    threshold    = Column(Float, nullable=True)
    resolved     = Column(Boolean, default=False, index=True)
    resolved_by  = Column(String(255), nullable=True)
    resolved_at  = Column(DateTime, nullable=True)
    dedup_key    = Column(String(120), nullable=True, index=True)
    meta         = Column(JSON, nullable=True)


class ImprovementReport(Base):
    """รายงานปรับปรุงรายวัน — สร้างตอนเที่ยงคืน (idempotent ต่อวัน)."""
    __tablename__ = "improvement_reports"

    id            = Column(Integer, primary_key=True, index=True)
    report_date   = Column(String(10), unique=True, index=True)  # YYYY-MM-DD (Bangkok)
    created_at    = Column(DateTime, default=func.now())
    window_start  = Column(DateTime, nullable=True)
    window_end    = Column(DateTime, nullable=True)
    summary       = Column(Text, nullable=True)
    top_issues        = Column(JSON, nullable=True)
    recurring_issues  = Column(JSON, nullable=True)
    root_cause        = Column(Text, nullable=True)
    recommended_fixes = Column(JSON, nullable=True)
    action_items      = Column(JSON, nullable=True)
    opportunities     = Column(JSON, nullable=True)
    metrics_snapshot  = Column(JSON, nullable=True)
    status        = Column(String(20), default="generated")  # generated | reviewed
    generated_by  = Column(String(40), default="nightly")    # nightly | manual
    llm_raw       = Column(Text, nullable=True)


class Ticket(Base):
    """งานที่ระบบเสนอให้วิศวกรทำ — สร้างจาก nightly. เปิดเป็น open รอ human."""
    __tablename__ = "tickets"

    id            = Column(Integer, primary_key=True, index=True)
    created_at    = Column(DateTime, default=func.now(), index=True)
    updated_at    = Column(DateTime, default=func.now(), onupdate=func.now())
    title         = Column(String(300))
    description   = Column(Text, nullable=True)
    severity      = Column(String(20), index=True)   # low | medium | high | critical
    status        = Column(String(20), default="open", index=True)  # open | in_progress | resolved | dismissed
    assignee      = Column(String(255), nullable=True)
    suggested_fix = Column(Text, nullable=True)
    source_report_id = Column(Integer, index=True, nullable=True)
    dedup_key     = Column(String(160), nullable=True, index=True)
    meta          = Column(JSON, nullable=True)


class LearnedGuidance(Base):
    """ข้อเสนอ skill/automation ระดับองค์กรจาก Opportunity Detection. draft รออนุมัติ."""
    __tablename__ = "learned_guidance"

    id            = Column(Integer, primary_key=True, index=True)
    created_at    = Column(DateTime, default=func.now(), index=True)
    kind          = Column(String(30), default="skill_proposal")  # skill_proposal | guidance
    title         = Column(String(300))
    description   = Column(Text, nullable=True)
    pattern_label = Column(String(160), index=True)
    user_count    = Column(Integer, default=0)
    occurrence    = Column(Integer, default=0)
    examples      = Column(JSON, nullable=True)
    status        = Column(String(20), default="draft", index=True)  # draft | approved | rejected
    approved_by   = Column(String(255), nullable=True)
    approved_at   = Column(DateTime, nullable=True)
    source_report_id = Column(Integer, nullable=True)


Index("ix_telemetry_created_status", TelemetryEvent.created_at, TelemetryEvent.status)


# ══════════════════════════════════════════════════════════════════════════════
# TELEMETRY (best-effort — ห้ามทำให้ hot path ล่ม)
# ══════════════════════════════════════════════════════════════════════════════

def record_telemetry(**kw) -> None:
    """บันทึก 1 TelemetryEvent ด้วย session ของตัวเอง. ห้าม raise."""
    db = SessionLocal()
    try:
        db.add(TelemetryEvent(**kw))
        db.commit()
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        print(f"[telemetry] skip: {e}")
    finally:
        db.close()


def record_feedback(db: Session, user_email: str, rating: int, skill_id=None,
                    skill_name=None, message_ref=None, comment=None, meta=None) -> FeedbackEvent:
    rec = FeedbackEvent(
        user_email=user_email, rating=1 if rating >= 0 else -1,
        skill_id=skill_id, skill_name=skill_name, message_ref=message_ref,
        comment=comment, meta=meta)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


# ══════════════════════════════════════════════════════════════════════════════
# OVERVIEW (dashboard data)
# ══════════════════════════════════════════════════════════════════════════════

def _percentile(values: list, pct: float) -> int:
    if not values:
        return 0
    s = sorted(values)
    k = int(round((pct / 100.0) * (len(s) - 1)))
    return int(s[min(k, len(s) - 1)])


def build_overview(db: Session) -> dict:
    """รวมตัวเลขทั้งหมดสำหรับการ์ด dashboard (หน้าต่าง 24 ชม.)."""
    since = datetime.utcnow() - timedelta(hours=24)
    events = db.query(TelemetryEvent).filter(TelemetryEvent.created_at >= since).all()
    total = len(events)
    errors = [e for e in events if e.status == "error"]
    latencies = [e.latency_ms for e in events if e.latency_ms is not None]
    active_users = len({e.user_email for e in events if e.user_email})

    # ค่าใช้จ่ายวันนี้ (เวลาไทย)
    today_start_utc = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - BANGKOK_OFFSET
    cost_today = (db.query(func.coalesce(func.sum(TelemetryEvent.est_cost_usd), 0.0))
                  .filter(TelemetryEvent.created_at >= today_start_utc).scalar() or 0.0)

    # top skills 24 ชม.
    skill_counts = {}
    for e in events:
        if e.skill_name:
            skill_counts[e.skill_name] = skill_counts.get(e.skill_name, 0) + 1
    top_skills = sorted(
        [{"name": k, "count": v} for k, v in skill_counts.items()],
        key=lambda x: x["count"], reverse=True)[:8]

    recent_errors = [{
        "created_at": e.created_at.isoformat() if e.created_at else None,
        "request_kind": e.request_kind, "error_type": e.error_type,
        "skill_name": e.skill_name, "user_email": e.user_email,
    } for e in sorted(errors, key=lambda x: x.created_at or datetime.min, reverse=True)[:10]]

    # ค่าใช้จ่ายแยกตามประเภทงาน 24 ชม. (chat ถูกมาก / ถอดเสียงแพงสุด)
    kind_cost = {}
    for e in events:
        k = e.request_kind or "other"
        agg = kind_cost.setdefault(k, {"kind": k, "count": 0, "cost": 0.0})
        agg["count"] += 1
        agg["cost"] += (e.est_cost_usd or 0)
    cost_by_kind = sorted(
        [{"kind": v["kind"], "count": v["count"], "cost": round(v["cost"], 4)}
         for v in kind_cost.values()],
        key=lambda x: x["cost"], reverse=True)

    # รายการล่าสุดที่มีค่าใช้จ่าย — ให้เห็น "แต่ละครั้ง" ใช้เงินเท่าไร
    paid = [e for e in events if (e.est_cost_usd or 0) > 0]
    recent_costs = [{
        "created_at": e.created_at.isoformat() if e.created_at else None,
        "request_kind": e.request_kind, "skill_name": e.skill_name,
        "user_email": e.user_email, "status": e.status,
        "cost": round(e.est_cost_usd or 0, 4),
        "duration_min": (e.meta or {}).get("duration_min") if isinstance(e.meta, dict) else None,
    } for e in sorted(paid, key=lambda x: x.created_at or datetime.min, reverse=True)[:15]]

    # feedback score 24 ชม.
    fb = db.query(FeedbackEvent).filter(FeedbackEvent.created_at >= since).all()
    up = sum(1 for f in fb if f.rating > 0)
    down = sum(1 for f in fb if f.rating < 0)
    fb_score = round((up / (up + down)) * 100, 1) if (up + down) else None

    unresolved_alerts = db.query(SystemAlert).filter(SystemAlert.resolved == False).count()  # noqa: E712
    open_tickets = db.query(Ticket).filter(Ticket.status.in_(["open", "in_progress"])).count()
    draft_opps = db.query(LearnedGuidance).filter(LearnedGuidance.status == "draft").count()

    return {
        "window_hours": 24,
        "active_users_24h": active_users,
        "requests_24h": total,
        "error_count_24h": len(errors),
        "error_rate_24h": round(len(errors) / total * 100, 1) if total else 0.0,
        "avg_latency_ms": int(sum(latencies) / len(latencies)) if latencies else 0,
        "p95_latency_ms": _percentile(latencies, 95),
        "cost_today_usd": round(float(cost_today), 4),
        "cost_24h_usd": round(sum((e.est_cost_usd or 0) for e in events), 4),
        "tokens_24h": sum((e.total_tokens or 0) for e in events),
        "cost_by_kind": cost_by_kind,
        "recent_costs": recent_costs,
        "top_skills": top_skills,
        "recent_errors": recent_errors,
        "feedback_up_24h": up,
        "feedback_down_24h": down,
        "feedback_score": fb_score,
        "unresolved_alerts": unresolved_alerts,
        "open_tickets": open_tickets,
        "draft_opportunities": draft_opps,
    }


# ══════════════════════════════════════════════════════════════════════════════
# MONITORING & ALERTING (โผล่ใน dashboard เท่านั้น)
# ══════════════════════════════════════════════════════════════════════════════

# thresholds (override ผ่าน env ได้)
_MON_WINDOW_MIN   = int(os.getenv("MON_WINDOW_MIN", "15"))
_MON_MIN_REQS     = int(os.getenv("MON_MIN_REQS", "5"))     # ต้องมี request พอ ถึงจะตัดสิน error rate
_MON_ERR_RATE     = float(os.getenv("MON_ERR_RATE", "30"))  # %
_MON_P95_MS       = int(os.getenv("MON_P95_MS", "15000"))   # ช้าผิดปกติ
_MON_COST_DAY     = float(os.getenv("MON_COST_DAY", "5.0")) # $ / วัน


def _raise_alert(db: Session, severity, alert_type, message, dedup_key,
                 metric_value=None, threshold=None, meta=None) -> bool:
    """สร้าง alert ถ้ายังไม่มีตัวที่ dedup_key เดียวกัน + ยัง unresolved. คืน True ถ้าสร้างใหม่."""
    existing = (db.query(SystemAlert)
                .filter(SystemAlert.dedup_key == dedup_key, SystemAlert.resolved == False)  # noqa: E712
                .first())
    if existing:
        return False
    db.add(SystemAlert(severity=severity, alert_type=alert_type, message=message,
                       dedup_key=dedup_key, metric_value=metric_value,
                       threshold=threshold, meta=meta))
    db.commit()
    return True


def run_monitor(db: Session = None) -> dict:
    """เช็ค threshold จาก telemetry ล่าสุด → สร้าง SystemAlert. เรียกโดย scheduler ทุก N นาที."""
    own = db is None
    if own:
        db = SessionLocal()
    created = []
    try:
        since = datetime.utcnow() - timedelta(minutes=_MON_WINDOW_MIN)
        events = db.query(TelemetryEvent).filter(TelemetryEvent.created_at >= since).all()
        total = len(events)
        errors = [e for e in events if e.status == "error"]
        hour_bucket = now_bkk().strftime("%Y-%m-%dT%H")

        # 1) error rate spike
        if total >= _MON_MIN_REQS:
            rate = len(errors) / total * 100
            if rate >= _MON_ERR_RATE:
                if _raise_alert(db, "critical", "error_rate_spike",
                                f"Error rate {rate:.0f}% ในช่วง {_MON_WINDOW_MIN} นาที ({len(errors)}/{total} requests)",
                                dedup_key=f"error_rate_spike:{hour_bucket}",
                                metric_value=rate, threshold=_MON_ERR_RATE):
                    created.append("error_rate_spike")

        # 2) slow latency (p95)
        latencies = [e.latency_ms for e in events if e.latency_ms is not None]
        if len(latencies) >= _MON_MIN_REQS:
            p95 = _percentile(latencies, 95)
            if p95 >= _MON_P95_MS:
                if _raise_alert(db, "warning", "slow_latency",
                                f"p95 latency {p95} ms ในช่วง {_MON_WINDOW_MIN} นาที (เกิน {_MON_P95_MS} ms)",
                                dedup_key=f"slow_latency:{hour_bucket}",
                                metric_value=p95, threshold=_MON_P95_MS):
                    created.append("slow_latency")

        # 3) api failure (error_type บ่งว่า API/auth พัง)
        api_fail = [e for e in errors if (e.error_type or "").lower() not in ("", "none")]
        if api_fail and total >= _MON_MIN_REQS and len(errors) == total:
            if _raise_alert(db, "critical", "api_failure",
                            f"ทุก request ({total}) ล้มเหลวในช่วง {_MON_WINDOW_MIN} นาที — อาจเป็นปัญหา API/key/เครือข่าย",
                            dedup_key=f"api_failure:{hour_bucket}",
                            metric_value=total):
                created.append("api_failure")

        # 4) cost spike (วันนี้)
        today_start_utc = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - BANGKOK_OFFSET
        cost_today = (db.query(func.coalesce(func.sum(TelemetryEvent.est_cost_usd), 0.0))
                      .filter(TelemetryEvent.created_at >= today_start_utc).scalar() or 0.0)
        if cost_today >= _MON_COST_DAY:
            if _raise_alert(db, "warning", "cost_spike",
                            f"ค่าใช้จ่าย AI วันนี้ ${cost_today:.2f} (เกินงบ ${_MON_COST_DAY:.2f})",
                            dedup_key=f"cost_spike:{today_bkk_str()}",
                            metric_value=round(float(cost_today), 2), threshold=_MON_COST_DAY):
                created.append("cost_spike")

        return {"checked": total, "alerts_created": created}
    except Exception as e:
        print(f"[monitor] error: {e}")
        return {"error": str(e)}
    finally:
        if own:
            db.close()


# ══════════════════════════════════════════════════════════════════════════════
# OPPORTUNITY DETECTION (รวม BEHAVIOR ข้าม user)
# ══════════════════════════════════════════════════════════════════════════════

_OPP_MIN_USERS = int(os.getenv("OPP_MIN_USERS", "2"))      # อย่างน้อยกี่ user ที่ทำ intent นี้
_OPP_MIN_TOTAL = int(os.getenv("OPP_MIN_TOTAL", "5"))      # รวมกี่ครั้ง


def detect_opportunities(db: Session) -> list:
    """รวม UserMemory.BEHAVIOR intents ข้าม user → หา pattern ซ้ำที่ควรมี skill กลาง."""
    from models import UserMemory, MemoryType
    rows = (db.query(UserMemory)
            .filter(UserMemory.memory_type == MemoryType.BEHAVIOR,
                    UserMemory.is_active == True)  # noqa: E712
            .all())
    # label -> {users:set, total:int, examples:[]}
    agg = {}
    for r in rows:
        content = r.content or {}
        dismissed = set(content.get("dismissed", []))
        for label, entry in (content.get("intents", {}) or {}).items():
            if label in dismissed:
                continue
            a = agg.setdefault(label, {"users": set(), "total": 0, "examples": []})
            a["users"].add(r.user_email)
            a["total"] += entry.get("count", 0)
            for ex in (entry.get("examples") or [])[:2]:
                if ex and len(a["examples"]) < 5:
                    a["examples"].append(ex)

    found = []
    for label, a in agg.items():
        if len(a["users"]) >= _OPP_MIN_USERS and a["total"] >= _OPP_MIN_TOTAL:
            found.append({
                "pattern_label": label,
                "user_count": len(a["users"]),
                "occurrence": a["total"],
                "examples": a["examples"],
            })
    found.sort(key=lambda x: (x["user_count"], x["occurrence"]), reverse=True)
    return found[:10]


def _persist_opportunities(db: Session, opps: list, report_id: int) -> int:
    """บันทึก opportunity เป็น LearnedGuidance draft (กันซ้ำด้วย pattern_label ที่ยัง draft/approved)."""
    n = 0
    for o in opps:
        label = o.get("pattern_label", "")
        exists = (db.query(LearnedGuidance)
                  .filter(LearnedGuidance.pattern_label == label,
                          LearnedGuidance.status.in_(["draft", "approved"]))
                  .first())
        if exists:
            continue
        title = f"Skill ใหม่ที่แนะนำ: {label}"
        desc = (f"ผู้ใช้ {o.get('user_count')} คนทำงานแบบ '{label}' รวม {o.get('occurrence')} ครั้ง "
                f"— ควรมี skill กลางให้ทั้งองค์กรใช้ร่วมกัน")
        db.add(LearnedGuidance(
            kind="skill_proposal", title=title, description=desc,
            pattern_label=label, user_count=o.get("user_count", 0),
            occurrence=o.get("occurrence", 0), examples=o.get("examples", []),
            status="draft", source_report_id=report_id))
        n += 1
    db.commit()
    return n


# ══════════════════════════════════════════════════════════════════════════════
# MIDNIGHT SELF-IMPROVEMENT ENGINE
# ══════════════════════════════════════════════════════════════════════════════

_NIGHTLY_PROMPT = """คุณคือวิศวกร AI อาวุโสที่ดูแลแพลตฟอร์ม Hermes (AI Skill Hub ขององค์กร)
ด้านล่างคือข้อมูลการใช้งานจริงรอบ 24 ชม.ที่ผ่านมา วิเคราะห์หา root cause และเสนอการปรับปรุง
ตอบเป็น JSON ภาษาไทยเท่านั้น ไม่มีข้อความอื่น รูปแบบ:
{
  "summary": "สรุปสุขภาพระบบ + ปัญหาเด่น 2-4 บรรทัด",
  "top_issues": [{"title":"ปัญหา","frequency":จำนวน,"user_impact":"ผลกระทบต่อผู้ใช้","severity":"low|medium|high|critical"}],
  "recurring_issues": ["ปัญหาที่เกิดซ้ำบ่อย"],
  "root_cause": "วิเคราะห์สาเหตุที่แท้จริง",
  "recommended_fixes": [{"title":"สิ่งที่ควรแก้","fix":"วิธีแก้ที่แนะนำ","priority":"low|medium|high|critical"}],
  "action_items": [{"title":"งานที่ควรทำต่อ","owner_hint":"ใครควรทำ","priority":"low|medium|high|critical"}]
}
หมายเหตุ: อิงข้อมูลจริงเท่านั้น ห้ามแต่งเติม ถ้าระบบปกติดีให้บอกตามตรงและใส่ array ว่าง"""


def _gather_24h(db: Session) -> dict:
    """รวบรวมตัวชี้วัด + ตัวอย่าง error/feedback รอบ 24 ชม. สำหรับป้อน LLM."""
    since = datetime.utcnow() - timedelta(hours=24)
    events = db.query(TelemetryEvent).filter(TelemetryEvent.created_at >= since).all()
    total = len(events)
    errors = [e for e in events if e.status == "error"]

    err_by_type = {}
    for e in errors:
        k = e.error_type or "unknown"
        err_by_type[k] = err_by_type.get(k, 0) + 1

    skill_counts = {}
    for e in events:
        if e.skill_name:
            skill_counts[e.skill_name] = skill_counts.get(e.skill_name, 0) + 1

    latencies = [e.latency_ms for e in events if e.latency_ms is not None]
    cost = sum((e.est_cost_usd or 0) for e in events)

    fb = db.query(FeedbackEvent).filter(FeedbackEvent.created_at >= since).all()
    down = [f for f in fb if f.rating < 0]

    return {
        "metrics": {
            "requests": total,
            "errors": len(errors),
            "error_rate_pct": round(len(errors) / total * 100, 1) if total else 0.0,
            "avg_latency_ms": int(sum(latencies) / len(latencies)) if latencies else 0,
            "p95_latency_ms": _percentile(latencies, 95),
            "cost_usd": round(float(cost), 4),
            "feedback_up": sum(1 for f in fb if f.rating > 0),
            "feedback_down": len(down),
        },
        "errors_by_type": err_by_type,
        "top_skills": sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:8],
        "negative_feedback_examples": [
            {"skill": f.skill_name, "comment": f.comment, "ref": f.message_ref}
            for f in down[:15]
        ],
    }


def _create_tickets_from_report(db: Session, report) -> int:
    """สร้าง Ticket จาก recommended_fixes ที่ priority สูง (กันซ้ำด้วย dedup_key)."""
    fixes = report.recommended_fixes or []
    n = 0
    for fx in fixes:
        if not isinstance(fx, dict):
            continue
        prio = (fx.get("priority") or "medium").lower()
        if prio not in ("high", "critical"):
            continue  # ticket เฉพาะเรื่องสำคัญ — เรื่องเล็กอยู่ใน report พอ
        title = (fx.get("title") or "")[:300]
        dedup = f"{report.report_date}:{title[:120]}"
        exists = db.query(Ticket).filter(Ticket.dedup_key == dedup).first()
        if exists:
            continue
        db.add(Ticket(
            title=title or "ปัญหาที่ระบบตรวจพบ",
            description=fx.get("fix") or "",
            severity=prio, status="open",
            suggested_fix=fx.get("fix") or "",
            source_report_id=report.id, dedup_key=dedup))
        n += 1
    db.commit()
    return n


def run_nightly(db: Session = None, force: bool = False, generated_by: str = "nightly") -> dict:
    """รวบรวมข้อมูล 24 ชม. → LLM RCA → ImprovementReport (idempotent/วัน) → Ticket + Opportunity."""
    own = db is None
    if own:
        db = SessionLocal()
    try:
        date_str = today_bkk_str()
        existing = db.query(ImprovementReport).filter(
            ImprovementReport.report_date == date_str).first()
        if existing and not force:
            return {"skipped": True, "reason": "มีรายงานของวันนี้แล้ว", "report_date": date_str,
                    "report_id": existing.id}

        window_end = datetime.utcnow()
        window_start = window_end - timedelta(hours=24)
        data = _gather_24h(db)

        # เรียก LLM (late import เลี่ยง circular)
        summary, top_issues, recurring, root_cause = "", [], [], ""
        rec_fixes, action_items, llm_raw = [], [], ""
        try:
            from main import _claude_chat
            payload = json.dumps(data, ensure_ascii=False)
            llm_raw = _claude_chat(
                [{"role": "user", "content": f"ข้อมูล 24 ชม.:\n{payload}"}],
                _NIGHTLY_PROMPT, max_tokens=3000)
            if reply_is_error(llm_raw):
                raise RuntimeError(llm_raw)
            # ดึง JSON ออกจากคำตอบ (เผื่อมี ```json)
            raw = llm_raw.strip()
            if "```" in raw:
                raw = raw.split("```")[1].replace("json", "", 1).strip() if raw.count("```") >= 2 else raw
            parsed = json.loads(raw)
            summary = parsed.get("summary", "")
            top_issues = parsed.get("top_issues", [])
            recurring = parsed.get("recurring_issues", [])
            root_cause = parsed.get("root_cause", "")
            rec_fixes = parsed.get("recommended_fixes", [])
            action_items = parsed.get("action_items", [])
        except Exception as e:
            m = data["metrics"]
            summary = (f"รอบ 24 ชม.: {m['requests']} requests, error {m['errors']} "
                       f"({m['error_rate_pct']}%), p95 {m['p95_latency_ms']}ms, "
                       f"cost ${m['cost_usd']}. (วิเคราะห์อัตโนมัติไม่สำเร็จ: {e})")

        # opportunity detection
        opps = detect_opportunities(db)

        # บันทึก/อัปเดต report
        if existing:
            rep = existing
        else:
            rep = ImprovementReport(report_date=date_str)
            db.add(rep)
        rep.window_start = window_start
        rep.window_end = window_end
        rep.summary = summary
        rep.top_issues = top_issues
        rep.recurring_issues = recurring
        rep.root_cause = root_cause
        rep.recommended_fixes = rec_fixes
        rep.action_items = action_items
        rep.opportunities = opps
        rep.metrics_snapshot = data["metrics"]
        rep.generated_by = generated_by
        rep.llm_raw = (llm_raw or "")[:8000]
        try:
            db.commit()
            db.refresh(rep)
        except Exception as e:
            db.rollback()
            # ชนกับ UNIQUE (job ยิงซ้ำ) → ดึงตัวเดิม
            rep = db.query(ImprovementReport).filter(
                ImprovementReport.report_date == date_str).first()
            if not rep:
                return {"error": f"report commit failed: {e}"}

        tickets_n = _create_tickets_from_report(db, rep)
        opps_n = _persist_opportunities(db, opps, rep.id)

        return {"report_id": rep.id, "report_date": date_str,
                "tickets_created": tickets_n, "opportunities_created": opps_n,
                "metrics": data["metrics"]}
    finally:
        if own:
            db.close()


# ══════════════════════════════════════════════════════════════════════════════
# SCHEDULER (APScheduler) — เริ่มจาก startup hook ใน main.py
# ══════════════════════════════════════════════════════════════════════════════

_scheduler = None
_MONITOR_INTERVAL_MIN = int(os.getenv("MONITOR_INTERVAL_MIN", "10"))


def start_scheduler() -> bool:
    """เริ่ม BackgroundScheduler: nightly 00:00 Asia/Bangkok + monitor ทุก N นาที.
    ปิดได้ด้วย env ENABLE_SCHEDULER=0. คืน True ถ้าเริ่มจริง."""
    global _scheduler
    if os.getenv("ENABLE_SCHEDULER", "1") in ("0", "false", "no"):
        print("[scheduler] disabled by ENABLE_SCHEDULER")
        return False
    if _scheduler is not None:
        return True
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        sched = BackgroundScheduler(timezone="Asia/Bangkok")
        sched.add_job(lambda: run_nightly(), CronTrigger(hour=0, minute=0),
                      id="nightly_improvement", replace_existing=True)
        sched.add_job(lambda: run_monitor(), "interval",
                      minutes=_MONITOR_INTERVAL_MIN, id="monitor", replace_existing=True)
        # cleanup เอกสารจากแชตที่เก่าเกิน retention (กัน DB/MinIO บวม) — ทุกวัน 03:30
        def _doc_cleanup():
            try:
                from main import _cleanup_old_chat_documents
                _cleanup_old_chat_documents()
            except Exception as _e:
                print(f"[scheduler] doc_cleanup failed: {_e}")
        sched.add_job(_doc_cleanup, CronTrigger(hour=3, minute=30),
                      id="doc_cleanup", replace_existing=True)
        sched.start()
        _scheduler = sched
        print(f"[scheduler] started — nightly 00:00 Asia/Bangkok, monitor ทุก {_MONITOR_INTERVAL_MIN} นาที")
        return True
    except Exception as e:
        print(f"[scheduler] start failed: {e}")
        return False


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        try:
            _scheduler.shutdown(wait=False)
        except Exception:
            pass
        _scheduler = None

