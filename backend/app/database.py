from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path


# =========================================================
# DATABASE PATH
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_PATH = BASE_DIR / "specpilot.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


print("====================================")
print("DATABASE CONFIGURATION")
print("====================================")
print("Database path:")
print(DATABASE_PATH)
print("====================================")


# =========================================================
# DATABASE ENGINE
# =========================================================

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False
    }
)


# =========================================================
# SESSION
# =========================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# =========================================================
# BASE
# =========================================================

Base = declarative_base()


# =========================================================
# DATABASE DEPENDENCY
# =========================================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
        