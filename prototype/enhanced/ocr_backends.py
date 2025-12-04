"""
OCR backends module providing a unified interface for multiple OCR services.

Supports:
- Local Tesseract OCR (pytesseract)
- Google Cloud Vision API
- AWS Textract

Example usage:
    from ocr_backends import OCRBackend, get_ocr_backend
    
    # Get available backend
    backend = get_ocr_backend('tesseract')
    text = backend.extract_text('image.png')
    
    # Compare backends
    from ocr_backends import OCRComparator
    comparator = OCRComparator(['tesseract', 'google', 'aws'])
    results = comparator.compare_accuracy('test_images/', 'ground_truth.json')
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from pathlib import Path
import json
import time

import pytesseract
from PIL import Image


@dataclass
class OCRResult:
    """Result from OCR extraction."""
    text: str
    confidence: float
    backend: str
    processing_time: float
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'text': self.text,
            'confidence': self.confidence,
            'backend': self.backend,
            'processing_time': self.processing_time,
            'metadata': self.metadata or {}
        }


class OCRBackend(ABC):
    """Abstract base class for OCR backends."""
    
    @abstractmethod
    def extract_text(self, image_path: str) -> OCRResult:
        """
        Extract text from an image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            OCRResult with extracted text and metadata
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend is available (credentials configured, etc.)."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the backend name."""
        pass


class TesseractBackend(OCRBackend):
    """Local Tesseract OCR backend."""
    
    def __init__(self):
        """Initialize Tesseract backend."""
        self._available = None
    
    @property
    def name(self) -> str:
        return "tesseract"
    
    def is_available(self) -> bool:
        """Check if Tesseract is installed."""
        if self._available is None:
            try:
                pytesseract.get_tesseract_version()
                self._available = True
            except Exception:
                self._available = False
        return self._available
    
    def extract_text(self, image_path: str) -> OCRResult:
        """Extract text using Tesseract."""
        start_time = time.time()
        
        try:
            # Open image
            img = Image.open(image_path)
            
            # Extract text with confidence data
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            
            # Get text
            text = pytesseract.image_to_string(img)
            
            # Calculate average confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                text=text.strip(),
                confidence=avg_confidence / 100.0,  # Normalize to 0-1
                backend=self.name,
                processing_time=processing_time,
                metadata={'word_count': len(data['text'])}
            )
        
        except Exception as e:
            processing_time = time.time() - start_time
            return OCRResult(
                text="",
                confidence=0.0,
                backend=self.name,
                processing_time=processing_time,
                metadata={'error': str(e)}
            )


class GoogleVisionBackend(OCRBackend):
    """Google Cloud Vision API backend."""
    
    def __init__(self):
        """Initialize Google Vision backend."""
        self._available = None
        self._client = None
    
    @property
    def name(self) -> str:
        return "google_vision"
    
    def is_available(self) -> bool:
        """Check if Google Cloud credentials are configured."""
        if self._available is None:
            try:
                # Check for credentials
                creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
                if not creds_path or not os.path.exists(creds_path):
                    self._available = False
                else:
                    # Try to import and initialize client
                    from google.cloud import vision
                    self._client = vision.ImageAnnotatorClient()
                    self._available = True
            except Exception:
                self._available = False
        return self._available
    
    def extract_text(self, image_path: str) -> OCRResult:
        """Extract text using Google Cloud Vision."""
        start_time = time.time()
        
        try:
            from google.cloud import vision
            
            if self._client is None:
                self._client = vision.ImageAnnotatorClient()
            
            # Load image
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            
            # Perform text detection
            response = self._client.text_detection(image=image)
            
            if response.error.message:
                raise Exception(response.error.message)
            
            texts = response.text_annotations
            
            if texts:
                # First annotation contains the full text
                full_text = texts[0].description
                
                # Calculate average confidence from word-level annotations
                if len(texts) > 1:
                    # texts[1:] are individual words
                    confidences = []
                    for text_annotation in texts[1:]:
                        if hasattr(text_annotation, 'confidence'):
                            confidences.append(text_annotation.confidence)
                    
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.95
                else:
                    avg_confidence = 0.95  # Default confidence
                
                processing_time = time.time() - start_time
                
                return OCRResult(
                    text=full_text.strip(),
                    confidence=avg_confidence,
                    backend=self.name,
                    processing_time=processing_time,
                    metadata={'num_annotations': len(texts)}
                )
            else:
                processing_time = time.time() - start_time
                return OCRResult(
                    text="",
                    confidence=0.0,
                    backend=self.name,
                    processing_time=processing_time,
                    metadata={'num_annotations': 0}
                )
        
        except Exception as e:
            processing_time = time.time() - start_time
            return OCRResult(
                text="",
                confidence=0.0,
                backend=self.name,
                processing_time=processing_time,
                metadata={'error': str(e)}
            )


class AWSTextractBackend(OCRBackend):
    """AWS Textract backend."""
    
    def __init__(self):
        """Initialize AWS Textract backend."""
        self._available = None
        self._client = None
    
    @property
    def name(self) -> str:
        return "aws_textract"
    
    def is_available(self) -> bool:
        """Check if AWS credentials are configured."""
        if self._available is None:
            try:
                # Check for AWS credentials
                import boto3
                from botocore.exceptions import NoCredentialsError, PartialCredentialsError
                
                # Try to create client (will fail if no credentials)
                self._client = boto3.client('textract')
                
                # Test if credentials work by calling get_caller_identity
                sts = boto3.client('sts')
                sts.get_caller_identity()
                
                self._available = True
            except (NoCredentialsError, PartialCredentialsError, Exception):
                self._available = False
        return self._available
    
    def extract_text(self, image_path: str) -> OCRResult:
        """Extract text using AWS Textract."""
        start_time = time.time()
        
        try:
            import boto3
            
            if self._client is None:
                self._client = boto3.client('textract')
            
            # Load image
            with open(image_path, 'rb') as image_file:
                image_bytes = image_file.read()
            
            # Call Textract
            response = self._client.detect_document_text(
                Document={'Bytes': image_bytes}
            )
            
            # Extract text from blocks
            text_lines = []
            confidences = []
            
            for block in response['Blocks']:
                if block['BlockType'] == 'LINE':
                    text_lines.append(block['Text'])
                    confidences.append(block['Confidence'] / 100.0)
            
            full_text = '\n'.join(text_lines)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                text=full_text.strip(),
                confidence=avg_confidence,
                backend=self.name,
                processing_time=processing_time,
                metadata={'num_blocks': len(response['Blocks'])}
            )
        
        except Exception as e:
            processing_time = time.time() - start_time
            return OCRResult(
                text="",
                confidence=0.0,
                backend=self.name,
                processing_time=processing_time,
                metadata={'error': str(e)}
            )


def get_ocr_backend(backend_name: str) -> Optional[OCRBackend]:
    """
    Get an OCR backend by name.
    
    Args:
        backend_name: Name of the backend ('tesseract', 'google', 'aws')
        
    Returns:
        OCRBackend instance or None if not available
    """
    backends = {
        'tesseract': TesseractBackend,
        'google': GoogleVisionBackend,
        'google_vision': GoogleVisionBackend,
        'aws': AWSTextractBackend,
        'aws_textract': AWSTextractBackend,
        'textract': AWSTextractBackend,
    }
    
    backend_class = backends.get(backend_name.lower())
    if backend_class is None:
        return None
    
    backend = backend_class()
    if backend.is_available():
        return backend
    
    return None


def get_available_backends() -> List[OCRBackend]:
    """Get all available OCR backends."""
    backend_classes = [TesseractBackend, GoogleVisionBackend, AWSTextractBackend]
    available = []
    
    for backend_class in backend_classes:
        backend = backend_class()
        if backend.is_available():
            available.append(backend)
    
    return available


class OCRComparator:
    """Tool for comparing accuracy of different OCR backends."""
    
    def __init__(self, backend_names: Optional[List[str]] = None):
        """
        Initialize comparator.
        
        Args:
            backend_names: List of backend names to compare. If None, uses all available.
        """
        if backend_names:
            self.backends = [get_ocr_backend(name) for name in backend_names]
            self.backends = [b for b in self.backends if b is not None]
        else:
            self.backends = get_available_backends()
    
    def compare_accuracy(self, test_images_dir: str, ground_truth_file: str, 
                        output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Compare OCR accuracy across backends.
        
        Args:
            test_images_dir: Directory containing test images
            ground_truth_file: JSON file with ground truth text for each image
            output_file: Optional path to save results (CSV or JSON)
            
        Returns:
            Dictionary with comparison results
        """
        # Load ground truth
        with open(ground_truth_file, 'r') as f:
            ground_truth = json.load(f)
        
        results = {
            'backends': [b.name for b in self.backends],
            'images': [],
            'summary': {}
        }
        
        test_dir = Path(test_images_dir)
        
        for image_name, expected_text in ground_truth.items():
            image_path = test_dir / image_name
            
            if not image_path.exists():
                print(f"Warning: Image not found: {image_name}")
                continue
            
            image_results = {
                'image': image_name,
                'ground_truth': expected_text,
                'backends': {}
            }
            
            for backend in self.backends:
                ocr_result = backend.extract_text(str(image_path))
                
                # Calculate accuracy metrics
                word_accuracy = self._calculate_word_accuracy(
                    expected_text, ocr_result.text
                )
                char_accuracy = self._calculate_char_accuracy(
                    expected_text, ocr_result.text
                )
                
                image_results['backends'][backend.name] = {
                    'text': ocr_result.text,
                    'confidence': ocr_result.confidence,
                    'word_accuracy': word_accuracy,
                    'char_accuracy': char_accuracy,
                    'processing_time': ocr_result.processing_time
                }
            
            results['images'].append(image_results)
        
        # Calculate summary statistics
        for backend in self.backends:
            word_accuracies = []
            char_accuracies = []
            processing_times = []
            
            for img_result in results['images']:
                backend_result = img_result['backends'].get(backend.name, {})
                if backend_result:
                    word_accuracies.append(backend_result['word_accuracy'])
                    char_accuracies.append(backend_result['char_accuracy'])
                    processing_times.append(backend_result['processing_time'])
            
            results['summary'][backend.name] = {
                'avg_word_accuracy': sum(word_accuracies) / len(word_accuracies) if word_accuracies else 0,
                'avg_char_accuracy': sum(char_accuracies) / len(char_accuracies) if char_accuracies else 0,
                'avg_processing_time': sum(processing_times) / len(processing_times) if processing_times else 0,
                'num_images': len(word_accuracies)
            }
        
        # Save results
        if output_file:
            self._save_results(results, output_file)
        
        return results
    
    def _calculate_word_accuracy(self, expected: str, actual: str) -> float:
        """Calculate word-level accuracy using simple token matching."""
        expected_words = set(expected.lower().split())
        actual_words = set(actual.lower().split())
        
        if not expected_words:
            return 1.0 if not actual_words else 0.0
        
        correct = len(expected_words & actual_words)
        total = len(expected_words)
        
        return correct / total
    
    def _calculate_char_accuracy(self, expected: str, actual: str) -> float:
        """Calculate character-level accuracy using edit distance."""
        # Simple Levenshtein distance calculation
        if not expected:
            return 1.0 if not actual else 0.0
        
        # Normalize
        expected = expected.lower().strip()
        actual = actual.lower().strip()
        
        if expected == actual:
            return 1.0
        
        # Calculate edit distance
        dist = self._levenshtein_distance(expected, actual)
        max_len = max(len(expected), len(actual))
        
        return 1.0 - (dist / max_len) if max_len > 0 else 0.0
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """
        Calculate Levenshtein distance between two strings.
        
        Note: This is an iterative implementation suitable for moderate string lengths.
        For production use with large texts, consider using optimized libraries like
        'python-Levenshtein' or 'jellyfish' for better performance.
        """
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _save_results(self, results: dict, output_file: str) -> None:
        """Save results to file (JSON or CSV)."""
        output_path = Path(output_file)
        
        if output_path.suffix.lower() == '.json':
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
        elif output_path.suffix.lower() == '.csv':
            import csv
            
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow(['Backend', 'Avg Word Accuracy', 'Avg Char Accuracy', 
                               'Avg Processing Time', 'Num Images'])
                
                # Write summary data
                for backend_name, stats in results['summary'].items():
                    writer.writerow([
                        backend_name,
                        f"{stats['avg_word_accuracy']:.3f}",
                        f"{stats['avg_char_accuracy']:.3f}",
                        f"{stats['avg_processing_time']:.3f}",
                        stats['num_images']
                    ])
        else:
            # Default to JSON
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)


def main():
    """CLI interface for OCR backend comparison."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Compare OCR backend accuracy')
    parser.add_argument('--test-dir', required=True, help='Directory with test images')
    parser.add_argument('--ground-truth', required=True, help='JSON file with ground truth')
    parser.add_argument('--output', required=True, help='Output file for results (JSON or CSV)')
    parser.add_argument('--backends', nargs='+', help='Backends to test (default: all available)')
    
    args = parser.parse_args()
    
    comparator = OCRComparator(backend_names=args.backends)
    
    if not comparator.backends:
        print("Error: No OCR backends available")
        print("Install Tesseract or configure cloud credentials")
        return
    
    print(f"Testing backends: {[b.name for b in comparator.backends]}")
    
    results = comparator.compare_accuracy(
        args.test_dir,
        args.ground_truth,
        args.output
    )
    
    print("\nResults Summary:")
    print("-" * 80)
    for backend_name, stats in results['summary'].items():
        print(f"\n{backend_name}:")
        print(f"  Word Accuracy: {stats['avg_word_accuracy']:.2%}")
        print(f"  Char Accuracy: {stats['avg_char_accuracy']:.2%}")
        print(f"  Avg Time: {stats['avg_processing_time']:.3f}s")
    
    print(f"\nDetailed results saved to: {args.output}")


if __name__ == '__main__':
    main()
