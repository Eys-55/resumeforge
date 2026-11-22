"""Central path and database URL configuration for ResumeForge."""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
DATA_DIR = REPO_ROOT / "data"
DEFAULT_DB_PATH = DATA_DIR / "resumes.db"
ALEMBIC_INI_PATH = REPO_ROOT / "alembic.ini"
MIGRATIONS_DIR = REPO_ROOT / "migrations"


def get_database_url(db_url_or_path: Path | str | None = None) -> str:
    """Resolve the active SQLAlchemy database URL.

    Priority:
    1. Explicit `db_url_or_path` argument (Path or URL string)
    2. `RESUMEFORGE_DATABASE_URL` environment variable
    3. `RESUMEFORGE_DB_PATH` environment variable
    4. Default local SQLite database at `data/resumes.db`
    """
    if db_url_or_path is not None:
        raw = str(db_url_or_path).strip()
        if "://" in raw:
            return raw
        resolved = Path(raw).expanduser().resolve()
        return f"sqlite:///{resolved.as_posix()}"

    env_url = os.environ.get("RESUMEFORGE_DATABASE_URL", "").strip()
    if env_url:
        return env_url

    env_path = os.environ.get("RESUMEFORGE_DB_PATH", "").strip()
    if env_path:
        resolved = Path(env_path).expanduser().resolve()
        return f"sqlite:///{resolved.as_posix()}"

    return f"sqlite:///{DEFAULT_DB_PATH.resolve().as_posix()}"


def sqlite_path_from_url(url: str) -> Path | None:
    """Return the filesystem Path if `url` points to a file-backed SQLite database."""
    if not url.startswith("sqlite:///"):
        return None
    raw = url[len("sqlite:///"):]
    if not raw or raw == ":memory:" or raw.startswith("file::memory:"):
        return None
    if raw.startswith("file:"):
        raw = raw[len("file:"):].split("?", 1)[0]
    return Path(raw)
