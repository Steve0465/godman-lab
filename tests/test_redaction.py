from godman_ai.utils.logging_config import scrub_sensitive


def test_scrub_sensitive_masks_multiple_patterns():
    msg = "token=abcd password=abc api_key=XYZ secret=mysecret"
    cleaned = scrub_sensitive(msg)
    assert "token=***" in cleaned
    assert "password=***" in cleaned
    assert "api_key=***" in cleaned
    assert "secret=***" in cleaned


def test_scrub_sensitive_is_case_insensitive():
    msg = "Token=abcd PASSWORD=abc Api_Key=XYZ"
    cleaned = scrub_sensitive(msg)
    assert "Token=***" in cleaned or "token=***" in cleaned
    assert "PASSWORD=***" in cleaned or "password=***" in cleaned
