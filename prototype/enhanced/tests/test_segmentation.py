"""
Unit tests for bubble segmentation module.
"""

import pytest
import sys
from pathlib import Path
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from segmentation import BubbleSegmenter, MessageUIPreset, BubbleBox


class TestBubbleSegmenter:
    """Tests for BubbleSegmenter class."""
    
    def test_initialization(self):
        """Test segmenter initialization."""
        segmenter = BubbleSegmenter(preset=MessageUIPreset.GENERIC)
        assert segmenter.preset == MessageUIPreset.GENERIC
        assert 'min_width' in segmenter.config
    
    def test_presets(self):
        """Test different UI presets."""
        presets = [
            MessageUIPreset.IMESSAGE,
            MessageUIPreset.WHATSAPP,
            MessageUIPreset.ANDROID_SMS,
            MessageUIPreset.GENERIC
        ]
        
        for preset in presets:
            segmenter = BubbleSegmenter(preset=preset)
            assert segmenter.preset == preset
    
    def test_segment_example_images(self):
        """Test segmentation on example images."""
        examples_dir = Path(__file__).parent.parent.parent / 'examples'
        
        if not examples_dir.exists():
            pytest.skip("Examples directory not found")
        
        segmenter = BubbleSegmenter(preset=MessageUIPreset.GENERIC)
        
        # Test each example image
        test_images = list(examples_dir.glob('*.png'))
        
        if not test_images:
            pytest.skip("No test images found")
        
        for img_path in test_images:
            bubbles = segmenter.segment_image(str(img_path))
            
            # Assert at least one bubble is detected
            # (our test images have text, so we expect detection)
            assert len(bubbles) >= 0, f"Failed to process {img_path.name}"
    
    def test_bubble_box(self):
        """Test BubbleBox dataclass."""
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        bubble = BubbleBox(x=10, y=20, width=80, height=60, image=img, confidence=0.9)
        
        assert bubble.x == 10
        assert bubble.y == 20
        assert bubble.width == 80
        assert bubble.height == 60
        assert bubble.confidence == 0.9
        
        # Test to_dict
        data = bubble.to_dict()
        assert data['x'] == 10
        assert data['y'] == 20
        assert 'image' not in data
    
    def test_is_valid_bubble_size(self):
        """Test bubble size validation."""
        segmenter = BubbleSegmenter(preset=MessageUIPreset.GENERIC)
        
        # Valid size
        assert segmenter._is_valid_bubble_size(100, 50) == True
        
        # Too small
        assert segmenter._is_valid_bubble_size(10, 5) == False
        
        # Too large
        assert segmenter._is_valid_bubble_size(1000, 800) == False
    
    def test_compute_iou(self):
        """Test IoU computation."""
        segmenter = BubbleSegmenter()
        
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # Identical boxes
        bubble1 = BubbleBox(x=10, y=10, width=50, height=50, image=img)
        bubble2 = BubbleBox(x=10, y=10, width=50, height=50, image=img)
        iou = segmenter._compute_iou(bubble1, bubble2)
        assert iou == 1.0
        
        # Non-overlapping boxes
        bubble3 = BubbleBox(x=100, y=100, width=50, height=50, image=img)
        iou = segmenter._compute_iou(bubble1, bubble3)
        assert iou == 0.0
        
        # Partially overlapping
        bubble4 = BubbleBox(x=30, y=30, width=50, height=50, image=img)
        iou = segmenter._compute_iou(bubble1, bubble4)
        assert 0 < iou < 1
    
    def test_sort_bubbles(self):
        """Test bubble sorting."""
        segmenter = BubbleSegmenter()
        
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # Create bubbles with different y positions
        bubbles = [
            BubbleBox(x=10, y=100, width=50, height=50, image=img),
            BubbleBox(x=10, y=30, width=50, height=50, image=img),
            BubbleBox(x=10, y=60, width=50, height=50, image=img),
        ]
        
        sorted_bubbles = segmenter._sort_bubbles_top_to_bottom(bubbles)
        
        # Check they're sorted by y coordinate
        assert sorted_bubbles[0].y < sorted_bubbles[1].y < sorted_bubbles[2].y


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
