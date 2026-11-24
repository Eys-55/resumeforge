"""Normalized SQLAlchemy 2.0 ORM models for ResumeForge."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base declarative class for all ResumeForge tables."""


class Niche(Base):
    __tablename__ = "niches"
    __table_args__ = (
        CheckConstraint(
            "demand_tier IN ('high', 'very_high', 'emerging')",
            name="ck_niches_demand_tier",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    market_year: Mapped[int] = mapped_column(Integer, nullable=False, default=2026)
    demand_tier: Mapped[str] = mapped_column(String(32), nullable=False, default="very_high")
    ph_market_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    roles: Mapped[list[NicheRole]] = relationship(
        back_populates="niche", cascade="all, delete-orphan", order_by="NicheRole.id"
    )
    reference_patterns: Mapped[list[ReferencePattern]] = relationship(
        back_populates="niche", cascade="all, delete-orphan"
    )
    resumes: Mapped[list[Resume]] = relationship(back_populates="niche")
    job_postings: Mapped[list[JobPosting]] = relationship(
        back_populates="niche", cascade="all, delete-orphan", order_by="JobPosting.id"
    )


class NicheRole(Base):
    __tablename__ = "niche_roles"
    __table_args__ = (
        CheckConstraint(
            "seniority_band IN ('entry', 'mid', 'senior', 'lead')",
            name="ck_niche_roles_seniority_band",
        ),
        CheckConstraint(
            "salary_php_max >= salary_php_min",
            name="ck_niche_roles_salary_range",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    niche_id: Mapped[int] = mapped_column(
        ForeignKey("niches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    seniority_band: Mapped[str] = mapped_column(String(24), nullable=False, default="mid")
    salary_php_min: Mapped[int] = mapped_column(Integer, nullable=False)
    salary_php_max: Mapped[int] = mapped_column(Integer, nullable=False)
    work_setup_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    required_skills_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    trending_tools_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    common_certs_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    typical_kpis_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    niche: Mapped[Niche] = relationship(back_populates="roles")
    resumes: Mapped[list[Resume]] = relationship(back_populates="niche_role")


class ReferencePattern(Base):
    __tablename__ = "reference_patterns"
    __table_args__ = (
        CheckConstraint(
            "source_type IN ('pasted_text', 'image_extract', 'pdf_extract', 'url_extract')",
            name="ck_ref_patterns_source_type",
        ),
        CheckConstraint(
            "seniority_observed IN ('entry', 'mid', 'senior', 'lead')",
            name="ck_ref_patterns_seniority",
        ),
        CheckConstraint(
            "pii_scrubbed = 1",
            name="ck_ref_pattern_pii_scrubbed",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pattern_key: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    niche_id: Mapped[int] = mapped_column(
        ForeignKey("niches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_label: Mapped[str] = mapped_column(String(160), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="pasted_text")
    seniority_observed: Mapped[str] = mapped_column(String(24), nullable=False, default="mid")
    layout_archetype: Mapped[str] = mapped_column(String(80), nullable=False)
    section_order_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    ph_conventions_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    metric_patterns_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    tool_clusters_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    career_arc_summary: Mapped[str] = mapped_column(Text, nullable=False)
    strengths_notes: Mapped[str] = mapped_column(Text, nullable=False)
    modernization_notes: Mapped[str] = mapped_column(Text, nullable=False)
    pii_scrubbed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    niche: Mapped[Niche] = relationship(back_populates="reference_patterns")
    resumes: Mapped[list[Resume]] = relationship(back_populates="reference_pattern")


class Resume(Base):
    __tablename__ = "resumes"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'needs_revision', 'gold_standard', 'archived')",
            name="ck_resumes_status",
        ),
        CheckConstraint(
            "seniority IN ('entry', 'mid', 'senior', 'lead')",
            name="ck_resumes_seniority",
        ),
        CheckConstraint(
            "total_years_experience >= 0.0",
            name="ck_resumes_years_nonneg",
        ),
        Index("ix_resumes_niche_status", "niche_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    niche_id: Mapped[int] = mapped_column(
        ForeignKey("niches.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    niche_role_id: Mapped[int | None] = mapped_column(
        ForeignKey("niche_roles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    reference_pattern_id: Mapped[int | None] = mapped_column(
        ForeignKey("reference_patterns.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", index=True)
    seniority: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    target_role_title: Mapped[str] = mapped_column(String(200), nullable=False)
    layout_archetype: Mapped[str] = mapped_column(String(80), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    headline: Mapped[str] = mapped_column(String(250), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(String(64), nullable=False)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    region: Mapped[str] = mapped_column(String(120), nullable=False)
    work_setup_preference: Mapped[str] = mapped_column(String(80), nullable=False)
    timezone_readiness: Mapped[str] = mapped_column(String(120), nullable=False)
    expected_salary_php: Mapped[int | None] = mapped_column(Integer)
    linkedin_slug: Mapped[str | None] = mapped_column(String(160))
    portfolio_url: Mapped[str | None] = mapped_column(String(300))
    professional_summary: Mapped[str] = mapped_column(Text, nullable=False)
    total_years_experience: Mapped[float] = mapped_column(Float, nullable=False)
    quality_score: Mapped[int | None] = mapped_column(Integer)
    target_job_posting_id: Mapped[int | None] = mapped_column(
        ForeignKey("job_postings.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    niche: Mapped[Niche] = relationship(back_populates="resumes")
    niche_role: Mapped[NicheRole | None] = relationship(back_populates="resumes")
    reference_pattern: Mapped[ReferencePattern | None] = relationship(back_populates="resumes")
    target_job_posting: Mapped[JobPosting | None] = relationship(back_populates="resumes")

    experiences: Mapped[list[ResumeExperience]] = relationship(
        back_populates="resume", cascade="all, delete-orphan", order_by="ResumeExperience.sort_order"
    )
    education: Mapped[list[ResumeEducation]] = relationship(
        back_populates="resume", cascade="all, delete-orphan", order_by="ResumeEducation.sort_order"
    )
    skills: Mapped[list[ResumeSkill]] = relationship(
        back_populates="resume", cascade="all, delete-orphan", order_by="ResumeSkill.sort_order"
    )
    certifications: Mapped[list[ResumeCertification]] = relationship(
        back_populates="resume", cascade="all, delete-orphan", order_by="ResumeCertification.sort_order"
    )
    projects: Mapped[list[ResumeProject]] = relationship(
        back_populates="resume", cascade="all, delete-orphan", order_by="ResumeProject.sort_order"
    )
    languages: Mapped[list[ResumeLanguage]] = relationship(
        back_populates="resume", cascade="all, delete-orphan", order_by="ResumeLanguage.sort_order"
    )
    reviews: Mapped[list[ResumeReview]] = relationship(
        back_populates="resume", cascade="all, delete-orphan", order_by="ResumeReview.id"
    )
    ats_runs: Mapped[list[ResumeAtsRun]] = relationship(
        back_populates="resume", cascade="all, delete-orphan", order_by="ResumeAtsRun.id"
    )


class ResumeExperience(Base):
    __tablename__ = "resume_experiences"
    __table_args__ = (
        CheckConstraint(
            "employment_type IN ('Full-time', 'Part-time', 'Contract', 'Freelance', 'Internship')",
            name="ck_resume_exp_employment_type",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    company_archetype: Mapped[str] = mapped_column(String(120), nullable=False)
    role_title: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[str] = mapped_column(String(160), nullable=False)
    employment_type: Mapped[str] = mapped_column(String(32), nullable=False, default="Full-time")
    start_date: Mapped[str] = mapped_column(String(16), nullable=False)
    end_date: Mapped[str] = mapped_column(String(16), nullable=False, default="present")
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    resume: Mapped[Resume] = relationship(back_populates="experiences")
    bullets: Mapped[list[ResumeBullet]] = relationship(
        back_populates="experience", cascade="all, delete-orphan", order_by="ResumeBullet.sort_order"
    )


class ResumeBullet(Base):
    __tablename__ = "resume_bullets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    experience_id: Mapped[int] = mapped_column(
        ForeignKey("resume_experiences.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    action_verb: Mapped[str] = mapped_column(String(64), nullable=False)
    metric_value: Mapped[str | None] = mapped_column(String(120))
    tags_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    experience: Mapped[ResumeExperience] = relationship(back_populates="bullets")


class ResumeEducation(Base):
    __tablename__ = "resume_education"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    institution: Mapped[str] = mapped_column(String(200), nullable=False)
    degree: Mapped[str] = mapped_column(String(200), nullable=False)
    field_of_study: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[str] = mapped_column(String(160), nullable=False)
    start_year: Mapped[int | None] = mapped_column(Integer)
    graduation_year: Mapped[int] = mapped_column(Integer, nullable=False)
    honors: Mapped[str | None] = mapped_column(String(200))
    relevant_coursework_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    resume: Mapped[Resume] = relationship(back_populates="education")


class ResumeSkill(Base):
    __tablename__ = "resume_skills"
    __table_args__ = (
        UniqueConstraint("resume_id", "category", "name", name="uq_resume_skill"),
        CheckConstraint(
            "proficiency IN ('Core', 'Proficient', 'Working')",
            name="ck_resume_skill_proficiency",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    proficiency: Mapped[str] = mapped_column(String(24), nullable=False, default="Core")
    years_used: Mapped[float | None] = mapped_column(Float)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    resume: Mapped[Resume] = relationship(back_populates="skills")


class ResumeCertification(Base):
    __tablename__ = "resume_certifications"
    __table_args__ = (
        CheckConstraint(
            "credential_type IN ('tech', 'bpo_ops', 'tesda', 'healthcare', 'finance', 'language', 'industry')",
            name="ck_resume_cert_type",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    issuer: Mapped[str] = mapped_column(String(200), nullable=False)
    year_earned: Mapped[int] = mapped_column(Integer, nullable=False)
    expiry_year: Mapped[int | None] = mapped_column(Integer)
    credential_type: Mapped[str] = mapped_column(String(32), nullable=False, default="industry")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    resume: Mapped[Resume] = relationship(back_populates="certifications")


class ResumeProject(Base):
    __tablename__ = "resume_projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(160), nullable=False)
    tech_stack_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    impact_metric: Mapped[str | None] = mapped_column(String(200))
    url: Mapped[str | None] = mapped_column(String(300))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    resume: Mapped[Resume] = relationship(back_populates="projects")


class ResumeLanguage(Base):
    __tablename__ = "resume_languages"
    __table_args__ = (
        UniqueConstraint("resume_id", "language", name="uq_resume_language"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    language: Mapped[str] = mapped_column(String(80), nullable=False)
    proficiency: Mapped[str] = mapped_column(String(80), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    resume: Mapped[Resume] = relationship(back_populates="languages")


class ResumeReview(Base):
    __tablename__ = "resume_reviews"
    __table_args__ = (
        CheckConstraint(
            "reviewer_type IN ('deterministic', 'agent_auditor')",
            name="ck_resume_review_type",
        ),
        CheckConstraint(
            "total_score >= 0 AND total_score <= max_score",
            name="ck_resume_review_score_bounds",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewer_type: Mapped[str] = mapped_column(String(32), nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    total_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_score: Mapped[int] = mapped_column(Integer, nullable=False, default=35)
    rubric_scores_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    deterministic_errors_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    critique_summary: Mapped[str] = mapped_column(Text, nullable=False)
    required_fixes_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    resume: Mapped[Resume] = relationship(back_populates="reviews")


JOB_PLATFORMS = ("onlinejobs_ph", "linkedin", "upwork", "jobstreet", "indeed", "agency", "other")


class JobPosting(Base):
    """A real (PII-scrubbed) remote job post that fictional resumes are targeted at and ATS-scored against."""

    __tablename__ = "job_postings"
    __table_args__ = (
        CheckConstraint(
            "platform IN ('onlinejobs_ph', 'linkedin', 'upwork', 'jobstreet', 'indeed', 'agency', 'other')",
            name="ck_job_postings_platform",
        ),
        CheckConstraint(
            "source_type IN ('pasted_text', 'url_extract')",
            name="ck_job_postings_source_type",
        ),
        CheckConstraint("pii_scrubbed = 1", name="ck_job_postings_pii_scrubbed"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    posting_key: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    niche_id: Mapped[int] = mapped_column(
        ForeignKey("niches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    employer_type: Mapped[str] = mapped_column(String(200), nullable=False)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="pasted_text")
    source_url: Mapped[str | None] = mapped_column(String(500))
    remote_setup: Mapped[str] = mapped_column(String(160), nullable=False)
    timezone_overlap: Mapped[str | None] = mapped_column(String(160))
    pay_band: Mapped[str | None] = mapped_column(String(160))
    description_text: Mapped[str] = mapped_column(Text, nullable=False)
    keywords_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    captured_on: Mapped[str] = mapped_column(String(16), nullable=False)
    pii_scrubbed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    niche: Mapped[Niche] = relationship(back_populates="job_postings")
    resumes: Mapped[list[Resume]] = relationship(back_populates="target_job_posting")
    ats_runs: Mapped[list[ResumeAtsRun]] = relationship(back_populates="job_posting")


class ResumeAtsRun(Base):
    """One external ATS evaluation (Resume-Matcher) of a resume against a job posting."""

    __tablename__ = "resume_ats_runs"
    __table_args__ = (
        CheckConstraint("ats_score >= 0 AND ats_score <= 100", name="ck_resume_ats_score_bounds"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_posting_id: Mapped[int] = mapped_column(
        ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tool: Mapped[str] = mapped_column(String(64), nullable=False, default="resume-matcher")
    tool_version: Mapped[str] = mapped_column(String(32), nullable=False)
    ats_score: Mapped[float] = mapped_column(Float, nullable=False)
    sub_scores_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    missing_keywords_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    recommendations_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    parse_check_ok: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    parse_score: Mapped[float | None] = mapped_column(Float)
    parse_issues_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    resume: Mapped[Resume] = relationship(back_populates="ats_runs")
    job_posting: Mapped[JobPosting] = relationship(back_populates="ats_runs")
