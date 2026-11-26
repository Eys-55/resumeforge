#!/usr/bin/env python3
"""Deterministic validator for ResumeForge Philippine gold-standard resumes.

Checks PII/injection safety, reverse chronology, full-time overlap, tenure &
seniority math, education alignment, anti-slop / outdated PH biodata tokens,
bullet metric density, skill evidence, and database deduplication.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from tools.pii_guard import scan_payload

YM_RE = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")
WORD_RE = re.compile(r"[a-z0-9+#.]+", re.IGNORECASE)
QUANTIFIED_METRIC_RE = re.compile(
    r"(?<![A-Za-z0-9])\d+(?:[.,]\d+)?"
    r"(?:%|\+|x\b|(?:\s*(?:ms|s|m|min|mins|minute|minutes|h|hr|hrs|hour|hours|d|day|days|wk|wks|week|weeks|mo|mos|month|months|yr|yrs|year|years|k|m|b)\b))?"
    r"(?![A-Za-z0-9])",
    re.IGNORECASE,
)

SENIORITY_BOUNDS: dict[str, tuple[float, float]] = {
    "entry": (0.0, 2.5),
    "mid": (2.0, 5.5),
    "senior": (4.5, 10.0),
    "lead": (6.5, 22.0),
}

CLICHE_NAMES = (
    "juan dela cruz",
    "maria clara",
    "pedro penduko",
    "jose rizal",
    "john doe",
    "jane doe",
    "test user",
    "sample candidate",
)

PLACEHOLDER_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\[(?:todo|tbd|insert[^\]]*|your[^\]]*|placeholder[^\]]*)\]", re.IGNORECASE),
    re.compile(r"\blorem\s+ipsum\b", re.IGNORECASE),
    re.compile(r"\bTBD\b"),
    re.compile(r"\bXXX+\b"),
)

OUTDATED_PH_BIODATA_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:marital|civil)\s+status\s*:", re.IGNORECASE),
    re.compile(r"\breligion\s*:", re.IGNORECASE),
    re.compile(r"\bheight\s*:", re.IGNORECASE),
    re.compile(r"\bweight\s*:", re.IGNORECASE),
    re.compile(r"\b(?:2x2|1x1)\s+(?:id\s+)?photo\b", re.IGNORECASE),
    re.compile(r"\bcharacter\s+references?\b", re.IGNORECASE),
    re.compile(r"\breferences\s+available\s+upon\s+request\b", re.IGNORECASE),
    re.compile(r"\bobjective\s*:\s*to\s+obtain\b", re.IGNORECASE),
    re.compile(r"\bi\s+hereby\s+certify\b", re.IGNORECASE),
)

AI_SLOP_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bsynergistic\b", re.IGNORECASE),
    re.compile(r"\bdelve\s+into\b", re.IGNORECASE),
    re.compile(r"\bresults-driven\s+go-getter\b", re.IGNORECASE),
    re.compile(r"\bdynamic\s+self-starter\b", re.IGNORECASE),
    re.compile(r"\bcutting-edge\s+paradigm\b", re.IGNORECASE),
    re.compile(r"\bproven\s+track\s+record\s+of\s+excellence\b", re.IGNORECASE),
    re.compile(r"\bwears?\s+many\s+hats\b", re.IGNORECASE),
    re.compile(r"\b(?:code|tech|ai)\s+(?:ninja|rockstar|guru)\b", re.IGNORECASE),
)


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings,
            "metrics": self.metrics,
        }


def _parse_ym(value: str) -> int | None:
    m = YM_RE.fullmatch(value.strip())
    if not m:
        return None
    year = int(m.group(1))
    month = int(m.group(2))
    return year * 12 + (month - 1)


def _current_ym() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _all_narrative_texts(payload: dict[str, Any]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for key in ("full_name", "headline", "professional_summary", "city", "region"):
        val = payload.get(key)
        if isinstance(val, str):
            out.append((key, val))
    for i, exp in enumerate(payload.get("experiences") or []):
        if isinstance(exp, dict):
            for k in ("company_name", "role_title", "location"):
                if isinstance(exp.get(k), str):
                    out.append((f"experiences[{i}].{k}", exp[k]))
            for j, b in enumerate(exp.get("bullets") or []):
                if isinstance(b, dict) and isinstance(b.get("text"), str):
                    out.append((f"experiences[{i}].bullets[{j}].text", b["text"]))
    for i, proj in enumerate(payload.get("projects") or []):
        if isinstance(proj, dict):
            for k in ("name", "role", "summary", "impact_metric"):
                if isinstance(proj.get(k), str):
                    out.append((f"projects[{i}].{k}", proj[k]))
    for i, edu in enumerate(payload.get("education") or []):
        if isinstance(edu, dict):
            for k in ("institution", "degree", "field_of_study", "honors"):
                if isinstance(edu.get(k), str):
                    out.append((f"education[{i}].{k}", edu[k]))
    return out


def _skill_tokens(skill_name: str) -> list[str]:
    low = skill_name.lower().strip()
    tokens = [low]
    # Split parenthetical or slash variants, e.g., "CRM Integration (HubSpot / GoHighLevel)"
    base = re.sub(r"\([^)]*\)", "", low).strip()
    if base and base != low:
        tokens.append(base)
    for part in re.split(r"[/,()]+", low):
        cleaned = part.strip()
        if len(cleaned) >= 2:
            tokens.append(cleaned)
    return list(dict.fromkeys(tokens))


def _jaccard_similarity(text_a: str, text_b: str) -> float:
    words_a = set(WORD_RE.findall(text_a.lower()))
    words_b = set(WORD_RE.findall(text_b.lower()))
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / len(words_a | words_b)


def validate_resume_data(
    payload: dict[str, Any],
    *,
    session: Session | None = None,
    exclude_resume_code: str | None = None,
    reference_ym: str | None = None,
) -> ValidationResult:
    """Run all deterministic gold-standard checks on a structured resume payload."""
    errors: list[str] = []
    warnings: list[str] = []

    # 1. PII & injection gate
    pii_result = scan_payload(payload, mode="resume")
    if not pii_result.clean:
        for finding in pii_result.findings:
            errors.append(f"PII/Security [{finding['category']}] {finding['field']}: {finding['detail']}")

    # 2. Cliché names, placeholders, outdated PH biodata, AI slop, em-dash spam
    full_name = str(payload.get("full_name") or "").strip()
    if full_name.lower() in CLICHE_NAMES:
        errors.append(f"Cliché synthetic name disallowed: {full_name!r}")

    narrative = _all_narrative_texts(payload)
    em_dash_count = 0
    for path, text in narrative:
        em_dash_count += text.count("—")
        for pat in PLACEHOLDER_PATTERNS:
            m = pat.search(text)
            if m:
                errors.append(f"Placeholder token in {path}: {m.group(0)!r}")
        for pat in OUTDATED_PH_BIODATA_PATTERNS:
            m = pat.search(text)
            if m:
                errors.append(f"Outdated PH biodata pattern in {path}: {m.group(0)!r}")
        for pat in AI_SLOP_PATTERNS:
            m = pat.search(text)
            if m:
                errors.append(f"Banned AI cliché in {path}: {m.group(0)!r}")

    if em_dash_count > 2:
        errors.append(f"Excessive em-dash usage ({em_dash_count} > 2 max).")

    # 3. Chronology & full-time overlap
    ref_ym_str = reference_ym or _current_ym()
    ref_ym_idx = _parse_ym(ref_ym_str)
    if ref_ym_idx is None:
        raise ValueError(f"Invalid reference_ym: {reference_ym!r}")

    experiences = payload.get("experiences") or []
    if not isinstance(experiences, list) or len(experiences) == 0:
        errors.append("Resume must include at least 1 experience entry.")
        experiences = []

    parsed_spans: list[dict[str, Any]] = []
    covered_months: set[int] = set()
    full_time_intervals: list[tuple[int, int, int]] = []
    earliest_ft_start_year: int | None = None

    total_bullets = 0
    quantified_bullets = 0

    for idx, exp in enumerate(experiences):
        if not isinstance(exp, dict):
            errors.append(f"experiences[{idx}] must be an object.")
            continue
        start_raw = str(exp.get("start_date") or "").strip()
        end_raw = str(exp.get("end_date") or "").strip()
        is_current = bool(exp.get("is_current", False))
        emp_type = str(exp.get("employment_type") or "Full-time").strip()

        start_idx = _parse_ym(start_raw)
        if start_idx is None:
            errors.append(f"experiences[{idx}].start_date must be YYYY-MM, got {start_raw!r}")
            continue
        if start_idx > ref_ym_idx:
            errors.append(f"experiences[{idx}].start_date {start_raw!r} is in the future (after {ref_ym_str}).")

        if end_raw.lower() == "present":
            if not is_current:
                errors.append(f"experiences[{idx}] has end_date='present' but is_current=false.")
            end_idx = ref_ym_idx
            sort_end_idx = ref_ym_idx + 1
        else:
            if is_current:
                errors.append(f"experiences[{idx}] has is_current=true so end_date must be 'present', got {end_raw!r}.")
            end_idx = _parse_ym(end_raw)
            if end_idx is None:
                errors.append(f"experiences[{idx}].end_date must be YYYY-MM or 'present', got {end_raw!r}")
                continue
            if end_idx > ref_ym_idx:
                errors.append(f"experiences[{idx}].end_date {end_raw!r} is in the future (after {ref_ym_str}).")
            sort_end_idx = end_idx

        if end_idx < start_idx:
            errors.append(f"experiences[{idx}] end_date ({end_raw}) precedes start_date ({start_raw}).")
        else:
            for m in range(start_idx, end_idx + 1):
                covered_months.add(m)
            if emp_type == "Full-time":
                full_time_intervals.append((idx, start_idx, end_idx))
                start_year = int(start_raw.split("-")[0])
                if earliest_ft_start_year is None or start_year < earliest_ft_start_year:
                    earliest_ft_start_year = start_year

        parsed_spans.append({"idx": idx, "sort_key": (sort_end_idx, start_idx)})

        bullets = exp.get("bullets") or []
        min_b, max_b = (3, 6) if idx == 0 else (2, 5)
        if not (min_b <= len(bullets) <= max_b):
            errors.append(
                f"experiences[{idx}] must have {min_b}-{max_b} bullets (found {len(bullets)})."
            )
        for b_idx, b in enumerate(bullets):
            if not isinstance(b, dict):
                errors.append(f"experiences[{idx}].bullets[{b_idx}] must be an object.")
                continue
            b_text = str(b.get("text") or "").strip()
            words = b_text.split()
            if not (8 <= len(words) <= 42):
                errors.append(
                    f"experiences[{idx}].bullets[{b_idx}] length must be 8-42 words (found {len(words)})."
                )
            total_bullets += 1
            if QUANTIFIED_METRIC_RE.search(b_text):
                quantified_bullets += 1

    # Reverse-chronological order verification
    for pos in range(1, len(parsed_spans)):
        prev_key = parsed_spans[pos - 1]["sort_key"]
        curr_key = parsed_spans[pos]["sort_key"]
        if curr_key > prev_key:
            errors.append(
                f"Experiences are not in reverse-chronological order at index {parsed_spans[pos]['idx']}."
            )

    # Full-time overlap verification (> 1 month overlap disallowed)
    for i in range(len(full_time_intervals)):
        idx_a, sa, ea = full_time_intervals[i]
        for j in range(i + 1, len(full_time_intervals)):
            idx_b, sb, eb = full_time_intervals[j]
            overlap_months = min(ea, eb) - max(sa, sb) + 1
            if overlap_months > 1:
                errors.append(
                    f"Full-time experiences[{idx_a}] and experiences[{idx_b}] overlap by {overlap_months} months."
                )

    # 4. Experience math, seniority band, and education alignment
    computed_years = round(len(covered_months) / 12.0, 2)
    try:
        declared_years = float(payload.get("total_years_experience", -1))
    except (TypeError, ValueError):
        declared_years = -1.0

    if declared_years < 0:
        errors.append("total_years_experience must be a non-negative number.")
    elif covered_months and abs(computed_years - declared_years) > 0.6:
        errors.append(
            f"total_years_experience ({declared_years}) disagrees with timeline ({computed_years} yrs)."
        )

    seniority = str(payload.get("seniority") or "").strip()
    if seniority not in SENIORITY_BOUNDS:
        errors.append(f"Invalid seniority {seniority!r}; expected one of {sorted(SENIORITY_BOUNDS)}.")
    elif declared_years >= 0:
        min_y, max_y = SENIORITY_BOUNDS[seniority]
        if not (min_y <= declared_years <= max_y):
            errors.append(
                f"Seniority {seniority!r} expects {min_y}-{max_y} years, got {declared_years}."
            )

    education = payload.get("education") or []
    if not isinstance(education, list) or len(education) == 0:
        errors.append("Resume must include at least 1 education entry.")
    else:
        grad_years: list[int] = []
        for idx, edu in enumerate(education):
            if not isinstance(edu, dict):
                errors.append(f"education[{idx}] must be an object.")
                continue
            gy = edu.get("graduation_year")
            sy = edu.get("start_year")
            if not isinstance(gy, int):
                errors.append(f"education[{idx}].graduation_year must be an integer.")
                continue
            grad_years.append(gy)
            if sy is not None and isinstance(sy, int) and sy > gy:
                errors.append(f"education[{idx}].start_year ({sy}) exceeds graduation_year ({gy}).")

        if grad_years and earliest_ft_start_year is not None:
            min_grad_year = min(grad_years)
            if earliest_ft_start_year < (min_grad_year - 1):
                errors.append(
                    f"Earliest full-time role ({earliest_ft_start_year}) starts >1 year before earliest graduation ({min_grad_year})."
                )

    # 5. Bullet metric density & skill evidence alignment
    quant_ratio = (quantified_bullets / total_bullets) if total_bullets else 0.0
    if total_bullets > 0 and quant_ratio < 0.5:
        errors.append(
            f"At least 50% of experience bullets must contain quantified digits/metrics (got {quantified_bullets}/{total_bullets})."
        )

    skills = payload.get("skills") or []
    if not isinstance(skills, list) or len(skills) < 5:
        errors.append(f"Resume must list at least 5 skills (found {len(skills) if isinstance(skills, list) else 0}).")
        skills = []

    corpus_parts = [str(payload.get("headline") or ""), str(payload.get("professional_summary") or "")]
    for exp in experiences:
        if isinstance(exp, dict):
            corpus_parts.append(str(exp.get("role_title") or ""))
            for b in exp.get("bullets") or []:
                if isinstance(b, dict):
                    corpus_parts.append(str(b.get("text") or ""))
    for proj in payload.get("projects") or []:
        if isinstance(proj, dict):
            corpus_parts.append(str(proj.get("summary") or ""))
            corpus_parts.extend(str(t) for t in (proj.get("tech_stack") or []))
    evidence_corpus = " \n ".join(corpus_parts).lower()

    matched_skills = 0
    for sk in skills:
        if not isinstance(sk, dict):
            continue
        name = str(sk.get("name") or "").strip()
        if not name:
            continue
        if any(tok in evidence_corpus for tok in _skill_tokens(name)):
            matched_skills += 1

    skill_evidence_ratio = (matched_skills / len(skills)) if skills else 0.0
    if skills and skill_evidence_ratio < 0.5:
        errors.append(
            f"At least 50% of listed skills must appear in summary/bullets/projects (got {matched_skills}/{len(skills)})."
        )

    # 6. Database uniqueness & bullet deduplication
    if session is not None:
        from resumeforge.db.models import Resume, ResumeBullet, ResumeExperience

        email_norm = str(payload.get("email") or "").strip().lower()
        name_norm = full_name.lower()

        dup_name_stmt = select(Resume.resume_code).where(func.lower(Resume.full_name) == name_norm)
        dup_email_stmt = select(Resume.resume_code).where(func.lower(Resume.email) == email_norm)
        if exclude_resume_code:
            dup_name_stmt = dup_name_stmt.where(Resume.resume_code != exclude_resume_code)
            dup_email_stmt = dup_email_stmt.where(Resume.resume_code != exclude_resume_code)

        # Targeted variants of the same fictional persona may share name/email with
        # resumes they are explicitly linked to (parent, children, and siblings).
        # Bullet near-duplicate checks below still apply to every other resume.
        own_code = str(payload.get("resume_code") or exclude_resume_code or "").strip()
        variant_of = str(payload.get("variant_of") or "").strip()
        root_code = variant_of or own_code
        if root_code:
            linked_codes = {root_code}
            linked_codes.update(
                session.scalars(select(Resume.resume_code).where(Resume.variant_of_code == root_code)).all()
            )
            linked_codes.discard(own_code)
            if linked_codes:
                dup_name_stmt = dup_name_stmt.where(Resume.resume_code.not_in(linked_codes))
                dup_email_stmt = dup_email_stmt.where(Resume.resume_code.not_in(linked_codes))

        dup_name = session.scalar(dup_name_stmt)
        if dup_name:
            errors.append(f"Duplicate full_name {full_name!r} already used by {dup_name}.")

        dup_email = session.scalar(dup_email_stmt)
        if dup_email:
            errors.append(f"Duplicate email {email_norm!r} already used by {dup_email}.")

        existing_bullets_stmt = (
            select(Resume.resume_code, ResumeBullet.text)
            .join(ResumeExperience, ResumeExperience.id == ResumeBullet.experience_id)
            .join(Resume, Resume.id == ResumeExperience.resume_id)
        )
        if exclude_resume_code:
            existing_bullets_stmt = existing_bullets_stmt.where(Resume.resume_code != exclude_resume_code)
        existing_bullets = session.execute(existing_bullets_stmt).all()

        for exp in experiences:
            if not isinstance(exp, dict):
                continue
            for b in exp.get("bullets") or []:
                if not isinstance(b, dict):
                    continue
                b_text = str(b.get("text") or "").strip()
                for other_code, other_text in existing_bullets:
                    sim = _jaccard_similarity(b_text, other_text)
                    if sim >= 0.85:
                        errors.append(
                            f"Near-duplicate bullet (similarity {sim:.2f} with {other_code}): {b_text[:80]!r}"
                        )
                        break

    metrics = {
        "computed_years_experience": computed_years,
        "declared_years_experience": declared_years,
        "total_bullets": total_bullets,
        "quantified_bullets": quantified_bullets,
        "quantified_ratio": round(quant_ratio, 3),
        "skill_count": len(skills),
        "matched_skills": matched_skills,
        "skill_evidence_ratio": round(skill_evidence_ratio, 3),
        "em_dash_count": em_dash_count,
    }
    return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings, metrics=metrics)


def _main() -> int:
    parser = argparse.ArgumentParser(description="Validate a ResumeForge JSON draft")
    parser.add_argument("--in", dest="input_path", required=True, help="JSON file path or '-' for stdin")
    parser.add_argument("--ref-ym", dest="reference_ym", default=None, help="Override current YYYY-MM")
    parser.add_argument("--json", action="store_true", help="Output structured JSON")
    args = parser.parse_args()

    raw = sys.stdin.read() if args.input_path == "-" else Path(args.input_path).read_text(encoding="utf-8")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("Expected top-level JSON object.")

    result = validate_resume_data(payload, reference_ym=args.reference_ym)
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        status = "VALID" if result.valid else f"INVALID ({len(result.errors)} error(s))"
        print(f"validate_resume: {status}")
        for err in result.errors:
            print(f"  - {err}")
    return 0 if result.valid else 1


if __name__ == "__main__":
    sys.exit(_main())
