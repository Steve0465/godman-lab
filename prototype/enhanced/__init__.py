"""Enhanced OCR and thread analysis features."""

from .segmentation import BubbleSegmenter, MessageUIPreset, BubbleBox
from .ocr_backends import (
    OCRBackend, TesseractBackend, GoogleVisionBackend, AWSTextractBackend,
    get_ocr_backend, get_available_backends, OCRResult, OCRComparator
)
from .embeddings import MessageEmbedder, compute_sentiment_scores

__all__ = [
    'BubbleSegmenter', 'MessageUIPreset', 'BubbleBox',
    'OCRBackend', 'TesseractBackend', 'GoogleVisionBackend', 'AWSTextractBackend',
    'get_ocr_backend', 'get_available_backends', 'OCRResult', 'OCRComparator',
    'MessageEmbedder', 'compute_sentiment_scores'
]
