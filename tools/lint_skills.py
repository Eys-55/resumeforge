#!/usr/bin/env python3
"""Lint ResumeForge canonical skills, Claude command wrappers, and agent definitions.

Run from anywhere: uv run python tools/lint_skills.py

Exit code 0 on success, 1 with diagnostics otherwise.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("lint_skills.py requires PyYAML: uv sync")

ROOT = Path(__file__).resolve().parent.parent
MD_LINK_RE = re.compile(r"\[[^\]]+\]\((\./[^)#]+)(?:#[^)]*)?\)")


def _parse_frontmatter(path: Path) -> tuple[dict | None, str, str | None]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None, text, f"{path.relative_to(ROOT)}: missing YAML frontmatter (must start with ---)"
    end = text.find("\n---", 4)
    if end == -1:
        return None, text, f"{path.relative_to(ROOT)}: unterminated YAML frontmatter"
    try:
        data = yaml.safe_load(text[4:end])
    except yaml.YAMLError as exc:
        return None, text, f"{path.relative_to(ROOT)}: invalid YAML frontmatter: {exc}"
    if not isinstance(data, dict):
        return None, text, f"{path.relative_to(ROOT)}: frontmatter must parse to a YAML mapping"
    return data, text[end + 4 :], None


def lint_all() -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []

    skills = sorted(ROOT.glob(".agents/skills/*/SKILL.md"))
    commands = sorted((ROOT / ".claude" / "commands").glob("*.md"))
    agents = sorted((ROOT / ".claude" / "agents").glob("*.md"))

    if not skills:
        errors.append("No SKILL.md files found under .agents/skills/*/")
    if not commands:
        errors.append("No command files found under .claude/commands/")
    if not agents:
        errors.append("No agent files found under .claude/agents/")

    for skill_path in skills:
        rel_path = skill_path.relative_to(ROOT)
        data, body, err = _parse_frontmatter(skill_path)
        if err:
            errors.append(err)
            continue
        assert data is not None
        for key in ("name", "description"):
            if not str(data.get(key) or "").strip():
                errors.append(f"{rel_path}: frontmatter missing required key '{key}'")
        folder_name = skill_path.parent.name
        if data.get("name") and data.get("name") != folder_name:
            errors.append(f"{rel_path}: frontmatter name {data.get('name')!r} != directory {folder_name!r}")

        # Verify relative markdown links inside SKILL.md resolve cleanly
        for match in MD_LINK_RE.finditer(body):
            target = (skill_path.parent / match.group(1)).resolve()
            if not target.exists():
                errors.append(f"{rel_path}: broken relative link {match.group(1)!r}")

    for cmd_path in commands:
        rel_path = cmd_path.relative_to(ROOT)
        lines = cmd_path.read_text(encoding="utf-8").lstrip().splitlines()
        first = lines[0] if lines else ""
        expected_prefix = f"# /{cmd_path.stem}"
        if not first.startswith(expected_prefix):
            errors.append(f"{rel_path}: command file must start with '{expected_prefix}' (got {first[:60]!r})")

    for agent_path in agents:
        rel_path = agent_path.relative_to(ROOT)
        data, _body, err = _parse_frontmatter(agent_path)
        if err:
            errors.append(err)
            continue
        assert data is not None
        for key in ("name", "description", "tools"):
            if not str(data.get(key) or "").strip():
                errors.append(f"{rel_path}: agent frontmatter missing required key '{key}'")

    counts = {
        "skills": len(skills),
        "commands": len(commands),
        "agents": len(agents),
    }
    return errors, counts


def main() -> int:
    errors, counts = lint_all()
    if errors:
        print(f"lint_skills: {len(errors)} failure(s)")
        for err in errors:
            print(f"  - {err}")
        return 1
    agent_word = "agent" if counts["agents"] == 1 else "agents"
    print(
        f"lint_skills: OK ({counts['skills']} skills, {counts['commands']} commands, {counts['agents']} {agent_word})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
