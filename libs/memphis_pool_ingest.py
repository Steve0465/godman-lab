"""
Memphis Pool Trello board ingest and indexing.

Card-by-card ingestion with attachment tracking for bills analysis.
Does NOT compute pricing or make assumptions about job costs.
"""

from __future__ import annotations

import csv
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from trello_client import TrelloClient, TrelloError


# Environment variable defaults
DEFAULT_MEMPHIS_POOL_BOARD_ID = "60df29145c9a576f23056516"
DEFAULT_MEMPHIS_POOL_BILLS_LIST_ID = "67d1e94e3597c3ef2fdc8300"


def safe_write_json(path: Path, data: dict) -> None:
    """Write JSON data to file safely with pretty formatting.
    
    Args:
        path: Destination file path
        data: Dictionary to serialize as JSON
        
    Creates parent directories if needed.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def parse_bill_date_from_filename(name: str) -> str:
    """Extract bill date from filename pattern like _MMDDYYYYHHMMSS.
    
    Args:
        name: Filename to parse (e.g., "Xerox Scan_11192025103635.pdf")
        
    Returns:
        Date string in YYYY-MM-DD format, or empty string if parse fails
        
    Example:
        >>> parse_bill_date_from_filename("Xerox Scan_11192025103635.pdf")
        "2025-11-19"
        >>> parse_bill_date_from_filename("invoice.pdf")
        ""
    """
    # Pattern: _MMDDYYYYHHMMSS (12 digits)
    match = re.search(r'_(\d{2})(\d{2})(\d{4})\d{6}', name)
    if match:
        month, day, year = match.groups()
        try:
            # Validate date
            dt = datetime(int(year), int(month), int(day))
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            # Invalid date
            return ""
    return ""


def get_lists_by_id(board_id: str, *, client: TrelloClient) -> Dict[str, str]:
    """Fetch all lists from board and return mapping of list_id to list_name.
    
    Args:
        board_id: Trello board ID
        client: Authenticated TrelloClient instance
        
    Returns:
        Dictionary mapping list IDs to list names
        
    Example:
        >>> lists = get_lists_by_id("abc123", client=client)
        >>> lists["67d1e94e3597c3ef2fdc8300"]
        "BILLS"
    """
    print(f"Fetching lists for board {board_id}")
    lists = client.get_board_lists(board_id)
    
    lists_by_id = {lst["id"]: lst["name"] for lst in lists}
    print(f"✓ Mapped {len(lists_by_id)} lists")
    
    return lists_by_id


def pull_cards_one_by_one(
    out_dir: Path, 
    board_id: str, 
    *, 
    client: TrelloClient
) -> List[Path]:
    """Fetch all cards from board one-by-one with full details.
    
    First fetches minimal card list, then fetches each card individually
    with attachments and filtered actions. Saves each card as JSON.
    
    Args:
        out_dir: Directory to save card JSON files
        board_id: Trello board ID
        client: Authenticated TrelloClient instance
        
    Returns:
        List of Path objects for successfully saved card files
        
    Actions are filtered to:
        - createCard
        - updateCard
        - addAttachmentToCard
        - deleteAttachmentFromCard
        
    Files are saved as: <out_dir>/<card_id>.json
    
    Resilient: Logs failures but continues processing remaining cards.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*70}")
    print(f"Pulling cards from board {board_id}")
    print(f"Output directory: {out_dir}")
    print(f"{'='*70}\n")
    
    # Step 1: Fetch minimal card list
    print("Step 1: Fetching minimal card list...")
    try:
        cards = client.get_board_cards(
            board_id,
            fields="id,shortLink,name,idList,dateLastActivity"
        )
    except TrelloError as e:
        print(f"❌ Failed to fetch cards: {e}")
        return []
    
    if not cards:
        print("⚠️  No cards found on board")
        return []
    
    print(f"✓ Found {len(cards)} cards to process\n")
    
    # Step 2: Fetch each card with full details
    print("Step 2: Fetching full card details...")
    saved_files: List[Path] = []
    failed_cards: List[tuple[str, str]] = []
    
    action_types = "createCard,updateCard,addAttachmentToCard,deleteAttachmentFromCard"
    
    for idx, card in enumerate(cards, 1):
        card_id = card["id"]
        card_name = card.get("name", "Unknown")
        
        print(f"[{idx}/{len(cards)}] {card_name[:50]}...", end=" ")
        
        try:
            # Fetch full card details with filtered actions
            full_card = client.get_card(
                card_id,
                attachments=True,
                actions=True,
                action_types=action_types
            )
            
            # Save to file
            card_file = out_dir / f"{card_id}.json"
            safe_write_json(card_file, full_card)
            saved_files.append(card_file)
            print("✓")
            
        except TrelloError as e:
            print(f"❌ {e}")
            failed_cards.append((card_id, str(e)))
            continue
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            failed_cards.append((card_id, f"Unexpected: {e}"))
            continue
    
    # Summary
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"✓ Successfully saved: {len(saved_files)} cards")
    
    if failed_cards:
        print(f"❌ Failed: {len(failed_cards)} cards")
        print("\nFailed cards:")
        for card_id, error in failed_cards[:10]:  # Show first 10
            print(f"  - {card_id}: {error}")
        if len(failed_cards) > 10:
            print(f"  ... and {len(failed_cards) - 10} more")
    
    print(f"{'='*70}\n")
    
    return saved_files


def build_cards_index(
    raw_cards_dir: Path,
    lists_by_id: Dict[str, str],
    out_csv: Path
) -> None:
    """Build index CSV of all cards with basic metadata.
    
    Args:
        raw_cards_dir: Directory containing card JSON files (from pull_cards_one_by_one)
        lists_by_id: Mapping of list IDs to list names
        out_csv: Output CSV file path
        
    CSV columns:
        card_id, shortLink, name, idList, list_name, created_at, 
        last_activity, attachments_count
        
    created_at is extracted from createCard action if present, else empty.
    attachments_count from badges.attachments or len(attachments).
    """
    raw_cards_dir = Path(raw_cards_dir)
    out_csv = Path(out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*70}")
    print(f"Building cards index from {raw_cards_dir}")
    print(f"Output: {out_csv}")
    print(f"{'='*70}\n")
    
    card_files = sorted(raw_cards_dir.glob("*.json"))
    
    if not card_files:
        print("⚠️  No card files found")
        return
    
    print(f"Processing {len(card_files)} card files...")
    
    rows = []
    
    for card_file in card_files:
        try:
            with open(card_file, 'r', encoding='utf-8') as f:
                card = json.load(f)
            
            card_id = card.get("id", "")
            short_link = card.get("shortLink", "")
            name = card.get("name", "")
            id_list = card.get("idList", "")
            list_name = lists_by_id.get(id_list, "")
            last_activity = card.get("dateLastActivity", "")
            
            # Extract created_at from createCard action
            created_at = ""
            actions = card.get("actions", [])
            for action in reversed(actions):  # Start from oldest
                if action.get("type") == "createCard":
                    created_at = action.get("date", "")
                    if created_at:
                        # Convert to YYYY-MM-DD format
                        try:
                            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                            created_at = dt.strftime("%Y-%m-%d")
                        except ValueError:
                            pass
                    break
            
            # Get attachments count
            attachments_count = card.get("badges", {}).get("attachments", 0)
            if attachments_count == 0:
                # Fallback to actual attachments array
                attachments_count = len(card.get("attachments", []))
            
            rows.append({
                "card_id": card_id,
                "shortLink": short_link,
                "name": name,
                "idList": id_list,
                "list_name": list_name,
                "created_at": created_at,
                "last_activity": last_activity,
                "attachments_count": attachments_count
            })
            
        except Exception as e:
            print(f"⚠️  Error processing {card_file.name}: {e}")
            continue
    
    # Write CSV
    if rows:
        fieldnames = [
            "card_id", "shortLink", "name", "idList", "list_name",
            "created_at", "last_activity", "attachments_count"
        ]
        
        with open(out_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        print(f"✓ Wrote {len(rows)} cards to {out_csv}")
    else:
        print("❌ No valid cards to write")
    
    print(f"{'='*70}\n")


def build_bills_index(
    raw_cards_dir: Path,
    bills_list_id: str,
    out_csv: Path
) -> None:
    """Build index CSV of bill attachments from cards in BILLS list.
    
    Scans cards in BILLS list and extracts attachment metadata from
    addAttachmentToCard actions. Does NOT download files.
    
    Args:
        raw_cards_dir: Directory containing card JSON files
        bills_list_id: Trello list ID for BILLS list
        out_csv: Output CSV file path
        
    CSV columns:
        bill_date_action, bill_date_filename, attachment_name, attachment_id,
        attachment_url, source_card_id, source_card_name, action_id, 
        action_datetime_utc
        
    bill_date_action: Date from action timestamp (YYYY-MM-DD UTC)
    bill_date_filename: Parsed from filename pattern _MMDDYYYYHHMMSS
    
    Note: This is index-only. Use download_url() separately to fetch PDFs.
    """
    raw_cards_dir = Path(raw_cards_dir)
    out_csv = Path(out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*70}")
    print(f"Building bills index from BILLS list")
    print(f"BILLS list ID: {bills_list_id}")
    print(f"Output: {out_csv}")
    print(f"{'='*70}\n")
    
    card_files = sorted(raw_cards_dir.glob("*.json"))
    
    if not card_files:
        print("⚠️  No card files found")
        return
    
    print(f"Scanning {len(card_files)} card files for BILLS list cards...")
    
    rows = []
    bills_cards_count = 0
    
    for card_file in card_files:
        try:
            with open(card_file, 'r', encoding='utf-8') as f:
                card = json.load(f)
            
            # Only process cards in BILLS list
            if card.get("idList") != bills_list_id:
                continue
            
            bills_cards_count += 1
            
            card_id = card.get("id", "")
            card_name = card.get("name", "")
            actions = card.get("actions", [])
            
            # Find all addAttachmentToCard actions
            for action in actions:
                if action.get("type") != "addAttachmentToCard":
                    continue
                
                action_id = action.get("id", "")
                action_date = action.get("date", "")
                
                # Extract bill_date_action (YYYY-MM-DD from action date)
                bill_date_action = ""
                if action_date:
                    try:
                        dt = datetime.fromisoformat(action_date.replace("Z", "+00:00"))
                        bill_date_action = dt.strftime("%Y-%m-%d")
                        action_datetime_utc = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                    except ValueError:
                        action_datetime_utc = action_date
                else:
                    action_datetime_utc = ""
                
                # Extract attachment details from action data
                attachment_data = action.get("data", {}).get("attachment", {})
                attachment_id = attachment_data.get("id", "")
                attachment_name = attachment_data.get("name", "")
                attachment_url = attachment_data.get("url", "")
                
                # Parse bill_date_filename from attachment name
                bill_date_filename = parse_bill_date_from_filename(attachment_name)
                
                rows.append({
                    "bill_date_action": bill_date_action,
                    "bill_date_filename": bill_date_filename,
                    "attachment_name": attachment_name,
                    "attachment_id": attachment_id,
                    "attachment_url": attachment_url,
                    "source_card_id": card_id,
                    "source_card_name": card_name,
                    "action_id": action_id,
                    "action_datetime_utc": action_datetime_utc
                })
        
        except Exception as e:
            print(f"⚠️  Error processing {card_file.name}: {e}")
            continue
    
    print(f"✓ Found {bills_cards_count} cards in BILLS list")
    print(f"✓ Found {len(rows)} attachment actions")
    
    # Write CSV
    if rows:
        fieldnames = [
            "bill_date_action", "bill_date_filename", "attachment_name",
            "attachment_id", "attachment_url", "source_card_id",
            "source_card_name", "action_id", "action_datetime_utc"
        ]
        
        with open(out_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        print(f"✓ Wrote {len(rows)} bill attachments to {out_csv}")
    else:
        print("⚠️  No bill attachments found")
    
    print(f"{'='*70}\n")


def main():
    """Example usage: ingest Memphis Pool board and build indexes."""
    
    # Read configuration from environment
    board_id = os.environ.get("MEMPHIS_POOL_BOARD_ID", DEFAULT_MEMPHIS_POOL_BOARD_ID)
    bills_list_id = os.environ.get("MEMPHIS_POOL_BILLS_LIST_ID", DEFAULT_MEMPHIS_POOL_BILLS_LIST_ID)
    
    # Setup output directories
    output_root = Path("data/memphis_pool")
    raw_cards_dir = output_root / "raw_cards"
    indexes_dir = output_root / "indexes"
    
    print("=" * 70)
    print("MEMPHIS POOL TRELLO INGEST")
    print("=" * 70)
    print(f"Board ID: {board_id}")
    print(f"BILLS List ID: {bills_list_id}")
    print(f"Output: {output_root}")
    print("=" * 70)
    
    try:
        # Initialize Trello client (reads TRELLO_KEY and TRELLO_TOKEN from env)
        client = TrelloClient()
        
        # Fetch lists mapping
        lists_by_id = get_lists_by_id(board_id, client=client)
        
        # Pull all cards
        saved_files = pull_cards_one_by_one(raw_cards_dir, board_id, client=client)
        
        if not saved_files:
            print("❌ No cards were saved. Exiting.")
            return
        
        # Build cards index
        cards_csv = indexes_dir / "cards_index.csv"
        build_cards_index(raw_cards_dir, lists_by_id, cards_csv)
        
        # Build bills index
        bills_csv = indexes_dir / "bills_attachments_index.csv"
        build_bills_index(raw_cards_dir, bills_list_id, bills_csv)
        
        print("\n" + "=" * 70)
        print("✅ INGEST COMPLETE")
        print("=" * 70)
        print(f"Raw cards: {raw_cards_dir}")
        print(f"Cards index: {cards_csv}")
        print(f"Bills index: {bills_csv}")
        print("=" * 70 + "\n")
        
    except TrelloError as e:
        print(f"\n❌ Trello error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
