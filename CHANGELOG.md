# Changelog — Hermes AI Skill Hub

## 13 Jun 2026 (v7) — แก้ Company Directory ว่างเปล่า + Add Employee ขัดแย้งกัน

- **อาการ:** Directory โชว์ 0 คน / "No employees found" แต่กด Add Employee กลับเตือน "Employee already exists"
- **สาเหตุ:** list/stats กรองเฉพาะ user ที่ `password_set = true` แต่ (1) user ที่ login ครั้งแรกและ (2) พนักงานที่เพิ่มผ่านปุ่ม Add Employee ยังไม่มีรหัสผ่าน → ถูกซ่อนจาก directory ตลอดกาล ขณะที่ตัวเช็คตอน create ดูจาก email ตรงๆ จึงบอกว่ามีอยู่แล้ว
- **แก้:** directory แสดงพนักงาน active ทุกคนไม่สนสถานะรหัสผ่าน (4 จุด: stats, employees list, departments, directory assistant) — ทดสอบแล้ว: เห็นครบ + เพิ่มคนใหม่โผล่ทันที

## 13 Jun 2026 (v6) — ทำตามแผน skill-design.html: Auto-Skill Generator เต็มรูปแบบ + P1 Catalog

### ✨ Auto-Skill Generator (อัปเกรดใหญ่)
- **เช็ค Skill Store ก่อนสร้างซ้ำ:** intent ที่ทำซ้ำ ถ้ามี skill ใน Store ที่ตรงอยู่แล้ว → เสนอ "ติดตั้ง" แทนการสร้างใหม่ (ทดสอบ: review-code 2 ครั้ง → เสนอติดตั้ง Code Review Assistant)
- **ออกแบบ skill แบบ personalize:** ใช้ตัวอย่างคำขอจริง + แผนก + PREFERENCE + FACT ของ user — prompt ที่ได้สะท้อนวิธีทำงานจริง (ทดสอบ: ขอเขียนสคริปต์ tiktok 2 ครั้ง → ได้ skill ที่จำสเปก "ไม่เกิน 30 วินาที" จากคำขอจริง)
- **ข้าม intent ที่มี skill ครอบคลุมแล้ว** (สร้างเอง/ติดตั้งแล้ว) — ไม่เสนอซ้ำซาก
- **Generate on-demand:** `POST /api/skills/suggestions/{email}/generate` — สั่งคิด skill ได้ทันทีไม่ต้องรอครบ 3 ครั้ง
- **การ์ด suggestion ในแชท** พร้อมปุ่ม "✨ สร้าง Skill เลย / ➕ ติดตั้งเลย / ไม่ต้อง" + ดู prompt ที่ออกแบบให้ก่อนตัดสินใจ (เดิมต้องพิมพ์ตอบ)
- accept รองรับทั้ง create และ install (`action: created|installed`)

### 📚 P1 Skill Catalog — seed เข้า Skill Store ตามแผน (7 ตัว)
Annual Report Summarizer, Financial Highlight Extractor (IR) · Code Review Assistant, Log Analyzer (Dev) · EN-TH IR Translator (Content) · Test Case Generator (QA) · Client Email Draft (Sales) — ทุกตัวมี prompt template คุณภาพ production (โครงสร้าง output + ข้อห้ามแต่งเติม) สถานะ Published ติดตั้งได้ทันที

### 📊 IR Document Q&A (Hero Skill P1)
- PDF แตกเป็นรายหน้า มี marker `[หน้า N]` ทุกหน้า + ขยาย limit 8,000 → 30,000 ตัวอักษร (เดิม Annual Report เห็นแค่ ~3 หน้าแรก)
- ถามจากไฟล์แล้ว Hermes **อ้างอิงเลขหน้า** ในคำตอบ และบอกตรงๆ เมื่อหาไม่พบ

### 🗣 แทนชื่อจริงผู้พูด (Roadmap item)
- พิมพ์ "ผู้พูด A คือ คุณนริศรา และผู้พูด B คือ คุณสมชาย" → อัปเดต transcript ใน memory เป็นชื่อจริงทันที ใช้ทำ MOM/สรุปต่อด้วยชื่อจริงได้ (ทดสอบผ่าน)

## 13 Jun 2026 (v5) — Hermes เข้าถึง Transcript ที่ถอดไว้ได้ (ถาม-ตอบ/สรุปต่อในแชท)

- **ปัญหา:** ถอดเสียงเสร็จแล้วพิมพ์ "สรุปมา" → Hermes ตอบ "ไม่มีข้อมูลให้สรุป" เพราะ transcript อยู่แค่ในการ์ด UI ไม่เคยถึง `/api/chat`
- **แก้:** เพิ่ม `MemoryType.TRANSCRIPT` — ถอดเสียงเสร็จ backend เก็บ transcript ผูกกับ user อัตโนมัติ (ทั้ง endpoint ปกติและ async job, frontend ส่ง `user_email` ไปกับไฟล์)
- chat โหลด transcript ล่าสุดเข้า system prompt ทุกครั้ง — ขอสรุป/ถามเจาะจง/สั่งทำ MOM ต่อได้ทันที **แม้รีเฟรชหน้าหรือเปิดแชทใหม่**
- ไฟล์ยาว >36k ตัวอักษรถูกย่อแบบเก็บสาระก่อน inject (มี cache md5 — ย่อครั้งเดียวต่อไฟล์ ไม่หน่วงทุกข้อความ)
- ทดสอบจริง: "สรุปมา" → สรุป+action items ถูกต้อง / "ใครต้องตอบลูกค้าเมื่อไหร่" → ตอบ "ฝ่ายขาย ภายในวันศุกร์" ตรง transcript

## 13 Jun 2026 (v4) — Quick Summary / Intelligence / Draft Email การ์ดใหญ่ + แก้บั๊กการทำงาน

### 🐛 แก้บั๊กการทำงาน
- **Draft Email ไม่อิงเนื้อหาประชุม:** frontend ส่ง `meeting_text/participants/action_items` ตรงๆ แต่ backend อ่านจาก `meeting_data` ที่ซ้อนอีกชั้นเท่านั้น → ข้อมูลถูกทิ้งหมด อีเมลออกมากลวง ตอนนี้รับทั้ง 2 รูปแบบ + ส่งเนื้อหาประชุมเข้า prompt ด้วย (ทดสอบแล้ว: อีเมลอ้างถึงมติ/action items จริง)
- **MOM แต่งวันที่/สถานที่เอง:** เข้ม prompt — ข้อมูลที่ไม่มีใน transcript ต้องคงเป็น `[...]` (ทดสอบแล้วไม่ hallucinate)
- **Error ถูกกลืนเงียบ:** เพิ่ม `_miJson` เช็ค HTTP status ทุก fetch — พังแล้วเห็นสาเหตุ ไม่ใช่การ์ดว่างเปล่า; โหมด Quick แต่ละส่วนพังได้โดยไม่ล้มทั้งหมด

### 🎨 การ์ดผลลัพธ์ใหญ่ครบทุกโหมด (สไตล์เดียวกับ Full Transcript)
- **⚡ QUICK SUMMARY (เขียว):** สรุปประเด็น + Action Items เลขกำกับ + MOM + ร่างอีเมล ครบในการ์ดเดียว
- **🧠 MEETING INTELLIGENCE (ม่วง):** Executive Summary, Decisions, Risks, Action Items (badge HIGH), Timeline, Next Steps + footer นับจำนวน
- **✉️ DRAFT EMAIL (ส้ม):** Subject + เนื้อหาเต็ม + Open in Email Composer
- ทุกการ์ดมีปุ่ม **Download .txt / Copy / ขยาย-ย่อ** และกว้าง 96% ของแชท

## 13 Jun 2026 (v3) — Full Transcript Card ใหม่ (UI)

- **Transcript card ขนาดใหญ่เต็มความกว้างแชท** แทนกล่องเล็ก 420px เดิม
- แต่ละบรรทัดแสดงเป็นแถว `[MM:SS]` + ป้ายผู้พูดสีประจำตัว (A=น้ำเงิน, B=เขียว, C=ม่วง, ...) + เนื้อหา
- Header: ชื่อไฟล์ต้นฉบับ + ความยาว | ปุ่ม **Download .txt**, **Copy Transcript**, **ขยาย/ย่อ**
- Footer: `Total MM:SS | Speakers: N (A, B)` เหมือน mock design
- รองรับ transcript แบบเก่า (ไม่มี timestamp) — แสดงเป็นบรรทัดธรรมดา

## 13 Jun 2026 (v2) — Timestamps + Speaker Diarization

### 🎙️ Transcript แบบ `[MM:SS] ผู้พูด A: ...` (segment-based pipeline ใหม่ทั้งชุด)
- **โมเดลหลักเปลี่ยนเป็น `gpt-4o-transcribe-diarize`** (ทดสอบกับ API จริงแล้ว): คืน segments พร้อมเวลาเริ่ม/จบ + ป้ายผู้พูด A/B/C — รองรับ `language` + `chunking_strategy=auto`, ลิมิต 1,400 วิ/call
- **ไฟล์ ≤ 23 นาที → diarize ครั้งเดียวทั้งไฟล์** = ป้ายผู้พูดสม่ำเสมอ 100%
- **ไฟล์ยาวกว่า → chunk 10 นาที + overlap 30 วิ** แล้ว map ป้ายผู้พูดข้าม chunk โดยโหวตจากช่วงเสียงที่ถอดซ้ำ, ตัด segment ซ้ำด้วยเวลา (แม่นกว่า text-merge เดิม)
- **dual-check ทุก chunk กับ whisper-1 `verbose_json`**: จาก log จริง gpt-4o-transcribe เคยคืน 22 ตัวอักษรจากเสียง 10 นาที และข้ามเนื้อหากลางไฟล์ — ถ้า whisper-1 ได้เนื้อหายาวกว่า >10% จะใช้ข้อความ whisper-1 แล้วยืมป้ายผู้พูดจาก diarize มาใส่ตามช่วงเวลา (ปิดได้: `TRANSCRIBE_MODE=single`)
- ผู้พูดคนเดียว → ไม่ใส่ป้ายให้รก แสดงแค่ `[MM:SS] ...`
- API คืนเพิ่ม: `segments` (โครงสร้างเต็ม) + `plain_text` (ไม่มี timestamp)
- clean-transcript รักษา `[MM:SS]` และ `ผู้พูด X:` ไว้เสมอ
- ทดสอบ E2E ผ่าน: ไฟล์ 12 นาทีแบบ 3 chunks → coverage 715/715 วินาที ไม่มีรูโหว่ >30 วิ

## 13 Jun 2026 — Transcription Overhaul + Smart Memory + Auto-Skill

### 🎤 ถอดเสียงครบและแม่นขึ้น (แก้ปัญหา "ถอดมาไม่ครบ/ถอดไม่ดี")
- **แก้สาเหตุหลักของ transcript หาย:** `/api/meeting/clean-transcript` เดิมตัด input เหลือ 6,000 ตัวอักษร + output 2,048 tokens แล้ว frontend เอาผลไปแทน transcript เต็ม → ประชุมยาวหายเกือบหมด ตอนนี้ clean ทีละท่อนครบทั้งไฟล์ และถ้า LLM ตอบสั้นผิดปกติจะคงต้นฉบับท่อนนั้นไว้
- **Chunk 20 นาที → 10 นาที:** `gpt-4o-transcribe` ตัดเสียงยาวทิ้งเงียบๆ (สาเหตุที่ถอดไม่ครบ) — chunk สั้นลงปลอดภัยกว่า
- **Overlap 15 วินาทีระหว่าง chunk + fuzzy merge:** คำตรงรอยต่อไม่หายอีก
- **Prompt ต่อเนื่องข้าม chunk:** ส่งท้าย transcript ก่อนหน้าเป็น context → สะกดชื่อคน/ศัพท์เฉพาะสม่ำเสมอ
- **Retry 3 ครั้ง/chunk + fallback model:** chunk เดียวพังไม่ทำให้งานทั้งชั่วโมงพัง (ใส่ marker บอกช่วงนาทีที่พลาดแทน)
- **ตรวจความครบอัตโนมัติ:** ถ้า output สั้นผิดปกติเทียบกับความยาวเสียง → ถอดซ้ำด้วย whisper-1 แล้วเก็บผลที่ยาวกว่า
- **แก้ regex ลบคำซ้ำที่กินข้อความจริง:** เดิมลบคำที่พูดซ้ำ 3 ครั้ง (ซึ่งคนพูดจริง) + ตัวเลขอย่าง "555555" — ตอนนี้ลบเฉพาะ loop hallucination จริงๆ (4-6+ copies) และไม่แตะตัวเลข
- **เพิ่ม language hint `th`** (ตั้งผ่าน env `TRANSCRIBE_LANGUAGE`)
- **สรุป/MOM/Intelligence ครอบคลุมทั้งประชุม:** เดิมตัด transcript เหลือ 2,000-6,000 ตัวอักษรแรก ตอนนี้ประชุมยาวถูกย่อทีละท่อนแบบเก็บมติ/action items/ตัวเลขครบทุกช่วงก่อนส่งให้ LLM

### 🧠 ความจำอัจฉริยะ (Smart Memory)
- **FACT memory:** Hermes สกัดข้อเท็จจริงระยะยาวจากบทสนทนาอัตโนมัติ (ตำแหน่ง, โปรเจค, ลูกค้า) — จำข้ามเซสชัน
- **PREFERENCE memory:** จำรูปแบบที่ user ชอบ (ภาษา, รูปแบบสรุป, ความยาว) แล้วทำตามเสมอ
- **SKILL memory เก็บประวัติ 50 ครั้งล่าสุด** (เดิมจำได้แค่ skill เดียวล่าสุด)
- **Chat memory ขยายเป็น 40 ข้อความ + cross-session continuity:** เปิดแชทใหม่ Hermes ยังจำบทสนทนาก่อนหน้า
- ทั้งหมด inject เข้า system prompt ของ chat อัตโนมัติ

### ✨ จำพฤติกรรม + คิด Skill ให้เอง (Auto-Skill Generation)
- **BEHAVIOR memory:** ทุกข้อความถูกจัดหมวด intent ใน background (ไม่หน่วงการตอบ) และนับความถี่
- **สั่งงานแบบเดิมครบ 3 ครั้ง → Hermes ออกแบบ Skill ให้เอง** (ชื่อ, คำอธิบาย, prompt template, tags) แล้วเสนอในแชท
- ตอบ "สร้าง skill ที่แนะนำ" → สร้างเป็น Private Skill ทันที / "ไม่ต้อง" → ไม่เสนอ intent นั้นอีก
- REST API: `GET/POST /api/skills/suggestions/{user_email}` (+ `/accept`, `/dismiss`)

## Latest Changes (Jun 2026)

### 🎯 Major Features Added

#### 1. **Dashboard Removed** ✅
- ❌ Deleted Dashboard page entirely
- ✅ Chat Assistant is now the default landing page after login
- ✅ Cleaner navigation with 4 main sections: Chat, My Skills, Skill Store, Create Skill

#### 2. **Web Interface Improvements** ✅
- ✅ **Draft Email Modal** — Auto-fill "To" field from saved contacts
  - Click contact in Address Book → adds email to To field
  - Lookup by alias (e.g., "คุณเอ") → finds email from contact book
- ✅ **Meeting Report** — Date handling
  - "วันนี้" auto-converts to Thai Buddhist calendar date (CE + 543)
  - Example: "27 มิถุนายน 2569"
- ✅ **Create Skill Page** — 2-column responsive layout
  - Left: Skill form fields
  - Right: Prompt preview (matches height dynamically)
  - Simple Mode switch works correctly
- ✅ **Chat Textarea** — Auto-expanding input
  - Grows as you type (up to 200px max)
  - Resets after sending message
- ✅ **Message Rendering** — Markdown to HTML
  - Headings: `# ` to `###### ` (with proper sizing)
  - Bold: `**text**` → `<b>text</b>`
  - Italic: `*text*` → `<i>text</i>`
  - Bullets: `- item` → `• item`
  - Code: `` `code` `` → styled inline code
  - Skill badge now displays below response (not beside)

#### 3. **Skill Management** ✅
- ✅ **Share to Store** button (Draft → Team Available)
- ✅ **Unshare** button (Team Available → Private)
- ✅ **Delete Skill** button with confirmation
  - Works for all skill statuses
  - Cleans up installations automatically
- ✅ Removed approval system entirely
  - No more 3-step approval workflow
  - Direct share/unshare without review

#### 4. **Telegram Bot Integration** ✅
- ✅ **Polling Mode** — No webhook setup needed
  - Runs as background thread on backend startup
  - Auto-detects duplicate updates (offset tracking)
  - Prevents multiple processes (lock file mechanism)
- ✅ **Account Linking**
  - `/start email@example.com` — Link Telegram to account
- ✅ **Commands**
  - `/skills` — List user's skills
  - `/store` — View Skill Store
  - Regular chat — AI-powered responses
- ✅ **Chat Integration**
  - Sends user messages to Claude API
  - Claude responds (maintains chat history per user)
  - Markdown converted to Telegram HTML
  - Shows headings, bold, italic, bullets correctly
- ✅ **No Extra Buttons**
  - Removed persistent "My Skills" / "Skill Store" buttons
  - Chat is clean, focused on conversation

---

## Technical Details

### Backend Changes
- **File:** `backend/main.py`
- **Added Functions:**
  - `get_chat_history()` — Manage Telegram chat history
  - `add_to_history()` — Store messages per user
  - `is_skill_request()` — Detect if user wants skill help
  - `find_relevant_skills()` — AI-match skills to user intent
  - `md_to_tg()` — Convert markdown to Telegram HTML
  - `process_telegram_update()` — Handle incoming updates
  - `telegram_polling_thread()` — Background polling loop
- **Telegram Bot Features:**
  - Polling (not webhook) for easier local development
  - Chat history per user (last 20 messages)
  - Claude integration for intelligent responses
  - Markdown-to-HTML conversion for proper formatting

### Frontend Changes
- **File:** `app.html` (~3000+ lines)
- **Improvements:**
  - Chat textarea auto-resize on input
  - Meeting report date conversion (Thai calendar)
  - Markdown heading support (6 levels)
  - Skill sharing/unsharing UI
  - Delete skill with confirmation
  - Contact auto-fill in draft email
  - Address Book click-to-add functionality

### Database
- **No schema changes** — existing models support all new features
- `User.telegram_chat_id` — links Telegram to account
- `SkillInstallation` — auto-cleanup on skill delete

---

## How to Run

### Backend (with Telegram Bot)
```bash
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

**Important:** Do NOT use `--reload` — it spawns multiple polling threads

### Frontend
```bash
python3 -m http.server 8080
# Open http://localhost:8080/app.html
```

### Telegram Bot
- Automatically starts when backend runs
- No separate setup needed
- Find bot: `@HermesAISkillHubBot`
- First message: `/start narisara.pa@shareinvestor.com`

---

## Known Issues & Limitations

1. **OpenAI API** — Currently uses OpenAI (GPT-4o-mini)
   - Can switch to Claude if needed
   - API key in `.env` under `OPENAI_API_KEY`

2. **Telegram Polling** — Uses long polling (not webhook)
   - More reliable for local development
   - Slight delay (30s timeout + 0.5s loop interval)
   - Production should use webhook

3. **Chat History** — Stored in memory
   - Lost on server restart
   - Consider DB storage for production

---

## Testing Checklist

- [x] Web login works
- [x] Create skill with 2-column layout
- [x] Share skill to store
- [x] Unshare skill
- [x] Delete skill
- [x] Draft email with contact lookup
- [x] Meeting report date auto-fill
- [x] Chat textarea expands
- [x] Markdown rendering (headings, bold, etc)
- [x] Telegram bot receives messages
- [x] Telegram auto-links account
- [x] Telegram Claude integration
- [x] No duplicate Telegram responses
- [x] Telegram markdown formatting

---

## Next Steps (Future)

1. **Database Chat History** — Persist conversations
2. **Skill Execution** — Run skills from Telegram
3. **Webhook Mode** — For production deployment
4. **Claude API** — Switch from OpenAI if preferred
5. **Better Skill Matching** — Semantic search
6. **User Profiles** — Preferences, settings
7. **Analytics** — Track skill usage

---

## File Changes Summary

```
Modified:
- backend/main.py          (+500 lines) Telegram polling, chat integration
- app.html                 (+100 lines) UI improvements, markdown rendering

Created:
- RUN.md                   Quick start guide
- CHANGELOG.md             This file
```

---

**Last Updated:** 2026-06-07  
**Status:** ✅ Ready for testing  
**Next Release:** Skill execution from Telegram
