"""
Configuration loader with multi-source support.
"""
import os
import yaml
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_cached_settings = None


def load_settings(reload: bool = False):
    """
    Load settings from multiple sources with precedence:
    1. Environment variables (highest priority)
    2. ~/.godman/config.yaml
    3. .env file in project root
    4. Defaults (lowest priority)
    
    Args:
        reload: Force reload settings from disk
        
    Returns:
        Settings instance
    """
    global _cached_settings
    
    if _cached_settings is not None and not reload:
        return _cached_settings
    
    from godman_ai.config.settings import Settings, create_pydantic_settings
    
    settings_data = {}
    
    # 1. Try loading from ~/.godman/config.yaml
    home_config = Path.home() / ".godman" / "config.yaml"
    if home_config.exists():
        try:
            with open(home_config, 'r') as f:
                yaml_data = yaml.safe_load(f) or {}
                settings_data.update(yaml_data)
                logger.debug(f"Loaded config from {home_config}")
        except Exception as e:
            logger.warning(f"Error loading {home_config}: {e}")
    
    # 2. Try loading from .env file
    env_file = Path(".env")
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            logger.debug("Loaded .env file")
        except ImportError:
            logger.debug("python-dotenv not installed, skipping .env file")
        except Exception as e:
            logger.warning(f"Error loading .env: {e}")
    
    # 3. Load from environment variables
    env_keys = [
        'OPENAI_API_KEY', 'LOG_LEVEL', 'SCHEDULER_ENABLED', 'MEMORY_ENABLED',
        'EMAIL_HOST', 'EMAIL_PORT', 'EMAIL_USER', 'EMAIL_PASSWORD',
        'TRELLO_API_KEY', 'TRELLO_TOKEN'
    ]
    
    for key in env_keys:
        value = os.environ.get(key)
        if value is not None:
            # Convert to lowercase for settings_data
            settings_key = key.lower()
            
            # Handle boolean conversion
            if settings_key in ['scheduler_enabled', 'memory_enabled']:
                value = value.lower() in ('true', '1', 'yes', 'on')
            
            # Handle int conversion
            if settings_key == 'email_port':
                try:
                    value = int(value)
                except ValueError:
                    pass
            
            settings_data[settings_key] = value
    
    # 4. Try to create Pydantic settings (falls back to basic Settings)
    SettingsClass = create_pydantic_settings()
    
    try:
        if hasattr(SettingsClass, 'model_validate'):
            # Pydantic v2
            _cached_settings = SettingsClass.model_validate(settings_data)
        elif hasattr(SettingsClass, '__init__'):
            # Basic Settings class
            _cached_settings = SettingsClass(**settings_data)
        else:
            _cached_settings = SettingsClass()
    except Exception as e:
        logger.warning(f"Error creating settings: {e}")
        _cached_settings = Settings()
    
    logger.debug(f"Settings loaded: {_cached_settings}")
    return _cached_settings


def save_config(config_data: dict, target: str = "user"):
    """
    Save configuration to file.
    
    Args:
        config_data: Configuration dictionary
        target: "user" for ~/.godman/config.yaml, "local" for ./.env
    """
    if target == "user":
        config_path = Path.home() / ".godman" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False)
        
        logger.info(f"Saved config to {config_path}")
    
    elif target == "local":
        env_path = Path(".env")
        
        lines = []
        for key, value in config_data.items():
            env_key = key.upper()
            lines.append(f"{env_key}={value}\n")
        
        with open(env_path, 'w') as f:
            f.writelines(lines)
        
        logger.info(f"Saved config to {env_path}")
