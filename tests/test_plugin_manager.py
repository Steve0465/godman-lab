"""Tests for plugin manager."""

import pytest
from pathlib import Path
import tempfile
import shutil
from godman_ai.os_core.plugin_manager import PluginManager
from godman_ai.engine import BaseTool


def test_plugin_manager_initialization():
    """Test PluginManager initializes correctly."""
    pm = PluginManager()
    
    assert pm.plugin_dir.exists()
    assert pm.loaded_plugins == {}
    assert pm.registered_tools == []
    assert pm.registered_agents == []


def test_load_plugins_empty_directory():
    """Test loading from empty plugin directory."""
    pm = PluginManager()
    
    # Should not crash with empty directory
    pm.load_plugins()
    
    assert len(pm.loaded_plugins) == 0


def test_create_and_load_dummy_plugin():
    """Test creating and loading a test plugin."""
    # Create temporary plugin directory
    with tempfile.TemporaryDirectory() as tmpdir:
        plugin_dir = Path(tmpdir)
        
        # Create a test plugin
        plugin_code = '''
from godman_ai.engine import BaseTool

class TestPlugin Tool(BaseTool):
    name = "test_plugin"
    description = "A test plugin tool"
    
    def run(self, **kwargs):
        return {"success": True, "message": "Test plugin executed"}
'''
        
        plugin_file = plugin_dir / "test_plugin.py"
        with open(plugin_file, 'w') as f:
            f.write(plugin_code)
        
        # Create plugin manager with custom directory
        pm = PluginManager()
        pm.plugin_dir = plugin_dir
        
        # Load plugins
        pm.load_plugins()
        
        # Verify plugin was loaded
        assert "test_plugin" in pm.loaded_plugins
        assert len(pm.registered_tools) == 1


def test_plugin_with_syntax_error_doesnt_crash():
    """Test that plugin with syntax error doesn't crash the system."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugin_dir = Path(tmpdir)
        
        # Create a broken plugin
        plugin_code = '''
# This plugin has a syntax error
def broken function(:
    return "invalid"
'''
        
        plugin_file = plugin_dir / "broken_plugin.py"
        with open(plugin_file, 'w') as f:
            f.write(plugin_code)
        
        pm = PluginManager()
        pm.plugin_dir = plugin_dir
        
        # Should not raise exception
        pm.load_plugins()
        
        # Plugin should not be loaded
        assert "broken_plugin" not in pm.loaded_plugins


def test_get_plugin_info():
    """Test plugin info retrieval."""
    pm = PluginManager()
    pm.load_plugins()
    
    info = pm.get_plugin_info()
    
    assert "loaded_plugins" in info
    assert "total_tools" in info
    assert "total_agents" in info
    assert "tools" in info
    assert "agents" in info


def test_register_with_orchestrator():
    """Test registering plugins with orchestrator."""
    class MockOrchestrator:
        def __init__(self):
            self.registered = []
        
        def register_tool(self, name, tool_cls):
            self.registered.append((name, tool_cls))
    
    pm = PluginManager()
    orchestrator = MockOrchestrator()
    
    # Add a dummy tool to plugin manager
    class DummyTool(BaseTool):
        name = "dummy"
        description = "Dummy tool"
        
        def run(self, **kwargs):
            return {}
    
    pm.registered_tools.append(DummyTool)
    
    # Register with orchestrator
    pm.register_with_orchestrator(orchestrator)
    
    assert len(orchestrator.registered) == 1
    assert orchestrator.registered[0][0] == "dummy"


def test_skips_private_files():
    """Test that plugin manager skips files starting with underscore."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugin_dir = Path(tmpdir)
        
        # Create a private file
        private_file = plugin_dir / "_private_plugin.py"
        with open(private_file, 'w') as f:
            f.write("# This should be skipped")
        
        pm = PluginManager()
        pm.plugin_dir = plugin_dir
        
        pm.load_plugins()
        
        # Private file should not be loaded
        assert "_private_plugin" not in pm.loaded_plugins
