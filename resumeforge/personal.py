"""Personal mode: build, check, render and ATS-score a real person's OWN resume.

Everything here works on local JSON files under `my_resumes/` (git-ignored) and
never touches the game database. The game pipeline (`resumeforge resume ...`)
stays synthetic-only; this is the path for "make my resume".
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

import typer
from rich.console import Console

from resumeforge.config import REPO_ROOT, get_ats_min_score

console = Console()
err_console = Console(stderr=True)

MY_RESUMES_DIR = REPO_ROOT / "my_resumes"
TEMPLATE_PATH = REPO_ROOT / "templates" / "my-resume.example.json"

mine_app = typer.Typer(help="Your own real resume: local files only, never stored in the game DB", no_args_is_help=True)
ats_app = typer.Typer(help="Standalone ATS checker for any resume file (JSON, PDF, DOCX, TXT)", no_args_is_help=True)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "resume"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        err_console.print(f"[red]File not found:[/red] {path}")
        raise typer.Exit(code=1)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        err_console.print(f"[red]Invalid JSON in {path}:[/red] {exc}")
        raise typer.Exit(code=1) from exc


def _render(data: dict[str, Any], out_pdf: Path, one_page: bool) -> tuple[Path, bool]:
    """Render to PDF with Chrome; fall back to an HTML file the user can print to PDF."""
    from tools.render_pdf import build_resume_html, render_html_to_pdf

    html = build_resume_html(data, one_page=one_page)
    try:
        render_html_to_pdf(html, out_pdf)
        return out_pdf, True
    except FileNotFoundError:
        out_html = out_pdf.with_suffix(".html")
        out_html.write_text(html, encoding="utf-8")
        return out_html, False


def _print_score(result: dict[str, Any], parse: dict[str, Any] | None) -> None:
    threshold = get_ats_min_score()
    score = result["overall_score"]
    ok = score >= threshold and (parse is None or parse["parse_check_ok"])
    color = "green" if ok else "yellow"
    console.print(f"[{color}]ATS score {score:.1f}/100[/{color}] (target {threshold:.0f}+)")
    console.print("  " + ", ".join(f"{k}={v}" for k, v in result["sub_scores"].items()))
    if result["missing_keywords"]:
        console.print("  missing: " + ", ".join(result["missing_keywords"]))
    for rec in result["recommendations"]:
        console.print(f"  - {rec}")
    if parse is not None:
        state = "[green]ok[/green]" if parse["parse_check_ok"] else "[red]FAILED[/red]"
        console.print(f"  PDF parse check {state} ({parse['parse_score']:.0f}/100, {parse['page_count']} page(s))")
        for issue in parse["parse_issues"]:
            console.print(f"  ! {issue}")


# --------------------------------------------------------------------------- mine


@mine_app.command("new")
def mine_new(name: str = typer.Argument(..., help="Your name or a label, e.g. 'maria-santos'")) -> None:
    """Create my_resumes/<name>/resume.json from the example template."""
    folder = MY_RESUMES_DIR / _slug(name)
    target = folder / "resume.json"
    if target.exists():
        err_console.print(f"[yellow]Already exists:[/yellow] {target}")
        raise typer.Exit(code=1)
    folder.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TEMPLATE_PATH, target)
    console.print(f"Created {target.relative_to(REPO_ROOT)}")


@mine_app.command("check")
def mine_check(path: Path, as_json: bool = typer.Option(False, "--json")) -> None:
    """Run every quality check on your resume (real contact details allowed)."""
    from tools.validate_resume import validate_resume_data

    result = validate_resume_data(_load_json(path), personal=True).to_dict()
    if as_json:
        typer.echo(json.dumps(result, indent=2))
    else:
        state = "[green]PASS[/green]" if result["valid"] else "[red]FAIL[/red]"
        console.print(f"{state} {path}")
        for e in result["errors"]:
            console.print(f"  [red]error[/red] {e}")
        for w in result["warnings"]:
            console.print(f"  [yellow]warn[/yellow]  {w}")
    if not result["valid"]:
        raise typer.Exit(code=1)


@mine_app.command("render")
def mine_render(
    path: Path,
    out: Path | None = typer.Option(None, "--out", help="Output PDF (default: next to the JSON)"),
    one_page: bool = typer.Option(False, "--one-page", help="Compact one-page layout"),
) -> None:
    """Render your resume to an ATS-safe single-column PDF."""
    data = _load_json(path)
    out_pdf = out or path.with_name(f"{_slug(data.get('full_name', 'resume'))}-resume.pdf")
    written, is_pdf = _render(data, out_pdf, one_page)
    if is_pdf:
        console.print(f"Rendered {written}")
    else:
        console.print(f"[yellow]Chrome not found.[/yellow] Wrote {written}: open it in any browser and Print > Save as PDF.")


@mine_app.command("ats")
def mine_ats(
    path: Path,
    job: Path = typer.Option(..., "--job", help="Job keywords JSON (or a job-post JSON with a 'keywords' object)"),
    one_page: bool = typer.Option(False, "--one-page"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Render your resume, ATS-score it against a job post, and parse-check the PDF."""
    from tools import ats_local

    data = _load_json(path)
    keywords = _load_json(job)
    result = ats_local.score(data, keywords)
    out_pdf = path.with_name(f"{_slug(data.get('full_name', 'resume'))}-resume.pdf")
    written, is_pdf = _render(data, out_pdf, one_page)
    parse = ats_local.parse_check(written, expected_name=data.get("full_name")) if is_pdf else None
    report = {**result, "pdf": str(written), "parse": parse}
    path.with_name(f"ats-report-{_slug(job.stem)}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if as_json:
        typer.echo(json.dumps(report, indent=2))
    else:
        _print_score(result, parse)
        if not is_pdf:
            console.print("[yellow]Chrome not found, so the PDF parse check was skipped.[/yellow]")


# --------------------------------------------------------------------------- ats


@ats_app.command("score")
def ats_score(
    resume: Path = typer.Option(..., "--resume", help="Resume as JSON, PDF, DOCX or TXT"),
    job: Path = typer.Option(..., "--job", help="Job keywords JSON (or a job-post JSON)"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Score ANY resume file against a job post (no database, nothing stored)."""
    from tools import ats_local

    if not resume.exists():
        err_console.print(f"[red]File not found:[/red] {resume}")
        raise typer.Exit(code=1)
    result = ats_local.score(ats_local.load_resume_input(resume), _load_json(job))
    parse = ats_local.parse_check(resume) if resume.suffix.lower() in {".pdf", ".docx"} else None
    if as_json:
        typer.echo(json.dumps({**result, "parse": parse}, indent=2))
    else:
        _print_score(result, parse)
