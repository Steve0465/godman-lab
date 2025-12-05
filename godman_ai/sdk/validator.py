"""
Skill Validator for GodmanAI SDK

Validates skill manifests and structure.
"""

import importlib.util
import sys
from pathlib import Path
from typing import List


def validate_manifest(manifest: dict) -> List[str]:
    """
    Validate a skill manifest dictionary.
    
    Args:
        manifest: Parsed manifest data
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    # Required fields
    required = ["name", "version", "type", "entrypoint"]
    for field in required:
        if field not in manifest:
            errors.append(f"Missing required field: {field}")
    
    # Type validation
    if "type" in manifest:
        valid_types = ["tool", "agent", "mixed"]
        if manifest["type"] not in valid_types:
            errors.append(f"Invalid type: {manifest['type']}. Must be one of: {valid_types}")
    
    # Entrypoint format
    if "entrypoint" in manifest:
        if ":" not in manifest["entrypoint"]:
            errors.append("Entrypoint must be in format 'module:ClassName'")
    
    return errors


def validate_skill(path: Path) -> List[str]:
    """
    Validate a complete skill directory or archive.
    
    Args:
        path: Path to skill directory
        
    Returns:
        List of validation error messages (empty if valid)
    """
    path = Path(path)
    errors = []
    
    if not path.exists():
        return [f"Skill path does not exist: {path}"]
    
    # Check manifest exists
    manifest_path = path / "manifest.yaml"
    if not manifest_path.exists():
        errors.append("Missing manifest.yaml")
        return errors
    
    # Parse and validate manifest
    try:
        import yaml
        with open(manifest_path) as f:
            manifest = yaml.safe_load(f)
        
        errors.extend(validate_manifest(manifest))
        
        # Validate entrypoint exists and is importable
        if "entrypoint" in manifest and ":" in manifest["entrypoint"]:
            module_name, class_name = manifest["entrypoint"].split(":", 1)
            module_path = path / f"{module_name}.py"
            
            if not module_path.exists():
                errors.append(f"Entrypoint module not found: {module_name}.py")
            else:
                # Try to load and validate class
                try:
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        if not hasattr(module, class_name):
                            errors.append(f"Class {class_name} not found in {module_name}.py")
                        else:
                            cls = getattr(module, class_name)
                            
                            # Validate tool type
                            if manifest.get("type") == "tool":
                                # Check if it's a BaseTool subclass (lazy check)
                                if not hasattr(cls, "run"):
                                    errors.append(f"{class_name} must have a 'run' method")
                
                except Exception as e:
                    errors.append(f"Failed to load entrypoint: {e}")
    
    except ImportError:
        errors.append("PyYAML not installed. Install with: pip install pyyaml")
    except Exception as e:
        errors.append(f"Failed to parse manifest.yaml: {e}")
    
    return errors
