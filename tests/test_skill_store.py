"""Tests for skill store"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch


def test_skill_store_initialization():
    """Test SkillStore can be initialized"""
    from godman_ai.service.skill_store import SkillStore
    
    store = SkillStore()
    assert store.plugins_dir.exists()


def test_list_available_skills():
    """Test listing available skills"""
    from godman_ai.service.skill_store import SkillStore
    
    store = SkillStore()
    
    # Mock the catalog fetch
    with patch.object(store, '_fetch_catalog') as mock_fetch:
        mock_fetch.return_value = {
            "skills": [
                {"name": "test-tool", "description": "Test tool", "url": "http://example.com/tool.py"}
            ]
        }
        
        skills = store.list_available()
        assert isinstance(skills, list)
        assert len(skills) > 0
        assert skills[0]["name"] == "test-tool"


def test_list_installed_skills():
    """Test listing installed skills"""
    from godman_ai.service.skill_store import SkillStore
    
    store = SkillStore()
    installed = store.list_installed()
    
    assert isinstance(installed, list)
