"""Plugin registry and discovery."""

from godman_ai.plugins.registry import list_plugins, load_plugins, register_plugin

__all__ = ["register_plugin", "list_plugins", "load_plugins"]
