# Plugin Architecture

Plugins extend the platform by registering new skills, tools, or routing hooks.

## Registry
- `register_plugin(name, plugin)` to add a plugin.
- `list_plugins()` to list registered names.
- `load_plugins(directory)` to discover plugins with a `plugin.py` containing `register()` that returns the plugin object.

## Discovery
- Scans subdirectories for `plugin.py`.
- Safe import: missing or failing plugins are skipped.

## Usage
```python
from godman_ai.plugins import load_plugins, list_plugins

load_plugins("examples/plugins")
print(list_plugins())
```

## Hooks (future-ready)
- Plugins may attach skills, tools, or routing metadata as the platform evolves.
