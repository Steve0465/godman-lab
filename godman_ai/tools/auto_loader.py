"""Auto-discovery module for dynamically loading tools from godman_ai/tools."""
import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Dict, Type
import logging

logger = logging.getLogger("godman_ai.tools.auto_loader")


def discover_tool_classes(package_path: str = "godman_ai.tools") -> Dict[str, Type]:
    """
    Dynamically discover and return all BaseTool subclasses from a package.
    
    Args:
        package_path: Python package path (e.g., "godman_ai.tools")
    
    Returns:
        Dict mapping tool names to tool classes: {tool_name: ToolClass}
    
    Behavior:
        - Uses pkgutil.iter_modules to iterate modules inside the package
        - Dynamically imports each module using importlib.import_module
        - Inspects attributes to find subclasses of BaseTool
        - Returns a dict: {tool_name: tool_class}
        - No heavy imports at top-level
        - Lightweight and dependency-minimal
    
    Example:
        >>> tools = discover_tool_classes("godman_ai.tools")
        >>> print(tools.keys())
        dict_keys(['ocr', 'vision', 'sheets', 'trello', 'drive', 'reports'])
    """
    # Lazy import BaseTool to avoid circular imports
    from ..engine import BaseTool
    
    discovered_tools: Dict[str, Type] = {}
    
    try:
        # Import the package
        package = importlib.import_module(package_path)
        package_dir = Path(package.__file__).parent
        
        logger.debug(f"🔍 Scanning package: {package_path} at {package_dir}")
        
    except ImportError as e:
        logger.error(f"❌ Failed to import package {package_path}: {e}")
        return discovered_tools
    
    # Iterate through all modules in the package
    for importer, module_name, is_pkg in pkgutil.iter_modules([str(package_dir)]):
        # Skip private modules and the auto_loader itself
        if module_name.startswith("_") or module_name == "auto_loader":
            continue
        
        full_module_name = f"{package_path}.{module_name}"
        
        try:
            # Dynamically import the module
            module = importlib.import_module(full_module_name)
            logger.debug(f"📦 Imported module: {full_module_name}")
            
            # Inspect all classes in the module
            for attr_name, attr_value in inspect.getmembers(module, inspect.isclass):
                # Check if it's a BaseTool subclass
                if (inspect.isclass(attr_value) and
                    issubclass(attr_value, BaseTool) and
                    attr_value is not BaseTool):
                    
                    # Get tool name from class attribute or use class name
                    tool_name = getattr(attr_value, 'name', attr_name.lower())
                    
                    if tool_name:
                        discovered_tools[tool_name] = attr_value
                        logger.debug(f"✅ Discovered tool: {tool_name} ({attr_value.__name__})")
                    
        except Exception as e:
            logger.warning(f"⚠️  Failed to load module {full_module_name}: {e}")
            continue
    
    logger.info(f"✅ Discovered {len(discovered_tools)} tools from {package_path}")
    return discovered_tools


__all__ = ['discover_tool_classes']
