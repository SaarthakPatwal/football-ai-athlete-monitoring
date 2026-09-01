from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from database.models import Base


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "processed" / "football_ai.db"


def get_database_url() -> str:
    """Return a database URL that can later point at PostgreSQL."""
    return os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DATABASE_PATH.as_posix()}")


def get_engine(database_url: str | None = None) -> Engine:
    url = database_url or get_database_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args, future=True)


engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def init_db(target_engine: Engine | None = None) -> None:
    DEFAULT_DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    active_engine = target_engine or engine
    Base.metadata.create_all(bind=active_engine)
    _apply_lightweight_migrations(active_engine)


def _apply_lightweight_migrations(active_engine: Engine) -> None:
    """Keep the demo SQLite schema compatible as Phase 1 evolves."""
    inspector = inspect(active_engine)
    if "match_records" not in inspector.get_table_names():
        return
    match_columns = {column["name"] for column in inspector.get_columns("match_records")}
    if "result" not in match_columns:
        with active_engine.begin() as connection:
            connection.execute(text("ALTER TABLE match_records ADD COLUMN result VARCHAR(20) NOT NULL DEFAULT 'Not recorded'"))


@contextmanager
def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
