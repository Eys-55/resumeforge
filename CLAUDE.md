# Claude Code Instructions

Follow the canonical rules and thin-pointer skill layout in [AGENTS.md](AGENTS.md).

- Canonical skills live under `.agents/skills/` (`ph-niche-scout`, `ph-resume-ingest`, `ph-resume-draft`, `ph-resume-review`, `ph-resume-query`).
- Slash command wrappers live under `.claude/commands/`.
- The independent read-only auditor subagent is defined in `.claude/agents/resume-auditor.md`.
- Do not duplicate skill specifications or rubric text in this file.
