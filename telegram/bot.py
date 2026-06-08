import os
import requests
import json
from dotenv import load_dotenv
from typing import Optional, Dict, Any

load_dotenv()

class TelegramBot:
    """
    Telegram Bot สำหรับ Approval และแจ้งเตือน
    """

    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.channel_id = os.getenv("TELEGRAM_CHANNEL_ID")
        self.api_base = "https://api.telegram.org"

    def is_configured(self) -> bool:
        """ตรวจสอบว่า Telegram ได้รับการตั้งค่าหรือไม่"""
        return bool(self.token and self.channel_id)

    def send_message(self, text: str, chat_id: Optional[str] = None) -> Optional[Dict]:
        """ส่งข้อความตรงไป Telegram"""
        if not self.is_configured():
            print("⚠️  Telegram ยังไม่ได้ตั้งค่า ข้อความจะไม่ส่ง")
            print(f"ข้อความ: {text}")
            return None

        target_chat = chat_id or self.channel_id
        url = f"{self.api_base}/bot{self.token}/sendMessage"

        data = {
            "chat_id": target_chat,
            "text": text,
            "parse_mode": "HTML"
        }

        try:
            response = requests.post(url, json=data, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error sending message: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Exception: {e}")
            return None

    def send_skill_review_notification(self, skill_data: Dict[str, Any]) -> Optional[Dict]:
        """
        ส่ง notification เมื่อมี Skill ใหม่ต้อง review
        """
        if not self.is_configured():
            return None

        skill_id = skill_data.get("id", "N/A")
        skill_name = skill_data.get("name", "Unknown")
        owner = skill_data.get("owner", "Unknown")
        description = skill_data.get("description", "No description")

        message = f"""
🧠 <b>New Skill Submitted for Review</b>

<b>Skill Name:</b> {skill_name}
<b>Skill ID:</b> {skill_id}
<b>Owner:</b> {owner}
<b>Description:</b> {description[:200]}...

<b>Choose Action:</b>
/approve_{skill_id} - Approve to Team
/reject_{skill_id} - Reject
/edit_{skill_id} - Request Edit
        """

        return self.send_message(message)

    def send_approval_notification(
        self,
        skill_id: int,
        skill_name: str,
        approval_type: str,
        details: str
    ) -> Optional[Dict]:
        """
        ส่ง notification ว่า Skill ถูกอนุมัติ
        approval_type: "team" หรือ "company"
        """
        if not self.is_configured():
            return None

        icon = "✅" if approval_type == "team" else "🎉"
        message = f"""
{icon} <b>Skill Approved</b>

<b>Skill:</b> {skill_name} (ID: {skill_id})
<b>Level:</b> {approval_type.title()}
<b>Details:</b> {details}

The skill is now available in the library!
        """

        return self.send_message(message)

    def send_rejection_notification(
        self,
        skill_id: int,
        skill_name: str,
        reason: str
    ) -> Optional[Dict]:
        """ส่ง notification เมื่อ Skill ถูกปฏิเสธ"""
        if not self.is_configured():
            return None

        message = f"""
❌ <b>Skill Rejected</b>

<b>Skill:</b> {skill_name} (ID: {skill_id})
<b>Reason:</b> {reason}

Please review and make improvements.
        """

        return self.send_message(message)

    def send_daily_summary(self, summary_data: Dict[str, Any]) -> Optional[Dict]:
        """ส่ง daily summary report"""
        if not self.is_configured():
            return None

        total_skills = summary_data.get("total_skills", 0)
        active_users = summary_data.get("active_users", 0)
        top_skills = summary_data.get("top_skills", [])
        failed_tasks = summary_data.get("failed_tasks", 0)

        message = f"""
📊 <b>Daily AI Skills Summary</b>

<b>Total Skills:</b> {total_skills}
<b>Active Users Today:</b> {active_users}
<b>Failed Tasks:</b> {failed_tasks}

<b>Top Skills Used:</b>
"""
        for i, skill in enumerate(top_skills[:3], 1):
            message += f"{i}. {skill.get('name')} ({skill.get('usage_count')} uses)\n"

        return self.send_message(message)

    def send_alert(self, alert_type: str, message_text: str) -> Optional[Dict]:
        """ส่ง alert/warning message"""
        if not self.is_configured():
            return None

        icons = {
            "error": "⚠️",
            "warning": "🚨",
            "info": "ℹ️",
            "success": "✅"
        }

        icon = icons.get(alert_type, "📢")
        message = f"{icon} <b>{alert_type.upper()}</b>\n\n{message_text}"

        return self.send_message(message)

    def handle_webhook(self, webhook_data: Dict) -> Optional[str]:
        """
        จัดการ webhook จาก Telegram
        (สำหรับเมื่อ user กด button)
        """
        try:
            message = webhook_data.get("message", {})
            callback_query = webhook_data.get("callback_query", {})

            # Handle message
            if message:
                text = message.get("text", "")
                chat_id = message.get("chat", {}).get("id")
                # ประมวลผลข้อมูล
                return f"Received: {text}"

            # Handle button click (callback_query)
            if callback_query:
                data = callback_query.get("data", "")
                # ประมวลผล action เช่น approve, reject
                if data.startswith("approve_"):
                    skill_id = data.split("_")[1]
                    return f"Approving skill {skill_id}"
                elif data.startswith("reject_"):
                    skill_id = data.split("_")[1]
                    return f"Rejecting skill {skill_id}"

        except Exception as e:
            print(f"Error handling webhook: {e}")
            return None

        return None


if __name__ == "__main__":
    bot = TelegramBot()

    # Test 1: Check configuration
    print("=" * 50)
    print("Test 1: Check Telegram Configuration")
    print("=" * 50)
    if bot.is_configured():
        print("✅ Telegram is configured")
    else:
        print("⚠️  Telegram is not configured (using mock)")

    # Test 2: Send test message
    print("\n" + "=" * 50)
    print("Test 2: Send Test Message")
    print("=" * 50)
    result = bot.send_message("🧪 Test message from Hermes AI Skill Hub")
    if result:
        print(f"✅ Message sent: {result.get('result', {}).get('message_id')}")
    else:
        print("Message not sent (mock mode)")

    # Test 3: Send skill review notification
    print("\n" + "=" * 50)
    print("Test 3: Send Skill Review Notification")
    print("=" * 50)
    skill_data = {
        "id": 1,
        "name": "Annual Report Summarizer",
        "owner": "john@example.com",
        "description": "สรุม Annual Report อัตโนมัติ"
    }
    bot.send_skill_review_notification(skill_data)
    print("Notification sent")

    # Test 4: Send approval notification
    print("\n" + "=" * 50)
    print("Test 4: Send Approval Notification")
    print("=" * 50)
    bot.send_approval_notification(1, "Annual Report Summarizer", "team", "Skill works well")
    print("Approval notification sent")

    # Test 5: Send daily summary
    print("\n" + "=" * 50)
    print("Test 5: Send Daily Summary")
    print("=" * 50)
    summary = {
        "total_skills": 15,
        "active_users": 42,
        "top_skills": [
            {"name": "Annual Report Summarizer", "usage_count": 28},
            {"name": "Code Review Assistant", "usage_count": 15},
            {"name": "Meeting Summarizer", "usage_count": 12}
        ],
        "failed_tasks": 2
    }
    bot.send_daily_summary(summary)
    print("Summary sent")
