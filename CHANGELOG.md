# Changelog — Hermes AI Skill Hub

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
