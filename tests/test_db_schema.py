"""Tests for SQLAlchemy 2.0 schema, Alembic migrations, WAL, RO guard, and seed data."""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError

from resumeforge.db.engine import get_engine, session_scope
from resumeforge.db.migrations_helper import get_db_stats, upgrade_head
from resumeforge.db.models import Niche, ReferencePattern
from resumeforge.db.seed import seed_initial_niches
from resumeforge.db.views import ensure_views, run_readonly_sql


def test_migrations_views_and_seed(tmp_path) -> None:
    db_path = tmp_path / "schema.db"
    upgrade_head(db_path)
    engine = get_engine(db_path, read_only=False)
    try:
        ensure_views(engine)
        with engine.connect() as conn:
            journal = conn.execute(text("PRAGMA journal_mode;")).scalar()
            assert str(journal).lower() == "wal"

            tables = {
                row[0]
                for row in conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                ).all()
            }
            expected_tables = {
                "alembic_version",
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
            }
            assert expected_tables.issubset(tables)

            views = {
                row[0]
                for row in conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='view'")
                ).all()
            }
            assert {"v_gold_resumes_summary", "v_niche_coverage"}.issubset(views)
    finally:
        engine.dispose()

    with session_scope(db_path, read_only=False) as session:
        first = seed_initial_niches(session)
        assert first == {"niches_created": 2, "roles_created": 10}
    # Idempotent re-seed
    with session_scope(db_path, read_only=False) as session:
        second = seed_initial_niches(session)
        assert second == {"niches_created": 0, "roles_created": 0}

    stats = get_db_stats(db_path)
    assert stats["niches"] == 2
    assert stats["niche_roles"] == 10
    assert stats["resumes"] == 0


def test_readonly_mode_rejects_writes(tmp_path) -> None:
    db_path = tmp_path / "readonly.db"
    upgrade_head(db_path)
    engine = get_engine(db_path, read_only=False)
    ensure_views(engine)
    engine.dispose()
    with session_scope(db_path, read_only=False) as session:
        seed_initial_niches(session)

    cols, rows = run_readonly_sql("SELECT niche_slug, role_archetypes_count FROM v_niche_coverage", db_path)
    assert cols == ["niche_slug", "role_archetypes_count"]
    assert len(rows) == 2

    with pytest.raises(OperationalError):
        run_readonly_sql("DELETE FROM niches", db_path)


def test_pii_scrubbed_check_constraint(tmp_path) -> None:
    db_path = tmp_path / "constraint.db"
    upgrade_head(db_path)
    with session_scope(db_path, read_only=False) as session:
        seed_initial_niches(session)

    with pytest.raises(IntegrityError):
        with session_scope(db_path, read_only=False) as session:
            niche = session.query(Niche).filter_by(slug="tech-ai-automation").one()
            session.add(
                ReferencePattern(
                    pattern_key="bad-pattern-1",
                    niche_id=niche.id,
                    source_label="chat-test",
                    source_type="pasted_text",
                    seniority_observed="mid",
                    layout_archetype="single-column-ats",
                    career_arc_summary="3 years backend engineering.",
                    strengths_notes="Clear layout",
                    modernization_notes="Quantify API latency",
                    pii_scrubbed=False,
                )
            )
