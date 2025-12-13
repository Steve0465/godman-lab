import importlib

MODULES = [
    "godman_ai.orchestrator.orchestrator",
    "godman_ai.orchestrator.router_v2",
    "godman_ai.orchestrator.tool_router",
    "godman_ai.tools.registry",
    "godman_ai.tools.receipts",
    "libs.tool_runner",
]


def test_imports_succeed():
    for mod in MODULES:
        importlib.import_module(mod)
