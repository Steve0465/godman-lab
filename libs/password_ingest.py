from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence
from urllib.parse import urlparse


def load_password_csv(path: Path) -> List[Dict[str, str]]:
    """Load a password CSV with common column names."""
    rows: List[Dict[str, str]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(
                {
                    "url": (row.get("url") or row.get("site") or row.get("website") or "").strip(),
                    "username": (row.get("username") or row.get("user") or "").strip(),
                    "password": (row.get("password") or row.get("pass") or "").strip(),
                }
            )
    return rows


def load_multiple_csv(paths: Sequence[Path]) -> List[Dict[str, str]]:
    """Load and merge multiple password CSV files."""
    combined: List[Dict[str, str]] = []
    for path in paths:
        combined.extend(load_password_csv(path))
    return combined


def _extract_domain(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url if "://" in url else f"http://{url}")
    domain = parsed.netloc or parsed.path
    if domain.startswith("www."):
        domain = domain[4:]
    return domain.lower()


def normalize_entry(entry: Dict[str, str]) -> Dict[str, str]:
    """Normalize a single entry and derive domain."""
    url = str(entry.get("url", "") or "").strip()
    username = str(entry.get("username", "") or "").strip()
    password = str(entry.get("password", "") or "").strip()
    domain = _extract_domain(url)
    return {"url": url, "username": username, "password": password, "domain": domain}


def normalize_entries(entries: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    """Normalize all entries."""
    return [normalize_entry(entry) for entry in entries]


def dedupe(entries: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    """Remove duplicate records using domain/url + username + password."""
    seen = set()
    unique: List[Dict[str, str]] = []
    for entry in entries:
        key = (
            (entry.get("domain") or entry.get("url") or "").lower(),
            (entry.get("username") or "").lower(),
            entry.get("password") or "",
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(entry)
    return unique


def _count_types(password: str) -> int:
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    return sum([has_upper, has_lower, has_digit, has_special])


def compute_strength(password: str) -> str:
    """Classify password strength."""
    length = len(password)
    types = _count_types(password)
    if length >= 12 and types >= 3:
        return "strong"
    if 8 <= length <= 12 and types >= 2:
        return "medium"
    return "weak"


def compute_complexity_score(password: str) -> int:
    """
    Score password complexity between 0-100 using length, variety, and repetition.
    """
    if not password:
        return 0
    length_component = min(len(password), 20) / 20 * 40
    type_component = _count_types(password) / 4 * 40
    freq_counter = Counter(password)
    most_common = freq_counter.most_common(1)[0][1]
    repetition_component = (1 - (most_common / len(password))) * 20
    score = length_component + type_component + repetition_component
    return max(0, min(100, int(round(score))))


def audit_strength(entries: Iterable[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group entries by strength classification."""
    grouped = {"weak": [], "medium": [], "strong": []}
    for entry in entries:
        strength = entry.get("strength") or compute_strength(entry.get("password", ""))
        enriched = dict(entry)
        enriched["strength"] = strength
        grouped[strength].append(enriched)
    return grouped


def detect_invalid(entries: Iterable[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Detect invalid and empty-password records."""
    invalid: List[Dict[str, Any]] = []
    empty_passwords: List[Dict[str, Any]] = []
    for entry in entries:
        has_url = bool(entry.get("url"))
        has_username = bool(entry.get("username"))
        password = entry.get("password") or ""
        if not has_url or not has_username:
            invalid.append(dict(entry, issue="missing_url_or_username"))
        if has_url and has_username and password == "":
            empty_passwords.append(dict(entry, issue="empty_password"))
    return {"invalid": invalid, "empty_passwords": empty_passwords}


def export_csv(entries: Iterable[Dict[str, Any]], path: Path) -> Path:
    """Export entries to CSV including derived metrics when present."""
    fieldnames = ["url", "username", "password", "domain", "strength", "complexity_score"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for entry in entries:
            writer.writerow({field: entry.get(field, "") for field in fieldnames})
    return path


def export_json(data: Dict[str, Any], path: Path) -> Path:
    """Export a dictionary as formatted JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True, default=str)
    return path


def summarize_dataset(entries: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Summarize dataset composition and metrics."""
    entries_list = list(entries)
    domains = [entry.get("domain", "") for entry in entries_list if entry.get("domain")]
    strength_counts = {"weak": 0, "medium": 0, "strong": 0}
    username_counts: Counter[str] = Counter()
    complexity_scores: List[int] = []

    for entry in entries_list:
        strength = entry.get("strength") or compute_strength(entry.get("password", ""))
        strength_counts[strength] += 1
        username = (entry.get("username") or "").strip()
        if username:
            username_counts[username.lower()] += 1
        complexity_scores.append(entry.get("complexity_score") or compute_complexity_score(entry.get("password", "")))

    domain_counts = Counter(domains)
    domains_most_used = [[domain, count] for domain, count in domain_counts.most_common()]
    avg_complexity = round(sum(complexity_scores) / len(complexity_scores), 2) if complexity_scores else 0.0

    by_username_usage = {name: count for name, count in sorted(username_counts.items(), key=lambda item: (-item[1], item[0]))}

    return {
        "total_entries": len(entries_list),
        "unique_domains": len(set(domains)),
        "by_strength": strength_counts,
        "by_username_usage": by_username_usage,
        "average_complexity_score": avg_complexity,
        "domains_most_used": domains_most_used,
    }


def validate_dataset(entries: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate dataset for missing credentials and empty passwords."""
    issues = detect_invalid(entries)
    issues["has_issues"] = bool(issues["invalid"] or issues["empty_passwords"])
    return issues


def export_full_report(entries: Iterable[Dict[str, Any]], path: Path) -> Path:
    """Export a combined report with summary, validation, and raw entries."""
    entries_list = list(entries)
    report = {
        "entries": entries_list,
        "summary": summarize_dataset(entries_list),
        "validation": validate_dataset(entries_list),
    }
    return export_json(report, path)


def simulate_login_test(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate a login test by scoring the credential's readiness.
    
    A credential is treated as successful when it has a password and is not weak.
    """
    strength = entry.get("strength") or compute_strength(entry.get("password", ""))
    complexity = entry.get("complexity_score") or compute_complexity_score(entry.get("password", ""))
    has_password = bool(entry.get("password"))
    success = has_password and strength != "weak" and complexity >= 40
    reason = "ok"
    if not has_password:
        reason = "missing password"
    elif strength == "weak":
        reason = "weak credential"
    elif complexity < 40:
        reason = "low complexity"

    return {
        "url": entry.get("url", ""),
        "username": entry.get("username", ""),
        "domain": entry.get("domain", ""),
        "strength": strength,
        "complexity_score": complexity,
        "success": success,
        "status": "success" if success else "failure",
        "reason": reason,
    }


def batch_login_test(entries: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run simulated login tests for all entries."""
    return [simulate_login_test(entry) for entry in entries]


def export_login_test_report(results: Iterable[Dict[str, Any]], path: Path) -> Path:
    """Export login test results with a summary."""
    results_list = list(results)
    summary = {
        "total": len(results_list),
        "success": sum(1 for r in results_list if r.get("success")),
        "failure": sum(1 for r in results_list if not r.get("success")),
    }
    payload = {"summary": summary, "results": results_list}
    return export_json(payload, path)
