"""
Memphis Pool invoice packet generator.

Generates invoice summary and email draft from invoice queue.

Input:
- data/memphis_pool/indexes/invoice_queue.csv (ready to invoice)
- data/memphis_pool/indexes/invoice_queue_needs_review.csv (optional)

Output:
- data/memphis_pool/indexes/MEMPHIS_POOL_INVOICE_PACKET.txt
- data/memphis_pool/indexes/MEMPHIS_POOL_EMAIL_DRAFT.txt

Usage:
    python3 libs/memphis_pool_invoice_packet_from_queue.py
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict


def load_invoice_queue(queue_csv: Path) -> List[Dict]:
    """Load invoice queue items.
    
    Args:
        queue_csv: Path to invoice queue CSV
        
    Returns:
        List of invoice line items
    """
    if not queue_csv.exists():
        return []
    
    with open(queue_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def parse_amount(amount_str: str) -> float:
    """Parse amount string to float.
    
    Args:
        amount_str: Amount string like "$700.00"
        
    Returns:
        Float value
    """
    return float(amount_str.replace('$', '').replace(',', ''))


def generate_invoice_packet(
    invoice_queue: List[Dict],
    needs_review: List[Dict],
    invoice_date: str
) -> str:
    """Generate invoice packet text.
    
    Args:
        invoice_queue: Ready to invoice items
        needs_review: Items needing review
        invoice_date: Invoice date string
        
    Returns:
        Invoice packet text
    """
    lines = []
    
    # Header
    lines.append("=" * 80)
    lines.append("MEMPHIS POOL SERVICES - INVOICE PACKET")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Invoice Date: {invoice_date}")
    lines.append("")
    
    # Calculate totals
    total_ready = sum(parse_amount(item['line_total']) for item in invoice_queue)
    total_review = sum(parse_amount(item['line_total']) for item in needs_review)
    grand_total = total_ready + total_review
    
    # Summary
    lines.append("INVOICE SUMMARY")
    lines.append("-" * 80)
    lines.append(f"Ready to invoice: {len(invoice_queue)} jobs")
    lines.append(f"Total amount: ${total_ready:,.2f}")
    lines.append("")
    
    if needs_review:
        lines.append(f"Pending review: {len(needs_review)} jobs")
        lines.append(f"Pending amount: ${total_review:,.2f}")
        lines.append("")
    
    lines.append(f"TOTAL DUE: ${grand_total:,.2f}")
    lines.append("")
    
    # Line items
    lines.append("=" * 80)
    lines.append("INVOICE LINE ITEMS")
    lines.append("=" * 80)
    lines.append("")
    
    if invoice_queue:
        lines.append(f"{'Customer / Job':<55} {'Type':<18} {'Amount':>10}")
        lines.append("-" * 80)
        
        # Sort by date if available
        sorted_queue = sorted(
            invoice_queue,
            key=lambda x: x.get('job_date', '9999-99-99')
        )
        
        for item in sorted_queue:
            job_name = item['job_card_name'][:53]
            job_type = item['job_type'][:16]
            line_total = item['line_total']
            
            lines.append(f"{job_name:<55} {job_type:<18} {line_total:>10}")
        
        lines.append("-" * 80)
        lines.append(f"{'SUBTOTAL':<73} ${total_ready:>9,.2f}")
        lines.append("")
    
    # Needs review section
    if needs_review:
        lines.append("=" * 80)
        lines.append("ITEMS NEEDING REVIEW / CONFIRMATION")
        lines.append("=" * 80)
        lines.append("")
        lines.append("The following jobs require pricing confirmation before final invoicing:")
        lines.append("")
        
        for item in needs_review:
            job_name = item['job_card_name'][:70]
            job_type = item['job_type']
            notes = item.get('notes', '')
            
            lines.append(f"• {job_name}")
            lines.append(f"  Job Type: {job_type}")
            if notes:
                lines.append(f"  Notes: {notes}")
            lines.append("")
        
        lines.append(f"Pending amount: ${total_review:,.2f}")
        lines.append("")
    
    # Footer
    lines.append("=" * 80)
    lines.append("PAYMENT INFORMATION")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Total Amount Due: ${grand_total:,.2f}")
    lines.append(f"Invoice Date: {invoice_date}")
    lines.append("Payment Terms: Net 30 days")
    lines.append("")
    lines.append("Please make payment payable to:")
    lines.append("  Memphis Pool Services")
    lines.append("")
    lines.append("Thank you for your business!")
    lines.append("")
    lines.append("=" * 80)
    
    return '\n'.join(lines)


def generate_email_draft(
    invoice_queue: List[Dict],
    needs_review: List[Dict],
    invoice_date: str
) -> str:
    """Generate email draft text.
    
    Args:
        invoice_queue: Ready to invoice items
        needs_review: Items needing review
        invoice_date: Invoice date string
        
    Returns:
        Email draft text
    """
    lines = []
    
    # Calculate totals
    total_ready = sum(parse_amount(item['line_total']) for item in invoice_queue)
    total_review = sum(parse_amount(item['line_total']) for item in needs_review)
    grand_total = total_ready + total_review
    
    # Subject
    lines.append("=" * 80)
    lines.append("EMAIL DRAFT - MEMPHIS POOL INVOICE")
    lines.append("=" * 80)
    lines.append("")
    lines.append("SUBJECT:")
    lines.append(f"Invoice for Pool Services - {invoice_date} - ${grand_total:,.2f} Total")
    lines.append("")
    lines.append("-" * 80)
    lines.append("BODY:")
    lines.append("-" * 80)
    lines.append("")
    
    # Greeting
    lines.append("Dear Memphis Pool Services,")
    lines.append("")
    
    # Main message
    if needs_review:
        lines.append(f"Please find attached the invoice for pool services completed through {invoice_date}.")
        lines.append("")
        lines.append(f"Ready to invoice: {len(invoice_queue)} jobs totaling ${total_ready:,.2f}")
        lines.append("")
        lines.append(f"Additionally, we have {len(needs_review)} job(s) pending pricing confirmation:")
    else:
        lines.append(f"Please find attached the invoice for {len(invoice_queue)} pool service jobs completed through {invoice_date}.")
        lines.append("")
    
    # List ready items by category
    cover_installs = [j for j in invoice_queue if j['job_type'] == 'COVER_INSTALL']
    other_jobs = [j for j in invoice_queue if j['job_type'] != 'COVER_INSTALL']
    
    if cover_installs:
        lines.append(f"Cover Installations ({len(cover_installs)} jobs):")
        for job in cover_installs[:5]:
            customer = job['job_card_name'].split(':')[0] if ':' in job['job_card_name'] else job['job_card_name'][:40]
            lines.append(f"  • {customer} - {job['line_total']}")
        if len(cover_installs) > 5:
            lines.append(f"  ... and {len(cover_installs) - 5} more cover installations")
        lines.append("")
    
    if other_jobs:
        lines.append(f"Other Services ({len(other_jobs)} jobs):")
        for job in other_jobs:
            customer = job['job_card_name'].split(':')[0] if ':' in job['job_card_name'] else job['job_card_name'][:40]
            job_type = job['job_type'].replace('_', ' ').title()
            lines.append(f"  • {customer} - {job_type} - {job['line_total']}")
        lines.append("")
    
    # Needs review section
    if needs_review:
        lines.append("Items needing confirmation:")
        for job in needs_review:
            customer = job['job_card_name'].split(':')[0] if ':' in job['job_card_name'] else job['job_card_name'][:40]
            lines.append(f"  • {customer} - {job['job_type']} - {job.get('notes', 'Needs classification')}")
        lines.append("")
        lines.append(f"Pending amount: ${total_review:,.2f}")
        lines.append("")
    
    # Payment information
    lines.append("INVOICE SUMMARY:")
    if needs_review:
        lines.append(f"  Ready to invoice: ${total_ready:,.2f}")
        lines.append(f"  Pending review: ${total_review:,.2f}")
    lines.append(f"  TOTAL DUE: ${grand_total:,.2f}")
    lines.append("")
    lines.append("Payment Terms: Net 30 days")
    lines.append(f"Invoice Date: {invoice_date}")
    lines.append("")
    
    if needs_review:
        lines.append("Please review the pending items and confirm pricing so we can finalize the complete invoice.")
        lines.append("")
    
    # Closing
    lines.append("Please remit payment at your earliest convenience. If you have any questions about")
    lines.append("this invoice, please don't hesitate to contact us.")
    lines.append("")
    lines.append("Thank you for your continued business!")
    lines.append("")
    lines.append("Best regards,")
    lines.append("[Your Name]")
    lines.append("Memphis Pool Services")
    lines.append("")
    lines.append("=" * 80)
    
    return '\n'.join(lines)


def main():
    """Run invoice packet generator."""
    
    parser = argparse.ArgumentParser(
        description="Generate invoice packet and email draft from invoice queue"
    )
    parser.add_argument(
        '--queue-csv',
        type=str,
        default='data/memphis_pool/indexes/invoice_queue.csv',
        help="Path to invoice queue CSV"
    )
    parser.add_argument(
        '--review-csv',
        type=str,
        default='data/memphis_pool/indexes/invoice_queue_needs_review.csv',
        help="Path to needs review CSV"
    )
    parser.add_argument(
        '--packet-txt',
        type=str,
        default='data/memphis_pool/indexes/MEMPHIS_POOL_INVOICE_PACKET.txt',
        help="Output invoice packet text"
    )
    parser.add_argument(
        '--email-txt',
        type=str,
        default='data/memphis_pool/indexes/MEMPHIS_POOL_EMAIL_DRAFT.txt',
        help="Output email draft text"
    )
    
    args = parser.parse_args()
    
    queue_csv = Path(args.queue_csv)
    review_csv = Path(args.review_csv)
    packet_txt = Path(args.packet_txt)
    email_txt = Path(args.email_txt)
    
    print("=" * 70)
    print("MEMPHIS POOL INVOICE PACKET GENERATOR")
    print("=" * 70)
    print()
    print(f"Invoice queue: {queue_csv}")
    print(f"Needs review: {review_csv}")
    print(f"Packet output: {packet_txt}")
    print(f"Email output: {email_txt}")
    print("=" * 70)
    print()
    
    # Check prerequisites
    if not queue_csv.exists():
        print(f"❌ Invoice queue not found: {queue_csv}")
        print("\nRun this first:")
        print("  python3 libs/memphis_pool_invoice_queue.py")
        return
    
    try:
        # Get invoice date (today)
        invoice_date = datetime.now().strftime("%B %d, %Y")
        
        # Step 1: Load invoice queue
        print("Step 1: Loading invoice queue...")
        invoice_queue = load_invoice_queue(queue_csv)
        print(f"✓ Loaded {len(invoice_queue)} ready jobs")
        
        # Step 2: Load needs review
        print("Step 2: Loading needs review items...")
        needs_review = load_invoice_queue(review_csv)
        if needs_review:
            print(f"✓ Loaded {len(needs_review)} jobs needing review")
        else:
            print("✓ No jobs need review")
        print()
        
        # Calculate totals
        total_ready = sum(parse_amount(item['line_total']) for item in invoice_queue)
        total_review = sum(parse_amount(item['line_total']) for item in needs_review)
        grand_total = total_ready + total_review
        
        # Step 3: Generate invoice packet
        print("Step 3: Generating invoice packet...")
        packet_text = generate_invoice_packet(invoice_queue, needs_review, invoice_date)
        
        packet_txt.parent.mkdir(parents=True, exist_ok=True)
        with open(packet_txt, 'w', encoding='utf-8') as f:
            f.write(packet_text)
        
        print(f"✓ Wrote: {packet_txt}")
        print()
        
        # Step 4: Generate email draft
        print("Step 4: Generating email draft...")
        email_text = generate_email_draft(invoice_queue, needs_review, invoice_date)
        
        with open(email_txt, 'w', encoding='utf-8') as f:
            f.write(email_text)
        
        print(f"✓ Wrote: {email_txt}")
        print()
        
        # Summary
        print("=" * 70)
        print("INVOICE PACKET SUMMARY")
        print("=" * 70)
        print(f"Invoice Date: {invoice_date}")
        print()
        print(f"Ready to invoice: {len(invoice_queue)} jobs")
        print(f"Amount: ${total_ready:,.2f}")
        print()
        
        if needs_review:
            print(f"Needs review: {len(needs_review)} jobs")
            print(f"Pending: ${total_review:,.2f}")
            print()
        
        print(f"💰 TOTAL DUE: ${grand_total:,.2f}")
        print()
        
        # Show job breakdown
        job_types = {}
        for job in invoice_queue + needs_review:
            jt = job['job_type']
            job_types[jt] = job_types.get(jt, 0) + 1
        
        print("Job breakdown:")
        for job_type, count in sorted(job_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {count:2d} × {job_type}")
        print()
        
        print("=" * 70)
        print("✅ INVOICE PACKET GENERATION COMPLETE")
        print()
        print("NEXT STEPS:")
        print(f"1. Review invoice packet: {packet_txt}")
        print(f"2. Review email draft: {email_txt}")
        print("3. Copy email text and send to Memphis Pool")
        print("4. Attach invoice packet or create formal PDF invoice")
        print("5. Update Trello cards after sending")
        print()
        print("Files ready for copy-paste!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
