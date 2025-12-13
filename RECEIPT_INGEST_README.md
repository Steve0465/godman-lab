# Receipt Ingest with Dynamic Year Routing

## Overview

The `receipt_ingest()` function provides end-to-end receipt processing with automatic year-based routing to the TAX_MASTER_ARCHIVE structure.

## Features

✅ **Automatic Year Detection** - Extracts tax year from OCR text using `extract_tax_year()`  
✅ **Dynamic Path Building** - Creates year-specific folder structure  
✅ **Auto-Folder Creation** - Creates all necessary directories automatically  
✅ **Complete Archival** - Saves OCR text and moves PDF to archive  
✅ **CSV Integration** - Appends receipt data to year-specific CSV  
✅ **Workflow Logging** - Returns comprehensive result with routing info  

## Function Signature

```python
from godman_ai.tools import receipt_ingest

result = receipt_ingest(
    pdf_path: Path,              # Path to receipt PDF
    ocr_text: str,               # OCR extracted text
    base_archive: Path = None    # Optional: defaults to ~/Desktop/TAX_MASTER_ARCHIVE
) -> Dict[str, Any]
```

## Usage Example

```python
from pathlib import Path
from godman_ai.tools import receipt_ingest

# Process a receipt
result = receipt_ingest(
    pdf_path=Path("/path/to/receipt.pdf"),
    ocr_text="HOME DEPOT\nDate: 05/15/2024\nTotal: $169.28"
)

# Check result
if result['success']:
    print(f"✓ Receipt routed to year: {result['year']}")
    print(f"  CSV: {result['paths']['receipts_csv']}")
    print(f"  Receipt: {result['receipt'].vendor} - ${result['receipt'].amount}")
else:
    print(f"✗ Error: {result['message']}")
```

## Return Value Structure

```python
{
    'success': bool,          # True if ingestion succeeded
    'year': int,              # Extracted tax year (for logging)
    'paths': {                # All dynamically built paths
        'year_base': str,                    # e.g., ~/Desktop/TAX_MASTER_ARCHIVE/2024
        'receipts_csv': str,                 # e.g., .../2024/receipts_tax.csv
        'receipts_processed_dir': str,       # e.g., .../2024/Receipts/processed/
        'ocr_dir': str                       # e.g., .../2024/OCR_TEXT/receipts/
    },
    'receipt': Receipt,       # Extracted receipt object (or None if failed)
    'message': str            # Status message for logging
}
```

## Archive Structure

The function creates this structure automatically:

```
~/Desktop/TAX_MASTER_ARCHIVE/
├── 2024/
│   ├── receipts_tax.csv               # Year-specific CSV
│   ├── Receipts/
│   │   └── processed/                 # Processed PDFs
│   │       └── receipt_20240515.pdf
│   └── OCR_TEXT/
│       └── receipts/                  # OCR text files
│           └── receipt_20240515.txt
├── 2023/
│   ├── receipts_tax.csv
│   ├── Receipts/processed/...
│   └── OCR_TEXT/receipts/...
└── 2025/
    └── ...
```

## Workflow Integration

The return value provides complete logging information:

```python
# Log workflow execution
print(f"Year routing decision: {result['year']}")
print(f"Status: {result['message']}")
print(f"Paths created:")
for key, path in result['paths'].items():
    print(f"  {key}: {path}")

if result['receipt']:
    r = result['receipt']
    print(f"Receipt details: {r.vendor} | ${r.amount} | {r.date} | {r.category}")
```

## Year Detection

The function uses `extract_tax_year()` which:

- Scans OCR text for date patterns (MM/DD/YY, YYYY-MM-DD, Month DD YYYY, etc.)
- Normalizes 2-digit years (23 → 2023, 25 → 2025)
- Returns the year nearest to today if multiple found
- Falls back to current year if no dates detected

## Error Handling

The function handles errors gracefully:

```python
result = receipt_ingest(pdf_path, ocr_text)

if not result['success']:
    print(f"Error: {result['message']}")
    # Possible errors:
    # - Failed to create directories
    # - Failed to save OCR text
    # - Failed to move PDF
    # - Failed to process receipt data
```

## Files Modified

- `godman_ai/tools/receipts.py` - Added `receipt_ingest()` function
- `godman_ai/tools/__init__.py` - Added export
- `libs/tax_receipts_processor.py` - Contains `extract_tax_year()` helper

## Testing

Run the test suite:

```bash
cd /Users/stephengodman/Desktop/godman-lab
source .venv_release/bin/activate
python3 -c "from godman_ai.tools import receipt_ingest; print('✓ Import successful')"
```

## Related Functions

- `extract_tax_year(text: str) -> int` - Extract year from OCR text
- `build_receipt_from_ocr(ocr: OCRResult) -> Receipt` - Parse receipt data
- `append_receipt(path, receipt)` - Append receipt to CSV

## Notes

- PDFs are **moved** (not copied) to the archive
- OCR text is saved alongside the PDF for future reference
- Each year has its own `receipts_tax.csv` file
- All directories are created automatically with `mkdir(parents=True, exist_ok=True)`
- The function is idempotent - safe to call multiple times
