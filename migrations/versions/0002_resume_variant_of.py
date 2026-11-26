"""Add resumes.variant_of_code and move persona uniqueness into the validator.

A persona may now have several targeted resume variants (e.g. a GoHighLevel
version and an AI Automation Engineer version of the same fictional person).
The DB-level UNIQUE(full_name) / UNIQUE(email) constraints are dropped; the
deterministic validator keeps enforcing uniqueness for every resume that is not
explicitly linked through `variant_of_code`.

SQLite cannot drop table constraints in place, so this follows SQLite's
documented 12-step table rebuild with foreign keys disabled (otherwise dropping
`resumes` would cascade-delete every child row).

Revision ID: 0002_resume_variant_of
Revises: 0001_initial_schema
Create Date: 2026-11-26 00:00:00
"""

from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "0002_resume_variant_of"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None

_VIEW_NAMES = ("v_gold_resumes_summary", "v_niche_coverage")

_COPY_COLUMNS = (
    "id, resume_code, niche_id, niche_role_id, reference_pattern_id, status, seniority, "
    "target_role_title, layout_archetype, full_name, headline, email, phone, city, region, "
    "work_setup_preference, timezone_readiness, expected_salary_php, linkedin_slug, portfolio_url, "
    "professional_summary, total_years_experience, quality_score, created_at, updated_at"
)

_INDEXES = (
    "CREATE INDEX ix_resumes_niche_id ON resumes (niche_id)",
    "CREATE INDEX ix_resumes_niche_role_id ON resumes (niche_role_id)",
    "CREATE INDEX ix_resumes_niche_status ON resumes (niche_id, status)",
    "CREATE INDEX ix_resumes_reference_pattern_id ON resumes (reference_pattern_id)",
    "CREATE UNIQUE INDEX ix_resumes_resume_code ON resumes (resume_code)",
    "CREATE INDEX ix_resumes_seniority ON resumes (seniority)",
    "CREATE INDEX ix_resumes_status ON resumes (status)",
)


def _create_table_sql(name: str, *, with_variant: bool, with_uniques: bool) -> str:
    variant_col = "\tvariant_of_code VARCHAR(64), \n" if with_variant else ""
    uniques = ", \n\tUNIQUE (email), \n\tUNIQUE (full_name)" if with_uniques else ""
    return f"""CREATE TABLE {name} (
	id INTEGER NOT NULL,
	resume_code VARCHAR(64) NOT NULL,
	niche_id INTEGER NOT NULL,
	niche_role_id INTEGER,
	reference_pattern_id INTEGER,
	status VARCHAR(32) NOT NULL,
	seniority VARCHAR(24) NOT NULL,
	target_role_title VARCHAR(200) NOT NULL,
	layout_archetype VARCHAR(80) NOT NULL,
	full_name VARCHAR(200) NOT NULL,
	headline VARCHAR(250) NOT NULL,
	email VARCHAR(255) NOT NULL,
	phone VARCHAR(64) NOT NULL,
	city VARCHAR(120) NOT NULL,
	region VARCHAR(120) NOT NULL,
	work_setup_preference VARCHAR(80) NOT NULL,
	timezone_readiness VARCHAR(120) NOT NULL,
	expected_salary_php INTEGER,
	linkedin_slug VARCHAR(160),
	portfolio_url VARCHAR(300),
	professional_summary TEXT NOT NULL,
	total_years_experience FLOAT NOT NULL,
	quality_score INTEGER,
	created_at DATETIME NOT NULL,
	updated_at DATETIME NOT NULL,
{variant_col}	PRIMARY KEY (id),
	CONSTRAINT ck_resumes_status CHECK (status IN ('draft', 'needs_revision', 'gold_standard', 'archived')),
	CONSTRAINT ck_resumes_seniority CHECK (seniority IN ('entry', 'mid', 'senior', 'lead')),
	CONSTRAINT ck_resumes_years_nonneg CHECK (total_years_experience >= 0.0),
	FOREIGN KEY(niche_id) REFERENCES niches (id) ON DELETE RESTRICT,
	FOREIGN KEY(niche_role_id) REFERENCES niche_roles (id) ON DELETE SET NULL,
	FOREIGN KEY(reference_pattern_id) REFERENCES reference_patterns (id) ON DELETE SET NULL{uniques}
)"""


def _rebuild_resumes(*, with_variant: bool, with_uniques: bool) -> None:
    bind = op.get_bind()
    bind.exec_driver_sql("PRAGMA foreign_keys = OFF")
    if bind.exec_driver_sql("PRAGMA foreign_keys").scalar() != 0:
        raise RuntimeError(
            "Could not disable SQLite foreign keys before rebuilding `resumes`; "
            "aborting to avoid cascade-deleting resume child rows."
        )

    for view_name in _VIEW_NAMES:
        bind.exec_driver_sql(f"DROP VIEW IF EXISTS {view_name}")

    bind.exec_driver_sql(_create_table_sql("resumes_new", with_variant=with_variant, with_uniques=with_uniques))
    bind.exec_driver_sql(f"INSERT INTO resumes_new ({_COPY_COLUMNS}) SELECT {_COPY_COLUMNS} FROM resumes")
    bind.exec_driver_sql("DROP TABLE resumes")
    bind.exec_driver_sql("ALTER TABLE resumes_new RENAME TO resumes")
    for stmt in _INDEXES:
        bind.exec_driver_sql(stmt)
    if with_variant:
        bind.exec_driver_sql("CREATE INDEX ix_resumes_variant_of_code ON resumes (variant_of_code)")

    violations = bind.exec_driver_sql("PRAGMA foreign_key_check").fetchall()
    if violations:
        raise RuntimeError(f"Foreign key violations after rebuilding `resumes`: {violations!r}")

    from resumeforge.db.views import VIEW_DEFINITIONS

    for view_name in _VIEW_NAMES:
        bind.execute(text(VIEW_DEFINITIONS[view_name]))


def upgrade() -> None:
    _rebuild_resumes(with_variant=True, with_uniques=False)


def downgrade() -> None:
    _rebuild_resumes(with_variant=False, with_uniques=True)
