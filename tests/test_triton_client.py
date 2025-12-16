"""Tests for Triton client interface."""
import pytest
from libs.triton.client import TritonClient
from libs.triton.models import TritonConfig, ModelMetadata


@pytest.fixture
def default_config():
    """Default Triton configuration for testing."""
    return TritonConfig(
        endpoint_url="http://localhost:8000",
        protocol="http",
        model_name="test_model",
    )


def test_client_initialization_offline_mode(default_config):
    """Test client initializes in offline mode by default."""
    client = TritonClient(default_config)
    
    assert client.config == default_config
    assert client.offline_mode is True


def test_client_initialization_explicit_offline(default_config):
    """Test client initializes with explicit offline mode."""
    client = TritonClient(default_config, offline_mode=True)
    
    assert client.offline_mode is True


def test_client_initialization_live_mode(default_config):
    """Test client initializes in live mode (no error yet)."""
    # Live mode initialization should not raise error
    client = TritonClient(default_config, offline_mode=False)
    
    assert client.offline_mode is False


def test_health_check_offline_mode(default_config):
    """Test health check returns stub data in offline mode."""
    client = TritonClient(default_config, offline_mode=True)
    
    health = client.health_check()
    
    assert health["ready"] is True
    assert health["live"] is True
    assert health["model_ready"] is True
    assert health["offline_mode"] is True


def test_health_check_live_mode_not_implemented(default_config):
    """Test health check raises NotImplementedError in live mode."""
    client = TritonClient(default_config, offline_mode=False)
    
    with pytest.raises(NotImplementedError) as exc_info:
        client.health_check()
    
    assert "Live mode" in str(exc_info.value)
    assert "offline_mode=True" in str(exc_info.value)


def test_infer_offline_mode(default_config):
    """Test inference returns stub data in offline mode."""
    client = TritonClient(default_config, offline_mode=True)
    
    result = client.infer(
        model_name="object_detection",
        inputs={"input_frames": [[1, 2, 3]]}
    )
    
    assert "outputs" in result
    assert "detections" in result["outputs"]
    assert "scores" in result["outputs"]
    assert result["model_name"] == "object_detection"
    assert result["model_version"] == "1"
    assert result["offline_mode"] is True


def test_infer_with_model_version(default_config):
    """Test inference with specific model version."""
    client = TritonClient(default_config, offline_mode=True)
    
    result = client.infer(
        model_name="test_model",
        inputs={"input": [1, 2, 3]},
        model_version="2"
    )
    
    assert result["model_version"] == "2"


def test_infer_live_mode_not_implemented(default_config):
    """Test inference raises NotImplementedError in live mode."""
    client = TritonClient(default_config, offline_mode=False)
    
    with pytest.raises(NotImplementedError) as exc_info:
        client.infer(
            model_name="test_model",
            inputs={"input": [1, 2, 3]}
        )
    
    assert "Live mode" in str(exc_info.value)


def test_get_model_metadata_offline_mode(default_config):
    """Test model metadata returns stub data in offline mode."""
    client = TritonClient(default_config, offline_mode=True)
    
    metadata = client.get_model_metadata("object_detection")
    
    assert isinstance(metadata, ModelMetadata)
    assert metadata.name == "object_detection"
    assert metadata.version == "1"
    assert metadata.backend == "tensorrt"
    assert "input_frames" in metadata.inputs
    assert "detections" in metadata.outputs
    assert metadata.max_batch_size == 8


def test_get_model_metadata_with_version(default_config):
    """Test model metadata with specific version."""
    client = TritonClient(default_config, offline_mode=True)
    
    metadata = client.get_model_metadata("test_model", model_version="3")
    
    assert metadata.version == "3"


def test_get_model_metadata_live_mode_not_implemented(default_config):
    """Test metadata raises NotImplementedError in live mode."""
    client = TritonClient(default_config, offline_mode=False)
    
    with pytest.raises(NotImplementedError):
        client.get_model_metadata("test_model")


def test_list_models_offline_mode(default_config):
    """Test list models returns stub data in offline mode."""
    client = TritonClient(default_config, offline_mode=True)
    
    models = client.list_models()
    
    assert isinstance(models, list)
    assert len(models) > 0
    assert "object_detection" in models
    assert "audio_transcription" in models
    assert "video_classifier" in models
    assert "image_upscaler" in models


def test_list_models_live_mode_not_implemented(default_config):
    """Test list models raises NotImplementedError in live mode."""
    client = TritonClient(default_config, offline_mode=False)
    
    with pytest.raises(NotImplementedError):
        client.list_models()


def test_config_validation():
    """Test TritonConfig validation and defaults."""
    # Test with minimal config
    config = TritonConfig()
    assert config.endpoint_url == "http://localhost:8000"
    assert config.protocol == "http"
    assert config.timeout_seconds == 30
    assert config.verify_ssl is True
    
    # Test with custom values
    config = TritonConfig(
        endpoint_url="https://nas.local:8000",
        protocol="grpc",
        model_name="custom_model",
        timeout_seconds=60,
        verify_ssl=False
    )
    assert config.endpoint_url == "https://nas.local:8000"
    assert config.protocol == "grpc"
    assert config.model_name == "custom_model"
    assert config.timeout_seconds == 60
    assert config.verify_ssl is False


def test_model_metadata_validation():
    """Test ModelMetadata validation and defaults."""
    # Test with minimal fields
    metadata = ModelMetadata(name="test_model")
    assert metadata.name == "test_model"
    assert metadata.version is None
    assert metadata.backend is None
    assert metadata.inputs == []
    assert metadata.outputs == []
    assert metadata.max_batch_size == 1
    
    # Test with full fields
    metadata = ModelMetadata(
        name="full_model",
        version="2",
        backend="pytorch",
        platform="pytorch_libtorch",
        inputs=["input1", "input2"],
        outputs=["output1"],
        max_batch_size=16
    )
    assert metadata.name == "full_model"
    assert metadata.version == "2"
    assert metadata.backend == "pytorch"
    assert metadata.platform == "pytorch_libtorch"
    assert metadata.inputs == ["input1", "input2"]
    assert metadata.outputs == ["output1"]
    assert metadata.max_batch_size == 16


def test_config_protocol_validation():
    """Test that only valid protocols are accepted."""
    # Valid protocols
    config = TritonConfig(protocol="http")
    assert config.protocol == "http"
    
    config = TritonConfig(protocol="grpc")
    assert config.protocol == "grpc"
    
    # Invalid protocol should raise validation error
    with pytest.raises(Exception):  # Pydantic ValidationError
        TritonConfig(protocol="invalid")


def test_offline_mode_is_default():
    """Test that offline mode is the default behavior."""
    config = TritonConfig()
    
    # Client without explicit offline_mode parameter
    client = TritonClient(config)
    assert client.offline_mode is True
    
    # All methods should work in offline mode
    assert client.health_check()["offline_mode"] is True
    assert client.infer("test", {})["offline_mode"] is True
    assert client.list_models() is not None


def test_client_with_different_configs():
    """Test client works with various config combinations."""
    configs = [
        TritonConfig(),
        TritonConfig(endpoint_url="http://server1:8000"),
        TritonConfig(protocol="grpc", endpoint_url="http://server2:8001"),
        TritonConfig(model_name="default_model", timeout_seconds=120),
    ]
    
    for config in configs:
        client = TritonClient(config, offline_mode=True)
        
        # All operations should work
        health = client.health_check()
        assert health["ready"] is True
        
        result = client.infer("test", {"input": [1, 2, 3]})
        assert "outputs" in result
        
        metadata = client.get_model_metadata("test")
        assert metadata.name == "test"
        
        models = client.list_models()
        assert len(models) > 0
