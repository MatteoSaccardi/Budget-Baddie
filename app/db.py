from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import os

DB_PATH = os.getenv("BUDGET_DB", os.path.join(os.path.dirname(__file__), "..", "Data","budget.sqlite"))
DB_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))

def get_session():
    return SessionLocal()

