"""
Hermes Telegram Bot - รับข้อความจาก Telegram และตอบด้วย OpenAI
รัน: python telegram/bot_polling.py
"""
import os
import sys
import re
import time
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# เก็บ conversation history แยกตาม chat_id
conversations: dict = {}

# เก็บ meeting context ล่าสุดแยกตาม chat_id (สำหรับ post-meeting actions)
_meeting_context: dict = {}  # chat_id → {owners: [...], title: str, summary: str}

MEETING_KEYWORDS = ["action items", "ผู้รับผิดชอบ", "สรุปการประชุม", "action item",
                    "มติที่ประชุม", "follow-up", "กำหนดส่ง"]


def tg_get(method: str, params: dict = None):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    r = requests.get(url, params=params, timeout=30)
    return r.json()


def md_to_tg_html(text: str) -> str:
    """แปลง Markdown **bold** *italic* `code` เป็น Telegram HTML"""
    import re
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<b><i>\1</i></b>', text, flags=re.DOTALL)
    text = re.sub(r'\*\*(.+?)\*\*',    r'<b>\1</b>',         text, flags=re.DOTALL)
    text = re.sub(r'\*(.+?)\*',        r'<i>\1</i>',         text, flags=re.DOTALL)
    text = re.sub(r'`([^`]+)`',        r'<code>\1</code>',   text)
    text = re.sub(r'^#{1,3}\s+(.+)$',  r'<b>\1</b>',         text, flags=re.MULTILINE)
    return text


def tg_send(chat_id: int, text: str):
    html = md_to_tg_html(text)
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": html, "parse_mode": "HTML"},
        timeout=10,
    )


def tg_send_html(chat_id: int, html: str, reply_markup: dict = None):
    """ส่ง HTML โดยตรง ไม่ผ่าน md_to_tg_html พร้อม optional inline keyboard"""
    payload = {"chat_id": chat_id, "text": html, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json=payload,
        timeout=10,
    )


def tg_send_typing(chat_id: int):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendChatAction",
        json={"chat_id": chat_id, "action": "typing"},
        timeout=5,
    )


# ── Email draft detection ─────────────────────────────────────────────────────
EMAIL_DRAFT_RE = re.compile(
    r'(ร่าง|draft|เขียน|ส่ง|compose)\s*(email|อีเมล|mail)',
    re.IGNORECASE
)
# คำที่นำหน้าชื่อผู้รับ
TO_PATTERNS = [
    re.compile(r'(?:หา|ถึง|to|send to|ส่งหา|ส่งให้)\s*([ก-๙a-zA-Z][ก-๙a-zA-Z\s]{0,30}?)(?:\s+เรื่อง|\s+about|\s+re:|\s*$)', re.IGNORECASE),
]
SUBJECT_PATTERN = re.compile(r'เรื่อง[:\s]+(.+)', re.IGNORECASE)

EMAIL_RE = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')

# คำที่บ่งบอกว่ากำลังบอก department
DEPT_TRIGGERS = ["แผนก", "ทีม", "department", "team", "สังกัด", "หน่วยงาน"]
# คำที่บ่งบอกว่ากำลังบอกชื่อตัวเอง
NAME_TRIGGERS = ["ชื่อฉัน", "ชื่อผม", "ชื่อหนู", "ผมชื่อ", "ฉันชื่อ", "i am", "my name is", "call me"]


def do_link_telegram(chat_id: int, email: str, from_user: dict) -> dict | None:
    """Link Telegram chat_id กับ email จริงๆ ใน backend"""
    try:
        r = requests.post(
            f"{BACKEND_URL}/api/users/link-telegram",
            json={
                "email": email,
                "telegram_chat_id": str(chat_id),
                "telegram_username": from_user.get("username"),
                "telegram_first_name": from_user.get("first_name"),
                "telegram_last_name": from_user.get("last_name"),
            },
            timeout=10,
        )
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def do_update_profile(email: str, department: str = None, full_name: str = None) -> bool:
    """อัปเดต department / full_name ใน backend"""
    payload = {}
    if department:
        payload["department"] = department
    if full_name:
        payload["full_name"] = full_name
    if not payload:
        return False
    try:
        r = requests.patch(
            f"{BACKEND_URL}/api/users/profile/{requests.utils.quote(email)}",
            json=payload,
            timeout=8,
        )
        return r.status_code == 200
    except Exception:
        return False


def detect_profile_update(chat_id: int, text: str, from_user: dict) -> str | None:
    """
    ตรวจหาข้อมูลโปรไฟล์ในข้อความสั้นๆ เท่านั้น
    ป้องกันการจับข้อความยาว เช่น meeting reports ผิดพลาด
    """
    # ข้อความยาวเกิน 200 ตัวอักษร = ไม่ใช่การอัปเดตโปรไฟล์
    if len(text) > 200:
        return None

    text_lower = text.lower()
    updated_fields = []
    current_email = get_linked_email(chat_id)
    is_linked = "@telegram.user" not in current_email

    # ── ตรวจหา Email ─────────────────────────────────────────────────────────
    found_emails = EMAIL_RE.findall(text)
    real_emails = [e for e in found_emails if "@telegram.user" not in e and "example.com" not in e]

    if real_emails:
        email = real_emails[0]
        result = do_link_telegram(chat_id, email, from_user)
        if result:
            current_email = email
            is_linked = True
            updated_fields.append(f"Email: {email}")

    # ── ตรวจหา Department (ต้องมี : หรือ = ตามหลัง trigger) ──────────────────
    dept_value = None
    for trigger in DEPT_TRIGGERS:
        if trigger in text_lower:
            pattern = re.compile(
                rf'(?:{trigger})\s*[:=]\s*([ก-๙a-zA-Z0-9 /&._-]{{1,40}})',
                re.IGNORECASE
            )
            m = pattern.search(text)
            if m:
                dept_value = m.group(1).strip().rstrip(".,!?ครับค่ะ").strip()
                break

    if dept_value and is_linked:
        if do_update_profile(current_email, department=dept_value):
            updated_fields.append(f"แผนก: {dept_value}")

    # ── ตรวจหา ชื่อตัวเอง ────────────────────────────────────────────────────
    name_value = None
    for trigger in NAME_TRIGGERS:
        if trigger in text_lower:
            pattern = re.compile(
                rf'(?:{trigger})[:\s]+([ก-๙a-zA-Z0-9 ._-]{{1,60}})',
                re.IGNORECASE
            )
            m = pattern.search(text, re.IGNORECASE)
            if m:
                name_value = m.group(1).strip().rstrip(".,!?ครับค่ะ").strip()
                break

    if name_value and is_linked:
        if do_update_profile(current_email, full_name=name_value):
            updated_fields.append(f"ชื่อ: {name_value}")

    if not updated_fields:
        return None

    reply = "✅ บันทึกข้อมูลโปรไฟล์แล้ว\n\n" + "\n".join(updated_fields)
    if is_linked:
        reply += f"\n\nดูโปรไฟล์เต็มได้ด้วย /profile"
    else:
        reply += "\n\nกรุณา link email ก่อนด้วยคำสั่ง:\n/link your.email@company.com"
    return reply


def get_linked_email(chat_id: int) -> str:
    """ดึง email จากฐานข้อมูลโดยใช้ Telegram chat_id"""
    try:
        r = requests.get(f"{BACKEND_URL}/api/users/by-telegram/{chat_id}", timeout=5)
        if r.status_code == 200:
            return r.json().get("email", f"{chat_id}@telegram.user")
    except Exception:
        pass
    return f"{chat_id}@telegram.user"


def draft_email_from_tg(chat_id: int, text: str) -> tuple | None:
    """
    ตรวจว่าเป็นคำสั่งร่าง email หรือไม่
    คืนค่า (html, reply_markup) หรือ None ถ้าไม่ใช่คำสั่ง email
    """
    if not EMAIL_DRAFT_RE.search(text):
        return None

    # ดึงชื่อผู้รับ
    recipient_name = ""
    for pat in TO_PATTERNS:
        m = pat.search(text)
        if m:
            recipient_name = m.group(1).strip()
            break

    # ดึงเรื่อง
    subj_m = SUBJECT_PATTERN.search(text)
    topic = subj_m.group(1).strip() if subj_m else ""

    user_email = get_linked_email(chat_id)
    history = conversations.get(chat_id, [])

    try:
        r = requests.post(
            f"{BACKEND_URL}/api/telegram/draft-email",
            json={
                "recipient_name": recipient_name,
                "topic": topic,
                "conversation_history": history[-8:],
                "user_email": user_email,
            },
            timeout=30,
        )
        d = r.json()
    except Exception as e:
        return (f"⚠️ ร่าง email ไม่ได้: {e}", None)

    to_name  = d.get("to_name") or recipient_name or "ผู้รับ"
    to_email = d.get("to_email") or ""
    subject  = d.get("subject") or "ติดตามผลการสนทนา"
    body     = d.get("body") or ""

    if not body:
        return (f"⚠️ ไม่สามารถร่างอีเมลได้ กรุณาลองใหม่", None)

    def esc(s): return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

    to_line = esc(to_name)
    if to_email:
        to_line += f" &lt;{esc(to_email)}&gt;"

    body_safe = esc(body[:2000])
    suffix = "\n\n<i>…(แสดงบางส่วน)</i>" if len(body) > 2000 else ""

    html = (
        f"📧 <b>ร่าง Email</b>\n"
        f"<b>To:</b> {to_line}\n"
        f"<b>Subject:</b> {esc(subject)}\n"
        f"─────────────────────\n\n"
        f"{body_safe}{suffix}"
    )

    reply_markup = None
    if to_email:
        import urllib.parse
        open_url = "http://localhost:8000/mail-open?to={}&subject={}&body={}".format(
            urllib.parse.quote(to_email),
            urllib.parse.quote(subject),
            urllib.parse.quote(body[:1800]),
        )
        reply_markup = {
            "inline_keyboard": [[
                {"text": "📬 เปิดใน Mail App", "url": open_url}
            ]]
        }

    return (html, reply_markup)


def is_meeting_report(text: str) -> bool:
    """ตรวจว่า response ของ Hermes เป็น meeting report หรือไม่"""
    lower = text.lower()
    return sum(1 for kw in MEETING_KEYWORDS if kw.lower() in lower) >= 2


def extract_owners_from_reply(reply: str) -> list[str]:
    """ดึงชื่อผู้รับผิดชอบจาก reply ของ Hermes"""
    owners = []
    # จับ "คุณX", "นายX", "นางX" ฯลฯ
    for m in re.finditer(r'(?:คุณ|นาย|นาง(?:สาว)?)\s*([ก-๙a-zA-Z]+)', reply):
        name = "คุณ" + m.group(1)
        if name not in owners:
            owners.append(name)
    return owners[:5]


def send_meeting_actions(chat_id: int, owners: list[str]):
    """ส่ง inline keyboard ของ Post-Meeting Actions"""
    # สร้างปุ่ม "ส่ง email หา [ชื่อ]" สำหรับแต่ละ owner
    email_buttons = []
    for name in owners:
        email_buttons.append(
            {"text": f"📧 ส่ง Email หา {name}", "callback_data": f"email|{name}"}
        )

    # จัดเรียงเป็นแถวๆ ละ 1 ปุ่ม
    keyboard = [[btn] for btn in email_buttons]
    # เพิ่มปุ่ม "ส่ง Email ทุกคน" ถ้ามีหลายคน
    if len(owners) > 1:
        all_names = ",".join(owners)
        keyboard.append([{"text": "📨 ส่ง Email ทุกคน", "callback_data": f"email_all|{all_names}"}])

    markup = {"inline_keyboard": keyboard}
    tg_send_html(chat_id,
        "<b>Post-Meeting Actions</b>\n"
        "เลือกการดำเนินการต่อ:",
        markup
    )


def answer_callback(callback_id: str, text: str = ""):
    """ตอบ callback query เพื่อหยุด loading spinner"""
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery",
        json={"callback_query_id": callback_id, "text": text},
        timeout=5,
    )


def handle_callback(update: dict):
    """จัดการ callback query จาก inline keyboard"""
    cb = update.get("callback_query", {})
    if not cb:
        return
    cb_id   = cb["id"]
    chat_id = cb["message"]["chat"]["id"]
    data    = cb.get("data", "")

    answer_callback(cb_id)

    # email|คุณเอ  หรือ  email_all|คุณเอ,คุณบี
    if data.startswith("email|") or data.startswith("email_all|"):
        names_str = data.split("|", 1)[1]
        names     = [n.strip() for n in names_str.split(",") if n.strip()]

        tg_send_typing(chat_id)

        user_email = get_linked_email(chat_id)
        history    = conversations.get(chat_id, [])
        ctx        = _meeting_context.get(chat_id, {})
        topic      = ctx.get("title", "")

        # ถ้ามีหลายคนให้ draft ทีละคนและส่งรวมกัน
        results = []
        for name in names:
            try:
                r = requests.post(
                    f"{BACKEND_URL}/api/telegram/draft-email",
                    json={
                        "recipient_name": name,
                        "topic": topic,
                        "conversation_history": history[-8:],
                        "user_email": user_email,
                    },
                    timeout=30,
                )
                d = r.json()
                results.append((name, d))
            except Exception as e:
                results.append((name, {"error": str(e)}))

        import urllib.parse

        for name, d in results:
            to_email = d.get("to_email") or ""
            subject  = d.get("subject") or topic or "ติดตามผลการประชุม"
            body     = d.get("body") or ""

            if not body:
                tg_send_html(chat_id, f"⚠️ ร่าง email หา {name} ไม่สำเร็จ")
                continue

            def esc(s): return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

            to_line = esc(d.get("to_name") or name)
            if to_email:
                to_line += f" &lt;{esc(to_email)}&gt;"

            html = (
                f"📧 <b>ร่าง Email</b>\n"
                f"<b>To:</b> {to_line}\n"
                f"<b>Subject:</b> {esc(subject)}\n"
                f"─────────────────────\n\n"
                f"{esc(body[:1800])}"
            )

            markup = None
            if to_email:
                open_url = "http://localhost:8000/mail-open?to={}&subject={}&body={}".format(
                    urllib.parse.quote(to_email),
                    urllib.parse.quote(subject),
                    urllib.parse.quote(body[:1800]),
                )
                markup = {"inline_keyboard": [[
                    {"text": "📬 เปิดใน Mail App", "url": open_url}
                ]]}

            tg_send_html(chat_id, html, markup)


def ask_hermes(chat_id: int, user_msg: str, user_name: str) -> str:
    """ส่งข้อความไปหา Backend /api/chat แล้วได้คำตอบจาก OpenAI"""
    history = conversations.get(chat_id, [])

    try:
        user_email = get_linked_email(chat_id)
        r = requests.post(
            f"{BACKEND_URL}/api/chat",
            json={
                "message": user_msg,
                "user_email": user_email,
                "department": "general",
                "conversation_history": history[-10:],
            },
            timeout=30,
        )
        data = r.json()
        reply = data.get("reply", "ไม่ได้รับคำตอบ")

        # บันทึก history
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": reply})
        conversations[chat_id] = history[-20:]

        # ถ้ามี skill แนะนำ
        suggested = data.get("suggested_skills", [])
        if suggested:
            skills_text = "\n".join([f"  • {s['name']}" for s in suggested])
            reply += f"\n\n🧩 <b>Skill ที่เกี่ยวข้อง:</b>\n{skills_text}"

        return reply

    except Exception as e:
        return f"⚠️ เชื่อมต่อ Backend ไม่ได้: {e}"


def run_skill_via_api(skill_id: int, input_text: str, chat_id: int) -> str:
    """เรียกใช้ Skill ผ่าน Backend"""
    try:
        r = requests.post(
            f"{BACKEND_URL}/api/skills/{skill_id}/run",
            json={"input_text": input_text, "user_email": f"{chat_id}@telegram.user"},
            timeout=60,
        )
        data = r.json()
        return data.get("output", "ไม่มีผลลัพธ์")
    except Exception as e:
        return f"⚠️ Error: {e}"


def handle_message(update: dict):
    """จัดการข้อความที่รับจาก Telegram"""
    message = update.get("message", {})
    if not message:
        return

    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()
    user_name = message.get("from", {}).get("first_name", "User")

    if not text:
        return

    print(f"[{chat_id}] {user_name}: {text}")

    # ── คำสั่งพิเศษ ────────────────────────────────────────────────────────────

    # /start
    if text == "/start":
        linked_email = get_linked_email(chat_id)
        is_linked = "@telegram.user" not in linked_email
        link_hint = (
            f"\nบัญชีของคุณเชื่อมกับ <b>{linked_email}</b> แล้ว"
            if is_linked else
            "\n\nเชื่อม Telegram กับระบบ:\n/link your.email@company.com"
        )
        tg_send(chat_id,
            f"สวัสดีครับ <b>{user_name}</b>\n\n"
            "ผมคือ <b>Hermes AI Assistant</b>\n"
            "สามารถถามอะไรก็ได้ หรือใช้คำสั่งต่อไปนี้:\n\n"
            "/skills - ดู Skill ทั้งหมด\n"
            "/run [id] [ข้อความ] - เรียกใช้ Skill\n"
            "/profile - ดูข้อมูลโปรไฟล์\n"
            "/link [email] - เชื่อมบัญชีกับระบบ\n"
            "/clear - ล้างประวัติการสนทนา\n"
            "/help - ดูคำสั่งทั้งหมด"
            + link_hint
        )
        return

    # /help
    if text == "/help":
        tg_send(chat_id,
            "<b>คำสั่งทั้งหมด</b>\n\n"
            "/start — เริ่มต้นใช้งาน\n"
            "/profile — ดูข้อมูลโปรไฟล์และสถานะการเชื่อม\n"
            "/link [email] — เชื่อม Telegram กับ email องค์กร\n"
            "/skills — ดูรายชื่อ Skill ที่ใช้งานได้\n"
            "/run [id] [ข้อความ] — เรียกใช้ Skill เช่น /run 1 สรุปเอกสารนี้\n"
            "/clear — ล้างประวัติการสนทนา\n\n"
            "<b>ร่าง Email</b>\n"
            "พิมพ์: <b>ร่าง email หา [ชื่อ] เรื่อง [หัวข้อ]</b>\n"
            "เช่น: ร่าง email หาคุณเอ เรื่องสรุปประชุม\n\n"
            "<b>คำสั่ง Approval</b>\n"
            "/approve_[id] — อนุมัติ Skill\n"
            "/reject_[id] — ปฏิเสธ Skill\n"
            "/edit_[id] — ขอแก้ไข Skill"
        )
        return

    # /profile
    if text == "/profile":
        linked_email = get_linked_email(chat_id)
        is_linked = "@telegram.user" not in linked_email
        if is_linked:
            try:
                r = requests.get(f"{BACKEND_URL}/api/users/profile/{linked_email}", timeout=5)
                if r.status_code == 200:
                    p = r.json()
                    tg_send(chat_id,
                        f"<b>โปรไฟล์ของคุณ</b>\n\n"
                        f"ชื่อ: {p.get('full_name') or user_name}\n"
                        f"Email: {p.get('email')}\n"
                        f"แผนก: {p.get('department') or '-'}\n"
                        f"Role: {p.get('role') or 'member'}\n"
                        f"Telegram: @{p.get('telegram_username') or user_name}\n"
                    )
                    return
            except Exception:
                pass
        tg_send(chat_id,
            f"<b>โปรไฟล์ของคุณ</b>\n\n"
            f"ชื่อ (Telegram): {user_name}\n"
            f"Chat ID: {chat_id}\n"
            f"สถานะ: ยังไม่ได้เชื่อมกับระบบ\n\n"
            f"ใช้คำสั่ง /link your.email@company.com เพื่อเชื่อม"
        )
        return

    # /link [email]
    if text.startswith("/link"):
        parts = text.split(" ", 1)
        if len(parts) < 2 or "@" not in parts[1]:
            tg_send(chat_id, "รูปแบบผิด ใช้: /link your.email@company.com")
            return
        email = parts[1].strip()
        from_user = message.get("from", {})
        try:
            r = requests.post(
                f"{BACKEND_URL}/api/users/link-telegram",
                json={
                    "email": email,
                    "telegram_chat_id": str(chat_id),
                    "telegram_username": from_user.get("username"),
                    "telegram_first_name": from_user.get("first_name"),
                    "telegram_last_name": from_user.get("last_name"),
                },
                timeout=10,
            )
            if r.status_code == 200:
                d = r.json()
                tg_send(chat_id,
                    f"เชื่อมบัญชีสำเร็จ\n\n"
                    f"ชื่อ: {d.get('full_name') or user_name}\n"
                    f"Email: {d.get('email')}\n"
                    f"ตอนนี้ Skill ที่สร้างจากระบบจะแสดงชื่อที่ถูกต้องแล้ว"
                )
            elif r.status_code == 409:
                tg_send(chat_id, f"Telegram นี้เชื่อมกับ {r.json().get('detail', 'email อื่น')} อยู่แล้ว")
            else:
                tg_send(chat_id, f"เชื่อมไม่สำเร็จ: {r.json().get('detail', 'ไม่ทราบสาเหตุ')}")
        except Exception as e:
            tg_send(chat_id, f"เชื่อมต่อ Backend ไม่ได้: {e}")
        return

    # /clear
    if text == "/clear":
        conversations[chat_id] = []
        tg_send(chat_id, "🗑 ล้างประวัติการสนทนาแล้วครับ")
        return

    # /skills
    if text == "/skills":
        try:
            r = requests.get(f"{BACKEND_URL}/api/skills/list?limit=20", timeout=10)
            data = r.json()
            skills = data.get("items", [])
            if not skills:
                tg_send(chat_id, "ยังไม่มี Skill ในระบบ")
                return

            msg = "🧩 <b>Skill ที่มีในระบบ:</b>\n\n"
            for s in skills:
                status_icon = {
                    "team_available": "✅",
                    "company_published": "🌐",
                    "draft": "📝",
                    "private": "🔒",
                    "pending_team_review": "⏳",
                    "rejected": "❌",
                }.get(s["status"], "•")
                msg += f"{status_icon} <b>ID:{s['id']}</b> {s['name']}\n"
                if s.get("description"):
                    msg += f"   {s['description'][:60]}...\n"
                msg += "\n"
            msg += "ใช้ /run [id] [ข้อความ] เพื่อเรียกใช้ Skill"
            tg_send(chat_id, msg)
        except Exception as e:
            tg_send(chat_id, f"⚠️ โหลด Skill ไม่ได้: {e}")
        return

    # /run [skill_id] [input]
    if text.startswith("/run "):
        parts = text.split(" ", 2)
        if len(parts) < 3:
            tg_send(chat_id, "❌ รูปแบบผิด ใช้: /run [id] [ข้อความ]\nเช่น: /run 1 สรุมเอกสารนี้")
            return
        try:
            skill_id = int(parts[1])
            input_text = parts[2]
            tg_send_typing(chat_id)
            tg_send(chat_id, f"⏳ กำลังประมวลผล Skill ID {skill_id}...")
            result = run_skill_via_api(skill_id, input_text, chat_id)
            tg_send(chat_id, f"✅ <b>ผลลัพธ์:</b>\n\n{result[:3000]}")
        except ValueError:
            tg_send(chat_id, "❌ ID ต้องเป็นตัวเลข เช่น /run 1 ข้อความ")
        return

    # /approve_X /reject_X /edit_X  ── Approval via Telegram
    for prefix, action in [("/approve_", "approve"), ("/reject_", "reject"), ("/edit_", "request_edit")]:
        if text.startswith(prefix):
            try:
                approval_id = int(text.replace(prefix, "").strip())
                r = requests.post(
                    f"{BACKEND_URL}/api/approvals/{approval_id}/action",
                    json={
                        "approval_id": approval_id,
                        "action": action,
                        "reviewed_by": f"@{user_name}",
                        "comments": f"ดำเนินการผ่าน Telegram โดย {user_name}",
                    },
                    timeout=10,
                )
                data = r.json()
                icon = {"approve": "✅", "reject": "❌", "request_edit": "📝"}[action]
                tg_send(chat_id,
                    f"{icon} <b>{action.replace('_',' ').title()}</b> สำเร็จ!\n"
                    f"Skill ID: {data.get('skill_id')}\n"
                    f"Status ใหม่: {data.get('new_status', '-')}"
                )
            except Exception as e:
                tg_send(chat_id, f"⚠️ Error: {e}")
            return

    # ── ร่าง Email ─────────────────────────────────────────────────────────────
    email_result = draft_email_from_tg(chat_id, text)
    if email_result is not None:
        tg_send_typing(chat_id)
        html_msg, markup = email_result
        tg_send_html(chat_id, html_msg, markup)
        return

    # ── ตรวจหาข้อมูลโปรไฟล์ในข้อความก่อน ────────────────────────────────────
    profile_reply = detect_profile_update(chat_id, text, message.get("from", {}))
    if profile_reply:
        tg_send(chat_id, profile_reply)
        return

    # ── ข้อความทั่วไป → ส่งให้ Hermes Agent ──────────────────────────────────
    tg_send_typing(chat_id)
    reply = ask_hermes(chat_id, text, user_name)
    print(f"[{chat_id}] Hermes: {reply[:100]}...")
    tg_send(chat_id, reply)

    # ── ตรวจว่าเป็น Meeting Report → แสดง Post-Meeting Actions ───────────────
    if is_meeting_report(reply):
        owners = extract_owners_from_reply(reply)
        # บันทึก meeting context สำหรับ callback
        _meeting_context[chat_id] = {
            "title": text[:80] if len(text) < 80 else "",
            "owners": owners,
        }
        if owners:
            send_meeting_actions(chat_id, owners)


def main():
    if not TOKEN or "your_telegram" in TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN ยังไม่ได้ตั้งค่าใน .env")
        return

    print("🤖 Hermes Telegram Bot กำลังเริ่มต้น...")
    print(f"   Backend: {BACKEND_URL}")

    # ตรวจสอบ Backend
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=5)
        print(f"   Backend: ✅ {r.json()}")
    except Exception:
        print("   Backend: ⚠️ ไม่สามารถเชื่อมต่อได้ ตรวจสอบว่า Backend ทำงานอยู่")

    print("\n✅ Bot พร้อมรับข้อความแล้ว (Ctrl+C เพื่อหยุด)\n")

    offset = 0
    while True:
        try:
            result = tg_get("getUpdates", {"offset": offset, "timeout": 25})
            updates = result.get("result", [])

            for update in updates:
                offset = update["update_id"] + 1
                if "callback_query" in update:
                    handle_callback(update)
                else:
                    handle_message(update)

        except KeyboardInterrupt:
            print("\n🛑 Bot หยุดทำงาน")
            break
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(3)


if __name__ == "__main__":
    main()
