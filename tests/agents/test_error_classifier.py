import pytest

from godman_ai.agents.error_classifier import ErrorClass, classify_error


def test_transient():
    assert classify_error(TimeoutError()) == ErrorClass.TRANSIENT


def test_tool_config():
    assert classify_error(KeyError()) == ErrorClass.TOOL_CONFIG


def test_model_quality_from_critic():
    class Dummy:
        score = 0.1
    assert classify_error(Exception("x"), Dummy()) == ErrorClass.MODEL_QUALITY


def test_requires_human():
    assert classify_error(PermissionError()) == ErrorClass.REQUIRES_HUMAN
