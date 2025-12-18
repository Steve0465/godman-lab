"""
Memphis Pool bill line items extractor and totals calculator.

Extracts individual line items from bills and computes totals by summing them.
Excludes subtotals, totals, and other non-item amounts transparently.

Input:
- data/memphis_pool/bills_text/*.txt (OCR text)

Output:
- data/memphis_pool/indexes/bill_items.csv (all line items with exclusions)
- data/memphis_pool/indexes/bill_totals_summed.csv (computed totals per bill)
- data/memphis_pool/indexes/billing_summary_for_memphis_pool.txt (plain text summary)

Usage:
    python3 libs/memphis_pool_bill_items.py
"""

from __future__ import annotations

import csv
import re
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional


# Money regex patterns
DOLLAR_SIGN_PATTERN = re.compile(r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?')
PLAIN_DECIMAL_PATTERN = re.compile(r'\b\d{1,3}(?:,\d{3})*\.\d{2}\b')

# Job/service keywords that suggest nearby numbers are monetary amounts
JOB_KEYWORDS = [
    'cover', 'install', 'anchor', 'service', 'liner', 'repair', 
    'replacement', 'maintenance', 'clean', 'measure', 'snap',
    'skimmer', 'pump', 'filter', 'heater', 'light', 'tile',
    'coping', 'deck', 'concrete', 'plaster', 'resurface',
    'warranty', 'labor', 'material', 'equipment', 'chemical',
    'delivery', 'haul', 'removed', 'pulled', 'reset'
]

# Exclusion keywords (do NOT include in sum)
EXCLUSION_KEYWORDS = [
    'subtotal',
    'sub-total',
    'sub total',
    'total',
    'amount due',
    'balance due',
    'due',
    'paid',
    'payment',
    'deposit',
    'credit',
    'balance forward',
    'previous balance',
    'prev balance',
    'balance',
]


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


def check_exclusion_keywords(line_text: str) -> Optional[str]:
    """Check if line contains exclusion keywords.
    
    Args:
        line_text: Line of text to check
        
    Returns:
        Keyword that matched, or None if no match
    """
    line_lower = line_text.lower().strip()
    
    for keyword in EXCLUSION_KEYWORDS:
        if keyword in line_lower:
            return keyword
    
    return None


def has_job_keywords(line_text: str) -> bool:
    """Check if line contains job/service keywords.
    
    Args:
        line_text: Line of text to check
        
    Returns:
        True if line contains job keywords
    """
    line_lower = line_text.lower()
    
    for keyword in JOB_KEYWORDS:
        if keyword in line_lower:
            return True
    
    return False


def is_valid_money_amount(amount: float) -> bool:
    """Check if amount is likely a monetary value.
    
    Args:
        amount: Float value to check
        
    Returns:
        True if amount looks like money (between 10.00 and 10000.00)
    """
    return 10.00 <= amount <= 10000.00


def extract_line_items(text_path: Path) -> Tuple[List[dict], str]:
    """Extract all line items from bill text.
    
    Args:
        text_path: Path to bill text file
        
    Returns:
        Tuple of (list of line item dicts, bill_date)
    """
    bill_file = text_path.stem + '.pdf'
    bill_date = extract_date_from_filename(text_path.name)
    
    with open(text_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    items = []
    processed_amounts = set()  # Track (line_no, amount) to avoid duplicates
    
    for line_no, line in enumerate(lines, 1):
        line_text = line.strip()
        
        # Strategy 1: Find dollar sign amounts (priority)
        dollar_matches = DOLLAR_SIGN_PATTERN.findall(line)
        
        for match in dollar_matches:
            try:
                amount = parse_money(match)
                amount_key = (line_no, amount)
                
                if amount_key in processed_amounts:
                    continue
                
                processed_amounts.add(amount_key)
                
                # Check for exclusion keywords
                exclude_keyword = check_exclusion_keywords(line_text)
                
                # Determine item type and exclusion
                if exclude_keyword:
                    item_type = 'excluded'
                    exclude_reason = f'keyword:{exclude_keyword}'
                elif amount == 0.0:
                    item_type = 'excluded'
                    exclude_reason = 'zero_amount'
                elif amount < 0:
                    item_type = 'excluded'
                    exclude_reason = 'negative_amount'
                else:
                    item_type = 'line_item'
                    exclude_reason = ''
                
                items.append({
                    'bill_file': bill_file,
                    'bill_date': bill_date,
                    'line_no': line_no,
                    'amount': amount,
                    'amount_str': f"${amount:,.2f}",
                    'line_text': line_text[:200],  # Cap at 200 chars
                    'item_type': item_type,
                    'exclude_reason': exclude_reason,
                    'amount_source': 'dollar_sign'
                })
            except ValueError:
                continue
        
        # Strategy 2: Find plain decimal amounts (only if no dollar sign found on this line)
        if not dollar_matches:
            plain_matches = PLAIN_DECIMAL_PATTERN.findall(line)
            
            for match in plain_matches:
                try:
                    amount = parse_money(match)
                    amount_key = (line_no, amount)
                    
                    if amount_key in processed_amounts:
                        continue
                    
                    # Filter: only accept if amount is in valid range
                    if not is_valid_money_amount(amount):
                        continue
                    
                    # Filter: prefer lines with job keywords
                    has_keywords = has_job_keywords(line_text)
                    
                    processed_amounts.add(amount_key)
                    
                    # Check for exclusion keywords
                    exclude_keyword = check_exclusion_keywords(line_text)
                    
                    # Determine item type and exclusion
                    if exclude_keyword:
                        item_type = 'excluded'
                        exclude_reason = f'keyword:{exclude_keyword}'
                    elif amount == 0.0:
                        item_type = 'excluded'
                        exclude_reason = 'zero_amount'
                    elif amount < 0:
                        item_type = 'excluded'
                        exclude_reason = 'negative_amount'
                    elif not has_keywords:
                        # Low confidence without job keywords
                        item_type = 'line_item'
                        exclude_reason = ''  # Include but mark source
                    else:
                        item_type = 'line_item'
                        exclude_reason = ''
                    
                    items.append({
                        'bill_file': bill_file,
                        'bill_date': bill_date,
                        'line_no': line_no,
                        'amount': amount,
                        'amount_str': f"${amount:,.2f}",
                        'line_text': line_text[:200],  # Cap at 200 chars
                        'item_type': item_type,
                        'exclude_reason': exclude_reason,
                        'amount_source': 'plain_decimal'
                    })
                except ValueError:
                    continue
    
    return items, bill_date


def compute_bill_total(items: List[dict], bill_file: str, bill_date: str) -> dict:
    """Compute bill total by summing line items.
    
    Args:
        items: List of line item dicts
        bill_file: Bill filename
        bill_date: Bill date
        
    Returns:
        Dict with bill total info
    """
    # Separate included vs excluded items
    included_items = [item for item in items if item['item_type'] == 'line_item']
    excluded_items = [item for item in items if item['item_type'] == 'excluded']
    
    # Calculate sum
    sum_amount = sum(item['amount'] for item in included_items)
    
    # Check for needs_review conditions
    needs_review = False
    notes = []
    
    # Condition 1: Has any "total" style exclusions (might be double-counting)
    total_style_exclusions = [
        item for item in excluded_items
        if 'total' in item['exclude_reason'] or 'due' in item['exclude_reason']
    ]
    if total_style_exclusions:
        needs_review = True
        notes.append(f"has_{len(total_style_exclusions)}_total_lines")
    
    # Condition 2: High item count (> 20)
    if len(included_items) > 20:
        needs_review = True
        notes.append("high_item_count")
    
    # Condition 3: High sum (> $5,000)
    if sum_amount > 5000:
        needs_review = True
        notes.append("high_sum_amount")
    
    # Condition 4: No items found
    if len(included_items) == 0:
        needs_review = True
        notes.append("no_items_found")
    
    return {
        'bill_file': bill_file,
        'bill_date': bill_date,
        'item_count': len(included_items),
        'sum_amount': f"${sum_amount:,.2f}",
        'sum_amount_raw': sum_amount,
        'excluded_count': len(excluded_items),
        'notes': ';'.join(notes) if notes else '',
        'needs_review': str(needs_review).lower()
    }


def build_line_items_index(
    text_dir: Path,
    out_items_csv: Path,
    out_totals_csv: Path,
    out_summary_txt: Path
) -> None:
    """Build line items index and compute totals.
    
    Args:
        text_dir: Directory containing bill text files
        out_items_csv: Output CSV for line items
        out_totals_csv: Output CSV for bill totals
        out_summary_txt: Output text file for summary
    """
    text_dir = Path(text_dir)
    out_items_csv = Path(out_items_csv)
    out_totals_csv = Path(out_totals_csv)
    out_summary_txt = Path(out_summary_txt)
    
    out_items_csv.parent.mkdir(parents=True, exist_ok=True)
    out_totals_csv.parent.mkdir(parents=True, exist_ok=True)
    out_summary_txt.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*70}")
    print(f"EXTRACTING BILL LINE ITEMS AND COMPUTING TOTALS")
    print(f"{'='*70}")
    print(f"Input: {text_dir}")
    print(f"Output (items): {out_items_csv}")
    print(f"Output (totals): {out_totals_csv}")
    print(f"Output (summary): {out_summary_txt}")
    print(f"{'='*70}\n")
    
    text_files = sorted(text_dir.glob("*.txt"))
    
    if not text_files:
        print("⚠️  No text files found")
        return
    
    print(f"Processing {len(text_files)} text files...\n")
    
    all_items = []
    all_totals = []
    
    for idx, text_path in enumerate(text_files, 1):
        bill_file = text_path.stem + '.pdf'
        
        print(f"[{idx}/{len(text_files)}] {text_path.name[:50]}...", end=" ")
        
        # Extract line items
        items, bill_date = extract_line_items(text_path)
        
        # Compute total
        total = compute_bill_total(items, bill_file, bill_date)
        
        # Display summary
        included_count = total['item_count']
        excluded_count = total['excluded_count']
        sum_amount = total['sum_amount']
        needs_review = total['needs_review']
        
        status = "✓"
        if needs_review == 'true':
            status = "⚠️ "
        
        print(f"{status} {included_count} items, {sum_amount} (excluded: {excluded_count})")
        
        # Store results
        all_items.extend(items)
        all_totals.append(total)
    
    # Write items CSV
    items_fieldnames = [
        'bill_file', 'bill_date', 'line_no', 'amount',
        'line_text', 'item_type', 'exclude_reason', 'amount_source'
    ]
    
    with open(out_items_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=items_fieldnames)
        writer.writeheader()
        for item in all_items:
            writer.writerow({
                'bill_file': item['bill_file'],
                'bill_date': item['bill_date'],
                'line_no': item['line_no'],
                'amount': item['amount_str'],
                'line_text': item['line_text'],
                'item_type': item['item_type'],
                'exclude_reason': item['exclude_reason'],
                'amount_source': item.get('amount_source', 'dollar_sign')
            })
    
    # Write totals CSV
    totals_fieldnames = [
        'bill_file', 'bill_date', 'item_count', 'sum_amount',
        'excluded_count', 'notes', 'needs_review'
    ]
    
    with open(out_totals_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=totals_fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(all_totals)
    
    # Write summary text file
    with open(out_summary_txt, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("MEMPHIS POOL BILLS - BILLING SUMMARY\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Bills: {len(all_totals)}\n")
        f.write("=" * 80 + "\n\n")
        
        # Sort by date
        sorted_totals = sorted(all_totals, key=lambda x: x['bill_date'] or '9999-99-99')
        
        for total in sorted_totals:
            date_str = total['bill_date'] or 'NO-DATE'
            file_str = total['bill_file']
            items_str = f"items={total['item_count']}"
            amount_str = f"total={total['sum_amount']}"
            review_str = f"needs_review={total['needs_review']}"
            
            line = f"{date_str} | {file_str:45} | {items_str:12} | {amount_str:20} | {review_str}"
            f.write(line + "\n")
        
        # Summary statistics
        total_billed = sum(t['sum_amount_raw'] for t in all_totals)
        total_items = sum(t['item_count'] for t in all_totals)
        total_excluded = sum(t['excluded_count'] for t in all_totals)
        needs_review_count = sum(1 for t in all_totals if t['needs_review'] == 'true')
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("SUMMARY STATISTICS\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total Billed Amount:    ${total_billed:,.2f}\n")
        f.write(f"Total Line Items:       {total_items}\n")
        f.write(f"Total Excluded Items:   {total_excluded}\n")
        f.write(f"Bills Needing Review:   {needs_review_count}/{len(all_totals)}\n")
        f.write("=" * 80 + "\n")
    
    # Summary
    print(f"\n{'='*70}")
    print(f"LINE ITEMS & TOTALS SUMMARY")
    print(f"{'='*70}")
    
    total_bills = len(all_totals)
    total_items = sum(t['item_count'] for t in all_totals)
    total_excluded = sum(t['excluded_count'] for t in all_totals)
    total_billed = sum(t['sum_amount_raw'] for t in all_totals)
    needs_review_count = sum(1 for t in all_totals if t['needs_review'] == 'true')
    
    print(f"✓ Bills processed: {total_bills}")
    print(f"✓ Total line items: {total_items}")
    print(f"✓ Total excluded items: {total_excluded}")
    print(f"⚠️  Bills needing review: {needs_review_count}")
    print()
    print(f"💰 Total billed amount: ${total_billed:,.2f}")
    print()
    
    # Breakdown by amount source
    source_counts = {'dollar_sign': 0, 'plain_decimal': 0}
    for item in all_items:
        if item['item_type'] == 'line_item':
            source = item.get('amount_source', 'dollar_sign')
            source_counts[source] = source_counts.get(source, 0) + 1
    
    print(f"Amount source breakdown:")
    print(f"  - Dollar sign ($): {source_counts['dollar_sign']}")
    print(f"  - Plain decimal: {source_counts['plain_decimal']}")
    print()
    
    # Breakdown by exclusion reason
    exclusion_counts = {}
    for item in all_items:
        if item['item_type'] == 'excluded':
            reason = item['exclude_reason']
            exclusion_counts[reason] = exclusion_counts.get(reason, 0) + 1
    
    if exclusion_counts:
        print(f"Exclusion breakdown:")
        for reason, count in sorted(exclusion_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {reason}: {count}")
        print()
    
    # Top bills by amount
    top_bills = sorted(all_totals, key=lambda x: x['sum_amount_raw'], reverse=True)[:5]
    print(f"Top 5 bills by amount:")
    for i, bill in enumerate(top_bills, 1):
        review_flag = " ⚠️" if bill['needs_review'] == 'true' else ""
        print(f"  {i}. {bill['sum_amount']:>12} - {bill['bill_file'][:40]}{review_flag}")
    
    print(f"{'='*70}\n")


def main():
    """Run line items extraction and totals computation."""
    
    print("=" * 70)
    print("MEMPHIS POOL BILL LINE ITEMS EXTRACTION")
    print("=" * 70)
    print()
    
    # Setup paths
    data_root = Path("data/memphis_pool")
    text_dir = data_root / "bills_text"
    indexes_dir = data_root / "indexes"
    
    items_csv = indexes_dir / "bill_items.csv"
    totals_csv = indexes_dir / "bill_totals_summed.csv"
    summary_txt = indexes_dir / "billing_summary_for_memphis_pool.txt"
    
    print(f"Text directory: {text_dir}")
    print(f"Items CSV: {items_csv}")
    print(f"Totals CSV: {totals_csv}")
    print(f"Summary TXT: {summary_txt}")
    print("=" * 70)
    
    # Check prerequisites
    if not text_dir.exists():
        print(f"❌ Text directory not found: {text_dir}")
        print("\nRun this first:")
        print("  python3 libs/memphis_pool_bills.py --local-pdf-dir <pdf_dir>")
        return
    
    try:
        # Extract line items and compute totals
        build_line_items_index(text_dir, items_csv, totals_csv, summary_txt)
        
        # Final summary
        print("✅ EXTRACTION COMPLETE")
        print(f"Output files:")
        print(f"  - {items_csv}")
        print(f"  - {totals_csv}")
        print(f"  - {summary_txt}")
        print()
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
