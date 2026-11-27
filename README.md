# ResumeForge — Philippine Gold-Standard Resume Suite

An Agent Skill suite for **ATS-ready resumes**: build and ATS-check your own real resume, or generate, audit and export fictional Philippine gold-standard resumes for a game. New here? Read [START_HERE.md](START_HERE.md).

## Architecture

- **SQL System of Record (`resumeforge`):** SQLite (`data/resumes.db`, WAL mode + `mode=ro` read-only queries) managed with SQLAlchemy 2.0 + Alembic migrations and portable to PostgreSQL via `RESUMEFORGE_DATABASE_URL`.
- **Canonical Skills (`.agents/skills/`):**
  0. `my-resume` — Build, check, ATS-score and render a real person's own resume (local files in `my_resumes/`, never the DB).
  1. `ph-niche-scout` — Philippine 2025–2026 niche specs & role archetypes (`tech-ai-automation`, `bpo-va-ops`, extensible).
  2. `ph-resume-ingest` — Chat-only ingestion of public internet resumes with strict PII stripping (`tools/pii_guard.py`).
  3. `ph-resume-draft` — Synthesizes 100% fictional, modern Filipino resumes grounded in SQL niches & patterns.
  4. `ph-resume-ats` — Deterministic ATS score + PDF parse check against a real target remote job post (built-in engine, optional Resume-Matcher).
  5. `ph-resume-review` — Independent Drafter-Reviewer quality gate (`tools/validate_resume.py` + `resume-auditor` rubric).
  6. `ph-resume-query` — Read-only SQL views (`v_gold_resumes_summary`, `v_niche_coverage`) & game-ready exports.

## Quickstart

```bash
uv sync
uv run resumeforge db init
uv run resumeforge db stats
```

Or just run `./setup.sh` (Windows: `setup.ps1`).

### ATS engine

The ATS check is built in (`tools/ats_local.py`): deterministic, no LLM, nothing extra to install. [Resume-Matcher](https://github.com/srbhr/Resume-Matcher) is an optional second engine; see [docs/optional-resume-matcher.md](docs/optional-resume-matcher.md). `RESUMEFORGE_ATS_MIN_SCORE` changes the default gate of 80.

## Your Own Resume

```bash
uv run resumeforge mine new "your name"
uv run resumeforge mine check my_resumes/your-name/resume.json
uv run resumeforge mine ats my_resumes/your-name/resume.json --job job.json --one-page
uv run resumeforge ats score --resume any-resume.pdf --job job.json
```

## Game Workflow

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
5. **ATS Check**
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
