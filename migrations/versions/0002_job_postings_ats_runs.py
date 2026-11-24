"""Add remote job postings, resume target postings, and external ATS runs.

Revision ID: 0002_job_postings_ats_runs
Revises: 0001_initial_schema
Create Date: 2026-11-25 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002_job_postings_ats_runs"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None

# Views reference `resumes`; SQLite batch table rebuilds fail while they exist.
# `resumeforge db init` recreates them via `resumeforge.db.views.ensure_views` after migrating.
_VIEWS = ("v_gold_resumes_summary", "v_niche_coverage")


def _drop_views() -> None:
    for view in _VIEWS:
        op.execute(f"DROP VIEW IF EXISTS {view}")


def upgrade() -> None:
    op.create_table(
        "job_postings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("posting_key", sa.String(length=120), nullable=False),
        sa.Column("niche_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("employer_type", sa.String(length=200), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("remote_setup", sa.String(length=160), nullable=False),
        sa.Column("timezone_overlap", sa.String(length=160), nullable=True),
        sa.Column("pay_band", sa.String(length=160), nullable=True),
        sa.Column("description_text", sa.Text(), nullable=False),
        sa.Column("keywords_json", sa.Text(), nullable=False),
        sa.Column("captured_on", sa.String(length=16), nullable=False),
        sa.Column("pii_scrubbed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "platform IN ('onlinejobs_ph', 'linkedin', 'upwork', 'jobstreet', 'indeed', 'agency', 'other')",
            name="ck_job_postings_platform",
        ),
        sa.CheckConstraint("source_type IN ('pasted_text', 'url_extract')", name="ck_job_postings_source_type"),
        sa.CheckConstraint("pii_scrubbed = 1", name="ck_job_postings_pii_scrubbed"),
        sa.ForeignKeyConstraint(["niche_id"], ["niches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_postings_posting_key", "job_postings", ["posting_key"], unique=True)
    op.create_index("ix_job_postings_niche_id", "job_postings", ["niche_id"], unique=False)

    _drop_views()
    with op.batch_alter_table("resumes") as batch:
        batch.add_column(sa.Column("target_job_posting_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_resumes_target_job_posting_id",
            "job_postings",
            ["target_job_posting_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch.create_index("ix_resumes_target_job_posting_id", ["target_job_posting_id"], unique=False)

    op.create_table(
        "resume_ats_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("resume_id", sa.Integer(), nullable=False),
        sa.Column("job_posting_id", sa.Integer(), nullable=False),
        sa.Column("tool", sa.String(length=64), nullable=False),
        sa.Column("tool_version", sa.String(length=32), nullable=False),
        sa.Column("ats_score", sa.Float(), nullable=False),
        sa.Column("sub_scores_json", sa.Text(), nullable=False),
        sa.Column("missing_keywords_json", sa.Text(), nullable=False),
        sa.Column("recommendations_json", sa.Text(), nullable=False),
        sa.Column("parse_check_ok", sa.Boolean(), nullable=False),
        sa.Column("parse_score", sa.Float(), nullable=True),
        sa.Column("parse_issues_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("ats_score >= 0 AND ats_score <= 100", name="ck_resume_ats_score_bounds"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_posting_id"], ["job_postings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_resume_ats_runs_resume_id", "resume_ats_runs", ["resume_id"], unique=False)
    op.create_index("ix_resume_ats_runs_job_posting_id", "resume_ats_runs", ["job_posting_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_resume_ats_runs_job_posting_id", table_name="resume_ats_runs")
    op.drop_index("ix_resume_ats_runs_resume_id", table_name="resume_ats_runs")
    op.drop_table("resume_ats_runs")
    _drop_views()
    with op.batch_alter_table("resumes") as batch:
        batch.drop_index("ix_resumes_target_job_posting_id")
        batch.drop_constraint("fk_resumes_target_job_posting_id", type_="foreignkey")
        batch.drop_column("target_job_posting_id")
    op.drop_index("ix_job_postings_niche_id", table_name="job_postings")
    op.drop_index("ix_job_postings_posting_key", table_name="job_postings")
    op.drop_table("job_postings")
