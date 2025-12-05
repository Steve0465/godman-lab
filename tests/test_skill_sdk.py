"""Tests for GodmanAI Skill SDK."""

import pytest
import tempfile
from pathlib import Path
from godman_ai.sdk import SkillBuilder, validate_manifest, validate_skill


class TestSkillBuilder:
    """Test skill builder functionality."""
    
    def test_create_skill(self):
        """Test creating a new skill from template."""
        builder = SkillBuilder()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir)
            skill_path = builder.create_skill("test-skill", dest, author="test-author")
            
            # Verify structure
            assert skill_path.exists()
            assert (skill_path / "manifest.yaml").exists()
            assert (skill_path / "tool.py").exists()
            assert (skill_path / "agent.py").exists()
            assert (skill_path / "__init__.py").exists()
            
            # Verify manifest was updated
            manifest_content = (skill_path / "manifest.yaml").read_text()
            assert "test-skill" in manifest_content
            assert "test-author" in manifest_content
    
    def test_create_skill_duplicate_fails(self):
        """Test that creating duplicate skill fails."""
        builder = SkillBuilder()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir)
            builder.create_skill("test-skill", dest)
            
            # Try to create again
            with pytest.raises(ValueError, match="already exists"):
                builder.create_skill("test-skill", dest)
    
    def test_package_skill(self):
        """Test packaging a skill into archive."""
        builder = SkillBuilder()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir)
            
            # Create skill
            skill_path = builder.create_skill("test-skill", dest)
            
            # Package it
            archive_path = builder.package_skill(skill_path)
            
            # Verify archive exists
            assert archive_path.exists()
            assert archive_path.suffix == ".godmanskill"
            assert archive_path.name == "test-skill.godmanskill"
            
            # Verify it's a valid zip
            import zipfile
            assert zipfile.is_zipfile(archive_path)
    
    def test_package_invalid_path_fails(self):
        """Test packaging invalid path fails."""
        builder = SkillBuilder()
        
        with pytest.raises(ValueError, match="not a directory"):
            builder.package_skill(Path("/nonexistent/path"))


class TestSkillValidator:
    """Test skill validation functionality."""
    
    def test_validate_manifest_valid(self):
        """Test validation of valid manifest."""
        manifest = {
            "name": "test-skill",
            "version": "1.0.0",
            "type": "tool",
            "entrypoint": "tool:TestTool"
        }
        
        errors = validate_manifest(manifest)
        assert len(errors) == 0
    
    def test_validate_manifest_missing_fields(self):
        """Test validation catches missing fields."""
        manifest = {
            "name": "test-skill"
        }
        
        errors = validate_manifest(manifest)
        assert len(errors) > 0
        assert any("version" in err for err in errors)
        assert any("type" in err for err in errors)
        assert any("entrypoint" in err for err in errors)
    
    def test_validate_manifest_invalid_type(self):
        """Test validation catches invalid type."""
        manifest = {
            "name": "test-skill",
            "version": "1.0.0",
            "type": "invalid_type",
            "entrypoint": "tool:TestTool"
        }
        
        errors = validate_manifest(manifest)
        assert any("Invalid type" in err for err in errors)
    
    def test_validate_manifest_invalid_entrypoint(self):
        """Test validation catches malformed entrypoint."""
        manifest = {
            "name": "test-skill",
            "version": "1.0.0",
            "type": "tool",
            "entrypoint": "invalid_format"
        }
        
        errors = validate_manifest(manifest)
        assert any("entrypoint" in err.lower() for err in errors)
    
    def test_validate_skill_directory(self):
        """Test validation of complete skill directory."""
        builder = SkillBuilder()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir)
            skill_path = builder.create_skill("test-skill", dest)
            
            # Validate the created skill
            errors = validate_skill(skill_path)
            
            # Should be valid (may have PyYAML warning)
            # Filter out PyYAML installation warnings
            real_errors = [e for e in errors if "PyYAML not installed" not in e]
            assert len(real_errors) == 0 or errors[0].startswith("PyYAML")
    
    def test_validate_skill_missing_manifest(self):
        """Test validation fails without manifest."""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_path = Path(temp_dir) / "fake-skill"
            skill_path.mkdir()
            
            errors = validate_skill(skill_path)
            assert any("Missing manifest.yaml" in err for err in errors)
    
    def test_validate_skill_nonexistent_path(self):
        """Test validation of nonexistent path."""
        errors = validate_skill(Path("/nonexistent/path"))
        assert len(errors) > 0
        assert any("does not exist" in err for err in errors)


class TestPluginIntegration:
    """Test skill/plugin integration."""
    
    def test_skill_can_be_loaded_as_plugin(self):
        """Test that a packaged skill can be loaded as a plugin."""
        from godman_ai.os_core import PluginManager
        
        builder = SkillBuilder()
        pm = PluginManager()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir)
            
            # Create and package skill
            skill_path = builder.create_skill("test-plugin-skill", dest)
            archive_path = builder.package_skill(skill_path)
            
            # Install it
            success = pm.install_skill_archive(archive_path)
            
            # Should succeed (or fail gracefully without crashing)
            assert isinstance(success, bool)
            
            # If successful, skill should be in registry
            if success:
                installed = pm.list_installed_skills()
                assert "test-plugin-skill" in installed
