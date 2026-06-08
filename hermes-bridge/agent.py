import json
import os
from anthropic import Anthropic
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class HermesAgent:
    """
    Hermes Agent - AI ตัวกลางที่ใช้ Claude API
    ทำหน้าที่:
    1. เข้าใจคำสั่งของผู้ใช้
    2. เลือก Skill ที่เหมาะ
    3. ประมวลผลคำสั่ง
    4. ตรวจสอบ permission
    """

    def __init__(self):
        self.client = Anthropic()
        self.model = "claude-3-5-sonnet-20241022"
        self.conversation_history = []
        self.api_base = os.getenv("BACKEND_URL", "http://localhost:8000")

    def system_prompt(self) -> str:
        """ระบบ Prompt สำหรับ Hermes Agent"""
        return """คุณคือ Hermes Agent - ผู้ช่วย AI สำหรับการจัดการ Skill และประมวลผลงาน

ทำหน้าที่หลัก:
1. เข้าใจว่าผู้ใช้ต้องการอะไร (Intent)
2. เลือก Skill ที่เหมาะจากระบบ
3. ตรวจสอบ permission และ risk level
4. ประมวลผลข้อมูล และให้ผลลัพธ์
5. บันทึก usage log และ feedback

ความสามารถ:
- สามารถใช้งาน Skill ที่มีอยู่
- สามารถเสนอสร้าง Skill ใหม่
- สามารถบันทึก Skill เข้า Skill Registry
- สามารถแชร์ Skill ให้ทีม
- สามารถดูสถิติการใช้งาน

กฎสำคัญ:
- ต้องเคารพ Permission ของผู้ใช้ ห้าม access Skill ที่ไม่มีสิทธิ์
- ห้าม delete หรือแก้ไข Skill โดยไม่ได้รับอนุญาต
- ถ้า Skill ที่ต้องใช้มีความเสี่ยงสูง ให้ขออนุมัติจาก Admin
- ทำงานแบบ transparent ให้ผู้ใช้เข้าใจว่ากำลังทำอะไร
- ตัดสินใจฉลาดเลือก Skill ที่ปลอดภัยและมีประสิทธิภาพสูง"""

    def chat(self, user_message: str, user_context: Optional[Dict[str, Any]] = None) -> str:
        """
        คุยกับ Agent แบบ Conversation
        user_context: ข้อมูล user เช่น email, department, permissions
        """
        if user_context is None:
            user_context = {}

        # เพิ่ม context ลงในข้อความ
        context_str = f"ผู้ใช้: {user_context.get('email', 'unknown')}\nแผนก: {user_context.get('department', 'unknown')}\n\n"
        full_message = context_str + user_message

        # เพิ่มข้อความเข้า conversation history
        self.conversation_history.append({
            "role": "user",
            "content": full_message
        })

        # เรียก Claude API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=self.system_prompt(),
            messages=self.conversation_history
        )

        assistant_message = response.content[0].text

        # เพิ่มตอบกลับเข้า history
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        return assistant_message

    def select_skill(self, user_intent: str, available_skills: List[Dict]) -> Optional[Dict]:
        """
        เลือก Skill ที่เหมาะกับ intent ของผู้ใช้
        """
        prompt = f"""
จากรายชื่อ Skill ต่อไปนี้ เลือก 1-3 skill ที่เหมาะที่สุดกับ intent นี้:
Intent: {user_intent}

Available Skills:
{json.dumps(available_skills, ensure_ascii=False, indent=2)}

ตอบให้ว่า:
1. Skill ที่เลือก (ชื่อ + ID)
2. เหตุผลที่เลือก
3. ความมั่นใจ (0-100%)

Respond ในรูปแบบ JSON"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        try:
            # ลองแปลง response เป็น JSON
            response_text = response.content[0].text
            # ลองหา JSON block
            if "{" in response_text:
                json_str = response_text[response_text.find("{"):response_text.rfind("}")+1]
                return json.loads(json_str)
        except:
            pass

        return None

    def generate_skill_prompt(self, skill_description: str) -> str:
        """
        สร้าง System Prompt สำหรับ Skill ใหม่
        """
        prompt = f"""
สร้าง System Prompt ที่ดีสำหรับ Skill นี้:
รายละเอียด Skill: {skill_description}

Prompt ควร:
1. ชัดเจนว่า skill ทำอะไร
2. บอก input/output format
3. ให้ instructions ละเอียด
4. ระบุข้อจำกัดและเตือนภัย

Respond ให้ prompt เต็ม พร้อมใช้ได้เลย"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        return response.content[0].text

    def check_permission(self, user_email: str, skill_id: int) -> Dict[str, Any]:
        """
        ตรวจสอบว่า user มีสิทธิ์ใช้ skill นี้หรือไม่
        (ในรุ่นจริง ควรเรียก Backend API)
        """
        return {
            "can_use": True,
            "can_edit": False,
            "can_share": False,
            "risk_level": "low"
        }

    def analyze_feedback(self, skill_id: int, feedback: str) -> Dict[str, Any]:
        """
        วิเคราะห์ feedback จากผู้ใช้
        """
        prompt = f"""
วิเคราะห์ feedback นี้:
{feedback}

ให้:
1. ความหมาย (positive/negative/neutral)
2. ประเด็นหลัก
3. แนะนำปรับปรุง

Respond ในรูปแบบ JSON"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        try:
            response_text = response.content[0].text
            if "{" in response_text:
                json_str = response_text[response_text.find("{"):response_text.rfind("}")+1]
                return json.loads(json_str)
        except:
            return {"sentiment": "neutral", "feedback": feedback}

        return {}

    def clear_history(self):
        """ล้าง conversation history"""
        self.conversation_history = []

    def get_history(self) -> List[Dict]:
        """ดู conversation history"""
        return self.conversation_history


if __name__ == "__main__":
    # ตัวอย่างการใช้
    agent = HermesAgent()

    # Test 1: Chat กับ Agent
    print("=" * 50)
    print("Test 1: Chat with Agent")
    print("=" * 50)
    response = agent.chat(
        "ต้องการสรุป Annual Report",
        user_context={
            "email": "john@example.com",
            "department": "ir_team"
        }
    )
    print(f"Agent: {response}\n")

    # Test 2: เลือก Skill
    print("=" * 50)
    print("Test 2: Select Skill")
    print("=" * 50)
    available_skills = [
        {"id": 1, "name": "Annual Report Summarizer", "department": "ir"},
        {"id": 2, "name": "Financial Highlight Extractor", "department": "ir"},
        {"id": 3, "name": "Dividend Policy Finder", "department": "ir"},
    ]
    selected = agent.select_skill("สรุป Annual Report", available_skills)
    if selected:
        print(f"Selected: {json.dumps(selected, ensure_ascii=False, indent=2)}\n")

    # Test 3: สร้าง Prompt สำหรับ Skill
    print("=" * 50)
    print("Test 3: Generate Skill Prompt")
    print("=" * 50)
    skill_description = "Skill สำหรับสรุป Annual Report ให้ง่ายเข้าใจสำหรับนักลงทุน"
    generated_prompt = agent.generate_skill_prompt(skill_description)
    print(f"Generated Prompt:\n{generated_prompt}\n")
