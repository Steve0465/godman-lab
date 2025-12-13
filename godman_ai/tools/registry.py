"""Registry helpers for tools."""

from typing import Any, Callable, Dict, List, Optional, Type

from godman_ai.tools.base import BaseTool

TOOL_REGISTRY: Dict[str, Any] = {}


def register_tool(tool_cls: Type[BaseTool]) -> None:
    """
    Register a tool class by its name attribute.
    """
    TOOL_REGISTRY[tool_cls.name] = tool_cls


def register_function_tool(name: str, func: Callable[..., Any], description: str = "") -> None:
    """
    Register a function as a tool.
    
    Args:
        name: Tool name
        func: Function to register
        description: Tool description
    """
    TOOL_REGISTRY[name] = {
        "type": "function",
        "name": name,
        "function": func,
        "description": description
    }


def get_tool(name: str) -> Optional[Any]:
    """
    Retrieve a tool class by name.
    """
    return TOOL_REGISTRY.get(name)


def list_tools() -> List[str]:
    """
    List registered tool names.
    """
    return list(TOOL_REGISTRY.keys())


# Register MCP tools
def initialize_mcp_tools() -> None:
    """Initialize and register MCP tools."""
    from .pdf_tool import pdf_text_extraction_tool
    from .image_tool import (
        image_feature_detection_tool,
        image_edge_detection_tool,
        image_object_detection_tool,
    )
    from .encryption_tool_mcp import (
        encrypt_string_tool,
        decrypt_string_tool,
        encrypt_file_tool,
        decrypt_file_tool,
        generate_encryption_key_tool,
    )
    
    register_function_tool(
        "pdf_text_extraction",
        pdf_text_extraction_tool,
        "Extract text from PDF files with layout preservation"
    )
    
    register_function_tool(
        "image_feature_detection",
        image_feature_detection_tool,
        "Detect features in images using computer vision"
    )
    
    register_function_tool(
        "image_edge_detection",
        image_edge_detection_tool,
        "Detect edges in images"
    )
    
    register_function_tool(
        "image_object_detection",
        image_object_detection_tool,
        "Detect objects using contour analysis"
    )
    
    register_function_tool(
        "encrypt_string",
        encrypt_string_tool,
        "Encrypt text using AES-256-GCM"
    )
    
    register_function_tool(
        "decrypt_string",
        decrypt_string_tool,
        "Decrypt text using AES-256-GCM"
    )
    
    register_function_tool(
        "encrypt_file",
        encrypt_file_tool,
        "Encrypt file using AES-256-GCM"
    )
    
    register_function_tool(
        "decrypt_file",
        decrypt_file_tool,
        "Decrypt file using AES-256-GCM"
    )
    
    register_function_tool(
        "generate_encryption_key",
        generate_encryption_key_tool,
        "Generate random 256-bit encryption key"
    )
