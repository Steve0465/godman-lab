"""OCR Tool - Optical Character Recognition for documents."""
import sys
from pathlib import Path
from typing import Union, Dict, Any

# Add libs to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "libs"))

from ..engine import BaseTool


class OCRTool(BaseTool):
    """Extract text from images and PDFs using Tesseract OCR."""
    
    name = "ocr"
    description = "Extract text from images and PDF files using OCR"
    
    def execute(self, file_path: Union[str, Path], **kwargs) -> Dict[str, Any]:
        """
        Extract text from a file using OCR.
        
        Args:
            file_path: Path to image or PDF file
            **kwargs: Additional parameters (max_pages, lang, etc.)
        
        Returns:
            Dictionary with extracted text and metadata
        """
        from ocr import ocr_file
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Extract text
        text = ocr_file(
            file_path,
            max_pages=kwargs.get("max_pages", None)
        )
        
        return {
            "file": str(file_path),
            "text": text,
            "length": len(text),
            "lines": len(text.split('\n'))
        }


class OCRBatchTool(BaseTool):
    """Batch OCR processing for multiple files."""
    
    name = "ocr_batch"
    description = "Process multiple files with OCR in batch"
    
    def execute(self, file_paths: list, **kwargs) -> Dict[str, Any]:
        """
        Process multiple files with OCR.
        
        Args:
            file_paths: List of file paths to process
            **kwargs: Additional parameters
        
        Returns:
            Dictionary with results for each file
        """
        from ocr import ocr_file
        
        results = {}
        
        for file_path in file_paths:
            try:
                text = ocr_file(Path(file_path))
                results[str(file_path)] = {
                    "success": True,
                    "text": text,
                    "length": len(text)
                }
            except Exception as e:
                results[str(file_path)] = {
                    "success": False,
                    "error": str(e)
                }
        
        return {
            "total": len(file_paths),
            "successful": sum(1 for r in results.values() if r.get("success")),
            "failed": sum(1 for r in results.values() if not r.get("success")),
            "results": results
        }
