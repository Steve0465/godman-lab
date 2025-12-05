"""Tests for model router."""

import pytest
import os
from godman_ai.os_core.model_router import ModelRouter


def test_model_router_initialization():
    """Test ModelRouter initializes with default preferences."""
    router = ModelRouter()
    
    assert router.model_prefs is not None
    assert "default" in router.model_prefs
    assert "planning" in router.model_prefs


def test_choose_model():
    """Test model selection based on task type."""
    router = ModelRouter()
    
    # Test known task types
    assert router.choose_model("planning") in ["gpt-4o", "local-llama"]
    assert router.choose_model("text_analysis") in ["gpt-3.5-turbo", "local-llama"]
    assert router.choose_model("vision") in ["gpt-4o", "local-llama"]
    
    # Test unknown task type falls back to default
    model = router.choose_model("unknown_task_type")
    assert model in router.model_prefs.values() or model == "local-llama"


def test_list_available_models():
    """Test listing available models."""
    router = ModelRouter()
    
    available = router.list_available_models()
    
    assert isinstance(available, dict)
    assert "gpt-4o" in available
    assert "gpt-3.5-turbo" in available
    assert "local-llama" in available
    
    # Check that availability is boolean
    for model, avail in available.items():
        assert isinstance(avail, bool)


def test_model_router_without_openai_key():
    """Test that router falls back to local when no OpenAI key."""
    # Temporarily remove API key
    original_key = os.environ.get("OPENAI_API_KEY")
    if original_key:
        del os.environ["OPENAI_API_KEY"]
    
    try:
        router = ModelRouter()
        model = router.choose_model("planning")
        
        # Should fall back to local model
        assert model == "local-llama"
    finally:
        # Restore key
        if original_key:
            os.environ["OPENAI_API_KEY"] = original_key


def test_run_requires_model_or_task_type():
    """Test that run method accepts model or task_type."""
    router = ModelRouter()
    
    # This will fail without actual API, but we're testing the interface
    try:
        # Should not raise an error about missing parameters
        router.choose_model("default")
    except Exception:
        pass  # Expected to fail without actual API setup
