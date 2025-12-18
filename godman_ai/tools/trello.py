"""Trello integration tools for part identification and favorites management."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Set

from libs.trello_client import TrelloClient, TrelloError

logger = logging.getLogger(__name__)


class FavoritesManager:
    """Manages favorite parts with persistence to JSON file.
    
    Attributes:
        storage_path: Path to JSON file storing favorites
        favorites: Set of favorite part numbers/identifiers
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize favorites manager.
        
        Args:
            storage_path: Path to JSON storage file. Defaults to data/favorites.json
        """
        if storage_path is None:
            repo_root = Path(__file__).resolve().parents[2]
            storage_path = repo_root / "data" / "favorites.json"
        
        self.storage_path = Path(storage_path)
        self.favorites: Set[str] = set()
        self._load()
    
    def _load(self) -> None:
        """Load favorites from JSON file."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.favorites = set(data.get("favorites", []))
                logger.info(f"Loaded {len(self.favorites)} favorites from {self.storage_path}")
            except Exception as e:
                logger.error(f"Failed to load favorites from {self.storage_path}: {e}")
                self.favorites = set()
        else:
            logger.info(f"No favorites file found at {self.storage_path}, starting fresh")
    
    def _save(self) -> None:
        """Save favorites to JSON file."""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump({"favorites": sorted(list(self.favorites))}, f, indent=2)
            logger.info(f"Saved {len(self.favorites)} favorites to {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to save favorites to {self.storage_path}: {e}")
    
    def add(self, part_id: str) -> bool:
        """Add a part to favorites.
        
        Args:
            part_id: Part number or identifier
            
        Returns:
            True if added (new), False if already existed
        """
        if part_id in self.favorites:
            return False
        self.favorites.add(part_id)
        self._save()
        logger.info(f"Added {part_id} to favorites")
        return True
    
    def remove(self, part_id: str) -> bool:
        """Remove a part from favorites.
        
        Args:
            part_id: Part number or identifier
            
        Returns:
            True if removed, False if not found
        """
        if part_id not in self.favorites:
            return False
        self.favorites.remove(part_id)
        self._save()
        logger.info(f"Removed {part_id} from favorites")
        return True
    
    def is_favorite(self, part_id: str) -> bool:
        """Check if a part is marked as favorite.
        
        Args:
            part_id: Part number or identifier
            
        Returns:
            True if part is in favorites
        """
        return part_id in self.favorites
    
    def list_all(self) -> list[str]:
        """Get all favorite parts.
        
        Returns:
            Sorted list of favorite part identifiers
        """
        return sorted(list(self.favorites))


def add_part_info_to_card(
    card_id: str, 
    part_info: Dict[str, Any], 
    favorite: bool = False,
    trello_client: Optional[TrelloClient] = None
) -> Dict[str, Any]:
    """Add part identification info to a Trello card as a formatted comment.
    
    Formats part information into a Markdown block with:
    - Primary match details (part number, confidence, description)
    - Alternative matches (if any)
    - Cross-reference equivalents (if any)
    - Favorite indicator (★ emoji prefix) when marked as favorite
    
    Args:
        card_id: Trello card ID or short link
        part_info: Dictionary containing part identification results with keys:
                   - primary_match: dict with 'part_number', 'confidence', 'description'
                   - alternatives: optional list of alternative matches
                   - equivalents: optional list of cross-reference part numbers
                   - dimensions: optional dict with measurements
        favorite: Whether to mark this part as a favorite (adds ★ prefix)
        trello_client: Optional TrelloClient instance (creates new if not provided)
    
    Returns:
        API response dictionary containing the created comment
    
    Raises:
        TrelloError: If API call fails
        ValueError: If part_info is missing required fields
        
    Example:
        >>> part_info = {
        ...     "primary_match": {
        ...         "part_number": "SPX1091Z2",
        ...         "confidence": 0.95,
        ...         "description": "Housing Assembly"
        ...     },
        ...     "alternatives": [
        ...         {"part_number": "SPX1091Z1", "confidence": 0.75}
        ...     ],
        ...     "equivalents": ["HAY-SPX1091Z2", "PEN-355331"]
        ... }
        >>> result = add_part_info_to_card("abc123", part_info, favorite=True)
    """
    # Validate input
    if not part_info:
        raise ValueError("part_info cannot be empty")
    
    primary = part_info.get("primary_match")
    if not primary:
        raise ValueError("part_info must contain 'primary_match' key")
    
    part_number = primary.get("part_number")
    confidence = primary.get("confidence", 0.0)
    description = primary.get("description", "")
    
    if not part_number:
        raise ValueError("primary_match must contain 'part_number'")
    
    # Build Markdown comment
    lines = []
    
    # Add favorite indicator
    if favorite:
        lines.append("★ **Favorite Part**\n")
    
    # Primary match section
    lines.append("## 🔍 Part Identification")
    lines.append(f"**Part Number:** `{part_number}`")
    lines.append(f"**Confidence:** {confidence:.1%}")
    
    if description:
        lines.append(f"**Description:** {description}")
    
    # Dimensions if available
    dimensions = part_info.get("dimensions")
    if dimensions:
        lines.append("\n### 📏 Dimensions")
        for key, value in dimensions.items():
            lines.append(f"- **{key.title()}:** {value}")
    
    # Alternative matches
    alternatives = part_info.get("alternatives", [])
    if alternatives:
        lines.append("\n### 🔄 Alternative Matches")
        for i, alt in enumerate(alternatives[:3], 1):  # Limit to top 3
            alt_number = alt.get("part_number", "Unknown")
            alt_conf = alt.get("confidence", 0.0)
            alt_desc = alt.get("description", "")
            lines.append(f"{i}. `{alt_number}` ({alt_conf:.1%})")
            if alt_desc:
                lines.append(f"   - {alt_desc}")
    
    # Cross-reference equivalents
    equivalents = part_info.get("equivalents", [])
    if equivalents:
        lines.append("\n### 🔗 Cross-Reference Equivalents")
        for equiv in equivalents:
            lines.append(f"- `{equiv}`")
    
    # Additional notes
    notes = part_info.get("notes")
    if notes:
        lines.append(f"\n### 📝 Notes")
        lines.append(notes)
    
    comment_text = "\n".join(lines)
    
    # Post comment to Trello
    client = trello_client or TrelloClient()
    
    try:
        logger.info(f"Posting part info to card {card_id} (favorite={favorite})")
        
        # Trello API endpoint for adding comments
        response = client.request(
            "POST",
            f"cards/{card_id}/actions/comments",
            params={"text": comment_text}
        )
        
        logger.info(f"Successfully added comment to card {card_id}")
        return response
        
    except TrelloError as e:
        logger.error(f"Failed to add comment to card {card_id}: {e}")
        raise


def get_card_part_comments(
    card_id: str,
    trello_client: Optional[TrelloClient] = None
) -> list[Dict[str, Any]]:
    """Retrieve all part identification comments from a card.
    
    Filters card comments to return only those containing part identification data
    (identified by the "Part Identification" header).
    
    Args:
        card_id: Trello card ID or short link
        trello_client: Optional TrelloClient instance
        
    Returns:
        List of comment dictionaries containing part info
        
    Example:
        >>> comments = get_card_part_comments("abc123")
        >>> for comment in comments:
        ...     print(comment['data']['text'])
    """
    client = trello_client or TrelloClient()
    
    try:
        # Get card with comment actions
        card = client.get_card(
            card_id,
            attachments=False,
            actions=True,
            action_types="commentCard"
        )
        
        # Filter for part identification comments
        part_comments = []
        for action in card.get("actions", []):
            if action.get("type") == "commentCard":
                text = action.get("data", {}).get("text", "")
                if "Part Identification" in text or "★" in text:
                    part_comments.append(action)
        
        logger.info(f"Found {len(part_comments)} part comments on card {card_id}")
        return part_comments
        
    except TrelloError as e:
        logger.error(f"Failed to retrieve comments from card {card_id}: {e}")
        raise


__all__ = [
    "FavoritesManager",
    "add_part_info_to_card",
    "get_card_part_comments",
]
