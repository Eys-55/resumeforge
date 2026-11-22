"""Initial normalized ResumeForge schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-11-23 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "niches",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("market_year", sa.Integer(), nullable=False),
        sa.Column("demand_tier", sa.String(length=32), nullable=False),
        sa.Column("ph_market_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("demand_tier IN ('high', 'very_high', 'emerging')", name="ck_niches_demand_tier"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_niches_slug", "niches", ["slug"], unique=True)

    op.create_table(
        "niche_roles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("niche_id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("seniority_band", sa.String(length=24), nullable=False),
        sa.Column("salary_php_min", sa.Integer(), nullable=False),
        sa.Column("salary_php_max", sa.Integer(), nullable=False),
        sa.Column("work_setup_json", sa.Text(), nullable=False),
        sa.Column("required_skills_json", sa.Text(), nullable=False),
        sa.Column("trending_tools_json", sa.Text(), nullable=False),
        sa.Column("common_certs_json", sa.Text(), nullable=False),
        sa.Column("typical_kpis_json", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("seniority_band IN ('entry', 'mid', 'senior', 'lead')", name="ck_niche_roles_seniority_band"),
        sa.CheckConstraint("salary_php_max >= salary_php_min", name="ck_niche_roles_salary_range"),
        sa.ForeignKeyConstraint(["niche_id"], ["niches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_niche_roles_niche_id", "niche_roles", ["niche_id"], unique=False)
    op.create_index("ix_niche_roles_slug", "niche_roles", ["slug"], unique=True)

    op.create_table(
        "reference_patterns",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("pattern_key", sa.String(length=120), nullable=False),
        sa.Column("niche_id", sa.Integer(), nullable=False),
        sa.Column("source_label", sa.String(length=160), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("seniority_observed", sa.String(length=24), nullable=False),
        sa.Column("layout_archetype", sa.String(length=80), nullable=False),
        sa.Column("section_order_json", sa.Text(), nullable=False),
        sa.Column("ph_conventions_json", sa.Text(), nullable=False),
        sa.Column("metric_patterns_json", sa.Text(), nullable=False),
        sa.Column("tool_clusters_json", sa.Text(), nullable=False),
        sa.Column("career_arc_summary", sa.Text(), nullable=False),
        sa.Column("strengths_notes", sa.Text(), nullable=False),
        sa.Column("modernization_notes", sa.Text(), nullable=False),
        sa.Column("pii_scrubbed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("source_type IN ('pasted_text', 'image_extract', 'pdf_extract', 'url_extract')", name="ck_ref_patterns_source_type"),
        sa.CheckConstraint("seniority_observed IN ('entry', 'mid', 'senior', 'lead')", name="ck_ref_patterns_seniority"),
        sa.CheckConstraint("pii_scrubbed = 1", name="ck_ref_pattern_pii_scrubbed"),
        sa.ForeignKeyConstraint(["niche_id"], ["niches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reference_patterns_niche_id", "reference_patterns", ["niche_id"], unique=False)
    op.create_index("ix_reference_patterns_pattern_key", "reference_patterns", ["pattern_key"], unique=True)

    op.create_table(
        "resumes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("resume_code", sa.String(length=64), nullable=False),
        sa.Column("niche_id", sa.Integer(), nullable=False),
        sa.Column("niche_role_id", sa.Integer(), nullable=True),
        sa.Column("reference_pattern_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("seniority", sa.String(length=24), nullable=False),
        sa.Column("target_role_title", sa.String(length=200), nullable=False),
        sa.Column("layout_archetype", sa.String(length=80), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("headline", sa.String(length=250), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=64), nullable=False),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("region", sa.String(length=120), nullable=False),
        sa.Column("work_setup_preference", sa.String(length=80), nullable=False),
        sa.Column("timezone_readiness", sa.String(length=120), nullable=False),
        sa.Column("expected_salary_php", sa.Integer(), nullable=True),
        sa.Column("linkedin_slug", sa.String(length=160), nullable=True),
        sa.Column("portfolio_url", sa.String(length=300), nullable=True),
        sa.Column("professional_summary", sa.Text(), nullable=False),
        sa.Column("total_years_experience", sa.Float(), nullable=False),
        sa.Column("quality_score", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('draft', 'needs_revision', 'gold_standard', 'archived')", name="ck_resumes_status"),
        sa.CheckConstraint("seniority IN ('entry', 'mid', 'senior', 'lead')", name="ck_resumes_seniority"),
        sa.CheckConstraint("total_years_experience >= 0.0", name="ck_resumes_years_nonneg"),
        sa.ForeignKeyConstraint(["niche_id"], ["niches.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["niche_role_id"], ["niche_roles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reference_pattern_id"], ["reference_patterns.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("full_name"),
    )
    op.create_index("ix_resumes_niche_id", "resumes", ["niche_id"], unique=False)
    op.create_index("ix_resumes_niche_role_id", "resumes", ["niche_role_id"], unique=False)
    op.create_index("ix_resumes_niche_status", "resumes", ["niche_id", "status"], unique=False)
    op.create_index("ix_resumes_reference_pattern_id", "resumes", ["reference_pattern_id"], unique=False)
    op.create_index("ix_resumes_resume_code", "resumes", ["resume_code"], unique=True)
    op.create_index("ix_resumes_seniority", "resumes", ["seniority"], unique=False)
    op.create_index("ix_resumes_status", "resumes", ["status"], unique=False)

    op.create_table(
        "resume_experiences",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("resume_id", sa.Integer(), nullable=False),
        sa.Column("company_name", sa.String(length=200), nullable=False),
        sa.Column("company_archetype", sa.String(length=120), nullable=False),
        sa.Column("role_title", sa.String(length=200), nullable=False),
        sa.Column("location", sa.String(length=160), nullable=False),
        sa.Column("employment_type", sa.String(length=32), nullable=False),
        sa.Column("start_date", sa.String(length=16), nullable=False),
        sa.Column("end_date", sa.String(length=16), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.CheckConstraint("employment_type IN ('Full-time', 'Part-time', 'Contract', 'Freelance', 'Internship')", name="ck_resume_exp_employment_type"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_resume_experiences_resume_id", "resume_experiences", ["resume_id"], unique=False)

    op.create_table(
        "resume_bullets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("experience_id", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("action_verb", sa.String(length=64), nullable=False),
        sa.Column("metric_value", sa.String(length=120), nullable=True),
        sa.Column("tags_json", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["experience_id"], ["resume_experiences.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_resume_bullets_experience_id", "resume_bullets", ["experience_id"], unique=False)

    op.create_table(
        "resume_education",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("resume_id", sa.Integer(), nullable=False),
        sa.Column("institution", sa.String(length=200), nullable=False),
        sa.Column("degree", sa.String(length=200), nullable=False),
        sa.Column("field_of_study", sa.String(length=200), nullable=False),
        sa.Column("location", sa.String(length=160), nullable=False),
        sa.Column("start_year", sa.Integer(), nullable=True),
        sa.Column("graduation_year", sa.Integer(), nullable=False),
        sa.Column("honors", sa.String(length=200), nullable=True),
        sa.Column("relevant_coursework_json", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_resume_education_resume_id", "resume_education", ["resume_id"], unique=False)

    op.create_table(
        "resume_skills",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("resume_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("proficiency", sa.String(length=24), nullable=False),
        sa.Column("years_used", sa.Float(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.CheckConstraint("proficiency IN ('Core', 'Proficient', 'Working')", name="ck_resume_skill_proficiency"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("resume_id", "category", "name", name="uq_resume_skill"),
    )
    op.create_index("ix_resume_skills_resume_id", "resume_skills", ["resume_id"], unique=False)

    op.create_table(
        "resume_certifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("resume_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("issuer", sa.String(length=200), nullable=False),
        sa.Column("year_earned", sa.Integer(), nullable=False),
        sa.Column("expiry_year", sa.Integer(), nullable=True),
        sa.Column("credential_type", sa.String(length=32), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.CheckConstraint("credential_type IN ('tech', 'bpo_ops', 'tesda', 'healthcare', 'finance', 'language', 'industry')", name="ck_resume_cert_type"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_resume_certifications_resume_id", "resume_certifications", ["resume_id"], unique=False)

    op.create_table(
        "resume_projects",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("resume_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("role", sa.String(length=160), nullable=False),
        sa.Column("tech_stack_json", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("impact_metric", sa.String(length=200), nullable=True),
        sa.Column("url", sa.String(length=300), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_resume_projects_resume_id", "resume_projects", ["resume_id"], unique=False)

    op.create_table(
        "resume_languages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("resume_id", sa.Integer(), nullable=False),
        sa.Column("language", sa.String(length=80), nullable=False),
        sa.Column("proficiency", sa.String(length=80), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("resume_id", "language", name="uq_resume_language"),
    )
    op.create_index("ix_resume_languages_resume_id", "resume_languages", ["resume_id"], unique=False)

    op.create_table(
        "resume_reviews",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("resume_id", sa.Integer(), nullable=False),
        sa.Column("reviewer_type", sa.String(length=32), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("total_score", sa.Integer(), nullable=False),
        sa.Column("max_score", sa.Integer(), nullable=False),
        sa.Column("rubric_scores_json", sa.Text(), nullable=False),
        sa.Column("deterministic_errors_json", sa.Text(), nullable=False),
        sa.Column("critique_summary", sa.Text(), nullable=False),
        sa.Column("required_fixes_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("reviewer_type IN ('deterministic', 'agent_auditor')", name="ck_resume_review_type"),
        sa.CheckConstraint("total_score >= 0 AND total_score <= max_score", name="ck_resume_review_score_bounds"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_resume_reviews_resume_id", "resume_reviews", ["resume_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_resume_reviews_resume_id", table_name="resume_reviews")
    op.drop_table("resume_reviews")
    op.drop_index("ix_resume_languages_resume_id", table_name="resume_languages")
    op.drop_table("resume_languages")
    op.drop_index("ix_resume_projects_resume_id", table_name="resume_projects")
    op.drop_table("resume_projects")
    op.drop_index("ix_resume_certifications_resume_id", table_name="resume_certifications")
    op.drop_table("resume_certifications")
    op.drop_index("ix_resume_skills_resume_id", table_name="resume_skills")
    op.drop_table("resume_skills")
    op.drop_index("ix_resume_education_resume_id", table_name="resume_education")
    op.drop_table("resume_education")
    op.drop_index("ix_resume_bullets_experience_id", table_name="resume_bullets")
    op.drop_table("resume_bullets")
    op.drop_index("ix_resume_experiences_resume_id", table_name="resume_experiences")
    op.drop_table("resume_experiences")
    op.drop_index("ix_resumes_status", table_name="resumes")
    op.drop_index("ix_resumes_seniority", table_name="resumes")
    op.drop_index("ix_resumes_resume_code", table_name="resumes")
    op.drop_index("ix_resumes_reference_pattern_id", table_name="resumes")
    op.drop_index("ix_resumes_niche_status", table_name="resumes")
    op.drop_index("ix_resumes_niche_role_id", table_name="resumes")
    op.drop_index("ix_resumes_niche_id", table_name="resumes")
    op.drop_table("resumes")
    op.drop_index("ix_reference_patterns_pattern_key", table_name="reference_patterns")
    op.drop_index("ix_reference_patterns_niche_id", table_name="reference_patterns")
    op.drop_table("reference_patterns")
    op.drop_index("ix_niche_roles_slug", table_name="niche_roles")
    op.drop_index("ix_niche_roles_niche_id", table_name="niche_roles")
    op.drop_table("niche_roles")
    op.drop_index("ix_niches_slug", table_name="niches")
    op.drop_table("niches")
