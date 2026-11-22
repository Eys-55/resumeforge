---
name: ph-niche-scout
description: >-
  Use this skill to inspect, research, or expand Philippine 2025-2026 high-demand
  job niches, role archetypes, PHP salary bands, tool stacks, and local market norms
  stored in ResumeForge SQL.
---

# Philippine Niche Scout (`ph-niche-scout`)

Maintains the 2025–2026 Philippine hiring intelligence and SQL niche/role catalog used by `ph-resume-ingest` and `ph-resume-draft`.

## When to Use

- Before drafting resumes for a PH niche so stack, seniority, PHP compensation, and local conventions match current market expectations.
- When expanding ResumeForge into a new Philippine niche (e.g., licensed healthcare, CPA/finance, creative/marketing) or adding fresh role archetypes.

## Workflow

1. **Inspect existing SQL niches and roles:**
   ```bash
   uv run resumeforge niche list
   uv run resumeforge niche show tech-ai-automation
   uv run resumeforge niche show bpo-va-ops
   ```
2. **Load relevant 2025–2026 PH reference guides:**
   - Broad Philippine resume norms, universities, regional hubs, and outdated conventions to reject: [ph-landscape-2026.md](./references/ph-landscape-2026.md)
   - Tech, Software & AI/Automation benchmarks: [niche-tech-ai-automation.md](./references/niche-tech-ai-automation.md)
   - BPO, Virtual Assistant & Operations benchmarks: [niche-bpo-va-ops.md](./references/niche-bpo-va-ops.md)
3. **Research & add a new niche or role archetype (when requested):**
   - Gather 2025–2026 PH job requirements, realistic PHP monthly salary bands, local/remote work setups, trending tools, certifications, and typical KPIs.
   - Persist via `uv run resumeforge niche add --json -` (matching `NicheCreateInput` in `resumeforge/schemas.py`).
4. **Verify coverage in SQL:**
   ```bash
   uv run resumeforge db sql "SELECT * FROM v_niche_coverage"
   ```
