#!/usr/bin/env python3
"""Built-in deterministic ATS checker (no LLM, no external install).

Scores a resume against a job post's keywords with the same five weighted
dimensions Resume-Matcher uses, so results are comparable:

    keyword_match 40% | skills_match 20% | title_match 15% | section_completeness 15% | date_consistency 10%

and parse-checks a rendered PDF the way an ATS reads it (text layer only).

Inputs:
- resume: a ResumeForge resume dict (import/serialized JSON shape), or plain text
  extracted from someone's existing PDF/DOCX/TXT resume.
- keywords: `{"role": str, "required_skills": [...], "preferred_skills": [...],
  "keywords": [...], "experience_requirements": [...]}`. A stored job-post JSON
  (`data/job_posts/*.json`) also works: its `keywords` object is used.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

ENGINE_NAME = "resumeforge-ats"
ENGINE_VERSION = "1.0.0"

WEIGHTS = {
    "keyword_match": 0.40,
    "skills_match": 0.20,
    "title_match": 0.15,
    "section_completeness": 0.15,
    "date_consistency": 0.10,
}

TITLE_STOPWORDS = {"a", "an", "and", "the", "of", "for", "in", "to", "at", "&"}
_YEAR = r"(?:19|20)\d{2}"
_MONTH = (r"(?i:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?"
          r"|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)")
DATE_STYLE_RE = re.compile(
    rf"(?P<iso>\b{_YEAR}[-/]\d{{1,2}}\b)|(?P<numeric>\b\d{{1,2}}[/.-]{_YEAR}\b)"
    rf"|(?P<name_year>\b{_MONTH}\.?,?\s+{_YEAR}\b)|(?P<name_short_year>\b{_MONTH}\.?\s+'\d{{2}}\b)"
    rf"|(?P<year>\b{_YEAR}\b)"
)

SECTION_HEADINGS = {
    "summary": ("summary", "profile", "professional summary", "about"),
    "experience": ("experience", "work experience", "employment", "professional experience", "work history"),
    "education": ("education", "academic"),
    "skills": ("skills", "technical skills", "core skills", "competencies", "tools"),
}

LIGATURES = ("ﬀ", "ﬁ", "ﬂ", "ﬃ", "ﬄ")
MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
PHONE_RE = re.compile(r"(\+?\d[\d\s().-]{7,}\d)")
TEXT_DATE_RANGE_RE = re.compile(
    r"(?P<sm>[A-Za-z]{3,9})\.?\s+(?P<sy>\d{4})\s*[-–—to]+\s*"
    r"(?:(?P<em>[A-Za-z]{3,9})\.?\s+(?P<ey>\d{4})|(?P<present>present|current|now))",
    re.IGNORECASE,
)


# --------------------------------------------------------------------------- normalization


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "").lower()
    text = text.replace("’", "'").replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", text)


def _variants(term: str) -> list[str]:
    """Spellings an ATS would treat as the same term (`Node.js` ~ `nodejs` ~ `node js`)."""
    base = _norm(term).strip()
    out = {base, base.replace(".", ""), base.replace(".", " "), base.replace("-", " "), base.replace("-", "")}
    paren = re.match(r"^(.*?)\s*\((.*?)\)\s*$", base)  # "GoHighLevel (GHL)" -> both parts
    if paren:
        out.update({paren.group(1).strip(), paren.group(2).strip()})
    return [v for v in out if v]


def _literal(haystack: str, term: str) -> bool:
    """Whole-word, case-insensitive match of the posting's exact spelling (how ATS filters search)."""
    t = _norm(term).strip()
    return bool(t) and re.search(r"(?<!\w)" + re.escape(t) + r"(?!\w)", haystack) is not None


def _near_spelling(haystack: str, term: str) -> bool:
    """True when the term appears only under another spelling (`NodeJS` for `Node.js`)."""
    for v in _variants(term):
        if re.search(r"(?<![a-z0-9])" + re.escape(v).replace(r"\ ", r"[\s\-/]?") + r"(?![a-z0-9])", haystack):
            return True
    return False


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[^\W_]+", _norm(text)) if t not in TITLE_STOPWORDS}


# --------------------------------------------------------------------------- resume view


@dataclass
class ResumeView:
    full_text: str
    headline: str
    summary: str
    date_strings: list[str]
    skills_text: str
    sections: set[str]
    date_ranges: list[tuple[int | None, int | None, bool]]  # (start_idx, end_idx, is_current)
    has_email: bool
    has_phone: bool
    notes: list[str] = field(default_factory=list)


def _ym_index(value: str) -> int | None:
    try:
        d = datetime.strptime(str(value).strip(), "%Y-%m")
        return d.year * 12 + d.month
    except ValueError:
        return None


def _label(value: str) -> str:
    """Render `YYYY-MM` as the PDF does (`Jan 2024`); `present` stays as is."""
    try:
        return datetime.strptime(value.strip(), "%Y-%m").strftime("%b %Y")
    except ValueError:
        return value.strip().title()


def view_from_structured(data: dict[str, Any]) -> ResumeView:
    parts: list[str] = [data.get("full_name", ""), data.get("headline", ""), data.get("target_role_title", ""),
                        data.get("professional_summary", "")]
    ranges: list[tuple[int | None, int | None, bool]] = []
    date_strings: list[str] = []
    for exp in data.get("experiences") or []:
        date_strings.append(f"{_label(exp.get('start_date', ''))} - {_label(str(exp.get('end_date') or ''))}")
        parts += [exp.get("role_title", ""), exp.get("company_name", "")]
        parts += [b.get("text", "") if isinstance(b, dict) else str(b) for b in exp.get("bullets") or []]
        end = str(exp.get("end_date") or "")
        current = bool(exp.get("is_current")) or end.lower() == "present"
        ranges.append((_ym_index(exp.get("start_date", "")), None if current else _ym_index(end), current))
    skills = [s.get("name", "") if isinstance(s, dict) else str(s) for s in data.get("skills") or []]
    parts += skills
    for proj in data.get("projects") or []:
        parts += [proj.get("name", ""), proj.get("summary", ""), proj.get("impact_metric") or "",
                  " ".join(proj.get("tech_stack") or [])]
    for cert in data.get("certifications") or []:
        parts += [cert.get("name", ""), cert.get("issuer", "")]
    for edu in data.get("education") or []:
        sy, gy = edu.get("start_year"), edu.get("graduation_year")
        date_strings.append(f"{sy} - {gy}" if sy else str(gy or ""))
        parts += [edu.get("degree", ""), edu.get("field_of_study") or "", edu.get("institution", "")]

    sections = set()
    if str(data.get("professional_summary") or "").strip():
        sections.add("summary")
    if data.get("experiences"):
        sections.add("experience")
    if data.get("education"):
        sections.add("education")
    if skills:
        sections.add("skills")
    return ResumeView(
        full_text=_norm(" \n ".join(str(p) for p in parts if p)),
        headline=_norm(str(data.get("headline") or "")),
        summary=_norm(str(data.get("professional_summary") or "")),
        date_strings=date_strings,
        skills_text=_norm(" | ".join(skills)),
        sections=sections,
        date_ranges=ranges,
        has_email=bool(EMAIL_RE.search(str(data.get("email") or ""))),
        has_phone=bool(str(data.get("phone") or "").strip()),
    )


def _detect_headings(lines: list[str]) -> set[str]:
    found = set()
    for line in lines:
        clean = _norm(line).strip(" :")
        if not clean or len(clean) > 40:
            continue
        for section, names in SECTION_HEADINGS.items():
            if clean in names or any(clean.startswith(n) for n in names):
                found.add(section)
    return found


def view_from_text(text: str) -> ResumeView:
    lines = [ln for ln in (text or "").splitlines() if ln.strip()]
    sections = _detect_headings(lines)
    ranges: list[tuple[int | None, int | None, bool]] = []
    for m in TEXT_DATE_RANGE_RE.finditer(text or ""):
        sm = MONTHS.get(m.group("sm")[:3].lower())
        start = int(m.group("sy")) * 12 + sm if sm else None
        if m.group("present"):
            ranges.append((start, None, True))
        else:
            em = MONTHS.get((m.group("em") or "")[:3].lower())
            ranges.append((start, int(m.group("ey")) * 12 + em if em else None, False))
    skills_block: list[str] = []
    capture = False
    for line in lines:
        heading = _detect_headings([line])
        if heading:
            capture = "skills" in heading
            continue
        if capture:
            skills_block.append(line)
    return ResumeView(
        full_text=_norm(text),
        headline=_norm(" ".join(lines[1:3])),
        summary=_norm(" ".join(lines[:12])),
        date_strings=[m.group(0) for m in TEXT_DATE_RANGE_RE.finditer(text or "")],
        skills_text=_norm(" ".join(skills_block)) or _norm(text),
        sections=sections,
        date_ranges=ranges,
        has_email=bool(EMAIL_RE.search(text or "")),
        has_phone=bool(PHONE_RE.search(text or "")),
        notes=[] if skills_block else ["No Skills heading detected; skills were matched against the full text."],
    )


# --------------------------------------------------------------------------- scoring


def normalize_keywords(raw: dict[str, Any]) -> dict[str, Any]:
    kw = raw.get("keywords") if isinstance(raw.get("keywords"), dict) else raw
    role = kw.get("role") or raw.get("title") or ""
    return {
        "role": str(role),
        "required_skills": [str(s) for s in kw.get("required_skills") or []],
        "preferred_skills": [str(s) for s in kw.get("preferred_skills") or []],
        "keywords": [str(s) for s in (kw.get("keywords") if isinstance(kw.get("keywords"), list) else []) or []],
    }


def _date_consistency(view: ResumeView) -> tuple[float | None, list[str]]:
    """Share of dates in the dominant format (as Resume-Matcher), minus 25 per chronology problem."""
    issues: list[str] = []
    styles: dict[str, int] = {}
    for value in view.date_strings:
        for m in DATE_STYLE_RE.finditer(value):
            styles[m.lastgroup] = styles.get(m.lastgroup, 0) + 1
    total = sum(styles.values())
    fmt = 100.0 * max(styles.values()) / total if total >= 2 else None
    if fmt is not None and fmt < 100:
        issues.append('Write every date in one format (e.g. "Jan 2020 - Mar 2023", including education).')
    for start, end, current in view.date_ranges:
        if start is None or (end is None and not current):
            issues.append("A job has a missing or unreadable date.")
        elif end is not None and end < start:
            issues.append("A job ends before it starts.")
    starts = [r[0] for r in view.date_ranges if r[0] is not None]
    if starts != sorted(starts, reverse=True):
        issues.append("Jobs are not in reverse-chronological order (newest first).")
    chronology_issues = len(issues) - (1 if fmt is not None and fmt < 100 else 0)
    if fmt is None and not view.date_ranges:
        return None, issues
    return max(0.0, (fmt if fmt is not None else 100.0) - 25.0 * chronology_issues), issues


def score(resume: dict[str, Any] | str, keywords: dict[str, Any]) -> dict[str, Any]:
    """Return {overall_score, sub_scores, matched_keywords, missing_keywords, recommendations}."""
    view = view_from_text(resume) if isinstance(resume, str) else view_from_structured(resume)
    kw = normalize_keywords(keywords)
    required, preferred, extra = kw["required_skills"], kw["preferred_skills"], kw["keywords"]

    terms: list[str] = []
    for t in required + preferred + extra:
        if _norm(t) not in {_norm(x) for x in terms}:
            terms.append(t)
    matched = [t for t in terms if _literal(view.full_text, t)]
    missing = [t for t in terms if t not in matched]
    respell = [t for t in missing if _near_spelling(view.full_text, t)]
    keyword_match = 100.0 * len(matched) / len(terms) if terms else None

    skill_terms = required + preferred
    if skill_terms:
        listed = [t for t in skill_terms if _literal(view.skills_text, t)]
        skills_match = 100.0 * sum(1 for t in skill_terms if _literal(view.full_text, t)) / len(skill_terms)
    else:
        skills_match, listed = None, []

    role = _norm(kw["role"]).strip()
    if not role:
        title_match = None
    elif _literal(view.headline, role):
        title_match = 100.0
    elif _literal(view.summary, role):
        title_match = 75.0
    else:
        role_tokens = _tokens(role)
        title_match = round(50.0 * len(role_tokens & _tokens(view.headline)) / len(role_tokens), 1) if role_tokens else 0.0

    required_parts = ["summary", "experience", "education", "skills"]
    present = [s for s in required_parts if s in view.sections]
    contact_ok = view.has_email and view.has_phone
    section_completeness = 100.0 * (len(present) + (1 if contact_ok else 0)) / (len(required_parts) + 1)

    date_consistency, date_issues = _date_consistency(view)

    raw = {
        "keyword_match": keyword_match,
        "skills_match": skills_match,
        "title_match": title_match,
        "section_completeness": section_completeness,
        "date_consistency": date_consistency,
    }
    # Unscorable parts (no title in the post, fewer than two dates) are dropped and the weights re-normalized.
    subs = {k: round(v, 1) for k, v in raw.items() if v is not None}
    weight = sum(WEIGHTS[k] for k in subs)
    overall = round(sum(subs[k] * WEIGHTS[k] for k in subs) / weight, 1) if weight else 0.0

    recs: list[str] = []
    missing_required = [t for t in required if t in missing]
    if missing_required:
        recs.append("Required skills not found anywhere: " + ", ".join(missing_required)
                    + ". Add one only if it is true, and prove it in a bullet or project.")
    if respell:
        recs.append("Found under a different spelling; ATS filters are literal, so use the post's exact form: "
                    + ", ".join(respell) + ".")
    unlisted = [t for t in skill_terms if t in matched and t not in listed]
    if unlisted:
        recs.append("Mentioned in bullets but missing from the Skills section: " + ", ".join(unlisted) + ".")
    if title_match is not None and title_match < 100:
        recs.append(f"Put the exact posted title ({kw['role']!r}) in the headline if you truly do that job; "
                    "recruiters filter by title literally.")
    for part in required_parts:
        if part not in view.sections:
            recs.append(f"Add a clearly labelled {part.title()} section.")
    if not contact_ok:
        recs.append("Put an email and a phone number in the header as plain text.")
    recs += date_issues + view.notes

    return {
        "engine": ENGINE_NAME,
        "engine_version": ENGINE_VERSION,
        "overall_score": overall,
        "sub_scores": subs,
        "matched_keywords": matched,
        "missing_keywords": missing,
        "recommendations": recs,
    }


# --------------------------------------------------------------------------- parse check


def extract_text(path: Path) -> tuple[str, int]:
    """Return (text, page_count) the way a text-layer ATS sees the file."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return "\n".join((p.extract_text() or "") for p in reader.pages), len(reader.pages)
    if suffix == ".docx":
        import zipfile

        with zipfile.ZipFile(path) as zf:
            xml = zf.read("word/document.xml").decode("utf-8", errors="ignore")
        xml = re.sub(r"</w:p>", "\n", xml)
        return re.sub(r"<[^>]+>", "", xml), 1
    return path.read_text(encoding="utf-8", errors="ignore"), 1


def parse_check(path: Path, *, expected_name: str | None = None, max_pages: int = 2) -> dict[str, Any]:
    text, pages = extract_text(path)
    checks: list[dict[str, Any]] = []

    def add(cid: str, ok: bool, severity: str, detail: str) -> None:
        checks.append({"id": cid, "status": "pass" if ok else "fail", "severity": severity, "detail": detail})

    chars = len(text.strip())
    add("text_extractable", chars > 300, "high",
        f"{chars} characters in the text layer" + ("" if chars > 300 else " (scanned image or canvas text?)"))
    lines = [ln for ln in text.splitlines() if ln.strip()]
    found = _detect_headings(lines)
    for section in ("experience", "education", "skills"):
        add(f"heading_{section}", section in found, "high", f"{section.title()} heading readable as text")
    add("contact_email", bool(EMAIL_RE.search(text)), "high", "Email readable in the text layer")
    add("contact_phone", bool(PHONE_RE.search(text)), "medium", "Phone readable in the text layer")
    if expected_name:
        add("name_present", _norm(expected_name) in _norm(text), "medium", "Name readable in the text layer")
    lig = [c for c in LIGATURES if c in text]
    add("no_ligatures", not lig, "medium", "No ligature glyphs (fi/fl) that break keyword matching")
    split = re.search(r"\b(?:[a-z]{1,3} ){3,}[a-z]{1,3}\b", _norm(" ".join(l for l in lines if len(l) < 30)))
    add("no_split_words", split is None, "medium",
        "Headings not split into fragments" + (f" (saw {split.group(0)!r})" if split else ""))
    add("page_count", pages <= max_pages, "low", f"{pages} page(s); {max_pages} or fewer is safest")

    passed = sum(1 for c in checks if c["status"] == "pass")
    high_fail = any(c["status"] == "fail" and c["severity"] == "high" for c in checks)
    return {
        "engine": ENGINE_NAME,
        "parse_check_ok": not high_fail,
        "parse_score": round(100.0 * passed / len(checks), 1),
        "page_count": pages,
        "checks": checks,
        "parse_issues": [f"{c['id']} ({c['severity']}): {c['detail']}" for c in checks if c["status"] != "pass"],
    }


# --------------------------------------------------------------------------- CLI


def load_resume_input(path: Path) -> dict[str, Any] | str:
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    return extract_text(path)[0]


def _main() -> int:
    ap = argparse.ArgumentParser(description="Built-in deterministic ATS score + parse check")
    ap.add_argument("--resume", required=True, help="Resume JSON, PDF, DOCX or TXT")
    ap.add_argument("--keywords", required=True, help="Keywords JSON or job-post JSON")
    args = ap.parse_args()
    resume_path = Path(args.resume)
    result = score(load_resume_input(resume_path), json.loads(Path(args.keywords).read_text(encoding="utf-8")))
    if resume_path.suffix.lower() in {".pdf", ".docx"}:
        result["parse"] = parse_check(resume_path)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
