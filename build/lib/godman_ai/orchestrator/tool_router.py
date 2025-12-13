"""
Tool Router - Intelligent dispatch system for tools and functions.

The ToolRouter discovers available tools in godman_ai/tools and provides
keyword-based routing to automatically select the right tool for a given task.
"""

import logging
from typing import Optional, Callable, Dict, List, Any
from dataclasses import dataclass
import importlib
import inspect

# Configure logging
logger = logging.getLogger(__name__)
from godman_ai.utils.deprecation import deprecated


@dataclass
class RoutedTool:
    """
    Representation of a callable tool for routing purposes.
    
    Attributes:
        name: Human-readable tool name
        callable: The actual function/method to call
        description: Brief description of what the tool does
        keywords: List of keywords that trigger this tool
        module: Module path where tool is defined
    """
    name: str
    callable: Callable
    description: str
    keywords: List[str]
    module: str


class ToolRouter:
    """
    Intelligent router for discovering and dispatching to available tools.
    
    The ToolRouter maintains a registry of available tools and uses
    keyword-based matching to route plan steps to the appropriate tool.
    """
    
    def __init__(self, enable_logging: bool = True):
        """
        Initialize the ToolRouter.
        
        Args:
            enable_logging: Whether to enable debug logging
        """
        self.enable_logging = enable_logging
        self.registry: Dict[str, RoutedTool] = {}
        self._initialize_registry()
        
        if enable_logging:
            logger.info(f"ToolRouter initialized with {len(self.registry)} tools")
    
    def _initialize_registry(self):
        """
        Discover and register available tools from godman_ai/tools and root modules.
        
        This method attempts to import various tool modules and registers
        their callable functions. If a module fails to import, it logs
        a warning and continues (safe import).
        """
        # Define tool configurations
        tool_configs = [
            {
                "name": "receipts_processor",
                "module": "godman_ai.tools.receipts",
                "callable_name": "load_receipts",
                "description": "Load and process receipt data from CSV files",
                "keywords": ["receipt", "csv", "expense", "transaction", "purchase"]
            },
            {
                "name": "receipts_category",
                "module": "godman_ai.tools.receipts",
                "callable_name": "infer_category",
                "description": "Infer tax category from receipt data",
                "keywords": ["category", "categorize", "classify", "tax"]
            },
            {
                "name": "receipts_query",
                "module": "godman_ai.tools.receipts",
                "callable_name": "get_receipts_by_category",
                "description": "Query receipts by category",
                "keywords": ["filter", "query", "search receipts", "find receipt"]
            },
            {
                "name": "pattern_analyzer",
                "module": "pattern_analyzer",
                "callable_name": "main",
                "description": "Analyze spending patterns and detect anomalies",
                "keywords": ["pattern", "anomaly", "spending", "analyze", "trend", "forecast"]
            },
            {
                "name": "netflix_analyzer",
                "module": "netflix_analyzer",
                "callable_name": "main",
                "description": "Analyze Netflix viewing history and recommend shows",
                "keywords": ["netflix", "viewing", "watch", "movie", "show", "recommend"]
            },
            {
                "name": "ocr_extractor",
                "module": "godman_ai.tools.ocr",
                "callable_name": "extract_text_basic",
                "description": "Extract text from images and PDFs using OCR",
                "keywords": ["ocr", "extract", "scan", "image", "pdf", "document"]
            },
            {
                "name": "llm_extractor",
                "module": "ocr.llm_extractor",
                "callable_name": "extract_fields",
                "description": "Extract structured fields from OCR text using LLM",
                "keywords": ["extract fields", "structured", "parse receipt"]
            },
            {
                "name": "enhanced_extractor",
                "module": "ocr.enhanced_extractor",
                "callable_name": "EnhancedReceiptExtractor",
                "description": "Enhanced receipt data extraction with LLM",
                "keywords": ["enhanced ocr", "receipt extraction"]
            }
        ]
        
        # Register each tool
        for config in tool_configs:
            self._register_tool(
                name=config["name"],
                module_path=config["module"],
                callable_name=config["callable_name"],
                description=config["description"],
                keywords=config["keywords"]
            )
    
    def _register_tool(
        self,
        name: str,
        module_path: str,
        callable_name: str,
        description: str,
        keywords: List[str]
    ) -> bool:
        """
        Register a single tool in the registry.
        
        Args:
            name: Tool name for registry
            module_path: Python module path (e.g., 'godman_ai.tools.receipts')
            callable_name: Name of function/class to import
            description: Tool description
            keywords: Keywords that trigger this tool
            
        Returns:
            True if registration succeeded, False otherwise
        """
        try:
            # Attempt to import module
            module = importlib.import_module(module_path)
            
            # Get the callable
            if not hasattr(module, callable_name):
                logger.warning(
                    f"Module {module_path} does not have '{callable_name}'"
                )
                return False
            
            callable_obj = getattr(module, callable_name)
            
            # Validate it's actually callable
            if not callable(callable_obj) and not inspect.isclass(callable_obj):
                logger.warning(
                    f"{module_path}.{callable_name} is not callable"
                )
                return False
            
            # Create RoutedTool and register
            tool = RoutedTool(
                name=name,
                callable=callable_obj,
                description=description,
                keywords=keywords,
                module=module_path
            )
            
            self.registry[name] = tool
            
            if self.enable_logging:
                logger.debug(f"Registered tool: {name} ({module_path}.{callable_name})")
            
            return True
            
        except ImportError as e:
            logger.warning(
                f"Failed to import {module_path} for tool '{name}': {e}"
            )
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error registering tool '{name}': {e}"
            )
            return False
    
    def route(self, plan_step: str) -> Optional[RoutedTool]:
        """
        Route a plan step to the appropriate tool based on keyword matching.
        
        Analyzes the plan step text and matches it against registered tool
        keywords to find the best tool for the task.
        
        Args:
            plan_step: A single step from a plan (e.g., "Load receipt data")
            
        Returns:
            RoutedTool if a match is found, None otherwise
            
        Example:
            >>> router = ToolRouter()
            >>> tool = router.route("Load receipt data from CSV")
            >>> if tool:
            ...     result = tool.callable('receipts.csv')
        """
        if not plan_step or not plan_step.strip():
            logger.warning("Empty plan step provided to router")
            return None
        
        step_lower = plan_step.lower()
        
        # Score each tool based on keyword matches
        scores: Dict[str, int] = {}
        
        for tool_name, tool in self.registry.items():
            score = 0
            for keyword in tool.keywords:
                if keyword.lower() in step_lower:
                    score += 1
            
            if score > 0:
                scores[tool_name] = score
        
        # Return tool with highest score
        if scores:
            best_tool_name = max(scores, key=scores.get)
            best_tool = self.registry[best_tool_name]
            
            if self.enable_logging:
                logger.debug(
                    f"Routed '{plan_step}' to tool '{best_tool_name}' "
                    f"(score: {scores[best_tool_name]})"
                )
            
            return best_tool
        
        # No match found
        if self.enable_logging:
            logger.debug(f"No tool found for plan step: '{plan_step}'")
        
        return None
    
    def route_multiple(self, plan_steps: List[str]) -> Dict[str, Optional[RoutedTool]]:
        """
        Route multiple plan steps at once.
        
        Args:
            plan_steps: List of plan steps
            
        Returns:
            Dictionary mapping each step to its matched tool (or None)
        """
        results = {}
        for step in plan_steps:
            results[step] = self.route(step)
        return results
    
    def get_available_tools(self) -> List[str]:
        """
        Get list of all available tool names.
        
        Returns:
            List of registered tool names
        """
        return list(self.registry.keys())
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Dictionary with tool information or None if not found
        """
        if tool_name not in self.registry:
            return None
        
        tool = self.registry[tool_name]
        return {
            "name": tool.name,
            "description": tool.description,
            "keywords": tool.keywords,
            "module": tool.module,
            "callable": tool.callable.__name__
        }
    
    def list_tools(self) -> None:
        """
        Print a formatted list of all available tools.
        """
        print("Available Tools:")
        print("=" * 70)
        
        if not self.registry:
            print("No tools registered")
            return
        
        for tool_name, tool in self.registry.items():
            print(f"\n🔧 {tool.name}")
            print(f"   Description: {tool.description}")
            print(f"   Keywords: {', '.join(tool.keywords)}")
            print(f"   Module: {tool.module}")
    
    def add_custom_tool(
        self,
        name: str,
        callable_obj: Callable,
        description: str,
        keywords: List[str]
    ) -> None:
        """
        Manually register a custom tool.
        
        Extension point for adding tools not in the standard locations.
        
        Args:
            name: Tool name
            callable_obj: The callable function/method
            description: Tool description
            keywords: Keywords that trigger this tool
            
        Example:
            >>> def my_tool(data):
            ...     return process(data)
            >>> router.add_custom_tool(
            ...     "my_tool",
            ...     my_tool,
            ...     "Custom processing tool",
            ...     ["custom", "special"]
            ... )
        """
        tool = RoutedTool(
            name=name,
            callable=callable_obj,
            description=description,
            keywords=keywords,
            module="custom"
        )
        
        self.registry[name] = tool
        
        if self.enable_logging:
            logger.info(f"Custom tool registered: {name}")


# Convenience function for quick routing (deprecated)
@deprecated("Use RouterV2 or ToolRouter directly.")
def quick_route(plan_step: str) -> Optional[RoutedTool]:
    router = ToolRouter(enable_logging=False)
    return router.route(plan_step)
