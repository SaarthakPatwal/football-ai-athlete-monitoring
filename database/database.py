from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.orm import sessionmaker
from database.models import Base

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "football_ml.db"


def get_database_url():
    # Separate from the legacy populated football_ai.db; no legacy data is migrated.
    return os.getenv("FOOTBALL_ML_DATABASE_URL", f"sqlite:///{DEFAULT_DATABASE_PATH.as_posix()}")


def get_engine(database_url=None):
    url = database_url or get_database_url()
    active = create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {})
    if url.startswith("sqlite"):
        @event.listens_for(active, "connect")
        def enable_foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
    return active


engine = get_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db(target_engine=None):
    active = target_engine or engine
    if active is engine:
        DEFAULT_DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    inspector = inspect(active)
    existing = set(inspector.get_table_names())
    for table in Base.metadata.sorted_tables:
        if table.name in existing:
            expected = set(table.columns.keys())
            actual = {column["name"] for column in inspector.get_columns(table.name)}
            if actual != expected:
                raise ValueError("Incompatible database schema. Use a fresh FOOTBALL_ML_DATABASE_URL.")
    if existing - set(Base.metadata.tables):
        raise ValueError("Legacy database detected. Use a fresh FOOTBALL_ML_DATABASE_URL.")
    Base.metadata.create_all(active)


@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
