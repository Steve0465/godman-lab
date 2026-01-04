"""Test suite for MeasurementsOCRBatchWorkflow."""
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock
from typing import Dict, Any

from godman_ai.workflows.measurements_ocr_batch import (
    MeasurementsOCRBatchWorkflow,
    OCRResult,
)


class MockEngine:
    """Mock engine for testing."""
    
    def __init__(self, ocr_text: str = ""):
        self.ocr_text = ocr_text
    
    def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Mock tool call."""
        if tool_name == "ocr":
            return {
                "text": self.ocr_text,
                "length": len(self.ocr_text),
                "file": kwargs.get("file_path", "")
            }
        return {}


class TestOCRResult:
    """Test OCRResult dataclass."""
    
    def test_ocr_result_valid(self):
        """Test valid OCR result."""
        result = OCRResult(
            file="test.pdf",
            text="Pool: 20 x 40\nCustomer: John Doe",
            customer_name="John Doe",
            measurements=(20.0, 40.0),
            confidence=0.9
        )
        
        assert result.is_valid
        assert result.customer_name == "John Doe"
        assert result.measurements == (20.0, 40.0)
        assert result.confidence == 0.9
    
    def test_ocr_result_invalid_no_measurements(self):
        """Test invalid result with no measurements."""
        result = OCRResult(
            file="test.pdf",
            text="Some text",
            customer_name="John Doe",
            measurements=None
        )
        
        assert not result.is_valid
    
    def test_ocr_result_invalid_with_errors(self):
        """Test invalid result with validation errors."""
        result = OCRResult(
            file="test.pdf",
            text="Pool: 2 x 3",
            customer_name="John Doe",
            measurements=(2.0, 3.0),
            validation_errors=["Width 2.0 ft is below minimum 5.0 ft"]
        )
        
        assert not result.is_valid
        assert len(result.validation_errors) > 0
    
    def test_ocr_result_valid_without_customer(self):
        """Test valid result with measurements but no customer name."""
        result = OCRResult(
            file="test.pdf",
            text="Pool: 20 x 40",
            customer_name=None,
            measurements=(20.0, 40.0),
            confidence=0.9
        )
        
        # Should be valid even without customer name
        assert result.is_valid
        assert result.customer_name is None
        assert result.measurements == (20.0, 40.0)
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = OCRResult(
            file="test.pdf",
            text="Pool: 20 x 40",
            customer_name="John Doe",
            measurements=(20.0, 40.0),
            confidence=0.9
        )
        
        result_dict = result.to_dict()
        assert result_dict["file"] == "test.pdf"
        assert result_dict["customer_name"] == "John Doe"
        assert result_dict["measurements"] == (20.0, 40.0)
        assert result_dict["is_valid"]


class TestMeasurementExtraction:
    """Test measurement extraction logic."""
    
    def test_extract_simple_dimensions(self):
        """Test extraction of simple 'X x Y' format."""
        workflow = MeasurementsOCRBatchWorkflow(engine=MockEngine())
        
        text = "Pool dimensions: 20 x 40"
        measurements, confidence = workflow.extract_measurements(text)
        
        assert measurements == (20.0, 40.0)
        assert confidence > 0.5
    
    def test_extract_dimensions_with_feet(self):
        """Test extraction with foot markers."""
        workflow = MeasurementsOCRBatchWorkflow(engine=MockEngine())
        
        text = "Pool size: 15' x 30'"
        measurements, confidence = workflow.extract_measurements(text)
        
        assert measurements == (15.0, 30.0)
        assert confidence > 0.5
    
    def test_extract_dimensions_with_ft(self):
        """Test extraction with 'ft' markers."""
        workflow = MeasurementsOCRBatchWorkflow(engine=MockEngine())
        
        text = "Pool: 18ft x 36ft"
        measurements, confidence = workflow.extract_measurements(text)
        
        assert measurements == (18.0, 36.0)
        assert confidence > 0.5
    
    def test_extract_dimensions_by_format(self):
        """Test extraction with 'by' separator."""
        workflow = MeasurementsOCRBatchWorkflow(engine=MockEngine())
        
        text = "Pool dimensions: 25 by 50"
        measurements, confidence = workflow.extract_measurements(text)
        
        assert measurements == (25.0, 50.0)
        assert confidence > 0.0
    
    def test_extract_decimal_dimensions(self):
        """Test extraction of decimal dimensions."""
        workflow = MeasurementsOCRBatchWorkflow(engine=MockEngine())
        
        text = "Pool: 20.5 x 40.75"
        measurements, confidence = workflow.extract_measurements(text)
        
        assert measurements == (20.5, 40.75)
        assert confidence > 0.5
    
    def test_extract_no_measurements(self):
        """Test when no measurements are found."""
        workflow = MeasurementsOCRBatchWorkflow(engine=MockEngine())
        
        text = "This is some text without measurements"
        measurements, confidence = workflow.extract_measurements(text)
        
        assert measurements is None
        assert confidence == 0.0
    
    def test_extract_invalid_dimensions(self):
        """Test when dimensions are out of valid range."""
        workflow = MeasurementsOCRBatchWorkflow(engine=MockEngine())
        
        # Too large
        text = "Pool: 300 x 400"
        measurements, confidence = workflow.extract_measurements(text)
        
        assert measurements is None
        assert confidence == 0.0
    
    def test_extract_multiple_patterns(self):
        """Test extraction from text with multiple number patterns."""
        workflow = MeasurementsOCRBatchWorkflow(engine=MockEngine())
        
        text = """
        Invoice #12345
        Date: 01/04/2023
        Pool dimensions: 20 x 40
        Total: $1234.56
        """
        measurements, confidence = workflow.extract_measurements(text)
        
        assert measurements == (20.0, 40.0)
        assert confidence > 0.5


class TestCustomerNameExtraction:
    """Test customer name extraction logic."""
    
    def test_extract_customer_with_label(self):
        """Test extraction with 'Customer:' label."""
        workflow = MeasurementsOCRBatchWorkflow(engine=MockEngine())
        
        text = "Customer: John Doe\nPool: 20 x 40"
        name = workflow.extract_customer_name(text)
        
        assert name == "John Doe"
    
    def test_extract_owner_with_label(self):
        """Test extraction with 'Owner:' label."""
        workflow = MeasurementsOCRBatchWorkflow(engine=MockEngine())
        
        text = "Owner: Jane Smith\nDimensions: 15 x 30"
        name = workflow.extract_customer_name(text)
        
        assert name == "Jane Smith"
    
    def test_extract_name_with_label(self):
        """Test extraction with 'Name:' label."""
        workflow = MeasurementsOCRBatchWorkflow(engine=MockEngine())
        
        text = "Name: Bob Johnson\nService Date: 01/04/2023"
        name = workflow.extract_customer_name(text)
        
        assert name == "Bob Johnson"
    
    def test_extract_capitalized_name(self):
        """Test extraction of capitalized name in first lines."""
        workflow = MeasurementsOCRBatchWorkflow(engine=MockEngine())
        
        text = """
        Pool Service Invoice
        Alice Williams
        123 Main Street
        Pool: 20 x 40
        """
        name = workflow.extract_customer_name(text)
        
        assert name == "Alice Williams"
    
    def test_extract_three_word_name(self):
        """Test extraction of three-word name."""
        workflow = MeasurementsOCRBatchWorkflow(engine=MockEngine())
        
        text = "Customer: Mary Jane Watson"
        name = workflow.extract_customer_name(text)
        
        assert name == "Mary Jane Watson"
    
    def test_no_name_found(self):
        """Test when no name is found."""
        workflow = MeasurementsOCRBatchWorkflow(engine=MockEngine())
        
        text = "Pool dimensions: 20 x 40\nTotal: $500"
        name = workflow.extract_customer_name(text)
        
        assert name is None
    
    def test_single_word_not_extracted(self):
        """Test that single words are not extracted as names."""
        workflow = MeasurementsOCRBatchWorkflow(engine=MockEngine())
        
        text = "Customer: John"
        name = workflow.extract_customer_name(text)
        
        # Should not extract single word names (requires at least 2 words)
        assert name is None


class TestMeasurementValidation:
    """Test measurement validation logic."""
    
    def test_validate_valid_measurements(self):
        """Test validation of valid measurements."""
        workflow = MeasurementsOCRBatchWorkflow(engine=MockEngine())
        
        errors = workflow.validate_measurements((20.0, 40.0))
        
        assert len(errors) == 0
    
    def test_validate_none_measurements(self):
        """Test validation when measurements are None."""
        workflow = MeasurementsOCRBatchWorkflow(engine=MockEngine())
        
        errors = workflow.validate_measurements(None)
        
        assert len(errors) > 0
        assert any("No measurements found" in err for err in errors)
    
    def test_validate_too_small_width(self):
        """Test validation of too small width."""
        workflow = MeasurementsOCRBatchWorkflow(engine=MockEngine())
        
        errors = workflow.validate_measurements((2.0, 40.0))
        
        assert len(errors) > 0
        assert any("Width" in err and "below minimum" in err for err in errors)
    
    def test_validate_too_small_height(self):
        """Test validation of too small height."""
        workflow = MeasurementsOCRBatchWorkflow(engine=MockEngine())
        
        errors = workflow.validate_measurements((20.0, 3.0))
        
        assert len(errors) > 0
        assert any("Height" in err and "below minimum" in err for err in errors)
    
    def test_validate_too_large_dimensions(self):
        """Test validation of too large dimensions."""
        workflow = MeasurementsOCRBatchWorkflow(engine=MockEngine())
        
        errors = workflow.validate_measurements((250.0, 300.0))
        
        assert len(errors) > 0
        assert any("exceeds maximum" in err for err in errors)
    
    def test_validate_unusual_aspect_ratio(self):
        """Test validation of unusual aspect ratio."""
        workflow = MeasurementsOCRBatchWorkflow(engine=MockEngine())
        
        errors = workflow.validate_measurements((10.0, 150.0))
        
        assert len(errors) > 0
        assert any("aspect ratio" in err.lower() for err in errors)
    
    def test_validate_edge_case_minimum(self):
        """Test validation at minimum boundary."""
        workflow = MeasurementsOCRBatchWorkflow(engine=MockEngine())
        
        errors = workflow.validate_measurements((5.0, 5.0))
        
        assert len(errors) == 0
    
    def test_validate_edge_case_maximum(self):
        """Test validation at maximum boundary."""
        workflow = MeasurementsOCRBatchWorkflow(engine=MockEngine())
        
        errors = workflow.validate_measurements((200.0, 200.0))
        
        assert len(errors) == 0


class TestWorkflowIntegration:
    """Test complete workflow integration."""
    
    def test_process_single_file_success(self, tmp_path):
        """Test processing a single file successfully."""
        # Create a temporary file
        test_file = tmp_path / "pool_invoice.txt"
        test_file.write_text("Customer: John Doe\nPool: 20 x 40")
        
        # Create workflow with mock engine
        mock_engine = MockEngine(ocr_text="Customer: John Doe\nPool: 20 x 40")
        workflow = MeasurementsOCRBatchWorkflow(engine=mock_engine)
        
        # Process file
        result = workflow._process_single_file(str(test_file))
        
        assert result.customer_name == "John Doe"
        assert result.measurements == (20.0, 40.0)
        assert result.is_valid
        assert len(result.validation_errors) == 0
    
    def test_process_single_file_not_found(self):
        """Test processing a file that doesn't exist."""
        mock_engine = MockEngine()
        workflow = MeasurementsOCRBatchWorkflow(engine=mock_engine)
        
        result = workflow._process_single_file("/nonexistent/file.pdf")
        
        assert not result.is_valid
        assert len(result.validation_errors) > 0
        assert any("not found" in err.lower() for err in result.validation_errors)
    
    def test_batch_processing_empty_list(self):
        """Test batch processing with empty file list."""
        mock_engine = MockEngine()
        workflow = MeasurementsOCRBatchWorkflow(engine=mock_engine)
        
        result = workflow.run([])
        
        assert result["status"] == "error"
        assert result["total_files"] == 0
    
    def test_batch_processing_multiple_files(self, tmp_path):
        """Test batch processing with multiple files."""
        # Create test files
        file1 = tmp_path / "file1.txt"
        file1.write_text("temp")
        file2 = tmp_path / "file2.txt"
        file2.write_text("temp")
        
        # Create workflow with mock engine
        mock_engine = MockEngine(ocr_text="Customer: Jane Smith\nPool: 15 x 30")
        workflow = MeasurementsOCRBatchWorkflow(engine=mock_engine)
        
        # Process files
        result = workflow.run([str(file1), str(file2)])
        
        assert result["status"] == "success"
        assert result["total_files"] == 2
        assert len(result["results"]) == 2
    
    def test_metadata_included(self, tmp_path):
        """Test that metadata is included in results."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Customer: Bob Jones\nPool: 25 x 50")
        
        mock_engine = MockEngine(ocr_text="Customer: Bob Jones\nPool: 25 x 50")
        workflow = MeasurementsOCRBatchWorkflow(engine=mock_engine)
        
        result = workflow._process_single_file(str(test_file))
        
        assert "file_size" in result.metadata
        assert "file_extension" in result.metadata
        assert "text_length" in result.metadata
        assert result.metadata["file_extension"] == ".txt"
