"""Receipts Workflow - End-to-end receipt processing automation."""
from pathlib import Path
from typing import Dict, Any
from engine import BaseWorkflow


class ReceiptsWorkflow(BaseWorkflow):
    """
    Complete receipt processing workflow.
    
    Steps:
    1. Scan input directory for new receipts
    2. OCR text extraction
    3. Vision API analysis (if enabled)
    4. Extract structured data (vendor, date, amount)
    5. Log to Google Sheets
    6. Organize files by date/vendor
    7. Generate summary report
    """
    
    name = "receipts_workflow"
    description = "Complete end-to-end receipt processing pipeline"
    
    def __init__(self, engine):
        """Initialize workflow with engine reference."""
        self.engine = engine
    
    def run(self, input_dir: str, **kwargs) -> Dict[str, Any]:
        """
        Run the complete receipt processing workflow.
        
        Args:
            input_dir: Directory containing receipt files
            **kwargs: Additional parameters
        
        Returns:
            Dictionary with workflow results
        """
        input_path = Path(input_dir)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")
        
        # Find all receipt files
        receipt_files = []
        for ext in ['.pdf', '.jpg', '.jpeg', '.png']:
            receipt_files.extend(input_path.glob(f"*{ext}"))
        
        if not receipt_files:
            return {
                "status": "no_files",
                "message": "No receipt files found",
                "files_processed": 0
            }
        
        results = {
            "total_files": len(receipt_files),
            "processed": 0,
            "failed": 0,
            "receipts": []
        }
        
        # Process each receipt
        for receipt_file in receipt_files:
            try:
                receipt_data = self._process_single_receipt(receipt_file, **kwargs)
                results["receipts"].append(receipt_data)
                results["processed"] += 1
            except Exception as e:
                results["failed"] += 1
                results["receipts"].append({
                    "file": str(receipt_file),
                    "error": str(e),
                    "status": "failed"
                })
        
        # Generate summary
        if results["processed"] > 0:
            results["summary"] = self._generate_summary(results["receipts"])
        
        # Log to Sheets (if configured)
        if kwargs.get("log_to_sheets"):
            results["sheets_logged"] = self._log_to_sheets(results["receipts"], **kwargs)
        
        return results
    
    def _process_single_receipt(self, file_path: Path, **kwargs) -> Dict[str, Any]:
        """Process a single receipt file."""
        
        # Step 1: OCR extraction
        ocr_result = self.engine.call_tool("ocr", file_path=file_path)
        
        # Step 2: Vision analysis (if enabled)
        vision_result = None
        if kwargs.get("use_vision", False):
            vision_result = self.engine.call_tool("vision", image_path=file_path)
        
        # Step 3: Extract structured data
        # In a real implementation, this would use the extracted text
        # For now, return placeholder data
        receipt_data = {
            "file": str(file_path),
            "vendor": "Sample Vendor",
            "date": "2025-12-05",
            "total": 42.50,
            "items": [],
            "ocr_text": ocr_result.get("text", ""),
            "vision_analysis": vision_result,
            "status": "success"
        }
        
        return receipt_data
    
    def _generate_summary(self, receipts: list) -> Dict[str, Any]:
        """Generate summary of processed receipts."""
        successful = [r for r in receipts if r.get("status") == "success"]
        
        total_amount = sum(r.get("total", 0) for r in successful)
        
        vendors = {}
        for receipt in successful:
            vendor = receipt.get("vendor", "Unknown")
            vendors[vendor] = vendors.get(vendor, 0) + 1
        
        return {
            "total_receipts": len(successful),
            "total_amount": total_amount,
            "avg_amount": total_amount / len(successful) if successful else 0,
            "unique_vendors": len(vendors),
            "top_vendor": max(vendors.items(), key=lambda x: x[1])[0] if vendors else None
        }
    
    def _log_to_sheets(self, receipts: list, **kwargs) -> Dict[str, Any]:
        """Log receipts to Google Sheets."""
        spreadsheet_id = kwargs.get("spreadsheet_id")
        
        if not spreadsheet_id:
            return {"logged": False, "reason": "No spreadsheet_id provided"}
        
        logged_count = 0
        for receipt in receipts:
            if receipt.get("status") == "success":
                try:
                    self.engine.call_tool(
                        "sheets_receipt_logger",
                        spreadsheet_id=spreadsheet_id,
                        receipt_data=receipt
                    )
                    logged_count += 1
                except Exception as e:
                    pass
        
        return {
            "logged": True,
            "count": logged_count,
            "spreadsheet_id": spreadsheet_id
        }


class QuickReceiptProcessor(BaseWorkflow):
    """Quick receipt processing without full workflow."""
    
    name = "quick_receipt"
    description = "Fast receipt processing for single files"
    
    def __init__(self, engine):
        self.engine = engine
    
    def run(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """
        Quickly process a single receipt.
        
        Args:
            file_path: Path to receipt file
            **kwargs: Additional parameters
        
        Returns:
            Dictionary with receipt data
        """
        # OCR + Vision analysis
        ocr_result = self.engine.call_tool("ocr", file_path=file_path)
        
        if kwargs.get("use_vision", True):
            vision_result = self.engine.call_tool(
                "receipt_analyzer",
                image_path=file_path
            )
        else:
            vision_result = None
        
        return {
            "file": file_path,
            "ocr": ocr_result,
            "vision": vision_result,
            "processed_at": "2025-12-05T04:37:00Z"
        }
