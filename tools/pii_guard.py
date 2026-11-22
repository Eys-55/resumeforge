#!/usr/bin/env python3
"""Deterministic PII and prompt-injection firewall for ResumeForge.

Can be imported by `resumeforge` or run directly via CLI:
    python tools/pii_guard.py --mode pattern --in pattern.json --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SYNTHETIC_EMAIL_DOMAINS = frozenset({"example.ph", "example.com", "synthetic.ph"})
SYNTHETIC_PH_PHONE_RE = re.compile(r"^\+63 9\d{2} 000 \d{4}$")

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PH_MOBILE_RE = re.compile(
    r"(?<!\d)(?:\+?63[\s.-]?9\d{2}[\s.-]?\d{3}[\s.-]?\d{4}|09\d{2}[\s.-]?\d{3}[\s.-]?\d{4})(?!\d)"
)
PH_LANDLINE_RE = re.compile(
    r"(?<!\d)(?:\(0\d{1,2}\)[\s.-]?\d{3,4}[\s.-]?\d{4}|\+?63[\s.-]?2[\s.-]?\d{4}[\s.-]?\d{4})(?!\d)"
)
PERSONAL_URL_RE = re.compile(
    r"(?:https?://)?(?:www\.)?(?:linkedin\.com/in/[A-Za-z0-9._%-]+|github\.com/[A-Za-z0-9._-]+)",
    re.IGNORECASE,
)

PH_GOV_ID_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("TIN", re.compile(r"(?:\bTIN\b[:\s#-]*\d{3}[-\s]?\d{3}[-\s]?\d{3}(?:[-\s]?\d{3,5})?|\b\d{3}-\d{3}-\d{3}-\d{3,5}\b)", re.IGNORECASE)),
    ("SSS", re.compile(r"(?:\bSSS\b[:\s#-]*\d{2}[-\s]?\d{7}[-\s]?\d\b|\b\d{2}-\d{7}-\d\b)", re.IGNORECASE)),
    ("PhilHealth", re.compile(r"(?:\b(?:PhilHealth|PHIC)\b[:\s#-]*\d{2}[-\s]?\d{9}[-\s]?\d\b|\b\d{2}-\d{9}-\d\b)", re.IGNORECASE)),
    ("Pag-IBIG", re.compile(r"(?:\b(?:Pag-?IBIG|HDMF)\b[:\s#-]*\d{4}[-\s]?\d{4}[-\s]?\d{4}\b|\b\d{4}-\d{4}-\d{4}\b)", re.IGNORECASE)),
    ("UMID", re.compile(r"\bUMID\b[:\s#-]*\d{4}[-\s]?\d{7}[-\s]?\d\b", re.IGNORECASE)),
    ("PRC_License", re.compile(r"\bPRC(?:\s+(?:License|Lic\.?|No\.?|ID|Reg\.?))+\s*[:#-]*\s*\d{6,8}\b", re.IGNORECASE)),
)

ZERO_WIDTH_RE = re.compile(r"[\u200b\u200c\u200d\u200e\u200f\ufeff\u202a-\u202e]")
HTML_COMMENT_RE = re.compile(r"<!--")

INJECTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("ignore_instructions", re.compile(r"\bignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions?\b", re.IGNORECASE)),
    ("disregard_prior", re.compile(r"\bdisregard\s+(?:all\s+)?(?:previous|prior)\b", re.IGNORECASE)),
    ("system_prompt", re.compile(r"\bsystem\s+prompt\b", re.IGNORECASE)),
    ("persona_hijack", re.compile(r"\byou\s+are\s+now\b", re.IGNORECASE)),
    ("override_rules", re.compile(r"\boverride\s+(?:your\s+)?(?:instructions|rules|system)\b", re.IGNORECASE)),
)


@dataclass
class PIIScanResult:
    clean: bool
    mode: str
    findings: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "clean": self.clean,
            "mode": self.mode,
            "finding_count": len(self.findings),
            "findings": self.findings,
        }


def _iter_strings(obj: Any, prefix: str = "") -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    if isinstance(obj, str):
        items.append((prefix or "text", obj))
    elif isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else str(k)
            items.extend(_iter_strings(v, path))
    elif isinstance(obj, (list, tuple)):
        for idx, v in enumerate(obj):
            path = f"{prefix}[{idx}]"
            items.extend(_iter_strings(v, path))
    return items


def _scan_text_field(
    field_path: str,
    text: str,
    *,
    mode: str,
    findings: list[dict[str, str]],
) -> None:
    if ZERO_WIDTH_RE.search(text):
        findings.append({
            "field": field_path,
            "category": "zero_width_char",
            "detail": "Hidden zero-width or directional Unicode character detected.",
        })

    if HTML_COMMENT_RE.search(text):
        findings.append({
            "field": field_path,
            "category": "html_comment",
            "detail": "HTML comment markup '<!--' is disallowed.",
        })

    for inj_name, inj_re in INJECTION_PATTERNS:
        m = inj_re.search(text)
        if m:
            findings.append({
                "field": field_path,
                "category": f"prompt_injection:{inj_name}",
                "detail": f"Instruction-like payload detected: {m.group(0)!r}",
            })

    for id_name, id_re in PH_GOV_ID_PATTERNS:
        m = id_re.search(text)
        if m:
            findings.append({
                "field": field_path,
                "category": f"gov_id:{id_name}",
                "detail": f"Philippine government/PRC ID pattern detected: {m.group(0)!r}",
            })

    for email_match in EMAIL_RE.finditer(text):
        addr = email_match.group(0)
        domain = addr.rsplit("@", 1)[-1].lower()
        if mode == "pattern":
            findings.append({
                "field": field_path,
                "category": "email",
                "detail": f"Email address disallowed in anonymized patterns: {addr}",
            })
        elif field_path != "email" or domain not in SYNTHETIC_EMAIL_DOMAINS:
            findings.append({
                "field": field_path,
                "category": "non_synthetic_email",
                "detail": f"Non-synthetic or out-of-header email detected: {addr}",
            })

    for phone_match in PH_MOBILE_RE.finditer(text):
        raw_phone = phone_match.group(0)
        if mode == "pattern":
            findings.append({
                "field": field_path,
                "category": "phone",
                "detail": f"Phone number disallowed in anonymized patterns: {raw_phone}",
            })
        elif field_path != "phone" or not SYNTHETIC_PH_PHONE_RE.match(raw_phone.strip()):
            findings.append({
                "field": field_path,
                "category": "non_synthetic_phone",
                "detail": f"Unmasked or out-of-header PH mobile detected: {raw_phone}",
            })

    for landline_match in PH_LANDLINE_RE.finditer(text):
        findings.append({
            "field": field_path,
            "category": "landline",
            "detail": f"PH landline number detected: {landline_match.group(0)}",
        })

    if mode == "pattern":
        for url_match in PERSONAL_URL_RE.finditer(text):
            findings.append({
                "field": field_path,
                "category": "personal_profile_url",
                "detail": f"Personal profile URL disallowed in anonymized patterns: {url_match.group(0)}",
            })


def scan_text(text: str, *, mode: str = "pattern") -> PIIScanResult:
    """Scan raw text for PII, PH government IDs, and prompt-injection attempts."""
    if mode not in {"pattern", "resume"}:
        raise ValueError(f"Unsupported mode: {mode!r}")
    findings: list[dict[str, str]] = []
    _scan_text_field("text", text, mode=mode, findings=findings)
    return PIIScanResult(clean=len(findings) == 0, mode=mode, findings=findings)


def scan_payload(payload: dict[str, Any], *, mode: str = "pattern") -> PIIScanResult:
    """Scan a structured pattern or resume payload for PII and injection markers."""
    if mode not in {"pattern", "resume"}:
        raise ValueError(f"Unsupported mode: {mode!r}")

    findings: list[dict[str, str]] = []

    if mode == "pattern":
        if payload.get("pii_scrubbed") is not True:
            findings.append({
                "field": "pii_scrubbed",
                "category": "pii_flag_missing",
                "detail": "Reference pattern payload must explicitly set pii_scrubbed=true.",
            })

    if mode == "resume":
        email = str(payload.get("email") or "").strip()
        if not EMAIL_RE.fullmatch(email):
            findings.append({
                "field": "email",
                "category": "invalid_email",
                "detail": f"Resume email is missing or malformed: {email!r}",
            })
        else:
            domain = email.rsplit("@", 1)[-1].lower()
            if domain not in SYNTHETIC_EMAIL_DOMAINS:
                findings.append({
                    "field": "email",
                    "category": "non_synthetic_email",
                    "detail": f"Resume email domain must be one of {sorted(SYNTHETIC_EMAIL_DOMAINS)}, got {domain!r}",
                })

        phone = str(payload.get("phone") or "").strip()
        if not SYNTHETIC_PH_PHONE_RE.fullmatch(phone):
            findings.append({
                "field": "phone",
                "category": "non_synthetic_phone",
                "detail": "Resume phone must match synthetic PH format '+63 9XX 000 XXXX'.",
            })

        portfolio_url = payload.get("portfolio_url")
        if portfolio_url:
            url_str = str(portfolio_url).strip()
            if PERSONAL_URL_RE.search(url_str) and "example" not in url_str.lower() and "synthetic" not in url_str.lower():
                findings.append({
                    "field": "portfolio_url",
                    "category": "non_synthetic_url",
                    "detail": f"portfolio_url looks like a real personal profile URL: {url_str}",
                })

    for field_path, text in _iter_strings(payload):
        _scan_text_field(field_path, text, mode=mode, findings=findings)

    return PIIScanResult(clean=len(findings) == 0, mode=mode, findings=findings)


def _main() -> int:
    parser = argparse.ArgumentParser(description="ResumeForge deterministic PII and injection firewall")
    parser.add_argument("--mode", choices=("pattern", "resume"), required=True)
    parser.add_argument("--in", dest="input_path", required=True, help="JSON file path or '-' for stdin")
    parser.add_argument("--text", action="store_true", help="Treat input as plain text instead of JSON")
    parser.add_argument("--json", action="store_true", help="Output structured JSON")
    args = parser.parse_args()

    if args.input_path == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(args.input_path).read_text(encoding="utf-8")

    if args.text:
        result = scan_text(raw, mode=args.mode)
    else:
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Expected JSON object at top level.")
        result = scan_payload(data, mode=args.mode)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        status = "CLEAN" if result.clean else f"BLOCKED ({len(result.findings)} finding(s))"
        print(f"pii_guard [{args.mode}]: {status}")
        for f in result.findings:
            print(f"  - [{f['category']}] {f['field']}: {f['detail']}")

    return 0 if result.clean else 1


if __name__ == "__main__":
    sys.exit(_main())
