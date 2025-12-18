"""
Memphis Pool bill totals extractor.

Extracts ONE payable total per bill from OCR text using smart heuristics.
Does NOT sum all amounts - identifies the most likely "AMOUNT DUE" line.

Input:
- data/memphis_pool/bills_text/*.txt (OCR text)
- data/memphis_pool/indexes/bills_text_index.csv (optional metadata)

Output:
- data/memphis_pool/indexes/bills_payables.csv (one total per bill)
- data/memphis_pool/indexes/bills_amounts_debug.csv (debug info)

Usage:
    python3 libs/memphis_pool_bill_totals.py
"""

from __future__ import annotations

import csv
import re
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional


# Money regex: $1,234.56 or $100 or $ 50.00
MONEY_PATTERN = re.compile(r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?')


def parse_money(money_str: str) -> float:
    """Parse money string to float.
    
    Args:
        money_str: String like "$1,234.56" or "$ 50.00"
        
    Returns:
        Float value
    """
    cleaned = money_str.replace('$', '').replace(',', '').replace(' ', '')
    return float(cleaned)


def extract_date_from_filename(filename: str) -> str:
    """Extract date from filename.
    
    Patterns:
    1. Xerox Scan_MMDDYYYYHHMMSS.pdf -> YYYY-MM-DD
    2. "May 27 mp bill.pdf" -> 2025-05-27 (assume current year)
    3. "July 22 Mp Bill.pdf" -> 2025-07-22
    
    Args:
        filename: Bill filename
        
    Returns:
        ISO date string (YYYY-MM-DD) or empty string
    """
    # Pattern 1: Xerox Scan_MMDDYYYYHHMMSS
    xerox_match = re.search(r'(\d{2})(\d{2})(\d{4})\d{6}', filename)
    if xerox_match:
        month, day, year = xerox_match.groups()
        try:
            date_obj = datetime(int(year), int(month), int(day))
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            pass
    
    # Pattern 2: "Month Day" format (e.g., "May 27", "July 22")
    month_names = {
        'january': 1, 'jan': 1,
        'february': 2, 'feb': 2,
        'march': 3, 'mar': 3,
        'april': 4, 'apr': 4,
        'may': 5,
        'june': 6, 'jun': 6,
        'july': 7, 'jul': 7,
        'august': 8, 'aug': 8,
        'september': 9, 'sep': 9, 'sept': 9,
        'october': 10, 'oct': 10,
        'november': 11, 'nov': 11,
        'december': 12, 'dec': 12,
    }
    
    for month_name, month_num in month_names.items():
        pattern = rf'\b{month_name}\s+(\d{{1,2}})\b'
        match = re.search(pattern, filename.lower())
        if match:
            day = int(match.group(1))
            # Assume current year (2025 for bills in 2025 directory)
            year = 2025
            try:
                date_obj = datetime(year, month_num, day)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                pass
    
    return ''


def find_all_amounts(lines: List[str]) -> List[Tuple[int, float, str]]:
    """Find all dollar amounts in text lines.
    
    Args:
        lines: List of text lines
        
    Returns:
        List of (line_no, amount, line_text) tuples
    """
    amounts = []
    
    for line_no, line in enumerate(lines, 1):
        matches = MONEY_PATTERN.findall(line)
        for match in matches:
            try:
                amount = parse_money(match)
                amounts.append((line_no, amount, line.strip()))
            except ValueError:
                continue
    
    return amounts


def extract_payable_total(
    text_path: Path
) -> Tuple[Optional[float], str, str, str, bool]:
    """Extract the most likely payable total from a bill text file.
    
    Heuristics (priority order):
    1. Lines with "amount due", "total due", "balance due", etc. (high confidence)
    2. Lines with "total" but not "subtotal" (medium confidence)
    3. Largest amount in last 25% of document (low confidence)
    
    Args:
        text_path: Path to bill text file
        
    Returns:
        Tuple of (amount, evidence_line, evidence_rule, confidence, needs_review)
    """
    with open(text_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    if not lines:
        return None, '', 'no_text', 'low', True
    
    # Rule 1: High-priority keywords (high confidence)
    high_priority_keywords = [
        'amount due',
        'total due',
        'balance due',
        'amount owed',
        'total amount due',
        'payment due',
    ]
    
    for line_no, line in enumerate(lines, 1):
        line_lower = line.lower()
        for keyword in high_priority_keywords:
            if keyword in line_lower:
                # Extract FIRST dollar amount on this line
                matches = MONEY_PATTERN.findall(line)
                if matches:
                    try:
                        amount = parse_money(matches[0])
                        if amount > 0:  # Ignore $0 unless it's the only option
                            evidence = line.strip()[:200]
                            return amount, evidence, f'keyword:{keyword}', 'high', False
                    except ValueError:
                        continue
    
    # Rule 2: "total" keywords, but NOT "subtotal" (medium confidence)
    total_keywords = [
        'invoice total',
        'total amount',
        'grand total',
    ]
    
    # Also check lines that START with "total"
    for line_no, line in enumerate(lines, 1):
        line_lower = line.lower().strip()
        
        # Check explicit keywords
        for keyword in total_keywords:
            if keyword in line_lower and 'subtotal' not in line_lower:
                matches = MONEY_PATTERN.findall(line)
                if matches:
                    try:
                        amount = parse_money(matches[0])
                        if amount > 0:
                            evidence = line.strip()[:200]
                            return amount, evidence, f'keyword:{keyword}', 'medium', False
                    except ValueError:
                        continue
        
        # Check lines starting with "total"
        if line_lower.startswith('total') and 'subtotal' not in line_lower:
            matches = MONEY_PATTERN.findall(line)
            if matches:
                try:
                    amount = parse_money(matches[0])
                    if amount > 0:
                        evidence = line.strip()[:200]
                        return amount, evidence, 'keyword:total_line_start', 'medium', False
                except ValueError:
                    continue
    
    # Rule 3: Largest amount in last 25% of document (low confidence)
    last_quarter_start = int(len(lines) * 0.75)
    last_quarter_lines = lines[last_quarter_start:]
    
    amounts_in_last_quarter = []
    for line_no_offset, line in enumerate(last_quarter_lines):
        line_no = last_quarter_start + line_no_offset + 1
        matches = MONEY_PATTERN.findall(line)
        for match in matches:
            try:
                amount = parse_money(match)
                if amount > 0:
                    amounts_in_last_quarter.append((amount, line.strip(), line_no))
            except ValueError:
                continue
    
    if amounts_in_last_quarter:
        # Get largest amount
        amounts_in_last_quarter.sort(reverse=True)
        amount, line_text, line_no = amounts_in_last_quarter[0]
        evidence = line_text[:200]
        return amount, evidence, 'heuristic:largest_in_last_quarter', 'low', True
    
    # Rule 4: Fallback - largest amount anywhere in document (very low confidence)
    all_amounts = find_all_amounts(lines)
    if all_amounts:
        all_amounts.sort(key=lambda x: x[1], reverse=True)
        line_no, amount, line_text = all_amounts[0]
        if amount > 0:
            evidence = line_text[:200]
            return amount, evidence, 'fallback:largest_amount', 'low', True
    
    # No amounts found
    return None, '', 'no_amounts_found', 'low', True


def build_payables_index(
    text_dir: Path,
    out_payables_csv: Path,
    out_debug_csv: Path
) -> None:
    """Build payables index from bill text files.
    
    Args:
        text_dir: Directory containing bill text files
        out_payables_csv: Output CSV for payables (one per bill)
        out_debug_csv: Output CSV for debug info (all amounts)
    """
    text_dir = Path(text_dir)
    out_payables_csv = Path(out_payables_csv)
    out_debug_csv = Path(out_debug_csv)
    
    out_payables_csv.parent.mkdir(parents=True, exist_ok=True)
    out_debug_csv.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*70}")
    print(f"EXTRACTING BILL PAYABLE TOTALS")
    print(f"{'='*70}")
    print(f"Input: {text_dir}")
    print(f"Output (payables): {out_payables_csv}")
    print(f"Output (debug): {out_debug_csv}")
    print(f"{'='*70}\n")
    
    text_files = sorted(text_dir.glob("*.txt"))
    
    if not text_files:
        print("⚠️  No text files found")
        return
    
    print(f"Processing {len(text_files)} text files...\n")
    
    payables_rows = []
    debug_rows = []
    
    for idx, text_path in enumerate(text_files, 1):
        bill_file = text_path.stem + '.pdf'  # Convert .txt back to .pdf
        
        print(f"[{idx}/{len(text_files)}] {text_path.name[:50]}...", end=" ")
        
        # Extract date from filename
        bill_date = extract_date_from_filename(text_path.name)
        
        # Extract payable total
        amount, evidence, rule, confidence, needs_review = extract_payable_total(text_path)
        
        if amount is not None:
            status = "✓"
            if needs_review:
                status = "⚠️ "
            print(f"{status} ${amount:,.2f} ({confidence}, {rule})")
            
            payables_rows.append({
                'bill_file': bill_file,
                'bill_date': bill_date,
                'candidate_total': f"${amount:,.2f}",
                'currency': 'USD',
                'evidence_line': evidence,
                'evidence_rule': rule,
                'confidence': confidence,
                'needs_review': str(needs_review).lower()
            })
        else:
            print(f"❌ No amounts found")
            payables_rows.append({
                'bill_file': bill_file,
                'bill_date': bill_date,
                'candidate_total': '',
                'currency': 'USD',
                'evidence_line': '',
                'evidence_rule': rule,
                'confidence': confidence,
                'needs_review': 'true'
            })
        
        # Build debug info (all amounts in this file)
        with open(text_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        all_amounts = find_all_amounts(lines)
        for line_no, amt, line_text in all_amounts:
            # Check if this line matches any rule
            line_lower = line_text.lower()
            rule_match = ''
            
            # Check high-priority keywords
            for keyword in ['amount due', 'total due', 'balance due', 'amount owed']:
                if keyword in line_lower:
                    rule_match = f'HIGH:{keyword}'
                    break
            
            # Check medium-priority keywords
            if not rule_match:
                for keyword in ['invoice total', 'total amount', 'grand total']:
                    if keyword in line_lower and 'subtotal' not in line_lower:
                        rule_match = f'MEDIUM:{keyword}'
                        break
            
            # Check if line starts with "total"
            if not rule_match and line_lower.strip().startswith('total') and 'subtotal' not in line_lower:
                rule_match = 'MEDIUM:total_line_start'
            
            # Check if in last quarter
            if not rule_match:
                last_quarter_start = int(len(lines) * 0.75)
                if line_no > last_quarter_start:
                    rule_match = 'LOW:last_quarter'
            
            debug_rows.append({
                'bill_file': bill_file,
                'line_no': line_no,
                'amount': f"${amt:,.2f}",
                'line_text': line_text[:200],
                'rule_match': rule_match
            })
    
    # Write payables CSV
    payables_fieldnames = [
        'bill_file', 'bill_date', 'candidate_total', 'currency',
        'evidence_line', 'evidence_rule', 'confidence', 'needs_review'
    ]
    
    with open(out_payables_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=payables_fieldnames)
        writer.writeheader()
        writer.writerows(payables_rows)
    
    # Write debug CSV
    debug_fieldnames = ['bill_file', 'line_no', 'amount', 'line_text', 'rule_match']
    
    with open(out_debug_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=debug_fieldnames)
        writer.writeheader()
        writer.writerows(debug_rows)
    
    # Summary
    print(f"\n{'='*70}")
    print(f"PAYABLE TOTALS SUMMARY")
    print(f"{'='*70}")
    
    success_count = sum(1 for r in payables_rows if r['candidate_total'])
    review_count = sum(1 for r in payables_rows if r['needs_review'] == 'true')
    
    high_conf = sum(1 for r in payables_rows if r['confidence'] == 'high')
    medium_conf = sum(1 for r in payables_rows if r['confidence'] == 'medium')
    low_conf = sum(1 for r in payables_rows if r['confidence'] == 'low')
    
    print(f"✓ Bills processed: {len(payables_rows)}")
    print(f"✓ Totals extracted: {success_count}")
    print(f"⚠️  Needs review: {review_count}")
    print()
    print(f"Confidence breakdown:")
    print(f"  🟢 High: {high_conf}")
    print(f"  🟡 Medium: {medium_conf}")
    print(f"  🔴 Low: {low_conf}")
    print()
    
    # Calculate total
    total_sum = 0.0
    for row in payables_rows:
        if row['candidate_total']:
            try:
                amount = parse_money(row['candidate_total'])
                total_sum += amount
            except:
                pass
    
    print(f"💰 Total payables sum: ${total_sum:,.2f}")
    print(f"{'='*70}\n")


def main():
    """Run payable totals extraction."""
    
    print("=" * 70)
    print("MEMPHIS POOL BILL PAYABLE TOTALS EXTRACTION")
    print("=" * 70)
    print()
    
    # Setup paths
    data_root = Path("data/memphis_pool")
    text_dir = data_root / "bills_text"
    indexes_dir = data_root / "indexes"
    
    payables_csv = indexes_dir / "bills_payables.csv"
    debug_csv = indexes_dir / "bills_amounts_debug.csv"
    
    print(f"Text directory: {text_dir}")
    print(f"Payables CSV: {payables_csv}")
    print(f"Debug CSV: {debug_csv}")
    print("=" * 70)
    
    # Check prerequisites
    if not text_dir.exists():
        print(f"❌ Text directory not found: {text_dir}")
        print("\nRun this first:")
        print("  python3 libs/memphis_pool_bills.py --local-pdf-dir <pdf_dir>")
        return
    
    try:
        # Extract payables
        build_payables_index(text_dir, payables_csv, debug_csv)
        
        # Final summary
        print("✅ EXTRACTION COMPLETE")
        print(f"Output files:")
        print(f"  - {payables_csv}")
        print(f"  - {debug_csv}")
        print()
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
