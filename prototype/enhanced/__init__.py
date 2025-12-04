"""Enhanced OCR and thread analysis features."""

# Import modules individually to avoid dependency issues during testing
try:
    from .segmentation import BubbleSegmenter, MessageUIPreset, BubbleBox
except ImportError:
    pass

try:
    from .ocr_backends import (
        OCRBackend, TesseractBackend, GoogleVisionBackend, AWSTextractBackend,
        get_ocr_backend, get_available_backends, OCRResult, OCRComparator
    )
except ImportError:
    pass

try:
    from .embeddings import MessageEmbedder, compute_sentiment_scores
except ImportError:
    pass

__all__ = [
    'BubbleSegmenter', 'MessageUIPreset', 'BubbleBox',
    'OCRBackend', 'TesseractBackend', 'GoogleVisionBackend', 'AWSTextractBackend',
    'get_ocr_backend', 'get_available_backends', 'OCRResult', 'OCRComparator',
    'MessageEmbedder', 'compute_sentiment_scores'
]
