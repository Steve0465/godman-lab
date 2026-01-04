"""Measurements OCR Batch Workflow - Extract pool measurements from images/PDFs."""
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

from ..engine import BaseWorkflow


@dataclass
class OCRResult:
    """Detailed OCR result with extracted measurements and metadata."""
    
    file: str
    text: str
    customer_name: Optional[str] = None
    measurements: Optional[Tuple[float, float]] = None  # (width, height) or (length, width)
    confidence: float = 0.0
    validation_errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_valid(self) -> bool:
        """Check if the result has valid extracted data."""
        return bool(self.measurements and self.customer_name and not self.validation_errors)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "file": self.file,
            "text": self.text,
            "customer_name": self.customer_name,
            "measurements": self.measurements,
            "confidence": self.confidence,
            "validation_errors": self.validation_errors,
            "metadata": self.metadata,
            "is_valid": self.is_valid
        }


class MeasurementsOCRBatchWorkflow(BaseWorkflow):
    """
    Batch OCR processing workflow for extracting pool measurements.
    
    Features:
    - OCR text extraction from images and PDFs
    - Pool dimension parsing (e.g., "20 x 40", "15' x 30'")
    - Customer name extraction
    - Measurement validation
    - Batch processing support
    """
    
    name = "measurements_ocr_batch"
    description = "Extract pool measurements and customer names from images/PDFs"
    
    # Validation bounds for reasonable pool dimensions (in feet)
    MIN_DIMENSION = 5.0
    MAX_DIMENSION = 200.0
    
    def __init__(self, engine):
        """Initialize workflow with engine reference."""
        self.engine = engine
    
    def run(self, input_files: List[str], **kwargs) -> Dict[str, Any]:
        """
        Run batch OCR processing on multiple files.
        
        Args:
            input_files: List of file paths to process
            **kwargs: Additional parameters
        
        Returns:
            Dictionary with batch results
        """
        if not input_files:
            return {
                "status": "error",
                "message": "No input files provided",
                "total_files": 0,
                "processed": 0,
                "results": []
            }
        
        results = []
        processed = 0
        failed = 0
        
        for file_path in input_files:
            try:
                ocr_result = self._process_single_file(file_path, **kwargs)
                results.append(ocr_result)
                if ocr_result.is_valid:
                    processed += 1
                else:
                    failed += 1
            except Exception as e:
                failed += 1
                results.append(OCRResult(
                    file=str(file_path),
                    text="",
                    validation_errors=[f"Processing error: {str(e)}"]
                ))
        
        return {
            "status": "success",
            "total_files": len(input_files),
            "processed": processed,
            "failed": failed,
            "results": [r.to_dict() for r in results]
        }
    
    def _process_single_file(self, file_path: str, **kwargs) -> OCRResult:
        """
        Process a single file with OCR and extract measurements.
        
        Args:
            file_path: Path to file
            **kwargs: Additional parameters
        
        Returns:
            OCRResult with extracted data
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return OCRResult(
                file=str(file_path),
                text="",
                validation_errors=[f"File not found: {file_path}"]
            )
        
        # Step 1: OCR extraction using the OCRTool
        try:
            ocr_data = self.engine.call_tool("ocr", file_path=str(file_path))
            text = ocr_data.get("text", "")
        except Exception as e:
            return OCRResult(
                file=str(file_path),
                text="",
                validation_errors=[f"OCR failed: {str(e)}"]
            )
        
        # Step 2: Extract measurements
        measurements, measurement_confidence = self.extract_measurements(text)
        
        # Step 3: Extract customer name
        customer_name = self.extract_customer_name(text)
        
        # Step 4: Validate measurements
        validation_errors = self.validate_measurements(measurements)
        
        # Step 5: Build result
        result = OCRResult(
            file=str(file_path),
            text=text,
            customer_name=customer_name,
            measurements=measurements,
            confidence=measurement_confidence,
            validation_errors=validation_errors,
            metadata={
                "file_size": file_path.stat().st_size,
                "file_extension": file_path.suffix,
                "text_length": len(text)
            }
        )
        
        return result
    
    def extract_measurements(self, text: str) -> Tuple[Optional[Tuple[float, float]], float]:
        """
        Extract pool dimensions from OCR text.
        
        Patterns supported:
        - "20 x 40"
        - "20' x 40'"
        - "20ft x 40ft"
        - "20 by 40"
        - "Pool: 20x40"
        
        Args:
            text: OCR extracted text
        
        Returns:
            Tuple of (measurements, confidence) where measurements is (width, height) or None
        """
        if not text:
            return None, 0.0
        
        # Define regex patterns for various measurement formats
        patterns = [
            # Pattern: "20 x 40", "20' x 40'", "20ft x 40ft"
            r'(\d+(?:\.\d+)?)\s*(?:\'|ft|feet)?\s*[xX×]\s*(\d+(?:\.\d+)?)\s*(?:\'|ft|feet)?',
            # Pattern: "20 by 40"
            r'(\d+(?:\.\d+)?)\s*(?:\'|ft|feet)?\s+by\s+(\d+(?:\.\d+)?)\s*(?:\'|ft|feet)?',
            # Pattern: "dimensions: 20 x 40"
            r'(?:dimension|size|pool)s?:\s*(\d+(?:\.\d+)?)\s*(?:\'|ft|feet)?\s*[xX×]\s*(\d+(?:\.\d+)?)\s*(?:\'|ft|feet)?',
        ]
        
        confidence = 0.0
        measurements = None
        
        for idx, pattern in enumerate(patterns):
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    dim1 = float(match.group(1))
                    dim2 = float(match.group(2))
                    
                    # Higher confidence for more specific patterns
                    pattern_confidence = 1.0 - (idx * 0.1)
                    
                    # If we find a valid measurement, use it
                    if self.MIN_DIMENSION <= dim1 <= self.MAX_DIMENSION and \
                       self.MIN_DIMENSION <= dim2 <= self.MAX_DIMENSION:
                        measurements = (dim1, dim2)
                        confidence = pattern_confidence
                        break
                except (ValueError, IndexError):
                    continue
            
            if measurements:
                break
        
        return measurements, confidence
    
    def extract_customer_name(self, text: str) -> Optional[str]:
        """
        Extract customer name from OCR text.
        
        Looks for patterns like:
        - "Customer: John Doe"
        - "Name: Jane Smith"
        - "Owner: Bob Johnson"
        
        Args:
            text: OCR extracted text
        
        Returns:
            Customer name or None if not found
        """
        if not text:
            return None
        
        # Define patterns for customer name extraction
        # Match capitalized words but stop at newlines or non-name characters
        patterns = [
            r'(?:customer|client|owner|name):\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+?)(?:\n|$|[,;:])',
            r'(?:for|to):\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+?)(?:\n|$|[,;:])',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Basic validation: should have at least first and last name
                if len(name.split()) >= 2:
                    return name
        
        # Fallback: Look for capitalized names in first few lines
        lines = text.split('\n')[:5]  # Check first 5 lines
        for line in lines:
            # Skip lines that look like titles or headings
            if any(word in line.lower() for word in ['invoice', 'service', 'pool', 'receipt']):
                continue
            # Look for pattern of capitalized words (likely a name)
            name_match = re.search(r'^[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?$', line.strip())
            if name_match:
                return name_match.group(0).strip()
        
        return None
    
    def validate_measurements(self, measurements: Optional[Tuple[float, float]]) -> List[str]:
        """
        Validate extracted measurements are reasonable.
        
        Args:
            measurements: Tuple of (width, height)
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if measurements is None:
            errors.append("No measurements found in text")
            return errors
        
        width, height = measurements
        
        # Check minimum dimensions
        if width < self.MIN_DIMENSION:
            errors.append(f"Width {width} ft is below minimum {self.MIN_DIMENSION} ft")
        
        if height < self.MIN_DIMENSION:
            errors.append(f"Height {height} ft is below minimum {self.MIN_DIMENSION} ft")
        
        # Check maximum dimensions
        if width > self.MAX_DIMENSION:
            errors.append(f"Width {width} ft exceeds maximum {self.MAX_DIMENSION} ft")
        
        if height > self.MAX_DIMENSION:
            errors.append(f"Height {height} ft exceeds maximum {self.MAX_DIMENSION} ft")
        
        # Check aspect ratio (pools typically aren't extremely elongated)
        if width > 0 and height > 0:
            aspect_ratio = max(width, height) / min(width, height)
            if aspect_ratio > 10:
                errors.append(f"Unusual aspect ratio: {aspect_ratio:.1f}:1")
        
        return errors
