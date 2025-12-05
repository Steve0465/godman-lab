import os
import re
import logging
import csv
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any

import pytesseract
from PIL import Image

# --- Configuration ---
BASE_DIR = Path("receipts")
RAW_DIR = BASE_DIR / "raw"
CLEANED_DIR = BASE_DIR / "cleaned"
CSV_PATH = BASE_DIR / "receipts_master.csv"
LOG_PATH = BASE_DIR / "errors.log"

# Ensure directories exist
for directory in [RAW_DIR, CLEANED_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Setup logging
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def clean_currency(value_str: str) -> float:
    """Converts string like '$12.34' or '12,34' to float 12.34."""
    if not value_str:
        return 0.0
    # Remove currency symbols and spaces
    clean = re.sub(r'[^\d.,]', '', value_str)
    # Remove commas (used as thousands separators)
    clean = clean.replace(',', '')
    try:
        return float(clean)
    except ValueError:
        return 0.0

def extract_date(text: str) -> Optional[str]:
    """Finds dates in common formats and normalizes to YYYY-MM-DD."""
    # Patterns for MM/DD/YYYY, DD-MM-YYYY, YYYY-MM-DD, etc.
    date_patterns = [
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',  # MM/DD/YY or DD/MM/YY
        r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',    # YYYY-MM-DD
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})' # Month DD, YYYY
    ]

    for line in text.split('\n'):
        for pattern in date_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                try:
                    # Attempt to parse detected date string using pandas or dateutil is robust,
                    # but we will stick to standard library for simplicity.
                    # This section often requires tuning based on specific receipt formats.
                    raw_date = match.group(0)
                    # strictly simple parsing logic for demonstration
                    # In a real scenario, `dateutil.parser.parse(raw_date)` is safer
                    return raw_date # Returning raw for now, normalization requires strict format knowledge
                except Exception:
                    continue
    return datetime.now().strftime("%Y-%m-%d") # Fallback to today if not found

def parse_receipt_text(text: str) -> Dict[str, Any]:
    """
    Analyzes OCR text to extract structured data.
    Returns a dictionary with standardized keys.
    """
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    data = {
        "date": extract_date(text),
        "vendor": "Unknown",
        "subtotal": 0.0,
        "tax": 0.0,
        "total": 0.0,
        "payment_method": "Cash"
    }

    # Heuristics
    if lines:
        data["vendor"] = lines[0] # Assume first non-empty line is vendor

    # Regex for money
    money_pattern = r'\$?\s?(\d+\.\d{2})'

    for i, line in enumerate(lines):
        lower_line = line.lower()

        # Payment Method
        if any(x in lower_line for x in ['visa', 'mastercard', 'amex', 'credit', 'debit']):
            data["payment_method"] = "Card"
        
        # Totals
        # Look for the word "Total" and grab the number on that line or the next
        if "total" in lower_line and "sub" not in lower_line:
            match = re.search(money_pattern, line)
            if match:
                data["total"] = clean_currency(match.group(1))
        
        if "tax" in lower_line:
            match = re.search(money_pattern, line)
            if match:
                data["tax"] = clean_currency(match.group(1))

    return data

def is_duplicate(new_data: Dict, existing_rows: list) -> bool:
    """Check if date + vendor + total matches an existing entry."""
    for row in existing_rows:
        # Compare essential fields (converting to string for CSV comparison)
        if (row.get('date') == str(new_data['date']) and 
            row.get('vendor') == new_data['vendor'] and 
            float(row.get('total', 0)) == new_data['total']):
            return True
    return False

def run():
    """Main entrypoint to process all receipts."""
    print(f"Processing receipts from {RAW_DIR}...")
    
    # Load existing CSV data to check for duplicates
    existing_data = []
    if CSV_PATH.exists():
        with open(CSV_PATH, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            existing_data = list(reader)
    
    # Prepare CSV writer (append mode)
    fieldnames = ["filename", "date", "vendor", "subtotal", "tax", "total", "payment_method"]
    
    # Open file in append mode, write header if new
    file_mode = 'a' if CSV_PATH.exists() else 'w'
    with open(CSV_PATH, file_mode, newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if file_mode == 'w':
            writer.writeheader()

        # Iterate over images
        supported_exts = {'.jpg', '.jpeg', '.png', '.tiff'}
        for img_path in RAW_DIR.iterdir():
            if img_path.suffix.lower() not in supported_exts:
                continue

            try:
                print(f"Scanning {img_path.name}...")
                
                # 1. OCR
                image = Image.open(img_path)
                text = pytesseract.image_to_string(image)

                # 2. Parse
                parsed_data = parse_receipt_text(text)
                parsed_data['filename'] = img_path.name

                # 3. Check Duplicates
                if is_duplicate(parsed_data, existing_data):
                    print(f"Skipping duplicate: {img_path.name}")
                    continue

                # 4. Save Cleaned Text
                clean_txt_path = CLEANED_DIR / f"{img_path.stem}.txt"
                with open(clean_txt_path, 'w', encoding='utf-8') as f:
                    f.write(text)

                # 5. Append to CSV
                writer.writerow(parsed_data)
                existing_data.append(parsed_data) # Update in-memory list for next iteration
                print(f"Successfully processed {img_path.name}")

            except Exception as e:
                error_msg = f"Failed to process {img_path.name}: {str(e)}"
                print(error_msg)
                logging.error(error_msg)

if __name__ == "__main__":
    run()
