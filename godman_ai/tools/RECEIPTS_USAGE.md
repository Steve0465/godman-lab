# Receipt Processing Module - Usage Guide

## Overview

The `godman_ai.tools.receipts` module provides a clean, typed API for managing receipt data stored in CSV files. It includes OCR integration for automatically extracting receipt information from scanned documents.

## Quick Start

```python
from godman_ai.tools import (
    Receipt,
    load_receipts,
    append_receipt,
    build_receipt_from_ocr,
    OCRResult
)
from decimal import Decimal
from datetime import date

# Load existing receipts
receipts = load_receipts()  # Uses default path from Settings
print(f"Loaded {len(receipts)} receipts")

# Create a new receipt manually
receipt = Receipt(
    id="2025-12-07_starbucks_001",
    date=date(2025, 12, 7),
    vendor="Starbucks Coffee",
    amount=Decimal("5.95"),
    category="meals_entertainment",
    source_file="receipt_001.jpg",
    notes="Morning coffee"
)

# Append to CSV
append_receipt(receipt=receipt)

# Extract from OCR
ocr_result = OCRResult(
    raw_text="""
    WALMART SUPERCENTER
    123 MAIN ST
    12/07/2025
    
    GROCERIES      $45.67
    TAX            $3.65
    TOTAL:         $49.32
    """,
    confidence=0.92,
    metadata={'source_file': 'scan_002.pdf'}
)

receipt = build_receipt_from_ocr(ocr_result)
print(f"Extracted: {receipt.vendor} - ${receipt.amount}")
print(f"Auto-categorized as: {receipt.category}")
```

## Core Models

### Receipt

```python
class Receipt(BaseModel):
    id: str                      # Unique identifier
    date: date                   # Purchase date
    vendor: str                  # Merchant name
    amount: Decimal              # Total amount
    category: Optional[str]      # Expense category
    source_file: Optional[str]   # Source document path
    notes: Optional[str]         # Additional notes
```

### OCRResult

```python
class OCRResult(BaseModel):
    raw_text: str                # OCR extracted text
    confidence: float            # Extraction confidence (0-1)
    metadata: dict               # Additional metadata
```

## Key Functions

### Loading & Saving

#### `load_receipts(path: Optional[Path] = None) -> list[Receipt]`

Load all receipts from CSV into typed models.

```python
# Use default path from Settings
receipts = load_receipts()

# Or specify custom path
from pathlib import Path
receipts = load_receipts(Path("my_receipts.csv"))
```

#### `append_receipt(path: Optional[Path] = None, receipt: Receipt = None) -> None`

Append a single receipt to the CSV. Creates file with headers if it doesn't exist.

```python
append_receipt(receipt=my_receipt)
```

#### `upsert_receipts(path: Optional[Path] = None, receipts: list[Receipt] = None) -> None`

Merge receipts by ID (update existing, insert new).

```python
# Update multiple receipts at once
upsert_receipts(receipts=[receipt1, receipt2, receipt3])
```

### OCR Integration

#### `build_receipt_from_ocr(ocr: OCRResult) -> Receipt`

Extract receipt information from OCR text using regex and heuristics.

**Current extraction capabilities:**
- **Date**: Supports MM/DD/YYYY, YYYY-MM-DD, DD-MM-YYYY formats
- **Amount**: Finds currency patterns like $XX.XX, Total: $XX.XX
- **Vendor**: Extracts from first line of text
- **Category**: Auto-inferred based on vendor name

```python
ocr = OCRResult(raw_text="...", confidence=0.95)
receipt = build_receipt_from_ocr(ocr)
```

#### `add_receipt_from_ocr(ocr: OCRResult, csv_path: Optional[Path] = None) -> Receipt`

Convenience function: extract and save in one step.

```python
receipt = add_receipt_from_ocr(ocr)
```

### Category Management

#### `infer_category(receipt: Receipt) -> str`

Auto-categorize based on vendor name and amount.

**Built-in categories:**
- `technology` - Apple, Best Buy, Amazon, etc.
- `meals_entertainment` - Restaurants, cafes, Starbucks, etc.
- `auto_transport` - Gas stations, auto services
- `office_supplies` - Staples, Office Depot, shipping
- `utilities` - Electric, water, internet, phone
- `professional_services` - Consulting, legal, accounting
- `major_purchase` - Amounts > $1000
- `miscellaneous` - Amounts < $10
- `uncategorized` - Default fallback

```python
receipt.category = infer_category(receipt)
```

**Easy to extend:**

```python
def infer_category(receipt: Receipt) -> str:
    vendor_lower = receipt.vendor.lower()
    
    # Add custom rules
    if 'my_vendor' in vendor_lower:
        return 'my_custom_category'
    
    # Or call ML model
    # return ml_model.predict(receipt.vendor, receipt.amount)
    
    # ... existing rules ...
```

### Filtering & Analysis

#### `get_receipts_by_category(category: str, path: Optional[Path] = None) -> list[Receipt]`

Filter receipts by category.

```python
meals = get_receipts_by_category('meals_entertainment')
print(f"Found {len(meals)} meal receipts")
```

#### `get_receipts_by_date_range(start_date: date, end_date: date, path: Optional[Path] = None) -> list[Receipt]`

Filter receipts by date range.

```python
from datetime import date

# Get December 2025 receipts
dec_receipts = get_receipts_by_date_range(
    start_date=date(2025, 12, 1),
    end_date=date(2025, 12, 31)
)
```

#### `calculate_total(receipts: list[Receipt]) -> Decimal`

Calculate total amount across receipts.

```python
meals = get_receipts_by_category('meals_entertainment')
total = calculate_total(meals)
print(f"Total spent on meals: ${total}")
```

## Complete Example: Tax Report

```python
from godman_ai.tools import (
    load_receipts,
    get_receipts_by_date_range,
    get_receipts_by_category,
    calculate_total
)
from datetime import date

# Load all receipts
receipts = load_receipts()

# Filter by tax year
tax_year_receipts = get_receipts_by_date_range(
    start_date=date(2025, 1, 1),
    end_date=date(2025, 12, 31)
)

# Calculate by category
categories = {}
for receipt in tax_year_receipts:
    if receipt.category:
        if receipt.category not in categories:
            categories[receipt.category] = []
        categories[receipt.category].append(receipt)

# Generate report
print("2025 Tax Summary")
print("=" * 50)
for category, receipts in sorted(categories.items()):
    total = calculate_total(receipts)
    print(f"{category:30s} ${total:>10.2f} ({len(receipts)} receipts)")

grand_total = calculate_total(tax_year_receipts)
print("=" * 50)
print(f"{'TOTAL':30s} ${grand_total:>10.2f}")
```

## Integration with OCR Pipeline

```python
from godman_ai.tools import add_receipt_from_ocr, OCRResult
from pathlib import Path
import os

# Watch a directory for new scans
scan_dir = Path("~/scans").expanduser()

for pdf_file in scan_dir.glob("*.pdf"):
    # Run OCR (pseudocode - use your OCR engine)
    ocr_text = run_ocr(pdf_file)
    
    # Create OCR result
    ocr = OCRResult(
        raw_text=ocr_text,
        confidence=0.90,
        metadata={'source_file': str(pdf_file)}
    )
    
    # Extract and save receipt
    receipt = add_receipt_from_ocr(ocr)
    print(f"✅ Processed: {receipt.vendor} - ${receipt.amount}")
    
    # Move processed file
    processed_dir = scan_dir / "processed"
    processed_dir.mkdir(exist_ok=True)
    pdf_file.rename(processed_dir / pdf_file.name)
```

## CSV Format

The module works with CSV files containing these columns:

```csv
id,date,vendor,amount,category,source_file,notes
2025-12-07_starbucks_001,2025-12-07,Starbucks Coffee,5.95,meals_entertainment,receipt_001.jpg,Morning coffee
2025-12-07_walmart_002,2025-12-07,Walmart Supercenter,49.32,uncategorized,scan_002.pdf,Extracted from OCR (confidence: 0.92)
```

## Configuration

The module uses `Settings` to get the default CSV path. To configure:

```python
# In your settings/config file
class Settings(BaseSettings):
    receipts_csv_path: str = "receipts_tax.csv"
```

Or pass explicit paths:

```python
from pathlib import Path

custom_path = Path("~/Documents/my_receipts.csv").expanduser()
receipts = load_receipts(custom_path)
append_receipt(custom_path, receipt)
```

## Future Enhancements

The module is designed to be easily extended:

1. **ML-based categorization** - Replace rule-based `infer_category()` with trained model
2. **LLM-based extraction** - Use GPT/Claude for more accurate OCR parsing
3. **Duplicate detection** - Add fuzzy matching to prevent duplicate entries
4. **Receipt validation** - Add business rules (e.g., amount > 0, vendor not empty)
5. **Multi-currency support** - Handle receipts in different currencies
6. **Tax rule engine** - Auto-calculate deductible percentages by category
7. **Audit trail** - Track changes to receipt records over time

## Testing

Run the module directly to see example usage:

```bash
python3 -m godman_ai.tools.receipts
```

Output:
```
Receipt Processing Module
==================================================

Extracted Receipt:
  ID: 2025-12-07_STARBUCKS__5_95
  Date: 2025-12-07
  Vendor: STARBUCKS COFFEE
  Amount: $5.95
  Category: meals_entertainment
  Notes: Extracted from OCR (confidence: 0.95)
```
