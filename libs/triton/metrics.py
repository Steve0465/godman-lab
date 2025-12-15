"""Triton metrics parsing and formatting utilities.

Provides functions to parse and format Triton server metrics including:
- GPU utilization
- Inference throughput
- Latency percentiles
"""
import json
import re
from typing import Any


def parse_metrics(raw_text: str) -> dict[str, Any]:
    """Parse Triton metrics from text or JSON format.
    
    Supports both Prometheus-style text format and JSON metrics.
    
    Args:
        raw_text: Raw metrics string (Prometheus text or JSON)
    
    Returns:
        dict: Parsed metrics with standardized keys:
            - gpu_utilization: GPU usage percentage (0-100)
            - inference_count: Total number of inferences
            - inference_success: Number of successful inferences
            - inference_failure: Number of failed inferences
            - latency_p50: 50th percentile latency (microseconds)
            - latency_p95: 95th percentile latency (microseconds)
            - latency_p99: 99th percentile latency (microseconds)
            - throughput_rps: Requests per second
    
    Example:
        ```python
        # Prometheus format
        metrics_text = '''
        nv_gpu_utilization 85.5
        nv_inference_request_success 1250
        nv_inference_latency_us{quantile="0.5"} 1500
        '''
        parsed = parse_metrics(metrics_text)
        print(f"GPU: {parsed['gpu_utilization']}%")
        
        # JSON format
        metrics_json = '{"gpu_utilization": 85.5, "inference_count": 1250}'
        parsed = parse_metrics(metrics_json)
        ```
    """
    # Try parsing as JSON first
    try:
        data = json.loads(raw_text)
        return _normalize_metrics(data)
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Parse as Prometheus-style text format
    metrics = {}
    
    # GPU utilization
    gpu_match = re.search(r'nv_gpu_utilization\s+([\d.]+)', raw_text)
    if gpu_match:
        metrics['gpu_utilization'] = float(gpu_match.group(1))
    
    # Inference counts
    success_match = re.search(r'nv_inference_request_success\s+([\d.]+)', raw_text)
    if success_match:
        metrics['inference_success'] = int(float(success_match.group(1)))
    
    failure_match = re.search(r'nv_inference_request_failure\s+([\d.]+)', raw_text)
    if failure_match:
        metrics['inference_failure'] = int(float(failure_match.group(1)))
    
    count_match = re.search(r'nv_inference_count\s+([\d.]+)', raw_text)
    if count_match:
        metrics['inference_count'] = int(float(count_match.group(1)))
    
    # Latency percentiles (microseconds)
    latency_p50 = re.search(r'nv_inference_latency_us\{quantile="0\.5[0]*"\}\s+([\d.]+)', raw_text)
    if latency_p50:
        metrics['latency_p50'] = float(latency_p50.group(1))
    
    latency_p95 = re.search(r'nv_inference_latency_us\{quantile="0\.95"\}\s+([\d.]+)', raw_text)
    if latency_p95:
        metrics['latency_p95'] = float(latency_p95.group(1))
    
    latency_p99 = re.search(r'nv_inference_latency_us\{quantile="0\.99"\}\s+([\d.]+)', raw_text)
    if latency_p99:
        metrics['latency_p99'] = float(latency_p99.group(1))
    
    # Throughput (requests per second)
    throughput_match = re.search(r'nv_inference_request_success_rate\s+([\d.]+)', raw_text)
    if throughput_match:
        metrics['throughput_rps'] = float(throughput_match.group(1))
    
    return metrics


def _normalize_metrics(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize metrics from various formats to standard keys.
    
    Args:
        data: Raw metrics dictionary
    
    Returns:
        dict: Normalized metrics with standard keys
    """
    # Handle different naming conventions
    normalized = {}
    
    # GPU utilization
    for key in ['gpu_utilization', 'gpu_util', 'nv_gpu_utilization']:
        if key in data:
            normalized['gpu_utilization'] = float(data[key])
            break
    
    # Inference counts
    for key in ['inference_count', 'total_inferences', 'nv_inference_count']:
        if key in data:
            normalized['inference_count'] = int(data[key])
            break
    
    for key in ['inference_success', 'successful_inferences', 'nv_inference_request_success']:
        if key in data:
            normalized['inference_success'] = int(data[key])
            break
    
    for key in ['inference_failure', 'failed_inferences', 'nv_inference_request_failure']:
        if key in data:
            normalized['inference_failure'] = int(data[key])
            break
    
    # Latency
    for key in ['latency_p50', 'p50_latency', 'median_latency']:
        if key in data:
            normalized['latency_p50'] = float(data[key])
            break
    
    for key in ['latency_p95', 'p95_latency']:
        if key in data:
            normalized['latency_p95'] = float(data[key])
            break
    
    for key in ['latency_p99', 'p99_latency']:
        if key in data:
            normalized['latency_p99'] = float(data[key])
            break
    
    # Throughput
    for key in ['throughput_rps', 'requests_per_second', 'rps', 'nv_inference_request_success_rate']:
        if key in data:
            normalized['throughput_rps'] = float(data[key])
            break
    
    return normalized


def format_gpu_utilization(metrics: dict[str, Any]) -> str:
    """Format GPU utilization metrics for display.
    
    Args:
        metrics: Parsed metrics dictionary
    
    Returns:
        str: Formatted GPU utilization string
    
    Example:
        ```python
        metrics = {"gpu_utilization": 85.5}
        output = format_gpu_utilization(metrics)
        # Output: "GPU Utilization: 85.5%"
        ```
    """
    gpu_util = metrics.get('gpu_utilization')
    
    if gpu_util is None:
        return "GPU Utilization: N/A"
    
    # Color coding based on utilization
    if gpu_util < 50:
        status = "Low"
    elif gpu_util < 80:
        status = "Moderate"
    else:
        status = "High"
    
    return f"GPU Utilization: {gpu_util:.1f}% ({status})"


def format_throughput_latency(metrics: dict[str, Any]) -> str:
    """Format throughput and latency metrics for display.
    
    Args:
        metrics: Parsed metrics dictionary
    
    Returns:
        str: Formatted throughput and latency statistics
    
    Example:
        ```python
        metrics = {
            "throughput_rps": 45.2,
            "latency_p50": 1500,
            "latency_p95": 2800,
            "latency_p99": 3500
        }
        output = format_throughput_latency(metrics)
        ```
    """
    lines = []
    
    # Throughput
    throughput = metrics.get('throughput_rps')
    if throughput is not None:
        lines.append(f"Throughput: {throughput:.2f} requests/sec")
    else:
        lines.append("Throughput: N/A")
    
    # Latency percentiles (convert from microseconds to milliseconds)
    latency_p50 = metrics.get('latency_p50')
    latency_p95 = metrics.get('latency_p95')
    latency_p99 = metrics.get('latency_p99')
    
    if latency_p50 is not None or latency_p95 is not None or latency_p99 is not None:
        lines.append("\nLatency:")
        if latency_p50 is not None:
            lines.append(f"  p50: {latency_p50/1000:.2f} ms")
        if latency_p95 is not None:
            lines.append(f"  p95: {latency_p95/1000:.2f} ms")
        if latency_p99 is not None:
            lines.append(f"  p99: {latency_p99/1000:.2f} ms")
    else:
        lines.append("\nLatency: N/A")
    
    # Inference counts
    success = metrics.get('inference_success')
    failure = metrics.get('inference_failure')
    total = metrics.get('inference_count')
    
    if success is not None or failure is not None or total is not None:
        lines.append("\nInference Counts:")
        if total is not None:
            lines.append(f"  Total: {total:,}")
        if success is not None:
            lines.append(f"  Success: {success:,}")
        if failure is not None:
            lines.append(f"  Failure: {failure:,}")
        
        # Success rate
        if success is not None and total is not None and total > 0:
            success_rate = (success / total) * 100
            lines.append(f"  Success Rate: {success_rate:.2f}%")
    
    return "\n".join(lines)
