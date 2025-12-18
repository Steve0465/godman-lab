"""Tests for PartIdentifierWorkflow."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock

from godman_ai.workflows.part_identifier_workflow import PartIdentifierWorkflow
from godman_ai.tools.trello import FavoritesManager


@pytest.fixture
def temp_favorites_file(tmp_path):
    """Create a temporary favorites file."""
    return tmp_path / "test_favorites.json"


@pytest.fixture
def workflow(temp_favorites_file):
    """Create a PartIdentifierWorkflow with temp storage."""
    return PartIdentifierWorkflow(temp_favorites_file)


class TestPartIdentifierWorkflow:
    """Test suite for PartIdentifierWorkflow."""
    
    @pytest.mark.asyncio
    async def test_identify_part_with_image(self, workflow):
        """Test identifying a part from an image."""
        result = await workflow.identify_part(
            image_path=Path("/fake/path/part.jpg")
        )
        
        assert result["primary_match"] is not None
        assert "part_number" in result["primary_match"]
        assert "confidence" in result["primary_match"]
        assert isinstance(result["alternatives"], list)
        assert isinstance(result["equivalents"], list)
    
    @pytest.mark.asyncio
    async def test_identify_part_with_description(self, workflow):
        """Test identifying a part from text description."""
        result = await workflow.identify_part(
            description="Hayward Super Pump housing assembly"
        )
        
        assert result["primary_match"] is not None
        assert result["primary_match"]["part_number"] is not None
    
    @pytest.mark.asyncio
    async def test_identify_part_no_input(self, workflow):
        """Test error when no image or description provided."""
        with pytest.raises(ValueError, match="Must provide either image_path or description"):
            await workflow.identify_part()
    
    @pytest.mark.asyncio
    async def test_identify_part_with_favorite(self, workflow):
        """Test identifying a part that is marked as favorite."""
        # Add part to favorites first
        workflow.add_favorite("SPX1091Z2")
        
        result = await workflow.identify_part(
            image_path=Path("/fake/path/part.jpg")
        )
        
        assert result["is_favorite"] is True
    
    @pytest.mark.asyncio
    async def test_identify_part_not_favorite(self, workflow):
        """Test identifying a part that is not a favorite."""
        result = await workflow.identify_part(
            image_path=Path("/fake/path/part.jpg")
        )
        
        assert result["is_favorite"] is False
    
    @pytest.mark.asyncio
    @patch("godman_ai.workflows.part_identifier_workflow.add_part_info_to_card")
    async def test_identify_part_with_trello_card(self, mock_add_comment, workflow):
        """Test identifying a part and posting to Trello."""
        mock_add_comment.return_value = {"id": "comment123"}
        
        result = await workflow.identify_part(
            image_path=Path("/fake/path/part.jpg"),
            card_id="abc123"
        )
        
        assert result["trello_comment"] is not None
        assert result["trello_comment"]["id"] == "comment123"
        
        # Verify add_part_info_to_card was called
        mock_add_comment.assert_called_once()
        call_args = mock_add_comment.call_args
        assert call_args[1]["card_id"] == "abc123"
        assert "primary_match" in call_args[1]["part_info"]
    
    @pytest.mark.asyncio
    @patch("godman_ai.workflows.part_identifier_workflow.add_part_info_to_card")
    async def test_identify_part_with_trello_favorite(self, mock_add_comment, workflow):
        """Test that favorite flag is passed to Trello."""
        mock_add_comment.return_value = {"id": "comment123"}
        
        # Mark part as favorite
        workflow.add_favorite("SPX1091Z2")
        
        result = await workflow.identify_part(
            image_path=Path("/fake/path/part.jpg"),
            card_id="abc123"
        )
        
        # Verify favorite=True was passed
        call_args = mock_add_comment.call_args
        assert call_args[1]["favorite"] is True
    
    @pytest.mark.asyncio
    async def test_identify_part_without_trello(self, workflow):
        """Test identifying a part without Trello integration."""
        result = await workflow.identify_part(
            image_path=Path("/fake/path/part.jpg")
        )
        
        assert result["trello_comment"] is None
    
    @pytest.mark.asyncio
    @patch("godman_ai.workflows.part_identifier_workflow.add_part_info_to_card")
    async def test_identify_part_trello_error(self, mock_add_comment, workflow):
        """Test handling of Trello errors."""
        mock_add_comment.side_effect = Exception("Trello API Error")
        
        result = await workflow.identify_part(
            image_path=Path("/fake/path/part.jpg"),
            card_id="abc123"
        )
        
        # Workflow should continue despite Trello error
        assert result["primary_match"] is not None
        assert result["trello_comment"] is None
    
    def test_add_favorite(self, workflow):
        """Test adding a part to favorites."""
        result = workflow.add_favorite("TEST123")
        assert result is True
        assert "TEST123" in workflow.list_favorites()
    
    def test_remove_favorite(self, workflow):
        """Test removing a part from favorites."""
        workflow.add_favorite("TEST123")
        result = workflow.remove_favorite("TEST123")
        assert result is True
        assert "TEST123" not in workflow.list_favorites()
    
    def test_list_favorites(self, workflow):
        """Test listing all favorites."""
        workflow.add_favorite("PART1")
        workflow.add_favorite("PART2")
        workflow.add_favorite("PART3")
        
        favorites = workflow.list_favorites()
        assert len(favorites) == 3
        assert favorites == ["PART1", "PART2", "PART3"]
    
    @pytest.mark.asyncio
    async def test_workflow_includes_dimensions(self, workflow):
        """Test that dimensions are included in results."""
        result = await workflow.identify_part(
            image_path=Path("/fake/path/part.jpg")
        )
        
        assert result["dimensions"] is not None
        assert isinstance(result["dimensions"], dict)
    
    @pytest.mark.asyncio
    async def test_workflow_includes_alternatives(self, workflow):
        """Test that alternative matches are included."""
        result = await workflow.identify_part(
            image_path=Path("/fake/path/part.jpg")
        )
        
        assert len(result["alternatives"]) > 0
        for alt in result["alternatives"]:
            assert "part_number" in alt
            assert "confidence" in alt
    
    @pytest.mark.asyncio
    async def test_workflow_includes_equivalents(self, workflow):
        """Test that cross-reference equivalents are included."""
        result = await workflow.identify_part(
            image_path=Path("/fake/path/part.jpg")
        )
        
        assert len(result["equivalents"]) > 0
        assert all(isinstance(eq, str) for eq in result["equivalents"])


class TestPartIdentifierWorkflowIntegration:
    """Integration tests for full workflow execution."""
    
    @pytest.mark.asyncio
    @patch("godman_ai.workflows.part_identifier_workflow.add_part_info_to_card")
    async def test_full_workflow_with_favorite_and_trello(
        self, 
        mock_add_comment,
        temp_favorites_file
    ):
        """Test complete workflow: identify part, check favorite, post to Trello."""
        mock_add_comment.return_value = {"id": "comment123"}
        
        workflow = PartIdentifierWorkflow(temp_favorites_file)
        
        # Mark part as favorite
        workflow.add_favorite("SPX1091Z2")
        
        # Run full workflow
        result = await workflow.identify_part(
            image_path=Path("/fake/path/pump.jpg"),
            description="Hayward pump housing",
            card_id="trello123"
        )
        
        # Verify all aspects of result
        assert result["primary_match"]["part_number"] == "SPX1091Z2"
        assert result["is_favorite"] is True
        assert result["trello_comment"]["id"] == "comment123"
        assert len(result["alternatives"]) > 0
        assert len(result["equivalents"]) > 0
        
        # Verify Trello was called with correct favorite flag
        call_args = mock_add_comment.call_args
        assert call_args[1]["favorite"] is True
        assert call_args[1]["card_id"] == "trello123"
