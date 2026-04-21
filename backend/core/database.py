"""Database initialization and session management."""
import structlog
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.core.config import get_settings

settings = get_settings()
logger = structlog.get_logger(__name__)

Base = declarative_base()
_engine = None
_async_session = None


async def init_db():
    global _engine, _async_session
    try:
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            pool_pre_ping=True,
        )
        _async_session = sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
        logger.info("Database initialized")
    except Exception as e:
        logger.warning("Database not available – running in stateless mode", error=str(e))


def get_session():
    if _async_session:
        return _async_session()
    raise RuntimeError("Database not initialized")
