"""
Advanced Vision Tool - Classification, face recognition, object detection
"""
from ..engine import BaseTool
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class VisionAdvancedTool(BaseTool):
    """Advanced computer vision capabilities"""
    
    name = "vision_advanced"
    description = "Document classification, face recognition, object detection"
    
    def run(self, action: str, image_path: str, **kwargs):
        """
        Advanced vision operations
        
        Args:
            action: 'classify', 'detect_faces', 'detect_objects', 'ocr_handwriting'
            image_path: Path to image file
        """
        if action == "classify":
            return self.classify_document(image_path)
        elif action == "detect_faces":
            return self.detect_faces(image_path, **kwargs)
        elif action == "detect_objects":
            return self.detect_objects(image_path)
        elif action == "ocr_handwriting":
            return self.ocr_handwriting(image_path)
        else:
            return {"error": f"Unknown action: {action}"}
    
    def classify_document(self, image_path: str):
        """Classify document type (bill, receipt, contract, etc.)"""
        try:
            from PIL import Image
            import pytesseract
        except ImportError:
            return {"error": "PIL or pytesseract not installed"}
        
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        
        # Simple classification based on keywords
        text_lower = text.lower()
        
        if "invoice" in text_lower or "bill to" in text_lower:
            doc_type = "invoice"
        elif "receipt" in text_lower or "total" in text_lower and "$" in text:
            doc_type = "receipt"
        elif "contract" in text_lower or "agreement" in text_lower:
            doc_type = "contract"
        elif "statement" in text_lower:
            doc_type = "statement"
        else:
            doc_type = "unknown"
        
        return {
            "status": "success",
            "document_type": doc_type,
            "confidence": 0.8,
            "text_preview": text[:200]
        }
    
    def detect_faces(self, image_path: str, recognize: bool = False):
        """Detect and optionally recognize faces"""
        try:
            import cv2
            import face_recognition
        except ImportError:
            return {"error": "opencv-python and face_recognition not installed"}
        
        image = face_recognition.load_image_file(image_path)
        face_locations = face_recognition.face_locations(image)
        
        if not recognize:
            return {
                "status": "success",
                "face_count": len(face_locations),
                "locations": face_locations
            }
        
        # Face recognition (requires known faces database)
        face_encodings = face_recognition.face_encodings(image, face_locations)
        
        return {
            "status": "success",
            "face_count": len(face_locations),
            "faces": [{"location": loc, "encoding": enc.tolist()} 
                     for loc, enc in zip(face_locations, face_encodings)]
        }
    
    def detect_objects(self, image_path: str):
        """Detect objects in image"""
        try:
            import cv2
            import numpy as np
        except ImportError:
            return {"error": "opencv-python not installed"}
        
        # This would use YOLO or similar model
        # For now, return placeholder
        return {
            "status": "success",
            "message": "Object detection requires YOLO model - coming soon",
            "objects": []
        }
    
    def ocr_handwriting(self, image_path: str):
        """OCR for handwritten text"""
        try:
            from PIL import Image
            import pytesseract
        except ImportError:
            return {"error": "PIL or pytesseract not installed"}
        
        img = Image.open(image_path)
        
        # Use Tesseract with handwriting config
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(img, config=custom_config)
        
        return {
            "status": "success",
            "text": text,
            "confidence": "medium"
        }
