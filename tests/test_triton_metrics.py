"""Tests for Triton metrics parsing and formatting."""
import pytest
from libs.triton.metrics import (
    parse_metrics,
    format_gpu_utilization,
    format_throughput_latency,
)


@pytest.fixture
def sample_prometheus_metrics():
    """Sample Prometheus-style metrics."""
    return """
# HELP nv_gpu_utilization GPU utilization rate
# TYPE nv_gpu_utilization gauge
nv_gpu_utilization 85.5

# HELP nv_inference_count Total inference requests
# TYPE nv_inference_count counter
nv_inference_count 1250

# HELP nv_inference_request_success Successful inference requests
# TYPE nv_inference_request_success counter
nv_inference_request_success 1200

# HELP nv_inference_request_failure Failed inference requests
# TYPE nv_inference_request_failure counter
nv_inference_request_failure 50

# HELP nv_inference_latency_us Inference latency in microseconds
# TYPE nv_inference_latency_us summary
nv_inference_latency_us{quantile="0.5"} 1500
nv_inference_latency_us{quantile="0.95"} 2800
nv_inference_latency_us{quantile="0.99"} 3500

# HELP nv_inference_request_success_rate Request success rate
# TYPE nv_inference_request_success_rate gauge
nv_inference_request_success_rate 45.2
"""


@pytest.fixture
def sample_json_metrics():
    """Sample JSON-format metrics."""
    return """{
    "gpu_utilization": 85.5,
    "inference_count": 1250,
    "inference_success": 1200,
    "inference_failure": 50,
    "latency_p50": 1500,
    "latency_p95": 2800,
    "latency_p99": 3500,
    "throughput_rps": 45.2
}"""


def test_parse_metrics_from_text(sample_prometheus_metrics):
    """Test parsing Prometheus-style text metrics."""
    parsed = parse_metrics(sample_prometheus_metrics)
    
    assert parsed['gpu_utilization'] == 85.5
    assert parsed['inference_count'] == 1250
    assert parsed['inference_success'] == 1200
    assert parsed['inference_failure'] == 50
    assert parsed['latency_p50'] == 1500
    assert parsed['latency_p95'] == 2800
    assert parsed['latency_p99'] == 3500
    assert parsed['throughput_rps'] == 45.2


def test_parse_metrics_from_json(sample_json_metrics):
    """Test parsing JSON-format metrics."""
    parsed = parse_metrics(sample_json_metrics)
    
    assert parsed['gpu_utilization'] == 85.5
    assert parsed['inference_count'] == 1250
    assert parsed['inference_success'] == 1200
    assert parsed['inference_failure'] == 50
    assert parsed['latency_p50'] == 1500
    assert parsed['latency_p95'] == 2800
    assert parsed['latency_p99'] == 3500
    assert parsed['throughput_rps'] == 45.2


def test_parse_metrics_partial():
    """Test parsing metrics with only some fields present."""
    partial_metrics = """
nv_gpu_utilization 65.0
nv_inference_count 500
"""
    parsed = parse_metrics(partial_metrics)
    
    assert parsed['gpu_utilization'] == 65.0
    assert parsed['inference_count'] == 500
    assert 'latency_p50' not in parsed
    assert 'throughput_rps' not in parsed


def test_format_gpu_utilization():
    """Test GPU utilization formatting."""
    # Low utilization
    metrics = {"gpu_utilization": 35.5}
    output = format_gpu_utilization(metrics)
    assert "35.5%" in output
    assert "Low" in output
    
    # Moderate utilization
    metrics = {"gpu_utilization": 65.0}
    output = format_gpu_utilization(metrics)
    assert "65.0%" in output
    assert "Moderate" in output
    
    # High utilization
    metrics = {"gpu_utilization": 88.3}
    output = format_gpu_utilization(metrics)
    assert "88.3%" in output
    assert "High" in output
    
    # Missing data
    metrics = {}
    output = format_gpu_utilization(metrics)
    assert "N/A" in output


def test_format_throughput_latency():
    """Test throughput and latency formatting."""
    metrics = {
        "throughput_rps": 45.2,
        "latency_p50": 1500,
        "latency_p95": 2800,
        "latency_p99": 3500,
        "inference_count": 1250,
        "inference_success": 1200,
        "inference_failure": 50,
    }
    
    output = format_throughput_latency(metrics)
    
    # Check throughput
    assert "45.20 requests/sec" in output
    
    # Check latency (converted from microseconds to milliseconds)
    assert "1.50 ms" in output  # p50
    assert "2.80 ms" in output  # p95
    assert "3.50 ms" in output  # p99
    
    # Check inference counts
    assert "1,250" in output
    assert "1,200" in output
    assert "50" in output
    
    # Check success rate
    assert "96.00%" in output


def test_format_throughput_latency_minimal():
    """Test formatting with minimal metrics."""
    metrics = {"throughput_rps": 30.0}
    
    output = format_throughput_latency(metrics)
    
    assert "30.00 requests/sec" in output
    assert "N/A" in output  # For missing latency


def test_format_throughput_latency_missing():
    """Test formatting with no metrics."""
    metrics = {}
    
    output = format_throughput_latency(metrics)
    
    assert "N/A" in output


def test_invalid_metrics_handling():
    """Test handling of malformed input."""
    # Empty string
    parsed = parse_metrics("")
    assert parsed == {}
    
    # Invalid JSON
    parsed = parse_metrics("{invalid json}")
    assert parsed == {}
    
    # Random text
    parsed = parse_metrics("This is not metrics data")
    assert parsed == {}


def test_parse_metrics_with_alternative_names():
    """Test parsing metrics with alternative naming conventions."""
    json_with_alt_names = """{
        "gpu_util": 75.0,
        "total_inferences": 500,
        "successful_inferences": 490,
        "failed_inferences": 10,
        "median_latency": 1200,
        "p95_latency": 2400,
        "p99_latency": 3000,
        "rps": 40.0
    }"""
    
    parsed = parse_metrics(json_with_alt_names)
    
    # Should normalize to standard keys
    assert parsed['gpu_utilization'] == 75.0
    assert parsed['inference_count'] == 500
    assert parsed['inference_success'] == 490
    assert parsed['inference_failure'] == 10
    assert parsed['latency_p50'] == 1200
    assert parsed['latency_p95'] == 2400
    assert parsed['latency_p99'] == 3000
    assert parsed['throughput_rps'] == 40.0


def test_format_success_rate_calculation():
    """Test success rate calculation in throughput formatting."""
    # 100% success rate
    metrics = {
        "inference_count": 1000,
        "inference_success": 1000,
        "inference_failure": 0,
    }
    output = format_throughput_latency(metrics)
    assert "100.00%" in output
    
    # 95% success rate
    metrics = {
        "inference_count": 1000,
        "inference_success": 950,
        "inference_failure": 50,
    }
    output = format_throughput_latency(metrics)
    assert "95.00%" in output
    
    # Handle division by zero
    metrics = {
        "inference_count": 0,
        "inference_success": 0,
    }
    output = format_throughput_latency(metrics)
    # Should not crash, just skip success rate


def test_parse_metrics_float_vs_int():
    """Test parsing handles both float and int values correctly."""
    metrics_text = """
nv_gpu_utilization 85.5
nv_inference_count 1250.0
nv_inference_request_success 1200.5
"""
    parsed = parse_metrics(metrics_text)
    
    assert parsed['gpu_utilization'] == 85.5
    assert parsed['inference_count'] == 1250  # Should be converted to int
    assert parsed['inference_success'] == 1200  # Should be converted to int
