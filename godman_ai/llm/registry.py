"""Model registry for local LLM configurations."""

MODEL_REGISTRY = {
    "godman-raw:latest": {"type": "local", "model": "godman-raw:latest"},
    "deepseek-r1:latest": {"type": "local", "model": "deepseek-r1:latest"},
    "phi4-14b:latest": {"type": "local", "model": "phi4-14b:latest"},
}


def available_models():
    """Return registered model names."""
    return list(MODEL_REGISTRY.keys())
