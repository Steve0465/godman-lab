"""Plugin manager for GodmanAI - enables dynamic extension loading."""

import importlib.util
import logging
from pathlib import Path
from typing import Dict, List, Any
import sys

logger = logging.getLogger(__name__)


class PluginManager:
    """
    Manages dynamic loading of plugins from the godman_ai/plugins/ directory.
    
    Plugins can add:
    - New tools (subclasses of BaseTool)
    - New agents (subclasses of PlannerAgent, ExecutorAgent, ReviewerAgent)
    - New CLI commands
    """

    def __init__(self):
        self.plugin_dir = Path(__file__).parent.parent / "plugins"
        self.plugin_dir.mkdir(exist_ok=True)
        
        self.loaded_plugins: Dict[str, Any] = {}
        self.registered_tools: List[Any] = []
        self.registered_agents: List[Any] = []

    def load_plugins(self):
        """
        Discover and load all Python files in the plugins directory.
        
        Safe failure: individual plugin failures won't crash the core.
        """
        logger.info(f"Loading plugins from: {self.plugin_dir}")
        
        # Find all .py files in plugin directory
        plugin_files = list(self.plugin_dir.glob("*.py"))
        
        if not plugin_files:
            logger.info("No plugins found")
            return
        
        for plugin_file in plugin_files:
            if plugin_file.name.startswith("_"):
                continue  # Skip private files
            
            try:
                self._load_plugin_file(plugin_file)
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_file.name}: {e}")
                # Continue loading other plugins

    def _load_plugin_file(self, plugin_path: Path):
        """Load a single plugin file."""
        plugin_name = plugin_path.stem
        
        logger.debug(f"Loading plugin: {plugin_name}")
        
        # Load the module
        spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Could not load spec for {plugin_path}")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[plugin_name] = module
        spec.loader.exec_module(module)
        
        # Store module reference
        self.loaded_plugins[plugin_name] = module
        
        # Discover plugin components
        self._discover_tools(module, plugin_name)
        self._discover_agents(module, plugin_name)
        
        logger.info(f"Loaded plugin: {plugin_name}")

    def _discover_tools(self, module, plugin_name: str):
        """Discover and register tools from a plugin module."""
        try:
            from godman_ai.engine import BaseTool
        except ImportError:
            logger.warning("BaseTool not available, skipping tool discovery")
            return
        
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            
            # Check if it's a BaseTool subclass
            if (isinstance(attr, type) and 
                issubclass(attr, BaseTool) and 
                attr is not BaseTool):
                
                logger.info(f"Discovered tool: {attr_name} from {plugin_name}")
                self.registered_tools.append(attr)

    def _discover_agents(self, module, plugin_name: str):
        """Discover and register agents from a plugin module."""
        agent_base_classes = []
        
        # Try to import agent base classes
        try:
            from godman_ai.agents.planner import PlannerAgent
            agent_base_classes.append(PlannerAgent)
        except ImportError:
            pass
        
        try:
            from godman_ai.agents.executor import ExecutorAgent
            agent_base_classes.append(ExecutorAgent)
        except ImportError:
            pass
        
        try:
            from godman_ai.agents.reviewer import ReviewerAgent
            agent_base_classes.append(ReviewerAgent)
        except ImportError:
            pass
        
        if not agent_base_classes:
            return
        
        # Discover agent subclasses
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            
            if not isinstance(attr, type):
                continue
            
            for base_class in agent_base_classes:
                if issubclass(attr, base_class) and attr is not base_class:
                    logger.info(f"Discovered agent: {attr_name} from {plugin_name}")
                    self.registered_agents.append(attr)
                    break

    def register_with_orchestrator(self, orchestrator):
        """
        Register all discovered tools with the orchestrator.
        
        Args:
            orchestrator: Orchestrator instance to register tools with
        """
        for tool_cls in self.registered_tools:
            try:
                tool_name = getattr(tool_cls, 'name', tool_cls.__name__)
                orchestrator.register_tool(tool_name, tool_cls)
                logger.info(f"Registered plugin tool: {tool_name}")
            except Exception as e:
                logger.error(f"Failed to register tool {tool_cls}: {e}")

    def get_plugin_info(self) -> Dict[str, Any]:
        """
        Get information about loaded plugins.
        
        Returns:
            dict: Plugin names, tools, and agents
        """
        return {
            "loaded_plugins": list(self.loaded_plugins.keys()),
            "total_tools": len(self.registered_tools),
            "total_agents": len(self.registered_agents),
            "tools": [
                getattr(tool, 'name', tool.__name__)
                for tool in self.registered_tools
            ],
            "agents": [
                agent.__name__
                for agent in self.registered_agents
            ],
        }

    def create_example_plugin(self):
        """Create an example plugin file to help users get started."""
        example_path = self.plugin_dir / "example_plugin.py"
        
        if example_path.exists():
            return  # Don't overwrite existing example
        
        example_code = '''"""Example GodmanAI plugin."""

from godman_ai.engine import BaseTool


class ExampleTool(BaseTool):
    """Example tool that demonstrates the plugin system."""
    
    name = "example_tool"
    description = "An example tool from a plugin"
    
    def run(self, **kwargs):
        """Execute the example tool."""
        return {
            "success": True,
            "message": "Hello from example plugin!",
            "input": kwargs,
        }


# You can add multiple tools in one plugin file
class AnotherExampleTool(BaseTool):
    """Another example tool."""
    
    name = "another_example"
    description = "Another example tool"
    
    def run(self, **kwargs):
        """Execute another example."""
        return {"success": True, "data": "More example output"}
'''
        
        try:
            with open(example_path, 'w') as f:
                f.write(example_code)
            logger.info(f"Created example plugin at: {example_path}")
        except Exception as e:
            logger.error(f"Failed to create example plugin: {e}")
