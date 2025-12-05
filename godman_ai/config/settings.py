"""
Settings configuration using Pydantic (lazy import).
"""
from typing import Optional


class Settings:
    """
    Application settings loaded from environment, .env, and config files.
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        log_level: str = "INFO",
        scheduler_enabled: bool = True,
        memory_enabled: bool = True,
        api_token: Optional[str] = None,
        email_host: Optional[str] = None,
        email_port: int = 587,
        email_user: Optional[str] = None,
        email_password: Optional[str] = None,
        trello_api_key: Optional[str] = None,
        trello_token: Optional[str] = None,
        **kwargs
    ):
        self.openai_api_key = openai_api_key
        self.log_level = log_level
        self.scheduler_enabled = scheduler_enabled
        self.memory_enabled = memory_enabled
        self.api_token = api_token
        self.email_host = email_host
        self.email_port = email_port
        self.email_user = email_user
        self.email_password = email_password
        self.trello_api_key = trello_api_key
        self.trello_token = trello_token
        
        # Store any additional settings
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    @classmethod
    def from_dict(cls, data: dict) -> "Settings":
        """Create Settings from dictionary."""
        return cls(**data)
    
    def to_dict(self) -> dict:
        """Export settings as dictionary."""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith('_')
        }
    
    def __repr__(self):
        # Mask sensitive fields
        safe_dict = self.to_dict()
        for key in ['openai_api_key', 'email_password', 'trello_token', 'api_token']:
            if key in safe_dict and safe_dict[key]:
                safe_dict[key] = '***'
        return f"Settings({safe_dict})"


def create_pydantic_settings():
    """
    Create Pydantic-based settings if pydantic is available.
    Falls back to basic Settings class.
    """
    try:
        from pydantic_settings import BaseSettings as PydanticBaseSettings
        from pydantic import Field
        
        class PydanticSettings(PydanticBaseSettings):
            openai_api_key: Optional[str] = Field(None, alias="OPENAI_API_KEY")
            log_level: str = Field("INFO", alias="LOG_LEVEL")
            scheduler_enabled: bool = Field(True, alias="SCHEDULER_ENABLED")
            memory_enabled: bool = Field(True, alias="MEMORY_ENABLED")
            api_token: Optional[str] = Field(None, alias="GODMAN_API_TOKEN")
            email_host: Optional[str] = Field(None, alias="EMAIL_HOST")
            email_port: int = Field(587, alias="EMAIL_PORT")
            email_user: Optional[str] = Field(None, alias="EMAIL_USER")
            email_password: Optional[str] = Field(None, alias="EMAIL_PASSWORD")
            trello_api_key: Optional[str] = Field(None, alias="TRELLO_API_KEY")
            trello_token: Optional[str] = Field(None, alias="TRELLO_TOKEN")
            
            class Config:
                env_file = ".env"
                env_file_encoding = "utf-8"
                case_sensitive = False
        
        return PydanticSettings
    
    except ImportError:
        return Settings
