#!/usr/bin/env python3
"""Render any ResumeForge SQL resume into a clean, ATS-ready single-column PDF."""

from __future__ import annotations

import argparse
import html
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from resumeforge.cli import _load_resume_with_children, _serialize_resume  # noqa: E402
from resumeforge.db.engine import session_scope  # noqa: E402

DEFAULT_CHROME_PATHS = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
)


def _format_ym(value: str) -> str:
    """Convert YYYY-MM or 'present' to a readable resume month-year label."""
    cleaned = value.strip()
    if cleaned.lower() == "present":
        return "Present"
    try:
        dt = datetime.strptime(cleaned, "%Y-%m")
    except ValueError:
        return cleaned
    return dt.strftime("%b %Y")


def _format_date_range(start_date: str, end_date: str) -> str:
    return f"{_format_ym(start_date)} – {_format_ym(end_date)}"


def _clean_portfolio_display(url: str) -> str:
    stripped = url.strip()
    for prefix in ("https://", "http://"):
        if stripped.startswith(prefix):
            return stripped[len(prefix) :]
    return stripped


def _esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def _find_chrome_binary(override: str | None = None) -> str:
    if override:
        if Path(override).exists():
            return override
        raise FileNotFoundError(f"Chrome binary not found at {override}")
    for candidate in DEFAULT_CHROME_PATHS:
        if Path(candidate).exists():
            return candidate
    for name in ("google-chrome", "chromium", "chromium-browser"):
        found = shutil.which(name)
        if found:
            return found
    raise FileNotFoundError("Google Chrome / Chromium binary not found for headless PDF rendering.")


def _clean_github_handle(raw: str) -> str:
    cleaned = raw.strip().rstrip("/")
    for prefix in ("https://github.com/", "http://github.com/", "github.com/", "@"):
        if cleaned.lower().startswith(prefix):
            cleaned = cleaned[len(prefix) :]
    return cleaned.strip("/")


def build_resume_html(
    data: dict[str, Any],
    *,
    one_page: bool = False,
    github_handle: str | None = None,
    email_override: str | None = None,
    phone_override: str | None = None,
) -> str:
    """Build single-column, ATS-parseable executive HTML for a ResumeForge record."""
    city_str = str(data.get("city") or "").strip()
    region_str = str(data.get("region") or "").strip()
    location_display = (
        _esc(city_str)
        if city_str.lower() == region_str.lower() or not region_str
        else f"{_esc(city_str)}, {_esc(region_str)}"
    )
    email_display = email_override.strip() if email_override and email_override.strip() else data["email"]
    phone_display = phone_override.strip() if phone_override and phone_override.strip() else data["phone"]
    primary_contact = [
        location_display,
        _esc(email_display),
        _esc(phone_display),
    ]
    links_parts: list[str] = []
    if github_handle:
        cleaned_gh = _clean_github_handle(github_handle)
        if cleaned_gh:
            links_parts.append(f"GitHub: github.com/{_esc(cleaned_gh)}")
    if data.get("linkedin_slug"):
        links_parts.append(f"LinkedIn: /in/{_esc(data['linkedin_slug'])}")
    if data.get("portfolio_url"):
        links_parts.append(f"Portfolio: {_esc(_clean_portfolio_display(data['portfolio_url']))}")

    contact_line_one = " · ".join(primary_contact)
    contact_line_two = " · ".join(
        [
            *links_parts,
            f"<strong>Work Setup:</strong> {_esc(data['work_setup_preference'])}",
            f"<strong>Timezone:</strong> {_esc(data['timezone_readiness'])}",
        ]
    )

    skills_by_cat: dict[str, list[str]] = {}
    for sk in data.get("skills", []):
        skills_by_cat.setdefault(sk["category"], []).append(sk["name"])

    skill_rows_html = "\n".join(
        f'<div class="skill-row"><span class="skill-cat">{_esc(cat)}:</span> '
        f'<span class="skill-items">{_esc(", ".join(names))}</span></div>'
        for cat, names in skills_by_cat.items()
    )

    exp_blocks: list[str] = []
    for exp in data.get("experiences", []):
        bullets_html = "\n".join(
            f"<li>{_esc(b['text'])}</li>" for b in exp.get("bullets", [])
        )
        date_label = _format_date_range(exp["start_date"], exp["end_date"])
        exp_sub_text = (
            f"{_esc(exp['location'])} · {_esc(exp['employment_type'])}"
            if one_page
            else f"{_esc(exp['location'])} · {_esc(exp['employment_type'])} · {_esc(exp['company_archetype'])}"
        )
        exp_blocks.append(
            f"""
            <article class="exp-item">
              <div class="row-between">
                <div class="exp-title">
                  <span class="role-title">{_esc(exp['role_title'])}</span>
                  <span class="sep">|</span>
                  <span class="company-name">{_esc(exp['company_name'])}</span>
                </div>
                <div class="date-range">{_esc(date_label)}</div>
              </div>
              <div class="exp-sub">{exp_sub_text}</div>
              <ul class="bullet-list">
                {bullets_html}
              </ul>
            </article>
            """
        )

    projects_html = ""
    if data.get("projects"):
        projects_heading = (
            "Selected GEO Projects"
            if data.get("niche_slug") == "geo-ai-search"
            else "Featured Projects"
        )
        proj_items: list[str] = []
        for proj in data["projects"]:
            stack = ", ".join(proj.get("tech_stack") or [])
            impact_html = (
                f'<div class="proj-impact"><strong>Impact:</strong> {_esc(proj["impact_metric"])}</div>'
                if proj.get("impact_metric")
                else ""
            )
            if one_page:
                stack_inline = (
                    f'<span class="proj-stack-inline"> | {_esc(stack)}</span>' if stack else ""
                )
                proj_items.append(
                    f"""
                    <article class="proj-item">
                      <div class="row-between">
                        <div class="proj-title"><strong>{_esc(proj['name'])}</strong>{stack_inline}</div>
                        <div class="proj-role">{_esc(proj['role'])}</div>
                      </div>
                      <p class="proj-summary">{_esc(proj['summary'])}</p>
                      {impact_html}
                    </article>
                    """
                )
            else:
                stack_html = f'<div class="proj-stack">Stack: {_esc(stack)}</div>' if stack else ""
                proj_items.append(
                    f"""
                    <article class="proj-item">
                      <div class="row-between">
                        <div class="proj-title"><strong>{_esc(proj['name'])}</strong></div>
                        <div class="proj-role">{_esc(proj['role'])}</div>
                      </div>
                      {stack_html}
                      <p class="proj-summary">{_esc(proj['summary'])}</p>
                      {impact_html}
                    </article>
                    """
                )
        projects_html = f"""
        <section class="section">
          <h2>{projects_heading}</h2>
          {''.join(proj_items)}
        </section>
        """

    edu_items: list[str] = []
    for edu in data.get("education", []):
        yr_range = (
            f"{edu['start_year']} – {edu['graduation_year']}"
            if edu.get("start_year")
            else str(edu["graduation_year"])
        )
        honors_html = f" · <em>{_esc(edu['honors'])}</em>" if edu.get("honors") else ""
        coursework = edu.get("relevant_coursework") or []
        coursework_html = (
            f'<div class="edu-coursework"><strong>Relevant Coursework:</strong> {_esc(", ".join(coursework))}</div>'
            if coursework
            else ""
        )
        edu_items.append(
            f"""
            <article class="edu-item">
              <div class="row-between">
                <div><strong>{_esc(edu['institution'])}</strong> — {_esc(edu['location'])}</div>
                <div class="date-range">{_esc(yr_range)}</div>
              </div>
              <div class="edu-sub">{_esc(edu['degree'])} in {_esc(edu['field_of_study'])}{honors_html}</div>
              {coursework_html}
            </article>
            """
        )

    certs = data.get("certifications") or []
    langs = data.get("languages") or []
    creds_html = ""
    if certs or langs:
        if certs and langs:
            creds_heading = "Certifications &amp; Languages"
        elif certs:
            creds_heading = "Certifications"
        else:
            creds_heading = "Languages"

        cert_list_html = ""
        if certs:
            cert_lis = "\n".join(
                f"<li><strong>{_esc(c['name'])}</strong> — {_esc(c['issuer'])} ({_esc(c['year_earned'])})</li>"
                for c in certs
            )
            cert_list_html = f'<ul class="cert-list">{cert_lis}</ul>'
        lang_line_html = ""
        if langs:
            lang_joined = " · ".join(
                f"{_esc(l['language'])} ({_esc(l['proficiency'])})" for l in langs
            )
            if one_page and not certs:
                lang_line_html = f'<div class="lang-line">{lang_joined}</div>'
            else:
                lang_line_html = f'<div class="lang-line"><strong>Languages:</strong> {lang_joined}</div>'
        creds_html = f"""
        <section class="section">
          <h2>{creds_heading}</h2>
          {cert_list_html}
          {lang_line_html}
        </section>
        """

    one_page_css = """
  @page {
    size: letter;
    margin: 0.30in 0.44in;
  }
  body {
    font-size: 8.45pt;
    line-height: 1.23;
  }
  header {
    margin-bottom: 4.5pt;
  }
  h1 {
    font-size: 17.5pt;
  }
  .headline {
    font-size: 9.4pt;
    margin-bottom: 2pt;
  }
  .contact-bar, .setup-bar {
    font-size: 8pt;
    line-height: 1.22;
  }
  .section {
    margin-top: 5.2pt;
  }
  h2 {
    font-size: 8.6pt;
    margin-bottom: 2.5pt;
    padding-bottom: 1pt;
  }
  .summary {
    font-size: 8.45pt;
    line-height: 1.24;
  }
  .skill-row {
    font-size: 8.25pt;
    line-height: 1.22;
    margin-bottom: 1.2pt;
  }
  .exp-item {
    margin-bottom: 4.5pt;
  }
  .exp-title {
    font-size: 8.9pt;
  }
  .exp-sub {
    font-size: 7.9pt;
    margin: 0.5pt 0 1.5pt 0;
  }
  .bullet-list li {
    font-size: 8.35pt;
    line-height: 1.22;
    margin-bottom: 1.3pt;
  }
  .proj-item {
    margin-bottom: 3.2pt;
  }
  .proj-title {
    font-size: 8.5pt;
  }
  .proj-stack-inline {
    font-weight: 500;
    font-size: 8pt;
    color: #4B5563;
  }
  .proj-summary {
    font-size: 8.25pt;
    line-height: 1.21;
    margin: 0.6pt 0;
  }
  .proj-impact {
    font-size: 8pt;
    color: #1E3A5F;
  }
  .edu-item {
    font-size: 8.4pt;
  }
  .lang-line {
    font-size: 8.25pt;
  }
""" if one_page else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{_esc(data['full_name'])} - {_esc(data['target_role_title'])}</title>
<style>
  @page {{
    size: letter;
    margin: 0.48in 0.55in;
  }}
  * {{
    box-sizing: border-box;
  }}
  body {{
    font-family: "Helvetica Neue", -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
    color: #111827;
    font-size: 9.4pt;
    line-height: 1.38;
    margin: 0;
    padding: 0;
    /* Keep the PDF text layer ATS-clean: no fi/fl ligature glyphs, no automatic hyphenation. */
    font-variant-ligatures: none;
    hyphens: manual;
  }}
  header {{
    margin-bottom: 10pt;
  }}
  h1 {{
    font-size: 20pt;
    font-weight: 700;
    letter-spacing: -0.2pt;
    color: #1E3A5F;
    margin: 0 0 2pt 0;
    line-height: 1.12;
  }}
  .headline {{
    font-size: 10.5pt;
    font-weight: 600;
    color: #1E3A5F;
    margin: 0 0 4pt 0;
  }}
  .contact-bar {{
    font-size: 8.6pt;
    color: #374151;
    margin: 0 0 2pt 0;
  }}
  .setup-bar {{
    font-size: 8.6pt;
    color: #4B5563;
    margin: 0;
  }}
  .section {{
    margin-top: 9pt;
  }}
  h2 {{
    font-size: 9.4pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.9pt;
    color: #1E3A5F;
    border-bottom: 1pt solid #1E3A5F;
    padding-bottom: 2pt;
    margin: 0 0 5.5pt 0;
  }}
  .summary {{
    font-size: 9.4pt;
    line-height: 1.42;
    margin: 0;
    color: #111827;
  }}
  .skill-row {{
    font-size: 9pt;
    line-height: 1.36;
    margin-bottom: 2pt;
  }}
  .skill-cat {{
    font-weight: 700;
    color: #111827;
  }}
  .skill-items {{
    color: #1F2937;
  }}
  .exp-item {{
    margin-bottom: 8pt;
    break-inside: avoid;
  }}
  .exp-item:last-child {{
    margin-bottom: 0;
  }}
  .row-between {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 10pt;
  }}
  .exp-title {{
    font-size: 9.8pt;
    color: #111827;
  }}
  .role-title {{
    font-weight: 700;
  }}
  .sep {{
    color: #6B7280;
    margin: 0 3pt;
  }}
  .company-name {{
    font-weight: 600;
    color: #1E3A5F;
  }}
  .date-range, .proj-role {{
    font-size: 8.7pt;
    font-weight: 600;
    color: #374151;
    white-space: nowrap;
  }}
  .exp-sub, .edu-sub {{
    font-size: 8.6pt;
    font-style: italic;
    color: #4B5563;
    margin: 1pt 0 3pt 0;
  }}
  .bullet-list {{
    margin: 0;
    padding-left: 14pt;
  }}
  .bullet-list li {{
    font-size: 9.2pt;
    line-height: 1.35;
    margin-bottom: 2.6pt;
    color: #111827;
  }}
  .bullet-list li:last-child {{
    margin-bottom: 0;
  }}
  .proj-item {{
    margin-bottom: 6pt;
    break-inside: avoid;
  }}
  .proj-item:last-child {{
    margin-bottom: 0;
  }}
  .proj-title {{
    font-size: 9.4pt;
    color: #111827;
  }}
  .proj-stack {{
    font-size: 8.5pt;
    font-style: italic;
    color: #4B5563;
    margin: 1pt 0 2pt 0;
  }}
  .proj-summary {{
    font-size: 9pt;
    line-height: 1.35;
    margin: 1.5pt 0 1.5pt 0;
    color: #111827;
  }}
  .proj-impact {{
    font-size: 8.9pt;
    color: #1E3A5F;
  }}
  .edu-item {{
    break-inside: avoid;
    font-size: 9.2pt;
  }}
  .edu-coursework {{
    font-size: 8.8pt;
    color: #374151;
    margin-top: 1.5pt;
  }}
  .cert-list {{
    margin: 0 0 4pt 0;
    padding-left: 14pt;
  }}
  .cert-list li {{
    font-size: 9pt;
    line-height: 1.34;
    margin-bottom: 2pt;
  }}
  .lang-line {{
    font-size: 9pt;
    color: #111827;
  }}{one_page_css}
</style>
</head>
<body>
  <header>
    <h1>{_esc(data['full_name'])}</h1>
    <div class="headline">{_esc(data['headline'])}</div>
    <p class="contact-bar">{contact_line_one}</p>
    <p class="setup-bar">{contact_line_two}</p>
  </header>

  <section class="section">
    <h2>Professional Summary</h2>
    <p class="summary">{_esc(data['professional_summary'])}</p>
  </section>

  <section class="section">
    <h2>Core Skills</h2>
    {skill_rows_html}
  </section>

  <section class="section">
    <h2>Professional Experience</h2>
    {''.join(exp_blocks)}
  </section>

  {projects_html}

  <section class="section">
    <h2>Education</h2>
    {''.join(edu_items)}
  </section>

  {creds_html}
</body>
</html>
"""


def render_html_to_pdf(
    html_content: str,
    out_path: Path,
    *,
    chrome_bin: str | None = None,
) -> None:
    """Render an HTML string to a PDF file using headless Chrome with an isolated temp profile."""
    chrome = _find_chrome_binary(chrome_bin)
    out_resolved = out_path.resolve()
    out_resolved.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="resumeforge_pdf_") as tmpdir:
        tmp_path = Path(tmpdir)
        html_file = tmp_path / "resume.html"
        profile_dir = tmp_path / "chrome_profile"
        html_file.write_text(html_content, encoding="utf-8")

        cmd = [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--user-data-dir={profile_dir}",
            f"--print-to-pdf={out_resolved}",
            html_file.as_uri(),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if proc.returncode != 0 or not out_resolved.exists():
            raise RuntimeError(
                f"Headless Chrome PDF render failed (code {proc.returncode}): {proc.stderr.strip()}"
            )


def render_resume_pdf(
    resume_code: str,
    out_path: Path,
    *,
    db_url: str | None = None,
    chrome_bin: str | None = None,
    one_page: bool = False,
    github_handle: str | None = None,
    email_override: str | None = None,
    phone_override: str | None = None,
) -> Path:
    """Fetch a resume by code from SQLite and render it to a PDF file."""
    with session_scope(db_url, read_only=True) as session:
        resume = _load_resume_with_children(session, resume_code)
        if resume is None:
            raise ValueError(f"Resume not found in SQL: {resume_code}")
        data = _serialize_resume(resume)

    html_content = build_resume_html(
        data,
        one_page=one_page,
        github_handle=github_handle,
        email_override=email_override,
        phone_override=phone_override,
    )
    render_html_to_pdf(html_content, out_path, chrome_bin=chrome_bin)
    return out_path


def _main() -> int:
    parser = argparse.ArgumentParser(description="Render a ResumeForge SQL resume to an ATS PDF")
    parser.add_argument("resume_code", help="Resume code in SQL (e.g. PH-GEO-SEN-001)")
    parser.add_argument("--out", default=None, help="Output PDF path")
    parser.add_argument("--db", default=None, help="Optional database path or SQLAlchemy URL")
    parser.add_argument("--chrome", default=None, help="Optional Chrome/Chromium binary path")
    parser.add_argument("--one-page", action="store_true", help="Use compact 1-page ATS print layout")
    parser.add_argument(
        "--github",
        default=None,
        help="Optional GitHub handle to display in header (e.g. eys-55)",
    )
    parser.add_argument(
        "--email",
        default=None,
        help="Optional email override for personal PDF export (not persisted to SQL)",
    )
    parser.add_argument(
        "--phone",
        default=None,
        help="Optional phone override for personal PDF export (not persisted to SQL)",
    )
    args = parser.parse_args()

    out_path = Path(args.out) if args.out else Path("exports") / f"{args.resume_code}.pdf"
    rendered = render_resume_pdf(
        args.resume_code,
        out_path,
        db_url=args.db,
        chrome_bin=args.chrome,
        one_page=args.one_page,
        github_handle=args.github,
        email_override=args.email,
        phone_override=args.phone,
    )
    print(f"Rendered PDF: {rendered}")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
