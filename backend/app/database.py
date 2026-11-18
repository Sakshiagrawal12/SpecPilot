
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


BASE_DIR = Path(__file__).resolve().parent.parent

# Use PostgreSQL when DATABASE_URL is configured.
# Otherwise, continue using SQLite locally.
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace(
            "postgres://",
            "postgresql://",
            1
        )

    connect_args = {"sslmode": "require"}

    print("Using PostgreSQL database")

else:
    DATABASE_PATH = BASE_DIR / "specpilot.db"
    DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

    connect_args = {
        "check_same_thread": False
    }

    print("Using local SQLite database:", DATABASE_PATH)


engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
