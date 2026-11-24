"""External ATS (Resume-Matcher) gate, job postings, and bridge conversion tests."""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from resumeforge.cli import app
from tests.test_cli_workflow import _passing_ats_run, _sample_job_posting, _sample_pattern, _sample_resume
from tools.ats_bridge import to_rm_resume_data

runner = CliRunner()


def _init_db(base, tmp_path) -> None:
    assert runner.invoke(app, [*base, "db", "init"]).exit_code == 0
    pat = tmp_path / "pattern.json"
    pat.write_text(json.dumps(_sample_pattern()), encoding="utf-8")
    assert runner.invoke(app, [*base, "pattern", "add", "--json", str(pat)]).exit_code == 0

HIGH_REVIEW = {
    "reviewer_type": "agent_auditor",
    "passed": True,
    "rubric_scores": {
        "deterministic_integrity": 5,
        "ph_market_authenticity": 5,
        "niche_tool_recency": 5,
        "quantified_impact_realism": 5,
        "readability_anti_slop": 5,
        "cross_section_coherence": 5,
        "pool_uniqueness_variety": 5,
    },
    "critique_summary": "Rubric is perfect; only the ATS gate decides here.",
    "required_fixes": [],
}


@pytest.fixture()
def seeded(tmp_path):
    base = ["--db", str(tmp_path / "ats.db")]
    _init_db(base, tmp_path)
    job = tmp_path / "job.json"
    job.write_text(json.dumps(_sample_job_posting()), encoding="utf-8")
    assert runner.invoke(app, [*base, "job", "add", "--json", str(job)]).exit_code == 0
    resume = tmp_path / "resume.json"
    resume.write_text(json.dumps(_sample_resume()), encoding="utf-8")
    res = runner.invoke(app, [*base, "resume", "import", "--json", str(resume)])
    assert res.exit_code == 0, res.output
    return base, tmp_path


def _record(base, tmp_path, payload: dict) -> None:
    f = tmp_path / "run.json"
    f.write_text(json.dumps(payload), encoding="utf-8")
    res = runner.invoke(app, [*base, "resume", "ats-record", "PH-TECH-MID-101", "--json", str(f)])
    assert res.exit_code == 0, res.output


def _review_status(base, tmp_path) -> str:
    f = tmp_path / "review.json"
    f.write_text(json.dumps(HIGH_REVIEW), encoding="utf-8")
    assert runner.invoke(app, [*base, "resume", "review", "PH-TECH-MID-101", "--json", str(f)]).exit_code == 0
    shown = runner.invoke(app, [*base, "resume", "show", "PH-TECH-MID-101", "--json"])
    return json.loads(shown.stdout)["status"]


def test_gate_blocks_without_ats_run(seeded) -> None:
    base, tmp_path = seeded
    assert _review_status(base, tmp_path) == "needs_revision"


def test_gate_blocks_low_ats_score(seeded) -> None:
    base, tmp_path = seeded
    _record(base, tmp_path, _passing_ats_run(score=72.5))
    assert _review_status(base, tmp_path) == "needs_revision"


def test_gate_blocks_failed_parse_check(seeded) -> None:
    base, tmp_path = seeded
    _record(base, tmp_path, _passing_ats_run(score=91.0, parse_ok=False))
    assert _review_status(base, tmp_path) == "needs_revision"


def test_gate_uses_latest_run(seeded) -> None:
    base, tmp_path = seeded
    _record(base, tmp_path, _passing_ats_run(score=91.0))
    _record(base, tmp_path, _passing_ats_run(score=60.0))
    assert _review_status(base, tmp_path) == "needs_revision"
    _record(base, tmp_path, _passing_ats_run(score=84.0))
    assert _review_status(base, tmp_path) == "gold_standard"


def test_gate_threshold_env_override(seeded, monkeypatch) -> None:
    base, tmp_path = seeded
    monkeypatch.setenv("RESUMEFORGE_ATS_MIN_SCORE", "90")
    _record(base, tmp_path, _passing_ats_run(score=86.0))
    assert _review_status(base, tmp_path) == "needs_revision"


def test_gate_blocks_resume_without_target_posting(tmp_path) -> None:
    base = ["--db", str(tmp_path / "nt.db")]
    _init_db(base, tmp_path)
    payload = _sample_resume()
    payload.pop("target_job_posting_key")
    f = tmp_path / "resume.json"
    f.write_text(json.dumps(payload), encoding="utf-8")
    assert runner.invoke(app, [*base, "resume", "import", "--json", str(f)]).exit_code == 0
    assert _review_status(base, tmp_path) == "needs_revision"


def test_import_rejects_unknown_target_posting(tmp_path) -> None:
    base = ["--db", str(tmp_path / "unk.db")]
    _init_db(base, tmp_path)
    f = tmp_path / "resume.json"
    f.write_text(json.dumps(_sample_resume()), encoding="utf-8")
    res = runner.invoke(app, [*base, "resume", "import", "--json", str(f)])
    assert res.exit_code == 1


def test_job_show_and_summary_view(seeded) -> None:
    base, tmp_path = seeded
    shown = json.loads(runner.invoke(app, [*base, "job", "show", "ojph-2026-11-ai-automation-01"]).stdout)
    assert shown["keywords"]["required_skills"] == ["n8n", "Python", "FastAPI", "PostgreSQL"]
    _record(base, tmp_path, _passing_ats_run(score=88.0))
    assert _review_status(base, tmp_path) == "gold_standard"
    res = runner.invoke(
        app,
        [*base, "db", "sql", "SELECT target_posting_key, latest_ats_score FROM v_gold_resumes_summary", "--json"],
    )
    rows = json.loads(res.stdout)
    assert rows == [{"target_posting_key": "ojph-2026-11-ai-automation-01", "latest_ats_score": 88.0}]


def test_bridge_converts_resume_to_resume_matcher_shape() -> None:
    src = _sample_resume()
    src["certifications"] = [dict(c, expiry_year=None) for c in src["certifications"]]
    rm = to_rm_resume_data(src)
    assert rm["personalInfo"]["name"] == "Bianca Pangilinan"
    assert rm["personalInfo"]["location"] == "Pasig City, Metro Manila"
    first = rm["workExperience"][0]
    assert first["years"] == "Jun 2024 - Present"
    assert first["description"][0].startswith("Built 14 n8n")
    assert "n8n" in rm["additional"]["technicalSkills"]
    assert rm["education"][0]["years"] == "2019 - 2023"


def test_upgrade_preserves_child_rows(tmp_path) -> None:
    """Regression: SQLite batch rebuild of `resumes` must not cascade-delete child rows."""
    import sqlite3

    from alembic import command

    from resumeforge.db.migrations_helper import make_alembic_config

    db = tmp_path / "upgrade.db"
    base = ["--db", str(db)]
    _init_db(base, tmp_path)
    f = tmp_path / "resume.json"
    payload = _sample_resume()
    payload.pop("target_job_posting_key")
    f.write_text(json.dumps(payload), encoding="utf-8")
    assert runner.invoke(app, [*base, "resume", "import", "--json", str(f)]).exit_code == 0

    def counts() -> tuple[int, ...]:
        with sqlite3.connect(db) as conn:
            return tuple(
                conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                for t in ("resume_experiences", "resume_bullets", "resume_skills", "resume_languages")
            )

    before = counts()
    assert before[0] > 0
    command.downgrade(make_alembic_config(db), "0001_initial_schema")
    assert counts() == before
    assert runner.invoke(app, [*base, "db", "init"]).exit_code == 0
    assert counts() == before
