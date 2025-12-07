"""Enhanced receipt data extraction with structured JSON output and item-level parsing."""

import os
import json
import re
from typing import Dict, List, Optional, Any
from openai import OpenAI

# Strict JSON schema for receipt data
RECEIPT_SCHEMA = {
    "type": "object",
    "properties": {
        "vendor": {"type": "string", "description": "Store or merchant name"},
        "date": {"type": "string", "description": "Purchase date in YYYY-MM-DD format"},
        "time": {"type": "string", "description": "Purchase time if available"},
        "items": {
            "type": "array",
            "description": "Individual line items from receipt",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "price": {"type": "number"},
                    "quantity": {"type": "number", "default": 1}
                },
                "required": ["name", "price"]
            }
        },
        "subtotal": {"type": "number", "description": "Subtotal before tax"},
        "tax": {"type": "number", "description": "Tax amount"},
        "total": {"type": "number", "description": "Total amount paid"},
        "payment_method": {"type": "string", "description": "Cash, Card, Credit, Debit, etc."},
        "category": {"type": "string", "description": "IRS tax category"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1, "description": "Extraction confidence score"},
        "notes": {"type": "string", "description": "Any special notes or flags"}
    },
    "required": ["vendor", "date", "total"]
}

# Enhanced prompt with item-level instructions
PROMPT_SYSTEM = """You are a precise receipt data extractor specialized in IRS tax compliance.

Extract ALL information from the receipt OCR text and return ONLY valid JSON matching the schema.

Guidelines:
- Extract individual line items with names and prices
- Dates must be in YYYY-MM-DD format
- All monetary amounts as numbers (no $ symbols)
- If a field is missing, omit it or use null
- Calculate confidence (0-1) based on OCR quality
- Flag any unclear or ambiguous data in notes

IRS Categories: Office Expense, Car/Truck, Meals (50%), Travel, Utilities, Insurance, Professional Services, Supplies"""

PROMPT_USER_TEMPLATE = """Extract structured receipt data from this OCR text:

{ocr_text}

Return ONLY a JSON object with these fields:
- vendor (required)
- date (required, YYYY-MM-DD)
- time (optional)
- items (array of {{name, price, quantity}})
- subtotal
- tax
- total (required)
- payment_method
- category (IRS tax category)
- confidence (0-1 score)
- notes (any issues or flags)

Do not include markdown, explanations, or extra text. Output pure JSON only."""


class EnhancedReceiptExtractor:
    """Enhanced LLM-based receipt data extraction with structured output."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """Initialize with OpenAI API key and model."""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model = model or os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        
        if not self.api_key or self.api_key == 'your_openai_api_key_here':
            raise RuntimeError('OPENAI_API_KEY not set in environment')
        
        self.client = OpenAI(api_key=self.api_key)
    
    def extract_receipt_data(self, ocr_text: str, image_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Extract structured receipt data from OCR text using LLM.
        
        Args:
            ocr_text: Raw OCR text from receipt image
            image_path: Optional path to original image for reference
            
        Returns:
            Dictionary with structured receipt data or None on failure
        """
        if not ocr_text or not ocr_text.strip():
            return None
        
        try:
            messages = [
                {"role": "system", "content": PROMPT_SYSTEM},
                {"role": "user", "content": PROMPT_USER_TEMPLATE.format(ocr_text=ocr_text)}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.0,  # Deterministic output
                max_tokens=1024
            )
            
            output = response.choices[0].message.content
            
            # Parse JSON from response
            parsed = self._parse_json_response(output)
            
            if parsed and image_path:
                parsed['image_path'] = image_path
            
            return parsed
            
        except Exception as e:
            print(f'OpenAI extraction failed: {e}')
            return None
    
    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON from LLM response with fallback strategies.
        
        Handles:
        - Plain JSON
        - JSON wrapped in markdown code blocks
        - Malformed JSON with extra text
        """
        if not response:
            return None
        
        # Strategy 1: Direct JSON parse
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Extract from markdown code block
        code_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        match = re.search(code_block_pattern, response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Strategy 3: Find JSON object boundaries
        start = response.find('{')
        end = response.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(response[start:end+1])
            except json.JSONDecodeError:
                pass
        
        print(f"Failed to parse JSON from response: {response[:200]}")
        return None
    
    def extract_with_fallback(self, ocr_text: str, image_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract data with basic fallback if LLM fails.
        
        Returns minimal data structure even on complete failure.
        """
        # Try LLM extraction
        result = self.extract_receipt_data(ocr_text, image_path)
        if result:
            return result
        
        # Fallback: Basic regex extraction
        print("LLM extraction failed, using fallback regex parser")
        return self._basic_extraction(ocr_text, image_path)
    
    def _basic_extraction(self, text: str, image_path: Optional[str] = None) -> Dict[str, Any]:
        """Basic regex-based extraction as fallback."""
        data = {
            "vendor": "Unknown",
            "date": self._extract_date(text) or "Unknown",
            "total": self._extract_total(text) or 0.0,
            "confidence": 0.3,
            "notes": "Extracted using fallback regex parser",
            "items": []
        }
        
        if image_path:
            data['image_path'] = image_path
        
        # Try to get vendor from first line
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if lines:
            data['vendor'] = lines[0][:50]  # Limit length
        
        return data
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date from text using common patterns."""
        patterns = [
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY-MM-DD
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',  # MM/DD/YY(YY)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)  # Return raw match
        
        return None
    
    def _extract_total(self, text: str) -> Optional[float]:
        """Extract total amount from text."""
        # Look for "Total" followed by amount
        pattern = r'total[:\s]*\$?\s*(\d+\.?\d{0,2})'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        
        return None


def demo():
    """Demo the enhanced extractor."""
    sample_ocr = """
    WHOLE FOODS MARKET
    550 BOWIE ST, AUSTIN TX 78703
    512-476-1206
    
    Organic Bananas       $3.49
    Almond Milk           $4.99
    Chicken Breast        $12.99
    Mixed Greens          $5.99
    
    SUBTOTAL             $27.46
    TAX                   $2.37
    TOTAL                $29.83
    
    VISA ending in 1234
    12/06/2024 14:32
    """
    
    extractor = EnhancedReceiptExtractor()
    result = extractor.extract_with_fallback(sample_ocr)
    
    print("Extracted Data:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    demo()
