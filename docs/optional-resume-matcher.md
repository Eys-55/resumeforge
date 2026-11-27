# Optional: Resume-Matcher as a second ATS engine

ResumeForge ships its own deterministic ATS checker (`tools/ats_local.py`), so nothing extra is needed. If you want a second opinion from [Resume-Matcher](https://github.com/srbhr/Resume-Matcher) (Apache-2.0), install its backend and ResumeForge uses it automatically for `resume ats-check`:

```bash
git clone --branch v1.4.0 https://github.com/srbhr/Resume-Matcher ~/Developer/Resume-Matcher
cd ~/Developer/Resume-Matcher/apps/backend && uv sync
```

Installed somewhere else? Set `RESUMEFORGE_RESUME_MATCHER_DIR=/path/to/Resume-Matcher/apps/backend`.

No LLM key is needed: ResumeForge only calls its deterministic `score_resume` and `parse_check_file` tools. Force an engine with `uv run resumeforge resume ats-check <code> --engine builtin` or `--engine resume-matcher`.

To use Resume-Matcher's MCP server inside Claude Code, add this to a `.mcp.json` in the project root:

```json
{
  "mcpServers": {
    "resume-matcher": {
      "command": "uv",
      "args": ["run", "--quiet", "--directory", "/absolute/path/to/Resume-Matcher/apps/backend", "resume-matcher-mcp"]
    }
  }
}
```
