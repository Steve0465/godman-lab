"""Agent Engine - Dynamic tool and workflow orchestration."""
import importlib
import inspect
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Type
import os
import tomli

# Configure logging
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f"agent_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("godman_ai")


class BaseTool:
    """Base class for all tools."""
    name: str = "base_tool"
    description: str = "Base tool class"
    
    def execute(self, **kwargs) -> Any:
        """Execute the tool with given parameters."""
        raise NotImplementedError("Tool must implement execute method")


class BaseWorkflow:
    """Base class for all workflows."""
    name: str = "base_workflow"
    description: str = "Base workflow class"
    
    def run(self, **kwargs) -> Any:
        """Run the workflow with given parameters."""
        raise NotImplementedError("Workflow must implement run method")


class AgentEngine:
    """
    Main agent engine for dynamic tool and workflow orchestration.
    
    Features:
    - Dynamic tool loading from tools/
    - Dynamic workflow loading from workflows/
    - OpenAI integration for intelligent decision making
    - Comprehensive logging
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the Agent Engine.
        
        Args:
            config_path: Path to config.toml (defaults to godman_ai/config/config.toml)
        """
        self.base_dir = Path(__file__).parent
        self.config_path = config_path or self.base_dir / "config" / "config.toml"
        
        # Load configuration
        self.config = self._load_config()
        
        # Storage for tools and workflows
        self.tools: Dict[str, Type[BaseTool]] = {}
        self.workflows: Dict[str, Type[BaseWorkflow]] = {}
        
        # OpenAI client (placeholder)
        self.openai_client = None
        
        logger.info("🚀 Initializing Godman AI Agent Engine")
        
        # Load tools and workflows
        self._load_tools()
        self._load_workflows()
        
        logger.info(f"✓ Loaded {len(self.tools)} tools and {len(self.workflows)} workflows")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from TOML file."""
        if self.config_path.exists():
            with open(self.config_path, 'rb') as f:
                try:
                    import tomli
                    return tomli.load(f)
                except ImportError:
                    logger.warning("tomli not installed, using default config")
                    return {}
        else:
            logger.warning(f"Config file not found at {self.config_path}, using defaults")
            return {}
    
    def _load_tools(self):
        """Dynamically load all tools from tools/ directory."""
        tools_dir = self.base_dir / "tools"
        
        if not tools_dir.exists():
            logger.warning("Tools directory not found")
            return
        
        logger.info("Loading tools...")
        
        for tool_file in tools_dir.glob("*.py"):
            if tool_file.name.startswith("_"):
                continue
            
            module_name = f"godman_ai.tools.{tool_file.stem}"
            
            try:
                # Import the module using importlib
                module = importlib.import_module(module_name)
                
                # Find all tool classes
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, BaseTool) and 
                        obj is not BaseTool and
                        hasattr(obj, 'name')):
                        
                        self.tools[obj.name] = obj
                        logger.info(f"  ✓ Loaded tool: {obj.name}")
                        
            except Exception as e:
                logger.error(f"  ✗ Failed to load {tool_file.name}: {e}")
    
    def _load_workflows(self):
        """Dynamically load all workflows from workflows/ directory."""
        workflows_dir = self.base_dir / "workflows"
        
        if not workflows_dir.exists():
            logger.warning("Workflows directory not found")
            return
        
        logger.info("Loading workflows...")
        
        for workflow_file in workflows_dir.glob("*.py"):
            if workflow_file.name.startswith("_"):
                continue
            
            module_name = f"godman_ai.workflows.{workflow_file.stem}"
            
            try:
                # Import the module using importlib
                module = importlib.import_module(module_name)
                
                # Find all workflow classes
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, BaseWorkflow) and 
                        obj is not BaseWorkflow and
                        hasattr(obj, 'name')):
                        
                        self.workflows[obj.name] = obj
                        logger.info(f"  ✓ Loaded workflow: {obj.name}")
                        
            except Exception as e:
                logger.error(f"  ✗ Failed to load {workflow_file.name}: {e}")
    
    def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Call a tool by name with given parameters.
        
        Args:
            tool_name: Name of the tool to call
            **kwargs: Parameters to pass to the tool
        
        Returns:
            Result from the tool execution
        
        Raises:
            ValueError: If tool not found
        """
        logger.info(f"📞 Calling tool: {tool_name}")
        logger.debug(f"   Parameters: {kwargs}")
        
        if tool_name not in self.tools:
            available = ", ".join(self.tools.keys())
            raise ValueError(
                f"Tool '{tool_name}' not found. Available tools: {available}"
            )
        
        try:
            tool_class = self.tools[tool_name]
            tool_instance = tool_class()
            result = tool_instance.execute(**kwargs)
            
            logger.info(f"✓ Tool {tool_name} completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"✗ Tool {tool_name} failed: {e}")
            raise
    
    def run_workflow(self, workflow_name: str, **kwargs) -> Any:
        """
        Run a workflow by name with given parameters.
        
        Args:
            workflow_name: Name of the workflow to run
            **kwargs: Parameters to pass to the workflow
        
        Returns:
            Result from the workflow execution
        
        Raises:
            ValueError: If workflow not found
        """
        logger.info(f"▶️  Running workflow: {workflow_name}")
        logger.debug(f"   Parameters: {kwargs}")
        
        if workflow_name not in self.workflows:
            available = ", ".join(self.workflows.keys())
            raise ValueError(
                f"Workflow '{workflow_name}' not found. Available workflows: {available}"
            )
        
        try:
            workflow_class = self.workflows[workflow_name]
            workflow_instance = workflow_class(engine=self)
            result = workflow_instance.run(**kwargs)
            
            logger.info(f"✓ Workflow {workflow_name} completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"✗ Workflow {workflow_name} failed: {e}")
            raise
    
    def query_llm(self, prompt: str, **kwargs) -> str:
        """
        Query OpenAI model for intelligent decision making.
        
        Args:
            prompt: The prompt to send to the model
            **kwargs: Additional parameters (model, temperature, etc.)
        
        Returns:
            Response from the model
        """
        logger.info("🤖 Querying LLM")
        logger.debug(f"   Prompt: {prompt[:100]}...")
        
        # Placeholder for OpenAI integration
        if self.openai_client is None:
            logger.warning("OpenAI client not initialized")
            return "PLACEHOLDER: LLM response would go here"
        
        # TODO: Implement actual OpenAI call
        # response = self.openai_client.chat.completions.create(
        #     model=kwargs.get("model", "gpt-4"),
        #     messages=[{"role": "user", "content": prompt}],
        #     temperature=kwargs.get("temperature", 0.7)
        # )
        # return response.choices[0].message.content
        
        return "PLACEHOLDER: LLM response would go here"
    
    def list_tools(self) -> List[Dict[str, str]]:
        """Get list of available tools with descriptions."""
        return [
            {
                "name": name,
                "description": tool_class.description
            }
            for name, tool_class in self.tools.items()
        ]
    
    def list_workflows(self) -> List[Dict[str, str]]:
        """Get list of available workflows with descriptions."""
        return [
            {
                "name": name,
                "description": workflow_class.description
            }
            for name, workflow_class in self.workflows.items()
        ]
    
    def status(self) -> Dict[str, Any]:
        """Get current engine status."""
        return {
            "tools_loaded": len(self.tools),
            "workflows_loaded": len(self.workflows),
            "tools": list(self.tools.keys()),
            "workflows": list(self.workflows.keys()),
            "config_loaded": bool(self.config),
            "openai_ready": self.openai_client is not None
        }


# Export base classes for tool/workflow development
__all__ = ['AgentEngine', 'BaseTool', 'BaseWorkflow']
