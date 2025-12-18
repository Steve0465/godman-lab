"""Part identification workflow with Trello integration and favorites support."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from godman_ai.workflows.engine import Context, Step, Workflow
from godman_ai.tools.trello import FavoritesManager, add_part_info_to_card

logger = logging.getLogger(__name__)


class PartIdentifierWorkflow:
    """Workflow for identifying pool parts with Trello card integration.
    
    This workflow:
    1. Analyzes part images or descriptions using AI/vision models
    2. Identifies the part with confidence score and alternatives
    3. Optionally posts results to a Trello card as a formatted comment
    4. Marks parts as favorites based on FavoritesManager
    
    Attributes:
        favorites_manager: Manager for tracking favorite parts
    """
    
    def __init__(self, favorites_storage_path: Optional[Path] = None):
        """Initialize part identifier workflow.
        
        Args:
            favorites_storage_path: Optional custom path for favorites storage
        """
        self.favorites_manager = FavoritesManager(favorites_storage_path)
    
    async def identify_part(
        self,
        image_path: Optional[Path] = None,
        description: Optional[str] = None,
        card_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Identify a pool part and optionally post to Trello card.
        
        Args:
            image_path: Path to part image for vision analysis
            description: Text description of the part
            card_id: Optional Trello card ID to post results
            **kwargs: Additional parameters for part identification
            
        Returns:
            Dictionary with:
                - primary_match: Best matching part with confidence
                - alternatives: List of alternative matches
                - equivalents: Cross-reference part numbers
                - is_favorite: Whether part is marked as favorite
                - trello_comment: Trello API response if card_id provided
                
        Raises:
            ValueError: If neither image_path nor description provided
            
        Example:
            >>> workflow = PartIdentifierWorkflow()
            >>> result = await workflow.identify_part(
            ...     image_path=Path("pump_housing.jpg"),
            ...     card_id="abc123"
            ... )
            >>> print(result["primary_match"]["part_number"])
            'SPX1091Z2'
        """
        if not image_path and not description:
            raise ValueError("Must provide either image_path or description")
        
        # Build workflow context
        ctx = Context()
        ctx.set("image_path", image_path)
        ctx.set("description", description)
        ctx.set("card_id", card_id)
        ctx.set("kwargs", kwargs)
        
        # Define workflow steps
        steps = [
            Step("analyze_part", self._analyze_part_step),
            Step("enrich_with_equivalents", self._enrich_equivalents_step),
            Step("check_favorite", self._check_favorite_step),
            Step("post_to_trello", self._post_to_trello_step),
        ]
        
        workflow = Workflow(
            steps=steps,
            before_all=lambda c: logger.info("Starting part identification workflow"),
            after_all=lambda c: logger.info("Part identification workflow complete"),
        )
        
        # Execute workflow
        result_ctx = await workflow.run(ctx)
        
        # Build result dictionary
        return {
            "primary_match": result_ctx.get("primary_match"),
            "alternatives": result_ctx.get("alternatives", []),
            "equivalents": result_ctx.get("equivalents", []),
            "dimensions": result_ctx.get("dimensions"),
            "is_favorite": result_ctx.get("is_favorite", False),
            "trello_comment": result_ctx.get("trello_comment"),
        }
    
    async def _analyze_part_step(self, ctx: Context) -> Dict[str, Any]:
        """Step 1: Analyze part image/description to identify part number.
        
        This is a placeholder for integration with vision AI models (Gemini, GPT-4V, etc.)
        or part database lookup. In production, this would call your AI model.
        """
        image_path = ctx.get("image_path")
        description = ctx.get("description")
        
        logger.info(f"Analyzing part (image={image_path}, desc={description[:50] if description else None}...)")
        
        # PLACEHOLDER: Replace with actual AI/vision model integration
        # Example integration points:
        # - Google Gemini Vision API
        # - OpenAI GPT-4 Vision
        # - Custom CNN model
        # - Database lookup by description keywords
        
        # Mock response for demonstration
        primary_match = {
            "part_number": "SPX1091Z2",
            "confidence": 0.95,
            "description": "Super Pump Housing Assembly",
            "manufacturer": "Hayward",
        }
        
        alternatives = [
            {
                "part_number": "SPX1091Z1",
                "confidence": 0.78,
                "description": "Super Pump Housing (Older Model)",
                "manufacturer": "Hayward",
            },
            {
                "part_number": "SPX1500Z2",
                "confidence": 0.65,
                "description": "Power-Flo Housing Assembly",
                "manufacturer": "Hayward",
            }
        ]
        
        dimensions = {
            "outer_diameter": "8.5 inches",
            "thread_size": "2 inch",
            "material": "Thermoplastic",
        }
        
        # Store in context
        ctx.set("primary_match", primary_match)
        ctx.set("alternatives", alternatives)
        ctx.set("dimensions", dimensions)
        
        logger.info(f"Identified part: {primary_match['part_number']} (confidence: {primary_match['confidence']:.1%})")
        
        return {
            "primary_match": primary_match,
            "alternatives": alternatives,
            "dimensions": dimensions,
        }
    
    async def _enrich_equivalents_step(self, ctx: Context) -> Dict[str, Any]:
        """Step 2: Enrich with cross-reference equivalents from other manufacturers.
        
        This is a placeholder for integration with cross-reference databases.
        """
        primary = ctx.get("primary_match")
        part_number = primary.get("part_number")
        
        logger.info(f"Looking up equivalents for {part_number}")
        
        # PLACEHOLDER: Replace with actual cross-reference database lookup
        # Example integration points:
        # - Pool parts cross-reference API
        # - Manufacturer compatibility tables
        # - Custom equivalents database
        
        # Mock equivalents
        equivalents = [
            "PEN-355331",  # Pentair equivalent
            "JAC-39310700", # Jacuzzi equivalent  
        ]
        
        ctx.set("equivalents", equivalents)
        logger.info(f"Found {len(equivalents)} equivalent parts")
        
        return {"equivalents": equivalents}
    
    async def _check_favorite_step(self, ctx: Context) -> Dict[str, Any]:
        """Step 3: Check if part is marked as favorite."""
        primary = ctx.get("primary_match")
        part_number = primary.get("part_number")
        
        is_favorite = self.favorites_manager.is_favorite(part_number)
        ctx.set("is_favorite", is_favorite)
        
        logger.info(f"Part {part_number} favorite status: {is_favorite}")
        
        return {"is_favorite": is_favorite}
    
    async def _post_to_trello_step(self, ctx: Context) -> Optional[Dict[str, Any]]:
        """Step 4: Post identification results to Trello card if card_id provided."""
        card_id = ctx.get("card_id")
        
        if not card_id:
            logger.info("No card_id provided, skipping Trello post")
            return None
        
        # Build part_info for Trello comment
        part_info = {
            "primary_match": ctx.get("primary_match"),
            "alternatives": ctx.get("alternatives", []),
            "equivalents": ctx.get("equivalents", []),
            "dimensions": ctx.get("dimensions"),
        }
        
        is_favorite = ctx.get("is_favorite", False)
        
        try:
            logger.info(f"Posting part info to Trello card {card_id}")
            response = add_part_info_to_card(
                card_id=card_id,
                part_info=part_info,
                favorite=is_favorite
            )
            
            ctx.set("trello_comment", response)
            logger.info(f"Successfully posted to Trello card {card_id}")
            
            return {"trello_comment": response}
            
        except Exception as e:
            logger.error(f"Failed to post to Trello: {e}")
            ctx.set("trello_error", str(e))
            return {"trello_error": str(e)}
    
    def add_favorite(self, part_number: str) -> bool:
        """Add a part to favorites.
        
        Args:
            part_number: Part number to add
            
        Returns:
            True if added, False if already existed
        """
        return self.favorites_manager.add(part_number)
    
    def remove_favorite(self, part_number: str) -> bool:
        """Remove a part from favorites.
        
        Args:
            part_number: Part number to remove
            
        Returns:
            True if removed, False if not found
        """
        return self.favorites_manager.remove(part_number)
    
    def list_favorites(self) -> list[str]:
        """Get all favorite parts.
        
        Returns:
            Sorted list of favorite part numbers
        """
        return self.favorites_manager.list_all()


__all__ = ["PartIdentifierWorkflow"]
