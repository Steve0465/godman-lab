"""
Unit tests for OCR backends module.
"""

import pytest
from pathlib import Path
import sys

# Add prototype to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from prototype.enhanced.ocr_backends import (
    get_ocr_backend,
    get_available_backends,
    TesseractBackend,
    GoogleVisionBackend,
    AWSTextractBackend,
    OCRResult,
    calculate_accuracy
)


def test_get_available_backends():
    """Test getting list of available backends."""
    backends = get_available_backends()
    
    assert isinstance(backends, list)
    # At minimum, we should have some backends available in CI
    # (may be empty if no OCR installed)


def test_tesseract_backend_initialization():
    """Test TesseractBackend initialization."""
    backend = TesseractBackend()
    
    assert backend.get_name() == 'tesseract'
    # is_available may be False if tesseract not installed


def test_google_vision_backend_initialization():
    """Test GoogleVisionBackend initialization."""
    backend = GoogleVisionBackend()
    
    assert backend.get_name() == 'google_vision'
    # is_available will be False without credentials


def test_aws_textract_backend_initialization():
    """Test AWSTextractBackend initialization."""
    backend = AWSTextractBackend()
    
    assert backend.get_name() == 'aws_textract'
    # is_available will be False without credentials


def test_get_ocr_backend_invalid():
    """Test getting invalid backend raises error."""
    with pytest.raises(ValueError):
        get_ocr_backend('invalid_backend')


def test_ocr_result_dataclass():
    """Test OCRResult dataclass."""
    result = OCRResult(
        text="Hello World",
        confidence=0.95,
        word_count=2,
        processing_time=1.5,
        backend='tesseract'
    )
    
    assert result.text == "Hello World"
    assert result.confidence == 0.95
    assert result.word_count == 2
    assert result.processing_time == 1.5
    assert result.backend == 'tesseract'
    
    # Test to_dict
    result_dict = result.to_dict()
    assert result_dict['text'] == "Hello World"
    assert result_dict['backend'] == 'tesseract'


def test_calculate_accuracy():
    """Test accuracy calculation."""
    predicted = "hello world this is a test"
    ground_truth = "hello world this is a test"
    
    accuracy = calculate_accuracy(predicted, ground_truth)
    
    assert accuracy['precision'] == 1.0
    assert accuracy['recall'] == 1.0
    assert accuracy['f1'] == 1.0
    assert accuracy['word_error_rate'] == 0.0


def test_calculate_accuracy_partial_match():
    """Test accuracy with partial match."""
    predicted = "hello world"
    ground_truth = "hello world test"
    
    accuracy = calculate_accuracy(predicted, ground_truth)
    
    # Should have partial recall
    assert 0 < accuracy['recall'] < 1
    assert accuracy['precision'] == 1.0  # All predicted words are correct


def test_calculate_accuracy_no_match():
    """Test accuracy with no match."""
    predicted = "foo bar"
    ground_truth = "hello world"
    
    accuracy = calculate_accuracy(predicted, ground_truth)
    
    assert accuracy['precision'] == 0.0
    assert accuracy['recall'] == 0.0
    assert accuracy['f1'] == 0.0
    assert accuracy['word_error_rate'] == 1.0


def test_calculate_accuracy_empty_truth():
    """Test accuracy with empty ground truth."""
    predicted = "hello world"
    ground_truth = ""
    
    accuracy = calculate_accuracy(predicted, ground_truth)
    
    assert accuracy['precision'] == 0.0
    assert accuracy['recall'] == 0.0
    assert accuracy['f1'] == 0.0


def test_tesseract_backend_extract_text_missing_file():
    """Test OCR with missing file raises appropriate error."""
    backend = TesseractBackend()
    
    if not backend.is_available():
        pytest.skip("Tesseract not available")
    
    # Should handle gracefully and return empty result
    result = backend.extract_text("nonexistent.png")
    
    assert result.text == ""
    assert result.confidence == 0.0


@pytest.mark.skipif(
    not TesseractBackend().is_available(),
    reason="Tesseract not installed"
)
def test_tesseract_backend_extract_text():
    """Test Tesseract OCR on test image."""
    backend = TesseractBackend()
    
    examples_dir = Path(__file__).parent.parent.parent / "examples"
    test_image = examples_dir / "test_image1.png"
    
    if not test_image.exists():
        pytest.skip("Test image not found")
    
    result = backend.extract_text(str(test_image))
    
    assert isinstance(result, OCRResult)
    assert result.backend == 'tesseract'
    assert result.processing_time >= 0
    # Text may or may not be extracted depending on image quality
