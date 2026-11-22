"""Idempotent seed data for 2025-2026 Philippine niches and role archetypes."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from resumeforge.db.models import Niche, NicheRole

SEED_NICHES: list[dict[str, Any]] = [
    {
        "slug": "tech-ai-automation",
        "name": "Tech, Software & AI/Automation (PH)",
        "description": (
            "High-demand 2025-2026 Philippine software engineering, workflow/AI automation, "
            "QA automation, cloud/DevOps, and data engineering roles serving BGC/Makati/Cebu tech "
            "companies, APAC fintechs, and remote global product teams."
        ),
        "market_year": 2026,
        "demand_tier": "very_high",
        "ph_market_notes": (
            "Strong preference for clean reverse-chronological ATS layouts, quantified delivery metrics "
            "(latency, uptime, automation hours saved, test coverage), GitHub/portfolio proof, and "
            "async remote readiness across APAC/US/AU timezones."
        ),
        "roles": [
            {
                "slug": "fullstack-ts-nextjs-mid",
                "title": "Full-Stack TypeScript / Next.js Engineer",
                "seniority_band": "mid",
                "salary_php_min": 85000,
                "salary_php_max": 160000,
                "work_setup": ["Hybrid (BGC/Makati)", "Remote (PH/APAC)", "Remote (US overlap)"],
                "required_skills": [
                    "TypeScript",
                    "Next.js",
                    "React",
                    "Node.js",
                    "PostgreSQL",
                    "REST / GraphQL APIs",
                    "Tailwind CSS",
                    "Git & CI/CD",
                ],
                "trending_tools": [
                    "Next.js 15 App Router",
                    "Prisma / Drizzle ORM",
                    "Supabase",
                    "tRPC",
                    "Playwright",
                    "Docker",
                    "Vercel / AWS",
                ],
                "common_certs": [
                    "AWS Certified Developer - Associate",
                    "Meta Front-End / Full-Stack Certificate",
                ],
                "typical_kpis": [
                    "API p95 latency reduction (%)",
                    "Core Web Vitals / LCP improvement",
                    "Deployment frequency & release rollback rate",
                    "Checkout / onboarding conversion lift",
                ],
            },
            {
                "slug": "ai-workflow-automation-mid",
                "title": "AI & Workflow Automation Engineer",
                "seniority_band": "mid",
                "salary_php_min": 80000,
                "salary_php_max": 155000,
                "work_setup": ["Remote (US/AU clients)", "Hybrid (Metro Manila)", "Remote (Global)"],
                "required_skills": [
                    "Python",
                    "n8n / Make.com",
                    "LLM API Integration",
                    "Prompt & Eval Engineering",
                    "REST Webhooks",
                    "CRM Integration (HubSpot / GoHighLevel)",
                    "SQL & JSON Transformation",
                ],
                "trending_tools": [
                    "n8n",
                    "OpenAI / Anthropic / Gemini APIs",
                    "LangGraph / Agentic Workflows",
                    "FastAPI",
                    "Supabase / Postgres",
                    "HubSpot / GoHighLevel",
                    "Airtable / Retool",
                ],
                "common_certs": [
                    "n8n Verified Creator / Workflow Specialist",
                    "HubSpot Solutions Architecture / RevOps",
                    "AWS Certified AI Practitioner",
                ],
                "typical_kpis": [
                    "Manual ops hours saved per week",
                    "Lead response / SLA turnaround reduction",
                    "Workflow execution success rate (%)",
                    "LLM cost-per-task optimization (%)",
                ],
            },
            {
                "slug": "qa-automation-engineer-mid",
                "title": "QA Automation Engineer",
                "seniority_band": "mid",
                "salary_php_min": 70000,
                "salary_php_max": 135000,
                "work_setup": ["Hybrid (Ortigas/Eastwood/Cebu)", "Remote (PH/AU/EU)"],
                "required_skills": [
                    "Playwright / Cypress",
                    "TypeScript or Python",
                    "API Test Automation",
                    "CI/CD Quality Gates",
                    "Regression Strategy",
                    "SQL Verification",
                ],
                "trending_tools": [
                    "Playwright",
                    "Postman / Newman",
                    "k6 Load Testing",
                    "GitHub Actions",
                    "Allure Reports",
                    "BrowserStack",
                ],
                "common_certs": [
                    "ISTQB Certified Tester Foundation Level (CTFL)",
                    "ISTQB Test Automation Engineer",
                ],
                "typical_kpis": [
                    "Automated regression coverage (%)",
                    "Production escaped-defect reduction (%)",
                    "CI test suite execution runtime reduction",
                    "Flaky test rate below threshold (%)",
                ],
            },
            {
                "slug": "devops-cloud-engineer-senior",
                "title": "DevOps & Cloud Infrastructure Engineer",
                "seniority_band": "senior",
                "salary_php_min": 140000,
                "salary_php_max": 260000,
                "work_setup": ["Hybrid (BGC/Makati/Cebu)", "Remote (Global APAC/US)"],
                "required_skills": [
                    "AWS or GCP",
                    "Terraform (IaC)",
                    "Docker & Kubernetes",
                    "CI/CD Pipelines",
                    "Observability & Alerting",
                    "Linux & Cloud Security",
                ],
                "trending_tools": [
                    "Terraform / OpenTofu",
                    "AWS EKS / ECS",
                    "GitHub Actions / GitLab CI",
                    "Prometheus / Grafana / Datadog",
                    "ArgoCD",
                    "Cloudflare",
                ],
                "common_certs": [
                    "AWS Certified Solutions Architect - Associate / Professional",
                    "Certified Kubernetes Administrator (CKA)",
                    "HashiCorp Certified: Terraform Associate",
                ],
                "typical_kpis": [
                    "Production uptime SLA (99.95%+)",
                    "MTTR reduction (minutes)",
                    "Monthly cloud spend optimization (%)",
                    "Zero-downtime deployment lead time",
                ],
            },
            {
                "slug": "data-analytics-engineer-mid",
                "title": "Data & Analytics Engineer",
                "seniority_band": "mid",
                "salary_php_min": 85000,
                "salary_php_max": 165000,
                "work_setup": ["Hybrid (Makati/BGC)", "Remote (APAC/AU)"],
                "required_skills": [
                    "SQL (PostgreSQL / BigQuery / Snowflake)",
                    "dbt",
                    "Python (Pandas / Polars)",
                    "Data Modeling (Dimensional / Star Schema)",
                    "BI Dashboards",
                    "ETL / ELT Orchestration",
                ],
                "trending_tools": [
                    "dbt Core / Cloud",
                    "BigQuery / Snowflake",
                    "Apache Airflow / Dagster",
                    "Looker Studio / Power BI",
                    "Fivetran / Airbyte",
                    "DuckDB",
                ],
                "common_certs": [
                    "Google Cloud Professional Data Engineer",
                    "dbt Analytics Engineering Certification",
                    "Microsoft Certified: Power BI Data Analyst Associate",
                ],
                "typical_kpis": [
                    "Pipeline SLA timeliness & freshness (%)",
                    "Warehouse query cost / runtime reduction (%)",
                    "Automated reporting hours saved",
                    "Data quality test pass rate (%)",
                ],
            },
        ],
    },
    {
        "slug": "bpo-va-ops",
        "name": "BPO, Virtual Assistant & Operations (PH)",
        "description": (
            "High-demand 2025-2026 Philippine remote Virtual Assistant, SaaS customer operations, "
            "bookkeeping/e-commerce ops, HIPAA-compliant medical VA, and BPO team leadership roles "
            "serving US, Australian, UK, and regional enterprises."
        ),
        "market_year": 2026,
        "demand_tier": "very_high",
        "ph_market_notes": (
            "Top PH BPO/VA resumes replace old biodata with concrete operational metrics (CSAT, "
            "FCR, AHT, inbox SLA, monthly reconciliation accuracy), named SaaS/CRM tools, "
            "verified timezone shift readiness (US EST/PST or AU AEST), and relevant industry compliance."
        ),
        "roles": [
            {
                "slug": "executive-va-founders-mid",
                "title": "Executive Virtual Assistant (Founders & C-Suite)",
                "seniority_band": "mid",
                "salary_php_min": 55000,
                "salary_php_max": 105000,
                "work_setup": ["Remote (US EST/PST)", "Remote (AU AEST)", "Remote (UK GMT)"],
                "required_skills": [
                    "Executive Calendar & Inbox Management",
                    "SOP Documentation",
                    "Travel & Board Prep Logistics",
                    "Stakeholder Communication",
                    "Project & Task Coordination",
                    "Expense & Vendor Tracking",
                ],
                "trending_tools": [
                    "Google Workspace / Microsoft 365",
                    "Notion / ClickUp / Asana",
                    "Slack / Loom",
                    "AI Meeting Assistants (Fathom / Granola / Otter)",
                    "Zapier / Make",
                    "Expensify / Ramp",
                ],
                "common_certs": [
                    "TESDA Bookkeeping NC III or Events/Admin Training",
                    "Notion Essentials / ClickUp Verified",
                    "EF SET C1/C2 English Proficiency",
                ],
                "typical_kpis": [
                    "Executive hours reclaimed per week",
                    "Inbox zero / response SLA compliance (%)",
                    "SOPs authored & team onboarding time reduction",
                    "Scheduling conflict rate (~0%)",
                ],
            },
            {
                "slug": "saas-tech-support-cx-mid",
                "title": "SaaS Technical Support & Customer Experience Specialist",
                "seniority_band": "mid",
                "salary_php_min": 48000,
                "salary_php_max": 95000,
                "work_setup": ["Remote (US/APAC/EU Shifts)", "Hybrid (BGC/Cebu/Clark)"],
                "required_skills": [
                    "Tier 1-2 Technical Troubleshooting",
                    "API / Webhook Log Inspection",
                    "Omnichannel Ticketing (Email/Chat/Voice)",
                    "Bug Reproduction & Escalation",
                    "Help Center Documentation",
                ],
                "trending_tools": [
                    "Zendesk / Intercom / Freshdesk",
                    "Jira / Linear",
                    "Postman / Chrome DevTools",
                    "HubSpot Service Hub",
                    "Loom",
                    "AI Helpdesk Macros & Triage",
                ],
                "common_certs": [
                    "HubSpot Service Hub Software Certified",
                    "ITIL 4 Foundation",
                    "COPC CX Operations Training",
                ],
                "typical_kpis": [
                    "CSAT score (95%+)",
                    "First Contact Resolution (FCR %)",
                    "Median First Response Time (FRT)",
                    "Ticket deflection via help-center articles (%)",
                ],
            },
            {
                "slug": "bookkeeping-ecom-ops-va-mid",
                "title": "Bookkeeping & E-Commerce Operations VA",
                "seniority_band": "mid",
                "salary_php_min": 55000,
                "salary_php_max": 110000,
                "work_setup": ["Remote (AU/US E-Commerce Brands)", "Remote (Flexible Overlap)"],
                "required_skills": [
                    "Accounts Payable & Receivable",
                    "Bank & Payment Gateway Reconciliation",
                    "Month-End Close Support",
                    "Inventory & Order Fulfillment Ops",
                    "Supplier PO & 3PL Coordination",
                ],
                "trending_tools": [
                    "Xero / QuickBooks Online",
                    "Shopify Admin & Apps",
                    "Amazon Seller Central",
                    "A2X / Dext / Hubdoc",
                    "Gorgias",
                    "Google Sheets / Excel (Pivot/XLOOKUP)",
                ],
                "common_certs": [
                    "Xero Advisor Certified",
                    "QuickBooks Online ProAdvisor",
                    "TESDA Bookkeeping NC III",
                ],
                "typical_kpis": [
                    "Month-end close turnaround (business days)",
                    "Reconciliation accuracy (99.8%+)",
                    "Chargeback / refund dispute win rate (%)",
                    "Stockout & order fulfillment exception reduction",
                ],
            },
            {
                "slug": "medical-healthcare-va-mid",
                "title": "Medical & Healthcare Virtual Assistant",
                "seniority_band": "mid",
                "salary_php_min": 50000,
                "salary_php_max": 95000,
                "work_setup": ["Remote (US Clinic Hours - EST/CST/PST)", "Hybrid (Ortigas/Cebu)"],
                "required_skills": [
                    "HIPAA Privacy & Security Compliance",
                    "Insurance Verification & Prior Authorization",
                    "EHR Charting & Patient Intake",
                    "Medical Billing / ICD-10 / CPT Coordination",
                    "Referral & Lab Scheduling",
                ],
                "trending_tools": [
                    "Athenahealth / eClinicalWorks / Kareo (Tebra)",
                    "RingCentral / OpenPhone",
                    "Availity / Waystar",
                    "Google Workspace (BAA)",
                    "AI Medical Scribe Review",
                ],
                "common_certs": [
                    "HIPAA Compliance Certification",
                    "Medical Terminology & ICD-10-CM Training",
                    "Certified Medical Administrative Assistant (CMAA)",
                ],
                "typical_kpis": [
                    "Prior authorization approval turnaround (hours/days)",
                    "Claim clean-submission rate (%)",
                    "Patient no-show reduction via confirmation cadence (%)",
                    "Zero HIPAA audit violations",
                ],
            },
            {
                "slug": "bpo-ops-team-lead-senior",
                "title": "BPO Operations Team Lead / WFM Analyst",
                "seniority_band": "senior",
                "salary_php_min": 75000,
                "salary_php_max": 145000,
                "work_setup": ["Hybrid (Makati/Ortigas/Alabang/Cebu/Davao)", "On-site Enterprise BPO"],
                "required_skills": [
                    "Team Coaching & Performance Management (15-25 Agents)",
                    "SLA & Queue Shrinkage Management",
                    "Workforce Forecasting & Scheduling",
                    "QA Calibration & Root-Cause Analysis",
                    "Client Business Reviews (QBR/WBR)",
                ],
                "trending_tools": [
                    "NICE CXone / Genesys Cloud",
                    "Assembled / Calabrio WFM",
                    "Power BI / Excel Power Query",
                    "Zendesk / Salesforce Service Cloud",
                    "MaestroQA",
                ],
                "common_certs": [
                    "Lean Six Sigma Yellow / Green Belt",
                    "COPC Registered Coordinator / CX Management",
                ],
                "typical_kpis": [
                    "Account SLA compliance (98%+)",
                    "Team attrition reduction (percentage points)",
                    "Schedule adherence & shrinkage control (%)",
                    "CSAT / QA score uplift across coached cohort",
                ],
            },
        ],
    },
]


def seed_initial_niches(session: Session) -> dict[str, int]:
    """Idempotently upsert the initial 2025-2026 Philippine niches and role archetypes."""
    niches_created = 0
    roles_created = 0

    for niche_data in SEED_NICHES:
        niche = session.scalar(select(Niche).where(Niche.slug == niche_data["slug"]))
        if niche is None:
            niche = Niche(
                slug=niche_data["slug"],
                name=niche_data["name"],
                description=niche_data["description"],
                market_year=niche_data["market_year"],
                demand_tier=niche_data["demand_tier"],
                ph_market_notes=niche_data["ph_market_notes"],
            )
            session.add(niche)
            session.flush()
            niches_created += 1
        else:
            niche.name = niche_data["name"]
            niche.description = niche_data["description"]
            niche.market_year = niche_data["market_year"]
            niche.demand_tier = niche_data["demand_tier"]
            niche.ph_market_notes = niche_data["ph_market_notes"]

        for role_data in niche_data["roles"]:
            role = session.scalar(select(NicheRole).where(NicheRole.slug == role_data["slug"]))
            if role is None:
                role = NicheRole(
                    niche_id=niche.id,
                    slug=role_data["slug"],
                    title=role_data["title"],
                    seniority_band=role_data["seniority_band"],
                    salary_php_min=role_data["salary_php_min"],
                    salary_php_max=role_data["salary_php_max"],
                    work_setup_json=json.dumps(role_data["work_setup"]),
                    required_skills_json=json.dumps(role_data["required_skills"]),
                    trending_tools_json=json.dumps(role_data["trending_tools"]),
                    common_certs_json=json.dumps(role_data["common_certs"]),
                    typical_kpis_json=json.dumps(role_data["typical_kpis"]),
                )
                session.add(role)
                roles_created += 1
            else:
                role.niche_id = niche.id
                role.title = role_data["title"]
                role.seniority_band = role_data["seniority_band"]
                role.salary_php_min = role_data["salary_php_min"]
                role.salary_php_max = role_data["salary_php_max"]
                role.work_setup_json = json.dumps(role_data["work_setup"])
                role.required_skills_json = json.dumps(role_data["required_skills"])
                role.trending_tools_json = json.dumps(role_data["trending_tools"])
                role.common_certs_json = json.dumps(role_data["common_certs"])
                role.typical_kpis_json = json.dumps(role_data["typical_kpis"])

    session.flush()
    return {"niches_created": niches_created, "roles_created": roles_created}
