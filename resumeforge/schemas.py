"""Pydantic v2 schemas for ResumeForge JSON ingestion, drafting, and auditing."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

SeniorityBand = Literal["entry", "mid", "senior", "lead"]
DemandTier = Literal["high", "very_high", "emerging"]
SourceType = Literal["pasted_text", "image_extract", "pdf_extract", "url_extract"]
EmploymentType = Literal["Full-time", "Part-time", "Contract", "Freelance", "Internship"]
SkillProficiency = Literal["Core", "Proficient", "Working"]
JobPlatform = Literal["onlinejobs_ph", "linkedin", "upwork", "jobstreet", "indeed", "agency", "other"]
JobSourceType = Literal["pasted_text", "url_extract"]
CredentialType = Literal["tech", "bpo_ops", "tesda", "healthcare", "finance", "language", "industry"]

RUBRIC_KEYS = (
    "deterministic_integrity",
    "ph_market_authenticity",
    "niche_tool_recency",
    "quantified_impact_realism",
    "readability_anti_slop",
    "cross_section_coherence",
    "pool_uniqueness_variety",
)


class NicheRoleInput(BaseModel):
    slug: str = Field(min_length=2, max_length=120)
    title: str = Field(min_length=2, max_length=200)
    seniority_band: SeniorityBand = "mid"
    salary_php_min: int = Field(ge=10000)
    salary_php_max: int = Field(ge=10000)
    work_setup: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    trending_tools: list[str] = Field(default_factory=list)
    common_certs: list[str] = Field(default_factory=list)
    typical_kpis: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_salary(self) -> NicheRoleInput:
        if self.salary_php_max < self.salary_php_min:
            raise ValueError("salary_php_max must be >= salary_php_min")
        return self


class NicheCreateInput(BaseModel):
    slug: str = Field(min_length=2, max_length=80)
    name: str = Field(min_length=2, max_length=200)
    description: str = Field(min_length=10)
    market_year: int = Field(default=2026, ge=2024, le=2030)
    demand_tier: DemandTier = "high"
    ph_market_notes: str | None = None
    roles: list[NicheRoleInput] = Field(default_factory=list)


class ReferencePatternInput(BaseModel):
    pattern_key: str = Field(min_length=3, max_length=120)
    niche_slug: str = Field(min_length=2, max_length=80)
    source_label: str = Field(min_length=2, max_length=160)
    source_type: SourceType = "pasted_text"
    seniority_observed: SeniorityBand = "mid"
    layout_archetype: str = Field(min_length=2, max_length=80)
    section_order: list[str] = Field(default_factory=list)
    ph_conventions: list[str] = Field(default_factory=list)
    metric_patterns: list[str] = Field(default_factory=list)
    tool_clusters: dict[str, list[str]] = Field(default_factory=dict)
    career_arc_summary: str = Field(min_length=10)
    strengths_notes: str = Field(min_length=5)
    modernization_notes: str = Field(min_length=5)
    pii_scrubbed: bool = True


class ResumeBulletInput(BaseModel):
    text: str = Field(min_length=15)
    action_verb: str = Field(min_length=2, max_length=64)
    metric_value: str | None = Field(default=None, max_length=120)
    tags: list[str] = Field(default_factory=list)


class ResumeExperienceInput(BaseModel):
    company_name: str = Field(min_length=2, max_length=200)
    company_archetype: str = Field(min_length=2, max_length=120)
    role_title: str = Field(min_length=2, max_length=200)
    location: str = Field(min_length=2, max_length=160)
    employment_type: EmploymentType = "Full-time"
    start_date: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    end_date: str = Field(min_length=4, max_length=16)
    is_current: bool = False
    bullets: list[ResumeBulletInput] = Field(min_length=1)


class ResumeEducationInput(BaseModel):
    institution: str = Field(min_length=2, max_length=200)
    degree: str = Field(min_length=2, max_length=200)
    field_of_study: str = Field(min_length=2, max_length=200)
    location: str = Field(min_length=2, max_length=160)
    start_year: int | None = Field(default=None, ge=1980, le=2035)
    graduation_year: int = Field(ge=1985, le=2035)
    honors: str | None = Field(default=None, max_length=200)
    relevant_coursework: list[str] = Field(default_factory=list)


class ResumeSkillInput(BaseModel):
    category: str = Field(min_length=2, max_length=120)
    name: str = Field(min_length=1, max_length=160)
    proficiency: SkillProficiency = "Core"
    years_used: float | None = Field(default=None, ge=0.0, le=30.0)


class ResumeCertificationInput(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    issuer: str = Field(min_length=2, max_length=200)
    year_earned: int = Field(ge=2000, le=2030)
    expiry_year: int | None = Field(default=None, ge=2000, le=2040)
    credential_type: CredentialType = "industry"


class ResumeProjectInput(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    role: str = Field(min_length=2, max_length=160)
    tech_stack: list[str] = Field(default_factory=list)
    summary: str = Field(min_length=10)
    impact_metric: str | None = Field(default=None, max_length=200)
    url: str | None = Field(default=None, max_length=300)


class ResumeLanguageInput(BaseModel):
    language: str = Field(min_length=2, max_length=80)
    proficiency: str = Field(min_length=2, max_length=80)


class ResumeDraftInput(BaseModel):
    resume_code: str = Field(min_length=4, max_length=64)
    niche_slug: str = Field(min_length=2, max_length=80)
    role_slug: str | None = Field(default=None, max_length=120)
    pattern_key: str | None = Field(default=None, max_length=120)
    seniority: SeniorityBand
    target_role_title: str = Field(min_length=2, max_length=200)
    layout_archetype: str = Field(min_length=2, max_length=80)
    full_name: str = Field(min_length=3, max_length=200)
    headline: str = Field(min_length=5, max_length=250)
    email: str = Field(min_length=5, max_length=255)
    phone: str = Field(min_length=8, max_length=64)
    city: str = Field(min_length=2, max_length=120)
    region: str = Field(min_length=2, max_length=120)
    work_setup_preference: str = Field(min_length=2, max_length=80)
    timezone_readiness: str = Field(min_length=2, max_length=120)
    expected_salary_php: int | None = Field(default=None, ge=15000)
    linkedin_slug: str | None = Field(default=None, max_length=160)
    portfolio_url: str | None = Field(default=None, max_length=300)
    professional_summary: str = Field(min_length=30)
    total_years_experience: float = Field(ge=0.0, le=40.0)
    experiences: list[ResumeExperienceInput] = Field(min_length=1)
    education: list[ResumeEducationInput] = Field(min_length=1)
    skills: list[ResumeSkillInput] = Field(min_length=5)
    certifications: list[ResumeCertificationInput] = Field(default_factory=list)
    projects: list[ResumeProjectInput] = Field(default_factory=list)
    languages: list[ResumeLanguageInput] = Field(default_factory=list)
    target_job_posting_key: str | None = Field(default=None, max_length=120)


class ResumeReviewInput(BaseModel):
    reviewer_type: Literal["deterministic", "agent_auditor"] = "agent_auditor"
    passed: bool
    rubric_scores: dict[str, int]
    critique_summary: str = Field(min_length=10)
    required_fixes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_rubric(self) -> ResumeReviewInput:
        missing = [k for k in RUBRIC_KEYS if k not in self.rubric_scores]
        if missing:
            raise ValueError(f"rubric_scores missing required keys: {missing}")
        extra = [k for k in self.rubric_scores if k not in RUBRIC_KEYS]
        if extra:
            raise ValueError(f"rubric_scores has unexpected keys: {extra}")
        for key, score in self.rubric_scores.items():
            if not (1 <= int(score) <= 5):
                raise ValueError(f"rubric_scores[{key!r}] must be 1..5, got {score}")
        return self


class JobKeywordsInput(BaseModel):
    """Requirements extracted from a job post; mirrors Resume-Matcher's `JobKeywords` contract."""

    role: str = Field(min_length=2, max_length=200)
    company: str = ""
    required_skills: list[str] = Field(min_length=1)
    preferred_skills: list[str] = Field(default_factory=list)
    experience_requirements: list[str] = Field(default_factory=list)
    education_requirements: list[str] = Field(default_factory=list)
    key_responsibilities: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    experience_years: int | None = Field(default=None, ge=0, le=40)
    seniority_level: str | None = None


class JobPostingInput(BaseModel):
    """A real public remote job post (PII-scrubbed) used as an external target for ATS scoring."""

    posting_key: str = Field(min_length=3, max_length=120)
    niche_slug: str = Field(min_length=2, max_length=80)
    title: str = Field(min_length=2, max_length=200)
    employer_type: str = Field(min_length=3, max_length=200)
    platform: JobPlatform
    source_type: JobSourceType = "pasted_text"
    source_url: str | None = Field(default=None, max_length=500)
    remote_setup: str = Field(min_length=2, max_length=160)
    timezone_overlap: str | None = Field(default=None, max_length=160)
    pay_band: str | None = Field(default=None, max_length=160)
    description_text: str = Field(min_length=80)
    keywords: JobKeywordsInput
    captured_on: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    pii_scrubbed: bool = True


class AtsRunInput(BaseModel):
    """A Resume-Matcher result recorded against a resume's target job posting."""

    posting_key: str | None = Field(default=None, max_length=120)
    tool: str = "resume-matcher"
    tool_version: str = Field(min_length=1, max_length=32)
    overall_score: float = Field(ge=0.0, le=100.0)
    sub_scores: dict[str, float] = Field(default_factory=dict)
    missing_keywords: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    parse_check_ok: bool
    parse_score: float | None = Field(default=None, ge=0.0, le=100.0)
    parse_issues: list[str] = Field(default_factory=list)
