"""
Automated Receipt Processing Workflow
Monitors scan folder and auto-processes receipts
"""
from ..engine import BaseWorkflow
import logging

logger = logging.getLogger(__name__)


class AutoReceiptWorkflow(BaseWorkflow):
    """Automatically process receipts as they arrive"""
    
    name = "auto_receipt"
    description = "Watches for new receipts and auto-processes them"
    
    def run(self, engine, **kwargs):
        """
        Workflow steps:
        1. Watch scans/ directory
        2. Detect new PDF/image files
        3. Run OCR
        4. Extract receipt data
        5. Save to CSV
        6. Move to processed folder
        """
        steps = []
        
        # Step 1: Start file watcher
        watch_result = engine.call_tool("filesystem_watcher", 
            watch_dir="scans",
            patterns={
                "*.pdf": "process_receipt",
                "*.jpg": "process_receipt",
                "*.png": "process_receipt"
            }
        )
        steps.append({"step": "watch", "result": watch_result})
        
        # When new file detected, process it
        if watch_result.get("file"):
            file_path = watch_result["file"]
            
            # Step 2: OCR the file
            ocr_result = engine.call_tool("ocr", file_path=file_path)
            steps.append({"step": "ocr", "result": ocr_result})
            
            # Step 3: Extract receipt data
            if ocr_result.get("text"):
                parse_result = engine.call_tool("vision_advanced",
                    action="classify",
                    image_path=file_path
                )
                steps.append({"step": "classify", "result": parse_result})
            
            # Step 4: Save to database/CSV
            # (Would integrate with existing receipt processing)
            
        return {
            "workflow": self.name,
            "status": "running",
            "steps": steps
        }
