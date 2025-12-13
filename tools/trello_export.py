#!/usr/bin/env python3
"""
Trello Board Export Tool

Exports full Trello board structure (lists, cards, checklists, attachments, labels)
to formatted JSON for Codex analysis and archival purposes.
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    import requests
except ImportError:
    print("Error: 'requests' library not found. Install with: pip install requests")
    sys.exit(1)


class TrelloExporter:
    """
    Handles Trello API authentication and data export.
    """
    
    BASE_URL = "https://api.trello.com/1"
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    
    def __init__(self, api_key: str, token: str, verbose: bool = False):
        """
        Initialize Trello exporter.
        
        Args:
            api_key: Trello API key
            token: Trello API token
            verbose: Enable verbose logging
        """
        self.api_key = api_key
        self.token = token
        self.verbose = verbose
        self.session = requests.Session()
    
    def _log(self, message: str) -> None:
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        """
        Make authenticated request to Trello API with retry logic.
        
        Args:
            endpoint: API endpoint (e.g., "/boards/{id}")
            params: Additional query parameters
            
        Returns:
            JSON response data
            
        Raises:
            SystemExit: On persistent API errors
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        # Add authentication
        query_params = {
            "key": self.api_key,
            "token": self.token
        }
        if params:
            query_params.update(params)
        
        # Retry loop
        for attempt in range(self.MAX_RETRIES):
            try:
                self._log(f"GET {url}")
                response = self.session.get(url, params=query_params, timeout=30)
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', self.RETRY_DELAY))
                    self._log(f"Rate limited. Retrying after {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                
                # Raise for other errors
                response.raise_for_status()
                
                return response.json()
            
            except requests.exceptions.HTTPError as e:
                if attempt < self.MAX_RETRIES - 1:
                    self._log(f"HTTP error: {e}. Retrying in {self.RETRY_DELAY}s...")
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                else:
                    print(f"\n❌ API Error: {e}")
                    print(f"URL: {url}")
                    print(f"Response: {response.text if 'response' in locals() else 'N/A'}")
                    sys.exit(1)
            
            except requests.exceptions.RequestException as e:
                print(f"\n❌ Request failed: {e}")
                print(f"URL: {url}")
                sys.exit(1)
        
        print(f"\n❌ Max retries exceeded for: {url}")
        sys.exit(1)
    
    def get_boards(self) -> List[Dict[str, Any]]:
        """
        Get all boards accessible to the authenticated user.
        
        Returns:
            List of board objects
        """
        self._log("Fetching user boards...")
        return self._make_request("/members/me/boards")
    
    def find_board(self, board_name: str) -> Optional[Dict[str, Any]]:
        """
        Find board by name.
        
        Args:
            board_name: Name of board to find
            
        Returns:
            Board object or None if not found
        """
        boards = self.get_boards()
        matches = [b for b in boards if b['name'].lower() == board_name.lower()]
        
        if len(matches) == 0:
            return None
        elif len(matches) == 1:
            return matches[0]
        else:
            # Multiple matches
            print(f"\n⚠️  Multiple boards found matching '{board_name}':")
            for i, board in enumerate(matches, 1):
                print(f"  {i}. {board['name']} (ID: {board['id']}) - {board.get('url', '')}")
            print("\nPlease specify the exact board ID using --board-id")
            sys.exit(1)
    
    def get_board_by_id(self, board_id: str) -> Dict[str, Any]:
        """
        Get board by ID.
        
        Args:
            board_id: Trello board ID
            
        Returns:
            Board object
        """
        self._log(f"Fetching board {board_id}...")
        return self._make_request(f"/boards/{board_id}")
    
    def get_lists(self, board_id: str) -> List[Dict[str, Any]]:
        """
        Get all lists on a board.
        
        Args:
            board_id: Trello board ID
            
        Returns:
            List of list objects
        """
        self._log(f"Fetching lists for board {board_id}...")
        return self._make_request(f"/boards/{board_id}/lists", {"fields": "all"})
    
    def get_cards(self, board_id: str) -> List[Dict[str, Any]]:
        """
        Get all cards on a board.
        
        Args:
            board_id: Trello board ID
            
        Returns:
            List of card objects
        """
        self._log(f"Fetching cards for board {board_id}...")
        return self._make_request(
            f"/boards/{board_id}/cards",
            {
                "fields": "all",
                "attachments": "true",
                "checklists": "all"
            }
        )
    
    def get_labels(self, board_id: str) -> List[Dict[str, Any]]:
        """
        Get all labels on a board.
        
        Args:
            board_id: Trello board ID
            
        Returns:
            List of label objects
        """
        self._log(f"Fetching labels for board {board_id}...")
        return self._make_request(f"/boards/{board_id}/labels")
    
    def export_board(self, board_identifier: str, use_id: bool = False) -> Dict[str, Any]:
        """
        Export complete board structure.
        
        Args:
            board_identifier: Board name or ID
            use_id: If True, treat board_identifier as ID
            
        Returns:
            Structured export dictionary
        """
        # Get board
        if use_id:
            board = self.get_board_by_id(board_identifier)
        else:
            board = self.find_board(board_identifier)
            if not board:
                print(f"\n❌ Board '{board_identifier}' not found.")
                print("\nAvailable boards:")
                for b in self.get_boards():
                    print(f"  - {b['name']} (ID: {b['id']})")
                sys.exit(1)
        
        board_id = board['id']
        
        self._log(f"Exporting board: {board['name']} ({board_id})")
        
        # Get all data
        lists = self.get_lists(board_id)
        cards = self.get_cards(board_id)
        labels = self.get_labels(board_id)
        
        if not lists:
            print(f"\n⚠️  Warning: Board '{board['name']}' has no lists!")
        
        # Build label lookup
        label_map = {label['id']: label for label in labels}
        
        # Organize cards by list
        cards_by_list = {}
        for card in cards:
            list_id = card['idList']
            if list_id not in cards_by_list:
                cards_by_list[list_id] = []
            cards_by_list[list_id].append(card)
        
        # Build structured export
        export_data = {
            "board": {
                "id": board['id'],
                "name": board['name'],
                "url": board.get('url', ''),
                "desc": board.get('desc', ''),
                "closed": board.get('closed', False),
                "exported_at": datetime.now().isoformat()
            },
            "lists": []
        }
        
        # Process each list
        for trello_list in sorted(lists, key=lambda x: x.get('pos', 0)):
            list_cards = cards_by_list.get(trello_list['id'], [])
            
            list_data = {
                "id": trello_list['id'],
                "name": trello_list['name'],
                "pos": trello_list.get('pos', 0),
                "closed": trello_list.get('closed', False),
                "cards": []
            }
            
            # Process each card in list
            for card in sorted(list_cards, key=lambda x: x.get('pos', 0)):
                card_labels = []
                for label_id in card.get('idLabels', []):
                    if label_id in label_map:
                        label = label_map[label_id]
                        card_labels.append({
                            "id": label['id'],
                            "name": label.get('name', ''),
                            "color": label.get('color', '')
                        })
                
                # Process attachments
                attachments = []
                for att in card.get('attachments', []):
                    attachments.append({
                        "id": att['id'],
                        "name": att.get('name', ''),
                        "url": att.get('url', ''),
                        "mimeType": att.get('mimeType', ''),
                        "bytes": att.get('bytes', 0)
                    })
                
                # Process checklists
                checklists = []
                for checklist in card.get('checklists', []):
                    checklist_items = []
                    for item in checklist.get('checkItems', []):
                        checklist_items.append({
                            "id": item['id'],
                            "name": item.get('name', ''),
                            "state": item.get('state', ''),
                            "pos": item.get('pos', 0)
                        })
                    
                    checklists.append({
                        "id": checklist['id'],
                        "name": checklist.get('name', ''),
                        "pos": checklist.get('pos', 0),
                        "items": sorted(checklist_items, key=lambda x: x['pos'])
                    })
                
                card_data = {
                    "id": card['id'],
                    "name": card['name'],
                    "desc": card.get('desc', ''),
                    "due": card.get('due', ''),
                    "dueComplete": card.get('dueComplete', False),
                    "url": card.get('url', ''),
                    "labels": card_labels,
                    "attachments": attachments,
                    "checklists": sorted(checklists, key=lambda x: x['pos']),
                    "pos": card.get('pos', 0),
                    "closed": card.get('closed', False)
                }
                
                list_data['cards'].append(card_data)
            
            export_data['lists'].append(list_data)
        
        return export_data


def save_json(data: Any, output_path: Path, pretty: bool = True) -> None:
    """
    Save data as JSON file.
    
    Args:
        data: Data to save
        output_path: Output file path
        pretty: Enable pretty-printing
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        if pretty:
            json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            json.dump(data, f, ensure_ascii=False)
    
    print(f"✅ Saved: {output_path}")


def print_summary(data: Dict[str, Any]) -> None:
    """
    Print summary statistics of exported board.
    
    Args:
        data: Exported board data
    """
    total_cards = sum(len(lst['cards']) for lst in data['lists'])
    total_checklists = sum(
        len(card['checklists'])
        for lst in data['lists']
        for card in lst['cards']
    )
    total_attachments = sum(
        len(card['attachments'])
        for lst in data['lists']
        for card in lst['cards']
    )
    
    print(f"\n{'=' * 80}")
    print(f"EXPORT SUMMARY: {data['board']['name']}")
    print(f"{'=' * 80}")
    print(f"Lists:       {len(data['lists'])}")
    print(f"Cards:       {total_cards}")
    print(f"Checklists:  {total_checklists}")
    print(f"Attachments: {total_attachments}")
    print(f"{'=' * 80}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Export Trello board to structured JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/trello_export.py --board "Memphis Pool" --verbose
  python tools/trello_export.py --board-id 5a1b2c3d4e5f6g7h --raw
  
Environment Variables:
  TRELLO_API_KEY    Your Trello API key
  TRELLO_TOKEN      Your Trello API token
        """
    )
    
    parser.add_argument(
        '--board',
        type=str,
        help='Board name to export'
    )
    parser.add_argument(
        '--board-id',
        type=str,
        help='Board ID to export (overrides --board)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='exports/memphis_pool_board.json',
        help='Output JSON file path (default: exports/memphis_pool_board.json)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--raw',
        action='store_true',
        help='Also save raw API response for debugging'
    )
    
    args = parser.parse_args()
    
    # Validate board argument
    if not args.board and not args.board_id:
        parser.error("Either --board or --board-id is required")
    
    # Get credentials
    api_key = os.environ.get('TRELLO_API_KEY')
    token = os.environ.get('TRELLO_TOKEN')
    
    if not api_key or not token:
        print("❌ Error: Trello credentials not found in environment variables.")
        print("\nRequired environment variables:")
        print("  TRELLO_API_KEY    - Your Trello API key")
        print("  TRELLO_TOKEN      - Your Trello API token")
        print("\nSee tools/TRELLO_EXPORT_README.md for setup instructions.")
        sys.exit(1)
    
    # Initialize exporter
    exporter = TrelloExporter(api_key, token, verbose=args.verbose)
    
    print(f"\n{'=' * 80}")
    print("TRELLO BOARD EXPORT")
    print(f"{'=' * 80}\n")
    
    # Export board
    try:
        if args.board_id:
            export_data = exporter.export_board(args.board_id, use_id=True)
        else:
            export_data = exporter.export_board(args.board)
        
        # Save structured export
        output_path = Path(args.output)
        save_json(export_data, output_path, pretty=True)
        
        # Save raw export if requested
        if args.raw:
            raw_path = output_path.with_suffix('.raw.json')
            save_json(export_data, raw_path, pretty=True)
            print(f"✅ Saved raw: {raw_path}")
        
        # Print summary
        print_summary(export_data)
        
        print(f"Export complete! 🎉")
        print(f"\nUse this file for Codex analysis:")
        print(f"  {output_path.absolute()}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Export cancelled by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
