"""
Receipt processing module for godman_ai.

Provides typed models and functions for managing receipt data from CSV files.
Integrates with OCR results to automatically extract receipt information.
"""

from datetime import date as date_type
from decimal import Decimal
from pathlib import Path
from typing import Optional
import re
import csv

import pandas as pd
from pydantic import BaseModel, Field, ConfigDict

# Placeholder for Settings - adjust import path as needed
# from godman_ai.config import Settings


class Receipt(BaseModel):
    """Typed model for a receipt record."""
    
    model_config = ConfigDict(
        json_encoders={
            Decimal: float,
            date_type: lambda v: v.isoformat()
        }
    )
    
    id: str = Field(..., description="Unique identifier for the receipt")
    date: date_type = Field(..., description="Date of purchase")
    vendor: str = Field(..., description="Vendor/merchant name")
    amount: Decimal = Field(..., description="Total amount")
    category: Optional[str] = Field(None, description="Expense category")
    source_file: Optional[str] = Field(None, description="Path to source document/image")
    notes: Optional[str] = Field(None, description="Additional notes")


class OCRResult(BaseModel):
    """Placeholder model for OCR results."""
    
    raw_text: str
    confidence: float = 1.0
    metadata: dict = {}


def get_default_csv_path() -> Path:
    """
    Get the default CSV path from environment variable or fallback.
    
    Checks GODMAN_RECEIPTS_CSV environment variable first,
    then falls back to receipts_tax.csv in the current directory.
    
    Returns:
        Path to receipts CSV file
    """
    import os
    env_path = os.getenv("GODMAN_RECEIPTS_CSV")
    if env_path:
        return Path(env_path)
    return Path("receipts_tax.csv")


def load_receipts(path: Optional[Path] = None) -> list[Receipt]:
    """
    Load receipts from CSV file into typed Receipt models.
    
    Args:
        path: Path to CSV file. Uses default from Settings if None.
        
    Returns:
        List of Receipt objects
        
    Raises:
        FileNotFoundError: If CSV file doesn't exist
    """
    csv_path = path or get_default_csv_path()
    
    if not csv_path.exists():
        raise FileNotFoundError(f"Receipt CSV not found: {csv_path}")
    
    # Load CSV with pandas
    df = pd.read_csv(csv_path)
    
    receipts = []
    for _, row in df.iterrows():
        try:
            receipt = Receipt(
                id=str(row.get('id', '')),
                date=pd.to_datetime(row['date']).date(),
                vendor=str(row['vendor']),
                amount=Decimal(str(row['amount'])),
                category=str(row['category']) if pd.notna(row.get('category')) else None,
                source_file=str(row['source_file']) if pd.notna(row.get('source_file')) else None,
                notes=str(row['notes']) if pd.notna(row.get('notes')) else None,
            )
            receipts.append(receipt)
        except Exception as e:
            # Skip malformed rows but log them
            print(f"Warning: Skipping row due to error: {e}")
            continue
    
    return receipts


def append_receipt(path: Optional[Path] = None, receipt: Receipt = None) -> None:
    """
    Append a single receipt to the CSV file.
    Creates the file with headers if it doesn't exist.
    
    Args:
        path: Path to CSV file. Uses default from Settings if None.
        receipt: Receipt object to append
    """
    csv_path = path or get_default_csv_path()
    
    # Define CSV headers
    headers = ['id', 'date', 'vendor', 'amount', 'category', 'source_file', 'notes']
    
    # Check if file exists
    file_exists = csv_path.exists()
    
    # Open in append mode
    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        
        # Write headers if new file
        if not file_exists:
            writer.writeheader()
        
        # Write receipt data
        writer.writerow({
            'id': receipt.id,
            'date': receipt.date.isoformat(),
            'vendor': receipt.vendor,
            'amount': float(receipt.amount),
            'category': receipt.category or '',
            'source_file': receipt.source_file or '',
            'notes': receipt.notes or '',
        })


def upsert_receipts(path: Optional[Path] = None, receipts: list[Receipt] = None) -> None:
    """
    Merge receipts into CSV by ID (update existing, insert new).
    
    Args:
        path: Path to CSV file. Uses default from Settings if None.
        receipts: List of Receipt objects to upsert
    """
    csv_path = path or get_default_csv_path()
    
    # Load existing receipts
    try:
        existing = load_receipts(csv_path)
        existing_dict = {r.id: r for r in existing}
    except FileNotFoundError:
        existing_dict = {}
    
    # Merge new receipts
    for receipt in receipts:
        existing_dict[receipt.id] = receipt
    
    # Convert back to DataFrame and save
    records = []
    for receipt in existing_dict.values():
        records.append({
            'id': receipt.id,
            'date': receipt.date.isoformat(),
            'vendor': receipt.vendor,
            'amount': float(receipt.amount),
            'category': receipt.category or '',
            'source_file': receipt.source_file or '',
            'notes': receipt.notes or '',
        })
    
    df = pd.DataFrame(records)
    df.to_csv(csv_path, index=False)


def infer_category(receipt: Receipt) -> str:
    """
    Infer expense category based on vendor name and amount.
    
    This is a simple rule-based categorizer that can be extended with:
    - ML model predictions
    - More sophisticated rules
    - User-provided mappings
    
    Args:
        receipt: Receipt object
        
    Returns:
        Inferred category string
    """
    vendor_lower = receipt.vendor.lower()
    amount = float(receipt.amount)
    
    # Tech/Electronics
    if any(word in vendor_lower for word in ['apple', 'best buy', 'amazon', 'newegg', 'microcenter']):
        return 'technology'
    
    # Food & Dining
    if any(word in vendor_lower for word in ['restaurant', 'cafe', 'coffee', 'pizza', 'burger', 'starbucks', 'mcdonalds']):
        return 'meals_entertainment'
    
    # Gas & Auto
    if any(word in vendor_lower for word in ['shell', 'chevron', 'exxon', 'mobil', 'gas', 'auto']):
        return 'auto_transport'
    
    # Office Supplies
    if any(word in vendor_lower for word in ['staples', 'office depot', 'fedex', 'ups', 'usps']):
        return 'office_supplies'
    
    # Utilities
    if any(word in vendor_lower for word in ['electric', 'power', 'gas company', 'water', 'internet', 'phone']):
        return 'utilities'
    
    # Professional Services
    if any(word in vendor_lower for word in ['consulting', 'legal', 'accounting', 'professional']):
        return 'professional_services'
    
    # Amount-based categorization
    if amount > 1000:
        return 'major_purchase'
    elif amount < 10:
        return 'miscellaneous'
    
    # Default
    return 'uncategorized'


def build_receipt_from_ocr(ocr: OCRResult) -> Receipt:
    """
    Parse receipt information from OCR text using heuristics and regex.
    
    This is a basic implementation that can be enhanced with:
    - LLM-based extraction
    - Template matching
    - ML models trained on receipt formats
    
    Args:
        ocr: OCRResult containing raw text and metadata
        
    Returns:
        Receipt object with extracted information
    """
    text = ocr.raw_text
    
    # Extract date (various formats)
    date_patterns = [
        r'(\d{1,2}/\d{1,2}/\d{2,4})',  # MM/DD/YYYY or M/D/YY
        r'(\d{4}-\d{2}-\d{2})',         # YYYY-MM-DD
        r'(\d{2}-\d{2}-\d{4})',         # DD-MM-YYYY
    ]
    
    receipt_date = date_type.today()  # Default to today
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            date_str = match.group(1)
            try:
                # Try parsing with pandas
                receipt_date = pd.to_datetime(date_str).date()
                break
            except:
                continue
    
    # Extract amount (look for currency patterns)
    amount_patterns = [
        r'\$\s*(\d+\.?\d{0,2})',        # $XX.XX or $XX
        r'total:?\s*\$?\s*(\d+\.?\d{0,2})',  # Total: $XX.XX
        r'amount:?\s*\$?\s*(\d+\.?\d{0,2})',  # Amount: $XX.XX
    ]
    
    amount = Decimal('0.00')
    for pattern in amount_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Take the largest amount found (likely the total)
            amounts = [Decimal(m.replace(',', '')) for m in matches]
            amount = max(amounts)
            break
    
    # Extract vendor (first line usually contains business name)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    vendor = lines[0] if lines else 'Unknown Vendor'
    
    # Clean vendor name (remove common OCR artifacts)
    vendor = re.sub(r'[^a-zA-Z0-9\s\-\']', '', vendor).strip()
    if not vendor:
        vendor = 'Unknown Vendor'
    
    # Generate ID from date and amount
    receipt_id = f"{receipt_date.isoformat()}_{vendor[:10]}_{amount}"
    receipt_id = re.sub(r'[^a-zA-Z0-9_-]', '_', receipt_id)
    
    # Create receipt object
    receipt = Receipt(
        id=receipt_id,
        date=receipt_date,
        vendor=vendor,
        amount=amount,
        category=None,  # Will be inferred
        source_file=ocr.metadata.get('source_file'),
        notes=f"Extracted from OCR (confidence: {ocr.confidence:.2f})"
    )
    
    # Infer category
    receipt.category = infer_category(receipt)
    
    return receipt


# Convenience functions for common operations

def add_receipt_from_ocr(ocr: OCRResult, csv_path: Optional[Path] = None) -> Receipt:
    """
    Extract receipt from OCR and add to CSV in one step.
    
    Args:
        ocr: OCRResult to process
        csv_path: Optional path to CSV file
        
    Returns:
        The created Receipt object
    """
    receipt = build_receipt_from_ocr(ocr)
    append_receipt(csv_path, receipt)
    return receipt


def get_receipts_by_category(category: str, path: Optional[Path] = None) -> list[Receipt]:
    """
    Filter receipts by category.
    
    Args:
        category: Category to filter by
        path: Optional path to CSV file
        
    Returns:
        List of receipts in the specified category
    """
    all_receipts = load_receipts(path)
    return [r for r in all_receipts if r.category == category]


def get_receipts_by_date_range(
    start_date: date_type,
    end_date: date_type,
    path: Optional[Path] = None
) -> list[Receipt]:
    """
    Filter receipts by date range.
    
    Args:
        start_date: Start of date range (inclusive)
        end_date: End of date range (inclusive)
        path: Optional path to CSV file
        
    Returns:
        List of receipts in the date range
    """
    all_receipts = load_receipts(path)
    return [
        r for r in all_receipts
        if start_date <= r.date <= end_date
    ]


def calculate_total(receipts: list[Receipt]) -> Decimal:
    """Calculate total amount across receipts."""
    return sum((r.amount for r in receipts), Decimal('0.00'))


if __name__ == '__main__':
    # Example usage
    print("Receipt Processing Module")
    print("=" * 50)
    
    # Test OCR extraction
    sample_ocr = OCRResult(
        raw_text="""
        STARBUCKS COFFEE
        123 MAIN ST
        DATE: 12/07/2025
        
        COFFEE         $5.50
        TAX            $0.45
        TOTAL:         $5.95
        
        THANK YOU!
        """,
        confidence=0.95,
        metadata={'source_file': 'receipt_001.jpg'}
    )
    
    receipt = build_receipt_from_ocr(sample_ocr)
    print(f"\nExtracted Receipt:")
    print(f"  ID: {receipt.id}")
    print(f"  Date: {receipt.date}")
    print(f"  Vendor: {receipt.vendor}")
    print(f"  Amount: ${receipt.amount}")
    print(f"  Category: {receipt.category}")
    print(f"  Notes: {receipt.notes}")
