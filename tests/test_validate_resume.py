"""Tests for deterministic resume validation (`tools/validate_resume.py`)."""

from __future__ import annotations

import copy

from resumeforge.db.engine import session_scope
from resumeforge.db.migrations_helper import upgrade_head
from resumeforge.db.models import Niche, Resume, ResumeBullet, ResumeExperience
from resumeforge.db.seed import seed_initial_niches
from tools.validate_resume import validate_resume_data


def _valid_tech_resume() -> dict:
    return {
        "resume_code": "PH-TECH-MID-001",
        "niche_slug": "tech-ai-automation",
        "role_slug": "ai-workflow-automation-mid",
        "seniority": "mid",
        "target_role_title": "AI & Workflow Automation Engineer",
        "layout_archetype": "single-column-ats",
        "full_name": "Lorenzo Soriano",
        "headline": "AI & Workflow Automation Engineer | Python, n8n, FastAPI, HubSpot",
        "email": "lorenzo.soriano@example.ph",
        "phone": "+63 917 000 4821",
        "city": "Taguig City",
        "region": "Metro Manila",
        "work_setup_preference": "Hybrid (BGC) / Remote (US Overlap)",
        "timezone_readiness": "APAC & US EST Overlap",
        "expected_salary_php": 125000,
        "linkedin_slug": "lorenzo-soriano-automation",
        "portfolio_url": "https://example.ph/portfolio/lorenzo-soriano",
        "professional_summary": (
            "Mid-level AI and workflow automation engineer with 3.8 years of experience building "
            "production Python, FastAPI, n8n, and PostgreSQL integrations for US and APAC SaaS teams."
        ),
        "total_years_experience": 3.8,
        "experiences": [
            {
                "company_name": "Kestrel RevOps Labs",
                "company_archetype": "Remote AI & RevOps Consultancy (US Clients)",
                "role_title": "AI & Workflow Automation Engineer",
                "location": "Remote (Taguig City, PH)",
                "employment_type": "Full-time",
                "start_date": "2024-06",
                "end_date": "present",
                "is_current": True,
                "bullets": [
                    {
                        "text": "Architected 18 production n8n and FastAPI webhook workflows syncing HubSpot leads and PostgreSQL billing tables, cutting manual SDR triage by 22 hours weekly.",
                        "action_verb": "Architected",
                        "metric_value": "22 hrs/wk saved",
                        "tags": ["n8n", "fastapi", "hubspot"],
                    },
                    {
                        "text": "Implemented structured Gemini and OpenAI API extraction pipelines with deterministic schema checks, lifting CRM enrichment accuracy from 81% to 97%.",
                        "action_verb": "Implemented",
                        "metric_value": "97% accuracy",
                        "tags": ["llm", "python"],
                    },
                    {
                        "text": "Built automated Playwright smoke tests and retry queues in Docker for client webhooks, reducing failed sync incidents by 68% across 6 accounts.",
                        "action_verb": "Built",
                        "metric_value": "68% fewer incidents",
                        "tags": ["playwright", "docker"],
                    },
                ],
            },
            {
                "company_name": "Baybayin Fintech Solutions",
                "company_archetype": "BGC Digital Payments Scale-Up",
                "role_title": "Backend & Integration Developer",
                "location": "Taguig City, Metro Manila",
                "employment_type": "Full-time",
                "start_date": "2023-02",
                "end_date": "2024-05",
                "is_current": False,
                "bullets": [
                    {
                        "text": "Engineered Python ETL reconciliation scripts against PostgreSQL settlement logs, reducing daily finance closing turnaround from 3 hours to 25 minutes.",
                        "action_verb": "Engineered",
                        "metric_value": "3h to 25m",
                        "tags": ["python", "postgresql"],
                    },
                    {
                        "text": "Containerized internal billing microservices using Docker and GitHub Actions CI, cutting staging deployment lead time by 55%.",
                        "action_verb": "Containerized",
                        "metric_value": "55% faster deploys",
                        "tags": ["docker", "ci-cd"],
                    },
                ],
            },
        ],
        "education": [
            {
                "institution": "Polytechnic University of the Philippines",
                "degree": "BS Information Technology",
                "field_of_study": "Information Technology",
                "location": "Manila, Metro Manila",
                "start_year": 2019,
                "graduation_year": 2023,
                "honors": "Magna Cum Laude",
                "relevant_coursework": ["Database Systems", "Software Engineering"],
            }
        ],
        "skills": [
            {"category": "Automation", "name": "n8n", "proficiency": "Core", "years_used": 2.5},
            {"category": "Backend", "name": "Python", "proficiency": "Core", "years_used": 3.8},
            {"category": "Backend", "name": "FastAPI", "proficiency": "Core", "years_used": 2.5},
            {"category": "Data", "name": "PostgreSQL", "proficiency": "Core", "years_used": 3.5},
            {"category": "Infra", "name": "Docker", "proficiency": "Proficient", "years_used": 3.0},
            {"category": "CRM", "name": "HubSpot", "proficiency": "Proficient", "years_used": 2.0},
        ],
        "certifications": [
            {
                "name": "AWS Certified AI Practitioner",
                "issuer": "Amazon Web Services",
                "year_earned": 2025,
                "credential_type": "tech",
            }
        ],
        "projects": [
            {
                "name": "PH Invoice OCR & Xero Sync Bot",
                "role": "Creator",
                "tech_stack": ["Python", "FastAPI", "n8n", "PostgreSQL"],
                "summary": "Open-source receipt parser routing structured VAT totals into accounting queues.",
                "impact_metric": "Processed 500+ test invoices at 96% field accuracy",
                "url": "https://example.ph/projects/invoice-ocr",
            }
        ],
        "languages": [
            {"language": "English", "proficiency": "C2 Proficient"},
            {"language": "Filipino / Tagalog", "proficiency": "Native"},
        ],
    }


def _valid_bpo_resume() -> dict:
    return {
        "resume_code": "PH-BPO-MID-001",
        "niche_slug": "bpo-va-ops",
        "role_slug": "bookkeeping-ecom-ops-va-mid",
        "seniority": "mid",
        "target_role_title": "Bookkeeping & E-Commerce Operations VA",
        "layout_archetype": "compact-executive",
        "full_name": "Clarisse Villanueva",
        "headline": "E-Commerce Bookkeeping & Operations VA | Xero, A2X, Shopify, QuickBooks Online",
        "email": "clarisse.villanueva@example.ph",
        "phone": "+63 928 000 7319",
        "city": "Cebu City",
        "region": "Central Visayas",
        "work_setup_preference": "Remote (AU AEST / US Overlap)",
        "timezone_readiness": "AU AEST Full Shift + Dual Fiber ISP",
        "expected_salary_php": 78000,
        "linkedin_slug": "clarisse-villanueva-ops",
        "portfolio_url": "https://example.ph/portfolio/clarisse-villanueva",
        "professional_summary": (
            "E-Commerce bookkeeping and operations VA with 3.5 years supporting Australian and US "
            "Shopify brands in Xero, A2X, QuickBooks Online, and Gorgias customer escalations."
        ),
        "total_years_experience": 3.5,
        "experiences": [
            {
                "company_name": "Southern Cross Retail Group",
                "company_archetype": "Direct AU Shopify E-Commerce Brand",
                "role_title": "Bookkeeping & E-Commerce Operations VA",
                "location": "Remote (Cebu City, PH)",
                "employment_type": "Full-time",
                "start_date": "2024-05",
                "end_date": "present",
                "is_current": True,
                "bullets": [
                    {
                        "text": "Reconciled 2,100 monthly Shopify and Stripe payouts in Xero using A2X, closing monthly books in 4 business days at 99.9% audit accuracy.",
                        "action_verb": "Reconciled",
                        "metric_value": "99.9% accuracy",
                        "tags": ["xero", "a2x", "shopify"],
                    },
                    {
                        "text": "Resolved 140+ monthly Gorgias chargeback and courier exceptions across 3PL partners, lifting dispute recovery win rate from 52% to 78%.",
                        "action_verb": "Resolved",
                        "metric_value": "78% win rate",
                        "tags": ["gorgias", "3pl"],
                    },
                    {
                        "text": "Automated weekly SKU stockout alerts and supplier purchase order trackers in Google Sheets, cutting emergency air-freight reorders by 35%.",
                        "action_verb": "Automated",
                        "metric_value": "35% fewer air reorders",
                        "tags": ["inventory", "sheets"],
                    },
                ],
            },
            {
                "company_name": "Mactan Cloud Accounting Hub",
                "company_archetype": "Cebu Outsourced Finance BPO",
                "role_title": "Junior Bookkeeping Specialist",
                "location": "Cebu City, Central Visayas",
                "employment_type": "Full-time",
                "start_date": "2023-06",
                "end_date": "2024-04",
                "is_current": False,
                "bullets": [
                    {
                        "text": "Processed AP/AR coding for 12 SMB client ledgers in QuickBooks Online and Dext, maintaining a 99.4% QA audit pass rate.",
                        "action_verb": "Processed",
                        "metric_value": "99.4% QA pass",
                        "tags": ["quickbooks", "dext"],
                    },
                    {
                        "text": "Standardized client onboarding checklists in Notion, reducing new-account financial handover cycles from 10 days to 5 days.",
                        "action_verb": "Standardized",
                        "metric_value": "10d to 5d",
                        "tags": ["notion", "sop"],
                    },
                ],
            },
        ],
        "education": [
            {
                "institution": "University of San Carlos",
                "degree": "BS Accountancy",
                "field_of_study": "Accountancy",
                "location": "Cebu City, Central Visayas",
                "start_year": 2019,
                "graduation_year": 2023,
                "honors": "Cum Laude",
                "relevant_coursework": ["Financial Accounting", "Auditing Systems"],
            }
        ],
        "skills": [
            {"category": "Accounting", "name": "Xero", "proficiency": "Core", "years_used": 2.5},
            {"category": "Accounting", "name": "QuickBooks Online", "proficiency": "Core", "years_used": 3.0},
            {"category": "E-Commerce", "name": "A2X", "proficiency": "Core", "years_used": 2.5},
            {"category": "E-Commerce", "name": "Shopify Admin", "proficiency": "Core", "years_used": 2.5},
            {"category": "Support", "name": "Gorgias", "proficiency": "Proficient", "years_used": 2.0},
            {"category": "Docs", "name": "Notion", "proficiency": "Proficient", "years_used": 2.5},
        ],
        "certifications": [
            {
                "name": "Xero Advisor Certified",
                "issuer": "Xero",
                "year_earned": 2024,
                "credential_type": "finance",
            },
            {
                "name": "TESDA Bookkeeping NC III",
                "issuer": "TESDA",
                "year_earned": 2023,
                "credential_type": "tesda",
            },
        ],
        "projects": [],
        "languages": [
            {"language": "English", "proficiency": "C2 Proficient"},
            {"language": "Cebuano", "proficiency": "Native"},
            {"language": "Filipino / Tagalog", "proficiency": "Fluent"},
        ],
    }


def test_valid_tech_and_bpo_resumes_pass() -> None:
    res_tech = validate_resume_data(_valid_tech_resume(), reference_ym="2026-11")
    assert res_tech.valid, res_tech.errors

    res_bpo = validate_resume_data(_valid_bpo_resume(), reference_ym="2026-11")
    assert res_bpo.valid, res_bpo.errors


def test_validator_catches_chronology_overlap_and_math_errors() -> None:
    # 1. Full-time overlap > 1 month
    r1 = copy.deepcopy(_valid_tech_resume())
    r1["experiences"][1]["end_date"] = "2025-01"
    res = validate_resume_data(r1, reference_ym="2026-11")
    assert not res.valid
    assert any("overlap" in e.lower() for e in res.errors)

    # 2. end < start
    r2 = copy.deepcopy(_valid_tech_resume())
    r2["experiences"][1]["start_date"] = "2024-05"
    r2["experiences"][1]["end_date"] = "2023-02"
    res = validate_resume_data(r2, reference_ym="2026-11")
    assert not res.valid
    assert any("precedes" in e.lower() for e in res.errors)

    # 3. Future date
    r3 = copy.deepcopy(_valid_tech_resume())
    r3["experiences"][1]["end_date"] = "2028-01"
    res = validate_resume_data(r3, reference_ym="2026-11")
    assert not res.valid
    assert any("future" in e.lower() for e in res.errors)

    # 4. Seniority mismatch
    r4 = copy.deepcopy(_valid_tech_resume())
    r4["seniority"] = "entry"
    res = validate_resume_data(r4, reference_ym="2026-11")
    assert not res.valid
    assert any("seniority" in e.lower() for e in res.errors)

    # 5. Impossible graduation year
    r5 = copy.deepcopy(_valid_tech_resume())
    r5["education"][0]["graduation_year"] = 2026
    res = validate_resume_data(r5, reference_ym="2026-11")
    assert not res.valid
    assert any("graduation" in e.lower() for e in res.errors)


def test_validator_catches_cliche_biodata_slop_metrics_and_skills() -> None:
    # Cliché name
    r_name = copy.deepcopy(_valid_tech_resume())
    r_name["full_name"] = "Juan Dela Cruz"
    assert not validate_resume_data(r_name, reference_ym="2026-11").valid

    # Outdated PH biodata
    r_bio = copy.deepcopy(_valid_tech_resume())
    r_bio["professional_summary"] += " Marital Status: Single. Religion: Catholic."
    assert not validate_resume_data(r_bio, reference_ym="2026-11").valid

    # AI slop buzzword
    r_slop = copy.deepcopy(_valid_tech_resume())
    r_slop["professional_summary"] += " Known as a synergistic results-driven go-getter."
    assert not validate_resume_data(r_slop, reference_ym="2026-11").valid

    # Low metric density (<50% bullets with digits)
    r_metrics = copy.deepcopy(_valid_tech_resume())
    for exp in r_metrics["experiences"]:
        for b in exp["bullets"]:
            b["text"] = "Collaborated closely with engineering teams on Python and n8n workflow delivery."
    res_m = validate_resume_data(r_metrics, reference_ym="2026-11")
    assert not res_m.valid
    assert any("50%" in e and "metrics" in e.lower() for e in res_m.errors)

    # Unsubstantiated skills (<50% referenced)
    r_skills = copy.deepcopy(_valid_tech_resume())
    r_skills["skills"] = [
        {"category": "Other", "name": f"ObscureTool{i}", "proficiency": "Core"}
        for i in range(6)
    ]
    res_s = validate_resume_data(r_skills, reference_ym="2026-11")
    assert not res_s.valid
    assert any("skills" in e.lower() for e in res_s.errors)


def test_validator_db_dedup_checks(tmp_path) -> None:
    db_path = tmp_path / "dedup.db"
    upgrade_head(db_path)
    with session_scope(db_path, read_only=False) as session:
        seed_initial_niches(session)
        niche = session.query(Niche).filter_by(slug="tech-ai-automation").one()
        existing = Resume(
            resume_code="PH-TECH-MID-999",
            niche_id=niche.id,
            status="gold_standard",
            seniority="mid",
            target_role_title="AI Engineer",
            layout_archetype="single-column-ats",
            full_name="Lorenzo Soriano",
            headline="AI Engineer",
            email="existing@example.ph",
            phone="+63 917 000 1111",
            city="Taguig City",
            region="Metro Manila",
            work_setup_preference="Remote",
            timezone_readiness="EST",
            professional_summary="Experienced engineer.",
            total_years_experience=3.5,
        )
        exp = ResumeExperience(
            company_name="Acme PH",
            company_archetype="Startup",
            role_title="AI Engineer",
            location="Taguig City",
            employment_type="Full-time",
            start_date="2023-01",
            end_date="present",
            is_current=True,
            sort_order=0,
        )
        exp.bullets.append(
            ResumeBullet(
                text=_valid_tech_resume()["experiences"][0]["bullets"][0]["text"],
                action_verb="Architected",
                metric_value="22 hrs/wk",
                tags_json="[]",
                sort_order=0,
            )
        )
        existing.experiences.append(exp)
        session.add(existing)

    with session_scope(db_path, read_only=True) as session:
        res = validate_resume_data(_valid_tech_resume(), session=session, reference_ym="2026-11")
        assert not res.valid
        assert any("duplicate full_name" in e.lower() for e in res.errors)
        assert any("near-duplicate bullet" in e.lower() for e in res.errors)
