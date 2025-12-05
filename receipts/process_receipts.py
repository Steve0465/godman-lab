#!/usr/bin/env python3
"""
Receipt Processing System

This module processes receipt images using OCR, extracts key fields,
and maintains a master CSV of all processed receipts.
"""

import os
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List

import pytesseract
from PIL import Image
import pandas as pd


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('receipts/errors.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Directory paths
RAW_DIR = Path('receipts/raw')
CLEANED_DIR = Path('receipts/cleaned')
MASTER_CSV = Path('receipts/receipts_master.csv')


def parse_receipt_text(text: str) -> Dict[str, Optional[str]]:
    """
    Parse receipt text and extract key fields using regex and heuristics.
    
    Args:
        text: Raw OCR text from receipt
        
    Returns:
        Dictionary containing extracted fields:
        - date: Receipt date in YYYY-MM-DD format
        - vendor: Vendor/merchant name
        - subtotal: Subtotal amount as string
        - tax: Tax amount as string
        - total: Total amount as string
        - payment_method: Payment method used
    """
    result = {
        'date': None,
        'vendor': None,
        'subtotal': None,
        'tax': None,
        'total': None,
        'payment_method': None
    }
    
    if not text or not text.strip():
        return result
    
    # Extract date
    result['date'] = _extract_date(text)
    
    # Extract vendor (usually first non-empty line)
    result['vendor'] = _extract_vendor(text)
    
    # Extract amounts
    amounts = _extract_amounts(text)
    result['subtotal'] = amounts.get('subtotal')
    result['tax'] = amounts.get('tax')
    result['total'] = amounts.get('total')
    
    # Extract payment method
    result['payment_method'] = _extract_payment_method(text)
    
    return result


def _extract_date(text: str) -> Optional[str]:
    """
    Extract and normalize date from receipt text.
    
    Returns date in YYYY-MM-DD format or None if not found.
    """
    # Date patterns to search for
    patterns = [
        # MM/DD/YYYY or MM-DD-YYYY
        r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b',
        # YYYY/MM/DD or YYYY-MM-DD
        r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b',
        # MM/DD/YY or MM-DD-YY
        r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2})\b',
        # Month DD, YYYY (e.g., "Jan 15, 2024")
        r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2}),?\s+(\d{4})\b',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                groups = match.groups()
                
                # Handle different date formats
                if len(groups) == 3:
                    if re.match(r'^\d{4}$', groups[0]):  # YYYY-MM-DD format
                        year, month, day = groups
                        date_obj = datetime(int(year), int(month), int(day))
                    elif groups[0].isalpha():  # Month name format
                        month_str, day, year = groups
                        month_map = {
                            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
                            'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
                            'sep': 9, 'sept': 9, 'oct': 10, 'nov': 11, 'dec': 12
                        }
                        month = month_map.get(month_str.lower()[:3])
                        if month:
                            date_obj = datetime(int(year), month, int(day))
                        else:
                            continue
                    else:  # MM/DD/YYYY or MM/DD/YY format
                        month, day, year = groups
                        if len(year) == 2:
                            year = '20' + year if int(year) < 50 else '19' + year
                        date_obj = datetime(int(year), int(month), int(day))
                    
                    # Validate date is reasonable (not in future, not too old)
                    if 2000 <= date_obj.year <= datetime.now().year + 1:
                        return date_obj.strftime('%Y-%m-%d')
            except (ValueError, AttributeError):
                continue
    
    return None


def _extract_vendor(text: str) -> Optional[str]:
    """
    Extract vendor name from receipt text.
    
    Typically the vendor name is in the first few lines of the receipt.
    """
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if not lines:
        return None
    
    # Skip common receipt keywords to find actual vendor name
    skip_keywords = [
        'receipt', 'invoice', 'tax', 'total', 'subtotal', 
        'date', 'time', 'amount', 'payment', 'card', 'cash'
    ]
    
    for line in lines[:10]:  # Check first 10 lines
        lower_line = line.lower()
        # Skip if line contains common keywords or is too short
        if len(line) < 3 or any(keyword in lower_line for keyword in skip_keywords):
            continue
        # Skip if line is mostly numbers or special characters
        if sum(c.isalpha() for c in line) < len(line) * 0.3:
            continue
        return line[:100]  # Return first valid line, truncated
    
    return lines[0][:100] if lines else None


def _extract_amounts(text: str) -> Dict[str, Optional[str]]:
    """
    Extract monetary amounts (subtotal, tax, total) from receipt text.
    
    Returns dictionary with 'subtotal', 'tax', and 'total' keys.
    """
    amounts = {
        'subtotal': None,
        'tax': None,
        'total': None
    }
    
    # Split text into lines for line-by-line analysis
    lines = text.split('\n')
    
    # Pattern to match currency amounts (1-2 decimal places, or no decimals)
    amount_pattern = r'[\$€£]?\s*(\d{1,6}(?:[,]\d{3})*(?:\.\d{1,2})?)'
    
    for line in lines:
        lower_line = line.lower()
        
        # Extract total
        if 'total' in lower_line and amounts['total'] is None:
            # Prefer lines with "total" that aren't "subtotal"
            if 'subtotal' not in lower_line:
                matches = re.findall(amount_pattern, line)
                if matches:
                    # Take the last amount on the line (usually the total)
                    amounts['total'] = _normalize_amount(matches[-1])
        
        # Extract subtotal
        if 'subtotal' in lower_line or 'sub total' in lower_line:
            matches = re.findall(amount_pattern, line)
            if matches:
                amounts['subtotal'] = _normalize_amount(matches[-1])
        
        # Extract tax
        if 'tax' in lower_line:
            matches = re.findall(amount_pattern, line)
            if matches:
                amounts['tax'] = _normalize_amount(matches[-1])
    
    # If no total found, try to find largest amount in text
    if amounts['total'] is None:
        all_amounts = re.findall(amount_pattern, text)
        if all_amounts:
            try:
                amounts_float = [float(a.replace(',', '')) for a in all_amounts]
                amounts['total'] = _normalize_amount(str(max(amounts_float)))
            except ValueError:
                pass
    
    return amounts


def _normalize_amount(amount_str: str) -> Optional[str]:
    """
    Normalize amount string to float format.
    
    Args:
        amount_str: Amount string (may contain commas, currency symbols)
        
    Returns:
        Normalized amount as string or None if invalid
    """
    # Handle None input
    if amount_str is None:
        return None
    
    try:
        # Remove currency symbols and commas
        cleaned = amount_str.replace('$', '').replace('€', '').replace('£', '').replace(',', '').strip()
        value = float(cleaned)
        return f"{value:.2f}"
    except (ValueError, AttributeError):
        return None


def _extract_payment_method(text: str) -> Optional[str]:
    """
    Extract payment method from receipt text.
    """
    text_lower = text.lower()
    
    # Payment method keywords
    payment_methods = {
        'credit': ['credit', 'credit card', 'visa', 'mastercard', 'amex', 'discover'],
        'debit': ['debit', 'debit card'],
        'cash': ['cash', 'currency'],
        'check': ['check', 'cheque'],
        'gift_card': ['gift card', 'gift-card'],
        'mobile': ['apple pay', 'google pay', 'samsung pay', 'paypal', 'venmo'],
    }
    
    for method, keywords in payment_methods.items():
        if any(keyword in text_lower for keyword in keywords):
            return method
    
    return None


def _process_receipt_image(image_path: Path) -> Optional[str]:
    """
    Process a single receipt image with OCR.
    
    Args:
        image_path: Path to receipt image file
        
    Returns:
        Extracted text from image or None if processing fails
    """
    try:
        logger.info(f"Processing image: {image_path.name}")
        
        # Open and process image
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Run OCR
            text = pytesseract.image_to_string(img, lang='eng')
            
        return text
    
    except Exception as e:
        logger.error(f"Error processing image {image_path}: {e}")
        return None


def _save_cleaned_text(filename: str, text: str) -> None:
    """
    Save cleaned OCR text to file.
    
    Args:
        filename: Original image filename
        text: Cleaned text to save
    """
    try:
        # Create cleaned filename (replace extension with .txt)
        cleaned_filename = Path(filename).stem + '.txt'
        cleaned_path = CLEANED_DIR / cleaned_filename
        
        with open(cleaned_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        logger.info(f"Saved cleaned text to: {cleaned_path}")
    
    except Exception as e:
        logger.error(f"Error saving cleaned text for {filename}: {e}")


def _is_duplicate(record: Dict, existing_df: pd.DataFrame) -> bool:
    """
    Check if a receipt is a duplicate based on date, vendor, and total.
    
    Args:
        record: New receipt record to check
        existing_df: DataFrame of existing receipts
        
    Returns:
        True if duplicate found, False otherwise
    """
    if existing_df.empty:
        return False
    
    date = record.get('date')
    vendor = record.get('vendor')
    total = record.get('total')
    
    # Check for exact match on date, vendor, and total
    duplicates = existing_df[
        (existing_df['date'] == date) &
        (existing_df['vendor'] == vendor) &
        (existing_df['total'].astype(str) == str(total))
    ]
    
    return len(duplicates) > 0


def _load_existing_receipts() -> pd.DataFrame:
    """
    Load existing receipts from master CSV.
    
    Returns:
        DataFrame of existing receipts or empty DataFrame if file doesn't exist
    """
    if MASTER_CSV.exists():
        try:
            return pd.read_csv(MASTER_CSV)
        except Exception as e:
            logger.error(f"Error loading existing receipts: {e}")
            return pd.DataFrame()
    return pd.DataFrame()


def run() -> None:
    """
    Main entrypoint for receipt processing system.
    
    Processes all images in receipts/raw/, extracts data, and updates master CSV.
    """
    logger.info("Starting receipt processing system")
    
    # Ensure directories exist
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load existing receipts for duplicate detection
    existing_receipts = _load_existing_receipts()
    logger.info(f"Loaded {len(existing_receipts)} existing receipts")
    
    # Get all image files from raw directory
    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'}
    image_files = [
        f for f in RAW_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in image_extensions
    ]
    
    if not image_files:
        logger.info("No images found in receipts/raw/")
        return
    
    logger.info(f"Found {len(image_files)} images to process")
    
    # Process each image
    new_records = []
    processed_count = 0
    skipped_count = 0
    error_count = 0
    
    for image_path in image_files:
        try:
            # Run OCR
            text = _process_receipt_image(image_path)
            
            if text is None:
                error_count += 1
                continue
            
            # Parse receipt text
            parsed_data = parse_receipt_text(text)
            
            # Create record with filename
            record = {
                'filename': image_path.name,
                'date': parsed_data['date'],
                'vendor': parsed_data['vendor'],
                'subtotal': parsed_data['subtotal'],
                'tax': parsed_data['tax'],
                'total': parsed_data['total'],
                'payment_method': parsed_data['payment_method'],
                'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Check for duplicates
            if _is_duplicate(record, existing_receipts):
                logger.info(f"Skipping duplicate: {image_path.name}")
                skipped_count += 1
                continue
            
            # Save cleaned text
            _save_cleaned_text(image_path.name, text)
            
            # Add to new records
            new_records.append(record)
            processed_count += 1
            logger.info(f"Successfully processed: {image_path.name}")
        
        except Exception as e:
            logger.error(f"Unexpected error processing {image_path.name}: {e}")
            error_count += 1
    
    # Update master CSV if we have new records
    if new_records:
        new_df = pd.DataFrame(new_records)
        
        if not existing_receipts.empty:
            # Append to existing
            combined_df = pd.concat([existing_receipts, new_df], ignore_index=True)
        else:
            combined_df = new_df
        
        # Save to CSV
        try:
            MASTER_CSV.parent.mkdir(parents=True, exist_ok=True)
            combined_df.to_csv(MASTER_CSV, index=False)
            logger.info(f"Saved {len(new_records)} new receipts to {MASTER_CSV}")
        except Exception as e:
            logger.error(f"Error saving master CSV: {e}")
    
    # Print summary
    logger.info("=" * 50)
    logger.info("Processing complete!")
    logger.info(f"Processed: {processed_count}")
    logger.info(f"Skipped (duplicates): {skipped_count}")
    logger.info(f"Errors: {error_count}")
    logger.info("=" * 50)


if __name__ == '__main__':
    run()
