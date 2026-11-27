# Independent PH Resume Audit Checklist (`resume-auditor`)

Score each of the 7 canonical rubric dimensions from `1` to `5`. Be strict — this repository only admits **gold-standard** resumes for the game's reference pool.

## 1. `deterministic_integrity` (1–5)
- Did `resumeforge resume validate` return 0 errors?
- Are all date ranges continuous, reverse-chronological, and free of overlapping full-time roles?
- Does `total_years_experience` align naturally with both the timeline and `seniority` band?

## 2. `ph_market_authenticity` (1–5)
- Does the persona read like a real 2025–2026 Filipino candidate (authentic PH city/region, university, local/remote employer archetypes, realistic PHP compensation expectation, clear timezone readiness)?
- Are outdated biodata fields (age, religion, marital status, height/weight, 2x2 photo, character references) 100% absent?

## 3. `niche_tool_recency` (1–5)
- Do the tools, frameworks, certifications, and workflows reflect 2025–2026 market reality for the target PH niche (`niche_roles` reference)?
- Are senior/lead roles demonstrating architectural, ownership, or leadership scope rather than junior task execution?

## 4. `quantified_impact_realism` (1–5)
- Are metrics plausible, specific, and native to the role (e.g., p95 latency, hours saved/wk, CSAT, FCR, clean-claim rate, close cycle days)?
- Reject any hand-wavy claims or absurdly inflated numbers.

## 5. `readability_anti_slop` (1–5)
- Is the professional summary concise (3–4 punchy lines) and free of robotic AI clichés (`synergistic`, `delve`, `cutting-edge paradigm`)?
- Do bullets open with strong action verbs and stay crisp (`10–35` words)?

## 6. `cross_section_coherence` (1–5)
- Is every skill listed in `skills` genuinely evidenced in `professional_summary`, `experiences`, or `projects`?
- Do education graduation years, certifications, and project tech stacks align with the career arc?

## 7. `pool_uniqueness_variety` (1–5)
- Does this resume add distinct variety to the SQL pool (different persona name, PH hub, university, company mix, and bullet phrasing vs. existing rows)?

## External ATS & Remote-Fit Checks

- [ ] Resume has a `target_job_posting_key`, and the latest `ats_runs` entry for it is `>= 80` with `parse_check_ok = true`.
- [ ] Headline matches the post's role title, or a truthful close variant.
- [ ] Every post keyword the resume claims is **demonstrated** in a bullet or project, not only listed in skills (no keyword stuffing).
- [ ] Remote readiness is concrete: client type and country, time-zone overlap, async tools (Slack, Loom, ClickUp…) used in bullets.
- [ ] No PH-local-only artifacts that confuse overseas employers (PHP salary expectations where the post pays USD, biodata, long seminar lists).
