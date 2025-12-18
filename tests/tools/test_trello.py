"""Tests for Trello integration tools."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from godman_ai.tools.trello import (
    FavoritesManager,
    add_part_info_to_card,
    get_card_part_comments,
)
from libs.trello_client import TrelloError


@pytest.fixture
def temp_favorites_file(tmp_path):
    """Create a temporary favorites file."""
    return tmp_path / "test_favorites.json"


@pytest.fixture
def favorites_manager(temp_favorites_file):
    """Create a FavoritesManager with temp storage."""
    return FavoritesManager(temp_favorites_file)


class TestFavoritesManager:
    """Test suite for FavoritesManager."""
    
    def test_init_creates_empty_favorites(self, favorites_manager):
        """Test initialization with no existing file."""
        assert len(favorites_manager.favorites) == 0
        assert favorites_manager.list_all() == []
    
    def test_add_favorite(self, favorites_manager):
        """Test adding a part to favorites."""
        result = favorites_manager.add("SPX1091Z2")
        assert result is True
        assert favorites_manager.is_favorite("SPX1091Z2")
        assert "SPX1091Z2" in favorites_manager.list_all()
    
    def test_add_duplicate_favorite(self, favorites_manager):
        """Test adding the same part twice."""
        favorites_manager.add("SPX1091Z2")
        result = favorites_manager.add("SPX1091Z2")
        assert result is False  # Already existed
        assert len(favorites_manager.favorites) == 1
    
    def test_remove_favorite(self, favorites_manager):
        """Test removing a part from favorites."""
        favorites_manager.add("SPX1091Z2")
        result = favorites_manager.remove("SPX1091Z2")
        assert result is True
        assert not favorites_manager.is_favorite("SPX1091Z2")
    
    def test_remove_nonexistent_favorite(self, favorites_manager):
        """Test removing a part that isn't in favorites."""
        result = favorites_manager.remove("NOTEXIST")
        assert result is False
    
    def test_persistence(self, temp_favorites_file):
        """Test that favorites persist across instances."""
        # Add favorites in first instance
        mgr1 = FavoritesManager(temp_favorites_file)
        mgr1.add("PART1")
        mgr1.add("PART2")
        mgr1.add("PART3")
        
        # Load in second instance
        mgr2 = FavoritesManager(temp_favorites_file)
        assert mgr2.is_favorite("PART1")
        assert mgr2.is_favorite("PART2")
        assert mgr2.is_favorite("PART3")
        assert len(mgr2.list_all()) == 3
    
    def test_list_all_sorted(self, favorites_manager):
        """Test that list_all returns sorted results."""
        favorites_manager.add("ZEBRA")
        favorites_manager.add("ALPHA")
        favorites_manager.add("MIKE")
        
        result = favorites_manager.list_all()
        assert result == ["ALPHA", "MIKE", "ZEBRA"]


class TestAddPartInfoToCard:
    """Test suite for add_part_info_to_card function."""
    
    @pytest.fixture
    def mock_trello_client(self):
        """Create a mock TrelloClient."""
        mock_client = MagicMock()
        mock_client.request.return_value = {
            "id": "comment123",
            "data": {"text": "test comment"},
            "date": "2025-12-18T00:00:00.000Z"
        }
        return mock_client
    
    @pytest.fixture
    def sample_part_info(self):
        """Sample part info for testing."""
        return {
            "primary_match": {
                "part_number": "SPX1091Z2",
                "confidence": 0.95,
                "description": "Housing Assembly"
            },
            "alternatives": [
                {
                    "part_number": "SPX1091Z1",
                    "confidence": 0.75,
                    "description": "Older Model"
                }
            ],
            "equivalents": ["PEN-355331", "JAC-39310700"],
            "dimensions": {
                "outer_diameter": "8.5 inches",
                "thread_size": "2 inch"
            }
        }
    
    def test_add_part_info_basic(self, mock_trello_client, sample_part_info):
        """Test adding basic part info to a card."""
        result = add_part_info_to_card(
            card_id="abc123",
            part_info=sample_part_info,
            trello_client=mock_trello_client
        )
        
        assert result["id"] == "comment123"
        mock_trello_client.request.assert_called_once()
        
        # Verify the comment text was passed
        call_args = mock_trello_client.request.call_args
        assert call_args[0][0] == "POST"
        assert "cards/abc123/actions/comments" in call_args[0][1]
        
        comment_text = call_args[1]["params"]["text"]
        assert "SPX1091Z2" in comment_text
        assert "0.95" in comment_text or "95" in comment_text
        assert "Housing Assembly" in comment_text
    
    def test_add_part_info_with_favorite(self, mock_trello_client, sample_part_info):
        """Test adding part info with favorite flag."""
        result = add_part_info_to_card(
            card_id="abc123",
            part_info=sample_part_info,
            favorite=True,
            trello_client=mock_trello_client
        )
        
        call_args = mock_trello_client.request.call_args
        comment_text = call_args[1]["params"]["text"]
        assert "★" in comment_text
        assert "Favorite Part" in comment_text
    
    def test_add_part_info_with_alternatives(self, mock_trello_client, sample_part_info):
        """Test that alternatives are included in comment."""
        result = add_part_info_to_card(
            card_id="abc123",
            part_info=sample_part_info,
            trello_client=mock_trello_client
        )
        
        call_args = mock_trello_client.request.call_args
        comment_text = call_args[1]["params"]["text"]
        assert "Alternative Matches" in comment_text
        assert "SPX1091Z1" in comment_text
    
    def test_add_part_info_with_equivalents(self, mock_trello_client, sample_part_info):
        """Test that equivalents are included in comment."""
        result = add_part_info_to_card(
            card_id="abc123",
            part_info=sample_part_info,
            trello_client=mock_trello_client
        )
        
        call_args = mock_trello_client.request.call_args
        comment_text = call_args[1]["params"]["text"]
        assert "Cross-Reference Equivalents" in comment_text
        assert "PEN-355331" in comment_text
        assert "JAC-39310700" in comment_text
    
    def test_add_part_info_with_dimensions(self, mock_trello_client, sample_part_info):
        """Test that dimensions are included in comment."""
        result = add_part_info_to_card(
            card_id="abc123",
            part_info=sample_part_info,
            trello_client=mock_trello_client
        )
        
        call_args = mock_trello_client.request.call_args
        comment_text = call_args[1]["params"]["text"]
        assert "Dimensions" in comment_text
        assert "8.5 inches" in comment_text
        assert "2 inch" in comment_text
    
    def test_add_part_info_missing_primary_match(self, mock_trello_client):
        """Test error when primary_match is missing."""
        with pytest.raises(ValueError, match="must contain 'primary_match'"):
            add_part_info_to_card(
                card_id="abc123",
                part_info={},
                trello_client=mock_trello_client
            )
    
    def test_add_part_info_missing_part_number(self, mock_trello_client):
        """Test error when part_number is missing."""
        with pytest.raises(ValueError, match="must contain 'part_number'"):
            add_part_info_to_card(
                card_id="abc123",
                part_info={"primary_match": {"confidence": 0.9}},
                trello_client=mock_trello_client
            )
    
    def test_add_part_info_trello_error(self, mock_trello_client, sample_part_info):
        """Test handling of Trello API errors."""
        mock_trello_client.request.side_effect = TrelloError("API Error")
        
        with pytest.raises(TrelloError):
            add_part_info_to_card(
                card_id="abc123",
                part_info=sample_part_info,
                trello_client=mock_trello_client
            )


class TestGetCardPartComments:
    """Test suite for get_card_part_comments function."""
    
    @pytest.fixture
    def mock_trello_client(self):
        """Create a mock TrelloClient."""
        mock_client = MagicMock()
        mock_client.get_card.return_value = {
            "id": "card123",
            "name": "Test Card",
            "actions": [
                {
                    "type": "commentCard",
                    "data": {
                        "text": "## 🔍 Part Identification\n**Part Number:** `SPX1091Z2`"
                    }
                },
                {
                    "type": "commentCard",
                    "data": {
                        "text": "Regular comment without part info"
                    }
                },
                {
                    "type": "commentCard",
                    "data": {
                        "text": "★ **Favorite Part**\n## 🔍 Part Identification"
                    }
                }
            ]
        }
        return mock_client
    
    def test_get_card_part_comments(self, mock_trello_client):
        """Test retrieving part identification comments."""
        result = get_card_part_comments("card123", mock_trello_client)
        
        assert len(result) == 2  # Only 2 part comments
        assert all("Part Identification" in r["data"]["text"] or "★" in r["data"]["text"] 
                   for r in result)
    
    def test_get_card_part_comments_empty(self, mock_trello_client):
        """Test when card has no part comments."""
        mock_trello_client.get_card.return_value = {
            "id": "card123",
            "actions": [
                {"type": "commentCard", "data": {"text": "Regular comment"}}
            ]
        }
        
        result = get_card_part_comments("card123", mock_trello_client)
        assert len(result) == 0
    
    def test_get_card_part_comments_error(self, mock_trello_client):
        """Test handling of Trello API errors."""
        mock_trello_client.get_card.side_effect = TrelloError("API Error")
        
        with pytest.raises(TrelloError):
            get_card_part_comments("card123", mock_trello_client)
