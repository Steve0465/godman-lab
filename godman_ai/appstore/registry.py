"""
Skill Registry API

Manages the local skill registry with support for bundled defaults
and user-override registries.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class SkillRegistry:
    """
    Manages the skill registry for the GodmanAI App Store.
    
    Loads from user override if present, otherwise uses bundled index.
    """
    
    def __init__(self, override_path: Optional[Path] = None):
        """
        Initialize the registry.
        
        Args:
            override_path: Optional path to override registry file
        """
        self.skills: List[Dict] = []
        self._load_registry(override_path)
    
    def _load_registry(self, override_path: Optional[Path] = None):
        """Load registry from file system."""
        # Check for user override first
        user_registry = Path.home() / ".godman" / "registry" / "skills.json"
        
        if override_path and override_path.exists():
            registry_path = override_path
            logger.info(f"Loading registry from override: {registry_path}")
        elif user_registry.exists():
            registry_path = user_registry
            logger.info(f"Loading registry from user override: {registry_path}")
        else:
            # Use bundled default
            registry_path = Path(__file__).parent / "index.json"
            logger.info(f"Loading bundled registry: {registry_path}")
        
        try:
            with open(registry_path, 'r') as f:
                self.skills = json.load(f)
            logger.debug(f"Loaded {len(self.skills)} skills from registry")
        except Exception as e:
            logger.error(f"Failed to load registry: {e}")
            self.skills = []
    
    def list(self) -> List[Dict]:
        """
        Return all skills in the registry.
        
        Returns:
            List of skill dictionaries
        """
        return self.skills.copy()
    
    def search(self, query: str) -> List[Dict]:
        """
        Search for skills by name, description, or tags.
        
        Args:
            query: Search query string (case-insensitive)
        
        Returns:
            List of matching skill dictionaries
        """
        query_lower = query.lower()
        results = []
        
        for skill in self.skills:
            # Check name
            if query_lower in skill.get("name", "").lower():
                results.append(skill)
                continue
            
            # Check description
            if query_lower in skill.get("description", "").lower():
                results.append(skill)
                continue
            
            # Check tags
            tags = skill.get("tags", [])
            if any(query_lower in tag.lower() for tag in tags):
                results.append(skill)
                continue
        
        logger.debug(f"Search '{query}' returned {len(results)} results")
        return results
    
    def get(self, name: str) -> Optional[Dict]:
        """
        Get a specific skill by name.
        
        Args:
            name: Skill name
        
        Returns:
            Skill dictionary or None if not found
        """
        for skill in self.skills:
            if skill.get("name") == name:
                return skill.copy()
        
        logger.debug(f"Skill '{name}' not found in registry")
        return None
    
    def add(self, skill: Dict):
        """
        Add a new skill to the registry (runtime only).
        
        Args:
            skill: Skill dictionary with required fields
        """
        required_fields = ["name", "version", "description"]
        if not all(field in skill for field in required_fields):
            raise ValueError(f"Skill must contain: {required_fields}")
        
        # Check for duplicate
        if self.get(skill["name"]):
            raise ValueError(f"Skill '{skill['name']}' already exists")
        
        self.skills.append(skill)
        logger.info(f"Added skill '{skill['name']}' to registry")
    
    def save(self, path: Optional[Path] = None):
        """
        Save registry to file.
        
        Args:
            path: Optional custom save path, defaults to user registry
        """
        if path is None:
            path = Path.home() / ".godman" / "registry" / "skills.json"
        
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(self.skills, f, indent=2)
        
        logger.info(f"Registry saved to {path}")
