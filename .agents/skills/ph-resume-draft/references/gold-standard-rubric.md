# Gold-Standard Resume Quality Rubric (35-Point Scale)

Every resume in ResumeForge is audited across **7 dimensions (1–5 points each, max 35)**.
To earn `gold_standard` status:
- **Total Score `>= 30 / 35`**
- **Every single dimension `>= 4 / 5`**
- **Zero deterministic errors** from `tools/validate_resume.py` and `tools/pii_guard.py`

| Dimension Key | 5/5 Gold-Standard Bar | Reject (`<= 3`) Trigger |
|---|---|---|
| `deterministic_integrity` | Zero chronology gaps/overlaps, exact experience/grad-year math, zero biodata/slop, clean PII guard. | Any math drift, overlap, or formatting violation. |
| `ph_market_authenticity` | Realistic PH city/region, authentic university & employer archetypes, natural Filipino persona, believable PHP expectations & shift readiness. | Cliché name, mismatched city/school, or generic Western template feel. |
| `niche_tool_recency` | 2025–2026 tools, workflows, and compliance standards native to the target PH niche & seniority. | Outdated 2016 tools or mismatched stack for the role. |
| `quantified_impact_realism` | `>= 75%` of bullets pair strong verbs with believable, domain-accurate KPIs (latency, SLA, CSAT, hours saved). | Vague duties or inflated/implausible vanity metrics. |
| `readability_anti_slop` | Crisp executive summary, scannable 12–30 word bullets, zero buzzword fluff or em-dash spam. | Robotic AI phrasing, filler adjectives, or dense walls of text. |
| `cross_section_coherence` | Headline, summary, skills, certs, projects, and experience tell one unified, credible career progression. | Orphan skills never used in bullets/projects or sudden illogical role jumps. |
| `pool_uniqueness_variety` | Distinct persona, employer mix, school, region, and phrasing from all existing resumes in SQL. | Feels recycled from an earlier generated candidate. |
