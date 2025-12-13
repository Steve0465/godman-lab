"""Skill loader for packaged skills with manifest validation."""

from __future__ import annotations

import importlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REQUIRED_FIELDS = {"name", "version", "description", "entrypoint"}


class SkillLoadError(Exception):
    """Raised when a skill fails to load or validate."""


def _parse_manifest(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    data: Dict[str, Any] = {}
    try:
        import yaml  # type: ignore
    except ImportError:
        yaml = None  # type: ignore

    if yaml:
        try:
            loaded = yaml.safe_load(text)
            if isinstance(loaded, dict):
                data = loaded
        except Exception as exc:
            raise SkillLoadError(f"Failed to parse manifest {path}: {exc}") from exc
    else:
        try:
            data = json.loads(text)
        except Exception:
            # Minimal YAML-like fallback to support simple manifests without PyYAML
            current_key: Optional[str] = None
            for raw_line in text.splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("- "):
                    if not current_key:
                        continue
                    data.setdefault(current_key, [])
                    data[current_key].append(line[2:].strip())
                    continue
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip()
                    val = val.strip().strip('"')
                    current_key = key
                    if val:
                        data[key] = val
                    else:
                        data[key] = data.get(key, [])
    return data


def _validate_manifest(manifest: Dict[str, Any]) -> None:
    missing = REQUIRED_FIELDS - set(manifest.keys())
    if missing:
        raise SkillLoadError(f"Manifest missing required fields: {sorted(missing)}")
    if not isinstance(manifest.get("entrypoint"), str):
        raise SkillLoadError("Manifest entrypoint must be a string like 'module:func'")


def _import_entrypoint(entrypoint: str):
    if ":" not in entrypoint:
        raise SkillLoadError("Entrypoint must be in format 'module:function'")
    module_name, func_name = entrypoint.split(":", 1)
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        raise SkillLoadError(f"Failed to import module {module_name}: {exc}") from exc
    if not hasattr(module, func_name):
        raise SkillLoadError(f"Entrypoint function '{func_name}' missing in {module_name}")
    return getattr(module, func_name)


@dataclass
class Skill:
    manifest: Dict[str, Any]
    handler: Any
    path: Path


def load_skill(path: Path | str) -> Skill:
    """Load a single skill directory containing skill.yaml."""
    skill_path = Path(path)
    manifest_path = skill_path / "skill.yaml"
    if not manifest_path.exists():
        raise SkillLoadError(f"Missing manifest at {manifest_path}")

    manifest = _parse_manifest(manifest_path)
    _validate_manifest(manifest)
    handler = _import_entrypoint(manifest["entrypoint"])
    return Skill(manifest=manifest, handler=handler, path=skill_path)


def load_all_skills(directory: Path | str) -> List[Skill]:
    """Load all skills in a directory (non-recursive)."""
    base = Path(directory)
    skills: List[Skill] = []
    if not base.exists():
        return skills
    for item in base.iterdir():
        if item.is_dir() and (item / "skill.yaml").exists():
            skills.append(load_skill(item))
    return skills
