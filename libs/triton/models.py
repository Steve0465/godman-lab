"""Configuration models for Triton Inference Server integration.

Defines type-safe configuration schemas using Pydantic for:
- Triton server configuration
- Model metadata
"""
from typing import Optional, Literal, List
from pydantic import BaseModel, ConfigDict, Field


class TritonConfig(BaseModel):
    """Configuration for Triton Inference Server connection.
    
    Attributes:
        endpoint_url: Full URL to Triton server (e.g., "http://localhost:8000")
        protocol: Communication protocol ("http" or "grpc")
        model_name: Optional default model name for inference requests
        timeout_seconds: Request timeout in seconds
        verify_ssl: Whether to verify SSL certificates
    
    Example:
        ```python
        config = TritonConfig(
            endpoint_url="http://nas.local:8000",
            protocol="http",
            model_name="video_detector"
        )
        ```
    """
    endpoint_url: str = Field(
        default="http://localhost:8000",
        description="Triton server endpoint URL"
    )
    protocol: Literal["http", "grpc"] = Field(
        default="http",
        description="Communication protocol"
    )
    model_name: Optional[str] = Field(
        default=None,
        description="Default model name for inference"
    )
    timeout_seconds: int = Field(
        default=30,
        description="Request timeout in seconds"
    )
    verify_ssl: bool = Field(
        default=True,
        description="Verify SSL certificates"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "endpoint_url": "http://nas.local:8000",
                "protocol": "http",
                "model_name": "video_detector",
                "timeout_seconds": 30,
                "verify_ssl": True
            }
        }
    )


class ModelMetadata(BaseModel):
    """Metadata for a Triton model.
    
    Attributes:
        name: Model name as registered in Triton
        version: Model version (defaults to latest if not specified)
        backend: Model backend type (e.g., "tensorrt", "pytorch", "onnx")
        platform: Platform identifier (optional)
        inputs: List of input tensor names
        outputs: List of output tensor names
        max_batch_size: Maximum batch size supported
    
    Example:
        ```python
        metadata = ModelMetadata(
            name="object_detection",
            version="1",
            backend="tensorrt",
            inputs=["input_frames"],
            outputs=["detections", "scores"]
        )
        ```
    """
    name: str = Field(
        description="Model name"
    )
    version: Optional[str] = Field(
        default=None,
        description="Model version (None for latest)"
    )
    backend: Optional[str] = Field(
        default=None,
        description="Model backend (tensorrt, pytorch, onnx, etc.)"
    )
    platform: Optional[str] = Field(
        default=None,
        description="Platform identifier"
    )
    inputs: List[str] = Field(
        default_factory=list,
        description="Input tensor names"
    )
    outputs: List[str] = Field(
        default_factory=list,
        description="Output tensor names"
    )
    max_batch_size: int = Field(
        default=1,
        description="Maximum batch size"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "object_detection",
                "version": "1",
                "backend": "tensorrt",
                "inputs": ["input_frames"],
                "outputs": ["detections", "scores"],
                "max_batch_size": 8
            }
        }
    )
