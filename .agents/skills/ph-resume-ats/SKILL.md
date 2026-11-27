---
name: ph-resume-ats
description: >-
  Use this skill to score a draft ResumeForge resume with the external Resume-Matcher
  tool (deterministic ATS score + PDF parse check) against its real target remote
  job posting, record the run in SQL, and loop honest revisions until it clears the
  ATS gate required for gold_standard promotion.
---

# External ATS Check (`ph-resume-ats`)

Gives every resume an outside judgment that isn't ours: [Resume-Matcher](https://github.com/srbhr/Resume-Matcher) (Apache-2.0) computes a **non-LLM ATS score** (keyword 40%, skills 20%, title 15%, sections 15%, date consistency 10%) and parse-checks the rendered PDF. Promotion to `gold_standard` requires the latest run against the resume's target posting to reach `RESUMEFORGE_ATS_MIN_SCORE` (default **80**) with a clean parse check.

## Prerequisites

- Resume-Matcher backend installed at `~/Developer/Resume-Matcher/apps/backend` (tag `v1.4.0`, `uv sync`), or set `RESUMEFORGE_RESUME_MATCHER_DIR`. No LLM key is needed: ResumeForge calls only its deterministic `score_resume` and `parse_check_file` tools.
- The resume was imported with `target_job_posting_key` pointing to a stored posting (`uv run resumeforge job list`).

## Workflow

1. **Run the check** (renders the PDF, scores it, parse-checks it, and records the run):
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
