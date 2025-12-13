"""
Trello Metrics Module

Provides analytics and metrics calculation for normalized Trello exports.
All functions accept normalized data from trello_normalizer and return
simple data structures (dicts, lists) without I/O or printing.

Usage:
    from libs.trello_normalizer import normalize_trello_export
    from libs.trello_metrics import cards_per_list, average_comments_per_card
    
    normalized = normalize_trello_export(raw_data)
    metrics = cards_per_list(normalized)
"""

from typing import Any


def cards_per_list(normalized_data: dict[str, Any]) -> dict[str, int]:
    """
    Count cards in each list.
    
    Args:
        normalized_data: Output from normalize_trello_export()
        
    Returns:
        Dictionary mapping list_name -> card_count
        
    Example:
        {
            "SAFETY COVER INSTALLS": 45,
            "LINER INSTALLS": 32,
            "Completed": 346
        }
    """
    return {
        list_name: len(cards)
        for list_name, cards in normalized_data["cards_by_list_name"].items()
    }


def average_comments_per_card(normalized_data: dict[str, Any]) -> float:
    """
    Calculate average number of comments per card across all cards.
    
    Args:
        normalized_data: Output from normalize_trello_export()
        
    Returns:
        Average comment count (float), or 0.0 if no cards
    """
    cards = normalized_data["cards_by_id"].values()
    if not cards:
        return 0.0
    
    total_comments = sum(card.get("comment_count", 0) for card in cards)
    return total_comments / len(cards)


def average_attachments_per_card(normalized_data: dict[str, Any]) -> float:
    """
    Calculate average number of attachments per card across all cards.
    
    Args:
        normalized_data: Output from normalize_trello_export()
        
    Returns:
        Average attachment count (float), or 0.0 if no cards
    """
    cards = normalized_data["cards_by_id"].values()
    if not cards:
        return 0.0
    
    total_attachments = sum(card.get("attachment_count", 0) for card in cards)
    return total_attachments / len(cards)


def cards_with_no_attachments(normalized_data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Find all cards that have zero attachments.
    
    Args:
        normalized_data: Output from normalize_trello_export()
        
    Returns:
        List of card objects with attachment_count == 0
        
    Use case:
        Identify jobs missing photos/documents for billing or records
    """
    return [
        card
        for card in normalized_data["cards_by_id"].values()
        if card.get("attachment_count", 0) == 0
    ]


def cards_with_no_comments(normalized_data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Find all cards that have zero comments.
    
    Args:
        normalized_data: Output from normalize_trello_export()
        
    Returns:
        List of card objects with comment_count == 0
        
    Use case:
        Identify jobs with no status updates or work notes
    """
    return [
        card
        for card in normalized_data["cards_by_id"].values()
        if card.get("comment_count", 0) == 0
    ]


def cards_missing_both(normalized_data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Find cards with neither attachments nor comments.
    
    Args:
        normalized_data: Output from normalize_trello_export()
        
    Returns:
        List of card objects with both counts == 0
        
    Use case:
        High-risk cards: no documentation, no notes
    """
    return [
        card
        for card in normalized_data["cards_by_id"].values()
        if card.get("attachment_count", 0) == 0 
        and card.get("comment_count", 0) == 0
    ]


def cards_by_list_summary(normalized_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """
    Generate summary statistics for each list.
    
    Args:
        normalized_data: Output from normalize_trello_export()
        
    Returns:
        Dictionary mapping list_name -> stats dict:
        {
            "SAFETY COVER INSTALLS": {
                "card_count": 45,
                "avg_comments": 2.3,
                "avg_attachments": 4.1,
                "cards_missing_attachments": 5,
                "cards_missing_comments": 12
            }
        }
    """
    summary = {}
    
    for list_name, cards in normalized_data["cards_by_list_name"].items():
        if not cards:
            summary[list_name] = {
                "card_count": 0,
                "avg_comments": 0.0,
                "avg_attachments": 0.0,
                "cards_missing_attachments": 0,
                "cards_missing_comments": 0,
                "cards_missing_both": 0
            }
            continue
        
        total_comments = sum(card.get("comment_count", 0) for card in cards)
        total_attachments = sum(card.get("attachment_count", 0) for card in cards)
        
        missing_attachments = sum(
            1 for card in cards if card.get("attachment_count", 0) == 0
        )
        missing_comments = sum(
            1 for card in cards if card.get("comment_count", 0) == 0
        )
        missing_both = sum(
            1 for card in cards 
            if card.get("attachment_count", 0) == 0 
            and card.get("comment_count", 0) == 0
        )
        
        summary[list_name] = {
            "card_count": len(cards),
            "avg_comments": total_comments / len(cards),
            "avg_attachments": total_attachments / len(cards),
            "cards_missing_attachments": missing_attachments,
            "cards_missing_comments": missing_comments,
            "cards_missing_both": missing_both
        }
    
    return summary


def total_cards(normalized_data: dict[str, Any]) -> int:
    """
    Count total cards across all lists.
    
    Args:
        normalized_data: Output from normalize_trello_export()
        
    Returns:
        Total number of cards
    """
    return len(normalized_data["cards_by_id"])


def total_lists(normalized_data: dict[str, Any]) -> int:
    """
    Count total lists in board.
    
    Args:
        normalized_data: Output from normalize_trello_export()
        
    Returns:
        Total number of lists
    """
    return len(normalized_data["lists_by_id"])
