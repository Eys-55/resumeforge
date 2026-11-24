"""Analytical SQL views and strictly read-only SQL query execution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import Engine, text

from resumeforge.db.engine import get_engine

VIEW_DEFINITIONS: dict[str, str] = {
    "v_gold_resumes_summary": """
    CREATE VIEW v_gold_resumes_summary AS
    SELECT
        r.id AS resume_id,
        r.resume_code,
        n.slug AS niche_slug,
        n.name AS niche_name,
        nr.slug AS role_slug,
        r.target_role_title,
        r.seniority,
        r.layout_archetype,
        r.full_name,
        r.headline,
        r.city,
        r.region,
        r.work_setup_preference,
        r.timezone_readiness,
        r.expected_salary_php,
        r.total_years_experience,
        r.quality_score,
        (SELECT COUNT(*) FROM resume_experiences e WHERE e.resume_id = r.id) AS experience_count,
        (SELECT COUNT(*) FROM resume_skills s WHERE s.resume_id = r.id) AS skill_count,
        (SELECT COUNT(*) FROM resume_certifications c WHERE c.resume_id = r.id) AS certification_count,
        (SELECT COUNT(*) FROM resume_projects p WHERE p.resume_id = r.id) AS project_count,
        (
            SELECT rv.total_score
            FROM resume_reviews rv
            WHERE rv.resume_id = r.id
            ORDER BY rv.id DESC
            LIMIT 1
        ) AS latest_review_score,
        (SELECT jp.posting_key FROM job_postings jp WHERE jp.id = r.target_job_posting_id) AS target_posting_key,
        (
            SELECT ar.ats_score
            FROM resume_ats_runs ar
            WHERE ar.resume_id = r.id AND ar.job_posting_id = r.target_job_posting_id
            ORDER BY ar.id DESC
            LIMIT 1
        ) AS latest_ats_score,
        r.created_at,
        r.updated_at
    FROM resumes r
    JOIN niches n ON n.id = r.niche_id
    LEFT JOIN niche_roles nr ON nr.id = r.niche_role_id
    WHERE r.status = 'gold_standard';
    """,
    "v_niche_coverage": """
    CREATE VIEW v_niche_coverage AS
    SELECT
        n.slug AS niche_slug,
        n.name AS niche_name,
        n.market_year,
        n.demand_tier,
        (SELECT COUNT(*) FROM niche_roles nr WHERE nr.niche_id = n.id) AS role_archetypes_count,
        (SELECT COUNT(*) FROM reference_patterns rp WHERE rp.niche_id = n.id) AS reference_patterns_count,
        (SELECT COUNT(*) FROM resumes r WHERE r.niche_id = n.id AND r.status = 'draft') AS draft_count,
        (SELECT COUNT(*) FROM resumes r WHERE r.niche_id = n.id AND r.status = 'needs_revision') AS needs_revision_count,
        (SELECT COUNT(*) FROM resumes r WHERE r.niche_id = n.id AND r.status = 'gold_standard') AS gold_standard_count,
        (SELECT COUNT(*) FROM resumes r WHERE r.niche_id = n.id AND r.status = 'gold_standard' AND r.seniority = 'entry') AS gold_entry_count,
        (SELECT COUNT(*) FROM resumes r WHERE r.niche_id = n.id AND r.status = 'gold_standard' AND r.seniority = 'mid') AS gold_mid_count,
        (SELECT COUNT(*) FROM resumes r WHERE r.niche_id = n.id AND r.status = 'gold_standard' AND r.seniority = 'senior') AS gold_senior_count,
        (SELECT COUNT(*) FROM resumes r WHERE r.niche_id = n.id AND r.status = 'gold_standard' AND r.seniority = 'lead') AS gold_lead_count
    FROM niches n
    ORDER BY n.slug;
    """,
}


def ensure_views(engine: Engine) -> None:
    """Create or replace analytical SQL views idempotently."""
    with engine.begin() as conn:
        for view_name in reversed(list(VIEW_DEFINITIONS)):
            conn.execute(text(f"DROP VIEW IF EXISTS {view_name};"))
        for ddl in VIEW_DEFINITIONS.values():
            conn.execute(text(ddl))


def run_readonly_sql(
    sql: str,
    db_url_or_path: Path | str | None = None,
    params: dict[str, Any] | None = None,
) -> tuple[list[str], list[dict[str, Any]]]:
    """Execute a strictly read-only SQL query against the database.

    Uses SQLite `mode=ro` + `PRAGMA query_only = ON` so any write/DDL statement
    is rejected by the database engine.
    """
    engine = get_engine(db_url_or_path, read_only=True)
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql), params or {})
            columns = list(result.keys())
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
            return columns, rows
    finally:
        engine.dispose()
