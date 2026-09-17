import logging
import socket
from urllib.parse import urlparse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


def is_postgres_available(url: str) -> bool:
    try:
        parsed = urlparse(url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 5432
        with socket.create_connection((host, port), timeout=0.8):
            return True
    except Exception:
        return False


def init_engine():
    target_url = settings.DATABASE_URL
    if "postgresql" in target_url:
        if is_postgres_available(target_url):
            try:
                engine = create_engine(
                    target_url,
                    pool_pre_ping=True,
                )
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                logger.info("Successfully connected to PostgreSQL at %s", target_url.split("@")[-1])
                return engine
            except Exception as e:
                logger.warning("PostgreSQL connection failed: %s. Falling back to SQLite.", e)
        else:
            logger.info("PostgreSQL is not listening at target host/port. Using local SQLite database.")
        
        return create_engine(
            settings.SQLITE_FALLBACK_URL,
            connect_args={"check_same_thread": False},
        )
    else:
        return create_engine(
            target_url,
            connect_args={"check_same_thread": False} if "sqlite" in target_url else {},
        )


engine = init_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
