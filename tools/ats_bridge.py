#!/usr/bin/env python3
"""Bridge between ResumeForge and an external Resume-Matcher install.

Resume-Matcher (https://github.com/srbhr/Resume-Matcher, Apache-2.0) supplies an
independent, deterministic (non-LLM) ATS score and a PDF parse check. ResumeForge
never vendors it: we shell out to its `resume-matcher` CLI, which reads one JSON
object on stdin and prints one JSON object on stdout.

Location of the Resume-Matcher backend is resolved from
`RESUMEFORGE_RESUME_MATCHER_DIR`, defaulting to `~/Developer/Resume-Matcher/apps/backend`.
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_RM_DIR = Path.home() / "Developer" / "Resume-Matcher" / "apps" / "backend"
RM_TIMEOUT_SECONDS = 180


class ResumeMatcherError(RuntimeError):
    """Raised when the Resume-Matcher CLI is missing or a tool call fails."""


def resume_matcher_dir() -> Path:
    raw = os.environ.get("RESUMEFORGE_RESUME_MATCHER_DIR", "").strip()
    return Path(raw).expanduser() if raw else DEFAULT_RM_DIR


def run_rm_tool(tool: str, args: dict[str, Any]) -> dict[str, Any]:
    """Invoke one Resume-Matcher CLI tool with JSON args and return its parsed JSON result."""
    rm_dir = resume_matcher_dir()
    if not (rm_dir / "pyproject.toml").exists():
        raise ResumeMatcherError(
            f"Resume-Matcher backend not found at {rm_dir}. "
            "Clone it (tag v1.4.0) and run `uv sync` there, or set RESUMEFORGE_RESUME_MATCHER_DIR."
        )
    try:
        proc = subprocess.run(
            ["uv", "run", "--quiet", "--directory", str(rm_dir), "resume-matcher", tool, "-"],
            input=json.dumps(args),
            capture_output=True,
            text=True,
            timeout=RM_TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError as exc:  # uv missing
        raise ResumeMatcherError("`uv` is not on PATH; it is required to run Resume-Matcher.") from exc
    except subprocess.TimeoutExpired as exc:
        raise ResumeMatcherError(f"Resume-Matcher tool `{tool}` timed out.") from exc
    if proc.returncode != 0:
        raise ResumeMatcherError(f"Resume-Matcher tool `{tool}` failed: {proc.stderr.strip()[-800:]}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise ResumeMatcherError(f"Resume-Matcher tool `{tool}` returned non-JSON output.") from exc


def _month_label(value: str) -> str:
    """`YYYY-MM` -> `Jan 2024` (Resume-Matcher penalizes mixed date formats); 'present' -> 'Present'."""
    cleaned = str(value).strip()
    if cleaned.lower() == "present":
        return "Present"
    try:
        return datetime.strptime(cleaned, "%Y-%m").strftime("%b %Y")
    except ValueError:
        return cleaned


def _years(start: str, end: str) -> str:
    return f"{_month_label(start)} - {_month_label(end)}"


def to_rm_resume_data(data: dict[str, Any]) -> dict[str, Any]:
    """Convert a serialized ResumeForge resume (`_serialize_resume`) into Resume-Matcher `ResumeData`."""
    city = str(data.get("city") or "").strip()
    region = str(data.get("region") or "").strip()
    location = city if (not region or city.lower() == region.lower()) else f"{city}, {region}"

    work = []
    for idx, exp in enumerate(data.get("experiences", []), start=1):
        work.append(
            {
                "id": idx,
                "title": exp["role_title"],
                "company": exp["company_name"],
                "location": exp.get("location") or "",
                "years": _years(exp["start_date"], exp["end_date"]),
                "description": [b["text"] for b in exp.get("bullets", [])],
            }
        )

    education = []
    for idx, edu in enumerate(data.get("education", []), start=1):
        degree = edu["degree"]
        if edu.get("field_of_study") and edu["field_of_study"].lower() not in degree.lower():
            degree = f"{degree} in {edu['field_of_study']}"
        start = edu.get("start_year")
        grad = edu.get("graduation_year")
        years = f"{start} - {grad}" if start else str(grad or "")
        desc = [edu["honors"]] if edu.get("honors") else []
        education.append(
            {"id": idx, "institution": edu["institution"], "degree": degree, "years": years, "description": desc}
        )

    projects = []
    for idx, proj in enumerate(data.get("projects", []), start=1):
        desc = [proj["summary"]]
        if proj.get("impact_metric"):
            desc.append(proj["impact_metric"])
        if proj.get("tech_stack"):
            desc.append("Stack: " + ", ".join(proj["tech_stack"]))
        projects.append(
            {
                "id": idx,
                "name": proj["name"],
                "role": proj.get("role") or "",
                "years": "",
                "website": proj.get("url") or "",
                "description": desc,
            }
        )

    return {
        "personalInfo": {
            "name": data["full_name"],
            "title": data["headline"],
            "email": data.get("email") or "",
            "phone": data.get("phone") or "",
            "location": location,
            "website": data.get("portfolio_url") or "",
            "linkedin": f"linkedin.com/in/{data['linkedin_slug']}" if data.get("linkedin_slug") else "",
        },
        "summary": data.get("professional_summary") or "",
        "workExperience": work,
        "education": education,
        "personalProjects": projects,
        "additional": {
            "technicalSkills": [s["name"] for s in data.get("skills", [])],
            "languages": [f"{l['language']} ({l['proficiency']})" for l in data.get("languages", [])],
            "certificationsTraining": [
                f"{c['name']} ({c['issuer']}, {c['year_earned']})" for c in data.get("certifications", [])
            ],
            "awards": [],
        },
    }


def score_resume(data: dict[str, Any], keywords: dict[str, Any]) -> dict[str, Any]:
    """Score a serialized ResumeForge resume against extracted job keywords (no state saved in Resume-Matcher)."""
    return run_rm_tool("score_resume", {"resume_data": to_rm_resume_data(data), "keywords": keywords})


def parse_check_pdf(pdf_path: Path) -> dict[str, Any]:
    """Run Resume-Matcher's ATS parse check on a rendered PDF."""
    return run_rm_tool("parse_check_file", {"file_path": str(Path(pdf_path).resolve())})


def tool_version() -> str:
    try:
        return str(run_rm_tool("get_status", {}).get("version", "unknown"))
    except ResumeMatcherError:
        return "unknown"
