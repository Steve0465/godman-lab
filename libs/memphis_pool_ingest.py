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


def trello_id_created_at(card_id: str) -> str:
    """Extract created_at timestamp from Trello card ID.
    
    Trello IDs start with 8 hex chars representing Unix timestamp in seconds.
    
    Args:
        card_id: Trello card ID (e.g., "6836232640f2ffc8c8edb6a2")
        
    Returns:
        ISO datetime string (UTC) or empty string if parsing fails
        
    Example:
        >>> trello_id_created_at("6836232640f2ffc8c8edb6a2")
        "2024-05-24T..."
    """
    if not card_id or len(card_id) < 8:
        return ""
    
    try:
        # First 8 chars are hex timestamp
        timestamp_hex = card_id[:8]
        timestamp = int(timestamp_hex, 16)
        dt = datetime.fromtimestamp(timestamp, tz=None)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, OverflowError):
        return ""


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


def parse_bill_date_from_url(url: str) -> str:
    """Extract bill date from Trello attachment URL.
    
    Extracts the actual downloadable filename from URL and attempts to
    parse date using parse_bill_date_from_filename().
    
    Args:
        url: Trello attachment URL (e.g., 
             "https://trello.com/.../download/Xerox_Scan_05272025153405.pdf")
        
    Returns:
        Date string in YYYY-MM-DD format, or empty string if parse fails
        
    Example:
        >>> parse_bill_date_from_url("https://trello.com/.../download/Xerox_Scan_05272025153405.pdf")
        "2025-05-27"
    """
    if not url:
        return ""
    
    try:
        from urllib.parse import urlparse, unquote
        
        # Parse URL
        parsed = urlparse(url)
        path = parsed.path
        
        # Extract filename from path
        # Prefer substring after "/download/" if present
        if "/download/" in path:
            filename = path.split("/download/")[-1]
        else:
            # Use last path segment
            filename = path.split("/")[-1] if "/" in path else path
        
        # URL decode
        filename = unquote(filename)
        
        # Strip query params if any leaked through
        filename = filename.split("?")[0]
        
        # Try to parse date from filename
        return parse_bill_date_from_filename(filename)
        
    except Exception:
        return ""


def load_board_export(export_json_path: Path) -> dict:
    """Load Trello board export JSON from disk.
    
    Args:
        export_json_path: Path to board export JSON file
        
    Returns:
        Parsed board export dictionary
        
    Raises:
        FileNotFoundError: If export file doesn't exist
        ValueError: If JSON is invalid or missing required keys
    """
    export_json_path = Path(export_json_path)
    
    if not export_json_path.exists():
        raise FileNotFoundError(f"Board export not found: {export_json_path}")
    
    print(f"Loading board export from {export_json_path}")
    
    with open(export_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Validate required keys
    if not isinstance(data, dict):
        raise ValueError("Board export must be a JSON object")
    
    if 'cards' not in data:
        raise ValueError("Board export missing required key: 'cards'")
    
    if 'lists' not in data:
        raise ValueError("Board export missing required key: 'lists'")
    
    cards_count = len(data.get('cards', []))
    lists_count = len(data.get('lists', []))
    
    print(f"✓ Loaded export with {cards_count} cards and {lists_count} lists")
    
    return data


def write_raw_cards_from_export(export_data: dict, raw_cards_dir: Path) -> int:
    """Write individual card JSON files from board export.
    
    Args:
        export_data: Parsed board export dictionary
        raw_cards_dir: Directory to write card JSON files
        
    Returns:
        Number of cards written
    """
    raw_cards_dir = Path(raw_cards_dir)
    raw_cards_dir.mkdir(parents=True, exist_ok=True)
    
    cards = export_data.get('cards', [])
    
    print(f"\nWriting {len(cards)} cards to {raw_cards_dir}")
    
    written = 0
    for card in cards:
        card_id = card.get('id')
        if not card_id:
            print(f"⚠️  Skipping card without ID")
            continue
        
        card_file = raw_cards_dir / f"{card_id}.json"
        safe_write_json(card_file, card)
        written += 1
    
    print(f"✓ Wrote {written} card files")
    
    return written


def get_lists_by_id_from_export(export_data: dict) -> Dict[str, str]:
    """Build list ID to name mapping from board export.
    
    Args:
        export_data: Parsed board export dictionary
        
    Returns:
        Dictionary mapping list IDs to list names
    """
    lists = export_data.get('lists', [])
    lists_by_id = {lst['id']: lst['name'] for lst in lists if 'id' in lst and 'name' in lst}
    
    print(f"✓ Mapped {len(lists_by_id)} lists")
    
    return lists_by_id


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
            
            # Extract created_at from createCard action, or derive from card ID
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
            
            # Fallback: derive from card ID if no createCard action
            if not created_at and card_id:
                created_at = trello_id_created_at(card_id)
            
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
    
    Scans cards in BILLS list and extracts attachment metadata.
    Prefers addAttachmentToCard actions if present, otherwise falls back
    to card['attachments'] array. Does NOT download files.
    
    Args:
        raw_cards_dir: Directory containing card JSON files
        bills_list_id: Trello list ID for BILLS list
        out_csv: Output CSV file path
        
    CSV columns:
        bill_date, bill_date_action, bill_date_filename, attachment_name, 
        attachment_id, attachment_url, source_card_id, source_card_name, 
        action_id, action_datetime_utc
        
    bill_date: Best available date (action date > filename date > "UNKNOWN")
    bill_date_action: Date from action timestamp (YYYY-MM-DD UTC), empty if no action
    bill_date_filename: Parsed from attachment name or URL (pattern _MMDDYYYYHHMMSS)
    
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
            
            # Strategy 1: Try to extract from addAttachmentToCard actions (preferred)
            action_rows = []
            for action in actions:
                if action.get("type") != "addAttachmentToCard":
                    continue
                
                action_id = action.get("id", "")
                action_date = action.get("date", "")
                
                # Extract bill_date_action (YYYY-MM-DD from action date)
                bill_date_action = ""
                action_datetime_utc = ""
                if action_date:
                    try:
                        dt = datetime.fromisoformat(action_date.replace("Z", "+00:00"))
                        bill_date_action = dt.strftime("%Y-%m-%d")
                        action_datetime_utc = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                    except ValueError:
                        action_datetime_utc = action_date
                
                # Extract attachment details from action data
                attachment_data = action.get("data", {}).get("attachment", {})
                attachment_id = attachment_data.get("id", "")
                attachment_name = attachment_data.get("name", "")
                attachment_url = attachment_data.get("url", "")
                
                # Parse bill_date_filename with fallback to URL
                bill_date_filename = parse_bill_date_from_filename(attachment_name)
                if not bill_date_filename and attachment_url:
                    bill_date_filename = parse_bill_date_from_url(attachment_url)
                
                # Compute best bill_date
                bill_date = bill_date_action if bill_date_action else bill_date_filename
                if not bill_date:
                    bill_date = "UNKNOWN"
                
                action_rows.append({
                    "bill_date": bill_date,
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
            
            # Strategy 2: If no actions, fall back to card['attachments'] array
            if not action_rows:
                attachments = card.get("attachments", [])
                for attachment in attachments:
                    attachment_id = attachment.get("id", "")
                    attachment_name = attachment.get("name", "")
                    attachment_url = attachment.get("url", "")
                    
                    # Parse bill_date_filename with priority:
                    # a) from attachment name, b) from URL, c) blank
                    bill_date_filename = parse_bill_date_from_filename(attachment_name)
                    if not bill_date_filename and attachment_url:
                        bill_date_filename = parse_bill_date_from_url(attachment_url)
                    
                    # Compute best bill_date (no action date in export mode)
                    bill_date = bill_date_filename if bill_date_filename else "UNKNOWN"
                    
                    action_rows.append({
                        "bill_date": bill_date,
                        "bill_date_action": "",  # No action date available
                        "bill_date_filename": bill_date_filename,
                        "attachment_name": attachment_name,
                        "attachment_id": attachment_id,
                        "attachment_url": attachment_url,
                        "source_card_id": card_id,
                        "source_card_name": card_name,
                        "action_id": "",  # No action ID available
                        "action_datetime_utc": ""  # No action datetime available
                    })
            
            rows.extend(action_rows)
        
        except Exception as e:
            print(f"⚠️  Error processing {card_file.name}: {e}")
            continue
    
    print(f"✓ Found {bills_cards_count} cards in BILLS list")
    print(f"✓ Found {len(rows)} attachment actions")
    
    # Write CSV
    if rows:
        fieldnames = [
            "bill_date", "bill_date_action", "bill_date_filename", "attachment_name",
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


def ingest_from_board_export(
    export_json_path: Path,
    raw_cards_dir: Path,
    indexes_dir: Path,
    bills_list_id: str = DEFAULT_MEMPHIS_POOL_BILLS_LIST_ID
) -> None:
    """Ingest Memphis Pool board from a local JSON export file.
    
    Args:
        export_json_path: Path to Trello board export JSON
        raw_cards_dir: Directory to write individual card JSON files
        indexes_dir: Directory to write CSV index files
        bills_list_id: Trello list ID for BILLS list
    """
    print("=" * 70)
    print("MEMPHIS POOL TRELLO INGEST (FROM LOCAL EXPORT)")
    print("=" * 70)
    print(f"Export file: {export_json_path}")
    print(f"Raw cards output: {raw_cards_dir}")
    print(f"Indexes output: {indexes_dir}")
    print(f"BILLS list ID: {bills_list_id}")
    print("=" * 70)
    print()
    
    try:
        # Load board export
        export_data = load_board_export(export_json_path)
        
        # Write individual card JSON files
        cards_written = write_raw_cards_from_export(export_data, raw_cards_dir)
        
        if cards_written == 0:
            print("❌ No cards written. Exiting.")
            return
        
        # Build lists mapping
        lists_by_id = get_lists_by_id_from_export(export_data)
        
        # Build cards index
        cards_csv = indexes_dir / "cards_index.csv"
        build_cards_index(raw_cards_dir, lists_by_id, cards_csv)
        
        # Build bills index
        bills_csv = indexes_dir / "bills_attachments_index.csv"
        build_bills_index(raw_cards_dir, bills_list_id, bills_csv)
        
        print("\n" + "=" * 70)
        print("✅ INGEST COMPLETE (FROM EXPORT)")
        print("=" * 70)
        print(f"Raw cards: {raw_cards_dir}")
        print(f"Cards index: {cards_csv}")
        print(f"Bills index: {bills_csv}")
        print("=" * 70 + "\n")
        
    except (FileNotFoundError, ValueError) as e:
        print(f"\n❌ Error loading export: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Example usage: ingest Memphis Pool board and build indexes."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Ingest Memphis Pool Trello board (from API or local export)"
    )
    parser.add_argument(
        '--export-json',
        type=Path,
        help='Path to board export JSON file (if provided, ingests from local file instead of API)'
    )
    parser.add_argument(
        '--raw-cards-dir',
        type=Path,
        default=Path("data/memphis_pool/raw_cards"),
        help='Directory to write card JSON files (default: data/memphis_pool/raw_cards)'
    )
    parser.add_argument(
        '--indexes-dir',
        type=Path,
        default=Path("data/memphis_pool/indexes"),
        help='Directory to write CSV indexes (default: data/memphis_pool/indexes)'
    )
    parser.add_argument(
        '--bills-list-id',
        default=DEFAULT_MEMPHIS_POOL_BILLS_LIST_ID,
        help=f'BILLS list ID (default: {DEFAULT_MEMPHIS_POOL_BILLS_LIST_ID})'
    )
    
    args = parser.parse_args()
    
    # If export JSON provided, use local ingest
    if args.export_json:
        ingest_from_board_export(
            args.export_json,
            args.raw_cards_dir,
            args.indexes_dir,
            args.bills_list_id
        )
        return
    
    # Otherwise, use API-based ingest (original behavior)
    board_id = os.environ.get("MEMPHIS_POOL_BOARD_ID", DEFAULT_MEMPHIS_POOL_BOARD_ID)
    bills_list_id = args.bills_list_id
    raw_cards_dir = args.raw_cards_dir
    indexes_dir = args.indexes_dir
    
    print("=" * 70)
    print("MEMPHIS POOL TRELLO INGEST (FROM API)")
    print("=" * 70)
    print(f"Board ID: {board_id}")
    print(f"BILLS List ID: {bills_list_id}")
    print(f"Raw cards: {raw_cards_dir}")
    print(f"Indexes: {indexes_dir}")
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
