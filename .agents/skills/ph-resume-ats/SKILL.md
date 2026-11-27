---
name: ph-resume-ats
description: >-
  Use this skill to ATS-score a draft ResumeForge game resume (deterministic, non-LLM
  score + PDF parse check) against its real target remote job posting, record the run
  in SQL, and loop honest revisions until it clears the ATS gate required for
  gold_standard promotion. For a real person's own resume, use `my-resume` instead.
---

# External ATS Check (`ph-resume-ats`)

Gives every resume a judgment that isn't the drafter's: a **non-LLM ATS score** (keyword 40%, skills 20%, title 15%, sections 15%, date consistency 10%) plus a parse check of the rendered PDF's text layer. Promotion to `gold_standard` requires the latest run against the resume's target posting to reach `RESUMEFORGE_ATS_MIN_SCORE` (default **80**) with a clean parse check.

## Engines

- **Built-in (default, nothing to install):** `tools/ats_local.py`, same weights as Resume-Matcher.
- **Resume-Matcher (optional, stricter second opinion):** used automatically when its backend is installed. See [docs/optional-resume-matcher.md](../../../docs/optional-resume-matcher.md). Force one with `--engine builtin|resume-matcher`.

## Prerequisites

- The resume was imported with `target_job_posting_key` pointing to a stored posting (`uv run resumeforge job list`).
- Chrome or Chromium installed (used to render the PDF that gets parse-checked).

## Workflow

1. **Run the check** (scores it, renders and parse-checks the PDF, and records the run):
   ```bash
   uv run resumeforge resume ats-check <resume_code>
   ```
   Use `--posting <key>` to score against a different stored post and `--json` for machine output.
2. **Read the result**: overall score, sub-scores, missing keywords, recommendations, and parse issues.
3. **If below the threshold, revise honestly** (hand back to `ph-resume-draft`, `--update`):
   - **Title match low**: align the headline with the post's role title if the persona truly fits it.
   - **Missing keywords**: add one only when the persona would realistically have used it, and prove it in a bullet or project. Follow the anti-stuffing rules in [ph-remote-work-2026.md](../ph-niche-scout/references/ph-remote-work-2026.md).
   - **Parse issues**: fix in `tools/render_pdf.py` (layout) and never by changing content to game the parser.
   - Re-run `resumeforge resume validate` and then `ats-check`. Stop after **3 loops**. If the persona still can't reach the threshold honestly, the persona is wrong for this post: pick a better-fitting post, or redraft the persona.
4. **Hand off to `ph-resume-review`** once the run clears the threshold. The review gate re-checks the latest run automatically.

## Manual recording

If you ran Resume-Matcher yourself (for example through its MCP server), record the result with:
```bash
uv run resumeforge resume ats-record <resume_code> --json - <<'EOF'
{"tool_version": "1.4.0", "overall_score": 84.2, "sub_scores": {"keyword_match": 85.7},
 "missing_keywords": [], "recommendations": [], "parse_check_ok": true, "parse_score": 100}
EOF
```
