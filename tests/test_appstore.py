"""
Tests for App Store subsystem
"""

import json
import pytest
from pathlib import Path
from godman_ai.appstore import SkillRegistry, SkillFetcher


def test_registry_loads_bundled_index():
    """Test that registry loads bundled index.json by default."""
    registry = SkillRegistry()
    skills = registry.list()
    
    assert len(skills) >= 2
    assert any(s["name"] == "ocr-pro" for s in skills)
    assert any(s["name"] == "video-analyzer" for s in skills)


def test_registry_search():
    """Test registry search functionality."""
    registry = SkillRegistry()
    
    # Search by name
    results = registry.search("ocr")
    assert len(results) >= 1
    assert any(s["name"] == "ocr-pro" for s in results)
    
    # Search by tag
    results = registry.search("video")
    assert len(results) >= 1
    assert any(s["name"] == "video-analyzer" for s in results)
    
    # Search by description
    results = registry.search("receipts")
    assert len(results) >= 1


def test_registry_get():
    """Test getting specific skill by name."""
    registry = SkillRegistry()
    
    skill = registry.get("ocr-pro")
    assert skill is not None
    assert skill["name"] == "ocr-pro"
    assert "version" in skill
    assert "description" in skill
    
    # Non-existent skill
    skill = registry.get("non-existent-skill")
    assert skill is None


def test_registry_add():
    """Test adding new skill to registry."""
    registry = SkillRegistry()
    
    new_skill = {
        "name": "test-skill",
        "version": "1.0.0",
        "description": "Test skill",
        "url": "https://example.com/test.godmanskill",
        "tags": ["test"]
    }
    
    registry.add(new_skill)
    
    skill = registry.get("test-skill")
    assert skill is not None
    assert skill["name"] == "test-skill"


def test_registry_add_duplicate():
    """Test that adding duplicate skill raises error."""
    registry = SkillRegistry()
    
    skill = registry.list()[0]
    
    with pytest.raises(ValueError, match="already exists"):
        registry.add(skill)


def test_registry_add_invalid():
    """Test that adding invalid skill raises error."""
    registry = SkillRegistry()
    
    invalid_skill = {"name": "invalid"}
    
    with pytest.raises(ValueError, match="must contain"):
        registry.add(invalid_skill)


def test_registry_override(tmp_path):
    """Test loading registry from override path."""
    override_file = tmp_path / "custom_registry.json"
    
    custom_skills = [
        {
            "name": "custom-skill",
            "version": "1.0.0",
            "description": "Custom skill for testing",
            "url": "https://example.com/custom.godmanskill",
            "tags": ["custom"]
        }
    ]
    
    with open(override_file, 'w') as f:
        json.dump(custom_skills, f)
    
    registry = SkillRegistry(override_path=override_file)
    skills = registry.list()
    
    assert len(skills) == 1
    assert skills[0]["name"] == "custom-skill"


def test_fetcher_init():
    """Test fetcher initialization."""
    fetcher = SkillFetcher()
    assert fetcher.cache_dir.exists()


def test_fetcher_custom_cache(tmp_path):
    """Test fetcher with custom cache directory."""
    cache_dir = tmp_path / "cache"
    fetcher = SkillFetcher(cache_dir=cache_dir)
    
    assert fetcher.cache_dir == cache_dir
    assert cache_dir.exists()


def test_fetcher_cleanup(tmp_path):
    """Test fetcher cleanup."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    
    # Create dummy files
    (cache_dir / "skill1.godmanskill").touch()
    (cache_dir / "skill2.godmanskill").touch()
    (cache_dir / "other.txt").touch()
    
    fetcher = SkillFetcher(cache_dir=cache_dir)
    fetcher.cleanup()
    
    # Only .godmanskill files should be removed
    assert not (cache_dir / "skill1.godmanskill").exists()
    assert not (cache_dir / "skill2.godmanskill").exists()
    assert (cache_dir / "other.txt").exists()


def test_registry_save(tmp_path):
    """Test saving registry to file."""
    registry = SkillRegistry()
    
    new_skill = {
        "name": "saved-skill",
        "version": "1.0.0",
        "description": "Test save",
        "url": "https://example.com/saved.godmanskill",
        "tags": ["test"]
    }
    
    registry.add(new_skill)
    
    save_path = tmp_path / "saved_registry.json"
    registry.save(save_path)
    
    assert save_path.exists()
    
    # Load and verify
    with open(save_path) as f:
        saved_data = json.load(f)
    
    assert any(s["name"] == "saved-skill" for s in saved_data)
