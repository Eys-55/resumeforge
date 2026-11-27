"""Typer CLI for ResumeForge SQL operations, ingestion, drafting, auditing, and export."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from resumeforge.config import REPO_ROOT, get_ats_min_score, get_database_url
from resumeforge.db.engine import get_engine, session_scope
from resumeforge.db.migrations_helper import get_db_stats, upgrade_head
from resumeforge.db.models import (
    JobPosting,
    Niche,
    NicheRole,
    ReferencePattern,
    Resume,
    ResumeBullet,
    ResumeCertification,
    ResumeAtsRun,
    ResumeEducation,
    ResumeExperience,
    ResumeLanguage,
    ResumeProject,
    ResumeReview,
    ResumeSkill,
)
from resumeforge.db.seed import seed_initial_niches
from resumeforge.db.views import ensure_views, run_readonly_sql
from resumeforge.schemas import (
    AtsRunInput,
    JobPostingInput,
    NicheCreateInput,
    ReferencePatternInput,
    ResumeDraftInput,
    ResumeReviewInput,
)

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pii_guard import scan_payload  # noqa: E402
from tools.validate_resume import validate_resume_data  # noqa: E402

app = typer.Typer(help="ResumeForge — Philippine Gold-Standard Resume Suite CLI", no_args_is_help=True)
db_app = typer.Typer(help="Database lifecycle and read-only SQL operations", no_args_is_help=True)
niche_app = typer.Typer(help="Philippine job niche and role archetype management", no_args_is_help=True)
pattern_app = typer.Typer(help="Anonymized public resume blueprint management", no_args_is_help=True)
resume_app = typer.Typer(help="Synthetic PH gold-standard resume lifecycle", no_args_is_help=True)
job_app = typer.Typer(help="Real remote job postings used as external ATS targets", no_args_is_help=True)

app.add_typer(db_app, name="db")
app.add_typer(niche_app, name="niche")
app.add_typer(pattern_app, name="pattern")
app.add_typer(resume_app, name="resume")
app.add_typer(job_app, name="job")

from resumeforge.personal import ats_app, mine_app  # noqa: E402

app.add_typer(mine_app, name="mine")
app.add_typer(ats_app, name="ats")

console = Console()
err_console = Console(stderr=True)


def _db_opt(ctx: typer.Context) -> str | None:
    if ctx.obj and isinstance(ctx.obj, dict):
        return ctx.obj.get("db")
    return None


def _read_json_arg(json_arg: str) -> dict[str, Any]:
    raw = sys.stdin.read() if json_arg == "-" else Path(json_arg).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise typer.BadParameter("Expected a JSON object at top level.")
    return data


def _serialize_resume(resume: Resume) -> dict[str, Any]:
    return {
        "resume_code": resume.resume_code,
        "status": resume.status,
        "niche_slug": resume.niche.slug if resume.niche else None,
        "role_slug": resume.niche_role.slug if resume.niche_role else None,
        "pattern_key": resume.reference_pattern.pattern_key if resume.reference_pattern else None,
        "seniority": resume.seniority,
        "target_role_title": resume.target_role_title,
        "layout_archetype": resume.layout_archetype,
        "full_name": resume.full_name,
        "headline": resume.headline,
        "email": resume.email,
        "phone": resume.phone,
        "city": resume.city,
        "region": resume.region,
        "work_setup_preference": resume.work_setup_preference,
        "timezone_readiness": resume.timezone_readiness,
        "expected_salary_php": resume.expected_salary_php,
        "linkedin_slug": resume.linkedin_slug,
        "portfolio_url": resume.portfolio_url,
        "professional_summary": resume.professional_summary,
        "total_years_experience": resume.total_years_experience,
        "variant_of": resume.variant_of_code,
        "quality_score": resume.quality_score,
        "target_job_posting_key": (
            resume.target_job_posting.posting_key if resume.target_job_posting else None
        ),
        "experiences": [
            {
                "company_name": exp.company_name,
                "company_archetype": exp.company_archetype,
                "role_title": exp.role_title,
                "location": exp.location,
                "employment_type": exp.employment_type,
                "start_date": exp.start_date,
                "end_date": exp.end_date,
                "is_current": exp.is_current,
                "bullets": [
                    {
                        "text": b.text,
                        "action_verb": b.action_verb,
                        "metric_value": b.metric_value,
                        "tags": json.loads(b.tags_json),
                    }
                    for b in exp.bullets
                ],
            }
            for exp in resume.experiences
        ],
        "education": [
            {
                "institution": edu.institution,
                "degree": edu.degree,
                "field_of_study": edu.field_of_study,
                "location": edu.location,
                "start_year": edu.start_year,
                "graduation_year": edu.graduation_year,
                "honors": edu.honors,
                "relevant_coursework": json.loads(edu.relevant_coursework_json),
            }
            for edu in resume.education
        ],
        "skills": [
            {
                "category": sk.category,
                "name": sk.name,
                "proficiency": sk.proficiency,
                "years_used": sk.years_used,
            }
            for sk in resume.skills
        ],
        "certifications": [
            {
                "name": cert.name,
                "issuer": cert.issuer,
                "year_earned": cert.year_earned,
                "expiry_year": cert.expiry_year,
                "credential_type": cert.credential_type,
            }
            for cert in resume.certifications
        ],
        "projects": [
            {
                "name": proj.name,
                "role": proj.role,
                "tech_stack": json.loads(proj.tech_stack_json),
                "summary": proj.summary,
                "impact_metric": proj.impact_metric,
                "url": proj.url,
            }
            for proj in resume.projects
        ],
        "languages": [
            {
                "language": lang.language,
                "proficiency": lang.proficiency,
            }
            for lang in resume.languages
        ],
        "reviews": [
            {
                "reviewer_type": rv.reviewer_type,
                "passed": rv.passed,
                "total_score": rv.total_score,
                "max_score": rv.max_score,
                "rubric_scores": json.loads(rv.rubric_scores_json),
                "deterministic_errors": json.loads(rv.deterministic_errors_json),
                "critique_summary": rv.critique_summary,
                "required_fixes": json.loads(rv.required_fixes_json),
            }
            for rv in resume.reviews
        ],
        "ats_runs": [_serialize_ats_run(run) for run in resume.ats_runs],
    }


def _serialize_ats_run(run: ResumeAtsRun) -> dict[str, Any]:
    return {
        "posting_key": run.job_posting.posting_key if run.job_posting else None,
        "tool": run.tool,
        "tool_version": run.tool_version,
        "ats_score": run.ats_score,
        "sub_scores": json.loads(run.sub_scores_json),
        "missing_keywords": json.loads(run.missing_keywords_json),
        "recommendations": json.loads(run.recommendations_json),
        "parse_check_ok": run.parse_check_ok,
        "parse_score": run.parse_score,
        "parse_issues": json.loads(run.parse_issues_json),
        "created_at": run.created_at.isoformat() if run.created_at else None,
    }


def _serialize_job_posting(posting: JobPosting) -> dict[str, Any]:
    return {
        "posting_key": posting.posting_key,
        "niche_slug": posting.niche.slug if posting.niche else None,
        "title": posting.title,
        "employer_type": posting.employer_type,
        "platform": posting.platform,
        "source_type": posting.source_type,
        "source_url": posting.source_url,
        "remote_setup": posting.remote_setup,
        "timezone_overlap": posting.timezone_overlap,
        "pay_band": posting.pay_band,
        "captured_on": posting.captured_on,
        "keywords": json.loads(posting.keywords_json),
        "description_text": posting.description_text,
    }


def _resume_to_markdown(data: dict[str, Any]) -> str:
    city_str = str(data.get("city") or "").strip()
    region_str = str(data.get("region") or "").strip()
    location_display = (
        city_str
        if city_str.lower() == region_str.lower() or not region_str
        else f"{city_str}, {region_str}"
    )
    lines = [
        f"# {data['full_name']} (`{data['resume_code']}`)",
        f"**{data['headline']}**",
        f"{location_display} | {data['email']} | {data['phone']}",
        f"Work Setup: {data['work_setup_preference']} | Timezone: {data['timezone_readiness']} | Status: `{data['status']}`",
        "",
        "## Professional Summary",
        data["professional_summary"],
        "",
        "## Core Skills",
    ]
    by_cat: dict[str, list[str]] = {}
    for sk in data["skills"]:
        by_cat.setdefault(sk["category"], []).append(sk["name"])
    for cat, names in by_cat.items():
        lines.append(f"- **{cat}:** {', '.join(names)}")

    lines.extend(["", "## Experience"])
    for exp in data["experiences"]:
        lines.append(
            f"### {exp['role_title']} — {exp['company_name']} ({exp['start_date']} to {exp['end_date']})"
        )
        lines.append(f"*{exp['location']} · {exp['employment_type']}*")
        for b in exp["bullets"]:
            lines.append(f"- {b['text']}")
        lines.append("")

    if data["projects"]:
        lines.append("## Selected Projects")
        for proj in data["projects"]:
            stack = ", ".join(proj["tech_stack"])
            impact = f" ({proj['impact_metric']})" if proj.get("impact_metric") else ""
            lines.append(f"- **{proj['name']}** [{stack}]: {proj['summary']}{impact}")
        lines.append("")

    lines.append("## Education")
    for edu in data["education"]:
        honors = f" — {edu['honors']}" if edu.get("honors") else ""
        lines.append(f"- **{edu['degree']} in {edu['field_of_study']}**, {edu['institution']} ({edu['graduation_year']}){honors}")

    if data["certifications"]:
        lines.extend(["", "## Certifications"])
        for cert in data["certifications"]:
            lines.append(f"- {cert['name']} — {cert['issuer']} ({cert['year_earned']})")

    if data["languages"]:
        lines.extend(["", "## Languages"])
        for lang in data["languages"]:
            lines.append(f"- {lang['language']}: {lang['proficiency']}")

    return "\n".join(lines).strip() + "\n"


def _load_resume_with_children(session: Any, resume_code: str) -> Resume | None:
    stmt = (
        select(Resume)
        .where(Resume.resume_code == resume_code)
        .options(
            selectinload(Resume.niche),
            selectinload(Resume.niche_role),
            selectinload(Resume.reference_pattern),
            selectinload(Resume.experiences).selectinload(ResumeExperience.bullets),
            selectinload(Resume.education),
            selectinload(Resume.skills),
            selectinload(Resume.certifications),
            selectinload(Resume.projects),
            selectinload(Resume.languages),
            selectinload(Resume.reviews),
            selectinload(Resume.target_job_posting),
            selectinload(Resume.ats_runs).selectinload(ResumeAtsRun.job_posting),
        )
    )
    return session.scalar(stmt)


@app.callback()
def main_callback(
    ctx: typer.Context,
    db: str | None = typer.Option(None, "--db", help="Optional path or URL to SQLite/PostgreSQL database."),
) -> None:
    ctx.ensure_object(dict)
    ctx.obj["db"] = db


# ---------------------------------------------------------------------------
# db commands
# ---------------------------------------------------------------------------


@db_app.command("init")
def db_init(ctx: typer.Context) -> None:
    """Run Alembic migrations, create analytical views, and seed 2026 PH niches."""
    db = _db_opt(ctx)
    upgrade_head(db)
    engine = get_engine(db, read_only=False)
    try:
        ensure_views(engine)
    finally:
        engine.dispose()
    with session_scope(db, read_only=False) as session:
        seeded = seed_initial_niches(session)
    console.print(
        f"[green]Database initialized[/green] at {get_database_url(db)} "
        f"(niches +{seeded['niches_created']}, roles +{seeded['roles_created']})."
    )


@db_app.command("stats")
def db_stats(ctx: typer.Context, as_json: bool = typer.Option(False, "--json", help="Print JSON output.")) -> None:
    """Display row counts across all tables using a strictly read-only connection."""
    db = _db_opt(ctx)
    counts = get_db_stats(db)
    if as_json:
        typer.echo(json.dumps(counts, indent=2))
        return
    table = Table(title="ResumeForge SQL Table Counts")
    table.add_column("Table", style="cyan")
    table.add_column("Rows", justify="right", style="green")
    for k, v in counts.items():
        table.add_row(k, str(v))
    console.print(table)


@db_app.command("sql")
def db_sql(
    ctx: typer.Context,
    query: str = typer.Argument(..., help="Read-only SELECT query to execute."),
    as_json: bool = typer.Option(False, "--json", help="Print rows as JSON."),
) -> None:
    """Execute a strictly read-only SQL query (`mode=ro`, `PRAGMA query_only = ON`)."""
    db = _db_opt(ctx)
    try:
        columns, rows = run_readonly_sql(query, db)
    except Exception as exc:
        err_console.print(f"[red]Read-only SQL query rejected:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    if as_json:
        typer.echo(json.dumps(rows, indent=2, default=str))
        return
    table = Table(title=f"SQL Query Results ({len(rows)} rows)")
    for col in columns:
        table.add_column(col)
    for row in rows:
        table.add_row(*(str(row.get(c, "")) for c in columns))
    console.print(table)


# ---------------------------------------------------------------------------
# niche commands
# ---------------------------------------------------------------------------


@niche_app.command("list")
def niche_list(ctx: typer.Context, as_json: bool = typer.Option(False, "--json")) -> None:
    """List seeded and custom Philippine niches."""
    db = _db_opt(ctx)
    with session_scope(db, read_only=True) as session:
        niches = session.scalars(select(Niche).options(selectinload(Niche.roles)).order_by(Niche.slug)).all()
        payload = [
            {
                "slug": n.slug,
                "name": n.name,
                "market_year": n.market_year,
                "demand_tier": n.demand_tier,
                "role_count": len(n.roles),
            }
            for n in niches
        ]
    if as_json:
        typer.echo(json.dumps(payload, indent=2))
        return
    table = Table(title="Philippine Niches")
    table.add_column("Slug", style="cyan")
    table.add_column("Name")
    table.add_column("Year", justify="center")
    table.add_column("Demand")
    table.add_column("Roles", justify="right")
    for item in payload:
        table.add_row(
            item["slug"], item["name"], str(item["market_year"]), item["demand_tier"], str(item["role_count"])
        )
    console.print(table)


@niche_app.command("show")
def niche_show(ctx: typer.Context, slug: str, as_json: bool = typer.Option(False, "--json")) -> None:
    """Show full specification and role archetypes for a niche."""
    db = _db_opt(ctx)
    with session_scope(db, read_only=True) as session:
        niche = session.scalar(select(Niche).where(Niche.slug == slug).options(selectinload(Niche.roles)))
        if niche is None:
            err_console.print(f"[red]Niche not found:[/red] {slug}")
            raise typer.Exit(code=1)
        data = {
            "slug": niche.slug,
            "name": niche.name,
            "description": niche.description,
            "market_year": niche.market_year,
            "demand_tier": niche.demand_tier,
            "ph_market_notes": niche.ph_market_notes,
            "roles": [
                {
                    "slug": r.slug,
                    "title": r.title,
                    "seniority_band": r.seniority_band,
                    "salary_php_min": r.salary_php_min,
                    "salary_php_max": r.salary_php_max,
                    "work_setup": json.loads(r.work_setup_json),
                    "required_skills": json.loads(r.required_skills_json),
                    "trending_tools": json.loads(r.trending_tools_json),
                    "common_certs": json.loads(r.common_certs_json),
                    "typical_kpis": json.loads(r.typical_kpis_json),
                }
                for r in niche.roles
            ],
        }
    if as_json:
        typer.echo(json.dumps(data, indent=2))
        return
    console.print(f"[bold cyan]{data['name']}[/bold cyan] ({data['slug']}, {data['market_year']})")
    console.print(data["description"])
    if data["ph_market_notes"]:
        console.print(f"[dim]Market notes:[/dim] {data['ph_market_notes']}")
    table = Table(title="Role Archetypes")
    table.add_column("Role Slug", style="cyan")
    table.add_column("Title")
    table.add_column("Seniority")
    table.add_column("PHP Salary Band")
    for r in data["roles"]:
        table.add_row(
            r["slug"],
            r["title"],
            r["seniority_band"],
            f"PHP {r['salary_php_min']:,} - {r['salary_php_max']:,}",
        )
    console.print(table)


@niche_app.command("add")
def niche_add(ctx: typer.Context, json_path: str = typer.Option(..., "--json", help="JSON file or '-' for stdin.")) -> None:
    """Create or update a Philippine niche and its role archetypes."""
    db = _db_opt(ctx)
    data = NicheCreateInput.model_validate(_read_json_arg(json_path))
    with session_scope(db, read_only=False) as session:
        niche = session.scalar(select(Niche).where(Niche.slug == data.slug))
        if niche is None:
            niche = Niche(
                slug=data.slug,
                name=data.name,
                description=data.description,
                market_year=data.market_year,
                demand_tier=data.demand_tier,
                ph_market_notes=data.ph_market_notes,
            )
            session.add(niche)
            session.flush()
        else:
            niche.name = data.name
            niche.description = data.description
            niche.market_year = data.market_year
            niche.demand_tier = data.demand_tier
            niche.ph_market_notes = data.ph_market_notes

        for r in data.roles:
            role = session.scalar(select(NicheRole).where(NicheRole.slug == r.slug))
            if role is None:
                role = NicheRole(
                    niche_id=niche.id,
                    slug=r.slug,
                    title=r.title,
                    seniority_band=r.seniority_band,
                    salary_php_min=r.salary_php_min,
                    salary_php_max=r.salary_php_max,
                    work_setup_json=json.dumps(r.work_setup),
                    required_skills_json=json.dumps(r.required_skills),
                    trending_tools_json=json.dumps(r.trending_tools),
                    common_certs_json=json.dumps(r.common_certs),
                    typical_kpis_json=json.dumps(r.typical_kpis),
                )
                session.add(role)
            else:
                role.niche_id = niche.id
                role.title = r.title
                role.seniority_band = r.seniority_band
                role.salary_php_min = r.salary_php_min
                role.salary_php_max = r.salary_php_max
                role.work_setup_json = json.dumps(r.work_setup)
                role.required_skills_json = json.dumps(r.required_skills)
                role.trending_tools_json = json.dumps(r.trending_tools)
                role.common_certs_json = json.dumps(r.common_certs)
                role.typical_kpis_json = json.dumps(r.typical_kpis)
    console.print(f"[green]Upserted niche[/green] {data.slug} with {len(data.roles)} role(s).")


# ---------------------------------------------------------------------------
# pattern commands
# ---------------------------------------------------------------------------


@pattern_app.command("add")
def pattern_add(ctx: typer.Context, json_path: str = typer.Option(..., "--json", help="JSON file or '-' for stdin.")) -> None:
    """Ingest an anonymized reference pattern after passing the hard PII firewall."""
    db = _db_opt(ctx)
    raw_dict = _read_json_arg(json_path)
    model = ReferencePatternInput.model_validate(raw_dict)

    scan = scan_payload(raw_dict, mode="pattern")
    if not scan.clean:
        err_console.print("[red]Blocked by pii_guard (pattern mode):[/red]")
        for f in scan.findings:
            err_console.print(f"  - [{f['category']}] {f['field']}: {f['detail']}")
        raise typer.Exit(code=1)

    with session_scope(db, read_only=False) as session:
        niche = session.scalar(select(Niche).where(Niche.slug == model.niche_slug))
        if niche is None:
            err_console.print(f"[red]Unknown niche_slug:[/red] {model.niche_slug}")
            raise typer.Exit(code=1)
        existing = session.scalar(select(ReferencePattern).where(ReferencePattern.pattern_key == model.pattern_key))
        if existing is not None:
            err_console.print(f"[red]pattern_key already exists:[/red] {model.pattern_key}")
            raise typer.Exit(code=1)

        pattern = ReferencePattern(
            pattern_key=model.pattern_key,
            niche_id=niche.id,
            source_label=model.source_label,
            source_type=model.source_type,
            seniority_observed=model.seniority_observed,
            layout_archetype=model.layout_archetype,
            section_order_json=json.dumps(model.section_order),
            ph_conventions_json=json.dumps(model.ph_conventions),
            metric_patterns_json=json.dumps(model.metric_patterns),
            tool_clusters_json=json.dumps(model.tool_clusters),
            career_arc_summary=model.career_arc_summary,
            strengths_notes=model.strengths_notes,
            modernization_notes=model.modernization_notes,
            pii_scrubbed=True,
        )
        session.add(pattern)

    console.print(f"[green]Stored anonymized reference pattern:[/green] {model.pattern_key} ({model.niche_slug})")


@pattern_app.command("list")
def pattern_list(
    ctx: typer.Context,
    niche: str | None = typer.Option(None, "--niche", help="Filter by niche slug."),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """List ingested anonymized reference patterns."""
    db = _db_opt(ctx)
    with session_scope(db, read_only=True) as session:
        stmt = (
            select(ReferencePattern)
            .join(Niche)
            .options(selectinload(ReferencePattern.niche))
            .order_by(ReferencePattern.id.desc())
        )
        if niche:
            stmt = stmt.where(Niche.slug == niche)
        rows = session.scalars(stmt).all()
        payload = [
            {
                "pattern_key": p.pattern_key,
                "niche_slug": p.niche.slug,
                "source_type": p.source_type,
                "seniority_observed": p.seniority_observed,
                "layout_archetype": p.layout_archetype,
                "source_label": p.source_label,
            }
            for p in rows
        ]
    if as_json:
        typer.echo(json.dumps(payload, indent=2))
        return
    table = Table(title="Anonymized Reference Patterns")
    table.add_column("Pattern Key", style="cyan")
    table.add_column("Niche")
    table.add_column("Source Type")
    table.add_column("Seniority")
    table.add_column("Layout")
    for p in payload:
        table.add_row(p["pattern_key"], p["niche_slug"], p["source_type"], p["seniority_observed"], p["layout_archetype"])
    console.print(table)


@pattern_app.command("show")
def pattern_show(ctx: typer.Context, pattern_key: str) -> None:
    """Inspect a stored anonymized reference pattern as JSON."""
    db = _db_opt(ctx)
    with session_scope(db, read_only=True) as session:
        p = session.scalar(
            select(ReferencePattern)
            .where(ReferencePattern.pattern_key == pattern_key)
            .options(selectinload(ReferencePattern.niche))
        )
        if p is None:
            err_console.print(f"[red]Pattern not found:[/red] {pattern_key}")
            raise typer.Exit(code=1)
        data = {
            "pattern_key": p.pattern_key,
            "niche_slug": p.niche.slug,
            "source_label": p.source_label,
            "source_type": p.source_type,
            "seniority_observed": p.seniority_observed,
            "layout_archetype": p.layout_archetype,
            "section_order": json.loads(p.section_order_json),
            "ph_conventions": json.loads(p.ph_conventions_json),
            "metric_patterns": json.loads(p.metric_patterns_json),
            "tool_clusters": json.loads(p.tool_clusters_json),
            "career_arc_summary": p.career_arc_summary,
            "strengths_notes": p.strengths_notes,
            "modernization_notes": p.modernization_notes,
            "pii_scrubbed": p.pii_scrubbed,
        }
    typer.echo(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# job posting commands
# ---------------------------------------------------------------------------


@job_app.command("add")
def job_add(ctx: typer.Context, json_path: str = typer.Option(..., "--json", help="JSON file or '-' for stdin.")) -> None:
    """Store a real, PII-scrubbed remote job post plus its extracted ATS keywords."""
    db = _db_opt(ctx)
    raw_dict = _read_json_arg(json_path)
    model = JobPostingInput.model_validate(raw_dict)

    scan = scan_payload(raw_dict, mode="pattern")
    if not scan.clean:
        err_console.print("[red]Blocked by pii_guard (job posting):[/red]")
        for f in scan.findings:
            err_console.print(f"  - [{f['category']}] {f['field']}: {f['detail']}")
        raise typer.Exit(code=1)

    with session_scope(db, read_only=False) as session:
        niche = session.scalar(select(Niche).where(Niche.slug == model.niche_slug))
        if niche is None:
            err_console.print(f"[red]Unknown niche_slug:[/red] {model.niche_slug}")
            raise typer.Exit(code=1)
        if session.scalar(select(JobPosting).where(JobPosting.posting_key == model.posting_key)) is not None:
            err_console.print(f"[red]posting_key already exists:[/red] {model.posting_key}")
            raise typer.Exit(code=1)
        session.add(
            JobPosting(
                posting_key=model.posting_key,
                niche_id=niche.id,
                title=model.title,
                employer_type=model.employer_type,
                platform=model.platform,
                source_type=model.source_type,
                source_url=model.source_url,
                remote_setup=model.remote_setup,
                timezone_overlap=model.timezone_overlap,
                pay_band=model.pay_band,
                description_text=model.description_text,
                keywords_json=json.dumps(model.keywords.model_dump()),
                captured_on=model.captured_on,
                pii_scrubbed=True,
            )
        )

    console.print(f"[green]Stored job posting:[/green] {model.posting_key} ({model.platform}, {model.niche_slug})")


@job_app.command("list")
def job_list(
    ctx: typer.Context,
    niche: str | None = typer.Option(None, "--niche", help="Filter by niche slug."),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """List stored remote job postings."""
    db = _db_opt(ctx)
    with session_scope(db, read_only=True) as session:
        stmt = select(JobPosting).join(Niche).options(selectinload(JobPosting.niche)).order_by(JobPosting.id.desc())
        if niche:
            stmt = stmt.where(Niche.slug == niche)
        payload = [
            {
                "posting_key": jp.posting_key,
                "niche_slug": jp.niche.slug,
                "title": jp.title,
                "platform": jp.platform,
                "employer_type": jp.employer_type,
                "captured_on": jp.captured_on,
            }
            for jp in session.scalars(stmt).all()
        ]
    if as_json:
        typer.echo(json.dumps(payload, indent=2))
        return
    table = Table(title="Remote Job Postings")
    table.add_column("Posting Key", style="cyan")
    table.add_column("Niche")
    table.add_column("Title")
    table.add_column("Platform")
    table.add_column("Captured")
    for jp in payload:
        table.add_row(jp["posting_key"], jp["niche_slug"], jp["title"], jp["platform"], jp["captured_on"])
    console.print(table)


@job_app.command("show")
def job_show(ctx: typer.Context, posting_key: str) -> None:
    """Inspect a stored job posting (including extracted keywords) as JSON."""
    db = _db_opt(ctx)
    with session_scope(db, read_only=True) as session:
        jp = session.scalar(
            select(JobPosting).where(JobPosting.posting_key == posting_key).options(selectinload(JobPosting.niche))
        )
        if jp is None:
            err_console.print(f"[red]Job posting not found:[/red] {posting_key}")
            raise typer.Exit(code=1)
        data = _serialize_job_posting(jp)
    typer.echo(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# resume commands
# ---------------------------------------------------------------------------


def _replace_resume_children(
    resume: Resume,
    model: ResumeDraftInput,
    *,
    session: Any | None = None,
) -> None:
    resume.experiences.clear()
    resume.education.clear()
    resume.skills.clear()
    resume.certifications.clear()
    resume.projects.clear()
    resume.languages.clear()
    if session is not None:
        session.flush()

    for idx, exp_in in enumerate(model.experiences):
        exp = ResumeExperience(
            company_name=exp_in.company_name,
            company_archetype=exp_in.company_archetype,
            role_title=exp_in.role_title,
            location=exp_in.location,
            employment_type=exp_in.employment_type,
            start_date=exp_in.start_date,
            end_date=exp_in.end_date,
            is_current=exp_in.is_current,
            sort_order=idx,
        )
        for b_idx, b_in in enumerate(exp_in.bullets):
            exp.bullets.append(
                ResumeBullet(
                    text=b_in.text,
                    action_verb=b_in.action_verb,
                    metric_value=b_in.metric_value,
                    tags_json=json.dumps(b_in.tags),
                    sort_order=b_idx,
                )
            )
        resume.experiences.append(exp)

    for idx, edu_in in enumerate(model.education):
        resume.education.append(
            ResumeEducation(
                institution=edu_in.institution,
                degree=edu_in.degree,
                field_of_study=edu_in.field_of_study,
                location=edu_in.location,
                start_year=edu_in.start_year,
                graduation_year=edu_in.graduation_year,
                honors=edu_in.honors,
                relevant_coursework_json=json.dumps(edu_in.relevant_coursework),
                sort_order=idx,
            )
        )

    for idx, sk_in in enumerate(model.skills):
        resume.skills.append(
            ResumeSkill(
                category=sk_in.category,
                name=sk_in.name,
                proficiency=sk_in.proficiency,
                years_used=sk_in.years_used,
                sort_order=idx,
            )
        )

    for idx, cert_in in enumerate(model.certifications):
        resume.certifications.append(
            ResumeCertification(
                name=cert_in.name,
                issuer=cert_in.issuer,
                year_earned=cert_in.year_earned,
                expiry_year=cert_in.expiry_year,
                credential_type=cert_in.credential_type,
                sort_order=idx,
            )
        )

    for idx, proj_in in enumerate(model.projects):
        resume.projects.append(
            ResumeProject(
                name=proj_in.name,
                role=proj_in.role,
                tech_stack_json=json.dumps(proj_in.tech_stack),
                summary=proj_in.summary,
                impact_metric=proj_in.impact_metric,
                url=proj_in.url,
                sort_order=idx,
            )
        )

    for idx, lang_in in enumerate(model.languages):
        resume.languages.append(
            ResumeLanguage(
                language=lang_in.language,
                proficiency=lang_in.proficiency,
                sort_order=idx,
            )
        )


@resume_app.command("import")
def resume_import(
    ctx: typer.Context,
    json_path: str = typer.Option(..., "--json", help="JSON file path or '-' for stdin."),
    update: bool = typer.Option(False, "--update", help="Update an existing resume_code in place (resets status to draft)."),
) -> None:
    """Validate and import a structured synthetic PH resume into SQL as `draft`."""
    db = _db_opt(ctx)
    raw_dict = _read_json_arg(json_path)
    model = ResumeDraftInput.model_validate(raw_dict)

    with session_scope(db, read_only=False) as session:
        niche = session.scalar(select(Niche).where(Niche.slug == model.niche_slug))
        if niche is None:
            err_console.print(f"[red]Unknown niche_slug:[/red] {model.niche_slug}")
            raise typer.Exit(code=1)

        role_id: int | None = None
        if model.role_slug:
            role = session.scalar(select(NicheRole).where(NicheRole.slug == model.role_slug))
            if role is None:
                err_console.print(f"[red]Unknown role_slug:[/red] {model.role_slug}")
                raise typer.Exit(code=1)
            role_id = role.id

        pattern_id: int | None = None
        if model.pattern_key:
            pattern = session.scalar(
                select(ReferencePattern).where(ReferencePattern.pattern_key == model.pattern_key)
            )
            if pattern is None:
                err_console.print(f"[red]Unknown pattern_key:[/red] {model.pattern_key}")
                raise typer.Exit(code=1)
            pattern_id = pattern.id

        target_posting_id: int | None = None
        if model.target_job_posting_key:
            posting = session.scalar(
                select(JobPosting).where(JobPosting.posting_key == model.target_job_posting_key)
            )
            if posting is None:
                err_console.print(f"[red]Unknown target_job_posting_key:[/red] {model.target_job_posting_key}")
                raise typer.Exit(code=1)
            target_posting_id = posting.id

        existing = _load_resume_with_children(session, model.resume_code)
        if existing is not None and not update:
            err_console.print(
                f"[red]Resume {model.resume_code} already exists.[/red] Pass --update to replace its draft."
            )
            raise typer.Exit(code=1)
        if existing is None and update:
            err_console.print(f"[red]Cannot --update missing resume:[/red] {model.resume_code}")
            raise typer.Exit(code=1)

        if model.variant_of:
            if model.variant_of == model.resume_code:
                err_console.print(f"[red]A resume cannot be a variant of itself:[/red] {model.resume_code}")
                raise typer.Exit(code=1)
            parent = session.scalar(select(Resume).where(Resume.resume_code == model.variant_of))
            if parent is None:
                err_console.print(f"[red]Unknown variant_of resume_code:[/red] {model.variant_of}")
                raise typer.Exit(code=1)

        val = validate_resume_data(
            model.model_dump(),
            session=session,
            exclude_resume_code=model.resume_code if update else None,
        )
        if not val.valid:
            err_console.print(f"[red]Validation failed for {model.resume_code}:[/red]")
            for err in val.errors:
                err_console.print(f"  - {err}")
            raise typer.Exit(code=1)

        if existing is None:
            resume = Resume(
                resume_code=model.resume_code,
                niche_id=niche.id,
                niche_role_id=role_id,
                reference_pattern_id=pattern_id,
                target_job_posting_id=target_posting_id,
                status="draft",
                seniority=model.seniority,
                target_role_title=model.target_role_title,
                layout_archetype=model.layout_archetype,
                full_name=model.full_name,
                headline=model.headline,
                email=model.email,
                phone=model.phone,
                city=model.city,
                region=model.region,
                work_setup_preference=model.work_setup_preference,
                timezone_readiness=model.timezone_readiness,
                expected_salary_php=model.expected_salary_php,
                linkedin_slug=model.linkedin_slug,
                portfolio_url=model.portfolio_url,
                professional_summary=model.professional_summary,
                total_years_experience=model.total_years_experience,
                variant_of_code=model.variant_of,
                quality_score=None,
            )
            _replace_resume_children(resume, model)
            session.add(resume)
        else:
            existing.niche_id = niche.id
            existing.niche_role_id = role_id
            existing.reference_pattern_id = pattern_id
            existing.target_job_posting_id = target_posting_id
            existing.status = "draft"
            existing.seniority = model.seniority
            existing.target_role_title = model.target_role_title
            existing.layout_archetype = model.layout_archetype
            existing.full_name = model.full_name
            existing.headline = model.headline
            existing.email = model.email
            existing.phone = model.phone
            existing.city = model.city
            existing.region = model.region
            existing.work_setup_preference = model.work_setup_preference
            existing.timezone_readiness = model.timezone_readiness
            existing.expected_salary_php = model.expected_salary_php
            existing.linkedin_slug = model.linkedin_slug
            existing.portfolio_url = model.portfolio_url
            existing.professional_summary = model.professional_summary
            existing.total_years_experience = model.total_years_experience
            existing.variant_of_code = model.variant_of
            existing.quality_score = None
            _replace_resume_children(existing, model, session=session)

    console.print(
        f"[green]{'Updated' if update else 'Imported'} resume[/green] {model.resume_code} "
        f"as [yellow]draft[/yellow] (quantified={val.metrics['quantified_ratio']:.0%}, "
        f"skill_evidence={val.metrics['skill_evidence_ratio']:.0%})."
    )


@resume_app.command("validate")
def resume_validate(ctx: typer.Context, resume_code: str, as_json: bool = typer.Option(False, "--json")) -> None:
    """Re-run deterministic validation on a stored resume."""
    db = _db_opt(ctx)
    with session_scope(db, read_only=True) as session:
        resume = _load_resume_with_children(session, resume_code)
        if resume is None:
            err_console.print(f"[red]Resume not found:[/red] {resume_code}")
            raise typer.Exit(code=1)
        data = _serialize_resume(resume)
        result = validate_resume_data(data, session=session, exclude_resume_code=resume_code)

    if as_json:
        typer.echo(json.dumps(result.to_dict(), indent=2))
    else:
        if result.valid:
            console.print(f"[green]VALID[/green]: {resume_code} ({result.metrics})")
        else:
            err_console.print(f"[red]INVALID[/red]: {resume_code}")
            for err in result.errors:
                err_console.print(f"  - {err}")

    if not result.valid:
        raise typer.Exit(code=1)


def _ats_gate(resume: Resume) -> tuple[bool, str]:
    """ATS gate: the latest ATS run against the target posting must clear the threshold."""
    if resume.target_job_posting_id is None:
        return False, "no target job posting"
    runs = [r for r in resume.ats_runs if r.job_posting_id == resume.target_job_posting_id]
    if not runs:
        return False, "no ATS run against target posting"
    latest = max(runs, key=lambda r: r.id)
    threshold = get_ats_min_score()
    if latest.ats_score < threshold:
        return False, f"ATS {latest.ats_score:.1f} < {threshold:.0f}"
    if not latest.parse_check_ok:
        return False, "PDF parse check failed"
    return True, f"ATS {latest.ats_score:.1f} ok"


def _store_ats_run(session: Any, resume: Resume, posting: JobPosting, run_in: AtsRunInput) -> ResumeAtsRun:
    row = ResumeAtsRun(
        resume_id=resume.id,
        job_posting_id=posting.id,
        tool=run_in.tool,
        tool_version=run_in.tool_version,
        ats_score=run_in.overall_score,
        sub_scores_json=json.dumps(run_in.sub_scores),
        missing_keywords_json=json.dumps(run_in.missing_keywords),
        recommendations_json=json.dumps(run_in.recommendations),
        parse_check_ok=run_in.parse_check_ok,
        parse_score=run_in.parse_score,
        parse_issues_json=json.dumps(run_in.parse_issues),
    )
    session.add(row)
    return row


def _resolve_ats_posting(session: Any, resume: Resume, posting_key: str | None) -> JobPosting:
    if posting_key:
        posting = session.scalar(select(JobPosting).where(JobPosting.posting_key == posting_key))
        if posting is None:
            err_console.print(f"[red]Job posting not found:[/red] {posting_key}")
            raise typer.Exit(code=1)
        return posting
    if resume.target_job_posting is None:
        err_console.print(
            f"[red]{resume.resume_code} has no target_job_posting_key.[/red] Set it on import or pass --posting."
        )
        raise typer.Exit(code=1)
    return resume.target_job_posting


def _print_ats_result(resume_code: str, payload: dict[str, Any]) -> None:
    threshold = get_ats_min_score()
    score = payload["ats_score"]
    color = "green" if score >= threshold and payload["parse_check_ok"] else "yellow"
    console.print(
        f"[{color}]ATS {score:.1f}/100[/{color}] for {resume_code} vs {payload['posting_key']} "
        f"(threshold {threshold:.0f}; parse check {'ok' if payload['parse_check_ok'] else 'FAILED'})"
    )
    if payload["sub_scores"]:
        console.print("  sub-scores: " + ", ".join(f"{k}={v}" for k, v in payload["sub_scores"].items()))
    if payload["missing_keywords"]:
        console.print("  missing keywords: " + ", ".join(payload["missing_keywords"]))
    for rec in payload["recommendations"]:
        console.print(f"  - {rec}")
    for issue in payload["parse_issues"]:
        console.print(f"  ! parse: {issue}")


@resume_app.command("ats-record")
def resume_ats_record(
    ctx: typer.Context,
    resume_code: str,
    json_path: str = typer.Option(..., "--json", help="AtsRunInput JSON file or '-' for stdin."),
) -> None:
    """Record an externally computed Resume-Matcher result for a resume."""
    db = _db_opt(ctx)
    run_in = AtsRunInput.model_validate(_read_json_arg(json_path))
    with session_scope(db, read_only=False) as session:
        resume = _load_resume_with_children(session, resume_code)
        if resume is None:
            err_console.print(f"[red]Resume not found:[/red] {resume_code}")
            raise typer.Exit(code=1)
        posting = _resolve_ats_posting(session, resume, run_in.posting_key)
        row = _store_ats_run(session, resume, posting, run_in)
        session.flush()
        payload = _serialize_ats_run(row)
    _print_ats_result(resume_code, payload)


@resume_app.command("ats-check")
def resume_ats_check(
    ctx: typer.Context,
    resume_code: str,
    posting: str | None = typer.Option(None, "--posting", help="Posting key (defaults to the resume's target)."),
    one_page: bool = typer.Option(False, "--one-page", help="Parse-check the compact 1-page PDF layout."),
    engine: str = typer.Option(
        "auto", "--engine", help="auto (Resume-Matcher if installed, else built-in), builtin, or resume-matcher."
    ),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """ATS-score a resume against its target job post, parse-check the rendered PDF, and record the run."""
    import tempfile

    from tools import ats_local
    from tools.ats_bridge import resume_matcher_available
    from tools.render_pdf import render_resume_pdf

    if engine not in {"auto", "builtin", "resume-matcher"}:
        err_console.print(f"[red]Unknown --engine {engine!r}[/red]")
        raise typer.Exit(code=1)
    use_rm = engine == "resume-matcher" or (engine == "auto" and resume_matcher_available())

    db = _db_opt(ctx)
    with session_scope(db, read_only=True) as session:
        resume = _load_resume_with_children(session, resume_code)
        if resume is None:
            err_console.print(f"[red]Resume not found:[/red] {resume_code}")
            raise typer.Exit(code=1)
        target = _resolve_ats_posting(session, resume, posting)
        posting_key = target.posting_key
        keywords = json.loads(target.keywords_json)
        data = _serialize_resume(resume)

    if not use_rm:
        try:
            score = ats_local.score(data, keywords)
            with tempfile.TemporaryDirectory(prefix="resumeforge-ats-") as tmp:
                pdf_path = render_resume_pdf(
                    resume_code, Path(tmp) / f"{resume_code}.pdf", db_url=db, one_page=one_page
                )
                parse = ats_local.parse_check(pdf_path, expected_name=data["full_name"])
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            err_console.print(f"[red]ATS check failed:[/red] {exc}")
            raise typer.Exit(code=1) from exc
        run_in = AtsRunInput(
            posting_key=posting_key,
            tool=ats_local.ENGINE_NAME,
            tool_version=ats_local.ENGINE_VERSION,
            overall_score=score["overall_score"],
            sub_scores=score["sub_scores"],
            missing_keywords=score["missing_keywords"],
            recommendations=score["recommendations"],
            parse_check_ok=parse["parse_check_ok"],
            parse_score=parse["parse_score"],
            parse_issues=parse["parse_issues"],
        )
    else:
        run_in = _resume_matcher_run(resume_code, data, keywords, posting_key, db, one_page)

    with session_scope(db, read_only=False) as session:
        resume = _load_resume_with_children(session, resume_code)
        assert resume is not None
        target = session.scalar(select(JobPosting).where(JobPosting.posting_key == posting_key))
        row = _store_ats_run(session, resume, target, run_in)
        session.flush()
        payload = _serialize_ats_run(row)

    if as_json:
        typer.echo(json.dumps(payload, indent=2))
    else:
        _print_ats_result(resume_code, payload)


def _resume_matcher_run(
    resume_code: str, data: dict[str, Any], keywords: dict[str, Any], posting_key: str, db: str | None, one_page: bool
) -> AtsRunInput:
    """Score with an external Resume-Matcher install (optional; see docs/optional-resume-matcher.md)."""
    import tempfile

    from tools.ats_bridge import ResumeMatcherError, parse_check_pdf, score_resume, tool_version
    from tools.render_pdf import render_resume_pdf

    try:
        score = score_resume(data, keywords)
        with tempfile.TemporaryDirectory(prefix="resumeforge-ats-") as tmp:
            pdf_path = render_resume_pdf(
                resume_code, Path(tmp) / f"{resume_code}.pdf", db_url=db, one_page=one_page
            )
            parse = parse_check_pdf(pdf_path)
        version = tool_version()
    except (ResumeMatcherError, RuntimeError, ValueError) as exc:
        err_console.print(f"[red]ATS check failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    failed_checks = [c for c in parse.get("checks", []) if c.get("status") != "pass"]
    parse_ok = parse.get("extractability") == "full" and not any(
        c.get("severity") == "high" for c in failed_checks
    )
    run_in = AtsRunInput(
        posting_key=posting_key,
        tool_version=version,
        overall_score=float(score.get("overall_score", 0.0)),
        sub_scores={k: float(v) for k, v in (score.get("sub_scores") or {}).items() if v is not None},
        missing_keywords=list(score.get("missing_keywords") or []),
        recommendations=list(score.get("recommendations") or []),
        parse_check_ok=parse_ok,
        parse_score=float(parse["overall_score"]) if parse.get("overall_score") is not None else None,
        parse_issues=[f"{c.get('id')} ({c.get('severity')}): {c.get('status')}" for c in failed_checks],
    )
    return run_in


@resume_app.command("review")
def resume_review(
    ctx: typer.Context,
    resume_code: str,
    json_path: str = typer.Option(..., "--json", help="Review audit JSON file or '-' for stdin."),
) -> None:
    """Record an independent audit and promote to `gold_standard` only if all gates pass."""
    db = _db_opt(ctx)
    review_in = ResumeReviewInput.model_validate(_read_json_arg(json_path))
    total_score = sum(int(v) for v in review_in.rubric_scores.values())
    min_dim = min(int(v) for v in review_in.rubric_scores.values())

    with session_scope(db, read_only=False) as session:
        resume = _load_resume_with_children(session, resume_code)
        if resume is None:
            err_console.print(f"[red]Resume not found:[/red] {resume_code}")
            raise typer.Exit(code=1)

        data = _serialize_resume(resume)
        live_val = validate_resume_data(data, session=session, exclude_resume_code=resume_code)

        ats_ok, ats_reason = _ats_gate(resume)
        gate_passed = (
            bool(review_in.passed)
            and total_score >= 30
            and min_dim >= 4
            and live_val.valid
            and ats_ok
        )
        new_status = "gold_standard" if gate_passed else "needs_revision"

        review_row = ResumeReview(
            resume_id=resume.id,
            reviewer_type=review_in.reviewer_type,
            passed=gate_passed,
            total_score=total_score,
            max_score=35,
            rubric_scores_json=json.dumps(review_in.rubric_scores),
            deterministic_errors_json=json.dumps(live_val.errors),
            critique_summary=review_in.critique_summary,
            required_fixes_json=json.dumps(review_in.required_fixes),
        )
        session.add(review_row)
        resume.status = new_status
        resume.quality_score = total_score

    if gate_passed:
        console.print(
            f"[green]PROMOTED to gold_standard:[/green] {resume_code} (score {total_score}/35, min dimension {min_dim}/5)."
        )
    else:
        console.print(
            f"[yellow]Marked needs_revision:[/yellow] {resume_code} "
            f"(score {total_score}/35, min_dim={min_dim}, deterministic_errors={len(live_val.errors)}, "
            f"ats={ats_reason})."
        )


@resume_app.command("list")
def resume_list(
    ctx: typer.Context,
    niche: str | None = typer.Option(None, "--niche", help="Filter by niche slug."),
    seniority: str | None = typer.Option(None, "--seniority", help="Filter by seniority band."),
    status: str | None = typer.Option(None, "--status", help="Filter by status."),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """List resumes in SQL."""
    db = _db_opt(ctx)
    with session_scope(db, read_only=True) as session:
        stmt = (
            select(Resume)
            .join(Niche)
            .options(selectinload(Resume.niche))
            .order_by(Resume.id.desc())
        )
        if niche:
            stmt = stmt.where(Niche.slug == niche)
        if seniority:
            stmt = stmt.where(Resume.seniority == seniority)
        if status:
            stmt = stmt.where(Resume.status == status)
        rows = session.scalars(stmt).all()
        payload = [
            {
                "resume_code": r.resume_code,
                "status": r.status,
                "niche_slug": r.niche.slug,
                "seniority": r.seniority,
                "full_name": r.full_name,
                "target_role_title": r.target_role_title,
                "city": r.city,
                "quality_score": r.quality_score,
            }
            for r in rows
        ]
    if as_json:
        typer.echo(json.dumps(payload, indent=2))
        return
    table = Table(title="Resumes")
    table.add_column("Code", style="cyan")
    table.add_column("Status")
    table.add_column("Niche")
    table.add_column("Seniority")
    table.add_column("Persona")
    table.add_column("Role")
    table.add_column("City")
    table.add_column("Score", justify="right")
    for r in payload:
        table.add_row(
            r["resume_code"],
            r["status"],
            r["niche_slug"],
            r["seniority"],
            r["full_name"],
            r["target_role_title"],
            r["city"],
            str(r["quality_score"]) if r["quality_score"] is not None else "-",
        )
    console.print(table)


@resume_app.command("show")
def resume_show(
    ctx: typer.Context,
    resume_code: str,
    as_json: bool = typer.Option(False, "--json", help="Print structured JSON instead of Markdown."),
) -> None:
    """Display a stored resume in full detail."""
    db = _db_opt(ctx)
    with session_scope(db, read_only=True) as session:
        resume = _load_resume_with_children(session, resume_code)
        if resume is None:
            err_console.print(f"[red]Resume not found:[/red] {resume_code}")
            raise typer.Exit(code=1)
        data = _serialize_resume(resume)
    if as_json:
        typer.echo(json.dumps(data, indent=2))
    else:
        typer.echo(_resume_to_markdown(data))


@resume_app.command("export")
def resume_export(
    ctx: typer.Context,
    status: str = typer.Option("gold_standard", "--status", help="Status filter (or 'all')."),
    niche: str | None = typer.Option(None, "--niche", help="Optional niche slug filter."),
    seniority: str | None = typer.Option(None, "--seniority", help="Optional seniority filter."),
    fmt: str = typer.Option("json", "--format", help="Output format: json, jsonl, or md."),
    out: str | None = typer.Option(None, "--out", help="Optional file path to write output."),
) -> None:
    """Export resumes from SQL in read-only mode for game ingestion."""
    if fmt not in {"json", "jsonl", "md"}:
        raise typer.BadParameter("--format must be one of: json, jsonl, md")
    db = _db_opt(ctx)
    with session_scope(db, read_only=True) as session:
        stmt = (
            select(Resume)
            .join(Niche)
            .options(
                selectinload(Resume.niche),
                selectinload(Resume.niche_role),
                selectinload(Resume.reference_pattern),
                selectinload(Resume.experiences).selectinload(ResumeExperience.bullets),
                selectinload(Resume.education),
                selectinload(Resume.skills),
                selectinload(Resume.certifications),
                selectinload(Resume.projects),
                selectinload(Resume.languages),
                selectinload(Resume.reviews),
            )
            .order_by(Resume.resume_code)
        )
        if status != "all":
            stmt = stmt.where(Resume.status == status)
        if niche:
            stmt = stmt.where(Niche.slug == niche)
        if seniority:
            stmt = stmt.where(Resume.seniority == seniority)
        records = [_serialize_resume(r) for r in session.scalars(stmt).all()]

    if fmt == "json":
        rendered = json.dumps(records, indent=2)
    elif fmt == "jsonl":
        rendered = "\n".join(json.dumps(item) for item in records) + ("\n" if records else "")
    else:
        rendered = "\n---\n\n".join(_resume_to_markdown(item) for item in records)

    if out:
        out_path = Path(out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")
        console.print(f"[green]Exported {len(records)} resume(s)[/green] to {out_path}")
    else:
        typer.echo(rendered)
