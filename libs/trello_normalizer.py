"""
Trello Export Normalization Layer

Converts raw Trello export data into an optimized, indexed structure
for O(1) lookups and fast analytics.

WHY THIS EXISTS:
- Raw exports have 374+ cards in a flat list
- Finding cards by list requires O(n) scan every time
- Finding a card by ID requires O(n) scan
- Analytics queries would repeatedly scan the same data

WITH NORMALIZATION:
- All lookups become O(1) via dictionaries
- Cards are indexed by: id, list_id, list_name
- Lists are indexed by: id, name
- Summary stats (comment_count, attachment_count) pre-computed
- No repeated scanning = instant queries

Example:
    >>> import json
    >>> from libs.trello_normalizer import normalize_trello_export
    >>> 
    >>> # Load raw export
    >>> with open('exports/board.json') as f:
    ...     raw_data = json.load(f)
    >>> 
    >>> # Normalize
    >>> normalized = normalize_trello_export(raw_data)
    >>> 
    >>> # O(1) lookups
    >>> complete_cards = normalized['cards_by_list_name']['Complete']
    >>> bills = normalized['cards_by_list_name']['BILLS']
    >>> specific_card = normalized['cards_by_id']['card_abc123']
"""

from typing import Dict, List, Any
from collections import defaultdict


def normalize_trello_export(data: dict) -> dict:
    """
    Normalize a raw Trello export into an optimized, indexed structure.
    
    Converts the raw export format:
        {
            "board": {...},
            "lists": [...],
            "cards": [...]
        }
    
    Into an indexed structure:
        {
            "board": {...},
            "lists": [...],
            "cards": [...],
            "lists_by_id": {list_id: list_obj},
            "lists_by_name": {list_name: list_obj},
            "cards_by_id": {card_id: card_obj},
            "cards_by_list_id": {list_id: [card_obj, ...]},
            "cards_by_list_name": {list_name: [card_obj, ...]}
        }
    
    Each card is enriched with:
        - list_name: str (name of the list the card belongs to)
        - comment_count: int
        - attachment_count: int
        - checklist_count: int
        - checklist_items_total: int
        - checklist_items_complete: int
    
    Args:
        data: Raw Trello export dict with board, lists, and cards
        
    Returns:
        Normalized dict with all indexes and enriched cards
        
    Example:
        >>> normalized = normalize_trello_export(raw_export)
        >>> 
        >>> # Get all cards in "Complete" list
        >>> complete = normalized['cards_by_list_name']['Complete']
        >>> print(f"Found {len(complete)} completed jobs")
        >>> 
        >>> # Get a specific card
        >>> card = normalized['cards_by_id']['card123']
        >>> print(f"{card['name']}: {card['comment_count']} comments")
        >>> 
        >>> # Get all cards in a list by ID
        >>> cards = normalized['cards_by_list_id']['list456']
    """
    board = data.get('board', {})
    lists = data.get('lists', [])
    cards = data.get('cards', [])
    
    # Build list indexes
    lists_by_id: Dict[str, dict] = {}
    lists_by_name: Dict[str, dict] = {}
    
    for lst in lists:
        list_id = lst['id']
        list_name = lst['name']
        lists_by_id[list_id] = lst
        lists_by_name[list_name] = lst
    
    # Build card indexes
    cards_by_id: Dict[str, dict] = {}
    cards_by_list_id: Dict[str, List[dict]] = defaultdict(list)
    cards_by_list_name: Dict[str, List[dict]] = defaultdict(list)
    
    for card in cards:
        card_id = card['id']
        list_id = card.get('idList')
        
        # Enrich card with list_name
        list_obj = lists_by_id.get(list_id, {})
        list_name = list_obj.get('name', 'Unknown')
        card['list_name'] = list_name
        
        # Enrich card with summary counts
        card['comment_count'] = len(card.get('comments', []))
        card['attachment_count'] = len(card.get('attachments', []))
        
        # Checklist stats
        checklists = card.get('checklists', [])
        card['checklist_count'] = len(checklists)
        
        # Count checklist items (total and complete)
        total_items = 0
        complete_items = 0
        for checklist in checklists:
            items = checklist.get('checkItems', [])
            total_items += len(items)
            complete_items += sum(1 for item in items if item.get('state') == 'complete')
        
        card['checklist_items_total'] = total_items
        card['checklist_items_complete'] = complete_items
        
        # Index by ID
        cards_by_id[card_id] = card
        
        # Index by list_id
        if list_id:
            cards_by_list_id[list_id].append(card)
        
        # Index by list_name
        if list_name:
            cards_by_list_name[list_name].append(card)
    
    # Return normalized structure
    return {
        'board': board,
        'lists': lists,
        'cards': cards,
        'lists_by_id': lists_by_id,
        'lists_by_name': lists_by_name,
        'cards_by_id': cards_by_id,
        'cards_by_list_id': dict(cards_by_list_id),
        'cards_by_list_name': dict(cards_by_list_name)
    }


def get_list_summary(normalized: dict, list_name: str) -> dict:
    """
    Get summary statistics for a specific list.
    
    Args:
        normalized: Normalized Trello export data
        list_name: Name of the list
        
    Returns:
        Dict with summary stats:
            - card_count: Total cards in list
            - total_attachments: Sum of all attachments
            - total_comments: Sum of all comments
            - total_checklists: Sum of all checklists
            - cards_with_attachments: Count of cards with 1+ attachments
            - cards_with_comments: Count of cards with 1+ comments
            
    Example:
        >>> summary = get_list_summary(normalized, 'Complete')
        >>> print(f"Complete: {summary['card_count']} cards, {summary['total_attachments']} attachments")
    """
    cards = normalized['cards_by_list_name'].get(list_name, [])
    
    return {
        'card_count': len(cards),
        'total_attachments': sum(c['attachment_count'] for c in cards),
        'total_comments': sum(c['comment_count'] for c in cards),
        'total_checklists': sum(c['checklist_count'] for c in cards),
        'cards_with_attachments': sum(1 for c in cards if c['attachment_count'] > 0),
        'cards_with_comments': sum(1 for c in cards if c['comment_count'] > 0),
        'cards_with_checklists': sum(1 for c in cards if c['checklist_count'] > 0)
    }


def get_board_summary(normalized: dict) -> dict:
    """
    Get summary statistics for the entire board.
    
    Args:
        normalized: Normalized Trello export data
        
    Returns:
        Dict with board-wide summary stats
        
    Example:
        >>> summary = get_board_summary(normalized)
        >>> print(f"Board: {summary['list_count']} lists, {summary['card_count']} cards")
    """
    return {
        'board_name': normalized['board'].get('name', 'Unknown'),
        'board_url': normalized['board'].get('url', ''),
        'list_count': len(normalized['lists']),
        'card_count': len(normalized['cards']),
        'total_attachments': sum(c['attachment_count'] for c in normalized['cards']),
        'total_comments': sum(c['comment_count'] for c in normalized['cards']),
        'total_checklists': sum(c['checklist_count'] for c in normalized['cards']),
        'lists': [
            {
                'name': lst['name'],
                'card_count': len(normalized['cards_by_list_id'].get(lst['id'], []))
            }
            for lst in normalized['lists']
        ]
    }


def find_cards_with_attachments(normalized: dict, min_count: int = 1) -> List[dict]:
    """
    Find all cards with at least min_count attachments.
    
    Args:
        normalized: Normalized Trello export data
        min_count: Minimum number of attachments (default: 1)
        
    Returns:
        List of cards with attachment_count >= min_count
        
    Example:
        >>> # Find cards with work orders (typically have 2+ attachments)
        >>> work_orders = find_cards_with_attachments(normalized, min_count=2)
        >>> print(f"Found {len(work_orders)} work orders")
    """
    return [
        card for card in normalized['cards']
        if card['attachment_count'] >= min_count
    ]


def find_cards_by_name_pattern(normalized: dict, pattern: str, case_sensitive: bool = False) -> List[dict]:
    """
    Find cards whose name contains a specific pattern.
    
    Args:
        normalized: Normalized Trello export data
        pattern: String pattern to search for in card names
        case_sensitive: Whether search is case-sensitive (default: False)
        
    Returns:
        List of matching cards
        
    Example:
        >>> # Find all jobs for a specific customer
        >>> peggy_jobs = find_cards_by_name_pattern(normalized, "PEGGY")
        >>> print(f"Found {len(peggy_jobs)} jobs for Peggy")
    """
    if not case_sensitive:
        pattern = pattern.lower()
        return [
            card for card in normalized['cards']
            if pattern in card['name'].lower()
        ]
    else:
        return [
            card for card in normalized['cards']
            if pattern in card['name']
        ]


def group_cards_by_field(normalized: dict, field: str) -> Dict[Any, List[dict]]:
    """
    Group cards by any field value.
    
    Args:
        normalized: Normalized Trello export data
        field: Field name to group by (e.g., 'due', 'list_name')
        
    Returns:
        Dict mapping field values to lists of cards
        
    Example:
        >>> # Group cards by due date
        >>> by_date = group_cards_by_field(normalized, 'due')
        >>> for date, cards in by_date.items():
        ...     if date:
        ...         print(f"{date}: {len(cards)} cards due")
    """
    grouped: Dict[Any, List[dict]] = defaultdict(list)
    
    for card in normalized['cards']:
        value = card.get(field)
        grouped[value].append(card)
    
    return dict(grouped)


if __name__ == '__main__':
    # Example usage / testing
    import json
    import sys
    
    if len(sys.argv) > 1:
        # Load and normalize a Trello export
        export_file = sys.argv[1]
        print(f"Normalizing {export_file}...")
        
        with open(export_file, 'r') as f:
            raw_data = json.load(f)
        
        normalized = normalize_trello_export(raw_data)
        
        # Print summary
        summary = get_board_summary(normalized)
        print(f"\n{'='*70}")
        print(f"Board: {summary['board_name']}")
        print(f"{'='*70}")
        print(f"Lists: {summary['list_count']}")
        print(f"Cards: {summary['card_count']}")
        print(f"Attachments: {summary['total_attachments']}")
        print(f"Comments: {summary['total_comments']}")
        print(f"Checklists: {summary['total_checklists']}")
        print(f"\nCards per list:")
        for lst in summary['lists']:
            if lst['card_count'] > 0:
                print(f"  • {lst['name']:40s} {lst['card_count']:3d} cards")
        
        # Show cards with attachments
        with_attachments = find_cards_with_attachments(normalized, min_count=1)
        print(f"\nCards with attachments: {len(with_attachments)}")
        
        # Show work orders (cards with 2+ attachments)
        work_orders = find_cards_with_attachments(normalized, min_count=2)
        print(f"Cards with 2+ attachments (likely work orders): {len(work_orders)}")
        
        print(f"\n{'='*70}")
        print("Normalization complete! Indexes created:")
        print("  • lists_by_id")
        print("  • lists_by_name")
        print("  • cards_by_id")
        print("  • cards_by_list_id")
        print("  • cards_by_list_name")
        print(f"{'='*70}\n")
    else:
        print("Usage: python libs/trello_normalizer.py <export_file.json>")
        print("Example: python libs/trello_normalizer.py exports/memphis_pool_board.json")
