from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# สำหรับ PostgreSQL — echo ปิดเป็นดีฟอลต์ (log ทุก query ช้า+รก) เปิดได้ด้วย SQL_ECHO=1
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "0") in ("1", "true", "yes"),
    connect_args={} if "postgresql" in DATABASE_URL else {"check_same_thread": False},
    poolclass=None if "postgresql" in DATABASE_URL else StaticPool,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
