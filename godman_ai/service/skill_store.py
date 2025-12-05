"""
Skill Store for GodmanAI

Allows dynamic installation of tools and plugins.
"""

import logging
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
import urllib.request
import json

logger = logging.getLogger(__name__)


class SkillStore:
    """Manages installation of skills (tools/plugins)"""
    
    def __init__(self):
        self.plugins_dir = Path(__file__).parent.parent / "plugins"
        self.plugins_dir.mkdir(exist_ok=True)
        
        self.catalog_url = "https://raw.githubusercontent.com/Steve0465/godman-skills/main/catalog.json"
        self.catalog_cache = Path.home() / ".godman" / "skills_catalog.json"
    
    def _fetch_catalog(self) -> Dict:
        """Fetch skill catalog from remote or cache"""
        try:
            # Try to fetch from remote
            with urllib.request.urlopen(self.catalog_url, timeout=5) as response:
                data = json.loads(response.read().decode())
                
                # Cache it
                self.catalog_cache.parent.mkdir(parents=True, exist_ok=True)
                with open(self.catalog_cache, "w") as f:
                    json.dump(data, f)
                
                return data
        except Exception as e:
            logger.warning(f"Could not fetch remote catalog: {e}")
            
            # Fallback to cache
            if self.catalog_cache.exists():
                with open(self.catalog_cache) as f:
                    return json.load(f)
            
            # Return default catalog
            return {
                "skills": [
                    {
                        "name": "ocr-tool",
                        "description": "OCR processing tool",
                        "url": "https://raw.githubusercontent.com/Steve0465/godman-skills/main/ocr_tool.py",
                        "type": "tool"
                    },
                    {
                        "name": "vision-tool",
                        "description": "Vision analysis tool",
                        "url": "https://raw.githubusercontent.com/Steve0465/godman-skills/main/vision_tool.py",
                        "type": "tool"
                    }
                ]
            }
    
    def list_available(self) -> List[Dict]:
        """List available skills in catalog"""
        catalog = self._fetch_catalog()
        return catalog.get("skills", [])
    
    def install(self, name: str) -> bool:
        """
        Install a skill by name
        
        Args:
            name: Skill name from catalog
            
        Returns:
            True if installation successful
        """
        catalog = self._fetch_catalog()
        skills = catalog.get("skills", [])
        
        # Find skill
        skill = None
        for s in skills:
            if s["name"] == name:
                skill = s
                break
        
        if not skill:
            logger.error(f"Skill '{name}' not found in catalog")
            return False
        
        logger.info(f"Installing skill: {name}")
        
        try:
            # Download skill file
            url = skill["url"]
            filename = Path(url).name
            dest_path = self.plugins_dir / filename
            
            logger.info(f"Downloading from {url}")
            with urllib.request.urlopen(url, timeout=10) as response:
                with open(dest_path, "wb") as f:
                    f.write(response.read())
            
            logger.info(f"✅ Skill '{name}' installed to {dest_path}")
            
            # Auto-register plugin
            self._register_plugin(dest_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to install skill '{name}': {e}", exc_info=True)
            return False
    
    def _register_plugin(self, plugin_path: Path):
        """Register a plugin after installation"""
        try:
            from godman_ai.os_core.plugin_manager import PluginManager
            
            manager = PluginManager()
            manager.load_plugins()
            
            logger.info(f"Plugin registered: {plugin_path.name}")
        except Exception as e:
            logger.warning(f"Could not auto-register plugin: {e}")
    
    def uninstall(self, name: str) -> bool:
        """Uninstall a skill"""
        # Find installed plugin file
        for plugin_file in self.plugins_dir.glob("*.py"):
            if name in plugin_file.stem:
                try:
                    plugin_file.unlink()
                    logger.info(f"✅ Skill '{name}' uninstalled")
                    return True
                except Exception as e:
                    logger.error(f"Failed to uninstall '{name}': {e}")
                    return False
        
        logger.error(f"Skill '{name}' not found")
        return False
    
    def list_installed(self) -> List[str]:
        """List installed skills"""
        return [f.stem for f in self.plugins_dir.glob("*.py") if f.stem != "__init__"]
