#!/usr/bin/env python3
"""
Test script for Memphis Pool bills processing.

Usage:
    export TRELLO_KEY="your_key"
    export TRELLO_TOKEN="your_token"
    
    python3 test_memphis_bills.py
"""

import sys
from pathlib import Path

# Add libs to path
sys.path.insert(0, str(Path(__file__).parent / "libs"))

from memphis_pool_bills import (
    safe_filename,
    sha256_file,
    extract_text_from_pdf,
    build_bills_line_candidates,
)


def test_safe_filename():
    """Test safe filename generation."""
    print("Testing safe_filename()...")
    
    test_cases = [
        ("Invoice #123 (Final).pdf", "Invoice_123_Final.pdf"),
        ("Scan 11/19/2025.pdf", "Scan_11192025.pdf"),
        ("Bill & Receipt.pdf", "Bill_Receipt.pdf"),
        ("Normal_File.pdf", "Normal_File.pdf"),
        ("Multiple   Spaces.pdf", "Multiple_Spaces.pdf"),
    ]
    
    for input_name, expected in test_cases:
        result = safe_filename(input_name)
        status = "✓" if result == expected else "❌"
        print(f"  {status} {input_name!r} -> {result!r} (expected {expected!r})")
    
    print()


def test_dollar_pattern():
    """Test dollar amount regex pattern."""
    import re
    
    print("Testing dollar amount regex...")
    
    dollar_pattern = re.compile(r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?')
    
    test_cases = [
        ("Total: $100", ["$100"]),
        ("Amount due: $1,234.56", ["$1,234.56"]),
        ("Price $ 5000 today", ["$ 5000"]),
        ("Pay $12,345.00 by Friday", ["$12,345.00"]),
        ("$50 or $100", ["$50", "$100"]),
        ("No amounts here", []),
        ("100 dollars", []),  # No $ symbol
        ("Cost: $5.00, Tax: $0.45", ["$5.00", "$0.45"]),
    ]
    
    for text, expected in test_cases:
        matches = dollar_pattern.findall(text)
        status = "✓" if matches == expected else "❌"
        print(f"  {status} {text!r}")
        print(f"     Found: {matches}")
        print(f"     Expected: {expected}")
    
    print()


def test_text_extraction():
    """Test PDF text extraction (if test PDF available)."""
    print("Testing PDF text extraction...")
    
    # Check if we have any PDFs to test with
    test_pdf_dir = Path("data/memphis_pool/raw_bills")
    
    if not test_pdf_dir.exists():
        print("  ⚠️  No test PDFs available (run full pipeline first)")
        print()
        return
    
    pdf_files = list(test_pdf_dir.glob("*.pdf"))[:3]  # Test first 3
    
    if not pdf_files:
        print("  ⚠️  No PDF files found")
        print()
        return
    
    for pdf_path in pdf_files:
        print(f"  Testing: {pdf_path.name}")
        try:
            text, page_count = extract_text_from_pdf(pdf_path)
            print(f"    ✓ Extracted {len(text)} chars from {page_count} pages")
            
            # Show sample
            if text:
                sample = text[:100].replace('\n', ' ')
                print(f"    Sample: {sample}...")
            
            # Check if likely scanned
            if len(text) < 50:
                print(f"    ⚠️  Likely scanned (< 50 chars)")
        
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    print()


def test_sha256():
    """Test SHA256 file hashing."""
    print("Testing SHA256 file hashing...")
    
    # Create a test file
    test_file = Path("/tmp/test_sha256.txt")
    test_content = "Hello, Memphis Pool!"
    
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    hash1 = sha256_file(test_file)
    hash2 = sha256_file(test_file)
    
    print(f"  Hash: {hash1}")
    print(f"  ✓ Consistent: {hash1 == hash2}")
    print(f"  ✓ Length: {len(hash1)} chars (expected 64)")
    
    test_file.unlink()
    print()


def test_line_candidates():
    """Test building line candidates from text files."""
    print("Testing line candidates generation...")
    
    # Check if we have text files
    text_dir = Path("data/memphis_pool/bills_text")
    
    if not text_dir.exists() or not list(text_dir.glob("*.txt")):
        print("  ⚠️  No text files available (run full pipeline first)")
        print()
        return
    
    # Build line candidates to temp file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        temp_csv = Path(f.name)
    
    try:
        build_bills_line_candidates(text_dir, temp_csv)
        
        # Check output
        if temp_csv.exists():
            import csv
            with open(temp_csv) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            print(f"  ✓ Generated {len(rows)} line candidates")
            
            if rows:
                print(f"  Sample:")
                for row in rows[:3]:
                    print(f"    {row['amount']} in {row['pdf_file']} (line {row['line_no']})")
        
        temp_csv.unlink()
    
    except Exception as e:
        print(f"  ❌ Error: {e}")
        if temp_csv.exists():
            temp_csv.unlink()
    
    print()


def main():
    """Run all tests."""
    print("=" * 70)
    print("Testing Memphis Pool Bills Module")
    print("=" * 70)
    print()
    
    test_safe_filename()
    test_dollar_pattern()
    test_sha256()
    test_text_extraction()
    test_line_candidates()
    
    print("=" * 70)
    print("✅ Tests complete!")
    print("=" * 70)
    print()
    print("To run full pipeline:")
    print("  python3 libs/memphis_pool_bills.py")
    print()


if __name__ == "__main__":
    main()
