---
name: ph-resume-draft
description: >-
  Use this skill to generate a 100% synthetic, strictly gold-standard 2025-2026
  Philippine resume grounded in SQL niche specs and ingested anonymized patterns,
  validate it deterministically, and store it as `draft` for independent review.
---

# Philippine Gold-Standard Resume Drafter (`ph-resume-draft`)

Synthesizes realistic, modern, 100% fictional Filipino resumes into SQL (`resumes` + normalized child tables) with `status = 'draft'`.

## Grounding & Reference Files

- Read the 7-dimension quality target before drafting: [gold-standard-rubric.md](./references/gold-standard-rubric.md)
- Follow synthetic Filipino persona & contact rules: [ph-synthetic-identities.md](./references/ph-synthetic-identities.md)

## Drafting Workflow

1. **Pull context from SQL (read-only):**
   ```bash
   uv run resumeforge niche show <niche_slug>
   uv run resumeforge pattern list --niche <niche_slug>
   uv run resumeforge pattern show <pattern_key>   # if available
   uv run resumeforge resume list --niche <niche_slug>
   ```
   Check existing personas and `resume_code` values so you never duplicate a name, city/school cliché, or career arc.
2. **Design a unique Filipino synthetic persona:**
   - Choose a fresh `resume_code` (e.g., `PH-TECH-MID-001`, `PH-BPO-MID-002`).
   - Pick a culturally authentic, non-cliché Filipino full name, realistic PH city/region hub, appropriate regional/NCR university, synthetic email (`@example.ph`), and masked phone (`+63 9XX 000 XXXX`).
3. **Author high-craft, 2025–2026 sections (`ResumeDraftInput` JSON):**
   - **Chronology & Math:** Strict `YYYY-MM` dates, reverse-chronological order, zero overlapping full-time roles, `total_years_experience` matching the timeline within `<= 0.6` yrs and matching `seniority` (`entry` 0–2.5, `mid` 2.0–5.5, `senior` 4.5–10.0, `lead` 6.5–22.0).
   - **Bullets:** 3–6 bullets for the newest role, 2–5 for older roles; 8–42 words each; strong action verbs; `>= 50%` (aim for `>= 75%`) quantified with realistic PH/global KPIs.
   - **Skills & Evidence:** At least 5–12 categorized skills, with the majority explicitly demonstrated in `professional_summary`, experience bullets, or `projects`.
   - **Zero Slop & Zero Biodata:** No `Marital Status`, `Height`, `Weight`, `Religion`, `2x2 photo`, `Character References`, placeholders, or AI buzzword clichés.
4. **Import and run deterministic validation:**
   ```bash
   uv run resumeforge resume import --json - <<'EOF'
   { ... }
   EOF
   ```
   (Use `--update` if revising an existing `draft` or `needs_revision` resume.)
5. **Hand off to `ph-resume-review`:**
   - Never manually force `gold_standard`. Invoke `ph-resume-review` so the independent `resume-auditor` evaluates and promotes (or returns surgical fixes).
