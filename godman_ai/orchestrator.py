"""Orchestrator v2 - Advanced input-based task routing with dynamic tool loading."""
import importlib
import inspect
import logging
from typing import Any, Dict, Optional, Type, Union
from pathlib import Path

logger = logging.getLogger("godman_ai.orchestrator")

# Import BaseTool from engine (lazy import handled in methods for heavy packages)
from .engine import BaseTool


class Orchestrator:
    """
    Advanced task orchestrator with dynamic tool discovery and intelligent routing.
    
    Features:
    - Dynamic tool loading from godman_ai/tools/
    - Automatic input type detection (image, PDF, text, audio, video, CSV, JSON)
    - Lazy-loading of heavy dependencies (PIL, pdfplumber, numpy, pandas, etc.)
    - Smart tool selection based on input type
    - Comprehensive error handling with exception chaining
    - Debug-level lifecycle logging
    
    Compatible with future Agents system.
    """
    
    def __init__(self):
        """Initialize the orchestrator with empty tool registry."""
        self.tool_classes: Dict[str, Type[BaseTool]] = {}
        self.tool_instances: Dict[str, BaseTool] = {}
        
        # Default input type → tool name mappings
        self.type_handlers: Dict[str, str] = {
            "image": "vision",
            "pdf": "ocr",
            "text": "reports",
            "csv": "sheets",
            "json": "sheets",
            "audio": "audio_processor",
            "video": "video_processor",
        }
        
        logger.debug("🎭 Orchestrator v2 initialized")
    
    def register_tool(self, name: str, tool_cls: Type[BaseTool]):
        """
        Register a tool class (not an instance).
        
        Args:
            name: Tool name (e.g., 'vision', 'ocr', 'sheets')
            tool_cls: Tool class that inherits from BaseTool
        
        Raises:
            TypeError: If tool_cls doesn't inherit from BaseTool
        """
        if not issubclass(tool_cls, BaseTool):
            raise TypeError(f"Tool class must inherit from BaseTool, got {type(tool_cls)}")
        
        self.tool_classes[name] = tool_cls
        logger.debug(f"✅ Tool class registered: {name} ({tool_cls.__name__})")
    
    def load_tools_from_package(self, package_path: str = "godman_ai.tools"):
        """
        Auto-discover and register all tools from a package.
        
        Args:
            package_path: Python package path (default: "godman_ai.tools")
        
        Uses the auto_loader module to discover and register tools.
        """
        from .tools.auto_loader import discover_tool_classes
        
        logger.info(f"🔍 Auto-discovering tools from: {package_path}")
        
        # Use auto-loader to discover tools
        discovered_tools = discover_tool_classes(package_path)
        
        # Register all discovered tools
        for tool_name, tool_cls in discovered_tools.items():
            self.register_tool(tool_name, tool_cls)
        
        logger.info(f"✅ Loaded {len(discovered_tools)} tools from {package_path}")
    
    def detect_input_type(self, input_obj: Union[str, Path, bytes, dict]) -> str:
        """
        Detect input type from various input formats.
        
        Args:
            input_obj: Can be:
                - File path (str or Path)
                - Raw bytes
                - Dict (for JSON-like data)
        
        Returns:
            One of: "image", "pdf", "text", "audio", "video", "csv", "json", "unknown"
        
        Uses lazy imports for heavy packages like PIL.
        """
        logger.debug(f"🔍 Detecting input type for: {type(input_obj).__name__}")
        
        # Handle dict/JSON objects
        if isinstance(input_obj, dict):
            return "json"
        
        # Handle bytes (check magic numbers)
        if isinstance(input_obj, bytes):
            return self._detect_from_bytes(input_obj)
        
        # Handle file paths
        if isinstance(input_obj, (str, Path)):
            path = Path(input_obj)
            
            if not path.exists():
                logger.warning(f"⚠️  Input file does not exist: {input_obj}")
                return "unknown"
            
            suffix = path.suffix.lower()
            
            # Image types
            if suffix in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.ico']:
                return "image"
            
            # PDF
            elif suffix == '.pdf':
                return "pdf"
            
            # CSV
            elif suffix == '.csv':
                return "csv"
            
            # JSON
            elif suffix == '.json':
                return "json"
            
            # Audio
            elif suffix in ['.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac']:
                return "audio"
            
            # Video
            elif suffix in ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv']:
                return "video"
            
            # Text
            elif suffix in ['.txt', '.md', '.log', '.xml', '.html', '.yaml', '.yml', '.toml', '.ini']:
                return "text"
            
            else:
                logger.debug(f"⚠️  Unknown file extension: {suffix}")
                return "unknown"
        
        logger.warning(f"⚠️  Could not detect type for: {type(input_obj)}")
        return "unknown"
    
    def _detect_from_bytes(self, data: bytes) -> str:
        """
        Detect file type from raw bytes using magic numbers.
        
        Args:
            data: Raw file bytes
        
        Returns:
            Detected type string
        """
        # Check magic numbers (first few bytes)
        if data.startswith(b'\xff\xd8\xff'):
            return "image"  # JPEG
        elif data.startswith(b'\x89PNG'):
            return "image"  # PNG
        elif data.startswith(b'GIF8'):
            return "image"  # GIF
        elif data.startswith(b'%PDF'):
            return "pdf"
        elif data.startswith(b'ID3') or data.startswith(b'\xff\xfb'):
            return "audio"  # MP3
        elif data[:4] in [b'ftyp', b'mdat', b'moov', b'wide']:
            return "video"  # MP4
        
        return "unknown"
    
    def run_task(self, input_obj: Union[str, Path, bytes, dict], **kwargs) -> Dict[str, Any]:
        """
        Main entry point: detect input type, select tool, and execute.
        
        Args:
            input_obj: Input to process (file path, bytes, dict, etc.)
            **kwargs: Additional parameters to pass to the tool
        
        Returns:
            Dict with status, result, input_type, tool_name, and error (if any)
        
        Example:
            >>> orch = Orchestrator()
            >>> orch.load_tools_from_package()
            >>> result = orch.run_task("scans/receipt.pdf")
            >>> print(result['status'])
        """
        try:
            # Step 1: Detect input type
            logger.debug("🔍 Step 1: Detecting input type...")
            input_type = self.detect_input_type(input_obj)
            logger.info(f"📋 Detected input type: {input_type}")
            
            if input_type == "unknown":
                raise ValueError(f"Unable to determine input type for: {input_obj}")
            
            # Step 2: Select appropriate tool
            logger.debug("🔍 Step 2: Selecting tool...")
            handler_name = self.type_handlers.get(input_type)
            
            if not handler_name:
                raise ValueError(f"No handler configured for input type: {input_type}")
            
            if handler_name not in self.tool_classes:
                available = ", ".join(self.tool_classes.keys())
                raise ValueError(
                    f"Tool '{handler_name}' not registered. Available: {available}"
                )
            
            logger.info(f"🔧 Selected tool: {handler_name}")
            
            # Step 3: Get or create tool instance
            logger.debug("🔍 Step 3: Instantiating tool...")
            if handler_name not in self.tool_instances:
                tool_cls = self.tool_classes[handler_name]
                self.tool_instances[handler_name] = tool_cls()
                logger.debug(f"✅ Instantiated new tool: {handler_name}")
            
            tool = self.tool_instances[handler_name]
            
            # Step 4: Execute tool
            logger.debug("🔍 Step 4: Executing tool...")
            logger.info(f"🚀 Running {handler_name}.execute() with kwargs: {list(kwargs.keys())}")
            
            result = tool.execute(input=input_obj, **kwargs)
            
            logger.info(f"✅ Task completed successfully")
            
            return {
                "status": "success",
                "input_type": input_type,
                "tool": handler_name,
                "result": result,
                "metadata": {
                    "input": str(input_obj),
                    "kwargs": list(kwargs.keys())
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Task failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "input": str(input_obj),
                "traceback": True  # Full traceback logged above
            }
    
    def set_handler(self, input_type: str, tool_name: str):
        """
        Override the default handler for a specific input type.
        
        Args:
            input_type: Type of input ('image', 'pdf', 'text', 'csv', etc.)
            tool_name: Name of registered tool to handle this type
        """
        if tool_name not in self.tool_classes:
            logger.warning(f"⚠️  Tool '{tool_name}' not registered yet")
        
        self.type_handlers[input_type] = tool_name
        logger.info(f"🔧 Handler updated: {input_type} → {tool_name}")
    
    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        List all registered tools with metadata.
        
        Returns:
            Dict mapping tool names to their info (class, description, handled types)
        """
        result = {}
        
        for tool_name, tool_cls in self.tool_classes.items():
            # Find which input types this tool handles
            handled_types = [
                itype for itype, tname in self.type_handlers.items()
                if tname == tool_name
            ]
            
            result[tool_name] = {
                "class": tool_cls.__name__,
                "description": getattr(tool_cls, 'description', 'No description'),
                "handles": handled_types,
                "instantiated": tool_name in self.tool_instances
            }
        
        return result
    
    def status(self) -> Dict[str, Any]:
        """
        Get current orchestrator status.
        
        Returns:
            Dict with tool counts, mappings, and readiness info
        """
        return {
            "tools_registered": len(self.tool_classes),
            "tools_instantiated": len(self.tool_instances),
            "tool_names": list(self.tool_classes.keys()),
            "type_handlers": self.type_handlers,
            "ready": len(self.tool_classes) > 0
        }


__all__ = ['Orchestrator', 'BaseTool']
