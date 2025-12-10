from dataclasses import dataclass
from typing import Optional


@dataclass
class Preset:
    """Model preset configuration for WebUI"""
    name: str
    model: str
    prompt: str
    id: Optional[str] = None
    
    def to_dict(self):
        return {
            "id": self.id or self.name.lower().replace(" ", "_"),
            "name": self.name,
            "model": self.model,
            "prompt": self.prompt
        }
