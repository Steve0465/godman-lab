"""
Unit tests for OCR backends module.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ocr_backends import (
    OCRBackend, TesseractBackend, GoogleVisionBackend, AWSTextractBackend,
    get_ocr_backend, get_available_backends, OCRResult, OCRComparator
)


class TestOCRBackends:
    """Tests for OCR backend classes."""
    
    def test_tesseract_backend(self):
        """Test Tesseract backend."""
        backend = TesseractBackend()
        assert backend.name == "tesseract"
        
        # is_available should return bool
        available = backend.is_available()
        assert isinstance(available, bool)
    
    def test_google_vision_backend(self):
        """Test Google Vision backend."""
        backend = GoogleVisionBackend()
        assert backend.name == "google_vision"
        
        # Should return False if credentials not configured
        available = backend.is_available()
        assert isinstance(available, bool)
    
    def test_aws_textract_backend(self):
        """Test AWS Textract backend."""
        backend = AWSTextractBackend()
        assert backend.name == "aws_textract"
        
        # Should return False if credentials not configured
        available = backend.is_available()
        assert isinstance(available, bool)
    
    def test_get_ocr_backend(self):
        """Test get_ocr_backend function."""
        # Test with different names
        backend = get_ocr_backend('tesseract')
        if backend:
            assert isinstance(backend, TesseractBackend)
        
        # Test with invalid name
        backend = get_ocr_backend('invalid_backend')
        assert backend is None
    
    def test_get_available_backends(self):
        """Test get_available_backends function."""
        backends = get_available_backends()
        
        # Should return a list
        assert isinstance(backends, list)
        
        # All should be OCRBackend instances
        for backend in backends:
            assert isinstance(backend, OCRBackend)
            assert backend.is_available()
    
    def test_ocr_result(self):
        """Test OCRResult dataclass."""
        result = OCRResult(
            text="Hello World",
            confidence=0.95,
            backend="tesseract",
            processing_time=1.5,
            metadata={'key': 'value'}
        )
        
        assert result.text == "Hello World"
        assert result.confidence == 0.95
        assert result.backend == "tesseract"
        
        # Test to_dict
        data = result.to_dict()
        assert data['text'] == "Hello World"
        assert data['confidence'] == 0.95


class TestOCRComparator:
    """Tests for OCRComparator class."""
    
    def test_initialization(self):
        """Test comparator initialization."""
        comparator = OCRComparator()
        assert isinstance(comparator.backends, list)
    
    def test_levenshtein_distance(self):
        """Test Levenshtein distance calculation."""
        comparator = OCRComparator()
        
        # Identical strings
        dist = comparator._levenshtein_distance("hello", "hello")
        assert dist == 0
        
        # Completely different
        dist = comparator._levenshtein_distance("abc", "xyz")
        assert dist == 3
        
        # One insertion
        dist = comparator._levenshtein_distance("hello", "hellow")
        assert dist == 1
    
    def test_calculate_word_accuracy(self):
        """Test word accuracy calculation."""
        comparator = OCRComparator()
        
        # Perfect match
        acc = comparator._calculate_word_accuracy("hello world", "hello world")
        assert acc == 1.0
        
        # Partial match
        acc = comparator._calculate_word_accuracy("hello world", "hello there")
        assert 0 < acc < 1
        
        # No match
        acc = comparator._calculate_word_accuracy("hello world", "foo bar")
        assert acc == 0.0
    
    def test_calculate_char_accuracy(self):
        """Test character accuracy calculation."""
        comparator = OCRComparator()
        
        # Perfect match
        acc = comparator._calculate_char_accuracy("hello", "hello")
        assert acc == 1.0
        
        # Partial match
        acc = comparator._calculate_char_accuracy("hello", "helo")
        assert 0 < acc < 1
        
        # Empty strings
        acc = comparator._calculate_char_accuracy("", "")
        assert acc == 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
