"""SQLAlchemy 2.0 engine and session helpers with SQLite WAL and read-only modes."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from resumeforge.config import get_database_url, sqlite_path_from_url


def _configure_sqlite_rw(dbapi_connection: Any, _connection_record: Any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("PRAGMA journal_mode = WAL;")
    cursor.execute("PRAGMA synchronous = NORMAL;")
    cursor.execute("PRAGMA busy_timeout = 5000;")
    cursor.close()


def _configure_sqlite_ro(dbapi_connection: Any, _connection_record: Any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("PRAGMA query_only = ON;")
    cursor.execute("PRAGMA busy_timeout = 5000;")
    cursor.close()


def get_engine(
    db_url_or_path: Path | str | None = None,
    *,
    read_only: bool = False,
    echo: bool = False,
) -> Engine:
    """Create a SQLAlchemy Engine.

    When `read_only=True` on SQLite:
    - Opens via SQLite URI `mode=ro` (never creates missing files; OS-enforced read-only)
    - Executes `PRAGMA query_only = ON;` on every DBAPI connection
    """
    url = get_database_url(db_url_or_path)
    sqlite_path = sqlite_path_from_url(url)

    if sqlite_path is not None:
        if read_only:
            resolved = sqlite_path.resolve()
            if not resolved.exists():
                raise FileNotFoundError(
                    f"Database not found at {resolved}. Run `resumeforge db init` first."
                )
            ro_uri = f"{resolved.as_uri()}?mode=ro"
            engine = create_engine(
                "sqlite://",
                creator=lambda: sqlite3.connect(ro_uri, uri=True, check_same_thread=False),
                echo=echo,
                future=True,
            )
            event.listen(engine, "connect", _configure_sqlite_ro)
            return engine

        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            echo=echo,
            future=True,
        )
        event.listen(engine, "connect", _configure_sqlite_rw)
        return engine

    if url.startswith("sqlite://"):
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            echo=echo,
            future=True,
        )
        event.listen(
            engine,
            "connect",
            _configure_sqlite_ro if read_only else _configure_sqlite_rw,
        )
        return engine

    connect_args: dict[str, Any] = {}
    if read_only and url.startswith("postgresql"):
        connect_args["options"] = "-c default_transaction_read_only=on"

    return create_engine(url, connect_args=connect_args, echo=echo, future=True)


def create_session_factory(
    db_url_or_path: Path | str | None = None,
    *,
    read_only: bool = False,
) -> sessionmaker[Session]:
    """Return a configured SQLAlchemy sessionmaker."""
    engine = get_engine(db_url_or_path, read_only=read_only)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@contextmanager
def session_scope(
    db_url_or_path: Path | str | None = None,
    *,
    read_only: bool = False,
) -> Iterator[Session]:
    """Transactional session context manager (rolls back on exception or read-only mode)."""
    engine = get_engine(db_url_or_path, read_only=read_only)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = factory()
    try:
        yield session
        if not read_only:
            session.commit()
        else:
            session.rollback()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()
