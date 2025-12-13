import importlib


def test_core_imports():
    modules = [
        "godman_ai.llm",
        "godman_ai.sync",
        "godman_ai.tools.shell",
        "libs.security.process_safe",
        "libs.sandbox",
        "libs.tool_runner",
        "workflows",
    ]

    for mod in modules:
        importlib.import_module(mod)
