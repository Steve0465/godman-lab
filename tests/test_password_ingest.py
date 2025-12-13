from libs.password_ingest import (
    audit_strength,
    batch_login_test,
    compute_complexity_score,
    compute_strength,
    dedupe,
    detect_invalid,
    normalize_entries,
    summarize_dataset,
    validate_dataset,
)


def test_normalize_and_dedupe():
    raw = [
        {"url": "Example.com/login", "username": "Alice ", "password": "pass123"},
        {"url": "http://example.com/login", "username": "alice", "password": "pass123"},
    ]
    normalized = normalize_entries(raw)
    deduped = dedupe(normalized)
    assert len(deduped) == 1
    entry = deduped[0]
    assert entry["domain"] == "example.com"
    assert entry["username"] == "Alice"


def test_compute_strength_categories():
    assert compute_strength("short") == "weak"
    assert compute_strength("Abcdef12") == "medium"
    assert compute_strength("Abcdef1234!@") == "strong"


def test_complexity_score_increases_with_variety():
    simple = compute_complexity_score("aaaaaaa")
    complex_pw = compute_complexity_score("Abcdef123!")
    assert complex_pw > simple


def test_detect_invalid_and_empty_passwords():
    entries = normalize_entries(
        [
            {"url": "", "username": "user1", "password": "pw"},
            {"url": "example.com", "username": "", "password": "pw"},
            {"url": "example.com", "username": "user2", "password": ""},
        ]
    )
    issues = detect_invalid(entries)
    assert len(issues["invalid"]) == 2
    assert len(issues["empty_passwords"]) == 1


def test_summarize_dataset_and_strength_audit():
    entries = normalize_entries(
        [
            {"url": "alpha.com", "username": "alice", "password": "Abcdef1234!@"},
            {"url": "beta.com", "username": "bob", "password": "abcd1234"},
            {"url": "", "username": "carol", "password": "short"},
        ]
    )
    enriched = [
        {**entry, "strength": compute_strength(entry["password"]), "complexity_score": compute_complexity_score(entry["password"])}
        for entry in entries
    ]
    summary = summarize_dataset(enriched)
    assert summary["total_entries"] == 3
    assert summary["by_strength"] == {"weak": 1, "medium": 1, "strong": 1}
    assert summary["unique_domains"] == 2
    assert summary["domains_most_used"][0][0] in {"alpha.com", "beta.com"}

    grouped = audit_strength(enriched)
    assert len(grouped["strong"]) == 1
    assert len(grouped["medium"]) == 1
    assert len(grouped["weak"]) == 1


def test_validate_dataset_and_login_simulation():
    entries = normalize_entries(
        [
            {"url": "gamma.com", "username": "dave", "password": "Abcdef1234!@"},
            {"url": "gamma.com", "username": "dave", "password": ""},
        ]
    )
    enriched = [
        {**entry, "strength": compute_strength(entry["password"]), "complexity_score": compute_complexity_score(entry["password"])}
        for entry in entries
    ]
    validation = validate_dataset(enriched)
    assert validation["has_issues"]
    assert len(validation["empty_passwords"]) == 1

    results = batch_login_test(enriched)
    assert results[0]["success"] is True
    assert results[1]["success"] is False
