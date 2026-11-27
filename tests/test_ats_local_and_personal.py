"""Built-in ATS engine and personal (real-resume) mode."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from resumeforge.cli import app
from tools import ats_local
from tools.validate_resume import validate_resume_data

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "templates" / "my-resume.example.json"
JOB = ROOT / "templates" / "job-keywords.example.json"
runner = CliRunner()


def _template() -> dict:
    return json.loads(TEMPLATE.read_text())


def _job() -> dict:
    return json.loads(JOB.read_text())


def test_score_is_weighted_and_bounded() -> None:
    result = ats_local.score(_template(), _job())
    subs = result["sub_scores"]
    expected = sum(subs[k] * w for k, w in ats_local.WEIGHTS.items())
    assert abs(result["overall_score"] - round(expected, 1)) < 0.11
    assert 0 <= result["overall_score"] <= 100
    assert "Zendesk" in result["matched_keywords"]
    assert "Team Leadership" in result["missing_keywords"]


def test_missing_required_skill_lowers_score() -> None:
    job = _job()
    base = ats_local.score(_template(), job)["overall_score"]
    job["required_skills"] = job["required_skills"] + ["Salesforce Service Cloud", "Kustomer"]
    assert ats_local.score(_template(), job)["overall_score"] < base


def test_accepts_job_post_shape_and_spelling_variants() -> None:
    post = {"title": "Automation Engineer", "keywords": {"role": "Automation Engineer", "required_skills": ["Node.js"]}}
    resume = {"headline": "Automation Engineer", "skills": [{"name": "NodeJS"}], "experiences": []}
    result = ats_local.score(resume, post)
    # ATS filters are literal: a different spelling is a miss, with a hint to respell it.
    assert result["missing_keywords"] == ["Node.js"]
    assert any("different spelling" in r for r in result["recommendations"])
    assert result["sub_scores"]["title_match"] == 100.0
    assert "date_consistency" not in result["sub_scores"]  # no dates: unscorable, weight re-normalized


def test_text_resume_detects_sections_and_dates() -> None:
    text = (
        "Maria Santos\nSupport Team Lead\nmaria@mail.test | +63 917 123 4567\n"
        "Summary\nLead for SaaS support.\nExperience\nTeam Lead, Acme  Jul 2024 - Present\n"
        "Agent, Beta  Jan 2022 - Jun 2024\nEducation\nBS Business\nSkills\nZendesk, Google Sheets\n"
    )
    result = ats_local.score(text, _job())
    assert result["sub_scores"]["section_completeness"] == 100.0
    assert result["sub_scores"]["date_consistency"] == 100.0


def test_out_of_order_dates_penalized() -> None:
    data = _template()
    data["experiences"].reverse()
    assert ats_local.score(data, _job())["sub_scores"]["date_consistency"] < 100.0


def test_personal_mode_allows_real_contact_but_game_mode_does_not() -> None:
    data = _template()
    data["email"] = "maria.santos@gmail.com"
    data["phone"] = "+63 917 555 1234"
    game = validate_resume_data(data)
    personal = validate_resume_data(data, personal=True)
    assert any("non_synthetic_email" in e for e in game.errors)
    assert personal.valid, personal.errors


def test_personal_mode_still_enforces_quality() -> None:
    data = _template()
    data["professional_summary"] = "Results-driven [INSERT NAME] who leverages synergies."
    assert not validate_resume_data(data, personal=True).valid


def test_mine_cli_check_and_ats_score(tmp_path) -> None:
    resume = tmp_path / "resume.json"
    shutil.copyfile(TEMPLATE, resume)
    assert runner.invoke(app, ["mine", "check", str(resume)]).exit_code == 0
    res = runner.invoke(app, ["ats", "score", "--resume", str(resume), "--job", str(JOB), "--json"])
    assert res.exit_code == 0, res.output
    assert json.loads(res.output)["overall_score"] > 0


def test_parse_check_on_text_file(tmp_path) -> None:
    f = tmp_path / "resume.txt"
    f.write_text("Experience\nEducation\nSkills\nmaria@mail.test +63 917 123 4567\n" + "x " * 200)
    report = ats_local.parse_check(f)
    assert report["parse_check_ok"]
