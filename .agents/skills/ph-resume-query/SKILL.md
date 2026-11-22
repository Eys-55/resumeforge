---
name: ph-resume-query
description: >-
  Use this skill to run strictly read-only SQL queries against data/resumes.db,
  check niche coverage gaps across seniority bands, and export gold-standard
  resumes for the game engine.
---

# Philippine Resume SQL Query & Game Export (`ph-resume-query`)

Provides strictly read-only (`mode=ro`, `PRAGMA query_only = ON`) access to `data/resumes.db` for inspecting pool health, diagnosing coverage gaps, and exporting `gold_standard` resumes.

## Common Queries & Exports

1. **Check niche & seniority coverage:**
   ```bash
   uv run resumeforge db sql "SELECT * FROM v_niche_coverage"
   ```
2. **Inspect the game-ready `gold_standard` pool:**
   ```bash
   uv run resumeforge db sql "SELECT resume_code, niche_slug, target_role_title, seniority, city, quality_score FROM v_gold_resumes_summary ORDER BY niche_slug, seniority"
   ```
3. **Find drafts awaiting audit or revision:**
   ```bash
   uv run resumeforge resume list --status draft
   uv run resumeforge resume list --status needs_revision
   ```
4. **Export `gold_standard` resumes for the game engine:**
   ```bash
   uv run resumeforge resume export --status gold_standard --format json --out tmp/gold_resumes.json
   uv run resumeforge resume export --status gold_standard --niche tech-ai-automation --format jsonl
   uv run resumeforge resume export --status gold_standard --format md
   ```
5. **Custom read-only analytics:**
   ```bash
   uv run resumeforge db sql "SELECT city, COUNT(*) AS count FROM resumes WHERE status = 'gold_standard' GROUP BY city ORDER BY count DESC"
   ```
   All `db sql` calls physically reject `INSERT`, `UPDATE`, `DELETE`, `DROP`, and `ALTER`.
