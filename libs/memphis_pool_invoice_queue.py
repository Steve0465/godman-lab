"""
Memphis Pool invoice queue generator.

Generates an invoice-ready queue from unbilled jobs with pricing.

Input:
- data/memphis_pool/indexes/still_to_bill_now.csv (unbilled jobs)
- data/memphis_pool/config/pricing_rules.csv (pricing by job type)

Output:
- data/memphis_pool/indexes/invoice_queue.csv (ready to invoice)
- data/memphis_pool/indexes/invoice_queue_needs_review.csv (needs pricing review)

Usage:
    python3 libs/memphis_pool_invoice_queue.py
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Dict, List, Tuple


# Default pricing rules
DEFAULT_PRICING = {
    'COVER_INSTALL': 700,
    'SNAP_IN': 250,
    'INLAY_STEPS': 450,
    'LIGHT_WORK': 350,
}


def extract_job_date(job_card_name: str) -> str:
    """Extract job date from card name.
    
    Args:
        job_card_name: Trello card name
        
    Returns:
        Extracted date or empty string
    """
    # Look for patterns like "NOVEMBER 18, 2025" or "DECEMBER 12, 2025"
    date_pattern = r'(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+(\d{1,2}),?\s+(\d{4})'
    
    match = re.search(date_pattern, job_card_name.upper())
    if match:
        month_name = match.group(1)
        day = match.group(2)
        year = match.group(3)
        
        # Convert month name to number
        months = {
            'JANUARY': '01', 'FEBRUARY': '02', 'MARCH': '03', 'APRIL': '04',
            'MAY': '05', 'JUNE': '06', 'JULY': '07', 'AUGUST': '08',
            'SEPTEMBER': '09', 'OCTOBER': '10', 'NOVEMBER': '11', 'DECEMBER': '12'
        }
        month_num = months.get(month_name, '00')
        
        return f"{year}-{month_num}-{day.zfill(2)}"
    
    return ''


def classify_job_type(job_card_name: str) -> str:
    """Classify job type from card name.
    
    Args:
        job_card_name: Trello card name
        
    Returns:
        Job type classification
    """
    name_upper = job_card_name.upper()
    
    # Check for job type keywords (order matters - most specific first)
    if 'SNAP' in name_upper:
        return 'SNAP_IN'
    elif 'INLAY' in name_upper:
        return 'INLAY_STEPS'
    elif 'LIGHT' in name_upper:
        return 'LIGHT_WORK'
    elif 'COVER' in name_upper or 'INSTALL COVER' in name_upper:
        return 'COVER_INSTALL'
    else:
        return 'UNKNOWN'


def load_pricing_rules(pricing_file: Path) -> Tuple[Dict[str, float], bool]:
    """Load or create pricing rules.
    
    Args:
        pricing_file: Path to pricing rules CSV
        
    Returns:
        Tuple of (pricing dict, is_new_file)
    """
    if pricing_file.exists():
        # Load existing pricing rules
        pricing = {}
        with open(pricing_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                job_type = row.get('job_type', '')
                unit_price = row.get('unit_price', '0')
                try:
                    pricing[job_type] = float(unit_price)
                except ValueError:
                    pricing[job_type] = 0.0
        
        return pricing, False
    else:
        # Create default pricing file
        pricing_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(pricing_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['job_type', 'unit_price'])
            for job_type, price in DEFAULT_PRICING.items():
                writer.writerow([job_type, price])
        
        return DEFAULT_PRICING.copy(), True


def process_unbilled_jobs(
    unbilled_csv: Path,
    pricing: Dict[str, float],
    is_new_pricing: bool
) -> Tuple[List[Dict], List[Dict]]:
    """Process unbilled jobs into invoice queue.
    
    Args:
        unbilled_csv: Path to still_to_bill_now.csv
        pricing: Pricing rules by job type
        is_new_pricing: Whether pricing file was just created
        
    Returns:
        Tuple of (invoice_queue, needs_review)
    """
    invoice_queue = []
    needs_review = []
    
    with open(unbilled_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            job_card_name = row.get('job_card_name', '')
            
            # Extract job details
            job_date = extract_job_date(job_card_name)
            job_type = classify_job_type(job_card_name)
            qty = 1
            
            # Get pricing
            unit_price = pricing.get(job_type, 0.0)
            line_total = qty * unit_price
            
            notes = ''
            
            # Determine if needs review
            needs_review_flag = False
            
            if is_new_pricing:
                notes = 'NEW_PRICING_FILE - Please verify pricing'
                needs_review_flag = True
            elif job_type == 'UNKNOWN':
                notes = 'UNKNOWN job type - Please classify and price'
                needs_review_flag = True
            elif unit_price == 0.0:
                notes = 'NO PRICING FOUND - Please add to pricing_rules.csv'
                needs_review_flag = True
            
            # Build invoice line
            invoice_line = {
                'job_card_name': job_card_name,
                'job_date': job_date,
                'job_type': job_type,
                'qty': qty,
                'unit_price': f'${unit_price:.2f}',
                'line_total': f'${line_total:.2f}',
                'notes': notes
            }
            
            # Add to appropriate list
            if needs_review_flag:
                needs_review.append(invoice_line)
            else:
                invoice_queue.append(invoice_line)
    
    return invoice_queue, needs_review


def write_invoice_queue(
    invoice_queue: List[Dict],
    needs_review: List[Dict],
    queue_csv: Path,
    review_csv: Path
) -> None:
    """Write invoice queue CSVs.
    
    Args:
        invoice_queue: Ready-to-invoice jobs
        needs_review: Jobs needing review
        queue_csv: Output path for invoice queue
        review_csv: Output path for needs review
    """
    queue_csv.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        'job_card_name', 'job_date', 'job_type', 'qty',
        'unit_price', 'line_total', 'notes'
    ]
    
    # Write invoice queue
    with open(queue_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(invoice_queue)
    
    # Write needs review
    with open(review_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(needs_review)


def main():
    """Run invoice queue generator."""
    
    parser = argparse.ArgumentParser(
        description="Generate invoice queue from unbilled jobs"
    )
    parser.add_argument(
        '--unbilled-csv',
        type=str,
        default='data/memphis_pool/indexes/still_to_bill_now.csv',
        help="Path to still_to_bill_now.csv"
    )
    parser.add_argument(
        '--pricing-file',
        type=str,
        default='data/memphis_pool/config/pricing_rules.csv',
        help="Path to pricing rules CSV"
    )
    parser.add_argument(
        '--queue-csv',
        type=str,
        default='data/memphis_pool/indexes/invoice_queue.csv',
        help="Output invoice queue CSV"
    )
    parser.add_argument(
        '--review-csv',
        type=str,
        default='data/memphis_pool/indexes/invoice_queue_needs_review.csv',
        help="Output needs review CSV"
    )
    
    args = parser.parse_args()
    
    unbilled_csv = Path(args.unbilled_csv)
    pricing_file = Path(args.pricing_file)
    queue_csv = Path(args.queue_csv)
    review_csv = Path(args.review_csv)
    
    print("=" * 70)
    print("MEMPHIS POOL INVOICE QUEUE GENERATOR")
    print("=" * 70)
    print()
    print(f"Unbilled jobs: {unbilled_csv}")
    print(f"Pricing rules: {pricing_file}")
    print(f"Queue output: {queue_csv}")
    print(f"Review output: {review_csv}")
    print("=" * 70)
    print()
    
    # Check prerequisites
    if not unbilled_csv.exists():
        print(f"❌ Unbilled jobs file not found: {unbilled_csv}")
        print("\nRun this first:")
        print("  python3 libs/memphis_pool_reconcile_unbilled.py --last-bills 18")
        return
    
    try:
        # Step 1: Load or create pricing rules
        print("Step 1: Loading pricing rules...")
        pricing, is_new_pricing = load_pricing_rules(pricing_file)
        
        if is_new_pricing:
            print(f"⚠️  Created new pricing file: {pricing_file}")
            print("   Default pricing:")
            for job_type, price in pricing.items():
                print(f"     {job_type}: ${price:.2f}")
            print("   ⚠️  All jobs marked for review until you verify pricing!")
        else:
            print(f"✓ Loaded pricing rules: {len(pricing)} job types")
            for job_type, price in pricing.items():
                print(f"  - {job_type}: ${price:.2f}")
        print()
        
        # Step 2: Process unbilled jobs
        print("Step 2: Processing unbilled jobs...")
        invoice_queue, needs_review = process_unbilled_jobs(
            unbilled_csv,
            pricing,
            is_new_pricing
        )
        print(f"✓ Processed {len(invoice_queue) + len(needs_review)} jobs")
        print()
        
        # Step 3: Write outputs
        print("Step 3: Writing invoice queue...")
        write_invoice_queue(invoice_queue, needs_review, queue_csv, review_csv)
        print(f"✓ Wrote: {queue_csv}")
        print(f"✓ Wrote: {review_csv}")
        print()
        
        # Calculate totals
        total_ready = sum(
            float(job['line_total'].replace('$', '').replace(',', ''))
            for job in invoice_queue
        )
        
        total_review = sum(
            float(job['line_total'].replace('$', '').replace(',', ''))
            for job in needs_review
        )
        
        total_all = total_ready + total_review
        
        # Summary
        print("=" * 70)
        print("INVOICE QUEUE SUMMARY")
        print("=" * 70)
        print(f"✅ Ready to invoice: {len(invoice_queue)} jobs")
        print(f"   Total amount: ${total_ready:,.2f}")
        print()
        print(f"⚠️  Needs review: {len(needs_review)} jobs")
        print(f"   Total amount: ${total_review:,.2f}")
        print()
        print(f"💰 Grand total: ${total_all:,.2f} ({len(invoice_queue) + len(needs_review)} jobs)")
        print()
        
        # Show job type breakdown
        job_type_counts = {}
        for job in invoice_queue + needs_review:
            jt = job['job_type']
            job_type_counts[jt] = job_type_counts.get(jt, 0) + 1
        
        print("Job type breakdown:")
        for job_type, count in sorted(job_type_counts.items(), key=lambda x: x[1], reverse=True):
            price = pricing.get(job_type, 0.0)
            print(f"  {count:2d} × {job_type} @ ${price:.2f}")
        print()
        
        if needs_review:
            print("⚠️  ATTENTION: Jobs needing review:")
            for job in needs_review[:10]:
                job_name = job['job_card_name'][:50]
                notes = job['notes']
                print(f"  - {job_name}")
                print(f"    → {notes}")
            if len(needs_review) > 10:
                print(f"  ... and {len(needs_review) - 10} more")
            print()
            print(f"Review and update: {review_csv}")
            print()
        
        print("=" * 70)
        print("✅ INVOICE QUEUE GENERATION COMPLETE")
        
        if is_new_pricing:
            print()
            print("⚠️  NEXT STEPS:")
            print(f"1. Review pricing in: {pricing_file}")
            print(f"2. Verify all jobs in: {review_csv}")
            print("3. Update pricing if needed")
            print("4. Re-run this script after pricing verification")
        else:
            print()
            print("NEXT STEPS:")
            print(f"1. Review {queue_csv} for jobs ready to invoice")
            if needs_review:
                print(f"2. Review {review_csv} for jobs needing attention")
            print("3. Create invoices from invoice_queue.csv")
            print("4. Update Trello cards after invoicing")
        
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
