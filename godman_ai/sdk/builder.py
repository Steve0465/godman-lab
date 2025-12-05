"""
Skill Builder for GodmanAI SDK

Provides tools for creating and packaging custom skills.
"""

import shutil
import zipfile
from pathlib import Path
from typing import Optional


class SkillBuilder:
    """Builder for creating and packaging GodmanAI skills."""
    
    def __init__(self):
        self.template_dir = Path(__file__).parent / "skill_template"
    
    def create_skill(self, name: str, dest: Path, author: str = "unknown") -> Path:
        """
        Create a new skill from template.
        
        Args:
            name: Skill name (hyphenated)
            dest: Destination directory
            author: Skill author name
            
        Returns:
            Path: Path to created skill directory
        """
        skill_path = dest / name
        
        if skill_path.exists():
            raise ValueError(f"Skill directory already exists: {skill_path}")
        
        # Copy template
        shutil.copytree(self.template_dir, skill_path)
        
        # Update manifest
        manifest_path = skill_path / "manifest.yaml"
        if manifest_path.exists():
            content = manifest_path.read_text()
            content = content.replace("name: my-skill", f"name: {name}")
            content = content.replace("author: unknown", f"author: {author}")
            manifest_path.write_text(content)
        
        return skill_path
    
    def package_skill(self, path: Path, output_dir: Optional[Path] = None) -> Path:
        """
        Package a skill into a .godmanskill archive.
        
        Args:
            path: Path to skill directory
            output_dir: Optional output directory (defaults to path parent)
            
        Returns:
            Path: Path to created .godmanskill file
        """
        path = Path(path)
        
        if not path.is_dir():
            raise ValueError(f"Skill path is not a directory: {path}")
        
        manifest = path / "manifest.yaml"
        if not manifest.exists():
            raise ValueError(f"Missing manifest.yaml in {path}")
        
        # Determine output path
        if output_dir is None:
            output_dir = path.parent
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        skill_name = path.name
        archive_path = output_dir / f"{skill_name}.godmanskill"
        
        # Create zip archive
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(path)
                    zf.write(file_path, arcname)
        
        return archive_path
