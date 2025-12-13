"""
Archive registry for the Unified Archive Framework.

Maintains a central index of known archives for easy access.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import json

from .base_archive import BaseArchive


# Global registry (in-memory)
_ARCHIVE_REGISTRY: Dict[str, Path] = {}


def register_archive(name: str, path: Path) -> None:
    """
    Register an archive in the global registry.
    
    Args:
        name: Archive name identifier
        path: Path to archive root directory
    """
    path = Path(path)
    _ARCHIVE_REGISTRY[name] = path


def unregister_archive(name: str) -> bool:
    """
    Remove an archive from the registry.
    
    Args:
        name: Archive name identifier
        
    Returns:
        True if archive was found and removed, False otherwise
    """
    if name in _ARCHIVE_REGISTRY:
        del _ARCHIVE_REGISTRY[name]
        return True
    return False


def get_archive(name: str, config: Optional[Dict[str, Any]] = None) -> Optional[BaseArchive]:
    """
    Get an archive from the registry.
    
    Args:
        name: Archive name identifier
        config: Optional configuration to pass to BaseArchive
        
    Returns:
        BaseArchive instance if found, None otherwise
    """
    if name not in _ARCHIVE_REGISTRY:
        return None
    
    path = _ARCHIVE_REGISTRY[name]
    return BaseArchive(root=path, name=name, config=config)


def list_archives() -> List[Dict[str, Any]]:
    """
    List all registered archives.
    
    Returns:
        List of dictionaries with archive information
    """
    archives = []
    for name, path in sorted(_ARCHIVE_REGISTRY.items()):
        archives.append({
            "name": name,
            "path": str(path),
            "exists": path.exists()
        })
    return archives


def clear_registry() -> None:
    """Clear all archives from the registry."""
    _ARCHIVE_REGISTRY.clear()


def load_from_config(config_path: Path) -> int:
    """
    Load archives from a JSON configuration file.
    
    Expected format:
    {
        "archives": [
            {"name": "archive1", "path": "/path/to/archive1"},
            {"name": "archive2", "path": "/path/to/archive2"}
        ]
    }
    
    Args:
        config_path: Path to JSON configuration file
        
    Returns:
        Number of archives loaded
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    archives = config.get("archives", [])
    count = 0
    
    for archive_config in archives:
        name = archive_config.get("name")
        path = archive_config.get("path")
        
        if name and path:
            register_archive(name, Path(path))
            count += 1
    
    return count


def save_to_config(config_path: Path) -> None:
    """
    Save the current registry to a JSON configuration file.
    
    Args:
        config_path: Path where to save the configuration
    """
    config_path = Path(config_path)
    
    archives = [
        {"name": name, "path": str(path)}
        for name, path in sorted(_ARCHIVE_REGISTRY.items())
    ]
    
    config = {"archives": archives}
    
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def archive_exists(name: str) -> bool:
    """
    Check if an archive is registered.
    
    Args:
        name: Archive name identifier
        
    Returns:
        True if archive is registered, False otherwise
    """
    return name in _ARCHIVE_REGISTRY


def get_archive_path(name: str) -> Optional[Path]:
    """
    Get the path of a registered archive.
    
    Args:
        name: Archive name identifier
        
    Returns:
        Path to archive root, or None if not found
    """
    return _ARCHIVE_REGISTRY.get(name)
