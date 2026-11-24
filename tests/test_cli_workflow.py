"""End-to-end CLI workflow tests (`db init` -> `pattern add` -> `resume import` -> `review` -> `sql`)."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from resumeforge.cli import app

runner = CliRunner()


def _sample_pattern(with_pii: bool = False) -> dict:
    return {
        "pattern_key": "ph-tech-ai-mid-chat-01",
        "niche_slug": "tech-ai-automation",
        "source_label": "chat-2026-11-23-01",
        "source_type": "pasted_text",
        "seniority_observed": "mid",
        "layout_archetype": "single-column-ats",
        "section_order": ["Header", "Summary", "Skills", "Experience", "Education"],
        "ph_conventions": ["City/Region header", "Timezone overlap badge"],
        "metric_patterns": ["Reduced <task> hours by <X>/wk via n8n"],
        "tool_clusters": {"automation": ["n8n", "Python", "FastAPI"]},
        "career_arc_summary": "3.8 yrs: Backend developer to AI automation engineer.",
        "strengths_notes": "Real email leaked@gmail.com" if with_pii else "Clean single-column ATS structure.",
        "modernization_notes": "Quantify webhook latency and CRM accuracy.",
        "pii_scrubbed": True,
    }


def _sample_job_posting(with_pii: bool = False) -> dict:
    return {
        "posting_key": "ojph-2026-11-ai-automation-01",
        "niche_slug": "tech-ai-automation",
        "title": "AI Automation Engineer (Remote, US Hours)",
        "employer_type": "US B2B SaaS RevOps agency, ~30 staff",
        "platform": "onlinejobs_ph",
        "source_type": "pasted_text",
        "remote_setup": "Full-time remote, Philippines-based",
        "timezone_overlap": "US EST 4-hour overlap",
        "pay_band": "USD 1,200-1,600 / month",
        "description_text": (
            "We need an automation engineer to build n8n and Python FastAPI integrations between HubSpot "
            "and PostgreSQL, maintain Dockerized workers, and ship LLM-based ticket routing."
            + (" Send your CV to hiring.manager@gmail.com" if with_pii else "")
        ),
        "keywords": {
            "role": "AI Automation Engineer",
            "required_skills": ["n8n", "Python", "FastAPI", "PostgreSQL"],
            "preferred_skills": ["Docker", "HubSpot"],
            "keywords": ["integrations", "LLM"],
            "experience_years": 3,
        },
        "captured_on": "2026-11-20",
        "pii_scrubbed": True,
    }


def _passing_ats_run(score: float = 86.0, parse_ok: bool = True) -> dict:
    return {
        "tool_version": "1.4.0",
        "overall_score": score,
        "sub_scores": {"keyword_match": 90.0, "skills_coverage": 85.0},
        "missing_keywords": [],
        "recommendations": [],
        "parse_check_ok": parse_ok,
        "parse_score": 100.0,
        "parse_issues": [],
    }


def _sample_resume() -> dict:
    return {
        "resume_code": "PH-TECH-MID-101",
        "niche_slug": "tech-ai-automation",
        "role_slug": "ai-workflow-automation-mid",
        "pattern_key": "ph-tech-ai-mid-chat-01",
        "seniority": "mid",
        "target_role_title": "AI & Workflow Automation Engineer",
        "layout_archetype": "single-column-ats",
        "full_name": "Bianca Pangilinan",
        "headline": "AI & Workflow Automation Engineer | Python, n8n, FastAPI, PostgreSQL",
        "email": "bianca.pangilinan@example.ph",
        "phone": "+63 918 000 3214",
        "city": "Pasig City",
        "region": "Metro Manila",
        "work_setup_preference": "Hybrid (Ortigas) / Remote (US Overlap)",
        "timezone_readiness": "APAC & US EST Overlap",
        "expected_salary_php": 120000,
        "linkedin_slug": "bianca-pangilinan-ai",
        "portfolio_url": "https://example.ph/portfolio/bianca-pangilinan",
        "professional_summary": (
            "Mid-level AI workflow automation engineer with 3.5 years designing Python, FastAPI, "
            "n8n, and PostgreSQL pipelines for B2B SaaS revenue and operations teams."
        ),
        "total_years_experience": 3.5,
        "target_job_posting_key": "ojph-2026-11-ai-automation-01",
        "experiences": [
            {
                "company_name": "Ortigas Cloud Partners",
                "company_archetype": "PH Remote RevOps Agency",
                "role_title": "AI Automation Engineer",
                "location": "Pasig City, Metro Manila",
                "employment_type": "Full-time",
                "start_date": "2024-06",
                "end_date": "present",
                "is_current": True,
                "bullets": [
                    {
                        "text": "Built 14 n8n and Python FastAPI integrations connecting HubSpot webhooks to PostgreSQL reporting warehouses, saving 19 staff hours per week.",
                        "action_verb": "Built",
                        "metric_value": "19 hrs/wk saved",
                        "tags": ["n8n", "fastapi", "postgresql"],
                    },
                    {
                        "text": "Deployed LLM ticket classification endpoints with structured schema validation, boosting automated routing precision from 79% to 95%.",
                        "action_verb": "Deployed",
                        "metric_value": "95% precision",
                        "tags": ["llm", "python"],
                    },
                    {
                        "text": "Configured Dockerized retry workers and health alerts across 8 client integrations, maintaining 99.6% monthly workflow reliability.",
                        "action_verb": "Configured",
                        "metric_value": "99.6% reliability",
                        "tags": ["docker", "monitoring"],
                    },
                ],
            },
            {
                "company_name": "Laguna Systems Corp",
                "company_archetype": "Regional Enterprise Software Vendor",
                "role_title": "Junior Python Developer",
                "location": "Santa Rosa, Calabarzon",
                "employment_type": "Full-time",
                "start_date": "2023-05",
                "end_date": "2024-05",
                "is_current": False,
                "bullets": [
                    {
                        "text": "Maintained REST API microservices in Python and PostgreSQL, cutting query timeouts by 48% across inventory endpoints.",
                        "action_verb": "Maintained",
                        "metric_value": "48% fewer timeouts",
                        "tags": ["python", "postgresql"],
                    },
                    {
                        "text": "Authored 60+ automated pytest API contract checks in GitHub Actions, catching regressions prior to bi-weekly releases.",
                        "action_verb": "Authored",
                        "metric_value": "60+ API tests",
                        "tags": ["pytest", "ci"],
                    },
                ],
            },
        ],
        "education": [
            {
                "institution": "De La Salle University",
                "degree": "BS Computer Science",
                "field_of_study": "Computer Science",
                "location": "Manila, Metro Manila",
                "start_year": 2019,
                "graduation_year": 2023,
                "honors": "Cum Laude",
                "relevant_coursework": ["Distributed Systems", "Applied AI"],
            }
        ],
        "skills": [
            {"category": "Automation", "name": "n8n", "proficiency": "Core", "years_used": 2.5},
            {"category": "Backend", "name": "Python", "proficiency": "Core", "years_used": 3.5},
            {"category": "Backend", "name": "FastAPI", "proficiency": "Core", "years_used": 2.5},
            {"category": "Data", "name": "PostgreSQL", "proficiency": "Core", "years_used": 3.5},
            {"category": "Infra", "name": "Docker", "proficiency": "Proficient", "years_used": 2.5},
            {"category": "CRM", "name": "HubSpot", "proficiency": "Proficient", "years_used": 2.0},
        ],
        "certifications": [
            {
                "name": "n8n Workflow Specialist",
                "issuer": "n8n",
                "year_earned": 2025,
                "credential_type": "tech",
            }
        ],
        "projects": [],
        "languages": [
            {"language": "English", "proficiency": "C2 Proficient"},
            {"language": "Filipino / Tagalog", "proficiency": "Native"},
        ],
    }


def test_full_cli_lifecycle(tmp_path) -> None:
    db_path = tmp_path / "cli_test.db"
    base_args = ["--db", str(db_path)]

    # 1. db init + niche list
    res_init = runner.invoke(app, [*base_args, "db", "init"])
    assert res_init.exit_code == 0, res_init.output

    res_niches = runner.invoke(app, [*base_args, "niche", "list", "--json"])
    assert res_niches.exit_code == 0
    assert len(json.loads(res_niches.stdout)) == 2

    # 2. pattern add (PII rejected, clean accepted)
    bad_pat_file = tmp_path / "bad_pattern.json"
    bad_pat_file.write_text(json.dumps(_sample_pattern(with_pii=True)), encoding="utf-8")
    res_bad_pat = runner.invoke(app, [*base_args, "pattern", "add", "--json", str(bad_pat_file)])
    assert res_bad_pat.exit_code != 0

    good_pat_file = tmp_path / "good_pattern.json"
    good_pat_file.write_text(json.dumps(_sample_pattern(with_pii=False)), encoding="utf-8")
    res_good_pat = runner.invoke(app, [*base_args, "pattern", "add", "--json", str(good_pat_file)])
    assert res_good_pat.exit_code == 0, res_good_pat.output

    # 2b. remote job posting (PII-guarded) that the resume targets
    bad_job = tmp_path / "bad_job.json"
    bad_job.write_text(json.dumps(_sample_job_posting(with_pii=True)), encoding="utf-8")
    res_bad_job = runner.invoke(app, [*base_args, "job", "add", "--json", str(bad_job)])
    assert res_bad_job.exit_code == 1
    good_job = tmp_path / "good_job.json"
    good_job.write_text(json.dumps(_sample_job_posting()), encoding="utf-8")
    res_good_job = runner.invoke(app, [*base_args, "job", "add", "--json", str(good_job)])
    assert res_good_job.exit_code == 0, res_good_job.output

    # 3. resume import + validate
    resume_file = tmp_path / "resume.json"
    resume_file.write_text(json.dumps(_sample_resume()), encoding="utf-8")
    res_import = runner.invoke(app, [*base_args, "resume", "import", "--json", str(resume_file)])
    assert res_import.exit_code == 0, res_import.output

    res_val = runner.invoke(app, [*base_args, "resume", "validate", "PH-TECH-MID-101", "--json"])
    assert res_val.exit_code == 0
    assert json.loads(res_val.stdout)["valid"] is True

    # 4. Failing review keeps needs_revision (cannot promote with low score even if passed=True)
    low_review = tmp_path / "low_review.json"
    low_review.write_text(
        json.dumps({
            "reviewer_type": "agent_auditor",
            "passed": True,
            "rubric_scores": {
                "deterministic_integrity": 5,
                "ph_market_authenticity": 4,
                "niche_tool_recency": 3,
                "quantified_impact_realism": 4,
                "readability_anti_slop": 4,
                "cross_section_coherence": 4,
                "pool_uniqueness_variety": 4,
            },
            "critique_summary": "Score below gate (28/35 and one dim=3) should block promotion.",
            "required_fixes": ["Deepen 2026 tool stack"],
        }),
        encoding="utf-8",
    )
    res_low = runner.invoke(app, [*base_args, "resume", "review", "PH-TECH-MID-101", "--json", str(low_review)])
    assert res_low.exit_code == 0
    show_after_low = json.loads(runner.invoke(app, [*base_args, "resume", "show", "PH-TECH-MID-101", "--json"]).stdout)
    assert show_after_low["status"] == "needs_revision"

    # 4b. --update replaces children cleanly (including identical skill/language unique keys) and resets status to draft
    updated_payload = _sample_resume()
    updated_payload["headline"] = "Mid Automation Engineer (n8n / Python) | SaaS Integrations & LLM Workflows"
    updated_file = tmp_path / "resume_updated.json"
    updated_file.write_text(json.dumps(updated_payload), encoding="utf-8")
    res_update = runner.invoke(app, [*base_args, "resume", "import", "--json", str(updated_file), "--update"])
    assert res_update.exit_code == 0, res_update.output
    show_after_update = json.loads(runner.invoke(app, [*base_args, "resume", "show", "PH-TECH-MID-101", "--json"]).stdout)
    assert show_after_update["status"] == "draft"
    assert show_after_update["headline"] == updated_payload["headline"]
    assert len(show_after_update["languages"]) == len(updated_payload["languages"])

    # 4c. External ATS run recorded against the target posting (Resume-Matcher result)
    ats_file = tmp_path / "ats.json"
    ats_file.write_text(json.dumps(_passing_ats_run()), encoding="utf-8")
    res_ats = runner.invoke(app, [*base_args, "resume", "ats-record", "PH-TECH-MID-101", "--json", str(ats_file)])
    assert res_ats.exit_code == 0, res_ats.output

    # 5. Passing review promotes to gold_standard
    high_review = tmp_path / "high_review.json"
    high_review.write_text(
        json.dumps({
            "reviewer_type": "agent_auditor",
            "passed": True,
            "rubric_scores": {
                "deterministic_integrity": 5,
                "ph_market_authenticity": 5,
                "niche_tool_recency": 5,
                "quantified_impact_realism": 5,
                "readability_anti_slop": 5,
                "cross_section_coherence": 4,
                "pool_uniqueness_variety": 5,
            },
            "critique_summary": "Meets all 2026 Philippine Tech/AI gold-standard criteria.",
            "required_fixes": [],
        }),
        encoding="utf-8",
    )
    res_high = runner.invoke(app, [*base_args, "resume", "review", "PH-TECH-MID-101", "--json", str(high_review)])
    assert res_high.exit_code == 0, res_high.output

    res_list_gold = runner.invoke(app, [*base_args, "resume", "list", "--status", "gold_standard", "--json"])
    assert res_list_gold.exit_code == 0
    gold_items = json.loads(res_list_gold.stdout)
    assert len(gold_items) == 1
    assert gold_items[0]["quality_score"] == 34

    # 6. Export & read-only SQL views
    res_export = runner.invoke(app, [*base_args, "resume", "export", "--status", "gold_standard", "--format", "json"])
    assert res_export.exit_code == 0
    exported = json.loads(res_export.stdout)
    assert len(exported) == 1
    assert exported[0]["resume_code"] == "PH-TECH-MID-101"

    res_sql = runner.invoke(app, [*base_args, "db", "sql", "SELECT resume_code, quality_score FROM v_gold_resumes_summary", "--json"])
    assert res_sql.exit_code == 0
    assert json.loads(res_sql.stdout) == [{"resume_code": "PH-TECH-MID-101", "quality_score": 34}]

    # 7. Write via db sql is physically blocked
    res_write = runner.invoke(app, [*base_args, "db", "sql", "DELETE FROM resumes"])
    assert res_write.exit_code != 0
