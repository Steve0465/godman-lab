#!/usr/bin/env python3
"""
Test script for Memphis Pool ingest module.

Usage:
    export TRELLO_KEY="your_key"
    export TRELLO_TOKEN="your_token"
    export MEMPHIS_POOL_BOARD_ID="60df29145c9a576f23056516"  # optional
    export MEMPHIS_POOL_BILLS_LIST_ID="67d1e94e3597c3ef2fdc8300"  # optional
    
    python3 test_memphis_ingest.py
"""

import sys
from pathlib import Path

# Add libs to path
sys.path.insert(0, str(Path(__file__).parent / "libs"))

from memphis_pool_ingest import (
    parse_bill_date_from_filename,
    get_lists_by_id,
    pull_cards_one_by_one,
    build_cards_index,
    build_bills_index,
)
from trello_client import TrelloClient, TrelloError


def test_parse_bill_date():
    """Test bill date parsing from filenames."""
    print("Testing parse_bill_date_from_filename()...")
    
    test_cases = [
        ("Xerox Scan_11192025103635.pdf", "2025-11-19"),
        ("invoice_12012024120000.pdf", "2024-12-01"),
        ("invoice.pdf", ""),
        ("scan_99999999999999.pdf", ""),  # Invalid date
        ("document_01152025143000.jpg", "2025-01-15"),
    ]
    
    for filename, expected in test_cases:
        result = parse_bill_date_from_filename(filename)
        status = "✓" if result == expected else "❌"
        print(f"  {status} {filename} -> {result!r} (expected {expected!r})")
    
    print()


def test_full_ingest():
    """Test full ingest pipeline."""
    import os
    
    print("=" * 70)
    print("Testing Full Memphis Pool Ingest")
    print("=" * 70)
    print()
    
    # Configuration
    board_id = os.environ.get("MEMPHIS_POOL_BOARD_ID", "60df29145c9a576f23056516")
    bills_list_id = os.environ.get("MEMPHIS_POOL_BILLS_LIST_ID", "67d1e94e3597c3ef2fdc8300")
    
    # Output directories (test mode)
    output_root = Path("data/memphis_pool_test")
    raw_cards_dir = output_root / "raw_cards"
    indexes_dir = output_root / "indexes"
    
    print(f"Board ID: {board_id}")
    print(f"BILLS List ID: {bills_list_id}")
    print(f"Output: {output_root}")
    print()
    
    try:
        # Initialize client
        print("1. Initializing TrelloClient...")
        client = TrelloClient()
        print()
        
        # Get lists
        print("2. Fetching lists mapping...")
        lists_by_id = get_lists_by_id(board_id, client=client)
        print(f"✓ Got {len(lists_by_id)} lists")
        print(f"Sample lists: {list(lists_by_id.values())[:5]}")
        print()
        
        # Pull cards (limit to first 10 for testing)
        print("3. Pulling cards (limiting to first 10 for test)...")
        
        # Fetch minimal card list
        cards = client.get_board_cards(
            board_id,
            fields="id,shortLink,name,idList,dateLastActivity"
        )
        
        if not cards:
            print("❌ No cards found")
            return
        
        # Limit to first 10 for testing
        test_cards = cards[:10]
        print(f"Testing with {len(test_cards)} cards (out of {len(cards)} total)")
        
        # Create a temporary board-like structure for testing
        raw_cards_dir.mkdir(parents=True, exist_ok=True)
        
        saved_count = 0
        for card in test_cards:
            try:
                full_card = client.get_card(
                    card["id"],
                    attachments=True,
                    actions=True,
                    action_types="createCard,updateCard,addAttachmentToCard,deleteAttachmentFromCard"
                )
                
                card_file = raw_cards_dir / f"{card['id']}.json"
                import json
                with open(card_file, 'w') as f:
                    json.dump(full_card, f, indent=2)
                
                saved_count += 1
                print(f"  ✓ Saved {card.get('name', 'Unknown')[:40]}...")
                
            except Exception as e:
                print(f"  ❌ Failed {card.get('name', 'Unknown')[:40]}: {e}")
        
        print(f"✓ Saved {saved_count} cards")
        print()
        
        # Build cards index
        print("4. Building cards index...")
        cards_csv = indexes_dir / "cards_index.csv"
        build_cards_index(raw_cards_dir, lists_by_id, cards_csv)
        
        # Show sample
        if cards_csv.exists():
            with open(cards_csv) as f:
                lines = f.readlines()
                print(f"✓ Cards index has {len(lines)-1} rows")
                print("First 3 rows:")
                for line in lines[:4]:
                    print(f"  {line.rstrip()}")
        print()
        
        # Build bills index
        print("5. Building bills index...")
        bills_csv = indexes_dir / "bills_attachments_index.csv"
        build_bills_index(raw_cards_dir, bills_list_id, bills_csv)
        
        # Show sample
        if bills_csv.exists():
            with open(bills_csv) as f:
                lines = f.readlines()
                print(f"✓ Bills index has {len(lines)-1} rows")
                if len(lines) > 1:
                    print("First 2 rows:")
                    for line in lines[:3]:
                        print(f"  {line.rstrip()}")
        print()
        
        print("=" * 70)
        print("✅ Test completed successfully!")
        print("=" * 70)
        print(f"\nTest output directory: {output_root}")
        print("To run full ingest, use: python3 libs/memphis_pool_ingest.py")
        
    except TrelloError as e:
        print(f"\n❌ Trello error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Run all tests."""
    test_parse_bill_date()
    print()
    test_full_ingest()


if __name__ == "__main__":
    main()
