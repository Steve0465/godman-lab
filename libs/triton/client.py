"""Triton Inference Server client interface.

Provides a thin client wrapper for Triton with offline mode support.
In offline mode (default), all methods return stub data without requiring
a live Triton server.
"""
from typing import Any, Optional
from libs.triton.models import TritonConfig, ModelMetadata


class TritonClient:
    """Client interface for Triton Inference Server.
    
    Supports both offline mode (stub responses) and live mode (actual network calls).
    Offline mode is enabled by default for development and testing without a live server.
    
    Attributes:
        config: Triton server configuration
        offline_mode: If True, return stub data instead of making network calls
    
    Example:
        ```python
        # Offline mode (default)
        config = TritonConfig(endpoint_url="http://nas.local:8000")
        client = TritonClient(config, offline_mode=True)
        health = client.health_check()  # Returns stub data
        
        # Live mode (requires running Triton server)
        client_live = TritonClient(config, offline_mode=False)
        health = client_live.health_check()  # Makes actual network call
        ```
    """
    
    def __init__(self, config: TritonConfig, offline_mode: bool = True):
        """Initialize Triton client.
        
        Args:
            config: Triton server configuration
            offline_mode: If True, use stub responses without network calls (default: True)
        """
        self.config = config
        self.offline_mode = offline_mode
        
        if not offline_mode:
            # In live mode, we would initialize actual Triton client libraries here
            # For now, we raise NotImplementedError to indicate live mode is not yet supported
            pass
    
    def health_check(self) -> dict[str, Any]:
        """Check Triton server health status.
        
        Returns:
            dict: Health status with keys:
                - ready (bool): Server is ready to accept requests
                - live (bool): Server process is running
                - model_ready (bool): At least one model is ready
        
        Example:
            ```python
            client = TritonClient(config)
            health = client.health_check()
            if health["ready"]:
                print("Server is ready!")
            ```
        """
        if self.offline_mode:
            return {
                "ready": True,
                "live": True,
                "model_ready": True,
                "offline_mode": True,
            }
        
        raise NotImplementedError(
            "Live mode health check not yet implemented. "
            "Use offline_mode=True for development."
        )
    
    def infer(
        self,
        model_name: str,
        inputs: dict[str, Any],
        model_version: Optional[str] = None
    ) -> dict[str, Any]:
        """Run inference on a Triton model.
        
        Args:
            model_name: Name of the model to run inference on
            inputs: Dictionary mapping input tensor names to data
            model_version: Specific model version (None for latest)
        
        Returns:
            dict: Inference results with keys:
                - outputs (dict): Model output tensors
                - model_name (str): Model used for inference
                - model_version (str): Version used
        
        Example:
            ```python
            client = TritonClient(config)
            result = client.infer(
                model_name="object_detection",
                inputs={"input_frames": frame_data}
            )
            detections = result["outputs"]["detections"]
            ```
        """
        if self.offline_mode:
            return {
                "outputs": {
                    "detections": [[0.1, 0.2, 0.8, 0.9, 0.95]],  # Stub bbox + confidence
                    "scores": [0.95],
                },
                "model_name": model_name,
                "model_version": model_version or "1",
                "offline_mode": True,
            }
        
        raise NotImplementedError(
            "Live mode inference not yet implemented. "
            "Use offline_mode=True for development."
        )
    
    def get_model_metadata(
        self,
        model_name: str,
        model_version: Optional[str] = None
    ) -> ModelMetadata:
        """Get metadata for a specific model.
        
        Args:
            model_name: Name of the model
            model_version: Specific model version (None for latest)
        
        Returns:
            ModelMetadata: Model configuration and capabilities
        
        Example:
            ```python
            client = TritonClient(config)
            metadata = client.get_model_metadata("object_detection")
            print(f"Backend: {metadata.backend}")
            print(f"Inputs: {metadata.inputs}")
            ```
        """
        if self.offline_mode:
            return ModelMetadata(
                name=model_name,
                version=model_version or "1",
                backend="tensorrt",
                inputs=["input_frames"],
                outputs=["detections", "scores"],
                max_batch_size=8,
            )
        
        raise NotImplementedError(
            "Live mode metadata retrieval not yet implemented. "
            "Use offline_mode=True for development."
        )
    
    def list_models(self) -> list[str]:
        """List all available models on the Triton server.
        
        Returns:
            list[str]: Names of available models
        
        Example:
            ```python
            client = TritonClient(config)
            models = client.list_models()
            print(f"Available models: {', '.join(models)}")
            ```
        """
        if self.offline_mode:
            return [
                "object_detection",
                "audio_transcription",
                "video_classifier",
                "image_upscaler",
            ]
        
        raise NotImplementedError(
            "Live mode model listing not yet implemented. "
            "Use offline_mode=True for development."
        )
