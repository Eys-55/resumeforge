# ResumeForge — Philippine Gold-Standard Resume Suite

A SQL-backed Agent Skill suite for generating, auditing, and querying **strictly perfect, up-to-date (2025–2026), in-demand Philippine resumes** for game development.

## Architecture

- **SQL System of Record (`resumeforge`):** SQLite (`data/resumes.db`, WAL mode + `mode=ro` read-only queries) managed with SQLAlchemy 2.0 + Alembic migrations and portable to PostgreSQL via `RESUMEFORGE_DATABASE_URL`.
- **Canonical Skills (`.agents/skills/`):**
  1. `ph-niche-scout` — Philippine 2025–2026 niche specs & role archetypes (`tech-ai-automation`, `bpo-va-ops`, extensible).
  2. `ph-resume-ingest` — Chat-only ingestion of public internet resumes with strict PII stripping (`tools/pii_guard.py`).
  3. `ph-resume-draft` — Synthesizes 100% fictional, modern Filipino resumes grounded in SQL niches & patterns.
  4. `ph-resume-ats` — External ATS check with [Resume-Matcher](https://github.com/srbhr/Resume-Matcher) against a real target remote job post (deterministic score + PDF parse check).
  5. `ph-resume-review` — Independent Drafter-Reviewer quality gate (`tools/validate_resume.py` + `resume-auditor` rubric).
  6. `ph-resume-query` — Read-only SQL views (`v_gold_resumes_summary`, `v_niche_coverage`) & game-ready exports.

## Quickstart

```bash
uv sync
uv run resumeforge db init
uv run resumeforge db stats
```

### External ATS scorer (Resume-Matcher)

The promotion gate needs [Resume-Matcher](https://github.com/srbhr/Resume-Matcher) (Apache-2.0) installed beside this repo. No LLM key is needed: ResumeForge calls only its deterministic `score_resume` and `parse_check_file` tools.

```bash
git clone --depth 1 --branch v1.4.0 https://github.com/srbhr/Resume-Matcher.git ~/Developer/Resume-Matcher
cd ~/Developer/Resume-Matcher/apps/backend && uv sync   # pins litellm==1.104.2 (not the compromised 1.107.0)
```

Set `RESUMEFORGE_RESUME_MATCHER_DIR` if it lives elsewhere, and `RESUMEFORGE_ATS_MIN_SCORE` to change the default gate of 80.

## Core Workflow

1. **Scout / Inspect Niches**
   ```bash
   uv run resumeforge niche list
   uv run resumeforge niche show tech-ai-automation
   ```
2. **Ingest a Public PH Resume (Chat-Only -> Anonymized Blueprint)**
   Paste or attach a public resume in chat -> `ph-resume-ingest` strips all PII, checks `tools/pii_guard.py --mode pattern`, and stores a blueprint:
   ```bash
   uv run resumeforge pattern add --json pattern.json
   ```
3. **Store a Real Remote Job Post (the external target)**
   ```bash
   uv run resumeforge job add --json job.json
   uv run resumeforge job list
   ```
4. **Draft a Synthetic PH Gold-Standard Resume**
   `ph-resume-draft` generates structured JSON and imports it as a `draft` (auto-running `tools/validate_resume.py`):
   ```bash
   uv run resumeforge resume import --json draft.json
   ```
5. **External ATS Check (Resume-Matcher)**
   ```bash
   uv run resumeforge resume ats-check PH-TECH-MID-001
   ```
6. **Independent Review & Promotion (`gold_standard`)**
   `ph-resume-review` scores 7 rubric dimensions (out of 35; pass requires `>= 30`, min dimension `>= 4`, and 0 deterministic errors):
   ```bash
   uv run resumeforge resume review PH-TECH-MID-001 --json review.json
   ```
7. **Query & Export for the Game Engine**
   ```bash
   uv run resumeforge db sql "SELECT * FROM v_gold_resumes_summary"
   uv run resumeforge db sql "SELECT * FROM v_niche_coverage"
   uv run resumeforge resume export --status gold_standard --format json
   ```

## Verification

```bash
uv run python tools/lint_skills.py
uv run pytest -v
```
