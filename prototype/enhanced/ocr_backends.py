"""
OCR backends module providing unified interface for multiple OCR services.

Supports:
- Local Tesseract (pytesseract)
- Google Cloud Vision
- AWS Textract

All cloud backends gracefully skip if credentials are not available.

Example usage:
    from prototype.enhanced.ocr_backends import get_ocr_backend, OCRBackend
    
    # Auto-detect available backend
    backend = get_ocr_backend('tesseract')
    text = backend.extract_text('image.png')
    
    # Compare backends
    from prototype.enhanced.ocr_backends import compare_backends
    results = compare_backends('images/', 'labels.json')
"""

import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Tuple
from pathlib import Path
import json
import time
from dataclasses import dataclass, asdict

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    from google.cloud import vision
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False

try:
    import boto3
    AWS_TEXTRACT_AVAILABLE = True
except ImportError:
    AWS_TEXTRACT_AVAILABLE = False


@dataclass
class OCRResult:
    """Result from OCR extraction."""
    text: str
    confidence: Optional[float] = None
    word_count: int = 0
    processing_time: float = 0.0
    backend: str = ""
    
    def to_dict(self):
        return asdict(self)


class OCRBackend(ABC):
    """Abstract base class for OCR backends."""
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend is available/configured."""
        pass
    
    @abstractmethod
    def extract_text(self, image_path: str) -> OCRResult:
        """
        Extract text from an image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            OCRResult with extracted text and metadata
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get the backend name."""
        pass


class TesseractBackend(OCRBackend):
    """Local Tesseract OCR backend."""
    
    def is_available(self) -> bool:
        """Check if Tesseract is available."""
        if not TESSERACT_AVAILABLE:
            return False
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False
    
    def extract_text(self, image_path: str) -> OCRResult:
        """Extract text using Tesseract."""
        if not self.is_available():
            raise RuntimeError("Tesseract is not available")
        
        start_time = time.time()
        
        try:
            img = Image.open(image_path)
            
            # Get detailed data for confidence scores
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            
            # Extract text
            text = pytesseract.image_to_string(img)
            
            # Calculate average confidence (filter out -1 values)
            confidences = [float(c) for c in data['conf'] if int(c) != -1]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Normalize to 0-1 range (Tesseract gives 0-100)
            avg_confidence = avg_confidence / 100.0
            
            # Count words
            word_count = len([w for w in data['text'] if w.strip()])
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                text=text.strip(),
                confidence=avg_confidence,
                word_count=word_count,
                processing_time=processing_time,
                backend='tesseract'
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return OCRResult(
                text="",
                confidence=0.0,
                word_count=0,
                processing_time=processing_time,
                backend='tesseract'
            )
    
    def get_name(self) -> str:
        return "tesseract"


class GoogleVisionBackend(OCRBackend):
    """Google Cloud Vision OCR backend."""
    
    def __init__(self):
        self.client = None
        if self.is_available():
            self.client = vision.ImageAnnotatorClient()
    
    def is_available(self) -> bool:
        """Check if Google Cloud Vision credentials are available."""
        if not GOOGLE_VISION_AVAILABLE:
            return False
        
        # Check for credentials
        if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            return False
        
        return True
    
    def extract_text(self, image_path: str) -> OCRResult:
        """Extract text using Google Cloud Vision."""
        if not self.is_available():
            raise RuntimeError("Google Cloud Vision is not available or not configured")
        
        start_time = time.time()
        
        try:
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            response = self.client.text_detection(image=image)
            
            if response.error.message:
                raise Exception(response.error.message)
            
            texts = response.text_annotations
            
            if texts:
                full_text = texts[0].description
                
                # Extract confidence (if available)
                confidences = []
                word_count = 0
                
                # Get per-word details
                for text in texts[1:]:  # Skip first which is full text
                    word_count += 1
                    # Google Vision doesn't provide per-word confidence in text_detection
                    # but we can use a default high confidence
                    confidences.append(0.95)
                
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.95
            else:
                full_text = ""
                avg_confidence = 0.0
                word_count = 0
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                text=full_text.strip(),
                confidence=avg_confidence,
                word_count=word_count,
                processing_time=processing_time,
                backend='google_vision'
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            print(f"Google Vision error: {e}")
            return OCRResult(
                text="",
                confidence=0.0,
                word_count=0,
                processing_time=processing_time,
                backend='google_vision'
            )
    
    def get_name(self) -> str:
        return "google_vision"


class AWSTextractBackend(OCRBackend):
    """AWS Textract OCR backend."""
    
    def __init__(self):
        self.client = None
        if self.is_available():
            self.client = boto3.client('textract')
    
    def is_available(self) -> bool:
        """Check if AWS credentials are available."""
        if not AWS_TEXTRACT_AVAILABLE:
            return False
        
        # Check for AWS credentials (boto3 will auto-detect from env or config)
        try:
            session = boto3.Session()
            credentials = session.get_credentials()
            return credentials is not None
        except Exception:
            return False
    
    def extract_text(self, image_path: str) -> OCRResult:
        """Extract text using AWS Textract."""
        if not self.is_available():
            raise RuntimeError("AWS Textract is not available or not configured")
        
        start_time = time.time()
        
        try:
            with open(image_path, 'rb') as image_file:
                image_bytes = image_file.read()
            
            response = self.client.detect_document_text(
                Document={'Bytes': image_bytes}
            )
            
            # Extract text and confidence
            lines = []
            confidences = []
            word_count = 0
            
            for block in response['Blocks']:
                if block['BlockType'] == 'LINE':
                    lines.append(block['Text'])
                    confidences.append(block['Confidence'] / 100.0)  # Normalize to 0-1
                elif block['BlockType'] == 'WORD':
                    word_count += 1
            
            full_text = '\n'.join(lines)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                text=full_text.strip(),
                confidence=avg_confidence,
                word_count=word_count,
                processing_time=processing_time,
                backend='aws_textract'
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            print(f"AWS Textract error: {e}")
            return OCRResult(
                text="",
                confidence=0.0,
                word_count=0,
                processing_time=processing_time,
                backend='aws_textract'
            )
    
    def get_name(self) -> str:
        return "aws_textract"


def get_ocr_backend(backend_name: str) -> OCRBackend:
    """
    Get an OCR backend by name.
    
    Args:
        backend_name: Name of backend ('tesseract', 'google_vision', 'aws_textract')
        
    Returns:
        OCRBackend instance
        
    Raises:
        ValueError: If backend name is unknown or not available
    """
    backends = {
        'tesseract': TesseractBackend,
        'google_vision': GoogleVisionBackend,
        'aws_textract': AWSTextractBackend,
    }
    
    if backend_name not in backends:
        raise ValueError(f"Unknown backend: {backend_name}. Available: {list(backends.keys())}")
    
    backend = backends[backend_name]()
    
    if not backend.is_available():
        raise ValueError(f"Backend '{backend_name}' is not available. Check dependencies and credentials.")
    
    return backend


def get_available_backends() -> List[str]:
    """Get list of available OCR backends."""
    available = []
    
    for name in ['tesseract', 'google_vision', 'aws_textract']:
        try:
            backend = get_ocr_backend(name)
            if backend.is_available():
                available.append(name)
        except Exception:
            pass
    
    return available


def calculate_accuracy(predicted: str, ground_truth: str) -> Dict[str, float]:
    """
    Calculate word-level accuracy metrics.
    
    Args:
        predicted: OCR output text
        ground_truth: Ground truth text
        
    Returns:
        Dictionary with accuracy metrics
    """
    pred_words = set(predicted.lower().split())
    truth_words = set(ground_truth.lower().split())
    
    if not truth_words:
        return {
            'precision': 0.0,
            'recall': 0.0,
            'f1': 0.0,
            'word_error_rate': 1.0
        }
    
    correct = pred_words & truth_words
    precision = len(correct) / len(pred_words) if pred_words else 0.0
    recall = len(correct) / len(truth_words) if truth_words else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    # Simple word error rate (not edit distance based, but approximation)
    wer = 1.0 - recall
    
    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'word_error_rate': wer
    }


def compare_backends(images_folder: str, labels_file: str, output_file: str = 'comparison.json') -> Dict:
    """
    Compare OCR backends on a set of labeled images.
    
    Args:
        images_folder: Path to folder with test images
        labels_file: JSON file with ground truth labels
        output_file: Output file for comparison results
        
    Returns:
        Dictionary with comparison results
    """
    images_path = Path(images_folder)
    
    # Load ground truth labels
    with open(labels_file, 'r') as f:
        labels = json.load(f)
    
    # Get available backends
    available = get_available_backends()
    
    if not available:
        print("No OCR backends available!")
        return {}
    
    print(f"Available backends: {', '.join(available)}")
    
    results = {
        'backends': {},
        'images': [],
        'summary': {}
    }
    
    # Initialize backend results
    for backend_name in available:
        results['backends'][backend_name] = {
            'total_images': 0,
            'successful': 0,
            'avg_confidence': 0.0,
            'avg_processing_time': 0.0,
            'avg_precision': 0.0,
            'avg_recall': 0.0,
            'avg_f1': 0.0,
            'avg_wer': 0.0
        }
    
    # Process each labeled image
    for label_entry in labels:
        image_name = label_entry['image']
        ground_truth = label_entry['text']
        
        image_path = images_path / image_name
        if not image_path.exists():
            print(f"Warning: Image {image_name} not found, skipping")
            continue
        
        print(f"\nProcessing {image_name}...")
        
        image_results = {
            'image': image_name,
            'ground_truth': ground_truth,
            'backends': {}
        }
        
        # Run each backend
        for backend_name in available:
            try:
                backend = get_ocr_backend(backend_name)
                ocr_result = backend.extract_text(str(image_path))
                
                # Calculate accuracy
                accuracy = calculate_accuracy(ocr_result.text, ground_truth)
                
                image_results['backends'][backend_name] = {
                    'text': ocr_result.text,
                    'confidence': ocr_result.confidence,
                    'processing_time': ocr_result.processing_time,
                    **accuracy
                }
                
                # Update backend stats
                stats = results['backends'][backend_name]
                stats['total_images'] += 1
                stats['successful'] += 1 if ocr_result.text else 0
                stats['avg_confidence'] += ocr_result.confidence or 0.0
                stats['avg_processing_time'] += ocr_result.processing_time
                stats['avg_precision'] += accuracy['precision']
                stats['avg_recall'] += accuracy['recall']
                stats['avg_f1'] += accuracy['f1']
                stats['avg_wer'] += accuracy['word_error_rate']
                
                print(f"  {backend_name}: F1={accuracy['f1']:.3f}, WER={accuracy['word_error_rate']:.3f}")
                
            except Exception as e:
                print(f"  {backend_name}: Error - {e}")
                image_results['backends'][backend_name] = {'error': str(e)}
        
        results['images'].append(image_results)
    
    # Calculate averages
    for backend_name in available:
        stats = results['backends'][backend_name]
        if stats['total_images'] > 0:
            n = stats['total_images']
            stats['avg_confidence'] /= n
            stats['avg_processing_time'] /= n
            stats['avg_precision'] /= n
            stats['avg_recall'] /= n
            stats['avg_f1'] /= n
            stats['avg_wer'] /= n
    
    # Save results
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n=== Comparison Complete ===")
    print(f"Results saved to {output_file}")
    
    return results


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='OCR backend utilities')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # List available backends
    list_parser = subparsers.add_parser('list', help='List available backends')
    
    # Extract text
    extract_parser = subparsers.add_parser('extract', help='Extract text from image')
    extract_parser.add_argument('image', help='Image file path')
    extract_parser.add_argument('--backend', default='tesseract', help='Backend to use')
    
    # Compare backends
    compare_parser = subparsers.add_parser('compare', help='Compare backends on labeled data')
    compare_parser.add_argument('images', help='Folder with test images')
    compare_parser.add_argument('labels', help='JSON file with ground truth')
    compare_parser.add_argument('--output', default='comparison.json', help='Output file')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        available = get_available_backends()
        print("Available OCR backends:")
        for backend in available:
            print(f"  - {backend}")
    
    elif args.command == 'extract':
        backend = get_ocr_backend(args.backend)
        result = backend.extract_text(args.image)
        print(f"Backend: {result.backend}")
        print(f"Confidence: {result.confidence:.3f}")
        print(f"Word count: {result.word_count}")
        print(f"Processing time: {result.processing_time:.3f}s")
        print(f"\nText:\n{result.text}")
    
    elif args.command == 'compare':
        compare_backends(args.images, args.labels, args.output)
    
    else:
        parser.print_help()
