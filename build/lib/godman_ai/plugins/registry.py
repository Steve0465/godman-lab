"""Minimal plugin registry and discovery."""

from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from typing import Any, Dict, List

PLUGINS: Dict[str, Any] = {}


def register_plugin(name: str, plugin: Any) -> None:
    PLUGINS[name] = plugin


def list_plugins() -> List[str]:
    return sorted(PLUGINS.keys())


def load_plugins(directory: str | Path) -> List[Any]:
    loaded = []
    base = Path(directory)
    if not base.exists():
        return loaded
    for item in base.iterdir():
        plugin_file = item / "plugin.py"
        if item.is_dir() and plugin_file.exists():
            spec = importlib.util.spec_from_file_location(f"{item.name}_plugin", plugin_file)
            if not spec or not spec.loader:
                continue
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)  # type: ignore
            except Exception:
                continue
            if hasattr(module, "register"):
                try:
                    plugin_obj = module.register()
                    register_plugin(item.name, plugin_obj)
                    loaded.append(plugin_obj)
                except Exception:
                    continue
    return loaded
