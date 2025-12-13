from godman_ai.utils.logging_config import scrub_sensitive


def test_scrub_sensitive_redacts():
    msg = "user password=secret123 token=abcd api_key=XYZ secret=hidden"
    cleaned = scrub_sensitive(msg)
    assert "password=***" in cleaned
    assert "token=***" in cleaned
    assert "api_key=***" in cleaned
    assert "secret=***" in cleaned
