# 🧠 User Memory System - API Documentation

## Overview
ระบบเก็บข้อมูลที่ต้องจำเกี่ยวกับแต่ละ User เช่น Profile, Skill ที่ใช้ล่าสุด, Chat History, Custom Notes

---

## 📊 Database Structure

**ตาราง: `user_memory`**

```
┌─────────────┬──────────────┬──────────────────┐
│ Column      │ Type         │ Description      │
├─────────────┼──────────────┼──────────────────┤
│ id          │ Integer      │ Primary Key      │
│ user_email  │ String       │ User Email       │
│ memory_type │ Enum         │ Type of memory   │
│ content     │ JSON         │ Data             │
│ created_at  │ DateTime     │ Created time     │
│ updated_at  │ DateTime     │ Updated time     │
│ is_active   │ Boolean      │ Active status    │
└─────────────┴──────────────┴──────────────────┘
```

**Memory Types:**
- `profile` - Profile information (name, department, role)
- `skill` - Recently used skills
- `chat` - Chat context and history
- `custom` - Custom notes (user asked to remember)
- `preference` - User preferences (language, theme, etc.)

---

## 🔌 API Endpoints

### 1. **Save Generic Memory**
```http
POST /api/memory/save?user_email=user@example.com
Content-Type: application/json

{
  "memory_type": "custom",
  "content": {
    "key1": "value1",
    "key2": "value2"
  }
}
```

**Response:**
```json
{
  "id": 1,
  "user_email": "user@example.com",
  "memory_type": "custom",
  "content": {"key1": "value1", "key2": "value2"},
  "created_at": "2026-06-08T12:00:00",
  "updated_at": "2026-06-08T12:00:00",
  "is_active": true
}
```

---

### 2. **Save Profile Memory**
```http
POST /api/memory/profile?user_email=user@example.com
Content-Type: application/json

{
  "full_name": "Narisara Pae",
  "department": "Sales",
  "role": "member"
}
```

---

### 3. **Save Skill Memory**
```http
POST /api/memory/skill?user_email=user@example.com
Content-Type: application/json

{
  "skill_id": 1,
  "skill_name": "Meeting Minutes Generator"
}
```

---

### 4. **Save Chat Memory**
```http
POST /api/memory/chat?user_email=user@example.com
Content-Type: application/json

{
  "message": "สร้างรายงานการประชุม",
  "context": {
    "duration": "1 hour",
    "participants": 5,
    "topics": ["sales", "targets"]
  }
}
```

---

### 5. **Save Custom Note**
```http
POST /api/memory/custom?user_email=user@example.com
Content-Type: application/json

{
  "note": "ต้องทำให้สมบูรณ์จนถึงวันศุกร์นี้",
  "tags": ["important", "urgent", "todo"]
}
```

---

### 6. **Get User Memory**
```http
GET /api/memory/user@example.com?memory_type=skill&limit=5
```

**Parameters:**
- `memory_type` (optional) - Filter by type: profile, skill, chat, custom, preference
- `limit` (optional) - Max items to return (default: 10)

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "user_email": "user@example.com",
      "memory_type": "skill",
      "content": {"skill_id": 1, "skill_name": "Meeting Minutes Generator", "used_at": "..."},
      "created_at": "2026-06-08T12:00:00",
      "updated_at": "2026-06-08T12:00:00",
      "is_active": true
    }
  ],
  "total": 1
}
```

---

### 7. **Delete Single Memory**
```http
DELETE /api/memory/1
```

**Response:**
```json
{
  "success": true,
  "message": "Memory deleted"
}
```

---

### 8. **Delete All User Memory**
```http
DELETE /api/memory/user/user@example.com?memory_type=chat
```

**Parameters:**
- `memory_type` (optional) - Only delete specific type

**Response:**
```json
{
  "success": true,
  "deleted_count": 5
}
```

---

## 💡 Usage Examples

### **Python Example**
```python
import requests

BASE_URL = "http://localhost:8000"
USER_EMAIL = "narisara.pa@example.com"

# Save profile
requests.post(f"{BASE_URL}/api/memory/profile",
  params={"user_email": USER_EMAIL},
  json={
    "full_name": "Narisara Pae",
    "department": "Sales",
    "role": "member"
  }
)

# Save skill
requests.post(f"{BASE_URL}/api/memory/skill",
  params={"user_email": USER_EMAIL},
  json={
    "skill_id": 1,
    "skill_name": "Meeting Minutes Generator"
  }
)

# Get recent skills
response = requests.get(f"{BASE_URL}/api/memory/{USER_EMAIL}",
  params={"memory_type": "skill", "limit": 5}
)
print(response.json())
```

---

### **JavaScript/Frontend Example**
```javascript
const BASE_URL = "http://localhost:8000";
const USER_EMAIL = "user@example.com";

// Save custom note
async function saveNote(note, tags) {
  const response = await fetch(
    `${BASE_URL}/api/memory/custom?user_email=${USER_EMAIL}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ note, tags })
    }
  );
  return await response.json();
}

// Get memory
async function getUserMemory(type = null, limit = 10) {
  let url = `${BASE_URL}/api/memory/${USER_EMAIL}?limit=${limit}`;
  if (type) url += `&memory_type=${type}`;
  
  const response = await fetch(url);
  return await response.json();
}

// Usage
await saveNote("Remember to update contacts", ["contacts", "important"]);
const memories = await getUserMemory("custom");
console.log(memories);
```

---

### **cURL Example**
```bash
# Save profile
curl -X POST http://localhost:8000/api/memory/profile?user_email=user@example.com \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Doe",
    "department": "Sales",
    "role": "member"
  }'

# Get memory
curl http://localhost:8000/api/memory/user@example.com?memory_type=skill&limit=5

# Delete memory
curl -X DELETE http://localhost:8000/api/memory/1
```

---

## 🔧 Integration with Backend

### **Save Memory in Chat Handler**
```python
from memory_manager import UserMemoryManager
from models import MemoryType

# After user sends message
UserMemoryManager.save_chat_memory(
    db,
    user_email=email,
    message=user_message,
    context={
        "intent": detected_intent,
        "skills_mentioned": [skill.name for skill in found_skills],
        "timestamp": datetime.now().isoformat()
    }
)

# Track skill usage
UserMemoryManager.save_skill_memory(db, email, skill.id, skill.name)
```

---

## 📈 Advanced Usage

### **Get Recently Used Skills**
```python
from memory_manager import UserMemoryManager
from models import MemoryType

recent_skills = UserMemoryManager.get_recent_memory(
    db, user_email="user@example.com", memory_type=MemoryType.SKILL, limit=5
)

for memory in recent_skills:
    print(f"Skill: {memory.content['skill_name']}, Used: {memory.updated_at}")
```

### **Search in Memory**
```python
memories = db.query(UserMemory).filter(
    UserMemory.user_email == "user@example.com",
    UserMemory.memory_type == MemoryType.CUSTOM,
    UserMemory.content["tags"].contains(["important"]),
    UserMemory.is_active == True
).all()
```

---

## ⚠️ Notes

1. **Soft Delete**: Deleting memory sets `is_active=False`, not hard delete
2. **JSON Flexibility**: `content` field can store any JSON structure
3. **Query Limits**: Default limit is 10, can be customized per request
4. **Timestamp**: `created_at` and `updated_at` are auto-managed
5. **User Email**: Always required for all operations

---

## 🧪 Testing

### Check Memory in pgAdmin
1. Open pgAdmin
2. Database → hermes_db → Schemas → public → Tables → user_memory
3. View Data → First 100 Rows

### Check via SQL
```sql
-- View all memory
SELECT * FROM user_memory WHERE is_active = true;

-- View specific user
SELECT * FROM user_memory WHERE user_email = 'user@example.com';

-- View by type
SELECT * FROM user_memory WHERE memory_type = 'skill';

-- Count by type
SELECT memory_type, COUNT(*) FROM user_memory GROUP BY memory_type;
```

---

---

## 🔄 Memory Correction (ข้อมูลผิด ให้แก้ไข)

### **Use Case: User บอกว่าข้อมูลผิด**

**Scenario:**
```
AI: "You work in General department"
User: "No! I work in AI ENG"
→ System should learn the correction
```

---

### **Correct Profile**
```http
PUT /api/memory/correct-profile?user_email=user@example.com&reason=I%20work%20in%20AI%20ENG
Content-Type: application/json

{
  "full_name": "Narisara Pae",
  "department": "AI ENG",
  "role": "member"
}
```

**What happens:**
1. **UPDATE** existing record (ไม่สร้าง record ใหม่) - Clean data!
2. Update content ด้วยข้อมูลใหม่
3. Mark `corrected_by_user = true` and add timestamp
4. Only 1 record per user per memory type (ไม่มี data bloat)

### **Correct Skill**
```http
PUT /api/memory/correct-skill?user_email=user@example.com&reason=Wrong%20skill
Content-Type: application/json

{
  "skill_id": 2,
  "skill_name": "Annual Report Summarizer"
}
```

### **Correct Generic Memory**
```http
PUT /api/memory/correct-generic?user_email=user@example.com&memory_type=custom&reason=Update%20contact
Content-Type: application/json

{
  "memory_type": "custom",
  "content": {
    "email": "new-email@company.com"
  }
}
```

### **Get Active Memory (ข้อมูลล่าสุด)**
```http
GET /api/memory/active/user@example.com/profile
```

Returns the most recent active memory, which will be the corrected version.

---

### **Frontend Example**
```javascript
// User says "That's wrong, my department is AI ENG"
async function correctDepartment() {
  const response = await fetch(
    'http://localhost:8000/api/memory/correct-profile?user_email=user@email.com&reason=Actually%20in%20AI%20ENG',
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        full_name: 'Narisara',
        department: 'AI ENG',
        role: 'member'
      })
    }
  );
  const result = await response.json();
  console.log('Corrected:', result.content.department); // AI ENG
  console.log('Previous:', result.content.previous_data.department); // General
}
```

---

## 📋 API Summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/memory/save` | Generic memory save |
| POST | `/api/memory/profile` | Save profile memory |
| POST | `/api/memory/skill` | Save skill usage |
| POST | `/api/memory/chat` | Save chat context |
| POST | `/api/memory/custom` | Save custom notes |
| GET | `/api/memory/{user_email}` | Get user memory |
| GET | `/api/memory/active/{user_email}/{type}` | Get active (latest) memory |
| PUT | `/api/memory/correct-profile` | Correct profile info |
| PUT | `/api/memory/correct-skill` | Correct skill memory |
| PUT | `/api/memory/correct-generic` | Correct any memory type |
| DELETE | `/api/memory/{memory_id}` | Delete single memory |
| DELETE | `/api/memory/user/{user_email}` | Delete all user memory |

---

✅ **Complete Memory System Ready!** 🚀
- ✅ Save memory
- ✅ Retrieve memory
- ✅ Correct/update memory when user says "that's wrong"
- ✅ Track history of corrections
- ✅ Always use latest corrected data
