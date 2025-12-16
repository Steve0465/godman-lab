from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any

class Protocol(str, Enum):
    HTTP = "http"
    GRPC = "grpc"

@dataclass
class TritonConfig:
    endpoint_url: str
    protocol: Protocol = Protocol.HTTP
    model_repository: str = "/models"
    verbose: bool = False

@dataclass
class ModelRouting:
    model_name: str
    version: str = "1"
    metadata: Dict[str, Any] = field(default_factory=dict)
