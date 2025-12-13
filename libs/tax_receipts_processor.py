"""
Tax Receipts Processor - Integrates OCR and Tax Categorization Engine

Provides end-to-end receipt processing: PDF text extraction, field parsing,
and automatic tax categorization.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, date
import csv
import re

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("Warning: PyMuPDF not available. Install with: pip install PyMuPDF")

from libs.tax_category_rules import classify_receipt


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract text from a PDF file using PyMuPDF.
    
    Falls back to OCR placeholder if text extraction yields insufficient content.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Extracted text as a string
        
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        RuntimeError: If PyMuPDF is not available
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    if not PYMUPDF_AVAILABLE:
        raise RuntimeError("PyMuPDF is not installed. Cannot extract text from PDF.")
    
    try:
        doc = fitz.open(pdf_path)
        text_parts = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text:
                text_parts.append(text)
        
        doc.close()
        
        full_text = "\n".join(text_parts)
        
        # If text is too short, might need OCR
        if len(full_text.strip()) < 20:
            return f"[OCR_NEEDED] Insufficient text extracted from {pdf_path.name}"
        
        return full_text
    
    except Exception as e:
        return f"[ERROR] Failed to extract text: {str(e)}"


def extract_vendor(text: str) -> str:
    """
    Extract vendor name from receipt text using heuristics.
    
    Strategy:
    1. Look for known vendor patterns
    2. Check first few capitalized lines
    3. Return normalized vendor name or "Unknown"
    
    Args:
        text: Receipt text content
        
    Returns:
        Normalized vendor name
    """
    if not text or text.startswith("[OCR_NEEDED]") or text.startswith("[ERROR]"):
        return "Unknown"
    
    text_lower = text.lower()
    lines = text.split("\n")
    
    # Known vendor patterns (in priority order)
    vendor_patterns = [
        # Building Materials & Hardware
        (r"\bhome\s*depot\b", "Home Depot"),
        (r"\blowe'?s\b", "Lowe's"),
        (r"\bmenards\b", "Menards"),
        (r"\b84\s*lumber\b", "84 Lumber"),
        (r"\btractor\s*supply\b", "Tractor Supply"),
        
        # Pool Suppliers
        (r"\bscp\b", "SCP"),
        (r"\bleslie'?s\s*pool\b", "Leslie's Pool"),
        (r"\bpinch\s*a\s*penny\b", "Pinch A Penny"),
        (r"\bpoolcorp\b", "PoolCorp"),
        
        # Tools & Equipment
        (r"\bharbor\s*freight\b", "Harbor Freight"),
        (r"\bnorthern\s*tool\b", "Northern Tool"),
        (r"\broll\s*n\s*vac\b", "Roll N Vac"),
        (r"\broll-n-vac\b", "Roll N Vac"),
        (r"\bgrainger\b", "Grainger"),
        
        # Equipment Rental
        (r"\bu-?haul\b", "U-Haul"),
        (r"\bsunbelt\s*rentals\b", "Sunbelt Rentals"),
        (r"\bunited\s*rentals\b", "United Rentals"),
        
        # Gas Stations & Fuel
        (r"\bshell\b", "Shell"),
        (r"\bexxon\b", "Exxon"),
        (r"\bchevron\b", "Chevron"),
        (r"\bbp\b", "BP"),
        (r"\bquiktrip\b", "QuikTrip"),
        (r"\bqt\b", "QT"),
        (r"\bracetrac\b", "RaceTrac"),
        (r"\bcircle\s*k\b", "Circle K"),
        (r"\bmarathon\b", "Marathon"),
        (r"\bvalero\b", "Valero"),
        
        # Auto Parts
        (r"\bautozone\b", "AutoZone"),
        (r"\bo'?reilly\b", "O'Reilly"),
        (r"\badvance\s*auto\b", "Advance Auto"),
        (r"\bnapa\b", "NAPA"),
        
        # Office Supplies
        (r"\bstaples\b", "Staples"),
        (r"\boffice\s*depot\b", "Office Depot"),
        (r"\boffice\s*max\b", "Office Max"),
        (r"\bfedex\s*office\b", "FedEx Office"),
        (r"\bups\s*store\b", "UPS Store"),
        
        # Restaurants & Food
        (r"\bmcdonald'?s\b", "McDonald's"),
        (r"\bsubway\b", "Subway"),
        (r"\bchick-fil-a\b", "Chick-fil-A"),
        (r"\bpanera\b", "Panera"),
        (r"\bchipotle\b", "Chipotle"),
        (r"\bstarbucks\b", "Starbucks"),
        (r"\bdunkin\b", "Dunkin"),
        (r"\bwaffle\s*house\b", "Waffle House"),
        
        # General Retail (Ambiguous)
        (r"\bwalmart\b", "Walmart"),
        (r"\btarget\b", "Target"),
        (r"\bkroger\b", "Kroger"),
        (r"\bpublix\b", "Publix"),
        (r"\bsafeway\b", "Safeway"),
        (r"\bwhole\s*foods\b", "Whole Foods"),
        (r"\bcvs\b", "CVS"),
        (r"\bwalgreens\b", "Walgreens"),
        (r"\bamazon\b", "Amazon"),
        (r"\bcostco\b", "Costco"),
        (r"\bsam'?s\s*club\b", "Sam's Club"),
    ]
    
    # Try pattern matching first
    for pattern, vendor_name in vendor_patterns:
        if re.search(pattern, text_lower):
            return vendor_name
    
    # Fallback: Look for first capitalized line that looks like a business name
    for line in lines[:10]:  # Check first 10 lines
        line = line.strip()
        if not line:
            continue
        
        # Skip lines that are obviously not vendor names
        if any(skip in line.lower() for skip in ["receipt", "invoice", "date", "time", "page"]):
            continue
        
        # Look for lines with multiple capital letters (likely business names)
        if len(line) >= 3 and sum(1 for c in line if c.isupper()) >= 2:
            # Clean up the line
            vendor = re.sub(r'[^\w\s-]', '', line).strip()
            if len(vendor) >= 3:
                return vendor[:50]  # Limit length
    
    return "Unknown"


def extract_amount(text: str) -> float:
    """
    Extract total amount from receipt text.
    
    Looks for common patterns like:
    - "Total: $XX.XX"
    - "Amount Due: XX.XX"
    - "Balance: $XX.XX"
    - Last dollar amount in text
    
    Args:
        text: Receipt text content
        
    Returns:
        Extracted amount as float, or 0.0 if not found
    """
    if not text or text.startswith("[OCR_NEEDED]") or text.startswith("[ERROR]"):
        return 0.0
    
    text_lower = text.lower()
    
    # Patterns for total amount (in priority order)
    amount_patterns = [
        r"total[:\s]+\$?\s*(\d+[,\d]*\.?\d{0,2})",
        r"amount\s+(?:due|paid)[:\s]+\$?\s*(\d+[,\d]*\.?\d{0,2})",
        r"balance[:\s]+\$?\s*(\d+[,\d]*\.?\d{0,2})",
        r"grand\s+total[:\s]+\$?\s*(\d+[,\d]*\.?\d{0,2})",
        r"total\s+due[:\s]+\$?\s*(\d+[,\d]*\.?\d{0,2})",
        r"sale\s+total[:\s]+\$?\s*(\d+[,\d]*\.?\d{0,2})",
    ]
    
    # Try specific patterns first
    for pattern in amount_patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        if matches:
            # Get the last match (often the final total)
            amount_str = matches[-1].replace(",", "")
            try:
                return float(amount_str)
            except ValueError:
                continue
    
    # Fallback: Find all dollar amounts and take the largest one
    # This assumes the total is usually the largest amount on the receipt
    all_amounts = re.findall(r'\$?\s*(\d+[,\d]*\.\d{2})\b', text)
    if all_amounts:
        amounts_float = []
        for amt in all_amounts:
            try:
                amounts_float.append(float(amt.replace(",", "")))
            except ValueError:
                continue
        
        if amounts_float:
            # Return the largest amount (likely the total)
            return max(amounts_float)
    
    return 0.0


def extract_date(text: str) -> Optional[date]:
    """
    Extract date from receipt text.
    
    Supports common formats:
    - MM/DD/YYYY
    - MM-DD-YYYY
    - Month DD, YYYY
    
    Args:
        text: Receipt text content
        
    Returns:
        Extracted date or None if not found
    """
    if not text or text.startswith("[OCR_NEEDED]") or text.startswith("[ERROR]"):
        return None
    
    # Date patterns (in priority order)
    date_patterns = [
        # MM/DD/YYYY or MM-DD-YYYY
        (r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', '%m/%d/%Y'),
        # YYYY-MM-DD
        (r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', '%Y-%m-%d'),
        # Month DD, YYYY
        (r'(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{1,2}),?\s+(\d{4})', '%B %d %Y'),
    ]
    
    for pattern, date_format in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            for match in matches:
                try:
                    if date_format == '%m/%d/%Y':
                        month, day, year = match
                        date_str = f"{month}/{day}/{year}"
                    elif date_format == '%Y-%m-%d':
                        year, month, day = match
                        date_str = f"{year}-{month}-{day}"
                    elif date_format == '%B %d %Y':
                        month_str, day, year = match
                        date_str = f"{month_str} {day} {year}"
                    
                    parsed_date = datetime.strptime(date_str, date_format).date()
                    
                    # Sanity check: date should be reasonable (2000-2030)
                    if 2000 <= parsed_date.year <= 2030:
                        return parsed_date
                except (ValueError, TypeError):
                    continue
    
    return None


def extract_tax_year(text: str) -> int:
    """
    Extract tax year from OCR text by finding date patterns.
    
    Scans for various date formats and extracts the year:
    - MM/DD/YY or MM/DD/YYYY
    - YYYY-MM-DD
    - MM-DD-YY or MM-DD-YYYY
    - Month DD, YYYY
    - Month DD, YY
    
    Two-digit years are normalized:
    - 00-49 → 2000-2049
    - 50-99 → 1950-1999
    
    If multiple years are found, prefers the one nearest to today.
    Falls back to current year if no valid year is found.
    
    Args:
        text: OCR text content
        
    Returns:
        Tax year (4-digit integer)
    """
    if not text or text.startswith("[OCR_NEEDED]") or text.startswith("[ERROR]"):
        return datetime.now().year
    
    current_year = datetime.now().year
    found_years = []
    
    # Pattern 1: 4-digit years (YYYY-MM-DD, YYYY/MM/DD, or standalone)
    four_digit_years = re.findall(r'\b(20\d{2}|19\d{2})\b', text)
    for year_str in four_digit_years:
        year = int(year_str)
        if 1990 <= year <= current_year + 10:
            found_years.append(year)
    
    # Pattern 2: MM/DD/YY or MM-DD-YY (2-digit year)
    two_digit_dates = re.findall(r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2})\b', text)
    for month, day, year_str in two_digit_dates:
        year_int = int(year_str)
        # Normalize 2-digit year: 00-49 → 2000s, 50-99 → 1900s
        if year_int <= 49:
            year = 2000 + year_int
        else:
            year = 1900 + year_int
        
        # Sanity check: reasonable year range for tax purposes
        if 1990 <= year <= current_year + 10:
            found_years.append(year)
    
    # Pattern 3: Month DD, YYYY or Month DD, YY
    month_day_year = re.findall(
        r'\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
        r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|'
        r'Dec(?:ember)?)\s+(\d{1,2}),?\s+(\d{2,4})\b',
        text,
        re.IGNORECASE
    )
    for month, day, year_str in month_day_year:
        year_int = int(year_str)
        
        # Handle 2-digit years
        if year_int < 100:
            if year_int <= 49:
                year = 2000 + year_int
            else:
                year = 1900 + year_int
        else:
            year = year_int
        
        # Sanity check: reasonable year range for tax purposes
        if 1990 <= year <= current_year + 10:
            found_years.append(year)
    
    # If no years found, return current year
    if not found_years:
        return current_year
    
    # If multiple years found, prefer the one nearest to today
    if len(found_years) > 1:
        # Remove duplicates and sort
        unique_years = sorted(set(found_years))
        # Find year closest to current year
        closest_year = min(unique_years, key=lambda y: abs(y - current_year))
        return closest_year
    
    # Return the only year found
    return found_years[0]


def process_receipt(pdf_path: Path) -> Dict[str, Any]:
    """
    Process a single receipt PDF: extract text, parse fields, and classify.
    
    Args:
        pdf_path: Path to receipt PDF file
        
    Returns:
        Dictionary with all extracted and classified information:
            - date: Receipt date
            - vendor: Vendor name
            - amount: Receipt total
            - category: Tax category
            - subcategory: Tax subcategory
            - deductible_amount: Deductible amount
            - deductibility_rate: Deductibility rate
            - needs_review: Whether manual review is needed
            - confidence: Classification confidence
            - reason: Classification reason
            - source_file: Source PDF filename
    """
    result = {
        "date": None,
        "vendor": "Unknown",
        "amount": 0.0,
        "category": "Unknown",
        "subcategory": None,
        "deductible_amount": 0.0,
        "deductibility_rate": 0.0,
        "needs_review": True,
        "confidence": 0.0,
        "reason": "Processing failed",
        "source_file": pdf_path.name
    }
    
    try:
        # Step 1: Extract text from PDF
        text = extract_text_from_pdf(pdf_path)
        
        # Step 2: Extract fields
        vendor = extract_vendor(text)
        amount = extract_amount(text)
        receipt_date = extract_date(text)
        
        # Step 3: Classify receipt
        classification = classify_receipt(vendor, text, amount)
        
        # Step 4: Compile results
        result.update({
            "date": receipt_date.isoformat() if receipt_date else None,
            "vendor": classification.vendor,
            "amount": amount,
            "category": classification.category,
            "subcategory": classification.subcategory,
            "deductible_amount": classification.deductible_amount,
            "deductibility_rate": classification.deductibility_rate,
            "needs_review": classification.needs_review,
            "confidence": classification.confidence,
            "reason": classification.reason,
        })
        
    except Exception as e:
        result["reason"] = f"Error processing receipt: {str(e)}"
    
    return result


def process_all_receipts(year_path: Path, output_csv: Path) -> Dict[str, Any]:
    """
    Process all receipts in a year directory and export to CSV.
    
    Args:
        year_path: Path to year directory (should contain "Receipts" subfolder)
        output_csv: Path to output CSV file
        
    Returns:
        Dictionary with processing statistics:
            - total_receipts: Number of receipts processed
            - successful: Number successfully processed
            - failed: Number that failed
            - total_amount: Total receipt amounts
            - total_deductible: Total deductible amount
            - needs_review_count: Number needing review
    """
    receipts_dir = year_path / "Receipts"
    
    if not receipts_dir.exists():
        raise FileNotFoundError(f"Receipts directory not found: {receipts_dir}")
    
    # Find all PDF files
    pdf_files = list(receipts_dir.glob("*.pdf")) + list(receipts_dir.glob("*.PDF"))
    
    if not pdf_files:
        print(f"Warning: No PDF files found in {receipts_dir}")
        return {
            "total_receipts": 0,
            "successful": 0,
            "failed": 0,
            "total_amount": 0.0,
            "total_deductible": 0.0,
            "needs_review_count": 0
        }
    
    # Process each receipt
    results = []
    stats = {
        "total_receipts": len(pdf_files),
        "successful": 0,
        "failed": 0,
        "total_amount": 0.0,
        "total_deductible": 0.0,
        "needs_review_count": 0
    }
    
    for pdf_file in sorted(pdf_files):
        print(f"Processing: {pdf_file.name}...", end=" ")
        
        try:
            result = process_receipt(pdf_file)
            results.append(result)
            
            # Update stats
            if result["category"] != "Unknown" or result["amount"] > 0:
                stats["successful"] += 1
            else:
                stats["failed"] += 1
            
            stats["total_amount"] += result["amount"]
            stats["total_deductible"] += result["deductible_amount"]
            
            if result["needs_review"]:
                stats["needs_review_count"] += 1
            
            print(f"✓ {result['category']} | ${result['deductible_amount']:.2f}")
            
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            stats["failed"] += 1
    
    # Write results to CSV
    if results:
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = [
            "source_file",
            "date",
            "vendor",
            "amount",
            "category",
            "subcategory",
            "deductible_amount",
            "deductibility_rate",
            "needs_review",
            "confidence",
            "reason"
        ]
        
        with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        print(f"\n✓ Results written to: {output_csv}")
    
    return stats


def generate_summary_report(csv_path: Path) -> str:
    """
    Generate a summary report from processed receipts CSV.
    
    Args:
        csv_path: Path to receipts CSV file
        
    Returns:
        Formatted summary report as string
    """
    if not csv_path.exists():
        return f"CSV file not found: {csv_path}"
    
    # Read CSV
    receipts = []
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        receipts = list(reader)
    
    if not receipts:
        return "No receipts found in CSV file."
    
    # Calculate statistics
    total_receipts = len(receipts)
    total_amount = sum(float(r.get("amount", 0)) for r in receipts)
    total_deductible = sum(float(r.get("deductible_amount", 0)) for r in receipts)
    needs_review = sum(1 for r in receipts if r.get("needs_review", "False") == "True")
    avg_confidence = sum(float(r.get("confidence", 0)) for r in receipts) / total_receipts if total_receipts > 0 else 0
    
    # Category breakdown
    categories = {}
    for receipt in receipts:
        category = receipt.get("category", "Unknown")
        if category not in categories:
            categories[category] = {"count": 0, "deductible": 0.0}
        categories[category]["count"] += 1
        categories[category]["deductible"] += float(receipt.get("deductible_amount", 0))
    
    # Build report
    lines = [
        "=" * 80,
        "TAX RECEIPTS PROCESSING SUMMARY",
        "=" * 80,
        f"Total Receipts: {total_receipts}",
        f"Total Amount: ${total_amount:,.2f}",
        f"Total Deductible: ${total_deductible:,.2f}",
        f"Needs Review: {needs_review} ({needs_review/total_receipts*100:.1f}%)",
        f"Average Confidence: {avg_confidence:.2f}",
        "",
        "Category Breakdown:",
        "-" * 80,
    ]
    
    for category in sorted(categories.keys()):
        data = categories[category]
        lines.append(f"  {category:30s} {data['count']:4d} receipts  ${data['deductible']:12,.2f}")
    
    lines.extend([
        "=" * 80,
    ])
    
    return "\n".join(lines)


def process_year(year: int, archive_root: Path) -> None:
    """
    Convenience function to process all receipts for a specific year.
    
    Args:
        year: Tax year to process
        archive_root: Root path of TAX_MASTER_ARCHIVE
    """
    year_path = archive_root / "data" / str(year)
    output_csv = archive_root / "data" / str(year) / f"receipts_{year}.csv"
    
    print(f"\n{'=' * 80}")
    print(f"Processing Receipts for {year}")
    print(f"{'=' * 80}\n")
    
    stats = process_all_receipts(year_path, output_csv)
    
    print(f"\n{'=' * 80}")
    print(f"Processing Complete")
    print(f"{'=' * 80}")
    print(f"Total Receipts: {stats['total_receipts']}")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print(f"Total Amount: ${stats['total_amount']:,.2f}")
    print(f"Total Deductible: ${stats['total_deductible']:,.2f}")
    print(f"Needs Review: {stats['needs_review_count']}")
    
    # Generate and display summary
    if output_csv.exists():
        print("\n" + generate_summary_report(output_csv))


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        year = int(sys.argv[1])
        archive_root = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(".")
        process_year(year, archive_root)
    else:
        print("Usage: python tax_receipts_processor.py <year> [archive_root]")
        print("Example: python tax_receipts_processor.py 2024 /data/TAX_MASTER_ARCHIVE")
