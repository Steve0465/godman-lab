"""
Memphis Pool cards index builder.

Generates cards_index.csv from a Trello board export JSON file.

Input:
- Trello board export JSON (local file)

Output:
- data/memphis_pool/indexes/cards_index.csv

Usage:
    python3 libs/memphis_pool_build_cards_index.py
    python3 libs/memphis_pool_build_cards_index.py --export-json /path/to/board.json
    python3 libs/memphis_pool_build_cards_index.py --include-closed
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Dict, List


def load_board_export(export_path: Path) -> dict:
    """Load Trello board export JSON.
    
    Args:
        export_path: Path to board export JSON
        
    Returns:
        Board export data dict
    """
    if not export_path.exists():
        raise FileNotFoundError(f"Board export not found: {export_path}")
    
    with open(export_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_list_name_map(board_data: dict) -> Dict[str, str]:
    """Build list ID to list name mapping.
    
    Args:
        board_data: Board export data
        
    Returns:
        Dict mapping list ID to list name
    """
    lists = board_data.get('lists', [])
    
    list_map = {}
    for lst in lists:
        list_id = lst.get('id', '')
        list_name = lst.get('name', 'UNKNOWN')
        if list_id:
            list_map[list_id] = list_name
    
    return list_map


def build_cards_index(
    board_data: dict,
    list_map: Dict[str, str],
    include_closed: bool = False
) -> List[Dict]:
    """Build cards index from board data.
    
    Args:
        board_data: Board export data
        list_map: List ID to name mapping
        include_closed: Whether to include closed cards
        
    Returns:
        List of card dicts for CSV output
    """
    cards = board_data.get('cards', [])
    
    index_cards = []
    
    for card in cards:
        closed = card.get('closed', False)
        
        # Skip closed cards unless requested
        if closed and not include_closed:
            continue
        
        card_id = card.get('id', '')
        card_name = card.get('name', '')
        id_list = card.get('idList', '')
        list_name = list_map.get(id_list, 'UNKNOWN')
        date_last_activity = card.get('dateLastActivity', '')
        
        index_cards.append({
            'card_id': card_id,
            'card_name': card_name,
            'idList': id_list,
            'list_name': list_name,
            'closed': str(closed).lower(),
            'dateLastActivity': date_last_activity
        })
    
    return index_cards


def write_cards_index(cards: List[Dict], out_csv: Path) -> None:
    """Write cards index to CSV.
    
    Args:
        cards: List of card dicts
        out_csv: Output CSV path
    """
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        'card_id', 'card_name', 'idList', 'list_name',
        'closed', 'dateLastActivity'
    ]
    
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cards)


def main():
    """Run cards index builder."""
    
    parser = argparse.ArgumentParser(
        description="Build cards index from Trello board export JSON"
    )
    parser.add_argument(
        '--export-json',
        type=str,
        default='/Users/stephengodman/Downloads/Memphis pool board.json',
        help="Path to Trello board export JSON"
    )
    parser.add_argument(
        '--out-csv',
        type=str,
        default='data/memphis_pool/indexes/cards_index.csv',
        help="Output CSV path"
    )
    parser.add_argument(
        '--include-closed',
        action='store_true',
        help="Include closed cards (default: only open cards)"
    )
    
    args = parser.parse_args()
    
    export_path = Path(args.export_json)
    out_csv = Path(args.out_csv)
    
    print("=" * 70)
    print("MEMPHIS POOL CARDS INDEX BUILDER")
    print("=" * 70)
    print()
    print(f"Board export: {export_path}")
    print(f"Output CSV: {out_csv}")
    print(f"Include closed: {args.include_closed}")
    print("=" * 70)
    print()
    
    try:
        # Step 1: Load board export
        print("Step 1: Loading board export...")
        board_data = load_board_export(export_path)
        
        total_lists = len(board_data.get('lists', []))
        total_cards_raw = len(board_data.get('cards', []))
        
        print(f"✓ Loaded board export")
        print(f"  - Lists: {total_lists}")
        print(f"  - Cards: {total_cards_raw}")
        print()
        
        # Step 2: Build list name map
        print("Step 2: Building list name map...")
        list_map = build_list_name_map(board_data)
        print(f"✓ Created mapping for {len(list_map)} lists")
        print()
        
        # Show list names
        if list_map:
            print("Available lists:")
            for list_id, list_name in sorted(list_map.items(), key=lambda x: x[1]):
                print(f"  - {list_name}")
            print()
        
        # Step 3: Build cards index
        print("Step 3: Building cards index...")
        cards = build_cards_index(board_data, list_map, args.include_closed)
        print(f"✓ Processed {len(cards)} cards")
        print()
        
        # Step 4: Write CSV
        print("Step 4: Writing CSV...")
        write_cards_index(cards, out_csv)
        print(f"✓ Wrote: {out_csv}")
        print()
        
        # Summary
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Total cards written: {len(cards)}")
        print()
        
        # Count by list
        list_counts = Counter(card['list_name'] for card in cards)
        
        print("Cards per list (top 15):")
        for list_name, count in list_counts.most_common(15):
            print(f"  {count:3d} - {list_name}")
        
        if len(list_counts) > 15:
            remaining = len(list_counts) - 15
            print(f"  ... and {remaining} more lists")
        
        print()
        print("=" * 70)
        print("✅ CARDS INDEX COMPLETE")
        print(f"Output: {out_csv}")
        print()
        print("Next step:")
        print("  python3 libs/memphis_pool_reconcile_unbilled.py --last-bills 2")
        print("=" * 70)
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print()
        print("Available files in ~/Downloads:")
        downloads = Path.home() / "Downloads"
        if downloads.exists():
            json_files = list(downloads.glob("*.json"))
            if json_files:
                print("\nJSON files found:")
                for jf in sorted(json_files)[:10]:
                    print(f"  - {jf.name}")
                if len(json_files) > 10:
                    print(f"  ... and {len(json_files) - 10} more")
            else:
                print("  (no .json files found)")
        print()
        print("To export from Trello:")
        print("  1. Open board in Trello")
        print("  2. Menu → More → Print and export → Export as JSON")
        print("  3. Save to ~/Downloads/")
        print("  4. Run this script again")
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
