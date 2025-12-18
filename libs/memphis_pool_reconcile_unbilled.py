"""
Memphis Pool unbilled jobs reconciliation.

Cross-references Trello "Jobs I still need a bill for" cards against
the last N bills to identify which jobs are still unbilled.

Input:
- data/memphis_pool/indexes/cards_index.csv (Trello cards)
- data/memphis_pool/indexes/bill_items.csv (bill line items)
- data/memphis_pool/indexes/bill_totals_summed.csv (bill dates)

Output:
- data/memphis_pool/indexes/reconcile_unbilled_vs_last_bills.csv (all comparisons)
- data/memphis_pool/indexes/still_to_bill_now.csv (unmatched jobs)
- data/memphis_pool/indexes/already_on_last_bills.csv (matched jobs)

Usage:
    python3 libs/memphis_pool_reconcile_unbilled.py --last-bills 2
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import List, Tuple, Set, Dict


def normalize_text(text: str) -> str:
    """Normalize text for comparison.
    
    Args:
        text: Input text
        
    Returns:
        Normalized text (uppercase, no punctuation, collapsed whitespace)
    """
    # Convert to uppercase
    text = text.upper()
    
    # Remove punctuation
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def extract_tokens(text: str) -> Set[str]:
    """Extract word tokens from text.
    
    Args:
        text: Input text
        
    Returns:
        Set of word tokens (length >= 3)
    """
    normalized = normalize_text(text)
    tokens = normalized.split()
    
    # Filter short tokens and common words
    stopwords = {'THE', 'AND', 'FOR', 'WITH', 'FROM', 'THAT', 'THIS', 'HAVE', 'HAS', 'WAS', 'ARE', 'WILL'}
    
    return {token for token in tokens if len(token) >= 3 and token not in stopwords}


def calculate_match_score(job_name: str, line_text: str) -> float:
    """Calculate match score between job name and bill line text.
    
    Args:
        job_name: Trello card name
        line_text: Bill line text
        
    Returns:
        Match score between 0.0 and 1.0
    """
    job_tokens = extract_tokens(job_name)
    line_tokens = extract_tokens(line_text)
    
    if not job_tokens:
        return 0.0
    
    # Calculate token overlap (Jaccard similarity)
    intersection = job_tokens & line_tokens
    union = job_tokens | line_tokens
    
    if not union:
        return 0.0
    
    jaccard_score = len(intersection) / len(union)
    
    # Bonus for exact substring match
    normalized_job = normalize_text(job_name)
    normalized_line = normalize_text(line_text)
    
    if normalized_job in normalized_line or normalized_line in normalized_job:
        return max(jaccard_score, 0.8)
    
    return jaccard_score


def get_last_n_bills(
    bill_totals_csv: Path,
    n: int
) -> List[Tuple[str, str]]:
    """Get the last N bill files by date.
    
    Args:
        bill_totals_csv: Path to bill_totals_summed.csv
        n: Number of recent bills to return
        
    Returns:
        List of (bill_file, bill_date) tuples, sorted newest first
    """
    with open(bill_totals_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Filter out bills with no date
    dated_bills = [
        (row['bill_file'], row['bill_date'])
        for row in rows
        if row['bill_date']
    ]
    
    # Sort by date descending (newest first)
    dated_bills.sort(key=lambda x: x[1], reverse=True)
    
    # Return last N
    return dated_bills[:n]


def load_bill_line_items(
    bill_items_csv: Path,
    bill_files: List[str]
) -> List[Dict]:
    """Load line items from specified bills.
    
    Args:
        bill_items_csv: Path to bill_items.csv
        bill_files: List of bill file names to filter
        
    Returns:
        List of line item dicts
    """
    bill_files_set = set(bill_files)
    
    with open(bill_items_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        items = [
            row for row in reader
            if row['bill_file'] in bill_files_set
            and row['item_type'] == 'line_item'
        ]
    
    return items


def load_unbilled_job_cards(cards_index_csv: Path) -> List[Dict]:
    """Load Trello cards from 'Jobs I still need a bill for' list.
    
    Args:
        cards_index_csv: Path to cards_index.csv
        
    Returns:
        List of job card dicts
    """
    if not cards_index_csv.exists():
        print(f"❌ Cards index not found: {cards_index_csv}")
        print("\nRun this first:")
        print("  python3 libs/memphis_pool_ingest.py")
        return []
    
    with open(cards_index_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        cards = list(reader)
    
    # Find cards in "Jobs I still need a bill for" list
    unbilled_cards = []
    
    for card in cards:
        list_name_lower = card.get('list_name', '').lower()
        
        # Match variations
        if 'jobs i still need a bill for' in list_name_lower or \
           'jobs i need to bill' in list_name_lower or \
           'need a bill for' in list_name_lower or \
           'need to bill' in list_name_lower:
            unbilled_cards.append(card)
    
    # If none found, show available lists
    if not unbilled_cards:
        print("⚠️  No cards found in 'Jobs I still need a bill for' list")
        print("\nAvailable list names:")
        unique_lists = sorted(set(card.get('list_name', '') for card in cards))
        for list_name in unique_lists:
            count = sum(1 for c in cards if c.get('list_name') == list_name)
            print(f"  - {list_name} ({count} cards)")
        print()
    
    return unbilled_cards


def reconcile_jobs_against_bills(
    job_cards: List[Dict],
    bill_items: List[Dict],
    match_threshold: float = 0.6
) -> List[Dict]:
    """Reconcile job cards against bill line items.
    
    Args:
        job_cards: List of Trello job cards
        bill_items: List of bill line items
        match_threshold: Minimum score to consider a match
        
    Returns:
        List of reconciliation result dicts
    """
    results = []
    
    for job in job_cards:
        job_name = job.get('card_name', '')
        job_list = job.get('list_name', '')
        
        # Find best match in bill items
        best_score = 0.0
        best_match_bill = ''
        best_match_line = ''
        
        for item in bill_items:
            line_text = item.get('line_text', '')
            bill_file = item.get('bill_file', '')
            
            score = calculate_match_score(job_name, line_text)
            
            if score > best_score:
                best_score = score
                best_match_bill = bill_file
                best_match_line = line_text[:140]  # Truncate
        
        # Determine if matched
        matched = best_score >= match_threshold
        
        results.append({
            'job_card_name': job_name,
            'job_list_name': job_list,
            'matched_in_last_bills': str(matched).lower(),
            'best_match_bill_file': best_match_bill if matched else '',
            'best_match_line_text': best_match_line if matched else '',
            'match_score': f"{best_score:.3f}"
        })
    
    return results


def main():
    """Run unbilled jobs reconciliation."""
    
    parser = argparse.ArgumentParser(
        description="Reconcile Trello unbilled jobs against recent bills"
    )
    parser.add_argument(
        '--last-bills',
        type=int,
        default=2,
        help="Number of most recent bills to check (default: 2)"
    )
    parser.add_argument(
        '--match-threshold',
        type=float,
        default=0.6,
        help="Match score threshold (0.0-1.0, default: 0.6)"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("MEMPHIS POOL UNBILLED JOBS RECONCILIATION")
    print("=" * 70)
    print()
    
    # Setup paths
    data_root = Path("data/memphis_pool")
    indexes_dir = data_root / "indexes"
    
    cards_index_csv = indexes_dir / "cards_index.csv"
    bill_items_csv = indexes_dir / "bill_items.csv"
    bill_totals_csv = indexes_dir / "bill_totals_summed.csv"
    
    reconcile_all_csv = indexes_dir / "reconcile_unbilled_vs_last_bills.csv"
    still_to_bill_csv = indexes_dir / "still_to_bill_now.csv"
    already_billed_csv = indexes_dir / "already_on_last_bills.csv"
    
    print(f"Cards index: {cards_index_csv}")
    print(f"Bill items: {bill_items_csv}")
    print(f"Bill totals: {bill_totals_csv}")
    print(f"Last N bills: {args.last_bills}")
    print(f"Match threshold: {args.match_threshold}")
    print("=" * 70)
    print()
    
    # Check prerequisites
    if not cards_index_csv.exists():
        print(f"❌ Cards index not found: {cards_index_csv}")
        print("\nRun this first:")
        print("  python3 libs/memphis_pool_ingest.py")
        return
    
    if not bill_items_csv.exists():
        print(f"❌ Bill items not found: {bill_items_csv}")
        print("\nRun this first:")
        print("  python3 libs/memphis_pool_bill_items.py")
        return
    
    if not bill_totals_csv.exists():
        print(f"❌ Bill totals not found: {bill_totals_csv}")
        print("\nRun this first:")
        print("  python3 libs/memphis_pool_bill_items.py")
        return
    
    try:
        # Step 1: Get last N bills
        print(f"Step 1: Identifying last {args.last_bills} bills...")
        last_bills = get_last_n_bills(bill_totals_csv, args.last_bills)
        
        if not last_bills:
            print("❌ No dated bills found")
            return
        
        print(f"✓ Selected {len(last_bills)} most recent bills:")
        for bill_file, bill_date in last_bills:
            print(f"  - {bill_date}: {bill_file}")
        print()
        
        bill_files = [bill_file for bill_file, _ in last_bills]
        
        # Step 2: Load line items from last bills
        print(f"Step 2: Loading line items from last {len(bill_files)} bills...")
        bill_items = load_bill_line_items(bill_items_csv, bill_files)
        print(f"✓ Loaded {len(bill_items)} line items")
        print()
        
        # Step 3: Load unbilled job cards
        print("Step 3: Loading unbilled job cards from Trello...")
        job_cards = load_unbilled_job_cards(cards_index_csv)
        
        if not job_cards:
            print("❌ No unbilled job cards found")
            return
        
        print(f"✓ Loaded {len(job_cards)} unbilled job cards")
        print()
        
        # Step 4: Reconcile
        print("Step 4: Reconciling jobs against bills...")
        results = reconcile_jobs_against_bills(
            job_cards,
            bill_items,
            match_threshold=args.match_threshold
        )
        print(f"✓ Reconciled {len(results)} jobs")
        print()
        
        # Step 5: Write outputs
        print("Step 5: Writing output files...")
        
        # Write all results
        fieldnames = [
            'job_card_name', 'job_list_name', 'matched_in_last_bills',
            'best_match_bill_file', 'best_match_line_text', 'match_score'
        ]
        
        with open(reconcile_all_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        print(f"✓ Wrote: {reconcile_all_csv}")
        
        # Split results
        still_to_bill = [r for r in results if r['matched_in_last_bills'] == 'false']
        already_billed = [r for r in results if r['matched_in_last_bills'] == 'true']
        
        with open(still_to_bill_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(still_to_bill)
        
        print(f"✓ Wrote: {still_to_bill_csv}")
        
        with open(already_billed_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(already_billed)
        
        print(f"✓ Wrote: {already_billed_csv}")
        print()
        
        # Summary
        print("=" * 70)
        print("RECONCILIATION SUMMARY")
        print("=" * 70)
        print(f"Last {args.last_bills} bills checked:")
        for bill_file, bill_date in last_bills:
            print(f"  - {bill_date}: {bill_file}")
        print()
        print(f"Total unbilled job cards: {len(results)}")
        print(f"✅ Already on last bills: {len(already_billed)}")
        print(f"⚠️  Still to bill now: {len(still_to_bill)}")
        print()
        
        if already_billed:
            print("Already billed (do NOT bill again):")
            for job in already_billed[:10]:  # Show first 10
                score = job['match_score']
                print(f"  - {job['job_card_name'][:50]} (score: {score})")
            if len(already_billed) > 10:
                print(f"  ... and {len(already_billed) - 10} more")
            print()
        
        if still_to_bill:
            print("Still to bill:")
            for job in still_to_bill[:10]:  # Show first 10
                print(f"  - {job['job_card_name'][:50]}")
            if len(still_to_bill) > 10:
                print(f"  ... and {len(still_to_bill) - 10} more")
            print()
        
        print("=" * 70)
        print("✅ RECONCILIATION COMPLETE")
        print(f"Output files:")
        print(f"  - {reconcile_all_csv}")
        print(f"  - {still_to_bill_csv}")
        print(f"  - {already_billed_csv}")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
