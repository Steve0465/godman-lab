from pathlib import Path

from godman_ai.plugins.registry import list_plugins, load_plugins, register_plugin


def test_register_and_list_plugins():
    register_plugin("demo", {"name": "demo"})
    assert "demo" in list_plugins()


def test_load_plugins_from_directory(tmp_path):
    plugin_dir = tmp_path / "myplugin"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "__init__.py").write_text("")
    (plugin_dir / "plugin.py").write_text(
        "def register():\n    return {'name': 'p1'}\n"
    )

    loaded = load_plugins(tmp_path)
    assert loaded and list_plugins()
