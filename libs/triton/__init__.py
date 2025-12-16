"""Triton Inference Server integration for Shield Pro Media Box.

This package provides a modular interface for Triton Inference Server
with support for offline mode (no live server required).
"""
from libs.triton.models import TritonConfig, ModelMetadata
from libs.triton.client import TritonClient
from libs.triton.metrics import (
    parse_metrics,
    format_gpu_utilization,
    format_throughput_latency,
)

__version__ = "0.1.0"

__all__ = [
    "TritonConfig",
    "ModelMetadata",
    "TritonClient",
    "parse_metrics",
    "format_gpu_utilization",
    "format_throughput_latency",
]
