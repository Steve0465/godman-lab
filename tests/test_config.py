"""
Tests for config subsystem.
"""
import pytest
import tempfile
import shutil
from pathlib import Path
import os


@pytest.fixture
def temp_config_dir():
    """Create temporary config directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_settings_basic():
    """Test basic settings creation."""
    from godman_ai.config import Settings
    
    settings = Settings(
        openai_api_key="test-key",
        log_level="DEBUG",
        scheduler_enabled=True
    )
    
    assert settings.openai_api_key == "test-key"
    assert settings.log_level == "DEBUG"
    assert settings.scheduler_enabled is True


def test_settings_defaults():
    """Test settings default values."""
    from godman_ai.config import Settings
    
    settings = Settings()
    
    assert settings.log_level == "INFO"
    assert settings.scheduler_enabled is True
    assert settings.memory_enabled is True
    assert settings.email_port == 587


def test_settings_to_dict():
    """Test exporting settings to dictionary."""
    from godman_ai.config import Settings
    
    settings = Settings(openai_api_key="test-key", log_level="DEBUG")
    data = settings.to_dict()
    
    assert isinstance(data, dict)
    assert data['openai_api_key'] == "test-key"
    assert data['log_level'] == "DEBUG"


def test_settings_from_dict():
    """Test creating settings from dictionary."""
    from godman_ai.config import Settings
    
    data = {
        'openai_api_key': 'test-key',
        'log_level': 'DEBUG',
        'custom_field': 'custom_value'
    }
    
    settings = Settings.from_dict(data)
    
    assert settings.openai_api_key == "test-key"
    assert settings.log_level == "DEBUG"
    assert settings.custom_field == "custom_value"


def test_load_settings_with_env_vars(monkeypatch):
    """Test loading settings from environment variables."""
    from godman_ai.config import load_settings
    
    # Set environment variables
    monkeypatch.setenv("OPENAI_API_KEY", "env-test-key")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")
    
    # Force reload
    settings = load_settings(reload=True)
    
    assert settings.openai_api_key == "env-test-key"
    assert settings.log_level == "WARNING"
    assert settings.scheduler_enabled is False


def test_save_config_yaml(temp_config_dir, monkeypatch):
    """Test saving config to YAML file."""
    from godman_ai.config import save_config
    
    # Override home directory
    home_path = Path(temp_config_dir)
    monkeypatch.setenv("HOME", str(home_path))
    
    config_data = {
        'openai_api_key': 'test-key',
        'log_level': 'DEBUG'
    }
    
    save_config(config_data, target="user")
    
    config_file = home_path / ".godman" / "config.yaml"
    assert config_file.exists()


def test_save_config_env(temp_config_dir, monkeypatch):
    """Test saving config to .env file."""
    from godman_ai.config import save_config
    
    # Change to temp directory
    original_dir = os.getcwd()
    os.chdir(temp_config_dir)
    
    try:
        config_data = {
            'openai_api_key': 'test-key',
            'log_level': 'DEBUG'
        }
        
        save_config(config_data, target="local")
        
        env_file = Path(temp_config_dir) / ".env"
        assert env_file.exists()
        
        content = env_file.read_text()
        assert "OPENAI_API_KEY=test-key" in content
        assert "LOG_LEVEL=DEBUG" in content
    
    finally:
        os.chdir(original_dir)


def test_settings_repr_masks_secrets():
    """Test that sensitive fields are masked in repr."""
    from godman_ai.config import Settings
    
    settings = Settings(
        openai_api_key="secret-key",
        email_password="secret-password"
    )
    
    repr_str = repr(settings)
    
    assert "secret-key" not in repr_str
    assert "secret-password" not in repr_str
    assert "***" in repr_str
