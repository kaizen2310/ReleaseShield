import os
import logging
import threading
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

logger = logging.getLogger(__name__)

db_uri = settings.SQLALCHEMY_DATABASE_URI
engine = None

def _try_pg_connect_with_timeout(uri, timeout_seconds=5):
    """
    Attempt a PostgreSQL connection with a hard wall-clock timeout.
    Uses a daemon thread so a hanging DNS call never blocks the main thread.
    Returns the engine on success, or raises on failure/timeout.
    """
    result = [None]
    error = [None]
    done_event = threading.Event()

    def _connect():
        try:
            e = create_engine(uri, connect_args={"connect_timeout": 3})
            with e.connect() as conn:
                pass
            result[0] = e
        except Exception as ex:
            error[0] = ex
        finally:
            done_event.set()

    t = threading.Thread(target=_connect, daemon=True)
    t.start()
    completed = done_event.wait(timeout=timeout_seconds)

    if not completed:
        raise Exception(f"DB connection timed out after {timeout_seconds}s (DNS/network unreachable)")
    if error[0]:
        raise error[0]
    return result[0]

# Attempt to connect to configured DB; gracefully fall back to local SQLite if unreachable
try:
    if "postgresql" in db_uri:
        engine = _try_pg_connect_with_timeout(db_uri, timeout_seconds=5)
        logger.info("Connected to primary PostgreSQL database.")
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
