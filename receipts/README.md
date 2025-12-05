# Receipt Processing System

A Python system for processing receipt images using OCR and extracting structured data.

## Features

- **OCR Processing**: Uses `pytesseract` to extract text from receipt images
- **Field Extraction**: Extracts key fields including:
  - Date (normalized to YYYY-MM-DD format)
  - Vendor/merchant name
  - Subtotal
  - Tax amount
  - Total amount
  - Payment method
- **Duplicate Detection**: Prevents duplicate entries based on date + vendor + total
- **Data Storage**: Maintains a master CSV of all processed receipts
- **Text Archiving**: Saves cleaned OCR text for each receipt
- **Error Logging**: Logs errors and processing information

## Directory Structure

```
receipts/
├── process_receipts.py      # Main processing module
├── test_process_receipts.py # Unit tests
├── raw/                      # Input directory for receipt images
├── cleaned/                  # Output directory for cleaned text files
├── receipts_master.csv       # Master CSV of all receipts
└── errors.log                # Error and info logs
```

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Dependencies:
- `pytesseract` - OCR engine
- `Pillow` - Image processing
- `pandas` - CSV handling

You'll also need to install Tesseract OCR on your system:
- **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
- **macOS**: `brew install tesseract`
- **Windows**: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

## Usage

### As a Module

```python
from receipts.process_receipts import parse_receipt_text, run

# Parse receipt text
receipt_text = """
TARGET STORE
Date: 01/15/2024
Subtotal: $25.00
Tax: $2.25
Total: $27.25
Credit Card
"""

parsed = parse_receipt_text(receipt_text)
print(parsed)
# Output: {'date': '2024-01-15', 'vendor': 'TARGET STORE', ...}

# Process all images in receipts/raw/
run()
```

### Command Line

```bash
# Process all receipts in receipts/raw/
python3 -m receipts.process_receipts

# Or run directly
cd receipts && python3 process_receipts.py
```

### Workflow

1. Place receipt images (JPG, PNG, TIFF, BMP) in `receipts/raw/`
2. Run the processing system
3. Check `receipts/receipts_master.csv` for extracted data
4. Review cleaned text in `receipts/cleaned/`
5. Check `receipts/errors.log` for any issues

## Field Extraction

### Date Extraction
- Supports multiple formats: MM/DD/YYYY, YYYY-MM-DD, MM/DD/YY
- Handles month names: "Jan 15, 2024"
- Normalizes all dates to YYYY-MM-DD format
- Validates dates (rejects dates before 2000 or too far in future)

### Vendor Extraction
- Typically extracted from first few lines of receipt
- Skips common keywords (receipt, invoice, total, etc.)
- Filters out numeric-heavy lines

### Amount Extraction
- Detects subtotal, tax, and total amounts
- Handles various formats: $100.00, 100.00, 1,234.56
- Supports multiple currencies ($, €, £)
- Normalizes to two decimal places
- Falls back to largest amount if no "total" label found

### Payment Method Detection
- Detects: credit, debit, cash, check, gift card, mobile payments
- Recognizes card types: Visa, Mastercard, Amex, Discover
- Identifies mobile payments: Apple Pay, Google Pay, PayPal

## Testing

The system includes comprehensive unit tests:

```bash
# Run all tests
python3 -m unittest receipts.test_process_receipts -v

# Run specific test class
python3 -m unittest receipts.test_process_receipts.TestParseReceiptText -v

# Run specific test
python3 -m unittest receipts.test_process_receipts.TestExtractDate.test_extract_mmddyyyy_slash -v
```

Test coverage:
- 45 unit tests
- Tests all parsing functions
- Integration tests for complete receipt scenarios
- Edge case handling

## Error Handling

The system includes robust error handling:
- Logs all errors to `receipts/errors.log`
- Continues processing on individual file failures
- Validates extracted data
- Provides detailed error messages

## Output Format

### CSV Output (receipts_master.csv)

| Column | Description |
|--------|-------------|
| filename | Original image filename |
| date | Receipt date (YYYY-MM-DD) |
| vendor | Merchant/vendor name |
| subtotal | Subtotal amount |
| tax | Tax amount |
| total | Total amount |
| payment_method | Payment method used |
| processed_at | Processing timestamp |

### Cleaned Text Files

Each processed receipt generates a `.txt` file in `receipts/cleaned/` containing the raw OCR text.

## Duplicate Detection

The system prevents duplicate entries by checking:
- Receipt date
- Vendor name
- Total amount

If all three match an existing entry, the receipt is skipped.

## Limitations

- OCR accuracy depends on image quality
- Handwritten receipts may not be processed correctly
- Non-English receipts may have reduced accuracy
- Complex receipt formats may require manual review

## Future Enhancements

Potential improvements:
- Support for PDF receipts
- Machine learning-based field extraction
- Multi-language support
- Receipt image preprocessing
- Category classification
- Expense reporting integration

## License

This is part of the godman-lab personal automation repository.
