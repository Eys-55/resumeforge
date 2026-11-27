"""Programmatic Alembic migration runner and DB stats helper."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from resumeforge.config import ALEMBIC_INI_PATH, MIGRATIONS_DIR, get_database_url
from resumeforge.db.engine import get_engine


def make_alembic_config(db_url_or_path: Path | str | None = None) -> Config:
    cfg = Config(str(ALEMBIC_INI_PATH))
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", get_database_url(db_url_or_path))
    return cfg


def upgrade_head(db_url_or_path: Path | str | None = None) -> None:
    """Apply all Alembic migrations up to head."""
    command.upgrade(make_alembic_config(db_url_or_path), "head")


def downgrade_base(db_url_or_path: Path | str | None = None) -> None:
    """Downgrade all Alembic migrations back to base."""
    command.downgrade(make_alembic_config(db_url_or_path), "base")


def get_db_stats(db_url_or_path: Path | str | None = None) -> dict[str, int]:
    """Return row counts across core tables using a strictly read-only connection."""
    tables = [
        "niches",
        "niche_roles",
        "reference_patterns",
        "resumes",
        "resume_experiences",
        "resume_bullets",
        "resume_education",
        "resume_skills",
        "resume_certifications",
        "resume_projects",
        "resume_languages",
        "resume_reviews",
        "job_postings",
        "resume_ats_runs",
    ]
    engine = get_engine(db_url_or_path, read_only=True)
    counts: dict[str, int] = {}
    try:
        with engine.connect() as conn:
            for table in tables:
                counts[table] = int(conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar() or 0)
    finally:
        engine.dispose()
    return counts
