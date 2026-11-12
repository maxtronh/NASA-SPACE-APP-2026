import os
import threading
from collections.abc import AsyncGenerator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models.base import Base

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None
_sync_engine: Engine | None = None
_active_tier: str | None = None
_db_initialized: bool = False
_init_lock = threading.Lock()


def _probe_postgres(url: str) -> bool:
    """Attempts a quick synchronous probe to test PostgreSQL connectivity."""
    sync_url = url
    if "postgresql+psycopg://" in sync_url:
        pass
    elif "postgresql://" in sync_url:
        sync_url = sync_url.replace("postgresql://", "postgresql+psycopg://")

    try:
        test_engine = create_engine(
            sync_url,
            connect_args={"connect_timeout": 1},
            pool_pre_ping=True,
        )
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        test_engine.dispose()
        return True
    except (SQLAlchemyError, OSError) as exc:
        logger.warning(f"PostgreSQL probe failed ({exc}). Falling back to SQLite.")
        return False


def _ensure_tables_and_seeds(sync_engine: Engine, tier: str):
    """Ensures tables and authentic NASA seed data exist synchronously."""
    global _db_initialized
    with _init_lock:
        if _db_initialized:
            return
        try:
            if tier == "postgresql":
                with sync_engine.connect() as conn:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                    conn.commit()

            Base.metadata.create_all(bind=sync_engine)

            if settings.ENABLE_AUTO_SEED:
                from backend.app.services.seed_data import seed_database_sync
                seed_database_sync(sync_engine)

            _db_initialized = True
            logger.info(f"Database ({tier}) tables and authentic seeds verified.")
        except (SQLAlchemyError, OSError) as exc:
            logger.error(f"Error during table creation/seeding: {exc}")


def get_db_engines() -> tuple[AsyncEngine, async_sessionmaker[AsyncSession], Engine, str]:
    """Initializes and returns dual-tier async engine, session factory, sync engine, and tier name."""
    global _engine, _session_factory, _sync_engine, _active_tier

    if _engine is not None and _session_factory is not None and _sync_engine is not None and _active_tier is not None:
        return _engine, _session_factory, _sync_engine, _active_tier

    target_url = settings.DATABASE_URL
    use_sqlite = os.getenv("USE_SQLITE", "").lower() in ("1", "true", "yes")

    if not use_sqlite and "postgres" in target_url and _probe_postgres(target_url):
        logger.info(f"Connecting to PostgreSQL database at {target_url.split('@')[-1]}")
        _active_tier = "postgresql"
        if not target_url.startswith("postgresql+psycopg://"):
            async_url = target_url.replace("postgresql://", "postgresql+psycopg://")
        else:
            async_url = target_url

        _engine = create_async_engine(
            async_url,
            pool_pre_ping=True,
            echo=False,
        )
        sync_url = async_url
        _sync_engine = create_engine(sync_url, pool_pre_ping=True)
    else:
        sqlite_async_url = settings.SQLITE_FALLBACK_URL
        sqlite_sync_url = settings.SQLITE_SYNC_URL
        logger.info(f"Using resilient SQLite fallback database at {sqlite_async_url}")
        _active_tier = "sqlite_fallback"
        _engine = create_async_engine(
            sqlite_async_url,
            connect_args={"check_same_thread": False},
            echo=False,
        )
        _sync_engine = create_engine(
            sqlite_sync_url,
            connect_args={"check_same_thread": False},
        )

    _session_factory = async_sessionmaker(
        bind=_engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    # Initialize tables and seed records immediately if not running in Alembic migration context
    if os.getenv("ALEMBIC_CONTEXT") != "1":
        _ensure_tables_and_seeds(_sync_engine, _active_tier)

    return _engine, _session_factory, _sync_engine, _active_tier


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for obtaining an asynchronous database session."""
    _, session_factory, _, _ = get_db_engines()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_engine() -> Engine:
    """Returns the synchronous engine for Alembic migrations and tooling."""
    _, _, sync_engine, _ = get_db_engines()
    return sync_engine


async def init_db():
    """Initializes database schema and extensions."""
    _, _, sync_engine, tier = get_db_engines()
    _ensure_tables_and_seeds(sync_engine, tier)


async def check_db_health() -> dict:
    """Checks database connectivity and pgvector readiness."""
    _, session_factory, _, tier = get_db_engines()
    try:
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "tier": tier,
            "pgvector_ready": True,
            "version": settings.VERSION,
        }
    except (SQLAlchemyError, OSError) as exc:
        logger.error(f"Database health check failed: {exc}")
        return {
            "status": "unhealthy",
            "database": f"error: {exc!s}",
            "tier": tier,
            "pgvector_ready": False,
            "version": settings.VERSION,
        }
