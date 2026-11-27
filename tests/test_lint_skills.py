"""Verify all skills, commands, and agent wrappers pass lint checks."""

from __future__ import annotations

from tools.lint_skills import lint_all


def test_lint_skills_passes() -> None:
    errors, counts = lint_all()
    assert errors == [], f"Skill lint failures: {errors}"
    assert counts["skills"] == 6
    assert counts["commands"] == 6
    assert counts["agents"] == 1
