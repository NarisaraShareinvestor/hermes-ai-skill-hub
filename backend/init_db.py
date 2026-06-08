#!/usr/bin/env python3
"""
Database initialization script
รัน: python backend/init_db.py
"""

import sys
import os
from dotenv import load_dotenv
from database import engine, Base
from models import Skill, SkillInstallation, AuditLog, ApprovalQueue, UserMemory, SkillStatus, SkillVisibility

load_dotenv()

def init_database():
    """สร้าง tables ทั้งหมด"""
    print("📝 Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def add_sample_skills():
    """เพิ่มตัวอย่าง Skill"""
    from sqlalchemy.orm import sessionmaker

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # ตรวจสอบว่ามี skill อยู่แล้วหรือไม่
        existing = db.query(Skill).count()
        if existing > 0:
            print(f"⚠️  Database already has {existing} skills, skipping sample data")
            return

        sample_skills = [
            {
                "name": "Annual Report Summarizer",
                "description": "สรุป Annual Report อัตโนมัติให้เป็นภาษาที่นักลงทุนเข้าใจ",
                "owner": "ir_team@example.com",
                "department": "ir",
                "skill_type": "summarizer",
                "tags": ["ir", "financial", "annual-report"],
                "status": SkillStatus.TEAM_AVAILABLE,
                "visibility": SkillVisibility.TEAM,
                "uses_claude": True,
                "claude_model": "claude-3-5-sonnet-20241022"
            },
            {
                "name": "Code Review Assistant",
                "description": "ตรวจสอบ code และให้ feedback ด้านความปลอดภัย, performance, clean code",
                "owner": "dev_team@example.com",
                "department": "dev",
                "skill_type": "reviewer",
                "tags": ["dev", "code-review", "quality"],
                "status": SkillStatus.TEAM_AVAILABLE,
                "visibility": SkillVisibility.TEAM,
                "uses_claude": True,
                "claude_model": "claude-3-5-sonnet-20241022"
            },
            {
                "name": "IR Website Copy Reviewer",
                "description": "ตรวจเนื้อหาหน้าเว็บไซต์ IR ให้เป็นภาษาอังกฤษมืออาชีพ",
                "owner": "content_team@example.com",
                "department": "content",
                "skill_type": "reviewer",
                "tags": ["content", "ir", "english"],
                "status": SkillStatus.PRIVATE,
                "visibility": SkillVisibility.PRIVATE,
                "uses_claude": True,
                "claude_model": "claude-3-5-sonnet-20241022"
            },
            {
                "name": "Meeting Minutes Generator",
                "description": "สร้างรายงานการประชุมจากบันทึกเสียง หรือตัวอักษร",
                "owner": "sales_team@example.com",
                "department": "sales",
                "skill_type": "generator",
                "tags": ["sales", "meeting", "minutes"],
                "status": SkillStatus.DRAFT,
                "visibility": SkillVisibility.PRIVATE,
                "uses_claude": True,
                "claude_model": "claude-3-5-sonnet-20241022"
            }
        ]

        print(f"📚 Adding {len(sample_skills)} sample skills...")
        for skill_data in sample_skills:
            skill = Skill(**skill_data)
            db.add(skill)

        db.commit()
        print(f"✅ Added {len(sample_skills)} sample skills!")

    except Exception as e:
        print(f"❌ Error adding sample skills: {e}")
        db.rollback()
    finally:
        db.close()

def print_summary():
    """แสดงสรุปข้อมูล"""
    from sqlalchemy import text
    from sqlalchemy.orm import sessionmaker

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        skills_count = db.query(Skill).count()

        print("\n" + "=" * 50)
        print("📊 Database Summary")
        print("=" * 50)
        print(f"✅ Total Skills: {skills_count}")

        if skills_count > 0:
            skills = db.query(Skill).limit(5).all()
            print("\nRecent Skills:")
            for skill in skills:
                print(f"  - {skill.name} ({skill.status.value})")

        print("\n✅ Database is ready!")
        print("\nNext steps:")
        print("  1. Start Backend: python -m uvicorn backend.main:app --reload")
        print("  2. Start Frontend: python -m http.server 8080")
        print("  3. Open http://localhost:8080 in your browser")

    except Exception as e:
        print(f"Error getting summary: {e}")
    finally:
        db.close()

def main():
    """Main function"""
    print("\n" + "=" * 50)
    print("🚀 Hermes AI Skill Hub - Database Initialization")
    print("=" * 50 + "\n")

    # ตรวจสอบ DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not set in .env file")
        print("Please create .env with: DATABASE_URL=postgresql://user:password@localhost:5432/hermes_db")
        sys.exit(1)

    print(f"📍 Database: {database_url.split('@')[1] if '@' in database_url else 'unknown'}")

    # สร้าง tables
    if not init_database():
        sys.exit(1)

    # เพิ่ม sample data
    add_sample_skills()

    # แสดงสรุป
    print_summary()

if __name__ == "__main__":
    main()
