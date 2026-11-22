---
name: ph-resume-review
description: >-
  Use this skill to perform an independent Drafter-Reviewer hiring-manager audit
  on a `draft` or `needs_revision` resume in SQL, enforcing deterministic validation
  and the 35-point rubric before promoting to `gold_standard`.
---

# Philippine Gold-Standard Resume Reviewer (`ph-resume-review`)

Acts as an independent Philippine Hiring Manager proxy (`resume-auditor`) to verify that every resume promoted to `gold_standard` is realistic, current for 2025–2026, and free of mechanical or phrasing defects.

## Hard Promotion Gate

`uv run resumeforge resume review <resume_code>` promotes a resume to `gold_standard` **only when all of the following hold**:
1. Deterministic check (`tools/validate_resume.py` + `tools/pii_guard.py`) returns `0` errors.
2. `passed` is `true`.
3. `total_score >= 30` out of `35`.
4. Every one of the 7 rubric dimensions scores `>= 4` out of `5`.

If any gate fails, SQL marks the resume `needs_revision` with actionable `required_fixes`.

## Workflow

1. **Fetch the target resume & niche spec (read-only):**
   ```bash
   uv run resumeforge resume validate <resume_code> --json
   uv run resumeforge resume show <resume_code> --json
   uv run resumeforge niche show <niche_slug> --json
   ```
2. **Dispatch or run independent review using [audit-checklist.md](./references/audit-checklist.md):**
   - Check the resume against the 7 rubric dimensions (`deterministic_integrity`, `ph_market_authenticity`, `niche_tool_recency`, `quantified_impact_realism`, `readability_anti_slop`, `cross_section_coherence`, `pool_uniqueness_variety`).
   - Also compare against existing resumes (`uv run resumeforge resume list --niche <niche_slug>`) for persona/phrasing variety.
3. **Record the review verdict in SQL:**
   ```bash
   uv run resumeforge resume review <resume_code> --json - <<'EOF'
   {
     "reviewer_type": "agent_auditor",
     "passed": true,
     "rubric_scores": {
       "deterministic_integrity": 5,
       "ph_market_authenticity": 5,
       "niche_tool_recency": 5,
       "quantified_impact_realism": 4,
       "readability_anti_slop": 5,
       "cross_section_coherence": 5,
       "pool_uniqueness_variety": 5
     },
     "critique_summary": "Crisp 2026 PH profile with authentic regional trajectory and grounded KPIs.",
     "required_fixes": []
   }
   EOF
   ```
4. **Loop if `needs_revision`:**
   - Return the exact `required_fixes` list to `ph-resume-draft` to update via `uv run resumeforge resume import --json - --update`, then re-run `ph-resume-review`.
