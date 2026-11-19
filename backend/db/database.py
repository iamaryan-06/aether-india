"""
database.py — SQLAlchemy engine, session factory, and base class.

Usage:
    from db.database import get_db, engine, Base
    # In FastAPI dependency:
    #   db: Session = Depends(get_db)
"""
from __future__ import annotations

import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv()

# ── Database URL ──────────────────────────────────────────────────────────────
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./aether_store.db")

# ── SQLite-specific: enable WAL mode and foreign-key enforcement ──────────────
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )

    @event.listens_for(Engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record) -> None:  # type: ignore[type-arg]
        """Enable WAL journal mode and foreign-key support on every new connection."""
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

else:
    engine = create_engine(DATABASE_URL, echo=False)

# ── Session factory ───────────────────────────────────────────────────────────
SessionLocal: sessionmaker[Session] = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ── Declarative base ──────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Shared declarative base for all SQLAlchemy models."""
    pass


# ── FastAPI dependency ────────────────────────────────────────────────────────
def get_db() -> Generator[Session, None, None]:
    """
    Yield a database session for the duration of a single request,
    ensuring the session is properly closed afterwards.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables if they do not yet exist. Called on application startup."""
    # Import all models here so that Base.metadata is populated before create_all.
    from db import models  # noqa: F401  (side-effect import)

    Base.metadata.create_all(bind=engine)
