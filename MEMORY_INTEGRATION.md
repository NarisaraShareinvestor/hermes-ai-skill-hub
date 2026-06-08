# 🧠 Memory System - Integration Guide

## How to Integrate Memory in Chat Flow

### **Real-World Example: Sales Team Chat**

```
User: สร้างรายงานการประชุมวันนี้ 3 คน
  ↓
AI checks memory:
  - Department: Sales ✓
  - Recent skills: Meeting Minutes Generator ✓
  - Chat context: Last 3 meetings
  ↓
AI generates report using context
  ↓
User: ไม่ใช่ฉันอยู่ AI ENG นะ
  ↓
AI corrects memory:
  - Old: Department = Sales
  - New: Department = AI ENG
  - Saves correction with reason
  ↓
Next time AI will know: User is in AI ENG
```

---

## 🔌 Code Integration Points

### **1. In Chat Handler (save chat context)**

```python
@app.post("/api/chat/send")
async def send_chat(
    user_email: str,
    message: str,
    db: Session = Depends(get_db)
):
    from memory_manager import UserMemoryManager
    from models import MemoryType
    
    # 1. Save chat to database
    chat_record = save_to_db(user_email, message)
    
    # 2. Detect intent from message
    intent = detect_intent(message)  # "report", "skill", "data", etc.
    
    # 3. Find relevant skills
    skills = find_relevant_skills(message, db)
    
    # 4. **Save to memory**: This message & context
    UserMemoryManager.save_chat_memory(
        db, user_email,
        message=message,
        context={
            "intent": intent,
            "skills_found": [s.name for s in skills],
            "timestamp": datetime.now().isoformat()
        }
    )
    
    # 5. Get active profile to use correct info
    profile_memory = UserMemoryManager.get_active_memory(
        db, user_email, MemoryType.PROFILE
    )
    
    # 6. Generate response using memory
    response = generate_response(
        message=message,
        user_profile=profile_memory.content if profile_memory else {},
        skills=skills
    )
    
    return {"message": response}
```

---

### **2. In User Profile Update (when user corrects)**

```python
@app.post("/api/chat/correct")
async def handle_correction(
    user_email: str,
    correction_type: str,  # "department", "skill", "name", etc.
    new_data: dict,
    reason: str,
    db: Session = Depends(get_db)
):
    from memory_manager import UserMemoryManager
    
    if correction_type == "department":
        # User said: "ไม่ใช่ ฉันอยู่ AI ENG นะ"
        UserMemoryManager.correct_profile(
            db, user_email,
            full_name=new_data.get("full_name"),
            department=new_data.get("department"),
            role=new_data.get("role"),
            reason=reason
        )
        return {"status": "correction_saved", "new_department": new_data["department"]}
    
    elif correction_type == "skill":
        # User said: "ไม่ใช่ Skill ดังกล่าวนะ"
        UserMemoryManager.correct_skill(
            db, user_email,
            skill_id=new_data["skill_id"],
            skill_name=new_data["skill_name"],
            reason=reason
        )
        return {"status": "skill_corrected"}
```

---

### **3. Detect User Correction in Chat**

```python
def detect_correction(message: str) -> bool:
    """Detect if user is correcting the AI"""
    corrections = [
        "ไม่ใช่",  # Not correct
        "ผิดแล้ว",  # Wrong
        "แก้ให้หน่อย",  # Fix it
        "ข้อมูลไม่ถูก",  # Data is wrong
        "อยู่ใน",  # I'm in (department)
        "ทำงาน",  # I work (in/as)
        "ชื่อของฉัน",  # My name is
        "actually",
        "it's",
        "I'm in"
    ]
    
    return any(keyword in message.lower() for keyword in corrections)


@app.post("/api/chat/send")
async def send_chat(user_email: str, message: str, db: Session = Depends(get_db)):
    # Check if user is correcting
    if detect_correction(message):
        # Extract correction
        correction_data = extract_correction(message)  # NLP extraction
        
        # Save correction
        await handle_correction(
            user_email,
            correction_data["type"],  # "department", "skill", etc.
            correction_data["new_value"],
            reason=message
        )
        
        return {
            "message": f"ขอบคุณ! ฉันจำไว้แล้วว่าคุณ {correction_data['summary']}"
        }
```

---

### **4. NLP Extraction (Extract correction details)**

```python
def extract_correction(message: str) -> dict:
    """Extract correction details from user message"""
    import re
    
    # Example: "ไม่ใช่ ฉันอยู่ AI ENG"
    # Extract: department = "AI ENG"
    
    # Simple regex patterns
    if re.search(r'อยู่\s*(\w+)', message):
        dept = re.search(r'อยู่\s*(\w+)', message).group(1)
        return {
            "type": "department",
            "new_value": {"department": dept},
            "summary": f"อยู่แผนก {dept}"
        }
    
    # Pattern: "ชื่อของฉันคือ [name]"
    if re.search(r'ชื่อ.*?คือ\s*(\w+)', message):
        name = re.search(r'ชื่อ.*?คือ\s*(\w+)', message).group(1)
        return {
            "type": "name",
            "new_value": {"full_name": name},
            "summary": f"ชื่อคุณคือ {name}"
        }
    
    return {"type": "generic", "new_value": {}}
```

---

### **5. Use Memory in Response Generation**

```python
def generate_response(
    message: str,
    user_profile: dict,
    skills: list,
    db: Session
) -> str:
    """Generate AI response using memory"""
    
    # Get user info from memory
    name = user_profile.get("full_name", "User")
    dept = user_profile.get("department", "Unknown")
    
    # Get recent skills from memory
    recent_skills_ids = [s["skill_id"] for s in recent_skills]
    
    # Build context for AI
    context = f"""
    User Info:
    - Name: {name}
    - Department: {dept}
    - Recently used: {', '.join([s['skill_name'] for s in recent_skills])}
    
    User Message: {message}
    
    Generate response using this context...
    """
    
    # Call Claude or LLM
    response = call_llm(context)
    return response
```

---

## 📊 Memory Usage in Different Scenarios

### **Scenario 1: Generate Report**

```
User: "สร้างรายงานการประชุม"
       ↓
Memory check:
  - Name: Narisara → Greeting
  - Dept: AI ENG → Use AI context
  - Last skill: Meeting Minutes Generator → Suggest this
  ↓
AI: "สวัสดี Narisara! ท่านจากแผนก AI ENG ใช่ไหม? 
      ฉันจะสร้างรายงานด้วย Meeting Minutes Generator..."
```

### **Scenario 2: Skill Recommendation**

```
Memory has:
  - Recent skills used: [Skill A, Skill B, Skill C]
  - Chat context: Last messages about "sales report"
  ↓
When user asks for help:
  - Recommend Skill A (most recent)
  - Or suggest Skill related to "sales"
```

### **Scenario 3: User Correction**

```
AI: "You work in General"
User: "ไม่ ฉันอยู่ AI ENG"
       ↓
System:
  1. Detect correction
  2. Update memory
  3. Save previous value
  4. Next time use AI ENG
```

---

## 🔍 Query Examples

### **Get User's Active Profile**

```python
from memory_manager import UserMemoryManager
from models import MemoryType

user_email = "user@example.com"
profile = UserMemoryManager.get_active_memory(
    db, user_email, MemoryType.PROFILE
)

if profile:
    print(f"Name: {profile.content['full_name']}")
    print(f"Dept: {profile.content['department']}")
    print(f"Was corrected: {profile.content.get('corrected_by_user', False)}")
```

### **Get Recent Skill Usage**

```python
recent_skills = UserMemoryManager.get_recent_memory(
    db, user_email, MemoryType.SKILL, limit=5
)

skills_list = [mem.content['skill_name'] for mem in recent_skills]
print(f"Recently used: {skills_list}")
```

### **Get All Corrections Made by User**

```python
from models import UserMemory, MemoryType

corrections = db.query(UserMemory).filter(
    UserMemory.user_email == user_email,
    UserMemory.content["corrected_by_user"].astext.cast(Boolean) == True
).all()

for correction in corrections:
    print(f"Type: {correction.memory_type}")
    print(f"Reason: {correction.content.get('correction_reason')}")
    print(f"Before: {correction.content.get('previous_data')}")
    print(f"After: {correction.content}")
```

---

## 🎯 Implementation Checklist

- [ ] Integrate `UserMemoryManager` in chat handler
- [ ] Add correction detection in message processing
- [ ] Implement `get_active_memory()` in response generation
- [ ] Add correction endpoints to chat flow
- [ ] Test with real user scenarios
- [ ] Monitor memory usage growth
- [ ] Add memory cleanup for old inactive records (optional)

---

## ⚠️ Best Practices

1. **Always use `get_active_memory()`** - Returns the latest non-deleted memory
2. **Save context for every message** - Helps with future understanding
3. **Track corrections** - `corrected_by_user` flag helps identify user feedback
4. **Keep previous data** - Useful for audit trail and debugging
5. **Soft delete only** - Never hard delete, keep history with `is_active=False`

---

## 🚀 Example Flow

```python
# Complete chat handler with memory
@app.post("/api/chat/message")
async def chat(
    user_email: str,
    message: str,
    db: Session = Depends(get_db)
):
    # 1. Save message to memory
    UserMemoryManager.save_chat_memory(
        db, user_email, message, 
        {"timestamp": datetime.now().isoformat()}
    )
    
    # 2. Check if correction
    if detect_correction(message):
        correction = extract_correction(message)
        UserMemoryManager.correct_profile(
            db, user_email, **correction
        )
        return {"message": "Correction saved!"}
    
    # 3. Get user info from memory
    profile = UserMemoryManager.get_active_memory(
        db, user_email, MemoryType.PROFILE
    )
    
    # 4. Generate response
    response = generate_ai_response(
        message, profile.content if profile else {}
    )
    
    return {"message": response}
```

---

✅ **Ready to integrate!** Follow the patterns above to fully utilize the memory system.
