from godman_ai.tools.critics.factuality_critic import evaluate_factuality
from godman_ai.tools.critics.quality_critic import evaluate_quality
from godman_ai.tools.critics.safety_critic import check_safety
from godman_ai.tools.critics.structural_validator import validate_structure


def test_quality():
    result = evaluate_quality("ok")
    assert result.score == 1.0
    assert "complete" in result.labels


def test_structure():
    result = validate_structure({"a": 1}, required_keys=["a", "b"])
    assert result.score < 1.0
    assert "missing" in "".join(result.reasons)


def test_safety():
    unsafe = check_safety("rm -rf /tmp")
    safe = check_safety("echo hello")
    assert unsafe.score == 0.0
    assert safe.score == 1.0


def test_factuality():
    result = evaluate_factuality("This is fine.")
    assert result.score > 0.5
