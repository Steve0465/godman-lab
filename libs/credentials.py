import os
import subprocess
from pathlib import Path
from typing import Dict


def get_att_credentials() -> Dict[str, str]:
    """
    Get AT&T credentials from macOS Keychain or environment variables.
    
    Returns:
        Dict with 'username' and 'password' keys
        
    Raises:
        ValueError: If credentials are not found
    """
    username = None
    password = None
    
    # Try macOS Keychain first
    try:
        username = _get_keychain_item("att-login", "username")
        password = _get_keychain_item("att-login", "password")
    except Exception:
        pass
    
    # Fallback to environment variables or .env file
    if not username:
        username = os.getenv("ATT_USERNAME")
    if not password:
        password = os.getenv("ATT_PASSWORD")
    
    # Try loading from .env file if not found
    if not username or not password:
        _load_env_file()
        if not username:
            username = os.getenv("ATT_USERNAME")
        if not password:
            password = os.getenv("ATT_PASSWORD")
    
    # Validate credentials exist
    if not username or not password:
        raise ValueError(
            "AT&T credentials not found. Please set them either:\n"
            "1. In macOS Keychain (service='att-login', account='username' or 'password')\n"
            "2. As environment variables: ATT_USERNAME and ATT_PASSWORD"
        )
    
    return {
        "username": username,
        "password": password
    }


def _get_keychain_item(service: str, account: str) -> str:
    """
    Retrieve a password from macOS Keychain.
    
    Args:
        service: Keychain service name
        account: Keychain account name
        
    Returns:
        The password/value from keychain
        
    Raises:
        Exception: If keychain lookup fails
    """
    result = subprocess.run(
        ["security", "find-generic-password", "-s", service, "-a", account, "-w"],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()


def _load_env_file():
    """Load environment variables from .env file if it exists."""
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip("'\"")
                    if key and value:
                        os.environ[key] = value
