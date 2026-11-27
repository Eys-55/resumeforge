# Claude Code Instructions

Follow the canonical rules and thin-pointer skill layout in [AGENTS.md](AGENTS.md).

- Canonical skills live under `.agents/skills/` (`my-resume`, `ph-niche-scout`, `ph-resume-ingest`, `ph-resume-draft`, `ph-resume-ats`, `ph-resume-review`, `ph-resume-query`).
- Slash command wrappers live under `.claude/commands/`.
- First-time users: point them to `START_HERE.md` and `/setup`; "make my resume" requests use `/make-my-resume`.
- The independent read-only auditor subagent is defined in `.claude/agents/resume-auditor.md`.
- Do not duplicate skill specifications or rubric text in this file.
