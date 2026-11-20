import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

logger = logging.getLogger(__name__)

db_uri = settings.SQLALCHEMY_DATABASE_URI
engine = None

# Attempt to connect to configured DB; gracefully fall back to local SQLite if unreachable
try:
    if "postgresql" in db_uri:
        temp_engine = create_engine(db_uri, connect_args={"connect_timeout": 3})
        with temp_engine.connect() as conn:
            pass
        engine = temp_engine
    else:
        engine = create_engine(db_uri)
except Exception as e:
    logger.warning(f"Could not connect to primary database ({e}). Falling back to local SQLite database.")
    sqlite_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "releaseshield.db")
    engine = create_engine(f"sqlite:///{sqlite_path}", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
